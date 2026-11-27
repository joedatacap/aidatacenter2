"""Static, linkable investment research. Native disclosure controls also work offline."""
from html import escape
from pathlib import Path
from neocloud.equity import METRICS, narrative, num

CSS = """
:root{color-scheme:light;--ink:#112e33;--muted:#52666a;--line:#cad4d0;--green:#006858;--bg:#f5f6f1}*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--bg);font:16px/1.5 'Inter',system-ui,sans-serif}a{color:var(--green);text-underline-offset:3px}a:focus-visible,summary:focus-visible{outline:3px solid #ec9c2f;outline-offset:3px}.top,main,footer{max-width:1140px;margin:auto;padding:18px clamp(16px,4vw,54px)}.top{display:flex;justify-content:space-between;gap:18px;border-bottom:1px solid var(--line);align-items:center}.top b,.byline,th,.eyebrow{font-weight:700;letter-spacing:.065em}.eyebrow,.byline,th{font-size:.88rem}.mast{margin:26px 0 24px}.mast h1{font:500 clamp(2.15rem,5vw,4rem)/1.08 Georgia,serif;letter-spacing:-.045em;max-width:850px;margin:12px 0}.mast p,.lead{max-width:80ch}.mast p,.meta,.muted{color:var(--muted)}h2{font:500 2.15rem/1.15 Georgia,serif;margin:16px 0}h3{margin-bottom:6px}.strip,.tiles,.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}.strip>*,.tiles>*,.facts>*{background:white;padding:16px}.strip b,.facts strong{display:block;font-size:1.35rem;font-variant-numeric:tabular-nums}.strip small,.facts small{color:var(--muted);font-size:.9rem}.tiles a{text-decoration:none;font-weight:700}.tiles p{margin:4px 0}.call{padding:16px 20px;background:#deefea;border-left:4px solid #087562}.call b{display:block}.scroll{overflow-x:auto}.tabbar{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}.tabbar a,.pill{background:white;border:1px solid var(--line);border-radius:3px;padding:7px 11px;font-size:.95rem;text-decoration:none}.tabbar a[aria-current=page]{background:var(--ink);color:white}.section{margin:32px 0}table{width:100%;border-collapse:collapse;background:white;border:1px solid var(--line);text-align:left}th,td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#e6ece8;white-space:nowrap;letter-spacing:.015em}td.number{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}.kicker{color:var(--green);font-weight:650}details{border-top:1px solid var(--line);padding:12px 0}summary{cursor:pointer;color:var(--green);font-weight:650}.source{font-size:.9rem}.pane{scroll-margin-top:12px;border-top:2px solid var(--ink);padding-top:24px}.printonly{display:none}dl{margin:0}dt{font-weight:650;color:var(--ink)}dd{margin:0 0 10px 0}li{margin:4px 0}ul{padding-left:22px}.data dd{overflow-wrap:anywhere}.data{padding:12px;background:white;border:1px solid var(--line)}.source a{overflow-wrap:anywhere}footer{border-top:1px solid var(--line);color:var(--muted)}@media(max-width:700px){.strip,.tiles,.facts{grid-template-columns:1fr}.top{font-size:.9rem}td,th{padding:8px}h2{font-size:1.7rem}}@media print{.top,.tabbar{display:none}.scroll{overflow:visible}}
"""
LABELS = {"revenue":"Revenue","gross_profit":"Gross profit","ebitda":"EBITDA","net_income":"Net income","capex":"Capex","fcf":"FCF"}
FEATURES = [
    ("NBIS", "Funding the ramp", "Compare 2027 revenue with the cash required to deploy capacity."),
    ("IREN", "When power becomes revenue", "Check customer acceptance and the financing behind the build."),
    ("CRWV", "Backlog into cash", "Test how much contracted revenue reaches shareholders after interest and capex."),
    ("AGPU", "The share count behind the quote", "Trace pre-funded warrants and the steps from Georgia acceptance to billing."),
]


