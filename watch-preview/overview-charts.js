/* Reviewed homepage charts; insert inside the application closure. */
 function overviewChartColor(c){
  const colors=['#237363','#436b9c','#976147','#6a6b9e','#967437','#477f86','#7f657b','#677f47','#9a5661'];
  const focus=list(data.focus_tickers);const i=focus.indexOf(c.ticker);
  return colors[i<0?[...String(c.id)].reduce((n,ch)=>n+ch.charCodeAt(0),0)%colors.length:i%colors.length];
 }
 function overviewChartMoney(value,exact=false){
  if(!finite(value))return 'Not established';
  return (Number(value)<0?'−':'')+money(Math.abs(Number(value)),exact);
 }
 function overviewRevenuePoint(q){
  const f=q.metrics?.revenue||{};
  const period=q.period_end,scope=String(f.scope||q.scope||'').trim(),basis=String(f.accounting_basis||'').trim();
  const months=f.months??q.months;
  const dated=/^\d{4}-\d{2}-\d{2}$/.test(period||'')&&Number.isFinite(Date.parse(period))&&new Date(period).toISOString().slice(0,10)===period;
  const missingStatuses=['not_researched','not_disclosed','not_applicable','unknown','conflicting','not_comparable'];
  const incompatible=!dated||months!==3||q.months!==3||(q.period_type&&q.period_type!=='quarter')||(f.period_end&&f.period_end!==period)||f.comparable===false||q.comparable===false;
  const usd=(f.currency||f.unit)==='USD'&&(!f.unit||f.unit==='USD');
  const valid=!incompatible&&usd&&finite(f.value)&&!missingStatuses.includes(f.status);
  const reason=incompatible?'Not comparable: this is not a compatible three-month revenue observation.':!usd?'Currency or units not established as USD.':f.reason||f.note||'Quarterly revenue not established in the reviewed record.';
  return {q,f,period,scope,basis,valid,reason,value:valid?Number(f.value):null,
   key:scope&&basis?JSON.stringify([scope.toLowerCase(),basis.toLowerCase(),f.currency||f.unit,f.unit||'USD',months]):null};
 }
 function overviewRevenueSegments(points){
  const segments=[];let active=[];
  for(const p of points){
   const prev=active.at(-1),elapsed=prev?(Date.parse(p.period)-Date.parse(prev.period))/86400000:0;
   if(!p.valid){if(active.length)segments.push(active);active=[];continue;}
   if(prev&&(!p.key||p.key!==prev.key||!Number.isFinite(elapsed)||elapsed<70||elapsed>110)){
    segments.push(active);active=[];
   }
   active.push(p);
  }
  if(active.length)segments.push(active);
  return segments;
 }
 function overviewRevenueCard(c){
  // Retain missing quarter slots: filtering nulls before plotting would bridge gaps.
  const history=list(c.quarters).filter(q=>q.period_type==='quarter'||q.months===3)
   .slice().sort((a,b)=>String(a.period_end).localeCompare(String(b.period_end))).slice(-4);
  const points=history.map(overviewRevenuePoint),known=points.filter(p=>p.valid),last=points.at(-1);
  const color=overviewChartColor(c),floor=Math.min(0,...known.map(p=>p.value)),ceiling=Math.max(0,...known.map(p=>p.value)),span=ceiling-floor||1;
  const W=320,H=100,left=0,right=320,top=11,bottom=82;
  points.forEach((p,i)=>{p.x=(i+.5)*W/points.length;p.y=p.valid?bottom-(p.value-floor)/span*(bottom-top):null;});
  const segments=overviewRevenueSegments(points),broken=segments.length>1||points.some(p=>!p.valid)||points.some((p,i)=>i&&p.key!==points[i-1].key);
  const svg=known.length?`<svg class="overview-revenue-svg" data-revenue-chart viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="M${left} ${bottom}H${right}" class="revenue-axis"/>${segments.filter(segment=>segment.length>1).map(segment=>`<polyline data-line-segment data-periods="${esc(segment.map(p=>p.period).join(','))}" points="${segment.map(p=>p.x.toFixed(2)+','+p.y.toFixed(2)).join(' ')}" fill="none" stroke="${color}" vector-effect="non-scaling-stroke"/>`).join('')}${known.map(p=>`<circle data-revenue-point data-period-end="${esc(p.period)}" data-value="${p.value}" cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="4.5" fill="${color}" vector-effect="non-scaling-stroke"><title>${esc(p.period)}: ${esc(overviewChartMoney(p.value,true))} · ${esc(p.scope)}</title></circle>`).join('')}</svg>`:'<p class="chart-empty">No reviewed USD quarterly revenue values to plot.</p>';
  return `<article class="overview-revenue-card" data-chart-company="${esc(c.id)}" style="--company-color:${color}"><div class="chart-company-heading"><a data-app href="${esc(profile(c,'earnings'))}"><span class="ticker">${esc(c.ticker)}</span> ${esc(c.name)}</a><span class="chart-quarter-count">${history.length} ${history.length===1?'quarter':'quarters'}</span></div><div class="chart-latest"><strong>${last?.valid?overviewChartMoney(last.value):'Not established'}</strong><span>${last?'Quarter ended '+day(last.period):'Quarterly history not loaded'}</span></div><p class="chart-scope">${esc(last?.scope||'Entity scope not established')}${last?.basis?' · '+esc(words(last.basis)):''}${c.ticker==='IREN'?' · June fiscal year-end':c.ticker==='APLD'?' · May fiscal year-end':''}</p><div class="chart-axis-caption"><span>Independent USD scale</span><span>${known.length?(ceiling===floor?'Reviewed value '+overviewChartMoney(ceiling):overviewChartMoney(floor)+'–'+overviewChartMoney(ceiling)):'No verified scale'}</span></div>${svg}${points.length?`<div class="revenue-observations" style="--revenue-points:${points.length}">${points.map(p=>`<details class="revenue-observation" data-period-end="${esc(p.period)}"${p.valid?` data-value="${p.value}"`:''}><summary title="${esc(p.period)} · ${p.valid?esc(overviewChartMoney(p.value,true)):esc(p.reason)} · ${esc(p.scope)}" aria-label="Quarter ended ${esc(p.period)}, ${p.valid?esc(overviewChartMoney(p.value,true)):esc(p.reason)}. Open exact value and evidence."><span>${p.valid?overviewChartMoney(p.value):'Unavailable'}</span><time datetime="${esc(p.period)}">${day(p.period).replace('-','-<wbr>')}</time></summary><div class="revenue-observation-detail"><strong>${p.valid?overviewChartMoney(p.value,true):esc(p.reason)}</strong><p>Period ended ${day(p.period)} · ${esc(p.q.fiscal_label||'Three-month period')}</p><p>${esc(p.scope||'Scope not established')}${p.basis?' · '+esc(words(p.basis)):''}. ${esc(p.f.definition||'Revenue definition not established')}</p><p>Source published ${day(p.f.published_at||p.q.publication_date||p.q.release_date)}${p.q.record_kind==='later_comparative'?' · later comparative observation, not the original release date':''}.</p>${p.f.note?`<p>${esc(p.f.note)}</p>`:''}${p.q.comparability_note?`<p>${esc(p.q.comparability_note)}</p>`:''}${evidence(sourceIds(p.f).length?sourceIds(p.f):sourceIds(p.q))}</div></details>`).join('')}</div>`:'<p class="chart-empty">No quarterly history loaded. A shorter history is shown when that is all the evidence supports.</p>'}${broken?'<p class="chart-qualification">Line breaks mark missing values, nonadjacent quarters or changes in accounting scope/basis.</p>':''}<a data-app class="chart-detail-link" href="${esc(profile(c,'earnings'))}">Earnings & evidence</a></article>`;
 }
 function overviewBalanceFact(c,kind){
  const f=kind==='cash'?cash(c):debt(c),date=f?.as_of||f?.period_end||finance(c).as_of;
  const status=f?.status;
  const valid=finite(f?.value)&&Number(f.value)>=0&&(!f.currency||f.currency==='USD')&&(!f.unit||f.unit==='USD')&&!['not_researched','not_disclosed','not_applicable','unknown','conflicting'].includes(status);
  return {f,date,valid,value:valid?Number(f.value):null};
 }
 function overviewBalanceCard(c){
  const ca=overviewBalanceFact(c,'cash'),de=overviewBalanceFact(c,'debt'),max=Math.max(ca.value??0,de.value??0),sameDate=ca.date&&de.date&&ca.date===de.date;
  const f=finance(c),l=f.liquidity||{},extra=list(l.excluded_balances),leases=list(f.debt_context?.leases);
  const prepayments=extra.filter(b=>/prepay|contract liabil|customer financing/i.test(b.label||b.kind||''));
  const other=extra.filter(b=>!prepayments.includes(b));
  const scopeMismatch=ca.f?.scope&&de.f?.scope&&ca.f.scope.toLowerCase().trim()!==de.f.scope.toLowerCase().trim();
  const row=(kind,p,label)=>`<div class="balance-bar-row" data-balance-kind="${kind}"${p.valid?` data-value="${p.value}"`:''}><div class="balance-bar-label"><span>${label}</span><strong>${p.valid?overviewChartMoney(p.value,true):'Not established'}</strong></div><div class="balance-bar-track" aria-hidden="true">${p.valid?`<span class="balance-bar balance-bar-${kind}" style="width:${max>0?p.value/max*100:0}%"></span>`:''}</div><p class="balance-date">${p.date?'Balance sheet '+day(p.date):'Balance-sheet date not established'}${evidence(sourceIds(p.f))}</p></div>`;
  return `<article class="balance-pair" data-balance-company="${esc(c.id)}" style="--company-color:${overviewChartColor(c)}"><div class="chart-company-heading"><a data-app href="${esc(profile(c,'financing'))}"><span class="ticker">${esc(c.ticker)}</span> ${esc(c.name)}</a></div><p class="balance-scale">${ca.valid||de.valid?(max===0?'Reviewed balances are $0. ':'Same scale within this company pair: $0–'+overviewChartMoney(max,true)+'. ')+'Independent of other companies.':'No verified scale · cash and borrowing amounts unavailable.'}</p>${row('cash',ca,'Cash & equivalents')}${row('debt',de,'Borrowing / financing obligations')}${!sameDate||scopeMismatch?`<p class="chart-qualification">${!sameDate?'Observation dates differ or are incomplete. ':''}${scopeMismatch?'Entity scopes differ; inspect their definitions.':''}</p>`:''}<p class="balance-definition">${esc(de.f?.definition||de.f?.basis||'Borrowing definition not established. Missing is not zero.')}</p>${prepayments.map(b=>`<p class="balance-separate"><strong>${esc(b.label)}: ${finite(b.value)?overviewChartMoney(b.value,true):'Not established'}</strong> · ${day(b.as_of)}. Separate from bars; not borrowing or earned revenue. ${evidence(sourceIds(b))}</p>`).join('')}<details class="balance-scope-detail"><summary>Cash access, leases & other balances</summary><p>${esc(l.cash_caveat||ca.f?.definition||ca.f?.basis||'Cash scope and parent availability are not established.')}</p>${de.f?.note?`<p>${esc(de.f.note)}</p>`:''}${other.map(b=>`<p><strong>${esc(b.label||b.kind||'Separately classified balance')}: ${finite(b.value)?overviewChartMoney(b.value,true):'Not established'}</strong> · ${day(b.as_of)}. ${esc(b.basis||b.note||'Kept separate from the paired bars.')}${evidence(sourceIds(b))}</p>`).join('')}${leases.length?leases.map(b=>`<p><strong>${esc(words(b.kind||b.label||'Lease liability'))}: ${finite(b.value)?overviewChartMoney(b.value,true):'Not established'}</strong> · ${day(b.as_of)}. Lease liabilities are separate from borrowing bars. ${esc(b.note||'')}${evidence(sourceIds(b))}</p>`).join(''):'<p>Lease balances not established in this chart; missing is not zero.</p>'}<p>Customer funding, lease liabilities, restricted balances and conditional credit are not added to the cash or borrowing bars. Group cash is not necessarily deployable parent cash.</p></details><a data-app class="chart-detail-link" href="${esc(profile(c,'financing'))}">Financing definitions & sources</a></article>`;
 }
 function overviewCharts(){
  if(!visible.length)return '<section id="overview-charts" class="overview-charts"><h2>Company comparisons</h2><p class="chart-empty">No companies match the current filters. Clear the search or peer selection to see reviewed revenue and balance-sheet charts.</p></section>';
  return `<div id="overview-charts" class="overview-charts"><section aria-labelledby="revenue-charts-title"><div class="section-heading"><div><p class="eyebrow">OPERATING PERFORMANCE</p><h2 id="revenue-charts-title">Revenue, quarter by quarter</h2></div><a data-app href="${esc(href('earnings',{tab:'history'}))}">Explore earnings history</a></div><p class="chart-section-note">Recognized revenue · up to four three-month periods. Each company has an independent USD scale. Open a dated value for exact amounts and sources. ARR and contract values stay separate.</p><div class="overview-chart-grid">${visible.map(overviewRevenueCard).join('')}</div></section><section aria-labelledby="balance-charts-title"><div class="section-heading"><div><p class="eyebrow">FINANCING CONTEXT</p><h2 id="balance-charts-title">Cash & borrowing obligations</h2></div><a data-app href="${esc(href('financing',{tab:'cash'}))}">Inspect cash & funding</a></div><p class="chart-section-note">Each company’s bars share a scale; scales differ across companies. Dates and definitions stay attached. Cash minus debt does not measure deployable cash or financial health. Market cap stays separate.</p><div class="overview-chart-grid balance-chart-grid">${visible.map(overviewBalanceCard).join('')}</div></section></div>`;
 }
