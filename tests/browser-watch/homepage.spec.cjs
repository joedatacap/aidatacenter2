const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const artifact='work/Neocloud-Watch-V2.html';
function snapshot(){const html=fs.readFileSync(artifact,'utf8'),match=html.match(/<script id="watch-data" type="application\/json">([\s\S]*?)<\/script>/);return {html,encoded:match[1],data:JSON.parse(match[1])};}
async function offlineFixture(page,change){const {html,encoded,data}=snapshot();change(data);await page.context().setOffline(true);await page.setContent(html.replace(encoded,JSON.stringify(data).replaceAll('<','\\u003c')));}
const revenueCard=(page,id)=>page.locator(`.overview-revenue-card[data-chart-company="${id}"]`);
const balancePair=(page,id)=>page.locator(`.balance-pair[data-balance-company="${id}"]`);
const chartIds=async locator=>locator.evaluateAll(nodes=>nodes.map(n=>n.dataset.chartCompany).sort());
async function downloadJSON(page){const event=page.waitForEvent('download');await page.locator('#export-json').click();return JSON.parse(fs.readFileSync(await (await event).path(),'utf8'));}

test('overview charts and compact table share URL peers, search and navigation state',async({page})=>{
 await page.goto('/overview/?peers=agpu,shaz');
 await expect(page.locator('.overview-revenue-card')).toHaveCount(2);
 await expect(page.locator('.balance-pair')).toHaveCount(2);
 await expect(page.locator('[data-company]')).toHaveCount(2);
 expect(await chartIds(page.locator('.overview-revenue-card'))).toEqual(['agpu','shaz']);
 await page.locator('#q').fill('AGPU');
 await expect(page.locator('.overview-revenue-card')).toHaveCount(1);
 await expect(balancePair(page,'agpu')).toBeVisible();
 await expect(page.locator('[data-company]')).toHaveCount(1);
 expect(new URL(page.url()).searchParams.get('peers')).toBe('agpu,shaz');
 await page.reload();await expect(revenueCard(page,'agpu')).toBeVisible();
 await page.locator('#primary-nav').getByRole('link',{name:'Earnings',exact:true}).click();
 await expect(page.locator('[data-company]')).toHaveCount(1);
 await page.goBack();await expect(revenueCard(page,'agpu')).toBeVisible();
 await expect(page.locator('#q')).toHaveValue('AGPU');
});

test('latest change cards retain actual publication dates, periods, sources and company links',async({page})=>{
 await page.goto('/overview/');const {data}=snapshot();
 const cards=page.locator('#what-changed .change-card');await expect(cards).toHaveCount(3);
 for(const card of await cards.all()){
  const id=await card.getAttribute('data-change-company'),c=data.companies.find(c=>c.id===id);
  const quarter=[...c.quarters].sort((a,b)=>b.release_date.localeCompare(a.release_date))[0];
  await expect(card.locator('time[datetime="'+quarter.release_date+'"]')).toBeVisible();
  await expect(card).toContainText(quarter.period_end);
  await expect(card.locator('.change-number')).not.toBeEmpty();
  await expect(card.locator('a[data-app]').first()).toHaveAttribute('href',new RegExp('/companies/'+id+'/'));
  await card.getByRole('button',{name:/Sources \(/}).first().click();
  await expect(page.locator('#evidence-dialog')).toBeVisible();
  await expect(page.locator('#evidence-dialog a').first()).toHaveAttribute('href',/^https:\/\//);
  await page.locator('#close-evidence').click();
 }
});

test('Axe quarterly chart preserves exact values, short history and the continuing-operations scope break',async({page})=>{
 await page.goto('/overview/?peers=agpu');const card=revenueCard(page,'agpu');
 const {data}=snapshot(),c=data.companies.find(c=>c.id==='agpu');
 const quarter=c.quarters.find(q=>q.period_end==='2026-09-30');
 expect(quarter.metrics.revenue.value).toBe(7243043);
 await expect(card).toContainText(/independent|own scale|per.company/i);
 await expect(card.locator('.revenue-observation')).toHaveCount(c.quarters.length);
 const point=card.locator('.revenue-observation[data-period-end="2026-09-30"]');
 await expect(point).toHaveAttribute('data-value','7243043');
 await point.locator('summary').focus();await page.keyboard.press('Enter');
 await expect(point).toHaveAttribute('open','');await expect(point).toContainText('$7,243,043');
 await expect(card).toContainText(/scope|continuing operations/i);
 // Q1/Q2 consolidated points may connect; Q3 continuing operations must stand apart.
 const segments=await card.locator('[data-line-segment]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-periods')||n.getAttribute('points')||''));
 expect(segments.length).toBeLessThanOrEqual(1);
 for(const segment of segments)expect(segment).not.toMatch(/2026-06-30.*2026-09-30/);
 await expect(card.getByRole('link',{name:/earnings/i}).first()).toHaveAttribute('href',/companies\/agpu\/.*section=earnings/);
});

