# Neocloud Watch release and publication

The public site is [Neocloud Watch](https://neocloud-watch.gpuchips.chatgpt.site/). GitHub `joedatacap/aidatacenter2` on `main` is the application source. ChatGPT Sites stores the generated static publication in its own source repository on `main`. A GitHub merge runs tests and packaging dry runs. Publication is a separate operation.

## November 24, 2026 · public version 10

The existing [public site](https://neocloud-watch.gpuchips.chatgpt.site/) serves the ranked market-cap chart above both market comparison tables. The project and public audience are unchanged.

| Release record | Verified value |
| --- | --- |
| GitHub application | [PR #18](https://github.com/joedatacap/aidatacenter2/pull/18) · [merged main dddc74017f9880bdd21c60028d02dcd152644e8c](https://github.com/joedatacap/aidatacenter2/commit/dddc74017f9880bdd21c60028d02dcd152644e8c) |
| Sites deployment | Version 10 · saved version `appgprj_6afb8d8562c0819183402d9c41093312~appgver_4a98156e67fc8191acd207f66c0542d5` · deployment `appgdep_6b048822a6a48191b7ee4967408d5cf6` succeeded 24 November 2026 at 02:38:33 Singapore time · Sites source `b4facf28d2046d5da0f86611280a45ecb5c83028` |
| Source synchronization | A clean build from the release merge matched all 30 files in the candidate and in the Sites source checkout. Relative to version 9 only `watch.js` and `watch.css` changed. The financial research and the size data are unchanged. Public research JSON SHA-256 `e8ba7ea5f60218ac91d5f5d3a03250f33afb22bfb6459066092947998a89039a`. |
| Candidate | 248 Python tests including disposable TLS PostgreSQL, 110 Watch browser checks, 76 legacy preview checks, 38 workbench checks and three packaging dry runs passed. The native browser test also compared plotted lengths, exact USD labels, source and profile links, and size and peer selections against the accepted records. [CI](https://github.com/joedatacap/aidatacenter2/actions/runs/45239801724) · [Candidate browser verification](https://github.com/joedatacap/aidatacenter2/actions/runs/45239785433) |
| Public verification | Desktop and touch-emulated mobile rendered nine ranked bars and all nine monthly figures in the intact TradingView widget. Small and peer-filtered selections, dates and qualification labels, chart geometry, profiles, evidence, historical targets and research downloads passed. Served assets matched main. [Live check and screenshots](https://github.com/joedatacap/aidatacenter2/actions/runs/45240586787) |

The chart uses the [November 23 US intraday observations](SIZE_OBSERVATION_REVIEW_2026-11-24.md). Each full-dollar label preserves the rounded amount supplied by the provider. Exact valuation times are unavailable. The current Axe Compute observation is a dated, attributed headline of $79,400,000 and carries the explicit label “Provider-reported; share basis unresolved.” Its historical ratio restriction is unchanged.

On refresh, include an observation only when eligible, positive, USD-denominated, and backed by a dated current record and a public source. Omit conflicting values from the plot and give a reason. Keep the zero baseline when rescaling to a selected group. The combined size-versus-return scatter remains a future feature pending an appropriate return source. TradingView returns stay inside its hosted widget.

Production screenshots · [Desktop homepage](https://drive.google.com/file/d/1JrHV2oi9KppVzQnU7i-FbDNR0HdAxV6-/view?usp=drivesdk) · [Mobile chart](https://drive.google.com/file/d/1MsjdJ-bFxZhZE8Ug7h9LhV9FQBLG-CYa/view?usp=drivesdk) · [Mobile Small filter](https://drive.google.com/file/d/1CnDhJUIiQzZA4XMmc9J__GnByZBoC7hw/view?usp=drivesdk).

## November 24, 2026 · public version 9

The compact market comparison is live at the [existing public site](https://neocloud-watch.gpuchips.chatgpt.site/). The previous release was version 8. The project and public audience are unchanged.

| Release record | Verified value |
| --- | --- |
| Deployment | Version 9 · `appgdep_6b048324439881919d3121fbd89c5ac1` · succeeded November 24 at 02:17:16 Singapore time |
| GitHub | [Application merge 1fbc43cd2d2feb72936d6a5205b87c4cf2d50ed3](https://github.com/joedatacap/aidatacenter2/commit/1fbc43cd2d2feb72936d6a5205b87c4cf2d50ed3) · [PR #17](https://github.com/joedatacap/aidatacenter2/pull/17) |
| Sites source | `feb7c164505e6c98cf352ad620ee58f76c90f7e9` · saved version `appgprj_6afb8d8562c0819183402d9c41093312~appgver_5243de8208c08191a755c7d109e23b42`. All 30 static files match the accepted main build. |
| Data | USD caps for all nine issuers, observed intraday on November 23 US market time with date-only precision. The earlier provider metadata and the AGPU share-basis qualification appear in the sources. See the [dated source record](SIZE_OBSERVATION_REVIEW_2026-11-24.md). The research JSON hash is `e8ba7ea5f60218ac91d5f5d3a03250f33afb22bfb6459066092947998a89039a`. The complete v8 dataset outside the size observations and their review date matched before publication. |
| Tests | 248 Python tests including disposable TLS PostgreSQL, 96 Watch desktop/mobile checks, 76 legacy preview checks, 38 workbench checks and three packaging dry runs. [PR checks](https://github.com/joedatacap/aidatacenter2/actions/runs/45235606271) · [candidate and screenshots](https://github.com/joedatacap/aidatacenter2/actions/runs/45235597248) |
| Production | All nine TradingView rows displayed genuine monthly figures. The complete nine-row table, two selected peers, empty results, profile evidence, sources, original/revised Buildout targets and both research downloads passed on desktop and touch-emulated mobile. The public JS, CSS, embedded research and JSON matched main. [Live proof](https://github.com/joedatacap/aidatacenter2/actions/runs/45236796369) |

The official widget supplies performance and its timing. A separate compact table directly underneath shows the same selected tickers with linked profiles and capitalization sources. Small includes all eligible caps below $2B, Mid spans $2B to below $10B, and Large starts at $10B. The underlying research still distinguishes Micro below $300M. The original financing inputs, ratio restrictions, disclosure-review timestamps and financial cutoff of November 17 are preserved.

The [market source audit](WATCH_MARKET_SOURCES.md) documents the official widget configuration and the return-data entitlement gap. Homepage scatter coverage is 0/9. For a custom chart, establish the right to display a public derivative visualization of dated, comparable one-month returns and verify ticker-level coverage before enabling it.

For the next size update, inspect each capitalization heading and record whether the observation is intraday or a completed session. Retain conflicting metadata and exact source passages. Review the native browser artifact visually after publication and select a touch position where the entire 1M column is readable. The existing-site publication procedure below applies.

Production screenshots: [Desktop comparison](https://drive.google.com/file/d/1eWYGy6PEui_xm3CRgNCjAjGKFyicroJF/view?usp=drivesdk) · [Mobile 1M column](https://drive.google.com/file/d/1Z8Qo0Awr2a89Pt1i2NFsPwV_yWGT5OQm/view?usp=drivesdk) · [Mobile size table](https://drive.google.com/file/d/1p7I6lzNlMgYFkewTAIC_SNAytePQlm8F/view?usp=drivesdk).

## November 23, 2026 · public version 8

The existing [public site](https://neocloud-watch.gpuchips.chatgpt.site/) serves version **8**. Sites reported deployment `appgdep_6b03d2c312308191b5390b537840bd43` succeeded on November 23 at 13:44:40 Singapore time (05:44:40 UTC). The project and public audience are the same as version 6. The data was first deployed as version 7 at 13:36 Singapore time. Version 8 changed only the document policy in 26 HTML files.

Version 7 came from GitHub `0cbdbbc06482d3f95d39af8844774e3ea4e33fe9`, Sites source `6b4a97a1f61b8fd02526ed4b9ac34628f0342288`, deployment `appgdep_6b03d0ca29248191a82bd0bd7b6c434e`. [Data CI](https://github.com/joedatacap/aidatacenter2/actions/runs/45118409897) · [first public check](https://github.com/joedatacap/aidatacenter2/actions/runs/45118835435) · [host script diagnosis and research verification](https://github.com/joedatacap/aidatacenter2/actions/runs/45119031162)

| Release record | Verified value |
| --- | --- |
| GitHub application source | [Merged commit 8599abac0d8a49617830a7a15069c97f94bf19ad](https://github.com/joedatacap/aidatacenter2/commit/8599abac0d8a49617830a7a15069c97f94bf19ad) · [data PR #15](https://github.com/joedatacap/aidatacenter2/pull/15) and [hosting PR #16](https://github.com/joedatacap/aidatacenter2/pull/16) · tested release head `95e3d20a7d8c030f81f79a2fa3df5feb3074d0a7` |
| Sites publication | Source `a01fa53ece2c23f10c88214fa3f15fa3c4ba59fd` · saved version `appgprj_6afb8d8562c0819183402d9c41093312~appgver_2f491dc72bc88191ac0dda545c8c912f` · all 30 files matched the accepted root-path build before publication |
| Size observations | November 20, 2026, USD. Version 6 displayed November 13 observations. Each badge links to its dated provider observation. The company profile also links to relevant share-class, split and warrant disclosures. |
| Research review | November 17 at 18:35:45.406835 UTC through the company-specific November 23 checks at 13:19–13:28 Singapore time. No confirmed next earnings date surfaced. Historical financial statements retain their original cutoff and scopes. |
| Financial integrity | Removing only the new size and review fields reproduced the complete version 6 research dataset. Released research JSON SHA-256 `07f42383dfc5b14bc627d538427f8432cb054201c32a57c326895d879b744546`. All three historical debt/market-cap restrictions remain in force. |
| Candidate checks | 240 Python tests, including disposable TLS PostgreSQL, 94 Watch browser checks, 76 legacy preview checks, 38 workbench checks and three packaging dry runs. [PR checks](https://github.com/joedatacap/aidatacenter2/actions/runs/45119327236) · [networked desktop and mobile proof](https://github.com/joedatacap/aidatacenter2/actions/runs/45119313847) |
| Public verification | Desktop Chromium and touch-emulated mobile each displayed all nine branded monthly figures, in the badge order. Both passed peer navigation, the source drawer, APLD’s evidence excerpts, research CSV/JSON exports and the original/revised Nebius targets. The live application data and served JS, CSS and research JSON matched the accepted build. [Live browser run and original screenshots](https://github.com/joedatacap/aidatacenter2/actions/runs/45119687269) |

### Size and disclosure decisions

| Company | Nov 13 badge | Nov 20 badge · provider-reported USD | Post-cutoff primary-source review |
| --- | --- | --- | --- |
| CRWV | Large | Large · $21.97B | Checked. Seven Form 144 notices concern proposed holder sales. |
| NBIS | Size unverified | Large · $23.82B | Incomplete. An exchange notice describes future Israeli capacity. Secondary reporting names Nebius, but primary confirmation of customer identity is outstanding. The Nov 18 officer RSU grant has a future vesting schedule. |
| IREN | Medium | Medium · $5.02B | Checked. Ownership filings yielded no new issuer financing. |
| APLD | Medium | Medium · $3.47B | Updated. Applied Digital funded a $97M loan to ChronoScale. ChronoScale announced a conditional, phased Odessa project with a 65 MW first order and an H1 2027 deployment target. |
| HUT | Medium | Medium · $5.52B | Checked. No material update found. |
| WULF | Medium | Medium · $4.94B | Checked. The November 20 date was a webcast replay expiry. |
| WYFI | Small | Micro · $287.58M | Incomplete. SEC submissions and the issuer-distributed release feed were checked. The issuer's IR archive was incomplete. The November technical post referred to an earlier deployment. |
| SHAZ | Size unverified | Small · $647.59M | Checked. No material update found. The latest share count already includes exercised June prefunded warrants. |
| AGPU | Size unverified | Micro · $66.19M headline | Checked. A director’s Form 3 reported no holdings. The provider's history gives $77.90M for the same date. Both fall below $300M. The treatment of prefunded warrants remains unresolved. |

The [size evidence](../neocloud/data/quality_sizes.json) and [disclosure review](../neocloud/data/quality_reviews.json) record sources, passages and limitations. Use the disclosure timestamps to continue each company's review. Keep cited provider excerpts and figures in the editorial display, and preserve the research export projection.

### Production content security policy

The public root omitted the configured Content-Security-Policy HTTP response header on both devices. Both documents delivered `base-uri 'none'; object-src 'none'` in HTML. On the live audit page the browser rejected the controlled base URL change and reported a `base-uri` violation. Normal homepage loads recorded zero CSP violations, failed requests or page errors. The stricter HTTP policy and `frame-ancestors` require a host that supports custom response headers and can coordinate its injected scripts. The application continues to use the existing static host.

## Updating the size and disclosure evidence

The historical financial record retains its November 17 cutoff. The separately dated size observations and disclosure checks are in [quality_sizes.json](../neocloud/data/quality_sizes.json) and [quality_reviews.json](../neocloud/data/quality_reviews.json). On the website, open a badge for its quoted source and share-count basis, or a company brief for disclosure events, channels checked and gaps.

For future updates, review issuer releases and filings from the previous disclosure check through an explicit timestamp. Use filing acceptance timestamps at the cutoff boundary. Review material filings themselves, including counterparty filings where relevant. Distinguish the filing date from its underlying transaction date. The nine SEC submissions indexes for this release were retrieved once on a network with access to EDGAR. [Index check](https://github.com/joedatacap/aidatacenter2/actions/runs/45117057194)

Keep provider-reported size separate from validated ratio denominators. Check source and observation dates, genuine outstanding shares, class economics, recent issuance, splits and outstanding warrants. Disclose differences before assigning a band. Where alternative plausible figures cross a boundary, retain an unresolved band pending adequate evidence. Keep the three historical ratio guards and all prior financial records unless a separate review supports changing them.

Static Sites supports a directory setting. Its production responses omit the full policy in `_headers`. In version 7 the equivalent document policy blocked the platform’s per-response Cloudflare challenge bootstrap. It had different hashes on desktop and mobile. The partial document policy now restricts base URLs and embedded objects. The full HTTP policy remains available to compatible static servers. Verify the actual response, the blocked base-URL probe and zero resource-policy violations during normal page load. A host-supported response header and compatible handling of the platform script would be needed for full script restrictions and frame-ancestor enforcement. [Version 7 production diagnosis](https://github.com/joedatacap/aidatacenter2/actions/runs/45119031162)

## November 23, 2026 · public version 6

| Release record | Value |
| --- | --- |
| Public deployment | [Neocloud Watch](https://neocloud-watch.gpuchips.chatgpt.site/) · existing project and public audience · version **6** · deployment `appgdep_6b03b9f810c081919ac1f3fcddbf5bc4` succeeded on November 23 at 11:58 Singapore time (03:58 UTC). |
| GitHub source | [Release merge 52d196252c009c45a1a42bc07bdc2c9b4a5732d0](https://github.com/joedatacap/aidatacenter2/commit/52d196252c009c45a1a42bc07bdc2c9b4a5732d0) · [PR #14](https://github.com/joedatacap/aidatacenter2/pull/14). Its tree matches the tested integration head `f9f0c3173b04ee68869b8d4212fe63db9398a70c`. |
| Sites source | `2622b539cde6293344f253a6738164512106949c`. Saved version `appgprj_6afb8d8562c0819183402d9c41093312~appgver_6c895ed794308191aafdf33148406046`. All 30 staged files matched the clean main build. |
| Financial evidence | Cutoff `2026-11-17T18:35:45.406835Z`. The financial file is byte-identical to v5, SHA-256 `657d5141fe1a8b03e29429954a6829872a8a8c1e600de875eb29dbfb6f2b4838`. The November 17 corrections carry through intact. |
| Prepublication verification | 216 Python tests including disposable TLS PostgreSQL, 86 Watch browser checks, 76 legacy preview checks, 38 workbench checks and three packaging dry runs. The separate networked run rendered the nine real widget rows on desktop and mobile using the generated content security policy. [PR tests](https://github.com/joedatacap/aidatacenter2/actions/runs/45108710054) · [Candidate browser run](https://github.com/joedatacap/aidatacenter2/actions/runs/45108705587) |

### Public verification

Desktop Chromium (1440 × 1100) and touch-emulated mobile Chromium (390 × 844) opened the public root. Both showed the nine focus companies in badge order, TradingView’s attribution and delayed-data indicators. The desktop screenshot shows a numeric 1M figure in every row. Touch scrolling reveals 1M inside the widget and the page stays within the viewport. The served JavaScript, CSS and financial data matched the accepted build byte for byte. [Live browser run and original screenshots](https://github.com/joedatacap/aidatacenter2/actions/runs/45109112712)

On both viewports, two selected peers carried through research navigation. Source links opened in the evidence drawer, and downloaded CSV and JSON contained exactly those two companies. Markets, Financing & Debt, Earnings, Buildout and a company profile were exercised. The public Nebius Buildout card displayed the original December 2026 target and its February 2027 revision.

The staged server served the generated content-security-policy header. The public Sites root response omitted that header. Both public browsers loaded the widget without page errors or failed requests during initial rendering.

Production screenshots show the homepage at first load and after a touch swipe positions 1M beside the pinned company names. The second mobile capture used the same deployed release with a longer swipe for a clear view of the final row. [Desktop](https://drive.google.com/file/d/1xyM-izfrlgolPCZOem62xmcq-mUcCY6k/view) · [Mobile at first load](https://drive.google.com/file/d/1pulCEowFEYmsgJwZkHmO9WCjd1IuSwsa/view) · [Mobile with all nine 1M values](https://drive.google.com/file/d/1kAS2lq4BcEXC6d3IMCOGZcPTI_mGTDit/view) · [Touch verification](https://github.com/joedatacap/aidatacenter2/actions/runs/45109321834)

### Homepage data and limitations

The official TradingView Market Data widget supplies the Performance table on Overview and Markets. Use its 1M column for monthly performance. Today is a separate daily measure. TradingView supplies the actual periods, branding and delay indicators. Keep the nine focus listings in the same order as the adjacent Neocloud Watch market-cap badges. The November 13 capitalization observations support six size classifications. NBIS, SHAZ and AGPU remain **Size unverified**.

The widget has no supported column-priority setting. On a narrow screen, the homepage gives a swipe hint and the table scrolls inside its host. Market quotes stay with TradingView. Keep custom price charts, histories and stock-data exports out of the release build. Research CSV and JSON exports and the November 17 financial evidence remain available separately.

## November 22, 2026 stock-performance update

**Version 5 was public at this checkpoint.** The stock-first homepage and fifth page, Markets, are available in the GitHub build. Publication is held pending a price source with verified rights covering public display, cached history and exports. Building a local preview or merging source does not publish to Sites.

| Observation | Status |
| --- | --- |
| Public project | `appgprj_6afb8d8562c0819183402d9c41093312`, existing public audience. Version 5 deployment and source commit are recorded below. |
| Latest completed US session at the source check | November 20, 2026 at 21:00 UTC. Zero verified price histories acquired for the nine focus companies. The quote timestamp is unavailable. |
| Equity-size context | November 13 dated provider records. Six focus companies have a usable dated size band. Nebius, SharonAI and Axe Compute retain capitalization blockers. |
| Financial evidence | November 17, 2026 at 18:35:45.406835 UTC. The emitted financial file must match version 5 SHA-256 `657d5141fe1a8b03e29429954a6829872a8a8c1e600de875eb29dbfb6f2b4838` for this presentation-only release. |
| Next release gate | Obtain an entitled export, import it with the [refresh procedure](WATCH_MARKET_DATA.md), verify sample returns from the source closes and run the guarded build. Then follow the existing-site steps below. The [source audit](WATCH_MARKET_SOURCES.md) records which providers were checked. |

**Candidate source and QA.** Rebuild from [e461e0f83927a7639f78775286e436ae76bec356](https://github.com/joedatacap/aidatacenter2/commit/e461e0f83927a7639f78775286e436ae76bec356). Later receipt-only commits do not change its generated site. [PR #13](https://github.com/joedatacap/aidatacenter2/pull/13) records the merge to main. The candidate passed 216 Python checks including disposable TLS Postgres and 96 Watch browser checks across desktop and mobile. The [candidate CI run](https://github.com/joedatacap/aidatacenter2/actions/runs/44967910265) includes legacy and workbench regression tests and packaging. No Sites version was saved for this update.

**Release evidence.** The [November 22 production check](https://github.com/joedatacap/aidatacenter2/actions/runs/44967212699) exercised the existing version 5 over HTTPS. All 16 public desktop/mobile checks passed, including the served bundle and financial-file comparison, peer selection, sources, exports and original/revised Buildout dates. Local development could not reach the public origin through its proxy; the production results come from GitHub-hosted Chromium.

The candidate was checked at desktop and mobile widths. The checked-in market snapshot shows the source gap, and the guarded release build rejects it. Functional chart tests use isolated browser responses. Download the [offline candidate](https://drive.google.com/file/d/1htIEp8kkEFjnueyfFtlk1EfFlsKz3tqq/view) to try it locally. The [dated size table](https://drive.google.com/file/d/1JVOsoooZjtGq1-ZBLqhtmCRhlphr9bit/view) shows all nine focus peers. Candidate homepage screenshots show the actual price-availability state on [desktop](https://drive.google.com/file/d/1HUs64nfz1thgftskdZoSsyV8gTrFZf50/view) and [mobile](https://drive.google.com/file/d/1oUe2moXYvau5XYpsmu-1eERcNkb_hnZX/view).

## November 21, 2026 release receipt

| State | Source and evidence |
| --- | --- |
| Public site | Version **5**, public audience, [production homepage](https://neocloud-watch.gpuchips.chatgpt.site/). Sites confirmed deployment `appgdep_6b01b75857948191ae1afe54423c2867` succeeded at 15:23 UTC on November 21, 2026. |
| Previous deployment (version 4) | Deployment `appgdep_6b002589fa488191a3aee79a8f6734b4`. GitHub [5bf5d1ad8b8f6c2c1f255f247f4f0880723de902](https://github.com/joedatacap/aidatacenter2/commit/5bf5d1ad8b8f6c2c1f255f247f4f0880723de902), now in main history. Sites commit `2a21859e671f49de6a1951e1c252a3899efa56b2`. A clean rebuild matched all 29 files in that publication. |
| Canonical release on GitHub main | [PR #8](https://github.com/joedatacap/aidatacenter2/pull/8) merged at `128c07d63f2fce67ce654815a17fb4f8fea6ad9d`. PR #9 was retargeted to main. Both review findings were fixed and resolved. [PR #9](https://github.com/joedatacap/aidatacenter2/pull/9) merged at [ff7417ca8851c6488e40514d0a62460c2ae734d8](https://github.com/joedatacap/aidatacenter2/commit/ff7417ca8851c6488e40514d0a62460c2ae734d8). Its Git tree equals the tested PR head `727db69db02b85ec00b8e95397a7fd521c6746fd`. |
| Published release | Version **5**, Sites commit `2dc216a95a6e4264cc0ae14deb26a287f5edaee6`. Version ID `appgprj_6afb8d8562c0819183402d9c41093312~appgver_65279b0cf1d88191ae8128f565a01e25`. Before deployment, a clean output directory built from GitHub main `4f45fecbf0248cfbb29356ad98474bbe040890e4` matched all 29 files at this Sites commit byte for byte. The only GitHub change since the release merge was the runbook. |
| Data | Cutoff `2026-11-17T18:35:45.406835Z`. In both versions and canonical main, the exact file SHA-256 of `dist/data.json` is `657d5141fe1a8b03e29429954a6829872a8a8c1e600de875eb29dbfb6f2b4838`. The Axe and SharonAI Q3 corrections, fiscal dates, historical scopes and recorded market dates are preserved. |
| Version 4 to 5 | The only changed static asset was `watch.js`. Version 5 shows the recorded original and revised milestone windows on the Buildout page and company profiles. All homepage rendering code, route HTML, styles and financial inputs are identical. The other code fix creates the offline output directory on a first custom build. |
| Local build and CI | 179 Python tests, including disposable TLS Postgres, and 74 Watch desktop/mobile browser checks passed locally. [Final PR CI](https://github.com/joedatacap/aidatacenter2/actions/runs/44859523211) also passed 76 legacy and 38 workbench browser checks and all three packaging dry runs. These browser checks exercise built files on a local server and offline. |

**Version 5 production verification.** All 16 public checks passed in desktop Chromium and an emulated mobile Chromium viewport with touch. Both fetched `watch.js` and `data.json` from the public origin and compared their bytes to the main build. The renderer SHA-256 was `9df69412b05280272923046f62cf34d2a7f37b95cbefcf3a09ce68fffa790ace`; the financial file matched the November 17 checksum above. Peer selection, source drawers and CSV/JSON exports also passed. [GitHub Actions run 44919088688](https://github.com/joedatacap/aidatacenter2/actions/runs/44919088688)

The tests read each of these records on the live Buildout Projects page and the corresponding company profile:

| Company and milestone | Original target | Reviewed revision |
| --- | --- | --- |
| IREN, $4B ARR target | By December 31, 2026 | January 2027, potentially extending through February 2027 |
| Hut 8, initial River Bend data hall | Q2 2027 | No reviewed revision |
| Nebius, ARR target | December 2026 | February 2027 |

All three disclosed outcomes displayed “Not established.” These dates describe management targets.

**Historical version 4 production checks.** [Public smoke run 44860376208](https://github.com/joedatacap/aidatacenter2/actions/runs/44860376208) passed ten production checks using desktop Chromium and an emulated mobile Chromium viewport with touch. Both browsers reached the public URL, used the peer checkbox and search, followed a company link and opened source drawers to inspect their links, checked AGPU's buildout stage, exercised chart details, and downloaded and inspected CSV and JSON. The public renderer bytes matched v4 SHA-256 `4a71781cf49a93d45a84e17fe49fe201a4e8edd599cd382dd8bc07497f985279`. Public and main data had the same key-sorted JSON digest `13e3182bc5e5c67dd09765c7bbcd251cbf02670c9c4a3be7df2b54a7f70804bf`. Separately, the linked Axe and SharonAI Q3 SEC filings each returned HTTP 200 with HTML. The workspace proxy itself denied the public site with HTTP CONNECT 403. Production browser results come from GitHub-hosted runners.

The owner explicitly authorized publication of the existing saved version 5. Sites returned `succeeded` and the public HTTPS URL. A separate status read linked that deployment to the saved version, and the site access setting remained `public`.

## Update and publish

1. Read this release receipt, then fetch GitHub `origin/main`. Inspect open PRs and create a working branch from the current main. On Sites call `get_site` and `list_site_versions` for project `appgprj_6afb8d8562c0819183402d9c41093312`. Confirm the public URL and audience. Use `get_deployment_status` to identify the successful public version. Record its version, deployment ID and source SHA before making edits.
2. Open the **existing** Sites source repository using `create_source_repository_write_credential` for that project and the Sites source helper. Use the returned branch and short-lived credentials in memory. Read `.openai/hosting.json` and `maintenance/GITHUB_SOURCE.md`. Compare the remote HEAD and the current public commit, then compare published `dist/` with a fresh build of the GitHub commit it records. Reconcile any intervening edits before writing. The v3 `maintenance/source-corrections.patch` is historical and is already incorporated.
3. Edit canonical GitHub source. Homepage and views live in `watch-preview/`; inputs and validator live in `neocloud/data/` and `neocloud/watch.py`. For a financial update, review the dated primary evidence, scopes and reporting periods before editing observations. Refresh the coverage matrix with `python scripts/build_watch_coverage.py` if the research changed. See [data audit](NEOCLOUD_WATCH_AUDIT.md) and [source reconciliation](NEOCLOUD_WATCH_SOURCE_RECONCILIATION.md).
4. Install dependencies and run the release checks from the GitHub checkout:

   ```sh
   python -m pip install -e '.[test]'
   npm ci
   npx playwright install --with-deps chromium
   python -m pytest -q
   npm run test:watch
   npm run deploy:watch:dry-run
   ```

   Use a disposable TLS PostgreSQL database for the database integration tests. The GitHub Tests workflow provisions one and runs the existing preview and workbench suites too. Review CI and review threads before merging. Test the company links, sources, both exports, peer selection, charts and quarter dates. The hosted and offline suites run on desktop and mobile against a local build.
5. Fetch the accepted source commit, record its full SHA, and build from that exact revision into a new, empty directory. Use the root base for this public URL:

   ```sh
   stage_dir=$(mktemp -d)
   python scripts/build_neocloud_watch.py --release --base-path / --output "$stage_dir/dist"
   ```

   Inspect the staged file list and differences, including `data.json`, `audit.html`, `_headers`, assets and all route indexes. Version 5 has 29 files in `dist/`, including 24 route indexes. The TradingView edition has 30 files including 25 route indexes. It includes `markets/index.html` and excludes `market-data.json`. A failed release build stops publication, including reuse of any older staging directory. For a presentation or packaging change, compare `data.json` byte for byte with the previous publication. When generated files already match, retain the existing deployment.
6. For an authorized publication, update only the existing Sites checkout's `dist/` to match the staged tree. Record the full GitHub SHA in `maintenance/GITHUB_SOURCE.md`. Preserve the hosting manifest and all maintenance history. Verify with `diff -qr "$stage_dir/dist" "$site_checkout/dist"`, setting `site_checkout` to the path opened in step 2. Recheck the remote head and current version before pushing to prevent overwriting another publisher.
7. Follow the Sites source helper to commit, push and package. For a static Git checkout the equivalent archive command is `git archive --format=tar --output=/absolute/path/to/release.tar HEAD .openai/hosting.json dist` from the verified Sites checkout. The archive contains the manifest and generated output. Call `save_site_version` with the same project ID, **pushed Sites commit SHA** and unchanged archive, then `deploy_site_version` with the returned saved-version ID. Keep the existing public audience. If the call is pending, poll `get_deployment_status` until terminal. Verify `get_site` still returns the expected URL, version and access.
8. Run the **Watch native browser proof** workflow in candidate mode before publication and live mode after publication. Dispatch it against the accepted source, or push that exact source to a fresh `qa/watch-native-candidate-<release>` ref for the candidate and a fresh `qa/watch-native-live-<release>` ref for the public check. The candidate server enforces the generated headers. The live target is fixed to the public Sites origin. Download the workflow artifact and inspect the branded desktop and mobile screenshots for actual monthly figures across all nine companies, provider attribution, the Today and 1M labels, and mobile scrolling. Component registration alone is insufficient. Keep quote data out of tests and exports. Check peer selection, company profiles, source links, research CSV and JSON, and compare the served JavaScript, CSS and financial data to the accepted build. Record the build SHA, Sites SHA, version, deployment ID, data cutoff and links to the checks in this file.

### Reproduce the version 5 production browser check

The [release QA revision](https://github.com/joedatacap/aidatacenter2/commit/cc5c10ad408dccefd88841e3e2e561d61794ee2f) contains the public Playwright checks for version 5. The checks compare the deployed JavaScript and reviewed data to the build produced in that checkout. Use a separate checkout. Install the Python test dependencies as in step 4, then run:

```sh
git fetch origin qa/neocloud-watch-live
git worktree add --detach ../watch-public-qa cc5c10ad408dccefd88841e3e2e561d61794ee2f
cd ../watch-public-qa
python -m pip install -e '.[test]'
npm ci
npx playwright install --with-deps chromium
npm run build:watch
env -u WATCH_SMOKE_LOCAL_CONTROL npx playwright test --config playwright.watch.config.cjs public-live.spec.cjs
```

With that variable unset, the test navigations and downloads use the public Sites origin. The test runner also starts a local server for its build control. A run with `WATCH_SMOKE_LOCAL_CONTROL=1` checks local behavior only. When publishing a newer version, use a QA worktree based on its accepted GitHub release commit, carry over the smoke spec, and compare the public assets with the generated release files. Keep the public target and checks of real interactions intact.
