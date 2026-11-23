"""Build connected static routes and a self-contained offline Neocloud Watch.

No public backend, credentials, quote API or production deployment is involved.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse
from neocloud.directory import build_directory
from neocloud.website_v2 import build_website_v2
from neocloud.watch import build_watch
from neocloud.data_quality import enrich_data_quality, require_complete_data_quality

ROOT=Path(__file__).resolve().parents[1]

# Sites static hosting does not apply _headers. A document policy also works
# there. frame-ancestors is honored only when delivered as an HTTP header.
DOCUMENT_CSP = (
    "default-src 'none'; script-src 'self' https://widgets.tradingview-widget.com; "
    "frame-src https://widgets.tradingview-widget.com; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https://s3-symbol-logo.tradingview.com; connect-src 'self'; "
    "base-uri 'none'; form-action 'none'; object-src 'none'"
)


def hosted_document(html):
    charset = '<meta charset="utf-8">'
    if html.count(charset) != 1:
        raise ValueError('Expected a single UTF-8 declaration before hosted resources')
    return html.replace(charset, charset + '\n<meta http-equiv="Content-Security-Policy" content="' + DOCUMENT_CSP + '">')



def load_snapshot():
    directory=build_directory(json.loads((ROOT/'neocloud/data/debt_directory.json').read_text()))
    website=build_website_v2(directory,json.loads((ROOT/'neocloud/data/website_v2.json').read_text()))
    files=[json.loads(path.read_text()) for path in sorted((ROOT/'neocloud/data').glob('watch_*.json')) if path.name not in ('watch_import_audit.json',)]
    audit_path=ROOT/'neocloud/data/watch_import_audit.json'
    audit=json.loads(audit_path.read_text()) if audit_path.exists() else None
    baseline=build_watch(website,files,import_audit=audit)
    sizes_path=ROOT/'neocloud/data/quality_sizes.json'
    reviews_path=ROOT/'neocloud/data/quality_reviews.json'
    sizes=json.loads(sizes_path.read_text()) if sizes_path.exists() else None
    reviews=json.loads(reviews_path.read_text()) if reviews_path.exists() else None
    return enrich_data_quality(baseline,sizes,reviews)


def base_path(value):
    if not value.startswith('/') or any(part in ('.','..') for part in value.split('/')) or urlparse(value).netloc or '?' in value or '#' in value or '\\' in value:
        raise ValueError('Base path must be an absolute URL path without traversal/query/fragment')
    if not re.fullmatch(r'/[A-Za-z0-9/_-]*',value):raise ValueError('Unsupported base path')
    return value.rstrip('/')+'/'


def embedded_json(element_id, payload):
    serialized = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    return f'<script id="{element_id}" type="application/json">{serialized}</script>'


def build(*,base='/',output=None,release=False):
    base=base_path(base)
    source=ROOT/'watch-preview'
    if release and output is None:
        (ROOT / 'work').mkdir(exist_ok=True)
        output = tempfile.mkdtemp(prefix='watch-release-', dir=ROOT / 'work')
    target=Path(output) if output else ROOT/'work/neocloud-watch-site'
    if release and target.exists() and any(target.iterdir()):
        raise ValueError('Release output must be empty. Choose a fresh staging directory.')
    target.mkdir(parents=True,exist_ok=True)
    # Remove the retired generated snapshot when updating a local preview in place.
    (target / 'market-data.json').unlink(missing_ok=True)
    data=load_snapshot()
    if release:
        require_complete_data_quality(data)
    html=(source/'index.html').read_text()
    embed = embedded_json('watch-data', data)
    html=html.replace('</body>',embed+'</body>')
    hosted=hosted_document(html).replace('__WATCH_BASE__',base)
    hosted=hosted.replace('href="./watch.css"',f'href="{base}watch.css"').replace('src="./watch.js"',f'src="{base}watch.js"')
    routes=['','overview','markets','financing','earnings','buildout']+['companies/'+c['id'] for c in data['companies']]
    for route in routes:
        destination=target/route/'index.html';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(hosted)
    # The hosted and standalone editions share the same CSS and JS.
    # Keep chart functions inside the app closure to reuse evidence and URL helpers.
    js = (source/'watch.js').read_text()
    for component in ('overview-charts', 'tradingview'):
        marker = f'/* @include {component}.js */'
        if js.count(marker) != 1:
            raise ValueError(f'Expected one include for {component} in watch.js')
        js = js.replace(marker, (source/f'{component}.js').read_text())
    css = '\n'.join((source/f'{name}.css').read_text() for name in ('watch', 'overview-charts', 'tradingview'))
    (target/'watch.js').write_text(js)
    (target/'watch.css').write_text(css)
    audit_html = (source/'audit.html').read_text()
    (target/'audit.html').write_text(hosted_document(audit_html))
    (target/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (target/'_headers').write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  X-Frame-Options: DENY\n  Content-Security-Policy: " + DOCUMENT_CSP + "; frame-ancestors 'none'\n"
    )
    # Every route is a real static directory; no host-specific SPA rewrite is needed.
    offline=html.replace('__WATCH_BASE__','./').replace('name="watch-offline" content="false"','name="watch-offline" content="true"')
    offline=offline.replace('<link rel="stylesheet" href="./watch.css">','<style>'+css+'</style>')
    js=js.replace('</script','<\\/script')
    offline=re.sub(r'<script src="\./watch\.js"[^>]*></script>','',offline)
    audit_body = audit_html.split('<main>', 1)[1].split('</main>', 1)[0]
    audit_template = '<template id="offline-audit">'+audit_body+'</template>'
    offline=offline.replace('</body>',audit_template+'<script>'+js+'</script></body>')
    artifact = ROOT/'work/Neocloud-Watch-V2.html'
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(offline)
    return {'site':str(target),'offline':str(artifact),'companies':len(data['companies']),'routes':len(routes),'base_path':base}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-path',default='/');parser.add_argument('--output')
    parser.add_argument('--release', action='store_true', help='Stage the public widget edition into an empty output directory.')
    args=parser.parse_args()
    try:
        receipt = build(base=args.base_path, output=args.output, release=args.release)
    except ValueError as exc:
        parser.exit(1, f'{exc}\n')
    print(json.dumps(receipt, indent=2))
