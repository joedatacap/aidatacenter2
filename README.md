# NeoCloud Debt Intelligence

**Which AI infrastructure companies survive higher rates?**

FastAPI research application for **CRWV, NBIS, IREN and BTDR**, with a Crusoe-powered research manager, evidence ledger and rate scenarios. Bitdeer combines Bitcoin mining, ASIC manufacturing and emerging AI/HPC activity; it is not treated as a pure-play GPU cloud.

## Run locally

Python 3.11+:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
# Configure CRUSOE_API_KEY and DATABASE_URL securely in the process environment.
python scripts/verify_crusoe.py
uvicorn neocloud.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Open http://127.0.0.1:8000. Enter one or two tickers. Choose **Live** after Crusoe verification, or **Simulated** to inspect the UI and orchestration without credentials. Simulated runs use explicitly labeled task-brief fixtures and make no Crusoe calls or external source requests. They are not verified financial research.

`.env.example` documents configuration; the server reads process environment variables and does not automatically load `.env`. Never commit credentials. `CRUSOE_MODEL` can select an available Nemotron model; otherwise model discovery selects one. Startup verifies a real structured-JSON response, with bounded backoff for HTTP 429. Live investigations are rejected until verification succeeds. The **Verify Crusoe** button retries verification without restarting.

## Architecture

- FastAPI serves the comparison dashboard and run/scenario APIs. Browser polling only reads state. Closing or refreshing a tab does not stop server work.
- A server-owned asynchronous worker runs the manager and delegated debt, deal, market, auditor, follow-up and dossier tasks. The Crusoe manager chooses task roles, goals, tickers, parent IDs and follow-up primary URLs based on intermediate findings. It does not modify application source code.
- Auditor concerns require a manager-selected targeted child before concluding. The worker validates the plan but never invents the child's research goal. The feed distinguishes live model initiation from simulated recursion.
- Exact-URL source tools fetch bounded primary-source passages and discover additional links within an approved source-host set. The manager can request those observed links. Citation excerpts must match retrieved passages exactly. This checks lineage, not the complete semantic correctness of an LLM interpretation; the auditor and human review remain necessary.
- Pure Decimal calculations keep currencies separate. Current interest changes use known outstanding unhedged floating principal. Unknown hedge terms and unknown balances are excluded unless the user explicitly selects a no-hedge assumption. Commitments and drawn amounts are never substituted for outstanding principal. Fixed coupons do not change with traded yields. Refinancing is a separate future illustration.

The source brief remains [HACKATHON_TASK.md](HACKATHON_TASK.md).

## Neon persistence and recovery

Use a **dedicated hackathon Neon database/branch** and a scoped database role. Set its Postgres URI as `DATABASE_URL` in a secure runtime variable, with `sslmode=require` or stronger. A Postgres URI is not an HTTPS network-secret placeholder. The server applies `neocloud/schema.sql` on startup. It creates companies, runs, parent-child tasks, events, evidence, instruments, customer deals, financing links and market observations, using NUMERIC, JSONB and dated fields.

State transitions and normalized rows save in one transaction. The database snapshot contains the task queue and scoped source cache. A renewable database row lease supports Neon's transaction pooler and restricts execution to one worker; use **one Uvicorn worker**. After a crash, a new owner may need to wait up to 120 seconds for the old lease to expire. Interrupted tasks are retried without resetting reserved call budgets. A call can be repeated after a crash because its remote response may have been lost; external calls are at-least-once, not exactly-once.

If `DATABASE_URL` is missing or inaccessible, development continues with a clearly labeled **in-memory adapter**. It survives browser refresh, but **not a server restart**. It is not SQLite or a claim of Neon persistence. `/api/health` reports configured versus connected storage and worker readiness. A configured but unavailable database must be fixed and the server restarted to enable durable storage.

Budgets per run: **18 total tasks (including manager turns), 25 model attempts, 15 source retrieval attempts, 2 retries/task, 5 minutes**. Attempts are reserved before requests and count even when interrupted. Simulated model decisions count against the same limits but incur no inference calls. HTTP 429 retries are delayed. Stop reasons and retry metadata appear in run state. No search provider is configured; this MVP uses exact URLs and observed first-party links.

## Verification

```sh
python -m pytest -q
node --check neocloud/static/app.js
```

CI runs all tests against disposable **TLS Postgres**, including migration, repeat-save idempotency, worker ownership and recovery. Local database integration runs only when `TEST_DATABASE_URL` points to a dedicated disposable TLS Postgres database. It never reuses `DATABASE_URL` for destructive tests.

Tests also cover six possible two-ticker pairs in simulated mode, evidence rejection, retry/call/runtime caps, hedge timing, currency separation, undrawn capacity, refinancing, and server-owned execution across page refreshes. Simulated tests do not prove live Crusoe recursion.

## Current verified state and limitations

- Real authenticated Crusoe model discovery and Nemotron structured JSON inference succeeded on October 17, 2026. The provider also intermittently returns HTTP 429; success on verification does not guarantee later capacity.
- A live manager/delegate/auditor run was exercised. Initial planning looped on missing sources and stopped at its task cap; role guidance and audit-follow-up plan validation were tightened. See `docs/IMPLEMENTATION_STATUS.md` for final run evidence.
- The configured Neon connection failed DNS resolution in this build environment. No successful Neon connection or project provisioning is claimed. Source hosts (SEC and investor sites) are outside the current environment's HTTP allowlist; primary-source retrieval is unavailable here. Enable those destinations and the Neon host's outbound Postgres TCP access in the managed environment configuration to complete live evidence research.
- Six curated instrument fixtures illustrate the ledger, but **zero are presented as live-verified instruments**. Later outstanding balances remain unknown. BTDR terms are unknown until sourced.
- There is no verified customer deal or explicit financing link yet. No market-price provider is connected; the UI shows **Market data unavailable** and computes no fabricated returns.
- The current dossier is a caveated LLM synthesis, not a definitive risk ranking or investment recommendation. No durable deployment, public authentication layer, or live data completeness is claimed. The app is intended for a trusted local hackathon environment until those are added.
