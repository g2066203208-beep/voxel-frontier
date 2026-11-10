#!/usr/bin/env node
'use strict';
// Reconcile two archived rainflow DEL conventions; no physical solver.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const ROOT = __dirname;
const A = path.join(ROOT, 'legacy-primary-recovered-20261102', 'T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv');
const B = path.join(ROOT, 'S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv');
const OUTPUT = path.join(ROOT, 'S12_NTM18_DEL_NORMALIZATION_CROSSWALK_36ROW_20261110.csv');
const SHA_A = '12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2';
const SHA_B = '95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f';
const N_A = 100000, N_B = 600;
const CHANNELS = new Set(['TwrBsMxt', 'TwrBsMyt']);
const sha256 = s => crypto.createHash('sha256').update(s).digest('hex');
function fail(message) { throw new Error(message); }
function csv(text) {
  const lines = text.trim().split(/\r?\n/);
  const keys = lines.shift().split(',');
  if (new Set(keys).size !== keys.length) fail('duplicate header');
  return lines.map((line, index) => {
    const vals = line.split(',');
    if (vals.length !== keys.length) fail('column count at row ' + (index + 2));
    return Object.fromEntries(keys.map((key, i) => [key, vals[i]]));
  });
}
function finitePositive(value, name) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) fail('nonpositive/nonfinite ' + name);
  return n;
}
function evaluate(rowsA, rowsB, required = 36) {
  const keep = r => r.case.includes('_NTM_') && CHANNELS.has(r.channel);
  const a = rowsA.filter(keep), b = rowsB.filter(keep);
  if (a.length !== required || b.length !== required) fail('NTM channel cardinality');
  const map = new Map();
  for (const row of b) {
    const key = row.case + '|' + row.channel;
    if (map.has(key)) fail('duplicate native key ' + key);
    map.set(key, row);
  }
  const seen = new Set(), factor = Math.pow(N_A / N_B, 0.25), result = [];
  for (const row of a) {
    const key = row.case + '|' + row.channel;
    if (seen.has(key)) fail('duplicate corrected key ' + key);
    seen.add(key);
    const native = map.get(key);
    if (!native) fail('missing native key ' + key);
    if (!/^[a-f0-9]{64}$/.test(row.outb_sha256) || row.outb_sha256 !== native.outb_sha256) fail('OUTB SHA mismatch ' + key);
    const n1 = finitePositive(row.weighted_cycle_count, 'corrected cycle count');
    const n2 = finitePositive(native.rainflow_equivalent_cycles, 'native cycle count');
    if (Math.abs(n1 - n2) > 1e-8) fail('cycle-count mismatch ' + key);
    const d100k = finitePositive(row.one_line_fixed_DEL_kNm, 'corrected DEL');
    const d600 = finitePositive(native.DEL_m4_Nref600, 'native DEL');
    const ratio = d600 / d100k;
    const rel = ratio / factor - 1;
    if (Math.abs(rel) > 2e-10) fail('normalization mismatch ' + key);
    result.push({case:row.case, channel:row.channel, sha:row.outb_sha256, cycles:n1, d100k, d600, ratio, rel, implied:N_B * Math.pow(ratio, 4)});
  }
  if (seen.size !== map.size) fail('unpaired NTM channels');
  return result.sort((x,y) => (x.case + '|' + x.channel).localeCompare(y.case + '|' + y.channel, 'en'));
}
function render(rows) {
  const lines = ['case,channel,outb_sha256,weighted_cycles,corrected_DEL_Neq100000_kNm,native_DEL_Nref600_kNm,observed_ratio,expected_ratio,relative_ratio_residual,implied_corrected_Neq'];
  const factor = Math.pow(N_A/N_B, 0.25);
  for (const r of rows) lines.push([r.case,r.channel,r.sha,r.cycles.toFixed(1),r.d100k.toFixed(9),r.d600.toFixed(9),r.ratio.toPrecision(15),factor.toPrecision(15),r.rel.toExponential(8),r.implied.toFixed(6)].join(','));
  return lines.join('\n') + '\n';
}
function selftest() {
  const sha = 'a'.repeat(64), factor = Math.pow(N_A/N_B, 0.25);
  const a = {case:'U09p343881_NTM_S01',channel:'TwrBsMxt',outb_sha256:sha,weighted_cycle_count:'1',one_line_fixed_DEL_kNm:'10'};
  const b = {case:a.case,channel:a.channel,outb_sha256:sha,rainflow_equivalent_cycles:'1',DEL_m4_Nref600:String(10*factor)};
  const positive = evaluate([a],[b],1);
  if (Math.abs(positive[0].implied - 100000)>1e-6) fail('analytic oracle');
  const reject = (aa,bb) => {let failed=false;try{evaluate(aa,bb,1)}catch{failed=true}if(!failed)fail('negative case accepted')};
  reject([a],[{...b,outb_sha256:'b'.repeat(64)}]);
  reject([a],[{...b,rainflow_equivalent_cycles:'2'}]);
  reject([a],[{...b,DEL_m4_Nref600:String(10*factor*1.01)}]);
  reject([a,a],[b]);
  reject([a],[]);
  reject([{...a,one_line_fixed_DEL_kNm:'NaN'}],[b]);
  reject([a],[{...b,DEL_m4_Nref600:'0'}]);
  if (sha256('abc')!=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad') fail('SHA oracle');
  process.stdout.write('SELFTEST_PASS_1_ANALYTIC_7_REJECTIONS_SHA256\n');
}
function main() {
  if (process.argv.includes('--selftest')) return selftest();
  const textA=fs.readFileSync(A),textB=fs.readFileSync(B);
  if (sha256(textA)!==SHA_A || sha256(textB)!==SHA_B) fail('input SHA256 mismatch');
  const rows=evaluate(csv(textA.toString('utf8')),csv(textB.toString('utf8')));
  const out=render(rows);
  if (process.argv.includes('--write')) fs.writeFileSync(OUTPUT,out);
  else process.stdout.write(out);
  const worst=Math.max(...rows.map(r=>Math.abs(r.rel)));
  process.stderr.write('SOURCE_QC_PASS_36_NTM_CHANNELS worst_relative_ratio_residual='+worst.toExponential(5)+'\n');
}
if (require.main===module) main();
module.exports={csv,evaluate,render};
