"""Build NCW's read-only, versioned public research projection from reviewed ledgers."""
from __future__ import annotations

import calendar
import json
import math
from neocloud.equity_edition import investment_revision
from neocloud.market_snapshot import load_market_snapshot
from datetime import date, datetime, timezone
from pathlib import Path

DATA = Path(__file__).parent / "data"
METRICS = ("revenue", "gross_profit", "ebitda", "net_income", "capex", "fcf")
SCENARIOS = ("bear", "base", "bull")
PERIODS = (2027, 2028)


def read(path):
    return json.loads(path.read_text())


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def product(*args):
    return math.prod(args) if all(num(a) for a in args) else None


def ratio(a, b, *, positive=True):
    if not num(a) or not num(b) or b <= 0 or (positive and a < 0):
        return None
    return a / b


def month_end_offset(d, offset):
    year, month = divmod(d.year * 12 + d.month - 1 + offset, 12)
    return date(year, month + 1, calendar.monthrange(year, month + 1)[1])


def trailing(quarters, metric):
    """Four consecutive full quarter ends; never annualize an isolated quarter."""
    rows = sorted((q for q in quarters if q.get("months") == 3), key=lambda q: q["period_end"], reverse=True)[:4]
    if len(rows) != 4:
        return None
    end = date.fromisoformat(rows[0]["period_end"])
    scopes = set()
    amounts = []
    for i, q in enumerate(rows):
        cell = q["metrics"].get(metric, {})
        if date.fromisoformat(q["period_end"]) != month_end_offset(end, -3*i):
            return None
        if cell.get("unit") != "USD" or not num(cell.get("value")):
            return None
        scopes.add((q.get("scope"), cell.get("accounting_basis")))
        amounts.append(cell["value"])
    return sum(amounts) / 1e6 if len(scopes) == 1 else None


def validate(ledger):
    as_of = date.fromisoformat(ledger["as_of"])
    sources = ledger["sources"]
    for key, src in sources.items():
        if not src["url"].startswith("https://") or not src["title"]:
            raise ValueError(f"Invalid source {key}")
        if src.get("published") and date.fromisoformat(src["published"][:10]) > as_of:
            raise ValueError(f"Future source {key}")
    for f in ledger["facts"]:
        if f["source"] not in sources or not f["period"] or not f["unit"]:
            raise ValueError(f"Incomplete fact {f['metric']}")
        if f["value"] is not None and not num(f["value"]):
            raise ValueError(f"Invalid number {f['metric']}")
    seen = set()
    for row in ledger["models"]:
        key = row["year"], row["scenario"]
        if key in seen or key[0] not in PERIODS or key[1] not in SCENARIOS:
            raise ValueError(f"Invalid model case {key}")
        seen.add(key)
        if set(METRICS) - row["metrics"].keys() or not row["method"] or not row["sources"]:
            raise ValueError(f"Incomplete model {key}")
        if any(v is not None and not num(v) for v in row["metrics"].values()):
            raise ValueError(f"Invalid model value {key}")
    for record in [*ledger["models"], *ledger["contracts"], ledger["report"]]:
        if not record["sources"] or any(s not in sources for s in record["sources"]):
            raise ValueError(f"Unresolved source in {ledger['ticker']}")


