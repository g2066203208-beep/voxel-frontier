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
  return crypto.createHash("sha1").update("blob "+buf.length+"\\0").update(buf).digest("hex");
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
assert.ok(figureScript.includes("renderDocs"),"inline PDF reader renderer");
assert.ok(figureScript.includes("renderHe"),"He original pages renderer");
assert.ok(!figureScript.includes("raw.githubusercontent"),"all original images use same-site paths");
new Function(figureScript);

const home=read("index.html");
const notes=fs.readFileSync(path.resolve(__dirname,"../research-notes.html"),"utf8");
assert.ok(notes.includes('class="embedded-mode"'),"legacy drafts embedded rather than separate studio");
const redirect=fs.readFileSync(path.resolve(__dirname,"../index.html"),"utf8");
assert.ok(redirect.includes("./thesis-studio/"),"old home redirects to canonical studio");
assert.ok(home.includes('href="#library"'),"unified file library navigation");
assert.ok(home.includes('id="library-view"'),"file library embedded in single studio");
assert.ok(home.includes('id="notes-view"'),"original research records embedded in single studio");
assert.ok(home.includes('id="notes-frame"'),"original paper drafts kept accessible");
assert.ok(home.includes('id="figures-view"'),"unified scientific figure gallery");
assert.ok(home.includes('id="figure-lightbox"'),"large original preview");
assert.ok(home.includes('id="featured-figures"'),"real research images on home");
assert.ok(home.includes('figure2-1-word-zh.png'),"original tower diagram replaces decorative art");
assert.ok(home.includes('id="original-pdf-frame"'),"inline original PDF reader");
assert.ok(home.includes('id="he-original-grid"'),"He thesis page image gallery");
assert.ok(home.includes('id="original-document-tabs"'),"all source document tabs");
assert.ok(home.includes('嘉鱼县政府'),"Jiayu county government PDF is visible in UI");
assert.ok(!home.includes('id="figure-source"'),"image viewer cannot navigate to GitHub");

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
 console.log("JIAYU_STUDIO_QA_PASS",idx.fileCount,"files",figureIndex.total,"images",figureIndex.hosted,"SHA-verified originals and PDFs / ZIP UTF8 CRC / UI controls");
})().catch(e=>{console.error(e);process.exitCode=1;});
