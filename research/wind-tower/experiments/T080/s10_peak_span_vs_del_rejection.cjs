#!/usr/bin/env node
'use strict';
// T062 original summary, non-Abaqus; source-level screening, not material fatigue.
const fs=require('node:fs'),assert=require('node:assert/strict');
const path=require('node:path');
const input=process.argv[2]||path.resolve(__dirname,'../T062/recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv');
const lines=fs.readFileSync(input,'utf8').trim().split(/\r?\n/);
const header=lines.shift().split(',');
const records=lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[header[i],v])));
assert.equal(records.length,72);
const result={};
for(const channel of ['TwrBsMxt','TwrBsMyt']){
 const a=records.filter(r=>r.channel===channel).map(r=>{
  const del=Number(r.DEL), n=Number(r.cycle_count_sum), span=Number(r.signal_max)-Number(r.signal_min), neq=Number(r.Neq),m=Number(r.m);
  assert.ok([del,n,span,neq,m].every(Number.isFinite)&&del>0&&n>0&&span>0&&neq===100000&&m===4);
  const bound=span*Math.pow(n/neq,1/m), ratio=del/bound;
  assert.ok(ratio<=1+1e-12,'PHYSICAL_RANGE_BOUND_VIOLATION');
  return {id:r.case_id,del,span,n,bound,ratio};
 });
 assert.equal(a.length,36);
 const ordered=a.map(x=>x.ratio).sort((x,y)=>x-y);
 let discordant=0;
 for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++)if((a[i].del-a[j].del)*(a[i].span-a[j].span)<0)discordant++;
 const top=(key)=>a.reduce((p,x)=>x[key]>p[key]?x:p);
 result[channel]={n:a.length,discordant,totalPairs:630,ratioMin:ordered[0],ratioMedian:(ordered[17]+ordered[18])/2,ratioMax:ordered[35],topDEL:top('del'),topSpan:top('span')};
}
assert.equal(result.TwrBsMxt.discordant,21);
assert.equal(result.TwrBsMyt.discordant,83);
if(process.argv.includes('--selftest')){
 const valid=(del,span,n)=>del<=span*Math.pow(n/100000,.25)+1e-12;
 assert.ok(valid(1,2,100000));
 assert.ok(!valid(3,2,100000));
 assert.ok(!Number.isFinite(Math.pow(-1,.25)));
}
console.log(JSON.stringify(result,null,2));
