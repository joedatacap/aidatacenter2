import asyncio,json
from datetime import datetime,timedelta,timezone
from email.utils import format_datetime
import httpx
import pytest
from neocloud.crusoe import Crusoe,InferenceError,backoff_delay,retry_seconds
from neocloud.engine import Engine,new_run,task
from neocloud.repository import MemoryRepository


def test_model_fallback_is_discovered_budgeted_and_recorded(monkeypatch):
    primary='nvidia/Nemotron-3.5-Lightning-30B-A3B'
    fallback='nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B'
    monkeypatch.setenv('CRUSOE_API_KEY','test-key')
    monkeypatch.setenv('CRUSOE_MODEL',primary)
    monkeypatch.setenv('CRUSOE_FALLBACK_MODELS','not-discovered,'+fallback)
    real=httpx.AsyncClient;calls=[]
    def handler(request):
        model=json.loads(request.content)['model'];calls.append(model)
        if model==primary:return httpx.Response(503)
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'{"summary":"supported test response"}'}}],'usage':{'prompt_tokens':10,'completion_tokens':8}})
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:real(transport=httpx.MockTransport(handler),**kw))
    async def check():
        model=Crusoe();model.available_models=[primary,fallback]
        run=new_run(['CRWV']);run['tasks'][0]['status']='running'
        engine=Engine(MemoryRepository(),model)
        with pytest.raises(InferenceError):await engine.call(run,'test',{})
        result=await engine.call(run,'test',{})
        assert result['summary']=='supported test response'
        assert calls==[primary,fallback]
        assert run['budgets']['llm_calls']==2
        attempts=run['tasks'][0]['inference_attempts']
        assert [a['status'] for a in attempts]==['failed','succeeded']
        assert attempts[1]['model']==fallback
        assert attempts[1]['usage']['completion_tokens']==8
        assert 'test-key' not in str(run)
    asyncio.run(check())


def test_retry_after_http_date_and_jitter_are_respected(monkeypatch):
    monkeypatch.setattr('neocloud.crusoe.random.uniform',lambda a,b:b/2)
    assert backoff_delay(2)>backoff_delay(1)
    assert backoff_delay(1,900)==900
    stamp=format_datetime(datetime.now(timezone.utc)+timedelta(seconds=120),usegmt=True)
    assert 118<=retry_seconds(stamp)<=120


def test_checkpoint_recovery_avoids_duplicate_inference():
    class NeverCall:
        async def json(self,*args):raise AssertionError('Network inference repeated')
    async def check():
        repo=MemoryRepository();run=new_run(['CRWV'])
        run['status']='running';run['budgets']['llm_calls']=1
        run['tasks'][0].update(status='running',response_checkpoint={'tasks':[{'role':'debt','ticker':'CRWV','goal':'Read primary source'}],'reason':'plan'})
        await repo.save(run)
        engine=Engine(repo,NeverCall());await engine.recover()
        restored=await repo.get(run['id']);await engine.step(restored)
        assert restored['budgets']['llm_calls']==1
        assert restored['tasks'][0]['status']=='completed'
        assert restored['tasks'][1]['role']=='debt'
        assert any(e['kind']=='inference_recovered' for e in restored['events'])
    asyncio.run(check())


def test_late_manager_failure_returns_grounded_partial_dossier():
    class Broken:
        async def json(self,*args):raise RuntimeError('private-error-body')
    async def check():
        run=new_run(['CRWV','NBIS']);run['tasks'][0]['status']='completed'
        research=task('debt','CRWV','Read filing',run['tasks'][0]['id'])
        research.update(status='completed',result={'summary':'Primary source blocked'})
        run['tasks'].append(research)
        engine=Engine(MemoryRepository(),Broken())
        for _ in range(3):await engine.step(run)
        assert run['status']=='partially_completed'
        assert run['outcome']=='partially_completed'
        assert run['dossier']['verified_information']==[]
        assert any('unknown' in c for c in run['dossier']['concerns'])
        assert 'private-error-body' not in str(run)
        assert research['parent_task_id']==run['tasks'][0]['id']
    asyncio.run(check())

def test_replanning_retains_auditor_ancestry_after_interleaved_tasks():
    class Manager:
        async def json(self,instruction,context):
            current=next(t for t in context['tasks'] if t['role']=='manager' and t['status']=='running')
            return {'tasks':[{'role':'debt','ticker':'CRWV','goal':'Verify the auditor hedge concern','parent_task_id':current['id']}],'reason':'Auditor identified missing hedge dates'}
    async def check():
        run=new_run(['CRWV']);run['tasks'][0]['status']='completed'
        auditor=task('auditor','CRWV','Check hedges',run['tasks'][0]['id'])
        auditor.update(status='completed',result={'concerns':['Hedge dates unknown']})
        run['tasks'].append(auditor)
        other=task('followup','CRWV','Earlier unrelated check',run['tasks'][0]['id'])
        other.update(status='completed',result={'summary':'Limited sources'})
        run['tasks'].append(other)
        await Engine(MemoryRepository(),Manager()).step(run)
        child=run['tasks'][-1];manager=run['tasks'][-2]
        assert manager['parent_task_id']==auditor['id']
        assert child['parent_task_id']==manager['id']
        assert any(e['kind']=='recursive_child' and e['auditor_task_id']==auditor['id'] for e in run['events'])
    asyncio.run(check())
