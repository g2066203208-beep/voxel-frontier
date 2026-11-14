#!/usr/bin/env node
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const crypto=require("node:crypto");
const base=path.resolve(__dirname,"../public/thesis-studio");
const read=(p)=>fs.readFileSync(path.join(base,p),"utf8");
const script=read("library.js");
assert.match(script,/async function zipFiles\(/);
assert.match(script,/indexedDB\.open/);
assert.match(script,/async function refreshGithub\(/);
const input=script.replace(/\bboot\(\);\s*$/,"");
assert.notEqual(input,script,"must remove boot() for unit tests");
const sandbox={TextEncoder,Blob,console,URL,Uint8Array,Uint32Array,DataView,Date,Math,setTimeout,clearTimeout};
vm.createContext(sandbox);
vm.runInContext(input,sandbox,{filename:"library.js"});
const crc=sandbox.crc32(new Uint8Array(Buffer.from("123456789","utf8")));
assert.equal(crc>>>0,0xcbf43926,"CRC-32 IEEE test vector");
assert.equal(sandbox.nameSafe("../资料.csv"),".._资料.csv","zip filename traversal sanitized");
const idx=JSON.parse(read("data/repository-index.json"));
assert.equal(idx.files.length,idx.fileCount);
assert.ok(idx.fileCount>=3200);
assert.equal(new Set(idx.files.map(x=>x.p)).size,idx.fileCount,"unique paths");
assert.equal(idx.groups.reduce((n,g)=>n+g.count,0),idx.fileCount,"group totals");
assert.ok(idx.files.every(x=>x.p.startsWith("research/wind-tower/")));
assert.ok(idx.files.some(x=>x.g==="论文与期刊"));
assert.ok(idx.files.some(x=>x.g==="地震与风震联合"));
assert.ok(idx.files.some(x=>x.g==="风资源与载荷"));
assert.ok(idx.files.some(x=>x.l),"Git LFS pointers should be recognized");
const html=read("library.html");
for(const id of ["remote-list","local-list","dropzone","submit-issue","remote-bundle","local-zip","remote-refresh","file-input"]){
 assert.ok(html.includes('id="'+id+'"'),"missing UI control "+id);
}

const figureIndex=JSON.parse(read("data/figure-index.json"));
assert.equal(figureIndex.total,figureIndex.images.length,"figure catalog completeness");
assert.equal(figureIndex.total,541,"all images in the original research branch");
assert.equal(figureIndex.hosted,541,"all originals should be deployed in Pages");
assert.equal(figureIndex.hePages.length,11,"11 He Zeyu source pages");
assert.equal(figureIndex.documents.length,3,"Jiayu government, EIA, and He thesis PDFs");
function gitBlobSha(buf){
  return crypto.createHash("sha1").update("blob "+buf.length+"\0").update(buf).digest("hex");
}
const featuredNames=[
 "figure2-1-word-zh.png",
 "mesh-convergence-zh.png",
 "FIG_S05_03_ROTD_PUBLICATION.svg",
 "FIG4_S10_ETM4_TENSION_DEL4_AZIMUTH_TRADEOFF_20261109.svg"
];
for(const n of featuredNames){
  const matched=figureIndex.images.find(x=>x.h&&x.n===n);
  assert.ok(matched,"missing original image "+n);
}
let hostedFiles=0;
for(const f of figureIndex.images.filter(x=>x.h)){
  assert.ok(!f.p.includes("../"),"unexpected figure path");
  const asset=path.join(base,"figures",f.p);
  const buffer=fs.readFileSync(asset);
  assert.equal(buffer.length,f.s,"original source image size "+f.p);
  assert.equal(gitBlobSha(buffer),f.sha,"original Git blob SHA "+f.p);
  hostedFiles++;
}
assert.equal(hostedFiles,figureIndex.hosted,"hosted original image tally");
const allFigurePaths=new Set(figureIndex.images.map(x=>x.p));
for(const p of figureIndex.hePages)assert.ok(allFigurePaths.has(p),"missing He original-page file "+p);
for(const doc of figureIndex.documents){
  const file=path.join(base,"documents",doc.name);
  const bytes=fs.readFileSync(file);
  assert.equal(bytes.toString("latin1",0,5),"%PDF-","original PDF header "+doc.name);
  assert.equal(bytes.length,doc.size,"original PDF size "+doc.name);
  assert.equal(gitBlobSha(bytes),doc.sha,"original PDF Git SHA "+doc.name);
}
const figureScript=read("figures.js");
assert.ok(figureScript.includes("renderGrid"),"all-image grid renderer");
assert.ok(figureScript.includes("window.JYReader"),"figure catalog integrates PDF reader");
const readerScript=read("reader.js");
assert.ok(readerScript.includes("getDocument"),"PDF.js document loading");
assert.ok(readerScript.includes("renderPage"),"PDF canvas");
assert.ok(readerScript.includes("getOutline"),"PDF table of contents");
assert.ok(readerScript.includes("searchDocument"),"PDF text search");
assert.ok(readerScript.includes("reader-text-mode"),"PDF text mode");
assert.ok(readerScript.includes("showFallback"),"PDF fallback");
new Function(readerScript);
assert.ok(figureScript.includes("renderHe"),"He original pages renderer");
assert.ok(!figureScript.includes("raw.githubusercontent"),"all original images use same-site paths");
new Function(figureScript);


const references=JSON.parse(read("data/reference-index.json"));
assert.equal(references.total,81,"original PDF index count");
assert.equal(references.entries.length,81,"PDF source records complete");
assert.equal(references.readable,79,"readable PDF sources");
assert.equal(references.originalImageCount,395,"source pages and archive screenshots");
assert.equal(references.masterCount,163,"all bibliography master entries");
assert.equal(references.master.length,163,"literature master completeness");
assert.equal(new Set(references.master.map(x=>x.id)).size,163,"unique bibliography IDs");
assert.equal(new Set(references.entries.map(x=>x.path)).size,81,"unique PDF original paths");
assert.equal(references.images.length,395,"original evidence scan index");
assert.equal(references.images.reduce((x,y)=>x+(figureIndex.images.some(f=>f.p===y.p&&f.sha===y.sha)?1:0),0),395,"source screenshots SHA cross-index verified");
assert.ok(references.entries.some(x=>x.name==="He_Zeyu_2024_hybrid_tower_thesis.pdf"&&x.mode==="local"),"He thesis original");
assert.ok(references.entries.some(x=>x.name.includes("嘉鱼县政府")&&x.mode==="local"),"Jiayu government original");
assert.ok(references.entries.some(x=>x.name.includes("簰洲湾")&&x.mode==="local"),"Jiayu wind EIA original");
assert.ok(references.entries.some(x=>x.name.includes("李泽宇")&&x.url),"Li Zeyu thesis source available");
assert.ok(references.entries.some(x=>x.category==="规范与标准"&&!x.url),"restricted standards are not copied to public Pages");
const referenceScript=read("references.js");
assert.ok(referenceScript.includes("reference-master"),"full bibliography view");
assert.ok(referenceScript.includes("reference-scan-grid"),"original-page image viewer");
assert.ok(referenceScript.includes("focusReference"),"inline PDF source route");
new Function(referenceScript);

const home=read("index.html");
const notes=fs.readFileSync(path.resolve(__dirname,"../research-notes.html"),"utf8");
assert.ok(notes.includes('class="embedded-mode"'),"legacy drafts embedded rather than separate studio");
const redirect=fs.readFileSync(path.resolve(__dirname,"../index.html"),"utf8");
assert.ok(redirect.includes("./thesis-studio/"),"old home redirects to canonical studio");
assert.ok(home.includes('href="#library"'),"unified file library navigation");
assert.ok(home.includes('src="./references.js"'),"bibliography sources loaded in single studio");
assert.ok(home.includes('id="library-view"'),"file library embedded in single studio");
assert.ok(home.includes('id="notes-view"'),"original research records embedded in single studio");
assert.ok(home.includes('id="notes-frame"'),"original paper drafts kept accessible");
assert.ok(home.includes('id="figures-view"'),"unified scientific figure gallery");
assert.ok(home.includes('id="figure-lightbox"'),"large original preview");
assert.ok(home.includes('id="featured-figures"'),"real research images on home");
assert.ok(home.includes('id="reader-doc-list"'),"PDF source switcher");
assert.ok(home.includes('id="reader-stage"'),"PDF study workspace");
assert.ok(home.includes('id="reader-canvas"'),"PDF canvas");
assert.ok(home.includes('id="reader-reflow"'),"PDF selectable text");
assert.ok(home.includes('id="reader-query"'),"PDF search");
assert.ok(home.includes('id="figure-pageinfo"'),"paginated gallery");
assert.ok(!home.includes('class="metric-grid"'),"no decorative stats");
assert.ok(!home.includes('class="roadmap-grid"'),"no duplicate roadmap cards");
assert.ok(!home.includes('class="original-source-preview"'),"no nested homepage PDF previews");
assert.ok(!home.includes('id="original-pdf-frame"'),"legacy PDF iframe replaced");
assert.ok(home.includes('id="reader-fallback-frame"'),"native PDF fallback");
assert.ok(home.includes('id="he-original-grid"'),"He thesis page image gallery");
assert.ok(home.includes('id="reader-doc-list"'),"source document selector");
assert.ok(home.includes('嘉鱼县政府'),"Jiayu county government PDF is visible in UI");
assert.ok(!home.includes('id="figure-source"'),"gallery stays inside studio");
assert.ok(!home.includes('src="./documents/%E5%98%89'),"home no heavy PDF embed");

(async()=>{
 const blob=await sandbox.zipFiles([{name:"测试.csv",blob:new Blob(["abc"],{type:"text/plain"})},{name:"data.txt",blob:new Blob(["123456789"])}]);
 const data=Buffer.from(await blob.arrayBuffer());
 assert.equal(data.readUInt32LE(0),0x04034b50,"local file header");
 const length=data.readUInt16LE(26);
 assert.equal(data.subarray(30,30+length).toString("utf8"),"测试.csv","UTF-8 name preserved");
 assert.equal(data.readUInt16LE(6),0x0800,"ZIP UTF-8 flag");
 assert.equal(data.readUInt32LE(data.length-22),0x06054b50,"ZIP central directory trailer");
 assert.equal(data.readUInt16LE(data.length-22+10),2,"ZIP entry count");
 assert.ok(data.includes(Buffer.from("123456789")),"file payload retained");
 await assert.rejects(sandbox.zipFiles([{name:"huge.bin",blob:{size:101*1024*1024}}]),/100 MB/);
 console.log("JIAYU_STUDIO_QA_PASS",idx.fileCount,"project files",figureIndex.total,"images",references.total,"source PDFs",references.originalImageCount,"reference pages",references.masterCount,"bibliography entries");
})().catch(e=>{console.error(e);process.exitCode=1;});
