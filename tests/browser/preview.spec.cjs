const {test, expect} = require('@playwright/test');

test('scenario controls, provenance, sharing and export work without backend requests', async ({page}, testInfo) => {
  const errors=[], requests=[];
  page.on('pageerror', error=>errors.push(error.message));
  page.on('request', request=>requests.push({url:request.url(),method:request.method()}));
  await page.goto('/');
  await expect(page.locator('.company-card')).toHaveCount(2);
  await expect(page.locator('#takeaway')).toContainText('CRWV needs $400M more');
  await expect(page.locator('.gap-number').first()).toContainText('$654M');
  await page.locator('#scenario').selectOption('Base');
  await expect(page.locator('.gap-number').first()).toContainText('$200M');
  await expect(page.locator('#takeaway')).toContainText('same $200M funding gap');
  await page.locator('[data-horizon="18"]').click();
  await expect(page.locator('.gap-number').first()).toContainText('$450M');
  await page.locator('#shock').selectOption('300');
  await expect(page.locator('.mini-metrics').first()).toContainText('$15M');
  await page.reload();
  await expect(page.locator('#shock')).toHaveValue('300');
  await expect(page.locator('[data-horizon="18"]')).toHaveAttribute('aria-pressed','true');
  await page.locator('[data-pair="IREN,BTDR"]').click();
  await expect(page.locator('.company-head h3').first()).toHaveText('IREN');
  await page.locator('#swap').click();
  await expect(page.locator('.company-head h3').first()).toHaveText('Bitdeer Technologies Group');
  await page.locator('#left').selectOption('NBIS');
  await expect(page.locator('.company-head h3').first()).toHaveText('Nebius Group');
  await page.locator('.card-detail summary').first().click();
  await expect(page.locator('.card-detail').first()).toContainText('Unavailable — no quote feed');
  await page.getByText('Open the source ledger & supporting passages').click();
  await expect(page.locator('.evidence-card').first()).toBeVisible();
  await expect(page.locator('#reference-cards')).toContainText('$3.25B');
  await expect(page.locator('#reference-cards')).toContainText('6.192%');
  await expect(page.locator('#reference-cards')).toContainText('drawn balance unknown');
  const downloadPromise=page.waitForEvent('download');
  await page.locator('#download').click();
  const download=await downloadPromise;
  const payload=JSON.parse(require('fs').readFileSync(await download.path(),'utf8'));
  expect(payload.disclosure).toContain('Synthetic');
  expect(payload.selection.left).toBe('NBIS');
  await page.locator('#reset').click();
  await expect(page.locator('#scenario')).toHaveValue('Tight credit');
  await expect(page.locator('.gap-number').first()).toContainText('$654M');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  expect(requests.every(r=>r.method==='GET'&&!r.url.includes('/api/'))).toBe(true);
  await page.screenshot({path:`work/preview-${testInfo.project.name}.png`, fullPage:true});
});

test('invalid shared parameters fall back safely; failed data fetch shows recovery message', async ({page}) => {
  await page.goto('/?left=UNKNOWN&right=INVALID&scenario=unsupported&shock=999&horizon=99');
  await expect(page.locator('#left')).toHaveValue('CRWV');
  await expect(page.locator('#right')).toHaveValue('HUT');
  await expect(page.locator('#scenario')).toHaveValue('Tight credit');
  await page.route('**/data.json',route=>route.fulfill({status:503,body:'unavailable'}));
  await page.reload();
  await expect(page.locator('#error')).toBeVisible();
  await expect(page.locator('#error')).toContainText('reload');
});

test('subdirectory assets stay inside neoclouddebt and root is not an app fallback', async ({page, request}) => {
  const paths=[];
  page.on('request',r=>paths.push(new URL(r.url()).pathname));
  await page.goto('http://127.0.0.1:8001/neoclouddebt/');
  await expect(page.locator('.company-card')).toHaveCount(2);
  expect(paths.every(p=>p.startsWith('/neoclouddebt/'))).toBe(true);
  const root=await request.get('http://127.0.0.1:8001/');
  expect(await root.text()).not.toContain('SCENARIO WORKBENCH');
});

test('standalone HTML works offline when loaded directly as browser content', async ({page, context}) => {
  const requests=[], errors=[];
  page.on('request',r=>requests.push(r.url()));
  page.on('pageerror',e=>errors.push(e.message));
  await context.setOffline(true);
  const {resolve}=require('path');
  const html=require('fs').readFileSync(resolve('work/NeoCloud-Interactive-Preview.html'),'utf8');
  await page.setContent(html);
  await expect(page.locator('.company-card')).toHaveCount(2);
  await expect(page.locator('.gap-number').first()).toContainText('$654M');
  await page.locator('#scenario').selectOption('Base');
  await expect(page.locator('.gap-number').first()).toContainText('$200M');
  await page.locator('[data-horizon="18"]').click();
  await expect(page.locator('.gap-number').first()).toContainText('$450M');
  await page.locator('[data-pair="IREN,BTDR"]').click();
  await expect(page.locator('.company-head h3').first()).toHaveText('IREN');
  await expect(page.locator('#reference-cards')).toContainText('$3.25B');
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});
