"""Presentation of reviewed underwriting outputs; this module never recalculates cases."""
from html import escape
from math import isfinite
import re
from urllib.parse import urlsplit


CSS = """
.uw-opening{margin:18px 0 24px}
.uw-opening h1{font:500 clamp(1.9rem,4vw,3rem)/1.1 Georgia,serif;letter-spacing:-.03em;margin:12px 0}
.uw-stamp{font-size:.85rem;color:var(--muted);margin:8px 0}
.uw-decision{background:#e1eee7;border:1px solid #b8d0c1;padding:20px;border-radius:5px}
.uw-decision p{margin:8px 0}
.uw-price-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-top:0;background:white}
.uw-price-strip>div{padding:15px;border-right:1px solid var(--line)}
.uw-price-strip>div:last-child{border-right:0}
.uw-price-strip small{display:block;font-size:.8rem;color:var(--muted)}
.uw-price-strip strong{display:block;font:500 1.65rem/1.3 Georgia,serif;font-variant-numeric:tabular-nums}
.uw-tests{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:18px}
.uw-tests>section,.uw-card{min-width:0;padding:17px;background:white;border:1px solid var(--line);border-radius:4px}
.uw-tests h3{font-size:.85rem;color:var(--green);margin:0 0 9px}
.uw-tests p{margin:0;font-size:.94rem}
.uw-nav{display:flex;flex-wrap:wrap;gap:7px;margin:20px 0}
.uw-nav a{padding:7px 10px;border:1px solid var(--line);background:white;border-radius:3px;font-size:.85rem;text-decoration:none}
.uw-section{margin:30px 0;scroll-margin-top:20px}
.uw-section>h3{font:500 1.7rem/1.2 Georgia,serif}
.uw-note{font-size:.9rem;color:var(--muted)}
.uw-unavailable{color:var(--muted)}
.uw-table{font-size:.9rem}
.uw-table th{white-space:normal;font-size:.8rem}
.uw-table td{overflow-wrap:anywhere;min-width:115px}
.uw-table .uw-key{font-weight:650;min-width:180px}
.uw-bridge{min-width:650px}
.uw-evidence{font-size:.85rem;margin:9px 0}
.uw-evidence a{overflow-wrap:anywhere}
.uw-source{padding:14px 0}
.uw-source summary{font-size:.95rem}
.uw-source blockquote{margin:15px 0;padding:14px 17px;border-left:3px solid #87a48e;background:#edf2e9;white-space:pre-wrap;overflow-wrap:anywhere}
.uw-source p{overflow-wrap:anywhere}
.uw-formula{background:#ecf0e8;padding:12px 15px;font-size:.9rem;border-left:3px solid #7d9e82}
.uw-cases{min-width:1000px}
.uw-case-note{display:block;color:var(--muted);font-size:.8rem}
.uw-case-base{background:#edf4eb}
.uw-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.uw-facts>div{background:white;border:1px solid var(--line);padding:16px;min-width:0}
.uw-facts small{display:block;color:var(--muted)}
.uw-facts strong{font:500 1.6rem/1.3 Georgia,serif;display:block;margin:4px 0}
.uw-sensitivity{min-width:540px}
.uw-sensitivity td{text-align:right;font-variant-numeric:tabular-nums}
.uw-sensitivity small{display:block;color:var(--muted)}
.uw-audit{min-width:1050px}
.uw-audit td{min-width:130px}
.uw-audit .uw-claim{min-width:210px}
.uw-priorities{padding-left:24px}
.uw-priorities li{padding:10px 0}
.uw-priorities p{margin:5px 0;color:var(--muted)}
.uw-comparison{min-width:850px}
.uw-raw{font-size:.88rem;overflow-wrap:anywhere}
.uw-raw dl{padding:12px;background:white;border:1px solid var(--line)}
.uw-raw dt{font-weight:600}
.uw-raw dd{margin:3px 0 13px;overflow-wrap:anywhere}
.uw-historical{margin-top:38px;padding-top:20px;border-top:2px solid #82958c}
.uw-historical>summary{font-size:1.1rem}
.uw-scenario-block{margin:18px 0}
.uw-provenance{font-size:.82rem;color:var(--muted)}
.uw-overview-tests{grid-template-columns:repeat(2,minmax(0,1fr))}
.uw-mobile-decision{display:none}
.uw-overview-tests p+p{margin-top:12px}
.uw-audit details{border:0;padding:0}
.uw-audit details p{font-size:.88rem}
.uw-audit summary{font-size:.85rem}
@media(max-width:700px){.uw-price-strip{grid-template-columns:1fr 1fr}
.uw-price-strip>div:nth-child(-n+2){border-bottom:1px solid var(--line)}
.uw-price-strip>div:nth-child(2){border-right:0}
.uw-tests{grid-template-columns:1fr;gap:10px}
.uw-facts{grid-template-columns:1fr}
.uw-opening h1{font-size:2rem}
.pane-underwriting{display:flex;flex-direction:column;padding-top:8px}
.pane-underwriting>*{order:3;min-width:0}
.pane-underwriting>.eyebrow{order:0;font-size:.68rem;margin:5px 0}
.pane-underwriting>h2{order:0;font-size:1.5rem;margin:5px 0}
.pane-underwriting>.uw-opening{order:1;margin:4px 0 12px}
.pane-underwriting>.tabbar{order:2;margin:12px 0}
.uw-desktop-decision{display:none}
.uw-mobile-decision{display:block;background:white;border:1px solid var(--line);border-radius:4px;padding:13px}
.uw-mobile-rating{display:block;font-size:1.06rem;line-height:1.3;color:var(--green);margin-bottom:8px}
.uw-mobile-metrics{display:grid;grid-template-columns:1fr 1fr;gap:9px 12px;padding-bottom:9px}
.uw-mobile-metrics small{display:block;color:var(--muted);font-size:.73rem}
.uw-mobile-metrics strong{display:block;font-size:1.16rem;font-variant-numeric:tabular-nums}
.uw-mobile-metrics strong span{font-size:.82rem}
.uw-mobile-answers>section{padding:5px 0;border-top:1px solid var(--line)}
.uw-mobile-answers h3{font-size:.81rem;margin:0 0 3px;color:var(--green)}
.uw-mobile-answers p{font-size:.875rem;line-height:1.4;margin:0}
.uw-mobile-decision>details{padding:9px 0 0;font-size:.9rem}
.uw-mobile-decision>details>summary{font-size:.81rem}
.uw-stamp{font-size:.74rem;margin:5px 0 8px}
.uw-decision{padding:16px}
.uw-table td,.uw-table th{padding:9px}
.uw-price-strip strong{font-size:1.45rem}
}
@media(max-width:700px) and (max-height:720px){
.pane-underwriting>.eyebrow{order:2}
.pane-underwriting>.uw-opening{display:flex;flex-direction:column}
.uw-opening>.uw-stamp{order:1}
.uw-mobile-answers h3,.uw-mobile-answers p{display:inline}
.uw-mobile-answers h3::after{content:" · "}
.uw-mobile-answers>section{line-height:1.3}
.top:has(+main .pane-underwriting){padding-block:9px}
}
@media print{.uw-nav{display:none}
.uw-source blockquote{break-inside:avoid}
.uw-tests{grid-template-columns:1fr}
.uw-section{break-inside:auto}
}
"""


