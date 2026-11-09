#!/usr/bin/env node
'use strict';
// OFFICIAL: GB 55002-2021, MOHURD PDF printed pp.12-13, clauses 4.2.2-4.2.3.
// https://www.mohurd.gov.cn/gongkai/zc/wjk/art/2021/art_17339_761174.html
// This is a building/municipal-code conditional minimum-shear FLOOR, not a
// turbine response spectrum or a claim of GB 55002 applicability to a turbine.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const base=Object.freeze({'6_0p05g':.008,'7_0p10g':.016,'7_0p15g':.024,'8_0p20g':.032,'8_0p30g':.048,'9_0p40g':.064});
const Tg=Object.freeze({first:[.20,.25,.35,.45,.65],second:[.25,.30,.40,.55,.75],third:[.30,.35,.45,.65,.90]});
const periods=[3,3.5,4,4.5,5,6];
function factor(T,irregular=false){
  if(typeof T!=='number'||!Number.isFinite(T)||T<=0)throw Error('INVALID_PERIOD');
  if(typeof irregular!=='boolean')throw Error('INVALID_IRREGULAR_FLAG');
  return irregular||T<=3.5?1:T>=5?.75:(9.5-T)/6;
}
function lambda(T,key,irregular=false){
  if(!Object.hasOwn(base,key))throw Error('UNKNOWN_INTENSITY');
  return base[key]*factor(T,irregular);
}
function tgRatio(T,group,index){
  if(!Object.hasOwn(Tg,group)||!Number.isInteger(index)||index<0||index>4)throw Error('UNKNOWN_SITE');
  if(!Number.isFinite(T)||T<=0)throw Error('INVALID_PERIOD');
  return T/Tg[group][index];
}
function csv(){
  const keys=Object.keys(base),f=x=>x.toFixed(9);
  const head=['T_s','regular_floor_factor','irregular_floor_factor',...keys.map(k=>'regular_'+k),...keys.map(k=>'irregular_'+k),'T_over_Tg_min_15scenarios','T_over_Tg_max_15scenarios'];
  const rows=periods.map(T=>{
    const ratios=Object.keys(Tg).flatMap(g=>Tg[g].map((_,i)=>tgRatio(T,g,i)));
    return [f(T),f(factor(T)),f(factor(T,true)),...keys.map(k=>f(lambda(T,k))),...keys.map(k=>f(lambda(T,k,true))),f(Math.min(...ratios)),f(Math.max(...ratios))].join(',');
  });
  return [head.join(','),...rows].join('\n')+'\n';
}
function svg(){
  const x=T=>90+(T-2.5)*195,y=v=>380-(v-.70)*900;
  const points=[];for(let i=0;i<=80;i++){const T=2.5+i*.05;points.push(x(T).toFixed(2)+','+y(factor(T)).toFixed(2));}
  let ticks='';for(const T of [2.5,3,3.5,4,4.5,5,5.5,6,6.5])ticks+='<text x="'+x(T)+'" y="407" text-anchor="middle" font-size="14">'+T+'</text>';
  let lines='';for(const v of [.75,.8,.85,.9,.95,1])lines+='<line x1="90" y1="'+y(v)+'" x2="870" y2="'+y(v)+'" stroke="#ddd"/><text x="76" y="'+(y(v)+5)+'" text-anchor="end" font-size="14">'+v.toFixed(2)+'</text>';
  return '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="475" viewBox="0 0 960 475"><rect width="960" height="475" fill="white"/><text x="42" y="30" font-size="20">GB 55002-2021 clause 4.2.3: long-period minimum-shear FLOOR</text><text x="42" y="53" font-size="13">Official-source parameter study only; not a wind-turbine spectrum or response</text>'+lines+'<line x1="90" y1="65" x2="90" y2="380" stroke="#333"/><line x1="90" y1="380" x2="870" y2="380" stroke="#333"/>'+ticks+'<polyline points="'+points.join(' ')+'" fill="none" stroke="#16738b" stroke-width="4"/><line x1="90" y1="'+y(1)+'" x2="870" y2="'+y(1)+'" stroke="#bc6536" stroke-width="2" stroke-dasharray="7 5"/><text x="615" y="89" font-size="15">Regular: period-dependent</text><text x="615" y="110" font-size="15">Torsionally irregular: 1.00</text><text x="480" y="439" text-anchor="middle" font-size="17">Assumed fundamental period T1 (s)</text><text x="45" y="460" font-size="12">No verified site class, turbine-code applicability, response-spectrum ordinates, or physical seismic run.</text></svg>\n';
}
function selfTest(){
  assert.equal(factor(3.5),1);assert.equal(factor(5),.75);
  assert.equal(factor(4.5),5/6);assert.equal(factor(6,true),1);
  assert.equal(lambda(5,'7_0p10g'),.012);
  assert.equal(tgRatio(5,'third',4),5/.9);
  for(let t=3.5;t<=6;t+=.05)assert(factor(t)<=1+1e-12&&factor(t)>=.75-1e-12);
  for(const T of [0,-1,NaN,Infinity])assert.throws(()=>factor(T),/INVALID_PERIOD/);
  assert.throws(()=>factor(4,'bad'),/INVALID_IRREGULAR_FLAG/);
  assert.throws(()=>lambda(4,'7_0p20g'),/UNKNOWN_INTENSITY/);
  assert.throws(()=>tgRatio(4,'fourth',2),/UNKNOWN_SITE/);
  assert.throws(()=>tgRatio(4,'first',5),/UNKNOWN_SITE/);
  assert.equal(csv().trim().split('\n').length,7);
  return 'PASS 6 source anchors + 8 rejection tests + monotonicity + 6 rows';
}
if(require.main===module){
  if(process.argv[2]==='--self-test')console.log(selfTest());
  else if(process.argv[2]){
    fs.mkdirSync(process.argv[2],{recursive:true});
    fs.writeFileSync(path.join(process.argv[2],'S05_GB55002_LONG_PERIOD_MIN_SHEAR_20261109.csv'),csv());
    fs.writeFileSync(path.join(process.argv[2],'FIG_S05_GB55002_LONG_PERIOD_MIN_SHEAR_20261109.svg'),svg());
  }else{console.error('Usage: node script.cjs --self-test | output_dir');process.exitCode=2;}
}
module.exports={factor,lambda,tgRatio,csv,svg,selfTest};