def e(x):
    return escape(str(x),quote=True)


def cash(n):
    if not num(n):
        return "—"
    prefix = "−$" if n<0 else "$"
    return f"{prefix}{abs(n)/1000:,.2f}B" if abs(n)>=1000 else f"{prefix}{abs(n):,.1f}M"


def value(x):
    if x is None:
        return '<span class="muted">Unavailable</span>'
    if isinstance(x,dict):
        return '<dl class="data">'+''.join(f'<dt>{e(k.replace("_"," "))}</dt><dd>{value(v)}</dd>' for k,v in x.items() if k!="sources")+'</dl>'
    if isinstance(x,list):
        return '<ul>'+''.join(f'<li>{value(i)}</li>' for i in x)+'</ul>'
    return e(x)


def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>'+''.join(f'<th scope="col">{e(h)}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{v}</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def sources(c, ids):
    links=[]
    for i in dict.fromkeys(ids):
        s=c['sources'][i]
        links.append(f'<a href="{e(s["url"])}">{e(s["title"])}</a> ({e(s.get("published") or "undated")})')
    return '<p class="source">'+ ' · '.join(links)+'</p>'


def shell(title,body,home,offline):
    css=f'<style>{CSS}</style>' if offline else f'<link rel="stylesheet" href="{e(home)}research/research.css">'
    nav='' if offline else f'<a href="{e(home)}overview/">Markets and prices</a>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | Neocloud Watch</title>{css}</head><body><header class="top"><b>NEOCLOUD WATCH</b>{nav}</header><main>{body}</main><footer>Justin · AI equity research · USD reporting unless stated</footer></body></html>'


def brief(research, href):
    edition=research["edition"]
    companies=research["companies"]
    signals={}
    for t in ("NBIS","IREN","CRWV"):
        row=next(m["metrics"] for m in companies[t]["financials"]["models"] if m["year"]==2027 and m["scenario"]=="base")
        signals[t]=f"FY27 base revenue {cash(row['revenue'])} · "+(f"FCF {cash(row['fcf'])}" if row["fcf"] is not None else f"capex {cash(row['capex'])}")
    signals["AGPU"]="Customer acceptance and first billing remain the gates."
    cards="".join(f'<div><a href="{e(href(t))}">{t} · {e(label)}</a><p>{e(signals[t])}</p></div>' for t,label,copy in FEATURES)
    declines = sum(row["return_pct"] < 0 for row in research["quotes"].values())
    breadth = "All nine stocks fell" if declines==9 else f"{declines} of nine stocks fell"
    return f'<section class="mast"><span class="byline">JUSTIN / EQUITY RESEARCH · {edition}</span><h1>Who can fund the next build?</h1><p>{breadth} over the five sessions ended {research["quote_date"]}. The next distinction is how soon contracted capacity starts billing and how much cash each company needs to get there.</p></section><div class="tiles">{cards}</div>'


def overview(research, href, base, offline):
    companies=research["companies"]
    peers=[]
    for t,c in companies.items():
        q=research["quotes"][t]
        bridge=c["valuation"]["bridge"]
        fwd=next((x for x in bridge["forward"] if x["year"]==2027),{})
        mult=fwd.get("ev_revenue")
        peers.append([f'<a href="{e(href(t))}">{t}</a>',e(q["group"]),cash(bridge["common_equity_m"]),
                      f'<a href="{e(q["source_url"])}">{q["return_pct"]:+.1f}%</a>',
                      f'{mult:.2f}×' if num(mult) else "—"])
    doc=brief(research, href)+'<section class="section"><h2>Relative value</h2><p>Basic equity uses the November 25 close and each issuer’s dated common share count. Compare within the same business model. A dash indicates missing claims or consolidated earnings inputs.</p>'
    benchmarks = " · ".join(f'<a href="{e(b["source"])}">{e(b["ticker"])} {b["return_pct"]:+.1f}%</a>' for b in research["benchmark_citations"])
    doc+=f'<p><b>Five-session benchmarks</b> · {benchmarks}</p>'
    doc+=table(["Company","Business","Basic equity","5 sessions","EV / FY27 base revenue"],peers)+'</section>' 
    doc+='<section class="section"><h2>Next evidence to watch</h2>'+table(["Company","Financing or delivery checkpoint"],[[f'<a href="{e(href(t))}">{t}</a>',e(narrative(companies[t]["report"]["catalysts"][0]))] for t in companies if companies[t]["report"]["catalysts"]])+'</section>'
    doc+='<section class="section"><h2>Benchmarks and accountability</h2><p>Justin tracks the other eight stocks, QQQ and NVDA over one week and one, three, six and twelve months. Unpublished calls and observations without an eligible return series stay unscored.</p>'
    if not offline:
        doc+=f'<p><a href="{e(base)}api/v1/justin/scorecard.json">Recommendation scorecard</a> · <a href="{e(base)}api/v1/">Research API and downloads</a></p>'
    return doc+'</section>'


