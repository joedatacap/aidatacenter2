"""Separate, licensed end-of-day market snapshots for Neocloud Watch.

Financial research is never read-modified-written here. A confirmed exchange
calendar defines endpoints; a missing company close never substitutes an older
session. Imported files must explicitly establish public-display permission.
"""

from __future__ import annotations
import calendar as month_calendar
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import tempfile
import fcntl
import hashlib
from urllib.parse import urlparse, parse_qsl
import ipaddress
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "neocloud/data/market_snapshot.json"
FOCUS = {
    "CRWV": "CoreWeave",
    "NBIS": "Nebius",
    "IREN": "IREN",
    "APLD": "Applied Digital",
    "HUT": "Hut 8",
    "WULF": "TeraWulf",
    "WYFI": "WhiteFiber",
    "SHAZ": "SharonAI Holdings",
    "AGPU": "Axe Compute",
}
WINDOW_LABELS = {
    "1w": "this week",
    "1m": "this month",
    "3m": "over three months",
    "ytd": "year to date",
}
BASES = {"split_adjusted_price_return", "total_return"}


def timestamp(value):
    d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Explicit timezone required")
    return d.astimezone(timezone.utc)


def utc(value):
    return timestamp(value).isoformat().replace("+00:00", "Z")


def number(value, positive=False):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a price")
    try:
        n = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid market value") from exc
    if not n.is_finite() or (positive and n <= 0):
        raise ValueError("Market value must be finite and positive")
    return n


def public_url(value):
    parsed = urlparse(str(value))
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Public HTTPS evidence URL required")
    if host in ("localhost", "localhost.localdomain") or host.endswith(
        (".internal", ".local")
    ):
        raise ValueError("Non-public evidence host")
    try:
        if ipaddress.ip_address(host).is_private:
            raise ValueError("Non-public evidence host")
    except ValueError as exc:
        if str(exc) == "Non-public evidence host":
            raise
    if any(
        re.search(
            r"(?i)(token|api.?key|secret|password|signature|credential|authorization|access.?key)",
            key,
        )
        for key, _ in parse_qsl(parsed.query)
    ):
        raise ValueError("Credential-bearing source URL cannot enter public cache")
    return str(value)


def size_band(value):
    if value is None:
        return "unknown"
    n = number(value, True)
    return (
        "large"
        if n >= 10_000_000_000
        else "mid" if n >= 2_000_000_000 else "small" if n >= 300_000_000 else "micro"
    )


def validate_calendar(raw, now):
    if raw.get("confirmed") is not True:
        raise ValueError("Exchange calendar is not confirmed")
    public_url(raw["source_url"])
    if timestamp(raw["verified_at"]) > now:
        raise ValueError("Future calendar verification")
    start, end = date.fromisoformat(raw["coverage_start"]), date.fromisoformat(
        raw["coverage_end"]
    )
    local = now.astimezone(ZoneInfo("America/New_York")).date()
    if not start <= local <= end:
        raise ValueError(
            "Calendar coverage does not confirm the current session endpoint"
        )
    sessions = {}
    for row in raw["sessions"]:
        session = date.fromisoformat(row["date"])
        close = timestamp(row["close_at"])
        if (
            row["date"] in sessions
            or not start <= session <= end
            or session.weekday() > 4
        ):
            raise ValueError("Invalid or duplicate exchange session")
        close_local = close.astimezone(ZoneInfo("America/New_York"))
        if close_local.date() != session or (
            close_local.hour,
            close_local.minute,
        ) not in ((13, 0), (16, 0)):
            raise ValueError("Exchange close timestamp does not match the session")
        sessions[row["date"]] = close
    closures = {
        row["date"] for row in raw.get("closed_sessions", []) if row.get("reason")
    }
    if closures.intersection(sessions):
        raise ValueError("Exchange date is both closed and trading")
    day = start
    while day <= end:
        if (
            day.weekday() < 5
            and day.isoformat() not in sessions
            and day.isoformat() not in closures
        ):
            raise ValueError("Calendar omits a weekday without a confirmed closure")
        day += timedelta(days=1)
    completed = sorted(day for day, close in sessions.items() if close <= now)
    if not completed:
        raise ValueError("No confirmed completed exchange session")
    return sessions, completed[-1]


