"""V2 deterministic financing calculations. Monetary inputs are actual currency units.

Incomplete disclosures produce partial known amounts, never company-wide zeroes.
"""
import calendar
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

D = Decimal
Tick = Literal['CRWV', 'NBIS', 'IREN', 'BTDR', 'HUT']


def months_after(day, months):
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


class Fact(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    id: str
    ticker: Tick
    currency: str = 'USD'
    as_of: date
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: Literal['live', 'fixture', 'assumption'] = 'live'
    status: Literal['needs_review', 'auditor_verified', 'fixture', 'assumption', 'user_assumption'] = 'needs_review'
    note: str = ''


class FundingLine(Fact):
    horizon_months: Literal[12, 18]
    side: Literal['source', 'use']
    category: Literal['capex', 'project_equity', 'principal', 'operating_burn', 'mandatory',
                      'cash', 'operating_inflow', 'undrawn', 'prepayment', 'other_inflow']
    amount: Decimal = Field(ge=0)
    entity: str
    project: str | None = None
    segment: str = 'unknown'
    certainty: Literal['committed', 'management_guided', 'analyst_estimated', 'speculative']
    usable: bool | None = None
    conditions: str = 'unknown'
    deferrable: bool | None = None
    # Stable economic cash-flow identity, shared by debt proceeds/cash or prepayments/CFO.
    cashflow_key: str
    included_in: str | None = None
    rate_sensitive_principal: Decimal | None = Field(default=None, ge=0)
    rate_sensitivity: Literal['none', 'known_unhedged', 'future_refinancing'] = 'none'

    @model_validator(mode='after')
    def cashflow_side(self):
        uses={'capex','project_equity','principal','operating_burn','mandatory'}
        if (self.category in uses) != (self.side=='use'):
            raise ValueError('Cash flow category has the wrong side')
        if self.rate_sensitivity!='none' and self.side!='use':
            raise ValueError('Rate sensitivity must be an explicit incremental use')
        return self


class FundingPlan(Fact):
    horizon_months: Literal[12, 18]
    # Affirm completeness only when uses and sources of this entity/purpose were reviewed.
    complete: bool = False
    scope: str
    market_cap: Decimal | None = Field(default=None, gt=0)
    market_cap_at: date | None = None
    market_cap_evidence_ids: list[str] = Field(default_factory=list)
    lines: list[FundingLine] = Field(default_factory=list)

    @model_validator(mode='after')
    def scope_consistency(self):
        if any((x.ticker, x.currency, x.as_of, x.horizon_months) !=
               (self.ticker, self.currency, self.as_of, self.horizon_months) for x in self.lines):
            raise ValueError('Funding lines must share ticker, currency, as-of and horizon')
        if self.market_cap is not None and (self.market_cap_at is None or self.market_cap_at > self.as_of):
            raise ValueError('Market capitalization requires a date')
        return self


class BondQuote(Fact):
    instrument_id: str
    security_id: str
    observed_price: Decimal | None = Field(default=None, gt=0)
    market_yield_pct: Decimal | None = Field(default=None, ge=0)
    yield_type: Literal['YTM', 'YTW', 'current_yield', 'indicative']
    quoted_at: datetime
    source_url: str
    quote_type: Literal['trade', 'bid', 'ask', 'mid', 'media', 'indicative']
    bid_ask: str | None = None
    estimated_liquidity: str = 'unknown'
    treasury_yield_pct: Decimal | None = Field(default=None, ge=0)
    treasury_date: date | None = None
    treasury_maturity: date | None = None
    treasury_evidence_ids: list[str] = Field(default_factory=list)


class Contract(Fact):
    instrument_ids: list[str]
    project: str
    debt_entity: str
    recourse: str = 'unknown'
    customer: str
    legal_obligor: str
    contract_status: str
    category: Literal['verified guarantee/backstop', 'contracted-not-guaranteed', 'prepaid', 'merchant/spot', 'unverified']
    annual_minimum: Decimal | None = Field(default=None, ge=0)
    term: str = 'unknown'
    commencement: str = 'unknown'
    escalators: str = 'unknown'
    termination_conditions: str = 'unknown'
    collateral: str = 'unknown'
    guarantor: str | None = None
    guarantee_cap: Decimal | None = Field(default=None, ge=0)
    covered_obligations: str = 'unknown'
    covered_period: str = 'unknown'
    guarantee_conditions: str = 'unknown'
    guarantee_type: str = 'unknown'
    guarantor_rating: str = 'unknown'
    guarantor_rating_date: date | None = None
    prepayment: Decimal | None = Field(default=None, ge=0)
    prepayment_refundable: bool | None = None
    prepayment_restricted: bool | None = None
    financed_project_coverage: str = 'unknown'
    concentration: str = 'unknown'
    related_party: bool | None = None
    construction_risk: str = 'unknown'
    merchant_exposure: str = 'unknown'


class CashFlow(Fact):
    period_start: date
    period_end: date
    adjusted_ebitda: Decimal | None = None
    cash_interest: Decimal | None = Field(default=None, ge=0)
    interest_expense: Decimal | None = Field(default=None, ge=0)
    capitalized_interest: Decimal | None = Field(default=None, ge=0)
    revenue: Decimal | None = Field(default=None, gt=0)
    cfo: Decimal | None = None
    maintenance_capex: Decimal | None = Field(default=None, ge=0)
    growth_capex: Decimal | None = Field(default=None, ge=0)
    definition: str

    @model_validator(mode='after')
    def ttm(self):
        if not 360 <= (self.period_end - self.period_start).days <= 366 or self.period_end > self.as_of:
            raise ValueError('Coverage requires consistent trailing 12-month inputs ending by as-of')
        return self


class BalanceSnapshot(Fact):
    scope: str
    debt_scope_complete: bool = False
    gross_debt: Decimal | None = Field(default=None, ge=0)
    unrestricted_cash: Decimal | None = Field(default=None, ge=0)
    equity_market_cap: Decimal | None = Field(default=None, gt=0)
    equity_market_cap_at: date | None = None

    @model_validator(mode='after')
    def equity_date(self):
        if self.equity_market_cap is not None and (self.equity_market_cap_at is None or self.equity_market_cap_at > self.as_of):
            raise ValueError('Equity market cap date required')
        return self


class Repayment(Fact):
    instrument_id: str
    entity: str
    recourse: str = 'unknown'
    amount: Decimal = Field(ge=0)
    due_start: date
    due_end: date
    precision: Literal['day', 'quarter', 'year', 'range']
    kind: Literal['amortization', 'bullet', 'current_portion']
    cashflow_key: str
    # An aggregate current portion must reference the rows it includes.
    included_in: str | None = None
    repayment_support: str = 'unknown; collateral is not cash'

    @model_validator(mode='after')
    def dates(self):
        if self.due_start > self.due_end or (self.precision == 'day' and self.due_start != self.due_end):
            raise ValueError('Invalid repayment range')
        return self


def funding_gap(plan: FundingPlan, scenario='Base', inflow_factor=D('0.75'), capex_factor=D('1'), delta_bps=200):
    if scenario not in ('Base', 'Downside', 'Tight credit'):
        raise ValueError('Unsupported scenario')
    if not inflow_factor.is_finite() or not capex_factor.is_finite():
        raise ValueError('Sensitivity must be finite')
    if not D(0) <= inflow_factor <= D(1) or not D('0.5') <= capex_factor <= D(2):
        raise ValueError('Sensitivity outside supported range')
    uses = sources = D(0)
    rows, warnings, seen = [], [], set()
    keys = {x.cashflow_key for x in plan.lines}
    for line in plan.lines:
        amount, reason = line.amount, None
        if line.cashflow_key in seen or (line.included_in and line.included_in in keys):
            amount, reason = D(0), 'Already included in another cash flow'
        elif line.side == 'source' and line.usable is not True:
            amount, reason = D(0), 'Availability or entity/purpose eligibility not established'
        elif scenario == 'Tight credit' and line.category == 'undrawn' and line.certainty != 'committed':
            amount, reason = D(0), 'Uncommitted financing unavailable in tight credit'
        elif line.certainty == 'speculative':
            amount, reason = D(0), 'Speculative amount excluded'
        else:
            seen.add(line.cashflow_key)
            if (scenario != 'Base' and line.side == 'use' and line.rate_sensitivity != 'none'
                    and line.rate_sensitive_principal is not None):
                amount += line.rate_sensitive_principal * D(delta_bps) / 10000 * D(plan.horizon_months) / 12
            if line.category == 'capex':
                amount *= capex_factor
            if scenario in ('Downside', 'Tight credit') and line.category == 'operating_inflow':
                amount *= inflow_factor
        if reason:
            warnings.append(line.id + ': ' + reason)
        if line.side == 'use':
            uses += amount
        else:
            sources += amount
        rows.append({**line.model_dump(mode='json'), 'scenario_amount': str(amount), 'exclusion': reason})
    # Conflicting inflow/burn representations and duplicate flow identities need review.
    duplicate = len({x.cashflow_key for x in plan.lines}) != len(plan.lines)
    ambiguous = any(x.category == 'operating_burn' for x in plan.lines) and any(x.category == 'operating_inflow' for x in plan.lines)
    complete = (plan.complete and bool(rows) and not duplicate and not ambiguous and
                not any(x.certainty == 'speculative' for x in plan.lines))
    gap = max(D(0), uses - sources) if complete else None
    ratio = gap / plan.market_cap if gap is not None and plan.market_cap is not None else None
    return {'status': 'estimated_scenario' if complete else 'insufficient_inputs',
            'provenance':plan.provenance, 'input_status':plan.status, 'scenario': scenario, 'horizon_months': plan.horizon_months, 'as_of': str(plan.as_of),
            'scope': plan.scope, 'currency': plan.currency, 'gross_uses': str(uses), 'usable_sources': str(sources),
            'unfunded_gap': str(gap) if gap is not None else None,
            'funding_gap_to_market_cap': str(ratio) if ratio is not None else None,
            'market_cap': str(plan.market_cap) if plan.market_cap is not None else None,
            'market_cap_at': str(plan.market_cap_at) if plan.market_cap_at else None,
            'market_cap_evidence_ids': plan.market_cap_evidence_ids,
            'rows': rows, 'warnings': warnings + (['Ambiguous operating inflow/burn'] if ambiguous else []),
            'assumptions': {'operating_inflow_factor': str(inflow_factor) if scenario != 'Base' else '1',
                            'capex_factor': str(capex_factor), 'rate_shock_bps': delta_bps if scenario != 'Base' else 0, 'refinancing': 'Only separately identified committed inflows; no automatic rollovers'}}


def debt_cost(instrument, quotes, as_of, max_age_days=7):
    rows = [q for q in quotes if q.instrument_id == instrument['instrument_id'] and
            q.security_id == instrument.get('security_id') and q.currency == instrument['currency'] and q.quoted_at.date() <= as_of]
    quote = max(rows, key=lambda q: q.quoted_at) if rows else None
    maturity = instrument.get('maturity')
    maturity = date.fromisoformat(maturity) if isinstance(maturity, str) else maturity
    spread = None
    if (quote and quote.yield_type == 'YTM' and quote.quote_type not in ('media', 'indicative') and
            quote.treasury_date == quote.quoted_at.date() and quote.treasury_maturity == maturity and
            quote.treasury_evidence_ids and quote.treasury_yield_pct is not None and quote.market_yield_pct is not None):
        spread = str((quote.market_yield_pct - quote.treasury_yield_pct) * 100)
    fresh = quote and (as_of - quote.quoted_at.date()).days <= max_age_days and quote.quote_type not in ('media', 'indicative')
    return {'instrument_id': instrument['instrument_id'], 'name': instrument['name'], 'currency': instrument['currency'],
            'coupon_pct': instrument.get('coupon_pct'), 'original_issue_yield_pct': instrument.get('original_issue_yield_pct'),
            'reference_index': instrument.get('reference_index'), 'spread_bps': instrument.get('spread_bps'),
            'quote': quote.model_dump(mode='json') if quote else None,
            'status': 'dated_quote' if fresh else 'Yield unavailable',
            'quote_age_days': (as_of - quote.quoted_at.date()).days if quote else None,
            'yield_minus_coupon_bps': str((quote.market_yield_pct - D(str(instrument['coupon_pct']))) * 100)
            if quote and quote.market_yield_pct is not None and instrument.get('coupon_pct') is not None else None,
            'matched_treasury_spread_bps': spread, 'evidence_ids': instrument.get('evidence_ids', []),
            'caveat': 'Last dated observation only. YTM, YTW and current yield differ. Fixed contractual cash interest does not reprice.'}


def interest_coverage(flow):
    if flow is None:
        return {'status': 'insufficient_inputs', 'coverage': None, 'cash_flow': None}
    meaningful = flow.adjusted_ebitda is not None and flow.adjusted_ebitda > 0 and flow.cash_interest is not None and flow.cash_interest > 0
    status = ('negative/not meaningful' if flow.adjusted_ebitda is not None and flow.adjusted_ebitda <= 0
              else 'calculated' if meaningful else 'insufficient_inputs')
    fcf = flow.cfo - flow.maintenance_capex - flow.growth_capex if all(x is not None for x in (flow.cfo, flow.maintenance_capex, flow.growth_capex)) else None
    return {'status': status, 'coverage': str(flow.adjusted_ebitda / flow.cash_interest) if meaningful else None,
            'ebitda_margin': str(flow.adjusted_ebitda / flow.revenue) if flow.adjusted_ebitda is not None and flow.revenue else None,
            'fcf_after_capex': str(fcf) if fcf is not None else None, 'cash_flow': flow.model_dump(mode='json'),
            'caveat': 'Adjusted EBITDA definitions vary; it is not cash available for debt service. Cash interest, expense and capitalized interest differ.'}


def floating_exposure(instruments, as_of, delta_bps=200):
    totals, rows = {}, []
    for item in instruments:
        currency = item['currency']
        total = totals.setdefault(currency, dict.fromkeys(['fixed', 'gross_floating', 'hedged_floating', 'unhedged_floating', 'unknown_hedge', 'unknown_rate', 'unknown_balance_count', 'annual_shock'], D(0)))
        previous_unhedged = total['unhedged_floating']
        amount = item.get('outstanding_principal')
        row = {'instrument_id': item['instrument_id'], 'snapshot_date': item.get('snapshot_date'),
               'hedge_expiry': item.get('hedge_end_date'), 'floor_pct': item.get('floor_pct'),
               'repricing_cadence': item.get('repricing_cadence'), 'evidence_ids': item.get('evidence_ids', [])}
        if amount is None or (item.get('snapshot_date') and date.fromisoformat(str(item['snapshot_date'])) > as_of) or (item.get('maturity') and date.fromisoformat(str(item['maturity']))<=as_of):
            total['unknown_balance_count'] += 1
            row['status'] = 'balance unavailable for selected date'
        else:
            amount = D(str(amount))
            if item['rate_type'] in ('fixed', 'convertible'):
                total['fixed'] += amount
            elif item['rate_type'] == 'floating':
                total['gross_floating'] += amount
                start, end = item.get('hedge_effective_date'), item.get('hedge_end_date')
                if item.get('hedge_status') == 'unhedged':
                    total['unhedged_floating'] += amount
                elif (item.get('hedge_status') in ('hedged', 'partial') and item.get('hedge_notional') is not None and
                      start and end and date.fromisoformat(str(start)) <= as_of < date.fromisoformat(str(end))):
                    hedged = min(amount, D(str(item['hedge_notional'])))
                    total['hedged_floating'] += hedged
                    total['unhedged_floating'] += amount - hedged
                elif (item.get('hedge_status') in ('hedged','partial') and start and end and
                      (as_of < date.fromisoformat(str(start)) or as_of >= date.fromisoformat(str(end)))):
                    total['unhedged_floating'] += amount
                else:
                    total['unknown_hedge'] += amount
            else:
                total['unknown_rate'] += amount
            row['status'] = 'Known disclosed portion only'
        effective_delta = D(delta_bps) / 10000
        if item.get('floor_pct') is not None and item.get('reference_rate_pct') is not None:
            benchmark, floor = D(str(item['reference_rate_pct'])), D(str(item['floor_pct']))
            effective_delta = (max(benchmark + D(delta_bps)/100, floor) - max(benchmark, floor)) / 100
        total['annual_shock'] += (total['unhedged_floating'] - previous_unhedged) * effective_delta
        rows.append(row)
    return {'as_of': str(as_of), 'delta_bps': delta_bps, 'by_currency': {c: {k: str(v) for k, v in t.items()} for c, t in totals.items()},
            'rows': rows, 'caveat': 'Immediate annualized parallel benchmark shock on known unhedged balances; floors, resets and hedge expiry may alter realized cost. Unknown hedge coverage stays unknown. Refinancing is separate.'}


def maturity_wall(repayments, as_of, complete=False):
    rows, seen, buckets = [], set(), {}
    keys = {r.cashflow_key for r in repayments}
    for row in repayments:
        if row.as_of > as_of or row.cashflow_key in seen or (row.included_in and row.included_in in keys):
            continue
        seen.add(row.cashflow_key)
        if row.due_end <= as_of or row.due_start > months_after(as_of, 24):
            continue
        included = {}
        for horizon in (12, 18, 24):
            boundary = months_after(as_of, horizon)
            included[str(horizon)] = ('within' if as_of < row.due_start and row.due_end <= boundary
                                      else 'overlaps_boundary' if row.due_start <= boundary else 'outside')
        detail = {**row.model_dump(mode='json'), 'horizons': included}
        rows.append(detail)
        for horizon, status in included.items():
            if status == 'within':
                key = (row.currency, horizon)
                buckets[key] = buckets.get(key, D(0)) + row.amount
    return {'status': 'disclosed_schedule' if complete else 'partial_schedule' if rows else 'insufficient_inputs',
            'as_of': str(as_of), 'rows': rows,
            'known_due': {c: {str(h): str(buckets.get((c, str(h)), D(0))) for h in (12, 18, 24)} for c in {r['currency'] for r in rows}},
            'caveat': 'Partial known principal only unless schedule complete. Range overlaps remain unallocated; no invented monthly dates. Current portion and amortization must not duplicate bullets.'}


FACT_TYPES = {'funding_plans': FundingPlan, 'bond_quotes': BondQuote, 'contracts': Contract,
              'cash_flows': CashFlow, 'repayments': Repayment, 'balances': BalanceSnapshot}


def eligible(record, run):
    if record.get('provenance')=='assumption' and record.get('status')=='user_assumption':
        return True
    if run['mode'] == 'simulated':
        return record.get('provenance') in ('fixture', 'assumption')
    if record.get('status') != 'auditor_verified' or record.get('provenance') != 'live':
        return False
    evidence = {e['id'] for e in run['evidence'] if e.get('provenance') == 'live' and e.get('verification_status') == 'source_excerpt_matched'}
    ids = record.get('evidence_ids', [])
    return bool(ids) and set(ids) <= evidence


def comparison(run, as_of, scenario='Base', delta_bps=200, inflow_factor=D('.75'), capex_factor=D(1)):
    result = {}
    for ticker in run['tickers']:
        facts = {key: [model.model_validate(x) for x in run.get('risk', {}).get(key, [])
                      if x['ticker'] == ticker and date.fromisoformat(x['as_of']) <= as_of and eligible(x, run)]
                 for key, model in FACT_TYPES.items()}
        instruments = [i for i in run['instruments'] if i['ticker'] == ticker and
                       (run['mode'] == 'simulated' or i.get('verification_status') == 'auditor_verified') and
                       (not i.get('snapshot_date') or date.fromisoformat(i['snapshot_date']) <= as_of)]
        funding = []
        for h in (12, 18):
            plans = [p for p in facts['funding_plans'] if p.horizon_months == h]
            # Dated forecasts cannot be silently rebased to a new horizon.
            plans = [p for p in plans if p.as_of == as_of]
            funding.append(funding_gap(plans[-1], scenario, inflow_factor, capex_factor, delta_bps)
                           if plans else {'status': 'insufficient_inputs', 'horizon_months': h, 'unfunded_gap': None,
                                          'rows': [], 'funding_gap_to_market_cap': None, 'as_of': str(as_of),
                                          'note': 'No reviewed sources-and-uses plan for this date'})
        flows = facts['cash_flows']
        result[ticker] = {'funding': funding,
                         'debt_cost': [debt_cost(i, facts['bond_quotes'], as_of) for i in instruments],
                         'contracts': [c.model_dump(mode='json') for c in facts['contracts']],
                         'coverage': interest_coverage(max(flows, key=lambda f: f.period_end) if flows else None),
                         'floating': floating_exposure(instruments, as_of, delta_bps),
                         'maturities': maturity_wall(facts['repayments'], as_of),
                         'leverage': leverage_context(instruments, facts['balances']),
                         'provisional_count': sum(1 for key in FACT_TYPES for x in run.get('risk', {}).get(key, [])
                                                  if x['ticker'] == ticker and not eligible(x, run))}
    return {'as_of': str(as_of), 'scenario': scenario, 'mode': run['mode'], 'tickers': result,
            'disclosure': 'Known disclosed portions only. No composite safety score. HUT and BTDR have mixed segments.'}


def leverage_context(instruments, snapshots):
    # No company-wide leverage ratio without a complete debt scope and dated cash/equity values.
    amounts = {}
    for item in instruments:
        if item.get('outstanding_principal') is not None:
            amounts[item['currency']] = amounts.get(item['currency'], D(0)) + D(str(item['outstanding_principal']))
    snapshot = max(snapshots, key=lambda s: s.as_of) if snapshots else None
    ready = bool(snapshot and snapshot.debt_scope_complete and snapshot.gross_debt is not None and snapshot.equity_market_cap is not None)
    gross = snapshot.gross_debt / snapshot.equity_market_cap if ready else None
    net = (snapshot.gross_debt - snapshot.unrestricted_cash) / snapshot.equity_market_cap if ready and snapshot.unrestricted_cash is not None else None
    return {'known_principal_by_currency': {c: str(v) for c, v in amounts.items()},
            'gross_debt_to_market_cap': str(gross) if gross is not None else None,
            'net_debt_to_market_cap': str(net) if net is not None else None,
            'snapshot': snapshot.model_dump(mode='json') if snapshot else None,
            'status': 'calculated' if ready else 'insufficient_inputs', 'note': ('Reviewed consolidated balance; ' if ready else 'Incomplete company debt coverage; ')+'price declines mechanically raise debt/market cap. Issuance and commitments excluded.'}
