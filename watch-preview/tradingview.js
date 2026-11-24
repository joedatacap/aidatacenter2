/* Approved branded TradingView embed. Widget data never enters the research ledger. */
const tradingViewLoaderURL = 'https://widgets.tradingview-widget.com/w/en/tv-market-data.js';
const tradingViewFocus = ['CRWV', 'NBIS', 'IREN', 'APLD', 'HUT', 'WULF', 'WYFI', 'SHAZ', 'AGPU'];
let tradingViewLoad;

function tradingViewCompanies() {
  const selected = new Map(visible.map(company => [company.ticker, company]));
  return tradingViewFocus.filter(ticker => selected.has(ticker)).map(ticker => selected.get(ticker));
}

function tradingViewSizeName(company) {
  const band = comparisonSize(company);
  return {large:'Large', mid:'Mid', small:'Small', micro:'Small'}[band] || 'Unavailable';
}

function sizeQualification(cap) {
  return cap?.qualification_label === 'Share basis unresolved' && cap.status === 'provider_reported'
    ? 'Provider-reported; share basis unresolved.' : cap?.qualification_label;
}

function sizeObservationDate(cap) {
  if (!cap?.as_of) return 'Date unavailable';
  const date = `<time datetime="${esc(cap.as_of)}">${day(cap.as_of)}</time>`;
  return cap.session_status === 'intraday' ? date + ' · US intraday' : date;
}

function marketSizeRow(company, cap, sharedDate) {
  const size = tradingViewSizeName(company);
  const source = safeURL(cap?.source_url) || sourceIds(cap).map(id => safeURL(sources.get(id)?.url)).find(Boolean);
  const amount = cap?.eligible ? money(cap.value) : 'Unavailable';
  const value = source && cap?.eligible
    ? `<a href="${esc(source)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(company.ticker)} market cap ${esc(amount)}, source observation">${amount}</a>`
    : esc(amount);
  return `<tr data-size-company="${esc(company.id)}" data-size-date="${esc(cap?.as_of)}">
    <th scope="row"><a data-app class="tradingview-company-link" href="${esc(profile(company))}">
      <strong>${esc(company.ticker)}</strong><span>${esc(company.name)}</span></a></th>
    <td><span class="tradingview-size-badge ${size.toLowerCase()}">${size}</span></td>
    <td class="tradingview-size-attribution">${value}
      ${sharedDate ? '' : `<small>${sizeObservationDate(cap)}</small>`}
      ${cap?.qualification_label ? `<small class="tradingview-size-qualification">${esc(sizeQualification(cap))}</small>` : ''}
    </td></tr>`;
}

function tradingViewSizeContext(companies) {
  if (!companies.length) return '';
  const caps = companies.map(displaySizeObservation);
  const first = caps[0];
  const sharedDate = first?.as_of && caps.every(cap => cap?.as_of === first.as_of && cap.session_status === first.session_status);
  const rows = companies.map((company, index) => marketSizeRow(company, caps[index], sharedDate));
  return `<section id="tradingview-size-context" class="tradingview-size-context" aria-labelledby="tradingview-size-title">
    <div class="tradingview-section-heading"><h2 id="tradingview-size-title">Company size</h2>
      <p id="tradingview-size-date">Stock Analysis · ${sharedDate ? sizeObservationDate(first) : 'Observation dates shown by company'}</p></div>
    <p id="tradingview-size-basis">Provider-reported market caps. TradingView updates performance separately.</p>
    <div class="market-size-frame"><table class="market-size-table" aria-labelledby="tradingview-size-title" aria-describedby="tradingview-size-date tradingview-size-basis">
      <thead><tr><th scope="col">Company</th><th scope="col">Size</th><th scope="col">Market cap (USD)</th></tr></thead>
      <tbody>${rows.join('')}</tbody></table></div>
    <details class="tradingview-size-method"><summary>Size thresholds &amp; sources</summary>
      <p>Small is below $2B, Mid is $2B to below $10B, and Large is $10B or more. Small includes micro-caps below $300M. Unknown values are unavailable.</p>
      <p>Select a market cap for its source or a company for share-class details and qualifications. Research debt ratios retain their original dates and inputs.</p>
    </details></section>`;
}

