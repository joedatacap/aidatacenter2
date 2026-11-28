"""Funding identities and actual dated underwriting model regressions."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path

import pytest

from neocloud.underwriting import (
    DATA,
    build_underwriting,
    evaluate_case,
    historical_reproduction,
    load_underwriting,
    sensitivity,
    validate,
)


def fixture():
    source = {
        "url": "https://issuer.example/filing",
        "title": "Synthetic test evidence",
        "published": "2026-11-01",
        "section": "Test only",
        "excerpt": "Synthetic unit test, not actual financial data.",
    }
    case = {
        "id": "base",
        "annual_operating": {
            "year": 2027,
            "revenue": 1000,
            "ebitda_margin": 0.4,
            "note": "Synthetic assumption",
        },
        "valuation": {"method": "ev_ebitda", "multiple": 4, "other_ev_claims": 20},
        "issue": {"reference_price": 50, "discount": 0.2, "fee_rate": 0.05},
        "cash_debt_rate": 0.08,
        "additional_shares": 2,
        "conversions": [],
        "source_ids": ["filing"],
        "assumptions": ["Synthetic timing and financing assumptions"],
        "periods": [
            {
                "id": "q4",
                "start": "2026-10-01",
                "end": "2026-12-31",
                "ocf_before_interest": 40,
                "capex": 150,
                "other_uses": 3,
                "new_debt": 20,
                "debt_repayment": 5,
                "prepayments": [
                    {"id": "receipt1", "amount": 30, "included_in_ocf": True}
                ],
                "note": "Synthetic quarter timing",
            },
            {
                "id": "targetstub",
                "start": "2027-01-01",
                "end": "2027-11-27",
                "ocf_before_interest": 50,
                "capex": 120,
                "other_uses": 0,
                "new_debt": 0,
                "debt_repayment": 10,
                "prepayments": [],
                "note": "Synthetic stub timing",
            },
        ],
    }
    return {
        "ticker": "NBIS",
        "cutoff": "2026-11-27T09:00:00Z",
        "target_date": "2027-11-27",
        "reference": {"price": 50, "as_of": "2026-11-26", "source": "filing"},
        "sources": {"filing": source},
        "opening": {
            "as_of": "2026-09-30",
            "cash": 100,
            "restricted_cash": 20,
            "cash_includes_restricted": True,
            "minimum_cash": 10,
            "debt": 200,
            "shares": 20,
            "other_ev_claims": 20,
            "source_ids": ["filing"],
            "note": "Synthetic combined cash and legal restriction",
        },
        "transactions": [
            {
                "id": "refinancing",
                "date": "2026-10-15",
                "status": "closed",
                "gross_proceeds": 60,
                "fees": 3,
                "repayment": 50,
                "debt_added": 60,
                "debt_repaid": 50,
                "shares_added": 0,
                "source_ids": ["filing"],
                "note": "Net new cash7, net debt10; no gross cash addition",
            },
            {
                "id": "conditional",
                "date": "2026-11-01",
                "status": "conditional",
                "gross_proceeds": 400,
                "fees": 0,
                "repayment": 0,
                "debt_added": 400,
                "debt_repaid": 0,
                "shares_added": 0,
                "source_ids": ["filing"],
                "note": "Unfunded capacity, never available cash",
            },
        ],
        "convertibles": [
            {
                "id": "convert",
                "principal": 100,
                "conversion_shares": 4,
                "coupon_rate": 0.1,
                "cash_coupon_base": 70,
                "conversion_date": "2026-11-28",
                "source_ids": ["filing"],
                "note": "Coupon uses original70; redemption principal100",
            }
        ],
        "cases": [{**deepcopy(case), "id": cid} for cid in ("bear", "base", "bull")],
        "sensitivity": {
            "x": {"field": "multiple", "values": [3, 5]},
            "y": {"field": "issue_price", "values": [30, 60]},
        },
        "call": {"rating": "TEST ONLY", "summary": "Synthetic"},
        "gaps": [],
    }


def result(raw=None):
    return build_underwriting(raw or fixture())["computed"]["cases"][1]


def assert_case_identities(raw, case):
    for period in case["bridge"]:
        cash = (
            period["opening_cash"]
            + period["transaction_net_cash"]
            + period["ocf_before_interest"]
            + period["prepayments_added"]
            + period["new_debt"]
            - period["debt_repayment"]
            - period["cash_interest"]
            - period["capex"]
            - period["other_uses"]
        )
        assert period["cash_before_equity"] == pytest.approx(cash)
        assert period["ending_cash"] == pytest.approx(
            cash + period["gross_equity"] - period["issuance_fees"]
        )
        assert period["gross_equity"] == pytest.approx(
            period["new_shares"] * case["issue"]["actual_issue_price"]
        )
        assert period["issuance_fees"] == pytest.approx(
            period["gross_equity"] * case["issue"]["fee_rate"]
        )
        assert period["ending_cash"] >= raw["opening"]["minimum_cash"] - 1e-7
    assert case["funding_gap"] == pytest.approx(
        sum(p["equity_gap"] for p in case["bridge"])
    )
    assert case["equity_value"] == pytest.approx(
        case["enterprise_value"]
        - case["target_debt"]
        + case["target_cash"]
        - case["other_ev_claims"]
    )
    assert case["raw_value_per_share"] == pytest.approx(
        case["equity_value"] / case["post_financing_shares"]
    )
    assert case["value_per_share"] == pytest.approx(max(0, case["raw_value_per_share"]))
    assert case["return_pct"] == pytest.approx(
        (case["value_per_share"] / raw["reference"]["price"] - 1) * 100
    )
    assert case["dilution_pct"] == pytest.approx(
        (1 - raw["opening"]["shares"] / case["post_financing_shares"]) * 100
    )


def test_all_cash_equity_and_valuation_identities():
    raw = fixture()
    evaluated = result(raw)
    assert_case_identities(raw, evaluated)
    assert evaluated["bridge"][-1]["end"] == raw["target_date"]
    assert evaluated["annual_operating"]["year"] == 2027


def test_prepayment_already_embedded_in_operating_cash_is_never_added_twice():
    raw = fixture()
    embedded = result(raw)
    assert embedded["prepayments_embedded"] == 30
    assert embedded["prepayments_added"] == 0
    raw["cases"][1]["periods"][0]["prepayments"][0]["included_in_ocf"] = False
    separately_received = result(raw)
    assert separately_received["funding_gap"] == pytest.approx(
        embedded["funding_gap"] - 30
    )
    assert separately_received["prepayments_added"] == 30
    # Moving a receipt OUT of OCF and adding it separately preserves exactly the cash path.
    raw["cases"][1]["periods"][0]["ocf_before_interest"] -= 30
    reconciled = result(raw)
    assert reconciled["funding_gap"] == pytest.approx(embedded["funding_gap"])
    assert reconciled["value_per_share"] == pytest.approx(embedded["value_per_share"])


def test_prepaid_contract_amount_cannot_be_another_cash_transaction_or_repeat_receipt():
    raw = fixture()
    raw["cases"][1]["periods"][1]["prepayments"] = deepcopy(
        raw["cases"][1]["periods"][0]["prepayments"]
    )
    with pytest.raises(ValueError, match="same receipt"):
        validate(raw)
    raw = fixture()
    raw["cases"][1]["periods"][0]["prepayments"][0]["id"] = "refinancing"
    with pytest.raises(ValueError, match="same receipt"):
        validate(raw)


def test_restricted_cash_is_excluded_once_and_reserve_is_not_a_legal_restriction():
    raw = fixture()
    combined = build_underwriting(raw)["computed"]
    assert combined["opening"]["usable_cash"] == 80
    raw["opening"].update(cash=80, cash_includes_restricted=False)
    separate = build_underwriting(raw)["computed"]
    assert separate["opening"]["usable_cash"] == 80
    assert separate["cases"][1]["funding_gap"] == pytest.approx(
        combined["cases"][1]["funding_gap"]
    )
    assert separate["opening"]["minimum_cash"] == 10
    assert separate["cases"][1]["target_cash"] >= 10


def test_refinancing_counts_net_proceeds_fees_and_repayment_once():
    raw = fixture()
    evaluated = build_underwriting(raw)["computed"]
    assert evaluated["opening"]["closed_transaction_net_cash"] == 7
    assert evaluated["opening"]["debt"] == 210
    first = evaluated["cases"][1]["bridge"][0]
    assert first["transaction_net_cash"] == 7
    assert first["transaction_debt_change"] == 10
    # Merely announced/conditional debt is not actual opening or period cash/debt.
    raw["transactions"][1]["gross_proceeds"] *= 10
    raw["transactions"][1]["debt_added"] *= 10
    assert result(raw)["value_per_share"] == pytest.approx(
        evaluated["cases"][1]["value_per_share"]
    )


def test_converted_claim_removed_from_debt_and_cash_coupon_and_added_to_shares_once():
    raw = fixture()
    retained = result(raw)
    raw["cases"][1]["conversions"] = ["convert"]
    converted = result(raw)
    assert retained["target_debt"] - converted["target_debt"] == 100
    assert converted["convertible_principal_removed"] == 100
    assert converted["conversion_shares"] == 4
    assert converted["post_financing_shares"] == pytest.approx(
        raw["opening"]["shares"]
        + converted["new_shares"]
        + converted["additional_shares"]
        + 4
    )
    saved_days = (date(2027, 11, 27) - date(2026, 11, 28)).days + 1
    assert retained["cash_interest"] - converted["cash_interest"] == pytest.approx(
        70 * 0.1 * saved_days / 365.25
    )
    assert converted["funding_gap"] < retained["funding_gap"]


def test_fees_and_discount_raise_new_shares_without_becoming_another_cash_use():
    raw = fixture()
    original = result(raw)
    expected = original["funding_gap"] / (50 * 0.8 * 0.95)
    assert original["new_shares"] == pytest.approx(expected)
    raw["cases"][1]["issue"].update(discount=0, fee_rate=0)
    cheaper = result(raw)
    assert cheaper["funding_gap"] == pytest.approx(original["funding_gap"])
    assert cheaper["new_shares"] == pytest.approx(original["funding_gap"] / 50)
    assert cheaper["new_shares"] < original["new_shares"]


def test_negative_common_value_floors_display_but_preserves_raw_residual():
    raw = fixture()
    raw["cases"][1]["valuation"]["multiple"] = 0
    out = result(raw)
    assert out["raw_value_per_share"] < 0
    assert out["value_per_share"] == 0
    assert out["return_pct"] == -100


def test_reverse_multiple_reproduces_reference_price_holding_base_bridge_fixed():
    raw = fixture()
    output = build_underwriting(raw)
    reverse = output["computed"]["reverse"]
    case = deepcopy(raw["cases"][1])
    case["valuation"]["multiple"] = reverse["required_multiple"]
    evaluated = evaluate_case(raw, case)
    assert evaluated["value_per_share"] == pytest.approx(raw["reference"]["price"])
    assert evaluated["funding_gap"] == pytest.approx(result(raw)["funding_gap"])


def test_two_independent_sensitivity_inputs_rerun_actual_equity_paths():
    raw = fixture()
    grid = sensitivity(raw)
    assert len(grid["cells"]) == 4
    for cell in grid["cells"]:
        case = deepcopy(raw["cases"][1])
        case["valuation"]["multiple"] = cell["x"]
        case["issue"]["reference_price"] = cell["y"]
        evaluated = evaluate_case(raw, case)
        assert cell["value_per_share"] == pytest.approx(evaluated["value_per_share"])
        assert cell["dilution_pct"] == pytest.approx(evaluated["dilution_pct"])
    fixed_multiple = [c for c in grid["cells"] if c["x"] == 3]
    assert (
        fixed_multiple[0]["post_financing_shares"]
        != fixed_multiple[1]["post_financing_shares"]
    )
    assert fixed_multiple[0]["value_per_share"] != fixed_multiple[1]["value_per_share"]


def test_capex_sensitivity_changes_gap_and_denominator_not_only_valuation_display():
    raw = fixture()
    raw["sensitivity"]["y"] = {"field": "capex_scale", "values": [0.8, 1.2]}
    grid = sensitivity(raw)
    cells = [c for c in grid["cells"] if c["x"] == 3]
    assert cells[0]["funding_gap"] < cells[1]["funding_gap"]
    assert cells[0]["post_financing_shares"] < cells[1]["post_financing_shares"]
    assert cells[0]["value_per_share"] > cells[1]["value_per_share"]


def test_fiscal_year_supplement_does_not_extend_target_cashflows():
    raw = fixture()
    annual = raw["cases"][1]["annual_operating"]
    annual.update(
        ocf_before_interest=300,
        capex=500,
        cash_interest_assumption=50,
        free_cash_flow_before_interest=-200,
        cash_free_cash_flow=-250,
    )
    evaluated = result(raw)
    assert evaluated["bridge"][-1]["end"] == "2027-11-27"
    assert evaluated["annual_operating"]["cash_free_cash_flow"] == -250
    annual["cash_free_cash_flow"] = -200
    with pytest.raises(ValueError, match="cash FCF identity"):
        validate(raw)


@pytest.mark.parametrize(
    "failure",
    [
        "period_gap",
        "past_target",
        "same_axes",
        "bad_source",
        "missing_numeric",
        "repay_twice",
        "convert_twice",
    ],
)
def test_material_model_failures_are_rejected(failure):
    raw = fixture()
    case = raw["cases"][1]
    if failure == "period_gap":
        case["periods"][1]["start"] = "2027-01-02"
    elif failure == "past_target":
        case["periods"][1]["end"] = "2027-12-31"
    elif failure == "same_axes":
        raw["sensitivity"]["y"]["field"] = "multiple"
    elif failure == "bad_source":
        raw["opening"]["source_ids"] = ["absent"]
    elif failure == "missing_numeric":
        case["periods"][0]["capex"] = None
    elif failure == "repay_twice":
        case["periods"][0]["debt_repayment"] = 1000
    elif failure == "convert_twice":
        case["conversions"] = ["convert", "convert"]
    with pytest.raises(ValueError):
        build_underwriting(raw)


@pytest.mark.parametrize("ticker", ["NBIS", "CRWV"])
def test_actual_model_paths_recompute_every_displayed_case_and_preserve_history(ticker):
    legacy = DATA / "equity" / f"{ticker.lower()}.json"
    original_bytes = legacy.read_bytes()
    output = load_underwriting(ticker)
    assert output["ticker"] == ticker
    assert [c["id"] for c in output["computed"]["cases"]] == ["bear", "base", "bull"]
    for case in output["computed"]["cases"]:
        assert_case_identities(output, case)
        assert case["bridge"][-1]["end"] == output["target_date"]
        assert case["annual_operating"]["year"] == 2027
    assert legacy.read_bytes() == original_bytes
    assert len(output["computed"]["sensitivity"]["cells"]) >= 4
    # A market-value solver cannot change financing to make the answer work.
    base = next(c for c in output["cases"] if c["id"] == "base")
    modified = deepcopy(base)
    modified["valuation"]["multiple"] = output["computed"]["reverse"][
        "required_multiple"
    ]
    assert evaluate_case(output, modified)["value_per_share"] == pytest.approx(
        output["reference"]["price"]
    )


def test_actual_original_nebius_base_12550_revenue_and_negative_24703_2_fcf_reproduces():
    historical = historical_reproduction("NBIS")
    assert historical["reproduced"]["matches_stored"]
    assert historical["reproduced"]["revenue"] == pytest.approx(12550)
    assert historical["reproduced"]["free_cash_flow"] == pytest.approx(-24703.2)
    assert historical["original_model"]["inputs"]["new_customer_prepayments_m"] == 18500
    assert (
        historical["original_model"]["inputs"]["prepaid_revenue_recognition_m"] == 6500
    )


@pytest.mark.parametrize("ticker", ["NBIS", "CRWV"])
def test_actual_models_safely_reconcile_each_failure_mode(ticker):
    raw = json.loads((DATA / "underwriting" / f"{ticker.lower()}.json").read_text())
    baseline = result(raw)
    # A legal restriction amount kept outside reported cash is not subtracted again.
    separate = deepcopy(raw)
    separate["opening"]["cash"] = raw["opening"]["cash"] - (
        raw["opening"]["restricted_cash"]
        if raw["opening"]["cash_includes_restricted"]
        else 0
    )
    separate["opening"]["cash_includes_restricted"] = False
    assert result(separate)["funding_gap"] == pytest.approx(baseline["funding_gap"])
    # Every actual cash roll nets fees and cash repayment; no conditional credit.
    computed = build_underwriting(raw)["computed"]["opening"]
    expected = sum(
        t["gross_proceeds"] - t["fees"] - t["repayment"] - t.get("other_cash_uses", 0)
        for t in raw["transactions"]
        if t["status"] == "closed"
    )
    assert computed["closed_transaction_net_cash"] == pytest.approx(expected)
    # Case fee/discount denominator identity on real funding path.
    case = next(c for c in raw["cases"] if c["id"] == "base")
    net = (
        case["issue"]["reference_price"]
        * (1 - case["issue"]["discount"])
        * (1 - case["issue"]["fee_rate"])
    )
    assert baseline["new_shares"] == pytest.approx(baseline["funding_gap"] / net)
    # Distinct conversion path extinguishes the original debt claim and coupon.
    retained = deepcopy(case)
    retained["conversions"] = []
    converted = deepcopy(case)
    converted["conversions"] = [c["id"] for c in raw["convertibles"]]
    a, b = evaluate_case(raw, retained), evaluate_case(raw, converted)
    assert a["target_debt"] - b["target_debt"] == pytest.approx(
        sum(c["principal"] for c in raw["convertibles"])
    )
    assert b["conversion_shares"] == pytest.approx(
        sum(c["conversion_shares"] for c in raw["convertibles"])
    )
    assert b["cash_interest"] <= a["cash_interest"]


def test_no_fabricated_deep_targets_for_other_seven_companies():
    assert load_underwriting("AGPU") is None


@pytest.mark.parametrize("ticker", ["NBIS", "CRWV"])
def test_actual_tagged_embedded_receipts_are_memoranda_not_an_extra_cash_source(ticker):
    raw = json.loads((DATA / "underwriting" / f"{ticker.lower()}.json").read_text())
    base = next(c for c in raw["cases"] if c["id"] == "base")
    tagged = [
        p for row in base["periods"] for p in row["prepayments"] if p["included_in_ocf"]
    ]
    assert tagged, "Real model must explicitly identify embedded prepayment receipts"
    before = evaluate_case(raw, base)
    for receipt in tagged:
        receipt["amount"] *= 2
    after = evaluate_case(raw, base)
    assert after["funding_gap"] == pytest.approx(before["funding_gap"])
    assert after["post_financing_shares"] == pytest.approx(
        before["post_financing_shares"]
    )
    assert after["value_per_share"] == pytest.approx(before["value_per_share"])
    assert after["prepayments_embedded"] == pytest.approx(
        before["prepayments_embedded"] * 2
    )


def test_actual_historical_audit_commentary_is_retained_without_duplicate_model():
    raw = json.loads((DATA / "underwriting/nbis.json").read_text())
    output = build_underwriting(raw)
    for key in ("equations", "prepayment_audit", "comparison", "report_sha256"):
        assert output["historical"][key] == raw["historical"][key]
    assert output["historical"]["reproduced"]["matches_stored"]
    assert output["historical"]["sources"]
    assert "original_reconstruction" not in output


def test_dated_atm_share_checkpoint_quantifies_excess_without_creating_cash():
    raw = fixture()
    before = result(raw)
    raw["equity_capacity"] = {
        "as_of": "2026-11-01",
        "kind": "shares",
        "amount": 1,
        "source_ids": ["filing"],
        "note": "Dated remaining authorization; cutoff availability unverified.",
        "remaining_at_cutoff": None,
    }
    out = result(raw)
    assert out["funding_gap"] == pytest.approx(before["funding_gap"])
    assert out["value_per_share"] == pytest.approx(before["value_per_share"])
    comparison = out["equity_capacity"]
    assert comparison["modeled_beyond_observed_capacity"] == pytest.approx(
        out["new_shares"] - 1
    )
    assert comparison["comparison_unit"] == "shares millions"
    assert comparison["as_of"] == "2026-11-01"
    assert comparison["cutoff_status"] == "unknown_not_assured_capacity"
    assert comparison["remaining_at_cutoff"] is None
    raw["equity_capacity"]["kind"] = "gross_proceeds"
    out = result(raw)
    assert out["equity_capacity"]["modeled_beyond_observed_capacity"] == pytest.approx(
        out["gross_equity"] - 1
    )
    assert out["equity_capacity"]["comparison_unit"] == "USD millions gross"


def test_total_authorization_is_not_silently_treated_as_remaining_capacity():
    raw = fixture()
    assert result(raw)["equity_capacity"] is None
    raw["equity_capacity"] = {
        "as_of": "2026-11-01",
        "kind": "shares",
        "amount": 1,
        "source_ids": ["filing"],
        "note": "Unknown cutoff usage",
        "remaining_at_cutoff": 1,
    }
    with pytest.raises(ValueError, match="cutoff availability"):
        validate(raw)


@pytest.mark.parametrize("ticker", ["NBIS", "CRWV"])
def test_actual_atm_comparison_is_dated_optional_and_never_implies_cutoff_availability(
    ticker,
):
    output = load_underwriting(ticker)
    capacity = output.get("equity_capacity")
    assert capacity is not None
    assert capacity["kind"] == "shares"
    assert capacity["remaining_at_cutoff"] is None
    for case in output["computed"]["cases"]:
        comparison = case["equity_capacity"]
        assert comparison["as_of"] == capacity["as_of"]
        assert comparison["modeled_beyond_observed_capacity"] == pytest.approx(
            max(0, case["new_shares"] - capacity["amount"])
        )
        assert comparison["cutoff_status"] == "unknown_not_assured_capacity"
