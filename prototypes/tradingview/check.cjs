const {chromium}=require('playwright');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const page=await browser.newPage();
  await page.goto('https://www.tradingview.com/widget-docs/widgets/watchlists/market-data/', {waitUntil:'domcontentloaded',timeout:45000});
  await page.waitForTimeout(5000);
  // Read only the publisher's embed configurator. Never inspect widget quotes.
  console.log('constructor title',await page.title());
  console.log('configuration',await page.locator('tv-market-data').evaluateAll(els=>els.map(el=>el.outerHTML.slice(0,6500))));
  console.log('controls',await page.locator('main button,main label,main select,main textarea,main [role=tab]').evaluateAll(els=>els.slice(-100).map(e=>[e.tagName,(e.getAttribute('aria-label')||e.textContent||'').trim().slice(0,120)])));
  console.log('constructor embed',await page.locator('pre,textarea').evaluateAll(els=>els.map(el=>(el.value||el.innerText).slice(0,6000)).filter(text=>text.includes('tv-market-data')).slice(0,2)));
  console.log('frames',page.frames().map(f=>new URL(f.url()).hostname));
  await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1});
