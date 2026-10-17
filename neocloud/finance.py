"""Pure cash-interest scenarios. All amounts stay in their original currency."""
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Instrument(BaseModel):
    instrument_id: str
    ticker: Literal["CRWV", "NBIS", "IREN", "BTDR"]
    name: str
    currency: str
    snapshot_date: date | None = None
    issue_date: date | None = None
    commitment_amount: Decimal | None = Field(default=None, ge=0)
    drawn_amount: Decimal | None = Field(default=None, ge=0)
    outstanding_principal: Decimal | None = Field(default=None, ge=0)
    coupon_pct: Decimal | None = Field(default=None, ge=0)
    rate_type: Literal["fixed", "floating", "convertible", "unknown"] = "unknown"
    reference_index: str | None = None
    spread_bps: Decimal | None = None
    maturity: date | None = None
    parent_entity: str | None = None
    recourse_type: str = "unknown"
    secured: bool | None = None
    convertible: bool | None = None
    hedge_status: Literal["unhedged", "hedged", "partial", "unknown"] = "unknown"
    hedge_notional: Decimal | None = Field(default=None, ge=0)
    hedge_effective_date: date | None = None
    hedge_end_date: date | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: Literal["live", "fixture"] = "live"

    @model_validator(mode="after")
    def dated_balance(self):
        if self.outstanding_principal is not None and self.snapshot_date is None:
            raise ValueError("Outstanding principal requires a snapshot date")
        return self


def rate_scenario(instruments: list[Instrument], delta_bps: int, as_of: date,
                  assume_unknown_unhedged: bool = False) -> dict:
    if delta_bps not in (-100, 0, 100, 200, 300):
        raise ValueError("Unsupported rate shock")
    totals: dict[str, Decimal] = {}
    rows, warnings = [], []
    for item in instruments:
        impact = None
        reason = None
        if item.outstanding_principal is None:
            reason = "Outstanding balance unknown; commitment and issuance size are excluded."
        elif item.rate_type in ("fixed", "convertible"):
            if item.hedge_status != "unhedged":
                reason = "Economic swap exposure unknown; contractual coupon does not reprice."
            else:
                impact = Decimal(0)
        elif item.rate_type == "floating":
            principal = item.outstanding_principal
            active_hedge = (item.hedge_effective_date is not None
                            and item.hedge_effective_date <= as_of
                            and (item.hedge_end_date is None or as_of <= item.hedge_end_date))
            if item.hedge_status == "unhedged":
                impact = principal * Decimal(delta_bps) / 10000
            elif item.hedge_status in ("hedged", "partial") and item.hedge_notional is not None and active_hedge:
                impact = max(Decimal(0), principal - item.hedge_notional) * Decimal(delta_bps) / 10000
            elif assume_unknown_unhedged and item.hedge_status == "unknown":
                impact = principal * Decimal(delta_bps) / 10000
                reason = "Explicit no-hedge assumption; exposure is unverified."
            else:
                reason = "Hedge amount or effective dates unknown; excluded from known exposure."
        else:
            reason = "Rate type unknown."
        if item.snapshot_date and item.snapshot_date != as_of:
            warnings.append(item.instrument_id + ": balance is dated " + str(item.snapshot_date))
        if impact is not None:
            totals[item.currency] = totals.get(item.currency, Decimal(0)) + impact
        rows.append({"instrument_id": item.instrument_id, "currency": item.currency,
                     "annual_increment": str(impact) if impact is not None else None, "warning": reason})
    return {"delta_bps": delta_bps, "as_of": str(as_of),
            "known_annual_increment_by_currency": {k: str(v) for k, v in totals.items()},
            "coverage": "Disclosure incomplete" if not rows or any(r["warning"] for r in rows) else "Provided instruments only",
            "assumptions": "Parallel benchmark shock; annualized illustration; floors, amortization and future draws excluded. Fixed contractual coupons do not reprice.",
            "rows": rows, "warnings": sorted(set(warnings))}


def refinancing_scenario(item: Instrument, principal_to_refinance: Decimal,
                         old_rate_pct: Decimal, new_rate_pct: Decimal,
                         horizon: date, as_of: date) -> dict:
    if item.outstanding_principal is None or not item.maturity:
        raise ValueError("Dated principal and maturity required")
    if not as_of < item.maturity <= horizon:
        raise ValueError("Maturity outside future horizon")
    if not 0 <= principal_to_refinance <= item.outstanding_principal:
        raise ValueError("Refinancing principal exceeds outstanding balance")
    return {"label": "Future refinancing illustration",
            "annual_increment": str(principal_to_refinance * (new_rate_pct - old_rate_pct) / 100),
            "currency": item.currency,
            "assumption": "Selected principal refinances at assumed rate; repayment and dilution may change outcome."}