def esc(value):
    return escape(str(value), quote=True)


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def unavailable():
    return '<span class="uw-unavailable">Unavailable</span>'


def shown(value):
    return unavailable() if value is None or value == "" else esc(value)


def dollars(value):
    return "$" + f"{value:,.2f}" if numeric(value) else unavailable()


def amount(value):
    """Model monetary amounts are USD millions; no unit conversion is inferred."""
    if not numeric(value):
        return unavailable()
    return ("−$" if value < 0 else "$") + f"{abs(value):,.3f}M"


def shares(value):
    return f"{value:,.6f}M" if numeric(value) else unavailable()


def percent(value):
    return f"{value:+,.1f}%" if numeric(value) else unavailable()


def multiple(value):
    return f"{value:,.2f}×" if numeric(value) else unavailable()


def label(key):
    return str(key).replace("_", " ").replace(" pct", " (%)").replace(" usd", " USD")


def url(value):
    try:
        parsed = urlsplit(str(value))
        return str(value) if parsed.scheme == "https" and parsed.netloc and not parsed.username else None
    except ValueError:
        return None


def copy(value):
    if value is None:
        return unavailable()
    if isinstance(value, dict):
        for key in ("text", "claim", "summary", "description", "note"):
            if key in value:
                return esc(value[key])
        return raw(value)
    if isinstance(value, list):
        return "<ul>" + "".join("<li>" + copy(item) + "</li>" for item in value) + "</ul>"
    return esc(value)


def raw(value):
    """Keep documentary assumptions visible without interpreting their arithmetic."""
    if isinstance(value, dict):
        return '<dl class="uw-raw">' + "".join(
            "<dt>" + esc(label(key)) + "</dt><dd>" + raw(item) + "</dd>"
            for key, item in value.items()
        ) + "</dl>"
    if isinstance(value, list):
        return "<ul>" + "".join("<li>" + raw(item) + "</li>" for item in value) + "</ul>"
    return unavailable() if value is None else esc(value)


