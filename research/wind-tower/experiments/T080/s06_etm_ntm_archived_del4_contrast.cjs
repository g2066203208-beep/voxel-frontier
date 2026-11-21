'use strict';
// Archived 36-case ETM/NTM DEL4 comparison, matched by nominal wind speed and seed label only.
// Seed labels DO NOT prove paired stochastic inflow histories; not a causal turbulence contrast.
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const BINS=['U09p343881','U11p4','U19p202140'],CH=['TwrBsMxt','TwrBsMyt'];
function analyze(csv){
 const [head,...lines]=csv.trim().split(/\r?\n/),keys=head.split(',');
 for(const k of ['case_id','channel','m','Neq','DEL'])assert(keys.includes(k));
 const map=new Map();
 for(const line of lines){const a=line.split(',');assert.equal(a.length,keys.length);const r=Object.fromEntries(keys.map((k,i)=>[k,a[i]]));
  const key=r.case_id+'|'+r.channel;assert(!map.has(key));assert.equal(Number(r.m),4);assert.equal(Number(r.Neq),1e5);
  const d=Number(r.DEL);assert(Number.isFinite(d)&&d>0);map.set(key,d);
 }
 assert.equal(map.size,72);
 const result=[];
 for(const bin of BINS)for(const channel of CH){
  const ratios=[];for(let s=1;s<=6;s++){const stem=bin+'_',seed='S0'+s;
   const e=map.get(stem+'ETM_'+seed+'|'+channel),n=map.get(stem+'NTM_'+seed+'|'+channel);
   assert(e!==undefined&&n!==undefined);ratios.push(e/n);
  }
  result.push({bin,channel,n:6,etm_gt_ntm:ratios.filter(x=>x>1).length,
   geometric_ratio:Math.exp(ratios.reduce((a,x)=>a+Math.log(x),0)/6),
   min_ratio:Math.min(...ratios),max_ratio:Math.max(...ratios)});
 }
 return {source_rows:map.size,comparisons:36,all_gt:result.every(x=>x.etm_gt_ntm===6),results:result};
}
function selftest(){const lines=['case_id,channel,m,Neq,DEL'];
 for(const b of BINS)for(const c of CH)for(let s=1;s<=6;s++)for(const t of ['NTM','ETM'])
  lines.push(b+'_'+t+'_S0'+s+','+c+',4,100000,'+(t==='ETM'?120:100));
 const c=lines.join('\n'),r=analyze(c);assert(r.all_gt);assert.equal(r.results.length,6);
 assert(Math.abs(r.results[0].geometric_ratio-1.2)<1e-12);
 assert.throws(()=>analyze(c.replace('120','0')));assert.throws(()=>analyze(c.replace('ETM_S01','NTM_S01')));
 const flipped=c.replace('ETM_S01,TwrBsMxt,4,100000,120','ETM_S01,TwrBsMxt,4,100000,80');
 assert(!analyze(flipped).all_gt);return true;}
if(require.main===module){if(process.argv[2]==='--self-test'){selftest();console.log('PASS')}
 else{assert.equal(process.argv.length,3);const b=fs.readFileSync(process.argv[2]);const result=analyze(b.toString('utf8'));result.source_sha256=crypto.createHash('sha256').update(b).digest('hex');console.log(JSON.stringify(result,null,2));}}
module.exports={analyze,selftest};
