# Six-company evidence review — November 16, 2026

Research payload: `neocloud/data/watch_benchmarks.json`. The execution cutoff is November 16, 2026. Public issuer releases, SEC exhibits/filings and one issuer-hosted outlook presentation were reviewed; retrieval timestamps are retained separately from financial dates. The private Earnings Board file was used to find candidate reports, not as verified numeric evidence or public narrative.

## Latest reports and historical depth

| Company | Latest period | Latest source publication | Reviewed history | Revenue in latest quarter | Main qualifications |
| --- | --- | --- | --- | --- | --- |
| CoreWeave | Q3 2026, September 30 | November 10 release; original financing filing retains its separate date | Q4 2025–Q3 2026, four quarters | $3.661B | Cash capex is the cash-flow purchase line; issuer capital-expenditure guidance has a broader definition |
| Nebius | Q3 2026, September 30 | November 12 | Q4 2025–Q3 2026, four quarters | $980.8M | Continuing operations; prior Toloka amounts reclassified. Share-count/market-cap ratio blocker remains |
| IREN | Q1 FY2027, September 30 | November 5 | Q2 FY2026–Q1 FY2027, four quarters | $228M | June fiscal year-end. Q3 FY2026 is a March-quarter comparative observation in the August 27 release, not a claim that the original report occurred in August |
| Applied Digital | Q1 FY2027, August 31 | October 7 | Q2 FY2026–Q1 FY2027, four quarters | $341.875M GAAP | $300.393M adjusted revenue excludes ChronoScale. GAAP and adjusted company scopes remain distinct |
| Hut 8 | Q3 2026, September 30 | November 4 | Q4 2025–Q3 2026, four quarters | $71.071M GAAP | The $99.44M candidate reference does not replace GAAP revenue. Adjusted EBITDA definition changed in Q2 2026; historical accounting-basis labels preserve mark-to-market inclusion/exclusion |
| TeraWulf | Q3 2026, September 30 | November 6 | Q4 2025–Q3 2026, four quarters | $76.230M | HPC lease revenue $62.986M is a segment amount, not additional consolidated revenue |

All six latest-report statuses are `verified` after bounded issuer/filing searches and primary-content review. This means the latest available report was identified at the cutoff, not that every requested metric is populated. Every company has an explicit next-earnings-date status: a future issuer-confirmed date was not established. Future project targets remain separate from earnings-calendar dates.

Prior-year revenue comparisons are stored in the latest quarter as dated `revenue_prior_year` observations, with the later source publication retained. They are not fabricated historical release events. IREN's comparative revenue is rounded to USD millions in its latest filing; computed growth uses those disclosed rounded inputs. Other reported precision likewise remains the precision of the source.

## Guidance and promised-versus-delivered examples

CoreWeave's issuer-hosted August 11 Q2 outlook PDF was verified directly:
https://s205.q4cdn.com/133937190/files/doc_financials/2026/q2/CoreWeave-Q2-26-Earnings-Outlook-Presentation.pdf

Page 3 records FY2026 revenue guidance of $12.4B–$13.2B and capital expenditures of $35B–$39B. The November 10 release records $13.0B–$13.3B revenue and $37B–$39B capital expenditures. Both prior/current observations retain immutable dates, scope, units and the same future period. The builder derives the midpoint classifications and changes. The August presentation also contains Q3 revenue guidance of $3.45B–$3.60B, versus actual $3.661B. That is a management-guidance comparison, never a consensus beat.

Nebius's November 12 shareholder letter says FY2026 revenue is expected at the low end of its prior $3.0B–$3.4B range; no new point estimate is manufactured. It also moves December ARR timing to February. The separately dated original ARR record is not established here, so the revision is shown without a met/missed judgment.

IREN's August 27 FY2026 release states its operating ARR target for December 31, 2026. The November 5 release moves that target into January 2027, potentially February. The dataset preserves the original and the revision. ARR remains an operating target subject to commissioning, testing and customer acceptance, rather than recognized revenue.

Applied Digital's October 7 release records an additional 75 MW phase Ready for Service after quarter-end, taking Polaris Forge 1's live critical IT capacity to 250 MW. The financial period stays August 31; the operating disclosure stays October 7. It does not establish a consolidated fleet or a parent-owned GPU inventory.

TeraWulf's November 6 release distinguishes 102 MW of revenue-generating critical IT capacity from October energization of CB-3/CB-4 and ongoing tenant acceptance. It retains CB-5's early-2027 future phased-delivery target. Hut 8 retains River Bend's Q2 2027 initial data-hall target, project recourse and restricted-cash qualifications.

## Transparent quarter derivations

- Hut 8 Q3 operating cash flow: nine-month $(5.031)M minus six-month $(32.845)M = **$27.814M**. Original nine- and six-month observations are retained.
- Hut 8 Q3 cash property/equipment purchases: nine-month $1,092.208M minus six-month $616.182M = **$476.026M**. This does not add noncash equipment financing or leases.
- TeraWulf Q4 2025 revenue: annual $168.455M minus compatible nine-month $132.619M = **$35.836M**. Both source inputs and `period_difference/v1` are preserved; the quarter is explicitly derived. The nine-month comparative comes from the later quarterly filing, so the derivation is a reviewed historical reconstruction, not a claim about the exact original Q4 presentation.

IREN retains two distinct Q1 FY2027 cash investing lines: $2.131B property/plant/equipment net of computer hardware, and $2.693B computer hardware. The generic cash-capex field remains qualified rather than silently blending amounts or noncash additions. Quarter-specific cash flow/capex remains incomplete for other histories, especially WULF. YTD totals are never displayed as standalone-quarter values.

## Outstanding evidence work

- Reconcile all pre-release consensus snapshots, event timestamps and split-adjusted T+1/T+5 closing-price windows. Imported T+3 strings are not reused as other return windows.
- Complete remaining quarter-only cash-flow and cash-capex histories; preserve input dates and restatement versions when deriving them.
- Add current confirmed future earnings dates only when the issuer announces them. Do not roll expired dates forward by assumption.
- Expand current instrument-level amortization/recourse coverage beyond the inherited reviewed financing inventory. Existing repayment schedules and the Hut 8 timing discrepancy are preserved.
- Reconcile consolidated live IT capacity, utilization and GPU fleet ownership where not disclosed. Named deployments or energized power are not a company total.
- Keep American Bitcoin inside Hut 8 consolidated scope and ChronoScale inside Applied Digital GAAP scope; never aggregate these parent/subsidiary values as independent industry totals.

Direct shell access to some issuer IR hosts was denied by proxy policy. The same public primary pages were accessible through the web connector, and SEC alternatives were used where available. No paywall or account was bypassed. The review did not import private operational material, opinion scoreboards or monitoring claims from the reference repository.

## Resume instructions

Run `npm run build:watch` and the documented watch tests after changing the payload. The authoritative source facts are in `watch_benchmarks.json`; scratch fetch/extraction scripts and original downloads under `work/` are not production inputs. Do not rerun the initial scratch generator to overwrite subsequent evidence corrections. Use the build's reference validation and the generated coverage matrix to identify remaining fields. Updating review timestamps alone does not refresh financial, operating or market observations.
