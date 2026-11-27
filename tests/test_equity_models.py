"""Independent numerical checks for research scenarios, not forecast accuracy tests.

Amounts are USD millions and share denominators are millions. These tests enforce
accounting identities and missingness; they cannot validate an analyst assumption.
"""
import json
import math
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / 'neocloud/data/equity'
TICKERS = ('nbis', 'iren', 'crwv', 'agpu')


def load(ticker):
    return json.loads((DATA / f'{ticker}.json').read_text())


def facts(data):
    return {row['metric']: row['value'] for row in data['facts']}


def approximately(actual, expected, tolerance=0.011):
    assert actual is not None and math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance), (actual, expected)


def check_model_schema_units_sources_and_nulls(ticker):
    data = load(ticker)
    assert data['ticker'] == ticker.upper()
    assert len(data['models']) == 6
    assert {(m['year'], m['scenario']) for m in data['models']} == {
        (y, s) for y in (2027, 2028) for s in ('bear', 'base', 'bull')}
    for fact in data['facts']:
        assert fact['source'] in data['sources']
        assert fact['period'] and fact['unit']
        if fact['status'] == 'unavailable':
            assert fact['value'] is None
        if fact['value'] is not None:
            assert isinstance(fact['value'], (int, float))
            assert math.isfinite(fact['value'])
        if fact['metric'] in ('cash', 'debt', 'restricted_cash', 'ttm_revenue'):
            assert fact['unit'] in ('USD million', 'USD millions')
    for model in data['models']:
        assert model['sources'] and set(model['sources']) <= data['sources'].keys()
        assert model['period'] and model['method'] and model['gaps']
        assert set(('revenue', 'gross_profit', 'ebitda', 'net_income', 'capex', 'fcf')) <= model['metrics'].keys()
        for value in model['metrics'].values():
            assert value is None or (math.isfinite(value) and abs(value) < 1_000_000)
    for source in data['sources'].values():
        assert source['url'].startswith('https://')


def test_nbis_six_independent_income_and_cashflow_bridges():
    for model in load('nbis')['models']:
        i, x = model['inputs'], model['metrics']
        revenue = i['avg_revenue_earning_mw'] * i['realized_annual_revenue_per_mw_m'] + i['other_revenue_m']
        da = i['average_in_service_gpu_cost_m'] / i['gpu_life_years'] + i['infrastructure_da_m']
        gross_before_da = revenue * (1 - i['cash_cost_of_revenue_pct'] / 100)
        adjusted = gross_before_da - i['cash_opex_m']
        ebitda = adjusted - i['sbc_m']
        pretax = (ebitda - da - i['average_debt_m'] * i['cash_interest_rate_pct'] / 100
                  - i['customer_financing_noncash_interest_m']
                  + i['average_cash_m'] * i['interest_income_rate_pct'] / 100)
        income = pretax - max(pretax, 0) * i['tax_rate_on_profit_pct'] / 100
        fcf = (income + da + i['sbc_m'] + i['customer_financing_noncash_interest_m']
               + i['new_customer_prepayments_m'] - i['prepaid_revenue_recognition_m']
               - i['other_working_capital_use_m'] - i['capex_m'])
        for key, value in [('revenue', revenue), ('gross_profit', gross_before_da-da),
                           ('ebitda', ebitda), ('net_income', income), ('capex', i['capex_m']), ('fcf', fcf)]:
            approximately(x[key], value)
        approximately(i['adjusted_ebitda_m'], adjusted)
        assert i['prepaid_revenue_recognition_m'] > 0
        assert not math.isclose(x['fcf'], fcf + i['prepaid_revenue_recognition_m'], abs_tol=.01)


def test_nbis_share_identity_and_reverse_valuation_exclude_restricted_cash():
    d = load('nbis'); f = facts(d); v = d['valuation']
    approximately(f['minimum_economic_shares'], f['common_shares'] + f['prefunded_warrants'], 1e-9)
    approximately(v['basic_equity_value_m'], f['price']*f['common_shares'], .001)
    approximately(v['economic_equity_reference_m'], f['price']*f['minimum_economic_shares'], .001)
    ev = v['economic_equity_reference_m'] + f['debt'] - f['cash'] + f['noncontrolling_interest']
    approximately(v['historical_ev_reference_m'], ev, .001)
    assert abs(v['historical_ev_reference_m'] - (ev - f['restricted_cash'])) > 1000
    base = next(m['metrics'] for m in d['models'] if m['year']==2028 and m['scenario']=='base')
    approximately(v['reverse_2028_base_revenue_multiple'], ev/base['revenue'], .0006)
    approximately(v['reverse_2028_base_ebitda_multiple'], ev/base['ebitda'], .0006)


