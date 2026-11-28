const { test, expect } = require('@playwright/test');

test('research comparison opens the two sourced underwriting decisions', async ({page, request}, info) => {
  for (const ticker of ['NBIS', 'CRWV']) {
    await page.goto('/research/');
    await expect(page.locator('.uw-audit tbody tr')).toHaveCount(9);
    await page.locator('.uw-comparison').getByRole('link', {name: ticker, exact: true}).click();
    const response = await request.get('/api/v1/companies/' + ticker + '/underwriting.json');
    expect(response.ok()).toBeTruthy();
    const model = (await response.json()).data;
    const base = model.computed.cases.find(row => row.id === 'base');
    const decision = page.locator('[data-underwriting="' + ticker + '"]');
    await expect(decision).toContainText('$' + base.value_per_share.toFixed(2));
    await expect(page.locator('.uw-cases tbody tr')).toHaveCount(3);
    if (info.project.name === 'mobile') {
      const answers = decision.locator('[data-decision-answer]');
      await expect(answers).toHaveCount(3);
      for (const answer of await answers.all()) {
        await expect(answer).toBeInViewport({ratio: 1});
      }
    }
    await expect(page.locator('.uw-source')).toHaveCount(Object.keys(model.sources).length);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
});
