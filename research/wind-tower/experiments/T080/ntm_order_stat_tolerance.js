#!/usr/bin/env node
'use strict';
// Distribution-free one-sided coverage for an iid continuous sample maximum.
// Usage: node ntm_order_stat_tolerance.js [CSV_PATH]
const fs=require('node:fs');
const assert=require('node:assert/strict');
function confidence(n,p){if(!Number.isInteger(n)||n<1||!(p>0&&p<1))throw Error('invalid n/p');return 1-p**n;}
function coverage(n,conf){if(!Number.isInteger(n)||n<1||!(conf>0&&conf<1))throw Error('invalid n/conf');return (1-conf)**(1/n);}
function parseCSV(s){const lines=s.trim().split(/\r?\n/),headers=lines.shift().split(','),j=headers.indexOf('xy_same_time_over_async_peak_ratio');if(j<0)throw Error('ratio column missing');const groups=new Map();for(const line of lines){const a=line.split(','),id=a[0],v=Number(a[j]);if(!Number.isFinite(v)||v<=0||v>1)throw Error('bad ratio: '+id);const bin=id.split('_NTM_')[0];if(!groups.has(bin))groups.set(bin,[]);groups.get(bin).push(v);}return groups;}
assert.ok(Math.abs(confidence(1,.95)-.05)<1e-14);
assert.ok(Math.abs(confidence(6,.95)-.264908109375)<1e-14);
assert.ok(Math.abs(coverage(6,.95)-.6069622310029172)<1e-14);
assert.throws(()=>confidence(0,.95));
assert.throws(()=>parseCSV('case,xy_same_time_over_async_peak_ratio\nx,1.1'));

// Family-wise distribution-free upper tolerance for distinct wind bins.
// For independent bins: P(all bin maxima cover >=p of each bin) = product_i (1-p**n_i).
// Without cross-bin independence, Bonferroni lower bound = max(0,1-sum_i p**n_i).
// These are statements about three conditional distributions, NOT a pooled climate-wide bound.
function familyConfidence(ns,p,{independentBins=false}={}){
 if(!Array.isArray(ns)||ns.length<1||ns.some(n=>!Number.isInteger(n)||n<1)||!(p>0&&p<1))throw Error('invalid bins/p');
 const failures=ns.map(n=>p**n);
 return independentBins?failures.reduce((a,f)=>a*(1-f),1):Math.max(0,1-failures.reduce((a,b)=>a+b,0));
}
function minEqualBinN(bins,p,target,{independentBins=false}={}){
 if(!Number.isInteger(bins)||bins<1||!(target>0&&target<1)||!(p>0&&p<1))throw Error('invalid target');
 const threshold=independentBins?1-target**(1/bins):(1-target)/bins;
 let n=Math.max(1,Math.ceil(Math.log(threshold)/Math.log(p)));
 while(familyConfidence(Array(bins).fill(n),p,{independentBins})<target)n++;
 while(n>1&&familyConfidence(Array(bins).fill(n-1),p,{independentBins})>=target)n--;
 return n;
}
assert.ok(Math.abs(familyConfidence([6,6,6],.95,{independentBins:true})-(1-.95**6)**3)<1e-14);
assert.ok(Math.abs(familyConfidence([6,6,6],.95)-Math.max(0,1-3*.95**6))<1e-14);
assert.equal(minEqualBinN(3,.95,.95,{independentBins:true}),80);
assert.equal(minEqualBinN(3,.95,.95),80);
assert.ok(familyConfidence([80,80,80],.95)>=.95);
assert.ok(familyConfidence([79,79,79],.95,{independentBins:true})<.95);
assert.throws(()=>familyConfidence([6,0,6],.95));
assert.throws(()=>minEqualBinN(0,.95,.95));

const input=process.argv[2];
if(input){const groups=parseCSV(fs.readFileSync(input,'utf8'));for(const [bin,v] of groups){const maxOverstatement=Math.max(...v.map(r=>100*(1/r-1)));console.log(JSON.stringify({bin,n:v.length,maxObservedOverstatementPercent:maxOverstatement,confidenceOfAtLeast95PercentCoverage:confidence(v.length,.95),coverageAt95PercentConfidence:coverage(v.length,.95)}));}}
else console.log(JSON.stringify({selftest:'PASS',n6:{confidenceOf95Coverage:confidence(6,.95),coverageAt95Confidence:coverage(6,.95)},n18:{confidenceOf95Coverage:confidence(18,.95),coverageAt95Confidence:coverage(18,.95)},minimumNfor95_95:Math.ceil(Math.log(.05)/Math.log(.95)),threeBinFamilywise:{n6Independent:familyConfidence([6,6,6],.95,{independentBins:true}),n6WithoutIndependenceLowerBound:familyConfidence([6,6,6],.95),minimumEqualNPerBinIndependent:minEqualBinN(3,.95,.95,{independentBins:true}),minimumEqualNPerBinBonferroni:minEqualBinN(3,.95,.95),n80Independent:familyConfidence([80,80,80],.95,{independentBins:true}),n80Bonferroni:familyConfidence([80,80,80],.95)}}));