def valuation_bridge(company, ledger, quote):
    facts = {f["metric"]: f["value"] for f in ledger["facts"]}
    basic = product(quote, facts.get("common_shares"))
    economic = product(quote, facts.get("diluted_shares"))
    # Finance leases enter the bridge once. CRWV reports this separate from
    # recourse/nonrecourse debt. IREN already includes leases in the debt fact.
    debt_value = facts.get("debt")
    if "finance_leases" in facts and debt_value is not None:
        debt_value += facts["finance_leases"]
    ev_shares = facts.get("minimum_economic_shares") or facts.get("common_shares")
    ev_equity = product(quote, ev_shares)
    claims = [facts.get(k) for k in ("debt", "preferred", "noncontrolling_interest", "cash")]
    claims[0] = debt_value
    # Keep partial EV separate. A missing preferred interest is not evidence of zero.
    ev = None
    if basic is not None and all(num(v) for v in claims):
        debt, preferred, minority, cash = claims
        ev = ev_equity + debt + preferred + minority - cash
    proxy = None
    if basic is not None and all(num(v) for v in (claims[0], claims[-1])):
        proxy = basic + claims[0] - claims[-1]
    ttm = {k: facts.get("ttm_" + k) for k in ("revenue", "ebitda", "net_income", "fcf")}
    if ttm["revenue"] is None:
        ttm["revenue"] = trailing(company["quarters"], "revenue")
    if ttm["fcf"] is None:
        ocf = trailing(company["quarters"], "operating_cash_flow")
        capex = trailing(company["quarters"], "cash_capex")
        if num(ocf) and num(capex) and capex >= 0:
            ttm["fcf"] = ocf - capex
    available = {f["metric"]: {"period": f["period"], "source": f["source"], "unit": f["unit"]} for f in ledger["facts"]
                 if f["metric"] in ("price", "common_shares", "diluted_shares", "debt", "preferred", "noncontrolling_interest", "cash")}
    missing = [k for k in ("common_shares", "debt", "preferred", "noncontrolling_interest", "cash") if facts.get(k) is None]
    implied = []
    for row in ledger["models"]:
        if row["scenario"] == "base":
            revenue, ebitda = row["metrics"]["revenue"], row["metrics"]["ebitda"]
            implied.append({"year": row["year"], "period": row["period"], "ev_revenue": ratio(ev, revenue),
                            "ev_ebitda": ratio(ev, ebitda),
                            "partial_ev_revenue": ratio(proxy, revenue),
                            "partial_ev_ebitda":ratio(proxy, ebitda)})
    return {"unit": "USD millions except ratios", "economic_shares_used_for_ev_m":ev_shares, "ev_exceptions":ledger["valuation"].get("ev_blockers",[]), "method": "Dated common shares × reference close. Indicative mixed-date EV includes documented nominal-exercise claims when separately reconciled, reported debt and finance leases as identified, preferred and minority book claims, less cash; balance and share dates can differ. Lease treatment and cash restrictions follow the cited facts.",
            "common_equity_m": basic, "economic_diluted_equity_m": economic, "enterprise_value_m": ev, "status":"mixed_date_basic_reference" if ev is not None else "incomplete_claims",
            "partial_ev_m": proxy, "partial_ev_definition": "Basic equity + reported debt − reported cash; excludes preferred and minority claims. Use only with the issuer-specific cash and debt caveats.",
            "ev_missing":missing,"input_periods":available, "ttm_m": ttm, "ev_revenue": ratio(ev, ttm["revenue"]),
            "ev_ebitda": ratio(ev, ttm["ebitda"]), "pe": ratio(basic, facts.get("ttm_net_income_to_common")),
            "fcf_yield_pct": product(100, ratio(ttm["fcf"], basic, positive=False)), "forward": implied}


def action_sources(mapping, sources):
    ids = set()
    def visit(item):
        if isinstance(item, dict):
            for k,v in item.items():
                if k in ("sources","identity_sources") and isinstance(v, list):
                    ids.update(v)
                else:
                    visit(v)
        elif isinstance(item, list):
            for v in item:
                visit(v)
    visit(mapping)
    return {k:sources[k] for k in sorted(ids) if k in sources}


def export_actions(mapping):
    audit = mapping.get("price_audit", {})
    return {**mapping, "price_audit":{k:audit[k] for k in ("status","currency","method","basis","sources","checked_at") if k in audit},
            "audited_sessions":[audit.get("start",{}).get("date"), audit.get("end",{}).get("date")]}


def market_history(snapshot, audit):
    license_info = snapshot.get("license", {})
    # The existing ingestion pipeline is the entitlement authority.
    licensed = (license_info.get("status") == "public_display_permitted" and license_info.get("public_static_redistribution") is True
                and license_info.get("downloadable_cache_permitted") is True and snapshot.get("status") in ("ready", "partial"))
    return {"as_of": snapshot["as_of"], "reviewed_at": snapshot["availability_checked_at"],
            "basis": snapshot["price_basis"], "license": license_info, "status":snapshot["status"],
            "reason": snapshot.get("gap_reason"), "companies":[{"ticker":r["ticker"], "history":r["history"] if licensed else [],"history_status":r["history_status"]} for r in snapshot["companies"]],
            "benchmarks":[{**export_actions(b), "source_register":action_sources(b,audit["sources"])} for b in audit.get("benchmarks", [])], "coverage": "Dated editorial citations are separate from the licensed downloadable history."}


def referenced_ids(obj):
    if isinstance(obj, list):
        for item in obj:
            yield from referenced_ids(item)
    elif isinstance(obj, dict):
        yield from obj.get("source_ids", [])
        for value in obj.values():
            yield from referenced_ids(value)


