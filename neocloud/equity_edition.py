"""Assemble the current investment call without changing a dated ledger."""
import json

from .underwriting import build_underwriting


def investment_revision(ledger, data_dir):
    ticker = ledger["ticker"]
    if ticker not in {"NBIS", "CRWV"}:
        return None
    inputs = json.loads((data_dir / "underwriting" / f"{ticker.lower()}.json").read_text())
    if inputs["ticker"] != ticker:
        raise ValueError("Underwriting ticker does not match the investment ledger")
    model = build_underwriting(inputs, data_dir=data_dir)
    base = next(case for case in model["computed"]["cases"] if case["id"] == "base")
    call = model["call"]
    date = model["cutoff"][:10]
    report = {
        "rating": call["rating"], "thesis": call["summary"],
        "conviction": call.get("conviction", "Conditional on modeled funding"),
        "as_of": date, "horizon": "12 months", "kind": "Justin investment judgment",
        "target_12m": base["value_per_share"], "target_date": model["target_date"],
        "expected_return_pct": base["return_pct"], "catalysts": [call["falsifier"]],
        "risks": [call["strongest_objection"]], "invalidation": [call["falsifier"]],
        "missing": model["gaps"], "driver": call["driver"],
        "sources": ["underwriting-" + key for key in model["sources"]],
    }
    return model, report
