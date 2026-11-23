const {test,expect}=require('./support.cjs');
const fs=require('node:fs');
const FOCUS=['crwv','nbis','iren','apld','hut','wulf','wyfi','shaz','agpu'];
const row=(page,id)=>page.locator('#market-cap-chart [data-cap-company="'+id+'"]');
const readData=async page=>JSON.parse(await page.locator('#watch-data').textContent());
const rowIds=async(page,selector='#market-cap-chart [data-cap-company]')=>page.locator(selector).evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-cap-company')));
const dollars=value=>'$'+Number(value).toLocaleString('en-US',{maximumFractionDigits:2});

async function offlineFixture(page,change){
 const html=fs.readFileSync('work/Neocloud-Watch-V2.html','utf8');
 const match=html.match(/<script id="watch-data" type="application\/json">([\s\S]*?)<\/script>/);
 const data=JSON.parse(match[1]);change(data);
 await page.context().setOffline(true);
 await page.setContent(html.replace(match[1],JSON.stringify(data).replaceAll('<','\\u003c')));
}

async function axis(page){return Number(await page.locator('#market-cap-chart [data-cap-max]').first().getAttribute('data-cap-max'));}
async function fraction(page,id){
 const track=await row(page,id).locator('[data-cap-track]').boundingBox();
 const bar=await row(page,id).locator('[data-cap-bar]').boundingBox();
 expect(track).toBeTruthy();expect(bar).toBeTruthy();
 return {track,bar,share:bar.width/track.width};
}

async function expectGeometry(page,company,max){
 const {track,bar}=await fraction(page,company.id);
 const value=Number(company.size_observation.value_usd);
 expect(Math.abs(bar.x-track.x),'Bars begin at the common zero anchor').toBeLessThanOrEqual(1);
 expect(Math.abs(bar.width-track.width*value/max),'Fill is a fractional linear share of the displayed axis, not a minimum-width score').toBeLessThanOrEqual(1);
 expect(bar.x+bar.width).toBeLessThanOrEqual(track.x+track.width+1);
}

test('homepage capitalization chart ranks all nine reviewed providers with exact dates, sources and profile links',async({page})=>{
 await page.goto('/overview/');
 const data=await readData(page),companies=data.companies.filter(c=>FOCUS.includes(c.id));
 await expect(page.locator('#market-cap-chart')).toBeVisible();
 expect(companies).toHaveLength(9);
 const expected=[...companies].sort((a,b)=>b.size_observation.value_usd-a.size_observation.value_usd).map(c=>c.id);
 expect(await rowIds(page)).toEqual(expected);
 const max=await axis(page);
 expect(max).toBeGreaterThanOrEqual(Math.max(...companies.map(c=>Number(c.size_observation.value_usd))));
 for(const company of companies){
  const cap=company.size_observation,item=row(page,company.id);
  await expect(item).toHaveAttribute('data-cap-date',cap.as_of);
  await expect(item.locator('[data-cap-profile]')).toHaveAttribute('href',new RegExp('/companies/'+company.id+'/'));
  await expect(item.locator('[data-cap-profile]')).toContainText(company.ticker);
  await expect(item.locator('[data-cap-value]')).toContainText(dollars(cap.value_usd));
  await expect(item.locator('[data-cap-value]')).toHaveAttribute('href',cap.source_url);
  await expect(page.locator('#market-cap-chart')).toContainText(cap.as_of);
  if(company.id==='agpu')await expect(item).toContainText('Provider-reported; share basis unresolved.');
  await expectGeometry(page,company,max);
 }
 await page.locator('#primary-nav').getByRole('link',{name:'Markets',exact:true}).click();
 await expect(page.locator('#market-cap-chart')).toHaveCount(0);
});