test('a missing revenue observation stays a labelled gap rather than a zero or connecting line',async({page})=>{
 await offlineFixture(page,data=>{const c=data.companies.find(c=>c.id==='agpu'),q=c.quarters.find(q=>q.period_end==='2026-06-30');q.metrics.revenue={...q.metrics.revenue,value:null,status:'not_researched',reason:'Fixture: quarterly revenue not established'};});
 const card=revenueCard(page,'agpu');
 const point=card.locator('.revenue-observation[data-period-end="2026-06-30"]');
 await expect(point).toHaveCount(1);await expect(point).not.toHaveAttribute('data-value','0');
 await point.locator('summary').click();await expect(point).toContainText(/not established|not researched|unavailable|missing/i);
 await expect(card.locator('[data-line-segment]')).toHaveCount(0);
 expect(await card.locator('[data-value="0"]').count()).toBe(0);
});

test('a single reviewed quarter produces one observation without invented history',async({page})=>{
 await offlineFixture(page,data=>{const c=data.companies.find(c=>c.id==='agpu');c.quarters=c.quarters.filter(q=>q.period_end==='2026-09-30');});
 const card=revenueCard(page,'agpu');await expect(card.locator('.revenue-observation')).toHaveCount(1);
 await expect(card.locator('[data-line-segment]')).toHaveCount(0);
 await expect(card).toContainText('2026-09-30');
});

test('cash and financing bars preserve exact September Axe balances and keep prepayments distinct',async({page})=>{
 await page.goto('/overview/?peers=agpu');const pair=balancePair(page,'agpu');
 await expect(pair).toContainText('$147,710,376');await expect(pair).toContainText('$36,889,299');
 await expect(pair).toContainText('2026-09-30');
 await expect(pair).toContainText(/deferred|consideration/i);
 await expect(pair).toContainText(/independent|per.company|own scale/i);
 await expect(pair.locator('[data-balance-kind=cash]')).toHaveAttribute('data-value','147710376');
 await expect(pair.locator('[data-balance-kind=debt]')).toHaveAttribute('data-value','36889299');
 await expect(pair.locator('[data-balance-kind=debt]')).not.toHaveAttribute('data-value','569338973');
 await expect(pair).toContainText(/prepayment|customer/i);
 await expect(pair.locator('[data-balance-kind]')).toHaveCount(2);
 await expect(pair.locator('[data-balance-kind=net]')).toHaveCount(0);
});

test('missing balance input remains unavailable and does not become a zero-valued cash bar',async({page})=>{
 await offlineFixture(page,data=>{const c=data.companies.find(c=>c.id==='agpu');c.financing.metrics.cash={value:null,status:'not_researched',reason:'Fixture: cash definition not established'};});
 const cash=balancePair(page,'agpu').locator('[data-balance-kind=cash]');
 await expect(cash).toContainText(/not established|not researched|unavailable|missing/i);
 await expect(cash).not.toHaveAttribute('data-value','0');
});

