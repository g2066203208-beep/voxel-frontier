#!/usr/bin/env node
// Leakage-free wind-speed-group holdout of spatial control cells.
// Usage: node s11_speed_group_blind_topk_capture.cjs path/to/S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv
const fs=require('node:fs');
const assert=require('node:assert/strict');
const input=process.argv[2]; if(!input) throw Error('CSV path required');
const text=fs.readFileSync(input,'utf8').trim();
const [header,...lines]=text.split(/\r?\n/);
const fields=header.split(',');
for(const k of ['case','segment','azimuth_deg','DEL_m4_MPa','stress_class']) assert(fields.includes(k),k);
const ix=Object.fromEntries(fields.map((v,i)=>[v,i]));
const rows=lines.map(l=>{const a=l.split(',');return {case:a[ix.case],segment:a[ix.segment],azimuth:+a[ix.azimuth_deg],del:+a[ix.DEL_m4_MPa],cls:a[ix.stress_class]};});
assert.equal(rows.length,1984,'reject incomplete data');
assert(rows.every(x=>Number.isFinite(x.del)&&x.del>=0&&Number.isFinite(x.azimuth)&&x.cls==='SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE'),'invalid data');
const cases=[...new Set(rows.map(x=>x.case))];
assert.deepEqual(cases.sort(),['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06']);
const speed=c=>c.split('_')[0];
const speeds=[...new Set(cases.map(speed))].sort();
const cell=x=>x.segment+'|'+x.azimuth;
const allCells=new Set(rows.map(cell));assert.equal(allCells.size,496);
for(const c of cases){const subset=rows.filter(x=>x.case===c);assert.equal(subset.length,496);assert.equal(new Set(subset.map(cell)).size,496);}
const ks=[1,3,5,10,25];
const results=[];
for(const held of speeds){
 const training=rows.filter(x=>speed(x.case)!==held), testing=rows.filter(x=>speed(x.case)===held);
 const maxima=new Map();
 for(const x of training) maxima.set(cell(x),Math.max(maxima.get(cell(x))??-Infinity,x.del));
 const ranking=[...maxima].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).map(x=>x[0]);
 const oracle=Math.max(...testing.map(x=>x.del));
 for(const k of ks){const chosen=new Set(ranking.slice(0,k));const retained=Math.max(...testing.filter(x=>chosen.has(cell(x))).map(x=>x.del));results.push({held,k,retained_MPa:retained,oracle_MPa:oracle,ratio:retained/oracle});}
}
assert.equal(results.length,15);
assert(results.every(x=>x.ratio<=1+1e-12));
assert(results.filter(x=>x.k===5).every(x=>Math.abs(x.ratio-1)<1e-12));
const r1=results.filter(x=>x.k===1).map(x=>x.ratio);
assert(r1.every(x=>x<1),'reject optimistic exact-max claim for single cell');
console.log(JSON.stringify({input,rows:rows.length,cases,speeds,results},null,2));
