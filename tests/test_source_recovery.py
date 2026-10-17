import asyncio
import httpx
from neocloud import sources


def transport(monkeypatch,handler):
    real=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:real(transport=httpx.MockTransport(handler),**kw))


def test_failed_sec_source_uses_official_alternative_and_cache(monkeypatch):
    urls=['https://www.sec.gov/test.htm','https://investors.coreweave.com/news/test']
    monkeypatch.setitem(sources.SOURCES,'CRWV',urls)
    calls=[]
    def handler(request):
        calls.append(str(request.url))
        if request.url.host=='www.sec.gov':
            return httpx.Response(404)
        return httpx.Response(200,headers={'content-type':'text/html'},text='<title>Official test source</title><p>Debt outstanding as of June 30, 2026 is USD 100 million.</p>')
    transport(monkeypatch,handler)
    async def check():
        cache={}
        first=await sources.source_bundle('CRWV',[urls[0]],cache)
        assert [s['status'] for s in first]==['unavailable','retrieved']
        assert first[0]['category']=='http_404'
        second=await sources.source_bundle('CRWV',urls,cache)
        assert all(s['cache_hit'] for s in second)
        assert len(calls)==2
    asyncio.run(check())


def test_redirect_keeps_lineage_and_disallowed_host_is_never_requested(monkeypatch):
    calls=[]
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302,headers={'location':'https://127.0.0.1/private'})
    transport(monkeypatch,handler)
    result=asyncio.run(sources.retrieve('https://www.sec.gov/test'))
    assert result['category']=='unapproved_redirect'
    assert calls==['https://www.sec.gov/test']


def test_policy_denial_is_classified_and_not_retried_for_same_host(monkeypatch):
    urls=['https://www.sec.gov/a','https://www.sec.gov/b']
    monkeypatch.setitem(sources.SOURCES,'CRWV',urls)
    monkeypatch.setattr(sources,'http_policy_allows',lambda host:False)
    calls=[]
    def handler(request):
        calls.append(str(request.url))
        raise httpx.ProxyError('sensitive-proxy-body')
    transport(monkeypatch,handler)
    results=asyncio.run(sources.source_bundle('CRWV',urls,{}))
    assert len(calls)==1
    assert all(r['category']=='network_policy_restriction' for r in results)
    assert results[1]['skipped_known_host_failure']
    assert 'sensitive-proxy-body' not in str(results)
