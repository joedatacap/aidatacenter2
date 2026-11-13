const {test, expect} = require('@playwright/test');
const path = require('node:path');
const fs = require('node:fs');

test('universe separates public and private coverage and resets filters', async ({page}) => {
  await page.goto('/');
  await expect(page.locator('#company-rows tr')).toHaveCount(15);
  await page.locator('#listing').selectOption('all');
  await expect(page.locator('#company-rows tr')).toHaveCount(16);
  await page.locator('#search').fill('nscale');
  await expect(page.locator('#company-rows tr')).toHaveCount(1);
  await expect(page.locator('#company-rows')).toContainText('Private reference');
  await page.getByRole('button', {name:'Reset filters'}).click();
  await page.locator('#group').selectOption('gpu_cloud');
  await expect(page.locator('#company-rows tr')).toHaveCount(2);
  await page.locator('#search').fill('not-a-company');
  await expect(page.locator('#empty')).toBeVisible();
});

test('unknown borrowing values sort after known values in both directions', async ({page}) => {
  await page.goto('/');
  for (const value of ['debt_asc','debt_desc']) {
    await page.locator('#order').selectOption(value);
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
  await expect(page.locator('#valuation')).toContainText('No verified market-cap observation');
  await expect(page.locator('#operations')).toContainText('Research pending');
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
