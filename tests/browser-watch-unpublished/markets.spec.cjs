const {test,expect}=require('@playwright/test');
const fs=require('node:fs');

// SYNTHETIC QA DATA ONLY. Injected into localhost navigation responses in tests;
// never written to neocloud/data, a generated public asset, or a published site.
const IDS=['crwv','nbis','iren','apld','hut','wulf','wyfi','shaz','agpu'];
const FIXTURE_RETURNS=[20,-20,.1,10,-10,0,15,-5,7];
const CAPS=[10e9,10e9-1,20e9,1e9,200e6,299999999,300e6,2e9,null];
const STARTS={'1w':'2026-11-13','1m':'2026-10-20','3m':'2026-08-20',ytd:'2025-12-31'};
const END='2026-11-20';
const band=n=>n===null?'unknown':n>=10e9?'large':n>=2e9?'mid':n>=300e6?'small':'micro';
function syntheticMarkets(){
 const windows=Object.fromEntries(Object.entries(STARTS).map(([key,start])=>[key,{target_start:start,start_session:start,end_session:END}]));
 const companies=IDS.map((id,i)=>({id,ticker:id.toUpperCase(),listing_status:'listed',exchange:'NASDAQ',currency:'USD',history_status:'available',
  price:{value:100+FIXTURE_RETURNS[i],date:END,status:'available',currency:'USD',source_url:'https://example.invalid/synthetic-qa-only'},
  market_cap:{value:CAPS[i],status:CAPS[i]===null?'unavailable':'verified',size_band:band(CAPS[i]),as_of:END,currency:'USD',share_basis:'Synthetic QA common shares only',reason:CAPS[i]===null?'Synthetic QA: capitalization unresolved; do not substitute EPS weighted-average shares':null,source_url:'https://example.invalid/synthetic-qa-only'},
  returns:Object.fromEntries(Object.entries(STARTS).map(([key,start])=>[key,{value:FIXTURE_RETURNS[i]*({'1w':.5,'1m':1,'3m':2,ytd:3}[key]),status:'available',start_session:start,end_session:END,price_basis:'split_adjusted_price_return'}])),
  history:[...Object.entries(STARTS).map(([key,date])=>({date,close:(100+FIXTURE_RETURNS[i])/(1+FIXTURE_RETURNS[i]*({'1w':.5,'1m':1,'3m':2,ytd:3}[key])/100),segment:'verified-1'})),{date:'2026-11-10',close:100+FIXTURE_RETURNS[i]/2,segment:'verified-1'},{date:END,close:100+FIXTURE_RETURNS[i],segment:'verified-1'}].sort((a,b)=>a.date.localeCompare(b.date)),
 }));
 const normalizations=Object.fromEntries(Object.keys(STARTS).map(key=>[key,{status:'available',start_session:STARTS[key],end_session:END,shortened:false,series:companies.map(c=>{const points=c.history.filter(p=>p.date>=STARTS[key]),base=points[0].close;return {id:c.id,points:points.map(p=>({date:p.date,value:p.close/base*100}))};})}]));
 return {schema_version:1,synthetic_qa_only:true,status:'ready',as_of:'2026-11-20T21:05:00Z',expected_end_session:END,end_session:END,price_basis:'split_adjusted_price_return',
  provider:'SYNTHETIC QA ONLY — NOT FOR PUBLICATION',license:{status:'public_display_permitted',source_url:'https://example.invalid/synthetic-qa-only',permission_url:'https://example.invalid/synthetic-qa-only'},
  refresh:{status:'success',last_attempt_at:'2026-11-20T21:05:00Z',last_success_at:'2026-11-20T21:05:00Z',age_days:2,stale:false},windows,companies,normalizations};
}
async function injectSyntheticMarkets(page,change=()=>{}){
 const fixture=syntheticMarkets();change(fixture);
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());
  if(url.origin!=='http://127.0.0.1:8003')return route.continue();
  if(url.pathname.endsWith('/market-data.json'))return route.fulfill({json:fixture});
  if(!request.isNavigationRequest())return route.continue();
  const response=await route.fetch();let html=await response.text();
  const pattern=/(<script id="market-data" type="application\/json">)[\s\S]*?(<\/script>)/;
  expect(pattern.test(html),'Local fixture injection must find separate market JSON; never replace financial data').toBe(true);
  html=html.replace(pattern,(_,open,close)=>open+JSON.stringify(fixture).replaceAll('<','\\u003c')+close);
  return route.fulfill({response,body:html});
 });
 return fixture;
}
const ranked=page=>page.locator('#ranked-stock-returns .stock-return-row');
const stockRow=(page,id)=>page.locator(`#ranked-stock-returns .stock-return-row[data-stock-company="${id}"]`);
const ids=locator=>locator.evaluateAll(nodes=>nodes.map(n=>n.dataset.stockCompany||n.dataset.company));
async function jsonDownload(page){const pending=page.waitForEvent('download');await page.locator('#export-json').click();return JSON.parse(fs.readFileSync(await(await pending).path(),'utf8'));}

