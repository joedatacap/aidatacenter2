import asyncio
from datetime import datetime, timedelta, timezone
from itertools import combinations
import pytest
from neocloud.engine import Engine, new_run, MAX_TASKS, MAX_CALLS
from neocloud.repository import MemoryRepository
from neocloud.fixtures import bundle

class NoLiveCalls:
    async def json(self,*args):
        raise AssertionError("Simulated mode must never call Crusoe")

@pytest.mark.parametrize("tickers",list(combinations(["CRWV","NBIS","IREN","BTDR"],2)))
def test_simulated_comparison_has_parent_child_recursion_and_no_live_claims(tickers):
    async def check():
        repo = MemoryRepository()
        engine = Engine(repo,NoLiveCalls())
        run = new_run(list(tickers),"simulated")
        for _ in range(30):
            await engine.step(run)
            if run["status"] not in ("queued","running"):
                break
        assert run["status"]=="completed"
        recursive = [e for e in run["events"] if e["kind"]=="recursive_child"]
        assert recursive and all(e["initiated_by"]=="simulated model" for e in recursive)
        parent = next(t for t in run["tasks"] if t["id"]==recursive[0]["parent_task_id"])
        assert parent["role"]=="auditor"
        assert run["dossier"]
        assert len(run["tasks"]) <= MAX_TASKS
        assert run["budgets"]["llm_calls"] <= MAX_CALLS
        assert all(e["provenance"]=="fixture" for e in run["evidence"])
        assert all(i["outstanding_principal"] is None for i in run["instruments"])
        assert not run["market_observations"]
    asyncio.run(check())

def test_recovery_retries_running_task_without_resetting_reserved_budget():
    async def check():
        repo = MemoryRepository()
        run = new_run(["IREN"])
        run["status"]="running"
        run["tasks"][0]["status"]="running"
        run["budgets"]["llm_calls"]=4
        await repo.save(run)
        await Engine(repo,None).recover()
        recovered = await repo.get(run["id"])
        assert recovered["tasks"][0]["status"]=="pending"
        assert recovered["tasks"][0]["retries"]==1
        assert recovered["budgets"]["llm_calls"]==4
    asyncio.run(check())

def test_unmatched_and_fixture_excerpts_cannot_become_live_evidence():
    run = new_run(["CRWV"])
    current = run["tasks"][0]
    response = {"evidence":[{"source_index":0,"excerpt":bundle("CRWV")[0]["text"],"claim":"not live"}]}
    Engine(MemoryRepository(),None).accept_findings(run,current,response,bundle("CRWV"))
    assert not run["evidence"]
    assert run["events"][-1]["kind"]=="evidence_rejected"

def test_permanent_error_retries_at_most_twice_and_errors_are_sanitized():
    class BrokenModel:
        async def json(self,*args):
            raise RuntimeError("secret-must-not-appear")
    async def check():
        run = new_run(["BTDR"])
        engine = Engine(MemoryRepository(),BrokenModel())
        for _ in range(3):
            await engine.step(run)
        assert run["tasks"][0]["status"]=="failed"
        assert run["tasks"][0]["retries"]==3
        assert "secret-must-not-appear" not in str(run)
    asyncio.run(check())

def test_expired_run_stops_without_another_call():
    async def check():
        run = new_run(["NBIS"])
        run["started_at"]=(datetime.now(timezone.utc)-timedelta(seconds=301)).isoformat()
        await Engine(MemoryRepository(),NoLiveCalls()).step(run)
        assert run["status"]=="budget_exhausted"
        assert run["budgets"]["llm_calls"]==0
    asyncio.run(check())

def test_exhausted_call_budget_stops_without_another_call():
    async def check():
        run = new_run(["NBIS"])
        run["budgets"]["llm_calls"]=MAX_CALLS
        await Engine(MemoryRepository(),NoLiveCalls()).step(run)
        assert run["status"]=="budget_exhausted"
        assert run["budgets"]["llm_calls"]==MAX_CALLS
    asyncio.run(check())

def test_rate_limit_backoff_does_not_spin_or_spawn_more_tasks():
    from neocloud.crusoe import InferenceError
    class LimitedModel:
        async def json(self,*args):
            raise InferenceError('Crusoe inference HTTP 429',429,15)
    async def check():
        run=new_run(['NBIS'])
        engine=Engine(MemoryRepository(),LimitedModel())
        await engine.step(run)
        assert run['tasks'][0]['next_attempt_at']
        assert run['budgets']['llm_calls']==1
        await engine.step(run)
        assert run['budgets']['llm_calls']==1
        assert len(run['tasks'])==1
    asyncio.run(check())

def test_manager_cannot_claim_completion_without_a_dossier():
    class PrematureModel:
        async def json(self,*args):
            return {'finish':True,'reason':'No sources'}
    async def check():
        run=new_run(['BTDR'])
        engine=Engine(MemoryRepository(),PrematureModel())
        for _ in range(3):
            await engine.step(run)
        assert run['status']=='failed'
        assert run['tasks'][0]['retries']==3
        assert 'validation_feedback' in run['tasks'][0]['result']
        assert run['stop_reason']=='Research manager failed after two retries'
    asyncio.run(check())

def test_specialized_debt_child_can_follow_auditor_through_manager():
    from neocloud.engine import task,audit_ancestor
    run=new_run(['CRWV'])
    auditor=task('auditor','CRWV','Challenge hedge disclosure',run['tasks'][0]['id'])
    auditor['status']='completed'
    auditor['result']={'concerns':['Hedge effective date missing']}
    run['tasks'].append(auditor)
    manager=task('manager',None,'Choose targeted followup',auditor['id'])
    run['tasks'].append(manager)
    specialist=task('debt','CRWV','Verify swap effective date in filing',manager['id'])
    assert audit_ancestor(run,specialist)==auditor['id']
    run['tasks'].append(specialist)
    assert Engine(MemoryRepository(),None).context(run)['followup_required_for_auditors']==[]
