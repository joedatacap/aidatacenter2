import asyncio
import httpx
import pytest
from neocloud.crusoe import Crusoe,InferenceError

def client(monkeypatch,payload,status=200,headers=None):
    monkeypatch.setenv('CRUSOE_API_KEY','test-key-never-log')
    monkeypatch.setenv('CRUSOE_MODEL','nvidia/Nemotron-3.5-Lightning-30B-A3B')
    real_client=httpx.AsyncClient
    def respond(request):
        return httpx.Response(status,json=payload,headers=headers)
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:real_client(transport=httpx.MockTransport(respond),**kwargs))
    return Crusoe()

def test_fenced_model_json_is_accepted_without_treating_prose_as_json(monkeypatch):
    model=client(monkeypatch,{'choices':[{'finish_reason':'stop','message':{'content':'```json\n{"ok":true}\n```'}}]})
    assert asyncio.run(model.json('test',{}))=={'ok':True}

def test_truncated_json_is_rejected_even_if_parseable(monkeypatch):
    model=client(monkeypatch,{'choices':[{'finish_reason':'length','message':{'content':'{"ok":true}'}}]})
    with pytest.raises(InferenceError,match='output-token budget'):
        asyncio.run(model.json('test',{}))

def test_rate_limit_metadata_is_safe_and_bounded(monkeypatch):
    model=client(monkeypatch,{'error':'sensitive-server-body'},429,{'Retry-After':'900'})
    with pytest.raises(InferenceError) as result:
        asyncio.run(model.json('test',{}))
    assert result.value.status_code==429
    assert result.value.retry_after==30
    assert 'sensitive-server-body' not in str(result.value)
    assert 'test-key-never-log' not in str(result.value)