def window_target(end, window):
    d = date.fromisoformat(end)
    if window == "1w":
        return (d - timedelta(days=7)).isoformat()
    if window == "ytd":
        return date(d.year - 1, 12, 31).isoformat()
    months = {"1m": 1, "3m": 3}[window]
    year = d.year - (1 if d.month <= months else 0)
    month = (d.month - months - 1) % 12 + 1
    return date(
        year, month, min(d.day, month_calendar.monthrange(year, month)[1])
    ).isoformat()


def window_metadata(end, sessions):
    result = {}
    for key, label in WINDOW_LABELS.items():
        target = window_target(end, key)
        eligible = sorted(day for day in sessions if day <= target)
        result[key] = {
            "label": label,
            "target_start": target,
            "start_session": eligible[-1] if eligible else None,
            "end_session": end,
        }
    return result


def unavailable(reason, **fields):
    return dict(value=None, status="unavailable", reason=reason, **fields)


def registry_rows(registry=None):
    if registry is None:
        payload = json.loads((ROOT / "neocloud/data/watch_markets.json").read_text())
        caps = {c["ticker"]: c["market_observation"] for c in payload["companies"]}
        return [
            {
                "id": t.lower(),
                "ticker": t,
                "name": name,
                "listing_status": "listed",
                "capitalization_blocker": caps.get(t, {}).get("ratio_blocker"),
            }
            for t, name in FOCUS.items()
        ]
    return [
        {
            "id": c["id"],
            "ticker": c["ticker"],
            "name": c["name"],
            "listing_status": c.get(
                "listing_status",
                (c.get("financing") or {}).get("listing_status", "listed"),
            ),
            "capitalization_blocker": c.get("capitalization_blocker")
            or (c.get("market_cap") or {}).get("ratio_blocker")
            or ((c.get("financing") or {}).get("v2", {}).get("market_cap") or {}).get(
                "ratio_blocker"
            ),
        }
        for c in registry
        if c["ticker"] in FOCUS
    ]


def manual_cap_context(identity):
    """Preserve the previously published, manually reviewed dated size context."""
    payload = json.loads((ROOT / "neocloud/data/watch_markets.json").read_text())
    record = next(
        (
            c.get("market_observation")
            for c in payload["companies"]
            if c["id"] == identity["id"]
        ),
        None,
    )
    if not record:
        return unavailable(
            "No reviewed market capitalization.",
            currency=None,
            as_of=None,
            size_band="unknown",
            share_basis=None,
            source_url=None,
        )
    source_ids = record.get("source_ids", [])
    source = next((s for s in payload["sources"] if s["id"] in source_ids), {})
    blocker = identity.get("capitalization_blocker") or record.get("ratio_blocker")
    return {
        "value": record["value"],
        "currency": record["currency"],
        "as_of": record["as_of"],
        "status": "unreconciled" if blocker else "dated_manual",
        "size_band": "unknown" if blocker else size_band(record["value"]),
        "share_basis": record["definition"],
        "reason": blocker
        or "Previously reviewed provider snapshot; dated size context, not a newly refreshed capitalization.",
        "source_url": source.get("url"),
        "source_ids": source_ids,
    }


def gap_snapshot(reason, *, checked_at, registry=None, calendar_data=None):
    checked = timestamp(checked_at)
    expected = None
    if calendar_data:
        try:
            _, expected = validate_calendar(calendar_data, checked)
        except (KeyError, ValueError, TypeError):
            pass
    return {
        "schema_version": 1,
        "status": "unavailable",
        "availability_checked_at": utc(checked_at),
        "as_of": None,
        "expected_end_session": expected,
        "end_session": None,
        "price_basis": None,
        "license": {
            "status": "unverified",
            "provider": None,
            "source_url": None,
            "permission_url": None,
        },
        "gap_reason": reason,
        "windows": {
            key: {
                "label": label,
                "target_start": window_target(expected, key) if expected else None,
                "start_session": None,
                "end_session": expected,
            }
            for key, label in WINDOW_LABELS.items()
        },
        "companies": [
            dict(
                c,
                exchange=None,
                currency=None,
                market_cap=manual_cap_context(c),
                price=unavailable(reason, date=None, source_url=None),
                returns={
                    k: unavailable(reason, start_session=None, end_session=expected)
                    for k in WINDOW_LABELS
                },
                history=[],
                history_status="unavailable",
                history_reason=reason,
            )
            for c in registry_rows(registry)
        ],
        "normalizations": {
            key: {
                "status": "unavailable",
                "reason": reason,
                "start_session": None,
                "end_session": expected,
                "shortened": False,
                "series": [],
            }
            for key in WINDOW_LABELS
        },
        "refresh": {
            "status": "source_unavailable",
            "last_attempt_at": utc(checked_at),
            "last_success_at": None,
            "error_type": None,
            "age_days": None,
            "stale": False,
        },
        "calendar": deepcopy(calendar_data) if calendar_data else None,
    }