def company_package(c, ledger, quote, mapping, watch_sources):
    validate(ledger)
    sources = ledger["sources"]
    facts = []
    for f in ledger["facts"]:
        src = sources[f["source"]]
        facts.append({**f, "source_url":src["url"], "published_at":src.get("published"),
                      "last_updated": ledger["as_of"]})
    # Reference quotes appear as attributed editorial context on the human report.
    # The market-history download is governed separately by the verified entitlement.
    reports = {**ledger["report"], "as_of":ledger["as_of"], "horizon":"12 months", "kind":"Justin investment judgment",
               "expected_return_pct":None}
    target = reports["target_12m"]
    if num(target) and num(quote) and quote > 0:
        reports["expected_return_pct"] = (target / quote - 1) * 100
    checked = datetime.now(timezone.utc).date()
    period_end = date.fromisoformat(c.get("latest_report_period_end") or max(q["period_end"] for q in c["quarters"]))
    if period_end > checked or date.fromisoformat(ledger["as_of"]) > checked:
        raise ValueError("Future dated research or statement")
    result = {"freshness":{"statement_period_end":str(period_end), "statement_age_days_at_build":(checked-period_end).days,
                           "research_reviewed":ledger["as_of"], "last_filing_check":c["disclosure_review"].get("checked_at"),
                           "evaluated_on":str(checked), "scope":"A newer retrieval or market session does not refresh a statement."},
              "ticker":c["ticker"], "name":c["name"], "as_of":ledger["as_of"], "cik":c["cik"],
              "exchange":c["exchange"], "business_model":ledger["business_model"], "sources":sources,
              "audit":{"identity_and_actions":mapping,"ownership":ledger["ownership_audit"]},
              "financials":{"actuals":c["quarters"], "guidance":c["guidance"], "consensus":{"status":"unavailable","reason":"No dated, comparable consensus series cleared for export."},
                            "facts":facts,"models":ledger["models"], "model_basis":"Justin independent scenarios, USD millions. Fiscal year labels are issuer-specific."},
              "financing":{"analysis":ledger["financing"],"reported":{k:v for k,v in c["financing"].items() if k in ("metrics","liquidity","financing_rate_summary","as_of","filed_at","form","scope","source_ids","notes")}, "instruments":[], "rates":[]},
              "contracts":{"register":ledger["contracts"], "previously_reviewed":c["contracts"], "milestones":c["milestones"]},
              "valuation":{"bridge":valuation_bridge(c, ledger, quote),"analysis":ledger["valuation"]},
              "events":{"reviewed":c["events"],"disclosure_review":c["disclosure_review"],"catalysts":reports["catalysts"]},
              "report":reports}
    if ledger.get("conflict_disclosure"):
        result["conflict_disclosure"] = ledger["conflict_disclosure"]
    old_ids = set(referenced_ids(result))
    result["watch_sources"] = {i:watch_sources[i] for i in sorted(old_ids) if i in watch_sources}
    return result


def public_company(company):
    """Exclude vendor observations, excerpts and unlicensed market histories from bulk output."""
    import copy
    result = copy.deepcopy(company)
    for source in result["sources"].values():
        source.setdefault("last_verified_at", result["financials"].get("model_as_of", result["as_of"]))
    for group in ("models",):
        for model in result["financials"][group]:
            model.update(estimate_type="Justin modeled estimate",published_at=None, last_updated=result["financials"].get("model_as_of",result["as_of"]),
                         verification_status="analyst assumptions; see linked reported anchors")
    result["financials"]["fact_metadata"] = "Dates refer to source publication and editorial verification. Source keys resolve to the local register; watch source_ids resolve to watch_sources."

    for row in result["financials"]["facts"]:
        url = row["source_url"].lower()
        if row["metric"] == "price" or ("stockanalysis.com" in url and row["value"] is not None):
            row.update(value=None, status="display_only", note="See the attributed report and dated source.")
    for record in result["watch_sources"].values():
        record.pop("excerpt",None)
    # Company-authored analytical conclusions remain available, but provider
    # quote fields embedded by authors are excluded from the downloadable data.
    def strip(record):
        if isinstance(record, dict):
            for key in list(record):
                if key in {"price_anchor","reference_price","reference_price_usd","market_price_usd","quote_price","last_close","provider_market_cap_m"}:
                    record[key] = None
                else:
                    strip(record[key])
        elif isinstance(record, list):
            for item in record:
                strip(item)
    # Keep the attributed reference close on the report only. Funding and
    # valuation assumptions are authored estimates, distinct from market data.
    if "underwriting" in result:
        model = result["underwriting"]
        model["reference"]["price"] = None
        quote_key = model["reference"]["source"]
        model["sources"][quote_key].pop("excerpt", None)
        for key in (quote_key, "underwriting-" + quote_key):
            if key in result["sources"]:
                result["sources"][key].pop("excerpt", None)
    strip(result)
    return result


