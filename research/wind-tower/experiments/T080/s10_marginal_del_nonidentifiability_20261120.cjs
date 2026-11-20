#!/usr/bin/env node
'use strict';
// Exact analytical counterexample; NOT a physical OpenFAST, wind or seismic RUN.
const assert = require('node:assert/strict');
const x = [0,1,0,-1,0], y = x.map(v=>-v);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const range4=a=>(Math.max(...a)-Math.min(...a))**4;
assert.equal(range4(x),16);
assert.equal(range4(y),16);
assert.equal(range4(add(x,x)),256);
assert.equal(range4(add(x,y)),0);
assert.notEqual(range4(add(x,x)),range4(add(x,y)));
console.log(JSON.stringify({type:'ANALYTIC_NOT_PHYSICAL',marginal_range4:16,aligned_range4:256,opposed_range4:0,test:'PASS'}));