def validate_permission(provider):
    if (
        not all(
            provider.get(k) is True
            for k in (
                "public_display_permitted",
                "public_redistribution_permitted",
                "cached_history_permitted",
            )
        )
        or provider.get("permission_status") != "verified_public_display"
    ):
        raise ValueError(
            "Public static redistribution, downloadable cached history and display permission not verified"
        )
    for key in ("source_url", "permission_url"):
        public_url(provider[key])
    if not provider.get("permission_excerpt") or not provider.get("name"):
        raise ValueError("Provider and permission evidence required")
    attribution = provider.get("attribution_text", "")
    if (
        not isinstance(attribution, str)
        or len(attribution) > 2048
        or re.search(r"<[^>]*>", attribution)
    ):
        raise ValueError("Attribution must be bounded plain text, not HTML")
    timestamp(provider["terms_reviewed_at"])
    if provider.get("price_basis") not in BASES:
        raise ValueError(
            "Price/dividend adjustment method must be explicit and consistent"
        )


def current_segment(company):
    rows = company.get("history", [])
    if not rows:
        return []
    segment = rows[-1]["segment"]
    return [p for p in rows if p["segment"] == segment]


def normalize_common(companies, window):
    """Normalize only an intersection of contiguous, verified current segments."""
    selected = [c for c in companies if c.get("listing_status") == "listed"]
    if not selected:
        return {
            "status": "unavailable",
            "reason": "Select at least one public company.",
            "start_session": None,
            "end_session": window.get("end_session"),
            "shortened": False,
            "series": [],
        }
    maps = [
        {p["date"]: p for p in current_segment(c) if p["date"] <= window["end_session"]}
        for c in selected
    ]
    if any(not rows or window["end_session"] not in rows for rows in maps):
        return {
            "status": "unavailable",
            "reason": "Every selected company needs a verified close at the same end session.",
            "start_session": None,
            "end_session": window["end_session"],
            "shortened": False,
            "series": [],
        }
    common = set.intersection(*(set(rows) for rows in maps))
    nominal = window.get("start_session") or window["target_start"]
    dates = sorted(day for day in common if day >= nominal)
    if len(dates) < 2:
        return {
            "status": "unavailable",
            "reason": "Fewer than two common trading closes in a continuous verified segment.",
            "start_session": None,
            "end_session": window["end_session"],
            "shortened": False,
            "series": [],
        }
    start = dates[0]
    return {
        "status": "available",
        "start_session": start,
        "end_session": window["end_session"],
        "shortened": start != window.get("start_session"),
        "reason": (
            "Common available period shortened for listing/history gaps or a corporate-action boundary."
            if start != window.get("start_session")
            else "All selected companies start at 100 on the same verified session."
        ),
        "series": [
            {
                "id": c["id"],
                "points": [
                    {
                        "date": day,
                        "value": float(
                            number(rows[day]["close"], True)
                            / number(rows[start]["close"], True)
                            * 100
                        ),
                    }
                    for day in dates
                ],
            }
            for c, rows in zip(selected, maps)
        ],
    }


