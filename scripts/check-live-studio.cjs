"use strict";
const fs=require("node:fs");
const base="https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const report={base,started:new Date().toISOString(),attempts:[],ok:false};
async function getJSON(rel){
 const r=await fetch(base+rel,{cache:"no-store",signal:AbortSignal.timeout(16000)});
 if(!r.ok)throw Error(rel+" HTTP "+r.status);
 return r.json();
}
async function main(){
 for(let i=1;i<=48;i++){
  try{
   const catalog=await getJSON("data/catalog.json");
   report.attempts.push({i,version:catalog?.meta?.version,time:new Date().toISOString()});
   if(catalog?.meta?.version==="v1.9.2"){
    const [fig,ref,files,man]=await Promise.all([
     getJSON("data/figure-index.json"),
     getJSON("data/reference-index.json"),
     getJSON("data/repository-index.json"),
     getJSON("primary-data/manifest.json")]);
    const result={figures:fig.images?.length,refs:ref.entries?.length,bibliography:ref.master?.length,scans:ref.images?.length,files:files.files?.length,datasets:man.datasets?.length,chapters:man.chapters?.length};
    report.assetCounts=result;
    report.ok=result.figures===541&&result.refs===81&&result.bibliography===163&&result.scans===395&&result.files===3235&&result.datasets===9&&result.chapters===6;
    if(report.ok)break;
   }
  }catch(e){report.attempts.push({i,error:e.message,time:new Date().toISOString()})}
  if(i<48)await sleep(10000);
 }
 report.finished=new Date().toISOString();
 fs.mkdirSync("artifacts",{recursive:true});
 fs.writeFileSync("artifacts/studio-live-deployment.json",JSON.stringify(report,null,2));
 console.log(JSON.stringify({ok:report.ok,latest:report.attempts.at(-1),assetCounts:report.assetCounts,attempts:report.attempts.length}));
 if(!report.ok)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1});