def table(headers, rows, classes=""):
    return '<div class="scroll"><table class="uw-table ' + esc(classes) + '"><thead><tr>' + "".join(
        '<th scope="col">' + esc(header) + "</th>" for header in headers
    ) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join("<td>" + cell + "</td>" for cell in row) + "</tr>" for row in rows
    ) + "</tbody></table></div>"


def references(value, registry):
    found = []
    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key in ("source", "sources", "source_ids"):
                    for identifier in child if isinstance(child, list) else [child]:
                        if isinstance(identifier, str) and identifier in registry and identifier not in found:
                            found.append(identifier)
                else:
                    visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
    visit(value)
    return found


def evidence(u, identifiers):
    registry = u.get("sources", {})
    links = []
    for identifier in dict.fromkeys(identifiers):
        source = registry.get(identifier)
        if not source:
            continue
        anchor = u["ticker"].lower() + "-uw-source-" + identifier
        primary = url(source.get("url"))
        links.append('<a href="' + esc(primary or "#" + anchor) + '">' + esc(source.get("title", identifier)) + "</a>"
            + " · " + esc(source.get("published", "Publication date unavailable"))
            + (" · " + esc(source.get("section") or source.get("locator")) if source.get("section") or source.get("locator") else "")
            + ' · <a href="#' + esc(anchor) + '">Quoted passage</a>')
    return '<p class="uw-evidence">' + "<br>".join(links) + "</p>" if links else ""


def base_case(u):
    cases = u.get("computed", {}).get("cases", [])
    return next((case for case in cases if case.get("id") == "base"), {})


def first_statement(value):
    """Display a complete authored sentence; retain the full argument below."""
    if isinstance(value, str):
        return esc(re.split(r"(?<=[.!?])\s+(?=[A-Z])", value.strip(), maxsplit=1)[0])
    return copy(value)


def compact_decision(u, case, call, reference, price):
    gap = case.get("funding_gap")
    compact_gap = ("$" + f"{gap / 1000:,.2f}B") if numeric(gap) and abs(gap) >= 1000 else amount(gap)
    body = '<section class="uw-mobile-decision" aria-label="12-month investment decision"><strong class="uw-mobile-rating" role="heading" aria-level="1">12-month call · ' + copy(call.get("rating")) + "</strong>"
    body += '<div class="uw-mobile-metrics"><div><small>Reference · ' + esc(reference.get("as_of", "Date unavailable")) + "</small><strong>" + price
    body += "</strong></div><div><small>Base value / share</small><strong>" + dollars(case.get("value_per_share")) + ' <span>' + percent(case.get("return_pct")) + "</span></strong></div>"
    body += "<div><small>Modeled net equity gap</small><strong>" + compact_gap + "</strong></div><div><small>Total modeled dilution</small><strong>" + percent(case.get("dilution_pct")) + "</strong></div></div>"
    body += '<div class="uw-mobile-answers">'
    for key, title in (("driver", "Main fact"), ("strongest_objection", "Strongest objection"), ("falsifier", "Change the rating")):
        body += '<section data-decision-answer="' + key + '"><h3>' + title + "</h3><p>" + first_statement(call.get(key)) + "</p></section>"
    body += "</div><details><summary>Full decision evidence & valuation hurdle</summary>"
    body += "<p>" + copy(call.get("summary")) + "</p>"
    for key, title in (("driver", "Main fact"), ("strongest_objection", "Strongest objection"), ("falsifier", "Change the rating"), ("rating_hurdle", "Analyst valuation hurdle")):
        if call.get(key):
            body += "<h4>" + title + "</h4><p>" + copy(call[key]) + "</p>"
    body += '<p class="uw-note">Reference observation: ' + shown(reference.get("observed_at", reference.get("as_of"))) + ". " + copy(reference.get("note")) + "</p>"
    return body + "</details></section>"


