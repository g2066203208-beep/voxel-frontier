#!/usr/bin/env node
// S11: exact piecewise-prismatic Euler-Bernoulli integral versus midpoint rule.
// This is a geometry-only proxy; NOT a 158 m structural model, wind load, or design verification.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..','T071');
function read(file){const [header,...lines]=fs.readFileSync(path.join(root,file),'utf8').trim().split(/\r?\n/);const names=header.split(',');return lines.map(line=>Object.fromEntries(line.split(',').map((x,i)=>[names[i],x])));}
const A=read('T071_31SEG_GEOMETRY_REBAR_BASELINE.csv'),B=read('S11_T071_31SEG_VOLUME_NEUTRAL_MINIMAX_20261112.csv');
function analyze(H, candidate=B) {
 assert.equal(A.length,31);assert.equal(candidate.length,31);assert.ok(Number.isFinite(H)&&H>=112);
 let midpoint=[0,0],exact=[0,0],volume=[0,0];
 for(let i=0;i<31;i++){const a=A[i],b=candidate[i];assert.equal(a.segment,b.segment);
 const lo=+a.z_bottom_m,hi=+a.z_top_m,z=+a.z_center_m,D=+a.D_outer_m;
 assert.ok([lo,hi,z,D].every(Number.isFinite)&&hi>lo&&lo>=0&&D>0&&z>=lo&&z<=hi);
 for(let k=0;k<2;k++){const t=+(k?b.t_candidate_mm:b.t_base_mm)/1000;
 assert.ok(Number.isFinite(t)&&t>0&&2*t<D);
 const I=Math.PI/64*(D**4-(D-2*t)**4);
 midpoint[k]+=(hi-lo)*(H-z)**2/I;
 exact[k]+=((H-lo)**3-(H-hi)**3)/(3*I);
 volume[k]+=(Math.PI/4)*(D*D-(D-2*t)**2)*(hi-lo);
 }}
 return {H_m:H,midpoint_ratio:midpoint[1]/midpoint[0],exact_ratio:exact[1]/exact[0],exact_change_pct:100*(exact[1]/exact[0]-1),quadrature_ratio_bias_pct:100*((midpoint[1]/midpoint[0])/(exact[1]/exact[0])-1),base_midpoint_integral_error_pct:100*(midpoint[0]/exact[0]-1),volume_delta_m3:volume[1]-volume[0]};
}
const low=analyze(112),high=analyze(158);
assert.ok(Math.abs(low.exact_ratio-1.003191780708762)<1e-11);
assert.ok(Math.abs(high.exact_ratio-1.0007467109830328)<1e-11);
assert.ok(Math.abs(low.volume_delta_m3)<1e-7);
assert.ok(low.exact_change_pct>high.exact_change_pct&&high.exact_change_pct>0);
const identity=B.map(r=>({...r,t_candidate_mm:r.t_base_mm}));
assert.ok(Math.abs(analyze(112,identity).exact_ratio-1)<1e-12);
const bad=B.map(r=>({...r}));bad[0].segment='BAD';assert.throws(()=>analyze(112,bad));
const badT=B.map(r=>({...r}));badT[0].t_candidate_mm='-2';assert.throws(()=>analyze(112,badT));
assert.throws(()=>analyze(111));
console.log(JSON.stringify({source_geometry:'T071_31SEG_GEOMETRY_REBAR_BASELINE.csv',source_candidate:'S11_T071_31SEG_VOLUME_NEUTRAL_MINIMAX_20261112.csv',interpretation:'H=158 is an applied load height on concrete-only segment integrals, not full 158m tower',at_concrete_top:low,at_nominal_tower_top:high,tests:'PASS: two numerical regressions, volume, monotonic load-height response, identity, segment mismatch, negative thickness, invalid height'},null,2));
