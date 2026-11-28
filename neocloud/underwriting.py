"""Dated financing-to-common-share scenarios, separate from historical ledgers.

All monetary amounts are USD millions, shares millions, and rates decimals.
Quarter/stub cash flows are analyst timing assumptions, not observed daily cash.
No unconditional credit is assigned to announced/undrawn financing. A funding
shortfall is explicitly hypothetical equity; failed issuance invalidates the path.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

DATA = Path(__file__).parent / "data"
SCENARIOS = ("bear", "base", "bull")


def number(value, label, *, minimum=None, maximum=None):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{label}: finite numeric input required")
    if (
        minimum is not None
        and value < minimum
        or maximum is not None
        and value > maximum
    ):
        raise ValueError(f"{label}: outside permitted range")
    return value


def day(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label}: ISO date required")
    try:
        result = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label}: invalid ISO date") from None
    if result.isoformat() != value:
        raise ValueError(f"{label}: canonical ISO date required")
    return result


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: nonempty explanation required")
    return value


def source_url(value):
    text(value, "source.url")
    try:
        parsed = urlsplit(value)
        credentials = parsed.username is not None or parsed.password is not None
        port = parsed.port
    except ValueError:
        raise ValueError("source.url: invalid public HTTPS URL") from None
    sensitive = (
        "token",
        "secret",
        "password",
        "signature",
        "authorization",
        "api_key",
        "apikey",
    )
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or credentials
        or port not in (None, 443)
        or any(c.isspace() for c in value)
        or any(
            any(part in key.lower() for part in sensitive)
            for key, _ in parse_qsl(parsed.query)
        )
    ):
        raise ValueError("source.url: public HTTPS source without credentials required")


def validate(raw):
    """Reject silent units, funding, date and evidence substitutions."""
    if not isinstance(raw, dict) or raw.get("ticker") not in ("NBIS", "CRWV"):
        raise ValueError("Unsupported underwriting company")
    try:
        cutoff = datetime.fromisoformat(raw["cutoff"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        raise ValueError("cutoff: UTC ISO timestamp required") from None
    if cutoff.tzinfo is None or cutoff.utcoffset().total_seconds() != 0:
        raise ValueError("cutoff: UTC ISO timestamp required")
    if cutoff > datetime.now(timezone.utc):
        raise ValueError("cutoff: future verification prohibited")
    target = day(raw["target_date"], "target_date")
    if not 350 <= (target - cutoff.date()).days <= 380:
        raise ValueError(
            "target_date: explicit approximately 12-month horizon required"
        )
    sources = raw["sources"]
    if not isinstance(sources, dict) or not sources:
        raise ValueError("sources: dated evidence register required")
    for sid, source in sources.items():
        text(sid, "source.id")
        source_url(source["url"])
        for key in ("title", "excerpt"):
            text(source.get(key), f"source.{key}")
        if not (source.get("section") or source.get("locator")):
            raise ValueError("source: page, section or locator required")
        if day(source["published"], "source.published") > cutoff.date():
            raise ValueError("source: after information cutoff")

    def refs(ids, label):
        if (
            not isinstance(ids, list)
            or not ids
            or any(sid not in sources for sid in ids)
        ):
            raise ValueError(f"{label}: unresolved evidence references")

    capacity = raw.get("equity_capacity")
    if capacity is not None:
        if capacity["kind"] not in ("shares", "gross_proceeds"):
            raise ValueError("equity_capacity: shares or gross proceeds basis required")
        number(capacity["amount"], "equity_capacity.amount", minimum=0)
        if day(capacity["as_of"], "equity_capacity.as_of") > cutoff.date():
            raise ValueError("equity_capacity: future checkpoint")
        if capacity.get("remaining_at_cutoff") is not None:
            raise ValueError(
                "equity_capacity: dated checkpoint must not imply known cutoff availability"
            )
        refs(capacity["source_ids"], "equity_capacity")
        text(capacity["note"], "equity_capacity.note")

    reference = raw["reference"]
    number(reference["price"], "reference.price", minimum=0.000001)
    if day(reference["as_of"], "reference.as_of") > cutoff.date():
        raise ValueError("reference: future observation")
    refs([reference["source"]], "reference")
    opening = raw["opening"]
    opening_date = day(opening["as_of"], "opening.as_of")
    if opening_date > cutoff.date():
        raise ValueError("opening: after cutoff")
    for key in (
        "cash",
        "restricted_cash",
        "minimum_cash",
        "debt",
        "shares",
        "other_ev_claims",
    ):
        number(opening[key], f"opening.{key}", minimum=0)
    if opening["shares"] <= 0 or type(opening["cash_includes_restricted"]) is not bool:
        raise ValueError(
            "opening: positive shares and explicit cash restriction scope required"
        )
    if (
        opening["cash_includes_restricted"]
        and opening["restricted_cash"] > opening["cash"]
    ):
        raise ValueError("opening: restricted cash exceeds combined cash")
    refs(opening["source_ids"], "opening")
    text(opening["note"], "opening.note")
    txids = set()
    for tx in raw["transactions"]:
        if tx["id"] in txids:
            raise ValueError("transaction: duplicate economic event")
        txids.add(tx["id"])
        txdate = day(tx["date"], "transaction.date")
        if tx["status"] not in ("closed", "announced", "conditional"):
            raise ValueError("transaction: explicit closing status required")
        if tx["status"] == "closed" and not opening_date < txdate <= cutoff.date():
            raise ValueError(
                "closed transaction: must follow opening and precede cutoff"
            )
        for key in (
            "gross_proceeds",
            "fees",
            "repayment",
            "debt_added",
            "debt_repaid",
            "shares_added",
        ):
            number(tx[key], f"transaction.{key}", minimum=0)
        number(tx.get("other_cash_uses", 0), "transaction.other_cash_uses", minimum=0)
        if tx["fees"] > tx["gross_proceeds"] and tx["gross_proceeds"] > 0:
            raise ValueError("transaction: fees exceed gross proceeds")
        refs(tx["source_ids"], "transaction")
        text(tx["note"], "transaction.note")
    converts = {}
    for conv in raw["convertibles"]:
        if conv["id"] in converts:
            raise ValueError("convertible: duplicate claim")
        for key in ("principal", "conversion_shares", "coupon_rate"):
            number(conv[key], f"convertible.{key}", minimum=0)
        number(
            conv.get("cash_coupon_base", conv["principal"]),
            "convertible.cash_coupon_base",
            minimum=0,
        )
        if conv["principal"] > 0 and conv["conversion_shares"] <= 0:
            raise ValueError(
                "convertible: positive principal cannot disappear without an explicit share claim"
            )
        if conv["coupon_rate"] > 1:
            raise ValueError("convertible: coupon must be a decimal rate")
        if conv.get("conversion_date"):
            cdate = day(conv["conversion_date"], "convertible.conversion_date")
            if not cutoff.date() < cdate <= target:
                raise ValueError(
                    "convertible: conversion must fall within modeled horizon"
                )
        refs(conv["source_ids"], "convertible")
        text(conv["note"], "convertible.note")
        converts[conv["id"]] = conv
    if sum(c["principal"] for c in converts.values()) > opening["debt"] + 1e-7:
        raise ValueError("convertibles: opening principal not contained in debt claim")
    cases = raw["cases"]
    if {c["id"] for c in cases} != set(SCENARIOS) or len(cases) != 3:
        raise ValueError("cases: exactly bear, base, bull required")
    for case in cases:
        refs(case["source_ids"], "case")
        if not isinstance(case["assumptions"], list) or not case["assumptions"]:
            raise ValueError("case: explicit analyst assumptions required")
        for assumption in case["assumptions"]:
            text(assumption, "case.assumption")
        number(case["cash_debt_rate"], "cash_debt_rate", minimum=0, maximum=1)
        number(case.get("additional_shares", 0), "additional_shares", minimum=0)
        if len(set(case["conversions"])) != len(case["conversions"]) or any(
            cid not in converts for cid in case["conversions"]
        ):
            raise ValueError("conversions: duplicate or unresolved claim")
        annual = case["annual_operating"]
        if not isinstance(annual["year"], int) or isinstance(annual["year"], bool):
            raise ValueError("annual_operating.year: fiscal year required")
        number(annual["revenue"], "annual revenue", minimum=0.000001)
        number(annual["ebitda_margin"], "annual EBITDA margin", minimum=-1, maximum=1)
        text(annual["note"], "annual_operating.note")
        for field in (
            "ocf_before_interest",
            "capex",
            "cash_interest_assumption",
            "free_cash_flow_before_interest",
            "cash_free_cash_flow",
            "prepayments_embedded",
        ):
            if field in annual:
                number(annual[field], f"annual.{field}")
        if "free_cash_flow_before_interest" in annual:
            if not math.isclose(
                annual["free_cash_flow_before_interest"],
                annual["ocf_before_interest"] - annual["capex"],
                abs_tol=1e-5,
            ):
                raise ValueError("annual: pre-interest FCF identity fails")
        if "cash_free_cash_flow" in annual:
            if not math.isclose(
                annual["cash_free_cash_flow"],
                annual["ocf_before_interest"]
                - annual["cash_interest_assumption"]
                - annual["capex"],
                abs_tol=1e-5,
            ):
                raise ValueError("annual: cash FCF identity fails")
        val = case["valuation"]
        if val["method"] not in ("ev_revenue", "ev_ebitda"):
            raise ValueError("valuation: supported EV method required")
        number(val["multiple"], "valuation.multiple", minimum=0)
        number(val["other_ev_claims"], "valuation.other_ev_claims", minimum=0)
        issue = case["issue"]
        number(issue["reference_price"], "issue.reference_price", minimum=0.000001)
        for field in ("discount", "fee_rate"):
            number(issue[field], f"issue.{field}", minimum=0, maximum=0.999999)
        previous = opening_date
        prepays = set()
        pids = set()
        for period in case["periods"]:
            if period["id"] in pids:
                raise ValueError("period: duplicate id")
            pids.add(period["id"])
            start, end = day(period["start"], "period.start"), day(
                period["end"], "period.end"
            )
            if start != previous + timedelta(days=1) or end < start or end > target:
                raise ValueError(
                    "period: contiguous nonoverlapping bridge through target required"
                )
            previous = end
            for key in (
                "ocf_before_interest",
                "capex",
                "other_uses",
                "new_debt",
                "debt_repayment",
            ):
                number(
                    period[key],
                    f"period.{key}",
                    minimum=None if key == "ocf_before_interest" else 0,
                )
            text(period["note"], "period.note")
            for prepay in period["prepayments"]:
                if prepay["id"] in prepays or prepay["id"] in txids:
                    raise ValueError(
                        "prepayment: same receipt cannot occur twice or also as transaction"
                    )
                prepays.add(prepay["id"])
                number(prepay["amount"], "prepayment.amount", minimum=0)
                if type(prepay["included_in_ocf"]) is not bool:
                    raise ValueError("prepayment: explicit OCF treatment required")
        if previous != target:
            raise ValueError("period: bridge must end at target, not fiscal year-end")
    sensitivity = raw["sensitivity"]
    fields = []
    for axis in ("x", "y"):
        config = sensitivity[axis]
        field = config["field"]
        if field not in ("multiple", "revenue", "issue_price", "capex_scale"):
            raise ValueError("sensitivity: unsupported model input")
        fields.append(field)
        if not isinstance(config["values"], list) or len(set(config["values"])) < 2:
            raise ValueError(
                "sensitivity: at least two distinct values per variable required"
            )
        for value in config["values"]:
            number(value, "sensitivity value", minimum=0.000001)
    if fields[0] == fields[1]:
        raise ValueError("sensitivity: two independent inputs required")
    return raw


def _net_cash(tx):
    return (
        tx["gross_proceeds"]
        - tx["fees"]
        - tx["repayment"]
        - tx.get("other_cash_uses", 0)
    )


def _available_cash(opening):
    return opening["cash"] - (
        opening["restricted_cash"] if opening["cash_includes_restricted"] else 0
    )


def _conversion_date(conv, raw):
    cutoff_day = date.fromisoformat(raw["cutoff"][:10])
    return day(
        conv.get("conversion_date", (cutoff_day + timedelta(days=1)).isoformat()),
        "conversion_date",
    )


def evaluate_case(raw, case):
    """Run a genuinely timed bridge, then value remaining claims at target.

    New assumed debt/scheduled repayments use midpoint interest convention;
    known transaction/conversion dates receive actual day weighting. OCF is
    before cash interest and already includes any tagged embedded prepayments.
    """
    opening = raw["opening"]
    cash, shares = _available_cash(opening), opening["shares"]
    converts = {c["id"]: c for c in raw["convertibles"]}
    other_debt = opening["debt"] - sum(c["principal"] for c in converts.values())
    closed = [t for t in raw["transactions"] if t["status"] == "closed"]
    issue = case["issue"]
    issuance_price = issue["reference_price"] * (1 - issue["discount"])
    net_per_share = issuance_price * (1 - issue["fee_rate"])
    bridge = []
    totals = {
        key: 0.0
        for key in (
            "funding_gap",
            "gross_equity",
            "issuance_fees",
            "new_shares",
            "cash_interest",
            "conversion_shares",
            "convertible_principal_removed",
            "prepayments_added",
            "prepayments_embedded",
        )
    }
    converted = set()
    for period in case["periods"]:
        start, end = day(period["start"], "start"), day(period["end"], "end")
        days = (end - start).days + 1
        txs = [tx for tx in closed if start <= day(tx["date"], "tx.date") <= end]
        txcash = sum(_net_cash(tx) for tx in txs)
        txdebt = sum(tx["debt_added"] - tx["debt_repaid"] for tx in txs)
        txshares = sum(tx["shares_added"] for tx in txs)
        weighted_tx_debt = sum(
            (tx["debt_added"] - tx["debt_repaid"])
            * ((end - day(tx["date"], "tx.date")).days + 1)
            / days
            for tx in txs
        )
        average_other = (
            other_debt
            + (period["new_debt"] - period["debt_repayment"]) / 2
            + weighted_tx_debt
        )
        ending_other = (
            other_debt + txdebt + period["new_debt"] - period["debt_repayment"]
        )
        if min(average_other, ending_other) < -1e-7:
            raise ValueError("Debt repayment exceeds remaining nonconvertible claim")
        convertible_interest = 0.0
        removed, convshares = 0.0, 0.0
        for cid, conv in converts.items():
            cdate = (
                _conversion_date(conv, raw) if cid in case["conversions"] else date.max
            )
            live_days = max(0, min(days, (cdate - start).days))
            convertible_interest += (
                conv.get("cash_coupon_base", conv["principal"])
                * conv["coupon_rate"]
                * live_days
                / 365.25
            )
            if cid not in converted and cdate <= end:
                converted.add(cid)
                removed += conv["principal"]
                convshares += conv["conversion_shares"]
        interest = (
            average_other * case["cash_debt_rate"] * days / 365.25
            + convertible_interest
        )
        embedded = sum(
            p["amount"] for p in period["prepayments"] if p["included_in_ocf"]
        )
        added = sum(
            p["amount"] for p in period["prepayments"] if not p["included_in_ocf"]
        )
        before_equity = (
            cash
            + txcash
            + period["ocf_before_interest"]
            + added
            + period["new_debt"]
            - period["debt_repayment"]
            - period["capex"]
            - period["other_uses"]
            - interest
        )
        gap = max(0.0, opening["minimum_cash"] - before_equity)
        new_shares = gap / net_per_share
        gross = new_shares * issuance_price
        fees = gross * issue["fee_rate"]
        ending_cash = before_equity + gross - fees
        shares += txshares + convshares + new_shares
        debt = ending_other + sum(
            c["principal"] for cid, c in converts.items() if cid not in converted
        )
        row = {
            "id": period["id"],
            "start": period["start"],
            "end": period["end"],
            "days": days,
            "opening_cash": cash,
            "ocf_before_interest": period["ocf_before_interest"],
            "prepayments_embedded": embedded,
            "prepayments_added": added,
            "capex": period["capex"],
            "other_uses": period["other_uses"],
            "cash_interest": interest,
            "new_debt": period["new_debt"],
            "debt_repayment": period["debt_repayment"],
            "transaction_net_cash": txcash,
            "transaction_debt_change": txdebt,
            "transaction_shares": txshares,
            "convertible_principal_removed": removed,
            "conversion_shares": convshares,
            "cash_before_equity": before_equity,
            "equity_gap": gap,
            "gross_equity": gross,
            "issuance_fees": fees,
            "new_shares": new_shares,
            "ending_cash": ending_cash,
            "ending_debt": debt,
            "ending_shares": shares,
            "note": period["note"],
        }
        bridge.append(row)
        for key in totals:
            totals[key] += gap if key == "funding_gap" else row[key]
        cash, other_debt = ending_cash, ending_other
    additional_shares = case.get("additional_shares", 0)
    shares += additional_shares
    annual, valuation = case["annual_operating"], case["valuation"]
    metric = annual["revenue"] * (
        annual["ebitda_margin"] if valuation["method"] == "ev_ebitda" else 1
    )
    ev = metric * valuation["multiple"]
    equity = ev - debt + cash - valuation["other_ev_claims"]
    raw_value = equity / shares
    value = max(0.0, raw_value)
    capacity_comparison = None
    if raw.get("equity_capacity") is not None:
        capacity = raw["equity_capacity"]
        modeled = (
            totals["new_shares"]
            if capacity["kind"] == "shares"
            else totals["gross_equity"]
        )
        capacity_comparison = {
            **deepcopy(capacity),
            "modeled_new_shares": totals["new_shares"],
            "modeled_gross_equity": totals["gross_equity"],
            "modeled_beyond_observed_capacity": max(0.0, modeled - capacity["amount"]),
            "comparison_unit": (
                "shares millions"
                if capacity["kind"] == "shares"
                else "USD millions gross"
            ),
            "cutoff_status": "unknown_not_assured_capacity",
        }
    return {
        "id": case["id"],
        "annual_operating": deepcopy(annual),
        "valuation": deepcopy(valuation),
        "issue": {
            **issue,
            "actual_issue_price": issuance_price,
            "net_proceeds_per_share": net_per_share,
        },
        "assumptions": case["assumptions"],
        "source_ids": case["source_ids"],
        "bridge": bridge,
        **totals,
        "additional_shares": additional_shares,
        "equity_capacity": capacity_comparison,
        "post_financing_shares": shares,
        "dilution_pct": (1 - opening["shares"] / shares) * 100,
        "financing_dilution_pct": totals["new_shares"] / shares * 100,
        "target_debt": debt,
        "target_cash": cash,
        "other_ev_claims": valuation["other_ev_claims"],
        "enterprise_value": ev,
        "equity_value": equity,
        "raw_value_per_share": raw_value,
        "value_per_share": value,
        "return_pct": (value / raw["reference"]["price"] - 1) * 100,
        "status": "conditional_scenario_not_price_target_guarantee",
        "funding_status": (
            "hypothetical_equity_required"
            if totals["funding_gap"] > 0
            else "modeled_sources_cover_cash_uses"
        ),
        "valuation_cash_policy": "All unrestricted terminal cash added to EV; operating reserve remains cash and is not a legal restriction.",
        "interest_method": "Actual/365.25; stated coupons on coupon base; other debt at assumed rate, midpoint scenario draws/repayments, dated actual transactions.",
    }


def reverse_valuation(raw, base):
    """Hold financing, cash, shares and annual margin fixed; solve EV hurdle."""
    required_ev = (
        raw["reference"]["price"] * base["post_financing_shares"]
        + base["target_debt"]
        - base["target_cash"]
        + base["other_ev_claims"]
    )
    annual, valuation = base["annual_operating"], base["valuation"]
    margin = annual["ebitda_margin"] if valuation["method"] == "ev_ebitda" else 1
    metric = annual["revenue"] * margin
    return {
        "required_enterprise_value": required_ev,
        "required_multiple": required_ev / metric if metric > 0 else None,
        "required_revenue": (
            required_ev / (valuation["multiple"] * margin)
            if valuation["multiple"] * margin > 0
            else None
        ),
        "reference_price": raw["reference"]["price"],
        "held_fixed": "Base target-date debt, cash, other EV claims, diluted shares, annual EBITDA margin and financing/operating cash bridge; required revenue does not rerun cash flows.",
        "method": "RequiredEV=reference price×post-financing shares+target debt−target unrestricted cash+other claims. Required multiple=requiredEV/annual valuation metric.",
    }


def sensitivity(raw):
    base = next(c for c in raw["cases"] if c["id"] == "base")
    config = raw["sensitivity"]
    cells = []
    for x in config["x"]["values"]:
        for y in config["y"]["values"]:
            case = deepcopy(base)
            for axis, value in (("x", x), ("y", y)):
                field = config[axis]["field"]
                if field == "multiple":
                    case["valuation"]["multiple"] = value
                elif field == "issue_price":
                    case["issue"]["reference_price"] = value
                elif field == "revenue":
                    # Revenue-sensitive recurring OCF delta, holding prepayments,
                    # capex and other working capital fixed at their base values.
                    prior = base["annual_operating"]["revenue"]
                    case["annual_operating"]["revenue"] = value
                    fiscal_start = date(case["annual_operating"]["year"], 1, 1)
                    fiscal_end = date(case["annual_operating"]["year"], 12, 31)
                    year_days = (fiscal_end - fiscal_start).days + 1
                    for period in case["periods"]:
                        left = max(day(period["start"], "start"), fiscal_start)
                        right = min(day(period["end"], "end"), fiscal_end)
                        fraction = max(0, (right - left).days + 1) / year_days
                        period["ocf_before_interest"] += (
                            (value - prior)
                            * case["annual_operating"]["ebitda_margin"]
                            * fraction
                        )
                elif field == "capex_scale":
                    for period in case["periods"]:
                        period["capex"] *= value
            result = evaluate_case(raw, case)
            cells.append(
                {
                    "x": x,
                    "y": y,
                    **{
                        key: result[key]
                        for key in (
                            "value_per_share",
                            "return_pct",
                            "funding_gap",
                            "dilution_pct",
                            "post_financing_shares",
                            "target_debt",
                        )
                    },
                }
            )
    return {
        **deepcopy(config),
        "cells": cells,
        "method": "Each cell reruns the entire funding/equity/interest/valuation path. Issue-price axis is pre-discount; capex scale multiplies modeled period capex; revenue axis changes fiscal-year recurring OCF at fixed EBITDA margin with calendar-day stub weights, leaving prepayments/capex fixed.",
    }


def historical_reproduction(ticker, data_dir=DATA):
    path = Path(data_dir) / "equity" / f"{ticker.lower()}.json"
    if not path.exists():
        return {"status": "historical_ledger_unavailable"}
    ledger = json.loads(path.read_text())
    original = next(
        c for c in ledger["models"] if c["year"] == 2027 and c["scenario"] == "base"
    )
    result = {
        "as_of": ledger["as_of"],
        "original_model": deepcopy(original),
        "original_report": deepcopy(ledger["report"]),
        "source_path": f"neocloud/data/equity/{ticker.lower()}.json",
        "sources": deepcopy(ledger["sources"]),
    }
    if ticker == "NBIS":
        i = original["inputs"]
        revenue = (
            i["avg_revenue_earning_mw"] * i["realized_annual_revenue_per_mw_m"]
            + i["other_revenue_m"]
        )
        da = (
            i["average_in_service_gpu_cost_m"] / i["gpu_life_years"]
            + i["infrastructure_da_m"]
        )
        ebitda = (
            revenue * (1 - i["cash_cost_of_revenue_pct"] / 100)
            - i["cash_opex_m"]
            - i["sbc_m"]
        )
        pretax = (
            ebitda
            - da
            - i["average_debt_m"] * i["cash_interest_rate_pct"] / 100
            - i["customer_financing_noncash_interest_m"]
            + i["average_cash_m"] * i["interest_income_rate_pct"] / 100
        )
        ni = pretax - max(0, pretax) * i["tax_rate_on_profit_pct"] / 100
        fcf = (
            ni
            + da
            + i["sbc_m"]
            + i["customer_financing_noncash_interest_m"]
            + i["new_customer_prepayments_m"]
            - i["prepaid_revenue_recognition_m"]
            - i["other_working_capital_use_m"]
            - i["capex_m"]
        )
        result["reproduced"] = {
            "revenue": revenue,
            "free_cash_flow": fcf,
            "matches_stored": math.isclose(
                revenue, original["metrics"]["revenue"], abs_tol=1e-6
            )
            and math.isclose(fcf, original["metrics"]["fcf"], abs_tol=1e-6),
            "prepayment_treatment": "New customer prepayments added once, prior prepaid revenue recognition subtracted once; not counted again as financing. This identity does not independently verify assumed receipt/recognition timing.",
        }
    return result


def build_underwriting(raw, *, data_dir=DATA):
    validate(raw)
    cases = [
        evaluate_case(raw, next(c for c in raw["cases"] if c["id"] == cid))
        for cid in SCENARIOS
    ]
    base = cases[1]
    opening = raw["opening"]
    closed = [t for t in raw["transactions"] if t["status"] == "closed"]
    computed_opening = {
        "reported_cash": opening["cash"],
        "restricted_cash": opening["restricted_cash"],
        "usable_cash": _available_cash(opening),
        "minimum_cash": opening["minimum_cash"],
        "closed_transaction_net_cash": sum(_net_cash(t) for t in closed),
        "rolled_cash": _available_cash(opening) + sum(_net_cash(t) for t in closed),
        "debt": opening["debt"]
        + sum(t["debt_added"] - t["debt_repaid"] for t in closed),
        "shares": opening["shares"] + sum(t["shares_added"] for t in closed),
        "scope": "Financing-only subsequent transaction roll, not a current cash balance; intervening operations/capex remain modeled period flows.",
    }
    historical = deepcopy(raw.get("historical", {}))
    reproduced = historical_reproduction(raw["ticker"], data_dir)
    historical = {
        **historical,
        **reproduced,
        "reproduced": {
            **historical.get("reproduced", {}),
            **reproduced.get("reproduced", {}),
        },
    }
    payload = deepcopy(raw)
    # Collapse the temporary alias without dropping its unique audit commentary.
    alias = payload.pop("original_reconstruction", {})
    historical = {**alias, **historical}
    return {
        **payload,
        "unit": "USD millions and shares millions; per-share USD; rates decimal; return/dilution percent",
        "historical": historical,
        "computed": {
            "opening": computed_opening,
            "cases": cases,
            "reverse": reverse_valuation(raw, base),
            "sensitivity": sensitivity(raw),
        },
        "model_limitations": [
            "Quarter/stub receipt and spending timing are assumptions; intraperiod shortfalls may exceed period-end gaps.",
            "Modeled new debt and hypothetical equity are conditional financing, not assured availability.",
            "Minimum cash is an analyst reserve, separate from legally restricted cash.",
            "Valuation uses a named fiscal-year metric at a distinct 12-month target date; no automatic year-end target substitution.",
        ],
    }


def load_underwriting(ticker):
    ticker = ticker.upper()
    if ticker not in ("NBIS", "CRWV"):
        return None
    raw = json.loads((DATA / "underwriting" / f"{ticker.lower()}.json").read_text())
    return build_underwriting(raw)
