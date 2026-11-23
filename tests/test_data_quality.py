"""Dated quality overlays preserve the immutable November financial baseline."""

from copy import deepcopy
import json
from pathlib import Path
import pytest

from neocloud.data_quality import enrich_data_quality, size_category
from neocloud.directory import build_directory
from neocloud.website_v2 import build_website_v2
from neocloud.watch import build_watch

ROOT = Path(__file__).resolve().parents[1]


def financial_baseline():
    directory = build_directory(
        json.loads((ROOT / "neocloud/data/debt_directory.json").read_text())
    )
    original = build_website_v2(
        directory, json.loads((ROOT / "neocloud/data/website_v2.json").read_text())
    )
    research = [
        json.loads(p.read_text())
        for p in sorted((ROOT / "neocloud/data").glob("watch_*.json"))
        if p.name != "watch_import_audit.json"
    ]
    audit = json.loads((ROOT / "neocloud/data/watch_import_audit.json").read_text())
    return build_watch(original, research, import_audit=audit)


def cap(ticker="NBIS", value=33_960_000_000, **changes):
    return dict(
        {
            "ticker": ticker,
            "as_of": "2026-11-20",
            "value_usd": value,
            "basis": "Provider-reported listed equity capitalization; independent share reconciliation incomplete.",
            "status": "provider_reported",
            "source_url": "https://stockanalysis.com/stocks/nbis/market-cap/",
            "source_date": "2026-11-23",
            "source_excerpt": "SYNTHETIC TEST FIXTURE: market capitalization observation.",
            "share_sources": [
                {
                    "url": "https://issuer.example/filing",
                    "description": "Issuer share-class context; not an EPS denominator.",
                    "supporting_passages": ["Sample cover-page share count."],
                }
            ],
            "discrepancy": "Outstanding share-class reconciliation does not clear the debt-ratio guard.",
        },
        **changes,
    )


def review(ticker="NBIS", **changes):
    return dict(
        {
            "ticker": ticker,
            "status": "updated",
            "checked_at": "2026-11-23T10:00:00Z",
            "channels": [
                {
                    "url": "https://issuer.example/news",
                    "result": "Reviewed the dated issuer disclosures in this channel.",
                }
            ],
            "events": [
                {
                    "title": "Synthetic scoped event",
                    "supporting_passages": ["Sample issuer statement for this test."],
                    "publication_date": "2026-11-20",
                    "observation_date": "2026-11-20",
                    "source_url": "https://issuer.example/announcement",
                    "detail": "Future delivery is targeted for 2027; the November announcement is the observed event.",
                    "category": "buildout",
                }
            ],
            "gaps": [
                "Underlying statements and debt instruments have not all been refreshed."
            ],
        },
        **changes,
    )


def apply(base, observations=None, reviews=None):
    sizes = (
        None
        if observations is None
        else {"reviewed_at": "2026-11-23", "observations": observations}
    )
    disclosure = (
        None if reviews is None else {"reviewed_at": "2026-11-23", "reviews": reviews}
    )
    return enrich_data_quality(base, sizes, disclosure)


def test_size_and_review_are_additive_and_do_not_change_financial_history():
    base = financial_baseline()
    before = deepcopy(base)
    enriched = apply(base, [cap()], [review()])
    assert base == before
    assert enriched["reviewed_at"] == before["reviewed_at"] == "2026-11-17"
    assert enriched["cutoff_at"] == before["cutoff_at"]
    by_ticker = {c["ticker"]: c for c in enriched["companies"]}
    old = {c["ticker"]: c for c in before["companies"]}
    current = by_ticker["NBIS"]
    assert current["size_observation"]["size_band"] == "large"
    assert current["size_observation"]["as_of"] == "2026-11-20"
    assert current["size_observation"]["source_excerpt"] == cap()["source_excerpt"]
    assert current["market_cap"] == old["NBIS"]["market_cap"]
    assert current["market_cap_band"] == old["NBIS"]["market_cap_band"]
    assert current["financing"]["v2"]["debt_market_cap_percent"] is None
    assert current["disclosure_review"]["checked_at"] == "2026-11-23T10:00:00Z"
    for ticker, company in by_ticker.items():
        original = {
            k: v
            for k, v in company.items()
            if k not in ("size_observation", "disclosure_review")
        }
        assert original == old[ticker]
    assert enriched["data_quality"] == {
        "size_observation_reviewed_at": "2026-11-23",
        "disclosure_review_reviewed_at": "2026-11-23",
    }


