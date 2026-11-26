"""Independent checks for the five contract-level (non-consolidated) estimates."""
import json
from pathlib import Path

import pytest


DATA = Path(__file__).resolve().parents[1] / "neocloud" / "data" / "equity"
TICKERS = ("apld", "hut", "wulf", "wyfi", "shaz")


def read(ticker):
    return json.loads((DATA / f"{ticker}.json").read_text())


@pytest.mark.parametrize("ticker", TICKERS)
def test_company_projection_excludes_partial_contracts(ticker):
    company = read(ticker)
    by_case = {(row["year"], row["scenario"]): row for row in company["models"]}
    assert set(by_case) == {(year, scenario) for year in [2027, 2028]
                            for scenario in ["bear", "base", "bull"]}
    for row in by_case.values():
        assert all(number is None for number in row["metrics"].values())
        assert row["contract_bridge"]["scope"]
        assert row["gaps"]
        assert set(row["sources"]) <= company["sources"].keys()
        values = row["inputs"]
        bridge = row["contract_bridge"]
        if ticker == "apld":
            expected = values["remaining_scheduled_rent"] * values["collection_timing_fraction"]
            result = bridge["minimum_rent_receipts_usd_m"]
            if row["year"] == 2027:
                assert "9 months" in row["period"]
        elif ticker == "hut":
            active = values["average_billable_share"]
            expected = (7000 * active["river_bend"]
                        + 9800 * (active["beacon_1"] + active["beacon_2"])) / 15
            result = bridge["term_average_rent_proxy_usd_m"]
        elif ticker == "wulf":
            capacity = values["hall_it_mw"]
            served = sum(mw * fraction for mw, fraction in
                         zip(capacity, values["assumed_billable_fraction"], strict=True))
            expected = 950 * served / sum(capacity)
            result = bridge["term_average_rent_proxy_usd_m"]
        elif ticker == "wyfi":
            expected = (86.5 * values["nscale_effective_factor"]
                        + 0.979 * 12 * values["cadusd_relative_factor"])
            result = bridge["selected_contract_receipts_usd_m"]
        else:
            a = values["first_bucket_share"]
            b = values["second_bucket_share"]
            spans = [a, a, a, a if row["year"] == 2027 else b]
            quarterly = [3800 * pct / 8 for pct in spans]
            assert bridge["estimated_quarterly_usd_m"] == pytest.approx(quarterly)
            expected = sum(quarterly)
            result = bridge["rpo_revenue_usd_m"]
        assert result == pytest.approx(expected, abs=0.000051)


def test_source_bound_capital_claims():
    def facts(symbol):
        return {row["metric"]: row for row in read(symbol)["facts"]}
    a = facts("apld")
    assert a["preferred"]["value"] == pytest.approx(56.373 + 124.929)
    assert a["noncontrolling_interest"]["value"] == pytest.approx(2010.873 + 5.684)
    assert a["restricted_cash"]["value"] == pytest.approx(313.385 + 414.649)
    h = facts("hut")
    assert h["cash"]["value"] == 156.865
    assert h["restricted_short_term_investments"]["value"] == 2838.531
    w = facts("wulf")
    assert w["noncontrolling_interest"]["value"] == -.134
    assert w["quarter_end_issued_shares"]["value"] - 23.968750 == pytest.approx(501.371610)
    y = facts("wyfi")
    assert y["debt"]["value"] == pytest.approx(330.088 + 30.683 + 11.873 + 29.989)
    assert y["postquarter_advance"]["period"] > y["debt"]["period"]
    s = facts("shaz")
    assert s["common_shares"]["value"] == pytest.approx(38.341987 + .136341)
    assert s["prefunded_warrants_from_june_remaining"]["value"] == 0
    assert s["preferred"]["value"] is None
    assert s["debt"]["value"] == pytest.approx(1007.749910 + .020059 + .006097)
