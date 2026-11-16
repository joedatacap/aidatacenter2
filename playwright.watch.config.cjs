const {defineConfig, devices} = require('@playwright/test');
module.exports=defineConfig({
 testDir:'./tests/browser-watch',outputDir:'./work/playwright-watch-results',reporter:'list',
 use:{baseURL:'http://127.0.0.1:8003',launchOptions:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{}},
 webServer:{command:'python3 -m http.server 8003 --bind 127.0.0.1 --directory work/neocloud-watch-site',url:'http://127.0.0.1:8003',reuseExistingServer:false},
 projects:[{name:'desktop',use:{viewport:{width:1440,height:1100}}},{name:'mobile',use:{...devices['iPhone 13'],defaultBrowserType:'chromium'}}]
});