test('the actual market cache keeps financial dates separate and never substitutes test prices',async({page})=>{
 await page.goto('/markets/');
 const market=JSON.parse(await page.locator('#market-data').textContent());
 const financial=JSON.parse(await page.locator('#watch-data').textContent());
 expect(market.synthetic_qa_only).not.toBe(true);
 expect(JSON.stringify(market)).not.toContain('SYNTHETIC QA ONLY');
 expect(financial.reviewed_at).toBe('2026-11-17');
 await expect(page.locator('#market-data-status')).toContainText('Financial research cutoff 2026-11-17');
 await expect(page.locator('#primary-nav a')).toHaveText(['Overview','Markets','Financing & Debt','Earnings','Buildout']);
 if(market.status==='unavailable'||market.license.status!=='public_display_permitted'){
  await expect(page.locator('.market-blocked')).toBeVisible();
  await expect(page.locator('.stock-return-row[data-return]')).toHaveCount(0);
  await expect(page.locator('.market-blocked')).toContainText(market.gap_reason);
 }else{
  expect(market.as_of).toBeTruthy();expect(market.end_session).toBeTruthy();
  await expect(page.locator('#market-data-status')).toContainText(market.as_of.slice(0,10));
 }
});

test('stock hero leads the homepage with ranked signed returns, current size and a common linear scale',async({page},info)=>{
 await injectSyntheticMarkets(page);await page.goto('/overview/');
 await expect(page.locator('#stock-hero')).toBeVisible();
 await expect(page.locator('#stock-hero h1')).toContainText('Neocloud stocks this month');
 await expect(ranked(page)).toHaveCount(9);
 expect(await ids(ranked(page))).toEqual(['crwv','wyfi','apld','agpu','iren','wulf','shaz','hut','nbis']);
 await expect(stockRow(page,'crwv')).toContainText('+20');
 await expect(stockRow(page,'nbis')).toContainText('−20');
 await expect(stockRow(page,'iren')).toContainText('+0.1');
 await expect(stockRow(page,'wulf')).toHaveAttribute('data-return','0');
 await expect(stockRow(page,'agpu')).toContainText('Size unverified');
 await expect(stockRow(page,'hut')).toContainText('Micro');
 await expect(stockRow(page,'crwv')).toContainText('Large');
 await expect(stockRow(page,'shaz')).toContainText('Medium');
 await expect(stockRow(page,'wyfi')).toContainText('Small');
 const scales=await ranked(page).evaluateAll(nodes=>nodes.map(n=>n.dataset.scaleMax));
 expect(new Set(scales).size).toBe(1);expect(Number(scales[0])).toBeGreaterThanOrEqual(20);
 const plus=await stockRow(page,'crwv').locator('.stock-return-bar').boundingBox(),minus=await stockRow(page,'nbis').locator('.stock-return-bar').boundingBox();
 expect(Math.abs(plus.width-minus.width)).toBeLessThanOrEqual(1);
 const positions=await page.evaluate(()=>['#stock-hero','#what-changed','#overview-charts','#buildout-tracker','#overview-comparison'].map(s=>document.querySelector(s).getBoundingClientRect().top));
 for(let i=1;i<positions.length;i++)expect(positions[i]).toBeGreaterThan(positions[i-1]);
 await expect(page.locator('#stock-hero')).toContainText('2026-10-20');await expect(page.locator('#stock-hero')).toContainText(END);
 await page.locator('#stock-hero').evaluate(el=>{const mark=document.createElement('p');mark.id='synthetic-qa-watermark';mark.textContent='SYNTHETIC QA FIXTURE — NOT REAL MARKET DATA — NOT FOR PUBLICATION';mark.style.cssText='padding:12px;background:#fff0cc;color:#493509;font-weight:700;';el.prepend(mark);});
 await page.locator('#stock-hero').screenshot({path:`work/markets-synthetic-qa-only-${info.project.name}.png`});
 await page.locator('#synthetic-qa-watermark').evaluate(el=>el.remove());
 await page.locator('#stock-group-size').check();
 expect(await ids(ranked(page))).toEqual(['crwv','iren','shaz','nbis','wyfi','apld','wulf','hut','agpu']);
 await expect(page.locator('.stock-size-heading')).toHaveText(['Large companies','Medium companies','Small companies','Micro companies','Size unverified companies']);
});

