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
    const sourceMeta=await page.locator('#source-status').innerText();
    assert.ok(sourceMeta.includes('9e5940d0631680f4'),'Editor did not load illustrated Word V3 source: '+sourceMeta);
    checks.correct_illustrated_v3_source = true;
    await page.locator('#chapter-list button[data-chapter="02"]').click();
    await page.getByText('表2-2  参考混凝土塔段分节几何与纵筋数量', {exact:false}).waitFor({timeout:10000});
    const ch2Text=await page.locator('#document-body').innerText();
    for(const term of ['表2-2','表2-3','C01','C31','S04','BF1历史模型以36根']){
      assert.ok(ch2Text.includes(term),'Missing source or revision evidence '+term);
    }
    checks.chapter2_revised_geometry_tables_and_scientific_limits = true;
    const restoredFigures=page.locator('#document-body .thesis-inline-figure img');
    assert.equal(await restoredFigures.count(),4,'Expected exactly 4 restored figures in editable chapter 2');
    for(const fig of ['图2-1','图2-2','图2-3','图2-4']){
      const im=page.locator('img[data-figure="'+fig+'"]');
      assert.equal(await im.count(),1,'Missing correct caption image '+fig);
      const imageUrl=await im.getAttribute('src');
      const response=await page.request.get(new URL(imageUrl,SITE));
      assert.equal(response.status(),200,'Illustration cannot be fetched: '+fig);
    }
    checks.all_four_original_figures_visible_and_fetchable = true;
    await page.locator('#chapter-list button[data-chapter="front"]').click();
    const pdfResponse=await page.request.get(new URL('./downloads/10MW-thesis-illustrated-v3-20261121.pdf',SITE).toString());
    assert.equal(pdfResponse.status(),200,'PDF preview URL is broken');
    checks.pdf_source_downloadable = true;
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
    await page.locator('#export-menu').click();
    const docxPromise=page.waitForEvent('download',{timeout:180000});
    await page.getByRole('button',{name:'一键导出修改后的 Word（自动读取母本）'}).click();
    const wordDownload=await docxPromise;
    assert.ok(wordDownload.suggestedFilename().toLowerCase().endsWith('.docx'),'Word export filename invalid');
    const wordPath='/tmp/thesis-live-tested.docx';
    await wordDownload.saveAs(wordPath);
    assert.ok(fs.statSync(wordPath).size>1000000,'Downloaded Word appears incomplete');
    const xml=require('node:child_process').execFileSync('unzip',['-p',wordPath,'word/document.xml'],{maxBuffer:25000000}).toString('utf8');
    assert.ok(xml.includes(marker),'Downloaded Word XML does not contain the actual edit');
    checks.word_download_includes_edit = true;
    assert.ok((xml.match(/<w:drawing/g)||[]).length>=4,'Exported V3 DOCX lost the four restored source figures');
    checks.word_download_preserves_four_figures = true;
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