def company_view(t,c,research,href,base,offline):
    r=c["report"]; q=research["quotes"][t]
    nav='<nav class="tabbar" aria-label="Company research">'+''.join(f'<a href="{e(href(k))}"'+(' aria-current="page"' if k==t else '')+f'>{k}</a>' for k in research["companies"])+'</nav>'
    target=r["target_12m"]
    doc=f'<article class="pane" id="{t}"><p class="eyebrow">JUSTIN / INVESTMENT RESEARCH · {e(c["as_of"])}</p><h2>{e(c["name"])} <small>{t}</small></h2>'+nav
    doc+=f'<div class="call"><b>{e(r["rating"])}</b>{e(r["thesis"])}</div><div class="strip"><div><small>Nov 25 reference close</small><b><a href="{e(q["source_url"])}">${q["close"]:,.2f}</a></b></div><div><small>12-month target</small><b>{("Withheld" if target is None else f"${target:.2f}")}</b></div><div><small>Conviction</small><b>{e(r["conviction"])}</b></div></div>'
    if c.get("conflict_disclosure"):
        doc+=f'<p><b>Conflict disclosure.</b> {e(c["conflict_disclosure"]["text"])}</p>'
    tac=research["tactical"].get(t)
    if tac:
        doc+=f'<p><b>30–90 day trading view.</b> {e(tac["rating"])} existing shares · {e(tac["new_money"])} on new capital. Conditional objective ${tac["objective"]["price"]:.2f}. {e(tac["objective"]["condition"])}</p>'
    else:
        doc+='<p class="muted">Tactical coverage has yet to open for this stock.</p>'
    doc+='<section class="section"><h3>What changes the call</h3>'+table(["Next catalyst","Principal risk","Reassess if"],[[e(narrative(r[k][0])) if r[k] else "Unavailable" for k in ("catalysts","risks","invalidation")]])+'</section>'
    models=c["financials"]["models"]
    doc+='<h3>Forward financials</h3><p>Justin’s independent base case. Figures use each issuer’s fiscal year. Contract-only estimates appear under scenario assumptions.</p>'
    doc+=table(["Fiscal year",*LABELS.values()],[[str(m["year"]),*[cash(m["metrics"][k]) for k in METRICS]] for m in models if m["scenario"]=="base"])
    stress = c["financials"].get("delivery_stress")
    if stress:
        doc += "<h3>One-quarter delivery delay</h3>"
        doc += "".join(f"<p>{e(stress[key])}</p>" for key in ("anchor", "assumption", "cash_basis"))
        columns = ["revenue_delta_m", "ebitda_delta_m", "fcf_delta_if_collected_as_earned_m", "fcf_delta_if_already_prepaid_m"]
        doc += table(["2027 scenario", "Revenue change", "EBITDA change", "FCF change if collected as earned", "FCF change if prepaid"],
                     [[e(row["scenario"]), *[cash(row[key]) for key in columns]] for row in stress["rows"]])
        doc += sources(c, stress["sources"])
    doc+='<details><summary>Bear, base and bull assumptions</summary>'
    for m in models:
        doc+=f'<details><summary>{m["year"]} · {e(m["scenario"].title())} · {e(m["period"])}</summary><p>{e(m["method"])}</p>'+value(m["inputs"])+value(m["metrics"])
        for name in ("components","contract_bridge","supplemental_metrics","acceptance_delay"):
            if name in m:doc+=value(m[name])
        doc+=sources(c,m["sources"])+'</details>'
    doc+='</details>'
    for title,body in [
        ("Valuation and implied assumptions",value(c["valuation"]["analysis"])+value(c["valuation"]["bridge"])),
        ("Financing and funding gaps",value(c["financing"]["analysis"])),
        ("Contract conversion",''.join(f'<h3>{e(a["customer"])}</h3>'+value(a)+sources(c,a["sources"]) for a in c["contracts"]["register"])),
        ("Capitalization and corporate actions",value(c["audit"]["ownership"])+value(c["audit"]["identity_and_actions"])),
        ("Missing information",value(r["missing"])),("Primary evidence and other sources",sources(c,c["sources"]))]:
        doc+=f'<details><summary>{title}</summary>{body}</details>'
    if not offline:doc+=f'<p><a href="{e(base)}api/v1/companies/{t}.json">Company research JSON</a> · <a href="{e(base)}research/">Back to the research brief</a></p>'
    return doc+'</article>'


