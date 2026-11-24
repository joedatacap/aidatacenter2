const {test,expect}=require('./support.cjs');
const {pathToFileURL}=require('node:url');
const path=require('node:path');

test('market homepage and trading desk form one connected review site',async({page})=>{
 await page.goto('/overview/');
 const before=await page.locator('#watch-data').textContent();
 await expect(page.locator('[data-terminal-link]')).toHaveAttribute('href','/terminal/#/desk');
 await page.locator('[data-terminal-link]').click();
 await expect(page.locator('#page-title')).toContainText('What deserves your attention');
 await page.screenshot({path:test.info().outputPath('integrated-trading-desk.png'),fullPage:true});
 await page.locator('[data-view=catalysts]').click();
 await expect(page.locator('[data-catalyst]').first()).toBeVisible();
 await page.locator('[data-view=thesis]').click();
 const form=page.locator('[data-thesis=agpu]');
 await form.locator('[name=thesis]').fill('Review acceptance evidence');
 await form.locator('button[type=submit]').click();
 await expect(page.locator('#thesis-status')).toContainText('saved');
 await page.getByRole('link',{name:'Markets & prices',exact:true}).click();
 await expect(page).toHaveURL(/\/markets\//);
 await page.locator('[data-terminal-link]').click();
 await page.locator('[data-view=thesis]').click();
 await expect(page.locator('[data-thesis=agpu] [name=thesis]')).toHaveValue('Review acceptance evidence');
 await page.getByRole('link',{name:'← Market homepage',exact:true}).click();
 await expect(page).toHaveURL(/\/overview\//);
 expect(await page.locator('#watch-data').textContent()).toBe(before);
 await page.screenshot({path:test.info().outputPath('integrated-homepage.png'),fullPage:true});
});

test('downloaded review keeps homepage and terminal navigation together',async({page})=>{
 await page.goto(pathToFileURL(path.resolve('work/Neocloud-Watch-V2.html')).href);
 await page.locator('[data-terminal-link]').click();
 await expect(page.locator('#page-title')).toContainText('What deserves your attention');
 await page.getByRole('link',{name:'← Market homepage',exact:true}).click();
 await expect(page.locator('[data-terminal-link]')).toBeVisible();
});
