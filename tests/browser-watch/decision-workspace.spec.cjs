const {test,expect}=require('./support.cjs');

test('sourced decision briefs work across all three companies without overflowing',async({page})=>{
 for(const id of ['crwv','apld','agpu']){
  await page.goto('/terminal/#/user-research/'+id);
  await expect(page.locator('#page-title')).toContainText(id.toUpperCase()+' decision brief');
  await expect(page.locator('[data-case]')).toHaveCount(3);
  await expect(page.locator('.decision-checkpoints article').first()).toBeVisible();
  for(const width of [320,390,1440]){await page.setViewportSize({width,height:1000});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);}
 }
 await page.screenshot({path:test.info().outputPath('decision-brief.png'),fullPage:true});
});

test('scenario lab explains valuation, reverse hurdle and diluted equity without fabricating missing inputs',async({page})=>{
 await page.goto('/terminal/#/user-scenario/crwv');
 const f=page.locator('[data-scenario]');
 await expect(page.locator('#scenario-result')).toBeEmpty();
 await f.locator('[name=horizon]').fill('2027-12-31');
 await f.locator('[name=priceDate]').fill('2026-11-25');
 await f.locator('[name=priceSource]').fill('Synthetic test reference, not a quote');
 await f.locator('[name=revenuePeriod]').fill('Synthetic calendar 2027 recognized revenue, not exit ARR');
 await f.locator('[name=cashBasis]').fill('Synthetic consolidated cash after funding obligations; debt and claims counted once');
 await f.locator('[name=price]').fill('20');
 for(const k of ['bear','base','bull'])for(const [n,v] of Object.entries({revenue:100,margin:20,multiple:10,debt:50,cash:10,claims:5,shares:10}))await f.locator(`[name=${k}_${n}]`).fill(String(v));
 await f.locator('[name=assumptionsConfirmed]').check();
 await f.getByRole('button',{name:'Calculate scenarios',exact:true}).click();
 await expect(page.locator('#scenario-result')).toContainText('$15.50');
 await expect(page.locator('#scenario-result')).toContainText('$122.5M');
 await f.locator('[name=base_shares]').fill('20');
 await expect(page.locator('#scenario-result')).toContainText('Inputs changed');
 await expect(page.locator('#scenario-result')).not.toContainText('$15.50');
 await f.getByRole('button',{name:'Calculate scenarios',exact:true}).click();
 await expect(page.locator('#scenario-result')).toContainText('$7.75');
 // Clearing a required basis must remove the old output; a blocked submit
 // cannot leave a seemingly current valuation available for a decision.
 await f.locator('[name=cashBasis]').fill('');
 await f.getByRole('button',{name:'Calculate scenarios',exact:true}).click();
 await expect(page.locator('#scenario-result')).not.toContainText('$7.75');
 expect(await f.locator('[name=cashBasis]').evaluate(el=>el.validity.valueMissing)).toBe(true);
 await f.locator('[name=cashBasis]').fill('Synthetic reconciled cash, no double counting');
 await f.getByRole('button',{name:'Save assumptions',exact:true}).click();
 await page.reload();
 await expect(f.locator('[name=base_revenue]')).toHaveValue('100');
 await expect(f.locator('[name=revenuePeriod]')).toHaveValue('Synthetic calendar 2027 recognized revenue, not exit ARR');
 await expect(page.locator('#scenario-result')).toBeEmpty();
});

