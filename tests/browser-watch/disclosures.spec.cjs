const {test,expect}=require('./support.cjs');
const fs=require('node:fs');
const {expectedSize}=require('./size-contract.cjs');
const FOCUS=['crwv','nbis','iren','apld','hut','wulf','wyfi','shaz','agpu'];
async function appData(page){return JSON.parse(await page.locator('#watch-data').textContent());}
async function exportedJSON(page){const pending=page.waitForEvent('download');await page.locator('#export-json').click();return JSON.parse(fs.readFileSync(await(await pending).path(),'utf8'));}

test('dated size badges and common filters match accepted observations independently of historical ratios',async({page})=>{
 await page.goto('/overview/');
 const data=await appData(page);
 for(const id of FOCUS){
  const company=data.companies.find(c=>c.id===id),size=expectedSize(company),card=page.locator('[data-size-company='+id+']');
  expect(company.size_observation).toBeTruthy();
  await expect(card.locator('.tradingview-size-badge')).toHaveText(size.label);
  await expect(card.locator('.tradingview-size-attribution')).toContainText(size.date);
  await expect(card.locator('.tradingview-size-attribution a')).toHaveText('Stock Analysis');
  await expect(card.locator('.tradingview-size-attribution a')).toHaveAttribute('href',company.size_observation.source_url);
  const detail=card.locator('.tradingview-size-note');
  await detail.locator('summary').click();
  if(company.size_observation.source_excerpt)await expect(detail.locator('.size-source-excerpt')).toHaveText(company.size_observation.source_excerpt);
  await detail.locator('summary').click();
  if(company.size_observation.qualification_label)await expect(card.locator('.tradingview-size-qualification')).toHaveText(company.size_observation.qualification_label);
  if(company.size_observation.source_values_disagree||company.size_observation.qualification_label==='Provider figures differ')await expect(card.locator('.tradingview-provider-headline')).toHaveText('Provider headline');
 }
 await page.locator('#size').selectOption('large');
 const expected=data.companies.filter(c=>FOCUS.includes(c.id)&&expectedSize(c).band==='large').map(c=>c.id).sort();
 expect(await page.locator('[data-size-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.sizeCompany).sort())).toEqual(expected);
 await page.locator('#primary-nav').getByRole('link',{name:'Financing & Debt',exact:true}).click();
 expect(new URL(page.url()).searchParams.get('size')).toBe('large');
 expect(await page.locator('[data-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.company).sort())).toEqual(expected);
});

test('company summaries disclose review dates, channels, material events and unchanged historical inputs',async({page})=>{
 for(const id of FOCUS){
  await page.goto('/companies/'+id+'/');
  const data=await appData(page),company=data.companies.find(c=>c.id===id),review=company.disclosure_review;
  expect(review).toBeTruthy();
  const panel=page.locator('#company-data-review');
  await expect(panel).toBeVisible();
  await expect(panel.locator('[data-disclosure-review] time')).toHaveAttribute('datetime',review.checked_at);
  await expect(panel.locator('[data-disclosure-review]')).toContainText(review.checked_at.slice(0,10));
  await expect(panel.locator('[data-disclosure-review]')).toContainText(review.status.replaceAll('_',' '));
  for(const event of review.events||[]){
   await expect(panel.locator('.disclosure-event-list')).toContainText(event.title);
   await expect(panel.locator('.disclosure-event-list')).toContainText(event.publication_date);
   await expect(panel.locator('a[href="'+event.source_url+'"]').first()).toBeVisible();
  }
  await expect(panel).toContainText('Historical financing values, debt ratios and their restrictions retain their original inputs and dates.');
  await page.locator('[data-section=financing]').click();
  const finance=company.financing;
  if(finance?.v2?.market_cap?.as_of)await expect(page.locator('#company-financing')).toContainText(finance.v2.market_cap.as_of);
  if(finance?.v2?.market_cap?.ratio_blocker)await expect(page.locator('#company-financing')).toContainText(finance.v2.market_cap.ratio_blocker);
 }
});

test('research exports keep original financial values and disclosure events without exporting size-feed values or snippets',async({page})=>{
 await page.goto('/overview/?peers=nbis,agpu');
 const data=await appData(page),payload=await exportedJSON(page);
 expect(payload.companies).toHaveLength(2);
 for(const company of payload.companies){
  const accepted=data.companies.find(c=>c.id===company.id);
  expect(company.financing).toEqual(accepted.financing);
  expect(company.market_cap).toEqual(accepted.market_cap);
  expect(company.disclosure_review).toEqual(accepted.disclosure_review);
  expect(company.size_observation).toEqual({ticker:accepted.size_observation.ticker,as_of:accepted.size_observation.as_of,size_band:expectedSize(accepted).band,status:accepted.size_observation.status,source_url:accepted.size_observation.source_url});
  for(const field of ['value','value_usd','source_excerpt','basis','share_basis'])expect(company.size_observation).not.toHaveProperty(field);
 }
 const pending=page.waitForEvent('download');await page.locator('#export-csv').click();
 const csv=fs.readFileSync(await(await pending).path(),'utf8');
 expect(csv.split('\r\n')[0]).toContain('size_observation_json');
 expect(csv.split('\r\n')[0]).toContain('disclosure_review_json');
 expect(csv).not.toContain('source_excerpt');
});

test('new review panels and attributed size context fit phone and desktop widths',async({page})=>{
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:950});
  for(const route of ['/overview/','/companies/nbis/','/companies/agpu/']){
   await page.goto(route);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),route+' at '+width).toBe(true);
  }
 }
});