def test_iren_standardized_income_and_prepaid_cash_missingness():
    for model in load('iren')['models']:
        i, x, supplementary = model['inputs'], model['metrics'], model['supplemental_metrics']
        if model['year']==2027:
            revenue = sum(i['quarter_revenue'])
            assert i['quarter_revenue'][0] == 228
            assert i['capex'] == 4824 + 15000
            assert '2027-06-30' in model['period']
        else:
            revenue = (i['contracted_arr_anchor'] * i['existing_program_revenue_capture']
                       + i['additional_average_active_it_mw'] * i['annual_revenue_per_new_it_mw']
                       * i['new_capacity_recognition_capture'])
            assert '2028-06-30' in model['period']
        gross_before_da = revenue*i['gross_margin_ex_da']
        adjusted = gross_before_da-i['cash_opex_ex_sbc']
        ebitda = adjusted-i['stock_compensation']
        approximately(x['revenue'], revenue)
        approximately(x['gross_profit'], gross_before_da-i['depreciation_amortization'])
        approximately(x['ebitda'], ebitda)
        approximately(supplementary['adjusted_ebitda_proxy'], adjusted)
        approximately(x['net_income'], ebitda-i['depreciation_amortization']-i['net_interest']-i['cash_tax'])
        approximately(supplementary['cash_flow_before_customer_financing_and_prepaid_revenue_adjustment'],
                      adjusted-i['net_interest']-i['cash_tax']-i['capex']-i['working_capital_cash_use'])
        assert x['fcf'] is None, 'Missing prepayment recognition cannot become standardized FCF'


def test_iren_valuation_claims_once_and_zero_floor_with_deficit():
    d = load('iren'); v = d['valuation']; f = facts(d)
    assert f['debt'] == 9897 + 311
    assert f['restricted_cash'] == 2208 + 48
    for row in v['scenarios']:
        model = next(m for m in d['models'] if m['year']==2028 and m['scenario']==row['scenario'])
        adjusted = model['supplemental_metrics']['adjusted_ebitda_proxy']
        ev = adjusted*row['ev_ebitda']
        raw = ev-row['assumed_debt_and_finance_leases']+row['assumed_unrestricted_cash']-row['assumed_other_claims']
        approximately(row['enterprise_value'], ev)
        approximately(row['raw_common_equity'], raw)
        approximately(row['common_equity'], max(0,raw))
        approximately(row['price'], max(0,raw)/row['assumed_diluted_shares'])
        assert row['deficit'] == (raw < 0)
    r = v['reverse']
    approximately(r['required_adjusted_ebitda'], (r['price']*r['assumed_shares']+r['assumed_net_claims'])/r['ev_ebitda'])
    assert d['financing']['gap_12m'] is None and d['financing']['gap_24m'] is None
    assert d['report']['target_12m'] is None


def test_agpu_partial_project_never_promoted_to_company_forecast():
    for m in load('agpu')['models']:
        i = m['inputs']
        annual = i['georgia_lifetime_revenue_m']/i['contract_years']
        approximately(i['assumed_level_revenue_m'], annual, 1e-8)
        approximately(m['components']['georgia_revenue_sensitivity_m'], annual*i['assumed_annual_service_fraction'], 1e-8)
        assert all(value is None for value in m['metrics'].values())


def test_agpu_common_cash_hurdle_no_double_subtraction_of_project_debt():
    d = load('agpu'); f = facts(d); v = d['valuation']; r = v['reverse']
    economic_shares = f['common_shares_sep30']+f['prefunded_warrants_sep30']
    approximately(v['economic_shares_m'], economic_shares, 1e-9)
    exposure = f['price']*economic_shares
    approximately(v['partial_equity_exposure_m'], exposure, 1e-6)
    annuity_factor = sum((1+r['discount_rate_pct']/100)**(-t) for t in range(1, r['years']+1))
    approximately(r['annual_common_cash_m']*annuity_factor, exposure, 3e-6)
    approximately(r['dilution_sensitivity_m']*annuity_factor, f['price']*(economic_shares+2), 3e-6)
    assert r['terminal_equity_value_m'] == 0
    assert f['diluted_shares'] is None and v['target_12m'] is None
    approximately(f['q3_gross_profit'], f['q3_revenue']-f['q3_cost_revenue'], 1e-8)


def test_all_model_schemas():
    for ticker in TICKERS:
        check_model_schema_units_sources_and_nulls(ticker)


