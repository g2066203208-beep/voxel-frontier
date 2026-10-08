import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const base='research/wind-tower/references/reference-models-20261008/IEA-15-240-RWT_OpenFAST/OpenFAST/';
function read(path:string):string {return readFileSync(resolve(process.cwd(),base+path),'utf8');}
const ed=read('IEA-15-240-RWT-Monopile/IEA-15-240-RWT-Monopile_ElastoDyn.dat');
const aero=read('IEA-15-240-RWT-Monopile/IEA-15-240-RWT-Monopile_AeroDyn15.dat');
const blade=read('IEA-15-240-RWT/IEA-15-240-RWT_AeroDyn15_blade.dat');
function table(text:string,heading:string,n:number):number[][]{
  const s=text.split(/\r?\n/);
  const start=s.findIndex(v=>v.trim().startsWith(heading));
  assert.ok(start>=0,heading+' table exists');
  const values:number[][]=[];
  for(let i=start+1;i<s.length&&values.length<n;i++){
    const pieces=s[i].trim().split(/\s+/);
    if(pieces.length<2||pieces.slice(0,2).some(x=>!Number.isFinite(Number(x)))){
      if(values.length)break;
      continue;
    }
    values.push(pieces.map(Number).filter(Number.isFinite));
  }
  assert.equal(values.length,n,heading+' station count');
  return values;
}
test('IEA15 official OpenFAST model has correct rotor and geometry identity',()=>{
  assert.match(ed,/^\s*3\s+NumBl\b/m);
  assert.match(ed,/^\s*120\.97\s+TipRad\b/m);
  assert.match(ed,/^\s*3\.97\s+HubRad\b/m);
  assert.match(ed,/^\s*144\.386\s+TowerHt\b/m);
  assert.match(ed,/^\s*15\.\s+TowerBsHt\b/m);
});
test('20 authoritative tower elevation and diameter samples',()=>{
  const rows=table(aero,'TwrElev',20);
  assert.equal(rows[0][0],15);
  assert.equal(rows.at(-1)?.[0],144.386);
  assert.equal(rows[0][1],10);
  assert.equal(rows.at(-1)?.[1],6.5);
  assert.ok(rows.every((r,i)=>i===0 || r[0]>=rows[i-1][0]));
});
test('50 blade chord/twist/sweep stations and span agree with ElastoDyn',()=>{
  const rows=table(blade,'BlSpn',50);
  assert.ok(Math.abs((rows.at(-1)?.[0]||0)-117)<0.01);
  assert.equal(rows[0][5],5.2);
  assert.ok(rows.every(r=>r[5]>0));
});
