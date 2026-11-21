const {test,expect}=require('@playwright/test');

const cases=[
 {id:'iren',label:'Promised versus revised delivery',summary:'$4B ARR target',original:'By December 31, 2026',originalDate:'2026-08-27',completion:'2026-12-31',revision:'January 2027, may extend through February 2027',revisionDate:'2026-11-05',classification:'revised'},
 {id:'hut',label:'River Bend initial data hall delivery',summary:'Q2 2027 target',original:'Q2 2027',originalDate:'2026-11-04',completion:'Q2 2027',revision:'No reviewed revision loaded',classification:'pending'},
 {id:'nbis',label:'ARR target timing',summary:'December target now expected in February',original:'December 2026',completion:'December 2026',revision:'February 2027',revisionDate:'2026-11-12',classification:'revised'},
];
for(const record of cases){
 test(`${record.id.toUpperCase()} sourced target windows survive project and profile rendering`,async({page})=>{
  for(const route of [`/buildout/?tab=projects&peers=${record.id}`,`/companies/${record.id}/?section=buildout`]){
   await page.goto(route);
   const card=page.locator('.timeline .fact-card').filter({has:page.getByRole('heading',{name:record.label,exact:true})});
   await expect(card).toHaveCount(1);
   await expect(card.locator('.milestone-summary')).toContainText(record.summary);
   await expect(card.locator('.badge')).toHaveText(record.classification);
   const fields=card.locator('dl > dd');
   await expect(fields.nth(0)).toContainText(record.original);
   if(record.originalDate)await expect(fields.nth(0)).toContainText(record.originalDate);
   await expect(fields.nth(1)).toHaveText(record.completion);
   await expect(fields.nth(2)).toContainText(record.revision);
   if(record.revisionDate)await expect(fields.nth(2)).toContainText(record.revisionDate);
   // A disclosed target or revision is not proof of completed delivery.
   await expect(fields.nth(3)).toHaveText('Not established');
   await expect(card.getByRole('button',{name:/Sources/})).toBeVisible();
   if(record.id==='nbis')await expect(card).toContainText('Original separately dated target evidence remains a gap');
  }
 });
}
