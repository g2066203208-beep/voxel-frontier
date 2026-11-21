#!/usr/bin/env node
'use strict';
// T077 source-level control-case switch between m=4 and m=10, NOT Miner.
const fs=require('node:fs'),assert=require('node:assert/strict');
const cases=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
function analyze(csv){
 const lines=csv.trim().split(/\r?\n/),h=lines.shift().split(',');
 const ix=k=>{const n=h.indexOf(k);assert(n>=0,'missing '+k);return n;};
 const ci=ix('case'),si=ix('segment'),ai=ix('azimuth_deg'),d4=ix('DEL_m4_MPa'),d10=ix('DEL_m10_MPa'),cl=ix('stress_class');
 assert.equal(lines.length,1984,'source rows');
 const seen=new Set(),targets=new Map();
 for(const line of lines){
  const v=line.split(','),c=v[ci],s=v[si],a=Number(v[ai]),x=Number(v[d4]),y=Number(v[d10]);
  assert(cases.includes(c),'case');assert(/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(s),'section');
  assert(Number.isFinite(a)&&a>=0&&a<360&&a%22.5===0,'azimuth');
  assert(Number.isFinite(x)&&x>0&&Number.isFinite(y)&&y>0,'DEL');
  assert.equal(v[cl],'SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE');
  const key=c+'|'+s+'|'+a;assert(!seen.has(key),'duplicate');seen.add(key);
  const t=c+'|'+s,p=targets.get(t)||{case:c,section:s,m4:0,m10:0};
  p.m4=Math.max(p.m4,x);p.m10=Math.max(p.m10,y);targets.set(t,p);
 }
 assert.equal(seen.size,1984);assert.equal(targets.size,124);
 const switched=[],counts={m4:{},m10:{}};
 for(let n=1;n<=31;n++){
  const s='CSEG_'+String(n).padStart(2,'0'),rows=cases.map(c=>{const p=targets.get(c+'|'+s);assert(p);return p;});
  const w4=rows.reduce((p,q)=>q.m4>p.m4?q:p),w10=rows.reduce((p,q)=>q.m10>p.m10?q:p);
  counts.m4[w4.case]=(counts.m4[w4.case]||0)+1;counts.m10[w10.case]=(counts.m10[w10.case]||0)+1;
  if(w4.case!==w10.case)switched.push(s);
 }
 assert.deepEqual(switched,['CSEG_01','CSEG_02','CSEG_03','CSEG_04','CSEG_05','CSEG_24','CSEG_25','CSEG_26','CSEG_27','CSEG_28','CSEG_29','CSEG_30','CSEG_31']);
 assert.equal(counts.m10[cases[0]],31);
 return {source_rows:1984,targets:124,counts,switched,limitation:'fixed-design ETM nominal DEL, not material fatigue or DLC1.2'};
}
if(require.main===module){
 assert.equal(process.argv.length,3,'CSV required');const csv=fs.readFileSync(process.argv[2],'utf8'),r=analyze(csv);
 assert.throws(()=>analyze(csv.replace('6.83617569974','NaN')));
 assert.throws(()=>analyze(csv.replace('CSEG_01','CSEG_99')));
 assert.throws(()=>analyze(csv+'\n'+csv.trim().split(/\r?\n/)[1]));
 console.log(JSON.stringify(r,null,2));
}
module.exports={analyze};
