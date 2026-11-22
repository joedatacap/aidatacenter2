// Capture the intact, branded widget. No quotes, widget payloads or series are read.
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');

async function main() {
  const file = path.join(__dirname, 'index.html');
  const html = await fs.readFile(file);
  const output = path.resolve('work/tradingview-proof');
  await fs.mkdir(output, {recursive:true});
  const server = http.createServer((_req, res) => {
    res.writeHead(200, {'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});
    res.end(html);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const hosted = 'http://127.0.0.1:' + server.address().port;
  try {
    await Promise.all([
      ['desktop', hosted, 1320, 960],
      ['mobile', hosted, 390, 844],
      ['download', pathToFileURL(file).href, 1280, 960]
    ].map(async ([label, url, width, height]) => {
      const page = await browser.newPage({viewport:{width,height},hasTouch:label==='mobile'});
      try {
        await page.goto(url, {waitUntil:'domcontentloaded', timeout:45000});
        const loaded = await page.waitForFunction(() => customElements.get('tv-market-data') !== undefined, null, {timeout:20000}).then(()=>true,()=>false);
        // Inspect screenshots visually for each symbol after the embed settles.
        await page.waitForTimeout(13000);
        await page.screenshot({path:path.join(output,label+'.png'),fullPage:true});
        const overflow = await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth);
        console.log(label, {componentRegistered:loaded,pageOverflow:overflow});
      } finally { await page.close(); }
    }));
    await fs.copyFile(file, path.join(output, 'Neocloud-TradingView-preview.html'));
  } finally { await browser.close(); server.close(); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
