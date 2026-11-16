#!/usr/bin/env node
"use strict";
const assert=require("node:assert/strict");
const path=require("node:path");
const fs=require("node:fs");
const {chromium}=require("playwright");
const URL_SITE="https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/";
const out=path.join(process.cwd(),"artifacts","ui");
fs.mkdirSync(out,{recursive:true});
async function main(){
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--disable-dev-shm-usage"]});
 const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
 const fail=[];
 page.on("pageerror",e=>fail.push("PAGE_ERROR "+e.message));
 page.on("response",r=>{
  if(r.status()===404&&r.url().includes("/voxel-frontier/thesis-studio/"))fail.push("MISSING_ASSET "+r.url());
 });
 const response=await page.goto(URL_SITE,{waitUntil:"domcontentloaded",timeout:60000});
 assert.equal(response.status(),200,"site HTTP 200");
 await page.locator("#module-grid .module-card").first().waitFor({timeout:30000});
 assert.equal((await page.locator(".doc-access").count()),3,"three original sources on homepage");
 assert.equal((await page.locator(".metric-grid").count()),0,"remove vanity metrics");
 assert.equal((await page.locator(".original-source-preview").count()),0,"no distracting embedded PDF thumbnails on homepage");
 await page.locator("#featured-figures .figure-card").first().waitFor({timeout:18000});
 const homePictures=await page.locator("#featured-figures .figure-card img").count();
 assert.ok(homePictures>=2,"homepage must actually display scientific figures, not blank cards");
 await page.screenshot({path:path.join(out,"jiayu-home-desktop.png"),fullPage:true});
 // T091 direct original-data views: no GitHub navigation/download required.
 await page.locator('button[data-view="evidence"]').click();
 await page.locator("#evidence-view").waitFor({state:"visible",timeout:15000});
 await page.locator("#evidence-reader .evidence-detail .evidence-table tbody tr").first().waitFor({timeout:30000});
 assert.equal(await page.locator("#evidence-reader .evidence-dataset-card").count(),11,
   "9 source tables + one real-wave source status + 92 parameter archive");
 assert.equal(await page.locator("#evidence-reader .evidence-detail .evidence-table tbody tr").count(),31,
   "ERA5 full source bin table should have 31 rows");
 assert.ok((await page.locator("#evidence-reader").innerText()).includes("184,080"),
   "ERA5 full 21-year source clock visible");
 await page.screenshot({path:path.join(out,"jiayu-era5-original-data.png"),fullPage:false});
 await page.locator("#evidence-reader .evidence-dataset-card").filter({hasText:"ESM三分量同步加速度"}).click();
 const esmFigure=page.locator("#evidence-reader .evidence-detail .thesis-inline-figure img");
 await esmFigure.waitFor({timeout:25000});
 await esmFigure.scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>{
   const x=document.querySelector("#evidence-reader .evidence-detail .thesis-inline-figure img");
   return x&&x.complete&&x.naturalWidth>300;
 },null,{timeout:30000});
 await page.screenshot({path:path.join(out,"jiayu-real-esm-3component-original.png"),fullPage:false});
 await page.locator('button[data-view="thesis"]').click();
 await page.locator("#thesis-view").waitFor({state:"visible",timeout:15000});
 await page.locator("#thesis-reader .thesis-full-article h2").first().waitFor({timeout:35000});
 assert.equal(await page.locator("#thesis-reader .thesis-chapter-tab").count(),6,
  "six complete original manuscript chapters");
 await page.locator('#thesis-reader .thesis-chapter-tab[data-chapter="03"]').click();
 await page.waitForFunction(()=>{
  const x=document.querySelector("#thesis-reader .thesis-full-article");
  return x?.innerText.includes("184080")&&x?.innerText.length>12000;
 },null,{timeout:30000});
 await page.screenshot({path:path.join(out,"jiayu-six-chapter-thesis-inline.png"),fullPage:false});
 await page.locator('button[data-view="windResource"]').click();
 await page.locator('#module-view .source-inline-open').filter({hasText:"风资源证据图谱"}).click();
 await page.locator('#original-source-inline-reader .evidence-table tbody tr').first().waitFor({timeout:30000});
 assert.ok((await page.locator('#original-source-inline-reader .evidence-table tbody tr').count())>=1,
  "GitHub research TSV displays as full original in-page table without redirect");
 await page.screenshot({path:path.join(out,"jiayu-research-source-inline.png"),fullPage:false});
 await page.locator('button[data-view="literature"]').click();
 await page.locator("#journal-original-pages .journal-page").first().waitFor({timeout:30000});
 assert.equal(await page.locator("#journal-original-pages .journal-paper").count(),8,"six development papers and two legally archived comparators");
 assert.equal(await page.locator("#journal-original-pages .journal-page").count(),40,"18+22 genuine PDF page images inline");
 assert.equal(await page.locator("#journal-original-pages .journal-paper").filter({has:page.locator(".journal-page")}).count(),2,"only two CC BY papers have full page images");
 assert.equal(await page.locator("#journal-original-pages a").count(),0,"journal original-page reader never navigates away");
 const firstJ=page.locator("#journal-original-pages .journal-original-sheet").first();
 await firstJ.scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>{
  const n=document.querySelector("#journal-original-pages .journal-original-sheet");
  return n&&n.complete&&n.naturalWidth>300;
 },null,{timeout:30000});
 await page.screenshot({path:path.join(out,"jiayu-full-licensed-paper-page.png"),fullPage:false});
 await page.locator("#all-reference-corpus .corpus-file").first().waitFor({timeout:30000});
 assert.equal(await page.locator("#all-reference-corpus .corpus-file").count(),81,"all 81 archived reference records in page");
 assert.equal(await page.locator("#all-reference-corpus .corpus-open").count(),79,"79 existing PDF original sources individually accessible");
 assert.equal(await page.locator("#all-reference-corpus .corpus-master-row").count(),163,"all 163 academic bibliography records directly shown");
 assert.equal(await page.locator("#all-reference-corpus .corpus-scan-card").count(),395,"395 source sheets displayed without pagination");
 assert.equal(await page.locator("#all-reference-corpus a").count(),0,"complete corpus requires no links/downloads");
 await page.locator('#all-reference-corpus .corpus-file[data-ref="L040"] .corpus-open').click();
 await page.waitForFunction(()=>{
  const status=document.querySelector("#corpus-pdf-status")?.textContent||"";
  return status.includes("PDF.js已读取")||status.includes("失败");
 },null,{timeout:30000}).catch(()=>{});
 const pdfState=await page.locator("#corpus-pdf-status").innerText();
 console.log("REAL_ORIGINAL_PDF_STATUS",pdfState);
 if(!pdfState.includes("PDF.js已读取")){
  await page.screenshot({path:path.join(out,"jiayu-reference-pdf-failure-diagnostic.png"),fullPage:false});
  const detail=await page.locator("#corpus-pdf-pages").innerText();
  throw Error("Original indexed PDF not rendering: "+pdfState+" // "+detail.slice(0,700));
 }
 assert.ok((await page.locator("#corpus-pdf-pages .corpus-pdf-page").count())>=2,
   "real PDF continuous pages created after load");
 await page.locator("#corpus-pdf-page-1 canvas").waitFor({timeout:45000});
 assert.ok((await page.locator("#corpus-pdf-pages .corpus-pdf-page").count())>=2,
   "every genuine publisher PDF page has own position in continuous viewer");
 assert.equal(await page.locator("#corpus-fulltext-reader a").count(),0,
   "selected complete PDF pages have no external navigation or download anchor");
 await page.screenshot({path:path.join(out,"jiayu-81-archived-papers-inline.png"),fullPage:false});
 console.log("FULL_REFERENCE_CORPUS_OK: 81 PDF records, 79 indexed originals, 163 citations, 395 original sheets, PDF.js first real page rendered");
 await page.locator('button[data-view="overview"]').click();

 await page.locator('[data-open-document="jiayu-gov"]').click();
 await page.locator("#figures-view").waitFor({state:"visible",timeout:10000});
 await page.locator("#joint-atlas-gallery .atlas-journal-card").first().waitFor({timeout:30000});
 assert.equal(await page.locator("#joint-atlas-gallery .atlas-journal-card").count(),5,"five licensed journal originals are inlined");
 assert.equal(await page.locator("#joint-atlas-papers .atlas-paper").count(),24,"all 24 horizontal-joint papers displayed in original atlas");
 assert.equal(await page.locator("#atlas-complete-grid .atlas-file-card").count(),541,"all 541 archived original images rendered without pagination");
 assert.equal(await page.locator("#joint-atlas a").count(),0,"journal atlas has no offsite links or download anchors");
 assert.equal(await page.locator("#atlas-complete a").count(),0,"full original image reader has no navigation/download links");
 assert.equal(await page.locator("#joint-atlas .atlas-bibliography").getAttribute("open"),"","24 paper records expanded without click");
 const firstJournal=page.locator("#joint-atlas-gallery .atlas-journal-img").first();
 await firstJournal.scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>{
  const x=document.querySelector("#joint-atlas-gallery .atlas-journal-img");
  return x?.complete&&x.naturalWidth>0;
 },null,{timeout:30000});
 assert.ok((await firstJournal.evaluate(x=>x.naturalWidth))>0,"pinned Springer original PNG actually loads");
 await page.screenshot({path:path.join(out,"jiayu-joint-original-inline.png"),fullPage:false});
 console.log("INLINE_ATLAS_OK: 5 journal figures, 24 papers, 541 complete image cards, original PNG decoded, no atlas links");
 assert.equal((await page.locator("#reader-doc-list .reader-doc").count()),3,"all PDF sources in reader");
 await page.waitForFunction(()=>{
  const canvas=document.getElementById("reader-canvas");
  const status=document.getElementById("reader-status");
  return canvas&&canvas.width>100&&canvas.height>100&&status&&status.textContent.includes("页");
 },null,{timeout:60000}).catch(async e=>{
  console.log("READER_STATUS",await page.locator("#reader-status").innerText());
  console.log("FALLBACK_NOTE",await page.locator("#reader-fallback-note").innerText());
  throw e;
 });
 let pageCount=await page.locator("#reader-total").innerText();
 console.log("PDF_READER_OK gov pages",pageCount);
 assert.ok(pageCount.includes("/"),"reader pagination visible");
 await page.locator("#reader-next").click();
 await page.waitForFunction(()=>document.getElementById("reader-page")?.value==="2",null,{timeout:15000});
 await page.locator("#reader-zoom-in").click();
 await page.waitForTimeout(500);
 assert.notEqual(await page.locator("#reader-zoom-label").innerText(),"适合宽度");
 await page.locator("#reader-text-mode").click();
 await page.locator("#reader-reflow").waitFor({state:"visible",timeout:15000});
 await page.locator("#reader-text-mode").click();
 await page.locator('#reader-doc-list .reader-doc[data-id="he-thesis"]').click();
 await page.waitForFunction(()=>{
  const status=document.getElementById("reader-status");
  const h=document.getElementById("reader-title");
  return h?.textContent.includes("何泽瑜")&&status?.textContent.includes("页");
 },null,{timeout:60000});
 await page.screenshot({path:path.join(out,"jiayu-reader-desktop.png"),fullPage:false});
 console.log("PDF_READER_OK He thesis pages",await page.locator("#reader-total").innerText());
 // Modern public complete gallery has exactly 541 inline original cards, not hidden legacy paged UI.
 assert.equal(await page.locator("#atlas-complete-grid .atlas-file-card").count(),541);
 await page.locator("#atlas-complete-search").fill("RotD");
 assert.ok((await page.locator("#atlas-complete-grid .atlas-file-card").count())>0,"visible original figure search works");
 await page.locator("#atlas-complete-search").fill("");
 await page.screenshot({path:path.join(out,"jiayu-gallery-desktop.png"),fullPage:false});
 const mobile=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
 await mobile.goto(URL_SITE,{waitUntil:"domcontentloaded",timeout:60000});
 await mobile.locator("#module-grid .module-card").first().waitFor({timeout:30000});
 const size=await mobile.evaluate(()=>({scroll:document.documentElement.scrollWidth,visible:document.documentElement.clientWidth}));
 assert.ok(size.scroll-size.visible<=7,"mobile has no horizontal overflow: "+JSON.stringify(size));
 await mobile.screenshot({path:path.join(out,"jiayu-home-mobile.png"),fullPage:true});
 if(fail.length)throw Error("Browser errors:\n"+fail.slice(0,15).join("\n"));
 console.log("JIAYU_BROWSER_QA_PASS: homepage, PDF.js page render, navigation, zoom, text, He source, journal originals, full inline image atlas, gallery paging, 390px mobile");
 await browser.close();
}
main().catch(e=>{console.error(e);process.exitCode=1;});
