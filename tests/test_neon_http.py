import asyncio,json,os,re
import httpx
import psycopg
import pytest
from neocloud.engine import new_run
from neocloud.neon_http import endpoint_for,HTTPConnection,NeonHTTPRepository,DatabaseTransportError

URI='postgresql://test_role:test_password@ep-test-pooler.c-7.us-east-2.aws.neon.tech/testdb?sslmode=require'


def test_https_endpoint_matches_official_driver_and_rejects_other_hosts():
    assert endpoint_for(URI)=='https://api.c-7.us-east-2.aws.neon.tech/sql'
    with pytest.raises(ValueError):endpoint_for('postgresql://user:pass@untrusted.example/db')


def test_https_batches_are_parameterized_and_connection_string_stays_in_header(monkeypatch):
    real=httpx.Client;requests=[]
    def handler(request):
        requests.append(request)
        body=json.loads(request.content)
        assert 'test_password' not in str(request.url)
        assert 'test_password' not in request.content.decode()
        assert request.headers['Neon-Connection-String']==URI
        assert body['queries'][0]=={'query':'SELECT $1','params':['value']}
        return httpx.Response(200,json={'results':[{'fields':[{'dataTypeID':25}],'rows':[['value']]}]})
    monkeypatch.setattr(httpx,'Client',lambda **kw:real(transport=httpx.MockTransport(handler),**kw))
    with HTTPConnection(URI) as conn:
        assert conn.execute('SELECT %s',('value',)).fetchone()==('value',)
    assert len(requests)==1


def test_https_errors_do_not_expose_credentials_or_provider_error_body(monkeypatch):
    real=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kw:real(transport=httpx.MockTransport(lambda r:httpx.Response(400,json={'code':'28P01','message':'private database credentials'})),**kw))
    with pytest.raises(DatabaseTransportError) as failure:
        with HTTPConnection(URI) as conn:conn.execute('SELECT 1').fetchone()
    assert failure.value.category=='authentication_failure'
    assert 'private database credentials' not in str(failure.value)
    assert 'test_password' not in str(failure.value)


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'),reason='Dedicated TLS Postgres test database required')
def test_https_repository_protocol_bridge_roundtrip_and_atomic_rollback(monkeypatch):
    """Mock only Neon's wire protocol; execute all SQL against real CI TLS Postgres."""
    real=httpx.Client
    def handler(request):
        queries=json.loads(request.content)['queries'];results=[]
        try:
            with psycopg.connect(os.environ['TEST_DATABASE_URL']) as conn:
                for query in queries:
                    sql=re.sub(r'\$\d+','%s',query['query'])
                    cursor=conn.execute(sql,query['params'])
                    fields=[{'name':d.name,'dataTypeID':d.type_code} for d in cursor.description or []]
                    rows=[]
                    if cursor.description:
                        for row in cursor:
                            rows.append([None if v is None else json.dumps(v) if isinstance(v,(dict,list)) else ('t' if v else 'f') if isinstance(v,bool) else str(v) for v in row])
                    results.append({'fields':fields,'rows':rows})
            return httpx.Response(200,json={'results':results})
        except psycopg.Error as exc:
            return httpx.Response(400,json={'code':exc.sqlstate,'message':'SQL rejected in test bridge'})
    monkeypatch.setattr(httpx,'Client',lambda **kw:real(transport=httpx.MockTransport(handler),**kw))
    async def check():
        repo=NeonHTTPRepository(URI)
        await repo.initialize()
        try:
            run=new_run(['CRWV']);await repo.save(run)
            assert (await repo.get(run['id']))['tasks']==run['tasks']
            invalid=new_run(['CRWV'])
            invalid['instruments']=[{'instrument_id':'invalid','ticker':'NOT_A_COMPANY','currency':'USD'}]
            with pytest.raises(DatabaseTransportError):await repo.save(invalid)
            assert await repo.get(invalid['id']) is None
        finally:await repo.close()
    asyncio.run(check())
