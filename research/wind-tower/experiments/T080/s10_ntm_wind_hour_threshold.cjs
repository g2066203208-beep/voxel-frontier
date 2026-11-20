#!/usr/bin/env node
'use strict';
// S10 source-level threshold analysis. Usage: node s10_ntm_wind_hour_threshold.cjs path/to/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv
const fs=require('node:fs');
const assert=require('node:assert/strict');
const H=[5736,1426,2], B=['09p343881','11p4','19p202140'];
function analyze(csv){
 const lines=csv.trim().split(/\r?\n/), hdr=lines.shift().split(',');
 const idx=Object.fromEntries(hdr.map((v,i)=>[v,i]));
 for(const key of ['case_id','channel','DEL','m','Neq'])if(!(key in idx))throw Error('MISSING_COLUMN '+key);
 if(lines.length!==72)throw Error('EXPECTED_72_ROWS');
 const rows=lines.map(l=>{const a=l.split(',');return {id:a[idx.case_id],ch:a[idx.channel],del:Number(a[idx.DEL]),m:Number(a[idx.m]),neq:Number(a[idx.Neq])}});
 if(rows.some(x=>!Number.isFinite(x.del)||x.del<0||x.m!==4||x.neq!==100000))throw Error('INVALID_DEL_METADATA');
 const out={};
 for(const ch of ['TwrBsMxt','TwrBsMyt']){
   const A=B.map(b=>{const v=rows.filter(r=>r.id.startsWith('U'+b+'_NTM_S')&&r.ch===ch);if(v.length!==6||new Set(v.map(r=>r.id)).size!==6)throw Error('INVALID_SIX_SEEDS '+b);return v.reduce((s,r)=>s+r.del**4,0)/6});
   const baseline=H[0]*A[0]+H[1]*A[1];
   const threshold=p=>p*baseline/((1-p)*A[2]);
   const share=h=>h*A[2]/(baseline+h*A[2]);
   out[ch]={conditional_hour_counts:H,mean_del4:A,observed_high_share:share(2),continuous_h_at_5pct:threshold(.05),minimum_integer_h_at_least_5pct:Math.ceil(threshold(.05)),h_at_50pct:threshold(.5),h_equal_middle:H[1]*A[1]/A[2],shares_at_1_2_3_4_hours:[1,2,3,4].map(share)};
   assert(Math.abs(share(threshold(.05))-.05)<1e-12);
   assert(Math.abs(share(threshold(.5))-.5)<1e-12);
   assert(share(3)>share(2)&&share(4)>share(3));
 }
 return out;
}
if(require.main===module){
 if(process.argv.includes('--selftest')){
   assert.throws(()=>analyze('case_id,channel,DEL,m,Neq\nx,y,1,4,100000'),/EXPECTED_72_ROWS/);
   assert.throws(()=>analyze('a,b,c\n1,2,3'),/MISSING_COLUMN/);
   console.log('S10_THRESHOLD_SELFTEST_PASS');
 }else if(process.argv.length!==3){console.error('Usage: node s10_ntm_wind_hour_threshold.cjs <72-row-source.csv>');process.exit(2)}
 else console.log(JSON.stringify(analyze(fs.readFileSync(process.argv[2],'utf8')),null,2));
}
module.exports={analyze};
