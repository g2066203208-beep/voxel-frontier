'use strict';
// SOURCE: T062/recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv
// 20 common-index 3/3 seed splits, pilot allocation vs untouched holdout variance.
// The 20 splits overlap: NOT 20 independent experiments or coverage probabilities.
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const B=['U09p343881','U11p4','U19p202140'], HOURS=[5736,1426,2],H=7164;
function choose(){let a=[];for(let i=0;i<6;i++)for(let j=i+1;j<6;j++)for(let k=j+1;k<6;k++)a.push([i,j,k]);return a}
function allocations(){let a=[];for(let i=2;i<=14;i++)for(let j=2;j<=16-i;j++){let k=18-i-j;if(k>=2)a.push([i,j,k])}return a}
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
const variance=x=>{assert(x.length>=2);let m=mean(x);return x.reduce((s,v)=>s+(v-m)**2,0)/(x.length-1)};
const risk=(n,v)=>n.reduce((s,x,i)=>s+(HOURS[i]/H)**2*v[i]/x,0);
function analyze(csv){
 let [header,...lines]=csv.trim().split(/\r?\n/),keys=header.split(',');
 for(let k of ['case_id','channel','m','Neq','DEL'])assert(keys.includes(k));
 let rows=lines.map(l=>{let x=l.split(',');assert.equal(x.length,keys.length);return Object.fromEntries(keys.map((k,i)=>[k,x[i]]))});
 assert.equal(rows.length,72);
 let output={source_rows:rows.length,independent_seed_splits:false,splits:20,channels:{}};
 for(let channel of ['TwrBsMxt','TwrBsMyt']){
  let values=B.map(bin=>{let x=rows.filter(r=>r.case_id.startsWith(bin+'_NTM_S')&&r.channel===channel).sort((a,b)=>a.case_id.localeCompare(b.case_id));assert.equal(x.length,6);assert.equal(new Set(x.map(r=>r.case_id)).size,6);return x.map(r=>{assert.equal(Number(r.m),4);assert.equal(Number(r.Neq),100000);let d=Number(r.DEL);assert(Number.isFinite(d)&&d>0);return d**4/1e12})});
  let folds=choose().map(indices=>{
   let train=values.map(v=>indices.map(i=>v[i])),test=values.map(v=>v.filter((_,i)=>!indices.includes(i)));
   let pv=train.map(variance),tv=test.map(variance),alloc=allocations();
   let best=alloc.reduce((a,n)=>risk(n,pv)<risk(a,pv)?n:a,alloc[0]);
   let oracle=alloc.reduce((a,n)=>risk(n,tv)<risk(a,tv)?n:a,alloc[0]);
   return {pilot_indices:indices.map(i=>i+1),allocation:best,holdout_ratio_vs_equal:risk(best,tv)/risk([6,6,6],tv),holdout_regret_vs_oracle:risk(best,tv)/risk(oracle,tv)};
  });
  let ratio=folds.map(f=>f.holdout_ratio_vs_equal);
  output.channels[channel]={better:ratio.filter(x=>x<1).length,worse:ratio.filter(x=>x>1).length,mean_ratio:mean(ratio),min_ratio:Math.min(...ratio),max_ratio:Math.max(...ratio),mean_oracle_regret:mean(folds.map(f=>f.holdout_regret_vs_oracle)),folds};
 }
 return output;
}
function selftest(){let a=['case_id,channel,m,Neq,DEL'];for(let b of B)for(let t of ['NTM','ETM'])for(let i=1;i<=6;i++)for(let c of ['TwrBsMxt','TwrBsMyt'])a.push(b+'_'+t+'_S0'+i+','+c+',4,100000,'+(100+i));let csv=a.join('\n');assert.equal(analyze(csv).splits,20);assert.throws(()=>analyze(csv.replace('100000','99999')));assert.throws(()=>analyze(csv.replace('NTM_S01','NTM_S02')));return true}
if(require.main===module){if(process.argv[2]==='--self-test'){selftest();console.log('PASS')}else{assert.equal(process.argv.length,3);let b=fs.readFileSync(process.argv[2]);let x=analyze(b.toString('utf8'));x.source_sha256=crypto.createHash('sha256').update(b).digest('hex');console.log(JSON.stringify(x,null,2))}}
module.exports={analyze,selftest};
