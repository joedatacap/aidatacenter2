const {test, expect} = require('./support.cjs');

test('the default report gives a decision without inputs and compares every cohort member', async ({page}) => {
  await page.goto('/terminal/');
  const report = page.locator('[data-justin-report="crwv"]');
  await expect(report.locator('.justin-verdict')).toContainText('Hold existing shares');
  await expect(report.locator('input:visible')).toHaveCount(0);
  await expect(report.locator('.justin-peers tbody tr')).toHaveCount(9);
  await expect(report.locator('.justin-peers')).toContainText('2.39×');
  await expect(report.locator('.justin-peers')).toContainText('2 of 9');
  await expect(report.locator('.justin-model')).not.toHaveAttribute('open', '');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:test.info().outputPath('justin-report.png'), fullPage:true});
});

test('company profile opens the matching report and a single click saves the dated call', async ({page}) => {
  await page.goto('/companies/agpu/');
  await page.getByRole('link', {name:'Read Justin’s analyst call on AGPU'}).click();
  const report = page.locator('[data-justin-report="agpu"]');
  await expect(report.locator('.justin-call')).toContainText('$7.91');
  await expect(report.locator('.justin-selected')).toContainText('Unreconciled');
  await report.getByRole('button', {name:'Save Justin’s call'}).click();
  await expect(page).toHaveURL(/user-journal\/agpu/);
  await expect(page.locator('[data-journal-entry]')).toHaveCount(1);
  await expect(page.locator('[data-journal-entry]')).toContainText('Original objective $7.91');
  await expect(page.locator('[data-journal-entry]')).toContainText('Research 2026-11-26');
  await page.reload();
  await expect(page.locator('[data-journal-entry]')).toHaveCount(1);
});