def decision(u):
    case, call, reference = base_case(u), u.get("call", {}), u.get("reference", {})
    reference_source = u.get("sources", {}).get(reference.get("source"), {})
    reference_url = url(reference_source.get("url")) or url(reference.get("url"))
    price = dollars(reference.get("price"))
    if reference_url:
        price = '<a href="' + esc(reference_url) + '">' + price + "</a>"
    stamp = "Information cutoff " + esc(u.get("cutoff", "Unavailable")) + " · 12-month target date " + esc(u.get("target_date", "Unavailable"))
    desktop = ('<div class="uw-desktop-decision"><div class="uw-decision"><strong>12-month call · ' + copy(call.get("rating")) + "</strong>"
        + "<h1>" + copy(call.get("summary")) + "</h1></div>"
        + '<div class="uw-price-strip"><div><small>Reference price · ' + esc(reference.get("as_of", "Date unavailable")) + "</small><strong>" + price
        + "</strong>" + ("<small>" + esc(reference["observed_at"]) + "</small>" if reference.get("observed_at") else "")
        + "</div><div><small>12-month base value / share</small><strong>" + dollars(case.get("value_per_share"))
        + "</strong></div><div><small>Base return from reference</small><strong>" + percent(case.get("return_pct"))
        + "</strong></div><div><small>Modeled existing-holder dilution</small><strong>" + percent(case.get("dilution_pct")) + "</strong></div></div>"
        + '<div class="uw-tests"><section><h3>What does the most work</h3><p>' + copy(call.get("driver"))
        + "</p></section><section><h3>Strongest evidence against the call</h3><p>" + copy(call.get("strongest_objection"))
        + "</p></section><section><h3>What would change the rating</h3><p>" + copy(call.get("falsifier")) + "</p>"
        + ("<details><summary>Analyst valuation hurdle</summary><p>" + copy(call["rating_hurdle"]) + "</p></details>" if call.get("rating_hurdle") else "")
        + "</section></div></div>")
    return ('<section class="uw-opening" data-underwriting="' + esc(u["ticker"]) + '"><p class="uw-stamp">' + stamp + "</p>"
        + compact_decision(u, case, call, reference, price) + desktop
        + '<p class="uw-note">Analyst underwriting, not company guidance. Future financing, operating estimates and valuation multiples below are assumptions. '
        + "The target date is distinct from the fiscal operating period.</p></section>")


def opening_bridge(u):
    opening = u.get("computed", {}).get("opening", {})
    reported = u.get("opening", {})
    combined_cash = reported.get("cash_includes_restricted")
    rows = [
        ("Reported cash at the balance-sheet date", "reported_cash", "Includes restricted balances." if combined_cash else "Already excludes separately disclosed restricted cash."),
        ("Restricted cash disclosed separately", "restricted_cash", "Subtracted once from combined cash." if combined_cash else "Already outside the reported cash line; not subtracted a second time."),
        ("Usable opening cash", "usable_cash", "Calculated opening liquidity."),
        ("Minimum operating cash reserve", "minimum_cash", "Analyst assumption; not a legal restriction."),
        ("Closed subsequent transactions, net cash", "closed_transaction_net_cash", "Gross proceeds less fees, refinancing and repayments as modeled."),
        ("Financing-only cash roll-forward through cutoff", "rolled_cash", "Informational; excludes intervening operating / capex uses and is not a current cash balance. Conditional or undrawn capacity is not cash."),
        ("Debt after the closed financing-only roll", "debt", "Model debt claim; principal/redemption and carrying-value distinctions remain in the source notes."),
    ]
    body = '<p class="uw-note">Reported balance-sheet date ' + shown(reported.get("as_of")) + ". " + copy(reported.get("note")) + "</p>"
    body += table(["Opening bridge · USD millions", "Amount", "Treatment"], [
        [esc(name), amount(opening.get(key)), esc(note)] for name, key, note in rows
    ])
    body += evidence(u, references(u.get("opening", {}), u.get("sources", {})))
    body += "<details><summary>Reported opening inputs, dates, scope and source references</summary>" + raw(u.get("opening")) + "</details>"
    body += "<details><summary>Subsequent transactions: closed, announced and conditional</summary><p class=\"uw-note\">Only transactions accepted by the model as closed enter opening cash. Gross proceeds, fees and repayments retain their separate inputs.</p>"
    body += raw(u.get("transactions", [])) + evidence(u, references(u.get("transactions", []), u.get("sources", {}))) + "</details>"
    return body


def funding_bridge(u, case):
    periods = case.get("bridge", [])
    columns = [esc(str(period.get("start", ""))) + " → " + esc(str(period.get("end", ""))) for period in periods]
    lines = [
        ("Opening cash", "opening_cash"), ("Operating cash flow before modeled cash interest", "ocf_before_interest"),
        ("Prepayments already embedded in OCF — memo only", "prepayments_embedded"),
        ("Additional prepayments counted once", "prepayments_added"), ("Cash capex", "capex"),
        ("Other cash uses", "other_uses"), ("Cash interest", "cash_interest"),
        ("Closed transaction net cash in this period", "transaction_net_cash"),
        ("New debt proceeds", "new_debt"), ("Debt repayments / refinancing uses", "debt_repayment"),
        ("Closed transaction debt change — reconciliation", "transaction_debt_change"),
        ("Cash before hypothetical equity", "cash_before_equity"), ("Funding gap before equity", "equity_gap"),
        ("Gross hypothetical equity proceeds", "gross_equity"), ("Issuance fees", "issuance_fees"),
        ("Ending cash", "ending_cash"), ("Ending debt", "ending_debt"),
    ]
    body = table(["Model cash bridge · USD millions", *columns], [
        [esc(name), *[amount(period.get(key)) for period in periods]] for name, key in lines
    ], "uw-bridge")
    body += '<p class="uw-formula">A customer prepayment already embedded in modeled operating cash flow is shown as a memo, not added a second time. '
    body += "Backlog and total contract value are not cash receipts. The minimum operating reserve is an analyst liquidity assumption.</p>"
    body += table(["Period", "New equity shares", "Conversion shares", "Ending shares"], [
        [esc(str(period.get("start", ""))) + " → " + esc(str(period.get("end", ""))),
         shares(period.get("new_shares")), shares(period.get("conversion_shares")), shares(period.get("ending_shares"))] for period in periods
    ])
    body += '<p class="uw-note">Period-end financing is conditional; an intraperiod cash shortfall can exceed the modeled period-end gap.</p>'
    body += "<details><summary>Timing and classification notes by cash period</summary><ul>" + "".join(
        "<li>" + esc(period.get("start", "")) + " → " + esc(period.get("end", "")) + ": " + copy(period.get("note")) + "</li>"
        for period in periods
    ) + "</ul></details>"
    return body


