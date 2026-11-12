"""Read-only, dated borrowing comparisons; independent of the research runtime.

Company ranks describe accounting measurements, never creditworthiness.
Coupon observations concern individual instruments and have no company rank.
"""
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import calendar
import re

BORROWING_BASIS = 'carrying_value_excluding_all_leases'
GROUPS = {'gpu_cloud', 'ai_transition', 'bitcoin_mining', 'data_center_reit'}
DEFINITIONS = {
    'cash': {
        'title': 'Reported cash and equivalents',
        'description': 'Cash held by the company and its subsidiaries, with selected credit facilities shown separately. A complete available-funding total is not established.',
        'formula': 'Reported group cash; individual facility amounts remain separate',
        'caveat': 'Group cash is not a verified parent-only spending balance. Restricted balances and conditional credit are separate. Sorting cash amounts does not rank financial health; no cash-plus-credit total is calculated.',
    },
    'debt': {
        'title': 'Recorded borrowings',
        'description': 'How big is the borrowing balance? This is the amount recorded for loans and notes, with leases left out.',
        'formula': 'Short-term + long-term recorded borrowings, excluding leases',
        'caveat': 'The recorded balance can differ from the principal required by the debt contract because of discounts, fees and other accounting adjustments. Operating and finance leases are excluded but remain real obligations. A larger balance does not establish repayment ability; some project debt has limited claims on the parent company.',
    },
    'debt_assets': {
        'title': 'Borrowings / assets',
        'description': 'How large are borrowings relative to the company’s recorded assets? Read the percentage as dollars of borrowing for every $100 of assets.',
        'formula': 'Reported borrowings ÷ total assets × 100, from the same reporting date',
        'caveat': 'Assets are not the same as cash available to repay debt. This ratio does not show which assets were financed with borrowing or predict default. Leased infrastructure, crypto holdings and construction assets make company comparisons imperfect. Assets can include the recorded right to use leased property, while the borrowing measure excludes lease obligations.',
    },
    'coupon': {
        'title': 'Fixed note coupon',
        'description': 'Company-reported averages are shown only where verified; other references name a specific loan or note. Rate types, dates and coverage differ. The fixed-note coupon ledger is a separate reference.',
        'formula': 'Issuer averages, contractual rates, floating spreads and accounting effective rates remain separate; no blended company rate is calculated',
        'caveat': 'A coupon is not current market yield or total company funding cost. Loan spreads require a dated benchmark before an all-in rate can be known. Accounting effective rates include different economics. Company-reported averages retain their stated scope and method; examples are not a uniform company cost ranking. Continued outstanding status has not been reverified for every historical coupon example.',
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


def validate_context(company, sources):
    """Optional same-date explanatory facts never change the ranking numerator."""
    context = company.get('debt_context')
    if not context:
        return
    for bridge in context.get('bridges', []):
        if bridge['as_of'] != company['as_of']:
            raise ValueError('Principal bridge must match the financial snapshot date')
        if bridge.get('unit') != 'USD':
            raise ValueError('Principal bridges require dated reported USD values')
        if not bridge.get('source_ids') or any(i not in sources for i in bridge['source_ids']):
            raise ValueError('Principal bridge requires linked evidence')
        principal, carrying = number(bridge.get('principal')), number(bridge.get('carrying'))
        if bridge.get('complete_company_scope'):
            if bridge.get('scope') != 'consolidated_borrowings' or principal is None or carrying is None:
                raise ValueError('A complete principal bridge requires consolidated borrowing scope')
            if carrying != number(company['metrics']['debt']['value']):
                raise ValueError('Complete bridge does not match recorded company borrowings')
        if bridge.get('scope') == 'consolidated_carrying_only':
            if principal is not None or carrying != number(company['metrics']['debt']['value']):
                raise ValueError('Carrying-only context must preserve unknown principal and match the recorded balance')
        bridge['principal'] = str(principal) if principal is not None else None
        bridge['carrying'] = str(carrying) if carrying is not None else None
        bridge['difference'] = str(principal - carrying) if principal is not None and carrying is not None else None
    for lease in context.get('leases', []):
        value = number(lease.get('value'))
        if value is not None:
            if lease.get('unit') != 'USD' or lease.get('as_of') != company['as_of']:
                raise ValueError('Excluded lease balances need the same date and USD units')
            if not lease.get('source_ids') or any(i not in sources for i in lease['source_ids']):
                raise ValueError('Excluded lease balances require evidence')
            lease['value'] = str(value)


def maturity_end(value):
    """Validate stated year/month/day precision without inventing a display date."""
    if re.fullmatch(r'\d{4}', value):
        return date(int(value), 12, 31)
    if re.fullmatch(r'\d{4}-\d{2}', value):
        year, month = map(int, value.split('-'))
        return date(year, month, calendar.monthrange(year, month)[1])
    return date.fromisoformat(value)


def validate_liquidity(company, sources):
    """Selected facilities describe dated capacity, never a cash-plus-credit total."""
    liquidity = company.get('liquidity')
    if liquidity is None:
        return
    if liquidity.get('as_of') != company['as_of'] or not liquidity.get('cash_caveat'):
        raise ValueError('Liquidity requires the company snapshot date and cash qualification')
    overall = liquidity.get('company_available_credit', {})
    if overall.get('value') is not None or overall.get('unit') != 'USD':
        raise ValueError('Selected facilities cannot establish a company-wide available-credit total')
    kinds = {'commitment', 'drawn', 'unused_capacity', 'reported_available',
             'letters_of_credit', 'borrowing_cap', 'lc_capacity',
             'restricted_cash', 'restricted_investments'}

    def validate_fact(fact):
        if fact.get('synthetic') is True or fact.get('provenance') in ('fixture', 'assumption', 'user_assumption'):
            raise ValueError('Synthetic funding inputs cannot enter actual liquidity context')
        if fact.get('as_of') != company['as_of'] or fact.get('unit') != 'USD':
            raise ValueError('Liquidity amounts require same-date reported USD evidence')
        if fact.get('kind') not in kinds or not fact.get('label'):
            raise ValueError('Liquidity amount must identify its category')
        value = number(fact.get('value'))
        ids = fact.get('source_ids', [])
        if any(i not in sources for i in ids) or (value is not None and not ids):
            raise ValueError('Liquidity amount requires linked evidence')
        if fact.get('include_in_cash') is not False:
            raise ValueError('Credit capacity and restricted balances cannot be added to cash')
        fact['value'] = str(value) if value is not None else None

    for fact in liquidity.get('excluded_balances', []):
        if fact.get('kind') not in ('restricted_cash', 'restricted_investments'):
            raise ValueError('Excluded balances must distinguish restricted cash and investments')
        validate_fact(fact)
    seen = set()
    for facility in liquidity.get('facilities', []):
        identity = facility.get('id', '')
        if identity in seen or not re.fullmatch(r'[A-Za-z0-9:_-]+', identity):
            raise ValueError('Facility identity must be unique within the company')
        seen.add(identity)
        if facility.get('as_of') != company['as_of']:
            raise ValueError('Later financing cannot enter a prior liquidity snapshot')
        if not all(facility.get(k) for k in ('name', 'scope', 'access_note', 'conditions')):
            raise ValueError('Facility scope and access conditions must be explicit')
        if not isinstance(facility['conditions'], list) or any(not isinstance(c, str) or not c.strip() for c in facility['conditions']):
            raise ValueError('Facility conditions must be a list of explicit qualifications')
        ids = facility.get('source_ids', [])
        if not ids or any(i not in sources for i in ids):
            raise ValueError('Facility terms require linked evidence')
        for fact in facility.get('amounts', []):
            validate_fact(fact)


def validate_instrument(item, company, sources, cutoff):
    value = number(item.get('value'))
    if value is None or item.get('unit') != 'percent' or item.get('currency') != 'USD':
        raise ValueError('Instrument reference needs an evidenced USD coupon in percent units')
    if item.get('rate_type') != 'fixed' or not all(item.get(k) for k in ('instrument', 'type', 'maturity')):
        raise ValueError('Fixed note terms, type and maturity are required')
    if not item.get('source_ids') or any(i not in sources for i in item['source_ids']):
        raise ValueError('Instrument terms require linked source evidence')
    observed = date.fromisoformat(item['as_of'])
    if observed > cutoff:
        raise ValueError('Instrument observation is later than the review cutoff')
    end = maturity_end(item['maturity'])
    if item.get('issue_date'):
        issued = date.fromisoformat(item['issue_date'])
        if issued > observed or end < issued:
            raise ValueError('Instrument issue/observation/maturity chronology is inconsistent')
    principal = item.get('outstanding_principal', {})
    balance = number(principal.get('value'))
    if balance is not None:
        if principal.get('unit') != 'USD' or date.fromisoformat(principal['as_of']) > cutoff:
            raise ValueError('Note outstanding balance needs dated USD principal')
        if not principal.get('source_ids') or any(i not in sources for i in principal['source_ids']):
            raise ValueError('Note principal requires its own dated evidence')
        principal['value'] = str(balance)
    status = item.get('outstanding_status')
    if status not in ('verified_at_snapshot', 'verified_at_earlier_date', 'terms_only'):
        raise ValueError('Instrument outstanding status must be explicit')
    if status == 'verified_at_snapshot':
        evidence = item.get('outstanding_evidence_ids', [])
        if not evidence or any(i not in sources for i in evidence) or item['as_of'] != company['as_of']:
            raise ValueError('Snapshot-confirmed note must have same-date outstanding-status evidence')
        if balance is not None and principal.get('as_of') != company['as_of']:
            raise ValueError('Note principal from another period cannot become a snapshot balance')
    item['value'] = str(value)
    item['rankable'] = True  # Eligible reference, never an ordinal company rank.


def validate_financing_rates(result, companies, sources, cutoff):
    """Typed issuer averages and named examples never form a mixed cost ranking."""
    kinds = {'issuer_reported_average', 'fixed_coupon', 'fixed_loan_rate',
             'floating_formula', 'reported_floating_rate', 'effective_instrument_rate'}
    rates = {}
    for rate in result.get('financing_rates', []):
        identity = rate.get('id', '')
        if identity in rates or not re.fullmatch(r'[A-Za-z0-9:_-]+', identity):
            raise ValueError('Financing rate identity must be unique')
        if rate.get('ticker') not in companies or rate.get('kind') not in kinds:
            raise ValueError('Financing rate company and type must be explicit')
        if rate.get('provenance') in ('fixture', 'assumption', 'user_assumption'):
            raise ValueError('Synthetic rates cannot enter the reference')
        observed = date.fromisoformat(rate['as_of'])
        if observed > cutoff:
            raise ValueError('Financing rate is later than the review cutoff')
        ids = rate.get('source_ids', [])
        if not ids or any(i not in sources for i in ids):
            raise ValueError('Financing rates require primary evidence links')
        if not all(rate.get(k) for k in ('instrument', 'scope', 'currency_scope', 'coverage', 'status')):
            raise ValueError('Rate instrument, scope, coverage and status must be stated')
        status = rate['status']
        snapshot = date.fromisoformat(companies[rate['ticker']]['as_of'])
        if status not in ('verified_at_snapshot', 'terms_only', 'earlier_only', 'undrawn_at_snapshot'):
            raise ValueError('Rate reference status must distinguish snapshot facts and dated terms')
        if status in ('verified_at_snapshot', 'undrawn_at_snapshot') and observed != snapshot:
            raise ValueError('Snapshot rate must match the company financial date')
        if status == 'earlier_only' and observed >= snapshot:
            raise ValueError('Earlier rate reference needs an earlier date')
        if rate.get('benchmark_value_percent') is not None:
            number(rate['benchmark_value_percent'])
            benchmark_ids = rate.get('benchmark_source_ids', [])
            if (not rate.get('benchmark') or not rate.get('benchmark_as_of')
                    or date.fromisoformat(rate['benchmark_as_of']) > cutoff
                    or not benchmark_ids or any(i not in sources for i in benchmark_ids)):
                raise ValueError('A benchmark fixing requires its own dated source evidence')
        value, spread = number(rate.get('rate_percent')), number(rate.get('spread_percent'))
        if rate['kind'] == 'floating_formula':
            if value is not None or not rate.get('benchmark') or not (spread is not None or rate.get('formula')):
                raise ValueError('Floating terms cannot masquerade as a numeric all-in rate')
        elif value is None:
            raise ValueError('A numeric reported rate is required for this rate type')
        if rate['kind'] == 'issuer_reported_average' and not rate.get('method'):
            raise ValueError('Issuer averages require their stated method and scope limitations')
        if rate.get('market_yield') is not None:
            raise ValueError('Contractual and accounting rates are not market-yield quotes')
        rate['rate_percent'] = str(value) if value is not None else None
        rate['spread_percent'] = str(spread) if spread is not None else None
        rate['ranked'] = False
        rates[identity] = rate
    for company in companies.values():
        summary = company.get('financing_rate_summary')
        if summary is None:
            continue
        if summary.get('computed_average') is not None or summary.get('company_highest_rate') is not None:
            raise ValueError('Partial reviewed rates cannot establish a computed average or company maximum')
        for key in ('primary_rate_id', 'reported_average_id'):
            identity = summary.get(key)
            if identity is not None:
                if identity not in rates or rates[identity]['ticker'] != company['ticker']:
                    raise ValueError('Selected financing rate must belong to the same company')
                if key == 'reported_average_id' and rates[identity]['kind'] != 'issuer_reported_average':
                    raise ValueError('A named instrument rate cannot become a company-reported average')


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
        published = date.fromisoformat(company['filed_at'])
        if snapshot > cutoff or published > cutoff:
            raise ValueError('Company snapshot is later than review cutoff')
        if published < snapshot:
            raise ValueError('Source publication cannot precede the company snapshot')
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
            if name != 'coupon' and item['as_of'] != company['as_of']:
                item['rankable'] = False
                item['note'] = 'Excluded from comparison: observation date does not match the company snapshot.'
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
                if item.get('unit') != 'percent':
                    raise ValueError('Coupon observations must use percent units')
                if item.get('currency') != 'USD':
                    raise ValueError('Coupon examples require explicitly identified USD instruments')
                if not all(item.get(k) for k in ('instrument', 'type', 'maturity')):
                    raise ValueError('Coupon needs identified instrument, type and maturity')
                if item.get('rate_type') != 'fixed':
                    raise ValueError('Coupon reference only accepts fixed contractual coupons')
                if item.get('issue_date') and date.fromisoformat(item['issue_date']) > date.fromisoformat(item['as_of']):
                    raise ValueError('Coupon instrument was not yet issued at observation date')
                if item.get('issue_date') and len(item['maturity']) == 10:
                    if date.fromisoformat(item['maturity']) < date.fromisoformat(item['issue_date']):
                        raise ValueError('Note maturity cannot precede its issue date')
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
        validate_context(company, sources)
        validate_liquidity(company, sources)
    companies_by_id = {c['ticker']: c for c in result['companies']}
    validate_financing_rates(result, companies_by_id, sources, cutoff)
    note_ids = set()
    for item in result.get('instruments', []):
        if item.get('id') in note_ids or not re.fullmatch(r'[A-Za-z0-9:_-]+', item.get('id', '')):
            raise ValueError('Duplicate or invalid instrument identity')
        note_ids.add(item['id'])
        if item.get('ticker') not in companies_by_id:
            raise ValueError('Instrument refers to an unknown company')
        validate_instrument(item, companies_by_id[item['ticker']], sources, cutoff)
    instruments_by_id = {i['id']: i for i in result.get('instruments', [])}
    for company in result['companies']:
        selected = company['metrics']['coupon']
        if selected.get('instrument_id'):
            note = instruments_by_id.get(selected['instrument_id'])
            if note is None or note['ticker'] != company['ticker']:
                raise ValueError('Pinned coupon must refer to the same company in the note ledger')
            if number(note['value']) != number(selected['value']):
                raise ValueError('Pinned coupon rate differs from its note-ledger record')
            for field in ('issuer', 'as_of', 'issue_date', 'maturity', 'outstanding_status'):
                if note.get(field) != selected.get(field):
                    raise ValueError('Pinned coupon metadata differs from its note-ledger record')
    names = set()
    for watcher in result.get('coverage_watchlist', []):
        if watcher['name'] in names or watcher.get('ranking_eligible') is not False:
            raise ValueError('Coverage-only operators must be unique and explicitly unranked')
        names.add(watcher['name'])
        if watcher.get('comparable_debt_usd') is not None or watcher.get('comparable_assets_usd') is not None:
            raise ValueError('Announced facilities cannot become comparable company balances')
        for source in watcher.get('sources', []):
            u = urlparse(source['url'])
            if u.scheme != 'https' or not u.hostname or u.username or u.password:
                raise ValueError('Watchlist evidence requires credential-free HTTPS sources')
            if date.fromisoformat(source['published_on']) > cutoff:
                raise ValueError('Watchlist source is later than review cutoff')
        for transaction in watcher.get('transactions', []):
            number(transaction.get('amount'))
            if date.fromisoformat(transaction['announced_on']) > cutoff:
                raise ValueError('Watchlist announcement is later than review cutoff')
            if transaction.get('outstanding_balance_usd') is not None:
                raise ValueError('This watchlist contains announcements, not verified debt snapshots')
    result.update(schema_version=3, metric_definitions=deepcopy(DEFINITIONS),
                  disclosure='Actual, dated source records. No synthetic financial inputs enter these rankings. '
                             'This is a curated research snapshot, not a live market feed or credit rating.')
    return result
