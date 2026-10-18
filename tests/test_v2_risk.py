from datetime import date
from decimal import Decimal as D
import pytest
from pydantic import ValidationError
from neocloud.risk import (FundingPlan, BondQuote, CashFlow, Repayment, funding_gap,
                           debt_cost, interest_coverage, floating_exposure, maturity_wall, comparison, months_after)
from neocloud.v2_engine import new_v2_run, V2Engine
from neocloud.repository import MemoryRepository
from neocloud.hut_reference import seed, reference

DAY = date(2026, 10, 17)
COMMON = dict(ticker='CRWV', currency='USD', as_of=DAY, provenance='assumption', status='assumption')


def plan(**overrides):
    rows = []
    for cat, side, amt, usable, certainty in [('capex', 'use', '1000', None, 'committed'),
             ('principal', 'use', '100', None, 'committed'), ('cash', 'source', '300', True, 'committed'),
             ('operating_inflow', 'source', '200', True, 'analyst_estimated'),
             ('undrawn', 'source', '400', True, 'analyst_estimated')]:
        rows.append(dict(**COMMON, id=cat, horizon_months=12, category=cat, side=side, amount=amt,
                         entity='Parent', usable=usable, certainty=certainty, cashflow_key=cat))
    return FundingPlan(**{**COMMON, 'id': 'plan', 'horizon_months': 12, 'scope': 'Parent USD',
                           'complete': True, 'market_cap': '2000', 'market_cap_at': DAY, 'lines': rows, **overrides})


def test_sources_uses_stress_and_market_cap_denominator_are_separate():
    p = plan()
    base, down, tight = [funding_gap(p, scenario) for scenario in ('Base', 'Downside', 'Tight credit')]
    assert base['unfunded_gap'] == '200'
    assert D(base['funding_gap_to_market_cap']) == D('.1')
    assert D(down['unfunded_gap']) == 250
    assert D(tight['unfunded_gap']) == 650
    assert base['market_cap_at'] == str(DAY)
    assert funding_gap(p, 'Base', capex_factor=D('1.1'))['unfunded_gap'] == '300.0'


def test_restricted_cash_proceeds_and_unknown_availability_are_not_usable():
    p = plan()
    p.lines[2].usable = False
    assert funding_gap(p)['usable_sources'] == '600'
    p.lines[4].usable = None
    assert funding_gap(p)['usable_sources'] == '200'
    assert 'Availability' in str(funding_gap(p)['warnings'])


def test_double_counted_flows_and_partial_scope_never_produce_precise_gap():
    p = plan()
    p.lines[4].cashflow_key = 'cash'
    assert funding_gap(p)['status'] == 'insufficient_inputs'
    assert funding_gap(p)['unfunded_gap'] is None
    assert funding_gap(plan(complete=False))['funding_gap_to_market_cap'] is None
    p = plan()
    p.lines[4].included_in = 'cash'
    assert funding_gap(p)['usable_sources'] == '500'


def test_funding_currency_and_date_scope_cannot_be_mixed():
    p = plan().model_dump()
    p['lines'][0]['currency'] = 'EUR'
    with pytest.raises(ValidationError):
        FundingPlan.model_validate(p)
    with pytest.raises(ValidationError):
        plan(market_cap_at=None)
    with pytest.raises(ValidationError):
        plan(market_cap='0')
    with pytest.raises(ValueError):
        funding_gap(plan(), inflow_factor=D('NaN'))


def quote(**overrides):
    return BondQuote(**{**COMMON, 'id': 'q', 'instrument_id': 'bond', 'security_id': 'CUSIP-123',
                        'market_yield_pct': '15', 'yield_type': 'YTM', 'quoted_at': '2026-10-16T14:00:00Z',
                        'source_url': 'https://example.com/quote', 'quote_type': 'trade', **overrides})


BOND = dict(instrument_id='bond', security_id='CUSIP-123', currency='USD', name='Specified 2032 bond',
            coupon_pct='9.625', maturity='2032-06-15', evidence_ids=['filing'])


def test_dated_specific_security_yield_does_not_replace_coupon():
    r = debt_cost(BOND, [quote()], DAY)
    assert r['status'] == 'dated_quote'
    assert r['coupon_pct'] == '9.625'
    assert r['quote']['market_yield_pct'] == '15'
    assert D(r['yield_minus_coupon_bps']) == D('537.5')
    assert r['matched_treasury_spread_bps'] is None
    assert debt_cost(BOND, [quote(security_id='wrong-bond')], DAY)['quote'] is None
    assert debt_cost(BOND, [quote(quoted_at='2026-10-18T00:00:00Z')], DAY)['quote'] is None


