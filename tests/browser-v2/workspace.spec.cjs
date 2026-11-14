const {test, expect} = require('@playwright/test');
const path = require('node:path');
const fs = require('node:fs');
async function selectFilter(page, id, value) {
  if (!await page.locator('#'+id).isVisible()) await page.locator('#filter-toggle').click();
  await page.locator('#'+id).selectOption(value);
}

test('universe separates public and private coverage and resets filters', async ({page}) => {
  await page.goto('/');
  await expect(page.locator('#company-rows tr')).toHaveCount(15);
  await selectFilter(page, 'listing', 'all');
  await expect(page.locator('#company-rows tr')).toHaveCount(16);
  await page.locator('#search').fill('nscale');
  await expect(page.locator('#company-rows tr')).toHaveCount(1);
  await expect(page.locator('#company-rows')).toContainText('Private reference');
  await page.getByRole('button', {name:'Reset filters'}).click();
  await selectFilter(page, 'group', 'gpu_cloud');
  await expect(page.locator('#company-rows tr')).toHaveCount(2);
  await page.locator('#search').fill('not-a-company');
  await expect(page.locator('#empty')).toBeVisible();
});

test('unknown borrowing values sort after known values in both directions', async ({page}) => {
  await page.goto('/');
  for (const value of ['debt_asc','debt_desc']) {
    await selectFilter(page, 'order', value);
    await expect(page.locator('#company-rows tr').last()).toContainText('Galaxy');
    await expect(page.locator('#company-rows tr').last()).toContainText('Not established');
  }
});

test('brief keeps historical principal, note maturity and missing market valuation explicit', async ({page}) => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/#company=CRWV');
  await expect(page.locator('#brief-title')).toHaveText('CoreWeave');
  await expect(page.locator('#financing')).toContainText('$46,873,000,000');
  await expect(page.locator('#financing')).toContainText('no complete principal total inferred');
  await expect(page.locator('#rates')).toContainText('Term SOFR + 5.5 percentage points');
  await expect(page.locator('#rates')).toContainText('2032-07-15');
  await expect(page.locator('#rates')).toContainText('not a company maturity wall');
  await expect(page.locator('#valuation')).toContainText('148.9%');
  await expect(page.locator('#valuation')).toContainText('2026-11-12');
  await expect(page.locator('#operations')).toContainText('A: 24%; B: 30%');
  await page.locator('#financing details').first().locator('summary').click();
  await expect(page.locator('#financing details').first().locator('blockquote')).toBeVisible();
  await page.getByRole('link',{name:'← Company universe'}).click();
  await expect(page.locator('#universe')).toBeVisible();
  expect(errors).toEqual([]);
});

test('cash conditions and private valuation remain distinct', async ({page}) => {
  await page.goto('/#company=IREN');
  await expect(page.locator('#cash')).toContainText('Conditional unfunded commitment');
  await expect(page.locator('#cash')).toContainText('not immediately spendable cash');
  await page.goto('/#company=NSCALE');
  await expect(page.locator('#valuation')).toContainText('Public-market valuation not applicable');
  await expect(page.locator('#financing')).toContainText('Leases outside the borrowing total');
});

test('deep links restore company and unknown routes fall back safely', async ({page}) => {
  await page.goto('/#company=HUT');
  await page.reload();
  await expect(page.locator('#brief-title')).toHaveText('Hut 8');
  await page.goto('/#company=UNKNOWN');
  await expect(page.locator('#universe')).toBeVisible();
});

test('offline HTML works without network and page-level horizontal overflow', async ({page}, testInfo) => {
  const requests=[];const errors=[];
  page.on('request',r=>{if(/^https?:/.test(r.url())) requests.push(r.url());});
  page.on('pageerror',e=>errors.push(e.message));
  await page.context().setOffline(true);
  // The managed browser prohibits file: navigation. Test the exact standalone
  // bytes in an offline page; no server, fetch, or external assets are needed.
  await page.setContent(fs.readFileSync(path.resolve('work/NeoCloud-V2-Workspace.html'), 'utf8'));
  await expect(page.locator('#company-rows tr')).toHaveCount(15);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
  await page.screenshot({path:`work/v2-universe-${testInfo.project.name}.png`,fullPage:true});
  await page.getByRole('link',{name:'CoreWeave',exact:true}).click();
  await expect(page.locator('#brief-title')).toHaveText('CoreWeave');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
  await page.screenshot({path:`work/v2-brief-${testInfo.project.name}.png`,fullPage:true});
  expect(requests).toEqual([]);expect(errors).toEqual([]);
});

