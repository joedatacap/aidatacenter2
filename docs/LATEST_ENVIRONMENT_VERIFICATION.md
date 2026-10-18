# Published environment verification — October 17, 2026 (Pacific)

Checks ran in the latest attached published environment. Only service outcomes and public-source research are retained here; private cloud configuration identifiers, tenant database hostnames and account model inventory are omitted.

## Six configured hosts

| Host | Actual check |
| --- | --- |
| api.inference.crusoecloud.com | Authenticated model discovery and real structured JSON inference succeeded |
| www.sec.gov | Both CRWV 10-Q and NBIS convertible-note exhibit returned 200; document bodies retrieved |
| investors.coreweave.com | Specific senior-note pricing release returned 200; root initially returned 403 |
| nebius.com | Specific $775 million financing release returned 200; body retrieved |
| iren.com | Returned 200 |
| ir.bitdeer.com | Returned 200 on the diagnostic check; initial root probe returned 503 |

Initial local sandbox probes failed before reaching the network. Subsequent commands explicitly enabled sandbox network access while retaining the environment's inherited proxy and TLS verification. This did not change the published destination allowlist.

## Real Neon check, independently of source/inference checks

One bounded direct PostgreSQL `SELECT 1` attempt failed DNS resolution. Runtime policy has empty TCP domain/IP grants. No repeated retries were made. Thus direct Neon PostgreSQL connectivity is unproven and currently unavailable; a DNS error alone does not establish an invalid endpoint, password failure or provider outage.

One separate SQL-over-HTTPS `SELECT 1` attempt received `network_policy_restriction`. The regional Neon API host is outside the six custom allowed domains. There is no claim of actual Neon persistence or restart recovery. Diagnostics are in `connectivity-latest.json` without connection strings or credentials.

## Verified financing facts

`verified-financing-latest.json` contains four independently reviewed primary-source records, exact excerpts and field semantics. This development verification is distinguished from runtime model auditor approval. It includes CRWV DDTL 4.0 commitment, rounded fixed/floating balances and rate terms; CRWV's 2032 9.625% note; NBIS's $775 million facility and SOFR+250 bps pricing; and NBIS's $5.75 billion original convertible-note issuance. Facility/issuance sizes are not silently converted into later outstanding principal. Missing exact dates, hedge coverage and customer linkage remain unknown.

## Fixes prompted by live research

Debt-note passages now retain table headings/units before incidental cross-references and exclude hidden inline XBRL metadata. Short releases remain intact. Extraction requests are bounded and the structured-response allowance is 8192 tokens to avoid truncating real evidence ledgers. Specialists receive their assignment, primary sources and relevant company evidence, avoiding contamination from fallible cross-company manager summaries. The dossier UI displays the model synthesis with a review label alongside accepted evidence and caveats.

Citation passage IDs are explicitly numbered in model inputs and resolved by the server to retrieved text, with bounds/type checks and the existing exact-substring validation. The first completed debt-research round now requires model-selected auditor tasks before further extraction; the worker constrains roles without inventing research goals. Regression tests cover passage IDs, invalid IDs, hidden XBRL, debt-table scope, cross-company context isolation and review ordering.

Automated validation: **54 passed, 2 skipped**. The skipped cases require a dedicated disposable TLS Postgres database; production `DATABASE_URL` was not reused for destructive integration tests. Python compilation and JavaScript syntax checks pass. Actual Neon access was tested separately as described above.

## Latest real investigation and dossier check

Run `9ea3c09e-e446-4c91-978a-728c0e64f0f7` completed as **partially_completed** with a completed Crusoe dossier task. It used 17 actual model attempts, 8 source fetches, 15 total tasks and 2 model-initiated recursive children. Final stop: **Manager-approved dossier finalized; disclosure gaps preserved**. Six accepted excerpts were rechecked as exact substrings of actual retrieved source bodies. Six instrument records remain provisional; **zero auditor-approved records** are claimed. The independent financing verification report is separate from runtime auditor approval. There is no company-wide debt total or complete rate-exposure comparison.

The model dossier, six ledger rows and six citation excerpts were replayed through the real FastAPI UI in Chromium. Desktop and 390px mobile layouts had no page overflow or JavaScript errors; refresh retained the dossier. The scenario API returned disclosure-incomplete output with no fabricated known exposure. See `dossier-browser-verification.json` and `source-backed-live-trace.json`. This verifies dossier presentation and evidence access in development memory; it does not prove Neon persistence.

A prior run exhausted its research budget. That prompted an explicit final-review/dossier phase after a completed followup round, automatic closure after the model dossier, clearer phase feedback, and further financial gates for note issuance, drawn amounts, effective rates and hedge-date precision.
