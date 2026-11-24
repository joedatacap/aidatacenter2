// Real hosted verification of the intact official widget. Never inspect its
// shadow DOM, extract values, intercept data payloads, or persist quote streams.
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const {expectedSize}=require('../browser-watch/size-contract.cjs');

const ROOT = path.resolve(__dirname, '../..');
const SITE = path.join(ROOT, 'work/neocloud-watch-site');
const OUTPUT = path.join(ROOT, 'work/watch-native-proof');
const LIVE = 'https://neocloud-watch.gpuchips.chatgpt.site';
const MODE = process.env.WATCH_NATIVE_MODE || 'candidate';
const SYMBOLS = ['NASDAQ:CRWV','NASDAQ:NBIS','NASDAQ:IREN','NASDAQ:APLD','NASDAQ:HUT','NASDAQ:WULF','NASDAQ:WYFI','NASDAQ:SHAZ','NASDAQ:AGPU'];
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const originOnly = value => {try {const u = new URL(value);return ['https:','http:','wss:','ws:'].includes(u.protocol)?u.origin:u.protocol;} catch {return 'unknown';}};
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8'};

function headerRules(text) {
  const rules=[];let current;
  for(const line of text.split(/\r?\n/)) {
    if(!line.trim() || line.trim().startsWith('#'))continue;
    if(!/^\s/.test(line)){current={pattern:line.trim(),headers:{}};rules.push(current);}
    else if(current){const match=line.trim().match(/^([^:]+):\s*(.*)$/);if(match)current.headers[match[1].toLowerCase()]=match[2];}
  }
  return rules;
}