test('timeframe, size grouping and selected peers survive Markets navigation and refresh',async({page})=>{
 await injectSyntheticMarkets(page);await page.goto('/overview/?peers=crwv,nbis');
 for(const [window,expected] of [['3m','40'],['ytd','60'],['1w','10']]){
  await page.locator('[data-stock-window="'+window+'"]').click();
  await expect(stockRow(page,'crwv')).toHaveAttribute('data-return',expected);
 }
 expect(new URL(page.url()).searchParams.get('window')).toBe('1w');
 await expect(stockRow(page,'crwv')).toHaveAttribute('data-return','10');
 await expect(page.locator('#stock-hero h1')).not.toContainText('this month');
 await page.locator('#stock-group-size').check();expect(new URL(page.url()).searchParams.get('group')).toBe('size');
 await page.locator('#primary-nav').getByRole('link',{name:'Markets',exact:true}).click();
 expect(new URL(page.url()).pathname).toBe('/markets/');await expect(ranked(page)).toHaveCount(2);
 expect(new URL(page.url()).searchParams.get('peers')).toBe('crwv,nbis');
 await page.reload();await expect(page.locator('#stock-group-size')).toBeChecked();
 await expect(stockRow(page,'nbis')).toHaveAttribute('data-return','-10');
 for(const name of ['Financing & Debt','Earnings','Buildout','Overview']){
  await page.locator('#primary-nav').getByRole('link',{name,exact:true}).click();
  expect(new URL(page.url()).searchParams.get('peers')).toBe('crwv,nbis');
  expect(new URL(page.url()).searchParams.get('window')).toBe('1w');
 }
});

test('Markets offers logarithmic size scatter and normalized histories with common dates',async({page})=>{
 await injectSyntheticMarkets(page);await page.goto('/markets/?peers=crwv,nbis,agpu');
 await page.locator('[data-stock-view="scatter"]').click();
 expect(new URL(page.url()).searchParams.get('view')).toBe('scatter');
 await expect(page.locator('#market-scatter')).toBeVisible();
 await expect(page.locator('#market-scatter')).toContainText(/logarithmic|log scale/i);
 await expect(page.locator('#markets-table [data-company=agpu]')).toContainText('Size unverified');
 await expect(page.locator('#normalized-prices')).toBeVisible();
 const histories=page.locator('#normalized-prices [data-normalized-company]');await expect(histories).toHaveCount(3);
 for(const line of await histories.all()){
  await expect(line).toHaveAttribute('data-start-session','2026-10-20');await expect(line).toHaveAttribute('data-end-session',END);
 }
 await expect(page.locator('#normalized-prices')).toContainText('100');
 const details=page.locator('.normalized-series-details[data-history-company=crwv]');
 await details.locator('summary').click();
 await expect(details.locator('tbody tr').first().locator('td').nth(2)).toHaveText('100.0000');
 await expect(details.locator('tbody tr').last().locator('td').nth(2)).toHaveText('120.0000');
 await page.reload();await expect(page.locator('#market-scatter')).toBeVisible();
 await expect(page.locator('#markets-table [data-company]')).toHaveCount(3);
 await page.locator('#peer-picker summary').click();
 await page.getByRole('checkbox',{name:'Select AGPU',exact:true}).uncheck();
 await expect(page.locator('#markets-table [data-company]')).toHaveCount(2);
 await expect(page.locator('#normalized-prices [data-normalized-company]')).toHaveCount(2);
 expect(new URL(page.url()).searchParams.get('peers')).toBe('crwv,nbis');
 await page.reload();await expect(page.locator('#markets-table [data-company]')).toHaveCount(2);
});

