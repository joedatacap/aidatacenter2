from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import pytest
from neocloud.directory import BORROWING_BASIS, build_directory


def sample():
    def metric(value):
        return {'value': value, 'unit': 'USD', 'source_ids': ['filing'],
                'basis_key': BORROWING_BASIS, 'scope': 'consolidated'}
    return {'reviewed_at': '2026-11-11',
            'sources': [{'id': 'filing', 'url': 'https://www.sec.gov/Archives/example.htm',
                         'title': 'Test accounting record', 'excerpt': 'Test fixture, not actual financials',
                         'published_at': '2026-11-01'}],
            'companies': [{'ticker': 'TEST', 'group': 'gpu_cloud', 'synthetic': False, 'as_of': '2026-09-30',
                           'filed_at': '2026-11-01', 'metrics': {
                               'debt': metric('100'), 'assets': metric('300'), 'cash': metric('50'),
                               'coupon': {'value': None, 'unit': 'percent', 'source_ids': []}}}]}


def test_ratio_uses_same_date_evidenced_carrying_values_and_does_not_mutate_inputs():
    raw = sample()
    original = deepcopy(raw)
    result = build_directory(raw)
    ratio = result['companies'][0]['metrics']['debt_assets']
    assert Decimal(ratio['value']) == Decimal('100') / Decimal('300') * 100
    assert ratio['rankable'] and ratio['source_ids'] == ['filing']
    assert raw == original


@pytest.mark.parametrize('invalid', ['unknown', 'date_mismatch', 'zero_assets', 'foreign_currency', 'commitment', 'scope_mismatch'])
def test_unknown_and_incomparable_inputs_never_produce_ranked_ratios(invalid):
    raw = sample()
    metrics = raw['companies'][0]['metrics']
    if invalid == 'unknown': metrics['debt']['value'] = None
    if invalid == 'date_mismatch': metrics['assets']['as_of'] = '2026-06-30'
    if invalid == 'zero_assets': metrics['assets']['value'] = '0'
    if invalid == 'foreign_currency': metrics['debt']['unit'] = 'EUR'
    if invalid == 'commitment': metrics['debt']['basis_key'] = 'facility_commitment'
    if invalid == 'scope_mismatch': metrics['assets']['scope'] = 'parent_only'
    ratio = build_directory(raw)['companies'][0]['metrics']['debt_assets']
    assert ratio['value'] is None and not ratio['rankable']


def test_evidenced_zero_borrowing_is_distinct_from_unknown():
    raw = sample()
    raw['companies'][0]['metrics']['debt']['value'] = '0'
    metrics = build_directory(raw)['companies'][0]['metrics']
    assert metrics['debt']['rankable'] and metrics['debt_assets']['value'] == '0'


@pytest.mark.parametrize('failure', ['no_evidence', 'missing_source', 'future_date', 'nonfinite', 'unreconciled'])
def test_invalid_data_stops_the_bundle_instead_of_publishing_a_number(failure):
    raw = sample()
    debt = raw['companies'][0]['metrics']['debt']
    if failure == 'no_evidence': debt['source_ids'] = []
    if failure == 'missing_source': debt['source_ids'] = ['does-not-exist']
    if failure == 'future_date': raw['companies'][0]['as_of'] = '2027-01-01'
    if failure == 'nonfinite': debt['value'] = 'NaN'
    if failure == 'unreconciled': debt['components'] = [{'value': '99'}]
    with pytest.raises(ValueError): build_directory(raw)


def test_directory_bundle_matches_validated_curated_inputs():
    raw_path = Path('neocloud/data/debt_directory.json')
    assert raw_path.exists(), 'Curated source ledger must ship with the directory'
    bundle = json.loads(Path('preview/data.json').read_text())
    assert bundle == build_directory(json.loads(raw_path.read_text()))
    assert 10 <= len(bundle['companies']) <= 20
    assert all(c['metrics']['debt_assets']['as_of'] == c['as_of'] for c in bundle['companies'])


def test_published_coverage_and_special_scope_cases_are_explicit():
    data = json.loads(Path('preview/data.json').read_text())
    companies = {c['ticker']: c for c in data['companies']}
    assert len(companies) == 16
    assert sum(c['metrics']['debt']['rankable'] for c in companies.values()) == 15
    assert companies['GLXY']['metrics']['debt']['value'] is None
    assert companies['GLXY']['metrics']['debt_assets']['value'] is None
    assert companies['HUT']['metrics']['debt']['value'] == '7628225000'
    assert companies['NBIS']['as_of'] == '2026-06-30'
    assert companies['NBIS']['metrics']['coupon']['as_of'] == companies['NBIS']['as_of']
    assert companies['HIVE']['metrics']['coupon']['value'] == '0'
    assert companies['EQIX']['source_precision_usd'] == '1000000'
    assert companies['HIVE']['metrics']['coupon']['issue_date'] == '2026-04-21'
    assert companies['NSCALE']['listing_status'] == 'private_pending_ipo'
    assert companies['NSCALE']['metrics']['coupon']['value'] is None
    assert companies['NSCALE']['comparison_caveat']
    dlr_finance_lease = next(lease for lease in companies['DLR']['debt_context']['leases']
                             if lease['kind'] == 'finance')
    assert dlr_finance_lease['value'] is None
    assert dlr_finance_lease['source_ids'] == []
    assert companies['DLR']['metrics']['debt']['value'] == '19494615000'
    assert len(data['instruments']) == 44
    assert len(data['coverage_watchlist']) == 3