def scenarios(u):
    cases = u.get("computed", {}).get("cases", [])
    rows = []
    for case in cases:
        annual, valuation = case.get("annual_operating", {}), case.get("valuation", {})
        rows.append([
            "<strong>" + esc(str(case.get("id", "")).title()) + "</strong>",
            amount(annual.get("revenue")) + '<small class="uw-case-note">Fiscal ' + esc(annual.get("year", "year unavailable")) + "</small>",
            multiple(valuation.get("multiple")) + '<small class="uw-case-note">' + esc(label(valuation.get("method", ""))) + "</small>",
            amount(case.get("funding_gap")), percent(case.get("dilution_pct")),
            dollars(case.get("value_per_share")), percent(case.get("return_pct")),
        ])
    body = table(["Case", "Operating revenue", "Valuation assumption", "Funding gap before equity", "Total holder dilution", "Value / share", "Return from reference"], rows, "uw-cases")
    body += '<p class="uw-note">Dollar totals are USD millions; share counts are millions. Per-share prices are USD. New-model margins, discounts, fees and debt rates use decimal fractions; fields explicitly labeled (%) use percentage points. Financing dilution is separate from total dilution including conversions and modeled awards/options. Scenario outputs are calculated from the documented inputs, not issuer targets.</p>'
    body += "<h4>Equity issuance: discount, fees and the share denominator</h4>"
    body += table(["Case", "Gross issue price", "Net proceeds / share", "Issuance fees", "New shares", "Post-financing shares", "Financing dilution"], [
        [esc(case.get("id", "")), dollars(case.get("issue", {}).get("actual_issue_price")),
         dollars(case.get("issue", {}).get("net_proceeds_per_share")), amount(case.get("issuance_fees")),
         shares(case.get("new_shares")), shares(case.get("post_financing_shares")), percent(case.get("financing_dilution_pct"))]
        for case in cases
    ])
    body += "<h4>Enterprise value → common equity → value per share</h4>"
    body += table(["Case", "Enterprise value", "Less target debt", "Plus target cash", "Less other claims", "Common equity value", "Post-financing shares", "Value / share"], [
        [esc(case.get("id", "")), amount(case.get("enterprise_value")), amount(case.get("target_debt")), amount(case.get("target_cash")),
         amount(case.get("other_ev_claims")), amount(case.get("equity_value")), shares(case.get("post_financing_shares")), dollars(case.get("value_per_share"))]
        for case in cases
    ])
    body += '<p class="uw-formula">Common equity = enterprise value − target debt + target unrestricted cash − other claims. Value per share = common equity / post-financing shares, floored at zero. Return = value per share / reference price − 1.</p>'
    for case in cases:
        original = next((item for item in u.get("cases", []) if item.get("id") == case.get("id")), {})
        body += '<details class="uw-scenario-block" data-scenario="' + esc(case.get("id", "")) + '"><summary>' + esc(str(case.get("id", "")).title()) + " operating assumptions, financing terms and timing</summary>"
        body += "<h4>Operating assumptions and fiscal period</h4>" + raw(case.get("annual_operating"))
        if original.get("operating_assumptions"):
            body += "<h4>Capacity, yield, operating costs and cash conversion</h4>" + raw(original["operating_assumptions"])
            body += evidence(u, references(original["operating_assumptions"], u.get("sources", {})))
        body += "<h4>Equity issuance assumptions</h4>" + raw(case.get("issue"))
        body += "<h4>Valuation assumptions</h4>" + raw(case.get("valuation"))
        body += "<h4>Other scenario assumptions</h4>" + raw(case.get("assumptions"))
        body += "<p><strong>Case status:</strong> " + shown(case.get("status")) + "</p>"
        body += funding_bridge(u, case) + evidence(u, case.get("source_ids", [])) + "</details>"
    return body


