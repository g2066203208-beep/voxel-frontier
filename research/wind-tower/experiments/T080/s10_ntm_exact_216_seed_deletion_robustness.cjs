'use strict';
// Historical 18 NTM runs, 3 observed bins x 6 seeds, two tower-base moment channels.
// Exhaustive 6^3 independent per-bin one-seed deletion: sensitivity, NOT a bootstrap CI.
// Usage: node s10_ntm_exact_216_seed_deletion_robustness.cjs <05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv>
// Source is load-DEL in kN m, m=4, Neq=100000; output conditional 3-bin DEL4 in kN m.
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const B=['U09p343881','U11p4','U19p202140'],H=[5736,1426,2],W=H.map(h=>h/7164);
function analyze(csv){
 const [header,...lines]=csv.trim().split(/\r?\n/),keys=header.split(',');
 for(const k of ['case_id','channel','m','Neq','DEL'])assert(keys.includes(k),'missing '+k);
 const rows=lines.map(line=>{const a=line.split(',');assert.equal(a.length,keys.length);return Object.fromEntries(keys.map((k,i)=>[k,a[i]]))});
 assert.equal(rows.length,72,'expected 36 runs x 2 channels');
 const result={source_rows:rows.length,bin_hours:H,conditioning_hours:7164,deleted_combinations:216,channels:{}};
 for(const channel of ['TwrBsMxt','TwrBsMyt']){
  const V=B.map(bin=>{
   const x=rows.filter(r=>r.case_id.startsWith(bin+'_NTM_S')&&r.channel===channel).sort((a,b)=>a.case_id.localeCompare(b.case_id));
   assert.equal(x.length,6);assert.equal(new Set(x.map(r=>r.case_id)).size,6);
   return x.map((r,i)=>{assert(r.case_id.endsWith('_S0'+(i+1)));assert.equal(Number(r.m),4);assert.equal(Number(r.Neq),100000);const d=Number(r.DEL);assert(Number.isFinite(d)&&d>0);return d**4});
  });
  function calc(drop){return (V.reduce((s,v,b)=>s+W[b]*v.reduce((t,x,i)=>t+(drop[b]===i?0:x),0)/(6-(drop[b]>=0?1:0)),0))**.25}
  const full=calc([-1,-1,-1]),all=[];
  for(let a=0;a<6;a++)for(let b=0;b<6;b++)for(let c=0;c<6;c++)all.push({dropped_seed:[a+1,b+1,c+1],DEL4:calc([a,b,c])});
  assert.equal(all.length,216);all.sort((a,b)=>a.DEL4-b.DEL4);
  const per_bin=B.map((bin,b)=>{const v=Array.from({length:6},(_,i)=>calc([-1,-1,-1].map((x,j)=>j===b?i:x)));return {bin,min:Math.min(...v),max:Math.max(...v),max_abs_change_pct:Math.max(...v.map(x=>Math.abs(x/full-1)))*100}});
  result.channels[channel]={full,minimum:all[0],maximum:all[215],range_pct:[100*(all[0].DEL4/full-1),100*(all[215].DEL4/full-1)],per_bin};
 }
 return result;
}
function selftest(){
 const mock=['case_id,channel,m,Neq,DEL'];
 for(const bin of B)for(const regime of ['NTM','ETM'])for(let i=1;i<=6;i++)for(const c of ['TwrBsMxt','TwrBsMyt'])mock.push(bin+'_'+regime+'_S0'+i+','+c+',4,100000,'+(100+i));
 const csv=mock.join('\n'),r=analyze(csv);assert.equal(r.deleted_combinations,216);
 for(const x of Object.values(r.channels)){assert(x.minimum.DEL4<=x.full&&x.full<=x.maximum.DEL4);assert(x.per_bin.every(v=>v.min<=x.full&&v.max>=x.full))}
 assert.throws(()=>analyze(csv.replace('100000','99999')));
 assert.throws(()=>analyze(csv.replace('NTM_S01','NTM_S02')));
 assert.throws(()=>analyze(csv.replace('100,','NaN,')));
 return true;
}
if(require.main===module){if(process.argv[2]==='--self-test'){selftest();console.log('self-test PASS')}else{assert.equal(process.argv.length,3);const b=fs.readFileSync(process.argv[2]);const r=analyze(b.toString('utf8'));r.source_sha256=crypto.createHash('sha256').update(b).digest('hex');console.log(JSON.stringify(r,null,2))}}
module.exports={analyze,selftest};