test('Markets exports the displayed ranked selection and retains exact return-window and cap gaps',async({page})=>{
 await injectSyntheticMarkets(page);await page.goto('/markets/?peers=crwv,nbis,agpu&window=1m');
 const shown=await ids(ranked(page)),payload=await jsonDownload(page);
 expect(payload.market_performance.window).toBe('1m');
 const returned=payload.market_performance.companies;
 expect(returned.map(c=>c.id)).toEqual(shown);
 expect(returned.find(c=>c.id==='crwv').returns['1m'].value).toBe(20);
 expect(returned.find(c=>c.id==='agpu').market_cap.value).toBeNull();
 expect(JSON.stringify(payload.market_performance)).toContain('2026-10-20');
 const pending=page.waitForEvent('download');await page.locator('#export-csv').click();
 const csv=fs.readFileSync(await(await pending).path(),'utf8');
 for(const value of ['CRWV','NBIS','AGPU','return_pct','start_date','end_date','2026-10-20',END])expect(csv).toContain(value);
 expect(csv).not.toContain('NSCALE');
});

test('scatter uses equal horizontal distances for tenfold size changes with an explicit log axis',async({page})=>{
 await injectSyntheticMarkets(page,fixture=>{
  for(const [id,value] of [['crwv',10e9],['nbis',1e9],['iren',100e6]]){
   const cap=fixture.companies.find(c=>c.id===id).market_cap;
   Object.assign(cap,{value,status:'verified',size_band:band(value)});
  }
 });
 await page.goto('/markets/?peers=crwv,nbis,iren&view=scatter');
 const coordinates=[];
 for(const id of ['iren','nbis','crwv']){
  const point=page.locator(`#market-scatter [data-scatter-company=${id}]`);
  await expect(point).toBeVisible();await expect(point).toHaveAttribute('href',new RegExp('/companies/'+id+'/'));
  coordinates.push(await point.evaluate(node=>parseFloat(node.style.left)));
 }
 expect(coordinates[1]-coordinates[0]).toBeCloseTo(coordinates[2]-coordinates[1],6);
 expect(coordinates[2]).toBeGreaterThan(coordinates[0]);
 await expect(page.locator('#market-scatter')).toContainText(/logarithmic|log scale/i);
 await expect(page.locator('#market-scatter')).toContainText(/does\s+not\s+establish\s+causation/i);
});

test('missing and stale return observations remain labelled gaps rather than zero bars',async({page})=>{
 await injectSyntheticMarkets(page,fixture=>{
  fixture.status='partial';fixture.refresh={...fixture.refresh,stale:true,age_days:12,status:'failed',last_attempt_at:'2026-11-22T01:00:00Z'};
  const c=fixture.companies.find(c=>c.id==='nbis');c.price={...c.price,date:'2026-11-04',status:'stale',reason:'Synthetic QA stale session'};
  c.returns['1m']={value:null,status:'unavailable',reason:'Synthetic QA stale close does not match common end session'};
 });
 await page.goto('/markets/?peers=crwv,nbis');
 await expect(stockRow(page,'nbis')).not.toHaveAttribute('data-return');
 await expect(stockRow(page,'nbis')).toContainText(/stale|unavailable/i);
 await expect(stockRow(page,'nbis').locator('.stock-return-bar')).toHaveCount(0);
 await expect(stockRow(page,'crwv')).toHaveAttribute('data-return','20');
 await expect(page.locator('#market-data-status')).toContainText(/stale|failed|12|last good/i);
});

