> Superseded connectivity findings: see [latest published environment verification](LATEST_ENVIRONMENT_VERIFICATION.md). SEC/IR access now works; actual Neon remains blocked separately.

# V1 connectivity and reliability status — October 17, 2026

Implementation continues on `codex/neocloud-debt-intelligence`, [draft PR #3](https://github.com/joedatacap/aidatacenter2/pull/3). No V2, new database, hosting service or SQLite replacement was introduced.

## What was fixed

- Account-discovered model fallback, with a different model family preferred after failures. Exponential backoff has jitter and respects full Retry-After values/HTTP dates. Tasks retain model, attempt/error, latency and token metadata.
- Nemotron output-limit failures are identified explicitly; structured requests default to non-thinking mode. This option was accepted by a real Crusoe JSON verification request.
- Successful inference responses are checkpointed before interpretation. Recovery can reuse them without duplicating a model call or resetting budgets.
- Primary-source retrieval uses approved alternatives/redirects, original/final URL lineage, per-URL negative caching and shared denied-host caching. Source-dependent agents skip unnecessary inference when no text was retrieved.
- Exhausted research is suppressed after an audited follow-up. The manager selects a caveated dossier; its completion closes a partial run without another redundant manager request.
- Completed, partially completed and failed outcomes are explicit. A deterministic evidence snapshot preserves accepted facts and unresolved questions even after a late inference failure.
- Amount-unit, dated-balance, coupon/yield and hedge checks keep unsupported financial fields unknown. Live scenario calculations require explicit auditor approval of each instrument.
- Neon SQL-over-HTTPS fallback uses the existing database and schema, atomic batches and the official serverless-driver protocol. Database connection strings stay in the required HTTPS header, never logs or browser responses.

## Latest genuine live workflow

A Chromium user action started **CRWV vs NBIS**. The browser then closed while the server continued. A later browser reopened/refreshed the same investigation and displayed its final dossier/history.

- Outcome: **partially_completed**.
- Stop reason: **Primary sources unavailable; manager-approved dossier finalized**.
- 15 total tasks, 9 actual Crusoe inference attempts, 3 actual source requests.
- Two model-initiated research children with preserved auditor/manager ancestry.
- The actual model dossier agent completed; the final evidence snapshot retained its caveats.
- No JavaScript errors, no horizontal overflow at 390px, same run retained after refresh.
- **Zero verified financial instruments and zero accepted source excerpts.** Missing balances, terms, maturities and hedges remain unknown. No verified customer deal or market observations are claimed.

[Sanitized latest trace](connectivity-live-trace.json) contains task IDs, parent relationships, actual model attempts, auditor concerns and final outcome. The older `live-demo-trace.json` is historical evidence from the previous V1 run, which ended failed; it is not the latest result.

This proves live orchestration and graceful partial completion, **not successful financial research under blocked source access**. Cached host-denial results for eight approved URLs do not mean eight HTTP requests: only three source requests were made.

## Connectivity: observed facts

| Check | Actual result |
| --- | --- |
| CRUSOE_API_KEY / DATABASE_URL | Present in secure process configuration; values never displayed |
| Crusoe model discovery | HTTP 200, account model list returned |
| Real structured inference | Successful, including Nemotron; fallback exercised in the live workflow |
| Neon executor DNS | Resolution failed |
| Direct Neon PostgreSQL | Failed during DNS resolution; no authenticated DB session established |
| Neon SQL-over-HTTPS | Explicit proxy/network-policy denial at `<regional Neon HTTPS host>` |
| SEC and primary IR sources | Explicit proxy/network-policy denials; no source content retrieved |
| Actual Neon schema/save/read/restart | Not verified because connectivity is blocked |
| Disposable TLS Postgres and HTTPS protocol bridge | Passing CI integration tests; not a claim of actual Neon connectivity |

The latest observed running environment is **revision 8**, with current observations and enforced policy, but its general HTTP allowed-host list still includes only `api.inference.crusoecloud.com`. Earlier reports that settings were applied did not result in the required hosts appearing in this running instance. No provider outage or bad password is inferred from a proxy denial. Executor DNS failure alone does not establish that the configured Neon hostname is invalid.

## Exact external action needed

Apply **general HTTPS network access** for:

```text
www.sec.gov
investors.coreweave.com
nebius.com
iren.com
ir.iren.com
ir.bitdeer.com
<regional Neon HTTPS host>
```

Retain the existing Crusoe permission. These are general network rules, separate from the API key's credential allowed-domain binding. Apply the saved configuration to the active/replacement environment, then restart the app and start a fresh investigation. The HTTPS path uses the existing DATABASE_URL; no new credentials need to be supplied.

The documented managed raw TCP forwarder supports private/VPN destinations and requires replacement environments for changed TCP grants. A grant for a public Neon hostname alone does not make that transport usable. Use the implemented Neon HTTPS transport (`DATABASE_TRANSPORT=auto` or `neon_http`) instead.

Once the policy is effective, run:

```sh
python scripts/check_connectivity.py --include-inference --output work/connectivity.json
uvicorn neocloud.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Then verify actual Neon migration/save/read/recovery and retrieve at least one properly dated financing record for CRWV and NBIS. The code must not claim these criteria until those real checks succeed.

## Tests

The original 28 tests remain. Added tests cover retrieval failures and alternate sources, negative caching, safe redirects, model fallback and actual model selection, jitter/Retry-After, durable-response recovery, late-failure partial dossiers, exhausted-source suppression, auditor ancestry, monetary units, dates, coupon versus yield, hedges, HTTPS parameter binding, credential-safe errors and transaction rollback.

The latest final test count and check links are recorded in PR #3. Local database integration tests skip when a dedicated TEST_DATABASE_URL is not configured; CI supplies disposable TLS Postgres and executes them.
