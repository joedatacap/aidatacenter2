const {test,expect}=require('@playwright/test');
const fs=require('fs');
const {resolve}=require('path');

test('actual directory has dated borrowing ranks, honest unknowns and distinct peer groups',async({page},info)=>{
  const errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>requests.push({url:r.url(),method:r.method()}));
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
  await expect(page.locator('#company-count')).toHaveText('16');
  await expect(page.locator('#ranking-rows tr').first()).toHaveAttribute('data-ticker','CRWV');
  await expect(page.locator('[data-ticker="CRWV"] .metric-value')).toHaveText('$46.87B');
  await expect(page.locator('[data-ticker="GLXY"] .rank-number')).toHaveText('—');
  await expect(page.locator('[data-ticker="GLXY"] .metric-value')).toContainText('unknown');
  await expect(page.locator('#ranking-rows tr[data-ticker="NBIS"]')).toContainText('Jun 30, 2026');
  await page.locator('[data-group="all"]').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(16);
  await expect(page.locator('#result-count')).toContainText('15 ranked');
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
  await expect(page.locator('#ranking-rows tr')).toHaveCount(16);
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
  await expect(page.locator('#ranking-rows tr')).toHaveCount(44);
  expect((await page.locator('.rank-number').allTextContents()).every(r=>r==='—')).toBe(true);
  await expect(page.locator('[data-instrument="HIVE-2031-APR000"] .metric-value')).toHaveText('0%');
  await expect(page.locator('[data-instrument="CLOUD-HUT-1"] .metric-value')).toHaveText('6.192%');
  await expect(page.locator('[data-instrument="CLOUD-CRWV-1"] .metric-value')).toHaveText('9.625%');
  await expect(page.locator('[data-instrument="CIFR-2030-7125"]')).toContainText('project');
  await expect(page.locator('[data-ticker="DLR"] .metric-value')).toHaveText('4.45%');
  await expect(page.locator('#metric-caveat')).toContainText('not current market yield');
  await expect(page.locator('#metric-caveat')).toContainText('continued outstanding status');
  await page.locator('[data-instrument="APLD-2030-925"] .company-button').click();
  await expect(page.locator('#detail-content')).toContainText('APLD ComputeCo LLC');
  await expect(page.locator('#detail-content')).toContainText('6.75%');
  await expect(page.locator('#detail-content')).toContainText('selected');
  await page.keyboard.press('Escape');
  await page.locator('[data-ticker="DLR"] .company-button').click();
  await expect(page.locator('#detail-content')).toContainText('4.45% note due July 15, 2028');
  await expect(page.locator('#detail-content')).not.toContainText('unreviewed-coupon slot');
  await expect(page.locator('#detail-content')).not.toContainText('no independently reviewed USD fixed-note');
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
    await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
    await expect(page.locator('#error')).toBeHidden();
  }
  await page.locator('#search').fill('company that does not exist');
  await expect(page.locator('#empty')).toBeVisible();
  await page.locator('#clear-search').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
});

test('downloads preserve unknown values, dates, units and source lineage',async({page})=>{
  await page.goto('/?group=all');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(16);
  const jsonPromise=page.waitForEvent('download');
  await page.locator('#download-json').click();
  const jsonDownload=await jsonPromise;
  const exported=JSON.parse(fs.readFileSync(await jsonDownload.path(),'utf8'));
  expect(exported.rows).toHaveLength(16);
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
  expect(crwvNote.scope).toContain('CoreWeave, Inc.');
  expect(crwvNote.source_precision_usd).toBeNull();
  const dlr=coupons.rows.find(r=>r.ticker==='DLR');
  expect(dlr.value).toBe('4.450');
  expect(dlr.company_notes.join(' ')).toContain('4.45% note due July 15, 2028');
  expect(dlr.company_notes.join(' ')+dlr.note).not.toContain('unreviewed-coupon');
  expect(dlr.company_notes.join(' ')).not.toContain('no independently reviewed USD fixed-note');
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
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
  await page.locator('[data-group="all"]').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(16);
  await page.locator('#tab-coupon').click();
  await expect(page.locator('[data-instrument="HIVE-2031-APR000"] .metric-value')).toHaveText('0%');
  await page.locator('[data-instrument="CLOUD-HUT-1"] .company-button').click();
  await expect(page.locator('#detail-content')).toContainText('USD thousands');
  await page.keyboard.press('Escape');await page.locator('#nav-cash').click();
  await expect(page.locator('#tab-cash')).toHaveAttribute('aria-selected','true');
  await expect(page.locator('.bar-fill')).toHaveCount(0);
  await expect(page.locator('[data-ticker="EQIX"] .funding-summary')).toContainText('Approx. $5.5B');
  await page.locator('[data-ticker="EQIX"] .cash-funding-action').click();
  await expect(page.locator('.cash-funding')).toBeFocused();
  expect(requests).toEqual([]);expect(errors).toEqual([]);
});

