"""Immutable research versions and prospective, explicitly sourced accountability.

No broker execution or price downloader. Supply a reviewed/licensed observation
export to score; existing dated research quotes cannot create a backtested entry.
"""
from __future__ import annotations
import argparse
import calendar
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ''}:
    sys.path.insert(0, str(ROOT))

HORIZONS = {'1w': (0, 7), '1m': (1, 0), '3m': (3, 0), '6m': (6, 0), '12m': (12, 0)}
POLICY = ('Prospective underlying-stock price returns, not executed trades or rating win rates. '
          'Entry is the first observed session strictly after the version recording date; '
          'Calendar horizons start at that entry and roll to the next regular NYSE session. Missing expected sessions never shift entry/exit later. Emergency closures are not inferred; withhold scoring until a reviewed calendar correction. '
          'Benchmarks use the identical entry/exit sessions. Cohort is frozen at publication, equal-weight '
          'buy-and-hold excluding the subject, and requires every member (no survivor substitution). '
          'Only USD split-adjusted closes are comparable; dividends, costs, slippage and FX are excluded. '
          'Sell/Hold calls are not silently converted into short trades. Missing prices stay pending.')


def utc(value=None):
    result = datetime.now(timezone.utc) if value is None else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone required')
    return result.astimezone(timezone.utc)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def write_new(path, value):
    """Never replace a recorded version; a collision must have identical bytes."""
    payload = canonical(value) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8') as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_text(encoding='utf-8') != payload:
            raise ValueError(f'Immutable record collision: {path.name}')


def read_versions(history_dir):
    versions = []
    for path in sorted((Path(history_dir) / 'versions').glob('*/*.json')):
        row = json.loads(path.read_text())
        if row.get('schema_version') != 1 or row.get('version_id') != digest(row['content']):
            raise ValueError('History digest mismatch')
        if row['content']['report']['id'] != row.get('company') or path.stem != row['version_id']:
            raise ValueError('History identity mismatch')
        utc(row['recorded_at'])
        versions.append(row)
    return sorted(versions, key=lambda r: (r['recorded_at'], r['company'], r['version_id']))


def snapshot_reports(reports_dir, history_dir, recorded_at=None):
    recorded = utc(recorded_at).isoformat()
    directory = Path(reports_dir)
    cohort = json.loads((directory / 'cohort.json').read_text())
    existing = {(v['company'], v['version_id']): v for v in read_versions(history_dir)}
    result = []
    for path in sorted(directory.glob('*.json')):
        if path.name == 'cohort.json':
            continue
        report = json.loads(path.read_text())
        company = report.get('id')
        if company != path.stem or not company.isalnum() or not isinstance(report.get('rating'), str):
            raise ValueError('Invalid report identity/rating')
        # Freeze membership, not changing daily cohort prices: daily prices must
        # never manufacture a revised call when the report itself is unchanged.
        members = sorted({r['id'].upper() for r in cohort['rows'] if r['id'] != company})
        content = {'report': report, 'cohort_members': members}
        version_id = digest(content)
        key = company, version_id
        if key in existing:
            result.append(existing[key])
            continue
        row = {'schema_version': 1, 'company': company, 'version_id': version_id,
               'recorded_at': recorded, 'recording_basis': 'First observed in this immutable archive; not an asserted original publication timestamp.',
               'content': content}
        write_new(Path(history_dir) / 'versions' / company / (version_id + '.json'), row)
        result.append(row)
    return result


