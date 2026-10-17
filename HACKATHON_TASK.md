# NeoCloud Debt Intelligence: Recursive Agents Hackathon MVP

**Status:** ACTIVE. This supersedes the earlier "Autonomous Colo Scout" requirements entirely.
**Date:** 2026-10-17
**Repository:** https://github.com/joedatacap/aidatacenter2
**Mission:** In roughly two hours build a functional app that answers: **Which publicly traded neoclouds have greater exposure to higher rates and credit tightening, and why?** Implement a genuine Crusoe-powered autonomous research team that discovers, verifies, reconciles and maintains the evidence.

## Product and user journey

**Name:** NeoCloud Debt Intelligence. **Tagline:** Which AI infrastructure companies survive higher rates?

User enters **one or two stock tickers** (MVP supported: `CRWV`, `NBIS`, `IREN`, `BTDR`; optional `APLD`, `CORZ` later). Example: compare `CRWV` vs `NBIS`.

App shows:
1. **Company summary:** outstanding debt as of filing date; recourse/nonrecourse where available; cash, interest cost, maturities, fixed/floating/hedged exposure; disclosure coverage and caveats.
2. **Debt instrument ledger:** issue date, original commitment, drawn/outstanding principal *as of date*, seniority, maturity, coupon OR benchmark+spread, fixed/floating/convertible, hedge data, debt source URL and excerpt; never confuse capacity and borrowings.
3. **AI customer deal ledger:** major customer contracts, contract value, term and counterparties with citations. Link each contract to a financing instrument *only where direct evidence exists*. If unknown, explicitly show **Financing linkage unverified**. A $40B revenue commitment is not a $40B funded loan. A project financing may finance GPU capex, not the entire nominal future customer revenue.
4. **Markets:** historical stock closing prices and returns over user-selected 1W / 1M / 3M windows; optional benchmark ETF or NASDAQ comparison. Show market rates and bond yields only if credible time-stamped data are actually available. Dates and source required. Display price changes as association, NOT causal proof.
5. **Rate sensitivity:** interactive +0 / +100 / +200 / +300 bps (and -100 if easy) scenarios with **near-term cash interest impact only on unhedged floating debt**, separate from **future refinancing scenario** on debt maturities. Include modeled assumptions and insufficient-data warnings. No automatic assumption that fixed debt reprices with market yield.
6. **Investigation feed:** agent manager planning, spawning specialized agents, tool searches, citations, verifier objections, autonomous follow-up child task, resolution, final dossier. Filter by ticker/run.
7. **Comparison result:** interpret actual risk drivers (financing cost, rate exposure, time to refinance, hedges, recourse, customer/collateral risk, capex gap, equity dilution) rather than mechanically rank by total nominal debt.

IMPORTANT: No N+1, liquid cooling, 3–30 MW site filtering, or Q4 2027 site deadline. Those are from the *abandoned* Colo Scout project. Do not build them.

## Hackathon demonstration and recursive behavior (nonnegotiable)

Crusoe/Cerebral Valley asks for autonomous agent teams that plan, spawn subagents, delegate, communicate, maintain memory, recover from errors and finish without user micro-management. The demo MUST showcase a **manager that dynamically decides what other tasks to spawn** based on intermediate evidence, NOT a fixed pipeline of four prompts.

Suggested agents operating at **application runtime**:
- **Orchestrator / Research Manager:** decomposes ticker comparison into bounded tasks, supervises agents, detects gaps, reprioritizes, and decides when to stop.
- **Debt & SEC Filings Investigator:** searches company SEC 10-Q/10-K/8-K, debt tables and instrument indentures; extracts dated balance/rate/maturity/collateral/hedges.
- **Customer Deal & Financing Mapper:** researches customer contracts and project funding, builds explicit sourced links; differentiates announced deal vs financed capex vs facility commitment.
- **Public Markets Researcher:** gets dated equity price data/returns, optionally public bond yields or Treasury/SOFR, explains contemporaneous movements carefully; never invents stock/bond quotes.
- **Auditor / Challenge Agent:** checks data source lineage, flags coupon-vs-yield errors, stale outstanding amount, missing hedge info, double counting, inconsistent totals and false deal-to-loan matches.
- **Dossier / Presentation Agent:** compiles manager-approved findings into UI-ready narratives and comparison cards, *not* a code-writing agent.