def test_crwv_prepaid_cash_interest_and_funding_rollforward():
    d = load('crwv')
    for m in d['models']:
        i, x = m['inputs'], m['metrics']
        adjusted = i['revenue'] * i['adjusted_ebitda_margin']
        sbc = i['revenue'] * i['sbc_to_revenue']
        da = i['revenue'] * i['da_to_revenue']
        pretax = adjusted-sbc-da-i['cash_interest']
        tax = max(pretax, 0)*i['tax_rate_on_positive_pretax']
        prepaid_recognition = i['revenue']*i['prepaid_revenue_recognition_rate']
        customer_cash = i['customer_cash_receipts']-prepaid_recognition
        fcf = adjusted-i['cash_interest']-tax-i['cash_capex']+customer_cash+i['other_working_capital_cash']
        approximately(x['ebitda'], adjusted-sbc)
        approximately(x['adjusted_ebitda'], adjusted)
        approximately(x['net_income'], pretax-tax)
        approximately(x['fcf'], fcf)
        approximately(i['prepaid_revenue_recognized'], prepaid_recognition)
        approximately(i['net_customer_cash_benefit'], customer_cash)
        approximately(i['ending_prepaid_balance_assumed'], i['opening_prepaid_balance_assumed']+customer_cash)
        assert i['ending_prepaid_balance_assumed'] >= 0
        bridge = next(b for b in d['financing']['bridges'][m['scenario']]['annual'] if b['year']==m['year'])
        equity = i['new_atm_shares']*i['assumed_issue_price']*(1-i['issuance_fee'])
        draw = max(0,i['minimum_operating_cash']-i['opening_cash']-fcf+i['scheduled_principal']-equity)
        debt = i['opening_debt']-i['scheduled_principal']+draw
        cash = i['opening_cash']+fcf+draw+equity-i['scheduled_principal']
        approximately(bridge['new_debt_required'], draw)
        approximately(bridge['ending_debt'], debt)
        approximately(bridge['ending_cash'], cash)
        approximately(i['cash_interest'], i['annual_cash_interest_rate']*(i['opening_debt']+debt)/2)
        approximately(i['equity_proceeds'], equity)
        assert x['gross_profit'] is None
        if m['year']==2028:
            prior = next(b for b in d['financing']['bridges'][m['scenario']]['annual'] if b['year']==2027)
            approximately(i['opening_debt'], prior['ending_debt'])
            approximately(i['opening_cash'], prior['ending_cash'])
            approximately(i['ending_scenario_shares'], prior['ending_scenario_shares']+i['new_atm_shares']+i['assumed_rsu_vesting'])


def test_crwv_scenario_capitalization_and_reverse_hurdles():
    d = load('crwv'); historical = d['valuation']['current_historical_claims_bridge']
    approximately(historical['equity_capitalization'], historical['price']*historical['basic_shares'])
    approximately(historical['enterprise_value'], historical['equity_capitalization']+historical['debt_principal']+historical['finance_leases']-historical['cash'])
    for v in d['valuation']['cases']:
        m = next(m for m in d['models'] if (m['year'],m['scenario'])==(v['year'],v['scenario']))
        multiple = v['normalized_unlevered_fcf_fraction_of_adjusted_ebitda']*(1+v['perpetual_growth'])/(v['required_enterprise_return']-v['perpetual_growth'])
        ev = m['metrics']['adjusted_ebitda']*multiple
        raw = ev-v['debt_including_finance_leases']+v['surplus_cash']-v['additional_claims_assumed']
        approximately(v['implied_ev_adjusted_ebitda_multiple'], multiple)
        approximately(v['enterprise_value'], ev)
        approximately(v['raw_equity'], raw)
        approximately(v['equity'], max(0,raw))
        approximately(v['per_share'], max(0,raw)/v['scenario_shares'])
        hurdle = (v['reverse_reference_price']*v['scenario_shares']+v['debt_including_finance_leases']-v['surplus_cash']+v['additional_claims_assumed'])/multiple
        approximately(v['reverse_required_adjusted_ebitda'], hurdle)
        approximately(v['reverse_required_revenue'], hurdle/m['inputs']['adjusted_ebitda_margin'])
        bridge = next(b for b in d['financing']['bridges'][v['scenario']]['annual'] if b['year']==v['year'])
        approximately(v['debt_including_finance_leases'], bridge['ending_debt'])
    assert d['valuation']['published_target'] is None


def test_iren_dated_book_equity_claim_reconciliation():
    d = load('iren'); r = d['ownership_audit']['book_equity_reconciliation']; f = facts(d)
    approximately(r['parent_equity'], sum(r[k] for k in ('ordinary_capital','b_capital','apic','deficit','oci')))
    approximately(r['assets']-r['liabilities'], r['parent_equity'])
    assert f['preferred']==0 and f['noncontrolling_interest']==0
    for fact in d['facts']:
        if fact['metric'] in ('preferred','noncontrolling_interest'):
            assert fact['period']=='2026-09-30' and 'book' in fact['note']


if __name__ == '__main__':
    tests = [(name, fn) for name, fn in globals().copy().items() if name.startswith('test_') and callable(fn)]
    for name, fn in tests:
        fn()
        print('PASS', name)
    print(f'{len(tests)} independent model tests passed')


def test_nbis_customer_funding_period_and_scope():
    funding = load("nbis")["financing"]["september_customer_funding"]
    approximately(funding["closing_deferred_revenue_m"] - funding["opening_deferred_revenue_m"],
                  funding["nine_month_net_increase_m"])
    approximately(funding["management_expected_recognition_through_2028_09_30_m"],
                  funding["rpo_m"] * 0.4)
    assert funding["gross_customer_cash_received_m"] is None