@pytest.mark.parametrize(
    "value,expected",
    [
        (299_999_999, "micro"),
        (300_000_000, "small"),
        (1_999_999_999, "small"),
        (2_000_000_000, "mid"),
        (9_999_999_999, "mid"),
        (10_000_000_000, "large"),
        (None, "unknown"),
    ],
)
def test_actual_size_thresholds_are_independent_from_manual_focus_group(
    value, expected
):
    assert size_category(value) == expected


def test_null_or_discrepant_cap_never_becomes_zero_or_micro():
    base = financial_baseline()
    result = apply(base, [cap("AGPU", None, status="unresolved")])
    company = next(c for c in result["companies"] if c["ticker"] == "AGPU")
    assert company["size_observation"]["value_usd"] is None
    assert company["size_observation"]["size_band"] == "unknown"
    # The original source remains an independent historical observation.
    assert company["market_cap"]["value"] is not None
    result = apply(base, [cap("AGPU", 100_000_000, status="discrepant")])
    assert (
        next(c for c in result["companies"] if c["ticker"] == "AGPU")[
            "size_observation"
        ]["size_band"]
        == "unknown"
    )


@pytest.mark.parametrize(
    "value", [0, -1, True, float("nan"), float("inf"), "not a cap"]
)
def test_invalid_dollar_observations_are_rejected(value):
    with pytest.raises(ValueError):
        apply(financial_baseline(), [cap(value=value)])


def test_source_integrity_dates_and_share_basis_are_required():
    base = financial_baseline()
    cases = [
        cap(source_url="javascript:alert(1)"),
        cap(source_url="https://user:secret@example.com/data"),
        cap(source_url="https://example.com/data?api_key=secret"),
        cap(source_date="2026-11-24"),
        cap(as_of="2026-11-24"),
        cap(source_excerpt=""),
        cap(basis="Weighted-average EPS shares times price"),
    ]
    for row in cases:
        with pytest.raises(ValueError):
            apply(base, [row])
    with pytest.raises(ValueError):
        apply(base, [cap("NOT_A_COMPANY")])
    with pytest.raises(ValueError):
        apply(base, [cap(), cap()])


def test_scoped_reviews_keep_targets_separate_from_observation_and_publication():
    base = financial_baseline()
    result = apply(base, reviews=[review()])
    observed = next(c for c in result["companies"] if c["ticker"] == "NBIS")[
        "disclosure_review"
    ]
    assert observed["events"][0]["publication_date"] == "2026-11-20"
    assert observed["events"][0]["observation_date"] == "2026-11-20"
    assert "2027" in observed["events"][0]["detail"]
    assert "retain their original dates" in observed["scope_note"]
    bad = review()
    bad["events"][0]["observation_date"] = "2027-01-01"
    with pytest.raises(ValueError):
        apply(base, reviews=[bad])
    bad = review()
    bad["events"][0]["source_url"] = "javascript:unsafe()"
    with pytest.raises(ValueError):
        apply(base, reviews=[bad])
    with pytest.raises(ValueError):
        apply(base, reviews=[review(checked_at="2026-11-23")])
    with pytest.raises(ValueError):
        apply(base, reviews=[review(checked_at="2026-11-23T10:00:00")])
    with pytest.raises(ValueError):
        apply(base, reviews=[review(checked_at="2026-11-24T10:00:00Z")])


def test_no_update_is_a_scoped_search_result_and_incomplete_access_needs_gap():
    base = financial_baseline()
    result = apply(base, reviews=[review(status="no_material_update", events=[])])
    company = next(c for c in result["companies"] if c["ticker"] == "NBIS")
    assert (
        company["quarters"]
        == next(c for c in base["companies"] if c["ticker"] == "NBIS")["quarters"]
    )
    assert company["disclosure_review"]["status"] == "no_material_update"
    with pytest.raises(ValueError):
        apply(base, reviews=[review(status="no_material_update", channels=[])])
    with pytest.raises(ValueError):
        apply(base, reviews=[review(status="source_access_incomplete", gaps=[])])
    result = apply(
        base,
        reviews=[
            review(
                status="source_access_incomplete",
                channels=[],
                events=[],
                gaps=["Retry the unavailable issuer feed."],
            )
        ],
    )
    assert next(c for c in result["companies"] if c["ticker"] == "NBIS")[
        "disclosure_review"
    ]["gaps"]


