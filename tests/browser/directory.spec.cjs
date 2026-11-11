const {test,expect}=require('@playwright/test');
const fs=require('fs');
const {resolve}=require('path');

test('actual directory has dated borrowing ranks, honest unknowns and distinct peer groups',async({page},info)=>{
  const errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>requests.push({url:r.url(),method:r.method()}));
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(11);
  await expect(page.locator('#company-count')).toHaveText('15');
  await expect(page.locator('#ranking-rows tr').first()).toHaveAttribute('data-ticker','CRWV');
  await expect(page.locator('[data-ticker="CRWV"] .metric-value')).toHaveText('$46.87B');
  await expect(page.locator('[data-ticker="GLXY"] .rank-number')).toHaveText('—');
  await expect(page.locator('[data-ticker="GLXY"] .metric-value')).toContainText('unknown');
  await expect(page.locator('[data-ticker="NBIS"]')).toContainText('Jun 30, 2026');
  await page.locator('[data-group="all"]').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(15);
  await expect(page.locator('#result-count')).toContainText('14 ranked');
  await page.locator('[data-group="data_center_reit"]').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(2);
  expect(await page.locator('#ranking-rows tr').evaluateAll(rows=>rows.map(r=>r.dataset.ticker))).toEqual(['EQIX','DLR']);
  await page.locator('[data-group="bitcoin_mining"]').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(2);
  await page.locator('#reset').click();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  expect(requests.every(r=>r.method==='GET'&&!r.url.includes('/api/'))).toBe(true);
  await page.screenshot({path:`work/debt-preview-${info.project.name}.png`,fullPage:true});
});

test('asset ratios retain sources and HUT reconciliation excludes the SAFE liability',async({page})=>{
  await page.goto('/?metric=debt_assets&group=all');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(15);
  await expect(page.locator('#ranking-rows tr').first()).toHaveAttribute('data-ticker','HUT');
  await expect(page.locator('[data-ticker="HUT"] .metric-value')).toHaveText('73.82%');
  await expect(page.locator('#metric-description')).toContainText('$100');
  await page.locator('[data-ticker="HUT"] .company-button').click();
  await expect(page.locator('#company-dialog')).toBeVisible();
  await expect(page.locator('#detail-content')).toContainText('$7,628,225,000');
  await expect(page.locator('#detail-content')).toContainText('SAFE');
  await expect(page.locator('.reconciliation')).toBeVisible();
  await expect(page.locator('#detail-content')).toContainText('USD thousands');
  await expect(page.locator('#detail-content')).toContainText('3.275');
  await page.keyboard.press('Escape');
  await expect(page.locator('#company-dialog')).not.toBeVisible();
  await page.locator('#search').fill('NBIS');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(1);
  await page.locator('.company-button').click();
  await expect(page.locator('#detail-content')).toContainText('June');
  await expect(page.locator('#detail-content')).toContainText('August');
});

test('coupon reference has zero coupons and instrument terms but no company rank',async({page})=>{
  await page.goto('/?metric=coupon&group=all');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(15);
  expect((await page.locator('.rank-number').allTextContents()).every(r=>r==='—')).toBe(true);
  await expect(page.locator('[data-ticker="HIVE"] .metric-value')).toHaveText('0%');
  await expect(page.locator('[data-ticker="HUT"] .metric-value')).toHaveText('6.192%');
  await expect(page.locator('[data-ticker="CRWV"] .metric-value')).toHaveText('9.625%');
  await expect(page.locator('[data-ticker="CIFR"]')).toContainText('project');
  await expect(page.locator('[data-ticker="DLR"] .metric-value')).toContainText('unknown');
  await expect(page.locator('#metric-caveat')).toContainText('not current market yield');
  await expect(page.locator('#metric-caveat')).toContainText('continued outstanding status');
  await page.locator('[data-ticker="APLD"] .company-button').click();
  await expect(page.locator('#detail-content')).toContainText('Issue date unknown');
  await expect(page.locator('#detail-content')).toContainText('Exact legal issuer');
  await expect(page.locator('#detail-content')).toContainText('selected');
});

test('filters and company details survive reload; hostile URL keys cannot select inherited properties',async({page})=>{
  await page.goto('/?metric=debt_assets&group=gpu_cloud&order=asc&q=NBIS&company=NBIS');
  await expect(page.locator('#company-dialog')).toBeVisible();
  await expect(page.locator('#detail-title')).toHaveText('Nebius Group');
  await page.keyboard.press('Escape');
  await expect(page.locator('#search')).toHaveValue('NBIS');
  await page.reload();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(1);
  await expect(page.locator('#tab-debt_assets')).toHaveAttribute('aria-selected','true');
  for(const bad of ['__proto__','constructor','toString']){
    await page.goto('/?'+new URLSearchParams({metric:bad,group:bad,company:bad,order:bad}));
    await expect(page.locator('#ranking-rows tr')).toHaveCount(11);
    await expect(page.locator('#error')).toBeHidden();
  }
  await page.locator('#search').fill('company that does not exist');
  await expect(page.locator('#empty')).toBeVisible();
  await page.locator('#clear-search').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(11);
});

