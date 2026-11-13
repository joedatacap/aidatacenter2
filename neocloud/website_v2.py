"""Validated, offline website enrichment; never mutates the original ledger.

Market values are provider-reported snapshots, not a real-time quote service.
Debt/market-cap is deliberately separate from book leverage and enterprise value.
"""
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse


def amount(value, *, positive=False):
    if isinstance(value, bool):
        raise ValueError('Boolean is not a financial amount')
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid financial amount') from exc
    if not n.is_finite() or n < 0 or (positive and n == 0):
        raise ValueError('Expected finite non-negative amount')
    return n


def debt_market_cap(debt, market, *, listing, debt_date, debt_currency='USD'):
    """Return an indicative percentage only with usable, explicitly dated inputs."""
    if listing != 'listed' or debt is None or not market or market.get('ratio_blocker'):
        return None
    if market.get('currency') != debt_currency or market.get('status') != 'provider_reported':
        return None
    if date.fromisoformat(debt_date) > date.fromisoformat(market['as_of']):
        return None
    return float((amount(debt) / amount(market['value'], positive=True) * 100).quantize(Decimal('.01')))


def build_website_v2(directory, enrichment):
    result = deepcopy(directory)
    if enrichment.get('schema_version') != 1:
        raise ValueError('Unsupported website schema')
    reviewed = date.fromisoformat(enrichment['reviewed_at'])
    sources = {s['id']: s for s in result['sources']}
    for s in enrichment['sources']:
        if s['id'] in sources:
            raise ValueError('Duplicate source id')
        if urlparse(s['url']).scheme not in ('https', 'http') or not urlparse(s['url']).netloc:
            raise ValueError('Unsafe source URL')
        if not s.get('excerpt') or not s.get('title'):
            raise ValueError('Source requires title and supporting excerpt')
        date.fromisoformat(s['published_at'])
        date.fromisoformat(s['retrieved_at'])
        sources[s['id']] = s
    known = {c['ticker'] for c in result['companies']}
    if set(enrichment['companies']) != known:
        raise ValueError('Coverage must explicitly account for every company')

    def refs(record, *, required=True):
        ids = record.get('source_ids', [])
        if required and not ids:
            raise ValueError('Material assertion requires sources')
        if any(s not in sources for s in ids):
            raise ValueError('Unresolved source reference')

    for c in result['companies']:
        x = deepcopy(enrichment['companies'][c['ticker']])
        for category in ('contracts', 'capacity', 'hardware', 'revenue', 'events'):
            for f in x.get(category, []):
                if f['status'] not in {'reported','operating','contracted','construction','announced','commissioning','unknown','not_applicable'}:
                    raise ValueError('Unknown evidence status')
                if date.fromisoformat(f['as_of']) > reviewed:
                    raise ValueError('Future observation')
                if not f.get('scope') or not f.get('display'):
                    raise ValueError('Fact requires display and scope')
                refs(f, required=f['status'] != 'unknown')
        market = x.get('market_cap')
        if market:
            if market['currency'] != 'USD' or market['status'] != 'provider_reported':
                raise ValueError('Market size cohorts require provider-reported USD equity values')
            amount(market['value'], positive=True)
            refs(market)
            if date.fromisoformat(market['as_of']) > reviewed or market['time_precision'] != 'date':
                raise ValueError('Invalid market snapshot date')
            if c['listing_status'] != 'listed':
                raise ValueError('Private valuation cannot masquerade as public market cap')
        snapshot = x.get('snapshot')
        if snapshot:
            refs(snapshot)
            if not date.fromisoformat(c['as_of']) < date.fromisoformat(snapshot['as_of']) <= reviewed:
                raise ValueError('Replacement snapshot must be newer and not in future')
            x['previous_snapshot'] = {'as_of': c['as_of'], 'notes': c.get('notes', []), 'debt_context_notes': c.get('debt_context', {}).get('notes', [])}
            historical_date = c['as_of']
            c['notes'] = [snapshot['note']]
            c['debt_context']['notes'] = [f'Historical bridge and lease evidence retains its original dates, including {historical_date}; it is not a refreshed Q3 principal inventory.']
            c['liquidity']['historical_context_as_of'] = historical_date
            c['liquidity']['cash_caveat'] = 'Q3 group cash updated; parent availability is not established. Selected facility and excluded-balance records retain their historical dates.'
            c['liquidity']['takeaway'] = snapshot['note']
            c['liquidity']['notes'] = [f'Historical context from {historical_date}: {note}' for note in c['liquidity'].get('notes', [])]
            total = sum((amount(p['value']) for p in snapshot['debt_components']), Decimal(0))
            for key, value in [('debt', total), ('cash', amount(snapshot['cash'])), ('assets', amount(snapshot['assets']))]:
                c['metrics'][key] = dict(c['metrics'][key], value=str(value), as_of=snapshot['as_of'], source_ids=snapshot['source_ids'])
            c['metrics']['cash']['basis'] = 'Cash and cash equivalents; excludes separately classified restricted cash'
            c['metrics']['cash']['note'] = 'No company-wide parent-available liquidity total is inferred.'
            c['metrics']['debt']['components'] = snapshot['debt_components']
            c['metrics']['debt']['note'] = snapshot['note']
            c['metrics']['debt']['basis'] = 'Reported current debt plus non-current debt at carrying value; separately classified leases excluded'
            # Derived book leverage from the old snapshot must not leak into exports.
            c['metrics'].pop('debt_assets', None)
            c['as_of'], c['filed_at'] = snapshot['as_of'], snapshot['filed_at']
            c['source_ids'] = list(dict.fromkeys(c.get('source_ids', []) + snapshot['source_ids']))
        for instrument in x.get('debt_inventory', []):
            amount(instrument['principal'])
            refs(instrument)
            if instrument['currency'] != 'USD' or date.fromisoformat(instrument['as_of']) > reviewed:
                raise ValueError('Invalid inventory currency/date')
            if instrument['rate_kind'] not in ('contractual', 'effective_accounting'):
                raise ValueError('Unknown rate kind')
        schedule = x.get('maturity_schedule')
        if schedule:
            refs(schedule)
            if schedule['currency'] != 'USD' or date.fromisoformat(schedule['as_of']) > reviewed:
                raise ValueError('Invalid maturity schedule')
            if sum((amount(b['value']) for b in schedule['buckets']), Decimal(0)) != amount(schedule['total']):
                raise ValueError('Principal schedule does not reconcile')
        x['debt_market_cap_percent'] = debt_market_cap(c['metrics']['debt']['value'], market, listing=c['listing_status'], debt_date=c['as_of'])
        x['size_band'] = ('large' if amount(market['value']) >= 10_000_000_000 else 'mid' if amount(market['value']) >= 2_000_000_000 else 'small') if market else 'unknown'
        x['financial_age_days'] = (reviewed - date.fromisoformat(c['as_of'])).days
        x['context_coverage'] = sum(any(f['status'] != 'unknown' for f in x.get(k, [])) for k in ('contracts','capacity','hardware','revenue'))
        c['v2'] = x
    result['sources'] = list(sources.values())
    result['website_reviewed_at'] = enrichment['reviewed_at']
    return result
