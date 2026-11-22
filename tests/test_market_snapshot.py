"""Synthetic market inputs test arithmetic and eligibility, never public prices."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import pytest
from neocloud.market_snapshot import (
    ROOT,
    build_market_snapshot,
    gap_snapshot,
    load_market_snapshot,
    normalize_common,
    public_url,
    refresh_market_snapshot,
    size_band,
    validate_calendar,
    window_metadata,
    window_target,
)

NOW = "2026-11-22T01:00:00Z"
REGISTRY = [
    {"id": "crwv", "ticker": "CRWV", "name": "CoreWeave", "listing_status": "listed"},
    {"id": "wyfi", "ticker": "WYFI", "name": "WhiteFiber", "listing_status": "listed"},
]


@pytest.fixture
def raw():
    cal = json.loads((ROOT / "neocloud/data/market_calendar.json").read_text())
    cal["verified_at"] = "2026-11-01T12:00:00Z"
    days = [
        s["date"] for s in cal["sessions"] if "2025-12-15" <= s["date"] <= "2026-11-20"
    ]
    provider = {
        "name": "SYNTHETIC TEST FIXTURE",
        "source_url": "https://example.com/test-closes",
        "permission_url": "https://example.com/test-permission",
        "permission_excerpt": "SYNTHETIC FIXTURE ONLY, not a real provider entitlement.",
        "permission_status": "verified_public_display",
        "public_display_permitted": True,
        "public_redistribution_permitted": True,
        "cached_history_permitted": True,
        "terms_reviewed_at": "2026-11-01T12:00:00Z",
        "price_basis": "split_adjusted_price_return",
    }
    companies = []
    for n, c in enumerate(REGISTRY):
        rows = [{"date": day, "close": 100 + i * (n + 1)} for i, day in enumerate(days)]
        companies.append(
            {
                **c,
                "currency": "USD",
                "exchange": "XNAS",
                "listed_on": "2025-01-01",
                "prices": rows,
                "corporate_actions": [],
                "quote": {
                    "date": days[-1],
                    "value": rows[-1]["close"] + 20,
                    "currency": "USD",
                    "exchange": "XNAS",
                    "kind": "closing_price",
                    "source_url": "https://example.com/test-closes",
                },
                "market_cap": {
                    "value": 427060000 if n else 29550000000,
                    "currency": "USD",
                    "as_of": "2026-11-20",
                    "status": "verified",
                    "share_basis": "Dated shares outstanding × literal closing price; all share classes reconciled",
                    "source_url": "https://example.com/test-cap",
                },
            }
        )
    return {
        "schema_version": 1,
        "observed_at": "2026-11-21T01:00:00Z",
        "provider": provider,
        "calendar": cal,
        "companies": companies,
    }


def build(raw):
    return build_market_snapshot(raw, now=NOW, registry=REGISTRY)


def test_official_calendar_latest_completed_and_early_close():
    cal = json.loads((ROOT / "neocloud/data/market_calendar.json").read_text())
    sessions, end = validate_calendar(
        cal, datetime.fromisoformat(NOW.replace("Z", "+00:00"))
    )
    assert end == "2026-11-20"
    assert sessions["2026-11-27"].isoformat() == "2026-11-27T18:00:00+00:00"
    assert "2026-11-26" not in sessions
    assert "2026-11-20" in sessions  # Options expiration is not a holiday.
    assert sessions["2025-12-31"].hour == 21
    cal["verified_at"] = "2026-11-01T12:00:00Z"
    _, before_close = validate_calendar(
        cal, datetime.fromisoformat("2026-11-20T20:59:00+00:00")
    )
    assert before_close == "2026-11-19"
    _, after_close = validate_calendar(
        cal, datetime.fromisoformat("2026-11-20T21:00:00+00:00")
    )
    assert after_close == "2026-11-20"


def test_calendar_cannot_silently_omit_weekday_or_go_past_confirmed_coverage(raw):
    raw["calendar"]["sessions"] = [
        s for s in raw["calendar"]["sessions"] if s["date"] != "2026-11-20"
    ]
    with pytest.raises(ValueError, match="omits a weekday"):
        build(raw)
    cal = json.loads((ROOT / "neocloud/data/market_calendar.json").read_text())
    with pytest.raises(ValueError, match="coverage"):
        validate_calendar(cal, datetime.fromisoformat("2027-01-01T22:00:00+00:00"))


def test_calendar_month_rules_and_preceding_nontrading_close(raw):
    result = build(raw)
    assert result["windows"]["1w"]["start_session"] == "2026-11-13"
    assert result["windows"]["1m"]["start_session"] == "2026-10-20"
    assert result["windows"]["3m"]["start_session"] == "2026-08-20"
    assert result["windows"]["ytd"]["start_session"] == "2025-12-31"
    sessions, _ = validate_calendar(
        raw["calendar"], datetime.fromisoformat(NOW.replace("Z", "+00:00"))
    )
    assert (
        window_metadata("2026-06-30", sessions)["1m"]["start_session"] == "2026-05-29"
    )
    assert window_target("2026-03-31", "1m") == "2026-02-28"
    assert window_target("2026-01-31", "3m") == "2025-10-31"


def test_sample_return_independently_matches_exact_underlying_prices(raw):
    result = build(raw)
    company = result["companies"][0]
    closes = {p["date"]: p["close"] for p in raw["companies"][0]["prices"]}
    for window, r in company["returns"].items():
        expected = (
            (closes[r["end_session"]] - closes[r["start_session"]])
            / closes[r["start_session"]]
            * 100
        )
        assert r["status"] == "available" and r["value"] == pytest.approx(expected)
        assert r["end_session"] == "2026-11-20"
    assert (
        company["price"]["value"] == company["history"][-1]["close"] + 20
    )  # Literal close is never an adjusted-index proxy.


@pytest.mark.parametrize(
    "permission",
    [
        "public_display_permitted",
        "public_redistribution_permitted",
        "cached_history_permitted",
    ],
)
def test_static_download_redistribution_permission_is_mandatory(raw, permission):
    raw["provider"][permission] = False
    with pytest.raises(ValueError, match="permission"):
        build(raw)


@pytest.mark.parametrize("field", ["observed_at", "terms_reviewed_at", "verified_at"])
def test_future_observation_or_verification_rejected(raw, field):
    target = (
        raw
        if field == "observed_at"
        else raw["provider"] if field == "terms_reviewed_at" else raw["calendar"]
    )
    target[field] = "2027-01-01T12:00:00Z"
    with pytest.raises(ValueError, match="Future"):
        build(raw)


def test_missing_and_stale_prices_do_not_borrow_peer_endpoints(raw):
    raw["companies"][1]["prices"].pop()
    raw["companies"][1]["quote"]["date"] = "2026-11-19"
    result = build(raw)
    c = result["companies"][1]
    assert (
        result["expected_end_session"] == "2026-11-20"
        and result["end_session"] == "2026-11-20"
    )
    assert c["price"]["status"] == "stale" and c["price"]["date"] == "2026-11-19"
    assert all(r["value"] is None for r in c["returns"].values())
    assert result["status"] == "partial"
    assert result["normalizations"]["1m"]["status"] == "unavailable"


def test_missing_internal_trading_session_splits_history_and_blocks_return(raw):
    raw["companies"][1]["prices"] = [
        p for p in raw["companies"][1]["prices"] if p["date"] != "2026-11-05"
    ]
    result = build(raw)
    company = result["companies"][1]
    assert company["returns"]["1m"]["value"] is None
    assert len({p["segment"] for p in company["history"]}) == 2
    norm = result["normalizations"]["1m"]
    assert norm["shortened"] and norm["start_session"] == "2026-11-06"
    assert all(series["points"][0]["value"] == 100 for series in norm["series"])


def test_ipo_windows_are_unavailable_but_common_normalization_is_shortened(raw):
    c = raw["companies"][1]
    c["listed_on"] = "2026-11-02"
    c["prices"] = [p for p in c["prices"] if p["date"] >= c["listed_on"]]
    result = build(raw)
    assert result["companies"][1]["returns"]["1m"]["value"] is None
    assert "IPO" in result["companies"][1]["returns"]["1m"]["reason"]
    norm = result["normalizations"]["1m"]
    assert (
        norm["status"] == "available"
        and norm["shortened"]
        and norm["start_session"] == "2026-11-02"
    )
    assert all(
        s["points"][0]["date"] == norm["start_session"]
        and s["points"][0]["value"] == 100
        for s in norm["series"]
    )


def test_split_and_reverse_split_must_be_reflected_in_the_series(raw):
    action = {
        "effective_date": "2026-11-02",
        "type": "reverse_split",
        "ratio": 0.1,
        "verified": True,
        "source_url": "https://example.com/action",
        "series_treatment": "reflected_in_series",
    }
    raw["companies"][1]["corporate_actions"] = [action]
    assert build(raw)["companies"][1]["returns"]["1m"]["status"] == "available"
    action["verified"] = False
    result = build(raw)
    c = result["companies"][1]
    assert c["returns"]["1m"]["value"] is None
    assert len({p["segment"] for p in c["history"]}) == 2
    assert result["normalizations"]["1m"]["start_session"] == "2026-11-02"
    action["verified"] = True
    action.pop("ratio")
    assert build(raw)["companies"][1]["returns"]["1m"]["status"] == "unavailable"


def test_ticker_changes_require_chronology_and_canonical_final_identity(raw):
    c = raw["companies"][1]
    c["corporate_actions"] = [
        {
            "effective_date": "2026-11-02",
            "type": "ticker_change",
            "from_ticker": "OLD",
            "to_ticker": "WYFI",
            "verified": True,
            "source_url": "https://example.com/ticker",
            "series_treatment": "reflected_in_series",
        }
    ]
    for p in c["prices"]:
        p["ticker"] = "OLD" if p["date"] < "2026-11-02" else "WYFI"
    assert build(raw)["companies"][1]["returns"]["1m"]["status"] == "available"
    c["prices"][0]["ticker"] = "WYFI"
    with pytest.raises(ValueError, match="chronology"):
        build(raw)
    c["prices"][0]["ticker"] = "OLD"
    c["corporate_actions"][0]["to_ticker"] = "OTHER"
    with pytest.raises(ValueError, match="canonical"):
        build(raw)


def test_total_return_basis_dividends_and_raw_quotes_are_explicit(raw):
    raw["provider"]["price_basis"] = "total_return"
    action = {
        "type": "dividend",
        "effective_date": "2026-11-02",
        "verified": True,
        "source_url": "https://example.com/dividend",
        "series_treatment": "included_in_total_return",
    }
    raw["companies"][0]["corporate_actions"] = [action]
    result = build(raw)
    assert result["price_basis"] == "total_return"
    assert result["companies"][0]["last_adjusted_close"]["unit"] == "total_return_index"
    assert result["companies"][0]["price"]["kind"] == "closing_price"
    raw["companies"][0].pop("quote")
    assert build(raw)["companies"][0]["price"]["value"] is None
    raw["companies"][0]["prices"][0]["basis"] = "split_adjusted_price_return"
    with pytest.raises(ValueError, match="Mixed"):
        build(raw)


@pytest.mark.parametrize(
    "value,band",
    [
        (299999999, "micro"),
        (300000000, "small"),
        (1999999999, "small"),
        (2000000000, "mid"),
        (10000000000, "large"),
    ],
)
def test_size_thresholds(value, band):
    assert size_band(value) == band


def test_baseline_capitalization_blockers_and_weighted_average_eps_shares(raw):
    registry = deepcopy(REGISTRY)
    registry[0]["capitalization_blocker"] = "Unresolved share classes"
    result = build_market_snapshot(raw, now=NOW, registry=registry)
    assert result["companies"][0]["market_cap"]["size_band"] == "unknown"
    assert result["companies"][0]["returns"]["1m"]["value"] is not None
    raw["companies"][1]["market_cap"][
        "share_basis"
    ] = "weighted-average EPS shares × closing price"
    assert build(raw)["companies"][1]["market_cap"]["status"] == "unreconciled"
    blocked = gap_snapshot("No licensed feed", checked_at=NOW)
    by_ticker = {c["ticker"]: c for c in blocked["companies"]}
    for ticker in ("NBIS", "SHAZ", "AGPU"):
        assert by_ticker[ticker]["market_cap"]["size_band"] == "unknown"
    assert by_ticker["CRWV"]["market_cap"]["status"] == "dated_manual"
    assert by_ticker["CRWV"]["market_cap"]["as_of"] == "2026-11-13"


def test_credential_urls_and_unknown_private_fields_cannot_enter_cache(raw):
    for url in (
        "https://user:password@example.com/data",
        "https://example.com/data?api_key=private",
        "https://example.com/data?token=private",
    ):
        with pytest.raises(ValueError):
            public_url(url)
    raw["companies"][0]["corporate_actions"] = [
        {
            "type": "split",
            "effective_date": "2026-11-02",
            "ratio": 2,
            "verified": True,
            "series_treatment": "reflected_in_series",
            "source_url": "https://example.com/split",
            "api_key": "PRIVATE-CANARY",
        }
    ]
    raw["calendar"]["sessions"][0]["api_key"] = "PRIVATE-CANARY"
    encoded = json.dumps(build(raw))
    assert "PRIVATE-CANARY" not in encoded


def test_last_good_cache_is_atomic_and_stale_on_failed_refresh(raw, tmp_path):
    cache = tmp_path / "market.json"
    assert refresh_market_snapshot(raw, cache_path=cache, now=NOW, registry=REGISTRY)[
        "cache_replaced"
    ]
    original = cache.read_bytes()
    broken = deepcopy(raw)
    broken["provider"]["public_display_permitted"] = False
    assert not refresh_market_snapshot(
        broken, cache_path=cache, now=NOW, registry=REGISTRY
    )["cache_replaced"]
    assert cache.read_bytes() == original
    loaded = load_market_snapshot(cache, now="2026-11-24T01:00:00Z")
    assert loaded["refresh"]["status"] == "failed" and loaded["refresh"]["stale"]
    assert (
        loaded["end_session"] == "2026-11-20"
        and loaded["expected_end_session"] == "2026-11-23"
    )
    assert loaded["refresh"]["age_days"] > 2
    assert not list(tmp_path.glob("market.json.*[0-9]"))


def test_regressive_or_coverage_losing_partial_refresh_retains_cache(raw, tmp_path):
    cache = tmp_path / "market.json"
    refresh_market_snapshot(raw, cache_path=cache, now=NOW, registry=REGISTRY)
    original = cache.read_bytes()
    partial = deepcopy(raw)
    partial["companies"][1]["prices"].pop()
    assert (
        refresh_market_snapshot(partial, cache_path=cache, now=NOW, registry=REGISTRY)[
            "status"
        ]
        == "failed"
    )
    assert cache.read_bytes() == original
    regressive = deepcopy(raw)
    regressive["observed_at"] = "2026-11-20T23:00:00Z"
    assert (
        refresh_market_snapshot(
            regressive, cache_path=cache, now=NOW, registry=REGISTRY
        )["status"]
        == "failed"
    )
    assert cache.read_bytes() == original


def test_refresh_cli_direct_execution_and_input_failure_is_safe(tmp_path):
    cache = tmp_path / "market.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/refresh_market_snapshot.py"),
            "--input",
            str(tmp_path / "missing.json"),
            "--cache",
            str(cache),
            "--now",
            NOW,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2 and "FileNotFoundError" in result.stdout
    assert not cache.exists() and cache.with_suffix(".refresh.json").exists()


def test_gap_manifest_never_contains_invented_prices():
    snapshot = gap_snapshot(
        "Synthetic unavailable-state test",
        checked_at=NOW,
        calendar_data=json.loads(
            (ROOT / "neocloud/data/market_calendar.json").read_text()
        ),
    )
    assert snapshot["status"] == "unavailable" and snapshot["as_of"] is None
    assert snapshot["availability_checked_at"] == NOW
    assert snapshot["expected_end_session"] == "2026-11-20"
    assert len(snapshot["companies"]) == 9
    assert all(
        c["price"]["value"] is None and not c["history"] for c in snapshot["companies"]
    )
    assert all(
        r["value"] is None for c in snapshot["companies"] for r in c["returns"].values()
    )


def test_checked_in_cache_remains_refreshable_without_rewriting_tests():
    snapshot = load_market_snapshot()
    assert snapshot["schema_version"] == 1
    assert snapshot["availability_checked_at"]
    if snapshot["status"] == "unavailable":
        assert snapshot["as_of"] is None
        assert all(
            c["price"]["value"] is None and not c["history"]
            for c in snapshot["companies"]
        )
    else:
        assert snapshot["status"] in ("ready", "partial")
        assert snapshot["license"]["status"] == "public_display_permitted"
        assert snapshot["as_of"] and snapshot["end_session"]
        assert snapshot["price_basis"] in (
            "split_adjusted_price_return",
            "total_return",
        )
        for c in snapshot["companies"]:
            for result in c["returns"].values():
                if result["status"] == "available":
                    assert (
                        result["end_session"] == snapshot["end_session"]
                        and result["value"] is not None
                    )


def test_unexplained_large_price_move_is_a_review_boundary_not_a_fake_split(raw):
    prices = raw["companies"][1]["prices"]
    index = next(i for i, p in enumerate(prices) if p["date"] == "2026-11-02")
    for point in prices[index:]:
        point["close"] *= 10
    result = build(raw)
    company = result["companies"][1]
    assert company["returns"]["1m"]["value"] is None
    assert company["history"][index]["break_reason"].startswith(
        "Large inter-session move is unverified"
    )
    assert result["normalizations"]["1m"]["start_session"] == "2026-11-02"
    prices[index].update(
        continuity_verified=True,
        continuity_source_url="https://example.com/verified-move",
    )
    assert build(raw)["companies"][1]["returns"]["1m"]["status"] == "available"


def test_provider_attribution_is_preserved_as_text_without_arbitrary_html(raw):
    raw["provider"][
        "attribution_text"
    ] = "Synthetic data courtesy of Example Provider; fixture only."
    result = build(raw)
    assert result["license"]["attribution_text"] == raw["provider"]["attribution_text"]
    raw["provider"]["attribution_text"] = "<script>private()</script>"
    with pytest.raises(ValueError, match="plain text"):
        build(raw)


@pytest.mark.parametrize(
    "payload",
    [None, [], {"provider": None}, {"provider": [], "calendar": {}, "companies": []}],
)
def test_malformed_non_object_source_keeps_last_good_cache(raw, tmp_path, payload):
    cache = tmp_path / "market.json"
    refresh_market_snapshot(raw, cache_path=cache, now=NOW, registry=REGISTRY)
    before = cache.read_bytes()
    result = refresh_market_snapshot(
        payload, cache_path=cache, now=NOW, registry=REGISTRY
    )
    assert result["status"] == "failed" and cache.read_bytes() == before


def test_recorded_later_failed_attempt_drives_deterministic_cache_age(raw, tmp_path):
    cache = tmp_path / "market.json"
    refresh_market_snapshot(raw, cache_path=cache, now=NOW, registry=REGISTRY)
    cache.with_suffix(".refresh.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "last_attempt_at": "2026-11-24T01:00:00Z",
                "error_type": "OSError",
            }
        )
    )
    result = load_market_snapshot(cache)
    assert result["refresh"]["status"] == "failed" and result["refresh"]["age_days"] > 2
    assert result["expected_end_session"] == "2026-11-23" and result["refresh"]["stale"]
    gap = gap_snapshot("No source", checked_at=NOW)
    cache.write_text(json.dumps(gap))
    result = load_market_snapshot(cache)
    assert (
        result["availability_checked_at"] == "2026-11-24T01:00:00Z"
        and result["as_of"] is None
    )