test('failed evidence load explains how to recover', async ({page}) => {
  await page.route('**/data.json',r=>r.fulfill({status:503,body:'unavailable'}));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('standalone V2 HTML preview');
});

test('source content is rendered as text, not executable markup', async ({page}) => {
  await page.route('**/data.json',async route=>{
    const response=await route.fetch();const data=await response.json();
    data.sources.find(s=>s.id==='crwv-q3-2026').excerpt='<img src=x onerror="window.injected=true">';
    await route.fulfill({json:data});
  });
  await page.goto('/#company=CRWV');
  await page.locator('#financing summary').first().click();
  await expect(page.locator('#financing blockquote').first()).toContainText('<img src=x');
  expect(await page.evaluate(()=>window.injected)).toBeUndefined();
});

test('valuation handles known mismatch, updated statement and size cohorts', async ({page})=>{
  await page.goto('/#company=NBIS');
  await expect(page.locator('#financing')).toContainText('$14,190,800,000');
  await expect(page.locator('#valuation')).toContainText('Share-count reconciliation pending');
  await expect(page.locator('#valuation')).toContainText('Withheld');
  await expect(page.locator('#company')).not.toContainText('not yet in latest submissions');
  await page.getByRole('link',{name:'← Company universe'}).click();
  await selectFilter(page, 'size', 'small');
  await expect(page.locator('#company-rows tr')).toHaveCount(2);
  await expect(page.locator('#company-rows')).toContainText('HIVE');
  await selectFilter(page, 'order', 'ratio_desc');
  await expect(page.locator('#company-rows tr').first()).toContainText('Bitdeer');
});

test('operating comparison preserves pipeline, contract and hardware scope', async({page})=>{
  await page.goto('/');
  await page.locator('[data-view=operations]').click();
  await page.locator('#search').fill('iren');
  await expect(page.locator('#company-rows')).toContainText('50 MW IT load');
  await page.getByRole('link',{name:'IREN',exact:true}).click();
  await expect(page.locator('#operations')).toContainText('28% / 24% / 18%');
  await expect(page.locator('#operations')).toContainText('five years');
  await expect(page.locator('#operations')).toContainText('GB300');
  await page.goto('/#company=HIVE');
  await expect(page.locator('#operations')).toContainText('approximately 10% deposit');
  await expect(page.locator('#operations')).toContainText('not verified operating');
});

test('repayments preserve principal versus carrying value and no false rolling totals',async({page})=>{
  await page.goto('/#company=CRWV');
  await expect(page.locator('.maturity-chart')).toContainText('$10.97B');
  await expect(page.locator('#financing')).toContainText('$47,505,000,000');
  await expect(page.locator('#financing')).toContainText('Effective accounting rates');
  await page.goto('/#company=HUT');
  await expect(page.locator('#financing')).toContainText('Timing remains unresolved');
  await expect(page.locator('#operations')).toContainText('not the notes');
});

test('exports retain filtered companies, dates, scope and source links',async({page})=>{
  await page.goto('/');
  await page.locator('#search').fill('CRWV');
  let event=page.waitForEvent('download');await page.locator('#export-csv').click();
  let download=await event;const csv=fs.readFileSync(await download.path(),'utf8');
  expect(csv).toContain('debt_market_cap_percent');expect(csv).toContain('148.9');
  expect(csv).toContain('2026-11-12');expect(csv).toContain('2026-09-30');
  expect(csv).toContain('https://stockanalysis.com/stocks/crwv/market-cap/');
  expect(csv).toContain('effective_accounting');expect(csv).not.toContain('Nebius');
  event=page.waitForEvent('download');await page.locator('#export-json').click();
  download=await event;const payload=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  expect(payload.companies).toHaveLength(1);
  expect(payload.companies[0].v2.market_cap.status).toBe('provider_reported');
  expect(payload.sources.find(s=>s.id==='v2-crwv-q').url).toContain('sec.gov');
});

test('keyboard opens a company and mobile views fit the actual layout viewport',async({page})=>{
  await page.goto('/');
  const company=page.getByRole('link',{name:'CoreWeave',exact:true});
  await company.focus();await page.keyboard.press('Enter');
  await expect(page.locator('#brief-title')).toBeFocused();
  await page.getByRole('link',{name:'← Company universe'}).click();
  await expect(page.getByRole('link',{name:'CoreWeave',exact:true})).toBeFocused();
  await page.locator('[data-view=operations]').click();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
});

