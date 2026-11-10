#!/usr/bin/env node
'use strict';
// A summary-identifiability falsifier, not a rainflow reconstruction or a physical RUN.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const SOURCE = path.join(__dirname, 'S12_NTM18_DEL_NORMALIZATION_CROSSWALK_36ROW_20261110.csv');
const SOURCE_SHA256 = 'c630110d2aa1dcb15ae607469c7f8cba713c1bf1705544236b372a4f24c15142';
const NA = 100000, NB = 600;
const EXPECTED_FACTOR = Math.pow(NA / NB, 0.25);
function reject(s) { throw Error(s); }
function parseCsv(s) {
  const lines = s.trim().split(/\r?\n/), fields = lines.shift().split(',');
  if (new Set(fields).size !== fields.length) reject('duplicate header');
  return lines.map((line, index) => {
    const vals = line.split(',');
    if (vals.length !== fields.length) reject('CSV columns row ' + (index + 2));
    return Object.fromEntries(fields.map((f, i) => [f, vals[i]]));
  });
}
function analyze(rows, expectedCount = 36) {
  if (rows.length !== expectedCount) reject('wrong cardinality');
  const seen = new Set();
  let maxIdentityResidual = 0, maxCrosswalkResidual = 0;
  let minCount = Infinity, maxCount = 0, example;
  for (const row of rows) {
    const key = row.case + '|' + row.channel;
    if (seen.has(key)) reject('duplicate case/channel');
    seen.add(key);
    if (!/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(row.case) ||
        !['TwrBsMxt', 'TwrBsMyt'].includes(row.channel) ||
        !/^[a-f0-9]{64}$/.test(row.outb_sha256)) reject('source identity');
    const C = Number(row.weighted_cycles), L = Number(row.corrected_DEL_Neq100000_kNm);
    const native = Number(row.native_DEL_Nref600_kNm);
    if (![C, L, native].every(Number.isFinite) || C <= 16 || L <= 0 || native <= 0 ||
        Math.abs(2 * C - Math.round(2 * C)) > 1e-10) reject('cycle count or DEL');
    const ratioResidual = Math.abs(native / L / EXPECTED_FACTOR - 1);
    if (ratioResidual > 2e-12) reject('crosswalk ratio');
    // A: all C weighted cycles have range r0. B: one full cycle has range 2*r0,
    // and C-1 weighted cycles have range r1. Both have the SAME fourth-power sum.
    const r0 = L * Math.pow(NA / C, 0.25);
    const r1 = r0 * Math.pow((C - 16) / (C - 1), 0.25);
    const sumA = C * Math.pow(r0, 4);
    const sumB = Math.pow(2 * r0, 4) + (C - 1) * Math.pow(r1, 4);
    const identityResidual = Math.abs(sumA - sumB) / sumA;
    if (identityResidual > 1e-12 || Math.abs(Math.pow(sumB / NB, .25) / native - 1) > 2e-12)
      reject('fourth-power identity');
    maxIdentityResidual = Math.max(maxIdentityResidual, identityResidual);
    maxCrosswalkResidual = Math.max(maxCrosswalkResidual, ratioResidual);
    minCount = Math.min(minCount, C); maxCount = Math.max(maxCount, C);
    if (key === 'U09p343881_NTM_S01|TwrBsMyt')
      example = {case:row.case, channel:row.channel, C, r0_kNm:r0,
                 r1_kNm:r1, constructed_max_kNm:2*r0, native_DEL_kNm:native};
  }
  if (expectedCount === 36 && !example) reject('missing exemplar');
  return {matched_rows:rows.length, min_weighted_cycles:minCount,
          max_weighted_cycles:maxCount, max_relative_fourth_sum_residual:maxIdentityResidual,
          max_relative_crosswalk_residual:maxCrosswalkResidual,
          constructed_max_range_ratio:2, example};
}
function selftest() {
  const base = {case:'U09p343881_NTM_S01',channel:'TwrBsMyt',
    outb_sha256:'a'.repeat(64),weighted_cycles:'678',
    corrected_DEL_Neq100000_kNm:'14214.854620029',
    native_DEL_Nref600_kNm:String(14214.854620029 * EXPECTED_FACTOR)};
  if (analyze([base], 1).constructed_max_range_ratio !== 2) reject('positive selftest');
  const negatives = [
    [base,base], [{...base, weighted_cycles:'16'}],
    [{...base,weighted_cycles:'678.3'}], [{...base, native_DEL_Nref600_kNm:'1'}],
    [{...base,outb_sha256:'wrong'}], [{...base,channel:'unknown'}],
    [{...base, corrected_DEL_Neq100000_kNm:'NaN'}], []
  ];
  for (const rows of negatives) {
    let failed = false;
    try { analyze(rows, 1); } catch (_) { failed = true; }
    if (!failed) reject('negative selftest not rejected');
  }
  return {positive:1, negative_rejections:negatives.length};
}
if (require.main === module) {
  if (process.argv.includes('--selftest')) console.log(JSON.stringify(selftest()));
  else {
    const bytes = fs.readFileSync(SOURCE);
    if (crypto.createHash('sha256').update(bytes).digest('hex') !== SOURCE_SHA256)
      reject('source SHA256 mismatch');
    console.log(JSON.stringify(analyze(parseCsv(bytes.toString('utf8'))), null, 2));
  }
}
module.exports = {analyze, parseCsv, selftest};
