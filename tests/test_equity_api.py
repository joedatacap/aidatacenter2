"""Exercise the real static build, each documented HTTP resource and calculation guards."""
import json
from datetime import date
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen

import pytest
from neocloud.equity import DATA, METRICS, market_history, ratio, read, trailing, validate
from scripts.build_neocloud_watch import build


@pytest.fixture(scope="module")
def staged(tmp_path_factory):
    folder=tmp_path_factory.mktemp("research-static")
    build(output=folder,release=True)
    return folder


def test_http_resources(staged):
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(staged)))
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    origin=f"http://127.0.0.1:{server.server_port}"
    try:
        index=json.load(urlopen(origin+"/api/v1/index.json"))["data"]
        for name,url in index.items():
            with urlopen(origin+url,timeout=5) as response:
                assert response.status==200 and response.headers.get_content_type()=="application/json",name
                assert json.load(response)["schema_version"]=="1.0"
        assert "Model assumptions" in urlopen(origin+"/api/v1/snapshot.md").read().decode()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_market_rights(staged):
    market=read(staged/"api/v1/market/history.json")["data"]
    assert set(b["ticker"] for b in market["benchmarks"])=={"QQQ","NVDA"}
    if market["license"]["status"] != "public_display_permitted":
        assert all(not c["history"] for c in market["companies"])
    for c in market["benchmarks"]:
        assert "start" not in c["price_audit"]
    for p in (staged/"api/v1/companies").glob("*.json"):
        co=read(p)["data"]
        assert "source_register" not in co or isinstance(co["source_register"],dict)
        assert all(f["value"] is None for f in co["financials"]["facts"] if f["metric"]=="price")
        assert all(f["source"] in co["sources"] for f in co["financials"]["facts"])
        assert all(f["published_at"] is None or f["published_at"]<=co["as_of"] for f in co["financials"]["facts"])
        assert co["freshness"]["statement_age_days_at_build"]>=0
        assert co["report"]["target_12m"] is not None or co["report"]["expected_return_pct"] is None
        assert "start" not in co["audit"]["identity_and_actions"]["price_audit"]


def test_valuation_and_nulls(staged):
    def bridge(t):
        return read(staged/f"api/v1/companies/{t}/valuation.json")["data"]["bridge"]
    assert bridge("CRWV")["enterprise_value_m"]==pytest.approx(556.125724*42.57+47505+649-4122)
    assert bridge("NBIS")["enterprise_value_m"]==pytest.approx(313.968341*84.99+14190.8+1-7425.6)
    assert bridge("NBIS")["common_equity_m"]==pytest.approx(292.902405*84.99)
    assert bridge("IREN")["enterprise_value_m"]==pytest.approx(424.357381*12.85+10208-3522)
    assert bridge("AGPU")["enterprise_value_m"] is None
    assert bridge("NBIS")["ev_exceptions"]
    assert bridge("CRWV")["pe"] is None
    assert bridge("CRWV")["fcf_yield_pct"]<0
    assert ratio(2,-1) is None and ratio(0,0) is None and ratio(None,1) is None
    assert trailing([],"revenue") is None


def test_versions_and_ui(staged):
    snap=read(staged/"api/v1/snapshot.json")["data"]
    assert len(snap["companies"])==9
    assert len([v for v in snap["scorecard"]["versions"] if v["current_edition"]])==12
    assert len(snap["history"]) == len(snap["scorecard"]["versions"])
    assert any(v["tactical_objective"] for v in snap["history"])
    assert snap["events"]["checked_at"]
    for t,c in snap["companies"].items():
        assert len(c["financials"]["models"])==6
        assert all(set(METRICS)<=m["metrics"].keys() for m in c["financials"]["models"])
        page=(staged/f"research/{t.lower()}/index.html").read_text()
        assert "12-month target" in page and "Forward financials" in page
        assert c["sources"] and c["events"]["monitor"]["recent"]
    assert "professional ties" in (staged/"research/agpu/index.html").read_text()


def test_future_source_rejected():
    ledger=read(DATA/"equity/nbis.json")
    ledger["sources"][next(iter(ledger["sources"]))]["published"]="2099-01-01"
    with pytest.raises(ValueError,match="Future source"):
        validate(ledger)