**Codex Cloud** is the separate **build-time software engineer** writing the app. Do not waste hackathon time creating a runtime agent that self-modifies the application's source. The dossier agent is the runtime equivalent of "an agent that builds the answer".

**Prove recursion:** E.g., for CRWV investigator captures 2032 9.625% fixed note, market analyst sees a ~15% secondary yield, auditor flags an invalid inference that annual contractual coupon jumped to 15%, manager spawns `Verify bond issue coupon vs secondary market yield and refinancing implications`, specialized child collects SEC/IR evidence, result is corrected, timeline shows full sequence. Or hedge gap on IREN triggers hedge-research task. Only count as a live Crusoe agent workflow if a model actually initiated the follow-up; a fixture test must be labeled as simulated.

**Persistence:** Save runs, tasks, parent_task_id, agent event log, sources, evidence assertions, instruments and price observations in Neon Postgres. Run background task worker independent of browser tab. Browser can close/refresh without stopping active run so long as server remains running. Handle timeout, retries, duplicate tasks and crash recovery. Caps: max 18 delegated tasks, 25 Crusoe LLM calls, 15 searches, 2 retries/task, 5-minute runtime/run. Display explicit status and stop reason.

## Data model (minimum practical)

`companies`: ticker, name, asset/filing base currency, sector, URL. Include **Bitdeer Technologies Group (BTDR)** and distinguish its Bitcoin-mining legacy from newer AI/HPC activity; do not assume all revenue/capex is AI-specific.
`customer_deals`: company_id, counterparties, announced date, nominal contract value, value currency, duration, deal status, evidence_id.
`instruments`: company_id, instrument_id/name, parent entity/SPV, issue date, type, commitment_amount, drawn_amount, outstanding_principal, snapshot_date, currency, coupon_pct, rate_type, reference_index, spread_bps, maturity, recourse_type, secured, convertible, hedge_status, hedge_notional, evidence_id.
`deal_financing_links`: contract_id, instrument_id, link_type (explicit / uncertain), linked capex amount where disclosed, evidence_id.
`market_observations`: ticker_or_security, observation_date, metric_type (stock_close, bond_yield, SOFR, treasury_yield), value, currency/unit, source.
`evidence`: source_url, source_title, publisher, publication_or_filing_date, retrieved_at, exact supporting excerpt, confidence, claim_id.
`runs`, `tasks`, `agent_events`: lifecycle, dependencies, parent_id, status, retries, budget usage, timestamp.

Keep CSV/JSON source seed fixtures separate from real-time live research; mark `fixture` clearly.

## Required finance rules

1. **Issue coupon != secondary-market yield != refinancing rate.** An outstanding fixed coupon doesn't instantly change as traded yield rises.
2. Variable-rate current expense = outstanding unhedged benchmark-linked principal × (benchmark + spread), subject to floors; only unhedged principal responds immediately to a benchmark rate delta.
3. A fixed-to-floating swap or rate hedge changes economic exposure; do not label an entire facility as unhedged if SEC discloses a hedge.
4. +200 bp near-term illustration: annualized incremental cash interest ≈ `unhedged_float_outstanding * 0.02`; ignore uncommitted/undrawn amounts, show no-hedge assumption explicitly where hedge status unknown.
5. Refinancing scenario: `principal_maturing_within_horizon × (assumed_new_rate - old_rate)`, clearly labeled **future illustration**, not current cash expense. Some debt may repay/amortize or not refinance.
6. Convertible coupons can be low but economic costs include dilution and conditions; do not present a 0.5% convertible as automatically "cheapest capital".
7. Credit risk depends on recourse, structure/SPVs, cash flows and collateral; avoid blanket company rankings unless evidence supports them.
8. Different financing vintages matter: issued date, reference benchmark, spread, amount outstanding and as-of date.
9. Preserve EUR versus USD amounts; do not sum currencies without explicit dated FX rate. Do not sum commitment ceiling + drawn loan twice. Distinguish gross and net balances.
10. Missing evidence is `unknown`, not zero. Publish "Disclosure incomplete" if coverage is low.
11. No investment recommendations or fabricated causal explanations for market moves.

## High-value verified primary-source starting points (seed only faithfully extractable facts)