def share_bridge(u):
    opening = u.get("computed", {}).get("opening", {})
    body = '<p>Starting model denominator: <strong>' + shares(u.get("opening", {}).get("shares")) + "</strong> as of " + shown(u.get("opening", {}).get("shares_as_of", u.get("opening", {}).get("as_of"))) + ". "
    body += "After closed known share events: <strong>" + shares(opening.get("shares")) + "</strong>. "
    body += "Period-end common shares, economic claims and future issuance are distinct. Forecast equity financing is modeled rather than asserted as a completed transaction.</p>"
    body += table(["Case", "New equity shares", "Convertible debt removed", "Conversion shares", "Additional award / option shares", "Post-financing shares", "Target total debt"], [
        [esc(case.get("id", "")), shares(case.get("new_shares")), amount(case.get("convertible_principal_removed")),
         shares(case.get("conversion_shares")), shares(case.get("additional_shares")), shares(case.get("post_financing_shares")), amount(case.get("target_debt"))]
        for case in u.get("computed", {}).get("cases", [])
    ])
    body += "<details><summary>Convertible terms and share / debt treatment</summary>" + raw(u.get("convertibles", []))
    body += evidence(u, references(u.get("convertibles", []), u.get("sources", {}))) + "</details>"
    body += "<details><summary>Opening share-count reconciliation and assumptions</summary>" + raw(u.get("opening", {})) + "</details>"
    capacities = [case for case in u.get("computed", {}).get("cases", []) if case.get("equity_capacity")]
    if capacities:
        body += "<h4>Hypothetical issuance versus the dated issuance-capacity checkpoint</h4>"
        body += '<p class="uw-note">This is a dated comparison, not verified funding available at the cutoff. Additional authorization, new facilities or changed issuance terms may be required. No checkpoint amount is added to cash.</p>'
        for case in capacities:
            body += "<details><summary>" + esc(case["id"].title()) + " dated-capacity comparison</summary>" + raw(case["equity_capacity"])
            body += evidence(u, references(case["equity_capacity"], u.get("sources", {}))) + "</details>"
    return body


def reverse_and_sensitivity(u):
    reverse = u.get("computed", {}).get("reverse", {})
    sensitivity = u.get("computed", {}).get("sensitivity", {})
    body = '<div class="uw-facts"><div><small>Revenue multiple implied by the reference price</small><strong>' + multiple(reverse.get("required_multiple"))
    body += "</strong></div><div><small>Revenue required at the fixed base multiple</small><strong>" + amount(reverse.get("required_revenue")) + "</strong></div></div>"
    body += "<p><strong>Held fixed:</strong> " + copy(reverse.get("held_fixed")) + "</p><p>" + copy(reverse.get("method")) + "</p>"
    x, y = sensitivity.get("x", {}), sensitivity.get("y", {})
    cells = sensitivity.get("cells", [])
    if cells:
        body += "<h4>Two-variable value-per-share sensitivity</h4><p class=\"uw-note\">Model assumptions: "
        axis_labels = {"multiple": "EV multiple (×)", "issue_price": "Pre-discount issue reference (USD/share)", "revenue": "Annual revenue (USD millions)", "capex_scale": "Modeled capex scale (×)"}
        x_label, y_label = axis_labels.get(x.get("field"), label(x.get("field", "x"))), axis_labels.get(y.get("field"), label(y.get("field", "y")))
        body += esc(x_label) + " across columns; " + esc(y_label) + " down rows. "
        body += "Each cell shows USD value per share and return from the same dated reference price. Axis input values retain the model’s units.</p>"
        rows = []
        for y_value in y.get("values", []):
            row = [esc(y_value)]
            for x_value in x.get("values", []):
                cell = next((cell for cell in cells if cell.get("x") == x_value and cell.get("y") == y_value), {})
                row.append(dollars(cell.get("value_per_share")) + "<small>" + percent(cell.get("return_pct")) + "</small>")
            rows.append(row)
        body += table([y_label + " / " + x_label, *[str(item) for item in x.get("values", [])]], rows, "uw-sensitivity")
        body += '<p class="uw-note">' + copy(sensitivity.get("method")) + "</p>"
    else:
        body += '<p class="uw-unavailable">Two-variable sensitivity unavailable. See unresolved evidence and model gaps.</p>'
    return body