async function startCandidate() {
  const rules=headerRules(await fs.readFile(path.join(SITE,'_headers'),'utf8'));
  assert(rules.some(rule=>rule.headers['content-security-policy']), 'Generated build must declare a CSP');
  const server=http.createServer(async(req,res)=>{
    try {
      const pathname=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
      const headers={'cache-control':'no-store'};
      for(const rule of rules){const prefix=rule.pattern.endsWith('*')?rule.pattern.slice(0,-1):null;if(prefix!==null?pathname.startsWith(prefix):pathname===rule.pattern)Object.assign(headers,rule.headers);}
      let file=path.resolve(SITE,'.'+pathname);
      if(file!==SITE&&!file.startsWith(SITE+path.sep)){res.writeHead(403,headers);res.end();return;}
      const stat=await fs.stat(file);if(stat.isDirectory())file=path.join(file,'index.html');
      const bytes=await fs.readFile(file);res.writeHead(200,{...headers,'content-type':mime[path.extname(file)]||'application/octet-stream'});res.end(bytes);
    }catch{res.writeHead(404,{'content-type':'text/plain'});res.end('Not found');}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  return {server,origin:'http://127.0.0.1:'+server.address().port};
}

async function screenshotTop(page,label) {
  await page.evaluate(()=>window.scrollTo(0,0));
  const box=await page.locator('tv-market-data').boundingBox();
  assert(box&&box.width>100&&box.height>250,'Official widget host has a useful visible size');
  const width=page.viewportSize().width;
  const height=Math.ceil(Math.max(page.viewportSize().height,box.y+box.height+35));
  await page.screenshot({path:path.join(OUTPUT,label+'.png'),clip:{x:0,y:0,width,height}});
}

async function screenshotWidget(page,label) {
  // Capture the outer, intact official component shell. The chart above it can
  // make a top-of-page image very tall; this separate image retains the full
  // vendor display and attribution without reading or modifying its contents.
  const shell=page.locator('#tradingview-widget-shell');
  await shell.scrollIntoViewIfNeeded();
  const shellBox=await shell.boundingBox(),widgetBox=await page.locator('tv-market-data').boundingBox();
  assert(shellBox&&widgetBox&&widgetBox.height>250,'Full official widget is visible for capture');
  assert(widgetBox.y>=shellBox.y-1&&widgetBox.y+widgetBox.height<=shellBox.y+shellBox.height+1,
    'Widget capture includes the entire official host');
  await shell.screenshot({path:path.join(OUTPUT,label+'.png')});
}

async function capChartChecks(page,acceptedData,ids) {
  const section=page.locator('#market-cap-chart');
  await section.waitFor({state:'visible'});
  await page.getByRole('heading',{name:'Market capitalization',exact:true,level:1}).waitFor();
  const expected=ids.map(id=>({company:acceptedData.companies.find(item=>item.id===id)}))
    .map(item=>({...item,size:expectedSize(item.company)}))
    .sort((a,b)=>Number(b.size.value)-Number(a.size.value));
  assert.deepEqual(await section.locator('[data-cap-company]').evaluateAll(rows=>rows.map(row=>row.dataset.capCompany)),
    expected.map(item=>item.company.id),'Market-cap chart ranks the accepted selected companies by descending capitalization');
  if(!expected.length)return {rows:0};
  const axisMax=Number(await section.locator('[data-cap-max]').getAttribute('data-cap-max'));
  assert(Number.isFinite(axisMax)&&axisMax>=Math.max(...expected.map(item=>Number(item.size.value))),
    'Market-cap axis includes the largest accepted observation');
  const ticks=section.locator('.cap-ticks span');
  assert.equal(await ticks.first().innerText(),'$0');
  assert((await section.locator('[data-cap-scale]').innerText()).includes('$0 to '+await ticks.last().innerText()));
  for(const {company,size} of expected){
    const row=section.locator('[data-cap-company="'+company.id+'"]');
    assert.equal(await row.getAttribute('data-cap-date'),size.date,'Chart row retains its dated observation: '+company.id);
    assert((await section.innerText()).includes(size.date.slice(0,10)),'Chart visibly dates the accepted observation');
    const value=row.locator('[data-cap-value]');
    assert.equal((await value.innerText()).trim(),'$'+Number(size.value).toLocaleString('en-US',{maximumFractionDigits:2}),
      'Chart displays the accepted USD capitalization in full dollars: '+company.id);
    assert.equal(await value.getAttribute('href'),size.observation.source_url,'Chart value links to its attributed source');
    const profile=row.locator('[data-cap-profile]');
    assert(await profile.isVisible(),'Chart company link is visible');
    assert.equal(new URL(await profile.getAttribute('href'),page.url()).pathname,'/companies/'+company.id+'/',
      'Chart company link opens the corresponding company brief');
    const track=await row.locator('[data-cap-track]').boundingBox(),bar=await row.locator('[data-cap-bar]').boundingBox();
    assert(track&&bar&&track.width>0,'Chart has a visible plot track and bar');
    const expectedWidth=track.width*Number(size.value)/axisMax;
    assert(Math.abs(bar.width-expectedWidth)<=1.1,'Chart bar width follows its accepted USD value on the shared linear scale: '+company.id);
    assert(bar.x>=track.x-1&&bar.x+bar.width<=track.x+track.width+1,'Chart fill stays within its plot track');
    if(company.id==='agpu')assert((await row.innerText()).includes('Provider-reported; share basis unresolved.'),
      'AGPU carries the exact unresolved-share-basis qualification');
    if(size.observation.session_status==='intraday')assert((await section.innerText()).includes('intraday'),
      'Chart labels open-session capitalization observations');
  }
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),
    'Market-cap chart does not cause horizontal page overflow');
  return {rows:expected.length,descending:true,linear_scale:true,accepted_values:true,dated:true,source_links:true,profile_links:true,page_overflow:false};
}

