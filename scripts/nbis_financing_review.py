"""Reproduce the November 28 NBIS financing review from the repository root."""

from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path

from neocloud.underwriting import evaluate_case


def scenario(base, *, capex=42500, advances=18500, coverage=.80, revenue=12550,
             timing="base", issue_reference=None):
    """Annual inputs in USD millions. Keep the original FY26 and award assumptions."""
    case = deepcopy(base)
    case["annual_operating"]["revenue"] = revenue
    if issue_reference is not None:
        case["issue"]["reference_price"] = issue_reference
    annual_debt = capex * coverage - advances
    periods = case["periods"][2:]
    assert [period["id"] for period in periods] == [
        "2027Q1", "2027Q2", "2027Q3", "2027Q4-to-target"
    ]
    stub = 58 / 92
    weights = {
        "base": (.30, .30, .25, .15 * stub),
        "quarter_late": (0, .30, .30, .25 * stub),
        "early": (.45, .30, .25, 0),
    }[timing]
    for period, receipt_weight in zip(periods, weights):
        operating_weight = period["capex"] / base["annual_operating"]["capex"]
        previous_advance = period["prepayments"][0]["amount"]
        advance = advances * receipt_weight
        debt = annual_debt * operating_weight
        period["other_uses"] += .02 * (debt - period["new_debt"])
        period["new_debt"] = debt
        period["capex"] = capex * operating_weight
        period["ocf_before_interest"] += advance - previous_advance
        period["prepayments"][0]["amount"] = advance
        revenue_delta = revenue - base["annual_operating"]["revenue"]
        period["ocf_before_interest"] += (
            revenue_delta * case["annual_operating"]["ebitda_margin"] * operating_weight
        )
    return case


def split_at_maturity(case):
    """Schedule the full modeled Citi repayment on Oct 16 and pro-rate other flows."""
    result = deepcopy(case)
    original = result["periods"].pop()
    start = date.fromisoformat(original["start"])
    maturity = date(2027, 10, 16)
    end = date.fromisoformat(original["end"])
    scheduled_repayment = 3500
    for first, last in [(start, maturity - timedelta(days=1)), (maturity, maturity),
                        (maturity + timedelta(days=1), end)]:
        part = deepcopy(original)
        part.update(id=first.isoformat(), start=first.isoformat(), end=last.isoformat())
        weight = ((last - first).days + 1) / ((end - start).days + 1)
        for key in ("ocf_before_interest", "capex", "new_debt", "other_uses"):
            part[key] *= weight
        part["debt_repayment"] = (original["debt_repayment"] - scheduled_repayment) * weight
        if first == maturity:
            part["debt_repayment"] += scheduled_repayment
        for prepayment in part["prepayments"]:
            prepayment["amount"] *= weight
        result["periods"].append(part)
    return result


def main():
    data = Path(__file__).resolve().parents[1] / "neocloud/data/underwriting/nbis.json"
    raw = json.loads(data.read_text())
    base = next(case for case in raw["cases"] if case["id"] == "base")
    favorable = {"capex": 40000, "advances": 20000, "coverage": .85}
    cases = [
        ("Dated base", {}),
        ("85% coverage via new debt", {"coverage": .85}),
        ("One-quarter delay", {"timing": "quarter_late"}),
        ("Guidance mix, $12B revenue", {**favorable, "revenue": 12000}),
        ("Guidance mix, $13B revenue", {**favorable, "revenue": 13000}),
        ("Guidance mix, early receipts", {**favorable, "timing": "early"}),
        ("Early receipts, $100 issue reference", {
            **favorable, "timing": "early", "issue_reference": 100,
        }),
    ]
    for label, adjustments in cases:
        result = evaluate_case(raw, scenario(base, **adjustments))
        print(label, *(round(result[key], 4) for key in (
            "funding_gap", "new_shares", "dilution_pct", "value_per_share", "return_pct"
        )), sep=" | ")
    maturity = evaluate_case(raw, split_at_maturity(base))
    row = next(p for p in maturity["bridge"] if p["id"] == "2027-10-16")
    print("Maturity sensitivity", *(round(maturity[key], 4) for key in (
        "funding_gap", "new_shares", "dilution_pct", "value_per_share", "return_pct"
    )), sep=" | ")
    print("October 16 equity required that day (USD M)", round(row["equity_gap"], 2))


if __name__ == "__main__":
    main()
