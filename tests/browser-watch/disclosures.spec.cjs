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
  await expect(card).toHaveAttribute('data-size-date',size.date);
  await expect(page.locator('#tradingview-size-context')).toContainText(size.date);
  const source=card.locator('.tradingview-size-attribution a');
  await expect(source).toContainText('$');
  await expect(source).toHaveAttribute('href',company.size_observation.source_url);
  await expect(card.locator('.tradingview-company-link')).toHaveAttribute('href',new RegExp('/companies/'+id+'/'));
  if(company.size_observation.qualification_label)await expect(card.locator('.tradingview-size-qualification')).toContainText(new RegExp(company.size_observation.qualification_label,'i'));
 }
 for(const category of ['large','mid','small']){
  await page.locator('#size').selectOption(category);
  const expected=data.companies.filter(c=>FOCUS.includes(c.id)&&expectedSize(c).label.toLowerCase()===category).map(c=>c.id).sort();
  expect(await page.locator('[data-size-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.sizeCompany).sort())).toEqual(expected);
  await page.locator('#primary-nav').getByRole('link',{name:'Financing & Debt',exact:true}).click();
  expect(new URL(page.url()).searchParams.get('size')).toBe(category);
  expect(await page.locator('[data-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.company).sort())).toEqual(expected);
  await page.locator('#primary-nav').getByRole('link',{name:'Overview',exact:true}).click();
 }
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
  await expect(panel.locator('[data-disclosure-review]')).toContainText(new RegExp(review.status.replaceAll('_',' '),'i'));
  for(const event of review.events||[]){
   const item=panel.locator('.disclosure-event-list li').filter({hasText:event.title});
   await item.locator('summary').click();
   await expect(item.locator('blockquote')).toHaveText(event.supporting_passages);
   await expect(item.getByRole('link',{name:'Read disclosure'})).toHaveAttribute('href',event.source_url);
   await expect(item).toContainText(event.publication_date);
   await expect(panel.locator('a[href="'+event.source_url+'"]').first()).toBeVisible();
  }
  await expect(panel).toContainText('Historical debt ratios use their original inputs and dates.');
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

test('earnings distinguishes checked, partially checked and unreviewed issuers from reporting dates',async({page})=>{
 await page.goto('/earnings/?tab=upcoming&focus=all');
 const rows=page.locator('tr[data-company]');
 await expect(rows.filter({hasText:'Applied Digital'})).toContainText('Checked · no new earnings release');
 await expect(rows.filter({hasText:'WhiteFiber'})).toContainText('Partial check');
 await expect(page.locator('#page-content')).toContainText('Earnings release check: not checked');
 const report=rows.filter({hasText:'Applied Digital'}).locator('.earnings-dates time');
 await expect(report.nth(0)).toHaveAttribute('datetime','2026-08-31');
 await expect(report.nth(1)).toHaveAttribute('datetime','2026-10-07');
});