async function capChartGroupChecks(page,origin,acceptedData,label) {
  const ids=SYMBOLS.map(symbol=>symbol.split(':')[1].toLowerCase());
  const smallIds=ids.filter(id=>['small','micro'].includes(expectedSize(acceptedData.companies.find(company=>company.id===id)).band));
  await page.locator('#market-cap-chart [data-cap-group="small"]').click();
  assert.equal(new URL(page.url()).searchParams.get('size'),'small','Chart group control uses the shared size filter');
  const small=await capChartChecks(page,acceptedData,smallIds);
  await sizeTableChecks(page,acceptedData,smallIds);
  assert.deepEqual(JSON.parse(await page.locator('tv-market-data').getAttribute('symbol-sectors')).flatMap(group=>group.symbols),
    smallIds.map(id=>'NASDAQ:'+acceptedData.companies.find(company=>company.id===id).ticker),
    'Small group filters the chart, size table and configured widget symbols together');
  assert(smallIds.includes('agpu'),'Small group includes AGPU');
  await page.locator('#market-cap-chart').screenshot({path:path.join(OUTPUT,label+'-small-market-cap-chart.png')});
  await page.locator('#market-cap-chart [data-cap-group="all"]').click();
  await capChartChecks(page,acceptedData,ids);
  await page.goto(origin+'/?peers=wyfi,agpu');
  const selected=await capChartChecks(page,acceptedData,['wyfi','agpu']);
  await sizeTableChecks(page,acceptedData,['wyfi','agpu']);
  assert.deepEqual(JSON.parse(await page.locator('tv-market-data').getAttribute('symbol-sectors')).flatMap(group=>group.symbols),
    ['NASDAQ:WYFI','NASDAQ:AGPU'],'Chart peers match the table and configured widget selection');
  await page.locator('#market-cap-chart').screenshot({path:path.join(OUTPUT,label+'-selected-market-cap-chart.png')});
  await page.goto(origin+'/markets/?peers=wyfi,agpu');
  assert.equal(await page.locator('#market-cap-chart').count(),0,'Capitalization chart is confined to the homepage');
  await page.goto(origin+'/');
  return {small,selected,small_includes_micro:true,shared_filter:true,homepage_only:true};
}

// This is our dated editorial table, separate from the vendor component. Only
// application markup and accepted research are read; vendor figures stay visual.
async function sizeTableChecks(page,acceptedData,ids) {
  const section=page.locator('#tradingview-size-context');
  const rows=page.locator('#tradingview-size-context [data-size-company]');
  assert.deepEqual(await rows.evaluateAll(items=>items.map(item=>item.dataset.sizeCompany)),ids,
    'Compact size table matches the selected focus companies');
  if(!ids.length)return {rows:0,semantic:true,source_links:0,profile_links:0};
  assert.equal(await section.locator('table').count(),1,'Size context uses one semantic table');
  assert.equal(await section.locator('thead').count(),1,'Size table has a header group');
  assert.equal(await section.locator('tbody').count(),1,'Size table has a body group');
  assert.equal(await section.locator('thead th').count(),3,'Size table names the Company, Size and Market cap columns');
  for(const id of ids){
    const company=acceptedData.companies.find(item=>item.id===id);
    assert(company,'Accepted application data contains focus company '+id);
    const expected=expectedSize(company),row=section.locator('[data-size-company="'+id+'"]');
    assert.equal(await row.evaluate(item=>item.tagName),'TR','Each size record is a semantic row');
    assert.equal(await row.locator(':scope > th, :scope > td').count(),3,'Each size row has the three named cells');
    const label=(await row.locator('.tradingview-size-badge').innerText()).trim();
    assert.equal(label,expected.label,'Displayed size matches accepted app data: '+id);
    assert(['Large','Mid','Small','Unavailable'].includes(label),'Only three established display classes are used');
    assert.equal(await row.getAttribute('data-size-date'),expected.date,'Size row retains its actual observation date: '+id);
    assert((await section.innerText()).includes(expected.date.slice(0,10)),'Size observation date is visible in the row or shared table attribution: '+id);
    if(expected.band==='unknown'){
      assert((await row.locator('.tradingview-size-attribution').innerText()).includes('Unavailable'),'Unknown cap stays unavailable: '+id);
      assert.equal(await row.locator('.tradingview-size-attribution a').count(),0,'Unknown cap does not link an inferred value');
    }else if(expected.observation){
      const source=row.locator('.tradingview-size-attribution a');
      assert.equal(await source.getAttribute('href'),expected.observation.source_url,'Size attribution links to the accepted source: '+id);
      assert(await source.isVisible(),'Size source link is visible: '+id);
      const amount=Number(expected.value);
      const [divisor,suffix]=[[1e9,'B'],[1e6,'M'],[1e3,'K'],[1,'']].find(([threshold])=>Math.abs(amount)>=threshold)||[1,''];
      const display='$'+(amount/divisor).toLocaleString('en-US',{maximumFractionDigits:divisor===1?0:2})+suffix;
      assert.equal((await source.innerText()).trim(),display,'Displayed USD cap matches the accepted dated observation: '+id);
      if(expected.observation.session_status==='intraday'){
        assert((await section.innerText()).includes('intraday'),'Open-session size observations are visibly labeled intraday');
      }

    }
    const profile=row.locator('.tradingview-company-link');
    assert(await profile.isVisible(),'Company profile link is visible: '+id);
    const profileURL=new URL(await profile.getAttribute('href'),page.url());
    assert.equal(profileURL.pathname,'/companies/'+id+'/','Size row opens the matching company brief');
    assert((await profile.innerText()).trim(),'Company profile link has a visible name');
  }
  const geometry=await section.evaluate(element=>{
    const table=element.querySelector('table'),box=table.getBoundingClientRect();
    return {page:document.documentElement.scrollWidth<=document.documentElement.clientWidth,
      table:box.left>=-1&&box.right<=document.documentElement.clientWidth+1,
      unclipped:table.scrollHeight<=table.clientHeight+1};
  });
  assert(geometry.page&&geometry.table&&geometry.unclipped,'Entire compact size table fits without page overflow or clipped rows');
  return {rows:ids.length,semantic:true,source_links:ids.filter(id=>expectedSize(acceptedData.companies.find(item=>item.id===id)).band!=='unknown').length,profile_links:ids.length,display_classes:'Large/Mid/Small; Small includes micro',page_overflow:false};
}

