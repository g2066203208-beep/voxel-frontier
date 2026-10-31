#!/usr/bin/env node
'use strict';
// Source-level T057-specific coordinate/unit contract. No Abaqus keywords or solver execution.
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
const assert = require('node:assert/strict');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const EXPECTED_CSV = '1b8d4e2f2b47222694a363eb96aa1ec53217a8610b952aa8a519470a9142bc29';
const EXPECTED_T057 = 'c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db';
const EXPECTED_ESM = 'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34';
function map(e, n, u, angleDeg=0, scale=1) {
  if (![e,n,u,angleDeg,scale].every(Number.isFinite) || Math.abs(angleDeg)>360 || ![1,1000].includes(scale)) throw Error('BAD_AXIS_OR_UNITS');
  const a=angleDeg*Math.PI/180, c=Math.cos(a), s=Math.sin(a);
  // Right-handed tower-global X / Y(up) / Z: X=c E+s N; Y=U; Z=s E-c N.
  return [scale*(c*e+s*n),scale*u,scale*(s*e-c*n)];
}
function parseCsv(text) {
  const lines=text.trimEnd().split(/\r?\n/), hdr=lines.shift().split(',');
  assert.deepEqual(hdr,['metric','peak_m_s2','time_s','HNE_at_peak_m_s2','HNN_at_peak_m_s2','HNZ_at_peak_m_s2','interpretation']);
  const rows=lines.map(line=>{
    const a=line.split(','); if(a.length!==7) throw Error('BAD_CSV_WIDTH');
    const [metric,p,t,e,n,u,interpretation]=a;
    const nums=[p,t,e,n,u].map(Number);
    if(!nums.every(Number.isFinite)) throw Error('BAD_CSV_NUMBER');
    if(interpretation!=='SYNCHRONOUS_SOURCE_DIAGNOSTIC_NOT_DESIGN') throw Error('UNVERIFIED_SOURCE');
    return {metric,peak:Number(p),t:Number(t),e:Number(e),n:Number(n),u:Number(u)};
  });
  if(rows.length!==5 || new Set(rows.map(r=>r.metric)).size!==5) throw Error('BAD_CSV_COUNT');
  return rows;
}
function checkModel(audit,amp) {
  if(audit.sha256!==EXPECTED_T057 || audit.pt.y_min!==0 || audit.pt.y_max!==112 ||
      !audit.gravity_lines.some(r=>r[1].replace(/\s/g,'')===',GRAV,9.81,0.,-1.,0.') ||
      !audit.prestress.initial_stress_block.some(x=>x.includes('1.28e+09'))) throw Error('MODEL_AXIS_IDENTITY_HOLD');
  if(amp.source_sha256!==EXPECTED_ESM || amp.azimuth_deg_CCW_from_East!==0 ||
      !amp.assumed_frame.includes('HNZ Up') || !amp.acceleration_units.includes('mm/s^2') || amp.Abaqus_E_WE_RUN!==0) throw Error('PRIOR_RECEIPT_IDENTITY_HOLD');
}
function test() {
  const v=[0.475,-0.112,0.287];
  for(const a of [0,30,90,-45,180]) {
    const m=map(...v,a), c=Math.cos(a*Math.PI/180),s=Math.sin(a*Math.PI/180);
    const inv=[c*m[0]+s*m[2],s*m[0]-c*m[2],m[1]];
    for(let i=0;i<3;i++) assert.ok(Math.abs(inv[i]-v[i])<2e-15);
    assert.ok(Math.abs(Math.hypot(...m)-Math.hypot(...v))<2e-15);
    // The ENU -> XYZ row-matrix determinant is +1, not a reflection.
    const det=c*c+s*s; assert.ok(Math.abs(det-1)<2e-15);
  }
  assert.deepEqual(map(1,2,3,0),[1,3,-2]);
  const m90=map(1,2,3,90); assert.ok(Math.abs(m90[0]-2)<1e-14 && m90[1]===3 && Math.abs(m90[2]-1)<1e-14);
  assert.deepEqual(map(1,2,3,0,1000),[1000,3000,-2000]);
  for(const bad of [[1,2,3,0,10],[1,2,3,361,1],[NaN,2,3,0,1],[1,2,3,0,-1]]) {
    assert.throws(()=>map(...bad),/BAD_AXIS_OR_UNITS/);
  }
  assert.throws(()=>parseCsv('metric,peak_m_s2\nX,1'),/AssertionError/);
  assert.throws(()=>parseCsv('metric,peak_m_s2,time_s,HNE_at_peak_m_s2,HNN_at_peak_m_s2,HNZ_at_peak_m_s2,interpretation\nX,1,0,1,2,NaN,SYNCHRONOUS_SOURCE_DIAGNOSTIC_NOT_DESIGN'),/BAD_CSV_NUMBER/);
  console.log('S08_T057_YUP_FRAME_UNIT_SELFTEST_PASS: rotation/inverse/norm/det, units, 6 negative cases');
}
function run(csvPath,auditPath,ampPath,outPath) {
  test(); const csv=fs.readFileSync(csvPath),auditRaw=fs.readFileSync(auditPath),ampRaw=fs.readFileSync(ampPath);
  if(sha(csv)!==EXPECTED_CSV) throw Error('SOURCE_CSV_SHA256_MISMATCH');
  const rows=parseCsv(csv.toString('utf8')),audit=JSON.parse(auditRaw),amp=JSON.parse(ampRaw);
  checkModel(audit,amp);
  const sample=rows.find(x=>x.metric==='three_component_vector');
  const norm=Math.hypot(sample.e,sample.n,sample.u);
  if(Math.abs(norm-sample.peak)>2e-15) throw Error('SYNCHRONOUS_NORM_MISMATCH');
  const transformed=[0,30,90].map(angle=>{
    const xyz=map(sample.e,sample.n,sample.u,angle);
    return {azimuth_deg_ccw_from_east:angle,source_time_s:sample.t,global_X_m_s2:xyz[0],global_Y_up_m_s2:xyz[1],global_Z_m_s2:xyz[2],norm_m_s2:Math.hypot(...xyz)};
  });
  const maxNormError=Math.max(...transformed.map(r=>Math.abs(r.norm_m_s2-norm)));
  const report={SOURCE:'ESM v3 IT-2012-0008/NVL/MP processed three-component source, 5 synchronous diagnostic samples; NOT full wave re-read',
    SOURCE_SHA256:EXPECTED_ESM,SOURCE_SAMPLE_CSV_SHA256:sha(csv),SOURCE_MODEL_AUDIT_SHA256:sha(auditRaw),
    SOURCE_PREVIOUS_AMP_RECEIPT_SHA256:sha(ampRaw),T057_FROZEN_INP_SHA256:EXPECTED_T057,
    REF:'ESM v3 DOI 10.13127/esm.3',STANDARD:'IEC/GB target and applicable clauses NOT_VERIFIED',
    OFFICIAL:'T057 original input audit: gravity -Y, PT from Y=0 to Y=112 m, prestress 1.28e9 Pa; Abaqus native input semantics NOT_VERIFIED',
    RUN:'Node.js source-level deterministic self-test only; native Abaqus E/WE=0',FIG:'NONE',TAB:'5 source synchronous samples + 3 rotated values at same peak time in this JSON',
    assumptions:'ESM HNE=East, HNN=North, HNZ=Up assumed; X azimuth from East CCW, Y=Up, Z chosen for right-handed frame. Physical turbine azimuth and HNZ station header still unverified.',
    model_unit_contract:'T057 audit consistent with metre, second, Pa, gravity 9.81 m/s^2. Use factor=1 m/s^2 for this SI branch; previous 1000 mm/s^2 amplitudes are NOT directly compatible. Full density/mass-unit independent audit pending.',
    orientation_formula:'X=cos(theta)*HNE+sin(theta)*HNN; Y=HNZ; Z=sin(theta)*HNE-cos(theta)*HNN; determinant +1',
    sample_three_component_peak_time_s:sample.t,sample_peak_m_s2:norm,transformed,
    error_budget:{rotation_norm_abs_m_s2:maxNormError,source_sample_peak_abs_m_s2:Math.abs(norm-sample.peak),time_sampling_s:0.005,physical_azimuth_error:'NOT_ESTIMATED',vertical_sign_error:'NOT_ESTIMATED',low_frequency_reliability:'NOT_VERIFIED'},
    negative_tests:6,PASS:'STATIC_AXIS_AND_UNIT_CONTRACT_ONLY',HOLD:'Model-global Y-up and SI inference require full native Abaqus unit/BC audit; site spectrum, processed wave low-frequency validity, structural azimuth, HNZ sign and base-motion semantics unresolved.',
    generated_keywords:'NONE; no *AMPLITUDE, *BOUNDARY or *BASE MOTION load cards generated; no native run'};
  fs.writeFileSync(outPath,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({sample,transformed,maxNormError,receipt_sha256:sha(fs.readFileSync(outPath))},null,2));
}
if(require.main===module) {
  if(process.argv.length!==6) throw Error('usage: node script source5.csv T057_audit.json prior_amp_receipt.json output_receipt.json');
  run(...process.argv.slice(2));
}
module.exports={map,parseCsv,checkModel,test,run};
