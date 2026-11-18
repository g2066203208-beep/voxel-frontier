#!/usr/bin/env node
'use strict';
// S10: concentration of rainflow fourth/tenth moments in real historical 36-case screening ledger.
// Usage: node s10_rainflow_tail_concentration.cjs /path/to/ledger.csv
// No simulation, structural solver, or CAE dependency.
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const EXPECTED='067c60cea61b35398edd186ff509fe759d1c4420395f082d06c666d92d897ecb';
const HEADER='case_id,channel,source_column,range,mean,count,i_start,i_end';
function analyze(raw){
 const lines=raw.trimEnd().split(/\r?\n/);
 assert.equal(lines[0],HEADER,'ledger header mismatch');
 assert.equal(lines.length-1,48070,'ledger row count mismatch');
 const groups=new Map();
 for(let i=1;i<lines.length;i++){
  const p=lines[i].split(',');assert.equal(p.length,8,'column count '+i);
  const [caseId,ch]=p;assert(/^(U[^,]+)_(ETM|NTM)_S\d\d$/.test(caseId),'case '+i);
  assert(['TwrBsMxt','TwrBsMyt'].includes(ch),'channel '+i);
  const range=Number(p[3]),count=Number(p[5]);
  assert(Number.isFinite(range)&&range>=0&&[0.5,1].includes(count),'range/count '+i);
  const key=caseId+'|'+ch;if(!groups.has(key))groups.set(key,[]);
  groups.get(key).push({range,count});
 }
 assert.equal(groups.size,72,'36 cases x 2 channels required');
 const output=[];
 for(const [key,cycles] of groups){
  for(const m of [4,10]){
   const weights=cycles.map(x=>x.count*Math.pow(x.range,m));
   const total=weights.reduce((a,b)=>a+b,0);assert(total>0&&Number.isFinite(total));
   const sorted=weights.slice().sort((a,b)=>b-a);
   const topN=Math.ceil(cycles.length*.01);
   const share=sorted.slice(0,topN).reduce((a,b)=>a+b,0)/total;
   const single=sorted[0]/total;
   const neff=total*total/weights.reduce((a,b)=>a+b*b,0);
   assert(single<=share+1e-12&&share<=1+1e-12&&neff>=1);
   output.push({case_channel:key,m,cycles:cycles.length,top_n:topN,top_1pct_share:share,top_cycle_share:single,effective_cycles:neff});
  }
 }
 return output.sort((a,b)=>a.case_channel.localeCompare(b.case_channel)||a.m-b.m);
}
function median(x){const a=x.slice().sort((p,q)=>p-q),n=a.length;return(a[n/2-1]+a[n/2])/2}
function summarize(out){
 const s=[];
 for(const m of [4,10])for(const ch of ['TwrBsMxt','TwrBsMyt'])for(const typ of ['ETM','NTM']){
  const z=out.filter(x=>x.m===m&&x.case_channel.endsWith('|'+ch)&&x.case_channel.includes('_'+typ+'_'));
  assert.equal(z.length,18);
  s.push({m,channel:ch,type:typ,cases:18,median_top_1pct_share:median(z.map(x=>x.top_1pct_share)),min_top_1pct_share:Math.min(...z.map(x=>x.top_1pct_share)),max_top_1pct_share:Math.max(...z.map(x=>x.top_1pct_share)),median_effective_cycles:median(z.map(x=>x.effective_cycles))});
 }
 return s;
}
function selftest(){
 const weights=[1,2,3,4],s=weights.reduce((a,b)=>a+b,0);
 assert.equal(weights.slice().sort((a,b)=>b-a)[0]/s,0.4);
 assert.equal(median([1,2,3,4]),2.5);
 assert.throws(()=>analyze(HEADER+'\nX'),/row count/);
}
if(require.main===module){
 selftest();const file=process.argv[2];if(!file)throw Error('Usage: node s10_rainflow_tail_concentration.cjs ledger.csv');
 const bytes=fs.readFileSync(file),hash=crypto.createHash('sha256').update(bytes).digest('hex');
 assert.equal(hash,EXPECTED,'source bytes differ from historical ledger SHA256');
 const out=analyze(bytes.toString('utf8'));
 console.log(JSON.stringify({source_sha256:hash,rows:48070,groups:72,results:summarize(out),per_case:out},null,2));
}
module.exports={analyze,summarize,selftest};
