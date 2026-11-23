/* Approved branded TradingView embed. Widget data never enters the research ledger. */
const tradingViewLoaderURL = 'https://widgets.tradingview-widget.com/w/en/tv-market-data.js';
const tradingViewFocus = ['CRWV', 'NBIS', 'IREN', 'APLD', 'HUT', 'WULF', 'WYFI', 'SHAZ', 'AGPU'];
let tradingViewLoad;

function tradingViewCompanies() {
  const selected = new Map(visible.map(company => [company.ticker, company]));
  return tradingViewFocus.filter(ticker => selected.has(ticker)).map(ticker => selected.get(ticker));
}

function tradingViewSizeName(company) {
  const cap = market(company);
  if (!cap || cap.ratio_blocker || !finite(cap.value)) return 'Size unverified';
  return {large:'Large',mid:'Medium',small:'Small',micro:'Micro'}[comparisonSize(company)] || 'Size unverified';
}

function tradingViewSizeContext(companies) {
  if (!companies.length) return '';
  const dates = [...new Set(companies.map(company => market(company)?.as_of).filter(Boolean))];
  return `<section id="tradingview-size-context" class="tradingview-size-context" aria-labelledby="tradingview-size-title">
    <div class="tradingview-section-heading"><h2 id="tradingview-size-title">Company size</h2><span>Neocloud Watch research</span></div>
    <p>USD market caps ${dates.length === 1 ? 'as of <time datetime="'+esc(dates[0])+'">'+day(dates[0])+'</time>' : 'retain their individual observation dates'}. These dated research snapshots are separate from TradingView’s market data. Select a ticker for its capitalization source.</p>
    <ul class="tradingview-size-list">${companies.map(company => {
      const cap = market(company), size = tradingViewSizeName(company), known = size !== 'Size unverified';
      const source = sourceIds(cap).map(id => sources.get(id)).find(record => safeURL(record?.url));
      return `<li data-size-company="${esc(company.id)}"><div class="tradingview-size-value">${source ? '<a href="'+esc(safeURL(source.url))+'" target="_blank" rel="noopener noreferrer" aria-label="'+esc(company.ticker)+' capitalization source">'+esc(company.ticker)+'</a>' : '<span>'+esc(company.ticker)+'</span>'}${known ? '<span class="tradingview-cap">'+money(cap.value)+'</span>' : ''}<span class="tradingview-size-badge ${known ? esc(comparisonSize(company)) : 'unknown'}">${esc(size)}</span></div>${dates.length !== 1 && cap?.as_of ? '<time datetime="'+esc(cap.as_of)+'">'+day(cap.as_of)+'</time>' : ''}<a data-app class="tradingview-company-link" href="${esc(profile(company))}">Company brief</a>${!known && cap?.ratio_blocker ? '<details class="tradingview-size-note"><summary>Why size is unverified</summary><p>'+esc(cap.ratio_blocker)+'</p>'+evidence(sourceIds(cap))+'</details>' : ''}</li>`;
    }).join('')}</ul>
    <details class="tradingview-size-method"><summary>Size definitions & dated evidence</summary><p>Large: $10B+; Medium: $2B to below $10B; Small: $300M to below $2B; Micro: below $300M. These are market-cap categories, not the manually selected research groups. Unresolved capitalization stays unverified; a provider value alone does not resolve share-count or capital-structure blockers.</p><p>The official widget supplies its own attribution, market timestamps, performance periods and controls. Widget values are not copied into Neocloud Watch CSV or evidence exports.</p></details>
  </section>`;
}

function tradingViewHero() {
  const companies = tradingViewCompanies(), symbols = companies.map(company => 'NASDAQ:'+company.ticker);
  return `<section id="tradingview-performance" class="tradingview-performance" aria-labelledby="page-title">
    <div class="tradingview-heading"><div><h1 id="page-title">Neocloud stock performance</h1><p id="tradingview-guide">Compare monthly performance in the <strong>1M</strong> column. <span class="tradingview-mobile-guide">Swipe table to see 1M →</span></p></div><div id="tradingview-peer-slot"></div></div>
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
