# Disclosure intake and research review

The collector discovers possible new evidence for CRWV, APLD and AGPU. It does **not** extract financial facts, judge materiality, recommend trades, modify the reviewed ledger, send messages, or publish the site.

Run from the repository root:

```sh
python scripts/check_terminal_disclosures.py --since 2026-11-10 --output work/terminal-disclosures.json
```

Only Python's standard library is required. Requests identify the project using its public GitHub URL, make at most two requests a second, cap each response at 8 MB, and time out after 25 seconds. A different **public** identifying contact can be supplied with `--contact`; do not use secrets or an email address that should not be shared with issuers. Only the fixed SEC and issuer HTTPS hosts are allowed. Cross-origin redirects are rejected.

## What is checked

- SEC submissions JSON for each exact CIK, including all recent filing forms inside the date window. The collector checks issuer identity, column consistency, accession syntax and primary-document paths. It does not retrieve filing contents or exhibits.
- Applied Digital and Axe public RSS releases, with issuer publication dates.
- CoreWeave's IR news listing. If it returns JavaScript-only or otherwise unparseable content, the source is marked **error**. Its SEC coverage can still succeed; IR coverage is not inferred from that success.

The default window is the prior 14 UTC days. The SEC recent-filings array and a publisher's first feed/listing page are bounded sources, not an exhaustive archive. Broad historical backfills need a separate review. HTML links without reliable dates retain `published: null`; the discovery timestamp is never substituted as a publication date. They remain in the queue even if their age cannot be established. An empty IR result is conservatively classified as a coverage error, including when a feed only contains old records.

## JSON contract

`schema_version: 1`. Top-level fields:

- `checked_at`, `since`, `status` (`complete`, `partial`, `failed`), `summary`, `sources`, `items`.
- Each source records its exact URL, check timestamp, `ok`/`error`, item count or null, and error explanation. **Partial/failed must not be rendered as “no new changes.”** Exit code 2 makes incomplete coverage visible in CI; the queue is still saved.
- Each item records ID, ticker, kind, title, canonical URL, `published`, precision, accession/form where available, first/last discovery times, status and discovery sources.
- `new`: not found in the reviewed source ledger or prior queue. This does not mean economically material.
- `unreviewed`: previously discovered and still awaiting assessment.
- `known`: a document URL or SEC accession already appears in the reviewed ledger. `ledger_match: accession` does **not** establish that every exhibit or assertion in that filing was reviewed.
- `reviewed`/`dismissed`: explicit local review disposition with a nonempty reason. These are queue decisions, not automatic promotion into research.

URLs are canonicalized to ignore tracking queries and fragments. CoreWeave article `/default.aspx` variants collapse to one URL. SEC entries deduplicate by accession. A release and a filing covering the same event remain separate source documents. Reviewers must resolve that economic-event duplication rather than assuming two discoveries are two developments.

## Review loop

1. Open each new source. Check its publication time, period, entity, units and exact supporting evidence. Decide whether it changes a thesis, a financial input or a milestone.
2. Preserve the prior claim and add the new evidence to the appropriate `neocloud/data/terminal/*.json` record. Do not overwrite old commitments. Distinguish conditional financing from funded cash, and energization from customer acceptance and recognized revenue.
3. Validate/build and review the resulting company brief. Publication follows the normal PR and release process.
4. Optionally annotate a local queue item with `review: {"disposition":"reviewed","reason":"Added source and milestone in PR ...","reviewed_at":"..."}` or a reasoned dismissal. Reuse it with `--previous work/terminal-disclosures.json --output work/next-disclosures.json`. Prior observations and dispositions survive a source outage or a listing rotation. Review annotations remain local unless deliberately committed elsewhere.

The workflow **Terminal disclosure review queue** runs manually or at 23:30 UTC Monday–Friday (07:30 Singapore Tuesday–Saturday). It writes a 30-day GitHub Actions artifact and has read-only repository permission. A cron definition only becomes active once merged onto the default branch and allowed by repository settings; scheduling delays and provider outages remain possible. Scheduled runs compare against the committed reviewed ledger and do not restore the previous artifact, so an unreviewed item may reappear as `new` across runs. Use `--previous` locally for persistent triage. This first version intentionally does not mutate the repository or silently publish financial claims.
