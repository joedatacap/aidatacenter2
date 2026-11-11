# Actual borrowing comparison: methodology and evidence

Reviewed November 11, 2026. This is a curated snapshot, not a live market-data or
credit-rating service. The default screen covers the AI-infrastructure subset;
other peer-group filters add context without calling every company a neocloud.

## What the user can compare

1. **Reported borrowings, excluding leases.** USD consolidated carrying amounts of
   loans and notes, net of disclosed discounts and issue costs. This measures
   borrowing size, not all liabilities, face principal, available credit or
   repayment ability. Both operating and finance lease liabilities are excluded;
   those are real economic obligations, especially for lease-heavy operators.
2. **Borrowings / total assets.** Same-date borrowings divided by consolidated
   recorded assets, expressed as dollars of borrowing per $100 of assets. It
   does not identify which assets were funded by debt. Construction assets,
   crypto holdings, fair values and lease right-of-use assets make business-model
   comparisons imperfect. This is not debt/equity, debt/EBITDA or a health score.
3. **Bond coupon examples.** A sortable, unnumbered reference to 44 identified USD
   fixed-rate instruments across 15 companies where independently reviewed. The selection
   is a documented example, not a claim to the lowest, latest or average funding
   cost. Convertibles/exchangeables have equity-option economics; project notes
   and unsecured corporate notes have different security and recourse. Coupon
   differs from current market yield. Continued outstanding status is not
   reverified for every historical example. Filters separate convertibles, secured
   and unsecured notes, and notes confirmed at the company snapshot from older
   observations or terms-only records.

There are two company rankings and one instrument reference, rather than three
misleading company-health rankings. No market-cap denominator or current bond
quotes are invented. Numerical ordering describes only the selected accounting
metric within the chosen filter, not creditworthiness.

## Coverage and dates

| Business group | Companies | Balance-sheet dates |
|---|---|---|
| GPU cloud | CRWV, NBIS, Nscale (private IPO applicant) | September 30; NBIS and Nscale June 30 |
| AI infrastructure / mixed transition | IREN, BTDR, HUT, APLD, CORZ, WULF, CIFR, HIVE, GLXY | September 30; APLD August 31 |
| Bitcoin mining / adjacent | RIOT, MARA | September 30 |
| Data-center REITs | EQIX, DLR | September 30 |

All dates are in 2026. These are not exhaustive sector classifications or a claim
that AI is each company's principal business. Private operators without comparable
public financial statements are not filled with estimates just to increase breadth.

Fifteen companies have reconciled borrowing totals and same-date asset ratios.
Galaxy's dollar loans and notes are an incomplete subset of its financing
obligations; digital-asset borrowing/collateral liabilities need further work.
Its borrowing total and asset ratio therefore stay null and unranked. Its cash,
assets and one named project-note coupon remain separately sourced.

## Important scope cases

- CoreWeave's latest reviewed quarter-end release is November 10. Recourse and
  nonrecourse current/noncurrent borrowing rows sum to the numerator; leases stay
  separate. Nonrecourse does not mean a blanket claim on the parent.
- Nebius retains June 30 debt/assets. The subsequent August convertible issue is
  a separate coupon observation, not a pro-forma update to the earlier balance
  sheet. Its next reported results were scheduled November 12 at the review cutoff.
- Hut 8 uses $7.628225B borrowing carrying amount, excluding a $3.275M SAFE from
  a combined balance-sheet liability caption and separately classified miner
  purchase obligations. Restricted project cash is not unrestricted parent cash.
- Cipher's full borrowing reconciliation includes vehicle loans omitted from a
  smaller fair-value table. The full debt note and current/noncurrent rows agree.
- MARA's later $750M loan repayment is noted without changing September 30 assets
  or borrowings. Crypto assets and receivables are not counted as cash.
- Equinix source tables are rounded to USD millions. Dollar conversion does not
  create additional precision. Digital Realty's own net-debt/EBITDA measure uses
  JV and lease adjustments and is not substituted for this common asset ratio.
- Galaxy's cash is the balance-sheet cash/equivalents line, not its broader
  cash/stablecoin/Treasury liquidity headline. Qualifying short-term Treasuries
  may already be within cash equivalents; separately classified investments stay
  outside that line.

## Private operators and principal context

Nscale Limited has public SEC registration financials but no verified listed
trading ticker at the review cutoff. Its June 30 actual USD figures are used,
not IPO pro forma figures. The $137.4M borrowing numerator excludes $6.4926B
customer deferred revenue (including a significant financing component) and
$2.6254B operating leases. Its roughly 0.80% borrowings/assets ratio is therefore
especially unsuitable as a health ranking. Loan effective rates are not bond
coupons. The $136.9M contractual maturity table is not silently reconciled to
$137.4M carrying value; whole-company principal stays unknown.

Crusoe, Lambda and Vultr have a separate, unranked coverage watchlist with
first-party financing announcements. Facility capacity, transaction proceeds and
drawn debt are different quantities. No announced amount becomes a comparable
company borrowing balance without a dated consolidated statement.

Each company can show principal-to-carrying-value reconciliation and excluded
leases. Nine full-scope principal bridges are supported; partial note subsets and
unreconciled principal totals are labeled explicitly. Nebius's reported contract
principal includes accreted redemption amounts: it is not original proceeds or
cash owed today. Different dates, business models and project issuers remain
visible in side-by-side comparisons. Selecting a company does not imply its
pinned coupon example is representative of its overall financing cost.

