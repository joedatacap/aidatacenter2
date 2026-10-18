"""Bounded diagnostics. Outputs categories and hostnames, never credentials/URIs."""
import argparse
import asyncio
import json
import os
import socket
from pathlib import Path
from urllib.parse import urlsplit
import httpx
import psycopg
from neocloud.catalog import SOURCES
from neocloud.connectivity import classify_error,database_configuration,http_policy_allows
from neocloud.crusoe import Crusoe,InferenceError
from neocloud.neon_http import NeonHTTPRepository


async def main(include_inference,output):
    report={'configuration':{'crusoe_key_present':bool(os.getenv('CRUSOE_API_KEY')),
                            'database':database_configuration(os.getenv('DATABASE_URL'))},'checks':[]}
    def record(item):
        report['checks'].append(item)
        print(json.dumps(item),flush=True)
    async def source(url):
        host=urlsplit(url).hostname
        try:
            async with httpx.AsyncClient(timeout=10,follow_redirects=False) as client:
                async with client.stream('GET',url,headers={'User-Agent':os.getenv('SEC_USER_AGENT','NeoCloudResearch research@example.com')}) as response:
                    status=response.status_code
            record({'service':host,'http_status':status,'category':'success' if status==200 else 'http_'+str(status)})
        except httpx.HTTPError as exc:
            category=classify_error(exc)
            if isinstance(exc,httpx.ProxyError) and http_policy_allows(host) is False:
                category='network_policy_restriction'
            record({'service':host,'category':category,'error_type':type(exc).__name__})
    async def inference():
        client=Crusoe()
        try:
            if include_inference:
                record({'service':'Crusoe inference','category':'success',**await client.verify()})
            else:
                record({'service':'Crusoe discovery','category':'success','models':await client.models()})
        except InferenceError as exc:
            record({'service':'Crusoe','category':exc.category,'http_status':exc.status_code})
    async def database():
        uri=os.getenv('DATABASE_URL')
        if not uri:
            record({'service':'Neon','category':'missing_configuration'});return
        config=database_configuration(uri)
        if config.get('configuration_error') or not config.get('host') or not config.get('postgres_scheme') or not config.get('tls_required'):
            record({'service':'Neon','category':'incorrect_configuration'});return
        part=urlsplit(uri)
        try:
            await asyncio.wait_for(asyncio.to_thread(socket.getaddrinfo,part.hostname,part.port or 5432,type=socket.SOCK_STREAM),timeout=8)
            record({'service':'Neon executor DNS','category':'success','host':part.hostname})
        except Exception as exc:
            record({'service':'Neon executor DNS','category':'dns_resolution_failure','error_type':type(exc).__name__})
        def postgres():
            try:
                with psycopg.connect(uri,connect_timeout=6) as connection:
                    return {'service':'Neon Postgres','category':'success','query_ok':connection.execute('SELECT 1').fetchone()[0]==1}
            except Exception as exc:
                return {'service':'Neon Postgres','category':classify_error(exc)}
        record(await asyncio.to_thread(postgres))
        def https():
            try:
                repo=NeonHTTPRepository(uri)
                with repo._connection() as connection:
                    return {'service':'Neon HTTPS','category':'success','query_ok':connection.execute('SELECT 1').fetchone()[0]==1}
            except Exception as exc:
                return {'service':'Neon HTTPS','category':getattr(exc,'category',classify_error(exc))}
        record(await asyncio.to_thread(https))
    await asyncio.gather(inference(),database(),*(source(url) for url in
        [SOURCES['CRWV'][0],SOURCES['CRWV'][1],SOURCES['NBIS'][0],'https://iren.com','https://ir.bitdeer.com']))
    if output:
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-inference',action='store_true',help='Make a bounded real structured-JSON verification request')
    parser.add_argument('--output',help='Write sanitized JSON diagnostics')
    args=parser.parse_args()
    asyncio.run(main(args.include_inference,args.output))
