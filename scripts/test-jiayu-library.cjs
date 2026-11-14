#!/usr/bin/env node
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
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
assert.ok(figureIndex.total>=500,"expected GitHub original figure inventory");
assert.ok(figureIndex.hosted>=140,"expected published original research images");
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
  assert.ok(!f.p.startsWith("references/"),"third-party reference scan was republished");
  assert.ok(!f.p.includes("../"),"unexpected image path");
  const asset=path.join(base,"figures",f.p);
  const stat=fs.statSync(asset);
  assert.equal(stat.size,f.s,"copied Git blob must match source size "+f.p);
  hostedFiles++;
}
assert.equal(hostedFiles,figureIndex.hosted,"hosted image tally");
new Function(read("figures.js"));

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
 console.log("JIAYU_STUDIO_QA_PASS",idx.fileCount,"files",figureIndex.total,"images",figureIndex.hosted,"original hosted images / ZIP UTF8 CRC / UI controls");
})().catch(e=>{console.error(e);process.exitCode=1;});