def test_missing_overlays_do_not_create_unavailable_production_records():
    base = financial_baseline()
    assert enrich_data_quality(base) == base
    assert "data_quality" not in enrich_data_quality(base)


def test_qualification_labels_are_preserved_as_plain_text():
    label = "Provider figures differ"
    enriched = apply(
        financial_baseline(), [cap("AGPU", 100_000_000, qualification_label=label)]
    )
    company = next(c for c in enriched["companies"] if c["ticker"] == "AGPU")
    assert company["size_observation"]["qualification_label"] == label
    assert company["size_observation"]["size_band"] == "micro"
    assert company["financing"]["v2"]["debt_market_cap_percent"] is None
    for unsafe in ("", "<strong>Provider figures differ</strong>", "x" * 161, None):
        if unsafe is None:
            continue  # Optional null is permitted; it creates no rendered qualification.
        with pytest.raises(ValueError):
            apply(financial_baseline(), [cap(qualification_label=unsafe)])


def test_release_requires_both_overlays_for_all_nine_focus_names():
    from neocloud.data_quality import require_complete_data_quality
    from neocloud.watch import FOCUS

    base = financial_baseline()
    with pytest.raises(ValueError, match="both dated"):
        require_complete_data_quality(base)
    sizes = [cap(ticker) for ticker in FOCUS]
    reviews = [review(ticker) for ticker in FOCUS]
    with pytest.raises(ValueError, match="both dated"):
        require_complete_data_quality(apply(base, sizes))
    with pytest.raises(ValueError, match="lacks"):
        require_complete_data_quality(apply(base, sizes[:-1], reviews))
    require_complete_data_quality(apply(base, sizes, reviews))


def test_canonical_quality_inputs_cover_all_nine_without_changing_the_baseline():
    from scripts.build_neocloud_watch import load_snapshot
    from neocloud.data_quality import require_complete_data_quality
    from neocloud.watch import FOCUS

    sizes = json.loads((ROOT / "neocloud/data/quality_sizes.json").read_text())
    reviews = json.loads((ROOT / "neocloud/data/quality_reviews.json").read_text())
    assert set(FOCUS).issubset({r["ticker"] for r in sizes["observations"]})
    assert set(FOCUS).issubset({r["ticker"] for r in reviews["reviews"]})
    baseline = financial_baseline()
    canonical = load_snapshot()
    require_complete_data_quality(canonical)
    expected = enrich_data_quality(baseline, sizes, reviews)
    assert canonical == expected
    stripped = deepcopy(canonical)
    stripped.pop("data_quality")
    for company in stripped["companies"]:
        company.pop("size_observation", None)
        company.pop("disclosure_review", None)
    assert stripped == baseline
    for source in sizes["observations"]:
        company = next(
            c for c in canonical["companies"] if c["ticker"] == source["ticker"]
        )
        assert company["size_observation"]["source_url"] == source["source_url"]
        assert company["size_observation"]["source_date"] == source["source_date"]
        assert company["size_observation"].get("qualification_label") == source.get(
            "qualification_label"
        )


def test_static_research_json_excludes_editorial_cap_values_and_preserves_their_citations():
    from scripts.build_neocloud_watch import load_snapshot, research_snapshot
    data = load_snapshot()
    lookup = {c['ticker']: c for c in research_snapshot(data)['companies']}
    for company in data['companies']:
        observed = company.get('size_observation')
        if observed:
            summary = lookup[company['ticker']]['size_observation']
            assert set(summary) == {'ticker', 'as_of', 'size_band', 'status', 'source_url'}
            assert all(observed[key] == value for key, value in summary.items())
            assert observed['source_excerpt'] and observed['value_usd'] > 0


def test_material_disclosure_evidence_survives_normalization():
    row = review()
    original = row['events'][0]
    normalized = apply(financial_baseline(), reviews=[row])
    nbis = next(c for c in normalized['companies'] if c['ticker'] == 'NBIS')
    assert nbis['disclosure_review']['events'][0]['supporting_passages'] == original['supporting_passages']
    for invalid in ([], ['']):
        original['supporting_passages'] = invalid
        with pytest.raises(ValueError, match='[Pp]assage'):
            apply(financial_baseline(), reviews=[row])