test('every company brief opens without script errors',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await selectFilter(page, 'listing', 'all');
  const links=await page.locator('.company-name').evaluateAll(nodes=>nodes.map(n=>({name:n.textContent,hash:n.getAttribute('href')})));
  expect(links).toHaveLength(16);
  for(const link of links){
    await page.goto('/'+link.hash);
    await expect(page.locator('#brief-title')).toHaveText(link.name);
    await expect(page.locator('#operations')).toBeVisible();
  }
  expect(errors).toEqual([]);
});


test('repayment comparison preserves fiscal calendars and missing schedules',async({page})=>{
  await page.goto('/');
  await page.locator('[data-view=repayments]').click();
  await page.locator('#search').fill('IREN');
  await expect(page.locator('#company-rows')).toContainText('Remaining FY2027');
  await expect(page.locator('#company-rows')).toContainText('06-30');
  await expect(page.locator('#company-rows')).toContainText('$723M');
  await page.getByRole('link',{name:'IREN',exact:true}).click();
  await expect(page.locator('#financing')).toContainText('October 2026 through June 2027');
  await expect(page.locator('#financing')).toContainText('$10,041,000,000');
  await page.goto('/#company=NBIS');
  await expect(page.locator('#financing')).toContainText('Insufficient schedule coverage');
});

test('repayment export carries timing caveat and fiscal basis',async({page})=>{
  await page.goto('/');
  await page.locator('#search').fill('HUT');
  const event=page.waitForEvent('download');await page.locator('#export-json').click();
  const download=await event;const payload=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  const s=payload.companies[0].v2.maturity_schedule;
  expect(s.period_basis).toBe('calendar');expect(s.total).toBe(7726410000);
  expect(s.timing_issue).toContain('Timing remains unresolved');
  expect(payload.sources.find(r=>r.id===s.source_ids[0]).excerpt).toContain('26,410');
});

test('visible analysis controls preserve peers and expose selected state',async({page})=>{
  await page.goto('/');
  await page.locator('#search').fill('IREN');
  const repayments=page.getByRole('button',{name:/Debt repayment schedules/});
  await repayments.focus();await page.keyboard.press('Enter');
  await expect(repayments).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('[data-view=financing]')).toHaveAttribute('aria-pressed','false');
  await expect(page.locator('#company-rows tr')).toHaveCount(1);
  await expect(page.locator('#view-description')).toContainText('fiscal or calendar');
  await page.getByRole('link',{name:'IREN',exact:true}).click();
  await page.getByRole('link',{name:'← Company universe'}).click();
  await expect(repayments).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('#search')).toHaveValue('IREN');
  await page.locator('#search').fill('no-such-company');
  await page.getByRole('button',{name:/Clear filters/}).click();
  await expect(page.locator('#search')).toBeFocused();
  await expect(page.locator('#company-rows tr')).toHaveCount(15);
  await expect(page.locator('[data-view=financing]')).toHaveAttribute('aria-pressed','true');
});

test('brief navigation follows reading position and supports reduced motion and keyboard',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/#company=IREN');
  const nav=page.getByRole('navigation',{name:'Brief sections'});
  const operations=nav.getByRole('link',{name:'Customers & infrastructure'});
  await operations.focus();await page.keyboard.press('Enter');
  await expect(page.locator('#operations h2')).toBeFocused();
  await expect(operations).toHaveAttribute('aria-current','location');
  const position=await nav.boundingBox();
  expect(position.y).toBeGreaterThanOrEqual(0);expect(position.y).toBeLessThan(20);
  await page.locator('#cash').scrollIntoViewIfNeeded();
  await expect(nav.getByRole('link',{name:'Cash & facilities'})).toHaveAttribute('aria-current','location');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
});

test('compact filters stay discoverable on phones and retain active choices',async({page},testInfo)=>{
  await page.goto('/');
  if(testInfo.project.name==='desktop'){
    await expect(page.locator('#filter-toggle')).not.toBeVisible();
    await expect(page.locator('#group')).toBeVisible();
    return;
  }
  const toggle=page.getByRole('button',{name:/Filters & sort/});
  await expect(toggle).toHaveAttribute('aria-expanded','false');
  await expect(page.locator('#group')).not.toBeVisible();
  await toggle.click();
  await page.locator('#group').selectOption('gpu_cloud');
  await expect(toggle).toContainText('1 changed');
  await toggle.click();
  await expect(page.locator('#company-rows tr')).toHaveCount(2);
  await expect(page.locator('#group')).not.toBeVisible();
  await page.getByRole('button',{name:'Reset filters'}).click();
  await expect(toggle).not.toContainText('changed');
  await expect(page.locator('#company-rows tr')).toHaveCount(15);
});
