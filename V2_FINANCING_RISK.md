# V2 SPEC: NeoCloud Debt Intelligence — Financing Risk Engine
**Created:** October 17, 2026
**Status:** V2 backlog. Do NOT replace or interrupt the active V1 Codex Cloud task.
**Prerequisite:** V1 app establishes evidence-backed financing ledger, Crusoe research agents, Neon persistence and interactive comparison.
**V1 instructions:** [HACKATHON_TASK.md](HACKATHON_TASK.md)

## Product thesis

Don't ask only "How levered is the company?" Ask "**How much capital will it need soon, what price will lenders demand, and how much of its revenue reliably supports repayment?**" The risk engine should explain **why** two operators react differently to interest-rate or credit-spread shocks.

**Covered public companies:** CRWV (CoreWeave), NBIS (Nebius), IREN, BTDR (Bitdeer), **HUT (Hut 8)**. Hut 8 and Bitdeer also have non-neocloud revenue; label their segment mix and avoid pure-play comparisons without caveats.

### Five priority lenses, in order

| # | Lens | KPI | Caution |
|---|---|---|---|
| 1 | 12–18-month future **funding gap** | estimated net **unfunded financing need** / equity market cap, by base/downside case | Forward-looking estimate, not existing outstanding debt; avoid false precision |
| 2 | **Market cost of debt** | timestamped **yield-to-maturity/price** for a specified bond, versus its contract coupon and original yield | Different bonds/priority/trading dates not interchangeable; no data means unknown |
| 3 | **Revenue backing quality** | supported contract revenue, guarantee/prepay details, committed vs merchant exposure | Project-level Google support is not a guarantee of all corporate debt |
| 4 | **Debt service coverage and rate exposure** | annualized EBITDA/cash interest, cash-flow caveats, floating and unhedged principal | Negative EBITDA => N/M (not zero or infinity); capitalized interest and project construction can distort |
| 5 | **24-month maturities** | debt principal due inside 24 months and how funded | Include amortization/current portion, not just final bullet maturity |
| secondary | gross/net debt / market cap | leverage context; gross/net terms and as-of dates | Stock price decline mechanically increases the ratio |

## Model routing and roles: runtime Crusoe, not coding

**Use user's ChatGPT/Codex subscription for DEVELOPMENT. Never route Codex development through Crusoe unless user explicitly changes this.**
**Only application runtime agents consume Crusoe inference credits.** Keep shared backend/orchestrator in Python, persistence in Neon Postgres, and financial formulas deterministic Python.

| Runtime agent | Primary Crusoe model ID | Role / rationale | Fallback |
|---|---|---|---|
| Research manager | `zai/GLM-5.3` | Complex goal decomposition, dynamic child-task delegation, gap prioritization | `deepseek-ai/DeepSeek-V4-Pro` or `zai/GLM-5.3-Flash` |
| Financial auditor / critic | `zai/GLM-5.3` | Challenge disclosure mapping, double-counting, coupon/yield, guarantee scope | `deepseek-ai/DeepSeek-V4-Pro` |
| Debt extraction + SEC analyst | `deepseek-ai/DeepSeek-V4-Flash` | High-volume scoped extraction, normalization of tables | `zai/GLM-5.3-Flash` |
| Customer-deal / offtake analyst | `zai/GLM-5.3-Flash` | Contract risk, guarantee/prepay research | `deepseek-ai/DeepSeek-V4-Flash` |
| Equity/credit market analyst | `zai/GLM-5.3-Flash` | Timestamped prices and yields, interpretation | `deepseek-ai/DeepSeek-V4-Flash` |
| Dossier/presentation summarizer | `zai/GLM-5.3-Flash` | Compact attributed narrative after manager approval | `openai/gpt-oss-120b` |
| Tiny classification/triage | `openai/gpt-oss-120b` or `nvidia/Nemotron-3-Nano-30B-A3B` | Cheap labeling/routing; optional if model available | `deepseek-ai/DeepSeek-V4-Flash` |

Model IDs above align to the Crusoe published Serverless Inference model catalog as of October 17, 2026; **test /v1/models on user's account and a real structured/tool-call response before relying on any.** Do not assume every account has every endpoint. Agent role->model route should be configurable by env or DB settings with a UI diagnostics view. Track model ID, latency, input/output token usage, and estimated billed cost per run. Enforce default per-run Crusoe budget $2 (configurable) and global soft budget $40 of available $55, plus max tasks/turns and retries. Gracefully degrade to supported fallback models if 404/model unavailable, 429/rate-limited, or JSON/tool parsing fails. Do **not** route to an OpenAI API key or charge the user's ChatGPT subscription for runtime agents.

