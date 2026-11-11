'use strict';
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const METRICS=Object.freeze({
  debt:{title:'Reported borrowings',kicker:'BORROWING BALANCE / USD · LEASES EXCLUDED',headline:'Borrowing size, without the guesswork.',description:'Compare the borrowing carrying amount reported on each company’s balance sheet. This is loans and notes, with leases excluded—not a forecast or an unused credit facility.',formula:'Higher amount = more borrowing dollars',caveat:'Size is not safety. A larger company may borrow more. Debt scope, accounting basis and dates can differ; inspect each source before drawing conclusions.'},
  debt_assets:{title:'Debt / assets',kicker:'BALANCE-SHEET RATIO / %',headline:'Put the borrowing beside the balance sheet.',description:'For every $100 of recorded assets, how many dollars of reported borrowings does the company have? Both figures come from the same dated balance sheet.',formula:'Reported debt ÷ total assets × 100',caveat:'This is a balance-sheet ratio, not a health score or proof of which assets were funded by debt. Asset accounting and business mix differ. Missing or mismatched inputs are unranked.'},
  coupon:{title:'Bond coupon examples',kicker:'SELECTED NOTE TERMS / FIXED COUPON',headline:'One bond. One contractual interest rate.',description:'Browse the fixed coupons on selected, named notes. These are individual instruments, not a ranking of companies’ borrowing costs. Convertibles, secured project notes and unsecured bonds have different terms.',formula:'A selected note’s contractual rate',caveat:'A sortable reference, not a company ranking. Coupon is not current market yield or a rate on new borrowing. Different issue dates, maturities, security and conversion rights prevent a like-for-like cost ranking.'}
});
const GROUPS=Object.freeze({
  ai_infrastructure:{label:'AI infrastructure',note:'GPU clouds and mixed AI/HPC businesses. Business models differ.'},
  gpu_cloud:{label:'GPU cloud',note:'Companies whose core business includes AI/GPU cloud infrastructure. Financing structures, scale and disclosure dates still differ.'},
  ai_transition:{label:'AI transition / mixed',note:'Companies developing AI/HPC operations alongside mining, power, hosting or other activities. Company-wide debt is not automatically AI-only debt.'},
  data_center_reit:{label:'Data-center REITs',note:'Property and data-center landlords, shown separately from GPU cloud operators. Their asset base and financing model differ.'},
  bitcoin_mining:{label:'Bitcoin miners',note:'Mining businesses provide adjacent context. They are not assumed to be pure-play AI cloud operators.'},
  all:{label:'All companies',note:'A broad reference universe, not a uniform peer group. GPU clouds, mixed AI/mining companies and data-center landlords have different business and financing models.'}
});
const TYPE_NAMES={convertible:'Convertible note',exchangeable:'Exchangeable note',exchangeable_senior_notes:'Exchangeable senior notes',secured_project:'Secured project note',secured_project_notes:'Secured project notes',senior_secured_project_notes:'Senior secured project notes',project_senior_secured_nonconvertible:'Project senior secured / nonconvertible',senior_unsecured:'Senior unsecured note',senior_unsecured_notes:'Senior unsecured notes',senior_unsecured_nonconvertible:'Senior unsecured / nonconvertible',senior_unsecured_convertible:'Senior unsecured / convertible',senior_secured:'Senior secured note',secured:'Secured note',unsecured:'Unsecured note',fixed:'Fixed-rate note'};
const noteType=type=>TYPE_NAMES[type]||(typeof type==='string'?type.replaceAll('_',' '):'Type unknown');
let data,sourceMap=new Map(),state={metric:'debt',group:'ai_infrastructure',q:'',order:'desc'},detailTicker=null,visibleRows=[],toastTimer;
const isValue=v=>v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))&&Number(v)>=0;
const metricFor=(company,key=state.metric)=>company.metrics?.[key]||{};
const sourceIDs=metric=>(Array.isArray(metric.source_ids)?metric.source_ids:[]).filter(id=>sourceMap.has(id));
const eligible=(company,key=state.metric)=>{const m=metricFor(company,key);return m.rankable===true&&isValue(m.value)&&sourceIDs(m).length>0;};
function money(value,compact=true){if(!isValue(value))return 'Unknown';return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:compact?'compact':'standard',maximumFractionDigits:compact?2:0}).format(Number(value));}
function percent(value,places=2){return isValue(value)?Number(value).toLocaleString('en-US',{maximumFractionDigits:places})+'%':'Unknown';}
function displayValue(company,key=state.metric,compact=true){const m=metricFor(company,key);if(!isValue(m.value))return 'Unknown';return key==='debt'||key==='assets'||key==='cash'?money(m.value,compact):percent(m.value,key==='coupon'?3:2);}
function dateLabel(value){if(!value)return 'Date unknown';const parsed=new Date(value+'T12:00:00Z');return Number.isFinite(parsed.getTime())?parsed.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):String(value);}
function groupName(group){return GROUPS[group]?.label||'Other / scope noted';}
function rowDate(company){const m=metricFor(company);return state.metric==='coupon'?(m.as_of||company.as_of):company.as_of;}
function safeLink(url,title){try{const u=new URL(url);if(u.protocol!=='https:')throw new Error('Unsupported URL');const a=el('a',title);a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a;}catch{return el('span',title);}}
function showToast(message){clearTimeout(toastTimer);$('toast').textContent=message;$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,3500);}
function updateURL(){const params=new URLSearchParams({metric:state.metric,group:state.group,order:state.order});if(state.q)params.set('q',state.q);if(detailTicker)params.set('company',detailTicker);try{const u=new URL(location.href);u.search=params.toString();history.replaceState(null,'',u);}catch{/* Opaque-origin attachment previews can still use every local control. */}}
function inGroup(company){return state.group==='all'||company.group===state.group||(state.group==='ai_infrastructure'&&['gpu_cloud','ai_transition'].includes(company.group));}
function rowsForView(){
  const query=state.q.trim().toLocaleLowerCase('en-US');
  const rows=data.companies.filter(c=>inGroup(c)&&(!query||`${c.ticker} ${c.name} ${c.business||''}`.toLocaleLowerCase('en-US').includes(query)));
  rows.sort((a,b)=>{const ar=eligible(a),br=eligible(b);if(ar!==br)return ar?-1:1;if(ar){const delta=Number(metricFor(a).value)-Number(metricFor(b).value);if(delta!==0)return state.order==='asc'?delta:-delta;}return a.name.localeCompare(b.name);});
  return rows;
}
function metricDefinition(){return {...METRICS[state.metric],...(data.metric_definitions?.[state.metric]||{})};}
function render(){
  const definition=metricDefinition(),isCoupon=state.metric==='coupon';
  $('metric-kicker').textContent=definition.kicker||METRICS[state.metric].kicker;
  $('metric-title').textContent=definition.headline||METRICS[state.metric].headline;
  $('metric-description').textContent=definition.description;
  $('metric-formula').textContent=definition.formula;
  $('metric-caveat').textContent=definition.caveat+(isCoupon?' Terms observed in dated disclosure; continued outstanding status has not been reverified for every example.':'');
  $('value-heading').textContent=definition.title;
  $('ranking-panel').setAttribute('aria-labelledby','tab-'+state.metric);
  $('table-caption').textContent=isCoupon?'Selected bond coupon reference. Sorted instruments are not a company borrowing-cost ranking. Open a company for note terms and evidence.':`${definition.title}, ${GROUPS[state.group].label}. Ranks apply only to eligible companies matching this view; ties share a rank. Open any company to inspect definitions and evidence.`;
  document.querySelectorAll('[data-metric]').forEach(button=>{const selected=button.dataset.metric===state.metric;button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;});
  document.querySelectorAll('[data-group]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.group===state.group)));
  $('group-note').textContent=GROUPS[state.group].note+(isCoupon?' Note terms can predate the company balance-sheet snapshot.':' Dates vary by company.');
  $('direction').value=state.order;
  $('direction').options[0].textContent=isCoupon?'Higher coupons first':'Highest first';
  $('direction').options[1].textContent=isCoupon?'Lower coupons first':'Lowest first';
  $('search').value=state.q;
  visibleRows=rowsForView();
  const ranked=visibleRows.filter(c=>eligible(c)),max=Math.max(1,...ranked.map(c=>Number(metricFor(c).value)));
  $('result-count').textContent=`${visibleRows.length} compan${visibleRows.length===1?'y':'ies'} · ${ranked.length} ${isCoupon?'sourced note examples':'ranked'} · ${visibleRows.length-ranked.length} unranked`;
  const dates=ranked.map(rowDate).filter(Boolean).sort();
  $('date-range').textContent=dates.length?(dates[0]===dates.at(-1)?'Snapshot '+dateLabel(dates[0]):'Snapshots '+dateLabel(dates[0])+' – '+dateLabel(dates.at(-1))):'No comparable dated values in this view';
  const root=$('ranking-rows');root.replaceChildren();let lastValue=null,rank=0;
  visibleRows.forEach((company,index)=>{
    const m=metricFor(company),known=eligible(company),tr=el('tr');tr.dataset.ticker=company.ticker;
    let shownRank='—';if(known&&!isCoupon){if(lastValue===null||Number(m.value)!==lastValue)rank=index+1;lastValue=Number(m.value);shownRank=String(rank);}
    const rankCell=el('td',shownRank,'rank-number');if(isCoupon)rankCell.setAttribute('aria-label','Reference example; not ranked');
    const identity=el('td'),button=el('button',undefined,'company-button');button.type='button';button.setAttribute('aria-label',`Inspect ${company.name} (${company.ticker}) and its source evidence`);button.onclick=()=>openCompany(company.ticker);
    const text=el('span');text.append(el('strong',company.name),el('small',`${company.ticker} / ${groupName(company.group)}`));button.append(el('span',company.ticker.slice(0,1),'monogram'),text);identity.append(button,el('span',company.business||'Business scope not supplied','business-label'));
    const value=el('td'),valueText=el('span',known?displayValue(company):'Not comparable / unknown','metric-value'+(known?'':' unknown'));
    if(known)valueText.title=state.metric==='debt'?money(m.value,false)+' · borrowings (leases excluded)':displayValue(company);value.append(valueText);
    if(isCoupon){value.append(el('span',m.instrument||'No eligible note terms','metric-subtext'));if(m.type||m.maturity)value.append(el('span',[noteType(m.type),m.maturity?'Due '+m.maturity:null].filter(Boolean).join(' · '),'metric-subtext'));}
    else if(known){const track=el('div',undefined,'bar-track'),fill=el('div',undefined,'bar-fill');fill.style.width=Number(m.value)/max*100+'%';track.setAttribute('aria-hidden','true');track.append(fill);value.append(track);}
    if(!known)value.append(el('span',m.note||'A comparable, source-backed value is not available.','metric-subtext'));
    value.append(el('span','As of '+dateLabel(rowDate(company)),'mobile-date'));
    const date=el('td',undefined,'date-cell');date.append(el('span',dateLabel(rowDate(company)),'row-date'));const dateMeta=el('small',state.metric==='coupon'?(m.issue_date?'Issued '+m.issue_date:'Issue date unknown'):`${(company.form||'Disclosure').replaceAll('_',' ')}${company.filed_at?' · source date '+company.filed_at:''}`);date.firstChild.append(dateMeta);
    const status=el('td',undefined,'status-cell');status.append(el('span',known?'Source-backed':'Not ranked','evidence-pill'+(known?'':' unknown')),el('div',known?sourceIDs(m).length+' linked source'+(sourceIDs(m).length===1?'':'s'):'Scope or evidence incomplete','evidence-detail'));
    const inspect=el('td'),arrow=el('button','→','inspect-button');arrow.type='button';arrow.setAttribute('aria-label','Open '+company.ticker+' details');arrow.onclick=()=>openCompany(company.ticker);inspect.append(arrow);
    tr.append(rankCell,identity,value,date,status,inspect);root.append(tr);
  });
  $('ranking-table').hidden=visibleRows.length===0;$('empty').hidden=visibleRows.length!==0;
  updateURL();
}
function appendMetric(parent,company,key,label){
  const m=metricFor(company,key),card=el('article',undefined,'detail-metric');card.append(el('h3',label));
  const sourced=sourceIDs(m).length>0,hasValue=isValue(m.value);
  card.append(el('strong',hasValue?displayValue(company,key,false):'Unknown',hasValue?'':'unknown'));
  if(!sourced&&hasValue)card.append(el('p','Source linkage incomplete; excluded from ranking.'));
  if(key==='debt_assets'&&hasValue)card.append(el('p',`About $${Number(m.value).toFixed(2)} of borrowings per $100 of recorded assets. This does not identify which assets were funded with debt.`));
  if(key==='coupon'){if(m.instrument)card.append(el('p',m.instrument));const terms=[noteType(m.type),m.issue_date?'Issued '+m.issue_date:'Issue date unknown',m.maturity?'Matures '+m.maturity:'Maturity unknown'].filter(Boolean);card.append(el('p',terms.join(' · ')));if(m.issuer)card.append(el('p','Issuer / scope: '+m.issuer));card.append(el('p','Selected note only. Coupon is not current market yield or the company’s overall cost of debt. Terms observed in dated disclosure; continued outstanding status has not been reverified for every example.'));if(m.selection_rule)card.append(el('p','Selection: '+m.selection_rule));}
  if(m.basis)card.append(el('p',m.basis));if(m.note)card.append(el('p',m.note));
  if(['debt','assets','cash'].includes(key)&&hasValue&&Number(company.source_precision_usd)>1)card.append(el('p',`USD converted from source figures rounded to ${money(company.source_precision_usd)}. Displayed zeros do not imply dollar precision.`));
  card.append(el('p','As of '+dateLabel(key==='coupon'?(m.as_of||company.as_of):company.as_of)));
  parent.append(card);
}
function openCompany(ticker){
  const company=data.companies.find(c=>c.ticker===ticker);if(!company)return;
  detailTicker=ticker;$('detail-ticker').textContent=`${ticker} / ${groupName(company.group)}`;$('detail-title').textContent=company.name;
  const content=$('detail-content');content.replaceChildren(el('p',company.business||'Business description not available.','detail-business'));
  const status=el('div',undefined,'detail-status');status.append(el('strong',`Dated disclosure: ${dateLabel(company.as_of)}`),el('div',`${(company.form||'Company disclosure').replaceAll('_',' ')}${company.filed_at?' · source date '+dateLabel(company.filed_at):''}. These are reported figures under the stated scope, not a live market feed.`));content.append(status);
  const metrics=el('div',undefined,'detail-metrics');[['debt','Reported debt'],['debt_assets','Debt / recorded assets'],['assets','Total reported assets'],['cash','Cash & cash equivalents'],['coupon','Selected note coupon']].forEach(([key,label])=>appendMetric(metrics,company,key,label));content.append(metrics);
  const components=metricFor(company,'debt').components;
  if(Array.isArray(components)&&components.length){const section=el('section',undefined,'detail-section'),table=el('table',undefined,'reconciliation'),caption=el('caption','How the reported borrowing balance is reconciled'),tbody=el('tbody');table.append(caption);for(const component of components){const row=el('tr'),label=el('th',component.label||'Borrowing component');label.scope='row';const amount=el('td',(component.operation==='subtract'?'− ':'+ ')+money(component.value,false));row.append(label,amount);tbody.append(row);}table.append(tbody);section.append(el('h3','See the borrowing calculation'),table);if(Number(company.source_precision_usd)>1)section.append(el('p',`USD values converted from disclosures rounded to ${money(company.source_precision_usd)}; they are not precise to individual dollars.`));content.append(section);}
  const notes=(company.notes||[]).filter(Boolean);
  if(notes.length){const section=el('section',undefined,'detail-section'),list=el('ul');section.append(el('h3','What to keep in mind'));notes.forEach(note=>list.append(el('li',note)));section.append(list);content.append(section);}
  const ids=new Set([...(company.source_ids||[]),...Object.values(company.metrics||{}).flatMap(m=>Array.isArray(m?.source_ids)?m.source_ids:[])]),sources=[...ids].map(id=>sourceMap.get(id)).filter(Boolean),ledger=el('section',undefined,'detail-section');ledger.append(el('h3','Read the evidence'));
  if(!sources.length)ledger.append(el('p','No linked primary source is available for this company. Missing evidence does not mean zero debt.'));
  sources.forEach(source=>{const card=el('article',undefined,'source-card'),title=el('h4');title.append(safeLink(source.url,source.title||source.publisher||'Primary disclosure'));card.append(title,el('p',`${source.publisher||'Primary source'} · publication ${dateLabel(source.published_at||source.published_date)}${source.retrieved_at?' · retrieved '+source.retrieved_at:''}`));if(source.source_unit)card.append(el('p','Source units: '+source.source_unit));if(source.excerpt)card.append(el('blockquote',source.excerpt));ledger.append(card);});content.append(ledger);
  updateURL();if(!$('company-dialog').open)$('company-dialog').showModal();
}
function exportData(format){
  const rows=visibleRows.map(company=>{
    const m=metricFor(company),ids=sourceIDs(m),sources=ids.map(id=>sourceMap.get(id)),isCoupon=state.metric==='coupon';
    return {ticker:company.ticker,name:company.name,group:company.group,metric:state.metric,
      value:eligible(company)?m.value:null,unit:m.unit||(isCoupon?'percent':'USD'),
      ranked:!isCoupon&&eligible(company),as_of:rowDate(company)||null,
      source_date:sources[0]?.published_at||null,source_dates:sources.map(s=>s.published_at||null),
      company_as_of:company.as_of,company_source_date:company.filed_at||null,
      source_precision_usd:isCoupon?null:(company.source_precision_usd||null),
      scope:isCoupon?(m.scope||m.basis||m.issuer||''):(company.scope||m.scope||''),
      basis:m.basis||'',note:m.note||'',instrument:m.instrument||'',instrument_type:m.type||null,
      issuer:m.issuer||null,issue_date:m.issue_date||null,maturity:m.maturity||null,
      market_yield:null,source_ids:ids,source_urls:sources.map(s=>s.url)};
  });
  let text,type;
  if(format==='json'){text=JSON.stringify({disclosure:'Reported historical financial information. No synthetic values. Coupon examples are instruments, not a company cost ranking. Continued outstanding status has not been reverified for every note example.',reviewed_at:data.reviewed_at,view:{...state},definition:metricDefinition(),coupon_selection_policy:data.coupon_selection_policy||null,rows,sources:data.sources.filter(s=>rows.some(r=>r.source_urls.includes(s.url)))},null,2);type='application/json';}
  else{const keys=['ticker','name','group','metric','value','unit','ranked','as_of','source_date','source_dates','company_as_of','company_source_date','source_precision_usd','scope','basis','note','instrument','instrument_type','issuer','issue_date','maturity','market_yield','source_ids','source_urls'];const escape=value=>{let s=Array.isArray(value)?value.join(' | '):value==null?'':String(value);if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};text=[keys.map(escape).join(','),...rows.map(row=>keys.map(key=>escape(row[key])).join(','))].join('\r\n');type='text/csv;charset=utf-8';}
  const url=URL.createObjectURL(new Blob([text],{type})),a=el('a');a.href=url;a.download=`neocloud-${state.metric}-${state.group}.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function selectMetric(metric){if(!Object.hasOwn(METRICS,metric))return;state.metric=metric;state.order=metric==='coupon'?'asc':'desc';render();}
function bind(){
  document.querySelectorAll('[data-metric]').forEach(button=>{button.onclick=()=>selectMetric(button.dataset.metric);button.onkeydown=event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const keys=Object.keys(METRICS),current=keys.indexOf(button.dataset.metric),next=event.key==='Home'?0:event.key==='End'?keys.length-1:(current+(event.key==='ArrowRight'?1:-1)+keys.length)%keys.length;selectMetric(keys[next]);$('tab-'+keys[next]).focus();};});
  document.querySelectorAll('[data-group]').forEach(button=>button.onclick=()=>{state.group=button.dataset.group;render();});
  $('search').oninput=()=>{state.q=$('search').value.slice(0,100);render();};$('direction').onchange=()=>{state.order=$('direction').value==='asc'?'asc':'desc';render();};
  $('reset').onclick=()=>{state={metric:'debt',group:'ai_infrastructure',q:'',order:'desc'};render();};$('clear-search').onclick=()=>{state.q='';render();$('search').focus();};
  $('close-dialog').onclick=()=>$('company-dialog').close();$('company-dialog').addEventListener('close',()=>{detailTicker=null;updateURL();});
  $('download-csv').onclick=()=>exportData('csv');$('download-json').onclick=()=>exportData('json');
  $('share').onclick=async()=>{try{if(location.protocol==='file:')throw new Error('Local file');await navigator.clipboard.writeText(location.href);showToast('View link copied.');}catch{showToast('This preview cannot copy a link here. Share the HTML file, or copy the address from your browser.');}};
}
async function init(){
  try{
    const bundled=$('preview-data');if(bundled)data=JSON.parse(bundled.textContent);else{const response=await fetch('./data.json');if(!response.ok)throw new Error('The source dataset could not be loaded.');data=await response.json();}
    if(!Array.isArray(data.companies)||!Array.isArray(data.sources))throw new Error('The source dataset has an invalid format.');
    if(data.mock===true){$('error').hidden=false;$('error').textContent='INTERFACE TEST DATA ONLY — These mock companies and figures are not actual financial disclosures.';}
    sourceMap=new Map(data.sources.map(source=>[source.id,source]));
    const params=new URLSearchParams(location.search),metric=params.get('metric'),group=params.get('group'),order=params.get('order');
    if(Object.hasOwn(METRICS,metric))state.metric=metric;if(Object.hasOwn(GROUPS,group))state.group=group;state.order=order==='asc'||order==='desc'?order:(state.metric==='coupon'?'asc':'desc');state.q=(params.get('q')||'').slice(0,100);
    $('company-count').textContent=String(data.companies.length).padStart(2,'0');$('review-date').textContent='Sources reviewed '+dateLabel(data.reviewed_at);
    bind();render();$('rankings').setAttribute('aria-busy','false');
    const ticker=params.get('company');if(ticker&&data.companies.some(c=>c.ticker===ticker))openCompany(ticker);
  }catch(error){$('error').hidden=false;$('error').textContent=`The comparison could not load. ${error.message} Please reload the preview; if opening a local file, use the complete standalone HTML.`;$('rankings').setAttribute('aria-busy','false');$('result-count').textContent='Source dataset unavailable';$('ranking-rows').replaceChildren();}
}
init();
