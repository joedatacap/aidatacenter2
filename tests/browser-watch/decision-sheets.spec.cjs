const {test,expect}=require('./support.cjs');
test('all researched sheets expose sources, dated market context and conditional decisions',async({page})=>{
 for(const id of ['crwv','apld','agpu']){
  await page.goto('/terminal/#/user-sheet/'+id);
  await expect(page.locator('#page-title')).toHaveText(id.toUpperCase()+' trading decision sheet');
  await expect(page.getByRole('heading',{name:'Considering a new position',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Managing an existing holding',exact:true})).toBeVisible();
  await expect(page.locator('.sheet-market')).toContainText('2026-11-25 US close');
  await expect(page.locator('.sheet-market')).toContainText('not a live or executable quote');
  await expect(page.locator('#terminal-controls')).toBeHidden();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 }
 await page.screenshot({path:test.info().outputPath('agpu-decision-sheet.png'),fullPage:true});
});
test('CoreWeave market-calibrated table explicitly discloses circularity and historical basis',async({page})=>{
 await page.goto('/terminal/#/user-sheet/crwv');
 await expect(page.locator('#page-content')).toContainText('by construction');
 await expect(page.locator('#page-content')).toContainText('not an independent');
 await expect(page.locator('#page-content')).toContainText('not a verified future diluted denominator');
 await expect(page.locator('#page-content table tbody tr')).toHaveCount(3);
});
test('cash hurdle computes inputs, invalidates stale output and leaves private scenarios unchanged',async({page})=>{
 await page.goto('/terminal/#/user-sheet/agpu');
 const f=page.locator('[data-sheet-hurdle]');
 await f.locator('[name=price]').fill('10');await f.locator('[name=shares]').fill('10');await f.locator('[name=rate]').fill('10');await f.locator('[name=years]').fill('2');await f.locator('[name=basis]').fill('Synthetic test only');
 await f.getByRole('button').click();
 await expect(page.locator('#sheet-hurdle-result')).toContainText('$57.62M');
 expect(await page.evaluate(()=>localStorage.getItem('neocloud-decisions-v1'))).toBeNull();
 await f.locator('[name=years]').fill('3');
 await expect(page.locator('#sheet-hurdle-result')).toContainText('Inputs changed');
 await expect(page.locator('#sheet-hurdle-result')).not.toContainText('$57.62M');
});
test('APLD and AGPU numeric hurdle tables remain separate from independent price targets',async({page})=>{
 for(const id of ['apld','agpu']){
  await page.goto('/terminal/#/user-sheet/'+id);
  await expect(page.getByRole('heading',{name:'What cash flow would justify the price?',exact:true})).toBeVisible();
  await expect(page.locator('#page-content')).toContainText('Zero terminal value deliberately omits');
  await expect(page.getByRole('heading',{name:'Populated operating sensitivities',exact:true})).toHaveCount(0);
 }
});
