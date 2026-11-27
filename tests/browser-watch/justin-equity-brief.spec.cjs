const { test, expect } = require('@playwright/test');

for (const width of [390, 1280]) {
  test(`four-company decision brief at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 860 });
    await page.goto('/research/');
    await page.getByRole('link', { name: 'Four-company decision brief' }).click();
    const cards = page.locator('#decisions article');
    await expect(cards).toHaveCount(4);
    await expect(cards.first()).toContainText('$95.50 (+12.4%)');
    await expect(cards.last()).toContainText('professional ties');
    expect(await page.evaluate(() => document.body.scrollWidth <= window.innerWidth)).toBe(true);
    await page.getByRole('link', { name: 'Download JSON' }).click();
    expect(page.url()).toContain('/api/v1/justin/decisions.json');
  });
}
