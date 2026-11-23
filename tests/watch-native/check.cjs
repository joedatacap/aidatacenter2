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

async function swipeMonthly(page) {
  const widget=page.locator('tv-market-data');await widget.scrollIntoViewIfNeeded();
  const box=await widget.boundingBox();assert(box,'Widget host is visible for touch');
  const viewport=page.viewportSize();
  const y=Math.round(Math.min(viewport.height-20,Math.max(30,box.y+Math.min(120,box.height/2))));
  const touch=await page.context().newCDPSession(page);
  async function swipe(from,to){
    await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:from,y}]});
    for(let i=1;i<=12;i++){
      await touch.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:from+(to-from)*i/12,y}]});
      await page.waitForTimeout(25);
    }
    await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    await page.waitForTimeout(700);
  }
  // Prior native-widget proof established this small scroll reveals 1M beside
  // the widget's own pinned company column. Screenshots retain its branding.
  await swipe(Math.min(345,viewport.width-30),190);
  await swipe(Math.min(345,viewport.width-30),230);
  await touch.detach();
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
  return {json_companies:2,csv_companies:2,source_drawer:true,navigation:true,buildout_revised_target:true};
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
        assert(metaPolicy?.includes("default-src 'none'")&&metaPolicy.includes("connect-src 'self'"));
        const probe=await context.newPage();
        let blocked;
        try {
          await probe.goto(origin+'/audit.html');
          assert.equal(await probe.locator(policySelector).getAttribute('content'),metaPolicy);
          // This in-memory resource works without networking. A matching violation
          // proves that the browser enforced connect-src on a served document.
          blocked=await probe.evaluate(async()=>{
            const violation=new Promise(resolve=>{
              document.addEventListener('securitypolicyviolation',event=>{
                if(event.effectiveDirective==='connect-src'&&event.blockedURI==='data')resolve(true);
              });
              setTimeout(()=>resolve(false),1500);
            });
            try {await fetch('data:text/plain,policy-check');return false;}
            catch {return violation;}
          });
          assert(blocked,'Served document enforces connect-src in the browser');
        } finally {await probe.close();}

        await page.getByRole('heading',{name:'Neocloud stock performance',exact:true}).waitFor({timeout:20000});
        const widget=page.locator('tv-market-data');await widget.waitFor({state:'visible',timeout:20000});
        const configured=JSON.parse(await widget.getAttribute('symbol-sectors'));
        assert.deepEqual(configured.flatMap(section=>section.symbols),SYMBOLS,'Native component receives exactly the nine public focus listings');
        assert.equal(await widget.getAttribute('view'),'performance');
        assert.equal(hash(await page.locator('#watch-data').textContent()),hash(embedded[1]),'Served embedded research matches the accepted build');
        const sizeCards=page.locator('[data-size-company]');
        assert.deepEqual(await sizeCards.evaluateAll(cards=>cards.map(card=>card.dataset.sizeCompany)),SYMBOLS.map(symbol=>symbol.split(':')[1].toLowerCase()));
        for(const symbol of SYMBOLS){
          const id=symbol.split(':')[1].toLowerCase(),company=acceptedData.companies.find(c=>c.id===id);
          assert(company,'Accepted application data contains focus company '+id);
          const expected=expectedSize(company),card=page.locator('[data-size-company="'+id+'"]');
          assert.equal((await card.locator('.tradingview-size-badge').innerText()).trim(),expected.label,'Size classification matches accepted app data: '+id);
          if(expected.observation){
            assert((await card.innerText()).includes(expected.date),'Size card shows the actual observation date: '+id);
            assert.equal(await card.locator('.tradingview-size-attribution a').getAttribute('href'),expected.observation.source_url,'Size attribution links to the accepted source: '+id);
            if(expected.observation.source_excerpt)assert.equal((await card.locator('.size-source-excerpt').textContent()).trim(),expected.observation.source_excerpt.trim(),'Editorial source excerpt matches accepted app data: '+id);
            if(expected.observation.qualification_label)assert((await card.innerText()).includes(expected.observation.qualification_label),'Size qualification remains visible: '+id);
          }
        }
        await page.waitForFunction(()=>customElements.get('tv-market-data')!==undefined,null,{timeout:30000});
        await page.waitForTimeout(13000);
        await screenshotTop(page,device.name+'-homepage');
        if(device.touch){await swipeMonthly(page);await screenshotTop(page,'mobile-month');}
        const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth);
        assert(!overflow,'No horizontal page overflow');
        diagnostics.csp=await page.evaluate(()=>window.__watchCspViolations);
        assert.equal(diagnostics.csp.length,0,'CSP must allow the native component without broadening unrelated application permissions');
        const research=await researchChecks(page,origin,device.name);
        const assets=await verifyAssets(context.request,origin);
        summary.devices.push({name:device.name,viewport:{width:device.width,height:device.height},touch:device.touch,component_registered:true,configured_symbols:SYMBOLS.length,page_overflow:false,csp_header_present:Boolean(csp),document_csp:metaPolicy,document_csp_enforced:blocked,research,assets,diagnostics});
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
module.exports={headerRules,startCandidate,csvRows};
