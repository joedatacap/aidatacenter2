const {defineConfig, devices} = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/browser',
  outputDir: './work/playwright-results',
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8000',
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
      ? {executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE} : {},
  },
  webServer: [{
    command: 'python3 -m http.server 8000 --bind 127.0.0.1 --directory preview',
    url: 'http://127.0.0.1:8000',
    reuseExistingServer: !process.env.CI,
  }, {
    command: 'python3 scripts/stage_preview.py && python3 -m http.server 8001 --bind 127.0.0.1 --directory work/cloudflare-preview',
    url: 'http://127.0.0.1:8001/neoclouddebt/',
    reuseExistingServer: !process.env.CI,
  }],
  projects: [
    {name: 'desktop', use: {viewport: {width:1440,height:1100}}},
    {name: 'mobile', use: {...devices['iPhone 13'], defaultBrowserType:'chromium'}},
  ],
});
