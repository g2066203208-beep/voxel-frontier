#!/usr/bin/env node
// Source-level paired-channel comparison; no material stress or Miner inference.
const fs=require('fs');
const assert=require('assert');
function parse(csv){
 const lines=csv.trim().split(/\r?\n/), head=lines.shift().split(',');
 const idx=Object.fromEntries(head.map((x,i)=>[x,i]));
 for(const col of ['case_id','channel','quadratic_mean_collapse_gap_pct']) assert(col in idx,'missing '+col);
 const pairs=new Map();
 for(const line of lines){
  const v=line.split(','),id=v[idx.case_id],ch=v[idx.channel],g=Number(v[idx.quadratic_mean_collapse_gap_pct]);
  assert(Number.isFinite(g)&&g>=0&&g<=100,'invalid gap');
  assert(['TwrBsMxt','TwrBsMyt'].includes(ch),'invalid channel');
  if(!pairs.has(id))pairs.set(id,{});
  assert(!(ch in pairs.get(id)),'duplicate channel');
  pairs.get(id)[ch]=g;
 }
 assert(pairs.size===36,'expected 36 cases');
 const grouped=new Map(),diffs=[];
 for(const [id,p] of pairs){
  assert('TwrBsMxt' in p&&'TwrBsMyt' in p,'missing paired channel');
  const diff=p.TwrBsMxt-p.TwrBsMyt;
  diffs.push(diff);
  const group=id.replace(/_S\d+$/,'');
  if(!grouped.has(group))grouped.set(group,[]);
  grouped.get(group).push(diff);
 }
 assert(grouped.size===6,'expected 6 wind-bin/turbulence groups');
 const out=[];
 for(const [group,d] of [...grouped].sort()){
  assert(d.length===6,'expected 6 seeds');
  out.push({group,n:d.length,mean_diff_pctpt:d.reduce((a,b)=>a+b,0)/d.length,
   min_diff_pctpt:Math.min(...d),max_diff_pctpt:Math.max(...d),all_positive:d.every(x=>x>0)});
 }
 return {out,diffs};
}
function test(){
 const hdr='case_id,channel,quadratic_mean_collapse_gap_pct';
 assert.throws(()=>parse(hdr+'\nx,TwrBsMxt,1'),/expected 36/);
 assert.throws(()=>parse('case_id,channel\nx,TwrBsMxt'),/missing/);
 assert.throws(()=>parse(hdr+'\nx,TwrBsMxt,NaN'),/invalid/);
}
if(require.main===module){
 test();
 const p=process.argv[2];
 if(!p)throw Error('usage: node s10_paired_channel_mean_collapse.cjs SOURCE.csv');
 const {out,diffs}=parse(fs.readFileSync(p,'utf8'));
 console.log('group,n,mean_diff_pctpt,min_diff_pctpt,max_diff_pctpt,all_positive');
 for(const r of out)console.log([r.group,r.n,r.mean_diff_pctpt.toFixed(9),r.min_diff_pctpt.toFixed(9),r.max_diff_pctpt.toFixed(9),r.all_positive].join(','));
 const sorted=[...diffs].sort((a,b)=>a-b);
 console.error(JSON.stringify({paired_cases:36,all_36_positive:diffs.every(x=>x>0),median_diff_pctpt:(sorted[17]+sorted[18])/2,cluster_groups:6,all_6_group_means_positive:out.every(x=>x.mean_diff_pctpt>0),two_sided_group_sign_p_if_independent:2/64}));
}
module.exports={parse};