def build_market_snapshot(raw, *, now, registry=None):
    if (
        not isinstance(raw, dict)
        or not isinstance(raw.get("provider"), dict)
        or not isinstance(raw.get("calendar"), dict)
        or not isinstance(raw.get("companies"), list)
    ):
        raise ValueError(
            "Market input requires provider/calendar objects and a companies array"
        )
    if raw.get("schema_version") != 1:
        raise ValueError("Unsupported market import version")
    if not all(isinstance(c, dict) for c in raw["companies"]):
        raise ValueError("Market company record must be an object")
    now = timestamp(now)
    provider = raw["provider"]
    validate_permission(provider)
    if timestamp(provider["terms_reviewed_at"]) > now:
        raise ValueError("Future licensing verification")
    observed = timestamp(raw["observed_at"])
    if observed > now:
        raise ValueError("Future market observation timestamp")
    sessions, end = validate_calendar(raw["calendar"], now)
    windows = window_metadata(end, sessions)
    rows = registry_rows(registry)
    incoming = {c["id"]: c for c in raw["companies"]}
    if len(incoming) != len(raw["companies"]):
        raise ValueError("Duplicate market company identity")
    result = []
    for identity in rows:
        source = incoming.get(identity["id"], {})
        c = dict(
            identity, exchange=source.get("exchange"), currency=source.get("currency")
        )
        if source and source.get("ticker") != identity["ticker"]:
            raise ValueError("Canonical ticker does not match registry")
        if (
            source
            and source.get("listing_status", "listed") != identity["listing_status"]
        ):
            raise ValueError("Listing status conflicts with registry")
        if source and (
            source.get("currency") != "USD"
            or source.get("exchange") not in ("XNYS", "XNAS", "NYSE", "NASDAQ")
        ):
            raise ValueError("Verified USD quote currency and exchange required")
        if not isinstance(source.get("prices", []), list) or not isinstance(
            source.get("corporate_actions", []), list
        ):
            raise ValueError("Prices and corporate actions must be arrays")
        if not all(
            isinstance(a, dict) for a in source.get("corporate_actions", [])
        ) or not all(isinstance(p, dict) for p in source.get("prices", [])):
            raise ValueError("Price/action rows must be objects")
        if source.get("market_cap") is not None and not isinstance(
            source["market_cap"], dict
        ):
            raise ValueError("Market capitalization must be an object")
        if source.get("quote") is not None and not isinstance(source["quote"], dict):
            raise ValueError("Quote must be an object")
        actions = sorted(
            source.get("corporate_actions", []), key=lambda a: a["effective_date"]
        )
        breaks = set()
        known_actions = []
        for action in actions:
            when = date.fromisoformat(action["effective_date"]).isoformat()
            kind = action["type"]
            verified = (
                action.get("verified") is True
                and action.get("source_url")
                and action.get("series_treatment") == "reflected_in_series"
            )
            if action.get("source_url"):
                public_url(action["source_url"])
            if kind in ("split", "reverse_split"):
                if action.get("ratio") is None or number(action["ratio"], True) <= 0:
                    verified = False
            elif kind == "dividend":
                # Price returns deliberately exclude dividends; total-return series include them.
                verified = (
                    action.get("verified") is True
                    and bool(action.get("source_url"))
                    and action.get("series_treatment")
                    == (
                        "excluded_from_price_return"
                        if provider["price_basis"] == "split_adjusted_price_return"
                        else "included_in_total_return"
                    )
                )
            elif kind == "ticker_change":
                verified = (
                    verified
                    and bool(action.get("from_ticker"))
                    and bool(action.get("to_ticker"))
                )
            else:
                verified = False
            if not verified:
                breaks.add(when)
            safe_action = {
                key: deepcopy(action[key])
                for key in (
                    "effective_date",
                    "type",
                    "verified",
                    "source_url",
                    "series_treatment",
                    "ratio",
                    "from_ticker",
                    "to_ticker",
                )
                if key in action
            }
            known_actions.append(dict(safe_action, continuity_verified=bool(verified)))
        chain = [
            a
            for a in known_actions
            if a["type"] == "ticker_change"
            and a["continuity_verified"]
            and a["effective_date"] <= end
        ]
        for prior, later in zip(chain, chain[1:]):
            if prior["to_ticker"] != later["from_ticker"]:
                raise ValueError("Ticker-change predecessor chain is broken")
        if chain and chain[-1]["to_ticker"] != identity["ticker"]:
            raise ValueError("Ticker-change chain does not end at the canonical ticker")
        history = []
        segment = 0
        previous = None
        for price in sorted(source.get("prices", []), key=lambda p: p["date"]):
            day = date.fromisoformat(price["date"]).isoformat()
            value = number(price["close"], True)
            if day not in sessions:
                raise ValueError(
                    "Price observation is not a confirmed exchange session"
                )
            if sessions[day] > observed or sessions[day] > now:
                raise ValueError("Price close had not completed at observation time")
            if previous == day:
                raise ValueError("Duplicate closing price date")
            if price.get("basis", provider["price_basis"]) != provider["price_basis"]:
                raise ValueError("Mixed dividend/split adjustment methods")
            verified_changes = chain
            expected_symbol = (
                verified_changes[0]["from_ticker"]
                if verified_changes
                else source.get("ticker")
            )
            for action in verified_changes:
                if day >= action["effective_date"]:
                    expected_symbol = action["to_ticker"]
            symbol = price.get(
                "ticker",
                (
                    expected_symbol
                    if source.get("predecessor_series_verified") is True
                    else source.get("ticker")
                ),
            )
            if symbol != expected_symbol:
                raise ValueError("Predecessor ticker chronology is not verified")
            expected = [d for d in sessions if previous and previous < d < day]
            boundary = any(
                (previous is None or previous < b) and b <= day for b in breaks
            )
            extreme = False
            if history:
                move = value / number(history[-1]["close"], True)
                extreme = move > Decimal(2) or move < Decimal("0.5")
                if (
                    extreme
                    and price.get("continuity_verified") is True
                    and price.get("continuity_source_url")
                ):
                    public_url(price["continuity_source_url"])
                    extreme = False
            if history and (expected or boundary or extreme):
                segment += 1
            history.append(
                {
                    "date": day,
                    "close": float(value),
                    "segment": segment,
                    "break_reason": (
                        "Large inter-session move is unverified; it is not assumed to be a split."
                        if extreme
                        else (
                            "Missing exchange session or unverified corporate-action boundary."
                            if expected or boundary
                            else None
                        )
                    ),
                }
            )
            previous = day
        c["history"] = history
        c["corporate_actions"] = known_actions
        c["history_status"] = "available" if history else "unavailable"
        c["history_reason"] = (
            "Only validated closes; gaps and unverified corporate actions start new segments."
        )
        last = history[-1] if history else None
        c["last_adjusted_close"] = (
            {
                "value": last["close"],
                "date": last["date"],
                "unit": (
                    "total_return_index"
                    if provider["price_basis"] == "total_return"
                    else "split_adjusted_close"
                ),
                "source_url": provider["source_url"],
            }
            if last
            else None
        )
        quote = source.get("quote")
        if quote and quote.get("value") is not None:
            quote_date = date.fromisoformat(quote["date"]).isoformat()
            quote_value = number(quote["value"], True)
            public_url(quote["source_url"])
            if (
                quote.get("kind") != "closing_price"
                or quote.get("currency") != source["currency"]
                or quote.get("exchange") != source["exchange"]
            ):
                raise ValueError(
                    "Literal closing quote must identify its currency and exchange"
                )
            if quote_date not in sessions or sessions[quote_date] > observed:
                raise ValueError(
                    "Literal quote session had not completed at observation time"
                )
            c["price"] = {
                "value": float(quote_value),
                "date": quote_date,
                "currency": quote["currency"],
                "exchange": quote["exchange"],
                "status": "available" if quote_date == end else "stale",
                "reason": (
                    None
                    if quote_date == end
                    else "Literal company quote is older than the confirmed end session."
                ),
                "source_url": quote["source_url"],
                "kind": "closing_price",
            }
        else:
            c["price"] = unavailable(
                "Literal exchange closing quote unavailable; adjusted series is used only for returns.",
                date=None,
                source_url=provider["source_url"],
            )
        c["returns"] = {}
        for key, window in windows.items():
            start = window["start_session"]
            eligible = [p for p in history if start and start <= p["date"] <= end]
            expected = sorted(day for day in sessions if start and start <= day <= end)
            reason = None
            if identity["listing_status"] != "listed":
                reason = "Private companies are excluded from stock-return rankings."
            elif not start:
                reason = "Confirmed calendar coverage does not establish the required start session."
            elif source.get("listed_on") and start < source["listed_on"]:
                reason = "IPO/listing occurred after the required return-window start."
            elif not eligible or eligible[0]["date"] != start:
                reason = (
                    "Required starting close unavailable; history is not extrapolated."
                )
            elif eligible[-1]["date"] != end:
                reason = "Required common end-session close unavailable or stale."
            elif [p["date"] for p in eligible] != expected:
                reason = "Missing trading sessions or suspension inside the requested window."
            elif len({p["segment"] for p in eligible}) != 1:
                reason = "Unverified corporate action prevents a continuous comparable return."
            c["returns"][key] = (
                unavailable(reason, start_session=start, end_session=end)
                if reason
                else {
                    "value": float(
                        (
                            number(eligible[-1]["close"]) / number(eligible[0]["close"])
                            - 1
                        )
                        * 100
                    ),
                    "status": "available",
                    "reason": None,
                    "start_session": start,
                    "end_session": end,
                    "start_close": eligible[0]["close"],
                    "end_close": eligible[-1]["close"],
                    "formula": "close_ratio_minus_one/v1",
                    "source_url": provider["source_url"],
                }
            )
        cap = source.get("market_cap")
        blocker = identity.get("capitalization_blocker") or (cap or {}).get(
            "ratio_blocker"
        )
        if cap and cap.get("value") is not None:
            public_url(cap["source_url"])
            number(cap["value"], True)
            cap_date = date.fromisoformat(cap["as_of"])
            if cap.get("currency") != "USD":
                raise ValueError("Capitalization currency must be USD")
            if cap_date > observed.date():
                raise ValueError("Future market capitalization date")
            basis = cap.get("share_basis", "")
            valid_basis = bool(basis) and not re.search(
                r"(?i)(weighted.?average|earnings.?per.?share|EPS)", str(basis)
            )
            verified = cap.get("status") == "verified" and valid_basis and not blocker
            c["market_cap"] = {
                "value": float(number(cap["value"])),
                "currency": cap.get("currency", "USD"),
                "as_of": cap["as_of"],
                "status": "verified" if verified else "unreconciled",
                "size_band": size_band(cap["value"]) if verified else "unknown",
                "share_basis": cap.get("share_basis"),
                "reason": blocker
                or (
                    None
                    if verified
                    else "Capitalization/share-count basis not reconciled."
                ),
                "source_url": cap["source_url"],
            }
        else:
            c["market_cap"] = manual_cap_context(identity)
        result.append(c)
    available = sum(
        any(r["status"] == "available" for r in c["returns"].values()) for c in result
    )
    if not available:
        raise ValueError("No company has a valid comparable market-return window")
    calendar_public = {
        key: deepcopy(raw["calendar"][key])
        for key in (
            "exchange",
            "confirmed",
            "source_url",
            "verified_at",
            "coverage_start",
            "coverage_end",
        )
    }
    calendar_public["sessions"] = [
        {key: row[key] for key in ("date", "close_at")}
        for row in raw["calendar"]["sessions"]
    ]
    calendar_public["closed_sessions"] = [
        {key: row[key] for key in ("date", "reason")}
        for row in raw["calendar"].get("closed_sessions", [])
    ]
    return {
        "schema_version": 1,
        "status": (
            "ready"
            if all(c["returns"]["1m"]["status"] == "available" for c in result)
            else "partial"
        ),
        "availability_checked_at": utc(now.isoformat()),
        "as_of": utc(raw["observed_at"]),
        "end_session": end,
        "expected_end_session": end,
        "price_basis": provider["price_basis"],
        "license": {
            "status": "public_display_permitted",
            "provider": provider["name"],
            "source_url": provider["source_url"],
            "permission_url": provider["permission_url"],
            "permission_excerpt": provider["permission_excerpt"],
            "terms_reviewed_at": provider["terms_reviewed_at"],
            "attribution_text": provider.get("attribution_text", ""),
            "public_static_redistribution": True,
            "downloadable_cache_permitted": True,
        },
        "gap_reason": None,
        "calendar": calendar_public,
        "windows": windows,
        "companies": result,
        "normalizations": {
            key: normalize_common(result, window) for key, window in windows.items()
        },
        "refresh": {
            "status": "success",
            "last_attempt_at": utc(now.isoformat()),
            "last_success_at": utc(now.isoformat()),
            "error_type": None,
            "age_days": float((now - observed).total_seconds() / 86400),
            "stale": False,
        },
    }


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _refresh_market_snapshot(
    raw, *, cache_path=CACHE, now, registry=None, allow_partial_regression=False
):
    """Replace the cache only after complete validation; failed refresh retains bytes."""
    cache_path = Path(cache_path)
    status_path = cache_path.with_suffix(".refresh.json")
    try:
        snapshot = build_market_snapshot(raw, now=now, registry=registry)
        if cache_path.exists():
            old = json.loads(cache_path.read_text())
            if old.get("status") in ("ready", "partial"):
                if (
                    timestamp(snapshot["as_of"]) < timestamp(old["as_of"])
                    or snapshot["end_session"] < old["end_session"]
                ):
                    raise ValueError("Refusing a regressive market snapshot")
                previous = {
                    (c["id"], key)
                    for c in old["companies"]
                    for key, r in c["returns"].items()
                    if r["status"] == "available"
                }
                new = {
                    (c["id"], key)
                    for c in snapshot["companies"]
                    for key, r in c["returns"].items()
                    if r["status"] == "available"
                }
                if not allow_partial_regression and not previous.issubset(new):
                    raise ValueError(
                        "Partial source would remove previously verified return coverage"
                    )
    except (
        ValueError,
        KeyError,
        TypeError,
        InvalidOperation,
        json.JSONDecodeError,
    ) as exc:
        status = {
            "status": "failed",
            "last_attempt_at": utc(now),
            "error_type": type(exc).__name__,
            "reason": "Market source failed eligibility/calendar/data validation; last good snapshot retained.",
        }
        atomic_json(status_path, status)
        return {
            "status": "failed",
            "cache_replaced": False,
            "error_type": type(exc).__name__,
        }
    atomic_json(cache_path, snapshot)
    atomic_json(status_path, snapshot["refresh"])
    return {
        "status": "success",
        "cache_replaced": True,
        "as_of": snapshot["as_of"],
        "end_session": snapshot["end_session"],
    }


