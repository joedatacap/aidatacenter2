# NeoCloud Debt Intelligence

**Which AI infrastructure companies survive higher rates?**

FastAPI research application for **CRWV, NBIS, IREN, BTDR and HUT**, with a Crusoe research manager, evidence ledger, rate scenarios and visible agent history. Bitdeer combines Bitcoin mining, ASIC manufacturing and emerging AI/HPC activity; it is not treated as a pure-play GPU cloud. The V2 financing engine implements [V2_FINANCING_RISK.md](V2_FINANCING_RISK.md) while preserving the V1 ledger, APIs and Postgres interface.

## V2 financing dashboard

Open `/` or `/v2` for the comparison dashboard; `/v1` retains the original ledger. Default comparison is **CRWV vs HUT**, with quick switches to CRWV/NBIS and IREN/BTDR. Five panels cover 12/18-month funding, dated instrument yields, contract backing, cash-interest coverage and a 24-month principal wall. Every metric keeps its currency, observation date and evidence or assumption label. No quote or equity-market feed is configured; missing quotes and incomplete forecasts remain unavailable.

Select **Illustrative scenario demo** to exercise Base, Downside and Tight credit waterfalls without runtime inference or source retrieval. Demo funding, equity, cash-flow and floating-debt inputs are synthetic assumptions, deliberately labeled; they are not estimates of the actual companies. CRWV's illustrative funding is less committed and its floating debt less hedged than HUT's illustrative inputs, so tight credit and rate shocks produce different effects. SEC-backed HUT reference excerpts are displayed separately from those assumptions.

Live runs use role-routed Crusoe specialists and two audits: initial audit → manager-selected targeted followup → final audit → dossier. Only reviewed structured records feed live financial calculations. Explicit user funding assumptions can be added after a run finishes; they retain a separate `user_assumption` status and cannot become auditor-approved facts. Provisional extraction and model prose remain subject to review. No guarantee of full disclosure coverage is implied by a completed task.

HUT reference: River Bend **$3.25B, 6.192%, November 15 2042**, Beacon Point **$4.25B, 6.129%, November 30 2042**, both principal amounts dated June 30 2026; parent revolver **$1.07B commitment**, with drawn balance unknown. Beacon Point's Baa2 rating belongs to its project notes. Google backs River Bend lease payments and pass-through obligations; it does not guarantee all Hut 8 debt. Source excerpts, restricted project cash and annual maturity buckets are included in `neocloud/data/hut_reference.json`; live use requires runtime audit.

V2 JSON/CSV exports include source lineage and parent-child investigations. `/api/v2/routing` shows account-tested model routes, latency, usage, pricing estimates and budget diagnostics. The actual discovered IDs are `zai-org/GLM-5.3`, `deepseek-ai/Deepseek-V4-Flash`, `zai-org/GLM-5.3-Flash`, `openai/gpt-oss-120b` and `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. All five passed real JSON probes. Overrides use `CRUSOE_ROUTE_<ROLE>` (comma-separated IDs); only discovered, JSON-tested, priced models are eligible. DeepSeek V4 Pro is discoverable but excluded from runtime selection until a maintained price is available. GPT-OSS is served by Crusoe, without an OpenAI API key or runtime OpenAI billing.

V2 reserves conservative cost before each call: default **$2/run** and **$40 global soft cap**, configurable with `CRUSOE_RUN_BUDGET_USD` and `CRUSOE_GLOBAL_SOFT_BUDGET_USD`. A durable ledger survives Postgres restarts; failed or interrupted calls retain conservative reservations. Verification probes are shown separately in diagnostics and are outside investigation budgets. Pricing is estimated, not provider billing. Existing 18-task, 25-call, 15-fetch, 2-retry and 5-minute limits remain. Codex development continues on the user's subscription.

The additive [V2 migration](neocloud/migrations/002_financing_risk.sql) is included in startup `schema.sql` and this PR for coordination with the separate Neon connectivity task. It adds `schema_migrations`, `v2_financing_records`, `v2_model_attempts` and a risk JSON index. Authoritative V2 facts and cost reservations remain in the existing atomic `runs.body` snapshot; SQL views expose queryable records without a second write path. No Neon transport, hostname, credentials or infrastructure changes are included. The migration has been tested only on disposable TLS Postgres, including the existing HTTPS protocol bridge.

Run a bounded real investigation (no Neon network diagnosis):

```sh
python scripts/run_v2_investigation.py CRWV HUT --output work/v2-live.json
# Optional persistence proof against an explicitly disposable TEST_DATABASE_URL:
python scripts/run_v2_investigation.py CRWV NBIS --test-postgres --output work/v2-persisted.json
```

See [V2 validation and limitations](docs/V2_IMPLEMENTATION.md) and [runtime verification](docs/V2_LIVE_VERIFICATION.json). Financial calculations use Decimal and do not combine currencies, issue size with outstanding balances, or annual maturity buckets with overlapping bullet schedules. A dated project balance is not a current corporate total. Negative EBITDA gives N/M; unknown hedge coverage does not imply zero hedging.

To add your own funding assumptions, open the dashboard's **Use your own funding assumptions** panel after a run finishes, paste a FundingPlan JSON object, and save. For example, this deliberately small illustrative scenario has a $100 funding gap and a $1,000 equity denominator (10%):

```json
{
  "id": "example", "ticker": "CRWV", "currency": "USD", "as_of": "2026-10-17",
  "horizon_months": 12, "scope": "Illustrative parent obligations", "complete": true,
  "market_cap": "1000", "market_cap_at": "2026-10-17",
  "lines": [
    {"id":"capex","ticker":"CRWV","currency":"USD","as_of":"2026-10-17","horizon_months":12,
     "side":"use","category":"capex","amount":"300","entity":"Parent",
     "certainty":"analyst_estimated","cashflow_key":"capex"},
    {"id":"cash","ticker":"CRWV","currency":"USD","as_of":"2026-10-17","horizon_months":12,
     "side":"source","category":"cash","amount":"200","entity":"Parent","usable":true,
     "certainty":"analyst_estimated","cashflow_key":"opening-cash"}
  ]
}
```

Amounts are actual currency units. Mark `complete` only when the scenario intentionally covers every relevant use and source in its stated scope. Add an independent 18-month plan rather than extrapolating 12-month rows. Models cannot create user-assumption status; this endpoint strips claimed verification and citation IDs.

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
