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
import importlib.util
from neocloud.equity import build_research, make_api
from neocloud.equity_pages import render as render_equity, api_docs
from neocloud.directory import build_directory
from neocloud.website_v2 import build_website_v2
from neocloud.watch import build_watch
from neocloud.data_quality import enrich_data_quality, require_complete_data_quality

ROOT=Path(__file__).resolve().parents[1]
_terminal_spec = importlib.util.spec_from_file_location('watch_terminal_build', ROOT/'scripts/build_terminal.py')
_terminal_module = importlib.util.module_from_spec(_terminal_spec)
_terminal_spec.loader.exec_module(_terminal_module)
build_terminal = _terminal_module.build

# Static Sites adds a per-response Cloudflare script and iframe. The partial
# document policy has no script or frame restrictions on that managed runtime.
DOCUMENT_CSP = "base-uri 'none'; object-src 'none'"
HEADER_CSP = (
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


def research_snapshot(data):
    """Keep the public JSON download separate from attributed page excerpts."""
    companies = []
    for company in data['companies']:
        observation = company.get('size_observation')
        if observation is not None:
            context = {key: observation[key] for key in ('ticker', 'as_of', 'size_band', 'status', 'source_url')}
            company = {**company, 'size_observation': context}
        companies.append(company)
    return {**data, 'companies': companies}


def build(*,base='/',output=None,release=False,history_dir=None):
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
    equity = build_research(data)
    resources = make_api(equity, target, base, history_dir)
    (ROOT/"work").mkdir(exist_ok=True)
    render_equity(equity,target,base,ROOT/"work/NCW-Equity-Research.html")
    api_docs(target,base,resources)
    # Compile one dated briefing from the reviewed model inputs for both editions.
    from neocloud.equity_pages import cash
    nbis_base = next(m["metrics"] for m in equity["companies"]["NBIS"]["financials"]["models"] if m["year"]==2027 and m["scenario"]=="base")
    crwv_base = next(m["metrics"] for m in equity["companies"]["CRWV"]["financials"]["models"] if m["year"]==2027 and m["scenario"]=="base")
    brief_text = (f"Justin’s 2027 base case puts Nebius free cash flow at {cash(nbis_base['fcf'])} and CoreWeave’s at {cash(crwv_base['fcf'])}. "
                  "Before adding risk, watch cash receipts at CoreWeave, contract acceptance at IREN and the first Georgia billing at Axe.")
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
    js = (source/'watch.js').read_text().replace('__EQUITY_EDITION__',equity['edition']).replace('__EQUITY_BRIEF__',brief_text)
    for component in ('overview-charts', 'tradingview', 'market-cap-chart'):
        marker = f'/* @include {component}.js */'
        if js.count(marker) != 1:
            raise ValueError(f'Expected one include for {component} in watch.js')
        js = js.replace(marker, (source/f'{component}.js').read_text())
    css = '\n'.join((source/f'{name}.css').read_text() for name in ('watch', 'overview-charts', 'tradingview', 'market-cap-chart'))
    (target/'watch.js').write_text(js)
    (target/'watch.css').write_text(css)
    audit_html = (source/'audit.html').read_text()
    (target/'audit.html').write_text(hosted_document(audit_html))
    (target/'data.json').write_text(json.dumps(research_snapshot(data),ensure_ascii=False,indent=2)+'\n')
    (target/'_headers').write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  X-Frame-Options: DENY\n  Content-Security-Policy: " + HEADER_CSP + "; frame-ancestors 'none'\n"
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
    # One site: preserve the market landing page and mount research at /terminal/.
    # Use external hosted assets to retain the existing strict response CSP.
    terminal_file = target/'terminal/index.html'
    terminal = build_terminal(output=terminal_file).read_text()
    def connect_terminal(document, home, markets):
        document = document.replace('href="#/desk" aria-label="Neocloud Intelligence Terminal"', f'href="{home}" aria-label="Neocloud Watch homepage"')
        document = document.replace('<strong>NEOCLOUD</strong><small>INTELLIGENCE TERMINAL</small>', '<strong>NEOCLOUD WATCH</strong><small>TRADING DESK · REVIEW</small>')
        return document.replace('<nav id="primary-nav"', f'<nav class="primary-nav" aria-label="Site pages"><a href="{home}">← Market homepage</a><a href="{markets}">Markets &amp; prices</a><a href="#/desk" aria-current="page">Trading Desk</a></nav><nav id="primary-nav"')
    terminal_hosted = connect_terminal(terminal, base+'overview/', base+'markets/')
    terminal_css = re.search(r'<style>(.*?)</style>', terminal_hosted, re.S).group(1)
    terminal_js = re.search(r'<script>(.*?)</script>', terminal_hosted, re.S).group(1)
    (target/'terminal/terminal.css').write_text(terminal_css)
    (target/'terminal/terminal.js').write_text(terminal_js)
    terminal_hosted = re.sub(r'<style>.*?</style>', lambda _: f'<link rel="stylesheet" href="{base}terminal/terminal.css">', terminal_hosted, flags=re.S)
    terminal_hosted = re.sub(r'<script>.*?</script>', lambda _: f'<script src="{base}terminal/terminal.js" defer></script>', terminal_hosted, flags=re.S)
    terminal_file.write_text(hosted_document(terminal_hosted))
    terminal_offline = artifact.parent/'Neocloud-Intelligence-Terminal.html'
    terminal_offline.write_text(connect_terminal(terminal, './Neocloud-Watch-V2.html#/overview/', './Neocloud-Watch-V2.html#/markets/'))
    return {'research_endpoints':len(resources),'site':str(target),'offline':str(artifact),'companies':len(data['companies']),'routes':len(routes)+1,'base_path':base}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-path',default='/');parser.add_argument('--output')
    parser.add_argument('--release', action='store_true', help='Stage the public widget edition into an empty output directory.')
    parser.add_argument('--history-dir', type=Path, help='Reviewed immutable event/scorecard archive for this build')
    args=parser.parse_args()
    try:
        receipt = build(base=args.base_path, output=args.output, release=args.release, history_dir=args.history_dir)
    except ValueError as exc:
        parser.exit(1, f'{exc}\n')
    print(json.dumps(receipt, indent=2))
