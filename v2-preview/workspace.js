/* Dated evidence renderer. Financial calculations remain in the Python exporter. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const groups = {gpu_cloud:'GPU cloud', ai_transition:'AI infrastructure / mixed', bitcoin_mining:'Bitcoin mining', data_center_reit:'Data-center REIT'};
  const money = value => {
    if (value == null) return 'Not established';
    const n = Number(value);
    if (!Number.isFinite(n)) return 'Not established';
    const scale = Math.abs(n) >= 1e9 ? 1e9 : Math.abs(n) >= 1e6 ? 1e6 : 1;
    return '$' + (n / scale).toLocaleString('en-US', {maximumFractionDigits:scale === 1 ? 0 : 2}) + (scale === 1e9 ? 'B' : scale === 1e6 ? 'M' : '');
  };
  const exact = value => value == null ? 'Not established' : '$' + Number(value).toLocaleString('en-US', {maximumFractionDigits:2});
  const date = value => value ? esc(value) : 'Date not established';
  const words = value => esc(String(value || 'Not established').replaceAll('_', ' '));
  const fact = (label, value) => `<dl><dt>${esc(label)}</dt><dd>${value}</dd></dl>`;
  let data, sources, selected;

  function evidence(ids = []) {
    const unique = [...new Set(ids)].map(id => sources.get(id)).filter(Boolean);
    if (!unique.length) return '<p class="unknown">No linked source in this record.</p>';
    return `<details class="evidence"><summary>Sources & excerpts (${unique.length})</summary>${unique.map(s => {
      let url;
      try { const u = new URL(s.url); url = ['http:', 'https:'].includes(u.protocol) ? u.href : null; } catch { url = null; }
      return `<div class="source">${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a>` : esc(s.title)}<p>Published ${date(s.published_at)} · ${esc(s.source_unit || 'See source for units')}</p><blockquote>${esc(s.excerpt || 'Open the source document for the full disclosure.')}</blockquote></div>`;
    }).join('')}</details>`;
  }

  function renderUniverse() {
    const query = $('search').value.trim().toLowerCase();
    const group = $('group').value, listing = $('listing').value, order = $('order').value;
    let companies = data.companies.filter(c =>
      (!query || `${c.name} ${c.ticker}`.toLowerCase().includes(query)) &&
      (group === 'all' || c.group === group) &&
      (listing === 'all' || (listing === 'listed' ? c.listing_status === 'listed' : c.listing_status !== 'listed')));
    companies.sort((a, b) => {
      if (order === 'name') return a.name.localeCompare(b.name);
      const field = order.startsWith('cash') ? 'cash' : 'debt';
      const av = a.metrics[field]?.value, bv = b.metrics[field]?.value;
      if (av == null || bv == null) return av == null && bv == null ? a.name.localeCompare(b.name) : av == null ? 1 : -1;
      return (Number(av) - Number(bv)) * (order.endsWith('asc') ? 1 : -1) || a.name.localeCompare(b.name);
    });
    $('count').textContent = `${companies.length} of ${data.companies.length} records`;
    $('empty').hidden = companies.length > 0;
    $('company-rows').innerHTML = companies.map(c => `<tr>
      <td><a class="company-name" href="#company=${encodeURIComponent(c.ticker)}">${esc(c.name)}</a><span class="ticker">${esc(c.ticker)}</span><span class="business">${esc(groups[c.group])}</span>${c.listing_status !== 'listed' ? '<span class="cell-note">Private reference · listing not verified</span>' : ''}</td>
      <td><span class="${c.metrics.debt.value == null ? 'unknown' : 'number'}">${money(c.metrics.debt.value)}</span><span class="cell-note">Carrying value · leases excluded</span></td>
      <td><span class="number">${money(c.metrics.cash?.value)}</span><span class="cell-note">Group cash · access restrictions apply</span></td>
      <td><span class="unknown">${c.listing_status === 'listed' ? 'Not researched' : 'Not applicable'}</span><span class="cell-note">${c.listing_status === 'listed' ? 'Dated equity value needed' : 'No verified listed equity'}</span></td>
      <td><span class="unknown">Not calculated</span></td><td>${date(c.as_of)}</td>
      <td><a class="open-link" href="#company=${encodeURIComponent(c.ticker)}" aria-label="Open ${esc(c.name)} financing brief">Brief ↗</a></td></tr>`).join('');
  }

  function metric(label, value, note) {
    return `<div class="metric"><span class="label">${esc(label)}</span><strong>${value}</strong><p>${note}</p></div>`;
  }

  function renderCompany(c) {
    const debt = c.metrics.debt, cash = c.metrics.cash, context = c.debt_context || {}, liquidity = c.liquidity || {};
    const rates = data.financing_rates.filter(r => r.ticker === c.ticker);
    const notes = data.instruments.filter(r => r.ticker === c.ticker);
    const bridges = context.bridges || [];
    $('company').innerHTML = `<a class="back" href="#">← Company universe</a>
      <div class="page-heading"><div><p class="eyebrow">${esc(c.ticker)} / COMPANY BRIEF</p><h1 tabindex="-1" id="brief-title">${esc(c.name)}</h1><p class="intro">${esc(c.business)}</p></div><div class="review-date">FINANCIAL SNAPSHOT<strong>${date(c.as_of)}</strong><span>Published ${date(c.filed_at)}</span></div></div>
      <span class="badge">${esc(groups[c.group])}</span><span class="badge">${c.listing_status === 'listed' ? 'Public at ledger review' : 'Private reference / IPO applicant'}</span><span class="badge">${esc(c.scope || 'Scope in source records')}</span>
      <div class="brief-summary">${metric('Reported borrowings', money(debt.value), 'Carrying value · excludes leases')}${metric('Reported group cash', money(cash?.value), 'Availability to parent not established')}${metric('Market capitalization', '—', c.listing_status === 'listed' ? 'Needs a verified equity snapshot' : 'No verified public listing')}${metric('Debt / market cap', '—', 'Not calculated without a denominator')}</div>
      <div class="scope-note"><strong>What matters in this snapshot</strong>${esc(liquidity.takeaway || c.notes?.[0] || 'Review borrower scope and restrictions before comparing amounts.')}</div>
      <nav class="brief-nav" aria-label="Brief sections"><a href="#financing" data-section="financing">Debt structure</a><a href="#rates" data-section="rates">Rates & notes</a><a href="#cash" data-section="cash">Cash & facilities</a><a href="#valuation" data-section="valuation">Valuation</a><a href="#operations" data-section="operations">Customers & infrastructure</a></nav>
      <section id="financing" class="brief-section"><p class="eyebrow">01 / OBLIGATIONS</p><h2>Who owes what?</h2><p class="section-lead">Reported borrowing components preserve the issuer’s categories. They do not establish a complete instrument-level debt stack.</p>
      <div class="card"><h3>Reported borrowing balance</h3><div class="fact-grid">${fact('Carrying value', exact(debt.value))}${fact('Basis', esc(debt.basis))}${fact('As of', date(debt.as_of || c.as_of))}</div>${(debt.components || []).map(x => `<p>${esc(x.label)} <strong>${x.operation === 'subtract' ? '− ' : ''}${exact(x.value)}</strong></p>`).join('')}<p>${esc(debt.note)}</p>${evidence(debt.source_ids)}</div>
      ${bridges.map(b => `<div class="card"><h3>${esc(b.label)}</h3><div class="fact-grid">${fact('Principal', exact(b.principal))}${fact('Carrying value', exact(b.carrying))}${fact('Scope / date', `${words(b.scope)} · ${date(b.as_of)}`)}</div><p class="status-note">${b.complete_company_scope ? 'Source supports this company-scope reconciliation.' : 'Partial or carrying-only disclosure; no complete principal total inferred.'}</p><p>${esc(b.note)}</p>${evidence(b.source_ids)}</div>`).join('')}
      <h3>Leases outside the borrowing total</h3>${(context.leases || []).length ? context.leases.map(l => `<div class="card"><div class="fact-grid">${fact('Lease type', words(l.kind))}${fact('Reported liability', exact(l.value))}${fact('Date', date(l.as_of))}</div><p>${esc(l.note)}</p>${evidence(l.source_ids)}</div>`).join('') : '<p class="unknown">Lease balances are not established in the available records. This does not mean zero lease obligations.</p>'}
      ${(context.notes || []).map(n => `<p class="section-lead">${esc(n)}</p>`).join('')}</section>
      <section id="rates" class="brief-section"><p class="eyebrow">02 / TERMS & TIMING</p><h2>What does financing cost?</h2><p class="section-lead">These are selected, dated references. No company-wide average or current borrowing cost is inferred. A coupon is not a market yield.</p>
      ${rates.length ? rates.map(r => `<div class="card"><h3>${esc(r.instrument)}</h3><span class="badge">${words(r.kind)}</span><div class="fact-grid">${fact('Disclosed rate / formula', r.rate_percent != null ? esc(r.rate_percent) + '%' : esc(r.formula || 'Not established'))}${fact('Borrower', esc(r.borrower))}${fact('Terms as of', date(r.as_of))}</div><p>${esc(r.scope)}</p><p>${esc(r.coverage)}</p><p>${esc(r.note)}</p>${evidence(r.source_ids)}</div>`).join('') : '<p class="unknown">No verified financing-rate references in this ledger.</p>'}
      <h3>Named note examples & contractual maturity</h3><p class="section-lead">Historical examples may no longer be outstanding. Dates below are not a company maturity wall; amounts are never summed across snapshots.</p>
      ${notes.map(n => `<div class="card"><h3>${esc(n.instrument)}</h3><span class="badge">${words(n.type)}</span><div class="fact-grid">${fact('Cash coupon', n.value == null ? 'Not established' : esc(n.value) + '%')}${fact('Issuer', esc(n.issuer))}${fact('Contractual maturity', `${date(n.maturity)} (${words(n.maturity_precision)})`)}${fact('Observed principal', exact(n.outstanding_principal?.value))}${fact('Principal observation date', date(n.outstanding_principal?.as_of))}${fact('Outstanding evidence', words(n.outstanding_status))}</div><p class="status-note">${esc(n.note || 'Read the source dates and outstanding-status evidence.')}</p><p>${esc(n.scope)}</p>${evidence([...(n.source_ids || []), ...(n.outstanding_evidence_ids || [])])}</div>`).join('') || '<p class="unknown">No named notes in this record. Other financing may exist.</p>'}</section>
      <section id="cash" class="brief-section"><p class="eyebrow">03 / ACCESS TO FUNDS</p><h2>Cash is only part of the picture.</h2><div class="card"><h3>Reported cash & equivalents · ${money(cash?.value)}</h3><p>${esc(liquidity.cash_caveat || cash?.basis)}</p>${evidence(cash?.source_ids)}<p><strong>Company-wide available credit: not established.</strong> Selected commitments and conditional capacity cannot be added to group cash.</p></div>
      ${(liquidity.excluded_balances || []).map(b => `<div class="card"><h3>${esc(b.label)} · ${money(b.value)}</h3><p>${date(b.as_of)} · ${esc(b.basis)}</p>${evidence(b.source_ids)}</div>`).join('')}
      ${(liquidity.facilities || []).map(f => `<div class="card"><h3>${esc(f.name)}</h3><p>${esc(f.borrower)} · ${date(f.as_of)}</p><p>${esc(f.scope)}</p><div class="fact-grid">${(f.amounts || []).map(a => fact(a.label, `${exact(a.value)}<span class="cell-note">${date(a.as_of)} · ${esc(a.kind)}</span>`)).join('')}</div><p class="status-note">${esc(f.access_note)}</p>${(f.conditions || []).map(n => `<p>${esc(n)}</p>`).join('')}${evidence([...(f.source_ids || []), ...(f.amounts || []).flatMap(a => a.source_ids || [])])}</div>`).join('')}
      ${(liquidity.notes || []).map(n => `<p class="section-lead">${esc(n)}</p>`).join('')}</section>
      <section id="valuation" class="brief-section"><p class="eyebrow">04 / SHAREHOLDER CONTEXT</p><h2>Debt relative to equity value.</h2><div class="empty-panel"><h3>${c.listing_status === 'listed' ? 'Market-cap research pending' : 'Public-market valuation not applicable to this record'}</h3><p>Debt / market cap = reported borrowing carrying value ÷ dated equity market capitalization. Both dates, currency and the equity source will be shown. A stock-price move changes this ratio without changing the debt.</p><p>No verified market-cap observation is loaded. Private funding-round valuations will not substitute for public equity value.</p></div></section>
      <section id="operations" class="brief-section"><p class="eyebrow">05 / REVENUE FOUNDATIONS</p><h2>Customers, capacity & hardware.</h2><div class="coverage-grid"><article class="empty-panel"><h3>Customers & contracts</h3><p>Research pending: major customers, revenue concentration, contract term, termination conditions and guarantee scope. A contract’s face value is not cash in the bank.</p></article><article class="empty-panel"><h3>Revenue-producing capacity</h3><p>Research pending: operating, contracted, construction and announced capacity, with units and dates. Operating capacity does not establish utilization.</p></article><article class="empty-panel"><h3>GPU fleet</h3><p>Research pending: disclosed GPU generations, owned versus leased equipment and refresh obligations. A named deployment is not a full fleet inventory.</p></article></div></section>`;
    $('company').querySelectorAll('[data-section]').forEach(a => a.addEventListener('click', event => {
      event.preventDefault(); $(a.dataset.section).scrollIntoView({behavior:'smooth'});
    }));
  }

  function route() {
    const ticker = new URLSearchParams(location.hash.slice(1)).get('company');
    const c = data.companies.find(item => item.ticker === ticker);
    $('universe').hidden = Boolean(c); $('company').hidden = !c;
    if (c) { renderCompany(c); $('brief-title').focus({preventScroll:true}); window.scrollTo(0, 0); }
    else { renderUniverse(); if (selected) { const link = [...$('company-rows').querySelectorAll('.company-name')].find(a => a.hash === `#company=${selected}`); (link || $('search')).focus(); } }
    selected = c?.ticker;
  }

  async function init() {
    try {
      const embedded = $('workspace-data');
      if (embedded) data = JSON.parse(embedded.textContent);
      else { const response = await fetch('./data.json'); if (!response.ok) throw new Error('data'); data = await response.json(); }
      sources = new Map(data.sources.map(s => [s.id, s]));
      $('reviewed').textContent = data.reviewed_at;
      ['search', 'group', 'listing', 'order'].forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change', renderUniverse));
      $('reset').addEventListener('click', () => { $('search').value = ''; $('group').value = 'all'; $('listing').value = 'listed'; $('order').value = 'name'; renderUniverse(); });
      window.addEventListener('hashchange', route); route();
    } catch {
      $('error').hidden = false;
      $('error').textContent = 'The evidence ledger could not be loaded. Use the standalone V2 HTML preview, or build and serve the workspace with npm run preview:v2.';
    }
  }
  init();
})();
