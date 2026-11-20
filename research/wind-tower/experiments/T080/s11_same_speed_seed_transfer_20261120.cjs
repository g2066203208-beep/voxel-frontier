#!/usr/bin/env node
// S11 independent same-wind-speed seed-to-seed peak-location transfer.
// INPUT: T077 archived 1984-row gross-elastic DEL4 CSV; NOT material Miner or DLC1.2.
// Compare S04->S06 and S06->S04 only at U=19.202140 m/s. No held-out values select the winner.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
function analyze(csv){
 const [header,...lines]=csv.trim().split(/\r?\n/),fields=header.split(','),idx=k=>fields.indexOf(k);
 for(const k of ['case','segment','azimuth_deg','DEL_m4_MPa','stress_class'])assert(idx(k)>=0,k);
 const rows=lines.map(line=>{const v=line.split(',');return {c:v[idx('case')],s:v[idx('segment')],a:+v[idx('azimuth_deg')],y:+v[idx('DEL_m4_MPa')],cls:v[idx('stress_class')]};});
 assert.equal(rows.length,1984);
 assert(rows.every(x=>Number.isFinite(x.y)&&x.y>=0&&x.cls==='SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE'));
 const cases=['U19p202140_ETM_S04','U19p202140_ETM_S06'];
 const result=cases.map(train=>{
  const test=cases.find(c=>c!==train),tr=rows.filter(x=>x.c===train),te=rows.filter(x=>x.c===test);
  assert.equal(tr.length,496);assert.equal(te.length,496);
  const key=x=>x.s+'|'+x.a,lookup=new Map(te.map(x=>[key(x),x]));
  assert.equal(lookup.size,496);assert.equal(new Set(tr.map(key)).size,496);
  const predictedChampion=tr.reduce((a,b)=>b.y>a.y?b:a),oracle=te.reduce((a,b)=>b.y>a.y?b:a),actual=lookup.get(key(predictedChampion));
  assert(actual);
  return {train,test,train_champion:key(predictedChampion),test_oracle:key(oracle),test_oracle_MPa:oracle.y,test_response_at_train_champion_MPa:actual.y,peak_capture_pct:100*actual.y/oracle.y,absolute_regret_MPa:oracle.y-actual.y};
 });
 assert(Math.abs(result[0].peak_capture_pct-99.87676254956055)<1e-7);
 assert(Math.abs(result[1].peak_capture_pct-99.87954711824388)<1e-7);
 assert(result.every(x=>x.peak_capture_pct<100&&x.peak_capture_pct>99));
 // Negative test: duplicated test cell must be rejected.
 function validateUnique(items){assert.equal(new Set(items.map(x=>x.s+'|'+x.a)).size,items.length)}
 const fixture=rows.filter(x=>x.c===cases[1]);assert.throws(()=>validateUnique([...fixture,fixture[0]]));
 return {status:'REAL_ARCHIVE_SOURCE_LEVEL_PASS',rows:rows.length,wind_speed_mps:19.202140,split:'paired same-speed seed leave-one-out (2 seeds only)',result,negative_test:'duplicate cell rejected',physical_pass:false};
}
if(require.main===module){assert.equal(process.argv.length,3,'CSV path required');console.log(JSON.stringify(analyze(fs.readFileSync(process.argv[2],'utf8')),null,2))}
module.exports={analyze};
