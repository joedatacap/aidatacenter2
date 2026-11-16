const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const FOCUS=['CRWV','NBIS','IREN','APLD','HUT','WULF','WYFI','SHAZ','AGPU'];
const rows=page=>page.locator('[data-company]');
async function choosePeers(page,tickers){
 await page.locator('#peer-picker summary').click();
 for(const ticker of tickers) await page.getByRole('checkbox',{name:`Select ${ticker}`,exact:true}).check();
 await page.locator('#peer-picker summary').click();
}

test('all nine focus companies and wider universe remain reachable',async({page})=>{
 await page.goto('/overview/');
 await expect(rows(page)).toHaveCount(9);
 for(const ticker of FOCUS) await expect(page.locator('#page-content')).toContainText(ticker);
 await page.locator('#focus').selectOption('all');
 await expect(rows(page)).toHaveCount(19);
 await expect(page.locator('#page-content')).toContainText('Galaxy');
 await page.locator('#q').fill('AGPU');
 await expect(rows(page)).toHaveCount(1);
 await expect(rows(page)).toContainText('Axe Compute');
});

test('four pages preserve selected peers and restore back/forward state',async({page})=>{
 await page.goto('/overview/');
 await choosePeers(page,['CRWV','NBIS']);
 await expect(rows(page)).toHaveCount(2);
 for(const [name,path] of [['Earnings','/earnings/'],['Financing & Debt','/financing/'],['Buildout','/buildout/']]){
  await page.locator('#primary-nav').getByRole('link',{name,exact:true}).click();
  expect(new URL(page.url()).pathname).toBe(path);
  expect(new URL(page.url()).searchParams.get('peers')).toContain('crwv');
  await expect(rows(page)).toHaveCount(2);
  await expect(page.locator('#primary-nav').getByRole('link',{name,exact:true})).toHaveAttribute('aria-current','page');
 }
 await page.goBack();await expect(page.locator('#primary-nav').getByRole('link',{name:'Financing & Debt',exact:true})).toHaveAttribute('aria-current','page');
 await expect(rows(page)).toHaveCount(2);
 await page.goForward();await expect(rows(page)).toHaveCount(2);
});

test('shared URL restores filters on direct entry and refresh',async({page})=>{
 await page.goto('/earnings/?peers=agpu,wyfi&q=AGPU');
 await expect(rows(page)).toHaveCount(1);
 await expect(page.locator('#q')).toHaveValue('AGPU');
 await page.reload();await expect(rows(page)).toHaveCount(1);
 await page.locator('#primary-nav').getByRole('link',{name:'Financing & Debt',exact:true}).click();
 await expect(rows(page)).toHaveCount(1);await expect(page.locator('#q')).toHaveValue('AGPU');
});

test('nine selected peers are supported and saved locally',async({page})=>{
 await page.goto('/overview/');await choosePeers(page,FOCUS);
 await expect(rows(page)).toHaveCount(9);
 await page.locator('#save-peers').click();
 await page.locator('#reset').click();
 await page.locator('#load-peers').click();
 expect((new URL(page.url()).searchParams.get('peers')||'').split(',')).toHaveLength(9);
 await expect(page.locator('body')).toContainText(/local/i);
});

test('each generated page and all company profiles refresh without script errors',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 for(const route of ['/','/overview/','/financing/','/earnings/','/buildout/',...FOCUS.map(t=>`/companies/${t.toLowerCase()}/`)]){
  const response=await page.goto(route);expect(response.status()).toBe(200);
  await expect(page.locator('#page-content')).not.toBeEmpty();
 }
 expect(errors).toEqual([]);
});

test('financing retains principal, coupons, cash restrictions and fiscal repayment periods',async({page})=>{
 await page.goto('/companies/crwv/?section=financing');
 await expect(page.locator('#page-content')).toContainText(/47,505|47.505/);
 await expect(page.locator('#page-content')).toContainText(/SOFR/);
 await expect(page.locator('#page-content')).toContainText(/Carrying|carrying/);
 await page.goto('/financing/?peers=iren&tab=repayments');
 await expect(page.locator('#page-content')).toContainText(/FY2027/);
 await expect(page.locator('#page-content')).toContainText(/06-30|June 30/);
 await page.goto('/companies/hut/?section=financing');
 await expect(page.locator('#page-content')).toContainText(/restricted|restrictions/i);
 await expect(page.locator('#page-content')).toContainText(/Timing remains unresolved|timing discrepancy/);
});

