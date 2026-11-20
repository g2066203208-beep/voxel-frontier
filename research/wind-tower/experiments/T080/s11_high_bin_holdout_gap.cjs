// S11 high-bin holdout gap, retrospective source-level test; Node >=18.
// SOURCE: T077/recovery/S11_ETM4_CASE_VS_BIN_HOLDOUT_7ROW_20261113.csv
const fs=require('node:fs');const assert=require('node:assert/strict');
const path=process.argv[2];if(!path)throw Error('Usage: node s11_high_bin_holdout_gap.cjs <source.csv>');
const [header,...lines]=fs.readFileSync(path,'utf8').trim().split(/\r?\n/);
const keys=header.split(',');const rows=lines.map(s=>Object.fromEntries(s.split(',').map((v,i)=>[keys[i],v])));
assert.equal(rows.length,7);const high=rows.find(r=>r.type==='LOBO'&&r.held==='19.202140');
const cases=rows.filter(r=>r.type==='LOCO'&&r.held.startsWith('U19p202140'));
assert.ok(high&&cases.length===2);assert.equal(+high.n,cases.reduce((s,r)=>s+(+r.n),0));
const out={source_rows:rows.length,high_bin_n:+high.n,comparisons:{}};
for(const k of ['mean_rmse_MPa','nearest_rmse_MPa','linear_rmse_MPa']){
  const pooled=Math.sqrt(cases.reduce((s,r)=>s+(+r.n)*(+r[k])**2,0)/(+high.n));
  const held=+high[k];assert.ok(Number.isFinite(pooled)&&pooled>0&&Number.isFinite(held));
  out.comparisons[k]={same_bin_LOCO_pooled_MPa:pooled,LOBO_MPa:held,LOBO_to_LOCO_ratio:held/pooled};
}
assert.ok(out.comparisons.nearest_rmse_MPa.LOBO_to_LOCO_ratio>6);
assert.ok(out.comparisons.linear_rmse_MPa.LOBO_to_LOCO_ratio>6);
console.log(JSON.stringify(out,null,2));
