/* Stock performance UI. marketData is separate from the financial research ledger. */
function stockWindow() {
  return ["1w", "1m", "3m", "ytd"].includes(state.window) ? state.window : "1m";
}
function stockPermitted() {
  return (
    marketData?.license?.status === "public_display_permitted" &&
    ["ready", "partial"].includes(marketData?.status)
  );
}
function stockMethod() {
  return marketData?.price_basis === "total_return"
    ? "Total return · dividends included"
    : "Split-adjusted price return · dividends excluded";
}
function stockSigned(value) {
  if (!finite(value)) return "Unavailable";
  const n = Number(value);
  if (n !== 0 && Math.abs(n) < 0.01) return n < 0 ? "−<0.01%" : "+<0.01%";
  return (
    (n > 0 ? "+" : n < 0 ? "−" : "") +
    Math.abs(n).toLocaleString("en-US", {
      maximumFractionDigits: 2,
      minimumFractionDigits: 1,
    }) +
    "%"
  );
}
function stockPrice(value, currency = "USD") {
  return finite(value)
    ? (currency === "USD" ? "$" : esc(currency) + " ") +
        Number(value).toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 4,
        })
    : "Unavailable";
}
function stockSeriesValue(value, currency = "USD") {
  return marketData?.price_basis === "total_return" && finite(value)
    ? Number(value).toLocaleString("en-US", { maximumFractionDigits: 4 }) +
        " index"
    : stockPrice(value, currency);
}
function stockCap(value) {
  if (!finite(value)) return "Market cap unavailable";
  const rounded = money(value),
    n = Number(value);
  // A rounded label must not appear to cross its accompanying size boundary.
  return [300e6, 2e9, 10e9].some(
    (boundary) => n < boundary && rounded === money(boundary),
  )
    ? money(value, true)
    : rounded;
}
function stockSource(url, label = "Source") {
  const safe = safeURL(url);
  return safe
    ? `<a href="${esc(safe)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`
    : "";
}
function stockRows() {
  const records = new Map(list(marketData?.companies).map((c) => [c.id, c]));
  const rows = visible
    .filter((c) => {
      const listing =
        records.get(c.id)?.listing_status ||
        c.listing_status ||
        finance(c).listing_status;
      return listing === "listed" || listing === "public";
    })
    .map((company) => {
      const record = records.get(company.id),
        ret = record?.returns?.[stockWindow()];
      const available =
        stockPermitted() &&
        ret?.status === "available" &&
        finite(ret.value) &&
        ret.end_session === marketData.end_session;
      const cap = record?.market_cap,
        sizeBand =
          ["verified", "dated_manual"].includes(cap?.status) &&
          finite(cap.value) &&
          Number(cap.value) > 0
            ? cap.size_band || "unknown"
            : "unknown";
      return {
        company,
        market: record,
        ret: available
          ? ret
          : {
              ...ret,
              value: null,
              status: "unavailable",
              reason:
                ret?.reason ||
                record?.price?.reason ||
                marketData?.gap_reason ||
                "Verified observations are not available for this comparison.",
            },
        sizeBand,
      };
    });
  const sizeOrder = { large: 0, mid: 1, small: 2, micro: 3, unknown: 4 };
  rows.sort((a, b) => {
    if (state.groupSize && sizeOrder[a.sizeBand] !== sizeOrder[b.sizeBand])
      return sizeOrder[a.sizeBand] - sizeOrder[b.sizeBand];
    const av = finite(a.ret.value),
      bv = finite(b.ret.value);
    return av && bv
      ? Number(b.ret.value) - Number(a.ret.value) ||
          a.company.name.localeCompare(b.company.name)
      : av
        ? -1
        : bv
          ? 1
          : a.company.name.localeCompare(b.company.name);
  });
  return rows;
}
function stockSizeName(band) {
  return (
    {
      large: "Large",
      mid: "Medium",
      small: "Small",
      micro: "Micro",
      unknown: "Size unverified",
    }[band] || "Size unverified"
  );
}
function stockScale(rows) {
  const maximum = Math.max(
    0,
    ...rows
      .filter((r) => finite(r.ret.value))
      .map((r) => Math.abs(Number(r.ret.value))),
  );
  if (maximum === 0) return 1;
  const power = 10 ** Math.floor(Math.log10(maximum));
  return [1, 2, 5, 10].find((n) => n * power >= maximum) * power;
}
function stockStatus() {
  const observed = marketData?.as_of,
    refresh = marketData?.refresh || {};
  const observedDay = observed
      ? Date.parse(observed.slice(0, 10) + "T00:00:00Z")
      : NaN,
    today = Date.parse(new Date().toISOString().slice(0, 10) + "T00:00:00Z");
  const age = Number.isFinite(observedDay)
    ? Math.max(0, Math.floor((today - observedDay) / 86400000))
    : null;
  const timestamp = observed
    ? `<time datetime="${esc(observed)}">${esc(observed.replace("T", " ").replace("Z", " UTC"))}</time>`
    : "not available";
  return /* HTML */ `<div id="market-data-status" class="market-data-status">
    <span
      ><span class="market-status-dot" aria-hidden="true"></span>Market data as
      of ${timestamp}</span
    >${finite(age)
      ? `<span>${Number(age)} ${Number(age) === 1 ? "day" : "days"} old${refresh.stale ? " · stale snapshot" : ""}</span>`
      : ""}${refresh.status === "failed"
      ? '<span class="market-stale">Refresh failed; last good snapshot retained</span>'
      : ""}${stockPermitted() ? `<span>${stockSource(marketData.license.source_url, marketData.license.attribution_text || marketData.license.provider || "Price source")} · ${stockSource(marketData.license.permission_url, "Data terms")}</span>` : ""}
    <span>Financial research cutoff ${day(data.reviewed_at)}</span>
  </div>`;
}
function stockControls(showView = false) {
  return /* HTML */ `<div class="stock-toolbar">
    <div
      class="stock-window-control"
      role="group"
      aria-label="Stock return window"
    >
      ${[
        ["1w", "1W"],
        ["1m", "1M"],
        ["3m", "3M"],
        ["ytd", "YTD"],
      ]
        .map(
          ([id, label]) =>
            `<button type="button" data-stock-window="${id}" aria-pressed="${stockWindow() === id}">${label}</button>`,
        )
        .join("")}
    </div>
    <label class="stock-group-toggle"
      ><input
        id="stock-group-size"
        data-stock-group
        type="checkbox"
        ${state.groupSize ? "checked" : ""}
      />
      Group by size</label
    >${showView
      ? `<div class="stock-view-control" role="group" aria-label="Market chart view"><button type="button" data-stock-view="rank" aria-pressed="${state.marketView !== "scatter"}">Ranked returns</button><button type="button" data-stock-view="scatter" aria-pressed="${state.marketView === "scatter"}">Size vs return</button></div>`
      : ""}
    <div id="stock-peer-slot"></div>
  </div>`;
}
function stockWindowCaption() {
  const w = marketData?.windows?.[stockWindow()];
  return /* HTML */ `<p class="stock-window-caption">
    ${stockMethod()}${w?.start_session && w?.end_session
      ? ` · <strong>${day(w.start_session)} – ${day(w.end_session)}</strong>`
      : " · verified window dates unavailable"}<span
      >Common completed end session ${day(marketData?.end_session)}. Actual
      start dates stay attached to each result.</span
    >
  </p>`;
}
function stockBlocked() {
  const sized = stockRows().filter((r) => r.sizeBand !== "unknown").length;
  return /* HTML */ `<div class="market-blocked" role="status">
    <div class="market-blocked-mark" aria-hidden="true">—</div>
    <div>
      <h2>Verified stock performance is not available.</h2>
      <p>No approved, verified price series is available for public display.</p>
      <details class="market-access-detail">
        <summary>Why returns are unavailable</summary>
        <p>
          ${esc(
            marketData?.gap_reason ||
              "A verified price snapshot and public-display permission are required before stock returns can be shown.",
          )}
        </p>
        ${stockSource(
          marketData?.license?.permission_url ||
            marketData?.license?.source_url,
          "Data source & display policy",
        )}
      </details>
      <p class="market-policy-note">
        ${sized ? `${sized} selected ${sized === 1 ? "company has" : "companies have"} a dated market-cap classification.` : ""}${state.page !== "markets"
          ? ` <a data-app href="${esc(href("markets"))}">View dated company sizes in Markets</a>`
          : ""}
      </p>
    </div>
  </div>`;
}