def test_stale_and_media_quote_is_last_dated_reference_not_current():
    assert debt_cost(BOND, [quote()], date(2026, 11, 1))['status'] == 'Yield unavailable'
    assert debt_cost(BOND, [quote(quote_type='media')], DAY)['status'] == 'Yield unavailable'
    q = quote(treasury_yield_pct='4', treasury_date='2026-10-16', treasury_maturity='2032-06-15', treasury_evidence_ids=['tsy'])
    assert debt_cost(BOND, [q], DAY)['matched_treasury_spread_bps'] == '1100'
    q.treasury_date = date(2026, 10, 15)
    assert debt_cost(BOND, [q], DAY)['matched_treasury_spread_bps'] is None


def cashflow(**overrides):
    return CashFlow(**{**COMMON, 'id': 'ttm', 'period_start': '2025-10-18', 'period_end': DAY,
                       'adjusted_ebitda': '100', 'cash_interest': '25', 'definition': 'Adjusted EBITDA',
                       'cfo': '80', 'maintenance_capex': '10', 'growth_capex': '100', **overrides})


def test_coverage_negative_zero_missing_and_actual_cash_flow():
    assert interest_coverage(cashflow())['coverage'] == '4'
    assert interest_coverage(cashflow())['fcf_after_capex'] == '-30'
    for value in ('-10', '0'):
        result = interest_coverage(cashflow(adjusted_ebitda=value))
        assert result['status'] == 'negative/not meaningful'
        assert result['coverage'] is None
    for value in ('0', None):
        assert interest_coverage(cashflow(cash_interest=value))['coverage'] is None
    assert interest_coverage(None)['status'] == 'insufficient_inputs'
    with pytest.raises(ValidationError):
        cashflow(period_start='2026-07-01')


def test_fixed_yields_unknown_hedges_and_active_partial_hedges():
    common = dict(currency='USD', snapshot_date=str(DAY), outstanding_principal='1000', evidence_ids=[])
    items = [dict(**common, instrument_id='fixed', rate_type='fixed'),
             dict(**common, instrument_id='floating', rate_type='floating', hedge_status='partial', hedge_notional='600',
                  hedge_effective_date='2026-01-01', hedge_end_date='2027-01-01'),
             dict(**common, instrument_id='unknown', rate_type='floating', hedge_status='unknown')]
    r = floating_exposure(items, DAY)['by_currency']['USD']
    assert r['fixed'] == '1000' and r['hedged_floating'] == '600'
    assert r['unhedged_floating'] == '400' and r['unknown_hedge'] == '1000'
    assert D(r['annual_shock']) == 8
    items[1]['hedge_end_date'] = None
    assert floating_exposure(items, DAY)['by_currency']['USD']['unknown_hedge'] == '2000'


def repayment(**overrides):
    return Repayment(**{**COMMON, 'id': 'r', 'instrument_id': 'debt', 'entity': 'SPV', 'amount': '200',
                        'due_start': '2027-01-01', 'due_end': '2027-12-31', 'precision': 'year',
                        'kind': 'amortization', 'cashflow_key': '2027', **overrides})


def test_maturity_ranges_boundary_amortization_and_deduplication():
    rows = [repayment(), repayment(id='same-aggregate', cashflow_key='2027'),
            repayment(id='bullet', due_start='2028-10-17', due_end='2028-10-17', precision='day',
                      cashflow_key='bullet', amount='300', kind='bullet'),
            repayment(id='future', due_start='2030-01-01', due_end='2030-12-31', cashflow_key='future')]
    r = maturity_wall(rows, DAY)
    assert len(r['rows']) == 2
    assert r['rows'][0]['horizons']['12'] == 'overlaps_boundary'
    assert r['known_due']['USD'] == {'12': '0', '18': '200', '24': '500'}
    assert r['status'] == 'partial_schedule'
    assert months_after(date(2024, 2, 29), 12) == date(2025, 2, 28)
    assert maturity_wall([], DAY)['known_due'] == {}


