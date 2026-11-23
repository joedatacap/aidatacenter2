const {test,expect}=require('./support.cjs');
const fs=require('node:fs');
const {expectedSize}=require('./size-contract.cjs');

// These checks exercise our host, permissions boundary, research state and
// fallback only. The support fixture blocks nonlocal traffic. Native delivery
// has its own real-browser run; no third-party quote DOM is read here.
const FOCUS=['CRWV','NBIS','IREN','APLD','HUT','WULF','WYFI','SHAZ','AGPU'];
async function researchJSON(page){const pending=page.waitForEvent('download');await page.locator('#export-json').click();return JSON.parse(fs.readFileSync(await(await pending).path(),'utf8'));}

test('capitalization chart leads the homepage while the official stock host remains separate from unpublished price interfaces',async({page})=>{
 await page.goto('/overview/');
 await expect(page.locator('#tradingview-performance')).toBeVisible();
 await expect(page.locator('#page-title')).not.toBeEmpty();
 await expect(page.locator('#tradingview-widget-shell')).toBeVisible();
 await expect(page.locator('#tradingview-guide')).toContainText('1M');
 const widget=page.locator('#tradingview-market-data');
 await expect(widget).toHaveCount(1);
 const configuration=await widget.getAttribute('symbol-sectors');
 expect(configuration).toBeTruthy();
 for(const ticker of FOCUS)expect(configuration.toUpperCase()).toContain('NASDAQ:'+ticker);
 await expect(page.locator('#market-data')).toHaveCount(0);
 await expect(page.locator('.stock-return-row,.scatter-point,.normalized-series-details')).toHaveCount(0);
 const order=await page.evaluate(()=>['#market-cap-chart','#tradingview-performance','#what-changed','#overview-charts','#buildout-tracker','#overview-comparison'].map(s=>document.querySelector(s).getBoundingClientRect().top));
 for(let i=1;i<order.length;i++)expect(order[i]).toBeGreaterThan(order[i-1]);
 const financial=JSON.parse(await page.locator('#watch-data').textContent());
 expect(financial.reviewed_at).toBe('2026-11-17');
});

test('blocked widget loading exposes retry and independent dated research without fabricating returns',async({page})=>{
 await page.goto('/overview/?peers=agpu,nbis');
 await expect(page.locator('#tradingview-fallback')).toBeVisible();
 await expect(page.locator('#tradingview-fallback')).toContainText(/load|unavailable|blocked|network/i);
 await expect(page.locator('#error')).toBeHidden();
 await expect(page.locator('#tradingview-size-context')).toContainText(/Provider-reported market caps/);
 const accepted=JSON.parse(await page.locator('#watch-data').textContent());
 for(const id of ['agpu','nbis']){
  const company=accepted.companies.find(c=>c.id===id),size=expectedSize(company);
  await expect(page.locator('#tradingview-size-context [data-size-company='+id+'] .tradingview-size-badge')).toHaveText(size.label);
 }
 await expect(page.locator('.overview-revenue-card')).toHaveCount(2);
 await page.locator('[data-retry-tradingview]').click();
 await expect(page.locator('#tradingview-fallback')).toBeVisible();
 await expect(page.locator('#tradingview-widget-shell')).toHaveCount(1);
 await expect(page.locator('#tradingview-market-data')).toHaveCount(1);
});

test('a registered component retains one host and updates only our configured peer symbols',async({page})=>{
 // A lifecycle shim, not a replacement market widget: no prices or iframe data.
 await page.addInitScript(()=>{customElements.define('tv-market-data',class extends HTMLElement {});});
 await page.goto('/markets/?peers=crwv,nbis');
 await expect(page.locator('#tradingview-status')).toBeHidden();
 await expect(page.locator('#tradingview-fallback')).toBeHidden();
 await expect(page.locator('#tradingview-market-data')).toHaveCount(1);
 await page.locator('#peer-picker summary').click();
 await page.getByRole('checkbox',{name:'Select NBIS',exact:true}).uncheck();
 const configured=await page.locator('#tradingview-market-data').getAttribute('symbol-sectors');
 expect(configured).toContain('NASDAQ:CRWV');expect(configured).not.toContain('NASDAQ:NBIS');
 await expect(page.locator('#tradingview-size-context [data-size-company]')).toHaveCount(1);
 expect(new URL(page.url()).searchParams.get('peers')).toBe('crwv');
 await page.reload();await expect(page.locator('#tradingview-market-data')).toHaveCount(1);
 await expect(page.locator('#tradingview-fallback')).toBeHidden();
});

