"""Print a review candidate from SEC submissions and US-GAAP company facts.

Run on demand. Output never promotes or edits a reviewed terminal record.
"""
import argparse
from datetime import date, datetime, timezone
import json
import sys
import time
from urllib.request import Request, urlopen

ISSUERS = {"CRWV": 1769628, "APLD": 1144879, "AGPU": 1446159}
TAGS = {
    "CashAndCashEquivalentsAtCarryingValue": "instant",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "quarter",
    "Revenues": "quarter",
    "SalesRevenueNet": "quarter",
}


def get_json(url, contact):
    request = Request(url, headers={"User-Agent": f"Neocloud Watch research {contact}"})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def candidates(submissions, facts, since):
    recent = submissions["filings"]["recent"]
    fields = ("accessionNumber", "form", "filingDate", "acceptanceDateTime", "reportDate", "primaryDocument")
    rows = [dict(zip(fields, values)) for values in zip(*(recent[k] for k in fields), strict=True)]
    filings = [row for row in rows if row["acceptanceDateTime"][:10] >= since]
    report = next((row for row in rows if row["form"] in {"10-Q", "10-K", "10-Q/A", "10-K/A"}), None)
    result = []
    if report:
        for concept, period_type in TAGS.items():
            tag = facts["facts"].get("us-gaap", {}).get(concept, {})
            for fact in tag.get("units", {}).get("USD", []):
                if fact["accn"] != report["accessionNumber"] or fact["end"] != report["reportDate"]:
                    continue
                if period_type == "quarter":
                    if not fact.get("start"):
                        continue
                    days = (date.fromisoformat(fact["end"]) - date.fromisoformat(fact["start"])).days + 1
                    if not 80 <= days <= 100:
                        continue
                elif "start" in fact:
                    continue
                result.append({"concept": concept, "label": tag["label"], "unit": "USD", **fact})
    return {"latest_periodic_filing": report, "recent_filings": filings, "financial_candidates": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=date.fromisoformat, required=True, help="inclusive UTC acceptance date")
    parser.add_argument("--contact", required=True, help="public researcher contact for SEC fair access")
    args = parser.parse_args()
    records = []
    for ticker, cik in ISSUERS.items():
        key = f"CIK{cik:010d}"
        submissions_url = f"https://data.sec.gov/submissions/{key}.json"
        facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/{key}.json"
        row = {"ticker": ticker, "cik": cik, "submissions_url": submissions_url, "facts_url": facts_url}
        try:
            submissions = get_json(submissions_url, args.contact)
            time.sleep(0.4)
            facts = get_json(facts_url, args.contact)
            if int(submissions["cik"]) != cik or int(facts["cik"]) != cik:
                raise ValueError("Issuer CIK mismatch")
            row.update(legal_name=submissions["name"], tickers=submissions["tickers"],
                       **candidates(submissions, facts, args.since.isoformat()))
        except (OSError, KeyError, ValueError) as error:
            row["access_error"] = str(error)
        row["retrieved_at"] = datetime.now(timezone.utc).isoformat()
        records.append(row)
        time.sleep(0.4)
    print(json.dumps({"status": "pending_human_review", "issuers": records}, indent=2))
    return int(any("access_error" in row for row in records))


if __name__ == "__main__":
    sys.exit(main())