function stockCompany(row) {
  const c = row.company,
    cap = row.market?.market_cap;
  return /* HTML */ `<div class="stock-company">
    <a data-app href="${esc(profile(c))}"
      ><span class="stock-ticker">${esc(c.ticker)}</span
      ><strong>${esc(c.name)}</strong></a
    >
    <div class="stock-company-meta">
      <span
        >${finite(cap?.value)
          ? stockCap(cap.value)
          : "Market cap unavailable"}</span
      ><span class="stock-size stock-size-${esc(row.sizeBand)}"
        >${esc(stockSizeName(row.sizeBand))}</span
      >${cap?.as_of
        ? `<time datetime="${esc(cap.as_of)}">${day(cap.as_of)}</time>`
        : ""}
    </div>
    ${cap?.status === "unreconciled"
      ? '<span class="stock-cap-warning">Capitalization not reconciled</span>'
      : ""}
  </div>`;
}
function stockReturnDetails(row) {
  const r = row.ret,
    m = row.market,
    history = list(m?.history),
    start = history.find((p) => p.date === r.start_session),
    end = history.find((p) => p.date === r.end_session);
  return /* HTML */ `<div class="stock-return-detail">
    <dl>
      <div>
        <dt>Actual closing dates</dt>
        <dd>${day(r.start_session)} to ${day(r.end_session)}</dd>
      </div>
      <div>
        <dt>
          ${marketData?.price_basis === "total_return"
            ? "Starting / ending index"
            : "Starting / ending adjusted close"}
        </dt>
        <dd>
          ${stockSeriesValue(start?.close, m?.currency)} /
          ${stockSeriesValue(end?.close, m?.currency)}
        </dd>
      </div>
      <div>
        <dt>Exchange / currency</dt>
        <dd>
          ${esc(m?.exchange || "Not established")} ·
          ${esc(m?.currency || "Not established")}
        </dd>
      </div>
      <div>
        <dt>Capitalization share basis</dt>
        <dd>${esc(m?.market_cap?.share_basis || "Not established")}</dd>
      </div>
      <div>
        <dt>Return basis</dt>
        <dd>${esc(stockMethod())}</dd>
      </div>
    </dl>
    <p>
      ${esc(
        r.reason ||
          "Return = (ending adjusted close ÷ starting adjusted close − 1) × 100. Prices describe market performance; they are not an earnings verdict.",
      )}
    </p>
    ${stockSource(
      m?.price?.source_url || m?.source_url || marketData?.license?.source_url,
      "Price source",
    )}${row.market?.market_cap?.reason
      ? `<p>${esc(row.market.market_cap.reason)}</p>`
      : ""}
  </div>`;
}
function rankedStocks(rows) {
  const max = stockScale(rows),
    known = rows.filter((r) => finite(r.ret.value));
  if (!rows.length)
    return '<p class="market-empty">No public companies match this selection. Private records remain in the research universe.</p>';
  if (!known.length)
    return /* HTML */ `<div
      id="ranked-stock-returns"
      class="stock-unavailable-list"
    >
      <p class="market-empty">
        No verified returns are available for this window and selection.
      </p>
      ${rows
        .map(
          (r) =>
            `<article class="stock-return-row stock-missing-row" data-stock-company="${esc(r.company.id)}">${stockCompany(r)}<div><strong>Unavailable</strong><p>${esc(r.ret.reason)}</p></div></article>`,
        )
        .join("")}
    </div>`;
  const returnsByRank = known.map(row => row.ret.value).sort((a, b) => b - a);
  let group;
  return /* HTML */ `<div
    id="ranked-stock-returns"
    class="ranked-stock-returns"
    data-scale-max="${max}"
  >
    <div class="stock-axis-heading">
      <span>PUBLIC COMPANY / CURRENT SIZE</span>
      <div><span>−${max}%</span><strong>0%</strong><span>+${max}%</span></div>
    </div>
    ${rows
      .map((r) => {
        const valid = finite(r.ret.value),
          value = valid ? Number(r.ret.value) : null,
          direction = value > 0 ? "gain" : value < 0 ? "loss" : "flat",
          width = valid ? (Math.abs(value) / max) * 50 : 0;
        const groupLabel =
          state.groupSize && group !== r.sizeBand
            ? `<h3 class="stock-size-heading">${esc(stockSizeName(r.sizeBand))} companies</h3>`
            : "";
        group = r.sizeBand;
        return (
          groupLabel +
          `<article class="stock-return-row" data-stock-company="${esc(r.company.id)}" data-scale-max="${max}"${valid ? ` data-return="${value}"` : ""}><span class="stock-rank" title="Rank by return across selected companies">${valid ? returnsByRank.indexOf(value) + 1 : "—"}</span>${stockCompany(r)}${valid ? `<details class="stock-return-observation"><summary aria-label="${esc(r.company.name)}, ${stockSigned(value)}, ${esc(r.ret.start_session)} to ${esc(r.ret.end_session)}. Open closing prices and method." title="${esc(r.company.ticker)}: ${stockSigned(value)} · ${esc(r.ret.start_session)} to ${esc(r.ret.end_session)}"><span class="stock-return-lane"><span class="stock-return-domain"><span class="stock-zero-line"></span><span class="stock-guide stock-guide-left"></span><span class="stock-guide stock-guide-right"></span><span class="stock-return-bar stock-${direction}" data-value="${value}" style="${value < 0 ? "right" : "left"}:50%;width:${width}%"></span><span class="stock-return-value stock-value-${direction}" style="left:${50 + (value / max) * 50}%">${stockSigned(value)}</span>${value === 0 ? '<span class="stock-zero-point"></span>' : ""}</span></span><span class="stock-row-dates">${day(r.ret.start_session)} – ${day(r.ret.end_session)}<span>Details</span></span></summary>${stockReturnDetails(r)}</details>` : `<div class="stock-missing"><strong>Unavailable</strong><span>${esc(r.ret.reason)}</span></div>`}</article>`
        );
      })
      .join("")}
    <p class="stock-scale-note">
      One common linear return scale · bars are comparable across companies ·
      open any return for exact closes and dates. Size uses the dated
      capitalization snapshot, not size at the start of the return period.
    </p>
  </div>`;
}
function stockHero() {
  const titles = {
      "1w": "Neocloud stocks this week",
      "1m": "Neocloud stocks this month",
      "3m": "Neocloud stocks over three months",
      ytd: "Neocloud stocks year to date",
    },
    rows = stockRows();
  return /* HTML */ `<section id="stock-hero" class="stock-hero">
    <div class="stock-hero-heading">
      <div>
        <h1 id="page-title">${titles[stockWindow()]}</h1>

      </div>
      <a data-app class="stock-markets-link" href="${esc(href("markets"))}"
        >Explore Markets</a
      >
    </div>
    ${stockControls()}${stockStatus()}${stockPermitted()
      ? stockWindowCaption() + rankedStocks(rows)
      : stockBlocked()}
  </section>`;
}
function stockScatter(rows) {
  const usable = rows.filter(
    (r) =>
      finite(r.ret.value) &&
      ["verified", "dated_manual"].includes(r.market?.market_cap?.status) &&
      finite(r.market.market_cap.value) &&
      Number(r.market.market_cap.value) > 0,
  );
  if (!usable.length)
    return '<section id="market-scatter" class="market-empty">No verified capitalization/return pairs are available. An unresolved size does not remove a verified price return from the ranked chart.</section>';
  const logs = usable.map((r) => Math.log10(Number(r.market.market_cap.value))),
    lo = Math.floor(Math.min(...logs)),
    hi = Math.ceil(Math.max(...logs)) || lo + 1,
    span = hi - lo || 1,
    max = stockScale(usable);
  return /* HTML */ `<section id="market-scatter" class="market-scatter">
    <div class="stock-section-heading">
      <h2>Size vs return</h2>
      <span>Market cap · logarithmic scale</span>
    </div>
    <p class="stock-chart-note">
      Each point is a company. The horizontal axis is logarithmic; equal
      distances mean tenfold changes in capitalization. Association does not
      establish causation.
    </p>
    <div class="scatter-frame">
      <div class="scatter-y-labels">
        <span>+${max}%</span><strong>0%</strong><span>−${max}%</span>
      </div>
      <div class="scatter-plot">
        <span class="scatter-zero"></span>${Array.from(
          { length: Math.min(hi - lo + 1, 8) },
          (_, i) => lo + i,
        )
          .map(
            (tick) =>
              `<span class="scatter-grid" style="left:${((tick - lo) / span) * 100}%"><span>${money(10 ** tick)}</span></span>`,
          )
          .join("")}${usable
          .map((r, i) => {
            const cap = Number(r.market.market_cap.value),
              x = ((Math.log10(cap) - lo) / span) * 100,
              y = 50 + (Number(r.ret.value) / max) * 50;
            return /* HTML */ `<a
              data-app
              class="scatter-point scatter-label-${i % 2}"
              data-scatter-company="${esc(r.company.id)}"
              style="left:${x}%;bottom:${y}%"
              href="${esc(profile(r.company))}"
              title="${esc(r.company.name)} · ${money(
                cap,
                true,
              )} market cap · ${stockSigned(r.ret.value)}"
              aria-label="${esc(r.company.name)}, market cap ${money(
                cap,
                true,
              )}, return ${stockSigned(r.ret.value)}. Open profile."
              ><span></span><strong>${esc(r.company.ticker)}</strong></a
            >`;
          })
          .join("")}
      </div>
    </div>
    <p class="scatter-x-label">
      Current verified market capitalization (USD, log₁₀)
    </p>
    <div class="scatter-point-details">
      ${usable
        .map(
          (r) =>
            `<details><summary>${esc(r.company.ticker)} · ${stockSigned(r.ret.value)} · ${stockCap(r.market.market_cap.value)}</summary><p>${esc(r.company.name)} · market cap observed ${day(r.market.market_cap.as_of)}. Return ${day(r.ret.start_session)} to ${day(r.ret.end_session)}.</p><p>${esc(r.market.market_cap.share_basis || "Share-count basis not established.")}</p>${stockSource(r.market.market_cap.source_url, "Capitalization source")}<a data-app href="${esc(profile(r.company))}">Company profile</a></details>`,
        )
        .join("")}
    </div>
  </section>`;
}
function stockNormalized(rows) {
  const target =
      marketData?.windows?.[stockWindow()]?.start_session ||
      marketData?.windows?.[stockWindow()]?.target_start,
    end = marketData?.end_session;
  const candidates = rows
    .filter((r) => r.market && r.market.history_status !== "unavailable")
    .map((r) => {
      const history = list(r.market?.history)
        .filter((p) => p.date <= end && finite(p.close) && Number(p.close) > 0)
        .sort((a, b) => a.date.localeCompare(b.date));
      const last = history.find((p) => p.date === end);
      const segment = last?.segment;
      return {
        row: r,
        history: last
          ? history.filter((p) => p.date >= target && p.segment === segment)
          : [],
      };
    })
    .filter((v) => v.history.length);
  let common = candidates.length
    ? candidates[0].history.map((p) => p.date)
    : [];
  for (const c of candidates.slice(1)) {
    const dates = new Set(c.history.map((p) => p.date));
    common = common.filter((date) => dates.has(date));
  }
  if (common.length < 2 || common.at(-1) !== end)
    return /* HTML */ `<section id="normalized-prices" class="stock-normalized">
      <h2>Price paths, starting at 100</h2>
      <p class="market-empty">
        A common verified period is not available for the selected companies.
        Missing prices and corporate-action discontinuities are not bridged.
      </p>
    </section>`;
  const start = common[0],
    series = candidates.map((c) => {
      const lookup = new Map(c.history.map((p) => [p.date, p]));
      const initial = Number(lookup.get(start).close);
      return {
        row: c.row,
        points: common.map((date) => ({
          date,
          close: Number(lookup.get(date).close),
          value: (Number(lookup.get(date).close) / initial) * 100,
        })),
      };
    });
  const values = series.flatMap((s) => s.points.map((p) => p.value));
  let low = Math.floor(Math.min(100, ...values) / 10) * 10,
    high = Math.ceil(Math.max(100, ...values) / 10) * 10;
  if (high === low) {
    low -= 10;
    high += 10;
  }
  const span = high - low;
  const colors = [
    "#236c5c",
    "#557aa0",
    "#a37948",
    "#78629a",
    "#598384",
    "#9c6074",
    "#7a894b",
    "#b06f52",
    "#60778c",
  ];
  const W = 900,
    H = 220,
    left = 6,
    right = 894,
    top = 10,
    bottom = 205;
  const y = (v) => bottom - ((v - low) / span) * (bottom - top);
  return /* HTML */ `<section
    id="normalized-prices"
    class="stock-normalized"
    data-start-session="${esc(start)}"
    data-end-session="${esc(end)}"
  >
    <div class="stock-section-heading">
      <h2>Price paths, starting at 100</h2>
      <span>One common period · one common scale</span>
    </div>
    <p class="stock-chart-note">
      ${day(start)} –
      ${day(end)}${start !== target
        ? " · shortened to the common available verified history"
        : ""}.
      ${stockMethod()}. Each line starts at 100; no line crosses an unverified
      corporate-action boundary.
    </p>
    <div class="normalized-chart">
      <div class="normalized-y-labels">
        ${[high, ...(high !== 100 && low !== 100 ? [100] : []), low]
          .map(
            (value) =>
              `<span style="top:${(y(value) / H) * 100}%">${value}</span>`,
          )
          .join("")}
      </div>
      <svg
        viewBox="0 0 ${W} ${H}"
        preserveAspectRatio="none"
        role="img"
        aria-label="Normalized price histories from ${esc(start)} to ${esc(
          end,
        )}. Exact values are available in the company details below."
      >
        <path d="M${left} ${y(100)}H${right}" class="normalized-baseline" />
        ${series
          .map(
            (s, i) =>
              `<polyline data-normalized-company="${esc(s.row.company.id)}" data-start-session="${esc(start)}" data-end-session="${esc(end)}" fill="none" stroke="${colors[i % colors.length]}" vector-effect="non-scaling-stroke" points="${s.points.map((p, j) => (common.length === 1 ? 450 : left + (j / (common.length - 1)) * (right - left)).toFixed(2) + "," + y(p.value).toFixed(2)).join(" ")}"/>`,
          )
          .join("")}
      </svg>
    </div>
    <div class="normalized-dates">
      <time>${day(start)}</time><time>${day(end)}</time>
    </div>
    <div class="normalized-legend">
      ${series
        .map(
          (s, i) =>
            `<details class="normalized-series-details" data-history-company="${esc(s.row.company.id)}"><summary><span style="background:${colors[i % colors.length]}"></span><strong>${esc(s.row.company.ticker)}</strong><span>${s.points.at(-1).value.toFixed(2)}</span></summary><p>${esc(s.row.company.name)} · normalized to 100 at the ${day(start)} close.</p><div class="normalized-history-table"><table><thead><tr><th>Session</th><th>${marketData?.price_basis === "total_return" ? "Return index" : "Adjusted close"}</th><th>Normalized value</th></tr></thead><tbody>${s.points.map((p) => `<tr><td>${day(p.date)}</td><td>${stockSeriesValue(p.close, s.row.market.currency)}</td><td>${p.value.toFixed(4)}</td></tr>`).join("")}</tbody></table></div><a data-app href="${esc(profile(s.row.company))}">Company profile</a></details>`,
        )
        .join("")}
    </div>
    ${rows.length !== series.length
      ? `<p class="stock-chart-note">${rows.length - series.length} selected ${rows.length - series.length === 1 ? "company has" : "companies have"} insufficient verified common history and ${rows.length - series.length === 1 ? "is" : "are"} excluded from this chart; reasons remain in the market table.</p>`
      : ""}
  </section>`;
}
function marketQuoteCell(row) {
  const price = row.market?.price;
  if (stockPermitted() && price?.status === "available")
    return stockPrice(price.value, row.market.currency) + note(row.market.currency);
  return `<details><summary>Unavailable</summary><p>${esc(price?.reason || marketData.gap_reason || "No verified closing quote.")}</p></details>`;
}
function marketCapCell(row) {
  const cap = row.market?.market_cap;
  if (!finite(cap?.value)) return "Unavailable" + note(stockSizeName(row.sizeBand));
  return `<details><summary>${stockCap(cap.value)}</summary>
    <p>${esc(cap.share_basis || "Share-count basis unavailable.")}</p>
    ${cap.reason ? `<p>${esc(cap.reason)}</p>` : ""}${stockSource(cap.source_url, "Capitalization source")}
    </details>${note(stockSizeName(row.sizeBand))}${note(cap.as_of)}`;
}
function stockTable(rows) {
  return /* HTML */ `<section id="markets-table" class="markets-table-section">
    <div class="stock-section-heading">
      <h2>Market snapshot</h2>
      <span>Exact dates and missing reasons</span>
    </div>
    <div id="markets-control-slot"></div>
    <div
      class="table-wrap detail-table"
      tabindex="0"
      role="region"
      aria-label="Market snapshot table"
    >
      <table>
        <thead>
          <tr>
            <th>Company</th>
            <th>Closing price</th>
            <th>Market cap / size</th>
            ${[
              ["1w", "1W"],
              ["1m", "1M"],
              ["3m", "3M"],
              ["ytd", "YTD"],
            ]
              .map(([id, label]) => `<th>${label}</th>`)
              .join("")}
            <th>Observation</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (r) =>
                `<tr data-company="${esc(r.company.id)}"><td><a data-app class="company-name" href="${esc(profile(r.company))}">${esc(r.company.name)}</a><span class="ticker">${esc(r.company.ticker)}</span></td><td>${marketQuoteCell(r)}</td><td>${marketCapCell(r)}</td>${[
                  "1w",
                  "1m",
                  "3m",
                  "ytd",
                ]
                  .map((window) => {
                    const ret = r.market?.returns?.[window];
                    return /* HTML */ `<td>
                      ${stockPermitted() &&
                      ret?.status === "available" &&
                      ret.end_session === marketData.end_session &&
                      finite(ret.value)
                        ? stockSigned(ret.value)
                        : `<details><summary>Unavailable</summary><p>${esc(ret?.reason || marketData?.gap_reason || "Verified return not established.")}</p></details>`}
                    </td>`;
                  })
                  .join(
                    "",
                  )}<td>${day(r.market?.price?.date)}${note(r.market?.exchange)}${stockSource(r.market?.price?.source_url || marketData?.license?.source_url, "Price source")}</td></tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>
    <p class="stock-chart-note">
      Current market-cap bands: Large $10B+; Medium $2B–below $10B; Small
      $300M–below $2B; Micro below $300M. Unreconciled capitalizations retain
      Size unverified. Market observations do not update financial statement
      dates.
    </p>
  </section>`;
}
function marketsPage() {
  const rows = stockRows();
  return /* HTML */ `<section id="stock-hero" class="stock-hero markets-hero">
      <div class="stock-hero-heading">
        <div>
          <h1 id="page-title">Markets</h1>
          <p>
            Stock performance and company size, with the dates kept in view.
          </p>
        </div>
      </div>
      ${stockControls(true)}${stockStatus()}${stockPermitted()
        ? stockWindowCaption() +
          (state.marketView === "scatter"
            ? stockScatter(rows)
            : rankedStocks(rows))
        : stockBlocked()}
    </section>
    ${stockPermitted() ? stockNormalized(rows) : ""}${stockTable(rows)}`;
}
