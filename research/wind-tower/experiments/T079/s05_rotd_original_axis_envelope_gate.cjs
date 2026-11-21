#!/usr/bin/env node
'use strict';
// S05: archived ESM processed-response-spectrum axis-envelope test.
// This is input-motion diagnostics, NOT design-spectrum or structural validation.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const DEFAULT = 'research/wind-tower/experiments/T079/real-records/S05_ESM_IT2012_NVL_MP_RotD_16PERIOD_20261030.csv';
function parse(csv) {
  const lines = csv.trim().split(/\r?\n/);
  const head = lines.shift().split(',');
  const needed = ['period_s','HNE_psa_m_s2','HNN_psa_m_s2','RotD100_psa_m_s2'];
  for (const k of needed) assert(head.includes(k), 'missing column: '+k);
  const rows = lines.map((line,i) => {
    const cells=line.split(',');
    assert.equal(cells.length,head.length,'column count row '+(i+2));
    const v=Object.fromEntries(needed.map(k=>[k,Number(cells[head.indexOf(k)])]));
    for (const k of needed) assert(Number.isFinite(v[k]),'nonfinite '+k);
    assert(v.period_s>0 && v.HNE_psa_m_s2>=0 && v.HNN_psa_m_s2>=0 && v.RotD100_psa_m_s2>0,'invalid spectrum');
    return v;
  });
  assert.equal(rows.length,16,'expected 16 archived periods');
  for(let i=1;i<rows.length;i++) assert(rows[i].period_s>rows[i-1].period_s,'period order');
  return rows;
}
function calculate(rows) {
  return rows.map(r=>{
    const fixed=Math.max(r.HNE_psa_m_s2,r.HNN_psa_m_s2);
    const loss=100*(r.RotD100_psa_m_s2-fixed)/r.RotD100_psa_m_s2;
    assert(loss>=-1e-8,'RotD100 must envelop fixed axes');
    return {period_s:r.period_s,fixed_axis_max_m_s2:fixed,RotD100_m_s2:r.RotD100_psa_m_s2,miss_pct:Math.max(0,loss)};
  });
}
function tests() {
  assert.throws(()=>parse('period_s,HNE_psa_m_s2\n1,1'),/missing column/);
  const fixture=Array.from({length:16},(_,i)=>({period_s:i+1,HNE_psa_m_s2:1,HNN_psa_m_s2:2,RotD100_psa_m_s2:2.5}));
  assert.equal(calculate(fixture)[0].miss_pct,20);
  assert.throws(()=>calculate([{...fixture[0],RotD100_psa_m_s2:1}]),/envelop/);
  const swapped=fixture.map(r=>({...r,HNE_psa_m_s2:r.HNN_psa_m_s2,HNN_psa_m_s2:r.HNE_psa_m_s2}));
  assert.deepEqual(calculate(fixture),calculate(swapped));
}
function main() {
  tests();
  const rows=calculate(parse(fs.readFileSync(process.argv[2]||DEFAULT,'utf8')));
  const mean=rows.reduce((s,r)=>s+r.miss_pct,0)/rows.length;
  const peak=rows.reduce((a,b)=>a.miss_pct>=b.miss_pct?a:b);
  assert(Math.abs(mean-5.604572292457635)<1e-10,'mean regression');
  assert(Math.abs(peak.miss_pct-17.36042393879074)<1e-10 && peak.period_s===0.5,'peak regression');
  assert.equal(rows.filter(r=>r.miss_pct>10).length,3);
  console.log('S05_AXIS_ENVELOPE_SOURCE_QC_PASS '+JSON.stringify({count:rows.length,mean_miss_pct:mean,max:peak,over10:3}));
  console.log('period_s,fixed_axis_max_m_s2,RotD100_m_s2,miss_pct');
  for(const r of rows) console.log([r.period_s,r.fixed_axis_max_m_s2,r.RotD100_m_s2,r.miss_pct].join(','));
}
if(require.main===module) main();
module.exports={parse,calculate,tests};
