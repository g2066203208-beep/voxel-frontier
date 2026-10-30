#!/usr/bin/env node
"use strict";
/* S06 NTM source identity only: manifest+previous OUTB receipt, NO solver/31-gage claim.
   Run from repository root:
   node research/wind-tower/experiments/T062/s06_ntm_18case_input_identity.js \
     --static research/wind-tower/archive/local-assets-20261004/file-manifest.json \
     --supplement research/wind-tower/archive/local-assets-20261004-supplement/file-manifest.json \
     --receipt research/wind-tower/experiments/T062/S06_18NTM_ORIGINAL_LOAD_DEL_RECEIPT_20261031.json \
     --check research/wind-tower/experiments/T062/S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv --self-test
*/
import fs from "node:fs";
import crypto from "node:crypto";
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const expected={
  "--static":"c9da25b3a967c9ed3b3a859666263c6964d8480798185e6e031539c38e4c3302",
  "--supplement":"35235d543bae4b82b24260a16fae1885f8123ef3cf3d8482145c704ea1eaa392",
  "--receipt":"c0a061e5895c580de413dfa02ab828dbc8be09e05ead8c57ba45445b72581125"
};

function build(staticRows, outbRows, receipt) {
  const cases=["U09p343881","U11p4","U19p202140"].flatMap(u=>Array.from({length:6},(_,i)=>u+"_NTM_S"+String(i+1).padStart(2,"0")));
  const modules=[["fst","DTU_10MW_RWT.fst"],["ed","DTU_10MW_RWT_ElastoDyn.dat"],["tower","C02R3R2_158M_Tower.dat"],["servo","Control/DTU_10MW_RWT_ServoDyn.dat"],["inflow","DTU_10MW_InflowWind.dat"]];
  function byPath(arr) {
    const m=new Map();
    for(const x of arr) {
      if(x.section!=="openfast-36-r2")continue;
      if(!x.relative_path||m.has(x.relative_path))throw Error("DUPLICATE_OR_MISSING_PATH");
      m.set(x.relative_path,x);
    }
    return m;
  }
  const sm=byPath(staticRows),om=byPath(outbRows),rm=new Map();
  if(!receipt||!Array.isArray(receipt.sources)||receipt.sources.length!==18||
     receipt.original_outb_count!==18||receipt.assumptions?.gage_count!==9)throw Error("INVALID_RECEIPT");
  for(const x of receipt.sources) {
    if(rm.has(x.case))throw Error("DUPLICATE_RECEIPT_CASE");
    rm.set(x.case,x);
  }
  if(rm.size!==18||[...rm.keys()].some(x=>!cases.includes(x)))throw Error("WRONG_CASE_SET");
  const seen=Object.fromEntries(modules.map(([k])=>[k,new Set()])),outSha=new Set();
  const header=["case","fst_sha256","elastodyn_sha256","tower_sha256","servodyn_sha256",
    "inflowwind_sha256","inflowwind_archive","outb_sha256","outb_archive",
    "outb_bytes","outb_samples","gage_count","evidence_level"];
  const csv=[header.join(",")];
  for(const c of cases) {
    const rec=rm.get(c);
    if(!rec)throw Error("MISSING_RECEIPT_CASE:"+c);
    const data={};
    for(const [k,name] of modules) {
      const p="CASES/"+c+"/"+name,x=sm.get(p);
      if(!x||!/^[a-f0-9]{64}$/i.test(x.sha256)||!Number.isSafeInteger(x.bytes)||x.bytes<=0)throw Error("BAD_STATIC_INPUT:"+p);
      if(x.status==="duplicate-reference") {
        const original=sm.get(x.canonical_member);
        if(!original||original.sha256.toLowerCase()!==x.sha256.toLowerCase()||
           original.canonical_archive!==x.canonical_archive)throw Error("BROKEN_CANONICAL_LINK:"+p);
      } else if(x.status!=="included")throw Error("UNEXPECTED_STATIC_STATUS:"+p);
      data[k]=x.sha256.toLowerCase();
      if(k==="inflow")data.inflow_archive=x.canonical_archive;
      seen[k].add(data[k]);
    }
    const p="CASES/"+c+"/DTU_10MW_RWT.outb",x=om.get(p);
    if(!x||x.status!=="included"||x.sha256.toLowerCase()!==rec.outb_sha256.toLowerCase()||
       x.bytes!==rec.bytes||x.canonical_archive.split("/").pop()!==rec.archive||
       rec.n_samples!==12001||rec.n_channels!==295||rec.file_id!==4)
       throw Error("OUTB_RECEIPT_OR_FORMAT_MISMATCH:"+c);
    if(outSha.has(x.sha256.toLowerCase()))throw Error("DUPLICATE_OUTB_SHA");
    outSha.add(x.sha256.toLowerCase());
    csv.push([c,data.fst,data.ed,data.tower,data.servo,data.inflow,data.inflow_archive,
      x.sha256.toLowerCase(),x.canonical_archive,x.bytes,rec.n_samples,9,
      "STATIC_MANIFEST_PLUS_PRIOR_OUTB_SHA_RECEIPT"].join(","));
  }
  for(const k of ["fst","ed","tower","servo"])if(seen[k].size!==1)throw Error("FIXED_INPUT_IDENTITY_DIVERGENCE:"+k);
  if(seen.inflow.size!==18||outSha.size!==18)throw Error("WIND_SEED_IDENTITY_DIVERGENCE");
  return {csv:csv.join("\n")+"\n",rows:18,unique:Object.fromEntries(Object.entries(seen).map(([k,v])=>[k,v.size])),outb_unique:outSha.size};
}
function selfTest(a,b,c) {
  const clone=x=>JSON.parse(JSON.stringify(x));
  function mustReject(label,mutate) {
    const x=clone(a),y=clone(b),z=clone(c);
    mutate(x,y,z);
    try{build(x,y,z)}catch(e){console.log("NEGATIVE_PASS",label,e.message);return}
    throw Error("NEGATIVE_TEST_ACCEPTED:"+label);
  }
  mustReject("missing_FST",x=>x.splice(x.findIndex(e=>e.relative_path==="CASES/U11p4_NTM_S01/DTU_10MW_RWT.fst"),1));
  mustReject("outb_hash_tamper",(x,y)=>{y.find(e=>e.relative_path==="CASES/U11p4_NTM_S01/DTU_10MW_RWT.outb").sha256="0".repeat(64)});
  mustReject("tower_canonical_tamper",x=>{x.find(e=>e.relative_path==="CASES/U11p4_NTM_S01/C02R3R2_158M_Tower.dat").sha256="1".repeat(64)});
  mustReject("duplicate_wind_sha",x=>{x.find(e=>e.relative_path==="CASES/U11p4_NTM_S01/DTU_10MW_InflowWind.dat").sha256=x.find(e=>e.relative_path==="CASES/U11p4_NTM_S02/DTU_10MW_InflowWind.dat").sha256});
}
function main(args) {
  const flags={};
  for(let i=0;i<args.length;i++){
    if(args[i]==="--self-test"){flags["--self-test"]=true;continue}
    if(!args[i].startsWith("--")||!args[i+1])throw Error("INVALID_ARGUMENT");
    flags[args[i]]=args[++i];
  }
  const sources={};
  for(const [flag,hash] of Object.entries(expected)) {
    if(!flags[flag])throw Error("MISSING_REQUIRED_"+flag);
    const raw=fs.readFileSync(flags[flag]);
    if(sha(raw)!==hash)throw Error("SOURCE_SHA256_MISMATCH:"+flag);
    sources[flag]=JSON.parse(raw.toString("utf8"));
  }
  const a=sources["--static"],b=sources["--supplement"],c=sources["--receipt"];
  const out=build(a,b,c);
  if(flags["--self-test"])selfTest(a,b,c);
  if(flags["--check"]){
    if(fs.readFileSync(flags["--check"],"utf8")!==out.csv)throw Error("COMMITTED_CSV_MISMATCH");
  }
  if(flags["--out"])fs.writeFileSync(flags["--out"],out.csv);
  console.log("S06_NTM_18_INPUT_IDENTITY_NUMERIC_PASS",JSON.stringify({
    rows:out.rows,unique:out.unique,outb_unique:out.outb_unique,
    csv_sha256:sha(Buffer.from(out.csv,"utf8")),
    evidence:"MANIFEST_AND_PRIOR_OUTB_RECEIPT_ONLY",
    physical_pass:false}));
}
try{main(process.argv.slice(2))}catch(e){console.error(e.message);process.exitCode=1}
