'use strict';
// Conditional paired nonparametric bootstrap of six NTM seeds in each of three observed bins.
// Usage: node s10_ntm_paired_bootstrap_20261120.cjs <05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv>
// Not an ETM per-seed error model; not a DLC1.2 or physical verification.
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const bins=['U09p343881','U11p4','U19p202140'],channels=['TwrBsMxt','TwrBsMyt'];
const hours=[5736,1426,2],weights=hours.map(x=>x/7164);
function analyze(csv,n=20000,seed=20261120){
 const lines=csv.trim().split(/\r?\n/),cols=lines.shift().split(',');
 for(const k of ['case_id','channel','m','Neq','DEL'])assert(cols.includes(k));
 const rows=lines.map(s=>{let a=s.split(',');assert.equal(a.length,cols.length);return Object.fromEntries(cols.map((k,i)=>[k,a[i]]))});
 assert.equal(rows.length,72);assert(Number.isInteger(n)&&n>=1000&&n<=1e6);
 const data=bins.map(b=>Array.from({length:6},(_,i)=>channels.map(ch=>{
  const id=b+'_NTM_S0'+(i+1),matches=rows.filter(r=>r.case_id===id&&r.channel===ch);
  assert.equal(matches.length,1);const r=matches[0];assert.equal(+r.m,4);assert.equal(+r.Neq,100000);
  const d=+r.DEL;assert(Number.isFinite(d)&&d>0);return d;
 })));
 function calc(sample){return [0,1].map(c=>Math.pow(data.reduce((s,bin,b)=>s+weights[b]*sample[b].reduce((t,i)=>t+bin[i][c]**4,0)/6,0),.25))}
 const point=calc(bins.map(()=>[0,1,2,3,4,5]));let state=seed|0;
 function random(){state^=state<<13;state^=state>>>17;state^=state<<5;return(state>>>0)/4294967296}
 const draws=[[],[]];for(let k=0;k<n;k++){let sample=bins.map(()=>Array.from({length:6},()=>Math.floor(random()*6)));let v=calc(sample);for(let c=0;c<2;c++)draws[c].push(v[c])}
 function quant(a,p){a.sort((x,y)=>x-y);let z=(a.length-1)*p,l=Math.floor(z);return a[l]+(a[Math.ceil(z)]-a[l])*(z-l)}
 return {source_rows:rows.length,seed,n,observed_hours:7164,channels:Object.fromEntries(channels.map((ch,c)=>{let a=draws[c],q025=quant(a,.025),q975=quant(a,.975);return[ch,{point:point[c],q025,q975,relative_lower_pct:100*(q025/point[c]-1),relative_upper_pct:100*(q975/point[c]-1)}]}))};
}
if(require.main===module){assert.equal(process.argv.length,3);const b=fs.readFileSync(process.argv[2]);const r=analyze(b.toString('utf8'));r.source_sha256=crypto.createHash('sha256').update(b).digest('hex');console.log(JSON.stringify(r,null,2))}
module.exports={analyze};
