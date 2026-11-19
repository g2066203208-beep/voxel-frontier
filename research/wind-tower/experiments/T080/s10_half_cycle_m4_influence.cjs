#!/usr/bin/env node
'use strict';
// Independent source-level diagnostic, NOT a replacement rainflow method or material Miner result.
// Usage: node s10_half_cycle_m4_influence.cjs 03_RAINFLOW_CYCLE_LEDGER_RECOMPUTED.csv 05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const LEDGER_SHA256='067c60cea61b35398edd186ff509fe759d1c4420395f082d06c666d92d897ecb';
const H1='case_id,channel,source_column,range,mean,count,i_start,i_end';
const H2='case_id,channel,source_column,m,Neq,DEL,n_cycles_rows,cycle_count_sum,signal_min,signal_max,signal_mean,signal_std';
function analyze(ledger,del){
 const a=ledger.trimEnd().split(/\r?\n/),b=del.trimEnd().split(/\r?\n/);
 assert.equal(a[0],H1);assert.equal(b[0],H2);assert.equal(a.length-1,48070);assert.equal(b.length-1,72);
 const groups=new Map();
 for(let i=1;i<a.length;i++){
  const p=a[i].split(',');assert.equal(p.length,8);
  const key=p[0]+'|'+p[1],range=Number(p[3]),count=Number(p[5]);
  assert(Number.isFinite(range)&&range>=0&&[.5,1].includes(count));
  const g=groups.get(key)||{rows:0,halves:0,cycles:0,energy:0,halfEnergy:0};
  const e=count*range**4;g.rows++;g.cycles+=count;g.energy+=e;
  if(count===.5){g.halves++;g.halfEnergy+=e;}groups.set(key,g);
 }
 assert.equal(groups.size,72);
 const out=[];
 for(let i=1;i<b.length;i++){
  const p=b[i].split(','),g=groups.get(p[0]+'|'+p[1]);assert(g);
  assert.equal(Number(p[3]),4);assert.equal(Number(p[4]),100000);
  assert.equal(g.rows,Number(p[6]));assert(Math.abs(g.cycles-Number(p[7]))<1e-8);
  const reconstructed=(g.energy/100000)**.25;
  assert(Math.abs(reconstructed-Number(p[5]))<1e-7,'DEL mismatch '+p[0]+' '+p[1]);
  out.push({case_id:p[0],channel:p[1],rows:g.rows,half_rows:g.halves,half_m4_share:g.halfEnergy/g.energy,del4:reconstructed,full_only_counterfactual_del4:((g.energy-g.halfEnergy)/100000)**.25});
 }
 return out;
}
function median(a){const x=a.slice().sort((p,q)=>p-q);return(x[x.length/2-1]+x[x.length/2])/2;}
function summary(out){
 const groups={};for(const ch of ['TwrBsMxt','TwrBsMyt']){
  const x=out.filter(z=>z.channel===ch).map(z=>z.half_m4_share);
  groups[ch]={median:median(x),min:Math.min(...x),max:Math.max(...x),above_half:x.filter(v=>v>.5).length};
 }
 return {rows:out.reduce((s,x)=>s+x.rows,0),half_rows:out.reduce((s,x)=>s+x.half_rows,0),groups:out.length,channels:groups,worst:out.reduce((a,b)=>b.half_m4_share>a.half_m4_share?b:a)};
}
function selftest(){
 assert.equal(median([1,4,2,3]),2.5);
 const e=.5*2**4+1*1**4;assert.equal((.5*2**4)/e,8/9);
 assert.throws(()=>analyze(H1+'\ninvalid',H2),/48070/);
}
if(require.main===module){
 selftest();assert.equal(process.argv.length,4,'usage: node script ledger.csv del.csv');
 const bytes=fs.readFileSync(process.argv[2]);
 assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),LEDGER_SHA256,'ledger SHA256 mismatch');
 const out=analyze(bytes.toString('utf8'),fs.readFileSync(process.argv[3],'utf8'));
 console.log(JSON.stringify({source_sha256:LEDGER_SHA256,summary:summary(out),cases:out},null,2));
}
module.exports={analyze,summary,selftest};