test('buildout tracker retains observed acceptance boundaries and links to original evidence',async({page})=>{
 await page.goto('/overview/?peers=agpu');const tracker=page.locator('#buildout-tracker');
 await expect(tracker).toContainText(/acceptance|Georgia|Columbus/i);
 await expect(tracker).toContainText(/underway|not accepted|pending|not established|insufficient/i);
 await expect(tracker.locator('[data-milestone-company=agpu]')).toHaveCount(1);
 await expect(tracker.getByRole('link',{name:/buildout/i}).first()).toHaveAttribute('href',/buildout/);
 await tracker.getByRole('button',{name:/Sources \(/}).first().click();
 await expect(page.locator('#evidence-dialog')).toContainText(/2026/);
 await page.locator('#close-evidence').click();
});

test('reported November earnings remain historical instead of upcoming events',async({page})=>{
 await page.goto('/earnings/?peers=agpu,shaz&tab=upcoming');
 await expect(page.locator('#page-content .cards .fact-card')).toHaveCount(0);
 await expect(page.locator('#page-content')).toContainText(/No future report date|No upcoming|No confirmed upcoming/i);
});

test('overview exports match selected chart companies and protect the audited Axe Q3 facts',async({page})=>{
 await page.goto('/overview/?peers=agpu,shaz');const exported=await downloadJSON(page);
 expect(exported.companies.map(c=>c.id).sort()).toEqual(await chartIds(page.locator('.overview-revenue-card')));
 const c=exported.companies.find(c=>c.id==='agpu'),q=c.quarters.find(q=>q.period_end==='2026-09-30');
 expect(q.metrics.revenue.value).toBe(7243043);expect(q.metrics.adjusted_ebitda.value).toBe(-2275000);
 const net=q.metrics.net_income||q.metrics.net_loss;expect(net.value).toBe(11503607);
 expect(c.financing.metrics.cash.value).toBe(147710376);expect(c.financing.metrics.debt.value).toBe(36889299);
 expect(q.metrics.operating_cash_flow.value).toBeNull();
 expect(q.metrics.cash_capex.value).toBeNull();
 expect(JSON.stringify(c)).toContain('569338973');expect(JSON.stringify(c)).toMatch(/asset|gain/i);
 for(const company of exported.companies){const point=revenueCard(page,company.id).locator('.revenue-observation[data-period-end="'+company.quarters[0].period_end+'"]');await expect(point).toHaveAttribute('data-value',String(company.quarters[0].metrics.revenue.value));}
 const event=page.waitForEvent('download');await page.locator('#export-csv').click();const csv=fs.readFileSync(await (await event).path(),'utf8');
 for(const exact of ['7243043','147710376','36889299','569338973'])expect(csv).toContain(exact);
 expect(csv).not.toContain('aethir_bridge');
});

test('overview hierarchy is compact, chart details work by keyboard, and layouts fit supported widths',async({page})=>{
 await page.goto('/overview/?peers=agpu,iren,apld');
 const positions=await page.evaluate(()=>['#what-changed','#overview-charts','#buildout-tracker','#overview-comparison','#shared-controls','#overview-comparison .table-wrap'].map(id=>({id,top:document.querySelector(id)?.getBoundingClientRect().top})));
 for(let i=1;i<positions.length;i++)expect(positions[i].top,positions[i].id).toBeGreaterThanOrEqual(positions[i-1].top);
 await expect(page.locator('#overview-comparison thead')).not.toContainText('Next event');
 const detail=revenueCard(page,'agpu').locator('.revenue-observation summary').first();
 await detail.focus();await expect(detail).toBeFocused();await page.keyboard.press('Enter');
 await expect(detail.locator('..')).toHaveAttribute('open','');
 for(const width of [320,390,768,1100,1440]){await page.setViewportSize({width,height:1000});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),String(width)).toBe(true);}
});