test('a verified flat total-return series stays zero, starts at 100 and is never labelled as dollar prices',async({page})=>{
 await injectSyntheticMarkets(page,fixture=>{fixture.price_basis='total_return';});
 await page.goto('/markets/?peers=wulf');
 await expect(stockRow(page,'wulf')).toHaveAttribute('data-return','0');
 await expect(stockRow(page,'wulf')).toContainText('0.0%');
 await expect(page.locator('#stock-hero')).toContainText('Total return · dividends included');
 const line=page.locator('#normalized-prices [data-normalized-company=wulf]');
 await expect(line).toHaveCount(1);
 const points=(await line.getAttribute('points')).split(' ').map(point=>point.split(',').map(Number));
 expect(points.length).toBeGreaterThanOrEqual(2);
 expect(new Set(points.map(point=>point[1])).size).toBe(1);
 const detail=page.locator('.normalized-series-details[data-history-company=wulf]');
 await detail.locator('summary').click();
 await expect(detail.locator('thead')).toContainText('Return index');
 await expect(detail.locator('tbody')).not.toContainText('$');
 await expect(detail.locator('tbody tr').first().locator('td').nth(2)).toHaveText('100.0000');
 await expect(detail.locator('tbody tr').last().locator('td').nth(2)).toHaveText('100.0000');
});

test('a shortened verified segment never connects normalized history across a corporate-action gap',async({page})=>{
 await injectSyntheticMarkets(page,fixture=>{
  const c=fixture.companies.find(c=>c.id==='crwv');
  for(const point of c.history)point.segment=point.date<'2026-11-10'?'before-unverified-action':'after-unverified-action';
  c.returns['1m']={value:null,status:'unavailable',reason:'Synthetic QA unverified reverse split prevents full-window return'};
  fixture.normalizations['1m']={status:'available',start_session:'2026-11-10',end_session:END,shortened:true,reason:'Synthetic QA shortened to common verified segment after unverified reverse split',series:[{id:'crwv',points:[{date:'2026-11-10',value:100},{date:END,value:120/110*100}]}]};
 });
 await page.goto('/markets/?peers=crwv');
 await expect(stockRow(page,'crwv')).not.toHaveAttribute('data-return');
 await expect(page.locator('#normalized-prices')).toContainText(/shortened|common available|verified segment/i);
 const line=page.locator('#normalized-prices [data-normalized-company=crwv]');
 await expect(line).toHaveAttribute('data-start-session','2026-11-10');
 await expect(line).not.toHaveAttribute('data-start-session','2026-10-20');
});

test('a blocked public-display snapshot explains the source gap without invented performance',async({page})=>{
 await injectSyntheticMarkets(page,fixture=>{fixture.status='unavailable';fixture.license.status='unverified';fixture.gap_reason='Synthetic QA public-display permission not established';fixture.companies=[];fixture.normalizations={};});
 await page.goto('/overview/');
 await expect(page.locator('#stock-hero .market-blocked')).toContainText(/permission|public.display|unavailable/i);
 await expect(page.locator('#ranked-stock-returns .stock-return-row[data-return]')).toHaveCount(0);
 await expect(page.locator('.overview-revenue-card')).toHaveCount(9);
 await expect(page.locator('#what-changed')).toBeVisible();
 await page.locator('#primary-nav').getByRole('link',{name:'Markets',exact:true}).click();
 await expect(page.locator('.market-blocked').first()).toBeVisible();
 await expect(page.locator('#market-scatter [data-stock-company]')).toHaveCount(0);
});

test('stock details support keyboard or touch, company links and narrow viewports',async({page},info)=>{
 await injectSyntheticMarkets(page);await page.goto('/markets/?peers=crwv,nbis,agpu');
 const detail=stockRow(page,'crwv').locator('details.stock-return-observation');
 const summary=detail.locator('summary');
 if(info.project.name==='mobile')await summary.tap();else{await summary.focus();await expect(summary).toBeFocused();await page.keyboard.press('Enter');}
 await expect(detail).toHaveAttribute('open','');await expect(detail).toContainText('2026-10-20');
 await expect(stockRow(page,'crwv').getByRole('link').first()).toHaveAttribute('href',/companies\/crwv\//);
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:1000});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),String(width)).toBe(true);
  await expect(stockRow(page,'nbis')).toContainText('−20');
 }
 await stockRow(page,'crwv').getByRole('link').first().click();
 await expect(page.locator('#page-content')).toContainText('CoreWeave');
 expect(new URL(page.url()).searchParams.get('peers')).toBe('crwv,nbis,agpu');
});
