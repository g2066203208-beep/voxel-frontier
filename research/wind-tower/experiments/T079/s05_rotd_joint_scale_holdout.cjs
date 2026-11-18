#!/usr/bin/env node
'use strict';
// SOURCE: real-records/S05_ESM_33PERIOD_SCALAR_MINIMAX_20261113.csv
// One real processed ESM event, illustrative target only; NOT a design-spectrum check.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const source=process.argv[2]||path.join(__dirname,'real-records/S05_ESM_33PERIOD_SCALAR_MINIMAX_20261113.csv');
function parse(csv){
 const lines=csv.trim().split(/\r?\n/), head=lines.shift().split(',');
 const needed=['period_s','RotD50_raw_ratio','RotD100_raw_ratio'];
 for(const col of needed)if(!head.includes(col))throw Error('missing '+col);
 const data=lines.map((line,i)=>{const cells=line.split(',');if(cells.length!==head.length)throw Error('malformed row '+(i+2));const row={};for(const key of needed){row[key]=Number(cells[head.indexOf(key)]);if(!Number.isFinite(row[key])||row[key]<=0)throw Error('nonpositive/nonfinite '+key+' row '+(i+2));}return {T:row.period_s,q50:row.RotD50_raw_ratio,q100:row.RotD100_raw_ratio};});
 if(data.length!==33||data.some((r,i)=>i>0&&r.T<=data[i-1].T))throw Error('expected 33 strictly increasing periods');
 return data;
}
function fit(rows,keys){const q=rows.flatMap(r=>keys.map(k=>r[k]));return 1/Math.sqrt(Math.min(...q)*Math.max(...q));}
function evaluate(rows,k,keys){const v=rows.flatMap(r=>keys.map(key=>k*r[key]));return {minimum:Math.min(...v),maximum:Math.max(...v),max_abs_log_error:Math.max(...v.map(x=>Math.abs(Math.log(x)))),below_0p8:v.filter(x=>x<0.8).length,n:v.length};}
function run(rows){const train=rows.filter(r=>r.T<=3),hold=rows.filter(r=>r.T>3);if(train.length!==18||hold.length!==15)throw Error('training/holdout count drift');const k50=fit(train,['q50']),k100=fit(train,['q100']),kcommon=fit(train,['q50','q100']);return {train_count:train.length,hold_count:hold.length,k50,k100,kcommon,train_joint:evaluate(train,kcommon,['q50','q100']),hold_joint:evaluate(hold,kcommon,['q50','q100']),hold50:evaluate(hold,k50,['q50']),hold100:evaluate(hold,k100,['q100']),transfer50to100:evaluate(hold,k50,['q100']),transfer100to50:evaluate(hold,k100,['q50'])};}
function tests(){
 assert.throws(()=>parse('period_s,RotD50_raw_ratio,RotD100_raw_ratio\n1,0,1'),/nonpositive/);
 assert.throws(()=>parse('period_s,RotD50_raw_ratio,RotD100_raw_ratio\n1,1,NaN'),/nonpositive/);
 assert.equal(fit([{q50:1,q100:4}],['q50','q100']),0.5);
 assert.deepEqual(evaluate([{q50:1,q100:4}],0.5,['q50','q100']).n,2);
}
tests();
const result=run(parse(fs.readFileSync(source,'utf8')));
assert.ok(Math.abs(result.kcommon-0.7035259817832802)<1e-10,'archived-source regression');
assert.equal(result.hold_joint.below_0p8,30);
console.log(JSON.stringify({source,result,tests:'PASS (4 unit checks + 2 archived-source regression checks)'},null,2));
module.exports={parse,fit,evaluate,run};
