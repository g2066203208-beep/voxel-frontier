#!/usr/bin/env node
'use strict';
// S11: whole-wind-speed-group holdout on observed NTM DEL4 fourth moments.
// No Abaqus/CAE, no OpenFAST production runs, no seed-ID-as-physics shortcut.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const source=process.argv[2]||path.resolve(__dirname,'../T062/recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv');
const lines=fs.readFileSync(source,'utf8').trim().split(/\r?\n/);
const head=lines.shift().split(',');
const col=n=>{const i=head.indexOf(n);assert(i>=0,n);return i};
const ci=col('case_id'),ch=col('channel'),di=col('DEL'),mi=col('m'),ni=col('Neq');
assert.equal(lines.length,72,'72 historical case-channel rows required');
const g=new Map();
for(const line of lines){
 const a=line.split(','),m=/^U(\d+)p(\d+)_(NTM|ETM)_S(\d+)$/.exec(a[ci]);
 assert(m,'unexpected case ID');
 if(m[3]!=='NTM')continue;
 assert.equal(Number(a[mi]),4);assert.equal(Number(a[ni]),100000);
 const u=Number(m[1]+'.'+m[2]),d=Number(a[di]);assert(Number.isFinite(d)&&d>0);
 const key=a[ch]+'|'+u;if(!g.has(key))g.set(key,[]);
 g.get(key).push({seed:m[4],del:d});
}
assert.equal(g.size,6);
const results=[];
for(const channel of ['TwrBsMxt','TwrBsMyt']){
 const pts=[...g].filter(([k])=>k.startsWith(channel+'|')).map(([k,ds])=>{
  assert.equal(ds.length,6);assert.equal(new Set(ds.map(x=>x.seed)).size,6);
  return {u:Number(k.split('|')[1]),y:(ds.reduce((s,x)=>s+x.del**4,0)/6)**.25};
 }).sort((a,b)=>a.u-b.u);
 assert.equal(pts.length,3);
 for(let i=0;i<3;i++){
  const test=pts[i],train=pts.filter((_,j)=>i!==j),[a,b]=train;
  const t=(test.u-a.u)/(b.u-a.u);
  const linear=a.y+t*(b.y-a.y);
  const loglinear=Math.exp(Math.log(a.y)+t*(Math.log(b.y)-Math.log(a.y)));
  const mean=(a.y+b.y)/2;
  assert([linear,loglinear,mean].every(x=>Number.isFinite(x)&&x>0));
  results.push({channel,held_out_speed_mps:test.u,actual_del4_kNm:test.y,
   linear_del4_kNm:linear,linear_signed_pct:100*(linear/test.y-1),
   loglinear_del4_kNm:loglinear,loglinear_signed_pct:100*(loglinear/test.y-1),
   constant_mean_del4_kNm:mean,constant_mean_signed_pct:100*(mean/test.y-1),
   extrapolation:i!==1});
 }
}
assert.equal(results.length,6);
const m=results.find(r=>r.channel==='TwrBsMyt'&&r.held_out_speed_mps===19.20214);
assert(m.linear_signed_pct>70&&m.loglinear_signed_pct>140,'high-speed My extrapolation rejection');
const x=results.find(r=>r.channel==='TwrBsMxt'&&r.held_out_speed_mps===11.4);
assert(Math.abs(x.loglinear_signed_pct)<2,'middle-speed Mx interpolation control');
console.log(JSON.stringify({source,ntm_case_channel_rows:36,folds:results},null,2));
