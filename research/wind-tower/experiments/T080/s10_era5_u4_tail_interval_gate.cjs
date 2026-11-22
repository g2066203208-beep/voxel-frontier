#!/usr/bin/env node
'use strict';
// SOURCE: T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv
// Git blob 1bae743b385d4f24c8b5af3e0b445aae30d40c6f
// This is a mathematical U^4 exposure proxy, NEVER Miner damage or DLC1.2.
const fs=require('fs'),assert=require('assert'),path=require('path');
const csv=process.argv[2]||path.join(__dirname,'../T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv');
const lines=fs.readFileSync(csv,'utf8').trim().split(/\r?\n/);
assert(lines[0].startsWith('bin_lower_mps,bin_upper_mps_exclusive,hours,'));
const all=lines.slice(1).map(line=>{const a=line.split(',');return {j:Number(a[0]),upper:a[1],n:Number(a[2])};});
assert.strictEqual(all.length,31);
assert.strictEqual(all.reduce((s,x)=>s+x.n,0),184080);
const rows=all.filter(x=>x.j>=4&&x.j<25);
assert.strictEqual(rows.reduce((s,x)=>s+x.n,0),106900);
assert(rows.every(x=>Number.isSafeInteger(x.n)&&x.n>=0));
function bounds(t){
  assert(Number.isInteger(t)&&t>=4&&t<=20);
  const A={lo:0,hi:0,n:0},B={lo:0,hi:0,n:0};
  for(const x of rows){
    const z=x.j>=t?A:B;
    z.lo+=x.n*x.j**4;z.hi+=x.n*(x.j+1)**4;z.n+=x.n;
  }
  // Tight extrema under independent within-bin values U in [j,j+1).
  // Upper is a supremum because the upper bin edge is excluded.
  return {threshold_mps:t,hours:A.n,hour_share_pct:100*A.n/106900,
    u4_share_lower_pct:100*A.lo/(A.lo+B.hi),
    u4_share_upper_sup_pct:100*A.hi/(A.hi+B.lo)};
}
assert.strictEqual(bounds(19).hours,2);
assert.strictEqual(bounds(15).hours,104);
assert.strictEqual(bounds(12).hours,1187);
assert(bounds(9).u4_share_lower_pct>bounds(9).hour_share_pct);
assert(bounds(11).u4_share_lower_pct>bounds(11).hour_share_pct);
assert(bounds(15).u4_share_lower_pct>bounds(15).hour_share_pct);
for(const t of [9,11,12,15,18,19]){
 const x=bounds(t);assert(x.u4_share_lower_pct<=x.u4_share_upper_sup_pct);
 console.log([x.threshold_mps,x.hours,...['hour_share_pct','u4_share_lower_pct','u4_share_upper_sup_pct'].map(k=>x[k].toFixed(6))].join(','));
}