def build_research(watch):
    rows = read(DATA / "justin/cohort.json")
    quotes = {r["id"].upper():r for r in rows["rows"]}
    audit = read(DATA / "equity-audit.json")
    mappings = {c["ticker"]:c for c in audit["companies"]}
    watch_sources = {s["id"]:s for s in watch["sources"]}
    companies = {}
    original = {}
    for ticker in watch["focus_tickers"]:
        c = next(c for c in watch["companies"] if c["ticker"] == ticker)
        ledger = read(DATA / "equity" / (ticker.lower() + ".json"))
        if ledger["ticker"] != ticker:
            raise ValueError("Mismatched issuer identity")
        company = company_package(c, ledger, quotes[ticker]["close"], export_actions(mappings[ticker]), watch_sources)
        company["audit"]["sources"] = action_sources(mappings[ticker],audit["sources"])
        company["financing"]["instruments"] = [i for i in watch["instruments"] if i.get("ticker")==ticker]
        company["financing"]["rates"] = [i for i in watch["financing_rates"] if i.get("ticker")==ticker]
        for i in referenced_ids(company["financing"]):
            if i in watch_sources:
                company["watch_sources"][i] = watch_sources[i]
        revision = investment_revision(ledger, DATA)
        if revision:
            model, report = revision
            company["prior_report"] = company["report"]
            company["underwriting"] = model
            company["financials"]["model_as_of"] = ledger["as_of"]
            company["report"] = report
            company["as_of"] = report["as_of"]
            company["events"]["catalysts"] = report["catalysts"]
            company["freshness"].update(research_reviewed=report["as_of"], underwriting_cutoff=model["cutoff"])
            for key, source in model["sources"].items():
                company["sources"]["underwriting-" + key] = {**source, "last_verified_at": report["as_of"]}
        companies[ticker] = company
        path = DATA / "justin" / (ticker.lower()+".json")
        if path.exists():
            original[ticker] = read(path)
    benchmark_citations = [{"ticker":b["ticker"],"return_pct":b["price_audit"]["return_pct"],
                            "source":audit["sources"][b["price_audit"]["sources"][0]]["url"]}
                           for b in audit["benchmarks"]]
    return {"call_audit":read(DATA / "underwriting/audit.json"), "benchmark_citations":benchmark_citations, "edition":max(c["as_of"] for c in companies.values()), "companies":companies, "tactical":original,
            "quotes":quotes, "quote_date":rows["as_of"], "market":market_history(load_market_snapshot(DATA/"market_snapshot.json"), audit)}


def narrative(item):
    if isinstance(item, dict):
        return " · ".join(str(item[k]) for k in ("date", "event", "description", "reason") if item.get(k)) or json.dumps(item, ensure_ascii=False)
    return str(item)


def markdown(companies, date_label):
    lines = ["# Neocloud Watch equity research", "", f"Research edition {date_label}. Amounts in USD millions unless stated. Fiscal years follow each issuer. Blank estimates have no defensible value at this cutoff.", ""]
    for ticker, c in companies.items():
        r = c["report"]
        lines.extend([f"## {ticker} · {c['name']}", "", f"**{r['rating']}** · {r['conviction']} conviction · 12 months", "", r["thesis"], "",
                      f"Price target: {r['target_12m'] if r['target_12m'] is not None else 'Withheld'}.", "",
                      "| Year | Scenario | Revenue | Gross profit | EBITDA | Net income | Capex | FCF |",
                      "|---|---|---:|---:|---:|---:|---:|---:|"])
        for m in c["financials"]["models"]:
            cells = [f"{m['metrics'][k]:,.1f}" if num(m["metrics"][k]) else "—" for k in METRICS]
            lines.append("| " + " | ".join([str(m["year"]),m["scenario"],*cells]) + " |")
        lines.append("")
        for field,title in (("catalysts","Catalysts"),("risks","Risks"),("invalidation","Thesis breaks"),("missing","Evidence needed")):
            lines.extend([f"### {title}", "", *["- " + narrative(x) for x in r[field]], ""])
        lines.extend(["### Contracts", "", *[f"- {a['customer']}: {a['stage']}. {a['recognition']}" for a in c["contracts"]["register"]], "",
                      "### Model assumptions","", *[f"- {m['year']} {m['scenario']}: {m['method']}" for m in c["financials"]["models"]], "",
                      "### Sources", "", *[f"- [{s['title']}]({s['url']}) · {s.get('published') or 'publication date unavailable'}" for s in c["sources"].values()], ""])
        if c.get("conflict_disclosure"):
            lines.extend(["### Public interests", "", c["conflict_disclosure"].get("text",""), ""])
    return "\n".join(lines)


