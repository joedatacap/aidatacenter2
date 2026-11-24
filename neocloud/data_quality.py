"""Add dated size and disclosure reviews without rewriting historical research.

The November financial ledger remains a dated baseline. New disclosure checks
record what was actually checked, not a blanket assertion that every statement,
contract or debt instrument has been refreshed. Provider capitalization can
support a dated size category while a historical debt-ratio blocker remains.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import ipaddress
import re
from urllib.parse import parse_qsl, urlparse

from neocloud.watch import market_cap_band

CLASSIFIABLE_SIZE = {"provider_reported", "verified", "dated_provider", "reconciled"}
UNRESOLVED_SIZE = {
    "unavailable",
    "conflicting",
    "discrepant",
    "not_researched",
    "unresolved",
    "withheld",
    "unverified",
    "source_access_incomplete",
    "not_established",
}
REVIEW_STATUS = {"updated", "no_material_update", "source_access_incomplete"}


def public_source(value):
    """Evidence links are public HTTPS references, never authenticated fetch URLs."""
    if not isinstance(value, str):
        raise ValueError("Evidence source URL must be a string")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Evidence requires a public HTTPS URL without credentials")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(
        (".local", ".internal")
    ):
        raise ValueError("Evidence source cannot be a private host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ValueError("Evidence source cannot be a private address")
    credential_keys = {
        "key",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "auth",
        "password",
        "signature",
        "sig",
        "secret",
    }
    if any(key.lower() in credential_keys for key, _ in parse_qsl(parsed.query)):
        raise ValueError("Authenticated evidence URL cannot enter the public dataset")
    return value


def calendar_date(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO date") from exc
    return parsed


def checked_instant(value):
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("Disclosure checked_at requires an explicit timezone instant")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Disclosure checked_at requires an ISO instant") from exc
    if result.tzinfo is None:
        raise ValueError("Disclosure checked_at requires an explicit timezone")
    return result.astimezone(timezone.utc)


def positive_dollars(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a capitalization value")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid capitalization value") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError("Capitalization must be finite and positive; unknown is null")
    return int(result) if result == result.to_integral_value() else float(result)


def size_category(value):
    if value is None:
        return "unknown"
    value = positive_dollars(value)
    return market_cap_band(value)


def nonempty_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} requires text")
    return value


def supporting_passages(raw):
    passages = raw.get("supporting_passages")
    if not isinstance(passages, list) or not passages:
        raise ValueError("An evidence record requires supporting passages from its linked source")
    return [nonempty_text(text, "Supporting passage") for text in passages]


def size_record(raw, reviewed_at):
    for key in (
        "ticker",
        "as_of",
        "value_usd",
        "basis",
        "status",
        "source_url",
        "source_date",
        "share_sources",
        "discrepancy",
    ):
        if key not in raw:
            raise ValueError(f"Size observation missing {key}")
    as_of = calendar_date(raw["as_of"], "Size as_of")
    source_date = calendar_date(raw["source_date"], "Size source_date")
    if as_of > reviewed_at or source_date > reviewed_at:
        raise ValueError("Size observation/source date is after its review date")
    basis = nonempty_text(raw["basis"], "Capitalization basis")
    if re.search(
        r"(?i)weighted[\s-]*average|\bEPS\b|earnings[\s-]*per[\s-]*share", basis
    ):
        raise ValueError(
            "Weighted-average EPS shares cannot establish current capitalization"
        )
    public_source(raw["source_url"])
    status = raw["status"]
    if status not in CLASSIFIABLE_SIZE | UNRESOLVED_SIZE:
        raise ValueError("Unknown capitalization review status")
    value = None if raw["value_usd"] is None else positive_dollars(raw["value_usd"])
    if status in CLASSIFIABLE_SIZE and value is None:
        raise ValueError("Classifiable capitalization requires a sourced numeric value")
    if not isinstance(raw["discrepancy"], str):
        raise ValueError("Capitalization discrepancy must be text")
    if not isinstance(raw["share_sources"], list):
        raise ValueError("Share sources must be an explicit array")
    share_sources = []
    for source in raw["share_sources"]:
        if not isinstance(source, dict):
            raise ValueError("Share evidence must be an object")
        share_sources.append(
            {
                "url": public_source(source.get("url")),
                "supporting_passages": supporting_passages(source),
                "description": nonempty_text(
                    source.get("description"), "Share evidence description"
                ),
            }
        )
    if status == "reconciled" and not share_sources:
        raise ValueError("Reconciled capitalization needs independent share evidence")
    excerpt = raw.get("source_excerpt")
    if status in {"provider_reported", "dated_provider"}:
        excerpt = nonempty_text(excerpt, "Attributed provider source_excerpt")
    if excerpt is not None and (not isinstance(excerpt, str) or len(excerpt) > 2000):
        raise ValueError("Provider source_excerpt must be a short text passage")
    qualification = raw.get("qualification_label")
    if qualification is not None:
        nonempty_text(qualification, "Qualification label")
        if len(qualification) > 160 or re.search(r"<[^>]*>", qualification):
            raise ValueError("Qualification label must be short plain text")
    record = {
        "ticker": raw["ticker"],
        "as_of": raw["as_of"],
        "value_usd": value,
        "value": value,
        "currency": "USD",
        "basis": basis,
        "share_basis": basis,
        "status": status,
        "source_url": raw["source_url"],
        "source_date": raw["source_date"],
        "source_excerpt": excerpt,
        "share_sources": share_sources,
        "discrepancy": raw["discrepancy"],
        "caveat": raw["discrepancy"],
        "size_band": size_category(value) if status in CLASSIFIABLE_SIZE else "unknown",
        "ratio_policy": "Size classification does not clear historical debt/market-cap reconciliation guards.",
    }
    if qualification is not None:
        record["qualification_label"] = qualification
    if "session_status" in raw:
        session_status = raw["session_status"]
        if not isinstance(session_status, str) or session_status not in {
            "intraday", "completed_session"
        }:
            raise ValueError("Capitalization session_status must be intraday or completed_session")
        record["session_status"] = session_status
    if "time_precision" in raw:
        if raw["time_precision"] != "date":
            raise ValueError("Capitalization time_precision currently supports date only")
        record["time_precision"] = "date"
    if "metadata_last_updated" in raw:
        metadata_date = calendar_date(raw["metadata_last_updated"], "Capitalization metadata_last_updated")
        if metadata_date > reviewed_at:
            raise ValueError("Capitalization metadata date is after its review date")
        record["metadata_last_updated"] = raw["metadata_last_updated"]
    if "source_values_disagree" in raw:
        if not isinstance(raw["source_values_disagree"], bool):
            raise ValueError("Source-value disagreement flag must be boolean")
        record["source_values_disagree"] = raw["source_values_disagree"]
    return record


def _single_disclosure_review(raw, reviewed_at):
    for key in ("ticker", "status", "checked_at", "channels", "events", "gaps"):
        if key not in raw:
            raise ValueError(f"Disclosure review missing {key}")
    status = raw["status"]
    if status not in REVIEW_STATUS:
        raise ValueError("Unknown disclosure review status")
    instant = checked_instant(raw["checked_at"])
    if instant.date() > reviewed_at:
        raise ValueError("Disclosure check is after its review date")
    for key in ("channels", "events", "gaps"):
        if not isinstance(raw[key], list):
            raise ValueError(f"Disclosure {key} must be an array")
    if status != "source_access_incomplete" and not raw["channels"]:
        raise ValueError(
            "A completed disclosure check must identify the checked channels"
        )
    if status == "source_access_incomplete" and not raw["gaps"]:
        raise ValueError("Incomplete source access needs an actionable gap")
    channels = []
    for channel in raw["channels"]:
        if not isinstance(channel, dict):
            raise ValueError("Checked channel must be an object")
        channels.append(
            {
                "url": public_source(channel.get("url")),
                "result": nonempty_text(channel.get("result"), "Channel result"),
            }
        )
    events = []
    for event in raw["events"]:
        if not isinstance(event, dict):
            raise ValueError("Disclosure event must be an object")
        published = calendar_date(
            event.get("publication_date"), "Event publication_date"
        )
        observed = calendar_date(
            event.get("observation_date"), "Event observation_date"
        )
        if published > instant.date() or observed > instant.date():
            raise ValueError(
                "Event publication/observation cannot be after the disclosure check"
            )
        events.append(
            {
                "title": nonempty_text(event.get("title"), "Event title"),
                "publication_date": event["publication_date"],
                "observation_date": event["observation_date"],
                "source_url": public_source(event.get("source_url")),
                "detail": nonempty_text(event.get("detail"), "Event detail"),
                "category": nonempty_text(event.get("category"), "Event category"),
                "supporting_passages": supporting_passages(event),
            }
        )
    gaps = [nonempty_text(gap, "Disclosure gap") for gap in raw["gaps"]]
    earnings = raw.get("earnings_release_check")
    if earnings is not None and earnings not in {"new_release", "checked_no_new_release", "partial", "not_checked"}:
        raise ValueError("Unknown earnings release check outcome")
    return {
        **({"earnings_release_check": earnings} if earnings is not None else {}),
        "ticker": raw["ticker"],
        "status": status,
        "checked_at": raw["checked_at"],
        "channels": channels,
        "events": events,
        "gaps": gaps,
        "scope_note": "Review covers the listed channels and dated events only. Financial statements, instrument terms and operating observations retain their original dates.",
    }


def disclosure_record(raw, reviewed_at):
    current = _single_disclosure_review(raw, reviewed_at)
    history = []
    for entry in raw.get("previous_reviews", []):
        previous = _single_disclosure_review(entry, reviewed_at)
        if previous["ticker"] != current["ticker"] or "previous_reviews" in entry:
            raise ValueError("Review history must be flat and belong to the same issuer")
        if history and checked_instant(previous["checked_at"]) <= checked_instant(history[-1]["checked_at"]):
            raise ValueError("Review history must be chronological")
        history.append(previous)
    if history:
        if checked_instant(history[-1]["checked_at"]) >= checked_instant(current["checked_at"]):
            raise ValueError("Current review must follow its historical checks")
        current["previous_reviews"] = history
    return current


def enrich_data_quality(snapshot, sizes=None, reviews=None):
    """Apply independently reviewed overlays to a copy of the historical snapshot."""
    result = deepcopy(snapshot)
    known = {company["ticker"]: company for company in result["companies"]}
    metadata = {}
    for payload, key, field, validator in (
        (sizes, "observations", "size_observation", size_record),
        (reviews, "reviews", "disclosure_review", disclosure_record),
    ):
        if payload is None:
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
            raise ValueError(f"Data-quality payload requires {key} array")
        reviewed = calendar_date(payload.get("reviewed_at"), "Quality reviewed_at")
        seen = set()
        for raw in payload[key]:
            if not isinstance(raw, dict):
                raise ValueError("Quality record must be an object")
            ticker = raw.get("ticker")
            if ticker not in known:
                raise ValueError(
                    "Quality observation references unknown company identity"
                )
            if ticker in seen:
                raise ValueError("Duplicate quality observation for company")
            seen.add(ticker)
            known[ticker][field] = validator(raw, reviewed)
        metadata[field + "_reviewed_at"] = payload["reviewed_at"]
    if metadata:
        result["data_quality"] = metadata
    return result


def require_complete_data_quality(snapshot):
    """A dated-quality release requires both reviewed overlays for all focus names."""
    from .watch import FOCUS

    metadata = snapshot.get("data_quality", {})
    if not all(
        metadata.get(key)
        for key in ("size_observation_reviewed_at", "disclosure_review_reviewed_at")
    ):
        raise ValueError(
            "Publication held: both dated size and disclosure review inputs are required"
        )
    companies = {company["ticker"]: company for company in snapshot["companies"]}
    for ticker in FOCUS:
        company = companies.get(ticker, {})
        for field in ("size_observation", "disclosure_review"):
            record = company.get(field)
            if not record or record.get("ticker") != ticker:
                raise ValueError(f"Publication held: {ticker} lacks a reviewed {field}")
