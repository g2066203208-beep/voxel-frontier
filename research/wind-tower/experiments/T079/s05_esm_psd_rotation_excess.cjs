#!/usr/bin/env node
'use strict';
// Source-level diagnostic only: no original accelerogram reprocessing or tower response.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const SOURCE=path.join(__dirname,'real-records/S05_ESM_NVL_PSA_PSD_46PERIOD_20261107.csv');
function compute(csv){
 const lines=csv.trim().split(/\r?\n/),h=lines.shift().split(',');
 const req=['period_s','RotD100_PSD_m','HNE_PSD_m','HNN_PSD_m','in_4_to_10_s'];
 for(const k of req)if(!h.includes(k))throw Error('missing column '+k);
 let prev=-Infinity,ans=[];
 for(const line of lines){const v=line.split(',');if(v.length!==h.length)throw Error('column count');const row=Object.fromEntries(h.map((k,i)=>[k,v[i]]));if(row.in_4_to_10_s!=='1')continue;
 const T=Number(row.period_s),r=Number(row.RotD100_PSD_m),e=Number(row.HNE_PSD_m),n=Number(row.HNN_PSD_m);
 if(![T,r,e,n].every(Number.isFinite)||T<=prev||T<4||T>10||Math.min(r,e,n)<=0)throw Error('invalid numeric/period');
 const m=Math.max(e,n);if(r<m-1e-10)throw Error('RotD100 below fixed axis');
 ans.push({T,r,m,excess:100*(r/m-1),axis:e>=n?'HNE':'HNN'});prev=T;
 }if(ans.length<2)throw Error('insufficient periods');return ans;
}
function tests(){
 const h='period_s,RotD100_PSD_m,HNE_PSD_m,HNN_PSD_m,in_4_to_10_s\n';
 assert.equal(compute(h+'4,2,1,1,1\n5,3,2,1,1').length,2);
 for(const x of ['4,0.5,1,1,1\n5,2,1,1,1','4,2,1,1,1\n3,2,1,1,1','4,NaN,1,1,1\n5,2,1,1,1','4,2,1,1,1\n4,2,1,1,1'])assert.throws(()=>compute(h+x));
}
tests();
const a=compute(fs.readFileSync(SOURCE,'utf8'));
const header='period_s,RotD100_PSD_m,largest_fixed_axis_PSD_m,rotation_excess_pct,dominant_axis';
const lines=[header,...a.map(x=>[x.T.toFixed(12),x.r.toFixed(14),x.m.toFixed(14),x.excess.toFixed(9),x.axis].join(','))];
process.stdout.write(lines.join('\n')+'\n');
process.stderr.write(JSON.stringify({n:a.length,max_excess_pct:Math.max(...a.map(x=>x.excess)),min_excess_pct:Math.min(...a.map(x=>x.excess)),max_RotD100_PSD_m:Math.max(...a.map(x=>x.r))})+'\n');