function tradingViewHero() {
  const companies = tradingViewCompanies(), symbols = companies.map(company => 'NASDAQ:'+company.ticker);
  const homepage = state.page === 'overview';
  const title = homepage ? '<h2 id="performance-title">Neocloud stock performance</h2>' : '<h1 id="page-title">Neocloud stock performance</h1>';
  return `<section id="tradingview-performance" class="tradingview-performance" aria-labelledby="${homepage ? 'performance-title' : 'page-title'}">
    <div class="tradingview-heading"><div>${title}<p id="tradingview-guide">Compare monthly performance in the <strong>1M</strong> column. <span class="tradingview-mobile-guide">Swipe table to see 1M →</span></p></div>${homepage ? '' : '<div id="tradingview-peer-slot"></div>'}</div>
    ${symbols.length ? '<p class="tradingview-coverage-note" id="widget-timing">TradingView supplies market timing for each listing. Its D marker indicates delayed quotes.</p>' : ''}
    ${symbols.length ? `<div id="tradingview-widget-shell" class="tradingview-widget-shell"><p id="tradingview-status" class="tradingview-status" role="status">Loading TradingView’s market widget…</p><div id="tradingview-fallback" class="tradingview-fallback" hidden><p>TradingView could not load. Check your connection, then retry the widget. The research pages remain available.</p><button type="button" data-retry-tradingview>Retry TradingView</button></div><tv-market-data id="tradingview-market-data" symbol-sectors="${esc(JSON.stringify([{sectionName:'Focus companies',symbols}]))}" view="performance"></tv-market-data><noscript>Enable JavaScript to display TradingView’s market widget.</noscript></div>` : '<p class="empty-panel">No focus companies match the current research selection. Choose a focus company to display TradingView’s performance widget.</p>'}
    ${visible.length !== companies.length ? '<p class="tradingview-coverage-note">The verified widget covers the nine focus symbols. Other company records remain available in the research comparison and company briefs.</p>' : ''}
    ${tradingViewSizeContext(companies)}
  </section>`;
}

function tradingViewMarketsPage() {
  return tradingViewHero()+`<section class="tradingview-research-links" aria-label="Continue company research"><h2>Continue the research</h2><p>Peer selections travel with you. Widget market data and Neocloud Watch’s dated financial research remain separate.</p><div><a data-app href="${esc(href('earnings'))}">Earnings</a><a data-app href="${esc(href('financing'))}">Financing & debt</a><a data-app href="${esc(href('buildout'))}">Buildout</a></div></section>`;
}

function mountTradingViewWidget() {
  const widget = $('tradingview-market-data');
  if (!widget) return;
  const setFallback = message => {
    if (!widget.isConnected) return;
    const status = $('tradingview-status');
    if (status) {status.hidden = true; status.textContent = '';}
    const fallback = $('tradingview-fallback');
    if (fallback) {
      fallback.hidden = false;
      fallback.querySelector('p').textContent = message;
      fallback.querySelector('[data-retry-tradingview]').onclick = () => {
        tradingViewLoad = null;
        fallback.hidden = true;
        mountTradingViewWidget();
      };
    }
  };
  if (!navigator.onLine) {
    setFallback('An internet connection is required for TradingView. The downloaded financial research and company pages still work offline.');
    return;
  }
  const status = $('tradingview-status');
  if (status) {status.hidden = false; status.textContent = 'Loading TradingView’s market widget…';}
  if (!tradingViewLoad) tradingViewLoad = new Promise((resolve, reject) => {
    if (customElements.get('tv-market-data')) {resolve(); return;}
    const script = document.createElement('script');
    script.type = 'module';
    script.src = tradingViewLoaderURL;
    script.dataset.tradingviewLoader = 'true';
    script.addEventListener('error', () => {script.remove(); reject(new Error('TradingView module unavailable'));}, {once:true});
    script.addEventListener('load', () => {
      if (customElements.get('tv-market-data')) resolve();
      else reject(new Error('TradingView component unavailable'));
    }, {once:true});
    document.head.append(script);
  });
  tradingViewLoad.then(() => {
    if (!widget.isConnected) return;
    const loading = $('tradingview-status');
    if (loading) loading.hidden = true;
    const fallback = $('tradingview-fallback');
    if (fallback) fallback.hidden = true;
  }).catch(() => setFallback('TradingView could not load. Check your connection, then retry the widget. The research pages remain available.'));
}
