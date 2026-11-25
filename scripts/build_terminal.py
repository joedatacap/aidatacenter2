"""Validate reviewed terminal records and build a portable, offline prototype.

The input directory is a review boundary: stage candidate JSON outside it, review
its passages/dates/scopes, then copy approved records into the three canonical
files and run this command. This builder never fetches or promotes new evidence.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
COMPANIES = ("crwv", "apld", "agpu")
MARKERS = (
    "<!-- TERMINAL_STYLE -->",
    "<!-- TERMINAL_DATA -->",
    "<!-- TERMINAL_SCRIPT -->",
)
UNKNOWN = re.compile(
    r"unknown|unavailable|not (?:disclosed|established|verified|available|researched)|insufficient|unverified|not yet",
    re.I,
)


def _object(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected an object")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected nonempty text")
    if any(ord(c) < 32 and c not in "\n\t\r" for c in value):
        raise ValueError(f"{label}: unsupported control character")
    return value


def _date(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{label}: expected an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label}: invalid calendar date") from None


def _instant(value, label):
    _text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{label}: expected a UTC ISO timestamp") from None
    if (
        "T" not in value
        or parsed.tzinfo is None
        or parsed.utcoffset().total_seconds() != 0
    ):
        raise ValueError(f"{label}: expected a UTC ISO timestamp")
    return parsed


def _url(value, label):
    _text(value, label)
    try:
        parsed = urlsplit(value)
        credentials = parsed.username is not None or parsed.password is not None
        port = parsed.port
    except ValueError:
        raise ValueError(f"{label}: invalid source URL") from None
    sensitive = {
        "token",
        "key",
        "api_key",
        "apikey",
        "access_token",
        "password",
        "signature",
        "authorization",
    }
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or credentials
        or port not in (None, 443)
        or re.search(r"\s", value)
        or any(key.lower() in sensitive for key, _ in parse_qsl(parsed.query))
    ):
        raise ValueError(f"{label}: expected a public HTTPS source without credentials")
    return value


def _rows(value, label):
    if not isinstance(value, list):
        raise ValueError(f"{label}: expected an array")
    return value


def validate_company(value, *, expected_id=None, now=None):
    """Validate evidence and chronology without rewriting reviewed records.

    Formulas are documentary methods, never evaluated as code. Calculated facts
    must identify existing input facts, and their dependency graph must be acyclic.
    This verifies lineage, not arbitrary display-string arithmetic.
    """
    company = _object(value, "company")
    identifier = _text(company.get("id"), "company.id")
    if identifier not in COMPANIES or (
        expected_id is not None and identifier != expected_id
    ):
        raise ValueError("company.id: unexpected canonical company")
    if company.get("ticker") != identifier.upper():
        raise ValueError("company.ticker: does not match canonical company")
    for key in ("name", "role", "overview"):
        _text(company.get(key), f"company.{key}")
    reviewed = _instant(company.get("reviewed_at"), "reviewed_at")
    if reviewed > (now or datetime.now(timezone.utc)):
        raise ValueError("reviewed_at: future verification is not permitted")
    cutoff = reviewed.date()

    def observed(day, label):
        result = _date(day, label)
        if result > cutoff:
            raise ValueError(f"{label}: observation after review")
        return result

    sources = {}
    for row in _rows(company.get("sources"), "sources"):
        source = _object(row, "source")
        sid = _text(source.get("id"), "source.id")
        if sid in sources:
            raise ValueError("sources: duplicate id")
        for key in ("title", "excerpt"):
            _text(source.get(key), f"source.{key}")
        _url(source.get("url"), "source.url")
        observed(source.get("published"), "source.published")
        sources[sid] = source

    def reference(sid, label):
        if not isinstance(sid, str) or sid not in sources:
            raise ValueError(f"{label}: unknown source reference")

    def event_source(sid, publication, label):
        reference(sid, label)
        if sources[sid]["published"] != publication:
            raise ValueError(
                f"{label}: source publication must match the dated event disclosure"
            )

    reference(company.get("identity_source"), "identity_source")
    size = _object(company.get("size"), "size")
    for key in ("label", "basis"):
        _text(size.get(key), f"size.{key}")
    observed(size.get("as_of"), "size.as_of")
    reference(size.get("source"), "size.source")
    if "value_usd" not in size:
        raise ValueError("size.value_usd: explicit numeric value or null required")
    amount = size["value_usd"]
    if amount is not None and (
        isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or not math.isfinite(amount)
        or amount <= 0
    ):
        raise ValueError("size.value_usd: expected positive finite USD value or null")
    qualified_unknown = bool(UNKNOWN.search(size["label"]))
    label = re.sub(r"[ -]+cap$", "", size["label"].strip().lower())
    if amount is None and not qualified_unknown:
        raise ValueError("size.label: absent amount must be explicitly Unverified")
    if amount is not None and not qualified_unknown:
        expected = (
            "small"
            if amount < 2_000_000_000
            else "mid" if amount < 10_000_000_000 else "large"
        )
        if label != expected:
            raise ValueError(
                "size.label: does not match the dated numeric size category"
            )

    facts = {}
    for row in _rows(company.get("facts"), "facts"):
        fact = _object(row, "fact")
        fid = _text(fact.get("id"), "fact.id")
        if fid in facts:
            raise ValueError("facts: duplicate id")
        for key in (
            "kind",
            "label",
            "value",
            "unit",
            "definition",
            "scope",
            "verification",
        ):
            _text(fact.get(key), f"fact.{key}")
        if fact.get("basis") not in ("reported", "calculated", "estimated"):
            raise ValueError("fact.basis: unsupported evidence basis")
        observed(fact.get("as_of"), "fact.as_of")
        reference(fact.get("source"), "fact.source")
        if UNKNOWN.search(fact["verification"]) and not UNKNOWN.search(fact["value"]):
            raise ValueError(
                "fact.value: missing evidence must remain explicitly unknown"
            )
        facts[fid] = fact
    graph = {}
    for fid, fact in facts.items():
        inputs = _rows(fact.get("inputs", []), "fact.inputs")
        if "formula" in fact:
            _text(fact["formula"], "fact.formula")
        if fact["basis"] == "calculated":
            _text(fact.get("formula"), "fact.formula")
            if not inputs:
                raise ValueError(
                    "fact.inputs: calculated fact requires input references"
                )
        if inputs:
            _rows(inputs, "fact.inputs")
            if any(not isinstance(item, str) or item not in facts for item in inputs):
                raise ValueError("fact.inputs: unknown fact reference")
            if len(set(inputs)) != len(inputs):
                raise ValueError("fact.inputs: duplicate reference")
        if fact["basis"] == "calculated":
            available = sources[fact["source"]]["published"]
            if any(
                sources[facts[dependency]["source"]]["published"] > available
                for dependency in inputs
            ):
                raise ValueError(
                    "fact.inputs: derived disclosure cannot use future input evidence"
                )
        graph[fid] = inputs
    active, complete = set(), set()

    def visit(fid):
        if fid in active:
            raise ValueError("fact.inputs: circular calculation lineage")
        if fid in complete:
            return
        active.add(fid)
        for dependency in graph[fid]:
            visit(dependency)
        active.remove(fid)
        complete.add(fid)

    for fid in facts:
        visit(fid)

    for collection in ("milestones", "changes"):
        ids = set()
        for row in _rows(company.get(collection), collection):
            row = _object(row, collection)
            rid = _text(row.get("id"), f"{collection}.id")
            if rid in ids:
                raise ValueError(f"{collection}: duplicate id")
            ids.add(rid)
            if collection == "changes":
                if row.get("type") not in (
                    "delivery",
                    "capacity",
                    "financing",
                    "customer",
                    "guidance",
                ):
                    raise ValueError("change.type: unsupported category")
                for key in ("before", "after", "why"):
                    _text(row.get(key), f"change.{key}")
                observed(row.get("published"), "change.published")
                event_source(row.get("source"), row["published"], "change.source")
                if row.get("before_source") is not None:
                    reference(row["before_source"], "change.before_source")
                    if sources[row["before_source"]]["published"] > row["published"]:
                        raise ValueError(
                            "change.before_source: future source would leak into the as-of view"
                        )
                continue
            for key in ("project", "type", "status", "explanation"):
                _text(row.get(key), f"milestone.{key}")
            original = _object(row.get("original"), "milestone.original")
            previous = None
            for target in [
                original,
                *_rows(row.get("revisions"), "milestone.revisions"),
            ]:
                target = _object(target, "milestone target")
                published = observed(target.get("published"), "milestone.published")
                _text(target.get("target"), "milestone.target")
                if "target_end" in target:
                    _date(target["target_end"], "milestone.target_end")
                event_source(
                    target.get("source"), target["published"], "milestone.source"
                )
                if previous is not None and published < previous:
                    raise ValueError(
                        "milestone: revisions must follow original chronology"
                    )
                previous = published
            outcome = row.get("outcome")
            if outcome is not None:
                outcome = _object(outcome, "milestone.outcome")
                published = observed(
                    outcome.get("published"), "milestone.outcome.published"
                )
                _text(outcome.get("description"), "milestone.outcome.description")
                event_source(
                    outcome.get("source"),
                    outcome["published"],
                    "milestone.outcome.source",
                )
                if published < previous:
                    raise ValueError(
                        "milestone: outcome predates latest target disclosure"
                    )
            if (
                row["status"].lower() in ("met", "missed", "delivered", "completed")
                and outcome is None
            ):
                raise ValueError(
                    "milestone: definitive outcome status requires observed evidence"
                )
    for question in _rows(company.get("questions"), "questions"):
        _text(question, "question")
    return deepcopy(company)


def load_companies(root=ROOT, *, input_dir=None, now=None):
    directory = (
        Path(input_dir)
        if input_dir is not None
        else Path(root) / "neocloud/data/terminal"
    )
    return [
        validate_company(
            json.loads((directory / f"{identifier}.json").read_text(encoding="utf-8")),
            expected_id=identifier,
            now=now,
        )
        for identifier in COMPANIES
    ]


def build(*, root=ROOT, input_dir=None, output=None, now=None):
    root = Path(root)
    companies = load_companies(root, input_dir=input_dir, now=now)
    assets = root / "terminal-preview"
    template = (assets / "index.html").read_text(encoding="utf-8")
    for marker in MARKERS:
        if template.count(marker) != 1:
            raise ValueError(f"Template must contain exactly one {marker}")
    css = (assets / "terminal.css").read_text(encoding="utf-8")
    js = (assets / "terminal.js").read_text(encoding="utf-8")
    if re.search(r"</style\b", css, re.I) or re.search(r"</script\b", js, re.I):
        raise ValueError("Assets contain an unsafe inline closing tag")
    payload = (
        json.dumps(companies, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    replacements = (
        f"<style>{css}</style>",
        f'<script type="application/json" id="terminal-data">{payload}</script>',
        f"<script>{js}</script>",
    )
    for marker, replacement in zip(MARKERS, replacements):
        template = template.replace(marker, replacement)
    target = (
        Path(output)
        if output is not None
        else root / "work/Neocloud-Intelligence-Terminal.html"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template, encoding="utf-8")
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Standalone HTML output path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate reviewed inputs without building or publishing",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Reviewed or staged directory containing crwv.json, apld.json and agpu.json; no automatic promotion",
    )
    args = parser.parse_args(argv)
    if args.check:
        load_companies(input_dir=args.input_dir)
        print("Validated 3 reviewed terminal company records.")
    else:
        print(build(input_dir=args.input_dir, output=args.output))


if __name__ == "__main__":
    main()
