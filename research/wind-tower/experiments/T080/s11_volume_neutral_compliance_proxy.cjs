#!/usr/bin/env node
// S11: volume-neutral T071 thickness redistribution, unit-top-force Euler-Bernoulli geometric compliance proxy.
// No solver, local material stress, fatigue life, or design acceptance.
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const dir=path.join(__dirname,'..','T071');
function parse(file){const s=fs.readFileSync(path.join(dir,file),'utf8').trim().split(/\r?\n/);const h=s.shift().split(',');return s.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[h[i],v])));}
function analyze(A,B){
 assert.equal(A.length,31);assert.equal(B.length,31);
 const rows=A.map((r,j)=>{const b=B[j];assert.equal(r.segment,b.segment);
 const D=Number(r.D_outer_m),t0=Number(b.t_base_mm)/1000,t1=Number(b.t_candidate_mm)/1000,z0=Number(r.z_bottom_m),z1=Number(r.z_top_m),z=Number(r.z_center_m),L=z1-z0,H=112;
 assert.ok([D,t0,t1,z0,z1,z].every(Number.isFinite)&&D>2*Math.max(t0,t1)&&t0>0&&t1>0&&L>0);
 const Asec=t=>Math.PI/4*(D*D-(D-2*t)**2),I=t=>Math.PI/64*(D**4-(D-2*t)**4);
 return {segment:r.segment,volume0:Asec(t0)*L,volume1:Asec(t1)*L,I0:I(t0),I1:I(t1),C0:L*(H-z)**2/I(t0),C1:L*(H-z)**2/I(t1)};
 });
 const sum=k=>rows.reduce((s,r)=>s+r[k],0);
 const result={n:rows.length,volume_base_m3:sum('volume0'),volume_candidate_m3:sum('volume1'),delta_volume_m3:sum('volume1')-sum('volume0'),compliance_ratio:sum('C1')/sum('C0'),compliance_increase_pct:100*(sum('C1')/sum('C0')-1),changed:rows.filter(r=>Math.abs(r.I1/r.I0-1)>1e-10).map(r=>({segment:r.segment,I_ratio:r.I1/r.I0,delta_volume_m3:r.volume1-r.volume0,base_compliance_share:r.C0/sum('C0')}))};
 return result;
}
const A=parse('T071_31SEG_GEOMETRY_REBAR_BASELINE.csv'),B=parse('S11_T071_31SEG_VOLUME_NEUTRAL_MINIMAX_20261112.csv');
const out=analyze(A,B);
assert.ok(Math.abs(out.delta_volume_m3)<1e-7,'volume neutrality fails');
assert.ok(Math.abs(out.compliance_ratio-1.0031941080399787)<1e-10,'regression');
assert.equal(out.changed.length,7);
const identity=B.map(x=>({...x,t_candidate_mm:x.t_base_mm}));assert.ok(Math.abs(analyze(A,identity).compliance_ratio-1)<1e-12,'identity');
const malformed=B.map(x=>({...x}));malformed[0].segment='BAD';assert.throws(()=>analyze(A,malformed));
const invalid=B.map(x=>({...x}));invalid[0].t_candidate_mm='-1';assert.throws(()=>analyze(A,invalid));
console.log(JSON.stringify({source_geometry:'T071_31SEG_GEOMETRY_REBAR_BASELINE.csv',source_candidate:'S11_T071_31SEG_VOLUME_NEUTRAL_MINIMAX_20261112.csv',assumptions:'constant E, midpoint prismatic segments, fixed outer diameter, unit lateral force at z=112m, bending only',...out,tests:'PASS: regression, 31 identities, zero-perturbation, mismatched segment, invalid thickness'},null,2));
