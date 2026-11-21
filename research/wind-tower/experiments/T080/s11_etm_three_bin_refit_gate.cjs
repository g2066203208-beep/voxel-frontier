#!/usr/bin/env node
'use strict';
// S11: three-bin leave-one-wind-bin-out sectionwise refit, archive-specific.
// Usage: node s11_etm_three_bin_refit_gate.cjs <T077 1984-row CSV>
const fs=require('node:fs'),assert=require('node:assert/strict');
const cases=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
const speed=[9.343881,11.4,19.202140,19.202140],bins=[[0],[1],[2,3]];
function analyze(csv){
 const lines=csv.trim().split(/\r?\n/),header=lines.shift().split(',');
 const idx=k=>{const i=header.indexOf(k);assert(i>=0,'missing '+k);return i;};
 const ci=idx('case'),si=idx('segment'),ai=idx('azimuth_deg'),yi=idx('DEL_m4_MPa'),ki=idx('stress_class');
 assert.equal(lines.length,1984,'row count');const seen=new Set(),peak=new Map();
 for(const line of lines){
  const v=line.split(','),c=v[ci],s=v[si],a=Number(v[ai]),y=Number(v[yi]);
  assert(cases.includes(c),'case');assert(/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(s),'segment');
  assert(Number.isFinite(a)&&a>=0&&a<360&&a%22.5===0,'azimuth');
  assert(Number.isFinite(y)&&y>0,'DEL4');
  assert.equal(v[ki],'SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE','class');
  const id=c+'|'+s+'|'+a;assert(!seen.has(id),'duplicate');seen.add(id);
  const key=c+'|'+s;peak.set(key,Math.max(peak.get(key)||0,y));
 }
 assert.equal(seen.size,1984);assert.equal(peak.size,124);
 const result=bins.map((test,g)=>{
  let errN=[],errL=[],rejected=0,negative=0;
  for(let k=1;k<=31;k++){
   const s='CSEG_'+String(k).padStart(2,'0');
   const train=bins.filter((_,j)=>j!==g).map(ids=>({x:speed[ids[0]],y:ids.reduce((a,i)=>a+peak.get(cases[i]+'|'+s),0)/ids.length})).sort((a,b)=>a.x-b.x);
   assert.equal(train.length,2);const x=speed[test[0]];
   const near=train.reduce((a,b)=>Math.abs(a.x-x)<=Math.abs(b.x-x)?a:b).y;
   const linear=train[0].y+(x-train[0].x)*(train[1].y-train[0].y)/(train[1].x-train[0].x);
   if(x<train[0].x||x>train[1].x)rejected++;
   if(linear<=0)negative++;
   for(const i of test){const actual=peak.get(cases[i]+'|'+s);errN.push(near-actual);errL.push(linear-actual);}
  }
  const rmse=e=>Math.sqrt(e.reduce((a,v)=>a+v*v,0)/e.length);
  const mae=e=>e.reduce((a,v)=>a+Math.abs(v),0)/e.length;
  return {held_out_bin:g,n:errN.length,nearest_rmse_MPa:rmse(errN),linear_rmse_MPa:rmse(errL),nearest_mae_MPa:mae(errN),linear_mae_MPa:mae(errL),outside_training_hull_sections:rejected,nonpositive_linear_sections:negative,admission:rejected?'REJECT_EXTRAPOLATION':'INTERPOLATION_DIAGNOSTIC_ONLY'};
 });
 assert.deepEqual(result.map(x=>x.n),[31,31,62]);
 assert.deepEqual(result.map(x=>x.outside_training_hull_sections),[31,0,31]);
 assert(Math.abs(result[2].nearest_rmse_MPa-0.7968672476312398)<1e-9,'high-bin oracle');
 return {source_rows:1984,targets:124,results:result,limitations:'Four ETM realizations, three wind bins, correlated sections, unpaired seeds, no design variation. In-hull does not imply physical validation or calibrated uncertainty.'};
}
if(require.main===module){
 assert.equal(process.argv.length,3,'CSV argument required');
 const csv=fs.readFileSync(process.argv[2],'utf8');
 const out=analyze(csv);
 assert.throws(()=>analyze(csv.replace('CSEG_01','CSEG_99')));
 assert.throws(()=>analyze(csv+'\n'+csv.trim().split(/\r?\n/)[1]));
 assert.throws(()=>analyze(csv.replace('6.83617569974','NaN')));
 console.log(JSON.stringify(out,null,2));
}
module.exports={analyze};
