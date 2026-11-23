#!/usr/bin/env node
// T062 source-only NTM tower-base rainflow exponent ranking test.
// Usage: node s10_ntm_cross_exponent_seed_rank_reversal.cjs path/to/S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv
const fs = require('node:fs');
const assert = require('node:assert/strict');
function analyze(csv) {
  const lines = csv.trim().split(/\r?\n/);
  const header = lines.shift().split(',');
  const required = ['case','channel','DEL_m4_Nref600','DEL_m10_Nref600'];
  required.forEach(x=>assert(header.includes(x), 'missing '+x));
  const groups = new Map();
  for(const line of lines) {
    const cells=line.split(',');
    assert.equal(cells.length,header.length,'malformed CSV row');
    const row=Object.fromEntries(header.map((h,i)=>[h,cells[i]]));
    if(!/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(row.case))continue;
    if(!['TwrBsMxt','TwrBsMyt'].includes(row.channel))continue;
    const m4=Number(row.DEL_m4_Nref600),m10=Number(row.DEL_m10_Nref600);
    assert(Number.isFinite(m4)&&m4>0&&Number.isFinite(m10)&&m10>0,'invalid DEL');
    const key=row.case.split('_').slice(0,2).join('_')+'|'+row.channel;
    if(!groups.has(key))groups.set(key,[]);
    groups.get(key).push({case:row.case,m4,m10});
  }
  assert.equal(groups.size,6,'six wind-speed/channel groups required');
  const results=[];
  for(const [group,arr] of [...groups].sort(([a],[b])=>a.localeCompare(b))){
    assert.equal(arr.length,6,'six seeds per group');
    assert.equal(new Set(arr.map(x=>x.case)).size,6,'duplicate seed');
    let reversals=0,ties=0,example=null;
    for(let i=0;i<6;i++)for(let j=i+1;j<6;j++){
      const a=arr[i],b=arr[j],d4=a.m4-b.m4,d10=a.m10-b.m10;
      if(d4===0||d10===0){ties++;continue;}
      if(d4*d10<0){reversals++;example??=[a.case,b.case];}
    }
    results.push({group,comparisons:15,reversals,ties,example});
  }
  return {groups:results,totalReversals:results.reduce((s,x)=>s+x.reversals,0),
    totalPairs:90,totalTies:results.reduce((s,x)=>s+x.ties,0)};
}
if(require.main===module){
  assert.equal(analyze.__proto__,Function.prototype);
  assert.throws(()=>analyze('case,channel\nx,y'),/missing/);
  if(process.argv.length!==3)throw Error('provide source CSV path');
  const result=analyze(fs.readFileSync(process.argv[2],'utf8'));
  assert.equal(result.totalReversals,11,'archived-data regression gate');
  assert.equal(result.totalTies,0,'unexpected ties');
  console.log(JSON.stringify(result,null,2));
}
module.exports={analyze};
