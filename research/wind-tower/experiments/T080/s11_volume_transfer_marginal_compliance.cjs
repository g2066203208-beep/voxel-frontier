#!/usr/bin/env node
'use strict';
// S11: exact volume-transfer directional derivative for the archived 31-segment candidate.
// Geometry-only Euler-Bernoulli proxy; NOT a structural response or stress-feasible optimizer.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..','T071');
function csv(name){let [h,...ls]=fs.readFileSync(path.join(root,name),'utf8').trim().split(/\r?\n/);h=h.split(',');return ls.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[h[i],v])));}
const G=csv('T071_31SEG_GEOMETRY_REBAR_BASELINE.csv'),T=csv('S11_T071_31SEG_VOLUME_NEUTRAL_MINIMAX_20261112.csv');
assert.equal(G.length,31);assert.equal(T.length,31);
const rows=G.map((g,i)=>{const t=T[i];assert.equal(g.segment,t.segment);const D=+g.D_outer_m,L=+g.z_top_m-+g.z_bottom_m,z0=+g.z_bottom_m,z1=+g.z_top_m,th=+t.t_candidate_mm/1000;assert.ok([D,L,z0,z1,th].every(Number.isFinite)&&D>2*th&&th>0&&L>0);
return {segment:g.segment,D,L,z0,z1,t:th,stress:+t.sigma_candidate_MPa};});
function I(r,t){return Math.PI/64*(r.D**4-(r.D-2*t)**4);}
function V(r,t){return Math.PI*r.L*(r.D*t-t*t);}
function C(r,t,H=112){return ((H-r.z0)**3-(H-r.z1)**3)/(3*I(r,t));}
function dCdV(r,H=112){const dI=Math.PI/8*(r.D-2*r.t)**3,dV=Math.PI*r.L*(r.D-2*r.t);return -((H-r.z0)**3-(H-r.z1)**3)/3*dI/(I(r,r.t)**2*dV);}
function thicknessAtVolume(r,volume){const q=volume/(Math.PI*r.L);assert.ok(q>0&&q<r.D*r.D/4);return (r.D-Math.sqrt(r.D*r.D-4*q))/2;}
function transfer(receiver,donor,amount,H=112){assert.ok(amount>=0&&receiver!==donor);let a=rows[receiver],b=rows[donor],av=V(a,a.t),bv=V(b,b.t);assert.ok(amount<bv);let ta=thicknessAtVolume(a,av+amount),tb=thicknessAtVolume(b,bv-amount);let before=C(a,a.t,H)+C(b,b.t,H),after=C(a,ta,H)+C(b,tb,H);return {delta_C:after-before,volume_residual:V(a,ta)+V(b,tb)-av-bv,ta,tb};}
const H=112,total=rows.reduce((s,r)=>s+C(r,r.t,H),0),receiver=2,donor=27;
const slope=dCdV(rows[receiver])-dCdV(rows[donor]),eps=1e-4,fd=(transfer(receiver,donor,eps).delta_C-transfer(receiver,donor,0).delta_C)/eps;
assert.ok(Math.abs(slope-fd)<0.005);
assert.ok(Math.abs(transfer(receiver,donor,0.1).volume_residual)<1e-10);
assert.ok(transfer(receiver,donor,0.1).delta_C<0);
assert.throws(()=>transfer(2,2,0.1));assert.throws(()=>transfer(2,27,-1));
const rank=rows.map(r=>({segment:r.segment,dCdV:dCdV(r),stress_MPa:r.stress})).sort((a,b)=>a.dCdV-b.dCdV);
console.log(JSON.stringify({H_m:H,C_candidate_geometry:total,recipient:rows[receiver].segment,donor:rows[donor].segment,recipient_dCdV:dCdV(rows[receiver]),donor_dCdV:dCdV(rows[donor]),slope_dC_per_m3:slope,relative_slope_per_m3:slope/total,finite_difference_eps_m3:eps,finite_difference_slope:fd,transfer_0p1m3:transfer(receiver,donor,0.1),top_marginal:rank.slice(0,5),least_marginal:rank.slice(-5),tests:'PASS exact-volume, analytic vs finite difference, negative transfer, identity, same segment rejection; stress constraint NOT TESTED'},null,2));
