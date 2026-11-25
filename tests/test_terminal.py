"""Isolated evidence/lineage and portable-build tests; no real financial fixtures."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import pytest

from scripts.build_terminal import build, load_companies, validate_company

NOW = datetime(2026, 11, 24, 12, tzinfo=timezone.utc)


def company(identifier="crwv"):
    record = {
        "id": identifier,
        "ticker": identifier.upper(),
        "name": "Synthetic fixture company",
        "role": "Test only; not an investment record",
        "overview": "Synthetic evidence used only by isolated tests.",
        "reviewed_at": "2026-11-24T10:00:00Z",
        "identity_source": "release",
        "size": {
            "label": "Size not verified",
            "as_of": "2026-11-20",
            "basis": "Unknown share basis; no invented valuation.",
            "source": "release",
            "value_usd": None,
        },
        "sources": [
            {
                "id": "release",
                "title": "Synthetic release",
                "url": "https://issuer.example/release",
                "published": "2026-11-20",
                "excerpt": "This is synthetic test evidence only.",
            }
        ],
        "facts": [
            {
                "id": "revenue",
                "kind": "revenue",
                "label": "Synthetic reported revenue",
                "value": "$12 million",
                "unit": "USD millions",
                "definition": "Consolidated recognized revenue for test quarter.",
                "scope": "Synthetic consolidated company, three months",
                "as_of": "2026-09-30",
                "basis": "reported",
                "verification": "Source-backed test fixture",
                "source": "release",
            }
        ],
        "milestones": [
            {
                "id": "delivery",
                "project": "Synthetic test project",
                "type": "delivery",
                "original": {
                    "published": "2026-08-01",
                    "target": "Q4 2026",
                    "source": "release",
                },
                "revisions": [
                    {
                        "published": "2026-11-01",
                        "target": "January 2027",
                        "source": "release",
                    }
                ],
                "outcome": None,
                "status": "revised",
                "explanation": "A changed target is not an observed delivery.",
            }
        ],
        "changes": [
            {
                "id": "schedule",
                "type": "delivery",
                "published": "2026-11-20",
                "before": "Q4 target",
                "after": "January target",
                "why": "Issuer revised the target; not proof of completion.",
                "source": "release",
                "before_source": "release",
            }
        ],
        "questions": ["What evidence establishes delivery?"],
    }
    for sid, published in (("original", "2026-08-01"), ("revision", "2026-11-01")):
        record["sources"].append(
            {**record["sources"][0], "id": sid, "published": published}
        )
    record["milestones"][0]["original"]["source"] = "original"
    record["milestones"][0]["revisions"][0]["source"] = "revision"
    return record


def validate(record):
    return validate_company(record, now=NOW)


def test_preserves_records_scopes_unknowns_and_input_immutability():
    data = company()
    before = deepcopy(data)
    result = validate(data)
    assert result == before == data
    assert result is not data
    assert result["size"]["value_usd"] is None
    assert result["milestones"][0]["original"]["target"] == "Q4 2026"
    assert result["milestones"][0]["revisions"][0]["target"] == "January 2027"


@pytest.mark.parametrize(
    "container,key",
    [
        ("company", "identity_source"),
        ("size", "source"),
        ("fact", "source"),
        ("change", "source"),
        ("change", "before_source"),
        ("original", "source"),
    ],
)
def test_all_material_evidence_references_must_resolve(container, key):
    data = company()
    locations = {
        "company": data,
        "size": data["size"],
        "fact": data["facts"][0],
        "change": data["changes"][0],
        "original": data["milestones"][0]["original"],
    }
    locations[container][key] = "absent"
    with pytest.raises(ValueError, match="source reference"):
        validate(data)


@pytest.mark.parametrize(
    "value",
    [
        "http://issuer.example/release",
        "https://secret:password@issuer.example/release",
        "https://issuer.example/release?access_token=secret",
        "javascript:alert(1)",
        "https://issuer.example:444/release",
    ],
)
def test_no_credentials_or_nonpublic_protocol_in_source_links(value):
    data = company()
    data["sources"][0]["url"] = value
    with pytest.raises(ValueError, match="HTTPS"):
        validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewed_at", "2026-11-24"),
        ("reviewed_at", "2026-11-24T10:00:00-05:00"),
        ("reviewed_at", "2026-11-25T10:00:00Z"),
    ],
)
def test_review_is_a_real_nonfuture_utc_instant(field, value):
    data = company()
    data[field] = value
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize(
    "where,value",
    [
        ("fact", "2026-02-30"),
        ("fact", "2026-11-25"),
        ("source", "2026-11-25"),
        ("size", "2026-11-25"),
    ],
)
def test_observations_have_real_dates_at_or_before_review(where, value):
    data = company()
    if where == "source":
        data["sources"][0]["published"] = value
    elif where == "size":
        data["size"]["as_of"] = value
    else:
        data["facts"][0]["as_of"] = value
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize("amount", [0, -1, True, float("nan"), float("inf"), "12000"])
def test_missing_size_never_coerced_to_zero_or_accepts_invalid_amount(amount):
    data = company()
    data["size"]["value_usd"] = amount
    with pytest.raises(ValueError, match="finite USD"):
        validate(data)


def test_absent_facts_are_explicit_unknown_display_not_zero():
    data = company()
    fact = data["facts"][0]
    fact.update(verification="Not disclosed", value="Unknown; not disclosed")
    assert validate(data)["facts"][0]["value"] == "Unknown; not disclosed"
    fact["value"] = "$0"
    with pytest.raises(ValueError, match="explicitly unknown"):
        validate(data)
    fact["value"] = None
    with pytest.raises(ValueError, match="nonempty text"):
        validate(data)


def test_calculations_require_explicit_method_and_traceable_acyclic_inputs():
    data = company()
    derived = {
        **deepcopy(data["facts"][0]),
        "id": "difference",
        "basis": "calculated",
        "formula": "reported total less reported component",
        "inputs": ["revenue"],
    }
    data["facts"].append(derived)
    assert validate(data)["facts"][1]["inputs"] == ["revenue"]
    for updates, message in [
        ({"formula": ""}, "formula"),
        ({"inputs": []}, "requires input"),
        ({"inputs": ["missing"]}, "unknown fact"),
        ({"inputs": ["difference"]}, "circular"),
        ({"inputs": ["revenue", "revenue"]}, "duplicate"),
    ]:
        record = deepcopy(data)
        record["facts"][1].update(updates)
        with pytest.raises(ValueError, match=message):
            validate(record)
    data["facts"][0]["inputs"] = ["difference"]
    with pytest.raises(ValueError, match="circular"):
        validate(data)


def test_milestones_keep_original_revision_and_outcome_chronology():
    data = company()
    milestone = data["milestones"][0]
    milestone["revisions"][0]["published"] = "2026-07-01"
    data["sources"][2]["published"] = "2026-07-01"
    with pytest.raises(ValueError, match="chronology"):
        validate(data)
    milestone["revisions"][0]["published"] = "2026-11-01"
    data["sources"][2]["published"] = "2026-11-01"
    milestone["status"] = "met"
    with pytest.raises(ValueError, match="observed evidence"):
        validate(data)
    milestone["outcome"] = {
        "published": "2026-10-31",
        "description": "Actual outcome",
        "source": "release",
    }
    data["sources"][0]["published"] = "2026-10-31"
    with pytest.raises(ValueError, match="predates"):
        validate(data)
    milestone["outcome"]["published"] = "2026-11-20"
    data["sources"][0]["published"] = "2026-11-20"
    assert validate(data)["milestones"][0]["status"] == "met"


def test_duplicate_ids_and_wrong_identity_fail():
    for collection in ("sources", "facts", "milestones", "changes"):
        data = company()
        data[collection].append(deepcopy(data[collection][0]))
        with pytest.raises(ValueError, match="duplicate"):
            validate(data)
    data = company()
    data["ticker"] = "OTHER"
    with pytest.raises(ValueError, match="canonical"):
        validate(data)


def workspace(tmp_path):
    inputs = tmp_path / "neocloud/data/terminal"
    inputs.mkdir(parents=True)
    for identifier in ("agpu", "crwv", "apld"):
        (inputs / f"{identifier}.json").write_text(json.dumps(company(identifier)))
    assets = tmp_path / "terminal-preview"
    assets.mkdir()
    (assets / "index.html").write_text(
        "<!doctype html><html><head><!-- TERMINAL_STYLE --></head><body><!-- TERMINAL_DATA --><!-- TERMINAL_SCRIPT --></body></html>"
    )
    (assets / "terminal.css").write_text("body { color: navy; }")
    (assets / "terminal.js").write_text(
        'document.body.dataset.count = JSON.parse(document.getElementById("terminal-data").textContent).length;'
    )
    return tmp_path


def test_builder_outputs_portable_ordered_safe_json_and_reproducible_assets(tmp_path):
    root = workspace(tmp_path)
    path = root / "neocloud/data/terminal/crwv.json"
    data = json.loads(path.read_text())
    data["overview"] = '</script><img src=x onerror="alert(1)"> & Unicode –'
    path.write_text(json.dumps(data))
    output = build(root=root, now=NOW)
    assert output == root / "work/Neocloud-Intelligence-Terminal.html"
    html = output.read_text()
    payload = re.search(
        r'<script type="application/json" id="terminal-data">(.*?)</script>', html, re.S
    ).group(1)
    decoded = json.loads(payload)
    assert [row["ticker"] for row in decoded] == ["CRWV", "APLD", "AGPU"]
    assert decoded[0]["overview"] == data["overview"]
    assert "<img" not in payload
    assert "\\u003c/script>" in payload
    assert "<style>body { color: navy; }</style>" in html
    assert "<script src=" not in html and "<link " not in html
    target = build(root=root, output=root / "another/terminal.html", now=NOW)
    assert target.read_bytes() == output.read_bytes()
    assert [row["id"] for row in load_companies(root, now=NOW)] == [
        "crwv",
        "apld",
        "agpu",
    ]


def test_builder_rejects_incomplete_records_without_overwriting_existing_output(
    tmp_path,
):
    root = workspace(tmp_path)
    target = root / "previous.html"
    target.write_text("Last good standalone build")
    (root / "neocloud/data/terminal/agpu.json").unlink()
    with pytest.raises(FileNotFoundError):
        build(root=root, output=target, now=NOW)
    assert target.read_text() == "Last good standalone build"


@pytest.mark.parametrize(
    "marker",
    ["<!-- TERMINAL_STYLE -->", "<!-- TERMINAL_DATA -->", "<!-- TERMINAL_SCRIPT -->"],
)
def test_template_insertion_points_must_be_unambiguous(tmp_path, marker):
    root = workspace(tmp_path)
    template = root / "terminal-preview/index.html"
    text = template.read_text()
    for invalid in (text.replace(marker, ""), text + marker):
        template.write_text(invalid)
        with pytest.raises(ValueError, match="exactly one"):
            build(root=root, now=NOW)


@pytest.mark.parametrize(
    "asset,content",
    [
        ("terminal.js", "// </script><script>alert(1)</script>"),
        ("terminal.css", "/* </STYLE><script>alert(1)</script> */"),
    ],
)
def test_inline_asset_closing_tags_are_rejected(tmp_path, asset, content):
    root = workspace(tmp_path)
    (root / "terminal-preview" / asset).write_text(content)
    with pytest.raises(ValueError, match="unsafe inline"):
        build(root=root, now=NOW)


def test_staged_inputs_can_be_validated_without_promoting_or_building(tmp_path):
    root = workspace(tmp_path)
    stage = tmp_path / "staged-review"
    stage.mkdir()
    original = root / "neocloud/data/terminal"
    for identifier in ("crwv", "apld", "agpu"):
        row = company(identifier)
        row["overview"] = "Candidate record in an isolated review directory."
        (stage / f"{identifier}.json").write_text(json.dumps(row))
    rows = load_companies(root, input_dir=stage, now=NOW)
    assert rows[0]["overview"].startswith("Candidate")
    assert json.loads((original / "crwv.json").read_text())["overview"].startswith(
        "Synthetic"
    )
    assert not (root / "work").exists()


@pytest.mark.parametrize(
    "amount,label",
    [
        (1_999_999_999, "Small"),
        (2_000_000_000, "Mid"),
        (9_999_999_999, "Mid"),
        (10_000_000_000, "Large"),
        (1_500_000_000, "Small cap"),
        (12_000_000_000, "Unverified"),
        (None, "Unverified"),
    ],
)
def test_size_category_uses_dated_thresholds_with_explicit_unverified_exception(
    amount, label
):
    data = company()
    data["size"].update(value_usd=amount, label=label)
    assert validate(data)["size"]["label"] == label


@pytest.mark.parametrize(
    "amount,label",
    [
        (None, "Small"),
        (None, "Mid"),
        (None, "Large"),
        (1_999_999_999, "Mid"),
        (2_000_000_000, "Small"),
        (10_000_000_000, "Mid"),
    ],
)
def test_size_basis_caveat_cannot_classify_missing_or_wrong_numeric_value(
    amount, label
):
    data = company()
    data["size"].update(
        value_usd=amount, label=label, basis="Unknown share basis; not verified"
    )
    with pytest.raises(ValueError, match="size.label"):
        validate(data)


@pytest.mark.parametrize("target", ["original", "revision", "outcome", "change"])
def test_asof_events_cannot_claim_later_or_mismatched_source_publication(target):
    data = company()
    if target == "original":
        data["milestones"][0]["original"]["source"] = "release"
    elif target == "revision":
        data["milestones"][0]["revisions"][0]["source"] = "release"
    elif target == "outcome":
        data["milestones"][0]["outcome"] = {
            "published": "2026-11-19",
            "description": "Observed synthetic outcome",
            "source": "release",
        }
    else:
        data["changes"][0]["published"] = "2026-11-19"
    with pytest.raises(ValueError, match="source publication must match"):
        validate(data)


def test_change_prior_evidence_cannot_be_from_after_the_event():
    data = company()
    data["sources"].append(
        {**data["sources"][0], "id": "later", "published": "2026-11-21"}
    )
    data["changes"][0]["before_source"] = "later"
    with pytest.raises(ValueError, match="future source"):
        validate(data)


@pytest.mark.parametrize("inputs", [None, {}, "revenue"])
def test_optional_input_lineage_still_has_a_valid_array_shape(inputs):
    data = company()
    data["facts"][0]["inputs"] = inputs
    with pytest.raises(ValueError, match="expected an array"):
        validate(data)


def test_calculated_disclosure_cannot_reference_input_evidence_from_the_future():
    data = company()
    data["sources"].append(
        {**data["sources"][0], "id": "later-input", "published": "2026-11-21"}
    )
    data["facts"][0]["source"] = "later-input"
    data["facts"].append(
        {
            **deepcopy(data["facts"][0]),
            "id": "derived",
            "source": "release",
            "basis": "calculated",
            "formula": "Synthetic method",
            "inputs": ["revenue"],
        }
    )
    with pytest.raises(ValueError, match="future input evidence"):
        validate(data)
