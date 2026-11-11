const {test, expect} = require('@playwright/test');

test('scenario controls, provenance, sharing and export work without backend requests', async ({page}, testInfo) => {
  const errors=[], requests=[];
  page.on('pageerror', error=>errors.push(error.message));
  page.on('request', request=>requests.push({url:request.url(),method:request.method()}));
  await page.goto('/');
  await expect(page.locator('.company-card')).toHaveCount(2);
  await expect(page.locator('#takeaway')).toContainText('CRWV needs $400M more');
  await expect(page.locator('.gap-number').first()).toContainText('$654M');
  await page.locator('#scenario').selectOption('Base');
  await expect(page.locator('.gap-number').first()).toContainText('$200M');
  await expect(page.locator('#takeaway')).toContainText('same $200M funding gap');
  await page.locator('[data-horizon="18"]').click();
  await expect(page.locator('.gap-number').first()).toContainText('$450M');
  await page.locator('#shock').selectOption('300');
  await expect(page.locator('.mini-metrics').first()).toContainText('$15M');
  await page.reload();
  await expect(page.locator('#shock')).toHaveValue('300');
  await expect(page.locator('[data-horizon="18"]')).toHaveAttribute('aria-pressed','true');
  await page.locator('[data-pair="IREN,BTDR"]').click();
  await expect(page.locator('.company-head h3').first()).toHaveText('IREN');
  await page.locator('#swap').click();
  await expect(page.locator('.company-head h3').first()).toHaveText('Bitdeer Technologies Group');
  await page.locator('#left').selectOption('NBIS');
  await expect(page.locator('.company-head h3').first()).toHaveText('Nebius Group');
  await page.locator('.card-detail summary').first().click();
  await expect(page.locator('.card-detail').first()).toContainText('Unavailable — no quote feed');
  await page.getByText('Open the source ledger & supporting passages').click();
  await expect(page.locator('.evidence-card').first()).toBeVisible();
  await expect(page.locator('#reference-cards')).toContainText('$3.25B');
  await expect(page.locator('#reference-cards')).toContainText('6.192%');
  await expect(page.locator('#reference-cards')).toContainText('drawn balance unknown');
  const downloadPromise=page.waitForEvent('download');
  await page.locator('#download').click();
  const download=await downloadPromise;
  const payload=JSON.parse(require('fs').readFileSync(await download.path(),'utf8'));
  expect(payload.disclosure).toContain('Synthetic');
  expect(payload.selection.left).toBe('NBIS');
  await page.locator('#reset').click();
  await expect(page.locator('#scenario')).toHaveValue('Tight credit');
  await expect(page.locator('.gap-number').first()).toContainText('$654M');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  expect(requests.every(r=>r.method==='GET'&&!r.url.includes('/api/'))).toBe(true);
  await page.screenshot({path:`work/preview-${testInfo.project.name}.png`, fullPage:true});
});

test('invalid shared parameters fall back safely; failed data fetch shows recovery message', async ({page}) => {
  await page.goto('/?left=UNKNOWN&right=INVALID&scenario=unsupported&shock=999&horizon=99');
  await expect(page.locator('#left')).toHaveValue('CRWV');
  await expect(page.locator('#right')).toHaveValue('HUT');
  await expect(page.locator('#scenario')).toHaveValue('Tight credit');
  await page.route('**/data.json',route=>route.fulfill({status:503,body:'unavailable'}));
  await page.reload();
  await expect(page.locator('#error')).toBeVisible();
  await expect(page.locator('#error')).toContainText('reload');
});

test('inherited object keys in shared URLs fall back independently to valid tickers', async ({page}) => {
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  for(const key of ['__proto__','constructor','toString']) {
    for(const side of ['left','right']) {
      const params=new URLSearchParams({left:'IREN',right:'NBIS',[side]:key});
      await page.goto('/?'+params);
      await expect(page.locator('.company-card')).toHaveCount(2);
      await expect(page.locator('#left')).toHaveValue(side==='left'?'CRWV':'IREN');
      await expect(page.locator('#right')).toHaveValue(side==='right'?'HUT':'NBIS');
      await expect(page.locator('#error')).toBeHidden();
    }
  }
  expect(errors).toEqual([]);
});

