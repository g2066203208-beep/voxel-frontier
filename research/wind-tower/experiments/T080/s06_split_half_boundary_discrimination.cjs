#!/usr/bin/env node
// S06/S10 retrospective split-half vs boundary accounting; historical summaries only.
// Usage: node s06_split_half_boundary_discrimination.cjs [source.csv]
const fs=require('node:fs'),assert=require('node:assert/strict');
const path=process.argv[2]||'research/wind-tower/experiments/T077/recovery/S06_S10_4ETM_SPLIT_HALF_RAINFLOW_DEL_SUMMARY_20261105.csv';
function analyze(text){
 const rows=text.trim().split(/\r?\n/),keys=rows.shift().split(',');
 assert.equal(rows.length,48,'expected 4 cases x 6 channels x 2 exponents');
 const data=rows.map((line)=>{const v=line.split(',');assert.equal(v.length,keys.length);return Object.fromEntries(keys.map((k,i)=>[k,v[i]]));});
 const out={};
 for(const m of [4,10]){
  const r=data.filter(x=>Number(x.m)===m);assert.equal(r.length,24);
  const ratios=r.map(x=>{
   const h=Number(x.median_half_imbalance_pct),b=Number(x.max_boundary_gap_pct);
   assert.ok(Number.isFinite(h)&&Number.isFinite(b)&&h>=0&&b>0);
   return {case:x.case,channel:x.channel,ratio:h/b,half:h,boundary:b};
  }).sort((a,b)=>a.ratio-b.ratio);
  const count=ratios.filter(x=>x.ratio>1).length;
  out[m]={n:24,above:count,belowOrEqual:24-count,min:ratios[0],max:ratios[23],median:(ratios[11].ratio+ratios[12].ratio)/2,rows:ratios};
 }
 return out;
}
function selfTest(){
 assert.throws(()=>analyze('case,m\na,4'),/expected/);
 const t=fs.readFileSync(path,'utf8');const r=analyze(t);
 assert.equal(r[4].above,21);assert.equal(r[10].above,17);
 assert.equal(r[4].belowOrEqual,3);assert.equal(r[10].belowOrEqual,7);
 console.log(JSON.stringify({source:path,summary:{m4:{n:24,above:21,median:r[4].median,min:r[4].min,max:r[4].max},m10:{n:24,above:17,median:r[10].median,min:r[10].min,max:r[10].max}},tests:'PASS'},null,2));
}
selfTest();
