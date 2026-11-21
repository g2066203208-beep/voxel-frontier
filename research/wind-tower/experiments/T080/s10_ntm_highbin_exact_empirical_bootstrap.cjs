'use strict';
// Exact empirical six-draw-with-replacement enumeration within the high NTM wind bin.
// Not independent experiments, not a population confidence interval, not full-climate fatigue.
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const HOURS=[5736,1426,2], BINS=['U09p343881','U11p4','U19p202140'];
function evaluate(csv){
 const [header,...lines]=csv.trim().split(/\r?\n/),keys=header.split(',');
 for(const k of ['case_id','channel','m','Neq','DEL'])assert(keys.includes(k));
 const rows=lines.map(l=>{const a=l.split(',');assert.equal(a.length,keys.length);return Object.fromEntries(keys.map((k,i)=>[k,a[i]]))});
 assert.equal(rows.length,72);
 const result={method:'exact empirical high-bin six-draw bootstrap',draws:6**6,hours:HOURS,channels:{}};
 for(const ch of ['TwrBsMxt','TwrBsMyt']){
  const v=BINS.map(bin=>{
   const a=rows.filter(r=>r.case_id.startsWith(bin+'_NTM_S')&&r.channel===ch).sort((x,y)=>x.case_id.localeCompare(y.case_id));
   assert.equal(a.length,6);assert.equal(new Set(a.map(r=>r.case_id)).size,6);
   return a.map(r=>{assert.equal(Number(r.m),4);assert.equal(Number(r.Neq),100000);const d=Number(r.DEL);assert(Number.isFinite(d)&&d>0);return (d/1000)**4});
  });
  const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
  const fixed=HOURS[0]*mean(v[0])+HOURS[1]*mean(v[1]),hi=v[2];
  const share=x=>100*(HOURS[2]*x)/(fixed+HOURS[2]*x);
  const samples=[];
  for(let j=0;j<6**6;j++){let n=j,s=0;for(let k=0;k<6;k++){s+=hi[n%6];n=Math.floor(n/6)}samples.push(share(s/6))}
  samples.sort((a,b)=>a-b);
  const q=p=>samples[Math.ceil(p*samples.length)-1]; // empirical inverse CDF
  result.channels[ch]={original_pct:share(mean(hi)),min_pct:samples[0],q025_pct:q(.025),median_pct:q(.5),q975_pct:q(.975),max_pct:samples.at(-1),count_gt5:samples.filter(x=>x>5).length,critical_high_hours_all_below5:fixed/(19*Math.max(...hi)),critical_high_hours_all_above5:fixed/(19*Math.min(...hi))};
 }
 return result;
}
function selftest(){
 const h=['case_id,channel,m,Neq,DEL'];for(const b of BINS)for(const t of ['NTM','ETM'])for(let i=1;i<=6;i++)for(const c of ['TwrBsMxt','TwrBsMyt'])h.push(b+'_'+t+'_S0'+i+','+c+',4,100000,'+(100+i));
 const csv=h.join('\n');const r=evaluate(csv);assert.equal(r.draws,46656);assert(r.channels.TwrBsMxt.min_pct<=r.channels.TwrBsMxt.median_pct);assert(r.channels.TwrBsMxt.median_pct<=r.channels.TwrBsMxt.max_pct);assert(r.channels.TwrBsMxt.critical_high_hours_all_below5>0);assert(r.channels.TwrBsMxt.critical_high_hours_all_above5>=r.channels.TwrBsMxt.critical_high_hours_all_below5);
 assert.throws(()=>evaluate(csv.replace('100000','99999')));assert.throws(()=>evaluate(csv.replace('NTM_S01','NTM_S02')));return true;
}
if(require.main===module){
 if(process.argv[2]==='--self-test'){selftest();console.log('PASS')}else{assert.equal(process.argv.length,3);const b=fs.readFileSync(process.argv[2]);const r=evaluate(b.toString('utf8'));r.source_sha256=crypto.createHash('sha256').update(b).digest('hex');console.log(JSON.stringify(r,null,2))}
}
module.exports={evaluate,selftest};
