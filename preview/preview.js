'use strict';
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const METRICS=Object.freeze({
  cash:{title:'Reported cash',kicker:'CASH / SEPARATE FACILITY DISCLOSURES',headline:'Cash in the accounts. Conditions on credit.',description:'See reported cash beside selected borrowing facilities. Facility limits, conditional unused commitments and letters of credit are separate from cash.',formula:'Cash and credit are shown separately',caveat:'Sorted cash balances are not a funding or health ranking. Company-wide available credit has not been established from the selected facilities. Cash restrictions, business scope and dates matter.'},
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
const NOTE_TYPES=Object.freeze({all:'All note types',unsecured:'Conventional unsecured',secured:'Secured & project',convertible:'Convertible & exchangeable'});
const NOTE_STATUSES=Object.freeze({all:'All dated terms',confirmed:'Outstanding confirmed at snapshot'});
let data,sourceMap=new Map(),state={metric:'debt',group:'ai_infrastructure',q:'',order:'desc',noteType:'all',noteStatus:'all'},detailTicker=null,visibleRows=[],cohortRanks=new Map(),compareTickers=[],toastTimer;
const isValue=v=>typeof v!=='boolean'&&v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))&&Number(v)>=0;
const metricFor=(company,key=state.metric)=>key==='coupon'&&company._instrument?company._instrument:company.metrics?.[key]||{};
const sourceIDs=metric=>(Array.isArray(metric.source_ids)?metric.source_ids:[]).filter(id=>sourceMap.has(id));
const eligible=(company,key=state.metric)=>{const m=metricFor(company,key),currencyOK=['debt','assets','cash'].includes(key)?m.unit==='USD':m.unit==='percent'&&(key!=='coupon'||m.currency==='USD');return m.rankable===true&&isValue(m.value)&&sourceIDs(m).length>0&&currencyOK;};
function money(value,compact=true){if(!isValue(value))return 'Unknown';return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:compact?'compact':'standard',maximumFractionDigits:compact?2:0}).format(Number(value));}
function percent(value,places=2){return isValue(value)?Number(value).toLocaleString('en-US',{maximumFractionDigits:places})+'%':'Unknown';}
function currencyAmount(value,unit,compact=true){if(!isValue(value))return 'Unknown';if(unit==='USD')return money(value,compact);return `${unit||'Currency unknown'} ${Number(value).toLocaleString('en-US',{notation:compact?'compact':'standard',maximumFractionDigits:compact?2:0})}`;}
function signedCurrencyAmount(value,unit){if(value===null||value===undefined||value===''||!Number.isFinite(Number(value)))return 'Unknown';const amount=Number(value).toLocaleString('en-US',{maximumFractionDigits:0});return `${unit||'Currency unknown'} ${amount}`;}
function displayValue(company,key=state.metric,compact=true){const m=metricFor(company,key);if(!isValue(m.value))return 'Unknown';return ['debt','assets','cash'].includes(key)?currencyAmount(m.value,m.unit,compact):percent(m.value,key==='coupon'?3:2);}
function dateLabel(value){if(!value)return 'Date unknown';const parsed=new Date(value+'T12:00:00Z');return Number.isFinite(parsed.getTime())?parsed.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):String(value);}
function groupName(group){return GROUPS[group]?.label||'Other / scope noted';}
function companyCode(company){return company.display_code||company.ticker;}
function listingLabel(company){return company.listing_status==='private_pending_ipo'?'Private · pending IPO':String(company.listing_status||'').startsWith('private')?'Private company':null;}
function rowDate(company){return metricFor(company).as_of||company.as_of;}
function companyInstruments(company){if(Array.isArray(data.instruments))return data.instruments.filter(note=>note.ticker===company.ticker);const selected=company.metrics?.coupon;if(!selected||!isValue(selected.value)||!sourceIDs(selected).length)return [];return [{...selected,id:selected.id||'selected:'+company.ticker,ticker:company.ticker,outstanding_status:'terms_only',outstanding_principal:{value:null,unit:'USD',as_of:null,source_ids:[]}}];}
function noteCategory(note){const type=String(note.type||'').toLowerCase().replaceAll('nonconvertible','');if(/convertible|exchangeable/.test(type))return 'convertible';if(/unsecured/.test(type))return 'unsecured';if(/secured|project/.test(type))return 'secured';return 'other';}
function outstandingLabel(note){if(note.outstanding_status==='verified_at_snapshot')return 'Outstanding confirmed at '+dateLabel(note.outstanding_principal?.as_of||note.as_of);if(note.outstanding_status==='verified_at_earlier_date')return 'Balance confirmed only at earlier date '+dateLabel(note.outstanding_principal?.as_of||note.as_of)+'; latest snapshot status not confirmed';return 'Dated terms only; outstanding status not confirmed';}
function outstandingBadge(note){return note.outstanding_status==='verified_at_snapshot'?'Outstanding confirmed':note.outstanding_status==='verified_at_earlier_date'?'Earlier-date balance':'Dated terms only';}
function principalKnown(note){const principal=note.outstanding_principal;return principal&&isValue(principal.value)&&principal.unit==='USD'&&sourceIDs(principal).length>0;}
function appendPrincipal(parent,note){
  const principal=note.outstanding_principal||{},label=principal.label||'Disclosed outstanding principal';
  if(principalKnown(note))parent.append(el('p',label+': '+currencyAmount(principal.value,principal.unit,false)+' · as of '+dateLabel(principal.as_of)));
  else parent.append(el('p',label+': unknown; not inferred from original issue size.'));
  if(principal.basis)parent.append(el('p',principal.basis));
}
function safeLink(url,title){try{const u=new URL(url);if(u.protocol!=='https:')throw new Error('Unsupported URL');const a=el('a',title);a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a;}catch{return el('span',title);}}
function showToast(message){clearTimeout(toastTimer);const host=$('company-dialog').open?$('company-dialog'):$('comparison-dialog').open?$('comparison-dialog'):document.body;host.append($('toast'));$('toast').textContent=message;$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,3500);}
function updateURL(){const params=new URLSearchParams({metric:state.metric,group:state.group,order:state.order});if(state.q)params.set('q',state.q);if(state.noteType!=='all')params.set('note_type',state.noteType);if(state.noteStatus!=='all')params.set('outstanding',state.noteStatus);if(detailTicker)params.set('company',detailTicker);if(compareTickers.length)params.set('compare',compareTickers.join(','));if($('comparison-dialog').open)params.set('comparison','1');try{const u=new URL(location.href);u.search=params.toString();history.replaceState(null,'',u);}catch{/* Opaque-origin attachment previews can still use every local control. */}}
function inGroup(company){return state.group==='all'||company.group===state.group||(state.group==='ai_infrastructure'&&['gpu_cloud','ai_transition'].includes(company.group));}
function rowsForCohort(){
  const companies=data.companies.filter(inGroup),rows=state.metric==='coupon'?companies.flatMap(company=>companyInstruments(company).map(note=>({...company,_instrument:note}))).filter(company=>{const note=metricFor(company);return(state.noteType==='all'||noteCategory(note)===state.noteType)&&(state.noteStatus==='all'||note.outstanding_status==='verified_at_snapshot');}):companies;
  rows.sort((a,b)=>{const ar=eligible(a),br=eligible(b);if(ar!==br)return ar?-1:1;if(ar){const delta=Number(metricFor(a).value)-Number(metricFor(b).value);if(delta!==0)return state.order==='asc'?delta:-delta;}return a.name.localeCompare(b.name);});
  return rows;
}
function rowsForView(cohort){const query=state.q.trim().toLocaleLowerCase('en-US');return cohort.filter(c=>!query||`${c.ticker} ${c.name} ${c.business||''} ${state.metric==='coupon'?(metricFor(c).instrument||'')+' '+(metricFor(c).issuer||''):''}`.toLocaleLowerCase('en-US').includes(query));}
function metricDefinition(){return {...METRICS[state.metric],...(data.metric_definitions?.[state.metric]||{})};}
function render(){
  const definition=metricDefinition(),isCoupon=state.metric==='coupon',isCash=state.metric==='cash',unranked=isCoupon||isCash;
  $('metric-kicker').textContent=definition.kicker||METRICS[state.metric].kicker;
  $('metric-title').textContent=definition.headline||METRICS[state.metric].headline;
  $('metric-description').textContent=definition.description;
  $('metric-formula').textContent=definition.formula;
  $('metric-caveat').textContent=definition.caveat+(isCoupon?' Terms observed in dated disclosure; continued outstanding status has not been reverified for every example.':'');
  $('value-heading').textContent=definition.title;$('download-csv').textContent=isCoupon?'Fixed-note ledger CSV ↓':'CSV ↓';$('download-json').textContent=isCoupon?'Rate profiles + notes JSON ↓':'JSON ↓';
  document.querySelector('.rank-col').textContent=isCoupon?'Ref.':'#';
  $('ranking-table').classList.toggle('cash-view',isCash);$('funding-heading').hidden=!isCash;
  $('note-filters').hidden=!isCoupon;$('note-type').value=state.noteType;$('note-status').value=state.noteStatus;
  $('search').placeholder=isCoupon?'Find a company, ticker or note':'Find a company or ticker';
  $('search').setAttribute('aria-label',isCoupon?'Find a company, ticker, note or issuer':'Find a company or ticker');
  $('ranking-panel').setAttribute('aria-labelledby','tab-'+state.metric);
  $('table-caption').textContent=isCash?'Reported cash and separately qualified facility disclosures. Companies are sorted by reported cash, without ranks or a combined funding total. Open Cash & funding for sources and conditions.':isCoupon?'Dated bond coupon reference. Each row is an identified note; a company may have multiple examples. Instruments are not ranked as company borrowing costs. Open a company for all note terms and evidence.':`${definition.title}, ${GROUPS[state.group].label}. Ranks use the full selected peer group before search. Meters show borrowings / recorded assets on a fixed 0–100% scale. Ties share a rank. Open any company to inspect definitions and evidence.`;
  document.querySelectorAll('[data-metric]').forEach(button=>{const selected=button.dataset.metric===state.metric;button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;});
  document.querySelectorAll('[data-group]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.group===state.group)));
  $('group-note').textContent=GROUPS[state.group].note+(isCoupon?' Note terms can predate the company balance-sheet snapshot.':' Dates vary by company.');
  $('direction').value=state.order;$('direction').parentElement.firstChild.textContent=isCoupon?'FIXED-NOTE COUPON ORDER ':'ORDER ';
  $('direction').options[0].textContent=isCoupon?'Higher coupons first':isCash?'Largest reported cash first':state.metric==='debt'?'Largest borrowings first':'Highest debt / assets first';
  $('direction').options[1].textContent=isCoupon?'Lower coupons first':isCash?'Smallest reported cash first':state.metric==='debt'?'Smallest borrowings first':'Lowest debt / assets first';
  $('search').value=state.q;
  const cohort=rowsForCohort(),cohortEligible=cohort.filter(c=>eligible(c));
  visibleRows=rowsForView(cohort);
  const ranked=visibleRows.filter(c=>eligible(c));
  cohortRanks=new Map();let lastValue=null,rank=0;
  if(!unranked)cohortEligible.forEach((company,index)=>{const value=Number(metricFor(company).value);if(lastValue===null||value!==lastValue)rank=index+1;cohortRanks.set(company.ticker,rank);lastValue=value;});
  if(isCoupon){const firms=new Set(visibleRows.map(c=>c.ticker)).size,confirmed=visibleRows.filter(c=>metricFor(c).outstanding_status==='verified_at_snapshot').length;$('result-count').textContent=`${state.q.trim()?'Showing '+visibleRows.length+' of '+cohort.length:visibleRows.length} notes across ${firms} compan${firms===1?'y':'ies'} · ${confirmed} outstanding confirmed`;}
  else if(isCash)$('result-count').textContent=`${visibleRows.length} compan${visibleRows.length===1?'y':'ies'} shown · ${ranked.length} reported cash balance${ranked.length===1?'':'s'} · unranked`;
  else $('result-count').textContent=state.q.trim()?`Showing ${visibleRows.length} of ${cohort.length} companies · ${ranked.length} ranked shown`:`${cohort.length} compan${cohort.length===1?'y':'ies'} · ${cohortEligible.length} ranked · ${cohort.length-cohortEligible.length} unranked`;
  $('rank-context').textContent=(!unranked?'Positions describe this measure, not company health. ':'')+(isCash?'Sorted by reported cash only. Facility amounts stay separate: no cash-plus-credit total, company rank or health score. ':isCoupon?'Note examples are unranked. A company may have multiple rows. Confirmed status applies only to its stated snapshot. ':`Ranks stay anchored to all ${cohort.length} companies in ${GROUPS[state.group].label}, ${state.order==='asc'?'lowest':'highest'} first. Search only hides rows. Meters show borrowings / recorded assets on a 0–100% scale, not company size or health. `)+'Choose Compare on up to three companies. For cash and credit, compare companies or open a name.';
  const dates=ranked.map(rowDate).filter(Boolean).sort();
  $('date-range').textContent=dates.length?(dates[0]===dates.at(-1)?(isCoupon?'Terms observed ':'Snapshot ')+dateLabel(dates[0]):(isCoupon?'Terms observed ':'Snapshots ')+dateLabel(dates[0])+' – '+dateLabel(dates.at(-1))):'No comparable dated values in this view';
  const root=$('ranking-rows');root.replaceChildren();
  visibleRows.forEach(company=>{
    const m=metricFor(company),known=eligible(company),tr=el('tr');tr.dataset.ticker=company.ticker;if(isCoupon)tr.dataset.instrument=m.id;
    const shownRank=known&&!unranked?String(cohortRanks.get(company.ticker)):'—';
    const rankCell=el('td',shownRank,'rank-number');if(isCoupon)rankCell.setAttribute('aria-label','Reference example; not ranked');
    const identity=el('td'),button=el('button',undefined,'company-button');button.type='button';button.setAttribute('aria-label',`Inspect ${company.name} (${companyCode(company)})${isCoupon?' — '+m.instrument:''} and its source evidence`);button.onclick=()=>openCompany(company.ticker);
    const text=el('span');text.append(el('strong',company.name),el('small',`${companyCode(company)} / ${groupName(company.group)}`));if(listingLabel(company))text.append(el('span',listingLabel(company),'listing-badge'));button.append(el('span',company.ticker.slice(0,1),'monogram'),text);identity.append(button,el('span',company.business||'Business scope not supplied','business-label'));
    if(company.comparison_caveat)identity.append(el('p',company.comparison_caveat,'comparison-caveat'));
    const selected=compareTickers.includes(company.ticker),compare=el('button',selected?'✓ Selected':'+ Compare','compare-toggle');compare.type='button';compare.dataset.compare=company.ticker;if(isCoupon)compare.dataset.compareInstrument=m.id;compare.setAttribute('aria-pressed',String(selected));compare.setAttribute('aria-label',(selected?'Remove ':'Add ')+company.name+(selected?' from':' to')+' side-by-side comparison');if(!selected&&compareTickers.length>=3){compare.setAttribute('aria-disabled','true');compare.title='Remove a selected company before choosing another.';}compare.onclick=()=>toggleComparison(company.ticker,isCoupon?m.id:null);identity.append(compare);const fundingAction=el('button','Cash & funding →','cash-funding-action');fundingAction.type='button';fundingAction.dataset.liquidityCompany=company.ticker;fundingAction.setAttribute('aria-label','Read '+company.name+' cash and funding details');fundingAction.onclick=()=>openCompany(company.ticker,'liquidity');identity.append(fundingAction);
    const value=el('td'),valueText=el('span',known?displayValue(company):'Not comparable / unknown','metric-value'+(known?'':' unknown'));
    if(known)valueText.title=state.metric==='debt'?currencyAmount(m.value,m.unit,false)+' · borrowings (leases excluded)':displayValue(company);value.append(valueText);
    if(!known&&['debt','assets','cash'].includes(state.metric)&&isValue(m.value)&&m.unit!=='USD'){valueText.textContent=displayValue(company)+' · excluded';value.append(el('span','Different currency; no USD conversion.','metric-subtext'));}
    if(isCoupon){value.append(el('span',m.instrument||'No eligible note terms','metric-subtext'));if(m.type||m.maturity)value.append(el('span',[noteType(m.type),m.maturity?'Due '+m.maturity:null].filter(Boolean).join(' · '),'metric-subtext'));value.append(el('span',m.issuer||m.scope||'Issuer / scope unknown','metric-subtext'),el('span',outstandingLabel(m),'note-outstanding-mobile'));if(m.issue_date_note)value.append(el('span',m.issue_date_note,'metric-subtext'));}
    else if(!isCash)appendAssetShare(value,company);
    if(state.metric==='debt'||state.metric==='debt_assets')appendRateSummary(value,company);
    if(isCash){value.append(el('p',companyTakeaway(company),'company-takeaway'));const qualification=el('details',undefined,'cash-row-qualification');qualification.append(el('summary','Cash restrictions & scope'),el('p',cashQualification(company),'cash-qualification'));value.append(qualification);}
    if(!known)value.append(el('span',m.note||'A comparable, source-backed value is not available.','metric-subtext'));
    value.append(el('span','As of '+dateLabel(rowDate(company)),'mobile-date'));
    const date=el('td',undefined,'date-cell');date.append(el('span',dateLabel(rowDate(company)),'row-date'));const dateMeta=el('small',state.metric==='coupon'?(m.issue_date?'Issued '+m.issue_date:'Issue date unknown'):`${(company.form||'Disclosure').replaceAll('_',' ')}${company.filed_at?' · source date '+company.filed_at:''}`);date.firstChild.append(dateMeta);
    const status=el('td',undefined,'status-cell');status.append(el('span',isCoupon?outstandingBadge(m):(known?'Source-backed':'Not ranked'),'evidence-pill'+(isCoupon&&m.outstanding_status!=='verified_at_snapshot'||!known?' unknown':'')),el('div',isCoupon?outstandingLabel(m):(known?sourceIDs(m).length+' linked source'+(sourceIDs(m).length===1?'':'s'):'Scope or evidence incomplete'),'evidence-detail'));
    const inspect=el('td'),arrow=el('button','→','inspect-button');arrow.type='button';arrow.setAttribute('aria-label','Open '+company.name+' details');arrow.onclick=()=>openCompany(company.ticker);inspect.append(arrow);
    const funding=el('td',undefined,'funding-summary-cell');funding.hidden=!isCash;if(isCash)funding.append(renderFundingSummary(company));
    tr.append(rankCell,identity,value,funding,date,status,inspect);root.append(tr);
  });
  $('ranking-table').hidden=visibleRows.length===0;$('empty').hidden=visibleRows.length!==0;
  $('empty-title').textContent=isCoupon?'No note examples match this view.':'No companies match this view.';
  $('empty-description').textContent=isCoupon?'Try another company, choose all note types and statuses, or broaden the peer group.':'Try another ticker, clear the search, or choose a broader peer group.';
  $('clear-search').textContent=isCoupon?'Clear search & note filters':'Clear search';
  document.querySelectorAll('[data-guide-metric]').forEach(button=>button.disabled=false);
  const sourceExample=visibleRows[0];$('guide-source').disabled=!sourceExample;$('guide-source').textContent=sourceExample?'Open '+sourceExample.name+'’s sources →':'Clear search to inspect a source';
  renderComparisonTray();renderRateCards();
  updateURL();
}
function appendAssetShare(parent,company){
  const ratio=metricFor(company,'debt_assets'),assets=metricFor(company,'assets'),debt=metricFor(company,'debt'),snapshot=company.as_of;
  const sameDate=[ratio,assets,debt].every(metric=>(metric.as_of||snapshot)===snapshot),known=eligible(company,'debt_assets')&&eligible(company,'assets')&&eligible(company,'debt')&&sameDate&&Number(assets.value)>0;
  const section=el('div',undefined,'debt-asset-share');section.append(el('span','Borrowings / recorded assets','asset-meter-label'));
  if(!known){section.append(el('span','Ratio unavailable — source-backed borrowings and assets from the same snapshot are required.','asset-share-unknown'));parent.append(section);return;}
  if(state.metric==='debt')section.append(el('strong',percent(ratio.value,2),'asset-share-value'));
  const track=el('div',undefined,'bar-track asset-meter'),fill=el('div',undefined,'bar-fill asset-meter-fill');track.setAttribute('role','img');track.setAttribute('aria-label',percent(ratio.value,2)+' borrowings / recorded assets; meter scale 0 to 100 percent'+(Number(ratio.value)>100?'; value exceeds the displayed scale':''));fill.style.width=Math.min(100,Number(ratio.value))+'%';track.append(fill);section.append(track);
  const axis=el('div',undefined,'asset-meter-axis');axis.setAttribute('aria-hidden','true');axis.append(el('span','0%'),el('span','100% of recorded assets'));section.append(axis);
  if(Number(ratio.value)>100)section.append(el('p','Borrowings exceed recorded assets. The full percentage is shown; the meter stops at 100%. This is not a health score.','asset-meter-overflow'));
  const denominator=el('details',undefined,'asset-denominator');denominator.append(el('summary','Assets, date & sources'),el('p','Recorded assets: '+currencyAmount(assets.value,assets.unit,false)),el('p','Borrowings: '+currencyAmount(debt.value,debt.unit,false)+' · leases excluded'),el('p','Same balance-sheet snapshot: '+dateLabel(snapshot)));
  if(Number(company.source_precision_usd)>1)denominator.append(el('p','USD figures converted from source amounts rounded to '+money(company.source_precision_usd)+'. Displayed zeros do not imply dollar precision.'));
  const ids=[...new Set([...sourceIDs(assets),...sourceIDs(debt),...sourceIDs(ratio)])];ids.forEach(id=>{const source=sourceMap.get(id);denominator.append(el('p','Source publication: '+dateLabel(source.published_at||source.published_date)));});denominator.append(el('p','Borrowings ÷ recorded assets × 100. Recorded assets include more than cash. This does not identify which assets were funded by debt.'));appendSourceLinks(denominator,ids);section.append(denominator);parent.append(section);
}
const RATE_KINDS=Object.freeze({issuer_reported_average:'Company-reported average',fixed_coupon:'Fixed note coupon',fixed_loan_rate:'Fixed loan rate',floating_formula:'Floating-rate formula',reported_floating_rate:'Reported variable rate',effective_instrument_rate:'Instrument accounting effective rate'});
function companyRates(company){return (data.financing_rates||[]).filter(rate=>rate.ticker===company.ticker);}
function primaryRate(company){const id=company.financing_rate_summary?.primary_rate_id;return companyRates(company).find(rate=>rate.id===id&&sourceIDs(rate).length)||null;}
function rateValue(rate){if(rate.kind==='floating_formula')return rate.formula||(rate.benchmark&&isValue(rate.spread_percent)?rate.benchmark+' + '+rate.spread_percent+' percentage points':'Formula unknown');return isValue(rate.rate_percent)?percent(rate.rate_percent,3):'Unknown';}
function rateStatus(rate){return rate.status==='verified_at_snapshot'?'Verified at stated snapshot':'Dated terms only; outstanding status not confirmed';}
function rateRecordDetails(rate){
  const body=el('article',undefined,'typed-rate-record');body.dataset.rateId=rate.id||'';body.append(el('h4',rate.instrument||'Named financing terms'),el('span',RATE_KINDS[rate.kind]||'Rate type not established','financing-rate-kind'),el('strong',rateValue(rate),'financing-rate-value'),el('p','Borrower: '+(rate.borrower||'Unknown')),el('p','Scope: '+(rate.scope||'Unknown'),'financing-rate-scope'),el('p','Rate reference date: '+dateLabel(rate.as_of)),el('p',rateStatus(rate),'financing-rate-status'));
  if(rate.kind==='floating_formula')body.append(el('p','All-in interest rate: Unknown. Benchmark fixing value and fixing date have not been established; the contract reference date is not a benchmark fixing date.','floating-rate-unknown'));
  if(rate.kind==='issuer_reported_average')body.append(el('p','Issuer-reported under this scope; not a uniform company-wide cost comparison.'));
  else body.append(el('p','Named financing example; not a company-wide average or highest financing rate.'));
  for(const [label,value]of[['Currency coverage',rate.currency_scope],['Method',rate.method],['Coverage limits',rate.coverage],['Source note',rate.note]])if(value)body.append(el('p',label+': '+value));
  sourceIDs(rate).forEach(id=>{const source=sourceMap.get(id);body.append(el('p','Source publication: '+dateLabel(source.published_at||source.published_date)));});appendSourceLinks(body,sourceIDs(rate));return body;
}
function appendRateSummary(parent,company,{allExamples=true}={}){
  const summary=company.financing_rate_summary,rate=primaryRate(company),box=el('div',undefined,'financing-rate-summary');box.dataset.ticker=company.ticker;if(rate)box.dataset.rateId=rate.id;
  box.append(el('span',rate?.kind==='issuer_reported_average'?'Company-reported average':'Named financing example','financing-rate-label'));
  if(rate){box.append(el('span',RATE_KINDS[rate.kind]||'Rate type not established','financing-rate-kind'),el('strong',rateValue(rate),'financing-rate-value'),el('p',rate.instrument||'Named instrument not established','financing-rate-instrument'),el('p',rate.scope||summary?.selection_scope||'Scope unknown','financing-rate-scope'),el('p','Reference '+dateLabel(rate.as_of)+' · '+rateStatus(rate),'financing-rate-status'));
    if(rate.kind==='floating_formula')box.append(el('p','All-in rate: Unknown. Benchmark fixing value and date unknown.','floating-rate-unknown'));
    if(rate.kind==='effective_instrument_rate')box.append(el('p','Accounting effective rate; not the cash coupon.','financing-rate-note'));
    if(rate.kind==='issuer_reported_average')box.append(el('p','Scope-specific issuer average; methods and coverage differ between companies.','financing-rate-note'));
  }else box.append(el('strong','Unknown','financing-rate-value'),el('p',summary?.note||'A selected financing rate has not been established in this review. No company-wide average is inferred.','financing-rate-note'));
  const examples=companyRates(company);if(examples.length){const details=el('details',undefined,'financing-rate-details');details.append(el('summary',allExamples?'Rate sources & all '+examples.length+' reviewed example'+(examples.length===1?'':'s'):'Rate terms & source'));if(summary?.note)details.append(el('p',summary.note));(allExamples?examples:[rate].filter(Boolean)).forEach(example=>details.append(rateRecordDetails(example)));box.append(details);}
  parent.append(box);
}
function rateCompanies(){const query=state.q.trim().toLocaleLowerCase('en-US');return data.companies.filter(inGroup).filter(company=>!query||[company.ticker,company.name,company.business,...companyRates(company).flatMap(rate=>[rate.instrument,rate.borrower])].join(' ').toLocaleLowerCase('en-US').includes(query)).sort((a,b)=>a.name.localeCompare(b.name));}
function renderRateCards(){
  const host=$('company-rate-examples');host.hidden=state.metric!=='coupon';if(host.hidden)return;
  const companies=rateCompanies(),cards=$('company-rate-cards');cards.replaceChildren();
  $('rate-company-count').textContent=companies.length+' compan'+(companies.length===1?'y':'ies')+' · alphabetical, not ordered by interest rate';
  companies.forEach(company=>{const card=el('article',undefined,'company-rate-card');card.dataset.ticker=company.ticker;card.append(el('h4',company.name),el('small',companyCode(company)+' / '+groupName(company.group)));if(listingLabel(company))card.append(el('span',listingLabel(company),'listing-badge'));if(company.comparison_caveat)card.append(el('p',company.comparison_caveat,'comparison-caveat'));appendRateSummary(card,company);cards.append(card);});
  if(!companies.length)cards.append(el('p','No company rate references match this search. Clear the search or broaden the peer group.'));
}
function renderComparisonTray(){
  const tray=$('comparison-tray');tray.hidden=compareTickers.length===0;
  $('selection-count').textContent=`${compareTickers.length} of 3 selected`;
  const chips=$('selected-companies');chips.replaceChildren();
  compareTickers.forEach(ticker=>{const company=data.companies.find(c=>c.ticker===ticker),button=el('button',(listingLabel(company)?company.name:ticker)+' ×','selection-chip');button.type='button';button.setAttribute('aria-label','Remove '+company.name+' from comparison');button.onclick=()=>toggleComparison(ticker);chips.append(button);});
  const action=$('open-comparison');action.disabled=compareTickers.length<2;action.textContent=compareTickers.length<2?'Choose one more company':`Compare ${compareTickers.length} companies →`;
}
function toggleComparison(ticker,instrumentId=null){
  if(!data.companies.some(c=>c.ticker===ticker))return;
  if(compareTickers.includes(ticker))compareTickers=compareTickers.filter(t=>t!==ticker);
  else{if(compareTickers.length>=3){showToast('Up to three companies. Remove one from the tray to choose another.');return;}compareTickers.push(ticker);}
  render();
  const trigger=[...document.querySelectorAll('[data-compare]')].find(button=>button.dataset.compare===ticker&&(!instrumentId||button.dataset.compareInstrument===instrumentId));
  if(trigger)trigger.focus({preventScroll:true});else if(compareTickers.length)$('open-comparison').focus({preventScroll:true});else $('search').focus({preventScroll:true});
}
function comparisonCell(company,key){
  const m=metricFor(company,key),cell=el('td'),known=eligible(company,key),foreign=['debt','assets','cash'].includes(key)&&isValue(m.value)&&m.unit!=='USD',value=el('strong',known?displayValue(company,key):foreign?displayValue(company,key)+' · excluded':'Not comparable / unknown','comparison-value'+(known?'':' unknown'));cell.append(value);
  if(foreign)cell.append(el('p','Original currency; no USD conversion.'));
  if(key==='debt')cell.append(el('p','Loans and notes; operating and finance leases excluded.'));
  if(key==='debt_assets')cell.append(el('p','Borrowings per $100 of recorded assets. Not a credit rating.'));
  if(m.basis)cell.append(el('p',m.basis));
  if(key==='cash')cell.append(el('p',cashQualification(company),'cash-qualification'));
  if(!known&&m.note)cell.append(el('p',m.note));
  cell.append(el('p','As of '+dateLabel(m.as_of||company.as_of),'comparison-date'));
  return cell;
}
function openComparison(){
  const companies=compareTickers.map(t=>data.companies.find(c=>c.ticker===t)).filter(Boolean);if(companies.length<2)return;
  const content=$('comparison-content');content.replaceChildren();
  const groups=new Set(companies.map(c=>c.group)),dates=new Set(companies.map(c=>c.as_of));
  const context=el('p',undefined,'comparison-context');context.textContent=(groups.size>1?'Different business models are selected. ':'')+(dates.size>1?'Reporting dates differ. ':'')+'Read each company’s date and scope; no winner or combined health score is inferred.';content.append(context);
  content.append(el('p','On smaller screens, scroll the table sideways to compare columns.','comparison-scroll-hint'));
  const wrap=el('div',undefined,'comparison-table-wrap');wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Side-by-side company measurements; scroll horizontally if needed');
  const table=el('table',undefined,'comparison-table');table.style.setProperty('--comparison-columns',String(companies.length));const caption=el('caption','Reported borrowing and balance-sheet figures; selected coupon examples are separate historical instrument terms.');caption.className='sr-only';table.append(caption);
  const head=el('thead'),headRow=el('tr'),corner=el('th','Measure');corner.scope='col';headRow.append(corner);companies.forEach(company=>{const cell=el('th');cell.scope='col';cell.append(el('strong',company.name),el('small',companyCode(company)+' / '+groupName(company.group)));if(listingLabel(company))cell.append(el('span',listingLabel(company),'listing-badge'));headRow.append(cell);});head.append(headRow);table.append(head);
  const body=el('tbody');
  const scope=el('tr'),scopeLabel=el('th','Reporting scope');scopeLabel.scope='row';scope.append(scopeLabel);companies.forEach(company=>{const cell=el('td');cell.append(el('p',company.scope||company.business),el('p','Balance sheet: '+dateLabel(company.as_of),'comparison-date'),el('p','Source date: '+dateLabel(company.filed_at),'comparison-date'));if(company.comparison_caveat)cell.append(el('p',company.comparison_caveat,'comparison-caveat'));scope.append(cell);});body.append(scope);
  for(const [key,label]of[['debt','Borrowings'],['debt_assets','Borrowings / assets'],['assets','Recorded assets'],['cash','Cash & cash equivalents']]){const row=el('tr'),labelCell=el('th',label);labelCell.scope='row';row.append(labelCell,...companies.map(company=>comparisonCell(company,key)));body.append(row);}
  const credit=el('tr',undefined,'comparison-credit-row'),creditLabel=el('th','Company-wide available credit');creditLabel.scope='row';credit.append(creditLabel);companies.forEach(company=>{const cell=el('td'),fact=company.liquidity?.company_available_credit;cell.append(renderFundingSummary(company));const button=el('button','Cash & credit details →','outline-button');button.type='button';button.dataset.liquidityCompany=company.ticker;button.setAttribute('aria-label','Read '+company.name+' cash and credit details');button.onclick=()=>openCompany(company.ticker,'liquidity');cell.append(button);credit.append(cell);});body.append(credit);
  const precision=el('tr'),precisionLabel=el('th','Source rounding');precisionLabel.scope='row';precision.append(precisionLabel);companies.forEach(company=>{const cell=el('td');cell.append(el('p',Number(company.source_precision_usd)>1?'USD amounts converted from figures rounded to '+money(company.source_precision_usd)+'. Displayed zeros do not imply dollar precision.':'Read the original source units; displayed USD figures retain the disclosure’s precision.'));precision.append(cell);});body.append(precision);
  const coupons=el('tr'),couponLabel=el('th','One coupon example');couponLabel.scope='row';coupons.className='comparison-coupon-row';coupons.append(couponLabel);companies.forEach(company=>{const m=metricFor(company,'coupon'),cell=el('td'),hasNote=isValue(m.value)||Boolean(m.instrument);cell.append(el('strong',eligible(company,'coupon')?displayValue(company,'coupon'):'Unknown','comparison-value'));if(hasNote){cell.append(el('p',m.instrument||'Selected note terms'));if(m.type)cell.append(el('p',noteType(m.type)));if(m.issuer)cell.append(el('p','Issuer / scope: '+m.issuer));cell.append(el('p',m.maturity?'Matures '+m.maturity:'Maturity unknown'),el('p',m.issue_date?'Issued '+m.issue_date:'Issue date unknown'),el('p','Terms observed: '+dateLabel(m.as_of||company.as_of),'comparison-date'));if(m.outstanding_principal)appendPrincipal(cell,m);}else cell.append(el('p',m.note||'A selected note coupon has not been established in this review.'));coupons.append(cell);});body.append(coupons);
  const evidence=el('tr'),evidenceLabel=el('th','Read the evidence');evidenceLabel.scope='row';evidence.append(evidenceLabel);companies.forEach(company=>{const cell=el('td'),button=el('button','Sources & calculation →','outline-button');button.type='button';button.setAttribute('aria-label','Read '+company.name+' sources and calculation');button.onclick=()=>openCompany(company.ticker);cell.append(button);evidence.append(cell);});body.append(evidence);
  table.append(body);wrap.append(table);content.append(wrap,el('p','Coupon examples are terms of different instruments, not comparable company borrowing costs or current market yields. Continued outstanding status has not been reverified for every example.','comparison-coupon-note'));
  if(!$('comparison-dialog').open)$('comparison-dialog').showModal();updateURL();
}
function appendMetric(parent,company,key,label){
  const m=metricFor(company,key),card=el('article',undefined,'detail-metric'),sourced=sourceIDs(m).length>0,hasValue=isValue(m.value),hasNote=key==='coupon'&&(hasValue||Boolean(m.instrument));card.append(el('h3',key==='coupon'&&!hasNote?'Note coupon example':label));
  card.append(el('strong',hasValue?displayValue(company,key,false):'Unknown',hasValue?'':'unknown'));
  if(!sourced&&hasValue)card.append(el('p','Source linkage incomplete; excluded from ranking.'));
  if(key==='debt_assets'&&hasValue)card.append(el('p',`About $${Number(m.value).toFixed(2)} of borrowings per $100 of recorded assets. This does not identify which assets were funded with debt.`));
  if(hasNote){if(m.instrument)card.append(el('p',m.instrument));const terms=[noteType(m.type),m.issue_date?'Issued '+m.issue_date:'Issue date unknown',m.maturity?'Matures '+m.maturity:'Maturity unknown'].filter(Boolean);card.append(el('p',terms.join(' · ')));if(m.issuer)card.append(el('p','Issuer / scope: '+m.issuer));card.append(el('p','Selected note only. Coupon is not current market yield or the company’s overall cost of debt. Terms observed in dated disclosure; continued outstanding status has not been reverified for every example.'));if(m.selection_rule)card.append(el('p','Selection: '+m.selection_rule));if(m.outstanding_principal)appendPrincipal(card,m);}
  if(m.basis&&m.basis!=='unknown_unranked')card.append(el('p',m.basis));if(m.note)card.append(el('p',m.note));
  if(key==='cash')card.append(el('p',cashQualification(company),'cash-qualification'));
  if(['debt','assets','cash'].includes(key)&&hasValue&&m.unit!=='USD')card.append(el('p','Not comparable in the USD ranking. The original currency is shown without conversion.'));
  if(['debt','assets','cash'].includes(key)&&hasValue&&m.unit==='USD'&&Number(company.source_precision_usd)>1)card.append(el('p',`USD converted from source figures rounded to ${money(company.source_precision_usd)}. Displayed zeros do not imply dollar precision.`));
  card.append(el('p','As of '+dateLabel(m.as_of||company.as_of)));
  parent.append(card);
}
function appendSourceLinks(parent,ids){
  const links=el('div',undefined,'record-source-links');[...new Set(ids||[])].forEach(id=>{const source=sourceMap.get(id);if(source)links.append(safeLink(source.url,source.title||source.publisher||'Primary disclosure'));});if(links.childNodes.length)parent.append(links);
}
function appendCompanyNotes(parent,company){
  const notes=companyInstruments(company);if(!notes.length)return;
  const section=el('section',undefined,'detail-section company-note-examples');section.append(el('h3',`Observed note examples (${notes.length})`),el('p','Each is a separate instrument, not the company’s overall borrowing rate. Dated terms do not establish that every note remains outstanding. This is a curated set, not a complete debt inventory.'));
  notes.forEach(note=>{
    const card=el('article',undefined,'note-detail-card');card.dataset.instrument=note.id;card.append(el('h4',note.instrument||'Named note terms'),el('strong',isValue(note.value)?percent(note.value,3):'Coupon unknown','note-detail-rate'),el('span',note.currency?note.currency+' instrument':'Currency unknown','note-currency'),el('p',noteType(note.type)));
    card.append(el('p','Borrower / issuer: '+(note.issuer||'Unknown')),el('p','Scope: '+(note.scope||note.basis||'Unknown')));
    card.append(el('p',note.issue_date?'Issued: '+dateLabel(note.issue_date):'Issue date unknown'),el('p',note.maturity?'Maturity: '+note.maturity+(note.maturity_precision?' ('+note.maturity_precision+' precision)':''):'Maturity unknown'));
    if(note.issue_date_note)card.append(el('p',note.issue_date_note,'issue-date-note'));
    card.append(el('p','Terms observed: '+dateLabel(note.as_of)),el('p',outstandingLabel(note),'note-outstanding-status'));
    appendPrincipal(card,note);
    if(note.note)card.append(el('p',note.note));if(note.selection_rule)card.append(el('p','Selection: '+note.selection_rule));
    appendSourceLinks(card,[...sourceIDs(note),...sourceIDs(note.outstanding_principal||{})]);section.append(card);
  });parent.append(section);
}
function appendDebtContext(parent,company){
  const context=company.debt_context;if(!context)return;
  const bridges=Array.isArray(context.bridges)?context.bridges:[],leases=Array.isArray(context.leases)?context.leases:[],notes=Array.isArray(context.notes)?context.notes:[];if(!bridges.length&&!leases.length&&!notes.length)return;
  const details=el('details',undefined,'debt-context');details.append(el('summary','Principal, recorded debt and excluded leases'),el('p','Additional source context only. These figures are not added to the borrowing rankings, and partial schedules are not company-wide totals.'));
  bridges.forEach(bridge=>{
    const card=el('article',undefined,'bridge-card');card.append(el('h4',bridge.label||'Principal and carrying value'),el('p',bridge.complete_company_scope===true?'Company-wide scope as stated in the source.':bridge.scope==='consolidated_carrying_only'?'Company-wide recorded balance; principal total is not reconciled.':'PARTIAL SCOPE — these figures are not a complete company-wide debt total.','bridge-scope'+(bridge.complete_company_scope===true?'':' partial')));
    const scopeLabels={consolidated_borrowings:'Consolidated loans and notes',consolidated_carrying_only:'Company-wide recorded balance only',noncurrent_convertibles:'Long-term convertible notes only',convertible_notes_only:'Convertible and exchangeable notes only',notes_only:'Notes payable only; not total company borrowings'};
    if(bridge.scope)card.append(el('p',Object.hasOwn(scopeLabels,bridge.scope)?scopeLabels[bridge.scope]:bridge.scope));card.append(el('p','As of '+dateLabel(bridge.as_of)+' · '+(bridge.unit||'Unit unknown')));
    const list=el('dl',undefined,'context-values');for(const [label,value]of[[bridge.principal_label||'Principal',bridge.principal],['Recorded carrying amount',bridge.carrying],['Discounts, fees and other differences; see source note',bridge.difference]]){list.append(el('dt',label),el('dd',value===null||value===undefined||!sourceIDs(bridge).length?'Unknown':signedCurrencyAmount(value,bridge.unit)));}card.append(list);
    if(bridge.note)card.append(el('p',bridge.note));appendSourceLinks(card,sourceIDs(bridge));details.append(card);
  });
  if(leases.length){details.append(el('h4','Lease obligations excluded from ranked borrowings'),el('p','Lease rows can refer to overlapping scopes. They are shown separately; no lease total is inferred.'));leases.forEach(lease=>{const card=el('article',undefined,'lease-card'),label=lease.kind==='finance'?'Finance leases':lease.kind==='operating'?'Operating leases':lease.kind==='all'?'Combined lease obligation disclosure':'Lease disclosure';card.append(el('h4',label),el('strong',isValue(lease.value)&&sourceIDs(lease).length?currencyAmount(lease.value,lease.unit,false):'Unknown'),el('p','As of '+dateLabel(lease.as_of)));if(lease.note)card.append(el('p',lease.note));appendSourceLinks(card,sourceIDs(lease));details.append(card);});}
  if(notes.length){const list=el('ul');notes.forEach(note=>list.append(el('li',note)));details.append(list);}parent.append(details);
}
function cashQualification(company){return company.liquidity?.cash_caveat||'Cash is shown under the company’s stated scope. It is separate from facility commitments or conditional credit.';}
function liquidityFactKnown(fact){return fact&&isValue(fact.value)&&typeof fact.unit==='string'&&sourceIDs(fact).length>0;}
function liquiditySourceIDs(company){const liquidity=company.liquidity;if(!liquidity)return [];return [...sourceIDs(liquidity.company_available_credit||{}),...(liquidity.excluded_balances||[]).flatMap(sourceIDs),...(liquidity.facilities||[]).flatMap(facility=>[...sourceIDs(facility),...(facility.amounts||[]).flatMap(sourceIDs)])];}
function fundingFacts(company){return (company.liquidity?.facilities||[]).flatMap(facility=>(facility.amounts||[]).filter(fact=>liquidityFactKnown(fact)&&fact.as_of===company.as_of&&(['reported_available','unused_capacity'].includes(fact.kind)||(fact.kind==='lc_capacity'&&/remaining/i.test(fact.label||'')&&!/sublimit/i.test(fact.label||'')))).map(fact=>({facility,fact})));}
function renderFundingSummary(company){
  const root=el('div',undefined,'funding-summary'),facilities=company.liquidity?.facilities||[],total=company.liquidity?.company_available_credit;
  root.append(el('span','Company-wide available credit','funding-total-label'),el('strong',liquidityFactKnown(total)?currencyAmount(total.value,total.unit):'Total not established','funding-total-status credit-availability-value'),el('p',facilities.length+' selected facilit'+(facilities.length===1?'y':'ies')+' reviewed; not a complete company inventory.','funding-facility-count'));
  const facts=fundingFacts(company);
  facts.forEach(({facility,fact})=>{const row=el('div',undefined,'funding-amount');row.dataset.kind=fact.kind;row.append(el('span',facility.name),el('strong',(fact.precision||fact.precision_note?'Approx. ':'')+(fact.unit==='USD'?new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:3}).format(Number(fact.value)):currencyAmount(fact.value,fact.unit))),el('span',fact.kind==='lc_capacity'?'Remaining letter-of-credit capacity only — not cash':fact.kind==='unused_capacity'?'Conditional unfunded commitment — not cash':'Reported facility availability — subject to conditions'),el('small','As of '+dateLabel(fact.as_of)));const context=el('details',undefined,'funding-amount-context');context.append(el('summary','Conditions & source basis'));if(fact.basis)context.append(el('p',fact.basis));(facility.conditions||[]).forEach(condition=>context.append(el('p',condition)));if(fact.precision||fact.precision_note)context.append(el('p',fact.precision||fact.precision_note));appendSourceLinks(context,sourceIDs(fact));row.append(context);root.append(row);});
  if(!facts.length)root.append(el('p','No sourced remaining availability amount established here. Missing does not mean zero.','funding-unknown'));
  root.append(el('p','Separate facility amounts; not added together or to cash.','funding-separation'));return root;
}
function companyTakeaway(company){if(company.liquidity?.takeaway)return company.liquidity.takeaway;const cash=metricFor(company,'cash');return (liquidityFactKnown(cash)?currencyAmount(cash.value,cash.unit)+' reported cash as of '+dateLabel(cash.as_of||company.as_of)+'. ':'Reported cash is unknown. ')+(company.business||'Company-wide business scope applies.')+' Company-wide available credit is not established by this selected-facility review.';}
function renderLiquidityFact(fact){
  const row=el('div',undefined,'liquidity-fact');row.dataset.kind=fact.kind||'unknown';row.append(el('span',fact.label||'Reported facility amount','liquidity-fact-label'),el('strong',liquidityFactKnown(fact)?currencyAmount(fact.value,fact.unit):'Unknown','liquidity-fact-value'),el('span','As of '+dateLabel(fact.as_of)+' · '+(fact.unit||'Unit unknown'),'liquidity-fact-date'));
  const explanations={commitment:'Facility size or limit; not cash and not the amount borrowed.',drawn:'Amount already borrowed under this facility; not new cash available.',reported_available:'Availability reported for this facility at its stated date, subject to access conditions.',unused_capacity:'Unused capacity; conditions may limit whether it can be drawn.',letters_of_credit:'Letters of credit use facility capacity; they are not available cash.',borrowing_cap:'A borrowing limit; not an outstanding balance or the remaining amount available.',lc_capacity:'Letter-of-credit capacity; not cash available to spend.',restricted_cash:'Restrictions can limit how this cash is spent; it is shown separately from the cash measure.',restricted_investments:'Restricted investments are not the cash figure shown above.'};
  const detail=el('details',undefined,'liquidity-fact-context');detail.append(el('summary','Meaning & source basis'));if(explanations[fact.kind])detail.append(el('p',explanations[fact.kind],'liquidity-fact-meaning'));if(fact.basis)detail.append(el('p',fact.basis));row.append(detail);[...new Set([fact.precision,fact.precision_note].filter(value=>typeof value==='string'&&value.trim()))].forEach(text=>row.append(el('p',text,'liquidity-precision')));return row;
}
function appendLiquidity(parent,company){
  const liquidity=company.liquidity,section=el('section',undefined,'detail-section cash-funding');section.tabIndex=-1;section.setAttribute('aria-labelledby','cash-funding-title');const title=el('h3','Cash & funding');title.id='cash-funding-title';section.append(title,el('p',companyTakeaway(company),'company-takeaway'),el('p','Cash, facility commitments and amounts that might be borrowed are different. They are not added together here.'),el('p','A letter of credit supports a payment obligation to someone else. It can use a credit line’s capacity without putting cash in the company’s bank account.'));
  const cash=metricFor(company,'cash'),reportedCash=el('div',undefined,'liquidity-reported-cash');reportedCash.append(el('h4','Reported cash and equivalents'));const cashValue=el('strong',liquidityFactKnown(cash)?currencyAmount(cash.value,cash.unit):'Unknown','liquidity-cash-value');if(liquidityFactKnown(cash))cashValue.title=currencyAmount(cash.value,cash.unit,false);reportedCash.append(cashValue,el('p','As of '+dateLabel(cash.as_of||company.as_of),'liquidity-fact-date'),el('p',cashQualification(company),'cash-qualification'));appendSourceLinks(reportedCash,sourceIDs(cash));section.append(reportedCash);
  const available=liquidity?.company_available_credit,availability=el('div',undefined,'company-credit-availability');availability.append(el('h4','Company-wide available credit'),el('strong',liquidityFactKnown(available)?currencyAmount(available.value,available.unit):'Total not established','credit-availability-value'),el('p',available?.note||'Company-wide available credit has not been established from a complete facility inventory. Unknown does not mean zero.'));if(available?.as_of)availability.append(el('p','As of '+dateLabel(available.as_of)));appendSourceLinks(availability,sourceIDs(available||{}));section.append(availability);
  const excluded=el('div',undefined,'excluded-liquidity-balances');excluded.append(el('h4','Balances kept separate from cash'));
  if(liquidity?.excluded_balances?.length){liquidity.excluded_balances.forEach(fact=>{const row=renderLiquidityFact(fact);appendSourceLinks(row,sourceIDs(fact));excluded.append(row);});}else excluded.append(el('p','A separate inventory of excluded or restricted balances has not been established here. Do not read missing balances as zero.'));section.append(excluded);
  const facilities=liquidity?.facilities||[],facilityList=el('div',undefined,'liquidity-facilities');facilityList.append(el('h4','Selected borrowing facilities'));
  if(!facilities.length)facilityList.append(el('p','No verified facility inventory is available in this review. This does not establish that the company has no facilities or no borrowing capacity.','liquidity-inventory-unknown'));
  facilities.forEach(facility=>{const card=el('article',undefined,'liquidity-facility');card.dataset.facility=facility.id||'';card.append(el('h4',facility.name||'Selected facility'),el('p','Borrower: '+(facility.borrower||'Unknown')),el('p','Scope: '+(facility.scope||'Unknown')));if(facility.access_note)card.append(el('p',facility.access_note,'facility-access-note'));const amounts=el('div',undefined,'facility-amounts');(facility.amounts||[]).forEach(fact=>amounts.append(renderLiquidityFact(fact)));if(!facility.amounts?.length)amounts.append(el('p','Facility amounts have not been established.'));card.append(amounts);card.append(el('h5','What can limit access?'));if(facility.conditions?.length){const list=el('ul',undefined,'facility-conditions');facility.conditions.forEach(condition=>list.append(el('li',condition)));card.append(list);}else card.append(el('p','Separate access conditions have not been captured here; read the source before assuming the capacity can be used.'));appendSourceLinks(card,[...sourceIDs(facility),...(facility.amounts||[]).flatMap(sourceIDs)]);facilityList.append(card);});section.append(facilityList);
  if(liquidity?.notes?.length){const notes=el('ul',undefined,'liquidity-notes');liquidity.notes.forEach(note=>notes.append(el('li',note)));section.append(notes);}parent.append(section);
}
function openCompany(ticker,targetSection=null){
  const company=data.companies.find(c=>c.ticker===ticker);if(!company)return;
  detailTicker=ticker;$('detail-ticker').textContent=`${companyCode(company)} / ${groupName(company.group)}`;$('detail-title').textContent=company.name;
  const content=$('detail-content');content.replaceChildren(el('p',company.business||'Business description not available.','detail-business'));
  if(listingLabel(company)){content.append(el('p',listingLabel(company),'listing-badge'));if(company.ticker_note)content.append(el('p',company.ticker_note,'detail-business'));}
  if(company.comparison_caveat)content.append(el('p',company.comparison_caveat,'comparison-caveat'));
  const status=el('div',undefined,'detail-status');status.append(el('strong',`Dated disclosure: ${dateLabel(company.as_of)}`),el('div',`${(company.form||'Company disclosure').replaceAll('_',' ')}${company.filed_at?' · source date '+dateLabel(company.filed_at):''}. These are reported figures under the stated scope, not a live market feed.`));content.append(status);
  const metrics=el('div',undefined,'detail-metrics');[['debt','Reported debt'],['debt_assets','Debt / recorded assets'],['assets','Total reported assets'],['cash','Cash & cash equivalents'],['coupon','Selected note coupon']].forEach(([key,label])=>appendMetric(metrics,company,key,label));content.append(metrics);
  appendLiquidity(content,company);
  const components=metricFor(company,'debt').components;
  if(Array.isArray(components)&&components.length){const section=el('section',undefined,'detail-section'),table=el('table',undefined,'reconciliation'),caption=el('caption','How the reported borrowing balance is reconciled'),tbody=el('tbody');table.append(caption);for(const component of components){const row=el('tr'),label=el('th',component.label||'Borrowing component');label.scope='row';const amount=el('td',(component.operation==='subtract'?'− ':'+ ')+currencyAmount(component.value,component.unit||metricFor(company,'debt').unit,false));row.append(label,amount);tbody.append(row);}table.append(tbody);section.append(el('h3','See the borrowing calculation'),table);if(metricFor(company,'debt').unit==='USD'&&Number(company.source_precision_usd)>1)section.append(el('p',`USD values converted from disclosures rounded to ${money(company.source_precision_usd)}; they are not precise to individual dollars.`));content.append(section);}
  appendDebtContext(content,company);const rates=el('section',undefined,'detail-section company-financing-rates');rates.append(el('h3','Financing rate references'));appendRateSummary(rates,company);content.append(rates);appendCompanyNotes(content,company);
  const notes=(company.notes||[]).filter(Boolean);
  if(notes.length){const section=el('section',undefined,'detail-section'),list=el('ul');section.append(el('h3','What to keep in mind'));notes.forEach(note=>list.append(el('li',note)));section.append(list);content.append(section);}
  const ids=new Set([...(company.source_ids||[]),...Object.values(company.metrics||{}).flatMap(m=>Array.isArray(m?.source_ids)?m.source_ids:[]),...companyInstruments(company).flatMap(note=>[...sourceIDs(note),...sourceIDs(note.outstanding_principal||{})]),...(company.debt_context?.bridges||[]).flatMap(sourceIDs),...(company.debt_context?.leases||[]).flatMap(sourceIDs),...liquiditySourceIDs(company),...companyRates(company).flatMap(sourceIDs),...sourceIDs(company.financing_rate_summary||{})]),sources=[...ids].map(id=>sourceMap.get(id)).filter(Boolean),ledger=el('section',undefined,'detail-section');ledger.append(el('h3','Read the evidence'));
  if(!sources.length)ledger.append(el('p','No linked primary source is available for this company. Missing evidence does not mean zero debt.'));
  sources.forEach(source=>{const card=el('article',undefined,'source-card'),title=el('h4');title.append(safeLink(source.url,source.title||source.publisher||'Primary disclosure'));card.append(title,el('p',`${source.publisher||'Primary source'} · publication ${dateLabel(source.published_at||source.published_date)}${source.retrieved_at?' · retrieved '+source.retrieved_at:''}`));if(source.source_unit)card.append(el('p','Source units: '+source.source_unit));if(source.excerpt_note)card.append(el('p',source.excerpt_note,'source-excerpt-note'));if(source.excerpt)card.append(el('blockquote',source.excerpt));ledger.append(card);});content.append(ledger);
  updateURL();if(!$('company-dialog').open)$('company-dialog').showModal();
  if(targetSection==='liquidity'){const target=content.querySelector('.cash-funding');target.style.scrollMarginTop=($('company-dialog').querySelector('.dialog-heading').offsetHeight+15)+'px';target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'auto'});}
}
function exportData(format){
  const rows=visibleRows.map(company=>{
    const m=metricFor(company),ids=sourceIDs(m),sources=ids.map(id=>sourceMap.get(id)),isCoupon=state.metric==='coupon',unranked=isCoupon||state.metric==='cash';
    const principal=isCoupon&&principalKnown(m)?m.outstanding_principal:null;
    return {ticker:company.ticker,display_code:companyCode(company),listing_status:company.listing_status||null,trading_ticker:company.listing_status==='listed'?company.ticker:null,ticker_note:company.ticker_note||null,name:company.name,group:company.group,metric:state.metric,
      value:eligible(company)?m.value:null,reported_value:m.value??null,unit:m.unit||'unknown',currency:m.currency||(['debt','assets','cash'].includes(state.metric)?m.unit:null),
      ranked:!unranked&&eligible(company),cohort_rank:!unranked?(cohortRanks.get(company.ticker)||null):null,as_of:rowDate(company)||null,
      source_date:sources[0]?.published_at||null,source_dates:sources.map(s=>s.published_at||null),
      company_as_of:company.as_of,company_source_date:company.filed_at||null,
      borrowings_assets_percent:eligible(company,'debt_assets')?metricFor(company,'debt_assets').value:null,assets_value:eligible(company,'assets')?metricFor(company,'assets').value:null,assets_unit:metricFor(company,'assets').unit||null,assets_as_of:metricFor(company,'assets').as_of||company.as_of,assets_source_ids:sourceIDs(metricFor(company,'assets')),asset_share_disclosure:'Precomputed borrowings / recorded assets percentage; meter uses a fixed 0–100% scale with values above 100% labeled in full. Not a health score or a claim that these assets were funded by debt.',
      cash_value:eligible(company,'cash')?company.metrics.cash.value:null,cash_unit:company.metrics.cash.unit,cash_as_of:company.metrics.cash.as_of||company.as_of,cash_qualification:cashQualification(company),company_takeaway:companyTakeaway(company),cash_source_ids:sourceIDs(company.metrics.cash),cash_source_urls:sourceIDs(company.metrics.cash).map(id=>sourceMap.get(id).url),
      financing_rate_summary:company.financing_rate_summary||null,primary_financing_rate:primaryRate(company),financing_rate_examples:companyRates(company),rate_source_ids:[...new Set([...companyRates(company).flatMap(sourceIDs),...sourceIDs(company.financing_rate_summary||{})])],
      liquidity:company.liquidity||null,liquidity_source_ids:liquiditySourceIDs(company),liquidity_disclosure:'Cash, restricted balances and conditional credit are separate. No cash-plus-credit total or company-wide funding score is inferred.',
      source_precision_usd:isCoupon||m.unit!=='USD'?null:(company.source_precision_usd||null),
      scope:isCoupon?(m.scope||m.basis||m.issuer||''):(company.scope||m.scope||''),
      basis:m.basis||'',note:m.note||'',comparison_caveat:company.comparison_caveat||'',company_notes:company.notes||[],instrument_id:isCoupon?m.id||null:null,instrument:m.instrument||'',instrument_type:m.type||null,
      issuer:m.issuer||null,issue_date:m.issue_date||null,issue_date_note:m.issue_date_note||null,maturity:m.maturity||null,maturity_precision:m.maturity_precision||null,
      outstanding_status:isCoupon?m.outstanding_status||'terms_only':null,outstanding_principal:principal?.value??null,outstanding_principal_label:m.outstanding_principal?.label||null,outstanding_principal_basis:m.outstanding_principal?.basis||null,outstanding_principal_unit:principal?.unit??null,outstanding_principal_as_of:principal?.as_of??null,outstanding_principal_source_ids:principal?sourceIDs(principal):[],outstanding_principal_source_urls:principal?sourceIDs(principal).map(id=>sourceMap.get(id).url):[],
      market_yield:null,source_ids:ids,source_urls:sources.map(s=>s.url)};
  });
  let text,type;
  if(format==='json'){const cohort=rowsForCohort(),rateProfiles=rateCompanies().map(company=>({ticker:company.ticker,name:company.name,listing_status:company.listing_status||null,display_code:companyCode(company),trading_ticker:company.listing_status==='listed'?company.ticker:null,as_of:company.as_of,company_source_date:company.filed_at||null,financing_rate_summary:company.financing_rate_summary||null,primary_financing_rate:primaryRate(company),financing_rate_examples:companyRates(company)})),profileSourceIDs=new Set(rateCompanies().flatMap(company=>[...companyRates(company).flatMap(sourceIDs),...sourceIDs(company.financing_rate_summary||{})]));text=JSON.stringify({disclosure:'Reported historical financial information. No synthetic values. Coupon examples are instruments, not a company cost ranking. Continued outstanding status has not been reverified for every note example.',reviewed_at:data.reviewed_at,view:{...state,compare:[...compareTickers]},ranking_context:state.metric==='cash'?'Cash profiles are unranked; sorted by reported cash only. Facility amounts are shown separately with their dates and conditions. No cash-plus-credit total or health ranking is inferred.':'Ranks use the full selected peer cohort before text search. Meters show borrowings / recorded assets on a fixed 0–100% scale, not relative company size. Financing rate references and coupon rows are unranked; different rate kinds and scopes are not blended.',cohort_size:cohort.length,cohort_unit:state.metric==='coupon'?'notes':'companies',cohort_company_count:new Set(cohort.map(company=>company.ticker)).size,definition:metricDefinition(),coupon_selection_policy:data.coupon_selection_policy||null,company_rate_profiles:rateProfiles,rows,sources:data.sources.filter(s=>profileSourceIDs.has(s.id)||rows.some(r=>r.source_ids.includes(s.id)||r.assets_source_ids.includes(s.id)||r.outstanding_principal_source_ids.includes(s.id)||r.cash_source_ids.includes(s.id)||r.liquidity_source_ids.includes(s.id)||r.rate_source_ids.includes(s.id)))},null,2);type='application/json';}
  else{const keys=['ticker','display_code','listing_status','trading_ticker','ticker_note','name','group','metric','value','reported_value','unit','currency','ranked','cohort_rank','as_of','source_date','source_dates','company_as_of','company_source_date','borrowings_assets_percent','assets_value','assets_unit','assets_as_of','assets_source_ids','asset_share_disclosure','cash_value','cash_unit','cash_as_of','cash_qualification','company_takeaway','cash_source_ids','cash_source_urls','financing_rate_summary','primary_financing_rate','financing_rate_examples','rate_source_ids','liquidity','liquidity_source_ids','liquidity_disclosure','source_precision_usd','scope','basis','note','comparison_caveat','company_notes','instrument_id','instrument','instrument_type','issuer','issue_date','issue_date_note','maturity','maturity_precision','outstanding_status','outstanding_principal','outstanding_principal_label','outstanding_principal_basis','outstanding_principal_unit','outstanding_principal_as_of','outstanding_principal_source_ids','outstanding_principal_source_urls','market_yield','source_ids','source_urls'];const escape=value=>{let s=Array.isArray(value)?(value.some(item=>item!==null&&typeof item==='object')?JSON.stringify(value):value.join(' | ')):value==null?'':typeof value==='object'?JSON.stringify(value):String(value);if(/^[=+@\-\t\r\n]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};text=[keys.map(escape).join(','),...rows.map(row=>keys.map(key=>escape(row[key])).join(','))].join('\r\n');type='text/csv;charset=utf-8';}
  const url=URL.createObjectURL(new Blob([text],{type})),a=el('a');a.href=url;a.download=`neocloud-${state.metric}-${state.group}.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function selectMetric(metric){if(!Object.hasOwn(METRICS,metric))return;state.metric=metric;state.order=metric==='coupon'?'asc':'desc';render();}
async function copyViewLink(){try{if(location.protocol==='file:')throw new Error('Local file');await navigator.clipboard.writeText(location.href);showToast('View link copied.');}catch{showToast('This preview cannot copy a link here. Share the HTML file, or copy the address from your browser.');}}
function renderCoverage(){
  const watchers=data.coverage_watchlist||[],root=$('coverage-cards');
  $('coverage').hidden=watchers.length===0;root.replaceChildren();
  watchers.forEach(company=>{
    const card=el('article',undefined,'coverage-card');
    card.append(el('h3',company.name),el('p',company.business),el('p',company.disclosure_status));
    const details=el('details');details.append(el('summary','Read the dated financing announcements'));
    for(const transaction of company.transactions||[]){
      const item=el('div',undefined,'coverage-transaction');
      item.append(el('strong',transaction.kind),el('p','Announced '+dateLabel(transaction.announced_on)),
        el('p',(transaction.currency==='USD'?money(transaction.amount):transaction.currency+' '+transaction.amount)+' · '+transaction.amount_basis),
        el('p',transaction.scope),el('p',transaction.outstanding_status||'Outstanding balance not reviewed.'));
      details.append(item);
    }
    (company.cautions||[]).forEach(note=>details.append(el('p',note)));
    for(const source of company.sources||[]){
      details.append(safeLink(source.url,(source.source_kind||'Primary disclosure')+' · '+dateLabel(source.published_on)));
      if(source.short_exact_passages?.length)details.append(el('blockquote',source.short_exact_passages.join('; ')));
    }
    card.append(details);root.append(card);
  });
}
function bind(){
  for(const [id,metric] of [['nav-debt','debt'],['nav-cash','cash']])$(id).onclick=event=>{event.preventDefault();selectMetric(metric);$('tab-'+metric).focus({preventScroll:true});$('rankings').scrollIntoView({block:'start',behavior:'auto'});};
  document.querySelectorAll('[data-guide-metric]').forEach(button=>button.onclick=()=>{const metric=button.dataset.guideMetric;if(!Object.hasOwn(METRICS,metric))return;state.metric=metric;render();$('start-here').open=false;const target=$('company-figures');target.focus({preventScroll:true});target.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});});
  $('guide-source').onclick=()=>{const company=visibleRows[0];if(company)openCompany(company.ticker);};
  document.querySelectorAll('[data-metric]').forEach(button=>{button.onclick=()=>selectMetric(button.dataset.metric);button.onkeydown=event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const keys=['debt','debt_assets','coupon','cash'],current=keys.indexOf(button.dataset.metric),next=event.key==='Home'?0:event.key==='End'?keys.length-1:(current+(event.key==='ArrowRight'?1:-1)+keys.length)%keys.length;selectMetric(keys[next]);$('tab-'+keys[next]).focus();};});
  document.querySelectorAll('[data-group]').forEach(button=>button.onclick=()=>{state.group=button.dataset.group;render();});
  $('search').oninput=()=>{state.q=$('search').value.slice(0,100);render();};$('direction').onchange=()=>{state.order=$('direction').value==='asc'?'asc':'desc';render();};
  $('note-type').onchange=()=>{state.noteType=Object.hasOwn(NOTE_TYPES,$('note-type').value)?$('note-type').value:'all';render();};$('note-status').onchange=()=>{state.noteStatus=Object.hasOwn(NOTE_STATUSES,$('note-status').value)?$('note-status').value:'all';render();};
  $('reset').onclick=()=>{state={metric:'debt',group:'ai_infrastructure',q:'',order:'desc',noteType:'all',noteStatus:'all'};render();};$('clear-search').onclick=()=>{state.q='';if(state.metric==='coupon'){state.noteType='all';state.noteStatus='all';}render();$('search').focus();};
  $('close-dialog').onclick=()=>$('company-dialog').close();$('company-dialog').addEventListener('close',()=>{detailTicker=null;updateURL();});
  $('open-comparison').onclick=openComparison;$('close-comparison').onclick=()=>$('comparison-dialog').close();$('comparison-dialog').addEventListener('close',updateURL);
  $('clear-comparison').onclick=()=>{compareTickers=[];render();$('search').focus({preventScroll:true});};
  $('share-comparison').onclick=copyViewLink;
  $('download-csv').onclick=()=>exportData('csv');$('download-json').onclick=()=>exportData('json');
  $('share').onclick=copyViewLink;
}
async function init(){
  try{
    const bundled=$('preview-data');if(bundled)data=JSON.parse(bundled.textContent);else{const response=await fetch('./data.json');if(!response.ok)throw new Error('The source dataset could not be loaded.');data=await response.json();}
    if(!Array.isArray(data.companies)||!Array.isArray(data.sources))throw new Error('The source dataset has an invalid format.');
    if(data.mock===true){$('error').hidden=false;$('error').textContent='INTERFACE TEST DATA ONLY — These mock companies and figures are not actual financial disclosures.';}
    sourceMap=new Map(data.sources.map(source=>[source.id,source]));
    const params=new URLSearchParams(location.search),metric=params.get('metric'),group=params.get('group'),order=params.get('order');
    if(Object.hasOwn(METRICS,metric))state.metric=metric;if(Object.hasOwn(GROUPS,group))state.group=group;state.order=order==='asc'||order==='desc'?order:(state.metric==='coupon'?'asc':'desc');state.q=(params.get('q')||'').slice(0,100);
    const type=params.get('note_type'),status=params.get('outstanding');if(Object.hasOwn(NOTE_TYPES,type))state.noteType=type;if(Object.hasOwn(NOTE_STATUSES,status))state.noteStatus=status;
    compareTickers=[...new Set((params.get('compare')||'').split(','))].filter(ticker=>data.companies.some(company=>company.ticker===ticker)).slice(0,3);
    $('company-count').textContent=String(data.companies.length).padStart(2,'0');$('review-date').textContent='Sources reviewed '+dateLabel(data.reviewed_at);
    bind();render();renderCoverage();$('rankings').setAttribute('aria-busy','false');
    if(params.get('comparison')==='1'&&compareTickers.length>=2)openComparison();
    const ticker=params.get('company');if(ticker&&data.companies.some(c=>c.ticker===ticker))openCompany(ticker);
  }catch(error){$('error').hidden=false;$('error').textContent=`The comparison could not load. ${error.message} Please reload the preview; if opening a local file, use the complete standalone HTML.`;$('rankings').setAttribute('aria-busy','false');$('result-count').textContent='Source dataset unavailable';$('ranking-rows').replaceChildren();}
}
init();
