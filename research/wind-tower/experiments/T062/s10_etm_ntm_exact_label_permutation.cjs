'use strict';
// Exact 12-choose-6 randomization reference for archived six-seed ETM/NTM DEL4.
// Exchangeability is a hypothetical sharp null, NOT guaranteed by ETM/NTM generation.
// Each speed/channel is analyzed separately; no independence claim across channels.
const fs=require('fs'),crypto=require('crypto'),path=require('path');
const expected='b362bcd7c37ccc56e21035de39448b5e761ec03f371b6b2f3eb30f41b013630d';
function assert(ok,msg){if(!ok)throw Error(msg);}
function parse(s){
 const ls=s.trim().split(/\r?\n/),h='case_id,channel,source_column,m,Neq,DEL,n_cycles_rows,cycle_count_sum,signal_min,signal_max,signal_mean,signal_std';
 assert(ls.shift()===h,'HEADER');assert(ls.length===72,'ROWS');
 const g=new Map(),seen=new Set();
 for(const line of ls){
  const a=line.split(',');assert(a.length===12,'COLS');
  const m=/^U(09p343881|11p4|19p202140)_(ETM|NTM)_S0([1-6])$/.exec(a[0]);
  assert(m&&['TwrBsMxt','TwrBsMyt'].includes(a[1]),'ID');
  assert(a[2]===a[1]+'_[kN-m]'&&Number(a[3])===4&&Number(a[4])===100000,'UNIT_M_NEQ');
  const v=Number(a[5]);assert(Number.isFinite(v)&&v>0,'DEL');
  const key=m[1]+'|'+a[1],id=a[0]+'|'+a[1];assert(!seen.has(id),'DUPLICATE');seen.add(id);
  if(!g.has(key))g.set(key,{ETM:[],NTM:[]});
  g.get(key)[m[2]].push({seed:+m[3],v});
 }
 assert(g.size===6,'GROUPS');
 for(const v of g.values())for(const k of ['ETM','NTM']){
  v[k].sort((a,b)=>a.seed-b.seed);
  assert(v[k].length===6&&v[k].every((a,i)=>a.seed===i+1),'SEED_COVERAGE');
 }
 return g;
}
function subsets(n,k){
 const out=[];function rec(start,a){if(a.length===k){out.push(a.slice());return;}
  for(let i=start;i<=n-(k-a.length);i++){a.push(i);rec(i+1,a);a.pop();}}
 rec(0,[]);return out;
}
function analyze(s){
 const g=parse(s),combs=subsets(12,6);assert(combs.length===924,'COMBINATIONS');
 const out=[];
 for(const [key,v] of g){
  const e=v.ETM.map(x=>x.v),n=v.NTM.map(x=>x.v),q=[...e,...n].map(x=>x**4);
  const total=q.reduce((a,b)=>a+b,0),observed=e.reduce((a,b)=>a+b**4,0)/n.reduce((a,b)=>a+b**4,0);
  let upper=0,lower=0;
  for(const idx of combs){const x=idx.reduce((a,i)=>a+q[i],0),ratio=x/(total-x);
   if(ratio>=observed*(1-1e-12))upper++;
   if(ratio<=observed*(1+1e-12))lower++;
  }
  out.push({key,ratio:observed**.25,upper,lower,pUpper:upper/924,pTwo:Math.min(1,2*Math.min(upper,lower)/924)});
 }
 return out.sort((a,b)=>a.key.localeCompare(b.key));
}
function test(){
 assert(subsets(4,2).length===6,'COMB_TEST');
 const v=[1,1,1,1,2,2,2,2,2,2,2,2];assert(v.length===12,'TEST');
 let bad=false;try{parse('bad');}catch(e){bad=true;}assert(bad,'BAD_INPUT_ACCEPTED');
 return 'SELF_TEST_PASS';
}
if(require.main===module){
 const input=fs.readFileSync(path.join(__dirname,'recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv'));
 assert(crypto.createHash('sha256').update(input).digest('hex')===expected,'SOURCE_SHA256');
 console.log(test());
 console.log('wind_bin,channel,ETM_NTM_DEL4_ratio,upper_tail_count_of_924,lower_tail_count_of_924,upper_tail_probability,two_sided_probability');
 for(const r of analyze(input.toString('utf8')))console.log([r.key.split('|')[0],r.key.split('|')[1],r.ratio.toFixed(9),r.upper,r.lower,r.pUpper.toFixed(9),r.pTwo.toFixed(9)].join(','));
}
module.exports={parse,subsets,analyze,test};