test('compact chart group selection updates all visuals and keeps the shared research URL',async({page})=>{
 await page.goto('/overview/');
 const smaller=page.locator('#overview-selection [data-focus=smaller]');
 await smaller.click();await expect(smaller).toHaveAttribute('aria-pressed','true');
 await expect(page.locator('.overview-revenue-card')).toHaveCount(3);
 await expect(page.locator('.balance-pair')).toHaveCount(3);
 await expect(page.locator('[data-company]')).toHaveCount(3);
 expect(await chartIds(page.locator('.overview-revenue-card'))).toEqual(['agpu','shaz','wyfi']);
 expect(new URL(page.url()).searchParams.get('focus')).toBe('smaller');
 await page.reload();await expect(page.locator('.overview-revenue-card')).toHaveCount(3);
 await expect(page.locator('#focus')).toHaveValue('smaller');
});

test('fiscal dates and material accounting warnings remain visible before expanding notes',async({page})=>{
 await page.goto('/overview/?peers=agpu,iren,apld');
 await expect(revenueCard(page,'iren')).toContainText('2026-09-30');
 await expect(revenueCard(page,'iren')).toContainText(/June fiscal year.end/i);
 await expect(revenueCard(page,'apld')).toContainText('2026-08-31');
 await expect(revenueCard(page,'apld')).toContainText(/May fiscal year.end/i);
 const axeRow=page.locator('[data-company=agpu]');
 await expect(axeRow).toContainText(/scope|continuing/i);
 const explanation=axeRow.locator('.row-explainer').first();await expect(explanation).not.toHaveAttribute('open');
 await explanation.locator('summary').focus();await page.keyboard.press('Enter');
 await expect(explanation).toHaveAttribute('open','');
 await expect(explanation).toContainText(/2026-09-30|continuing operations/i);
});

test('chart histories retain up to four actual quarterly dates and source values for every focus company',async({page})=>{
 await page.goto('/overview/');const {data}=snapshot();
 for(const card of await page.locator('.overview-revenue-card').all()){
  const id=await card.getAttribute('data-chart-company'),c=data.companies.find(c=>c.id===id);
  const quarters=[...c.quarters].filter(q=>q.months===3||q.period_type==='quarter').sort((a,b)=>a.period_end.localeCompare(b.period_end)).slice(-4);
  await expect(card.locator('.revenue-observation')).toHaveCount(quarters.length);
  for(const q of quarters){const p=card.locator('.revenue-observation[data-period-end="'+q.period_end+'"]');await expect(p).toHaveCount(1);if(q.metrics.revenue.value!==null)await expect(p).toHaveAttribute('data-value',String(q.metrics.revenue.value));}
 }
});

test('missing middle quarter breaks a same-scope revenue series without bridging across the gap',async({page})=>{
 await offlineFixture(page,data=>{const c=data.companies.find(c=>c.id==='crwv');for(const q of c.quarters){q.scope='Fixture consolidated issuer';q.metrics.revenue.scope=q.scope;q.metrics.revenue.accounting_basis='GAAP';}const q=c.quarters.find(q=>q.period_end==='2026-06-30');q.metrics.revenue={...q.metrics.revenue,value:null,status:'not_researched',reason:'Fixture missing quarter'};});
 const card=revenueCard(page,'crwv');await expect(card.locator('.revenue-observation')).toHaveCount(4);
 const segments=await card.locator('[data-line-segment]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-periods').split(',')));
 expect(segments.length).toBe(1);expect(segments[0]).toHaveLength(2);
 expect(segments[0]).not.toContain('2026-09-30');expect(segments[0]).not.toContain('2026-06-30');
});

test('standalone audit opens without leaving the selected peer group',async({page})=>{
 await page.context().setOffline(true);
 await page.setContent(fs.readFileSync('work/Neocloud-Watch-V2.html','utf8'));
 await page.locator('[data-focus=smaller]').click();
 await page.locator('[data-audit]').click();
 const dialog=page.getByRole('dialog',{name:'Data audit & coverage'});
 await expect(dialog).toContainText('569,338,973');
 await page.keyboard.press('Escape');
 await expect(dialog).toBeHidden();
 await expect(page.locator('[data-company]')).toHaveCount(3);
});