def source_register(u):
    body = ""
    for identifier, source in u.get("sources", {}).items():
        link = url(source.get("url"))
        body += '<details class="uw-source" id="' + esc(u["ticker"].lower() + "-uw-source-" + identifier) + '"><summary>'
        body += esc(source.get("title", identifier)) + " · " + esc(source.get("published", "Publication date unavailable")) + "</summary>"
        body += "<p><strong>Locator:</strong> " + esc(source.get("section") or source.get("locator") or "Locator unavailable") + "</p>"
        body += '<p class="uw-provenance"><strong>Publication:</strong> ' + shown(source.get("published"))
        body += " · <strong>Observation / period:</strong> " + shown(source.get("period"))
        body += " · <strong>Units:</strong> " + shown(source.get("unit")) + "</p>"
        body += '<blockquote>' + esc(source.get("excerpt", "Supporting excerpt unavailable.")) + "</blockquote>"
        if link:
            body += '<p><a href="' + esc(link) + '">' + esc(source.get("title", "Open primary source")) + "</a><br>" + esc(link) + "</p>"
        body += "</details>"
    return body


def reconciliation_records(u, records):
    body = ""
    for title, key in records:
        record = u.get(key)
        if record:
            body += "<details><summary>" + esc(title) + "</summary>"
            if isinstance(record, dict) and any(isinstance(child, dict) and references(child, u.get("sources", {})) for child in record.values()):
                for key, child in record.items():
                    body += "<h4>" + esc(label(key)) + "</h4>" + raw(child)
                    body += evidence(u, references(child, u.get("sources", {})))
            else:
                body += raw(record)
            body += evidence(u, references(record, u.get("sources", {}))) + "</details>"
    return body


def historical_bridge(u):
    historical = u.get("historical", {})
    original = historical.get("original_model") or u.get("original_reconstruction", {}).get("original_model", {})
    metrics = original.get("metrics", {})
    body = "<p>The original fiscal-year operating forecast is not a 12-month equity financing gap. Timing, new borrowing, cash reserves, fees and the resulting share count are modeled explicitly in the new bridge.</p>"
    body += table(["Original base fiscal year", "Original revenue", "Original free cash flow", "Original model information date"], [
        [shown(original.get("year")), amount(metrics.get("revenue")), amount(metrics.get("fcf")),
         shown(historical.get("as_of") or u.get("original_reconstruction", {}).get("as_of"))]
    ])
    reproduced = historical.get("reproduced", {})
    if reproduced:
        body += "<p><strong>Independent reproduction:</strong> revenue " + amount(reproduced.get("revenue")) + "; free cash flow " + amount(reproduced.get("free_cash_flow")) + ".</p>"
        body += "<p>" + copy(reproduced.get("prepayment_treatment")) + "</p>"
    body += "<details><summary>Original equations, prepayment audit and preserved prior call</summary>" + raw(historical)
    if u.get("original_reconstruction"):
        body += raw(u["original_reconstruction"])
    return body + "</details>"


def report(u):
    ticker = u["ticker"].lower()
    opening = opening_bridge(u) + reconciliation_records(u, [
        ("Reported cash flow, cash restrictions, debt, leases and customer concentration", "observed"),
        ("Reported operating cash flow, deferred revenue and prepayments", "prepayment_reconciliation"),
        ("Gross proceeds, fees, refinancings and already-counted financing", "upfront_financing_audit"),
        ("Source-check scope, refresh dates and remaining access gaps", "freshness"),
    ])
    ownership = share_bridge(u) + reconciliation_records(u, [
        ("Reported ordinary shares, warrants, awards and excluded treasury shares", "share_bridge"),
        ("Reference-date equity / enterprise-value denominator reconciliation", "reference_denominator_bridge"),
        ("Conversion alternatives and their effect on debt, cash and shares", "conversion_audit"),
        ("Dated equity-issuance-capacity audit", "equity_capacity_audit"),
    ])
    valuation_notes = reconciliation_records(u, [
        ("Valuation-multiple rationale and comparison limits", "multiple_rationale"),
        ("Nonoperating investments: baseline treatment and alternative credit", "nonoperating_investments"),
    ])
    sections = [
        ("cash", "From reported cash to usable liquidity", opening),
        ("funding", "Base funding bridge and cash timing", funding_bridge(u, base_case(u))),
        ("scenarios", "Bear, base and bull: common-equity outcomes", scenarios(u) + valuation_notes),
        ("shares", "Dilution, share count and convertibles", ownership),
        ("reverse", "What the reference price already requires", reverse_and_sensitivity(u)),
        ("historical", "What changed from the historical operating model", historical_bridge(u)),
        ("gaps", "What remains an assumption or an evidence gap", copy(u.get("gaps", [])) + copy(u.get("model_limitations", []))),
        ("sources", "Dated sources and filing locators", source_register(u)),
    ]
    nav = '<nav class="uw-nav" aria-label="Underwriting sections">' + "".join(
        '<a href="#' + ticker + "-uw-" + key + '">' + esc(title.split(":")[0]) + "</a>" for key, title, _ in sections
    ) + "</nav>"
    return decision(u) + nav + "".join(
        '<section class="uw-section" id="' + ticker + "-uw-" + key + '"><h3>' + esc(title) + "</h3>" + body + "</section>"
        for key, title, body in sections
    )


