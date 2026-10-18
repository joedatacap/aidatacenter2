# NeoCloud Debt Intelligence

**Which AI infrastructure companies survive higher rates?**

FastAPI research application for **CRWV, NBIS, IREN and BTDR**, with a Crusoe research manager, evidence ledger, rate scenarios and visible agent history. Bitdeer combines Bitcoin mining, ASIC manufacturing and emerging AI/HPC activity; it is not treated as a pure-play GPU cloud. This implements V1 from [HACKATHON_TASK.md](HACKATHON_TASK.md); the V2 backlog remains out of scope.

## Start

Python 3.11+:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
# Set CRUSOE_API_KEY and DATABASE_URL securely in the process environment.
python scripts/verify_crusoe.py
uvicorn neocloud.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Open http://127.0.0.1:8000. Enter one or two tickers and select **Live** after Crusoe verification, or **Simulated** for labeled task-brief fixtures. Simulated runs make no Crusoe or external-source requests and are not live financial research. `.env.example` documents configuration; the server reads process variables and does not automatically load `.env`. Never commit credentials.

## Reliable runtime agents

The manager dynamically chooses debt, deal, market, auditor, follow-up and dossier tasks from intermediate evidence. It chooses research goals, tickers, primary URLs and parent IDs. The worker validates limits and audit ancestry; it never invents a follow-up research goal. Runtime agents use Crusoe Managed Inference; development does not route through Crusoe.

Model candidates come from the account's actual `/v1/models` response. `CRUSOE_MODEL` and optional comma-separated `CRUSOE_FALLBACK_MODELS` configure preferences. Failed requests can switch to another discovered model, favoring a different model family. Exponential backoff includes jitter and respects the full `Retry-After`, including HTTP dates. A delay beyond the remaining run budget produces a grounded final outcome instead of waiting indefinitely.

Nemotron structured requests default to `chat_template_kwargs.enable_thinking=false` to avoid spending the output budget on reasoning before JSON. Set `CRUSOE_DISABLE_THINKING=0` to omit that request option. Tasks retain model IDs, attempt/error categories, HTTP status, latency and token usage. Successful responses are checkpointed before interpretation, so an interrupted task can reuse its durable response without another inference call.

Budgets per run: **18 total tasks, 25 model attempts, 15 source retrieval attempts, 2 retries/task, 5 minutes**. Attempts are reserved before requests and survive recovery. Cached failures do not consume another retrieval attempt. Simulated decisions use the same caps but incur no inference calls. The server-owned worker continues when the browser closes or refreshes.

## Sources and financial rules

Exact-URL tools fetch bounded SEC/IR passages, follow only approved redirects and retain original/final URL lineage. Alternate approved company sources and observed first-party links can be selected. Failed URLs and policy-denied hosts are cached per run. Sources are untrusted data; instructions in a fetched page cannot alter agent rules.

Citation excerpts must match retrieved passages. Field checks remove unsupported amount units, outstanding-balance claims, exact dates and contractual coupons. A secondary yield cannot replace a coupon, and missing hedge disclosure cannot imply an unhedged facility. Individual live records enter rate scenarios only after explicit auditor approval with supporting evidence IDs. These checks supplement human review; source lineage is not a guarantee that every interpretation is correct.

Calculations use Decimal, preserve currencies, and model only outstanding unhedged floating principal. Undrawn commitments and issuance sizes never substitute for later principal outstanding. Unknown balances/hedges stay unknown. Fixed coupons do not reprice with traded yields. Refinancing remains a separate future illustration. Convertible dilution, recourse, collateral and disclosure coverage remain separate risk dimensions.

## Outcomes and recovery

`outcome` is **completed**, **partially_completed**, or **failed**. The dashboard displays this normalized outcome; the legacy `budget_exhausted` status remains for compatibility when a run stops before meaningful research.

- Completed live runs require a model dossier, auditor review and complete dated, source-backed instrument records for the selected tickers. Company-wide disclosure coverage may still be incomplete.
- Partial runs preserve accepted facts, source failures and unresolved questions. If a late model call fails, a deterministic evidence snapshot still produces a useful dossier without inventing numbers.
- Failed means no meaningful specialist research completed; the error summary retains the reason.

After an audited follow-up exhausts approved sources, repeated research tasks are suppressed and the manager selects a caveated dossier. Its completion closes the partial run without another unnecessary manager turn.