Pricing references (per 1M tokens, input/output):
GLM-5.3 $1.40/$4.40; DeepSeek V4 Flash $0.14/$0.28; GLM-5.3 Flash $0.15/$0.50; GPT-OSS 120B $0.05/$0.25; Nemotron 3 Nano $0.05/$0.20. Refresh from https://www.crusoe.ai/cloud/pricing and show estimated costs, not guaranteed billing.

## Metric 1: 12/18-month projected FUNDING GAP vs market capitalization

For each company and each horizon (12 and 18 months), build a traceable **sources-and-uses waterfall**. A useful starting heuristic:

```
gross_required_funding =
  projected committed_and_necessary_capex
+ project equity contributions
+ scheduled debt principal repayments / amortization
+ forecast operating cash burn
+ other mandatory cash uses

identified_internal_and_external_funding =
  unrestricted opening cash usable for these obligations
+ reasonably forecast net operating cash generation
+ committed UNDRAWN financing available for same purpose, net of covenants/conditions
+ binding customer prepayments usable in period
+ other secured committed inflows not already included

estimated_unfunded_gap = max(0, gross_required_funding - identified_internal_and_external_funding)
funding_gap_to_market_cap = estimated_unfunded_gap / equity_market_cap_as_of
```

**These are scenario estimates, not factual debt outstanding.** Keep independent rows for committed, management-guided, analyst-estimated, and speculative capex. Do not double-count debt proceeds already reflected in cash or count restricted project loans as unrestricted corporate funding. Tag source date, currency, segment, project, certainty, refinancing assumptions and management discretion to defer capex. Show numerator AND denominator plus market cap timestamp. Use explicit `insufficient_inputs` if gap cannot be estimated responsibly; allow clearly labeled scenario assumptions instead of a fake precise value.

MVP scenarios: `Base` (management guidance where available), `Downside` (operating inflows smaller, borrowing costs higher), `Tight credit` (undrawn not contractually secured unavailable / refinancing more expensive). Sensitivity sliders should affect assumptions, not claim forecasts as fact.

## Metric 2: current cost of debt and credit spread

Expand instrument model to include `security_id/ISIN/CUSIP`, `observed_price`, `market_yield_pct`, `yield_type` (YTM, yield-to-worst, current yield, indicative), `quoted_at`, `source`, `quote_type`, `bid_ask`, `estimated_liquidity`, and `coupon_pct`.
- Clearly distinguish **original issue coupon**, **original issue yield**, **current secondary-market yield**, **floating benchmark+spread**, and **refinancing scenario rate**.
- Quote must identify the specific bond and timestamp. If no licensed/free recent quote exists, show `Yield unavailable` plus last dated, attributed media reference; no unsourced “current 15.8%”.
- A secondary-market yield change does NOT reprice existing fixed debt's contractual cash interest.
- Credit spread = bond yield minus matched-maturity Treasury only when maturity and source dates align; otherwise don't show.
- Historical loan origination spreads also matter; compare fixed vs floating as separate lenses.
- **As of Oct 16, 2026, press reporting put CoreWeave bond yields around/above 15%**, but not a validated real-time 15.8% quote across all CRWV instruments. Do not create synthetic daily bond-price chart.

## Metric 3: Revenue backing / debt service support

Project- and instrument-level relationship graph:
`company -> SPV/project -> facility/notes -> underlying customer lease/offtake -> obligor -> guarantor -> prepayment -> evidence`.

Capture:
- customer and legal obligor, contract status/signed/executed, annual/minimum payment terms, escalators, term, commencement, termination/conditions
- contract coverage of financed project and collateral, take-or-pay/fixed rent vs capacity sold at market, related-party and concentration risk
- guarantee/backstop legal provider, amount/cap, covered obligations, covered period, conditions, whether direct/limited, credit rating **of guarantee provider** as of date
- cash prepayments and whether refundable/restricted
- debt entity (parent vs SPV), recourse, seniority, amortization, guarantees, liens
- construction completion milestones and project operating risk
- evidence URLs and a category: `verified guarantee/backstop`, `contracted-not-guaranteed`, `prepaid`, `merchant/spot`, `unverified`.