def test_note_status_does_not_infer_latest_balance_or_use_original_issuance():
    data = json.loads(Path('preview/data.json').read_text())
    notes = {n['id']: n for n in data['instruments']}
    assert notes['CLOUD-CRWV-1']['outstanding_status'] == 'verified_at_earlier_date'
    assert notes['CLOUD-CRWV-1']['outstanding_principal']['as_of'] == '2026-06-30'
    assert notes['CLOUD-NBIS-7']['outstanding_status'] == 'terms_only'
    assert notes['CLOUD-NBIS-7']['outstanding_principal']['value'] is None
    assert notes['ADJ-GLXY-SELECTED']['outstanding_status'] == 'verified_at_snapshot'
    assert notes['ADJ-GLXY-SELECTED']['outstanding_principal']['value'] is None
    assert notes['WULF-2030-775']['issue_date'] is None
    assert 'Conflicting' in notes['WULF-2030-775']['issue_date_note']
    assert 'independent-nbis-2032-indenture' in notes['CLOUD-NBIS-4']['source_ids']
    assert 'accretion' in notes['CLOUD-NBIS-5']['outstanding_principal']['basis']


def test_synthetic_assumptions_cannot_enter_actual_rankings():
    raw = sample()
    raw['companies'][0]['synthetic'] = True
    with pytest.raises(ValueError, match='actual reviewed'): build_directory(raw)


def test_dollar_rank_excludes_a_balance_from_another_observation_date():
    raw = sample()
    raw['companies'][0]['metrics']['debt']['as_of'] = '2026-06-30'
    metrics = build_directory(raw)['companies'][0]['metrics']
    assert not metrics['debt']['rankable']
    assert metrics['debt_assets']['value'] is None
    assert metrics['debt']['as_of'] == '2026-06-30'


def test_source_cannot_precede_the_financial_snapshot():
    raw = sample()
    raw['companies'][0]['filed_at'] = '2026-01-01'
    with pytest.raises(ValueError, match='precede'): build_directory(raw)


@pytest.mark.parametrize('invalid', ['currency_units', 'maturity_before_issue'])
def test_coupon_units_and_chronology_are_not_inferred(invalid):
    raw = sample()
    coupon = {'value': '5', 'unit': 'percent', 'currency': 'USD', 'source_ids': ['filing'],
              'as_of': '2026-09-30', 'instrument': 'Test note', 'type': 'senior_unsecured',
              'rate_type': 'fixed', 'issue_date': '2026-01-01', 'maturity': '2030-01-01'}
    if invalid == 'currency_units': coupon['unit'] = 'USD'
    if invalid == 'maturity_before_issue': coupon['maturity'] = '2025-12-31'
    raw['companies'][0]['metrics']['coupon'] = coupon
    with pytest.raises(ValueError): build_directory(raw)


def note_sample():
    return {'id': 'test-note', 'ticker': 'TEST', 'value': '0', 'unit': 'percent',
            'currency': 'USD', 'instrument': 'Test convertible', 'type': 'convertible',
            'maturity': '2030', 'as_of': '2026-09-30', 'issue_date': '2025-01-01',
            'rate_type': 'fixed', 'source_ids': ['filing'],
            'outstanding_status': 'verified_at_snapshot', 'outstanding_evidence_ids': ['filing'],
            'outstanding_principal': {'value': None, 'unit': 'USD', 'as_of': '2026-09-30', 'source_ids': []}}


def test_note_existence_can_be_verified_without_inventing_a_principal_amount():
    raw = sample()
    raw['instruments'] = [note_sample()]
    note = build_directory(raw)['instruments'][0]
    assert note['value'] == '0' and note['rankable']
    assert note['outstanding_principal']['value'] is None


@pytest.mark.parametrize('invalid', ['balance_date', 'no_status_evidence', 'currency', 'duplicate', 'unknown_company'])
def test_note_inventory_rejects_inferred_dates_balances_and_identity(invalid):
    raw = sample()
    note = note_sample()
    raw['instruments'] = [note]
    if invalid == 'balance_date': note['outstanding_principal'] = {'value': '90', 'unit': 'USD', 'as_of': '2026-06-30', 'source_ids': ['filing']}
    if invalid == 'no_status_evidence': note['outstanding_evidence_ids'] = []
    if invalid == 'currency': note['currency'] = 'EUR'
    if invalid == 'duplicate': raw['instruments'].append(deepcopy(note))
    if invalid == 'unknown_company': note['ticker'] = 'OTHER'
    with pytest.raises(ValueError): build_directory(raw)


def test_partial_principal_bridge_never_becomes_a_consolidated_company_total():
    raw = sample()
    company = raw['companies'][0]
    company['debt_context'] = {'bridges': [{'label': 'Notes only', 'scope': 'notes_only',
      'complete_company_scope': False, 'as_of': company['as_of'], 'unit': 'USD',
      'principal': '200', 'carrying': '150', 'source_ids': ['filing']}]}
    bridge = build_directory(raw)['companies'][0]['debt_context']['bridges'][0]
    assert bridge['difference'] == '50'
    assert not bridge['complete_company_scope']
    assert company['metrics']['debt']['value'] == '100'
    company['debt_context']['bridges'][0]['complete_company_scope'] = True
    with pytest.raises(ValueError, match='scope'): build_directory(raw)


def test_consolidated_principal_bridge_must_match_the_ranked_recorded_amount():
    raw = sample()
    raw['companies'][0]['debt_context'] = {'bridges': [{'label': 'Consolidated',
      'scope': 'consolidated_borrowings', 'complete_company_scope': True,
      'as_of': '2026-09-30', 'unit': 'USD', 'principal': '200', 'carrying': '150', 'source_ids': ['filing']}]}
    with pytest.raises(ValueError, match='match recorded'): build_directory(raw)
