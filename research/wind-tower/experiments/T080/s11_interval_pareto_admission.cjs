'use strict';
// S11: interval-dominance admission, independent of structural solvers.
// Minimize each objective. Intervals must be independently validated, not fitted residual guesses.
function check(rows) {
 if(!Array.isArray(rows)||rows.length<2) throw Error('NEED_TWO_DESIGNS');
 const ids=new Set(), d=rows[0]?.lo?.length;
 if(!Number.isInteger(d)||d<2) throw Error('OBJECTIVE_DIMENSION');
 for(const r of rows){
  if(typeof r.id!=='string'||!r.id||ids.has(r.id)) throw Error('DUPLICATE_ID');
  ids.add(r.id);
  if(!Array.isArray(r.lo)||!Array.isArray(r.hi)||r.lo.length!==d||r.hi.length!==d) throw Error('DIMENSION');
  if(r.verified!==true) throw Error('UNVERIFIED_INTERVAL');
  for(let j=0;j<d;j++) if(!Number.isFinite(r.lo[j])||!Number.isFinite(r.hi[j])||r.lo[j]>r.hi[j]) throw Error('INVALID_BOUNDS');
  if(r.constraints!==undefined && (!Array.isArray(r.constraints)||r.constraints.some(c=>!Number.isFinite(c.upper)||!Number.isFinite(c.limit)))) throw Error('INVALID_CONSTRAINT');
 }
}
function dominates(a,b){
 // Universal dominance: every possible objective vector in A weakly dominates every possible B,
 // and at least one dimension is strictly better for all realizations.
 return a.hi.every((v,j)=>v<=b.lo[j]) && a.hi.some((v,j)=>v<b.lo[j]);
}
function analyze(rows){
 check(rows);
 const admitted=rows.filter(r=>(r.constraints||[]).every(c=>c.upper<=c.limit));
 const refused=rows.filter(r=>!admitted.includes(r)).map(r=>r.id);
 const dominatedBy={}; for(const b of admitted) dominatedBy[b.id]=admitted.filter(a=>a!==b&&dominates(a,b)).map(a=>a.id);
 return {admitted:admitted.map(r=>r.id),refused,certifiedNondominated:admitted.filter(r=>dominatedBy[r.id].length===0).map(r=>r.id),dominatedBy,
 note:'Nondominated means not certainly dominated under validated intervals; it does not prove Pareto optimality.'};
}
function test(){
 const r=[
 {id:'A',lo:[1,2],hi:[2,3],verified:true,constraints:[{upper:9,limit:10}]},
 {id:'B',lo:[3,4],hi:[4,5],verified:true,constraints:[{upper:8,limit:10}]},
 {id:'C',lo:[1.5,2.5],hi:[3.5,4.5],verified:true,constraints:[{upper:10,limit:10}]},
 {id:'D',lo:[0,0],hi:[1,1],verified:true,constraints:[{upper:11,limit:10}]}];
 const x=analyze(r);
 if(JSON.stringify(x.dominatedBy.B)!=='["A"]'||x.refused[0]!=='D'||x.certifiedNondominated.includes('B')||!x.certifiedNondominated.includes('C')) throw Error('ORACLE_FAIL');
 for(const bad of [
 [{...r[0],verified:false},r[1]],
 [{...r[0],hi:[0,3]},r[1]],
 [{...r[0],lo:[NaN,2]},r[1]],
 [{...r[0],id:'B'},r[1]],
 [{...r[0],constraints:[{upper:NaN,limit:10}]},r[1]]]){
 let failed=false;try{analyze(bad)}catch(e){failed=true}if(!failed)throw Error('NEGATIVE_TEST_FAIL');
 }
 // A strict pointwise Pareto comparison is not universal interval dominance when intervals overlap.
 if(dominates(r[0],r[2])) throw Error('OVERLAP_FALSE_POSITIVE');
 return {tests:7,oracle:'PASS'};
}
if(require.main===module){console.log(JSON.stringify(test()));console.log(JSON.stringify(analyze([
{id:'candidate_1',lo:[1,2],hi:[2,3],verified:true},
{id:'candidate_2',lo:[3,4],hi:[4,5],verified:true}
])));}
module.exports={analyze,dominates,test};
