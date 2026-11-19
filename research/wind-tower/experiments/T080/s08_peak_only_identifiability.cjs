'use strict';
// S08 E-only proxy peak-envelope analysis. No solver, no inferred synchronous vector response.
const fs=require('fs'),crypto=require('crypto'),assert=require('assert');
const receiptPath=process.argv[2];
if(!receiptPath) throw Error('usage: node s08_peak_only_identifiability.cjs <S08_full_rate_receipt.json>');
const raw=fs.readFileSync(receiptPath);
const receipt=JSON.parse(raw.toString('utf8'));
assert.equal(receipt.classification,'REAL_ESM_E_ONLY_NONPRODUCTION_BEAM_PROXY_0P005S_NOT_S09_PAIRED');
assert.equal(receipt.full_rate_history.n_rows,64080);
assert.equal(receipt.full_rate_history.dt_s,0.005);
const rows=receipt.full_rate_history.eight_peak_integrator_checks;
assert.equal(rows.length,8);
const ids=['peak_top_relative_displacement_m','peak_top_absolute_acceleration_m_s2','peak_base_elastic_shear_kN','peak_base_elastic_moment_kNm'];
const output=ids.map(q=>{
 const e=rows.find(r=>r.direction==='HNE'&&r.qoi===q);
 const n=rows.find(r=>r.direction==='HNN'&&r.qoi===q);
 assert(e&&n&&e.full_rate_peak_abs>0&&n.full_rate_peak_abs>0);
 assert.equal(e.absolute_residual,0);assert.equal(n.absolute_residual,0);
 const lower=Math.max(e.full_rate_peak_abs,n.full_rate_peak_abs);
 const upper=Math.hypot(e.full_rate_peak_abs,n.full_rate_peak_abs);
 return {qoi:q,HNE:e.full_rate_peak_abs,HNN:n.full_rate_peak_abs,conditional_lower:lower,conditional_upper:upper,upper_over_lower:upper/lower};
});
assert.equal(output.length,4);
assert(output.every(x=>x.conditional_upper>=x.conditional_lower));
const sha=crypto.createHash('sha256').update(raw).digest('hex');
process.stdout.write(JSON.stringify({receipt_sha256:sha,classification:'CONDITIONAL_MATH_ENVELOPE_ONLY_NOT_PHYSICAL_VECTOR',rows:output},null,2)+'\n');