def snapshot_investment_reports(equity_dir, history_dir, cohort_members, recorded_at=None):
    recorded = utc(recorded_at).isoformat()
    existing = {(v['company'], v['version_id']): v for v in read_versions(history_dir)}
    result = []
    for path in sorted(Path(equity_dir).glob('*.json')):
        package = json.loads(path.read_text())
        company = package['ticker'].lower()
        if company != path.stem or not company.isalnum():
            raise ValueError('Investment report identity mismatch')
        report = {'id': company, **package['report']}
        if not isinstance(report.get('rating'), str):
            raise ValueError('Investment report rating required')
        content = {'report': report, 'research_package': package,
                   'cohort_members': sorted({m.upper() for m in cohort_members if m.lower() != company})}
        # An earlier standalone ledger directory remains a valid history input.
        if (path.parent.parent / 'underwriting' / path.name).is_file() and company in {'nbis', 'crwv'}:
            from neocloud.equity_edition import investment_revision
            underwriting, current = investment_revision(package, path.parent.parent)
            content['report'] = {'id': company, **current}
            content['underwriting'] = underwriting
        version_id = digest(content)
        row = existing.get((company, version_id))
        if row is None:
            row = {'schema_version': 1, 'company': company, 'version_id': version_id,
                   'recorded_at': recorded, 'publication_status': 'preview',
                   'recording_basis': 'Authored research preview; as_of is not evidence of public release.', 'content': content}
            write_new(Path(history_dir) / 'versions' / company / (version_id + '.json'), row)
        result.append(row)
    return result


def register_release(history_dir, version_id, published_at, source_url, recorded_at=None):
    recorded, published = utc(recorded_at), utc(published_at)
    if published > recorded:
        raise ValueError('Release cannot be in future')
    if version_id not in {r['version_id'] for r in read_versions(history_dir)}:
        raise ValueError('Release version missing')
    url = urlsplit(source_url)
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('Public HTTPS release evidence required')
    existing = list((Path(history_dir) / 'release-notices').glob(version_id + '.json'))
    if existing:
        prior = json.loads(existing[0].read_text())
        if prior['published_at'] != published.isoformat() or prior['source_url'] != source_url:
            raise ValueError('Cannot overwrite original release notice')
        return prior
    row = {'version_id': version_id, 'published_at': published.isoformat(),
           'source_url': source_url, 'recorded_at': recorded.isoformat()}
    write_new(Path(history_dir) / 'release-notices' / (version_id + '.json'), row)
    return row


def validate_observations(observations, as_of):
    result = {}
    for ticker, rows in observations.items():
        if not isinstance(ticker, str) or not ticker.isalnum() or not isinstance(rows, list):
            raise ValueError('Invalid observation series')
        seen = {}
        for row in rows:
            day = date.fromisoformat(row['date'])
            retrieved = utc(row['retrieved_at'])
            price = row['close']
            url = urlsplit(row['source_url'])
            if type(price) not in (int, float) or not math.isfinite(price) or price <= 0:
                raise ValueError('Invalid close')
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError('Public HTTPS price source required')
            if day > retrieved.date() or retrieved > as_of or day > as_of.date():
                raise ValueError('Observation chronology invalid')
            if row.get('basis') not in {'raw_close', 'split_adjusted_close'} or row.get('currency') != 'USD':
                raise ValueError('Explicit price basis and USD currency required')
            if day in seen and canonical(seen[day]) != canonical(row):
                raise ValueError('Conflicting same-session observations; resolve explicitly')
            seen[day] = deepcopy(row)
        result[ticker.upper()] = dict(sorted(seen.items()))
    return result


def target_date(entry, months, days):
    month = entry.month - 1 + months
    year = entry.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(entry.day, calendar.monthrange(year, month)[1])) + timedelta(days=days)


