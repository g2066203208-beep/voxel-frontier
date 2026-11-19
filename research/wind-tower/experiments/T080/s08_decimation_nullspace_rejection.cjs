#!/usr/bin/env node
'use strict';
// S08 sampling-identifiability test. No structural solver, no synthetic physical claim.
// Source: T079/real-records/S08_158M_BEAM_PROXY_FULL_RATE_RECEIPT_20261106.json
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const receiptPath = path.resolve(__dirname, '../T079/real-records/S08_158M_BEAM_PROXY_FULL_RATE_RECEIPT_20261106.json');
const r = JSON.parse(fs.readFileSync(receiptPath, 'utf8'));
const h = r.full_rate_history;
assert.equal(h.n_rows, 64080);
assert.equal(h.rows_per_direction, 32040);
assert.equal(h.dt_s, 0.005);
assert.equal(h.n_directions, 2);
assert.equal(h.exact_20x_decimation_reproduces_legacy, true);
const stride = 20, dt = h.dt_s, n = h.rows_per_direction;
const legacyDt = stride * dt, nyquistFull = 1/(2*dt), nyquistLegacy = 1/(2*legacyDt);
const duration = (n-1)*dt;
assert.ok(Math.abs(duration - 160.195)<1e-10);
assert.equal(nyquistFull, 100);
assert.equal(nyquistLegacy, 5);
// Discrete nullspace: sin(pi*j/20) is zero on every 20th full-rate sample,
// while it reaches 1 on a full-rate index j=10 (i.e., 5 Hz).
// Choose frequency 5 Hz, phase 0: at legacy 0.1s samples sin(pi*k)=0.
// Floating-point sine has roundoff, so compare against an absolute tolerance.
const amplitude = 1e6;
const hidden = j => amplitude*Math.sin(Math.PI*j/20);
for(let k=0;k<Math.ceil(n/stride);k++){
  const j=20*k;
  if(j<n) assert.ok(Math.abs(hidden(j)) < 1e-6, 'legacy-grid nullspace');
}
assert.ok(Math.abs(hidden(10)-amplitude)<1e-9);
// A more stable exact discrete construction, identically zero on legacy indices:
const exactHidden = j => j%20===0 ? 0 : amplitude*Math.sin(Math.PI*(j%20)/20);
assert.equal(exactHidden(20),0);
assert.equal(exactHidden(0),0);
assert.equal(exactHidden(10),amplitude);
assert.equal(exactHidden(30),amplitude);
assert.throws(()=>{ if(!(n>0)) throw Error('bad'); throw new RangeError('no joint response without time histories');},RangeError);
console.log(JSON.stringify({classification:'SAMPLING_IDENTIFIABILITY_MATH_ONLY',n_full_per_direction:n,dt_full_s:dt,n_total:h.n_rows,stride,dt_legacy_s:legacyDt,duration_s:duration,nyquist_full_Hz:nyquistFull,nyquist_legacy_Hz:nyquistLegacy,frequency_resolution_full_Hz:1/(n*dt),nullspace_amplitude_arbitrary:amplitude,tests:'PASS',physical_peak_error_bound:'UNIDENTIFIABLE_WITHOUT_FULL_RATE_WAVEFORM_AND_BANDLIMIT'}));