test('Markets keeps provider controls separate from research selections and downloadable evidence',async({page})=>{
 await page.goto('/markets/?peers=agpu,wyfi');
 await expect(page.locator('#primary-nav a')).toHaveText(['Overview','Markets','Financing & Debt','Earnings','Buildout']);
 await expect(page.locator('#tradingview-performance')).toBeVisible();
 await expect(page.locator('#shared-controls')).toBeHidden();
 await expect(page.locator('#export-json')).toBeHidden();
 await expect(page.locator('#export-csv')).toBeHidden();
 await page.reload();expect(new URL(page.url()).searchParams.get('peers')).toBe('agpu,wyfi');
 await page.locator('#primary-nav').getByRole('link',{name:'Earnings',exact:true}).click();
 await expect(page.locator('[data-company]')).toHaveCount(2);
 const payload=await researchJSON(page);
 expect(payload.companies.map(c=>c.id).sort()).toEqual(['agpu','wyfi']);
 expect(payload.reviewed_at).toBe('2026-11-17');
 expect(payload).not.toHaveProperty('market_performance');
 const axe=payload.companies.find(c=>c.id==='agpu'),q=axe.quarters.find(q=>q.period_end==='2026-09-30');
 expect(q.metrics.revenue.value).toBe(7243043);
 expect(axe.financing.metrics.cash.value).toBe(147710376);
 expect(axe.financing.metrics.debt.value).toBe(36889299);
 await page.locator('#primary-nav').getByRole('link',{name:'Overview',exact:true}).click();
 const overviewPayload=await researchJSON(page);
 expect(overviewPayload.companies.map(c=>c.id).sort()).toEqual(['agpu','wyfi']);
 expect(overviewPayload).not.toHaveProperty('market_performance');
 await page.locator('#primary-nav').getByRole('link',{name:'Markets',exact:true}).click();
 expect(new URL(page.url()).searchParams.get('peers')).toBe('agpu,wyfi');
 await expect(page.locator('#export-json')).toBeHidden();
});

test('widget fallback remains usable by touch and keyboard without page overflow',async({page},info)=>{
 await page.goto('/markets/');
 const retry=page.locator('[data-retry-tradingview]');
 await expect(page.locator('#tradingview-fallback')).toBeVisible();
 if(info.project.name==='mobile')await retry.tap();else{await retry.focus();await expect(retry).toBeFocused();await page.keyboard.press('Enter');}
 await expect(page.locator('#tradingview-fallback')).toBeVisible();
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:1000});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),String(width)).toBe(true);
  await expect(page.locator('#tradingview-guide')).toBeVisible();
 }
});

test('offline standalone navigation keeps research working and honestly marks the external widget unavailable',async({page})=>{
 const external=[];page.on('request',r=>{if(/^https?:/.test(r.url())&&!/^http:\/\/(?:127\.0\.0\.1|localhost)/.test(r.url()))external.push(r.url());});
 await page.context().setOffline(true);
 await page.setContent(fs.readFileSync('work/Neocloud-Watch-V2.html','utf8'));
 await expect(page.locator('#tradingview-fallback')).toBeVisible();
 await expect(page.locator('#tradingview-fallback')).toContainText(/offline|network|internet/i);
 await page.locator('#primary-nav').getByRole('link',{name:'Markets',exact:true}).click();
 await expect(page.locator('#tradingview-fallback')).toBeVisible();
 await page.locator('#primary-nav').getByRole('link',{name:'Financing & Debt',exact:true}).click();
 await expect(page.locator('[data-company]')).toHaveCount(9);
 expect(external).toEqual([]);
});