test('downloads preserve unknown values, dates, units and source lineage',async({page})=>{
  await page.goto('/?group=all');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(15);
  const jsonPromise=page.waitForEvent('download');
  await page.locator('#download-json').click();
  const jsonDownload=await jsonPromise;
  const exported=JSON.parse(fs.readFileSync(await jsonDownload.path(),'utf8'));
  expect(exported.rows).toHaveLength(15);
  const unknown=exported.rows.find(r=>r.ticker==='GLXY');
  expect(unknown.value).toBeNull();
  expect(unknown.ranked).toBe(false);
  const hut=exported.rows.find(r=>r.ticker==='HUT');
  expect(hut.value).toBe('7628225000');
  expect(hut.unit).toBe('USD');
  expect(hut.as_of).toBe('2026-09-30');
  expect(hut.source_urls[0]).toContain('sec.gov/Archives');
  await page.locator('#tab-coupon').click();
  const couponPromise=page.waitForEvent('download');
  await page.locator('#download-json').click();
  const couponDownload=await couponPromise;
  const coupons=JSON.parse(fs.readFileSync(await couponDownload.path(),'utf8'));
  expect(coupons.rows.every(r=>r.ranked===false)).toBe(true);
  expect(coupons.rows.find(r=>r.ticker==='HIVE').value).toBe('0');
  const crwvNote=coupons.rows.find(r=>r.ticker==='CRWV');
  expect(crwvNote.source_date).toBe('2026-06-18');
  expect(crwvNote.company_source_date).toBe('2026-11-10');
  expect(crwvNote.scope).toBe('Corporate unsecured note');
  expect(crwvNote.source_precision_usd).toBeNull();
  const csvPromise=page.waitForEvent('download');
  await page.locator('#download-csv').click();
  const csvDownload=await csvPromise;
  expect(fs.readFileSync(await csvDownload.path(),'utf8')).toContain('source_urls');
});

test('missing data shows a useful failure rather than an empty ranking',async({page})=>{
  await page.route('**/data.json',route=>route.fulfill({status:503,body:'unavailable'}));
  await page.goto('/');
  await expect(page.locator('#error')).toBeVisible();
  await expect(page.locator('#result-count')).toContainText('unavailable');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(0);
});

test('directory standalone runs with no server or network',async({page,context})=>{
  const requests=[],errors=[];
  page.on('request',r=>requests.push(r.url()));
  page.on('pageerror',e=>errors.push(e.message));
  await context.setOffline(true);
  await page.setContent(fs.readFileSync(resolve('work/NeoCloud-Interactive-Preview.html'),'utf8'));
  await expect(page.locator('#ranking-rows tr')).toHaveCount(11);
  await page.locator('[data-group="all"]').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(15);
  await page.locator('#tab-coupon').click();
  await expect(page.locator('[data-ticker="HIVE"] .metric-value')).toHaveText('0%');
  await page.locator('[data-ticker="HUT"] .company-button').click();
  await expect(page.locator('#detail-content')).toContainText('USD thousands');
  expect(requests).toEqual([]);expect(errors).toEqual([]);
});

test('directory assets work under the preferred subdirectory without API requests',async({page})=>{
  const paths=[];page.on('request',r=>paths.push(new URL(r.url()).pathname));
  await page.goto('http://127.0.0.1:8001/neoclouddebt/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(11);
  await page.locator('#tab-debt_assets').click();
  await expect(page.locator('[data-ticker="HUT"] .metric-value')).toHaveText('73.82%');
  expect(paths.every(p=>p.startsWith('/neoclouddebt/'))).toBe(true);
});

test('tabs support keyboard navigation and focus indicators on light and dark surfaces',async({page})=>{
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(11);
  await page.locator('#tab-debt').focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('#tab-debt_assets')).toBeFocused();
  await expect(page.locator('#tab-debt_assets')).toHaveAttribute('aria-selected','true');
  await page.keyboard.press('End');
  await expect(page.locator('#tab-coupon')).toBeFocused();
  for(const selector of ['header .brand','header nav a','#reset','#tab-coupon','[data-group="all"]','#search','#direction','#share','.company-button','#download-json']){
    const target=page.locator(selector).first();await target.focus();
    expect(await target.evaluate(e=>e.matches(':focus-visible')),selector).toBe(true);
    expect(await target.evaluate(e=>parseFloat(getComputedStyle(e).outlineWidth)),selector).toBeGreaterThanOrEqual(3);
  }
});

test('small directory text and keyboard outlines retain contrast on actual backgrounds',async({page})=>{
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(11);
  const ratios=await page.locator('.eyebrow,.metric-tabs small,.group-note,.rank-number,.row-date,.evidence-pill,footer p').evaluateAll(elements=>{
    const rgb=value=>value.match(/[\d.]+/g).map(Number);
    const luminance=values=>values.slice(0,3).map(v=>{const c=v/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4;}).reduce((sum,c,i)=>sum+c*[.2126,.7152,.0722][i],0);
    return elements.filter(e=>e.getClientRects().length).map(element=>{
      const fg=luminance(rgb(getComputedStyle(element).color));let node=element,bg=1;
      while(node){const values=rgb(getComputedStyle(node).backgroundColor);if(values.length===3||values[3]===1){bg=luminance(values);break;}node=node.parentElement;}
      return {text:element.textContent,ratio:(Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05)};
    });
  });
  for(const r of ratios)expect(r.ratio,r.text).toBeGreaterThanOrEqual(4.5);
});