Avoid a fake categorical one-number "safe" badge; show backing and structural protections individually.

### Verified HUT evidence, with narrow interpretation

1. Hut 8 Dec 17 2025 River Bend Fluidstack 245MW, 15yr ~$7B lease, Google financial backstop covering lease payment and related pass-through obligations (NOT a blanket guarantee for all HUT debt):
https://www.sec.gov/Archives/edgar/data/1964789/000110465925122052/hut-20251217xex99d1.htm
2. Hut 8 June 30 2026 SEC 10-Q: Hut 8 DC LLC $3.25B 6.192% senior secured River Bend notes, due Nov 15 2042; project finance supported by lease cash flows:
https://www.sec.gov/Archives/edgar/data/1964789/000110465926090025/hut-20260630x10q.htm
3. Hut 8 June 9 2026 investor announcement: Beacon Point $4.25B, 6.129% senior secured notes due 2042, **Baa2 investment-grade project debt**; company describes a total of $7.5B investment-grade project financing:
https://www.hut8.com/news-insights/press-releases/hut-8-closes-usd4-25-billion-of-investment-grade-senior-secured-notes-for-beacon-point-data
4. Sept 28 2026: Parent level $1.07B secured revolver; Hut 8 states it is **pursuing** an investment-grade corporate profile, not that all its debt/corporation already have that rating:
https://www.sec.gov/Archives/edgar/data/1964789/000110465926111154/tm2625691d1_ex99-1.htm
The user's ~0.9× debt/market-cap ratio is a **hypothesis to recalculate**, not a seeded verified point-in-time fact.

## Metric 4: coverage + floating exposure

- Calculate `adjusted EBITDA / cash interest` using consistent trailing 12-month periods and clearly explain EBITDA limitations. If adjusted EBITDA excludes significant recurring costs or company definition differs, surface caveat and optionally standardized EBITDA variant. Show EBITDA margin and coverage as separate context.
- Also show CFO, FCF after maintenance/growth capex if available and cash interest paid; interest may be capitalized during construction. Report both total interest expense and cash interest paid where disclosed and explain discrepancy.
- If adjusted EBITDA <= 0, `negative/not meaningful` instead of a misleading positive coverage score.
- `gross_floating_principal`, `fixed_principal`, `hedged_floating_principal`, `unhedged_floating_principal`, `hedge_notional`, `hedge_expiry` all as of date, with unknown bucket.
- +100/+200 bps immediate annualized expense = **known unhedged floating outstanding** × rate delta; add floors, hedge expiration dates and debt repricing cadence where available. Unknown hedge coverage != 0.
- Keep future refinancing sensitivity separate.

## Metric 5: 24-month maturity wall

- Identify scheduled amortization and maturity principal due in next 12, 18, and 24 months, relative to selected `as_of_date`. Group by company/parent/SPV and recourse type.
- Show capacity to repay: cash available to entity, cash generation, committed refinancing, asset-backed collateral (not automatically cash).
- If financial statements only publish maturity buckets, preserve ranges and precision; never invent a precise month.
- Charts should show principal due by quarter if source granularity allows, otherwise buckets.

## Dashboard / UX

**Top interaction**: enter one/two tickers; default `CRWV vs HUT` to dramatize divergent financing quality, with one click `CRWV vs NBIS`, `IREN vs BTDR`.

- **Overview**: side-by-side five risk dimensions as sourced facts + uncertainty states, no unsupported composite “safety score.”
- **Funding gap**: 12m/18m capex + cash + financing sources waterfall; market-cap denominator and dates; Base/Tight credit scenarios.
- **Debt cost**: instrument-level fixed coupon vs last dated traded yield; current benchmark/spread; 100/200/300bp shock.
- **Revenue backing**: financing-to-project-to-contract relationship explorer, backed lease vs merchant comparisons, guarantee scope.
- **Coverage & maturity**: TTM cash interest, adjusted EBITDA, floating hedge share, maturity wall.
- **Agent activity**: parent-child investigation tree, evidence citations, audit objections and corrections, latest fetched timestamps, model routing and cost.
- **Confidence/source legend**: verified filing, issuer announcement, reputable press, estimated scenario, unavailable.

