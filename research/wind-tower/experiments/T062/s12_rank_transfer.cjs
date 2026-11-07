'use strict';
// Exact single-cycle analytic example; NOT a physical tower or material-fatigue run.
const assert=require('node:assert/strict');
function calc(id,dM,dN,A=1,W=1,m=4){
  if(!/^[A-Za-z0-9_]+$/.test(id)||![dM,dN,A,W,m].every(Number.isFinite)||A<=0||W<=0||m<=0)throw Error('invalid input');
  const ds=Math.abs(dN/A+dM/W);
  return [id,dM,dN,Math.abs(dM),ds,ds**m];
}
function main(){
  const a=calc('A',2,-1.5),b=calc('B',1,0),c=calc('A_axial_fixed',2,0),d=calc('B_axial_fixed',1,0);
  assert.equal(a[3]/b[3],2);assert.equal(a[4]/b[4],0.5);assert.equal(a[5]/b[5],1/16);
  assert.equal(c[4]/d[4],2);assert.equal(c[5]/d[5],16);
  for(const args of [['bad',NaN,0],['bad',2,Infinity],['bad',2,0,0],['bad',2,0,1,-1],['bad',2,0,1,1,0],['../bad',2,0],['bad',2,0,1,1,NaN]])assert.throws(()=>calc(...args));
  return 'case_id,delta_M_MNm,delta_N_MN,load_DEL_MNm,stress_range_MPa,normalized_range_score_m4,scope\n'+[a,b,c,d].map(x=>x.join(',')+',ANALYTIC_NOT_PHYSICAL').join('\n')+'\n';
}
if(require.main===module){process.stdout.write(main());process.stderr.write('PASS: five analytic invariants and seven invalid-input refusals; not a physical run.\n');}
module.exports={calc,main};
