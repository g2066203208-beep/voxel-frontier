#!/usr/bin/env node
'use strict';
// Historical paired NTM/ETM seed-index maxima of two base bending DEL4 channels.
// Seed-index coincidence does NOT imply time-synchronous peaks.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const file=process.argv[2]||path.resolve(__dirname,'../T062/recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv');
function analyze(csv){
 const lines=csv.trim().split(/\r?\n/),hdr=lines.shift().split(',');
 const col=k=>{const i=hdr.indexOf(k);assert(i>=0,'missing '+k);return i};
 const [id,ch,del,m,neq]=['case_id','channel','DEL','m','Neq'].map(col);
 assert.equal(lines.length,72);
 const groups=new Map(),seen=new Set();
 for(const line of lines){
  const a=line.split(','),match=/^U(\d+p\d+)_(ETM|NTM)_S(0[1-6])$/.exec(a[id]);
  assert(match,'invalid case ID');assert(['TwrBsMxt','TwrBsMyt'].includes(a[ch]));
  assert.equal(Number(a[m]),4);assert.equal(Number(a[neq]),100000);
  const d=Number(a[del]);assert(Number.isFinite(d)&&d>0);
  const key=match[1]+'_'+match[2],unique=key+'|'+match[3]+'|'+a[ch];
  assert(!seen.has(unique),'duplicate');seen.add(unique);
  if(!groups.has(key))groups.set(key,{TwrBsMxt:[],TwrBsMyt:[]});
  groups.get(key)[a[ch]].push({seed:match[3],d});
 }
 assert.equal(groups.size,6);assert.equal(seen.size,72);
 const out=[];
 for(const [group,g] of [...groups].sort(([a],[b])=>a.localeCompare(b))){
  const x=g.TwrBsMxt,y=g.TwrBsMyt;
  assert.equal(x.length,6);assert.equal(y.length,6);
  assert.deepEqual(x.map(z=>z.seed).sort(),['01','02','03','04','05','06']);
  assert.deepEqual(y.map(z=>z.seed).sort(),['01','02','03','04','05','06']);
  const xmax=x.reduce((a,b)=>a.d>b.d?a:b),ymax=y.reduce((a,b)=>a.d>b.d?a:b);
  out.push({group,mx_seed:xmax.seed,my_seed:ymax.seed,
   mx_max_kNm:xmax.d,my_max_kNm:ymax.d,
   coincident_seed:xmax.seed===ymax.seed,
   my_at_mx_fraction:y.find(z=>z.seed===xmax.seed).d/ymax.d,
   mx_at_my_fraction:x.find(z=>z.seed===ymax.seed).d/xmax.d});
 }
 return out;
}
const synthetic=['case_id,channel,DEL,m,Neq'];
for(const typ of ['ETM','NTM'])for(const u of ['09p343881','11p4','19p202140'])
 for(let s=1;s<=6;s++)for(const c of ['TwrBsMxt','TwrBsMyt'])
 synthetic.push('U'+u+'_'+typ+'_S0'+s+','+c+','+(c==='TwrBsMxt'?s:7-s)+',4,100000');
const control=analyze(synthetic.join('\n'));
assert(control.every(r=>!r.coincident_seed),'synthetic mismatched maxima rejection');
assert.throws(()=>analyze(synthetic.join('\n').replace(',4,100000',',10,100000')));
const result=analyze(fs.readFileSync(file,'utf8'));
assert.equal(result.filter(r=>r.coincident_seed).length,3,'archive coincidence regression');
assert.equal(result.find(r=>r.group==='09p343881_ETM').my_at_mx_fraction.toFixed(6),'0.823630');
console.log(JSON.stringify({source:file,groups:result.length,coincident:3,noncoincident:3,rows:result},null,2));