Preserve fast-load skeleton even when missing data; do not wait for exhaustive research to render. Every number shows unit, as-of date and source link or estimate flag. Add JSON/CSV export if easy.

## Autonomy: what new research agents must do

V2 Research Manager on Crusoe:
1. Runs **coverage assessment** for requested ticker; identifies missing 12m/18m financing needs, missing bond-yield quotes, missing parent guarantee scope, or stale maturity table.
2. Delegates to `FundingNeedsAgent`, `BondMarketAgent`, `ContractBackingAgent`, `InterestCoverageAgent`, `MaturityAgent`, and `VerificationAgent` through actual scoped tasks with parent IDs.
3. Auditor identifies double counting, missing hedge facts, stale quote, or inaccurate guarantee attribution; requests a *new* follow-up child task.
4. Manager independently decides which issues are resolvable under search and cost limits; updates Neon Postgres source records, never fabricates unresolved fields.
5. Generates final risk explanation comparing why same +200bps or tighter credit availability yields different effects.

Budget initially <=25 LLM calls, <=18 tasks, <=15 web fetch/search operations, <=5min walltime per run, <=$2 estimated Crusoe inference charge per run, and logging/token costs. Set sensible configurable caps. This V2 work must **not modify V1 code until user starts a fresh Codex iteration**, because an earlier Codex Cloud task may still be writing V1.

## Build plan for Codex High (separate V2 task)

P0: Run V1 tests and check database migrations/credential environment. Preserve working V1.
P1: Add HUT primary-source seed (River Bend, Beacon Point, parent revolver) with source/legal-entity separation and issuer/guarantor fields; add V2 data migrations and date-aware modeling.
P2: Implement calculators and unit tests for 12m/18m funding-gap waterfall, safe ratios, interest coverage, unhedged floating shock and 24m maturity buckets.
P3: Route runtime agent models by role via Crusoe; test endpoints, structured output/retries and estimate token cost.
P4: Add V2 research roles with scoped evidence tools; prove actual dynamically spawned follow-up around Google guarantee scope or old bond-yield date.
P5: Build 2-ticker V2 comparison UI and confidence labels.
P6: Verify financial assumptions, deploy after end-to-end tests, demo with `CRWV vs HUT` and `CRWV vs NBIS`.

## V2 acceptance criteria

- [ ] V1 remains functional; V2 changes isolated on a branch/PR.
- [ ] Five tickers CRWV/NBIS/IREN/BTDR/HUT selectable.
- [ ] HUT River Bend and Beacon Point project debt sourced correctly; parent vs project and Google backstop scope clear.
- [ ] 12/18-month sources-and-uses funding-gap scenario with usable amounts and missing-data states.
- [ ] Last dated bond yield distinct from coupon, tied to specific instrument; no unsupported 'live yield'.
- [ ] Contract guarantees/prepayment information modeled with legal obligor, limits, evidence and coverage caveats.
- [ ] EBITDA/cash interest, cash flow, fixed/floating/hedged split as source data permit, no invented denominator.
- [ ] 24-month maturity chart with correct as-of date and scheduled amortization where available.
- [ ] One genuine Crusoe manager-driven follow-up task from an evidence gap, persisted and viewable.
- [ ] Role-based Crusoe routing with fallback and token/cost telemetry; no OpenAI API runtime calls.
- [ ] Unit tests on financial formulas and evidence provenance.
- [ ] Document unknowns and limitations; no unfounded ranking or investment recommendation.

## Ready-to-paste Codex V2 task

> Work on V2 only, in repo joedatacap/aidatacenter2 on a new branch. Read V2_FINANCING_RISK.md plus existing HACKATHON_TASK.md. Preserve V1. Add HUT and the five prioritized risk metrics, with verified sources and date-aware calculations. Use GPT Codex through my ChatGPT subscription for coding but call Crusoe Managed Inference for every runtime AI agent, with GLM-5.3 manager/auditor, DeepSeek V4 Flash SEC extractor, GLM-5.3 Flash deal/market/dossier analyst and GPT-OSS 120B/Nemotron Nano for cheap classification. Use Neon Postgres. Add real agent dynamic follow-up behavior, audit logs, tests, and a comparison dashboard. Don't fabricate financial metrics or market yields. Implement and test, not just plan. Prepare a V2 PR. No hard-coded keys.