## Neon Postgres, including HTTPS

Use a dedicated hackathon Neon database/branch and a scoped role. `DATABASE_URL` must be a real Postgres URI with `sslmode=require` or stronger, stored as a secure process variable rather than an HTTPS network-secret placeholder. Startup applies `neocloud/schema.sql` for companies, runs, tasks, events, evidence, instruments, customer deals, financing links and market observations.

`DATABASE_TRANSPORT=auto` tries normal PostgreSQL and then Neon's SQL-over-HTTPS transport on network failures. `postgres` or `neon_http` selects a path explicitly. HTTPS uses the **same Neon database**, atomic batched transactions and existing SQL schema. It adds no database or hosting service. The connection URI is sent only in Neon's required HTTPS header, never in URLs, logs or browser responses.

The HTTPS endpoint follows the official `@neondatabase/serverless` 1.2.0 protocol: replace the first DNS label of the database hostname with `api.`, then POST to `/sql`. For the configured database here, the required general HTTPS host is **<regional Neon HTTPS host>**. A CI protocol bridge executes the adapter's real SQL against disposable TLS Postgres and checks round trips and atomic rollback; it is not a claim of actual Neon connectivity.

Snapshots and normalized records save in one transaction. A renewable row lease supports Neon's transaction pooler and restricts execution to one worker; use **one Uvicorn worker**. After a crash, a new owner may need to wait up to 120 seconds for lease expiry. Interrupted tasks preserve budgets and parent relationships. External calls remain at-least-once when a response was lost before checkpointing.

Missing or inaccessible `DATABASE_URL` uses explicitly labeled **development memory**, surviving browser refresh but not server restart. It is not SQLite or a claim of Neon persistence. `/api/health` separates configured from connected storage and includes safe failure categories. Restart the app after correcting connectivity to enable durable storage.

## Diagnostics and tests

For a database-only check in a normal runtime, run `python scripts/verify_neon.py`.
It checks authenticated TLS SQL and temporary-table write/read without application
writes. See [Neon connectivity findings and exact network permission](docs/NEON_CONNECTIVITY.md).

```sh
python scripts/check_connectivity.py --output work/connectivity.json
# Optional bounded real JSON inference verification:
python scripts/check_connectivity.py --include-inference --output work/connectivity.json
python -m pytest -q
node --check neocloud/static/app.js
```

Diagnostics separately check credentials-present flags, Crusoe, executor DNS, direct Postgres, Neon HTTPS and primary-source HTTP. They output categories and hostnames, never keys, passwords or connection strings. DNS failure alone does not prove a provider outage or an invalid Neon endpoint.

CI uses disposable TLS Postgres. Local DB integration runs only with `TEST_DATABASE_URL` pointing to a dedicated disposable database; it never reuses `DATABASE_URL` for destructive tests. The original 28 tests remain, with added coverage for model fallback, backoff, response checkpoints, partial completion, source caching, safe redirects, field validation and HTTPS transaction rollback.

## Current deployment limits

See [implementation status](docs/IMPLEMENTATION_STATUS.md) and sanitized live traces for actual run metrics. Real Crusoe inference works and browser-started live runs produce explicit partial dossiers under restricted access.

The latest attached published environment now reaches all six configured service/source hosts. Exact SEC filings, CoreWeave's financing release, Nebius's financing release, IREN and Bitdeer returned HTTP 200, and authenticated Crusoe JSON inference passed. Root-page CoreWeave 403 and an initial Bitdeer 503 do not imply that every filing/release URL is inaccessible. See [verified financing excerpts](docs/verified-financing-latest.json).

Actual Neon remains blocked separately: the single direct PostgreSQL probe failed DNS resolution, the runtime has no TCP grants, and SQL-over-HTTPS was denied by network policy. The regional HTTPS host `<regional Neon HTTPS host>` is outside the six custom allowed hosts. No actual Neon save/read/restart is claimed; development memory remains explicitly nonpersistent. Do not repeatedly retry unchanged database paths.

A bounded live diagnostic run can be reproduced with `python scripts/run_live_investigation.py CRWV NBIS --output work/live-investigation.json`. This uses the same research engine with explicitly labeled development memory; it does not test Neon persistence.
Research and scenario analysis only. No investment recommendations, fabricated default probabilities, public authentication layer or durable hosting deployment is claimed. Intended for a trusted hackathon environment.
