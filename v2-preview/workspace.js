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
  let data, sources, selected, visibleCompanies = [], activeView = 'financing', sectionObserver;

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
    const group = $('group').value, listing = $('listing').value, order = $('order').value, size = $('size').value;
    let companies = data.companies.filter(c =>
      (!query || `${c.name} ${c.ticker}`.toLowerCase().includes(query)) &&
      (group === 'all' || c.group === group) && (size === 'all' || c.v2.size_band === size) &&
      (listing === 'all' || (listing === 'listed' ? c.listing_status === 'listed' : c.listing_status !== 'listed')));
    companies.sort((a, b) => {
      if (order === 'name') return a.name.localeCompare(b.name);
      const field = order.startsWith('cash') ? 'cash' : 'debt';
      const value = c => order.startsWith('market') ? c.v2.market_cap?.value : order.startsWith('ratio') ? c.v2.debt_market_cap_percent : c.metrics[field]?.value;
      const av = value(a), bv = value(b);
      if (av == null || bv == null) return av == null && bv == null ? a.name.localeCompare(b.name) : av == null ? 1 : -1;
      return (Number(av) - Number(bv)) * (order.endsWith('asc') ? 1 : -1) || a.name.localeCompare(b.name);
    });
    const filterCount = [group !== 'all', listing !== 'listed', order !== 'name', size !== 'all'].filter(Boolean).length;
    $('filter-count').textContent = filterCount ? `· ${filterCount} changed` : '';
    $('count').textContent = `${companies.length} of ${data.companies.length} records`;
    $('empty').hidden = companies.length > 0;
    visibleCompanies = companies;
    const operating = activeView === 'operations', repayments = activeView === 'repayments';
    document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === activeView)));
    $('view-description').textContent = repayments ? 'When does principal come due? Read annual buckets alongside their fiscal or calendar basis.' : operating ? 'What supports the business? Separate operating assets from contracted and announced capacity.' : 'Compare the balance sheet with the equity market.';
    const headings = repayments ? ['Company','Reported principal total','First reporting period','Next reporting period','Reporting calendar & scope','Evidence gaps'] : operating ? ['Company','Customers & contracts','Capacity status','GPU disclosures','Research scope'] : ['Company','Borrowings','Reported cash','Market cap','Debt / market cap','Statement date'];
    $('column-headings').innerHTML = '<tr>' + headings.map(h=>`<th scope="col">${esc(h)}</th>`).join('') + '</tr>';
    const cell = (label, html) => `<td data-label="${esc(label)}">${html}</td>`;
    const snippets = records => records.length ? records.slice(0,2).map(f=>`<strong>${esc(f.display)}</strong><span class="cell-note">${esc(f.label)} · ${words(f.status)} · ${date(f.as_of)}</span>`).join('<br>') : '<span class="unknown">Research gap</span>';
    $('company-rows').innerHTML = companies.map(c => {
      const x=c.v2, m=x.market_cap, ratio=x.debt_market_cap_percent;
      const name=`<a class="company-name" href="#company=${encodeURIComponent(c.ticker)}">${esc(c.name)}</a><span class="ticker">${esc(c.ticker)}</span><span class="business">${esc(groups[c.group])}</span><span class="cell-note">${m ? words(x.size_band)+' equity cap' : 'Private reference · IPO applicant'}</span>`;
      const schedule=x.maturity_schedule;
      const period=b=>b ? `<strong>${money(b.value)}</strong><span class="cell-note">${esc(b.label)}</span>` : '<span class="unknown">Not established</span>';
      return '<tr class="'+(operating ? 'operating-row' : repayments ? 'repayment-row' : 'financing-row')+'">'+cell('Company',name)+(repayments ?
        cell(headings[1],schedule ? `<strong>${money(schedule.total)}</strong><span class="cell-note">As of ${date(schedule.as_of)} · leases excluded</span>` : 'Not established')+
        cell(headings[2],period(schedule?.buckets[0]))+cell(headings[3],period(schedule?.buckets[1]))+
        cell(headings[4],schedule ? `${words(schedule.period_basis)} year · ends ${esc(schedule.year_end)}<span class="cell-note">${esc(schedule.scope)}</span>` : '<span class="unknown">Research gap</span>')+
        cell(headings[5],`<a href="#company=${encodeURIComponent(c.ticker)}">Open repayment evidence</a><span class="cell-note">${esc(schedule?.timing_issue || (schedule ? 'Annual buckets; no rolling totals inferred' : 'No verified repayment schedule'))}</span>`) : operating ?
        cell(headings[1],snippets(x.contracts))+cell(headings[2],snippets(x.capacity))+cell(headings[3],snippets(x.hardware))+cell(headings[4],`<a href="#company=${encodeURIComponent(c.ticker)}">Open sourced brief</a><span class="cell-note">${x.context_coverage}/4 context areas sourced; coverage is partial</span>`) :
        cell(headings[1],`<span class="number">${money(c.metrics.debt.value)}</span><span class="cell-note">Carrying value · leases excluded</span>`)+
        cell(headings[2],`<span class="number">${money(c.metrics.cash?.value)}</span><span class="cell-note">Group cash; access restrictions apply</span>`)+
        cell(headings[3],`<span class="number">${m ? money(m.value) : 'Not applicable'}</span><span class="cell-note">${m ? date(m.as_of)+' · provider reported' : 'No public equity snapshot'}</span>`)+
        cell(headings[4],`<span class="number">${ratio == null ? 'Not calculated' : ratio.toFixed(1)+'%'}</span><span class="cell-note">${x.market_cap?.ratio_blocker ? 'Share-count reconciliation pending' : ratio == null ? 'Missing eligible inputs' : 'Indicative · dates differ'}</span>`)+
        cell(headings[5],`${date(c.as_of)}<span class="cell-note">${x.financial_age_days} days before review</span>`))+'</tr>';
    }).join('');
  }

  function metric(label, value, note) {
    return `<div class="metric"><span class="label">${esc(label)}</span><strong>${value}</strong><p>${note}</p></div>`;
  }

  function renderCompany(c) {
    const debt = c.metrics.debt, cash = c.metrics.cash, context = c.debt_context || {}, liquidity = c.v2.snapshot ? {...c.liquidity, takeaway:c.v2.snapshot.note, cash_caveat:'Updated group cash snapshot; parent availability is not established. Facility references below retain their individual historical dates.'} : c.liquidity || {};
    const rates = data.financing_rates.filter(r => r.ticker === c.ticker);
    const notes = data.instruments.filter(r => r.ticker === c.ticker);
    const bridges = context.bridges || [];
    $('company').innerHTML = `<a class="back" href="#">← Company universe</a><button class="text-button print-button" type="button" id="print-brief">Print / save PDF</button>
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
    enrichBrief(c);
    $('company').querySelectorAll('.brief-section h2').forEach(heading => heading.tabIndex = -1);
    $('print-brief').addEventListener('click',()=>window.print());
    const sectionLinks = [...$('company').querySelectorAll('[data-section]')];
    sectionObserver = new IntersectionObserver(entries => {
      const visible = entries.filter(entry => entry.isIntersecting).sort((a,b) => a.boundingClientRect.top-b.boundingClientRect.top);
      if (!visible.length) return;
      sectionLinks.forEach(link => {
        if (link.dataset.section === visible[0].target.id) link.setAttribute('aria-current','location');
        else link.removeAttribute('aria-current');
      });
    }, {rootMargin:'-80px 0px -55% 0px', threshold:0});
    $('company').querySelectorAll('.brief-section').forEach(section => sectionObserver.observe(section));
    sectionLinks.forEach(a => a.addEventListener('click', event => {
      event.preventDefault(); $(a.dataset.section).scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
      $(a.dataset.section).querySelector('h2').focus({preventScroll:true});
    }));
  }

  function factCards(records, empty='Research gap: no verified disclosure loaded for this field.') {
    return records.length ? records.map(f=>`<article class="card"><span class="badge">${words(f.status)}</span><h3>${esc(f.label)} · ${esc(f.display)}</h3><p>${esc(f.scope)} · ${date(f.as_of)}</p><p>${esc(f.note)}</p>${evidence(f.source_ids)}</article>`).join('') : `<p class="empty-panel">${esc(empty)}</p>`;
  }

  function enrichBrief(c) {
    const x=c.v2,m=x.market_cap,ratio=x.debt_market_cap_percent;
    $('company').querySelector('.brief-summary').innerHTML = metric('Reported borrowings',money(c.metrics.debt.value),date(c.as_of)+' · leases excluded')+metric('Reported group cash',money(c.metrics.cash?.value),date(c.as_of)+' · access restrictions apply')+metric('Market cap',m ? money(m.value) : '—',m ? date(m.as_of)+' · provider reported' : 'No public equity snapshot')+metric('Debt / market cap',ratio==null ? '—' : ratio.toFixed(1)+'%',ratio==null ? 'Eligible denominator not established' : 'Indicative · different observation dates');
    $('valuation').innerHTML=`<p class="eyebrow">04 / SHAREHOLDER CONTEXT</p><h2>Debt relative to equity value.</h2>${m ? `<div class="card"><div class="fact-grid">${fact('Provider market cap',money(m.value))}${fact('Equity observation',date(m.as_of)+' · time precision: day')}${fact('Debt observation',date(c.as_of))}${fact('Borrowings / market cap',ratio==null ? 'Withheld' : ratio.toFixed(1)+'%')}</div><p>${esc(m.scope)}</p><p>${esc(m.note)}</p>${m.ratio_blocker ? `<p class="status-note">${esc(m.ratio_blocker)}</p>` : ''}${evidence(m.source_ids)}${evidence(c.metrics.debt.source_ids)}</div>` : '<p class="empty-panel">Public-market valuation not applicable to this record. Private funding-round values are not substituted.</p>'}<p class="section-lead">Formula: reported borrowing carrying value ÷ provider-reported equity capitalization × 100. Leases excluded. This is not enterprise value, book leverage, repayment capacity or default risk. A stock-price move changes the ratio without changing debt. No later financing is silently added to the statement balance.</p><h3>Revenue context</h3>${factCards(x.revenue)}`;
    $('operations').innerHTML=`<p class="eyebrow">05 / REVENUE FOUNDATIONS</p><h2>Customers, capacity & hardware.</h2><p class="section-lead">${esc(x.coverage_note)} Contracted and announced capacity must not be summed with operating capacity. Named hardware does not establish a fleet-wide mix.</p><h3>Customer concentration & contract conditions</h3>${factCards(x.contracts)}<h3>Capacity and delivery status</h3>${factCards(x.capacity)}<h3>GPU generations & equipment scope</h3>${factCards(x.hardware)}`;
    if(x.events.length) $('valuation').insertAdjacentHTML('beforeend','<h3>Listing & later events</h3>'+factCards(x.events));
    const inventory=x.debt_inventory;
    const schedule=x.maturity_schedule;
    $('financing').querySelector('.card').insertAdjacentHTML('afterend',`<h3>Scheduled principal repayments</h3>${schedule ? `<div class="card"><p><strong>${words(schedule.period_basis)} year · ends ${esc(schedule.year_end)}</strong></p>${schedule.timing_issue ? `<p class="status-note">${esc(schedule.timing_issue)}</p>` : ''}<p>${esc(schedule.scope)} As of ${date(schedule.as_of)}.</p><div class="maturity-chart">${schedule.buckets.map(b=>`<div class="maturity-row"><span>${esc(b.label)}</span><div class="bar-track"><div class="bar" style="width:${100*b.value/Math.max(...schedule.buckets.map(v=>v.value))}%"></div></div><strong>${money(b.value)}</strong></div>`).join('')}</div><p>Total principal: ${exact(schedule.total)}. ${esc(schedule.note)}</p>${evidence(schedule.source_ids)}</div>` : '<p class="empty-panel">Insufficient schedule coverage for 12/24/36-month totals. Unknown is not zero. Historical note maturities are not aggregated into repayments.</p>'}<h3>Current disclosed instrument inventory</h3>${inventory.length ? `<p class="section-lead">${c.ticker==='CRWV' ? 'Note 10 principal rows, including aggregated OEM/software financing. USD equivalent for EUR notes.' : 'Selected instruments only; this is not a complete company debt stack.'} Final maturity dates do not capture amortization. Effective accounting rates are shown separately from cash coupons above.</p><div class="table-wrap"><table><thead><tr><th>Instrument / principal</th><th>Final maturity</th><th>Rate basis</th><th>Recourse / security</th><th>Evidence</th></tr></thead><tbody>${inventory.map(i=>`<tr><td><strong>${esc(i.instrument)}</strong><p>${exact(i.principal)} ${esc(i.currency)}<br>${date(i.as_of)}</p></td><td>${esc(i.maturity)}<span class="cell-note">${words(i.maturity_precision)}</span></td><td>${esc(i.rate)}<span class="cell-note">${words(i.rate_kind)}</span></td><td>${esc(i.recourse)}<p>${esc(i.security)}</p></td><td>${evidence(i.source_ids)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-panel">No current instrument-level inventory established. Selected historical notes remain in Rates & notes.</p>'}`);
  }

  function download(name,content,type) {
    const url=URL.createObjectURL(new Blob([content],{type}));
    const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function exportCSV() {
    const quote=v=>{let s=String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
    const header=['ticker','company','business_model','listing_status','borrowings_usd','borrowings_as_of','reported_cash_usd','cash_as_of','cash_basis','market_cap_usd','market_cap_as_of','market_cap_status','market_cap_note','debt_market_cap_percent','ratio_blocker','ratio_basis','size_band','contracts_json','capacity_json','hardware_json','revenue_json','instrument_inventory_json','maturity_schedule_json','liquidity_json','later_events_json','source_urls'];
    const rows=visibleCompanies.map(c=>{const x=c.v2,m=x.market_cap;const ids=[...c.metrics.debt.source_ids,...(c.metrics.cash?.source_ids||[]),...(m?.source_ids||[]),...[...x.contracts,...x.capacity,...x.hardware,...x.revenue,...x.debt_inventory].flatMap(f=>f.source_ids),...(x.maturity_schedule?.source_ids||[])];return [c.ticker,c.name,c.group,c.listing_status,c.metrics.debt.value,c.as_of,c.metrics.cash?.value,c.metrics.cash?.as_of||c.as_of,c.metrics.cash?.basis,m?.value,m?.as_of,m?.status,m?.note,x.debt_market_cap_percent,m?.ratio_blocker,'Reported borrowing carrying value excluding leases / dated provider equity cap; different dates; no pro-forma adjustment',x.size_band,JSON.stringify(x.contracts),JSON.stringify(x.capacity),JSON.stringify(x.hardware),JSON.stringify(x.revenue),JSON.stringify(x.debt_inventory),JSON.stringify(x.maturity_schedule??null),JSON.stringify(c.liquidity),JSON.stringify(x.events),[...new Set(ids)].map(id=>sources.get(id)?.url).filter(Boolean).join(' | ')];});
    download('NeoCloud-V2-comparison.csv',[header,...rows].map(r=>r.map(quote).join(',')).join('\r\n'),'text/csv;charset=utf-8');
  }

  function route() {
    sectionObserver?.disconnect();
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
      $('reviewed').textContent = data.website_reviewed_at;
      $('coverage-summary').textContent = `${data.companies.filter(c=>c.v2.market_cap).length} dated market-cap snapshots; ${data.companies.filter(c=>c.v2.contracts.length).length} company contract profiles. ${data.companies.filter(c=>c.v2.maturity_schedule).length} issuer repayment schedules with explicit calendar/fiscal periods; selected current instrument inventories elsewhere. Nebius valuation ratio is withheld pending share-count reconciliation.`;
      ['search', 'group', 'listing', 'order', 'size'].forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change', renderUniverse));
      $('filter-toggle').addEventListener('click', () => {
        const expanded = $('filter-toggle').getAttribute('aria-expanded') !== 'true';
        $('filter-toggle').setAttribute('aria-expanded', String(expanded));
        $('filter-toggle').closest('form').classList.toggle('filters-expanded', expanded);
      });
      document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => { activeView = button.dataset.view; renderUniverse(); }));
      $('empty-reset').addEventListener('click', () => { $('reset').click(); $('search').focus(); });
      $('reset').addEventListener('click', () => { $('search').value = ''; $('group').value = 'all'; $('listing').value = 'listed'; $('order').value = 'name'; $('size').value = 'all'; activeView = 'financing'; renderUniverse(); });
      $('export-csv').addEventListener('click',exportCSV);
      $('export-json').addEventListener('click',()=>download('NeoCloud-V2-evidence.json',JSON.stringify({reviewed_at:data.website_reviewed_at,companies:visibleCompanies,sources:data.sources},null,2),'application/json'));
      window.addEventListener('hashchange', route); route();
    } catch {
      $('error').hidden = false;
      $('error').textContent = 'The evidence ledger could not be loaded. Use the standalone V2 HTML preview, or build and serve the workspace with npm run preview:v2.';
    }
  }
  init();
})();