def render(research,target,base,offline_path):
    folder=target/"research";folder.mkdir(parents=True,exist_ok=True)
    (folder/"research.css").write_text(CSS)
    href=lambda t:base+"research/"+t.lower()+"/"
    (folder/"index.html").write_text(shell("Justin’s equity research",overview(research,href,base,False),base,False))
    for t,c in research["companies"].items():
        page=folder/t.lower()/"index.html";page.parent.mkdir(exist_ok=True)
        page.write_text(shell(t+" investment report",company_view(t,c,research,href,base,False),base,False))
    anchor=lambda t:"#"+t
    body=overview(research,anchor,"",True)+"".join(company_view(t,c,research,anchor,"",True) for t,c in research["companies"].items())
    offline_path.write_text(shell("Equity research preview",body,"",True))


def api_docs(target,base,endpoints):
    root=base+"api/v1/"
    body='<div class="mast"><p class="byline">NEOCLOUD WATCH / DEVELOPERS</p><h1>Research API</h1><p>Use HTTP GET on the versioned JSON resources. Each response carries a schema version, an edition date and a data object. The canonical URLs end in .json. No login is required on a published public edition.</p></div>'
    body+=f'<p><a href="{e(root)}snapshot.json">Full JSON snapshot</a> · <a href="{e(root)}snapshot.md">Markdown research snapshot</a> · <a href="{e(root)}index.json">Endpoint index</a></p>'
    body+='<p>Company paths use uppercase US tickers. Decimal amounts in model and valuation records are USD millions. Source facts carry their own units. Null means missing or not meaningful. Issuer reports, guidance, independent models and published recommendations have separate fields. Compare fiscal period ends before ranking.</p>'
    body+=table(["Resource","Example"],[[e(name),f'<a href="{e(url)}">{e(url)}</a>'] for name,url in endpoints.items() if not name.startswith("companies/") or name.startswith("companies/NBIS")])
    body+='<h2>Coverage and freshness</h2><p>Source dates and statement periods remain attached to each record. The edition date records editorial review. The event monitor carries its own last run, source errors and review state. Adjusted price histories and consensus require export rights.</p>'
    (target/"api/v1/index.html").write_text(shell("Read-only research API",body,base,False))
    # Static hosts supporting the Cloudflare redirects format also accept the
    # short route names. The canonical JSON URLs work on any static server.
    redirects=target/"_redirects"
    redirects.write_text("\n".join(f'{base}api/v1/{name} {url} 200' for name,url in endpoints.items() if name!="index")+"\n")
