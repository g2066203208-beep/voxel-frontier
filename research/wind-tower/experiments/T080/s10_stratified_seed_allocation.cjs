#!/usr/bin/env node
'use strict';
// S10 planning experiment, not an IEC/DLC or fatigue-damage acceptance test.
// Run: node research/wind-tower/experiments/T080/s10_stratified_seed_allocation.cjs
const fs=require('fs'), path=require('path'), assert=require('assert');
const source=path.resolve(__dirname,'../T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv');
const rows=fs.readFileSync(source,'utf8').trim().split(/\r?\n/).slice(1).map(line=>line.split(','));
assert.strictEqual(rows.length,31);
const hours=rows.map(r=>Number(r[2]));
assert(hours.every(x=>Number.isSafeInteger(x)&&x>=0));
assert.strictEqual(hours.reduce((a,b)=>a+b,0),184080);
const h=hours.slice(4,25), total=h.reduce((a,b)=>a+b,0);
assert.strictEqual(total,106900);
const p=h.map(x=>x/total);
function variance(n,probs=p){return probs.reduce((a,x,i)=>a+x*x/n[i],0);}
function optimize(probs,budget=126,floor=1){
  if(budget<probs.length*floor)throw Error('infeasible budget');
  if(probs.some(x=>!Number.isFinite(x)||x<0))throw Error('invalid probability');
  const n=Array(probs.length).fill(floor);
  for(let k=n.length*floor;k<budget;k++){
    let best=-1,idx=-1;
    for(let i=0;i<n.length;i++){
      const gain=probs[i]*probs[i]/(n[i]*(n[i]+1));
      if(gain>best){best=gain;idx=i;}
    }
    n[idx]++;
  }
  return n;
}
const n=optimize(p), baseline=Array(21).fill(6);
assert.strictEqual(n.reduce((a,b)=>a+b,0),126);
assert(n.every(x=>x>=1));
assert.deepStrictEqual(optimize([1,0],3,1),[2,1]);
assert.throws(()=>optimize([1,0],1,1),/infeasible/);
assert.throws(()=>optimize([-1,2],3,1),/invalid/);
// Exchange optimality: no one-slot transfer improves the objective.
for(let i=0;i<21;i++)if(n[i]>1)for(let j=0;j<21;j++){
  if(i===j)continue;
  const trial=n.slice();trial[i]--;trial[j]++;
  assert(variance(trial)>=variance(n)-1e-14);
}
const v0=variance(baseline),v1=variance(n);
assert(v1<v0);
const out={source,observed_hours:184080,operating_hours:total,bins:21,positive_bins:h.filter(x=>x>0).length,budget:126,
  baseline_allocation:baseline,optimized_allocation:n,
  normalized_variance_equal_sigma_baseline:v0,normalized_variance_equal_sigma_optimized:v1,
  variance_ratio:v0/v1,relative_variance_reduction:1-v1/v0,
  limitations:'Conditional on fixed observed bin probabilities, independent seeds, equal within-bin response variance, and one slot per bin. NOT a fatigue, DLC1.2, or structural safety result.'};
// 2026-11-16: exact heteroscedastic rejection test for the fixed equal-variance allocation.
// A scenario is a statistical counterexample, NOT observed seed variance.
function weightedVariance(allocation,sd){
  assert.strictEqual(allocation.length,21);assert.strictEqual(sd.length,21);
  assert(sd.every(x=>Number.isFinite(x)&&x>0));
  return p.reduce((s,pi,i)=>s+(pi*sd[i])**2/allocation[i],0);
}
const lowAllocation=n.map(x=>x<6);
const adverse=lowAllocation.map(flag=>flag?10:1);
const badOpt=weightedVariance(n,adverse),badEqual=weightedVariance(baseline,adverse);
assert(badOpt>badEqual,'adversarial SD must reverse equal-variance ranking');
const gainTerms=p.map((pi,i)=>pi*pi*(1/6-1/n[i]));
const B=gainTerms.reduce((s,g,i)=>s+(n[i]>6?g:0),0);
const A=gainTerms.reduce((s,g,i)=>s+(n[i]<6?-g:0),0);
assert(A>0&&B>0);
const criticalSD=Math.sqrt(B/A);
assert(criticalSD>9&&criticalSD<10);
const boundary=lowAllocation.map(flag=>flag?criticalSD:1);
assert(Math.abs(weightedVariance(n,boundary)-weightedVariance(baseline,boundary))<1e-12);
assert(Math.abs(weightedVariance(n,Array(21).fill(1))-v1)<1e-14);
assert(Math.abs(weightedVariance(baseline,Array(21).fill(1))-v0)<1e-14);
out.heteroscedastic_counterexample={
  assumption:'Only a deliberately adverse hypothetical within-bin SD pattern; no physical seed variance inferred',
  sd_ratio_critical:criticalSD,variance_ratio_critical:B/A,
  sd_ratio_test:10,high_sd_bins_mps:lowAllocation.map((flag,i)=>flag?i+4:null).filter(x=>x!==null),
  adverse_variance_optimized:badOpt,adverse_variance_equal6:badEqual,
  adverse_relative_variance_change:badOpt/badEqual-1,
  interpretation:'At 10x SD for bins with n<6, the equal-variance allocation is 5.37% worse than equal-six, in variance. No fatigue or DLC claim.'
};
console.log(JSON.stringify(out,null,2));
