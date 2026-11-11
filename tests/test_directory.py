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
    assert len(companies) == 15
    assert sum(c['metrics']['debt']['rankable'] for c in companies.values()) == 14
    assert companies['GLXY']['metrics']['debt']['value'] is None
    assert companies['GLXY']['metrics']['debt_assets']['value'] is None
    assert companies['HUT']['metrics']['debt']['value'] == '7628225000'
    assert companies['NBIS']['as_of'] == '2026-06-30'
    assert companies['NBIS']['metrics']['coupon']['as_of'] > companies['NBIS']['as_of']
    assert companies['HIVE']['metrics']['coupon']['value'] == '0'
    assert companies['EQIX']['source_precision_usd'] == '1000000'


def test_synthetic_assumptions_cannot_enter_actual_rankings():
    raw = sample()
    raw['companies'][0]['synthetic'] = True
    with pytest.raises(ValueError, match='actual reviewed'): build_directory(raw)