**CoreWeave 2026 Q2 10-Q**, SEC Note 10:
https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/crwv-20260630.htm
- Contains Q2 2026 instrument-specific balances / recourse vs nonrecourse / effective rates / maturities.
- Issued DDTL 4.0 March 2026, $8.5B **facility commitment**, SOFR+2.25% or Treasury+2%; DDTL 5.0 May 2026 $3.1B facility, SOFR+4.50%.
- $2.75B 9.75% 2031 notes (Apr 2026); $1.25B 9.625% 2032 notes (Jun 2026); €2.0B 8.50% 2032 notes; $4B 1.75% convertible 2032 notes.
- Need carefully reconcile **undrawn facility size** versus on-balance debt; effective interest rates in debt table differ from contractual coupons.
IR announcement for June notes: https://investors.coreweave.com/news/news-details/2026/CoreWeave-Announces-Pricing-of-1-25-Billion-of-Senior-Notes-and-2-Billion-of-Senior-Notes/default.aspx

**Nebius July 17 2026 senior secured facility**:
https://nebius.com/newsroom/nebius-raises-775-million-in-first-secured-debt-financing-to-accelerate-global-buildout
- Approximately $775M secured facility, priced SOFR+2.50%, matures October 31 2030, GPU/contract cash flow backed.
**Nebius Aug 24 2026 convertibles**:
https://www.sec.gov/Archives/edgar/data/1513845/000110465926100347/tm2623863d1_ex99-1.htm
- $3.45B 0.50% convertibles due 2030 and $2.3B 4.50% convertibles due 2034 (aggregate originally issued $5.75B).

**IREN annual SEC filing for FY ended June 30 2026**:
https://www.sec.gov/Archives/edgar/data/1878848/000187884826000052/iren-20260630.htm
- GPU financing announced/entered in May 2026 through SPV: approximately $1.5B DDTL (1-month SOFR+2.25%) + $2.1B private secured notes (5.96% fixed).
- $413M DDTL drawn as of June 30, 2026;  ~$394M of that hedged under forward-starting swap (verify as-of, swap terms and notional before scenario modeling).

**Contemporary market context only, not an instrument table**:
https://www.reuters.com/business/red-hot-cpi-report-fuels-ai-rout-2026-10-14/
https://www.reuters.com/legal/transactional/coreweaves-ai-contracts-lenders-financing-its-build-out-2026-10-15/

Use primary SEC and investor disclosures first. Secondary press reporting as context or fallback and explicitly attributed. Discover additional first-party links through agent tools when available. Don't parse/reproduce huge SEC filings wholesale into prompts; retrieve and extract scoped passages.

## Technical architecture

- Python 3.11+, FastAPI server, Neon Postgres persistence, simple responsive HTML/CSS/JS or lightweight charts (Plotly CDN only if available, otherwise simple SVG/JS). No React build chain required for initial proof.
- Crusoe Managed Inference via OpenAI-compatible client `https://api.inference.crusoecloud.com/v1`, `CRUSOE_API_KEY` from secure environment; test available Nemotron model and structured JSON responses first.
- Search via available provider, preferably You.com with optional `YDC_API_KEY`. If live discovery isn't accessible, seeded known primary URLs with actual retrieval/extracting and citations; fall back to labeled curated offline fixtures if external internet blocked.
- Equity OHLC source optional, must have explicit source/as-of and use real data; fallback show **Market data unavailable**, not simulated market performance unless a DEMO MODE label. Financial chart is secondary to robust debt analysis.
- Store evidence as structured JSON. Verification rule-based plus LLM review. Include monetary units / date/currency normalization.
- Add .env.example and .gitignore; NEVER expose API keys, raw tokens or commit .env.

## Realistic 2-hour build order

**0–15 mins**: verify Crusoe API, build skeleton and run Postgres schema migration, start FastAPI app. A real inference test is the gate.
**15–40 mins**: create sourced CRWV/NBIS/IREN instrument seeds with 2–4 instruments each and add source-backed BTDR instruments as research permits; develop rate-sensitivity calculator. Prioritize accurate two-ticker demo and don't fabricate BTDR loan terms.
**40–75 mins**: implement Crusoe manager + researcher + auditor dynamic spawn/persistent queue (live or exact-URL tools).
**75–100 mins**: ticker input & comparison dashboard, evidence link cells, 100/200 bp calculator and activity feed.
**100–120 mins**: test actual end-to-end run, capture demo, polish README, commit and open PR; deployment only if core fully works.

## Judge demo: 90 seconds

