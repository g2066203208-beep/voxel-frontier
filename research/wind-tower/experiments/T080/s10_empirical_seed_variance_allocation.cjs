// Source-level pilot design only: 18 historical NTM runs, three bins, two channels.
// Usage: node s10_empirical_seed_variance_allocation.cjs <05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv>
// Output variance units: [(MN m)^4]^2 for the conditional three-bin mean.
// No formal DLC1.2 coverage or material fatigue claim.
'use strict';
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const bins=[['U09p343881',5736],['U11p4',1426],['U19p202140',2]];
function analyze(csv){
 const lines=csv.trim().split(/\r?\n/),head=lines.shift().split(',');
 for(const k of ['case_id','channel','m','Neq','DEL'])if(!head.includes(k))throw Error('missing '+k);
 const rows=lines.map(l=>{const a=l.split(',');if(a.length!==head.length)throw Error('CSV shape');return Object.fromEntries(head.map((k,i)=>[k,a[i]]));});
 const results={source_rows:rows.length,channels:{}};
 if(rows.length!==72)throw Error('expected 72 case-channel rows');
 for(const channel of ['TwrBsMxt','TwrBsMyt']){
  const groups=bins.map(([bin,hours])=>{
   const x=rows.filter(r=>r.case_id.startsWith(bin+'_NTM_S')&&r.channel===channel);
   if(x.length!==6||new Set(x.map(r=>r.case_id)).size!==6)throw Error('six distinct seeds required');
   const vals=x.map(r=>{const d=Number(r.DEL);if(Number(r.m)!==4||Number(r.Neq)!==100000||!Number.isFinite(d)||d<=0)throw Error('invalid DEL convention');return d**4/1e12;});
   const mean=vals.reduce((a,b)=>a+b,0)/6;
   const sd=Math.sqrt(vals.reduce((s,v)=>s+(v-mean)**2,0)/5);
   return {bin,hours,mean,sd,cv:sd/mean};
  });
  const H=groups.reduce((s,g)=>s+g.hours,0);
  if(H!==7164)throw Error('historical hour mismatch');
  const w=groups.map(g=>g.hours/H*g.sd);
  const variance=n=>n.reduce((s,v,i)=>s+w[i]**2/v,0);
  const equal=variance([6,6,6]);
  let best=null;
  for(let a=2;a<=14;a++)for(let b=2;b<=16-a;b++){
   const n=[a,b,18-a-b];if(n[2]<2)continue;
   const v=variance(n);if(!best||v<best.variance)best={allocation:n,variance:v};
  }
  if(!(best.variance<=equal))throw Error('optimization regression');
  results.channels[channel]={groups,equal_variance:equal,pilot_optimum:best,pilot_reduction:1-best.variance/equal};
 }
 return results;
}
function selftest(){
 const mock=['case_id,channel,m,Neq,DEL'];
 for(const [b] of bins)for(let i=1;i<=6;i++)for(const c of ['TwrBsMxt','TwrBsMyt'])mock.push(b+'_NTM_S0'+i+','+c+',4,100000,'+(100+i));
 const s=mock.join('\n'),r=analyze(s);
 assert.equal(r.source_rows,36*2);
 for(const c of Object.values(r.channels)){assert.equal(c.pilot_optimum.allocation.reduce((a,b)=>a+b),18);assert.ok(c.pilot_optimum.allocation.every(n=>n>=2));}
 assert.throws(()=>analyze(s.replace('100000','99999')));
 assert.throws(()=>analyze(s.replace('NTM_S01','NTM_S02')));
 return true;
}
if(require.main===module){
 if(process.argv[2]==='--self-test'){selftest();console.log('self-test PASS');}
 else{if(process.argv.length!==3)throw Error('usage: node script.cjs <source.csv>');
 const buf=fs.readFileSync(process.argv[2]),out=analyze(buf.toString('utf8'));out.source_sha256=crypto.createHash('sha256').update(buf).digest('hex');console.log(JSON.stringify(out,null,2));}
}
module.exports={analyze,selftest};