test('cap grouping controls share selection and URL filters with both comparison tables and rescale to the group',async({page})=>{
 await page.goto('/overview/');
 const data=await readData(page),companies=data.companies.filter(c=>FOCUS.includes(c.id));
 const allMax=await axis(page);
 const small=companies.filter(c=>Number(c.size_observation.value_usd)<2e9);
 expect(small.length).toBeGreaterThan(0);
 const example=small.reduce((a,b)=>a.size_observation.value_usd>b.size_observation.value_usd?a:b);
 const initial=await fraction(page,example.id);
 await page.locator('[data-cap-group=small]').click();
 expect(new URL(page.url()).searchParams.get('size')).toBe('small');
 await expect(page.locator('[data-cap-group=small]')).toHaveAttribute('aria-pressed','true');
 const groupMax=await axis(page);expect(groupMax).toBeLessThan(allMax);
 expect((await fraction(page,example.id)).share).toBeGreaterThan(initial.share);
 const expected=small.map(c=>c.id).sort();
 expect((await rowIds(page)).sort()).toEqual(expected);
 expect(await page.locator('[data-size-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.sizeCompany).sort())).toEqual(expected);
 expect(await page.locator('#overview-comparison [data-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.company).sort())).toEqual(expected);
 await expectGeometry(page,example,groupMax);
 await page.reload();expect((await rowIds(page)).sort()).toEqual(expected);
 await page.locator('#peer-picker summary').click();
 const chosen=expected.slice(0,2);
 for(const id of chosen)await page.getByRole('checkbox',{name:'Select '+companies.find(c=>c.id===id).ticker,exact:true}).check();
 expect((await rowIds(page)).sort()).toEqual(chosen);
 expect(await page.locator('[data-size-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.sizeCompany).sort())).toEqual(chosen);
 expect(await page.locator('#overview-comparison [data-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.company).sort())).toEqual(chosen);
 await page.locator('#primary-nav').getByRole('link',{name:'Financing & Debt',exact:true}).click();
 expect(new URL(page.url()).searchParams.get('size')).toBe('small');
 expect(await page.locator('[data-company]').evaluateAll(nodes=>nodes.map(n=>n.dataset.company).sort())).toEqual(chosen);
 await page.goBack();expect((await rowIds(page)).sort()).toEqual(chosen);
 await page.locator('[data-cap-group=mid]').click();
 expect(new URL(page.url()).searchParams.get('size')).toBe('mid');
 await expect(page.locator('#market-cap-chart .cap-empty')).toBeVisible();
 await expect(page.locator('#market-cap-chart [data-cap-company]')).toHaveCount(0);
 await page.locator('[data-cap-group=all]').click();
 expect(new URL(page.url()).searchParams.get('size')).toBeNull();
 expect((await rowIds(page)).sort()).toEqual(chosen);
});

test('mixed observation dates stay on individual bars and unusable observations never fall back to historical caps',async({page})=>{
 await offlineFixture(page,data=>{
  const byId=Object.fromEntries(data.companies.map(c=>[c.id,c]));
  byId.iren.size_observation.as_of='2026-11-20';
  byId.crwv.size_observation.as_of='2026-11-23';
  byId.agpu.size_observation={...byId.agpu.size_observation,value_usd:null,value:null,status:'unavailable',discrepancy:'Fixture: latest capitalization is not established.'};
  byId.shaz.size_observation={...byId.shaz.size_observation,source_values_disagree:true};
  byId.wyfi.size_observation={...byId.wyfi.size_observation,currency:'EUR'};
  byId.hut.size_observation={...byId.hut.size_observation,source_url:'javascript:unsafe()'};
  delete byId.apld.size_observation;
  byId.wulf.size_observation={...byId.wulf.size_observation,status:'conflicting'};
 });
 await expect(row(page,'iren')).toHaveAttribute('data-cap-date','2026-11-20');
 await expect(row(page,'crwv')).toHaveAttribute('data-cap-date','2026-11-23');
 await expect(page.locator('#market-cap-chart')).toContainText(/dates|dated|observation/i);
 for(const id of ['agpu','shaz','wyfi','hut','apld','wulf']){
  await expect(row(page,id)).toHaveCount(0);
  await expect(page.locator('[data-cap-omitted="'+id+'"]')).toHaveCount(1);
  await expect(page.locator('[data-cap-omitted="'+id+'"]')).toContainText(/unavailable|missing|source|conflict|currency|historical|date|USD|not established|disagree|reviewed|eligible/i);
  await expect(page.locator('[data-size-company="'+id+'"]')).toHaveCount(1);
 }
 await expect(page.locator('#market-cap-chart [data-cap-value][href^="javascript:"]')).toHaveCount(0);
 expect(await page.locator('#tradingview-size-context [data-size-company]').count()).toBe(9);
});

test('invalid dates and nonpositive caps remain explicit omissions instead of zero-width valued bars',async({page})=>{
 await offlineFixture(page,data=>{
  const byId=Object.fromEntries(data.companies.map(c=>[c.id,c]));
  byId.agpu.size_observation={...byId.agpu.size_observation,value_usd:0,value:0};
  byId.shaz.size_observation={...byId.shaz.size_observation,as_of:'not-a-date'};
  byId.wyfi.size_observation={...byId.wyfi.size_observation,source_date:'2026-99-99'};
 });
 for(const id of ['agpu','shaz','wyfi']){
  await expect(row(page,id)).toHaveCount(0);
  await expect(page.locator('[data-cap-omitted="'+id+'"]')).toHaveCount(1);
  await expect(page.locator('[data-size-company="'+id+'"]')).toHaveCount(1);
 }
});

test('native cap geometry and company/source labels fit 320px through desktop without hiding small companies',async({page})=>{
 await page.goto('/overview/');
 const companies=(await readData(page)).companies.filter(c=>FOCUS.includes(c.id));
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:1000});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),'Page width '+width).toBe(true);
  const max=await axis(page);
  for(const company of companies){
   await expectGeometry(page,company,max);
   for(const selector of ['[data-cap-profile]','[data-cap-value]']){
    const box=await row(page,company.id).locator(selector).boundingBox();expect(box).toBeTruthy();
    expect(box.x,selector+' left at '+width).toBeGreaterThanOrEqual(-1);
    expect(box.x+box.width,selector+' right at '+width).toBeLessThanOrEqual(width+1);
   }
  }
 }
});

test('cap group controls and row links work with keyboard and touch',async({page},info)=>{
 await page.goto('/overview/');
 const control=page.locator('[data-cap-group=large]');
 if(info.project.name==='mobile')await control.tap();else{await control.focus();await expect(control).toBeFocused();await page.keyboard.press('Enter');}
 await expect(control).toHaveAttribute('aria-pressed','true');
 expect(new URL(page.url()).searchParams.get('size')).toBe('large');
 const first=page.locator('#market-cap-chart [data-cap-profile]').first();
 const target=await first.getAttribute('href');
 await first.focus();await page.keyboard.press('Enter');
 await expect(page.locator('#page-title')).toBeVisible();
 expect(new URL(page.url()).pathname).toBe(new URL(target,'http://127.0.0.1:8003').pathname);
});


test('an entirely unusable selection retains company explanations without fabricating an axis or valued bars',async({page})=>{
 await offlineFixture(page,data=>{for(const c of data.companies.filter(c=>FOCUS.includes(c.id)))c.size_observation={...c.size_observation,value_usd:null,value:null,status:'unavailable'};});
 await expect(page.locator('#market-cap-chart .cap-empty')).toBeVisible();
 await expect(page.locator('#market-cap-chart [data-cap-company]')).toHaveCount(0);
 await expect(page.locator('#market-cap-chart [data-cap-bar]')).toHaveCount(0);
 await expect(page.locator('#market-cap-chart [data-cap-max]')).toHaveCount(0);
 await expect(page.locator('#market-cap-chart [data-cap-omitted]')).toHaveCount(9);
 await expect(page.locator('#tradingview-size-context [data-size-company]')).toHaveCount(9);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
});