## Evidence and calculation boundary

`neocloud/data/debt_directory.json` is the curated source of truth. It contains
dated amounts, component reconciliations, explicit definitions, short exact
source passages and primary URLs. No credentials or live research-run snapshots
are exported. Source publication dates are separate from bond issue dates and
financial statement dates.

`neocloud/directory.py` validates sources, rejects synthetic inputs, checks
component sums and same-date/consolidated/currency scope, and computes ratios
with Decimal. `scripts/build_debt_preview.py` produces `preview/data.json`.
JavaScript sorts and formats these exported values; it does not implement a
second financial model. Missing values never become zero. A genuine zero coupon
remains 0%, rather than being treated as unavailable.

The older synthetic scenario engine and fixtures are preserved separately at
`preview/scenarios/`; they cannot enter the source-backed directory.

## Delivery and operational limits

The static preview needs no API, database or inference key. HTML, CSS, JS and
curated read-only data can be hosted using the prepared Cloudflare Free Static
Assets configs, including a tested `/neoclouddebt/` prefix. No public deployment,
merge, paid feature or research-runtime migration is part of this change.

The standalone HTML embeds the whole directory and works without a server or
network. Source links need internet access when opened. Tests verify rankings,
unknown handling, grouping, coupon separation, exports, URL restoration,
keyboard interaction, source details, mobile layout and offline operation.

## Independent source review receipts

[Company balance review](DIRECTORY_SOURCE_AUDIT.json) records independent fresh
primary retrievals for all 15 baseline company snapshots, tied to baseline commit
079fd8e, plus Nscale's additional filing review. It does not assert that every
source in the expanded ledger received that initial audit.

[Note and bridge review](DIRECTORY_NOTE_AUDIT.json) records screening of all 44
note rows, 44 freshly retrieved primary HTML documents, nine full-scope bridges
and partial-scope context. This is an engineering source check, not a statutory
financial audit or exhaustive legal review. A precise Nebius 2032 maturity date
needed an additional original indenture link; that provenance correction is
recorded. Historical receipts retain their reviewed hashes rather than pretending
to certify subsequent editorial changes.


[Remaining-source coverage review](DIRECTORY_REMAINING_SOURCE_REVIEW.json) maps
the pre-correction 80 source IDs to 54 unique URLs: 47 have retained raw retrieval
receipts and six have web-text review. One presentation PDF could not be freshly
retrieved. SEC follow-up did not substantiate its optional Digital Realty
finance-lease amount, so that amount was changed to unknown and the unsupported
PDF record removed. After that correction, the ledger had 79 source records across 53 unique
URLs. The historical coverage map preserves the original reviewed hash and
records the correction separately. This does not change the SEC-supported
borrowing subtotal or imply the company has no finance leases.

[Private watchlist review](DIRECTORY_WATCHLIST_REVIEW.json) freshly checks all four
linked announcements via web-text retrieval. Those receipts do not claim raw
HTML hashes: direct HTTPS was blocked. Announced facility size and contractual
rates remain separate from current debt balances, market yields and company
credit ratings.


## Cash, commitments and credit access

Each company now has a separate, dated Cash & funding section, accessible from
company evidence or a comparison. Reported cash is cash held by the company and
its subsidiaries together; it is not a verified parent-only spending balance.
Restricted cash and investments stay separate. No cash-to-debt health ranking or
combined cash-plus-credit figure is introduced.

The section includes 21 selected facilities with source-backed amounts and access
conditions. A committed limit, a drawn loan, unused capacity and an amount the
issuer explicitly calls available are different facts. Some commitments also
support letters of credit, require collateral, depend on project completion or
permit only specific equipment purchases. Even an explicitly available amount is
not cash already in the bank. Company-wide available credit remains unknown
because the selected disclosures do not establish a complete inventory.

Important cases include IREN's conditional unfunded commitments, Hut 8's undrawn
revolver with unquantified actual availability, TeraWulf's remaining LC-only
headroom and precommencement cap, and Equinix's approximately $5.5B reported
facility availability. Nscale's reported unused GPU/revolver capacity remains
conditional and separate from cash. MARA's cash includes designated Exaion funds;
Galaxy's group cash includes funds at financial counterparties. Later amendments,
repayments and HIVE's subsequent supplier-escrow financing are excluded from the
older snapshots. No unused amount is calculated by subtracting a debt carrying
value from a commitment.

[Liquidity integration review](DIRECTORY_LIQUIDITY_REVIEW.json) records source
coverage and limitations. This pass adds 16 source records for specific liquidity
facts; the ledger now has 95 records across the same 53 unique URLs. The earlier
URL coverage map remains historical evidence, not a claim that every later
interpretation has an exhaustive independent legal review.


Source boxes display selected verified passages or labeled table cells, with
explicit context when comparison columns or intervening cells are omitted. They
are short reading aids alongside links to the complete documents. The latest
IREN recheck succeeded with a fresh HTTP200 response, while the earlier reviewer's
access limitation is retained in the liquidity receipt. This copy/source-reading
pass changes no financial amounts, dates, scopes or instrument source links.