test('new and existing position decisions retain timestamped assumptions and support outcome review',async({page})=>{
 await page.goto('/terminal/#/user-journal/agpu');
 await page.locator('[data-advanced-plan] > summary').click();
 const f=page.locator('[data-plan]');
 await f.locator('[name=context]').selectOption('existing');
 await f.locator('[name=decision]').selectOption('Watch');
 await f.locator('[name=reviewDate]').fill('2026-12-17');
 await f.locator('[name=priceDate]').fill('2026-11-25');
 await f.locator('[name=priceSource]').fill('Synthetic testing');
 for(const [n,v] of Object.entries({entry:20,stop:18,target:26,capital:10000,riskBudgetPct:1,maxPositionPct:20,currentShares:20,currentCost:15}))await f.locator(`[name=${n}]`).fill(String(v));
 for(const n of ['thesis','invalidation','catalyst','counterargument'])await f.locator(`[name=${n}]`).fill(n==='thesis'?'<img src=x onerror=alert(1)> Test thesis':'Synthetic '+n);
 await f.getByRole('button',{name:'Calculate position risk',exact:true}).click();
 await expect(page.locator('#position-result')).toContainText('50 shares');
 await expect(page.locator('#position-result')).toContainText('30 shares');
 await f.locator('[name=stop]').fill('19');
 await expect(page.locator('#position-result')).toContainText('Inputs changed');
 await expect(page.locator('#position-result')).not.toContainText('30 shares');
 await f.getByRole('button',{name:'Calculate position risk',exact:true}).click();
 await expect(page.locator('#position-result')).toContainText('80 shares');
 await f.getByRole('button',{name:'Save dated decision',exact:true}).click();
 await expect(page.locator('[data-journal-entry]')).toHaveCount(1);
 await expect(page.locator('[data-journal-entry] img')).toHaveCount(0);
 await page.reload();await expect(f.locator('[name=thesis]')).toHaveValue('<img src=x onerror=alert(1)> Test thesis');
 await page.locator('[data-journal-entry] summary').click();
 await page.locator('[name=outcome]').fill('Acceptance not yet verified; keep watch.');
 await page.getByRole('button',{name:'Save review',exact:true}).click();
 await page.reload();await page.locator('[data-journal-entry] summary').click();
 await expect(page.locator('[name=outcome]')).toHaveValue('Acceptance not yet verified; keep watch.');
 const download=page.waitForEvent('download');await page.locator('[data-decision-export]').click();expect((await download).suggestedFilename()).toBe('neocloud-decision-workspace.json');
});

test('APLD and AGPU residual models discount common cash after project claims without inventing EBITDA values',async({page})=>{
 for(const id of ['apld','agpu']){
  await page.goto('/terminal/#/user-scenario/'+id);
  const f=page.locator('[data-residual]');
  await expect(f).toBeVisible();
  await expect(page.locator('[data-scenario]')).toHaveCount(0);
  await expect(page.locator('#scenario-result')).toBeEmpty();
  await f.locator('[name=horizon]').fill('2026-11-25');
  await f.locator('[name=priceDate]').fill('2026-11-25');
  await f.locator('[name=priceSource]').fill('Synthetic test reference, not a quote');
  await f.locator('[name=price]').fill('8');
  await f.locator('[name=flowBasis]').fill('Synthetic year-end parent common distributions after project debt, minority waterfalls and corporate costs; terminal equity already net of debt');
  for(const k of ['bear','base','bull']){
   await f.locator(`[name=${k}_cashflows]`).fill('10,10');
   for(const [n,v] of Object.entries({discountRatePct:10,terminalEquityValue:100,corporateClaims:0,shares:10}))await f.locator(`[name=${k}_${n}]`).fill(String(v));
  }
  await f.locator('[name=assumptionsConfirmed]').check();
  await f.locator('button[type=submit]').click();
  await expect(page.locator('#scenario-result')).toContainText('$10.00');
  await expect(page.locator('#scenario-result')).toContainText('25');
  await f.locator('[name=base_cashflows]').fill('-10,10');
  await expect(page.locator('#scenario-result')).toContainText('Inputs changed');
  await expect(page.locator('#scenario-result')).not.toContainText('$10.00');
  await f.locator('button[type=submit]').click();
  await expect(page.locator('#scenario-result')).toContainText('$8.18');
  await f.locator('[name=bear_cashflows]').fill('10,,10');
  await f.locator('button[type=submit]').click();
  await expect(page.locator('#scenario-result')).not.toContainText('$8.18');
  await expect(page.locator('#scenario-result .decision-error')).toBeVisible();
 }
});