test('smaller company evidence and corrected future events remain explicit',async({page})=>{
 await page.goto('/earnings/?peers=agpu,shaz,wyfi');
 await expect(page.locator('#page-content')).toContainText('WhiteFiber');
 await expect(page.locator('#page-content')).toContainText(/2026-09-30/);
 await page.locator('#secondary-nav [data-tab=upcoming]').click();
 await expect(page.locator('#page-content')).toContainText('2026-11-17');
 await expect(page.locator('#page-content')).toContainText('2026-11-16');
});

test('evidence panel exposes sources, dates and excerpts without external navigation',async({page})=>{
 await page.goto('/companies/wyfi/?section=earnings');
 await page.getByRole('button',{name:/Sources \(/}).first().click();
 await expect(page.locator('#evidence-dialog')).toBeVisible();
 await expect(page.locator('#evidence-dialog a').first()).toHaveAttribute('href',/^https:\/\//);
 await expect(page.locator('#evidence-dialog')).toContainText(/2026/);
 await page.locator('#close-evidence').click();await expect(page.locator('#evidence-dialog')).not.toBeVisible();
});

test('filtered evidence export retains exact values, dates and missing reasons',async({page})=>{
 await page.goto('/earnings/?peers=agpu');
 let event=page.waitForEvent('download');await page.locator('#export-json').click();
 let download=await event;const payload=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
 expect(payload.companies).toHaveLength(1);expect(payload.companies[0].ticker).toBe('AGPU');
 expect(payload.sources.length).toBeGreaterThan(0);
 expect(JSON.stringify(payload)).toContain('2026-06-30');
 expect(JSON.stringify(payload)).toMatch(/reason|gaps/);
 expect(JSON.stringify(payload)).not.toContain('aethir_bridge');
 event=page.waitForEvent('download');await page.locator('#export-csv').click();
 download=await event;const csv=fs.readFileSync(await download.path(),'utf8');expect(csv).toContain('AGPU');expect(csv).toContain('2026-06-30');
});

test('standalone offline artifact navigates all pages and company sections without network',async({page},info)=>{
 const requests=[];const errors=[];page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});page.on('pageerror',e=>errors.push(e.message));
 await page.context().setOffline(true);
 await page.setContent(fs.readFileSync('work/Neocloud-Watch-V2.html','utf8'));
 await expect(rows(page)).toHaveCount(9);
 for(const name of ['Financing & Debt','Earnings','Buildout','Overview']){
  await page.locator('#primary-nav').getByRole('link',{name,exact:true}).click();await expect(rows(page)).toHaveCount(9);
 }
 await page.screenshot({path:`work/watch-overview-${info.project.name}.png`,fullPage:true});
 await page.locator('.company-name').filter({hasText:'Axe Compute'}).first().click();
 for(const section of ['financing','earnings','buildout','summary']){
  await page.locator(`[data-section=${section}]`).click();await expect(page.locator('#page-content')).not.toBeEmpty();
 }
 expect(requests).toEqual([]);expect(errors).toEqual([]);
});

test('all page layouts fit mobile and desktop viewports',async({page},info)=>{
 for(const route of ['/overview/','/financing/','/earnings/','/buildout/','/companies/agpu/?section=financing']){
  await page.goto(route);await expect(page.locator('#page-content')).not.toBeEmpty();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
  await page.screenshot({path:`work/watch-${route.split('/')[1]}-${info.project.name}.png`});
 }
});

test('percentage metrics never render as dollar amounts and historical periods retain their own growth',async({page})=>{
 await page.goto('/earnings/?peers=agpu');
 const row=page.locator('[data-company=agpu]').first();
 await expect(row).toContainText('119,772.9%');
 await expect(row).not.toContainText('$119.77K');
 await expect(row).toContainText(/not pure GPU|legacy drug/);
 await page.goto('/companies/iren/?section=earnings&period=2026-06-30');
 await expect(page.locator('#company-earnings')).toContainText('2026-06-30');
 await expect(page.locator('#company-earnings')).toContainText('$137.2M');
 await expect(page.locator('#period')).not.toHaveValue('iren-2026-09-30');
});

