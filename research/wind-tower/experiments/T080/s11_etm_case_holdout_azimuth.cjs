#!/usr/bin/env node
// Source-level, no simulation: leave-one-ETM-case-out azimuth screening.
// Usage: node s11_etm_case_holdout_azimuth.cjs <T077-1984-row-CSV>
const fs = require('node:fs');
const assert = require('node:assert/strict');
if (process.argv.length !== 3) throw Error('Usage: node script.cjs <source.csv>');
const lines = fs.readFileSync(process.argv[2], 'utf8').trim().split(/\r?\n/);
const header = lines.shift().split(',');
const need = ['case','segment','azimuth_deg','sigma_mean_MPa','sigma_max_MPa','DEL_m4_MPa'];
for (const col of need) assert(header.includes(col), 'missing '+col);
const rows = lines.map(line => {
  const fields = line.split(',');
  assert.equal(fields.length,header.length,'bad row width');
  const row=Object.fromEntries(header.map((k,i)=>[k,fields[i]]));
  for (const k of need.slice(2)) { row[k]=Number(row[k]); assert(Number.isFinite(row[k]),'nonfinite '+k); }
  return row;
});
const cases=[...new Set(rows.map(x=>x.case))].sort();
const segs=[...new Set(rows.map(x=>x.segment))].sort();
const az=[...new Set(rows.map(x=>x.azimuth_deg))].sort((a,b)=>a-b);
assert.equal(cases.length,4);assert.equal(segs.length,31);assert.equal(az.length,16);
assert.equal(rows.length,1984);
const lookup=new Map(rows.map(x=>[`${x.case}|${x.segment}|${x.azimuth_deg}`,x]));
assert.equal(lookup.size,rows.length,'duplicate case-segment-angle');
for(const c of cases)for(const s of segs)for(const a of az)
  assert(lookup.has(`${c}|${s}|${a}`),'incomplete grid');
const result=[];
for(const metric of ['DEL_m4_MPa','sigma_max_MPa','sigma_mean_MPa']){
 for(const hold of cases){
  let hits=0,top2=0,sum=0,maxRegret=0,selected={};
  for(const s of segs){
   const test=az.map(a=>lookup.get(`${hold}|${s}|${a}`));
   const scores=az.map(a=>{
    let score=0;
    for(const train of cases.filter(c=>c!==hold)){
     const vals=az.map(t=>lookup.get(`${train}|${s}|${t}`)[metric]);
     const lo=Math.min(...vals),hi=Math.max(...vals);
     assert(hi>lo,'flat training angular response');
     score+=(lookup.get(`${train}|${s}|${a}`)[metric]-lo)/(hi-lo)/3;
    }
    return {a,score};
   }).sort((x,y)=>y.score-x.score||x.a-y.a);
   const best=Math.max(...test.map(x=>x[metric])),worst=Math.min(...test.map(x=>x[metric]));
   assert(best>worst,'flat test angular response');
   const actual=test.find(x=>x[metric]===best).azimuth_deg;
   const chosen=scores[0].a;
   hits+=Number(chosen===actual);
   top2+=Number(scores.slice(0,2).some(x=>x.a===actual));
   const regret=100*(best-lookup.get(`${hold}|${s}|${chosen}`)[metric])/(best-worst);
   sum+=regret;maxRegret=Math.max(maxRegret,regret);
   selected[chosen]=(selected[chosen]||0)+1;
  }
  result.push({metric,hold,hits,top2,mean_normalized_regret_pct:sum/31,max_normalized_regret_pct:maxRegret,selected});
 }
}
console.log(JSON.stringify({source_rows:rows.length,source_cases:cases,segments:segs.length,angles:az.length,results:result},null,2));
