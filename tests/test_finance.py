from datetime import date
from decimal import Decimal
import pytest
from neocloud.finance import Instrument, rate_scenario, refinancing_scenario

ASOF = date(2026, 6, 30)

def instrument(**overrides):
    values = dict(instrument_id="test", ticker="IREN", name="test", currency="USD",
                  snapshot_date=ASOF, outstanding_principal="413000000", rate_type="floating")
    values.update(overrides)
    return Instrument(**values)

def test_hedged_cash_impact_excludes_undrawn_capacity():
    item = instrument(commitment_amount="1500000000", hedge_status="partial",
                      hedge_notional="394000000", hedge_effective_date="2026-06-01")
    result = rate_scenario([item],200,ASOF)
    assert result["known_annual_increment_by_currency"] == {"USD":"380000"}
    assert item.commitment_amount == Decimal("1500000000")

def test_unknown_hedges_are_not_silently_unhedged():
    item = instrument()
    assert rate_scenario([item],200,ASOF)["rows"][0]["annual_increment"] is None
    assumed = rate_scenario([item],200,ASOF,True)
    assert assumed["known_annual_increment_by_currency"]["USD"] == "8260000"
    assert "assumption" in assumed["rows"][0]["warning"]

def test_future_swap_is_not_assumed_effective():
    item = instrument(hedge_status="partial",hedge_notional="394000000",hedge_effective_date="2026-09-01")
    assert rate_scenario([item],200,ASOF)["rows"][0]["annual_increment"] is None

def test_fixed_coupon_does_not_reprice_with_yield():
    item = instrument(rate_type="fixed",coupon_pct="9.625",hedge_status="unhedged")
    assert rate_scenario([item],300,ASOF)["known_annual_increment_by_currency"]["USD"] == "0"

def test_currencies_and_unknown_balances_remain_separate():
    items = [instrument(hedge_status="unhedged"),
             instrument(instrument_id="eur",currency="EUR",outstanding_principal="100",hedge_status="unhedged"),
             instrument(instrument_id="capacity",outstanding_principal=None,commitment_amount="9999999999")]
    result = rate_scenario(items,100,ASOF)
    assert result["known_annual_increment_by_currency"] == {"USD":"4130000","EUR":"1"}
    assert result["rows"][2]["annual_increment"] is None

def test_refinancing_is_separate_future_assumption():
    item = instrument(maturity="2030-10-31")
    result = refinancing_scenario(item,Decimal("1000000"),Decimal("5"),Decimal("7"),date(2031,1,1),ASOF)
    assert result["annual_increment"] == "20000"
    with pytest.raises(ValueError):
        refinancing_scenario(item,Decimal("9999999999"),Decimal("5"),Decimal("7"),date(2031,1,1),ASOF)

def test_outstanding_requires_snapshot():
    with pytest.raises(ValueError):
        instrument(snapshot_date=None)

def test_database_requires_tls():
    from neocloud.repository import PostgresRepository
    with pytest.raises(ValueError):
        PostgresRepository("postgresql://localhost/neocloud")
