#!/usr/bin/env node
'use strict';
// S06 source-level non-identifiability demonstration. No OpenFAST/CAE execution.
// Usage: node s06_w_inverse_nonidentifiability.cjs path/to/S06_W_CROSSSOURCE_ADMISSION_18CASE_20261114.csv
const fs=require('node:fs'),assert=require('node:assert/strict');
function parse(csv){
 const lines=csv.trim().split(/\r?\n/);const h=lines.shift().split(',');
 const need=['case','mean_base_Fz_kN','original_gages','isolated_external_wind_force','same_state_WE','native_31gage_600s'];
 for(const k of need)assert(h.includes(k),'missing column '+k);
 return lines.map((line,i)=>{const v=line.split(',');assert.equal(v.length,h.length,'CSV columns row '+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]))});
}
function evaluate(csv){
 const r=parse(csv);assert.equal(r.length,18,'expected 18 historical NTM cases');
 const f=r.map(x=>Number(x.mean_base_Fz_kN));
 assert(f.every(Number.isFinite),'nonfinite axial force');
 const mean=f.reduce((a,b)=>a+b,0)/f.length;
 const sd=Math.sqrt(f.reduce((a,b)=>a+(b-mean)**2,0)/(f.length-1));
 const holds=['isolated_external_wind_force','same_state_WE','native_31gage_600s'];
 const nHold=Object.fromEntries(holds.map(k=>[k,r.filter(x=>x[k]==='HOLD').length]));
 // The same measured resultant y admits infinitely many (external, inertial) decompositions:
 // y=a+i=(a+delta)+(i-delta), with delta arbitrary.
 const y=100, a1=20,i1=80,delta=35,a2=a1+delta,i2=i1-delta;
 assert.equal(a1+i1,y);assert.equal(a2+i2,y);assert.notEqual(a1,a2);
 return {n:r.length,mean_base_Fz_kN:mean,sample_sd_kN:sd,
  min_kN:Math.min(...f),max_kN:Math.max(...f),
  nine_gage_cases:r.filter(x=>x.original_gages==='9').length,
  hold_counts:nHold,identifiability_counterexample:{resultant:y,external_1:a1,inertial_1:i1,external_2:a2,inertial_2:i2},
  admissible_W:false};
}
function selftest(){
 const hdr='case,mean_base_Fz_kN,original_gages,isolated_external_wind_force,same_state_WE,native_31gage_600s';
 const one='X,-100,9,HOLD,HOLD,HOLD';
 assert.throws(()=>evaluate(hdr+'\n'+one),/18/);
 assert.throws(()=>parse('case\nX'),/missing column/);
 const arr=Array.from({length:18},(_,i)=>'X'+i+','+(-100+i)+',9,HOLD,HOLD,HOLD');
 const result=evaluate(hdr+'\n'+arr.join('\n'));
 assert.equal(result.n,18);assert.equal(result.admissible_W,false);
 assert.equal(result.hold_counts.isolated_external_wind_force,18);
 return true;
}
if(require.main===module){selftest();if(process.argv[2])console.log(JSON.stringify(evaluate(fs.readFileSync(process.argv[2],'utf8')),null,2));else console.log('selftest PASS; supply archived CSV for source-level report');}
module.exports={parse,evaluate,selftest};
