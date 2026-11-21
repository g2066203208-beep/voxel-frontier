const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const SITE = 'https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/manuscript-workbench.html';
const delay = n => new Promise(resolve => setTimeout(resolve, n));
(async () => {
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({acceptDownloads:true});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const checks = {};
  let original = null, touched = false;
  try {
    let online = false;
    for (let k=0; k<25; k++) {
      try {
        const r=await page.goto(SITE+'?verify='+Date.now(),{waitUntil:'domcontentloaded',timeout:20000});
        if(r?.status() === 200) {
          await page.locator('#chapter-list button').first().waitFor({timeout:6000});
          online=true;break;
        }
        console.log('Deployment not yet available:',r?.status());
      } catch(e) { if(!/Timeout|net::|page.goto|Navigation|Target closed|ERR_/i.test(e.message))throw e; console.log('Retry:',e.message.slice(0,150)); }
      await delay(12000);
    }
    assert.ok(online,'Production GitHub Pages editor did not load');
    checks.public_site_load = true;
    assert.equal(await page.locator('#chapter-list button').count(),8);
    checks.front_and_seven_chapters = true;
    const paragraph=page.locator('#document-body .editable').first();
    original=await paragraph.innerText();
    assert.ok(original.length>0,'Original manuscript text empty');
    const marker='【E2E临时测试-不公开】'+Date.now();
    await paragraph.fill(original+marker);
    touched=true;
    await page.getByText('已自动保存 · 本机').waitFor({timeout:10000});
    checks.autosave_confirmed = true;
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('#document-body .editable').first().waitFor();
    assert.ok((await page.locator('#document-body .editable').first().innerText()).includes(marker),'Edit disappeared on reload');
    checks.edits_persist_after_reload = true;
    await page.locator('#snapshot-button').click();
    await page.locator('#history-button').click();
    assert.ok((await page.locator('#modal-body').innerText()).includes('1处修改'));
    checks.history_snapshot = true;
    await page.locator('#modal-close').click();
    await page.locator('#export-menu').click();
    const downloadPromise=page.waitForEvent('download');
    await page.getByRole('button',{name:'导出修改备份 JSON（可恢复）'}).click();
    const download=await downloadPromise;
    await download.saveAs('/tmp/thesis-live-test-backup.json');
    const backup=JSON.parse(fs.readFileSync('/tmp/thesis-live-test-backup.json','utf8'));
    assert.ok(JSON.stringify(backup.patches).includes(marker),'Download does not contain edited content');
    checks.download_includes_edit = true;
    await page.locator('#modal-close').click();
    await page.locator('#document-body .editable').first().fill(original);
    touched=false;
    await delay(1100);
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('#document-body .editable').first().waitFor();
    assert.equal(await page.locator('#document-body .editable').first().innerText(),original);
    assert.equal(await page.locator('#edit-counter').innerText(),'0处修改');
    checks.test_edit_reverted = true;
    assert.equal(errors.length,0,'Browser errors: '+errors.join('; '));
    checks.no_browser_errors = true;
    console.log('LIVE_THESIS_EDITOR_E2E_PASS',JSON.stringify({url:SITE,checks,tested_at:new Date().toISOString()}));
  } catch(e) {
    console.error('LIVE_THESIS_EDITOR_E2E_FAIL',e.stack || String(e));
    console.error('CHECKS',JSON.stringify(checks));
    process.exitCode=1;
  } finally {
    if(touched && original!==null) {
      try {await page.locator('#modal-close').click({timeout:500});} catch {}
      try {await page.locator('#document-body .editable').first().fill(original);await delay(1000);} catch {}
    }
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exitCode=1});
