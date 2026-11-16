"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const root=path.join(process.cwd(),"public/thesis-studio");
const read=(p)=>fs.readFileSync(path.join(root,p));
const json=p=>JSON.parse(read(p).toString("utf8"));
const summary={version:1,checkedAt:new Date().toISOString(),counts:{},missing:[],mismatches:[],warnings:[]};
const ref=json("data/reference-index.json"),fig=json("data/figure-index.json"),m=json("primary-data/manifest.json"),repository=json("data/repository-index.json");
function check(name,expected,actual){summary.counts[name]=actual;if(actual!==expected)summary.mismatches.push({name,expected,actual})}
check("PDF registry",81,ref.entries.length);
check("PDF indexed files",79,ref.entries.filter(x=>x.status==="indexed").length);
check("bibliography",163,ref.master.length);
check("archived source pages",395,ref.images.length);
check("original figures",541,fig.images.length);
check("research file inventory",3235,repository.files.length);
check("six original chapters",6,m.chapters.length);
check("inline datasets",9,m.datasets.length);
function confirmFile(name,rel,expectedSha256,expectedGitSha){
 const filename=path.join(root,rel);
 if(!fs.existsSync(filename)){summary.missing.push({name,path:rel});return}
 const bytes=fs.readFileSync(filename);
 if(!bytes.length){summary.missing.push({name,path:rel,issue:"empty"});return}
 if(expectedSha256){
  const got=crypto.createHash("sha256").update(bytes).digest("hex");
  if(got!==expectedSha256)summary.mismatches.push({name,path:rel,expected:expectedSha256,actual:got});
 }
 if(expectedGitSha){
  const blob=crypto.createHash("sha1").update(Buffer.from("blob "+bytes.length+"\0")).update(bytes).digest("hex");
  if(blob!==expectedGitSha)summary.mismatches.push({name,path:rel,expected:expectedGitSha,actual:blob});
 }
}
for(const f of fig.images)confirmFile("original figure",path.posix.join("figures",f.p),null,f.sha);
for(const d of m.datasets)confirmFile("research dataset",d.src.replace(/^\.\//,""),d.provenance?.sha256);
for(const d of m.chapters)confirmFile("manuscript chapter",d.src.replace(/^\.\//,""),d.provenance?.sha256);
for(const d of ref.entries.filter(x=>x.status==="indexed"&&x.url?.startsWith("./"))){
 const local=d.url.replace(/^\.\//,"").split("/").map(decodeURIComponent).join("/");
 confirmFile("published PDF",local);
 const full=path.join(root,local);
 if(fs.existsSync(full)&&read(local).subarray(0,5).toString("ascii")!=="%PDF-")
  summary.mismatches.push({name:"PDF bytes",path:local,expected:"%PDF- header"});
}
for(const x of ref.entries.filter(x=>x.status==="restricted"))summary.warnings.push(x.id+" original unavailable: "+x.mode);
summary.ok=summary.missing.length===0&&summary.mismatches.length===0;
fs.mkdirSync("artifacts",{recursive:true});
fs.writeFileSync("artifacts/studio-source-integrity.json",JSON.stringify(summary,null,2));
console.log(JSON.stringify({ok:summary.ok,counts:summary.counts,missing:summary.missing.slice(0,10),mismatches:summary.mismatches.slice(0,10),warnings:summary.warnings}));
if(!summary.ok)process.exitCode=1;