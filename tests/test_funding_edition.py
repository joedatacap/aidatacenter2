"""Cross-check the human reports, existing API and immutable history on a real build."""
import json

import pytest
from bs4 import BeautifulSoup

from neocloud.equity import DATA
from scripts.build_neocloud_watch import build


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    directory = tmp_path_factory.mktemp("funding-review")
    build(output=directory)
    return directory


def resource(site, name):
    return json.loads((site / "api/v1" / (name + ".json")).read_text())["data"]


@pytest.mark.parametrize("ticker", ["NBIS", "CRWV"])
def test_reports_and_archive_agree(site, ticker):
    company = resource(site, f"companies/{ticker}")
    model = resource(site, f"companies/{ticker}/underwriting")
    current = resource(site, "justin/research")[ticker]["investment"]
    base = next(c for c in model["computed"]["cases"] if c["id"] == "base")
    markdown = (site / "api/v1/snapshot.md").read_text()
    assert f"Historical operating forecasts from {company['prior_report']['as_of']}" in markdown
    assert f"| ${base['value_per_share']:,.2f} | {base['return_pct']:+.1f}% |" in markdown
    assert current == company["report"]
    assert current["target_12m"] == pytest.approx(base["value_per_share"])
    assert current["expected_return_pct"] == pytest.approx(base["return_pct"])
    assert model["reference"]["price"] is None
    assert company["financials"]["model_as_of"] == company["prior_report"]["as_of"]
    page = BeautifulSoup((site / "research" / ticker.lower() / "index.html").read_text(), "html.parser")
    text = page.get_text(" ", strip=True)
    assert current["rating"] in text
    assert f"${base['value_per_share']:,.2f}" in text
    assert model["sources"][model["reference"]["source"]]["url"] in {a.get("href") for a in page.select("a")}
    calls = [v for v in resource(site, "justin/history") if v["company"] == ticker.lower() and v["horizon"] == "investment"]
    assert any(not v["current_edition"] and v["rating"] == company["prior_report"]["rating"] for v in calls)
    active, = [v for v in calls if v["current_edition"]]
    assert active["rating"] == current["rating"] and active["target_12m"] == current["target_12m"]
    notice_file = DATA / "equity-history" / "release-notices" / f"{active['version_id']}.json"
    if notice_file.exists():
        assert active["publication_status"] == "released"
        assert active["release"] == json.loads(notice_file.read_text())
    else:
        assert active["publication_status"] == "publication_pending"
        assert active["release"] is None


def test_original_calls_audited_without_changing_coverage(site):
    rows = resource(site, "companies")
    audit = resource(site, "justin/call-audit")
    companies = {c["ticker"] for c in rows}
    assert len(companies) == len(audit["companies"]) == 9
    assert {c["ticker"] for c in audit["companies"]} == companies
    assert len({c["ticker"] for c in audit["priorities"]}) == 3
    index = resource(site, "index")
    assert {k.split("/")[1] for k in index if k.endswith("/underwriting")} == {"NBIS", "CRWV"}
