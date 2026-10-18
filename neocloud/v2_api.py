"""Additive V2 endpoints; V1 API and Postgres repository remain compatible."""
import csv
import io
from datetime import date
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response, FileResponse
from pydantic import Field
from .app import RunRequest, STATIC
from .risk import comparison, FundingPlan, FACT_TYPES
from .v2_engine import new_v2_run

router = APIRouter()


class RiskRunRequest(RunRequest):
    as_of: date = Field(default_factory=date.today)


@router.get('/v2')
async def dashboard():
    return FileResponse(STATIC / 'v2.html')


@router.post('/api/v2/runs', status_code=202)
async def start(request: Request, body: RiskRunRequest):
    state = request.app.state
    if body.mode == 'live' and not state.crusoe.router.view()['routes']['manager']['routable']:
        raise HTTPException(503, 'Verify Crusoe role routes before a live V2 run')
    if state.worker.done():
        raise HTTPException(503, 'Research worker unavailable')
    if len([r for r in await state.repo.all() if r['status'] in ('queued', 'running')]) >= 5:
        raise HTTPException(429, 'Five runs already active')
    run = new_v2_run(body.tickers, body.mode, body.as_of)
    if 'HUT' in body.tickers:
        from .hut_reference import seed
        seed(run)
    await state.repo.save(run)
    return {'id': run['id'], 'status': run['status'], 'version': 2}


async def fetch_run(request, run_id):
    run = await request.app.state.repo.get(run_id)
    if run is None:
        raise HTTPException(404, 'Run not found')
    return run


@router.get('/api/v2/runs/{run_id}/risk')
async def risk(request: Request, run_id: str, as_of: date | None = None,
               scenario: Literal['Base', 'Downside', 'Tight credit'] = 'Base',
               delta_bps: int = Query(default=200, ge=0, le=300),
               inflow_factor: Decimal = Query(default=Decimal('.75'), ge=0, le=1),
               capex_factor: Decimal = Query(default=Decimal(1), ge=Decimal('.5'), le=2)):
    run = await fetch_run(request, run_id)
    return comparison(run, as_of or date.fromisoformat(run.get('as_of', run['created_at'][:10])),
                      scenario, delta_bps, inflow_factor, capex_factor)


@router.get('/api/v2/routing')
async def routes(request: Request):
    import os
    result=request.app.state.crusoe.router.view()
    ledger=await request.app.state.repo.get('crusoe-v2-budget-ledger')
    result['budgets']={'run_usd':float(os.getenv('CRUSOE_RUN_BUDGET_USD','2')),
                       'global_soft_usd':float(os.getenv('CRUSOE_GLOBAL_SOFT_BUDGET_USD','40')),
                       'global_spent_usd':ledger['budgets']['estimated_cost_usd'] if ledger else 0}
    return result


@router.post('/api/v2/routing/verify')
async def verify(request: Request):
    from .crusoe import InferenceError
    try:
        return await request.app.state.crusoe.router.verify()
    except InferenceError:
        raise HTTPException(503, 'Crusoe route verification failed; see secure runtime configuration') from None


@router.get('/api/v2/reference/hut')
async def hut():
    from .hut_reference import reference
    return reference()


@router.get('/api/v2/runs/{run_id}/export')
async def export(request: Request, run_id: str, format: Literal['json', 'csv'] = 'json'):
    run = await fetch_run(request, run_id)
    run.pop('source_cache', None)
    if format == 'json':
        return run
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['type', 'id', 'ticker', 'as_of', 'status', 'record_json'])
    import json
    for kind, records in run.get('risk', {}).items():
        for row in records:
            values = [kind, row['id'], row['ticker'], row['as_of'], row['status'], json.dumps(row)]
            writer.writerow(["'"+v if v.startswith(('=', '+', '-', '@', '\t', '\r')) else v for v in values])
    return Response(output.getvalue(), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="financing-risk.csv"'})


@router.post('/api/v2/runs/{run_id}/assumptions')
async def funding_assumptions(request: Request, run_id: str, body: FundingPlan):
    """Explicit user estimates; never promote them to source facts or auditor-approved results."""
    from uuid import uuid4
    run=await fetch_run(request,run_id)
    if body.ticker not in run['tickers']:
        raise HTTPException(422,'Assumptions must concern a selected ticker')
    if run['status'] in ('queued','running'):
        raise HTTPException(409,'Wait for the investigation to finish before adding assumptions')
    item=body.model_dump(mode='json')
    item.update(id='user-assumption:'+str(uuid4()),provenance='assumption',status='user_assumption',
                evidence_ids=[],market_cap_evidence_ids=[])
    for line in item['lines']:
        line.update(provenance='assumption',status='user_assumption',evidence_ids=[])
    FundingPlan.model_validate(item)
    run.setdefault('risk',{k:[] for k in FACT_TYPES})
    run['risk'].setdefault('funding_plans',[]).append(item)
    from .engine import event
    event(run,'user_assumption','Explicit user funding scenario added; not reported financials',
          ticker=body.ticker,horizon_months=body.horizon_months)
    await request.app.state.repo.save(run)
    return item
