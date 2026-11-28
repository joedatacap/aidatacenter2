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
