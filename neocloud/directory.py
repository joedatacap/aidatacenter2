"""Read-only, dated borrowing comparisons; independent of the research runtime.

Company ranks describe accounting measurements, never creditworthiness.
Coupon observations concern individual instruments and have no company rank.
"""
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

BORROWING_BASIS = 'carrying_value_excluding_all_leases'
GROUPS = {'gpu_cloud', 'ai_transition', 'bitcoin_mining', 'data_center_reit'}
DEFINITIONS = {
    'debt': {
        'title': 'Reported borrowings',
        'description': 'How much the company owes on loans and notes, as recorded in its balance sheet.',
        'formula': 'Current borrowing carrying amount + noncurrent borrowing carrying amount',
        'caveat': 'USD carrying values exclude operating and finance leases, which are real obligations. Larger companies can have more debt without being less healthy. Project debt can be nonrecourse to the parent.',
    },
    'debt_assets': {
        'title': 'Borrowings / assets',
        'description': 'Dollars of borrowings for every $100 of recorded company assets.',
        'formula': 'Reported borrowings ÷ total assets × 100, from the same reporting date',
        'caveat': 'This is not a credit rating or repayment forecast. Lease-heavy vs owned infrastructure, crypto holdings and construction assets make comparisons imperfect. Assets include lease right-of-use assets, while the borrowing numerator excludes lease liabilities.',
    },
    'coupon': {
        'title': 'Bond coupon examples',
        'description': 'The stated annual interest rate on one identified fixed-rate note. Sort the examples, rather than rank company health.',
        'formula': 'Contractual fixed coupon for the named instrument; no blended borrowing-rate estimate',
        'caveat': 'Coupon is not current market yield or total funding cost. Convertible, secured project and unsecured notes differ. One note does not represent all company debt. These are terms from dated disclosures; continued outstanding status has not been reverified for every example.',
    },
}


def number(value):
    """Keep unknown separate from zero and reject nonfinite monetary values."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError('Boolean is not a financial number')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid financial number') from exc
    if not result.is_finite() or result < 0:
        raise ValueError('Financial values must be finite and nonnegative')
    return result


def build_directory(raw):
    result = deepcopy(raw)
    cutoff = date.fromisoformat(result['reviewed_at'])
    sources = {s['id']: s for s in result['sources']}
    if len(sources) != len(result['sources']):
        raise ValueError('Duplicate source identity')
    for source in sources.values():
        parsed = urlparse(source['url'])
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Sources require credential-free HTTPS URLs')
        if not source.get('excerpt') or not source.get('title'):
            raise ValueError('Source title and supporting passage required')
        if source.get('published_at') and date.fromisoformat(source['published_at']) > cutoff:
            raise ValueError('Source is later than review cutoff')
    seen = set()
    for company in result['companies']:
        if company.get('synthetic') is not False:
            raise ValueError('Company rankings accept actual reviewed records only')
        ticker = company['ticker']
        if ticker in seen or not ticker.isalnum():
            raise ValueError('Duplicate or invalid ticker')
        seen.add(ticker)
        if company['group'] not in GROUPS:
            raise ValueError('Unknown business group')
        snapshot = date.fromisoformat(company['as_of'])
        if snapshot > cutoff or date.fromisoformat(company['filed_at']) > cutoff:
            raise ValueError('Company snapshot is later than review cutoff')
        metrics = company['metrics']
        for name in ('debt', 'assets', 'cash', 'coupon'):
            item = metrics[name]
            if item.get('provenance') in ('fixture', 'assumption', 'user_assumption'):
                raise ValueError('Synthetic assumptions cannot enter actual company comparisons')
            value = number(item['value'])
            item['value'] = str(value) if value is not None else None
            item.setdefault('as_of', company['as_of'])
            if date.fromisoformat(item['as_of']) > cutoff:
                raise ValueError('Observation is later than review cutoff')
            if value is not None and not item.get('source_ids'):
                raise ValueError('Actual values require evidence')
            if any(s not in sources for s in item.get('source_ids', [])):
                raise ValueError('Metric refers to missing source evidence')
            item['rankable'] = value is not None
            if name != 'coupon' and item.get('unit') != 'USD':
                item['rankable'] = False
                item['note'] = 'Unavailable for USD comparison: no dated FX conversion.'
            if name == 'debt' and value is not None:
                if item.get('basis_key') != BORROWING_BASIS or item.get('scope') != 'consolidated':
                    item['rankable'] = False
                    item['note'] = 'Excluded from ranking: borrowing definition or scope is not comparable.'
                if item.get('components'):
                    if any(c.get('operation', 'add') not in ('add', 'subtract') for c in item['components']):
                        raise ValueError('Unknown borrowing reconciliation operation')
                    total = sum((number(c['value']) * (-1 if c.get('operation') == 'subtract' else 1)
                                 for c in item['components']), Decimal(0))
                    if total != value:
                        raise ValueError(f'{ticker}: borrowing components do not reconcile')
            if name == 'coupon' and value is not None:
                if item.get('currency') != 'USD':
                    raise ValueError('Coupon examples require explicitly identified USD instruments')
                if not all(item.get(k) for k in ('instrument', 'type', 'maturity')):
                    raise ValueError('Coupon needs identified instrument, type and maturity')
                if item.get('rate_type') != 'fixed':
                    raise ValueError('Coupon reference only accepts fixed contractual coupons')
                if item.get('issue_date') and date.fromisoformat(item['issue_date']) > date.fromisoformat(item['as_of']):
                    raise ValueError('Coupon instrument was not yet issued at observation date')
                item['note'] = item.get('note') or 'Selected instrument only; not current market yield.'
        debt, assets = metrics['debt'], metrics['assets']
        d, a = number(debt['value']), number(assets['value'])
        comparable = (debt['rankable'] and assets['rankable'] and assets.get('scope') == 'consolidated'
                      and a is not None and a > 0
                      and debt['as_of'] == assets['as_of'] == company['as_of'])
        ratio = d / a * Decimal(100) if comparable else None
        metrics['debt_assets'] = {
            'value': str(ratio) if ratio is not None else None, 'unit': 'percent',
            'rankable': comparable, 'as_of': company['as_of'],
            'basis': 'Borrowing carrying value / same-date consolidated total assets × 100',
            'note': '' if comparable else 'Unranked: comparable same-date borrowings and assets required.',
            'source_ids': sorted(set(debt.get('source_ids', []) + assets.get('source_ids', []))),
        }
    result.update(schema_version=1, metric_definitions=deepcopy(DEFINITIONS),
                  disclosure='Actual, dated source records. No synthetic financial inputs enter these rankings. '
                             'This is a curated research snapshot, not a live market feed or credit rating.')
    return result
