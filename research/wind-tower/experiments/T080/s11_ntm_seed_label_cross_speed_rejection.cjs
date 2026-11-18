#!/usr/bin/env node
'use strict';
// S11 diagnostic: cross-speed seed-index transfer is NOT a physical paired-seed test.
// Usage: node s11_ntm_seed_label_cross_speed_rejection.cjs [source.csv]
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const file=process.argv[2]||path.join(__dirname,'../T062/recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv');
function evaluate(csv){
 const lines=csv.trim().split(/\r?\n/), h=lines.shift().split(',');
 for(const col of ['case_id','channel','DEL']) assert(h.includes(col),'missing '+col);
 const idx=Object.fromEntries(h.map((k,i)=>[k,i]));
 const data=lines.map(l=>{const v=l.split(','),id=v[idx.case_id],m=id.match(/^(U[^_]+)_NTM_S(\d\d)$/);return m?{speed:m[1],seed:+m[2],ch:v[idx.channel],d:+v[idx.DEL]}:null}).filter(Boolean);
 assert.equal(data.length,36,'expect 18 NTM cases times 2 channels');
 const result=[];
 for(const ch of ['TwrBsMxt','TwrBsMyt']){
  const subset=data.filter(x=>x.ch===ch), speeds=[...new Set(subset.map(x=>x.speed))].sort();
  assert.equal(speeds.length,3);
  for(const hold of speeds){
   const train=subset.filter(x=>x.speed!==hold),test=subset.filter(x=>x.speed===hold);
   for(const rows of [train,test])for(let s=1;s<=6;s++)assert.equal(rows.filter(x=>x.seed===s).length,rows===train?2:1,'seed coverage');
   const score=Array.from({length:6},(_,i)=>({seed:i+1,v:train.filter(x=>x.seed===i+1).reduce((a,x)=>a+x.d**4,0)/2}));
   assert(score.every(x=>Number.isFinite(x.v)&&x.v>0));
   score.sort((a,b)=>b.v-a.v||a.seed-b.seed);
   test.sort((a,b)=>b.d-a.d||a.seed-b.seed);
   const top=score[0].seed,ratio=test.find(x=>x.seed===top).d/test[0].d;
   const order=score.map(x=>x.seed),tOrder=test.map(x=>x.seed);
   const rho=1-6*order.reduce((s,v,i)=>s+(i-tOrder.indexOf(v))**2,0)/(6*(36-1));
   result.push({channel:ch,holdout_speed:hold,train_top_seed:top,test_top_seed:test[0].seed,peak_capture:ratio,spearman:rho});
  }
 }
 return result;
}
if(require.main===module){
 assert.throws(()=>evaluate('case_id,channel,DEL\ninvalid,TwrBsMxt,1'),/expect 18/);
 const rows=evaluate(fs.readFileSync(file,'utf8'));
 assert.equal(rows.length,6);
 assert(rows.some(r=>r.peak_capture<1),'reject universal peak capture');
 for(const r of rows)console.log([r.channel,r.holdout_speed,r.train_top_seed,r.test_top_seed,r.peak_capture.toFixed(9),r.spearman.toFixed(9)].join(','));
}
module.exports={evaluate};
