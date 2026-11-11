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
  await expect(page.locator('[data-ticker="NBIS"]')).toContainText('Jun 30, 2026');
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
  await expect(page.locator('#tab-coupon')).toBeFocused();
  for(const selector of ['header .brand','header nav a','#reset','#tab-coupon','[data-group="all"]','#search','#direction','#share','.company-button','#download-json']){
    const target=page.locator(selector).first();await target.focus();
    expect(await target.evaluate(e=>e.matches(':focus-visible')),selector).toBe(true);
    expect(await target.evaluate(e=>parseFloat(getComputedStyle(e).outlineWidth)),selector).toBeGreaterThanOrEqual(3);
  }
});

test('small directory text and keyboard outlines retain contrast on actual backgrounds',async({page})=>{
  await page.goto('/');
  await expect(page.locator('#ranking-rows tr')).toHaveCount(12);
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

test('search preserves peer-group ranks and bar scale instead of making each lookup number one',async({page})=>{
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
  await expect(page.locator('[data-ticker="NSCALE"]')).toContainText('Private');
  await expect(page.locator('[data-ticker="NSCALE"]')).toContainText('customer financing');
  await page.locator('.company-button').click();
  await expect(page.locator('#detail-content')).toContainText('proposed NSCL is not a verified listed ticker');
  await expect(page.locator('#detail-content')).toContainText('6.4926');
  await expect(page.locator('#detail-content')).toContainText('must not be presented as bond coupons');
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