def test_live_unreviewed_assumptions_are_excluded_and_forecasts_not_rebased():
    run = new_v2_run(['CRWV'], 'simulated', DAY)
    result = comparison(run, DAY)
    assert result['tickers']['CRWV']['funding'][0]['unfunded_gap'] is not None
    assert comparison(run, date(2026, 10, 18))['tickers']['CRWV']['funding'][0]['unfunded_gap'] is None
    run['mode'] = 'live'
    assert comparison(run, DAY)['tickers']['CRWV']['funding'][0]['unfunded_gap'] is None


def test_hut_reference_legal_scope_and_provenance_survive_seed():
    ref = reference()
    river, beacon, revolver = ref['instruments']
    assert river['coupon_pct'] == '6.192' and river['maturity'] == '2042-11-15'
    assert beacon['credit_rating'] == 'Baa2' and 'project' in beacon['rating_scope']
    assert revolver['outstanding_principal'] is None
    assert revolver['commitment_amount'] == '1070000000'
    assert ref['contracts'][0]['guarantee_cap'] is None
    assert 'not all HUT' in ref['contracts'][0]['covered_obligations']
    assert 'in USD thousands' in next(e['excerpt'] for e in ref['evidence'] if e['id'] == 'hut-debt-table')
    run = new_v2_run(['HUT'], 'live', DAY)
    seed(run)
    assert all(i['verification_status'] == 'source_matched' for i in run['instruments'])
    assert comparison(run, DAY)['tickers']['HUT']['contracts'] == []
    assert all(e['id'].startswith(run['id']) for e in run['evidence'])


def test_fabricated_risk_evidence_or_quote_sources_are_rejected():
    run = new_v2_run(['CRWV'], 'live', DAY)
    e = V2Engine(MemoryRepository(), None)
    current = {'id': 'task', 'ticker': 'CRWV'}
    raw = quote().model_dump(mode='json')
    e.accept_risk(run, current, {'bond_quotes': [raw]}, {})
    assert not run['risk']['bond_quotes']
    assert run['events'][-1]['kind'] == 'risk_rejected'


def test_sourced_amount_units_and_google_scope_cannot_be_invented():
    from neocloud.risk_validation import validate_risk_record
    evidence = [{'id': 'e', 'excerpt': 'River Bend Fluidstack lease has a Google backstop of lease payments; USD 20 million.',
                 'source_url': 'https://www.sec.gov/filing'}]
    fact = {'evidence_ids': ['e'], 'amount': '20000000'}
    assert validate_risk_record('funding_plans', fact, evidence)
    fact['amount'] = '999000000'
    with pytest.raises(ValueError, match='Amount or units'):
        validate_risk_record('funding_plans', fact, evidence)
    with pytest.raises(ValueError, match='Google support'):
        validate_risk_record('contracts', {'evidence_ids': ['e'], 'project': 'River Bend', 'customer': 'Fluidstack',
                                           'guarantor': 'Google', 'covered_obligations': 'Guarantees all Hut 8 corporate debt'}, evidence)


def test_refinancing_stress_is_an_incremental_scenario_use_and_floors_limit_shock():
    p = plan()
    p.lines[1].rate_sensitivity = 'future_refinancing'
    p.lines[1].rate_sensitive_principal = D(100)
    assert D(funding_gap(p, 'Downside', delta_bps=200)['unfunded_gap']) == D(252)
    item = dict(instrument_id='floored', currency='USD', snapshot_date=str(DAY), outstanding_principal='1000',
                rate_type='floating', hedge_status='unhedged', reference_rate_pct='1', floor_pct='2')
    r = floating_exposure([item], DAY, 200)
    assert r['by_currency']['USD']['annual_shock'] == '10.00'
    item.update(hedge_status='hedged', hedge_notional='1000', hedge_effective_date='2025-01-01', hedge_end_date='2026-01-01')
    assert floating_exposure([item], DAY)['by_currency']['USD']['unhedged_floating'] == '1000'


def test_complete_dated_leverage_preserves_numerator_denominator_and_negative_net_cash():
    from neocloud.risk import BalanceSnapshot, leverage_context
    balance = BalanceSnapshot(**COMMON, id='balance', scope='Consolidated', debt_scope_complete=True,
                              gross_debt='1000', unrestricted_cash='1200', equity_market_cap='2000', equity_market_cap_at=DAY)
    r = leverage_context([], [balance])
    assert r['gross_debt_to_market_cap'] == '0.5'
    assert r['net_debt_to_market_cap'] == '-0.1'
    balance.debt_scope_complete = False
    assert leverage_context([], [balance])['gross_debt_to_market_cap'] is None
