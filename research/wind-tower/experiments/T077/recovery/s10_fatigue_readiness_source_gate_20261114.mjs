#!/usr/bin/env node
/**
 * S10 — REAL SOURCE ADMISSION FOR FATIGUE, 2026-11-14.
 * Pure Node 22; no solver, no invented S-N model or fatigue life.
 * Audits 1574 original gross ETM cycles and 2880 NTM gross-stress rows.
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const grossPath = join(here, 'S10_3CONTROL_REAL_GROSS_CYCLES_20261030.csv');
const receiptPath = join(here, 'S10_3CONTROL_REAL_CYCLE_MEAN_RECEIPT_20261030.json');
const ntmPath = join(here, '../../T062/S10_18NTM_10NEARBASE_16AZ_GROSS_RAINFLOW_20261031.csv');
const sha256 = b => createHash('sha256').update(b).digest('hex');
const PINS = Object.freeze({
  gross: '646065838456b6465e321c4c6fd24966f180f275df99c615000577557219ff83',
  ntm: 'd45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b'
});
const MODEL = Object.freeze({
  BF1_CURRENT: Object.freeze({locations:36,strands_per_location:1,area_per_strand_mm2:140,initial_stress_MPa:1280,total_area_mm2:5040,nominal_initial_force_MN:6.4512}),
  BF8_CODE_DESIGN: Object.freeze({locations:36,strands_per_location:8,area_per_strand_mm2:140,initial_stress_MPa:1280,total_area_mm2:40320,nominal_initial_force_MN:51.6096})
});
function parseCsv(raw, required) {
  const s = raw.toString('utf8').replace(/^\uFEFF/, '').trim();
  const lines = s.split(/\r?\n/);
  const columns = lines.shift().split(',');
  assert.deepEqual(columns, required, 'CSV_SCHEMA_CHANGED');
  return lines.map((line,i) => {
    const fields = line.split(',');
    assert.equal(fields.length, required.length, 'CSV_BAD_FIELD_COUNT_ROW_'+(i+2));
    return Object.fromEntries(columns.map((c,j)=>[c,fields[j]]));
  });
}
const grossColumns = ['case','segment','azimuth_deg','cycle_index','range_MPa','amplitude_MPa','mean_gross_MPa','mean_Pe_hypothesis_MPa','mean_P0_hypothesis_MPa','count','status'];
const ntmColumns = ['case','wind_bin','seed','station','z_m','local_azimuth_deg','mean_MPa','min_MPa','max_MPa','peak_time_s','peak_to_peak_MPa','DEL_m4_MPa','DEL_m10_MPa','rainflow_equivalent_cycles','quantization_sample_bound_MPa','source_outb_sha256','stress_class'];
function auditModel(modelBranch, values) {
  assert.ok(Object.hasOwn(MODEL, modelBranch), 'UNKNOWN_PT_MODEL_BRANCH');
  const m=MODEL[modelBranch];
  for (const [k,v] of Object.entries(m)) assert.equal(values[k],v,'MODEL_BRANCH_IDENTITY_MISMATCH_'+k);
  assert.equal(m.locations*m.strands_per_location*m.area_per_strand_mm2,m.total_area_mm2);
  assert.ok(Math.abs(m.total_area_mm2*m.initial_stress_MPa/1e6-m.nominal_initial_force_MN)<1e-10);
  return true;
}
function admitLocalMaterial(record) {
  // Neither historical gross-stress source satisfies the local material contract.
  assert.equal(record.stress_owner,'VERIFIED_LOCAL_MATERIAL_STRESS','NOT_LOCAL_MATERIAL_STRESS');
  assert.ok(['CONCRETE','REBAR','PT','STEEL'].includes(record.material_id),'INVALID_MATERIAL');
  assert.ok(record.material_model_ref,'MISSING_MATERIAL_S_N_REFERENCE');
  assert.ok(/^[a-f0-9]{64}$/.test(record.stress_source_sha256||''),'MISSING_SOURCE_SHA');
  assert.ok(record.model_branch==='BF1_CURRENT'||record.model_branch==='BF8_CODE_DESIGN','UNKNOWN_MODEL_BRANCH');
  assert.ok(Number.isFinite(+record.N_allow_cycles)&&+record.N_allow_cycles>0,'MISSING_POSITIVE_N_ALLOW');
  assert.ok(Number.isFinite(+record.stress_range_MPa)&&+record.stress_range_MPa>=0,'INVALID_STRESS_RANGE');
  assert.ok(Number.isFinite(+record.mean_stress_MPa),'INVALID_MEAN_STRESS');
  return true;
}
function analyse(grossBuf, ntmBuf, receipt) {
  assert.equal(sha256(grossBuf),PINS.gross,'GROSS_CYCLE_SOURCE_SHA_MISMATCH');
  assert.equal(sha256(ntmBuf),PINS.ntm,'NTM_STRESS_SOURCE_SHA_MISMATCH');
  assert.equal(receipt.full_cycle_csv_sha256,PINS.gross,'GROSS_RECEIPT_SHA_MISMATCH');
  auditModel('BF1_CURRENT',{...MODEL.BF1_CURRENT});
  auditModel('BF8_CODE_DESIGN',{...MODEL.BF8_CODE_DESIGN});

  const gross=parseCsv(grossBuf,grossColumns);
  const ntm=parseCsv(ntmBuf,ntmColumns);
  assert.equal(gross.length,1574,'GROSS_CYCLE_COUNT');
  assert.equal(ntm.length,2880,'NTM_STRESS_ROW_COUNT');
  const groups=new Map();
  for(const r of gross) {
    assert.equal(r.status,'REAL_GROSS_NOMINAL_CYCLES_PT_MEAN_SHIFT_HYPOTHESIS_NOT_LOCAL_MATERIAL','MISLABELED_LOCAL_STRESS');
    const n=Number(r.count),rg=Number(r.range_MPa),mu=Number(r.mean_gross_MPa),a=Number(r.amplitude_MPa);
    assert.ok(Number.isFinite(n)&&[0.5,1].includes(n)&&Number.isFinite(rg)&&rg>=0&&Number.isFinite(mu));
    assert.ok(Math.abs(a-rg/2)<1e-9,'RAIN_FLOW_AMPLITUDE');
    const k=[r.case,r.segment,r.azimuth_deg].join('|');
    let g=groups.get(k);
    if(!g) {g={case:r.case,segment:r.segment,azimuth_deg:Number(r.azimuth_deg),row_count:0,equivalent_cycles:0,range4_moment:0,range10_moment:0,max_range_MPa:-Infinity,min_mean_MPa:Infinity,max_mean_MPa:-Infinity,pe_gross_shift:null,p0_gross_shift:null};groups.set(k,g);}
    const shiftPe=Number(r.mean_Pe_hypothesis_MPa)-mu;
    const shiftP0=Number(r.mean_P0_hypothesis_MPa)-mu;
    if(g.pe_gross_shift!==null) {
      assert.ok(Math.abs(g.pe_gross_shift-shiftPe)<1e-7,'INCONSISTENT_BF8_PE_HYPOTHESIS');
      assert.ok(Math.abs(g.p0_gross_shift-shiftP0)<1e-7,'INCONSISTENT_BF8_P0_HYPOTHESIS');
    } else {g.pe_gross_shift=shiftPe;g.p0_gross_shift=shiftP0;}
    g.row_count+=1;g.equivalent_cycles+=n;g.range4_moment+=n*rg**4;g.range10_moment+=n*rg**10;
    g.max_range_MPa=Math.max(g.max_range_MPa,rg);g.min_mean_MPa=Math.min(g.min_mean_MPa,mu);g.max_mean_MPa=Math.max(g.max_mean_MPa,mu);
  }
  assert.equal(groups.size,3,'GROSS_CONTROL_COUNT');
  for(const g of groups.values()) {
    const expected=receipt.controls.find(x=>x.case===g.case&&x.segment===g.segment&&Number(x.angle_deg)===g.azimuth_deg);
    assert.ok(expected,'CONTROL_MISMATCH');
    assert.equal(g.row_count,expected.cycle_rows,'CONTROL_CYCLE_ROWS');
    assert.equal(g.equivalent_cycles,expected.eq_cycles,'CONTROL_EQ_CYCLES');
    g.DEL4_MPa=(g.range4_moment/600)**0.25;
    g.DEL10_MPa=(g.range10_moment/600)**0.1;
    assert.ok(Math.abs(g.DEL4_MPa-expected.DEL4_MPa)<1e-8,'DEL4_ORACLE_MISMATCH');
    assert.ok(Math.abs(g.DEL10_MPa-expected.DEL10_MPa)<1e-8,'DEL10_ORACLE_MISMATCH');
    delete g.range4_moment; delete g.range10_moment;
  }
  const ntmCases=new Set(),bins=new Set(),locations=new Set(),angles=new Set();
  for(const r of ntm) {
    assert.equal(r.stress_class,'ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE','NTM_MISLABELED_LOCAL');
    assert.ok(Number.isFinite(+r.DEL_m4_MPa)&&+r.DEL_m4_MPa>=0);
    assert.ok(/^[a-f0-9]{64}$/.test(r.source_outb_sha256),'NTM_SOURCE_ID_INVALID');
    ntmCases.add(r.case); bins.add(r.wind_bin); locations.add(r.station);angles.add(r.local_azimuth_deg);
  }
  assert.equal(ntmCases.size,18);assert.equal(bins.size,3);assert.equal(locations.size,10);assert.equal(angles.size,16);
  return {
    stage:'S10_FATIGUE_REAL_SOURCE_ADMISSION_NOT_MATERIAL_LIFE',
    current_model:{branch:'BF1_CURRENT',...MODEL.BF1_CURRENT},
    separate_design_candidate:{branch:'BF8_CODE_DESIGN',...MODEL.BF8_CODE_DESIGN},
    source:{gross_sha256:PINS.gross,ntm_sha256:PINS.ntm,gross_cycle_rows:gross.length,ntm_gross_stress_rows:ntm.length,ntm_cases:ntmCases.size,ntm_wind_bins:bins.size,ntm_near_base_locations:locations.size,ntm_azimuths:angles.size},
    gross_etm_controls:[...groups.values()],
    inherited_historical_work:'36 original NTM/ETM cases; load-level rainflow 48070 rows; ERA5 184080 h',
    admitted_for:'SOURCE_BACKED_GROSS_SECTION_RAINFLOW_AND_CONDITIONAL_COMPARISONS_ONLY',
    rejected_for:['BF8_PT_MEAN_USED_AS_CURRENT_BF1','GROSS_STRESS_AS_LOCAL_MATERIAL','LOAD_DEL_AS_MATERIAL_DAMAGE','ETM_AS_YEARLY_NTM','MISSING_WIND_BINS_AS_ZERO','E_OR_WE_EVENT_DAMAGE_WITHOUT_STRESS'],
    material_damage_annual:null,years_to_failure:null,physical_pass:false
  };
}
const rawGross=readFileSync(grossPath),rawNtm=readFileSync(ntmPath),receipt=JSON.parse(readFileSync(receiptPath,'utf8'));
const output=analyse(rawGross,rawNtm,receipt);
if(process.argv.includes('--self-test')) {
  let passed=0;
  function reject(fn){assert.throws(fn);passed++;}
  reject(()=>auditModel('BF1_CURRENT',{...MODEL.BF1_CURRENT,strands_per_location:8}));
  reject(()=>auditModel('BF8_CODE_DESIGN',{...MODEL.BF8_CODE_DESIGN,nominal_initial_force_MN:6.4512}));
  reject(()=>analyse(Buffer.concat([rawGross,Buffer.from('\n')]),rawNtm,receipt));
  reject(()=>analyse(rawGross,Buffer.concat([rawNtm,Buffer.from('\n')]),receipt));
  reject(()=>admitLocalMaterial({stress_owner:'GROSS_NOMINAL',material_id:'CONCRETE',N_allow_cycles:1e6}));
  reject(()=>admitLocalMaterial({stress_owner:'VERIFIED_LOCAL_MATERIAL_STRESS',material_id:'PT',model_branch:'BF1_CURRENT'}));
  console.error('S10 source admission: real source checks PASS; '+passed+' negative tests PASS');
}
console.log(JSON.stringify(output,null,2));
