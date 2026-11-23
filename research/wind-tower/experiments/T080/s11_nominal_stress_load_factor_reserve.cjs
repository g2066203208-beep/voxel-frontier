#!/usr/bin/env node
// S11 conditional load-factor reserve of archived T071 nominal-stress candidate.
// Stress values are archived nominal proxies, NOT material strength or design code limits.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const csv=fs.readFileSync(path.join(__dirname,'..','T071','S11_T071_31SEG_VOLUME_NEUTRAL_MINIMAX_20261112.csv'),'utf8').trim().split(/\r?\n/);
const h=csv.shift().split(',');
const rows=csv.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[h[i],v])));
function reserve(rows,cap){
 assert.equal(rows.length,31);assert.ok(Number.isFinite(cap)&&cap>0);
 const x=rows.map(r=>({segment:r.segment,base:Number(r.sigma_base_MPa),candidate:Number(r.sigma_candidate_MPa)}));
 assert.ok(x.every(r=>Number.isFinite(r.base)&&Number.isFinite(r.candidate)&&r.base>0&&r.candidate>0));
 const maxBase=Math.max(...x.map(r=>r.base)),maxCandidate=Math.max(...x.map(r=>r.candidate));
 const active=x.filter(r=>Math.abs(r.candidate-maxCandidate)<1e-9).map(r=>r.segment);
 return {cap_MPa:cap,max_base_MPa:maxBase,max_candidate_MPa:maxCandidate,lambda_base:cap/maxBase,lambda_candidate:cap/maxCandidate,active,margin_at_1pct_MPa:cap-1.01*maxCandidate,margin_at_5pct_MPa:cap-1.05*maxCandidate};
}
const cap=50.987301538555;const a=reserve(rows,cap);
assert.ok(Math.abs(a.lambda_candidate-1)<1e-12);
assert.deepEqual(a.active,['CSEG_27','CSEG_28']);
assert.ok(a.lambda_base<1&&a.margin_at_1pct_MPa<0);
assert.throws(()=>reserve(rows,NaN));
const bad=rows.map(x=>({...x}));bad[0].sigma_candidate_MPa='NaN';assert.throws(()=>reserve(bad,cap));
const loose=reserve(rows,1.05*cap);assert.ok(Math.abs(loose.lambda_candidate-1.05)<1e-12);
console.log(JSON.stringify({source:'T071 archived 31-section nominal stress candidate',model:'all nominal stress magnitudes multiplied by a common nonnegative factor lambda, frozen response pattern; cap is archived candidate minimax value, NOT allowable stress',...a,tests:'PASS 31 rows, active set, zero reserve, invalid input rejection, cap scaling'},null,2));