def refresh_market_snapshot(
    raw, *, cache_path=CACHE, now, registry=None, allow_partial_regression=False
):
    """Serialize compare-and-replace across writers so an older refresh cannot win."""
    lock_name = (
        "neocloud-market-"
        + hashlib.sha256(str(Path(cache_path).resolve()).encode()).hexdigest()
        + ".lock"
    )
    with open(Path(tempfile.gettempdir()) / lock_name, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _refresh_market_snapshot(
            raw,
            cache_path=cache_path,
            now=now,
            registry=registry,
            allow_partial_regression=allow_partial_regression,
        )


def load_market_snapshot(path=CACHE, *, now=None, registry=None):
    path = Path(path)
    cached = json.loads(path.read_text()) if path.exists() else None
    status_path = path.with_suffix(".refresh.json")
    attempt = json.loads(status_path.read_text()) if status_path.exists() else {}
    if not isinstance(attempt, dict):
        attempt = {}
    if attempt.get("last_attempt_at"):
        try:
            timestamp(attempt["last_attempt_at"])
        except (ValueError, TypeError):
            attempt = {}
    if now is None:
        # Reproducible builds advance only to an explicitly recorded check/refresh,
        # never to an invented price observation or the financial research cutoff.
        dates = [
            value
            for value in (
                (cached or {}).get("availability_checked_at"),
                attempt.get("last_attempt_at"),
            )
            if value
        ]
        now = max(dates, key=timestamp) if dates else "2026-11-22T00:28:36Z"
    now = timestamp(now)
    if not cached:
        return gap_snapshot(
            "No reviewed, licensed market snapshot is configured.",
            checked_at=now.isoformat(),
            registry=registry,
        )
    result = deepcopy(cached)
    if result.get("schema_version") != 1:
        raise ValueError("Unsupported market cache version")
    if result.get("status") == "unavailable":
        if registry is not None:
            known = {c["id"]: c for c in registry_rows(registry)}
            for company in result["companies"]:
                if company["id"] in known:
                    company["market_cap"] = manual_cap_context(known[company["id"]])
        if attempt:
            result["refresh"].update(attempt)
            result["availability_checked_at"] = utc(now.isoformat())
        if result.get("calendar"):
            try:
                _, result["expected_end_session"] = validate_calendar(
                    result["calendar"], now
                )
            except (ValueError, KeyError, TypeError):
                result["expected_end_session"] = None
        return result
    license_record = result.get("license", {})
    if (
        license_record.get("status") != "public_display_permitted"
        or license_record.get("public_static_redistribution") is not True
        or license_record.get("downloadable_cache_permitted") is not True
    ):
        raise ValueError(
            "Cached source lacks public static/downloadable redistribution permission"
        )
    result["refresh"].update(
        {
            k: v
            for k, v in attempt.items()
            if k not in ("last_success_at", "stale", "age_days")
        }
    )
    result["refresh"]["stale"] = False
    try:
        _, expected = validate_calendar(result["calendar"], now)
        result["calendar_status"] = "confirmed"
    except (ValueError, KeyError, TypeError):
        expected = None
        result["calendar_status"] = "coverage_unconfirmed"
        result["refresh"]["stale"] = True
    result["expected_end_session"] = expected
    if expected and expected != result["end_session"]:
        result["refresh"]["stale"] = True
    result["refresh"]["age_days"] = float(
        (now - timestamp(result["as_of"])).total_seconds() / 86400
    )
    return result
