const {test:base,expect}=require('@playwright/test');

// Production regression tests inspect our application only. Third-party widget
// contents and quote values are neither requested nor scraped. A separate live
// browser check verifies the official widget delivery outside this local suite.
const test=base.extend({
 page:async({page},use)=>{
  await page.route('**/*',route=>{
   const url=new URL(route.request().url());
   if(/^https?:$/.test(url.protocol)&&!['127.0.0.1','localhost'].includes(url.hostname))return route.abort('blockedbyclient');
   return route.continue();
  });
  await use(page);
 },
});
module.exports={test,expect};
