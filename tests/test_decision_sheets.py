"""Validation for sourced decision sheets and dated market observations."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest
from scripts.build_terminal import load_decisions

NOW = datetime(2026, 11, 26, 12, tzinfo=timezone.utc)
COMPANIES = [{'id': 'crwv', 'sources': [{'id': 'filing', 'published': '2026-11-20'}]}]


def brief():
    return {'id': 'crwv', 'reviewed_at': '2026-11-26T10:00:00Z', 'stance': 'Synthetic watch',
            'question': 'What evidence?', 'takeaway': 'Conditional', 'valuation_note': 'Assumptions only',
            'sources': [], 'cases': [{'name': name, 'thesis': 'Hypothesis', 'requires': 'Evidence',
                'invalidated_by': 'Counterevidence', 'sources': ['filing']} for name in ['Bull', 'Base', 'Bear']],
            'checkpoints': [{'date': '2026-12-31', 'label': 'Target', 'watch': 'Evidence',
                'positive': 'Confirmed', 'negative': 'Rejected', 'sources': ['filing']}],
            'metrics': [{'label': 'Cash', 'value': 'Unknown', 'basis': 'Not verified', 'sources': ['filing']}],
            'gaps': ['Unknown']}


def sheet():
    return {'id': 'crwv', 'reviewed_at': '2026-11-26T10:00:00Z',
            'sources': [{'id': 'sheet-source', 'title': 'Synthetic filing', 'url': 'https://example.org/filing',
                         'published': '2026-11-25'}],
            'capital_bridge': [{'label': 'Net cash', 'value': -20, 'basis': 'Signed synthetic net claim',
                                'sources': ['filing', 'sheet-source']}],
            'decision': dict(new_position='Wait for evidence', existing_holding='Review risk',
                             upgrade='Funding confirmed', downgrade='Funding withdrawn'),
            'gaps': ['Forward financing is unknown'],
            'horizon': '30–90 days', 'model': {'convention': 'Hypothetical'},
            'scenarios': [{'name': 'Stress', 'inputs': dict(revenue=100, margin=20, multiple=5,
                        debt=60, cash=20, claims=0, shares=10), 'rationale': 'Explicit assumptions',
                        'sources': ['sheet-source']}]}


def market():
    return {'crwv': {'as_of': '2026-11-25', 'retrieved_at': '2026-11-26T10:00:00Z',
        'source_url': 'https://example.org/history', 'provider': 'Synthetic fixture',
        'close': 10, 'day_low': 9, 'day_high': 11, 'day_volume': 1000,
        'note': 'Completed session fixture; not live',
        'metrics': {'ok': True, 'firstDate': '2026-10-28', 'lastDate': '2026-11-25', 'suppliedSessions': 20,
                    'complete': False, 'volatilityReturnCount': 19, 'return5SessionPct': -10,
                    'averageVolume20': 1000, 'averageDollarVolume20': 10000,
                    'closeLow20': 9, 'closeHigh20': 15, 'meanTrueRange14': 2,
                    'realizedVolatility20Pct': None, 'status': 'Partial history',
                    'dollarVolumeBasis': 'Close times volume proxy'},
        'levels': {'review_low': 9, 'recovery_level': 12, 'rationale': 'Illustrative review levels'}}}


def load(tmp_path, record=None, observations=None, companies=None):
    directory = tmp_path / 'neocloud/data/decisions'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'crwv.json').write_text(json.dumps(brief()))
    if record is not None:
        (directory / 'crwv-sheet.json').write_text(json.dumps(record))
    if observations is not None:
        (directory / 'market-context.json').write_text(json.dumps(observations))
    return load_decisions(tmp_path, companies or COMPANIES, now=NOW)


def mutate(record, path, value):
    if not path:
        return value
    parent = record
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    return record


def test_optional_files_preserve_old_briefs_and_empty_new_collections(tmp_path):
    result = load(tmp_path)
    assert result['briefs'][0]['id'] == 'crwv'
    assert result['sheets'] == [] and result['market'] == {}
    absent = load_decisions(tmp_path / 'absent', COMPANIES, now=NOW)
    assert absent == {'briefs': [], 'queue': None, 'sheets': [], 'market': {}}


def test_preserve_sources_signed_bridge_extra_metadata_and_missing_volatility(tmp_path):
    original_sheet, original_market = sheet(), market()
    result = load(tmp_path, original_sheet, original_market)
    assert result['sheets'] == [original_sheet]
    assert result['market'] == original_market
    assert result['sheets'][0]['capital_bridge'][0]['value'] == -20
    assert result['market']['crwv']['metrics']['realizedVolatility20Pct'] is None
    assert result['market']['crwv']['metrics']['return5SessionPct'] == -10
    result['sheets'][0]['model']['convention'] = 'Changed result'
    assert original_sheet['model']['convention'] == 'Hypothetical'


@pytest.mark.parametrize('path,value', [
    ((), []), (('id',), 'agpu'), (('reviewed_at',), '2026-11-27T00:00:00Z'),
    (('reviewed_at',), '2026-11-26T10:00:00'), (('sources',), {}),
    (('sources', 0, 'id'), 'filing'), (('sources', 0, 'title'), ''),
    (('sources', 0, 'url'), 'https://example.org/source?api_key=private'),
    (('sources', 0, 'published'), '2026-11-27'), (('sources', 0, 'published'), '2026-02-30'),
    (('capital_bridge',), []), (('capital_bridge', 0, 'value'), True),
    (('capital_bridge', 0, 'value'), float('nan')), (('capital_bridge', 0, 'value'), ''),
    (('capital_bridge', 0, 'basis'), None), (('capital_bridge', 0, 'sources'), []),
    (('capital_bridge', 0, 'sources'), ['missing']), (('capital_bridge', 0, 'sources'), ['filing', 'filing']),
    (('decision', 'upgrade'), ''), (('decision',), []), (('gaps',), [None]),
    (('scenarios',), {}), (('scenarios', 0, 'name'), ''),
    (('scenarios', 0, 'inputs', 'revenue'), True), (('scenarios', 0, 'inputs', 'margin'), 101),
    (('scenarios', 0, 'inputs', 'multiple'), 0), (('scenarios', 0, 'inputs', 'debt'), -1),
    (('scenarios', 0, 'inputs', 'shares'), 0), (('scenarios', 0, 'inputs', 'cash'), '20'),
    (('scenarios', 0, 'inputs', 'claims'), float('inf')), (('scenarios', 0, 'sources'), ['unknown']),
    (('scenarios', 0, 'rationale'), False), (('model', 'convention'), float('-inf')),
])
def test_invalid_sheet_rejected_before_publication(tmp_path, path, value):
    with pytest.raises(ValueError):
        load(tmp_path, mutate(sheet(), path, value))


def test_source_chronology_applies_to_terminal_sources_used_by_sheet(tmp_path):
    companies = deepcopy(COMPANIES)
    companies[0]['sources'].append({'id': 'later', 'published': '2026-11-27'})
    record = sheet()
    record['capital_bridge'][0]['sources'] = ['later']
    with pytest.raises(ValueError, match='published after review'):
        load(tmp_path, record, companies=companies)


def test_empty_or_omitted_scenarios_permitted_for_unresolved_valuation(tmp_path):
    record = sheet()
    record.pop('scenarios')
    assert load(tmp_path, record)['sheets'][0] == record
    record['scenarios'] = []
    assert load(tmp_path, record)['sheets'][0]['scenarios'] == []


def test_scenario_duplicate_names_and_arithmetic_overflow_rejected(tmp_path):
    record = sheet()
    record['scenarios'].append(deepcopy(record['scenarios'][0]))
    with pytest.raises(ValueError, match='duplicate name'):
        load(tmp_path, record)
    record = sheet()
    record['scenarios'][0]['inputs'].update(revenue=1e308, multiple=1e308)
    with pytest.raises(ValueError, match='finite'):
        load(tmp_path, record)


@pytest.mark.parametrize('path,value', [
    ((), []), (('crwv',), []), (('crwv', 'as_of'), '2026-11-27'),
    (('crwv', 'retrieved_at'), '2026-11-26T13:00:00Z'),
    (('crwv', 'retrieved_at'), '2026-11-24T10:00:00Z'),
    (('crwv', 'source_url'), 'http://example.org/history'),
    (('crwv', 'source_url'), 'https://user:pass@example.org/history'),
    (('crwv', 'provider'), ''), (('crwv', 'close'), True), (('crwv', 'close'), 0),
    (('crwv', 'close'), float('nan')), (('crwv', 'day_volume'), False),
    (('crwv', 'day_volume'), -1), (('crwv', 'day_low'), 12),
    (('crwv', 'day_high'), 8), (('crwv', 'note'), None), (('crwv', 'metrics'), []),
    (('crwv', 'metrics', 'return5SessionPct'), True),
    (('crwv', 'metrics', 'averageVolume20'), -1),
    (('crwv', 'metrics', 'realizedVolatility20Pct'), float('inf')),
    (('crwv', 'metrics', 'closeLow20'), 11),
    (('crwv', 'metrics', 'lastDate'), '2026-11-24'),
    (('crwv', 'metrics', 'firstDate'), '2026-11-26'),
    (('crwv', 'metrics', 'suppliedSessions'), 20.5),
    (('crwv', 'metrics', 'complete'), 'true'),
    (('crwv', 'levels', 'review_low'), False),
    (('crwv', 'levels', 'recovery_level'), 0),
    (('crwv', 'levels', 'rationale'), ''),
])
def test_market_dates_numbers_and_evidence_fail_closed(tmp_path, path, value):
    with pytest.raises(ValueError):
        load(tmp_path, observations=mutate(market(), path, value))


def test_market_unknown_issuer_rejected_and_zero_volume_is_not_missing(tmp_path):
    observations = market()
    observations['other'] = deepcopy(observations['crwv'])
    with pytest.raises(ValueError, match='unknown company'):
        load(tmp_path, observations=observations)
    observations = market()
    observations['crwv']['day_volume'] = 0
    assert load(tmp_path, observations=observations)['market']['crwv']['day_volume'] == 0


def hurdle():
    return {'method': 'Inverse annuity', 'formula': 'Price times shares over annuity factor',
            'sources': ['sheet-source'], 'rows': [{'label': 'Synthetic hurdle',
            'required_annual_cash_m': 10, 'rate_pct': 20, 'shares_m': 10, 'price': 4,
            'years': 5, 'explanation': 'Illustrative net common cash; zero residual'}]}


def test_hurdle_without_forward_scenarios_preserved(tmp_path):
    record = sheet()
    record['scenarios'] = []
    record['hurdle'] = hurdle()
    assert load(tmp_path, record)['sheets'][0]['hurdle'] == hurdle()


@pytest.mark.parametrize('path,value', [
    (['method'], ''), (['formula'], None), (['sources'], ['unknown']),
    (['rows'], []), (['rows', 0, 'required_annual_cash_m'], float('inf')),
    (['rows', 0, 'price'], True), (['rows', 0, 'shares_m'], 0),
    (['rows', 0, 'rate_pct'], -1), (['rows', 0, 'years'], 5.5),
    (['rows', 0, 'explanation'], ''), (['rows', 0, 'sources'], ['unknown']),
])
def test_invalid_hurdles_rejected(tmp_path, path, value):
    record = sheet()
    record['hurdle'] = mutate(hurdle(), path, value)
    with pytest.raises(ValueError):
        load(tmp_path, record)


def test_enormous_integer_rejected_as_value_error(tmp_path):
    record = sheet()
    record['capital_bridge'][0]['value'] = 10 ** 400
    with pytest.raises(ValueError):
        load(tmp_path, record)
