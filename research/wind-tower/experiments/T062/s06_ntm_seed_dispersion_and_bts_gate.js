#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),crypto=require("node:crypto");
const SRC="95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f",MAN="c9da25b3a967c9ed3b3a859666263c6964d8480798185e6e031539c38e4c3302";
const bins=["U09p343881_NTM","U11p4_NTM","U19p202140_NTM"];
const channels=["TwrBsMyt",...Array.from({length:9},(_,i)=>"TwHt"+(i+1)+"MLyt")];
function sha(b){return crypto.createHash("sha256").update(b).digest("hex")}
function must(x,m){if(!x)throw Error(m)}
function parse(s){
 const lines=s.trimEnd().split(/\r?\n/),h=lines.shift().split(",");
 must(new Set(h).size===h.length,"DUPLICATE_HEADER");
 for(const k of ["case","channel","unit","n_samples","t0_s","t1_s","dt_s","DEL_m4_Nref600","outb_sha256"])must(h.includes(k),"MISSING_"+k);
 return lines.map((l,i)=>{const a=l.split(",");must(a.length===h.length,"CSV_WIDTH_"+i);return Object.fromEntries(h.map((k,j)=>[k,a[j]]))});
}
function run(rows,manifest){
 must(rows.length===1080,"SOURCE_ROW_COUNT");
 const seen=new Set(),counts=new Map(),groups=new Map();
 for(const r of rows){
  const id=r.case+"|"+r.channel;must(!seen.has(id),"DUPLICATE_CASE_CHANNEL");seen.add(id);
  must(/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(r.case),"BAD_CASE");
  must(/^[0-9a-f]{64}$/.test(r.outb_sha256),"BAD_OUTB_SHA");
  must(+r.n_samples===12001&&+r.t0_s===100&&+r.t1_s===700&&+r.dt_s===0.05,"BAD_TIME_GRID");
  const d=+r.DEL_m4_Nref600;must(Number.isFinite(d)&&d>0,"BAD_DEL");
  counts.set(r.case,(counts.get(r.case)||0)+1);
  if(channels.includes(r.channel)){
   must(r.unit==="(kN-m)","BAD_MOMENT_UNIT");
   const key=r.case.replace(/_S0[1-6]$/,"")+"|"+r.channel;
   if(!groups.has(key))groups.set(key,[]);
   groups.get(key).push({seed:r.case.slice(-3),value:d});
  }
 }
 must(counts.size===18&&[...counts.values()].every(n=>n===60),"INCOMPLETE_CASES");
 const ts=manifest.filter(z=>z.section==="turbSim-36");
 const idx=new Map();for(const z of ts){must(!idx.has(z.relative_path),"DUPLICATE_MANIFEST");idx.set(z.relative_path,z)}
 const bts=ts.filter(z=>/^inputs\/U.*\.bts$/.test(z.relative_path));
 must(bts.length===36,"BTS_CASE_COUNT");
 let available=0,deferred=0;
 for(const z of bts){
  if(z.status==="included"&&z.canonical_archive&&/^[a-f0-9]{64}$/i.test(z.sha256))available++;
  else if(z.status==="prior-size-deferral-cancelled-see-transfer-ledger"&&!z.archive&&!z.sha256)deferred++;
  else throw Error("UNEXPECTED_BTS_SOURCE_STATE_"+z.relative_path);
  const stem=z.relative_path.slice(0,-4);
  for(const ext of ["inp","sum","dat"]){const x=idx.get(stem+"."+ext);must(x&&x.status==="included"&&x.canonical_archive&&/^[a-f0-9]{64}$/i.test(x.sha256),"MISSING_AUX_"+stem+"."+ext)}
 }
 const out=["wind_case,channel,seed_count,mean_DEL_m4_Nref600_kNm,sample_sd_kNm,CV_percent,min_kNm,max_kNm,max_min_ratio,min_seed,max_seed,source_csv_sha256"];
 for(const w of bins)for(const c of channels){
  const a=groups.get(w+"|"+c);
  must(a&&a.length===6&&a.map(x=>x.seed).sort().join(",")==="S01,S02,S03,S04,S05,S06","BAD_SEED_COVERAGE_"+w+"_"+c);
  const mean=a.reduce((s,x)=>s+x.value,0)/6;
  const sd=Math.sqrt(a.reduce((s,x)=>s+(x.value-mean)**2,0)/5);
  const lo=a.reduce((p,x)=>x.value<p.value?x:p),hi=a.reduce((p,x)=>x.value>p.value?x:p);
  out.push([w,c,6,mean.toFixed(9),sd.toFixed(9),(100*sd/mean).toFixed(6),lo.value.toFixed(9),hi.value.toFixed(9),(hi.value/lo.value).toFixed(9),lo.seed,hi.seed,SRC].join(","));
 }
 must(groups.size===30&&out.length===31,"OUTPUT_COVERAGE");
 return {csv:out.join("\n")+"\n",summary:{source_rows:1080,ntm_cases:18,groups:30,original_bts_available:available,original_bts_deferred:deferred,auxiliary_inp_sum_dat:108,physical_pass:false}};
}
function test(){
 const x=[1,2,3,4,5,6],m=x.reduce((a,b)=>a+b)/6;
 must(m===3.5&&Math.abs(Math.sqrt(x.reduce((a,b)=>a+(b-m)**2,0)/5)-Math.sqrt(3.5))<1e-12,"SD_TEST");
 for(const t of ["case,case\nA,B\n","case,channel\nA\n"]){let failed=false;try{parse(t)}catch{failed=true}must(failed,"NEGATIVE_HEADER_TEST")}
 console.log("SELFTEST_PASS sample_SD_and_invalid_CSV");
}
function main(){
 if(process.argv.includes("--self-test"))return test();
 const a=process.argv.slice(2),o={};for(let i=0;i<a.length;i+=2)o[a[i]]=a[i+1];
 for(const k of ["--source","--manifest","--out"])must(o[k],"MISSING_ARG_"+k);
 const src=fs.readFileSync(o["--source"]),man=fs.readFileSync(o["--manifest"]);
 must(sha(src)===SRC,"CSV_SHA256_MISMATCH");must(sha(man)===MAN,"MANIFEST_SHA256_MISMATCH");
 const r=run(parse(src.toString("utf8")),JSON.parse(man.toString("utf8")));
 fs.writeFileSync(o["--out"],r.csv);
 console.log(JSON.stringify({...r.summary,source_sha256:SRC,manifest_sha256:MAN,output_sha256:sha(Buffer.from(r.csv))}));
}
if(require.main===module)main();
