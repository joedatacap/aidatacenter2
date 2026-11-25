"""Public disclosure discovery regression tests, with synthetic input only."""
from datetime import date
import json
from urllib.request import Request
import pytest
from scripts.check_terminal_disclosures import (
    ISSUERS, SameOriginRedirect, build_queue, canonical_url, ir_items, sec_items,
)

NOW = '2026-11-25T04:00:00+00:00'
SINCE = date(2026, 11, 10)
TODAY = date(2026, 11, 25)


def submissions(cik=1769628, filed='2026-11-24'):
    return json.dumps({'cik': cik, 'filings': {'recent': {
        'accessionNumber': ['0001769628-26-000999'], 'form': ['8-K'],
        'filingDate': [filed], 'reportDate': ['2026-11-24'], 'primaryDocument': ['report.htm'],
    }}})


def rss(url, when='Tue, 24 Nov 2026 09:00:00 -0500'):
    return f'<rss><channel><item><title>Synthetic disclosure</title><link>{url}</link><pubDate>{when}</pubDate></item></channel></rss>'


def ledger(tmp_path, sources=None):
    for ticker in ISSUERS:
        (tmp_path / f'{ticker.lower()}.json').write_text(json.dumps({'sources': sources or []}))
    return tmp_path


def test_sec_mismatched_identity_dates_and_columns_fail():
    with pytest.raises(ValueError, match='CIK mismatch'):
        sec_items(submissions(123), 'CRWV', 1769628, SINCE, TODAY)
    with pytest.raises(ValueError, match='future'):
        sec_items(submissions(filed='2026-11-26'), 'CRWV', 1769628, SINCE, TODAY)
    payload = json.loads(submissions())
    payload['filings']['recent']['form'] = []
    with pytest.raises(ValueError, match='inconsistent'):
        sec_items(json.dumps(payload), 'CRWV', 1769628, SINCE, TODAY)
    assert sec_items(submissions(filed='2026-11-01'), 'CRWV', 1769628, SINCE, TODAY) == []


@pytest.mark.parametrize('document', ['../secret', '/evil.htm', 'https://evil.test/x', 'a/../b'])
def test_sec_document_path_cannot_escape_archive(document):
    payload = json.loads(submissions())
    payload['filings']['recent']['primaryDocument'] = [document]
    with pytest.raises(ValueError, match='document'):
        sec_items(json.dumps(payload), 'CRWV', 1769628, SINCE, TODAY)


def test_sec_transform_document_subdirectories_are_supported():
    payload = json.loads(submissions())
    payload['filings']['recent']['primaryDocument'] = ['xslSCHEDULE_13D_X02/primary_doc.xml']
    assert sec_items(json.dumps(payload), 'CRWV', 1769628, SINCE, TODAY)[0]['url'].endswith('xslSCHEDULE_13D_X02/primary_doc.xml')


@pytest.mark.parametrize('url', ['http://data.sec.gov/x', 'https://evil.test/x', 'https://user:password@data.sec.gov/x', 'https://data.sec.gov:8443/x'])
def test_only_public_allowlisted_https_origins(url):
    with pytest.raises(ValueError):
        canonical_url(url)


def test_cross_origin_redirect_blocked_even_between_allowlisted_hosts():
    with pytest.raises(ValueError, match='Cross-origin'):
        SameOriginRedirect().redirect_request(Request('https://data.sec.gov/x'), None, 302, '', {}, 'https://www.sec.gov/x')


def test_html_ignores_external_navigation_and_preserves_unknown_date():
    payload = '<a href="https://evil.test/news/news-details/a">Bad</a><a href="/news/news-details/2026/test/default.aspx?utm_source=x">A <b>test</b></a>'
    rows = ir_items(payload, 'CRWV', ISSUERS['CRWV']['ir'], '/news/news-details/', SINCE, TODAY)
    assert len(rows) == 1
    assert rows[0]['title'] == 'A test'
    assert rows[0]['published'] is None
    assert rows[0]['published_precision'] == 'unknown'
    assert rows[0]['url'] == 'https://investors.coreweave.com/news/news-details/2026/test'


def test_empty_html_is_coverage_failure_not_no_changes():
    with pytest.raises(ValueError, match='coverage is incomplete'):
        ir_items('<html>Javascript required</html>', 'CRWV', ISSUERS['CRWV']['ir'], '/news/news-details/', SINCE, TODAY)


def test_rss_uses_publication_not_discovery_date_and_rejects_future():
    url = 'https://ir.applieddigital.com/news-events/press-releases/detail/999/test'
    rows = ir_items(rss(url), 'APLD', ISSUERS['APLD']['ir'], ISSUERS['APLD']['path'], SINCE, TODAY)
    assert rows[0]['published'] == '2026-11-24'
    with pytest.raises(ValueError, match='future'):
        ir_items(rss(url, '2026-11-26'), 'APLD', ISSUERS['APLD']['ir'], ISSUERS['APLD']['path'], SINCE, TODAY)


def test_queue_dedupes_preserves_review_and_reports_partial_sources(tmp_path):
    data = ledger(tmp_path, [{'url': 'https://www.sec.gov/Archives/edgar/data/1769628/000176962826000999/exhibit.htm'}])
    release = 'https://ir.applieddigital.com/news-events/press-releases/detail/999/test'
    def fetch(url):
        if 'CIK0001769628' in url:
            return submissions()
        if url == ISSUERS['APLD']['ir']:
            return rss(release).replace('</channel>', '<item><title>Duplicate</title><link>'+release+'?utm_source=x</link></item></channel>')
        raise OSError('Source temporarily unavailable')
    first = build_queue(fetch, data, SINCE, checked_at=NOW)
    assert first['status'] == 'partial'
    assert len(first['items']) == 2
    assert next(i for i in first['items'] if i['kind'] == 'issuer_release')['published'] == '2026-11-24'
    assert first['summary']['known'] == 1
    assert first['summary']['new'] == 1
    sec = next(i for i in first['items'] if i['kind'] == 'sec_filing')
    assert sec['ledger_match'] == 'accession'
    assert sum(s['status'] == 'error' for s in first['sources']) == 4
    second = build_queue(fetch, data, SINCE, first, NOW)
    assert second['summary']['unreviewed'] == 1
    release_item = next(i for i in second['items'] if i['kind'] == 'issuer_release')
    release_item['review'] = {'disposition': 'dismissed', 'reason': 'Synthetic duplicate assessed', 'reviewed_at': NOW}
    third = build_queue(lambda u: (_ for _ in ()).throw(OSError('Outage')), data, SINCE, second, NOW)
    assert third['status'] == 'failed'
    assert len(third['items']) == 2
    assert third['summary']['dismissed'] == 1
    assert next(i for i in third['items'] if i['kind'] == 'issuer_release')['review']['reason'] == 'Synthetic duplicate assessed'