def expected_session(day):
    """Regular NYSE calendar, not a complete record of emergency closures."""
    def nth(year, month, weekday, count):
        first = date(year, month, 1)
        return first + timedelta(days=(weekday-first.weekday()) % 7 + (count-1)*7)
    def observed(d):
        return d - timedelta(days=1) if d.weekday() == 5 else d + timedelta(days=1) if d.weekday() == 6 else d
    def holidays(year):
        # Gregorian Easter algorithm; NYSE closes on Good Friday.
        a=year%19; b=year//100; c=year%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
        h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
        easter=date(year,(h+l-7*m+114)//31,(h+l-7*m+114)%31+1)
        last_may=date(year,5,31)
        ny=date(year,1,1)
        return {ny+timedelta(days=1) if ny.weekday()==6 else ny, nth(year,1,0,3), nth(year,2,0,3),
                easter-timedelta(days=2), last_may-timedelta(days=last_may.weekday()),
                observed(date(year,6,19)), observed(date(year,7,4)), nth(year,9,0,1),
                nth(year,11,3,4), observed(date(year,12,25))}
    for offset in range(8):
        candidate = day + timedelta(days=offset)
        if candidate.weekday() < 5 and candidate not in holidays(candidate.year):
            return candidate
    raise ValueError('No expected session within a week')


def pair_return(series, entry, exit):
    if entry not in series or exit not in series:
        return {'status': 'pending', 'reason': 'Missing matching entry/exit sessions'}
    rows = [series[entry], series[exit]]
    if any(r['basis'] != 'split_adjusted_close' for r in rows):
        return {'status': 'pending', 'reason': 'Split-adjusted price basis not verified'}
    return {'status': 'scored', 'return_pct': round((rows[1]['close'] / rows[0]['close'] - 1) * 100, 6),
            'entry': deepcopy(rows[0]), 'exit': deepcopy(rows[1])}


def build_scorecard(history_dir, observations, as_of=None):
    checked = utc(as_of)
    series = validate_observations(observations, checked)
    versions = []
    edition_paths = sorted((Path(history_dir) / 'editions').glob('*.json'))
    edition = json.loads(edition_paths[-1].read_text()) if edition_paths else None
    releases = {p.stem: json.loads(p.read_text()) for p in (Path(history_dir) / 'release-notices').glob('*.json')}
    for version in read_versions(history_dir):
        recorded = utc(version['recorded_at'])
        if recorded > checked:
            raise ValueError('Version recorded after scoring time')
        release = releases.get(version['version_id'])
        if release:
            recorded = max(recorded, utc(release['published_at']), utc(release['recorded_at']))
            if recorded > checked:
                release = None
        ticker = version['company'].upper()
        prices = series.get(ticker, {})
        # Finite entry window prevents a missing year from silently becoming entry.
        expected_entry = expected_session(recorded.date() + timedelta(days=1))
        entry = expected_entry if release and expected_entry <= checked.date() and expected_entry in prices else None
        row = {k: deepcopy(version[k]) for k in ('company', 'version_id', 'recorded_at')}
        row['current_edition'] = version['version_id'] in edition['current_version_ids'] if edition else True
        row.update(publication_status='released' if release else 'publication_pending', release=release, rating=version['content']['report']['rating'], entry_date=entry.isoformat() if entry else None, horizons={})
        for label, (months, days) in HORIZONS.items():
            result = {'status': 'pending', 'reason': 'No verified next-session entry observation' if release else 'Public release not recorded; authored dates are not publication', 'benchmarks': {name: {'status': 'pending', 'reason': 'Stock horizon not scored'} for name in ('QQQ', 'NVDA', 'cohort')}}
            row['horizons'][label] = result
            if not entry:
                continue
            due = target_date(entry, months, days)
            result['due_date'] = due.isoformat()
            if checked.date() < due:
                result['reason'] = 'Horizon not elapsed'
                continue
            expected_exit = expected_session(due)
            exit = expected_exit if expected_exit <= checked.date() and expected_exit in prices else None
            if not exit:
                result['reason'] = 'Missing horizon-session observation'
                continue
            stock = pair_return(prices, entry, exit)
            result.update(stock)
            if stock['status'] != 'scored':
                continue
            result.pop('reason', None)
            result['stock_return_pct'] = result.pop('return_pct')
            for benchmark in ('QQQ', 'NVDA'):
                metric = pair_return(series.get(benchmark, {}), entry, exit)
                if metric['status'] == 'scored':
                    metric['excess_return_pp'] = round(result['stock_return_pct'] - metric['return_pct'], 6)
                result['benchmarks'][benchmark] = metric
            members = version['content']['cohort_members']
            peer_returns = {member: pair_return(series.get(member, {}), entry, exit) for member in members}
            missing = [member for member, metric in peer_returns.items() if metric['status'] != 'scored']
            cohort = {'status': 'pending', 'members': members, 'missing_members': missing, 'reason': 'All frozen peers required'}
            if members and not missing:
                value = sum(metric['return_pct'] for metric in peer_returns.values()) / len(members)
                cohort = {'status': 'scored', 'members': members, 'return_pct': round(value, 6),
                          'excess_return_pp': round(result['stock_return_pct'] - value, 6), 'components': peer_returns}
            result['benchmarks']['cohort'] = cohort
        versions.append(row)
    freshness = {ticker: {'last_session': max(rows).isoformat() if rows else None,
                         'calendar_days_old': (checked.date() - max(rows)).days if rows else None,
                         'status': 'missing' if not rows else 'stale' if (checked.date() - max(rows)).days > 4 else 'dated',
                         'basis': sorted({r['basis'] for r in rows.values()})} for ticker, rows in series.items()}
    for ticker in {'QQQ', 'NVDA'} | {v['company'].upper() for v in versions}:
        freshness.setdefault(ticker, {'status': 'missing', 'last_session': None, 'calendar_days_old': None, 'basis': []})
    return {'schema_version': 1, 'checked_at': checked.isoformat(), 'policy': POLICY, 'edition': edition, 'versions': versions, 'freshness': freshness}


def seed_observations(root=ROOT):
    """Reuse current dated quotes, explicitly unadjusted and not scoring-ready."""
    cohort = json.loads((root / 'neocloud/data/justin/cohort.json').read_text())
    markets = json.loads((root / 'neocloud/data/decisions/market-context.json').read_text())
    out = {}
    for row in cohort['rows']:
        market = markets.get(row['id'])
        if market:
            out[row['id'].upper()] = [{'date': market['as_of'], 'close': market['close'],
                'source_url': market['source_url'], 'retrieved_at': market['retrieved_at'],
                'basis': 'raw_close', 'currency': 'USD'}]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history-dir', type=Path, default=ROOT / 'neocloud/data/equity-history')
    parser.add_argument('--reports-dir', type=Path, default=ROOT / 'neocloud/data/justin')
    parser.add_argument('--investment-dir', type=Path, default=ROOT / 'neocloud/data/equity')
    parser.add_argument('--release-manifest', type=Path, help='Explicit release notices; never inferred from research as_of')
    parser.add_argument('--observations', type=Path, help='Reviewed/licensed dated daily observation export; no credentials')
    parser.add_argument('--output', type=Path, default=ROOT / 'work/equity-scorecard.json')
    args = parser.parse_args()
    now = utc().isoformat()
    originals = snapshot_reports(args.reports_dir, args.history_dir, now)
    cohort = json.loads((args.reports_dir / 'cohort.json').read_text())
    investments = snapshot_investment_reports(args.investment_dir, args.history_dir, [r['id'] for r in cohort['rows']], now)
    current_ids = [v['version_id'] for v in originals + investments]
    edition = {'recorded_at': now, 'current_version_ids': current_ids,
               'historical_preview_ids': [v['version_id'] for v in read_versions(args.history_dir) if v['version_id'] not in current_ids],
               'policy': 'Current authored edition; investment packages remain internal previews until explicit public release.'}
    write_new(args.history_dir / 'editions' / (utc(now).strftime('%Y%m%dT%H%M%S%fZ') + '.json'), edition)
    if args.release_manifest:
        for notice in json.loads(args.release_manifest.read_text()):
            register_release(args.history_dir, notice['version_id'], notice['published_at'], notice['source_url'], now)
    observations = json.loads(args.observations.read_text()) if args.observations else seed_observations()
    result = build_scorecard(args.history_dir, observations, now)
    write_new(args.history_dir / 'scorecard-runs' / (utc(now).strftime('%Y%m%dT%H%M%S%fZ') + '.json'), result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'versions': len(result['versions']), 'output': str(args.output), 'price_feed': 'supplied export' if args.observations else 'dated research snapshot; no automated price feed'}))


if __name__ == '__main__':
    main()
