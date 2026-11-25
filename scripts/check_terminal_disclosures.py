"""Discover public disclosures for review; never alter the reviewed research ledger.

Standard library only. A successful fetch is not a claim that a disclosure is true,
material, or fully reviewed. Empty/unparseable IR pages are coverage errors.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ISSUERS = {
    'CRWV': {'cik': 1769628, 'ir': 'https://investors.coreweave.com/news/default.aspx', 'path': '/news/news-details/'},
    'APLD': {'cik': 1144879, 'ir': 'https://ir.applieddigital.com/news-events/press-releases/rss', 'path': '/news-events/press-releases/detail/'},
    'AGPU': {'cik': 1446159, 'ir': 'https://investors.axecompute.com/rss/news-releases.xml?items=15', 'path': '/news-releases/news-release-details/'},
}
ALLOWED_HOSTS = {'data.sec.gov', 'www.sec.gov', *(urlsplit(v['ir']).hostname for v in ISSUERS.values())}
DEFAULT_CONTACT = 'https://github.com/joedatacap/aidatacenter2'
MAX_BYTES = 8_000_000
ACCESSION = re.compile(r'/Archives/edgar/data/\d+/(\d{18})/', re.I)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def canonical_url(url):
    """Only public allowlisted HTTPS origins; strip tracking and fragments."""
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname not in ALLOWED_HOSTS or p.username or p.password or p.port not in (None, 443):
        raise ValueError('URL outside allowed HTTPS source origins')
    path = p.path.rstrip('/') or '/'
    # Q4 uses /default.aspx and slash interchangeably for the same article.
    if path.endswith('/default.aspx') and '/news/news-details/' in path:
        path = path[:-len('/default.aspx')]
    return urlunsplit(('https', p.hostname, path, '', ''))


def accession_from_url(url):
    match = ACCESSION.search(url)
    if not match:
        return None
    value = match.group(1)
    return f'{value[:10]}-{value[10:12]}-{value[12:]}'


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        canonical_url(newurl)
        if urlsplit(newurl).hostname != urlsplit(req.full_url).hostname:
            raise ValueError('Cross-origin source redirect rejected')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    def __init__(self, contact=DEFAULT_CONTACT):
        if not contact or '\n' in contact or '\r' in contact:
            raise ValueError('A single-line public research contact is required')
        self.user_agent = f'NeocloudWatch Research {contact}'
        self.opener = build_opener(SameOriginRedirect())
        self.last_request = 0.0

    def __call__(self, url):
        canonical_url(url)
        time.sleep(max(0, 0.5 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        request = Request(url, headers={'User-Agent': self.user_agent, 'Accept': 'application/json, application/rss+xml, text/html'})
        with self.opener.open(request, timeout=25) as response:
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError('Source exceeds response-size limit')
            return data.decode('utf-8-sig')


def publication(value):
    if not value:
        return None
    value = value.strip()
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        try:
            return parsedate_to_datetime(value).date().isoformat()
        except (ValueError, TypeError, OverflowError):
            return None


def sec_items(payload, ticker, cik, since, today):
    data = json.loads(payload)
    if int(data['cik']) != cik:
        raise ValueError('SEC issuer CIK mismatch')
    recent = data['filings']['recent']
    keys = ['accessionNumber', 'form', 'filingDate', 'reportDate', 'primaryDocument']
    arrays = [recent[k] for k in keys]
    if len({len(a) for a in arrays}) != 1:
        raise ValueError('SEC recent filing columns have inconsistent lengths')
    result = []
    for accession, form, filed, report, document in zip(*arrays):
        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}', accession):
            raise ValueError('Invalid SEC accession')
        filed = date.fromisoformat(filed)
        if filed > today:
            raise ValueError('SEC filing date is in the future')
        if filed < since:
            continue
        if not re.fullmatch(r'[A-Za-z0-9_./-]+', document) or any(part in {'', '.', '..'} for part in document.split('/')):
            raise ValueError('Invalid SEC primary document name')
        url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace("-", "")}/{document}'
        result.append({'id': f'{ticker}:sec:{accession}', 'ticker': ticker, 'kind': 'sec_filing',
                       'title': f'{form} filed {filed.isoformat()}', 'url': canonical_url(url),
                       'published': filed.isoformat(), 'published_precision': 'date',
                       'report_date': report or None, 'accession': accession, 'form': form})
    return result


class IRLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.rss = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and 'rss' in attrs.get('type', ''):
            self.rss.append(attrs.get('href', ''))
        if tag == 'a':
            self.current = {'url': attrs.get('href', ''), 'text': []}

    def handle_data(self, data):
        if self.current:
            self.current['text'].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append((self.current['url'], ' '.join(' '.join(self.current['text']).split()), None))
            self.current = None


def ir_items(payload, ticker, source_url, path, since, today):
    links = []
    if payload.lstrip().startswith('<?xml') or '<rss' in payload[:1000] or '<feed' in payload[:1000]:
        root = ET.fromstring(payload)
        for item in root.iter():
            if item.tag.split('}')[-1] not in {'item', 'entry'}:
                continue
            values = {c.tag.split('}')[-1]: c for c in item}
            title = values.get('title')
            link = values.get('link')
            dated = next((values.get(k) for k in ['pubDate', 'published', 'updated'] if k in values), None)
            links.append(((link.get('href') or link.text or '') if link is not None else '',
                          ''.join(title.itertext()).strip() if title is not None else '',
                          publication(dated.text) if dated is not None else None))
    else:
        parser = IRLinks()
        parser.feed(payload)
        links = parser.links
    result = []
    for href, title, published in links:
        try:
            url = canonical_url(urljoin(source_url, href))
        except ValueError:
            continue
        if urlsplit(url).hostname != urlsplit(source_url).hostname or path not in urlsplit(url).path or not title:
            continue
        if published and date.fromisoformat(published) > today:
            raise ValueError('IR publication date is in the future')
        if published and date.fromisoformat(published) < since:
            continue
        result.append({'id': f'{ticker}:ir:{url}', 'ticker': ticker, 'kind': 'issuer_release',
                       'title': title, 'url': url, 'published': published,
                       'published_precision': 'date' if published else 'unknown', 'accession': None, 'form': None})
    # A zero-result parse may mean dynamic HTML or a changed publisher schema.
    # Never report this as a successful proof of no new disclosures.
    if not result:
        raise ValueError('No dated/relevant disclosure links parsed; source coverage is incomplete')
    return result


def reviewed_index(data_dir):
    urls, accessions = set(), set()
    for ticker in ISSUERS:
        path = Path(data_dir) / f'{ticker.lower()}.json'
        for source in json.loads(path.read_text())['sources']:
            try:
                url = canonical_url(source['url'])
            except ValueError:
                continue
            urls.add(url)
            accession = accession_from_url(url)
            if accession:
                accessions.add(accession)
    return urls, accessions


def build_queue(fetch, data_dir, since, previous=None, checked_at=None):
    checked_at = checked_at or utc_now()
    today = datetime.fromisoformat(checked_at.replace('Z', '+00:00')).date()
    if since > today:
        raise ValueError('Discovery start date cannot be in the future')
    known_urls, known_accessions = reviewed_index(data_dir)
    prior = {i['id']: i for i in (previous or {}).get('items', [])}
    items, sources = {}, []
    for ticker, config in ISSUERS.items():
        sec_url = f'https://data.sec.gov/submissions/CIK{config["cik"]:010d}.json'
        for kind, url in [('sec', sec_url), ('ir', config['ir'])]:
            source_id = f'{ticker}:{kind}'
            source = {'id': source_id, 'ticker': ticker, 'url': url, 'checked_at': checked_at}
            try:
                payload = fetch(url)
                discovered = (sec_items(payload, ticker, config['cik'], since, today) if kind == 'sec'
                              else ir_items(payload, ticker, url, config['path'], since, today))
                source.update(status='ok', item_count=len(discovered))
                for item in discovered:
                    old = prior.get(item['id'], {})
                    item.update(first_seen=old.get('first_seen', checked_at), last_seen=checked_at,
                                discovered_via=sorted(set(old.get('discovered_via', []) + [source_id])))
                    is_known = item['url'] in known_urls or item['accession'] in known_accessions
                    item['status'] = 'known' if is_known else ('unreviewed' if old else 'new')
                    if is_known:
                        item['ledger_match'] = 'document' if item['url'] in known_urls else 'accession'
                    review = old.get('review', {})
                    if review.get('disposition') in {'reviewed', 'dismissed'} and str(review.get('reason', '')).strip():
                        item['review'] = review
                        item['status'] = review['disposition']
                    existing = items.get(item['id'])
                    if existing and existing.get('published') and not item.get('published'):
                        item['published'] = existing['published']
                        item['published_precision'] = existing['published_precision']
                    items[item['id']] = item
            except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
                # Do not log a request header, credentials, or full response body.
                source.update(status='error', item_count=None, error=f'{type(error).__name__}: {str(error)[:250]}')
            sources.append(source)
    # Keep prior observations/dispositions even when rolling off a listing or during outages.
    for key, old in prior.items():
        if key not in items:
            old = dict(old)
            if old.get('status') == 'new':
                old['status'] = 'unreviewed'
            review = old.get('review', {})
            if review.get('disposition') in {'reviewed', 'dismissed'} and str(review.get('reason', '')).strip():
                old['status'] = review['disposition']
            items[key] = old
    errors = sum(s['status'] == 'error' for s in sources)
    summary = {state: sum(i['status'] == state for i in items.values()) for state in ['new', 'unreviewed', 'known', 'reviewed', 'dismissed']}
    return {'schema_version': 1, 'checked_at': checked_at, 'since': since.isoformat(),
            'status': 'failed' if errors == len(sources) else 'partial' if errors else 'complete',
            'policy': 'Discovery only. New/unreviewed means not yet assessed, not a trading signal. Known accession does not mean every exhibit was reviewed.',
            'summary': summary, 'sources': sources,
            'items': sorted(items.values(), key=lambda i: (i.get('published') or '', i['id']), reverse=True)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since', type=date.fromisoformat, default=datetime.now(timezone.utc).date() - timedelta(days=14))
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'neocloud/data/terminal')
    parser.add_argument('--previous', type=Path, help='Previous queue, including optional review dispositions')
    parser.add_argument('--output', type=Path, default=ROOT / 'work/terminal-disclosures.json')
    parser.add_argument('--contact', default=DEFAULT_CONTACT, help='Public identifying research contact, never a secret')
    args = parser.parse_args()
    previous = json.loads(args.previous.read_text()) if args.previous else None
    result = build_queue(Fetcher(args.contact), args.data_dir, args.since, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'status': result['status'], 'summary': result['summary'],
                      'source_errors': [s for s in result['sources'] if s['status'] == 'error']}, indent=2))
    return 0 if result['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
