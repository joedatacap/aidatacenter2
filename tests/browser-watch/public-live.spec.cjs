/* QA branch only: public smoke checks against the existing, fixed website.
 * No credentials, proxy overrides, deployment or external source navigation.
 */
const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const crypto=require('node:crypto');
const PUBLIC='https://neocloud-watch.gpuchips.chatgpt.site/';
const canonicalFile='work/neocloud-watch-site/data.json';
function sorted(value){if(Array.isArray(value))return value.map(sorted);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,sorted(value[k])]));return value;}
const digest=value=>crypto.createHash('sha256').update(JSON.stringify(sorted(value))).digest('hex');
async function openPublic(page,route='overview/'){
 const url=PUBLIC+route;
 let response;try{response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:30000});}
 catch(error){throw new Error(`Public browser navigation failed for fixed URL ${url}: ${error.message}`);}
 expect(response?.status(),`Public HTTP status at ${url}; final URL ${page.url()}`).toBe(200);
 await expect(page.locator('#page-content'),`Application shell missing at ${url}`).not.toBeEmpty({timeout:15000});
 await expect(page.locator('#error')).toBeHidden();
}
const card=(page,id)=>page.locator(`.overview-revenue-card[data-chart-company="${id}"]`);

test.describe('authorized public Neocloud Watch smoke',()=>{
 test.setTimeout(60000);
 test('live snapshot exactly matches canonical reviewed data and the homepage renders its charts',async({page,request},info)=>{
  const response=await request.get(PUBLIC+'data.json',{timeout:30000});
  expect(response.status(),'Public data.json request status; access rejection is a blocker, not a pass').toBe(200);
  let live;try{live=await response.json();}catch{throw new Error('Public data.json did not return JSON. Content-Type: '+response.headers()['content-type']);}
  const canonical=JSON.parse(fs.readFileSync(canonicalFile,'utf8'));
  console.log('PUBLIC_SMOKE_DIGEST '+JSON.stringify({project:info.project.name,url:PUBLIC,live:digest(live),canonical:digest(canonical),reviewed_at:live.reviewed_at,companies:live.companies?.length}));
  expect(digest(live),'Public/canonical reviewed-data digests differ; do not claim synchronization').toBe(digest(canonical));
  await openPublic(page);
  await expect(page.locator('#what-changed .change-card')).toHaveCount(3);
  await expect(page.locator('.overview-revenue-card')).toHaveCount(9);
  await expect(page.locator('.balance-pair')).toHaveCount(9);
  await expect(page.locator('[data-company]')).toHaveCount(9);
  await expect(card(page,'agpu').locator('.revenue-observation[data-period-end="2026-09-30"]')).toHaveAttribute('data-value','7243043');
  await expect(page.locator('.balance-pair[data-balance-company=agpu] [data-balance-kind=cash]')).toHaveAttribute('data-value','147710376');
  await expect(page.locator('.balance-pair[data-balance-company=agpu] [data-balance-kind=debt]')).toHaveAttribute('data-value','36889299');
  await page.screenshot({path:`work/watch-live-${info.project.name}.png`,fullPage:true});
 });

 test('live shareable peers survive navigation and evidence drawers expose real source links',async({page})=>{
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await openPublic(page,'overview/?peers=agpu,shaz');
  await expect(page.locator('.overview-revenue-card')).toHaveCount(2);
  await expect(page.locator('.balance-pair')).toHaveCount(2);
  await page.locator('#q').fill('AGPU');
  await expect(page.locator('[data-company]')).toHaveCount(1);
  await expect(page.locator('.overview-revenue-card')).toHaveCount(1);
  await page.reload();await expect(card(page,'agpu')).toBeVisible();
  for(const name of ['Earnings','Financing & Debt','Buildout','Overview']){
   await page.locator('#primary-nav').getByRole('link',{name,exact:true}).click();
   expect(new URL(page.url()).origin).toBe(new URL(PUBLIC).origin);
   expect(new URL(page.url()).searchParams.get('peers')).toBe('agpu,shaz');
   await expect(page.locator('#q')).toHaveValue('AGPU');
   await expect(page.locator('[data-company]')).toHaveCount(1);
  }
  const observation=card(page,'agpu').locator('.revenue-observation[data-period-end="2026-09-30"]');
  await observation.locator('summary').click();
  await observation.getByRole('button',{name:/Sources \(/}).click();
  await expect(page.locator('#evidence-dialog')).toBeVisible();
  const links=await page.locator('#evidence-dialog a').evaluateAll(nodes=>nodes.map(n=>n.href));
  expect(links.length).toBeGreaterThan(0);for(const link of links)expect(link).toMatch(/^https:\/\//);
  expect(links.some(link=>/sec\.gov|axecompute/.test(link))).toBe(true);
  await page.locator('#close-evidence').click();
  await card(page,'agpu').getByRole('link',{name:'Earnings & evidence →',exact:true}).click();
  await expect(page.locator('#company-earnings')).toContainText('2026-09-30');
  await page.reload();await expect(page.locator('#company-earnings')).toBeVisible();
  expect(errors).toEqual([]);
 });

 test('live filtered downloads retain exact Axe Q3 values and match the chart selection',async({page})=>{
  await openPublic(page,'overview/?peers=agpu');
  const jsonEvent=page.waitForEvent('download');await page.locator('#export-json').click();
  const payload=JSON.parse(fs.readFileSync(await(await jsonEvent).path(),'utf8'));
  expect(payload.companies).toHaveLength(1);const c=payload.companies[0];expect(c.ticker).toBe('AGPU');
  const q=c.quarters.find(q=>q.period_end==='2026-09-30');
  expect(q.metrics.revenue.value).toBe(7243043);expect(q.metrics.adjusted_ebitda.value).toBe(-2275000);
  expect(q.metrics.net_income.value).toBe(11503607);expect(q.metrics.operating_cash_flow.value).toBeNull();
  expect(c.financing.metrics.cash.value).toBe(147710376);expect(c.financing.metrics.debt.value).toBe(36889299);
  expect(JSON.stringify(c)).toContain('569338973');
  await expect(card(page,c.id).locator('.revenue-observation[data-period-end="2026-09-30"]')).toHaveAttribute('data-value',String(q.metrics.revenue.value));
  const csvEvent=page.waitForEvent('download');await page.locator('#export-csv').click();
  const csv=fs.readFileSync(await(await csvEvent).path(),'utf8');
  for(const value of ['7243043','147710376','36889299','569338973'])expect(csv).toContain(value);
 });

 test('live chart details work by keyboard or tap and the page has no horizontal overflow',async({page},info)=>{
  await openPublic(page,'overview/?peers=agpu,iren,apld');
  const summary=card(page,'agpu').locator('.revenue-observation[data-period-end="2026-09-30"] summary');
  if(info.project.name==='mobile')await summary.tap();else{await summary.focus();await expect(summary).toBeFocused();await page.keyboard.press('Enter');}
  await expect(summary.locator('..')).toHaveAttribute('open','');
  await expect(summary.locator('..')).toContainText('$7,243,043');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
  await expect(page.locator('#buildout-tracker')).toContainText(/customer acceptance|acceptance underway/i);
 });
});