def test_nbis_delivery_delay_cash_timing(staged):
    stress = read(staged/"api/v1/companies/NBIS/financials.json")["data"]["delivery_stress"]
    rows = {row["scenario"]: row for row in stress["rows"]}
    assert set(rows) == {"bear", "base", "bull"}
    assert stress["actual_tranche_mw"] is None and stress["actual_cash_effect_m"] is None
    base = rows["base"]
    assert base["revenue_delta_m"] == -625
    assert base["ebitda_delta_m"] == -481.25
    # Baseline pretax 183.5 becomes a loss, removing 36.7 of modeled cash tax.
    assert base["fcf_delta_if_collected_as_earned_m"] == pytest.approx(-444.55)
    assert base["fcf_delta_if_already_prepaid_m"] == pytest.approx(180.45)
    for row in rows.values():
        assert row["capex_delta_m"] == 0
        assert row["fcf_delta_if_already_prepaid_m"] == pytest.approx(
            row["fcf_delta_if_collected_as_earned_m"] - row["revenue_delta_m"])
    for filename in ("research/nbis/index.html", "api/v1/snapshot.md"):
        assert "One-quarter delivery delay" in (staged/filename).read_text()


def test_iren_acceptance_delay_crosses_june_year_end(staged):
    company = read(staged/"api/v1/companies/IREN.json")["data"]
    for model in company["financials"]["models"]:
        if model["year"] != 2027:
            continue
        stress = model["acceptance_delay"]
        q1, q2, q3, q4 = model["inputs"]["quarter_revenue"]
        assert stress["delayed_quarterly_revenue_m"] == [q1, q2, q2, q3]
        revenue_delta = q2 - q4
        assert sum(stress["delayed_quarterly_revenue_m"]) == model["metrics"]["revenue"] + revenue_delta
        margin = model["inputs"]["gross_margin_ex_da"]
        assert stress["ebitda_delta_m"] == pytest.approx(revenue_delta * margin)
        assert stress["cash_delta_if_collected_as_earned_m"] == stress["ebitda_delta_m"]
        assert stress["cash_delta_if_already_prepaid_m"] == pytest.approx(revenue_delta * (margin - 1))
        shares = next(v["assumed_diluted_shares"] for v in company["valuation"]["analysis"]["scenarios"]
                      if v["scenario"] == model["scenario"])
        for cash_key, share_key in [("as_earned", "collected_as_earned"), ("prepaid", "already_prepaid")]:
            assert stress[f"conditional_cash_per_share_delta_{cash_key}"] == round(
                stress[f"cash_delta_if_{share_key}_m"] / shares, 3)
        assert stress["actual_cash_delta_m"] is None and stress["revised_target"] is None
    for path in ["research/iren/index.html", "api/v1/snapshot.md"]:
        assert "a quarter of delay cuts FY27 revenue by $690M" in (staged/path).read_text()


def test_agpu_sec_ownership_floor_and_accelerating_payoff(staged):
    root = staged/"api/v1/companies/AGPU"
    bridge = read(root/"audit.json")["data"]["ownership"]["record_date_bridge"]
    assert bridge["as_of"] == "2026-11-06"
    warrants = sum(holder["prefunded_in_beneficial_ownership"] + holder["prefunded_excluded_by_blocker"]
                   for holder in bridge["identified_holders"])
    assert bridge["identified_prefunded"] == warrants == 6694079
    assert bridge["legal_common"] + warrants == bridge["partial_economic_shares_floor"] == 20344393
    assert bridge["fully_diluted_shares"] is bridge["all_holder_prefunded"] is None
    seller = read(root/"financing.json")["data"]["analysis"]["georgia_seller_payoff"]
    assert seller["current_unpaid_m"] is None
    for case in seller["illustrations"]:
        assert case["paid_m"] == pytest.approx(case["installments_paid"] * seller["monthly_installment_m"])
        assert case["paid_m"] + case["remaining_payoff_m"] == pytest.approx(seller["face_m"])
    assert seller["illustrations"][-1]["remaining_payoff_m"] == 34.32
    for path in ["research/agpu/index.html", "api/v1/snapshot.md"]:
        report = (staged/path).read_text()
        assert "20,344,393" in report and "$34.32M" in report and "$18.23M" in report