async function sizeProfileChecks(page,origin,acceptedData,ids) {
  for(const id of ids){
    const company=acceptedData.companies.find(item=>item.id===id);
    const observation=company.size_observation;
    if(!observation)continue;
    await page.goto(origin+'/companies/'+id+'/');
    const review=page.locator('[data-size-review="'+id+'"]');
    await review.waitFor({state:'visible'});
    const text=await review.innerText();
    assert(text.includes(observation.as_of),'Company profile retains the size observation date: '+id);
    const excerpt=review.locator('.size-source-excerpt');
    if(observation.source_excerpt){
      assert.equal((await excerpt.textContent()).trim(),observation.source_excerpt.trim(),
        'Profile preserves the original attributed editorial passage: '+id);
    }
    for(const field of ['share_basis','basis','caveat','discrepancy','qualification_label']){
      if(observation[field])assert(text.toLowerCase().includes(observation[field].toLowerCase()),'Profile retains the size '+field+': '+id);
    }
    assert(await review.locator('a[href="'+observation.source_url+'"]').first().isVisible(),
      'Profile links to the dated capitalization source: '+id);
  }
  return {profiles:ids.length,attributed_passages:true,share_basis:true,qualifications:true};
}

async function screenshotSizeTable(page,label) {
  const section=page.locator('#tradingview-size-context');
  await section.scrollIntoViewIfNeeded();
  const table=section.locator('table'),sectionBox=await section.boundingBox(),tableBox=await table.boundingBox();
  assert(sectionBox&&tableBox,'Compact size section is visible for capture');
  assert(tableBox.y>=sectionBox.y-1&&tableBox.y+tableBox.height<=sectionBox.y+sectionBox.height+1,
    'Size capture includes every table row');
  await section.screenshot({path:path.join(OUTPUT,label+'-size-table.png')});
}

