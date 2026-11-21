#!/usr/bin/env node
'use strict';
// S11: falsification of monotone wind-speed DEL4 ordering, based on archived
// 4 ETM cases x 31 sections x 16 azimuths (not material stress or a DLC1.2 test).
// node s11_etm_speed_monotonicity_rejection.cjs <T077 1984-row CSV>
const fs=require('node:fs'),assert=require('node:assert/strict');
const ids=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
function analyze(csv){
 const lines=csv.trim().split(/\r?\n/),head=lines.shift().split(',');
 const col=k=>{const i=head.indexOf(k);assert(i>=0,'missing '+k);return i;};
 const ic=col('case'),is=col('segment'),ia=col('azimuth_deg'),iy=col('DEL_m4_MPa'),ik=col('stress_class');
 assert.equal(lines.length,1984,'unexpected source row count');
 const seen=new Set(),peaks=new Map();
 for(const line of lines){
  const v=line.split(','),c=v[ic],s=v[is],a=Number(v[ia]),y=Number(v[iy]);
  assert(ids.includes(c),'unknown case');assert(/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(s),'segment');
  assert(Number.isFinite(a)&&a>=0&&a<360&&a%22.5===0,'azimuth');
  assert(Number.isFinite(y)&&y>0,'DEL4');
  assert.equal(v[ik],'SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE');
  const key=c+'|'+s+'|'+a;assert(!seen.has(key),'duplicate cell');seen.add(key);
  const k=c+'|'+s;peaks.set(k,Math.max(peaks.get(k)||0,y));
 }
 assert.equal(seen.size,1984);assert.equal(peaks.size,124);
 const pairs=[[0,1],[1,2],[1,3],[0,2],[2,3]];
 const result=pairs.map(([i,j])=>{
  const low=ids[i],high=ids[j],dif=[];
  for(let n=1;n<=31;n++){const s='CSEG_'+String(n).padStart(2,'0');dif.push(peaks.get(high+'|'+s)-peaks.get(low+'|'+s));}
  return {low,high,n:31,increases:dif.filter(d=>d>0).length,decreases:dif.filter(d=>d<0).length,
   min_difference_MPa:Math.min(...dif),max_difference_MPa:Math.max(...dif)};
 });
 assert.deepEqual(result.map(r=>[r.increases,r.decreases]),[[13,18],[0,31],[0,31],[0,31],[20,11]],'source regression');
 assert(Math.abs(result[1].max_difference_MPa+0.34681053433)<1e-9);
 return {status:'SOURCE_LEVEL_PASS',source_rows:1984,section_case_targets:124,azimuths_per_target:16,result,
  limitation:'ETM cases have different seeds; monotonicity rejection is archive-specific, not a controlled wind-speed causal experiment.'};
}
if(require.main===module){
 assert.equal(process.argv.length,3,'input CSV required');
 const csv=fs.readFileSync(process.argv[2],'utf8');
 const out=analyze(csv);
 const broken=csv.replace('6.83617569974','NaN');
 assert.throws(()=>analyze(broken),'reject nonfinite');
 assert.throws(()=>analyze(csv.replace('CSEG_01','CSEG_99')),'reject unknown segment');
 assert.throws(()=>analyze(csv+'\n'+csv.trim().split(/\r?\n/)[1]),'reject duplicate row');
 console.log(JSON.stringify(out,null,2));
}
module.exports={analyze};