test('directory assets work under the preferred subdirectory without API requests',async({page})=>{
  const paths=[];page.on('request',r=>paths.push(new URL(r.url()).pathname));
  await page.goto('http://127.0.0.1:8001/neoclouddebt/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
  await page.locator('#tab-debt_assets').click();
  await expect(page.locator('[data-ticker="HUT"] .metric-value')).toHaveText('73.82%');
  expect(paths.every(p=>p.startsWith('/neoclouddebt/'))).toBe(true);
});

test('tabs support keyboard navigation and focus indicators on light and dark surfaces',async({page})=>{
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
  await page.locator('#tab-debt').focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('#tab-debt_assets')).toBeFocused();
  await expect(page.locator('#tab-debt_assets')).toHaveAttribute('aria-selected','true');
  await page.keyboard.press('End');
  await expect(page.locator('#tab-cash')).toBeFocused();
  for(const selector of ['header .brand','header nav a','#reset','#tab-coupon','[data-group="all"]','#search','#direction','#share','.company-button','#download-json']){
    const target=page.locator(selector).first();await target.focus();
    expect(await target.evaluate(e=>e.matches(':focus-visible')),selector).toBe(true);
    expect(await target.evaluate(e=>parseFloat(getComputedStyle(e).outlineWidth)),selector).toBeGreaterThanOrEqual(3);
  }
});

