// S11 source-version-robust minimum control-case portfolio, load-DEL only.
// Usage: node s11_source_robust_case_cover.cjs <T062_72CASE_RAINFLOW_RANK_TRANSITIONS_20261107.csv>
// No Abaqus/CAE; no production simulation. The two source columns are competing historical pipelines.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
function analyze(csv) {
 const lines=csv.trim().split(/\r?\n/), header=lines.shift().split(',');
 const needed=['case','channel','legacy_DEL_MNm','corrected_DEL_MNm'];
 const ix=Object.fromEntries(needed.map(k=>[k,header.indexOf(k)]));
 assert(needed.every(k=>ix[k]>=0),'missing required column');
 const rows=lines.map(line=>{const v=line.split(',');return {id:v[ix.case],ch:v[ix.channel],legacy:+v[ix.legacy_DEL_MNm],corrected:+v[ix.corrected_DEL_MNm]};});
 assert.equal(rows.length,72,'exact 36 cases x 2 channels');
 assert(rows.every(r=>r.id&&['TwrBsMxt','TwrBsMyt'].includes(r.ch)&&r.legacy>0&&r.corrected>0&&Number.isFinite(r.legacy)&&Number.isFinite(r.corrected)));
 const ids=[...new Set(rows.map(r=>r.id))].sort();assert.equal(ids.length,36);
 const lookup=new Map(rows.map(r=>[r.id+'|'+r.ch,r]));assert.equal(lookup.size,72,'duplicate case/channel');
 for(const id of ids)for(const ch of ['TwrBsMxt','TwrBsMyt'])assert(lookup.has(id+'|'+ch),'missing case/channel');
 const scenarios=[['TwrBsMxt','legacy'],['TwrBsMxt','corrected'],['TwrBsMyt','legacy'],['TwrBsMyt','corrected']];
 const max=scenarios.map(([ch,k])=>Math.max(...rows.filter(r=>r.ch===ch).map(r=>r[k])));
 const score=selected=>scenarios.map(([ch,k],i)=>Math.max(...selected.map(id=>lookup.get(id+'|'+ch)[k]))/max[i]);
 let bestPair={minimum:-Infinity,ids:null,coverage:null};
 for(let i=0;i<ids.length;i++)for(let j=i+1;j<ids.length;j++){
  const pair=[ids[i],ids[j]],coverage=score(pair),minimum=Math.min(...coverage);
  if(minimum>bestPair.minimum+1e-14)bestPair={minimum,ids:pair,coverage};
 }
 const triple=['U19p202140_ETM_S02','U11p4_ETM_S03','U11p4_ETM_S04'];
 const tripleCoverage=score(triple);
 assert(Math.abs(bestPair.minimum-0.876210597862838)<1e-12,'two-case regression');
 assert(tripleCoverage.every(x=>Math.abs(x-1)<1e-12),'three-case exact-max regression');
 assert(bestPair.minimum<0.95,'two-case 95% rejection');
 assert(score(['U11p4_ETM_S03'])[3]<0.86,'single legacy My champion fails corrected');
 // Independent negative test: an omitted row must be rejected, not silently imputed.
 return {rows:rows.length,cases:ids.length,scenario_maxima_MNm:max,scenarios:scenarios.map(x=>x.join('|')),best_two_case_maximin:bestPair,three_case_exact_maximum:{ids:triple,coverage:tripleCoverage},min_cases_for_95pct:3,min_cases_for_exact_maximum:3};
}
if(require.main===module){
 assert.equal(process.argv.length,3,'archived CSV required');
 const csv=fs.readFileSync(process.argv[2],'utf8'),r=analyze(csv);
 assert.throws(()=>analyze(csv.trim().split(/\r?\n/).slice(0,-1).join('\n')));
 console.log(JSON.stringify({status:'SOURCE_LEVEL_PASS',...r},null,2));
}
module.exports={analyze};
