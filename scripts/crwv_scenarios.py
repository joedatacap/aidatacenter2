"""Reproduce the November 25, 2026 CoreWeave financing and fleet sensitivity.
From the repository root run PYTHONPATH=. python scripts/crwv_scenarios.py.
"""
from copy import deepcopy
import json
from math import isclose

from neocloud.underwriting import DATA, evaluate_case


def scenario(raw, base, receipts, conversion):
    case = deepcopy(base)
    base_receipts = [p["prepayments"][0]["amount"] for p in base["periods"]]
    assert base_receipts == [6000, 3000, 0, 0, 0]
    annual_delta = sum(receipts[1:]) - sum(base_receipts[1:])
    for period, old, new in zip(case["periods"], base_receipts, receipts, strict=True):
        period["prepayments"][0]["amount"] = new
        period["ocf_before_interest"] += new - old
    for key in ("prepayments_embedded", "ocf_before_interest",
                "free_cash_flow_before_interest", "cash_free_cash_flow"):
        case["annual_operating"][key] += annual_delta
    anchor = case["valuation"]["anchor"]
    anchor["normalized_unlevered_cash_conversion"] = conversion
    case["valuation"]["multiple"] = (
        conversion * (1 + anchor["perpetual_growth"])
        / (anchor["required_return"] - anchor["perpetual_growth"])
    )
    result = evaluate_case(raw, case)
    assert isclose(sum(p["prepayments_embedded"] for p in result["bridge"]), sum(receipts))
    return result


def main():
    raw = json.loads((DATA / "underwriting/crwv.json").read_text())
    base = next(c for c in raw["cases"] if c["id"] == "base")
    timing_cases = {
        "on time": [6000, 3000, 0, 0, 0],
        "one quarter late": [0, 6000, 3000, 0, 0],
        "missing through target": [0, 0, 0, 0, 0],
    }
    for timing, receipts in timing_cases.items():
        for conversion in (0.5, 0.6, 0.65):
            result = scenario(raw, base, receipts, conversion)
            if timing == "on time" and conversion == 0.6:
                assert round(result["value_per_share"], 2) == 48.60
            first = result["bridge"][0]
            print(timing, conversion, "Q4 equity", round(first["equity_gap"] / 1000, 3),
                  "total net equity", round(result["funding_gap"] / 1000, 3),
                  "financing shares M", round(result["new_shares"], 2),
                  "dilution %", round(result["dilution_pct"], 2),
                  "value/share", round(result["value_per_share"], 2),
                  "return %", round(result["return_pct"], 2))
        result = scenario(raw, base, receipts, 0.6)
        shares = result["post_financing_shares"]
        claims = result["target_debt"] + result["other_ev_claims"] - result["target_cash"]
        annual = base["annual_operating"]
        ebitda = annual["ebitda_margin"] * annual["revenue"]
        for price in (raw["reference"]["price"], raw["reference"]["price"] * 1.30):
            required_multiple = (shares * price + claims) / ebitda
            print(timing, "price", round(price, 2), "conversion required %",
                  round(100 * required_multiple * (0.11 - 0.02) / (1 + 0.02), 2))


if __name__ == "__main__":
    main()
