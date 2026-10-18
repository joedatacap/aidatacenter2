"""Explicit scenario assumptions for the offline demo, never reported financials."""
from datetime import date, timedelta
from .risk import FundingPlan, CashFlow, Contract, Repayment, months_after
from .finance import Instrument


def populate(run):
    day = date.fromisoformat(run['as_of'])
    for ticker in run['tickers']:
        common = dict(ticker=ticker, as_of=day, currency='USD', evidence_ids=[],
                      provenance='assumption', status='assumption', note='Illustrative user scenario; not company disclosure')
        for h in (12, 18):
            scale = h / 12
            lines = []
            for category, side, amount, certainty in [('capex', 'use', 1_000_000_000, 'management_guided'),
                  ('principal', 'use', 100_000_000, 'committed'), ('cash', 'source', 300_000_000, 'committed'),
                  ('operating_inflow', 'source', 200_000_000, 'analyst_estimated'),
                  ('undrawn', 'source', 400_000_000, 'analyst_estimated')]:
                lines.append(dict(**common, id=f'{ticker}-{h}-{category}', horizon_months=h, category=category,
                                  side=side, amount=str(int(amount * (1 if category == 'cash' else scale))),
                                  certainty=('committed' if category=='undrawn' and ticker in ('HUT','NBIS') else certainty), usable=True, entity='Illustrative consolidated scope',
                                  cashflow_key=category, conditions='SCENARIO ASSUMPTION; financing not verified',
                                  rate_sensitive_principal='200000000' if category=='principal' else None,
                                  rate_sensitivity='future_refinancing' if category=='principal' else 'none'))
            plan = FundingPlan(**common, id=f'{ticker}-{h}', horizon_months=h,
                               scope='Illustrative consolidated scenario; not a company forecast', complete=True,
                               market_cap='2000000000', market_cap_at=day, lines=lines)
            run['risk']['funding_plans'].append(plan.model_dump(mode='json'))
        flow = CashFlow(**common, id=ticker+'-ttm', period_start=day-timedelta(days=364), period_end=day,
                        adjusted_ebitda='120000000', cash_interest='60000000', interest_expense='80000000',
                        capitalized_interest='20000000', revenue='600000000', cfo='200000000',
                        maintenance_capex='100000000', growth_capex='900000000', definition='ILLUSTRATIVE EBITDA; not reported results')
        run['risk']['cash_flows'].append(flow.model_dump(mode='json'))
        item = Instrument(instrument_id=ticker+':illustrative-floating', ticker=ticker, name='ILLUSTRATIVE floating debt',
                          currency='USD', outstanding_principal='500000000', snapshot_date=day, rate_type='floating',
                          hedge_status='unhedged' if ticker=='CRWV' else 'partial', hedge_notional=None if ticker=='CRWV' else '300000000', hedge_effective_date=day-timedelta(days=1),
                          hedge_end_date=months_after(day, 6), maturity=months_after(day, 24),
                          provenance='fixture', verification_status='fixture').model_dump(mode='json')
        run['instruments'].append(item)
        repayment = Repayment(**common, id=ticker+'-amortization', instrument_id=item['instrument_id'], entity='Illustrative entity',
                              amount='100000000', due_start=months_after(day, 12), due_end=months_after(day, 12),
                              precision='day', kind='amortization', cashflow_key='illustrative-principal')
        run['risk']['repayments'].append(repayment.model_dump(mode='json'))
