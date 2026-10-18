"""Neon's SQL-over-HTTPS protocol; same database and atomic batched transactions.

Endpoint/header protocol follows @neondatabase/serverless 1.2.0 (index.mjs).
Connection strings are only sent in the required HTTPS header, never in URLs/logs.
"""
import json
import re
from datetime import date,datetime
from decimal import Decimal
from urllib.parse import urlsplit
import httpx
from psycopg.types.json import Jsonb
from .connectivity import classify_error,http_policy_allows
from .repository import PostgresRepository


class DatabaseTransportError(RuntimeError):
    def __init__(self,category,status_code=None,sqlstate=None,attempts=None):
        super().__init__('Neon HTTPS '+category)
        self.category=category
        self.status_code=status_code
        self.sqlstate=sqlstate
        self.attempts=attempts or []


def endpoint_for(uri):
    host=urlsplit(uri).hostname or ''
    if not host.endswith('.neon.tech') or not re.fullmatch(r'[a-zA-Z0-9.-]+',host):
        raise ValueError('SQL-over-HTTPS requires a Neon hostname')
    # Current official driver replaces the endpoint-specific first DNS label with api.
    return 'https://api.'+host.split('.',1)[1]+'/sql'


def parameter(value):
    if value is None:
        return None
    if isinstance(value,Jsonb):
        return json.dumps(value.obj)
    if isinstance(value,(dict,list)):
        return json.dumps(value)
    if isinstance(value,(date,datetime)):
        return value.isoformat()
    if isinstance(value,bool):
        return str(value).lower()
    return str(value)


class HTTPResult:
    def __init__(self,connection):
        self.connection=connection
        self.rows=None
    def fetchone(self):
        self.connection.flush()
        return self.rows[0] if self.rows else None
    def __iter__(self):
        self.connection.flush()
        return iter(self.rows or [])


class HTTPConnection:
    def __init__(self,uri):
        self.uri=uri
        self.endpoint=endpoint_for(uri)
        self.pending=[]
    def __enter__(self):
        return self
    def __exit__(self,kind,value,traceback):
        if kind is None:
            self.flush()
        self.pending=[]
    def execute(self,query,params=None):
        if not params and ';' in query:
            result=None
            for statement in query.split(';'):
                if statement.strip():
                    result=self.execute(statement)
            return result
        values=list(params or [])
        position=iter(range(1,len(values)+1))
        try:
            text=re.sub(r'%s',lambda _: '$'+str(next(position)),query)
        except StopIteration:
            raise ValueError('SQL parameter count mismatch') from None
        if text.count('$')<len(values):
            raise ValueError('SQL parameter count mismatch')
        result=HTTPResult(self)
        self.pending.append(({'query':text,'params':[parameter(v) for v in values]},result))
        return result
    def flush(self):
        if not self.pending:
            return
        pending=self.pending
        self.pending=[]
        headers={'Neon-Connection-String':self.uri,'Neon-Raw-Text-Output':'true',
                 'Neon-Array-Mode':'true','Neon-Batch-Isolation-Level':'ReadCommitted'}
        try:
            with httpx.Client(timeout=20,follow_redirects=False) as client:
                response=client.post(self.endpoint,headers=headers,json={'queries':[q for q,_ in pending]})
        except httpx.HTTPError as exc:
            category=classify_error(exc)
            if isinstance(exc,httpx.ProxyError) and http_policy_allows(urlsplit(self.endpoint).hostname) is False:
                category='network_policy_restriction'
            raise DatabaseTransportError(category) from None
        if response.status_code!=200:
            state=None
            if response.status_code==400:
                try:
                    candidate=response.json().get('code','')
                    state=candidate if re.fullmatch('[A-Z0-9]{5}',candidate) else None
                except (ValueError,TypeError):
                    pass
            category='authentication_failure' if response.status_code in (401,403) or state in ('28P01','28000') else 'http_'+str(response.status_code)
            raise DatabaseTransportError(category,response.status_code,state)
        try:
            results=response.json()['results']
            if len(results)!=len(pending):
                raise ValueError()
            for (_,cursor),result in zip(pending,results):
                fields=result.get('fields',[])
                rows=[]
                for row in result.get('rows',[]):
                    decoded=[]
                    for index,value in enumerate(row):
                        oid=fields[index].get('dataTypeID') if index<len(fields) else None
                        if value is not None and oid in (114,3802):
                            value=json.loads(value) if isinstance(value,str) else value
                        elif value is not None and oid==16:
                            value=value in (True,'t','true')
                        elif value is not None and oid in (20,21,23):
                            value=int(value)
                        elif value is not None and oid==1700:
                            value=Decimal(value)
                        decoded.append(value)
                    rows.append(tuple(decoded))
                cursor.rows=rows
        except (KeyError,ValueError,TypeError,IndexError):
            raise DatabaseTransportError('invalid_protocol_response') from None


class NeonHTTPRepository(PostgresRepository):
    mode='Neon/Postgres over HTTPS'
    def __init__(self,uri):
        super().__init__(uri)
        self.endpoint=endpoint_for(uri)
    def _connection(self):
        return HTTPConnection(self.url)


class AutoNeonRepository:
    def __init__(self,uri):
        self.url=uri
        self.active=None
        self.connection_attempts=[]
    @property
    def mode(self):
        return self.active.mode if self.active else 'Neon connection pending'
    async def initialize(self):
        first=PostgresRepository(self.url)
        try:
            await first.initialize()
            self.active=first
            self.connection_attempts.append({'transport':'postgres','status':'connected'})
            return
        except Exception as exc:
            category=classify_error(exc)
            self.connection_attempts.append({'transport':'postgres','category':category})
            if category not in ('dns_resolution_failure','tcp_connection_failure','connection_failure','connection_timeout'):
                raise
        second=NeonHTTPRepository(self.url)
        try:
            await second.initialize()
            self.active=second
            self.connection_attempts.append({'transport':'neon_http','status':'connected'})
        except Exception as exc:
            category=getattr(exc,'category',classify_error(exc))
            self.connection_attempts.append({'transport':'neon_http','category':category})
            raise DatabaseTransportError(category,attempts=self.connection_attempts) from None
    async def heartbeat(self):
        await self.active.heartbeat()
    async def save(self,run):
        await self.active.save(run)
    async def get(self,run_id):
        return await self.active.get(run_id)
    async def all(self):
        return await self.active.all()
    async def close(self):
        if self.active:
            await self.active.close()