const backupEntry=(id='synthetic-1')=>({id,company:'agpu',savedAt:'2026-11-25T00:00:00.000Z',researchDate:'2026-11-24T00:00:00.000Z',values:{decision:'Watch',thesis:'Synthetic imported thesis',invalidation:'Synthetic invalidation',catalyst:'Synthetic next evidence'}});
const backup=(journal=[])=>({version:1,scenarios:{},plans:{},journal});
async function importBackup(page,value){
 await page.locator('#decision-import').setInputFiles({name:'synthetic-workspace.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
}

test('decision backups merge idempotently and preserve existing saved assumptions',async({page})=>{
 await page.goto('/terminal/#/user-journal/agpu');
 const existing=backup([backupEntry('existing')]);
 existing.plans.agpu={thesis:'Keep existing plan'};
 await page.evaluate(x=>localStorage.setItem('neocloud-decisions-v1',JSON.stringify(x)),existing);
 await page.reload();
 const incoming=backup([backupEntry('imported')]);incoming.plans.agpu={thesis:'Do not overwrite existing'};
 await importBackup(page,incoming);
 await expect(page.locator('#decision-status')).toContainText('Backup merged');
 await expect(page.locator('[data-journal-entry]')).toHaveCount(2);
 await expect(page.locator('[data-plan] [name=thesis]')).toHaveValue('Keep existing plan');
 await importBackup(page,incoming);
 await expect(page.locator('#decision-status')).toContainText('Backup merged');
 await expect(page.locator('[data-journal-entry]')).toHaveCount(2);
 const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem('neocloud-decisions-v1')));
 expect(stored.journal.map(r=>r.id).sort()).toEqual(['existing','imported']);
});

test('malformed decision backups cannot replace or poison an existing journal',async({page})=>{
 await page.goto('/terminal/#/user-journal/agpu');
 const original=JSON.stringify(backup([backupEntry()]));
 await page.evaluate(x=>localStorage.setItem('neocloud-decisions-v1',x),original);
 await page.reload();
 const noId=backupEntry();delete noId.id;
 const invalid=[backup([noId]),backup([backupEntry('duplicate'),backupEntry('duplicate')]),
  backup([{...backupEntry(),values:[]}]),backup([{...backupEntry(),savedAt:'not-a-date'}]),
  backup([{...backupEntry(),company:'unrecognized'}])];
 for(const input of invalid){
  await importBackup(page,input);
  await expect(page.locator('#decision-status')).toContainText('Import failed');
  expect(await page.evaluate(()=>localStorage.getItem('neocloud-decisions-v1'))).toBe(original);
 }
 await expect(page.locator('[data-journal-entry]')).toHaveCount(1);
});

test('corrupt decision storage is not silently overwritten',async({page})=>{
 await page.goto('/terminal/#/user-scenario/crwv');
 await page.evaluate(()=>localStorage.setItem('neocloud-decisions-v1','{broken'));
 await page.reload();
 await page.locator('[data-save-scenario]').click();
 await expect(page.locator('#decision-status')).toContainText('Nothing was overwritten');
 expect(await page.evaluate(()=>localStorage.getItem('neocloud-decisions-v1'))).toBe('{broken');
});

test('Justin paper call saves without portfolio inputs and preserves its report across reload and backup',async({page})=>{
 await page.goto('/terminal/#/user-journal/crwv');
 await expect(page.locator('[data-paper-call]')).toContainText('CRWV');
 await expect(page.locator('[data-plan]')).toBeHidden();
 await page.getByRole('button',{name:'Save Justin paper call',exact:true}).click();
 await expect(page.locator('[data-journal-entry]')).toHaveCount(1);
 await expect(page.locator('#decision-status')).toContainText('no order placed');
 const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem('neocloud-decisions-v1')));
 const record=stored.journal[0];
 expect(record.paperCall.version).toBe(1);
 expect(JSON.parse(record.paperCall.reportJSON).id).toBe('crwv');
 expect(JSON.parse(record.paperCall.marketJSON).as_of).toBe('2026-11-25');
 expect(stored.plans).toEqual({});
 await page.reload();
 await page.locator('[data-journal-entry] summary').click();
 await expect(page.locator('[data-journal-entry]')).toContainText('Original Justin paper call');
 const download=page.waitForEvent('download');await page.locator('[data-decision-export]').click();
 const fs=require('node:fs/promises');
 const exported=JSON.parse(await fs.readFile(await (await download).path(),'utf8'));
 expect(exported.journal[0].paperCall).toEqual(record.paperCall);
 await importBackup(page,exported);
 await expect(page.locator('[data-journal-entry]')).toHaveCount(1);
 expect((await page.evaluate(()=>JSON.parse(localStorage.getItem('neocloud-decisions-v1')))).journal[0].paperCall).toEqual(record.paperCall);
 const poisoned=backup([{...record,id:'bad-paper',paperCall:{...record.paperCall,reportJSON:'{broken'}}]);
 await importBackup(page,poisoned);
 await expect(page.locator('#decision-status')).toContainText('Import failed');
 await expect(page.locator('[data-journal-entry]')).toHaveCount(1);
});
