"use strict";
// S10 source-level PREPARATION, no solver: seed dependence among neighboring
// nine-gage historical OpenFAST INTERNAL load DEL channels, not material fatigue.
const SRC="95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f";
const WINDS=["U09p343881_NTM","U11p4_NTM","U19p202140_NTM"];
const COMPONENTS=["Fx","Fy","Fz","Mx","My","Mz"];
const SEEDS=["S01","S02","S03","S04","S05","S06"];
function check(x,s){if(!x)throw Error(s);}
function parse(csv){
 const lines=csv.trimEnd().split(/\r?\n/),h=lines.shift().split(",");
 check(new Set(h).size===h.length,"DUPLICATE_HEADER");
 for(const k of ["case","channel","unit","outb_sha256","n_samples","t0_s","t1_s","dt_s","DEL_m4_Nref600","DEL_m10_Nref600"])check(h.includes(k),"MISSING_"+k);
 return lines.map((line,i)=>{const v=line.split(",");check(v.length===h.length,"ROW_WIDTH_"+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]));});
}
function ch(g,c){return g===0?"TwrBs"+c+"t":"TwHt"+g+(c[0]==="F"?"FL":"ML")+c[1].toLowerCase()+"t";}
function corr(a,b){
 check(a.length===6&&b.length===6&&a.every(Number.isFinite)&&b.every(Number.isFinite),"BAD_VECTOR");
 const x=a.reduce((s,v)=>s+v,0)/6,y=b.reduce((s,v)=>s+v,0)/6;
 let xy=0,xx=0,yy=0;
 for(let i=0;i<6;i++){const p=a[i]-x,q=b[i]-y;xy+=p*q;xx+=p*p;yy+=q*q;}
 check(xx>0&&yy>0,"ZERO_VARIANCE");
 const r=xy/Math.sqrt(xx*yy);check(Number.isFinite(r)&&Math.abs(r)<1+1e-12,"BAD_CORRELATION");
 return Math.max(-1,Math.min(1,r));
}
function analyze(csv,receipt){
 check(receipt.result_sha256===SRC&&receipt.result_rows===1080&&receipt.original_outb_count===18,"BAD_RECEIPT");
 const hashes=new Map(receipt.sources.map(x=>[x.case,x.outb_sha256]));
 check(hashes.size===18,"BAD_RECEIPT_SOURCES");
 const rows=parse(csv);check(rows.length===1080,"ROW_COUNT");
 const data=new Map(),counts=new Map(),names=new Map();
 for(const c of COMPONENTS)for(let g=0;g<10;g++)names.set(ch(g,c),c);
 check(names.size===60,"CHANNEL_NAMES");
 for(const r of rows){
  check(/^(U(?:09p343881|11p4|19p202140)_NTM)_S0[1-6]$/.test(r.case),"BAD_CASE");
  check(hashes.get(r.case)===r.outb_sha256,"OUTB_SHA_MISMATCH");
  check(r.n_samples==="12001"&&r.t0_s==="100"&&r.t1_s==="700"&&r.dt_s==="0.05","TIME_GRID");
  const c=names.get(r.channel);check(c,"BAD_CHANNEL");
  check(r.unit===(c[0]==="F"?"(kN)":"(kN-m)"),"BAD_UNIT");
  for(const m of [4,10])check(Number.isFinite(+r["DEL_m"+m+"_Nref600"])&&+r["DEL_m"+m+"_Nref600"]>0,"BAD_DEL");
  const key=r.case+"|"+r.channel;check(!data.has(key),"DUPLICATE");data.set(key,r);
  counts.set(r.case,(counts.get(r.case)||0)+1);
 }
 check(counts.size===18&&[...counts.values()].every(x=>x===60),"INCOMPLETE_COVERAGE");
 const table=["wind_case,m,component,adjacent_pairs,minimum_pearson,median_pearson,maximum_pearson,adjacent_pairs_r_gt_0p99,worst_pair,source_csv_sha256"];
 const all=[];let worst=null;
 for(const w of WINDS)for(const m of [4,10])for(const c of COMPONENTS){
  const vec=Array.from({length:10},(_,g)=>SEEDS.map(seed=>+data.get(w+"_"+seed+"|"+ch(g,c))["DEL_m"+m+"_Nref600"]));
  const rs=Array.from({length:9},(_,g)=>corr(vec[g],vec[g+1]));
  const sorted=[...rs].sort((a,b)=>a-b),min=sorted[0],idx=rs.indexOf(min);
  const item={wind:w,m,component:c,min,median:sorted[4],max:sorted[8],worst_pair:ch(idx,c)+"__"+ch(idx+1,c)};
  if(!worst||min<worst.min)worst=item;
  all.push(...rs);
  table.push([w,m,c,9,min.toFixed(12),sorted[4].toFixed(12),sorted[8].toFixed(12),rs.filter(r=>r>0.99).length,item.worst_pair,SRC].join(","));
 }
 check(table.length===37&&all.length===324,"OUTPUT_COUNT");
 const sorted=[...all].sort((a,b)=>a-b);
 return {csv:table.join("\n")+"\n",summary:{source_rows:1080,outb_sources:18,wind_bins:3,seeds_per_bin:6,channels_per_seed:60,groups:36,adjacent_correlations:324,r_gt_0p99:all.filter(r=>r>0.99).length,min_r:sorted[0],median_r:(sorted[161]+sorted[162])/2,max_r:sorted[323],worst,physical_pass:false,material_fatigue_pass:false}};
}
function test(csv,receipt){
 check(Math.abs(corr([1,2,3,4,5,6],[2,4,6,8,10,12])-1)<1e-14,"ORACLE_POS");
 check(Math.abs(corr([1,2,3,4,5,6],[6,5,4,3,2,1])+1)<1e-14,"ORACLE_NEG");
 let rejected=0;
 try{corr([1,1,1,1,1,1],[1,2,3,4,5,6]);}catch{rejected++;}
 const mutants=[
  csv.replace("12001,100,700,0.05","12001,100,700,0.06"),
  csv.replace("DEL_m4_Nref600","BROKEN_M4"),
  csv.replace("454.096679522","NaN"),
  csv.replace("f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf","0".repeat(64))
 ];
 for(const bad of mutants){try{analyze(bad,receipt);}catch{rejected++;}}
 try{analyze(csv,{...receipt,original_outb_count:17});}catch{rejected++;}
 check(rejected===6,"NEGATIVE_REJECTION_FAILURE_"+rejected);
 return {synthetic_positive:2,negative_rejections:rejected};
}
module.exports={analyze,test,corr};
if(require.main===module){
 const fs=require("node:fs"),crypto=require("node:crypto"),a=process.argv.slice(2),opt={};
 for(let i=0;i<a.length;i+=2)opt[a[i]]=a[i+1];
 for(const k of ["--source","--receipt","--out"])check(opt[k],"MISSING_ARG_"+k);
 const bytes=fs.readFileSync(opt["--source"]);
 check(crypto.createHash("sha256").update(bytes).digest("hex")===SRC,"SOURCE_SHA256");
 const csv=bytes.toString("utf8"),receipt=JSON.parse(fs.readFileSync(opt["--receipt"],"utf8"));
 const tests=test(csv,receipt),res=analyze(csv,receipt);
 fs.writeFileSync(opt["--out"],res.csv);
 console.log(JSON.stringify({...res.summary,...tests,output_sha256:crypto.createHash("sha256").update(res.csv).digest("hex")}));
}
