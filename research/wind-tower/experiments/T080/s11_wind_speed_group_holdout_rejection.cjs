// S11: leave-one-wind-speed-class-out absolute gross-elastic DEL4 test.
// Usage: node s11_wind_speed_group_holdout_rejection.cjs <T077 1984-row CSV>
// No Abaqus, structural production run, or held-out response calibration.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
function analyze(csv){
 const [header,...lines]=csv.trim().split(/\r?\n/),cols=header.split(','),ix=k=>cols.indexOf(k);
 for(const k of ['case','segment','azimuth_deg','DEL_m4_MPa'])assert(ix(k)>=0,k);
 const speed=c=>c.startsWith('U09p343881_')?9.343881:c.startsWith('U11p4_')?11.4:c.startsWith('U19p202140_')?19.202140:NaN;
 const rows=lines.map(line=>{const v=line.split(',');return {c:v[ix('case')],s:v[ix('segment')],a:+v[ix('azimuth_deg')],y:+v[ix('DEL_m4_MPa')],u:speed(v[ix('case')])};});
 assert.equal(rows.length,1984);assert(rows.every(x=>Number.isFinite(x.u)&&Number.isFinite(x.y)&&x.y>0));
 const classes=[...new Set(rows.map(x=>x.u))].sort((a,b)=>a-b);assert.equal(classes.length,3);
 const results=classes.map(held=>{
  const train=rows.filter(x=>x.u!==held),test=rows.filter(x=>x.u===held);
  const speeds=[...new Set(train.map(x=>x.u))].sort((a,b)=>a-b),[lo,hi]=speeds;
  const cells=new Map();
  for(const x of train){const key=[x.u,x.s,x.a].join('|');if(!cells.has(key))cells.set(key,[]);cells.get(key).push(x.y);}
  const value=(u,s,a)=>{const a0=cells.get([u,s,a].join('|'));assert(a0&&a0.length);return a0.reduce((p,q)=>p+q,0)/a0.length;};
  const linear=x=>value(lo,x.s,x.a)+(held-lo)/(hi-lo)*(value(hi,x.s,x.a)-value(lo,x.s,x.a));
  const nearest=x=>value(Math.abs(held-lo)<Math.abs(held-hi)?lo:hi,x.s,x.a);
  const score=fn=>({MAE_MPa:test.reduce((z,x)=>z+Math.abs(fn(x)-x.y),0)/test.length,MAPE_pct:100*test.reduce((z,x)=>z+Math.abs(fn(x)-x.y)/x.y,0)/test.length,RMSE_MPa:Math.sqrt(test.reduce((z,x)=>z+(fn(x)-x.y)**2,0)/test.length),nonpositive:test.filter(x=>fn(x)<=0).length});
  return {held_speed_mps:held,n:test.length,train_speeds_mps:speeds,reject_extrapolation:held<lo||held>hi,linear:score(linear),nearest:score(nearest)};
 });
 assert.deepEqual(results.map(x=>x.n),[496,496,992]);
 const expected=[0.1514054956820243,0.11982712911889912,0.5761703339740974];
 results.forEach((r,i)=>assert(Math.abs(r.linear.MAE_MPa-expected[i])<1e-8,'source regression mismatch'));
 assert.deepEqual(results.map(r=>r.reject_extrapolation),[true,false,true]);
 return {source_rows:rows.length,wind_speed_classes:3,results};
}
if(require.main===module){assert.equal(process.argv.length,3,'T077 archived CSV path required');console.log(JSON.stringify({status:'SOURCE_LEVEL_TEST_PASS',...analyze(fs.readFileSync(process.argv[2],'utf8'))},null,2));}
module.exports={analyze};