def overview(research, href):
    companies = research.get("companies", {})
    deep = [(ticker, companies[ticker]["underwriting"]) for ticker in ("NBIS", "CRWV") if companies.get(ticker, {}).get("underwriting")]
    if not deep:
        return ""
    body = '<section class="mast"><span class="byline">JUSTIN / EQUITY RESEARCH</span><h1>From funding need to value per share.</h1>'
    body += "<p>Two independent 12-month investment tests, followed by the evidence audit across all nine companies. Financing and valuation assumptions remain separate from reported facts.</p></section>"
    rows = []
    for ticker, u in deep:
        case, reference, call = base_case(u), u.get("reference", {}), u.get("call", {})
        bear = next((item for item in u.get("computed", {}).get("cases", []) if item.get("id") == "bear"), {})
        bull = next((item for item in u.get("computed", {}).get("cases", []) if item.get("id") == "bull"), {})
        rows.append([
            '<a href="' + esc(href(ticker)) + '">' + esc(ticker) + "</a><small class=\"uw-case-note\">" + copy(call.get("rating")) + "</small>",
            dollars(reference.get("price")) + '<small class="uw-case-note">' + esc(reference.get("as_of", "Date unavailable")) + "</small>",
            amount(case.get("funding_gap")), percent(case.get("dilution_pct")), dollars(case.get("value_per_share")), percent(case.get("return_pct")),
            percent(bear.get("return_pct")) + " / " + percent(bull.get("return_pct")),
        ])
    body += table(["12-month call", "Reference price / date", "Base gap before equity", "Modeled dilution", "Base value / share", "Base return", "Bear / bull return"], rows, "uw-comparison")
    body += '<p class="uw-note">Funding gaps are USD millions before hypothetical common equity; dilution is existing-holder dilution. Both are scenario outputs. Read each report for its target date, debt treatment and fiscal valuation period.</p>'
    body += '<div class="uw-tests uw-overview-tests">' + "".join(
        '<section><h3>' + esc(ticker) + " · strongest fact and objection</h3><p>" + copy(u.get("call", {}).get("driver"))
        + "</p><p><strong>Against the call:</strong> " + copy(u.get("call", {}).get("strongest_objection"))
        + "</p><p><strong>Observable rating threshold:</strong> " + copy(u.get("call", {}).get("falsifier")) + "</p></section>"
        for ticker, u in deep
    ) + "</div>"
    audit = research.get("call_audit")
    if audit:
        body += call_audit(audit, href)
    return body


def call_audit(audit, href):
    body = '<section class="uw-section" id="call-audit"><h2>Nine-company call audit</h2><p class="uw-note">Information cutoff '
    body += esc(audit.get("cutoff", "Unavailable")) + ". Evidence support is distinct from share-price performance. Missing ratings and unresolved claims are not filled with new targets.</p>"
    rows = []
    for item in audit.get("companies", []):
        link = url(item.get("url"))
        citation = shown(item.get("source_title")) + "<br>" + shown(item.get("publication_date"))
        if link:
            citation = '<a href="' + esc(link) + '">' + citation + "</a>"
        checked = "<details><summary>Claim, finding & unresolved variable</summary><p><strong>Claim checked:</strong> " + copy(item.get("claim"))
        checked += "</p><p><strong>Disclosure finding:</strong> " + copy(item.get("finding"))
        checked += "</p><p><strong>Largest unresolved variable:</strong> " + copy(item.get("gap")) + "</p></details>"
        rows.append([
            '<a href="' + esc(href(item["ticker"])) + '">' + esc(item["ticker"]) + "</a>",
            copy(item.get("call")) + '<small class="uw-case-note">' + shown(item.get("call_date")) + "</small>",
            copy(item.get("verdict")), checked,
            citation + '<details><summary>Filing locator</summary>' + shown(item.get("locator")) + "</details>",
        ])
    body += table(["Company", "Dated call", "Evidence verdict", "Evidence check & research gap", "Source / publication / locator"], rows, "uw-audit")
    body += "<h3>Next three deep research priorities</h3><ol class=\"uw-priorities\">"
    for item in audit.get("priorities", [])[:3]:
        body += '<li><a href="' + esc(href(item["ticker"])) + '"><strong>' + esc(item["ticker"]) + "</strong></a> · " + copy(item.get("question"))
        body += "<p>" + copy(item.get("why")) + "</p></li>"
    return body + "</ol></section>"
