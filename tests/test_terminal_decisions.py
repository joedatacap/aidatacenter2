"""Decision evidence and intake publication boundaries; synthetic records only."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest
from scripts.build_terminal import load_decisions

NOW = datetime(2026, 11, 25, 12, tzinfo=timezone.utc)
COMPANIES = [{"id": "crwv", "sources": [{"id": "filing", "published": "2026-11-20"}]}]


def brief():
    return {
        "id": "crwv", "reviewed_at": "2026-11-25T10:00:00Z",
        "stance": "Synthetic assessment", "question": "Synthetic question?",
        "takeaway": "Synthetic interpretation", "valuation_note": "Unknown valuation",
        "cases": [{"name": n, "thesis": "Hypothesis", "requires": "Evidence",
                   "invalidated_by": "Counterevidence", "sources": ["filing"]}
                  for n in ("Bull", "Base", "Bear")],
        "checkpoints": [{"date": "2026-12-31", "label": "Future target", "watch": "Evidence",
                         "positive": "Confirmed", "negative": "Contradicted", "sources": ["filing"]}],
        "metrics": [{"label": "Historical metric", "value": "Unknown", "basis": "Unverified",
                     "sources": ["filing"]}],
        "gaps": ["Unknown economics"], "sources": [],
    }


def queue():
    return {"schema_version": 1, "checked_at": "2026-11-25T11:00:00Z", "since": "2026-11-10",
            "status": "complete", "sources": [{"id": "CRWV:sec", "ticker": "CRWV",
                "url": "https://data.sec.gov/example", "checked_at": "2026-11-25T11:00:00Z",
                "status": "ok", "item_count": 1}],
            "items": [{"id": "example", "ticker": "CRWV", "title": "Synthetic filing",
                "url": "https://www.sec.gov/example", "published": "2026-11-24",
                "published_precision": "date", "first_seen": "2026-11-24T12:00:00Z",
                "last_seen": "2026-11-25T11:00:00Z", "status": "new"}]}


def load(tmp_path, record=None, intake=None, companies=None):
    directory = tmp_path / "neocloud/data/decisions"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "crwv.json").write_text(json.dumps(brief() if record is None else record))
    if intake is not None:
        (directory / "disclosures.json").write_text(json.dumps(intake))
    return load_decisions(tmp_path, companies or COMPANIES, now=NOW)


def test_valid_future_target_and_unknown_intake_date_are_preserved(tmp_path):
    q = queue()
    q['items'][0].update(published=None, published_precision='unknown')
    result = load(tmp_path, intake=q)
    assert result['briefs'][0]['checkpoints'][0]['date'] == '2026-12-31'
    assert result['queue']['items'][0]['published'] is None
    assert result['queue']['items'][0]['status'] == 'new'


@pytest.mark.parametrize('path,value', [
    ((), []), (('sources',), {}), (('sources',), [None]),
    (('cases', 0), 'not an object'), (('metrics', 0, 'value'), 100),
    (('metrics', 0, 'sources'), [{}]), (('metrics', 0, 'sources'), ['missing']),
    (('metrics', 0, 'sources'), ['filing', 'filing']), (('gaps',), [False]),
    (('checkpoints', 0, 'date'), '2026-02-30'),
    (('reviewed_at',), '2026-11-26T01:00:00Z'),
])
def test_malformed_decision_rejected_as_value_error(tmp_path, path, value):
    record = brief()
    if not path:
        record = value
    else:
        parent = record
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = value
    with pytest.raises(ValueError):
        load(tmp_path, record=record)


def test_sources_from_company_cannot_postdate_decision_review(tmp_path):
    companies = deepcopy(COMPANIES)
    companies[0]['sources'][0]['published'] = '2026-11-26'
    with pytest.raises(ValueError, match='published after review'):
        load(tmp_path, companies=companies)


def test_source_id_shadowing_and_non_three_case_schema_rejected(tmp_path):
    record = brief()
    record['sources'] = [{'id': 'filing', 'title': 'Replacement', 'excerpt': 'Different evidence',
                          'url': 'https://example.org/source', 'published': '2026-11-24'}]
    with pytest.raises(ValueError, match='duplicate id'):
        load(tmp_path, record)
    record = brief()
    record['cases'][2]['name'] = 'Bull'
    with pytest.raises(ValueError, match='exactly Bull'):
        load(tmp_path, record)


@pytest.mark.parametrize('path,value', [
    ((), []), (('schema_version',), True), (('checked_at',), '2026-11-26T00:00:00Z'),
    (('since',), '2026-11-26'), (('sources', 0, 'item_count'), True),
    (('sources', 0, 'checked_at'), '2026-11-25T11:01:00Z'),
    (('status',), 'failed'), (('items', 0), False),
    (('items', 0, 'ticker'), {}), (('items', 0, 'published'), '2026-11-26'),
    (('items', 0, 'published'), '2026-02-30'),
    (('items', 0, 'first_seen'), '2026-11-25T11:01:00Z'),
    (('items', 0, 'last_seen'), '2026-11-26T01:00:00Z'),
    (('items', 0, 'status'), 'reviewed'), (('items', 0, 'published_precision'), 'unknown'),
])
def test_intake_cannot_publish_future_or_misrepresented_evidence(tmp_path, path, value):
    q = queue()
    if not path:
        q = value
    else:
        parent = q
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = value
    with pytest.raises(ValueError):
        load(tmp_path, intake=q)


def test_partial_source_failure_and_reasoned_review_survive(tmp_path):
    q = queue()
    failed = deepcopy(q['sources'][0])
    failed.update(id='CRWV:ir', status='error', item_count=None, error='Unavailable')
    q['sources'].append(failed)
    q['status'] = 'partial'
    q['items'][0].update(status='dismissed', review={'disposition': 'dismissed', 'reason': 'Duplicate'})
    result = load(tmp_path, intake=q)
    assert result['queue']['status'] == 'partial'
    assert result['queue']['items'][0]['review']['reason'] == 'Duplicate'


def test_no_decision_directory_remains_compatible(tmp_path):
    assert load_decisions(tmp_path, COMPANIES, now=NOW) == {'briefs': [], 'queue': None}
