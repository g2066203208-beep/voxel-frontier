'use strict';
// Source-level, conditional seed bootstrap for historical 158 m OpenFAST NTM load DEL.
// NOT a DLC1.2 compliance test, material fatigue model, or population guarantee.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const SOURCE_SHA256 = 'cbe5f3c13290641789a11fc7551169a4b16fd9b347b03de74f8bde1209e76a49';
const SOURCE_NAME = 'S10_RAINFLOW_MEAN_HETEROGENEITY_72ROW_20261110.csv';
const SPEEDS = ['09p343881', '11p4', '19p202140'];
const CHANNELS = ['TwrBsMxt', 'TwrBsMyt'];
const FACT = [1, 1, 2, 6, 24, 120, 720];
const N_BOOT = 6 ** 6; // 46,656 ordered resamples; 462 distinct count vectors.
function assert(ok, message) { if (!ok) throw Error(message); }
function sha256(s) { return crypto.createHash('sha256').update(s).digest('hex'); }
function parse(text, expectedSha = SOURCE_SHA256) {
  if (expectedSha !== null) assert(sha256(text) === expectedSha, 'SOURCE_SHA256_MISMATCH');
  const lines = text.trim().split(/\r?\n/), header = lines.shift().split(',');
  for (const name of ['case_id', 'channel', 'DEL_m4_kNm']) assert(header.includes(name), 'MISSING_COLUMN_' + name);
  assert(lines.length === 72, 'EXPECTED_72_SOURCE_ROWS');
  const result = new Map(), seen = new Set();
  for (const line of lines) {
    const parts = line.split(',');
    assert(parts.length === header.length, 'BAD_CSV_WIDTH');
    const row = Object.fromEntries(header.map((name, i) => [name, parts[i]]));
    const match = /^U(09p343881|11p4|19p202140)_(NTM|ETM)_(S0[1-6])$/.exec(row.case_id);
    assert(match && CHANNELS.includes(row.channel), 'BAD_CASE_OR_CHANNEL');
    const key = row.case_id + ':' + row.channel;
    assert(!seen.has(key), 'DUPLICATE_CASE_CHANNEL'); seen.add(key);
    const del = Number(row.DEL_m4_kNm);
    assert(row.DEL_m4_kNm.trim() && Number.isFinite(del) && del > 0, 'BAD_DEL');
    if (match[2] === 'NTM') result.set(match[1] + ':' + row.channel + ':' + match[3], del);
  }
  assert(seen.size === 72 && result.size === 36, 'SOURCE_CASE_COUNT');
  return Object.fromEntries(CHANNELS.map(ch => [ch, SPEEDS.map(speed =>
    Array.from({length: 6}, (_, i) => {
      const key = speed + ':' + ch + ':S0' + (i + 1);
      assert(result.has(key), 'MISSING_NTM_SEED_' + key); return result.get(key);
    }))]));
}
function countVectors() {
  const out = [];
  function rec(a, rem) {
    if (a.length === 5) { out.push([...a, rem]); return; }
    for (let i = 0; i <= rem; i++) rec([...a, i], rem - i);
  }
  rec([], 6);
  assert(out.length === 462, 'COMPOSITION_COUNT');
  assert(out.reduce((s, c) => s + 720 / c.reduce((p, x) => p * FACT[x], 1), 0) === N_BOOT, 'MULTINOMIAL_MASS');
  return out.map(c => ({c, weight: 720 / c.reduce((p, x) => p * FACT[x], 1)}));
}
const COUNTS = countVectors();
function root4(x) { return Math.sqrt(Math.sqrt(x)); }
function sampleValue(powers, c) { return root4(c.reduce((s, n, i) => s + n * powers[i], 0) / 6); }
function distribution(vals) {
  assert(vals.length === 6 && vals.every(x => Number.isFinite(x) && x > 0), 'INVALID_SIX_SEEDS');
  const powers = vals.map(x => x ** 4);
  const points = COUNTS.map(({c, weight}) => ({value: sampleValue(powers, c), weight})).sort((a, b) => a.value - b.value);
  const cum = []; let total = 0;
  for (const p of points) { total += p.weight; cum.push(total); }
  assert(total === N_BOOT, 'BOOT_MASS');
  function quantile(prob) {
    assert(prob >= 0 && prob <= 1, 'BAD_QUANTILE');
    const target = Math.max(1, Math.ceil(prob * N_BOOT - 1e-10));
    let lo = 0, hi = points.length - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (cum[mid] >= target) hi = mid; else lo = mid + 1; }
    return points[lo].value;
  }
  function cdfStrict(x) {
    let lo = 0, hi = points.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (points[mid].value < x) lo = mid + 1; else hi = mid; }
    return lo ? cum[lo - 1] / N_BOOT : 0;
  }
  return {points, quantile, cdfStrict, observed: root4(powers.reduce((a, b) => a + b, 0) / 6),
    bootMean: points.reduce((s, p) => s + p.value * p.weight, 0) / N_BOOT};
}
function analyze(data) {
  const rows = [], checks = {};
  for (const ch of CHANNELS) {
    const d = data[ch].map(distribution);
    const independent = d.map((di, i) => di.points.reduce((s, p) =>
      s + (p.weight / N_BOOT) * d.reduce((prod, dj, j) => prod * (i === j ? 1 : dj.cdfStrict(p.value)), 1), 0));
    const paired = [0, 0, 0];
    const pow = data[ch].map(a => a.map(x => x ** 4));
    for (const {c, weight} of COUNTS) {
      const x = pow.map(a => c.reduce((s, n, i) => s + n * a[i], 0));
      const top = Math.max(...x), winner = x.indexOf(top);
      assert(x.filter(v => v === top).length === 1, 'TIED_PAIRED_MAX');
      paired[winner] += weight / N_BOOT;
    }
    assert(Math.abs(independent.reduce((a, b) => a + b, 0) - 1) < 1e-10, 'INDEPENDENT_RANK_MASS');
    assert(Math.abs(paired.reduce((a, b) => a + b, 0) - 1) < 1e-10, 'PAIRED_RANK_MASS');
    checks[ch] = {independent, paired};
    for (let i = 0; i < 3; i++) rows.push({channel: ch, wind_bin: SPEEDS[i],
      observed_kNm: d[i].observed, bootstrap_q025_kNm: d[i].quantile(.025),
      bootstrap_q975_kNm: d[i].quantile(.975), bootstrap_bias_kNm: d[i].bootMean - d[i].observed,
      p_bin_max_independent: independent[i], p_bin_max_shared_label: paired[i]});
  }
  return {rows, checks};
}
function selfTest() {
  const d = distribution([1, 1, 1, 1, 1, 1]);
  assert(d.observed === 1 && d.quantile(.025) === 1 && d.quantile(.975) === 1, 'CONSTANT_TEST');
  assert(d.cdfStrict(1) === 0 && d.cdfStrict(1.001) === 1, 'CDF_STRICT_TEST');
  const toy = Object.fromEntries(CHANNELS.map(ch => [ch, [1, 2, 3].map(v => Array(6).fill(v))]));
  for (const v of Object.values(analyze(toy).checks)) {
    assert(v.independent[2] > .9999999999 && v.paired[2] > .9999999999, 'RANK_TEST');
  }
  let rejected = 0;
  for (const bad of [[1, 2, 3], [1, 2, 3, 4, 5, NaN], [1, 2, 3, 4, 5, 0]]) {
    try { distribution(bad); } catch (_) { rejected++; }
  }
  assert(rejected === 3, 'REJECTION_TEST');
  console.log('S06_EXACT_BOOTSTRAP_SELFTEST_PASS 462 compositions 46656 ordered samples 3 rejects');
}
function main() {
  if (process.argv.includes('--selftest')) { selfTest(); return; }
  const idx = process.argv.indexOf('--input');
  const input = idx >= 0 ? process.argv[idx + 1] : path.join(__dirname, SOURCE_NAME);
  assert(input, 'MISSING_INPUT');
  const bytes = fs.readFileSync(input);
  const data = parse(bytes.toString('utf8'), SOURCE_SHA256);
  const {rows, checks} = analyze(data);
  const columns = Object.keys(rows[0]);
  const csv = [columns.join(','), ...rows.map(row => columns.map(k =>
    typeof row[k] === 'number' ? row[k].toFixed(12) : row[k]).join(','))].join('\n') + '\n';
  const oi = process.argv.indexOf('--out');
  if (oi >= 0) { assert(process.argv[oi + 1], 'MISSING_OUTPUT'); fs.writeFileSync(process.argv[oi + 1], csv); }
  else process.stdout.write(csv);
  console.error(JSON.stringify({source_sha256: sha256(bytes), rows: rows.length, checks, csv_sha256: sha256(csv)}));
}
if (require.main === module) main();
module.exports = {parse, distribution, analyze, selfTest};