async function peerSizeChecks(page,origin,acceptedData,label) {
  await page.goto(origin+'/markets/?peers=crwv,nbis');
  await page.locator('#tradingview-size-context').waitFor();
  const selected=await sizeTableChecks(page,acceptedData,['crwv','nbis']);
  const configured=JSON.parse(await page.locator('tv-market-data').getAttribute('symbol-sectors'));
  assert.deepEqual(configured.flatMap(group=>group.symbols),['NASDAQ:CRWV','NASDAQ:NBIS'],
    'Native component and editorial size table receive the same selected peers');
  await screenshotSizeTable(page,label+'-selected');
  await page.goto(origin+'/markets/?peers=crwv,nbis&q=no-matching-focus-company');
  await page.getByRole('heading',{name:'Neocloud stock performance',exact:true}).waitFor();
  assert.equal(await page.locator('tv-market-data').count(),0,'Empty matching selection does not configure a widget');
  const empty=await sizeTableChecks(page,acceptedData,[]);
  assert((await page.locator('#page-content').innerText()).includes('No focus companies match'),
    'Empty matching selection provides an honest visible message');
  assert.equal(new URL(page.url()).searchParams.get('peers'),'crwv,nbis','Empty search preserves the selected peers');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),
    'Empty matching selection fits the viewport');
  return {selected,empty};
}

async function swipeMonthly(page) {
  const widget=page.locator('tv-market-data');
  const viewport=page.viewportSize();
  const touch=await page.context().newCDPSession(page);
  const captures=[];
  async function dragLeft(distance) {
    await widget.scrollIntoViewIfNeeded();
    const box=await widget.boundingBox();
    assert(box,'Widget host is visible for touch');
    const y=Math.round(Math.min(viewport.height-20,Math.max(30,box.y+Math.min(120,box.height/2))));
    const from=Math.min(345,viewport.width-30);
    await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:from,y}]});
    // Slow direct gestures, followed by a stationary hold before release, avoid
    // momentum flinging the monthly figures beneath the pinned company column.
    for(let step=1;step<=18;step++){
      const x=from-distance*step/18;
      await touch.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y}]});
      await page.waitForTimeout(35);
    }
    await page.waitForTimeout(250);
    await touch.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:from-distance,y}]});
    await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    await page.waitForTimeout(700);
  }
  try {
    // Capture three nearby positions for visual review. These distances are
    // touch gestures only; no vendor DOM, scroll offsets or quote cells are read.
    for(const position of [
      {distance:180,label:'mobile-month-less-scroll'},
      {distance:60,label:'mobile-month'},
      {distance:60,label:'mobile-month-more-scroll'}
    ]){
      await dragLeft(position.distance);
      await screenshotTop(page,position.label);
      await screenshotWidget(page,position.label+'-widget');
      captures.push(position.label+'.png',position.label+'-widget.png');
    }
  } finally {await touch.detach();}
  return captures;
}

function csvRows(text) {
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=0;i<text.length;i++){
    const ch=text[i];
    if(ch==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;}
    else if(ch===','&&!quoted){row.push(cell);cell='';}
    else if(ch==='\n'&&!quoted){row.push(cell.replace(/\r$/,''));rows.push(row);row=[];cell='';}
    else cell+=ch;
  }
  if(cell||row.length){row.push(cell.replace(/\r$/,''));rows.push(row);}
  return rows;
}