def make_api(research, target, base="/", history_dir=None):
    folder = target / "api/v1"
    rows = {t:public_company(c) for t,c in research["companies"].items()}
    edition = research["edition"]
    api_root = base + "api/v1/"
    endpoints = {}
    def emit(name, data):
        endpoints[name] = api_root + name + ".json"
        write_json(folder / (name + ".json"), {"schema_version":"1.0", "edition":edition, "data":data})
    history_dir = Path(history_dir) if history_dir else DATA/"equity-history"
    # Scheduled previews consume the same run's immutable scoring result, including
    # any entitled observation source. Otherwise build from the reviewed archive.
    score_runs = sorted((history_dir/"scorecard-runs").glob("*.json"))
    scores = read(score_runs[-1]) if score_runs else {
        "checked_at":None, "status":"awaiting_first_scorecard", "versions":[],
        "reason":"Run the accountability monitor to record an edition and score eligible observations."}
    events_dir = history_dir/"event-runs"
    events_paths = sorted(events_dir.glob("*.json"))
    last_events = read(events_paths[-1]) if events_paths else {"events":[],"status":"awaiting_first_monitor_run"}
    for ticker,c in rows.items():
        c["events"]["monitor"] = {"checked_at":last_events.get("checked_at"), "status":last_events.get("status"),
                                  "recent":[a for a in last_events.get("events", []) if a.get("ticker")==ticker]}
    market = research["market"]
    listing = [{"ticker":t,"name":c["name"],"cik":c["cik"],"business_model":c["business_model"],
                "resource":api_root+"companies/"+t+".json"} for t,c in rows.items()]
    emit("companies", listing)
    emit("overview", {"research_as_of":edition, "source_freshness":{t:c["freshness"] for t,c in rows.items()}, "cohort":listing, "benchmarks":["QQQ","NVDA"], "reference_price_date":research["quote_date"],
                      "market_history_status":market["status"], "data_policy":"Dated issuer evidence, independent scenario estimates and analyst judgment. Full source registers accompany company records."})
    emit("market/history", market)
    emit("justin/scorecard",scores)
    history = []
    for v in scores["versions"]:
        path = history_dir/"versions"/v["company"]/(v["version_id"]+".json")
        original = read(path)["content"]["report"]
        history.append({**{k:v[k] for k in ("company","version_id","current_edition","recorded_at","publication_status","release","rating")},
                        "horizon":"tactical" if "objective" in original else "investment",
                        "tactical_objective": original.get("objective"), "target_12m":original.get("target_12m"),
                        "thesis":original["thesis"], "invalidation":original.get("invalidation")})
    emit("justin/history",history)
    emit("events", last_events)
    reports={}
    for ticker,c in rows.items():
        ledger_date = c["financials"].get("model_as_of", c["as_of"])
        root = "companies/" + ticker
        emit(root,c)
        for section in ("financials","financing","contracts","valuation","events","audit"):
            emit(root+"/"+section, {"ticker":ticker, "as_of":ledger_date, **c[section],
                                    "sources":c["sources"], "watch_sources":c["watch_sources"]})
        reports[ticker] = {"investment":c["report"],"tactical":research["tactical"].get(ticker),
                           "tactical_status":"published" if ticker in research["tactical"] else "no_published_tactical_call",
                           "sources":c["sources"],"conflict_disclosure":c.get("conflict_disclosure")}
        if "underwriting" in c:
            emit(root+"/underwriting", c["underwriting"])
    emit("justin/call-audit", research["call_audit"])
    emit("justin/research",reports)
    emit("snapshot",{"overview":listing,"companies":rows,"justin":reports,"market":market,"scorecard":scores,"history":history,"events":last_events,"call_audit":research["call_audit"]})
    emit("index",dict(endpoints))
    (folder/"snapshot.md").write_text(markdown(rows,edition))
    return endpoints
