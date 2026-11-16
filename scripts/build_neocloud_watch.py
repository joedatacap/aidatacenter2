"""Build connected static routes and a self-contained offline Neocloud Watch.

No public backend, credentials, quote API or production deployment is involved.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse
from neocloud.directory import build_directory
from neocloud.website_v2 import build_website_v2
from neocloud.watch import build_watch

ROOT=Path(__file__).resolve().parents[1]


def load_snapshot():
    directory=build_directory(json.loads((ROOT/'neocloud/data/debt_directory.json').read_text()))
    website=build_website_v2(directory,json.loads((ROOT/'neocloud/data/website_v2.json').read_text()))
    files=[json.loads(path.read_text()) for path in sorted((ROOT/'neocloud/data').glob('watch_*.json')) if path.name not in ('watch_import_audit.json',)]
    audit_path=ROOT/'neocloud/data/watch_import_audit.json'
    audit=json.loads(audit_path.read_text()) if audit_path.exists() else None
    return build_watch(website,files,import_audit=audit)


def base_path(value):
    if not value.startswith('/') or any(part in ('.','..') for part in value.split('/')) or urlparse(value).netloc or '?' in value or '#' in value or '\\' in value:
        raise ValueError('Base path must be an absolute URL path without traversal/query/fragment')
    if not re.fullmatch(r'/[A-Za-z0-9/_-]*',value):raise ValueError('Unsupported base path')
    return value.rstrip('/')+'/'


def build(*,base='/',output=None):
    base=base_path(base)
    source=ROOT/'watch-preview'
    target=Path(output) if output else ROOT/'work/neocloud-watch-site'
    target.mkdir(parents=True,exist_ok=True)
    data=load_snapshot()
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    html=(source/'index.html').read_text()
    embed='<script id="watch-data" type="application/json">'+encoded+'</script>'
    html=html.replace('</body>',embed+'</body>')
    hosted=html.replace('__WATCH_BASE__',base)
    hosted=hosted.replace('href="./watch.css"',f'href="{base}watch.css"').replace('src="./watch.js"',f'src="{base}watch.js"')
    routes=['','overview','financing','earnings','buildout']+['companies/'+c['id'] for c in data['companies']]
    for route in routes:
        destination=target/route/'index.html';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(hosted)
    for asset in ('watch.css','watch.js'):
        shutil.copyfile(source/asset,target/asset)
    (target/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (target/'_headers').write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: DENY\n  Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'\n")
    # Every route is a real static directory; no host-specific SPA rewrite is needed.
    offline=html.replace('__WATCH_BASE__','./').replace('name="watch-offline" content="false"','name="watch-offline" content="true"')
    offline=offline.replace('<link rel="stylesheet" href="./watch.css">','<style>'+(source/'watch.css').read_text()+'</style>')
    js=(source/'watch.js').read_text().replace('</script','<\\/script')
    offline=re.sub(r'<script src="\./watch\.js"[^>]*></script>','',offline)
    offline=offline.replace('</body>','<script>'+js+'</script></body>')
    artifact=ROOT/'work/Neocloud-Watch-V2.html';artifact.write_text(offline)
    return {'site':str(target),'offline':str(artifact),'companies':len(data['companies']),'routes':len(routes),'base_path':base}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-path',default='/');parser.add_argument('--output')
    args=parser.parse_args()
    print(json.dumps(build(base=args.base_path,output=args.output),indent=2))
