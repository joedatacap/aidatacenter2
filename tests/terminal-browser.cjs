// Open the actual downloadable file. Pages and filters must work without a web server.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium, expect} = require('@playwright/test');

async function checkLayout(page) {
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    'Comparison scrolling must stay inside the table');
}

async function exercise(browser, directory, device, viewport) {
  const localURL = process.env.TERMINAL_PREVIEW_TEST_URL;
  const context = await browser.newContext({viewport, hasTouch: device === 'mobile', offline: !localURL});
  try {
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const preview = localURL || pathToFileURL(path.join(directory, 'Neocloud-Intelligence-Terminal.html')).href;
    await page.goto(preview + '#/desk-tools');
    await expect(page.locator('#page-title')).toContainText('What deserves your attention');
    await expect(page.locator('[data-desk-change]')).toHaveCount(6);
    await checkLayout(page);
    await page.screenshot({path: path.join(directory, device + '-desk.png')});
    await page.goto(preview + '#/catalysts?peers=agpu');
    await expect(page.locator('[data-catalyst=agpu-dec17-plan-vote]')).toHaveCount(1);
    await expect(page.locator('[data-catalyst]')).toHaveCount(3);
    await expect(page.locator('#page-content')).toContainText('first quarter 2027');
    await expect(page.locator('[data-catalyst="agpu-georgia-ownership"]')).toHaveCount(0);
    await checkLayout(page);
    await page.goto(preview + '#/catalysts?peers=apld');
    await expect(page.locator('[data-catalyst="apld-pf1-buildout"]')).toHaveCount(1);
    await page.goto(preview + '#/thesis');
    await expect(page.locator('[data-thesis]')).toHaveCount(3);
    const crwvForm = page.locator('[data-thesis=crwv]');
    const apldForm = page.locator('[data-thesis=apld]');
    await apldForm.locator('[name=thesis]').fill('Unsaved APLD draft');
    await crwvForm.locator('[name=thesis]').fill('<img src=x onerror=alert(1)> My growth thesis');
    await crwvForm.locator('[name=expectation]').fill('Delivery within this quarter');
    await crwvForm.locator('[name=invalidation]').fill('Customer acceptance postponed');
    await crwvForm.locator('[name=reviewedThrough]').fill('2026-11-01');
    await crwvForm.locator('button[type=submit]').click();
    await expect(page.locator('#thesis-status')).toContainText('saved');
    await expect(apldForm.locator('[name=thesis]')).toHaveValue('Unsaved APLD draft');
    await page.reload();
    await expect(crwvForm.locator('[name=thesis]')).toHaveValue('<img src=x onerror=alert(1)> My growth thesis');
    await expect(crwvForm.locator('img')).toHaveCount(0);
    await expect(apldForm.locator('[name=thesis]')).toHaveValue('');
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#export-theses').click();
    const download = await downloadPromise;
    const exported = JSON.parse(await fs.readFile(await download.path(), 'utf8'));
    assert.equal(exported.notes.crwv.invalidation, 'Customer acceptance postponed');
    await checkLayout(page);
    await page.screenshot({path: path.join(directory, device + '-thesis.png')});
    await page.goto(preview + '#/desk-tools?peers=crwv');
    await expect(page.locator('#page-content')).toContainText('Published after your last review');
    // Corrupt storage must never be silently overwritten by a save.
    await page.evaluate(() => localStorage.setItem('neocloud-theses-v1', '{broken'));
    await page.goto(preview + '#/thesis');
    await page.locator('[data-thesis=crwv] button[type=submit]').click();
    await expect(page.locator('#thesis-status')).toContainText('could not be read');
    assert.equal(await page.evaluate(() => localStorage.getItem('neocloud-theses-v1')), '{broken');
    await page.evaluate(() => localStorage.removeItem('neocloud-theses-v1'));
    await page.goto(preview + '#/compare');
    const data = JSON.parse(await page.locator('#terminal-data').textContent());
    assert.deepEqual(data.map(item => item.ticker), ['CRWV', 'APLD', 'AGPU']);
    await expect(page.locator('th[data-company]')).toHaveCount(3);
    await checkLayout(page);
    await page.screenshot({path: path.join(directory, device + '-comparison.png')});
    const metric = page.locator('td[data-company=crwv][data-kind=revenue] button[data-source]').first();
    await metric.click();
    const dialog = page.locator('#evidence-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('a.source-link')).toHaveAttribute('href', /^https:\/\//);
    await expect(dialog).toContainText('2026-09-30');
    assert((await dialog.locator('blockquote').innerText()).trim());
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();

    for (const company of data) {
      await page.goto(preview + '#/companies/' + company.id);
      await expect(page.locator('#page-title')).toContainText(company.name);
      await expect(page.locator('.questions')).toContainText(company.questions[0]);
      await checkLayout(page);
    }
    await expect(page.locator('.size-context')).toContainText(/unverified/i);
    await page.screenshot({path: path.join(directory, device + '-axe-profile.png')});

    await page.goto(preview + '#/history?peers=crwv');
    const company = data[0];
    const milestone = company.milestones.find(record => record.revisions.length && record.revisions[0].published > record.original.published);
    assert(milestone, 'Review data contains a genuine revision');
    const entry = page.locator('[data-milestone="' + milestone.id + '"]');
    await expect(entry).toContainText(milestone.revisions[0].target);
    await page.locator('#asof').fill(milestone.original.published);
    await expect(entry).toContainText(milestone.original.target);
    await expect(entry).not.toContainText(milestone.revisions[0].target);
    await page.reload();
    await expect(entry).not.toContainText(milestone.revisions[0].target);
    await checkLayout(page);
    await page.screenshot({path: path.join(directory, device + '-history.png')});

    await page.goto(preview + '#/history?peers=agpu&asof=2026-10-01');
    const georgia = page.locator('[data-milestone="agpu-georgia-acceptance"]');
    await expect(georgia).toContainText(/past target; completion unverified/i);
    await expect(georgia).not.toContainText(/first quarter 2027 roadmap/i);

    await page.goto(preview + '#/changes?peers=apld');
    await page.locator('#change-type').selectOption('financing');
    const financing = data[1].changes.filter(item => item.type === 'financing');
    assert(financing.length);
    await expect(page.locator('[data-change]')).toHaveCount(financing.length);
    for (const change of financing) {
      const card = page.locator('[data-change="' + change.id + '"]');
      await expect(card).toContainText(change.before);
      await expect(card).toContainText(change.after);
      await expect(card).toContainText(change.why);
    }
    await page.screenshot({path: path.join(directory, device + '-changes.png')});
    await page.locator('#q').fill('unmatched-unrelated-term');
    await expect(page.locator('[data-change]')).toHaveCount(0);
    await page.locator('#reset').click();
    await expect(page.locator('[data-change]')).toHaveCount(data.flatMap(item => item.changes).length);
    await page.locator('#peer-picker > summary').click();
    await page.locator('[data-select=none]').click();
    await expect(page.locator('[data-change]')).toHaveCount(0);
    await checkLayout(page);
    assert.deepEqual(errors, []);
  } finally {
    await context.close();
  }
}

(async () => {
  const directory = path.resolve(process.argv[2] || 'work/terminal-preview');
  await fs.access(path.join(directory, 'Neocloud-Intelligence-Terminal.html'));
  const options = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
    ? {executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE} : {channel: 'chrome'};
  const browser = await chromium.launch(options);
  try {
    await exercise(browser, directory, 'desktop', {width: 1440, height: 1000});
    await exercise(browser, directory, 'mobile', {width: 390, height: 844});
  } finally {
    await browser.close();
  }
  console.log('Standalone preview passed on desktop and touch-sized mobile. All four views, source drawer, three profiles, replay, filters and empty states verified.');
})().catch(error => {console.error(error); process.exitCode = 1;});