1. Type **CRWV** vs **NBIS** (or **IREN**).
2. Hit **Investigate** and show a Crusoe-powered planning agent dispatch the debt, deal, and market researchers.
3. Highlight a live *issue coupon vs market yield* contradiction or missing hedge detail.
4. Auditor asks manager to spawn an additional research child; show **parent task → new subagent → evidence → correction** live in the agent feed.
5. Review side-by-side instrument table, evidence citations, fixed vs floating vs hedged, and rate-shock comparison.
6. Refresh dashboard to demonstrate persistence. End with ranked risk *dimensions* and unknowns, NOT a fabricated definitive default probability.

## Definition of done

- [ ] Real Crusoe Nemotron call succeeds and logs sanitized model metadata.
- [ ] Two ticker comparison works for any of **CRWV/NBIS/IREN/BTDR**. All four appear in ticker search; at least two are fully researched in demo. Unsupported BTDR figures are flagged unknown.
- [ ] At least 5 source-backed debt instruments with dated principal, rate and maturity.
- [ ] At least one verified customer deal documented, but unlinked to debt if linkage absent.
- [ ] A real manager-initiated dynamic child task generated after auditor concern.
- [ ] Persistent manager, task queue, status feed and findings in **Neon Postgres**; browser refresh safe.
- [ ] Clear coupon vs market yield distinction, hedge handling, correct unhedged floating sensitivity.
- [ ] Finite budgets, retries, crash-safe states and unit test for calculator.
- [ ] Real market data with timestamp OR explicit unavailable label; no invented prices.
- [ ] Public GitHub commits, instructions, truthful demo state, simple README.


## Database decision: Neon Postgres, NOT SQLite

The user already has Neon, Supabase and Cloudflare accounts. **Use Neon as primary production and hackathon database** to store companies, contracts, debt instruments, market observations, evidence, investigations, parent-child tasks and agent event history. Avoid adding Supabase unless essential, and don't choose Cloudflare D1. Cloudflare can be used later for static frontend hosting, but it does not replace the persistent Python agent worker.

- Create a fresh Neon project or branch dedicated to the hackathon.
- Expect `DATABASE_URL` to be provided securely by the user in Codex Cloud environment/personal vault; never prompt them to paste it in chat or commit it.
- Configure `DATABASE_URL` and `CRUSOE_API_KEY` in Codex Cloud via the UI. Prefer **Network secret** for Crusoe on allowlisted `api.inference.crusoecloud.com` (HTTPS 443). Neon Postgres URI is a direct TCP connection, not a request eligible for HTTPS network-secret substitution; use a scoped **Personal vault environment variable** if needed, keeping its value from logs and commits.
- For managed deployment, set the same environment variables in the hosting provider's secret manager; Codex Cloud is for building and testing, not durable hosting.
- Use Postgres-specific SQL types sparingly. `NUMERIC` for financial amounts, `TIMESTAMPTZ`, `JSONB` for structured claims, foreign keys, and indexes on `ticker`, `instrument_id`, and `parent_task_id`.
- Pooled Neon connection string is recommended for the web app, SSL required. Check if Codex Cloud network supports outbound Postgres TCP; if restricted, test using deployed backend or use Neon's HTTPS Data API as a fallback. Never pretend a DB connection succeeded.
- If Neon is temporarily inaccessible, continue writing pure calculation and orchestration tests with fake repositories or mocks, but do not pivot to a SQLite-only solution.
- Restrict DB privileges and use a dedicated hackathon database to protect other user data.

## BTDR research requirements

**Bitdeer Technologies Group (NASDAQ: BTDR)** is added alongside CoreWeave (CRWV), Nebius (NBIS) and IREN (IREN). Extract primary financing facts from BTDR's SEC filings / official IR, capturing convertible issuance, coupons, security, and maturity where disclosed. Be careful to distinguish its Bitcoin mining and ASIC manufacturing activities from AI/HPC/neocloud initiatives. Show that mixed business model openly in the compare UI. This app tests financing exposure across AI-compute infrastructure companies, not an assertion that all four are pure-play neoclouds.

## Codex instruction

Implement this updated spec instead of previous site-selection instructions. Do not reuse or implement stale Colo Scout scope. Work to a running end-to-end MVP; prioritize recursion, evidence correctness and working two-ticker comparison. Make incremental commits; do not stop at a plan. If `CRUSOE_API_KEY` is missing or external access blocked, continue implementing and testing with explicitly marked fixtures, then report exactly what human input is needed.
