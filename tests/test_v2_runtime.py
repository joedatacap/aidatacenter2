import asyncio
import json
import os
from datetime import date
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from neocloud.app import app
from neocloud.crusoe import Crusoe, InferenceError
from neocloud.routing import RoleRouter, GLM, FLASH, DEEP, CHEAP, NANO
from neocloud.engine import BudgetStop
from neocloud.v2_engine import new_v2_run, V2Engine
from neocloud.repository import MemoryRepository, PostgresRepository


def test_routes_require_discovery_and_real_structured_probe_and_fallback(monkeypatch):
    monkeypatch.setenv('CRUSOE_API_KEY', 'test-secret')
    real = httpx.AsyncClient
    attempts = []
    def handler(request):
        if request.method == 'GET':
            return httpx.Response(200, json={'data': [{'id': m} for m in (GLM, FLASH, DEEP, CHEAP, NANO)]})
        model = json.loads(request.content)['model']
        attempts.append(model)
        if model == GLM:
            return httpx.Response(404)
        return httpx.Response(200, json={'choices': [{'message': {'content': '{"connectivity":"ok"}'}, 'finish_reason': 'stop'}]})
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    async def check():
        c = Crusoe(); r = RoleRouter(c)
        with pytest.raises(InferenceError):
            r.select('manager')
        await r.verify()
        assert r.select('manager') == FLASH
        assert r.select('debt') == DEEP
        assert r.select('triage') == CHEAP
        assert r.select('auditor') == FLASH
        c.note_failure(DEEP, InferenceError('rate limited', 429, 60))
        assert r.select('debt') == FLASH
        assert all(m in (GLM, FLASH, DEEP, CHEAP, NANO) for m in attempts)
    asyncio.run(check())


def test_dollar_budget_blocks_before_network_and_survives_restart(monkeypatch):
    monkeypatch.setenv('CRUSOE_API_KEY', 'test-secret')
    monkeypatch.setenv('CRUSOE_RUN_BUDGET_USD', '0.000001')
    async def check():
        c = Crusoe(); c.router = RoleRouter(c); c.router.verified = {GLM: True}
        run = new_v2_run(['CRWV']); run['tasks'][0]['status'] = 'running'
        repo = MemoryRepository(); engine = V2Engine(repo, c)
        with pytest.raises(BudgetStop):
            await engine.call(run, 'instructions', {})
        assert run['budgets']['llm_calls'] == 0
        monkeypatch.setenv('CRUSOE_RUN_BUDGET_USD', '2')
        ledger = new_v2_run([]); ledger.update(id='crusoe-v2-budget-ledger', status='telemetry', tasks=[], budgets={'estimated_cost_usd': 40})
        await repo.save(ledger)
        with pytest.raises(BudgetStop):
            await V2Engine(repo, c).call(run, 'instructions', {})
        assert run['budgets']['llm_calls'] == 0
    asyncio.run(check())


def test_v2_offline_demo_has_manager_audit_followup_and_hut_comparison():
    async def check():
        run = new_v2_run(['CRWV', 'HUT'], 'simulated', date(2026, 10, 17))
        engine = V2Engine(MemoryRepository(), None)
        for _ in range(25):
            await engine.step(run)
            if run['status'] not in ('queued', 'running'):
                break
        assert run['status'] == 'completed'
        followup = next(t for t in run['tasks'] if t['role'] == 'followup')
        assert next(t for t in run['tasks'] if t['id'] == followup['parent_task_id'])['role'] == 'auditor'
        assert 'SIMULATED' in run['dossier']['summary']
        assert len(run['tasks']) <= 18
    asyncio.run(check())


def test_v2_api_demo_scenario_exports_refresh_and_v1_remain_available(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('CRUSOE_API_KEY', raising=False)
    with TestClient(app) as c:
        for path in ('/', '/v1', '/v2'):
            assert c.get(path).status_code == 200
        assert 'HUT' in c.get('/api/companies').json()
        assert c.post('/api/v2/runs', json={'tickers': ['CRWV', 'HUT']}).status_code == 503
        r = c.post('/api/v2/runs', json={'tickers': ['CRWV', 'HUT'], 'mode': 'simulated', 'as_of': '2026-10-17'})
        assert r.status_code == 202
        run_id = r.json()['id']
        base = c.get(f'/api/v2/runs/{run_id}/risk').json()['tickers']['CRWV']['funding'][0]
        tight = c.get(f'/api/v2/runs/{run_id}/risk?scenario=Tight%20credit').json()['tickers']['CRWV']['funding'][0]
        assert float(tight['unfunded_gap']) > float(base['unfunded_gap'])
        assert c.get(f'/api/v2/runs/{run_id}/risk?inflow_factor=2').status_code == 422
        assert c.get(f'/api/v2/runs/{run_id}/risk?delta_bps=-1').status_code == 422
        exported = c.get(f'/api/v2/runs/{run_id}/export').json()
        assert 'source_cache' not in exported
        assert exported['version'] == 2
        assert c.get(f'/api/v2/runs/{run_id}/export?format=csv').headers['content-type'].startswith('text/csv')
        assert c.get('/api/v2/reference/hut').json()['evidence']
        assert c.get('/api/v2/routing').json()['routes']['manager']['verified'] == []


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Dedicated disposable TLS Postgres required')
def test_v2_migration_idempotency_v1_upgrade_persistence_and_sql_projections():
    import psycopg
    async def check():
        repo = PostgresRepository(os.environ['TEST_DATABASE_URL'])
        await repo.initialize()
        try:
            run = new_v2_run(['HUT'], 'simulated', date(2026, 10, 17))
            await repo.save(run)
            await repo.save(run)
            with repo._connection() as conn:
                sql = Path('neocloud/migrations/002_financing_risk.sql').read_text()
                conn.execute(sql); conn.execute(sql)
                assert conn.execute('SELECT count(*) FROM v2_financing_records WHERE run_id=%s', (run['id'],)).fetchone()[0] == sum(len(x) for x in run['risk'].values())
                assert conn.execute("SELECT count(*) FROM schema_migrations WHERE version='002_financing_risk'").fetchone()[0] == 1
            await repo.close()
            restored = PostgresRepository(os.environ['TEST_DATABASE_URL'])
            await restored.initialize()
            try:
                saved = await restored.get(run['id'])
                assert saved['risk'] == run['risk']
                assert saved['as_of'] == '2026-10-17'
            finally:
                await restored.close()
        finally:
            await repo.close()
    asyncio.run(check())


def test_user_assumptions_remain_explicit_and_cannot_claim_auditor_approval(monkeypatch):
    import time
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('CRUSOE_API_KEY', raising=False)
    with TestClient(app) as c:
        run_id=c.post('/api/v2/runs',json={'tickers':['CRWV'],'mode':'simulated','as_of':'2026-10-17'}).json()['id']
        for _ in range(100):
            run=c.get('/api/runs/'+run_id).json()
            if run['status'] not in ('queued','running'): break
            time.sleep(.1)
        plan=run['risk']['funding_plans'][0]
        plan.update(status='auditor_verified',provenance='live',evidence_ids=['forged'])
        result=c.post(f'/api/v2/runs/{run_id}/assumptions',json=plan)
        assert result.status_code==200
        saved=result.json()
        assert saved['status']=='user_assumption' and saved['provenance']=='assumption'
        assert saved['evidence_ids']==[]
        assert all(x['evidence_ids']==[] for x in saved['lines'])
        risk=c.get(f'/api/v2/runs/{run_id}/risk').json()['tickers']['CRWV']['funding'][0]
        assert risk['input_status']=='user_assumption'
