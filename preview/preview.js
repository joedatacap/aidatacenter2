'use strict';
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
const money = value => value == null ? 'Unavailable' : new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', notation:'compact', maximumFractionDigits:2}).format(Number(value));
const percent = value => value == null ? 'Unavailable' : (Number(value) * 100).toFixed(1) + '%';
let data, horizon = 12;
function sourceLink(url, title) {
  const a = el('a', title);
  try { const u = new URL(url); if(u.protocol !== 'https:') throw new Error('Invalid source'); a.href = u.href; a.target = '_blank'; a.rel = 'noopener noreferrer'; } catch { return el('span', title); }
  return a;
}
function detail(parent, label, value) { const row = el('div', undefined, 'detail-row'); row.append(el('span', label), el('strong', value)); parent.append(row); }
function selection() { return {left:$('left').value, right:$('right').value, scenario:$('scenario').value, shock:Number($('shock').value), horizon}; }
function current() { const s = selection(); return data.cases[`${s.scenario}:${s.shock}`]; }
function funding(report) { return report.funding.find(f => f.horizon_months === horizon); }
function card(ticker, report) {
  const f = funding(report), exposure = report.floating.by_currency.USD;
  const article = el('article', undefined, 'company-card');
  const head = el('div', undefined, 'company-head'), identity = el('div', undefined, 'company-identity'), name = el('div');
  name.append(el('h3', data.companies[ticker].name), el('p', ticker + ' · USD scenario'));
  identity.append(el('div', ticker.slice(0,1), 'monogram'), name);
  head.append(identity, el('span', '◇ SYNTHETIC INPUTS', 'assumption-tag'));
  const body = el('div', undefined, 'card-body');
  body.append(el('div', `${horizon}-MONTH UNFUNDED NEED`, 'metric-label'));
  const number = el('div', money(f.unfunded_gap), 'gap-number'); number.append(el('small','USD'));
  const caption = el('p', undefined, 'gap-caption'); caption.append(el('strong', percent(f.funding_gap_to_market_cap)), document.createTextNode(' of illustrative equity value'));
  body.append(number, caption);
  const max = Math.max(Number(f.gross_uses), Number(f.usable_sources), 1);
  for (const [label, amount, cls] of [['Capital needed',f.gross_uses,'uses'],['Usable funding',f.usable_sources,'']]) {
    const labels = el('div', undefined, 'chart-labels'); labels.append(el('span',label), el('strong',money(amount)));
    const track = el('div',undefined,'track'), bar = el('div',undefined,'bar '+cls); bar.style.width = Number(amount)/max*100+'%'; track.append(bar);
    if (label === 'Usable funding') { const gap = el('div',undefined,'bar gap'); gap.style.width = Number(f.unfunded_gap)/max*100+'%'; track.append(gap); }
    body.append(labels,track);
  }
  const legend = el('div',undefined,'chart-legend');
  for(const [label,cls] of [['Available capital',''],['Funding gap','gap-key']]) { const item=el('span'); item.append(el('i',undefined,cls),document.createTextNode(label));legend.append(item); }
  body.append(legend);
  const metrics=el('div',undefined,'mini-metrics');
  for(const [label,value,note] of [
    [`+${report.floating.delta_bps} BPS / ANNUAL INTEREST`,money(exposure.annual_shock),'Incremental cash interest on assumed unhedged floating debt'],
    ['CASH INTEREST COVERAGE',report.coverage.coverage == null ? 'Unavailable' : Number(report.coverage.coverage).toFixed(1)+'×','Synthetic TTM EBITDA / cash interest; before rate shock']
  ]) { const box=el('div');box.append(el('div',label,'metric-label'),el('strong',value),el('small',note));metrics.append(box); }
  body.append(metrics);
  const details=el('details',undefined,'card-detail');details.append(el('summary','Inspect assumptions & repayment schedule'));
  const lineNames={capex:'Capital expenditure',principal:'Principal / refinancing use',cash:'Opening usable cash',operating_inflow:'Operating inflows',undrawn:'Undrawn funding'};
  f.rows.forEach(row=>detail(details,`${lineNames[row.category] || row.category} · ${row.side}`,money(row.scenario_amount)));
  detail(details,'Illustrative equity denominator',money(f.market_cap));
  detail(details,'Assumed unhedged floating debt',money(exposure.unhedged_floating));
  detail(details,'Assumed hedge notional',money(exposure.hedged_floating));
  detail(details,'Known principal due within 24 months',money(report.maturities.known_due.USD?.['24']));
  detail(details,'Market bond yield','Unavailable — no quote feed');
  details.append(el('p',`Scenario dated ${data.as_of}. This is a partial synthetic maturity schedule. Hedge expiry in the original fixture is April 17, 2027; the rate shock is immediate and annualized, not a forecast through the funding horizon. Coverage does not mean cash available for debt service.`,'detail-note'));
  (f.warnings||[]).forEach(w=>details.append(el('p',w,'detail-note')));
  body.append(details);article.append(head,body);return article;
}
function render() {
  const s=selection(), c=current(), root=$('comparison');
  root.replaceChildren(...[s.left,s.right].map(t=>card(t,c.tickers[t])));
  const left=funding(c.tickers[s.left]),right=funding(c.tickers[s.right]);
  const difference=Number(left.unfunded_gap)-Number(right.unfunded_gap);
  $('takeaway').textContent=difference===0
    ? `These labels have the same ${money(left.unfunded_gap)} funding gap in this ${s.scenario.toLowerCase()} fixture. The model compares financing assumptions, not company quality. Try CRWV / HUT under Tight credit to see how committed funding changes the result.`
    : `${difference>0?s.left:s.right} needs ${money(Math.abs(difference))} more unfunded capital over ${horizon} months in this ${s.scenario.toLowerCase()} example. The difference comes from assumed funding commitments, not a judgment about the real companies. A +${s.shock} bps shock separately raises annual interest by ${money(c.tickers[s.left].floating.by_currency.USD.annual_shock)} for ${s.left} and ${money(c.tickers[s.right].floating.by_currency.USD.annual_shock)} for ${s.right}.`;
  const a=left.assumptions;
  $('scenario-notes').replaceChildren(el('p',`${s.scenario}: operating inflows ×${a.operating_inflow_factor}; capex ×${a.capex_factor}; funding-model rate shock ${a.rate_shock_bps} bps. ${a.refinancing}. The separately selected benchmark shock is +${s.shock} bps.`));
  document.querySelectorAll('[data-pair]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.pair===s.left+','+s.right)));
  document.querySelectorAll('[data-horizon]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.horizon)===horizon)));
  const u=new URL(location.href);u.search=new URLSearchParams(s).toString();
  try { history.replaceState(null,'',u); } catch { /* Sandboxed file previews may have an opaque origin. */ }
}
function references() {
  const r=data.reference, root=$('reference-cards');root.replaceChildren();
  for(const i of r.instruments) {
    const c=el('article',undefined,'reference-card');
    c.append(el('div',i.coupon_pct?'PROJECT NOTES':'PARENT FACILITY','metric-label'),el('h3',i.name.replace(' project senior secured notes','').replace(' senior secured revolving facility',' revolver')));
    c.append(el('div',money(i.outstanding_principal ?? i.commitment_amount),'ref-amount'));
    c.append(el('p',i.outstanding_principal == null?'Facility commitment · drawn balance unknown':'Dated outstanding principal · not a current company total'));
    c.append(el('p',i.coupon_pct ? `${i.coupon_pct}% fixed coupon · maturity ${i.maturity}` : `${i.reference_index} + ${i.spread_bps} bps · maturity ${i.maturity||'unknown'}`));
    c.append(el('p',`Snapshot ${i.snapshot_date || i.issue_date || 'unknown'} · Market yield unavailable`));
    const e=r.evidence.find(e=>i.evidence_ids.includes(e.id));if(e)c.append(sourceLink(e.source_url,'Read source disclosure ↗'));
    root.append(c);
  }
  const ledger=$('evidence');ledger.replaceChildren();
  r.evidence.forEach(e=>{const c=el('article',undefined,'evidence-card');c.append(el('h4'),el('p',`Retained source excerpt · source date ${e.publication_or_filing_date || 'unknown'} · document period ${e.document_period_end||'unspecified'} · not refreshed for this preview`),el('blockquote',e.excerpt),el('p',e.claim));c.firstChild.append(sourceLink(e.source_url,e.source_title||'SEC disclosure'));ledger.append(c);});
}
function setPair(left,right){$('left').value=left;$('right').value=right;render();}
function download(){const s=selection(), c=current(), payload={disclosure:data.disclosure,selection:s,as_of:data.as_of,comparison:{[s.left]:c.tickers[s.left],[s.right]:c.tickers[s.right]}};const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=`neocloud-${s.left}-${s.right}-illustrative.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function init(){
  try{
    const bundled=$('preview-data');
    if(bundled) data=JSON.parse(bundled.textContent);
    else { const response=await fetch('./data.json');if(!response.ok)throw new Error('Scenario data could not be loaded.');data=await response.json(); }
    for(const id of ['left','right'])for(const [ticker,company] of Object.entries(data.companies)){const o=el('option',`${ticker} / ${company.name}`);o.value=ticker;$(id).append(o);}
    const p=new URLSearchParams(location.search);
    $('left').value=data.companies[p.get('left')]?p.get('left'):'CRWV';$('right').value=data.companies[p.get('right')]?p.get('right'):'HUT';
    if(['Base','Downside','Tight credit'].includes(p.get('scenario')))$('scenario').value=p.get('scenario');
    if(['0','100','200','300'].includes(p.get('shock')))$('shock').value=p.get('shock');
    if(p.get('horizon')==='18')horizon=18;
    $('controls').onsubmit=e=>e.preventDefault();['left','right','scenario','shock'].forEach(id=>$(id).onchange=render);
    $('swap').onclick=()=>setPair($('right').value,$('left').value);
    $('reset').onclick=()=>{$('scenario').value='Tight credit';$('shock').value='200';horizon=12;setPair('CRWV','HUT');};
    document.querySelectorAll('[data-pair]').forEach(b=>b.onclick=()=>setPair(...b.dataset.pair.split(',')));
    document.querySelectorAll('[data-horizon]').forEach(b=>b.onclick=()=>{horizon=Number(b.dataset.horizon);render();});
    $('download').onclick=download;render();references();$('compare').setAttribute('aria-busy','false');
  }catch(e){$('error').hidden=false;$('error').textContent=`The preview could not load. ${e.message} Serve the preview directory over HTTP and reload.`;$('compare').setAttribute('aria-busy','false');}
}
init();
