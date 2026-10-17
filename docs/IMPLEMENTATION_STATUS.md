# Implementation status — October 17, 2026

## Implemented

FastAPI application, four-company catalog, one/two ticker UI, evidence/instrument/deal ledgers, interactive benchmark shocks, separate refinancing illustration, run history and filterable investigation feed. The background worker supports manager-chosen tasks, audit follow-ups, parent IDs, budgets, delayed rate-limit retries and recoverable persisted states.

Neon/Postgres schema and transactional repository are implemented. Missing/unreachable database configuration uses explicitly nonpersistent memory for development. No SQLite dependency is used.

## Live external checks

- Authenticated Crusoe `/v1/models`: HTTP 200, Nemotron models listed.
- Real Nemotron `/v1/chat/completions`: structured connectivity JSON verified. Subsequent calls sometimes returned HTTP 429 with `max_requests_limit (orchestrator)`.
- Neon: configured URI has a Postgres scheme and requires TLS. Connection failed during DNS resolution. Current network policy has no outbound TCP destination grants.
- SEC and Nebius primary-source retrieval: unavailable under the current environment's HTTP policy. No source access bypass attempted.

## Research completeness

Live verified instruments: none in this environment. Verified customer deals: none. Dated market observations: none. Those omissions remain unknown/unavailable in the application. Curated task-brief fixtures are labeled and isolated from live findings.

## Live recursive workflow evidence

The real CRWV/NBIS run used Nemotron 3.5 Lightning, made 13 model attempts, and created 10 total tasks. After auditor objections, the model manager spawned **two specialized debt research children**, preserving auditor → manager → specialist ancestry. Both child tasks completed. This was live model delegation, not a simulated fixture. [Sanitized trace](live-demo-trace.json) records task IDs, parent relationships, objections and stop reason.

The source-access gap was not resolved: all four primary URLs were unavailable, and no instruments or evidence were accepted. The manager proposed alternative searches, but the configured tool supports only exact primary URLs and cached results; no general web searches were executed. The final manager turn exhausted its two retries after inference errors, so this live run ended **failed**, without a final dossier. Live research completion is not claimed.

## Validation and remaining work

CI passed 25 tests including real TLS Postgres migration, repeat saves, worker ownership and restart recovery. Additional parser and duplicate-evidence changes have local coverage and are included in the final CI run. Browser verification found no JavaScript errors and no horizontal page overflow at 390px. The running server completed a simulated IREN/BTDR investigation and returned the same investigation after repeated page requests.

Completing the hackathon definition of done still requires reachable primary sources, verified dated balances and maturities, a source-backed customer deal, a successful final live dossier and a working Neon connection. The V2 backlog added concurrently on main is preserved and intentionally not implemented in this V1 task.
