'use strict';
const assert = require('node:assert/strict');
// Fourth-moment units are arbitrary; examples are mathematical, not observed loads.
function bounds(observed, missingHours, cap=Infinity) {
  if (![observed,missingHours].every(x=>Number.isFinite(x)&&x>=0)) throw Error('invalid input');
  if (!(cap>=0)) throw Error('invalid cap');
  return [observed, missingHours===0?observed:observed+missingHours*cap];
}
function certificate(a,b,h,cap=Infinity) {
  const A=bounds(a,h,cap), B=bounds(b,h,cap);
  return {A,B,aAlwaysLower:A[1]<B[0],bAlwaysLower:B[1]<A[0],
    undetermined:!(A[1]<B[0])&&!(B[1]<A[0])};
}
assert.equal(certificate(1,2,99736).undetermined,true);
assert.equal(certificate(1,2,0).aAlwaysLower,true);
assert.equal(certificate(1,2,99736,0).aAlwaysLower,true);
assert.equal(certificate(1,2,99736,0.5/99736).aAlwaysLower,true);
assert.equal(certificate(1,2,99736,1/99736).undetermined,true);
assert.throws(()=>bounds(-1,1));
assert.throws(()=>bounds(1,-1));
assert.throws(()=>bounds(1,1,-1));
const h=99736;
const witnessA={qA:0,qB:2/h,MA:1,MB:4};
const witnessB={qA:2/h,qB:0,MA:3,MB:2};
assert.ok(witnessA.MA<witnessA.MB&&witnessB.MA>witnessB.MB);
console.log(JSON.stringify({test:'PASS',missingHours:h,certificate:certificate(1,2,h),
  witnessA,witnessB,criticalCapForStrictAWin:1/h},null,2));
module.exports={bounds,certificate};
