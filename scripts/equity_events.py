"""Dedupe public disclosure discovery into review questions, never trading facts.

Reuses terminal intake's HTTPS allowlist, rate limit and issuer coverage. Rule
matches classify titles/forms only; no title implies a closed financing or beat.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_terminal_disclosures import canonical_url, accession_from_url
from scripts import check_terminal_disclosures as intake
from urllib.parse import urlsplit
from scripts.equity_history import ROOT, canonical, digest, utc, write_new

# CIKs and issuer index URLs reuse the reviewed source ledger / quality_reviews.
EXTRA_ISSUERS = {
    'NBIS': {'cik':1513845,'ir':'https://nebius.com/newsroom','path':'/newsroom/'},
    'IREN': {'cik':1878848,'ir':'https://iren.com/investors/news','path':'/'},
    'HUT': {'cik':1964789,'ir':'https://www.hut8.com/news-insights/press-releases','path':'/'},
    'WULF': {'cik':1083301,'ir':'https://investors.terawulf.com/news-events','path':'/'},
    'WYFI': {'cik':2042022,'ir':'https://www.whitefiber.com/investors-news','path':'/'},
    'SHAZ': {'cik':2068385,'ir':'https://sharonai.com/media-and-news/','path':'/press-releases/'},
}
PRESENTATIONS = {
    'NBIS':'https://nebius.com/investor-events', 'IREN':'https://iren.com/investors/reports',
    'HUT':'https://www.hut8.com/investors/events-presentations',
    'WULF':'https://investors.terawulf.com/news-events/ir-calendar',
    'WYFI':'https://www.whitefiber.com/events', 'SHAZ':'https://sharonai.com/events/',
}


def scan_equity(fetch=None, since=None, checked_at=None):
    """Nine issuer intake using the existing secure fetcher/parser contract."""
    now = utc(checked_at)
    since = since or now.date() - timedelta(days=14)
    original = intake.ISSUERS
    original_index = intake.reviewed_index
    known_index = original_index(ROOT/'neocloud/data/terminal')
    original_hosts = set(intake.ALLOWED_HOSTS)
    try:
        intake.ISSUERS = {**original, **EXTRA_ISSUERS}
        intake.reviewed_index = lambda data_dir: known_index
        intake.ALLOWED_HOSTS.update(urlsplit(c['ir']).hostname for c in EXTRA_ISSUERS.values())
        intake.ALLOWED_HOSTS.update(urlsplit(u).hostname for u in PRESENTATIONS.values())
        fetch = fetch or intake.Fetcher()
        queue = intake.build_queue(fetch, ROOT/'neocloud/data/terminal', since, checked_at=now.isoformat())
        for ticker, url in PRESENTATIONS.items():
            source={'id':ticker+':presentations','ticker':ticker,'url':url,'checked_at':now.isoformat()}
            try:
                rows=intake.ir_items(fetch(url),ticker,url,'/',since,now.date())
                rows=[r for r in rows if re.search(r'present|earning|result|quarter|webcast|conference|\.pdf',r['title']+' '+r['url'],re.I) and canonical_url(url)!=r['url']]
                if not rows:
                    raise ValueError('No relevant same-origin presentation/event documents; dynamic or cross-origin assets are not verified')
                for row in rows:
                    row.update(status='new',first_seen=now.isoformat(),last_seen=now.isoformat())
                    queue['items'].append(row)
                source.update(status='ok',item_count=len(rows))
            except (OSError, ValueError, KeyError, TypeError, intake.ET.ParseError) as exc:
                source.update(status='error',item_count=None,error=str(exc)[:200])
            queue['sources'].append(source)
        listings={canonical_url(c['ir']) for c in intake.ISSUERS.values()} | {canonical_url(u) for u in PRESENTATIONS.values()}
        queue['items']=[r for r in queue['items'] if r['url'] not in listings]
        queue['status']='partial' if any(s['status']!='ok' for s in queue['sources']) else 'complete'
        return queue
    finally:
        intake.ISSUERS=original
        intake.reviewed_index=original_index
        intake.ALLOWED_HOSTS.clear();intake.ALLOWED_HOSTS.update(original_hosts)


RULES = [
    ('financing', r'financ|credit|loan|debt|convertible|offering|placement|liquidity',
     'Reconcile commitment, actual proceeds, cash restrictions, dilution and senior claims before changing the funding thesis.'),
    ('delivery', r'energiz|commission|deliver|acceptance|construction|capacity|power|megawatt|\bmw\b',
     'Verify energization versus billable acceptance, dated milestones and ownership scope; compare with the original promise.'),
    ('customer', r'customer|contract|backlog|lease|partner',
     'Check counterparty concentration, enforceable term, cancellation clauses and whether announced value is recognized revenue.'),
    ('earnings', r'earnings|results|guidance|quarter|10-q|10-k|20-f',
     'Reconcile reported period, cash generation, financing and guidance with the current report; do not infer a beat from a title.'),
    ('governance', r'proxy|vote|meeting|director|incentive|def 14a',
     'Check the proposed versus approved change, effective date, share issuance and common-shareholder rights.'),
]


def event_url(url):
    hosts={urlsplit(c['ir']).hostname for c in EXTRA_ISSUERS.values()}
    parsed=urlsplit(url)
    if parsed.hostname in hosts:
        if parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443):
            raise ValueError('URL outside allowed HTTPS source origins')
        return parsed._replace(query='',fragment='').geturl().rstrip('/')
    return canonical_url(url)


def event_key(item):
    url = event_url(item['url'])
    accession = item.get('accession') or accession_from_url(url)
    if accession:
        normalized = re.sub(r'[^0-9]', '', accession)
        if len(normalized) != 18:
            raise ValueError('Invalid filing accession')
        return 'sec:' + normalized
    return 'url:' + digest(url)


def build_events(queue, reports, previous=None):
    checked = utc(queue['checked_at']).isoformat()
    utc(checked)
    report_map = {}
    report_sets = {}
    for report in reports:
        ticker = report['id'].upper()
        report_map.setdefault(ticker, report)
        report_sets.setdefault(ticker, []).append(report)
    events = {row['id']: deepcopy(row) for row in (previous or {}).get('events', [])}
    errors = []
    observed = set()
    for item in queue.get('items', []):
        try:
            key = event_key(item)
            ticker = item['ticker'].upper()
            if ticker not in report_map:
                raise ValueError('No covered report for event issuer')
            if item.get('published') and date.fromisoformat(item['published'][:10]) > utc(checked).date():
                raise ValueError('Future publication date')
            title = str(item.get('title') or item.get('form') or 'Disclosure')
            url = event_url(item['url'])
            document = {'url': url, 'title': title, 'form': item.get('form'), 'published': item.get('published')}
            row = events.setdefault(key, {'id': key, 'ticker': ticker, 'first_seen': checked, 'documents': [], 'revisions': []})
            if row['ticker'] != ticker:
                raise ValueError('Event accession belongs to conflicting issuer')
            if document not in row['documents']:
                row['documents'].append(document)
            row['last_seen'] = checked
            observed.add(key)
            text = ' '.join(d['title'] + ' ' + (d['form'] or '') for d in row['documents'])
            matches = [(category, question) for category, pattern, question in RULES if re.search(pattern, text, re.I)]
            questions = [q for _, q in matches] or ['Open the original document and determine whether it changes the reviewed thesis, objective, invalidation or timing.']
            report = report_map[ticker]
            revision = {'report_hash': digest(report), 'categories': [c for c, _ in matches] or ['unclassified'],
                        'review_questions': questions, 'open_report_gaps': [deepcopy(gap) for linked in report_sets[ticker] for gap in linked.get('gaps', [])],
                        'linked_report_hashes': [digest(linked) for linked in report_sets[ticker]],
                        'documents': deepcopy(row['documents'])}
            revision_id = digest(revision)
            if not any(r['revision_id'] == revision_id for r in row['revisions']):
                row['revisions'].append({'revision_id': revision_id, 'observed_at': checked, **revision})
            row.update(categories=revision['categories'], review_questions=questions,
                       open_report_gaps=revision['open_report_gaps'], report_hash=revision['report_hash'],
                       status='known_document' if item.get('status') == 'known' else 'needs_review',
                       impact='unassessed', classification_basis='Title/form keyword triage only; no fact extraction or verified trading impact.')
            review = item.get('review') or row.get('review')
            if isinstance(review, dict) and review.get('disposition') in {'reviewed', 'dismissed'} and isinstance(review.get('reason'), str) and review['reason'].strip():
                row['review'] = deepcopy(review)
                row['status'] = review['disposition']
        except (ValueError, KeyError, TypeError) as exc:
            errors.append({'item_id': str(item.get('id', 'unknown')), 'error': str(exc)[:200]})
    source_errors = [deepcopy(s) for s in queue.get('sources', []) if s.get('status') != 'ok']
    # Missing source inventory or a failed upstream status cannot be reported as clear.
    complete = queue.get('status') == 'complete' and bool(queue.get('sources')) and not source_errors and not errors
    for row in events.values():
        row['seen_this_run'] = row['id'] in observed
    return {'schema_version': 1, 'checked_at': checked, 'status': 'complete' if complete else 'partial',
            'coverage': {'monitored_tickers': sorted({s.get('ticker') or s.get('id','').split(':')[0] for s in queue.get('sources', [])}),
                         'report_tickers_without_intake': sorted(set(report_map) - {s.get('ticker') or s.get('id','').split(':')[0] for s in queue.get('sources', [])}),
                         'upstream_status': queue.get('status', 'unknown'), 'sources': deepcopy(queue.get('sources', [])),
                         'errors': errors, 'source_errors': source_errors},
            'policy': 'Discovery and review routing only. No automatic fact promotion, recommendation change, order or external notification. Known document does not mean every exhibit was reviewed.',
            'summary': {'observed_events': len(observed), 'retained_events': len(events),
                        'needs_review': sum(r['status'] == 'needs_review' for r in events.values()),
                        'no_changes_confirmed': False},
            'events': sorted(events.values(), key=lambda r: (r['first_seen'], r['id']), reverse=True)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, help='Existing intake fixture/snapshot; omit for live nine-issuer discovery')
    parser.add_argument('--reports-dir', type=Path, default=ROOT / 'neocloud/data/justin')
    parser.add_argument('--investment-dir', type=Path, default=ROOT / 'neocloud/data/equity')
    parser.add_argument('--history-dir', type=Path, default=ROOT / 'neocloud/data/equity-history')
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/equity-events.json')
    args = parser.parse_args()
    prior_path = args.previous
    if prior_path is None:
        prior_path = next(iter(sorted((args.history_dir / 'event-runs').glob('*.json'), reverse=True)), None)
    previous = json.loads(prior_path.read_text()) if prior_path else None
    reports = [json.loads(p.read_text()) for p in sorted(args.reports_dir.glob('*.json')) if p.name != 'cohort.json']
    for path in sorted(args.investment_dir.glob('*.json')):
        package = json.loads(path.read_text())
        reports.append({'id': package['ticker'].lower(), **package['report'], 'gaps': package.get('gaps', package['report'].get('missing', [])), 'publication_status': 'preview'})
    queue = json.loads(args.queue.read_text()) if args.queue else scan_equity()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_name('intake.json').write_text(json.dumps(queue, indent=2) + '\n')
    # Covered issuer without a finished report still receives disclosure triage.
    covered={r['id'].upper() for r in reports}
    for ticker in set(EXTRA_ISSUERS)|set(intake.ISSUERS):
        if ticker not in covered:
            reports.append({'id':ticker.lower(),'rating':'Unreviewed','gaps':['Reviewed company report unavailable']})
    result = build_events(queue, reports, previous)
    result['coverage']['content_gaps']=['Transcripts are not licensed or ingested.', 'Presentation links are discovered, not slide text or webcast transcripts.', 'SEC primary filings are discovered; all attached exhibits are not independently fetched.', 'Dynamic or cross-origin issuer assets remain source errors; no false all-clear.']
    stamp = utc(result['checked_at']).strftime('%Y%m%dT%H%M%S%fZ')
    write_new(args.history_dir / 'event-runs' / (stamp + '-' + digest(result)[:12] + '.json'), result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], **result['summary']}))


if __name__ == '__main__':
    main()