def test_peer_groups_and_fiscal_basis(staged):
    peers = read(staged/"api/v1/peers.json")["data"]
    assert peers == read(staged/"api/v1/snapshot.json")["data"]["peers"]
    members = {r["ticker"]: r for group in peers["groups"] for r in group["members"]}
    assert len(members) == sum(len(g["members"]) for g in peers["groups"]) == 9
    assert peers["benchmarks"] == ["QQQ", "NVDA"] and peers["benchmarks_verified"]
    assert all(row["matched_benchmark_window"] and row["source_urls"] for row in members.values())
    assert (peers["window_start"], peers["window_end"]) == ("2026-11-18", "2026-11-25")
    assert "return_pct" not in json.dumps(peers) and "adjusted_close" not in json.dumps(peers)
    assert "2027-06-30" in members["IREN"]["model_period"]
    assert "9 months" in members["APLD"]["model_period"]
    for ticker, row in members.items():
        bridge = read(staged/f"api/v1/companies/{ticker}/valuation.json")["data"]["bridge"]
        forward = next(r for r in bridge["forward"] if r["year"] == 2027)
        assert row["ev_to_base_revenue"] == forward["ev_revenue"]
        assert bool(row["withheld_reason"]) == (forward["ev_revenue"] is None)
    for path in ["research/index.html", "api/v1/snapshot.md"]:
        output = (staged/path).read_text()
        assert all(g["name"] in output for g in peers["groups"])


@pytest.mark.parametrize("change", ["date", "missing_close", "inconsistent_return", "currency", "missing_benchmark"])
def test_peer_window_rejects_incompatible_endpoints(staged, change):
    from neocloud.equity import peer_comparison
    companies = read(staged/"api/v1/snapshot.json")["data"]["companies"]
    audit = read(DATA/"equity-audit.json")
    target = next(r for r in audit["companies"] if r["ticker"] == "NBIS")["price_audit"]
    if change == "date":
        target["start"]["date"] = "2026-11-17"
    elif change == "missing_close":
        target["end"]["adjusted_close"] = None
    elif change == "inconsistent_return":
        target["return_pct"] = 0
    elif change == "currency":
        target["currency"] = "EUR"
    else:
        audit["benchmarks"] = [b for b in audit["benchmarks"] if b["ticker"] != "NVDA"]
    peers = peer_comparison(companies, audit, "2026-11-25")
    matched = {r["ticker"] for g in peers["groups"] for r in g["members"] if r["matched_benchmark_window"]}
    assert "NBIS" not in matched
    assert len(matched) == (0 if change == "missing_benchmark" else 8)


def test_decision_brief_preserves_horizons_and_preview(staged):
    from neocloud.equity import decision_markdown
    api = staged/"api/v1"
    brief = read(api/"justin/decisions.json")["data"]
    assert brief == read(api/"justin/decisions/2026-11-27.json")["data"]
    assert brief == read(api/"snapshot.json")["data"]["decisions"]
    assert brief["publication_status"] == "preview" and brief["public_release_at"] is None
    assert brief["reference_date"] == "2026-11-25"
    assert brief["recorded_at"].startswith(brief["edition"])
    markdown = decision_markdown(brief)
    assert markdown == (api/"justin/decisions.md").read_text()
    assert markdown in (api/"snapshot.md").read_text()
    html = (staged/"research/decisions/index.html").read_text()
    assert "Four-company decision brief" in (staged/"research/index.html").read_text()
    assert [r["ticker"] for r in brief["decisions"]] == ["NBIS","CRWV","IREN","AGPU"]
    quotes = {r["id"].upper():r for r in read(DATA/"justin/cohort.json")["rows"]}
    for row in brief["decisions"]:
        ticker = row["ticker"]
        assert (DATA/"equity-history/versions"/ticker.lower()/(row["investment_version_id"]+".json")).exists()
        assert row["reference_price"] is None and row["target_12m"] is None
        assert row["evidence"] and row["target_withheld_reason"] and row["reversal"]
        assert row["sensitivity"] in markdown and row["sensitivity"] in html
        assert f"${quotes[ticker]['close']:.2f}" in html
        if ticker in ("NBIS","CRWV"):
            assert row["conditional_value_date"] == "2027-11-27"
            assert row["conditional_return_pct"] == round((row["conditional_base_value"]/quotes[ticker]["close"]-1)*100,1)
        else:
            assert row["conditional_base_value"] is row["conditional_return_pct"] is None
    assert brief["decisions"][-1]["conflict_disclosure"] == read(DATA/"equity/agpu.json")["conflict_disclosure"]["text"]