test('small eyebrow labels meet 4.5:1 contrast on their actual backgrounds', async ({page}) => {
  await page.goto('/');
  await expect(page.locator('.company-card')).toHaveCount(2);
  const contrasts=await page.locator('.eyebrow').evaluateAll(labels=>{
    const channels=css=>css.match(/[\d.]+/g).map(Number);
    const luminance=rgb=>rgb.slice(0,3).map(v=>{
      const c=v/255;return c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4);
    }).reduce((sum,c,i)=>sum+c*[.2126,.7152,.0722][i],0);
    return labels.map(label=>{
      let background,element=label;
      while(element){
        const value=channels(getComputedStyle(element).backgroundColor);
        if(value.length===3||value[3]===1){background=value;break;}
        element=element.parentElement;
      }
      const fg=luminance(channels(getComputedStyle(label).color));
      const bg=luminance(background||[255,255,255]);
      return {text:label.textContent,ratio:(Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05)};
    });
  });
  for(const label of contrasts) expect(label.ratio,label.text).toBeGreaterThanOrEqual(4.5);
});

test('keyboard focus outlines meet 3:1 contrast on light and dark surroundings', async ({page}) => {
  await page.goto('/');
  await expect(page.locator('.company-card')).toHaveCount(2);
  await page.keyboard.press('Tab');
  for(const selector of ['header .brand','header nav a','#reset','#left','#swap','#right','#scenario','#shock',
    '[data-pair]','[data-horizon]','.card-detail summary','.assumptions summary','.reference-card a','#download','footer a']) {
    const target=page.locator(selector).first();
    await target.focus();
    const focus=await target.evaluate(element=>{
      const channels=css=>css.match(/[\d.]+/g).map(Number);
      const luminance=rgb=>rgb.slice(0,3).map(v=>{
        const c=v/255;return c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4);
      }).reduce((sum,c,i)=>sum+c*[.2126,.7152,.0722][i],0);
      let ancestor=element.parentElement,background;
      while(ancestor){
        const value=channels(getComputedStyle(ancestor).backgroundColor);
        if(value.length===3||value[3]===1){background=value;break;}
        ancestor=ancestor.parentElement;
      }
      const style=getComputedStyle(element),fg=luminance(channels(style.outlineColor)),bg=luminance(background||[255,255,255]);
      return {visible:element.matches(':focus-visible'),width:parseFloat(style.outlineWidth),
        ratio:(Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05)};
    });
    expect(focus.visible,selector).toBe(true);
    expect(focus.width,selector).toBeGreaterThanOrEqual(3);
    expect(focus.ratio,selector).toBeGreaterThanOrEqual(3);
  }
});

test('subdirectory assets stay inside neoclouddebt and root is not an app fallback', async ({page, request}) => {
  const paths=[];
  page.on('request',r=>paths.push(new URL(r.url()).pathname));
  await page.goto('http://127.0.0.1:8001/neoclouddebt/');
  await expect(page.locator('.company-card')).toHaveCount(2);
  expect(paths.every(p=>p.startsWith('/neoclouddebt/'))).toBe(true);
  const root=await request.get('http://127.0.0.1:8001/');
  expect(await root.text()).not.toContain('SCENARIO WORKBENCH');
});

test('standalone HTML works offline when loaded directly as browser content', async ({page, context}) => {
  const requests=[], errors=[];
  page.on('request',r=>requests.push(r.url()));
  page.on('pageerror',e=>errors.push(e.message));
  await context.setOffline(true);
  const {resolve}=require('path');
  const html=require('fs').readFileSync(resolve('work/NeoCloud-Interactive-Preview.html'),'utf8');
  await page.setContent(html);
  await expect(page.locator('.company-card')).toHaveCount(2);
  await expect(page.locator('.gap-number').first()).toContainText('$654M');
  await page.locator('#scenario').selectOption('Base');
  await expect(page.locator('.gap-number').first()).toContainText('$200M');
  await page.locator('[data-horizon="18"]').click();
  await expect(page.locator('.gap-number').first()).toContainText('$450M');
  await page.locator('[data-pair="IREN,BTDR"]').click();
  await expect(page.locator('.company-head h3').first()).toHaveText('IREN');
  await expect(page.locator('#reference-cards')).toContainText('$3.25B');
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});
