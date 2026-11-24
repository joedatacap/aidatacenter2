from scripts.stage_terminal_sec import candidates


def test_exact_accession_and_quarterly_scope_stay_distinct():
    accession = "0001144879-26-000059"
    end = "2026-08-31"
    filings = {"filings": {"recent": {
        "form": ["8-K", "10-Q"], "accessionNumber": ["other", accession],
        "filingDate": ["2026-10-10", "2026-10-07"],
        "reportDate": ["2026-10-10", end], "primaryDocument": ["event.htm", "report.htm"],
        "acceptanceDateTime": ["2026-10-10T10:00:00Z", "2026-10-07T16:30:00Z"],
    }}}
    base = {"end": end, "accn": accession}
    values = [
        {**base, "start": "2026-06-01", "val": 17},
        {**base, "start": "2025-09-01", "val": 83},
        {**base, "start": "2026-06-01", "accn": "other", "val": 99},
    ]
    facts = {"facts": {"us-gaap": {
        "Revenues": {"label": "Sales", "units": {"USD": values}},
        "CashAndCashEquivalentsAtCarryingValue": {"label": "Cash", "units": {"USD": [{**base, "val": 11}]}},
    }}}
    snapshot = candidates(filings, facts, "2026-10-09")
    assert snapshot["latest_periodic_filing"]["accessionNumber"] == accession
    assert [v["val"] for v in snapshot["financial_candidates"]] == [11, 17]
    assert [row["form"] for row in snapshot["recent_filings"]] == ["8-K"]
    assert candidates(filings, {"facts": {}}, "2026-10-12")["financial_candidates"] == []