test('small directory text and keyboard outlines retain contrast on actual backgrounds',async({page})=>{
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
  const ratios=await page.locator('.eyebrow,.metric-tabs small,.group-note,.rank-number,.row-date,.evidence-pill,.asset-meter-label,.asset-meter-axis,.financing-rate-label,.financing-rate-kind,.financing-rate-instrument,footer p').evaluateAll(elements=>{
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

test('search preserves peer-group ranks and the fixed asset-share meter',async({page})=>{
  await page.goto('/');
  const row=page.locator('[data-ticker="NBIS"]');
  await expect(row.locator('.rank-number')).toHaveText('3');
  const width=await row.locator('.bar-fill').evaluate(e=>e.style.width);
  await page.locator('#search').fill('NBIS');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(1);
  await expect(row.locator('.rank-number')).toHaveText('3');
  expect(await row.locator('.bar-fill').evaluate(e=>e.style.width)).toBe(width);
  await expect(page.locator('#rank-context')).toContainText('Search only hides rows');
  const downloadPromise=page.waitForEvent('download');await page.locator('#download-json').click();
  const payload=JSON.parse(fs.readFileSync(await (await downloadPromise).path(),'utf8'));
  expect(payload.rows[0].cohort_rank).toBe(3);
});

test('borrowing amounts display their actual asset percentage and sourced denominator',async({page})=>{
  await page.goto('/?q=CRWV');
  const row=page.locator('[data-ticker="CRWV"]');
  await expect(row.locator('.metric-value')).toHaveText('$46.87B');
  await expect(row.locator('.asset-share-value')).toHaveText('51.24%');
  await expect(row.locator('.asset-meter-label')).toHaveText('Borrowings / recorded assets');
  const width=await row.locator('.asset-meter-fill').evaluate(e=>parseFloat(e.style.width));
  expect(width).toBeCloseTo(51.23796,4);
  await expect(row.locator('.asset-meter')).toHaveAttribute('aria-label',/0 to 100 percent/);
  const denominator=row.locator('.asset-denominator');
  await denominator.locator('summary').focus();await page.keyboard.press('Enter');
  await expect(denominator).toHaveAttribute('open','');
  await expect(denominator).toContainText('$91,481,000,000');
  await expect(denominator).toContainText('$46,873,000,000');
  await expect(denominator).toContainText('Sep 30, 2026');
  await expect(denominator).toContainText('Nov 10, 2026');
  await expect(denominator).toContainText('leases excluded');
});

test('asset meters retain values above 100 percent and suppress mismatched snapshots',async({page})=>{
  await page.route('**/data.json',async route=>{
    const response=await route.fetch(),payload=await response.json();
    const crwv=payload.companies.find(c=>c.ticker==='CRWV');
    crwv.metrics.debt_assets.value='125.75';
    const nbis=payload.companies.find(c=>c.ticker==='NBIS');
    nbis.metrics.assets.as_of='2026-03-31';
    await route.fulfill({json:payload});
  });
  await page.goto('/');
  await expect(page.locator('[data-ticker="CRWV"] .asset-share-value')).toHaveText('125.75%');
  expect(await page.locator('[data-ticker="CRWV"] .asset-meter-fill').evaluate(e=>parseFloat(e.style.width))).toBe(100);
  await expect(page.locator('[data-ticker="CRWV"] .asset-meter-overflow')).toBeVisible();
  await expect(page.locator('[data-ticker="NBIS"] .asset-meter')).toHaveCount(0);
  await expect(page.locator('[data-ticker="NBIS"] .asset-share-unknown')).toBeVisible();
  await expect(page.locator('[data-ticker="GLXY"] .asset-meter')).toHaveCount(0);
});

test('up to three companies compare side by side with dated scopes and restored source-dialog focus',async({page})=>{
  await page.goto('/');
  for(const ticker of ['CRWV','NBIS','NSCALE'])await page.locator(`[data-compare="${ticker}"]`).click();
  await expect(page.locator('#selection-count')).toContainText('3');
  await expect(page.locator('[data-compare="HUT"]')).toHaveAttribute('aria-disabled','true');
  await expect(page.locator('#selected-companies .selection-chip')).toHaveCount(3);
  await page.locator('#open-comparison').click();
  await expect(page.locator('#comparison-dialog')).toBeVisible();
  await expect(page.locator('#comparison-content')).toContainText('Reporting dates differ');
  await expect(page.locator('#comparison-content')).toContainText('customer financing');
  await expect(page.locator('#comparison-content')).toContainText('includes accretion');
  await expect(page.locator('#comparison-content')).toContainText('not original amount raised');
  await page.reload();
  await expect(page.locator('#comparison-dialog')).toBeVisible();
  await expect(page.locator('#comparison-content')).toContainText('Private');
  const sourceButton=page.getByRole('button',{name:'Read Nebius Group sources and calculation'});
  await sourceButton.click();
  await expect(page.locator('#company-dialog')).toBeVisible();
  await expect(page.locator('#detail-title')).toHaveText('Nebius Group');
  await page.keyboard.press('Escape');
  await expect(page.locator('#company-dialog')).not.toBeVisible();
  await expect(page.locator('#comparison-dialog')).toBeVisible();
  await expect(sourceButton).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.locator('#comparison-dialog')).not.toBeVisible();
  await page.goto('/?compare=__proto__,CRWV,CRWV,constructor,NBIS,NSCALE,HUT&comparison=1');
  await expect(page.locator('#selected-companies .selection-chip')).toHaveCount(3);
  await expect(page.locator('#comparison-dialog')).toBeVisible();
});

test('note filters separate security types and snapshot confirmation without equating coupon and yield',async({page})=>{
  await page.goto('/?metric=coupon&group=all');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(44);
  await expect(page.locator('#result-count')).toContainText('15 companies');
  await page.locator('#note-type').selectOption('unsecured');
  const unsecured=await page.locator('#ranking-rows tr').evaluateAll(rows=>rows.map(r=>r.dataset.ticker));
  expect(unsecured).toContain('CRWV');expect(unsecured).toContain('DLR');expect(unsecured).not.toContain('CIFR');
  await page.locator('#note-status').selectOption('confirmed');
  expect(await page.locator('#ranking-rows tr').evaluateAll(rows=>rows.some(r=>r.dataset.ticker==='CRWV'))).toBe(false);
  await page.locator('#note-type').selectOption('all');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(38);
  await page.locator('#note-status').selectOption('all');
  await expect(page.locator('[data-instrument="CLOUD-NBIS-7"]')).toContainText('not confirmed');
  await expect(page.locator('[data-instrument="CLOUD-CRWV-1"]')).toContainText('earlier date');
  await page.locator('#note-type').selectOption('secured');
  await expect(page.locator('[data-instrument="CIFR-2030-7125"]')).toBeVisible();
  await expect(page.locator('[data-instrument="CLOUD-CRWV-1"]')).toHaveCount(0);
  await page.locator('#note-type').selectOption('convertible');
  await expect(page.locator('[data-instrument="HIVE-2031-APR000"] .metric-value')).toHaveText('0%');
  await page.reload();await expect(page.locator('#note-type')).toHaveValue('convertible');
});

test('private IPO applicant has actual filing data but no invented ticker or fixed-note coupon',async({page})=>{
  await page.goto('/?q=NSCALE&group=all');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(1);
  await expect(page.locator('[data-ticker="NSCALE"] .metric-value')).toHaveText('$137.4M');
  await expect(page.locator('#ranking-rows tr[data-ticker="NSCALE"]')).toContainText('Private');
  await expect(page.locator('#ranking-rows tr[data-ticker="NSCALE"]')).toContainText('customer financing');
  await page.locator('.company-button').click();
  await expect(page.locator('#detail-content')).toContainText('proposed NSCL is not a verified listed ticker');
  await expect(page.locator('#detail-content')).toContainText('6.4926');
  await expect(page.locator('#detail-content')).toContainText('must not be presented as bond coupons');
  const noCoupon=page.locator('.detail-metric').filter({has:page.getByRole('heading',{name:'Note coupon example',exact:true})});
  await expect(noCoupon.locator('strong')).toHaveText('Unknown');
  await expect(noCoupon).toContainText('No reviewed fixed-rate USD note example');
  await expect(noCoupon).not.toContainText('Type unknown');
  await expect(noCoupon).not.toContainText('Issue date unknown');
  await expect(page.locator('#detail-content')).not.toContainText('unknown_unranked');
  await page.keyboard.press('Escape');
  await page.locator('#tab-debt_assets').click();
  const downloadPromise=page.waitForEvent('download');await page.locator('#download-json').click();
  const payload=JSON.parse(fs.readFileSync(await (await downloadPromise).path(),'utf8'));
  expect(payload.rows[0].trading_ticker).toBeNull();
  expect(payload.rows[0].listing_status).toBe('private_pending_ipo');
  expect(payload.rows[0].metric).toBe('debt_assets');
  expect(payload.rows[0].comparison_caveat).toContain('$6.49B deferred customer revenue');
  expect(payload.rows[0].comparison_caveat).toContain('$2.63B operating leases');
  expect(payload.rows[0].company_notes.length).toBeGreaterThan(0);
  const csvPromise=page.waitForEvent('download');await page.locator('#download-csv').click();
  const csv=fs.readFileSync(await (await csvPromise).path(),'utf8');
  expect(csv).toContain('comparison_caveat');expect(csv).toContain('company_notes');
  expect(csv).toContain('$6.49B deferred customer revenue');
  expect(csv).toContain('$2.63B operating leases');
  await page.locator('#tab-coupon').click();
  await expect(page.locator('#ranking-rows tr')).toHaveCount(0);
  await expect(page.locator('#empty')).toBeVisible();
});

test('partial bridges, lease exclusions and conflicting issue dates remain explicit',async({page})=>{
  await page.goto('/?company=NBIS');
  await expect(page.locator('#company-dialog')).toBeVisible();
  await page.locator('.debt-context summary').click();
  await expect(page.locator('.debt-context')).toContainText('PARTIAL SCOPE');
  await expect(page.locator('.debt-context')).toContainText('Long-term convertible notes only');
  await expect(page.locator('.debt-context')).not.toContainText('noncurrent_convertibles');
  await expect(page.locator('.debt-context')).toContainText('includes accretion');
  await expect(page.locator('.debt-context')).toContainText('principal total is not reconciled');
  await page.keyboard.press('Escape');
  await page.goto('/?company=GLXY');
  await page.locator('.debt-context summary').click();
  await expect(page.locator('.debt-context')).toContainText('not a company debt total');
  await expect(page.locator('.debt-context')).toContainText('industrial');
  const glxyNote=page.locator('.note-detail-card[data-instrument="ADJ-GLXY-SELECTED"]');
  await expect(glxyNote).toContainText('unknown; not inferred from original issue size');
  await page.keyboard.press('Escape');
  await page.goto('/?company=WULF');
  await expect(page.locator('.note-detail-card[data-instrument="WULF-2030-775"]')).toContainText('Conflicting source dates');
  await expect(page.locator('.note-detail-card[data-instrument="WULF-2030-775"]')).toContainText('Issue date unknown');
  await page.keyboard.press('Escape');
  await page.goto('/?company=DLR');
  await page.locator('.debt-context summary').click();
  const financeLease=page.locator('.lease-card').filter({has:page.getByRole('heading',{name:'Finance leases',exact:true})});
  await expect(financeLease.locator('strong')).toHaveText('Unknown');
  await expect(financeLease).toContainText('not independently established');
});

test('private operator financing announcements stay separate from ranked borrowing balances',async({page})=>{
  await page.goto('/');
  await expect(page.locator('#coverage')).toBeVisible();
  await page.locator('#coverage>details>summary').click();
  await expect(page.locator('.coverage-card')).toHaveCount(3);
  await expect(page.locator('#coverage')).toContainText('Facility size is not an outstanding debt balance');
  await expect(page.locator('#coverage')).toContainText('Crusoe');
  await expect(page.locator('#coverage')).toContainText('Lambda');
  await expect(page.locator('#coverage')).toContainText('Vultr');
  expect(await page.locator('#ranking-rows tr').evaluateAll(rows=>rows.some(r=>/CRUSOE|LAMBDA|VULTR/.test(r.dataset.ticker)))).toBe(false);
});

test('first-use walkthrough supports keyboard metric choices and source inspection without an automatic tour',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
  const guide=page.locator('#start-here'),summary=page.locator('#start-here-summary');
  await expect(guide).not.toHaveAttribute('open');
  await expect(page.locator('dialog[open]')).toHaveCount(0);
  await summary.focus();await page.keyboard.press('Enter');
  await expect(guide).toHaveAttribute('open','');
  await expect(guide).toContainText('Arithmetic example — not a company estimate');
  await page.locator('#guide-debt-assets').focus();await page.keyboard.press('Enter');
  await expect(page.locator('#tab-debt_assets')).toHaveAttribute('aria-selected','true');
  await expect(guide).not.toHaveAttribute('open');
  await expect(page.locator('#company-figures')).toBeFocused();
  await expect(page.locator('#metric-description')).toContainText('$100');
  await summary.focus();await page.keyboard.press('Space');
  await page.locator('#guide-coupons').focus();await page.keyboard.press('Enter');
  await expect(page.locator('#tab-coupon')).toHaveAttribute('aria-selected','true');
  expect((await page.locator('.rank-number').allTextContents()).every(r=>r==='—')).toBe(true);
  await summary.focus();await page.keyboard.press('Enter');
  await page.locator('#guide-debt').focus();await page.keyboard.press('Enter');
  await summary.focus();await page.keyboard.press('Enter');
  const sources=page.locator('#guide-source');
  await expect(sources).toContainText('CoreWeave');
  await sources.focus();await page.keyboard.press('Enter');
  await expect(page.locator('#detail-title')).toHaveText('CoreWeave');
  await page.keyboard.press('Escape');
  await expect(page.locator('#company-dialog')).not.toBeVisible();
  await expect(sources).toBeFocused();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('walkthrough preserves a chosen peer group and search and does not fabricate a source for empty results',async({page})=>{
  await page.goto('/?group=gpu_cloud&q=no-such-company&order=desc&note_type=secured&outstanding=confirmed');
  await expect(page.locator('#empty')).toBeVisible();
  await page.locator('#start-here-summary').click();
  await expect(page.locator('#guide-source')).toBeDisabled();
  await page.locator('#guide-coupons').click();
  await expect(page.locator('#search')).toHaveValue('no-such-company');
  await expect(page.locator('[data-group="gpu_cloud"]')).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('#direction')).toHaveValue('desc');
  await expect(page.locator('#note-type')).toHaveValue('secured');
  await expect(page.locator('#note-status')).toHaveValue('confirmed');
  await expect(page.locator('#empty')).toBeVisible();
  await expect(page.locator('dialog[open]')).toHaveCount(0);
});

test('cash and funding distinguish an undrawn parent revolver from restricted project balances',async({page})=>{
  await page.goto('/?company=HUT');
  const funding=page.locator('.cash-funding');
  await expect(funding).toContainText('Cash & funding');
  await expect(funding.locator('.liquidity-reported-cash .liquidity-cash-value')).toHaveText('$156.87M');
  await expect(funding.locator('.liquidity-reported-cash')).toContainText('Sep 30, 2026');
  await expect(funding.locator('.company-credit-availability strong')).toHaveText('Total not established');
  const facility=funding.locator('.liquidity-facility').filter({hasText:'revolving credit'});
  await expect(facility.locator('[data-kind="commitment"] .liquidity-fact-value')).toHaveText('$1.07B');
  await expect(facility.locator('[data-kind="drawn"] .liquidity-fact-value')).toHaveText('$0');
  await expect(facility.locator('[data-kind="reported_available"] .liquidity-fact-value')).toHaveText('Unknown');
  await expect(funding.locator('[data-kind="restricted_cash"] .liquidity-fact-value')).toHaveText('$3.56B');
  await expect(funding.locator('[data-kind="restricted_investments"] .liquidity-fact-value')).toHaveText('$2.84B');
  await expect(funding).toContainText('not added together');
  await expect(funding).not.toContainText('calculated total available');
});

test('letter-of-credit headroom is not spendable cash and later facilities stay outside the snapshot',async({page})=>{
  await page.goto('/?company=WULF');
  const funding=page.locator('.cash-funding');
  const remaining=funding.locator('[data-kind="lc_capacity"]').filter({hasText:'Remaining LC capacity'});
  await expect(remaining.locator('.liquidity-fact-value')).toHaveText('$800K');
  await expect(remaining).toContainText('not cash');
  await expect(funding.locator('.company-credit-availability strong')).toHaveText('Total not established');
  await expect(funding.locator('[data-kind="borrowing_cap"] .liquidity-fact-value')).toHaveText('$75M');
  await expect(funding.locator('[data-kind="commitment"] .liquidity-fact-value')).toHaveText('$250M');
  await page.keyboard.press('Escape');await page.goto('/?company=HIVE');
  await expect(page.locator('.cash-funding .liquidity-facility')).toHaveCount(0);
  await expect(page.locator('.liquidity-inventory-unknown')).toBeVisible();
  await expect(page.locator('.cash-funding')).toContainText('Unknown');
  await page.keyboard.press('Escape');await page.goto('/?company=CRWV');
  await expect(page.locator('.cash-funding .liquidity-facility')).toHaveCount(0);
  await expect(page.locator('.liquidity-notes')).toContainText('Earlier financing announcements are not treated as current availability');
  await expect(page.locator('.liquidity-notes')).not.toContainText('disclosures below');
});

test('source boxes present readable verified passages with units and column context',async({page})=>{
  await page.goto('/?company=IREN');
  const source=page.locator('.source-card').filter({has:page.getByRole('link',{name:'IREN liquidity: cash restrictions and selected facility disclosures',exact:true})});
  await expect(source).toContainText('USD millions');
  await expect(source.locator('.source-excerpt-note')).toContainText('September 30, 2026');
  await expect(source.locator('blockquote')).toContainText('Unfunded commitments');
  await expect(source.locator('blockquote')).toContainText('subject to conditions precedent');
  await expect(source.locator('blockquote')).toContainText('$ 1,500 million of commitment remained available');
  await expect(source.locator('blockquote')).toHaveCSS('white-space','pre-line');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('cash qualifications and conditional credit survive comparison and machine-readable exports',async({page})=>{
  await page.goto('/?group=all&compare=MARA,EQIX&comparison=1');
  const comparison=page.locator('#comparison-dialog');
  await expect(comparison.locator('.cash-qualification').filter({hasText:'Exaion'})).toBeVisible();
  await expect(comparison.locator('.comparison-credit-row .credit-availability-value')).toHaveText(['Total not established','Total not established']);
  const detailButton=comparison.getByRole('button',{name:/Equinix.*cash|cash.*Equinix/i});
  await detailButton.click();
  await expect(page.locator('.cash-funding')).toBeFocused();
  const available=page.locator('.cash-funding [data-kind="reported_available"]');
  await expect(available.locator('.liquidity-fact-value')).toHaveText('$5.5B');
  await expect(available.locator('.liquidity-precision')).toContainText(/pproximate|ounded/);
  await page.keyboard.press('Escape');await expect(detailButton).toBeFocused();
  await page.keyboard.press('Escape');await page.goto('/?group=all&q=MARA');
  const jsonPromise=page.waitForEvent('download');await page.locator('#download-json').click();
  const output=JSON.parse(fs.readFileSync(await (await jsonPromise).path(),'utf8'));
  const row=output.rows[0];expect(row.cash_qualification).toContain('Exaion');
  expect(row.liquidity.company_available_credit.value).toBeNull();
  expect(row.liquidity_source_ids.length).toBeGreaterThan(0);
  expect(row.liquidity_source_ids.every(id=>output.sources.some(source=>source.id===id))).toBe(true);
  const csvPromise=page.waitForEvent('download');await page.locator('#download-csv').click();
  const csv=fs.readFileSync(await (await csvPromise).path(),'utf8');
  expect(csv).toContain('cash_qualification');expect(csv).toContain('Exaion');
  expect(csv).toContain('company_available_credit');expect(csv).not.toContain('[object Object]');
});

test('cash is a top-level unranked view with separately qualified facility amounts',async({page})=>{
  await page.goto('/');
  await expect(page.locator('#tab-cash')).toBeVisible();
  await page.locator('#nav-cash').focus();await page.keyboard.press('Enter');
  await expect(page.locator('#tab-cash')).toHaveAttribute('aria-selected','true');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
  expect((await page.locator('.rank-number').allTextContents()).every(text=>text==='—')).toBe(true);
  await expect(page.locator('.bar-fill')).toHaveCount(0);
  await expect(page.locator('#direction option:checked')).toContainText('Largest reported cash');
  const iren=page.locator('[data-ticker="IREN"] .funding-summary');
  await expect(iren.locator('.funding-total-status')).toHaveText('Total not established');
  await expect(iren.locator('.funding-facility-count')).toContainText('4 selected facilities');
  await expect(iren.locator('.funding-amount')).toHaveCount(3);
  await expect(iren).toContainText('$1.132B');await expect(iren).toContainText('$525M');
  await expect(iren).toContainText('$1.5B');await expect(iren).toContainText('Conditional');
  const wulf=page.locator('[data-ticker="WULF"] .funding-summary');
  await expect(wulf.locator('.funding-amount')).toHaveCount(1);
  await expect(wulf).toContainText('$800K');await expect(wulf).toContainText('not cash');
  await expect(wulf).not.toContainText('$150M');
  const hut=page.locator('[data-ticker="HUT"] .funding-summary');
  await expect(hut.locator('.funding-facility-count')).toContainText('1 selected facility');
  await expect(hut.locator('.funding-amount')).toHaveCount(0);
  await expect(page.locator('[data-ticker="HUT"] .company-takeaway')).toContainText('Zero revolver borrowings');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.locator('#nav-debt').click();
  await expect(page.locator('#tab-debt')).toHaveAttribute('aria-selected','true');
  await expect(page.locator('#direction option:checked')).toContainText('Largest borrowings');
  await expect(page.locator('#rank-context')).toContainText('not company health');
});

test('every row offers a keyboard-accessible direct funding action with expandable explanations',async({page})=>{
  await page.goto('/?q=HUT');
  const action=page.locator('.cash-funding-action');
  await expect(action).toBeVisible();await action.focus();await page.keyboard.press('Enter');
  await expect(page.locator('.cash-funding')).toBeFocused();
  await expect(page.locator('.liquidity-cash-value')).toHaveText('$156.87M');
  const meaning=page.locator('.liquidity-facility [data-kind="commitment"] .liquidity-fact-context');
  await expect(meaning).not.toHaveAttribute('open');
  await meaning.locator('summary').focus();await page.keyboard.press('Enter');
  await expect(meaning).toHaveAttribute('open','');
  await expect(meaning.locator('.liquidity-fact-meaning')).toBeVisible();
  await page.keyboard.press('Escape');await expect(action).toBeFocused();
  await page.locator('#tab-cash').click();await action.focus();await page.keyboard.press('Enter');
  await expect(page.locator('.cash-funding')).toBeFocused();
});

test('cash exports retain takeaways and qualifications without ordinal ranks or invented totals',async({page})=>{
  await page.goto('/?metric=cash&group=all&q=EQIX&order=asc');
  await expect(page.locator('#tab-cash')).toHaveAttribute('aria-selected','true');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(1);
  const amount=page.locator('.funding-summary-cell .funding-amount');
  await expect(amount).toContainText('Approx. $5.5B');
  await expect(amount).toContainText('subject to conditions');
  const download=page.waitForEvent('download');await page.locator('#download-json').click();
  const payload=JSON.parse(fs.readFileSync(await (await download).path(),'utf8'));
  expect(payload.ranking_context).toMatch(/^Cash/);
  expect(payload.rows[0].ranked).toBe(false);expect(payload.rows[0].cohort_rank).toBeNull();
  expect(payload.rows[0].value).toBe('2362000000');
  expect(payload.rows[0].company_takeaway).toContain('approximate');
  expect(payload.rows[0].liquidity.company_available_credit.value).toBeNull();
  await page.reload();await expect(page.locator('#direction')).toHaveValue('asc');
  await expect(page.locator('#tab-cash')).toHaveAttribute('aria-selected','true');
});

test('funding summaries exclude capacity from a different snapshot date',async({page})=>{
  await page.route('**/data.json',async route=>{
    const response=await route.fetch(),payload=await response.json();
    const company=payload.companies.find(c=>c.ticker==='EQIX');
    for(const facility of company.liquidity.facilities)for(const fact of facility.amounts)
      if(fact.kind==='reported_available')fact.as_of='2026-06-30';
    await route.fulfill({json:payload});
  });
  await page.goto('/?metric=cash&group=all&q=EQIX');
  await expect(page.locator('.funding-summary-cell .funding-amount')).toHaveCount(0);
  await expect(page.locator('.funding-summary-cell')).toContainText('Total not established');
});

test('named rates appear beside borrowings without inventing floating totals or company averages',async({page})=>{
  await page.goto('/');
  const crwv=page.locator('[data-ticker="CRWV"] .financing-rate-summary');
  await expect(crwv.locator('.financing-rate-value').first()).toContainText('Term SOFR + 5.5 percentage points');
  await expect(crwv.locator('.financing-rate-kind').first()).toHaveText('Floating-rate formula');
  await expect(crwv.locator('.financing-rate-instrument').first()).toContainText('DDTL5.5');
  await expect(crwv.locator('.floating-rate-unknown').first()).toContainText('All-in rate: Unknown');
  await expect(crwv.locator('.financing-rate-status').first()).toContainText('Aug 7, 2026');
  await expect(crwv).not.toContainText('7.9%');
  const nbis=page.locator('[data-ticker="NBIS"] .financing-rate-summary');
  await expect(nbis.locator('.financing-rate-value').first()).toHaveText('7.06%');
  await expect(nbis.locator('.financing-rate-kind').first()).toContainText('accounting effective');
  await expect(nbis).toContainText('not the cash coupon');
  const apld=page.locator('[data-ticker="APLD"] .financing-rate-summary');
  await expect(apld.locator('.financing-rate-label')).toHaveText('Company-reported average');
  await expect(apld.locator('.financing-rate-value').first()).toHaveText('7.3%');
  await expect(apld.locator('.financing-rate-scope').first()).toContainText('Term-loan portfolio');
  await expect(page.locator('[data-ticker="BTDR"] .financing-rate-summary .financing-rate-value')).toHaveText('Unknown');
});

test('rate cards retain types and scope separately from the complete fixed-coupon ledger',async({page})=>{
  await page.goto('/?metric=coupon&group=all');
  await expect(page.locator('#company-rate-cards .company-rate-card')).toHaveCount(16);
  await expect(page.locator('#ranking-rows tr')).toHaveCount(44);
  const dlr=page.locator('.company-rate-card[data-ticker="DLR"]');
  await expect(dlr.locator('.financing-rate-value').first()).toHaveText('3.07%');
  await expect(dlr.locator('.financing-rate-label')).toHaveText('Company-reported average');
  const details=dlr.locator('.financing-rate-details');await details.locator('summary').first().focus();
  await page.keyboard.press('Enter');await expect(details).toHaveAttribute('open','');
  await expect(details).toContainText('cross-currency');
  await expect(details).toContainText('Source publication');
  const nscale=page.locator('.company-rate-card[data-ticker="NSCALE"]');
  await expect(nscale.locator('.financing-rate-value').first()).toContainText('Term SOFR + 5.00 percentage points');
  await expect(nscale.locator('.floating-rate-unknown').first()).toBeVisible();
  await page.locator('#note-type').selectOption('convertible');
  await expect(page.locator('#company-rate-cards .company-rate-card')).toHaveCount(16);
  await expect(page.locator('#download-csv')).toContainText('Fixed-note ledger');
});

test('ratio and typed rate exports preserve private profiles and machine-readable nested examples',async({page})=>{
  await page.goto('/?group=all&q=NBIS');
  const jsonPromise=page.waitForEvent('download');await page.locator('#download-json').click();
  const payload=JSON.parse(fs.readFileSync(await (await jsonPromise).path(),'utf8'));
  const row=payload.rows[0];expect(row.borrowings_assets_percent).not.toBeNull();
  expect(row.assets_value).toBe('27961500000');expect(row.assets_as_of).toBe('2026-06-30');
  expect(row.primary_financing_rate.kind).toBe('effective_instrument_rate');
  expect(row.primary_financing_rate.rate_percent).toBe('7.06');
  expect(row.financing_rate_summary.computed_average).toBeNull();
  expect(row.rate_source_ids.every(id=>payload.sources.some(s=>s.id===id))).toBe(true);
  const csvPromise=page.waitForEvent('download');await page.locator('#download-csv').click();
  const csv=fs.readFileSync(await (await csvPromise).path(),'utf8');
  expect(csv).toContain('financing_rate_examples');expect(csv).not.toContain('[object Object]');
  await page.goto('/?metric=coupon&group=all&q=NSCALE');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(0);
  await expect(page.locator('.company-rate-card')).toHaveCount(1);
  const ratesPromise=page.waitForEvent('download');await page.locator('#download-json').click();
  const profiles=JSON.parse(fs.readFileSync(await (await ratesPromise).path(),'utf8'));
  expect(profiles.company_rate_profiles).toHaveLength(1);
  expect(profiles.company_rate_profiles[0].trading_ticker).toBeNull();
  expect(profiles.company_rate_profiles[0].listing_status).toBe('private_pending_ipo');
  expect(profiles.company_rate_profiles[0].primary_financing_rate.rate_percent).toBeNull();
});
