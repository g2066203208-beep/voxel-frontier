#!/usr/bin/env node
// S11: pre-registered wind-speed-group blind prediction of the spatial maximum.
// INPUT: archived T077 1984-row synchronous gross-elastic nominal DEL4 CSV.
// No solver, no material Miner, no PT contribution. Held-out speed never enters training.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
function analyze(csv) {
 const [head,...lines]=csv.trim().split(/\r?\n/),cols=head.split(','),ix=k=>cols.indexOf(k);
 for(const k of ['case','segment','azimuth_deg','DEL_m4_MPa','stress_class'])assert(ix(k)>=0,k);
 const u=c=>c.startsWith('U09p343881_')?9.343881:c.startsWith('U11p4_')?11.4:c.startsWith('U19p202140_')?19.202140:NaN;
 const rows=lines.map(line=>{const v=line.split(',');return {c:v[ix('case')],s:v[ix('segment')],a:+v[ix('azimuth_deg')],y:+v[ix('DEL_m4_MPa')],cls:v[ix('stress_class')],u:u(v[ix('case')])};});
 assert.equal(rows.length,1984);assert(rows.every(x=>Number.isFinite(x.u)&&Number.isFinite(x.y)&&x.y>0&&x.cls==='SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE'));
 const classes=[...new Set(rows.map(x=>x.u))].sort((a,b)=>a-b);assert.deepEqual(classes,[9.343881,11.4,19.202140]);
 const result=classes.map(held=>{
  const train=rows.filter(x=>x.u!==held),test=rows.filter(x=>x.u===held),speeds=[...new Set(train.map(x=>x.u))].sort((a,b)=>a-b);
  const cells=new Map();for(const x of train){const k=[x.u,x.s,x.a].join('|');if(!cells.has(k))cells.set(k,[]);cells.get(k).push(x.y)}
  const mean=(u,s,a)=>{const z=cells.get([u,s,a].join('|'));assert(z&&z.length);return z.reduce((a,b)=>a+b,0)/z.length};
  const scored=test.map(x=>{const pred=mean(speeds[0],x.s,x.a)+(held-speeds[0])/(speeds[1]-speeds[0])*(mean(speeds[1],x.s,x.a)-mean(speeds[0],x.s,x.a));return {x,pred,under:x.y-pred}});
  assert.equal(scored.length,held===19.202140?992:496);
  const oracle=Math.max(...scored.map(z=>z.x.y)),winner=scored.reduce((a,b)=>b.pred>a.pred?b:a),worst=scored.reduce((a,b)=>b.under>a.under?b:a);
  return {held_speed_mps:held,held_n:scored.length,extrapolation:held<speeds[0]||held>speeds[1],underprediction_n:scored.filter(z=>z.under>0).length,max_underprediction_MPa:worst.under,max_underprediction_case:worst.x.c,max_underprediction_cell:worst.x.s+'|'+worst.x.a,max_relative_underprediction_pct:100*Math.max(...scored.map(z=>z.under/z.x.y)),oracle_MPa:oracle,predicted_champion_actual_MPa:winner.x.y,champion_capture_pct:100*winner.x.y/oracle};
 });
 const expected=[99.90551846496963,100,95.92014358158445];
 result.forEach((x,i)=>assert(Math.abs(x.champion_capture_pct-expected[i])<1e-7,'real-source regression mismatch'));
 assert.deepEqual(result.map(x=>x.extrapolation),[true,false,true]);
 assert(result[2].champion_capture_pct<96,'reject universal 99%-capture hypothesis');
 return {status:'REAL_ARCHIVE_SOURCE_LEVEL_PASS',rows:rows.length,classes,result};
}
if(require.main===module){assert.equal(process.argv.length,3,'CSV path required');console.log(JSON.stringify(analyze(fs.readFileSync(process.argv[2],'utf8')),null,2))}
module.exports={analyze};