async function researchChecks(page,origin,label) {
  const nav=page.locator('#primary-nav');
  await page.locator('#peer-picker summary').click();
  await page.getByRole('checkbox',{name:'Select CRWV',exact:true}).check();
  await page.getByRole('checkbox',{name:'Select NBIS',exact:true}).check();
  await page.locator('#peer-picker summary').click();
  const jsonPromise=page.waitForEvent('download');await page.locator('#export-json').click();
  const jsonDownload=await jsonPromise;const payload=JSON.parse(await fs.readFile(await jsonDownload.path(),'utf8'));
  assert.equal(payload.companies.length,2,'Research JSON follows selected peers');
  assert.deepEqual(payload.companies.map(c=>c.ticker).sort(),['CRWV','NBIS']);
  assert(payload.companies.every(c=>c.quarters?.length&&c.financing),'Research exports retain financing and earnings');
  assert(!Object.hasOwn(payload,'market_performance'),'Research JSON must not contain native-widget market-performance fields');
  const csvPromise=page.waitForEvent('download');await page.locator('#export-csv').click();
  const csvDownload=await csvPromise;const csv=csvRows(await fs.readFile(await csvDownload.path(),'utf8'));
  assert.equal(csv.length,3,'CSV follows the two selected research peers');
  assert(!csv[0].some(name=>/^stock_|^return_|^price$|^normalized/.test(name)),'Research CSV must not contain native-widget price, return or normalization fields');
  // Downloads are inspected in memory only; no research or widget payload is
  // copied into this screenshot/metadata artifact.
  // Selection labels, application links and export contents are our own data.
  await nav.getByRole('link',{name:'Financing & Debt',exact:true}).click();
  await page.waitForURL(url=>url.pathname==='/financing/'&&url.searchParams.get('peers')?.includes('crwv'));
  assert(page.url().includes('nbis'),'Peer selections survive page navigation');
  await page.getByRole('link',{name:'CoreWeave',exact:true}).first().click();
  assert(new URL(page.url()).pathname.startsWith('/companies/crwv/'),'Company profile navigation works');
  await nav.getByRole('link',{name:'Earnings',exact:true}).click();
  await page.waitForURL(url=>url.pathname==='/earnings/');
  const dates=page.locator('.report-card .earnings-dates').first();
  assert.match(await dates.innerText(),/Reporting period ended .*Source published/);
  await dates.locator('..').screenshot({path:path.join(OUTPUT,label+'-earnings-dates.png')});
  const sources=page.locator('[data-sources]').first();await sources.click();
  await page.locator('#evidence-dialog').waitFor({state:'visible'});
  assert(await page.locator('#evidence-body a[href^="https://"]').count()>0,'Source drawer contains real research references');
  await page.locator('#close-evidence').click();
  await nav.getByRole('link',{name:'Markets',exact:true}).click();
  await page.locator('#tradingview-size-context').waitFor();
  assert.equal(await page.locator('[data-size-company]').count(),2);
  await nav.getByRole('link',{name:'Buildout',exact:true}).click();
  await page.waitForURL(url=>url.pathname==='/buildout/'&&url.searchParams.get('peers')?.includes('nbis'));
  await page.goto(origin+'/buildout/?tab=projects&peers=nbis');
  const target=page.locator('.timeline .fact-card').filter({has:page.getByRole('heading',{name:'ARR target timing',exact:true})});
  const fields=target.locator('dl > dd');
  assert.match(await fields.nth(0).innerText(),/December 2026/);
  assert.match(await fields.nth(2).innerText(),/February 2027/);
  await page.goto(origin+'/companies/apld/');
  await page.locator('.disclosure-history > summary').click();
  const disclosures=page.locator('#company-data-review [data-disclosure-event]');
  assert.equal(await disclosures.count(),4,'Current and historical Applied Digital disclosures are present');
  for(const item of await disclosures.all()){
    await item.locator('summary').click();
    assert(await item.locator('blockquote').first().isVisible(),'The original supporting passage is visible');
    assert.match(await item.getByRole('link',{name:'Read disclosure'}).getAttribute('href'),/^https:\/\//);
  }
  return {json_companies:2,csv_companies:2,source_drawer:true,navigation:true,buildout_revised_target:true,apld_disclosures:await disclosures.count()};
}

async function verifyAssets(request,origin) {
  const result={};
  for(const asset of ['watch.js','watch.css','data.json']){
    const expected=await fs.readFile(path.join(SITE,asset));
    const response=await request.get(origin+'/'+asset);assert(response.ok(),'Expected public asset served: '+asset);
    const actual=await response.body();assert.equal(hash(actual),hash(expected),'Served asset differs from accepted build: '+asset);
    result[asset]={sha256:hash(actual),bytes:actual.length};
  }
  // Read only known application paths; never print or retain any returned body.
  for(const protectedPath of ['/.env','/neocloud/app.py','/AGENTS.md']){
    const response=await request.get(origin+protectedPath);const text=await response.text();
    const looksSecret=/DATABASE_URL\s*=|CRUSOE_API_KEY\s*=|postgres(?:ql)?:\/\/[^\s]+@|# Codex project instructions/.test(text);
    assert(!looksSecret,'Protected source/configuration must not be served');
    result[protectedPath]={status:response.status(),source_or_secret_leak:false};
  }
  return result;
}

async function main() {
  assert(['candidate','live'].includes(MODE),'Controlled target must be candidate or live');
  await fs.mkdir(OUTPUT,{recursive:true});
  const candidate=MODE==='candidate'?await startCandidate():null;
  const origin=candidate?.origin||LIVE;
  const launch=process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{channel:process.env.WATCH_NATIVE_BROWSER_CHANNEL||'chrome'};
  let browser;
  try{browser=await chromium.launch({...launch,headless:true});}
  catch(error){if(candidate)await new Promise(resolve=>candidate.server.close(resolve));throw error;}
  const acceptedHtml=await fs.readFile(path.join(SITE,'index.html'),'utf8');
  const embedded=acceptedHtml.match(/<script id="watch-data" type="application\/json">([\s\S]*?)<\/script>/);
  assert(embedded,'Accepted build has an embedded editorial view');
  const acceptedData=JSON.parse(embedded[1]);
  const summary={mode:MODE,origin,commit:process.env.GITHUB_SHA||null,verified_at:new Date().toISOString(),
    policy:'Native widget output is captured only as intact branded screenshots. No shadow DOM, quote cells, network payloads or series are extracted.',
    visual_review:'Screenshots require visual confirmation of all nine monthly figures and TradingView attribution before publication.',devices:[]};
  let fatal;
  try {
    for(const device of [{name:'desktop',width:1440,height:1100,touch:false},{name:'mobile',width:390,height:844,touch:true}]){
      const context=await browser.newContext({viewport:{width:device.width,height:device.height},hasTouch:device.touch,isMobile:device.touch});
      const page=await context.newPage();const diagnostics={csp:[],failed_origins:[],page_errors:0};
      await page.addInitScript(()=>{window.__watchCspViolations=[];document.addEventListener('securitypolicyviolation',event=>{
        let origin;try{origin=new URL(event.blockedURI).origin;}catch{origin=event.blockedURI==='inline'?'inline':'unknown';}
        window.__watchCspViolations.push({directive:event.effectiveDirective,origin});
      });});
      page.on('pageerror',()=>{diagnostics.page_errors++;});
      page.on('requestfailed',request=>{diagnostics.failed_origins.push(originOnly(request.url()));});
      try {
        const response=await page.goto(origin+'/',{waitUntil:'domcontentloaded',timeout:60000});
        assert(response?.ok(),'Homepage navigation succeeds');
        const csp=response.headers()['content-security-policy']||null;
        if(MODE==='candidate')assert(csp,'Candidate server applies the generated CSP');
        const policySelector='meta[http-equiv="Content-Security-Policy"]';
        const metaPolicy=await page.locator(policySelector).getAttribute('content');
        assert.equal(metaPolicy,"base-uri 'none'; object-src 'none'");
        const probe=await context.newPage();
        let blocked;
        try {
          await probe.goto(origin+'/audit.html');
          assert.equal(await probe.locator(policySelector).getAttribute('content'),metaPolicy);
          // A temporary base element changes URL resolution without loading a
          // resource. Check both its actual effect and the browser's violation.
          blocked=await probe.evaluate(async()=>{
            const original=document.baseURI;
            const violation=new Promise(resolve=>{
              document.addEventListener('securitypolicyviolation',event=>{
                if(event.effectiveDirective==='base-uri')resolve(true);
              });
              setTimeout(()=>resolve(false),1500);
            });
            const base=document.createElement('base');
            base.href='/policy-check/';
            document.head.prepend(base);
            try {return document.baseURI===original&&await violation;}
            finally {base.remove();}
          });
          assert(blocked,'Served document enforces base-uri in the browser');
        } finally {await probe.close();}

        await page.getByRole('heading',{name:'Neocloud stock performance',exact:true}).waitFor({timeout:20000});
        const widget=page.locator('tv-market-data');await widget.waitFor({state:'visible',timeout:20000});
        const configured=JSON.parse(await widget.getAttribute('symbol-sectors'));
        assert.deepEqual(configured.flatMap(section=>section.symbols),SYMBOLS,'Native component receives exactly the nine public focus listings');
        assert.equal(await widget.getAttribute('view'),'performance');
        assert.equal(hash(await page.locator('#watch-data').textContent()),hash(embedded[1]),'Served embedded research matches the accepted build');
        const cap_chart=await capChartChecks(page,acceptedData,SYMBOLS.map(symbol=>symbol.split(':')[1].toLowerCase()));
        await page.locator('#market-cap-chart').screenshot({path:path.join(OUTPUT,device.name+'-market-cap-chart.png')});
        const sizeTable=await sizeTableChecks(page,acceptedData,SYMBOLS.map(symbol=>symbol.split(':')[1].toLowerCase()));
        await page.waitForFunction(()=>customElements.get('tv-market-data')!==undefined,null,{timeout:30000});
        await page.waitForTimeout(13000);
        await screenshotTop(page,device.name+'-homepage');
        await screenshotWidget(page,device.name+'-widget');
        const monthly_screenshots=device.touch?await swipeMonthly(page):[];
        await screenshotSizeTable(page,device.name);
        const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth);
        assert(!overflow,'No horizontal page overflow');
        diagnostics.csp=await page.evaluate(()=>window.__watchCspViolations);
        // The strict candidate server can block the vendor's optional analytics
        // beacon. Retain the diagnostic; every other blocked resource fails QA.
        const unexpected=diagnostics.csp.filter(event=>!(
          MODE==='candidate' && event.directive==='connect-src' &&
          event.origin==='https://snowplow-pixel.tradingview.com'
        ));
        assert.deepEqual(unexpected,[],'Unexpected CSP blocks during widget rendering');
        const cap_groups=await capChartGroupChecks(page,origin,acceptedData,device.name);
        const size_profiles=await sizeProfileChecks(page,origin,acceptedData,SYMBOLS.map(symbol=>symbol.split(':')[1].toLowerCase()));
        const peer_sizes=await peerSizeChecks(page,origin,acceptedData,device.name);
        await page.goto(origin+'/');
        const research=await researchChecks(page,origin,device.name);
        const assets=await verifyAssets(context.request,origin);
        summary.devices.push({name:device.name,viewport:{width:device.width,height:device.height},touch:device.touch,component_registered:true,configured_symbols:SYMBOLS.length,monthly_screenshots,page_overflow:false,csp_header_present:Boolean(csp),document_csp:metaPolicy,document_csp_enforced:blocked,cap_chart,cap_groups,size_table:sizeTable,size_profiles,peer_sizes,research,assets,diagnostics});
      } catch(error){
        await page.screenshot({path:path.join(OUTPUT,device.name+'-failure.png'),fullPage:true}).catch(()=>{});
        diagnostics.csp=await page.evaluate(()=>window.__watchCspViolations||[]).catch(()=>[]);
        summary.devices.push({name:device.name,status:'failed',diagnostics});throw error;
      } finally {await context.close();}
    }
  } catch(error){fatal=error;summary.status='failed';summary.failure=String(error.message).slice(0,700);}
  finally {await browser.close();if(candidate)await new Promise(resolve=>candidate.server.close(resolve));await fs.writeFile(path.join(OUTPUT,'verification.json'),JSON.stringify(summary,null,2)+'\n');}
  if(fatal)throw fatal;
  console.log(JSON.stringify({mode:MODE,status:'passed',devices:summary.devices.length,screenshots:OUTPUT,visual_review_required:true}));
}
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1;});
module.exports={headerRules,startCandidate,csvRows,sizeTableChecks,sizeProfileChecks,peerSizeChecks,capChartChecks,capChartGroupChecks};
