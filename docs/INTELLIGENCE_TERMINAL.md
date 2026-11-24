# Neocloud Intelligence Terminal prototype

Open the standalone `Neocloud-Intelligence-Terminal.html` from the **Intelligence Terminal preview** artifact on the pull request. Download the artifact, unzip it, and open the HTML in a browser. All four views, filters, source passages and dated history work offline. Following a source or a link to Watch needs internet access. The PR workflow also captures the desktop and mobile views. [Implementation brief](https://github.com/joedatacap/aidatacenter2/issues/20)

## What this branch builds

- **Comparison** shows the three business roles and the selected observations for each issuer. Period, unit, scope and definition travel with each fact. Do not sum a property operator’s contracted IT load and a GPU operator’s deployed capacity. A common tenant or counterparty can appear on both sides.
- **Company briefs** connect the financial and operational evidence to questions about funding, customer acceptance and delivery. Each fact opens its attributed source record. The original Watch remains available for its broader nine-company research and trading context.
- **Commitments and history** preserves original targets and dated revisions separately from outcomes. Use **Knowledge as of** to hide later disclosures. A company reporting that equipment is provisioned establishes only that reported stage.
- **Material changes** pairs earlier and later evidence with an analyst interpretation. Filter by company, type, publication window or knowledge date. Comparison and company briefs show the latest reviewed snapshot. Historical reconstruction covers the curated timelines and changes.

### Which repository serves the site?

`joedatacap/aidatacenter2` contains the canonical application and reviewed Watch ledgers. The live [Neocloud Watch](https://neocloud-watch.gpuchips.chatgpt.site/) serves a generated static build from a separate ChatGPT Sites source repository. Its authenticated project record reports public version 11. Its source pointer names GitHub application commit `c44d19d76cfd1287885bf7c4718c1ffdc0bf8999` and Sites commit `88c199d644aae5df5d9059e24e4b5467a8d665bb`. The prototype branch started from `1d972ad69fde07fa70c2c9cf3752a197409bc68e`. On November 24 a networked runner fetched production `watch.js`, `watch.css` and `data.json`. All three SHA-256 digests matched the mounted release source; the JSON digest was `1547050e7c1f45cd45727e825f3d714ca47bab64350344de4940da54e0f19bf5`. A GitHub PR builds a preview. Changing production requires a separate Sites publication. [Live asset and SEC evidence](https://github.com/joedatacap/aidatacenter2/actions/runs/45380883983) · [Release runbook](NEOCLOUD_WATCH_RELEASE.md)

The existing PostgreSQL schema stores research runs, companies keyed by ticker, evidence, deals and instruments. Its V2 migration projects financing records from research runs. The public Watch reads a static research snapshot. This prototype uses three reviewed, versioned files and a deterministic standalone build, with no database writes or schema migrations. [Database schema](../neocloud/schema.sql) · [Reviewed terminal records](../neocloud/data/terminal)

## Coverage and outstanding evidence

| Issuer | Research covered | Open diligence |
| --- | --- | --- |
| CoreWeave (CRWV) | Cloud operator. September quarter; unrestricted and restricted cash; carrying and principal debt; active versus contracted power; concentration, RPO, management backlog and guidance revisions. November 23 USD equity observation supports the Large display band. | Source does not establish the latest share denominator independently. Future customer prepayments, site handovers and year-end targets need later evidence. |
| Applied Digital (APLD) | Data-center developer and landlord. August-quarter revenue, cash, debt and customers; Polaris Forge 1 in-service evidence; project-specific delayed-draw bridge; signed 150 MW lease and conditional first delivery. November 23 provider cap of $4.18B supports Mid. | Exact provider share count, draw amount, unnamed lessee and site of the new lease remain open. Contracted revenue is a base-term estimate and the operating phase needs a dated handover. |
| Axe Compute (AGPU) | Compute-services operator. September quarter and SPV acquisition; cash, deferred purchase financing and leases; Georgia GPU ownership, energization, provisioning and acceptance stages. | Size remains unverified. Prefunded warrants, share counts and subsequent transactions require reconciliation. Customer acceptance, billable commencement and average operating IT load remain unverified. |

The scope is curated, not an issuer-wide inventory of every contract or financing. Thresholds for this prototype are Small below $2B, Mid from $2B to below $10B, and Large at $10B or above. Provider caps have date-only precision. “Size unverified” can accompany a separately attributed headline. Capture source-dependent measures independently: signed commercial value, RPO, recognized revenue, project finance commitments and drawn cash have different accounting and contractual definitions. The inputs do not establish comparable same-period average operating capacity for revenue per MW.

### Data Center Crosscheck identifiers

Inspected the Crosscheck publication ledger read-only at `joedatacap/aidatacenters1`, revision `38dfdcb5424ae2e77920a3a991948921b1696c29`. Its `companies`, `sites`, `contracts`, `sources` and `capacity` are separate collections. Use this crosswalk for reviewed lookup and preserve the namespace if imported later. [Pinned Crosscheck publication ledger](https://github.com/joedatacap/aidatacenters1/blob/38dfdcb5424ae2e77920a3a991948921b1696c29/public-release/production/dist/combined-data.json)

| Watch / terminal company | SEC CIK | Crosscheck company ID | Site mapping boundary |
| --- | --- | --- | --- |
| `crwv` | 1769628 | `coreweave` | Crosscheck has named campus IDs. Keep the anonymized utility-delivery disclosure at company scope until a primary source names the site. |
| `apld` | 1144879 | `applied-digital` | Polaris Forge 1, Ellendale → `applied-digital-polaris-forge-1-ellendale-nd`. Delta Forge 1, Louisiana → `applied-digital-delta-forge-1-la`. The new 150 MW lease has no verified site ID. |
| `agpu` | 1446159 | `axe-compute` | Columbus, Georgia → `duos-axe-columbus-ga`. Keep the separate undisclosed-site ID `agpu-us-site` distinct. |

For sources, coalesce by exact SEC accession and document (including exhibit) or the same issuer release URL. For example, Crosscheck’s `pass2-apld-10q-20261007` references accession `0001144879-26-000059`. Preserve the original source IDs, scope, phase, operator and ownership roles on either side. A shared URL or ticker alone cannot justify combining MW or dollars.

## Update and verify

1. Review the issuer’s latest SEC submissions, exhibits and IR releases since its last actual review timestamp. The on-demand command below stages SEC identity, filings accepted from the supplied UTC date, and exact-accession US-GAAP cash and quarterly revenue observations. Use a public research contact. Inspect the candidate JSON even on failure; a failed or empty result requires follow-up.

   ```sh
   mkdir -p work
   python scripts/stage_terminal_sec.py --since 2026-11-23 --contact research@example.org > work/terminal-sec-candidates.json
   ```

2. Reconcile the filed rows against the financial statements and notes. The November 24 SEC pass found CRWV quarterly revenue of $3.661B and cash of $4.122B. For APLD the revenue tags covered $262.755M of services/other revenue and $341.875M total revenue for the same quarter. AGPU had a matching $147,710,376 cash tag and no matching revenue tag in the bounded screening list; its reviewed revenue comes from the filing. The accession, period start, end and units in the candidate are preserved. Do not sum the tags or substitute a missing tag with zero.
3. Copy the three reviewed JSON files to a staging directory. Add issuer passages, filing section or table locators, publication dates, observation dates, units and full scope. Preserve original targets and append revisions. Add a before/after record when new evidence changes a commitment. Keep interpretations under `why`. Calculated values require an explicit formula and references to input fact IDs. Check the arithmetic against the source. Keep earlier financial observations and their source records rather than moving their dates forward.
4. Run `python scripts/build_terminal.py --input-dir work/terminal-candidates --check`. Review the diff against the canonical inputs, then promote only approved facts to `neocloud/data/terminal/` on a review branch. Neither the SEC command nor the existing document-fingerprinting dry run promotes a candidate. There is no scheduled extraction or publication.
5. Build and test the review artifact:

   ```sh
   python -m pytest -q tests/test_terminal.py
   python scripts/build_terminal.py --output work/terminal-preview/Neocloud-Intelligence-Terminal.html
   npm ci
   node tests/terminal-browser.cjs work/terminal-preview
   ```

   The browser check uses local Chrome or `PLAYWRIGHT_CHROMIUM_EXECUTABLE`. It opens the generated file offline. In managed environments that restrict file navigation, serve that same directory on loopback and set `TERMINAL_PREVIEW_TEST_URL` to the served HTML URL. The PR workflow tests the downloadable file directly.

**Recommended next iteration.** Close one measurable evidence gap: backfill primary dated acceptance and first-billing disclosures for the Georgia cluster, when available. Cross-reference the exact physical phase and ownership, keeping technical power-on, customer acceptance, service entry and first recognized revenue as separate events. That gives the team a concrete delivery test before expanding coverage.

## Trading workflow prototype (follow-up to PR #21)

The default **Trading desk** shows the six most recent curated disclosure changes, with prior disclosure, new evidence, interpretation and a source drawer. It is ordered by publication date, not a buy/sell score. A saved review-through date flags subsequently published changes for that company; this is a date comparison, not automated thesis interpretation.

**Catalysts** reuses unresolved milestones and retains partially completed projects. Exact events and broad management target windows are labeled separately. Sorting uses the existing explicit target-end field; no dates are inferred from prose. Passed windows request a fresh outcome check rather than declaring a delay. All reviewed records remain a static snapshot, with a visible review date and no live prices or consensus.

**My theses** stores thesis, expectation/horizon, invalidation condition, next evidence and a user-selected disclosure review-through date. Notes save to localStorage on this browser/origin only and are not team-synced. Export creates a personal JSON backup. Corrupt or blocked storage produces an error without claiming a successful save. Moving the standalone file or changing the origin may change storage availability. Notes never enter the public company ledger, URL or repository. Team storage and authenticated synchronization remain future work.

Run the existing terminal Python tests and `node tests/terminal-browser.cjs work/terminal-preview` after building. The browser suite covers all original research views plus desk filtering, pending/partial catalysts, saved notes after refresh, text escaping, export and corrupt-storage protection at desktop/mobile sizes.