test('source excerpts and company names are escaped and unsafe source URLs are inert',async({page})=>{
 let html=fs.readFileSync('work/Neocloud-Watch-V2.html','utf8');
 const match=html.match(/<script id="watch-data" type="application\/json">([\s\S]*?)<\/script>/);
 const data=JSON.parse(match[1]);
 data.companies.find(c=>c.id==='crwv').name='<img src=x onerror="window.injected=true">';
 for(const source of data.sources){source.excerpt='<img src=x onerror="window.injected=true">';source.url='javascript:alert(1)';}
 html=html.replace(match[1],JSON.stringify(data).replaceAll('<','\\u003c'));
 await page.context().setOffline(true);await page.setContent(html);
 await expect(page.locator('[data-company=crwv]')).toContainText('<img src=x');
 await page.getByRole('button',{name:/Sources \(/}).first().click();
 await expect(page.locator('#evidence-dialog')).toContainText('<img src=x');
 await expect(page.locator('#evidence-dialog img')).toHaveCount(0);
 await expect(page.locator('#evidence-dialog a[href^="javascript:"]')).toHaveCount(0);
 expect(await page.evaluate(()=>window.injected)).toBeUndefined();
});

test('snapshot load errors explain recovery',async({page})=>{
 const html=fs.readFileSync('work/Neocloud-Watch-V2.html','utf8').replace(/(<script id="watch-data" type="application\/json">)[\s\S]*?(<\/script>)/,'$1invalid-json$2');
 await page.setContent(html);
 await expect(page.getByRole('alert')).toBeVisible();
 await expect(page.getByRole('alert')).toContainText(/build|snapshot|load/i);
});

test('generated static pages work under a configurable nested base path',async({page},info)=>{
 const {execFileSync}=require('node:child_process');
 const base=`/nested-${info.project.name}/watch/`,output=`work/neocloud-watch-site/nested-${info.project.name}`;
 try {
  execFileSync('python3',['scripts/build_neocloud_watch.py','--base-path',base,'--output',output+'/watch']);
  await page.goto(base+'earnings/?peers=wyfi');
  await expect(rows(page)).toHaveCount(1);
  await page.locator('#primary-nav').getByRole('link',{name:'Buildout',exact:true}).click();
  expect(new URL(page.url()).pathname).toBe(base+'buildout/');
  await page.reload();await expect(rows(page)).toHaveCount(1);
  await page.locator('.company-name').first().click();
  expect(new URL(page.url()).pathname).toBe(base+'companies/wyfi/');
  await page.reload();await expect(page.locator('#page-content')).toContainText('WhiteFiber');
 } finally {fs.rmSync(output,{recursive:true,force:true});}
});

test('historical quarter guidance excludes later revisions',async({page})=>{
 await page.goto('/companies/crwv/?section=earnings&period=2026-06-30');
 await expect(page.locator('#company-earnings .guidance')).toContainText(['$35B–$39B','$12.4B–$13.2B']);
 await expect(page.locator('#company-earnings .guidance')).not.toContainText(['$37B–$39B','$13B–$13.3B']);
 await page.goto('/companies/crwv/?section=earnings&period=2026-09-30');
 await expect(page.locator('#company-earnings .guidance').first()).toContainText('raised');
});

test('profile return link restores the originating secondary view and fiscal period',async({page})=>{
 await page.goto('/earnings/?peers=crwv&tab=history&period=2026-06-30');
 await page.locator('.company-name').first().click();
 await page.locator('[data-section=financing]').click();
 await page.locator('.back').click();
 expect(new URL(page.url()).pathname).toBe('/earnings/');
 expect(new URL(page.url()).searchParams.get('tab')).toBe('history');
 expect(new URL(page.url()).searchParams.get('period')).toBe('2026-06-30');
 await expect(rows(page)).toHaveCount(1);
});
