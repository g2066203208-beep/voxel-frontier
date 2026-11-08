#!/usr/bin/env node
'use strict';
// GB18306-2015 Table C.17 printed p126: Jiayu eight-town transcription.
// Not a site-specific target spectrum, structural modal period, or seismic response.
const EXPECTED=['陆溪镇','高铁岭镇','官桥镇','鱼岳镇','新街镇','渡普镇','潘家湾镇','簰洲湾镇'];
function verify(text){
 if(typeof text!=='string')throw Error('not text');
 const lines=text.replaceAll(String.fromCharCode(13),'').trimEnd().split(String.fromCharCode(10));
 if(lines[0]!=='township,pga_g,tg_s,standard,appendix,printed_page')throw Error('header');
 if(lines.length!==9)throw Error('row count');
 const seen=new Set();
 for(const line of lines.slice(1)){
  const f=line.split(',');
  if(f.length!==6||!EXPECTED.includes(f[0])||seen.has(f[0]))throw Error('town identity');
  seen.add(f[0]);
  if(f[1]!=='0.05'||f[2]!=='0.35')throw Error('parameter');
  if(f[3]!=='GB18306-2015'||f[4]!=='C.17'||f[5]!=='126')throw Error('source');
 }
 return {towns:seen.size,pga_g:0.05,tg_s:0.35,pga_m_s2:0.05*9.80665,
         period_ratios:[4,6,6.230958,8].map(T=>({T_s:T,T_over_Tg:T/0.35}))};
}
function selfTest(valid){
 const a=verify(valid);
 if(a.towns!==8||Math.abs(a.period_ratios[2].T_over_Tg-17.802737142857143)>1e-12)throw Error('oracle');
 const bad=[
  valid.replace('township,pga_g','town,pga_g'),
  valid.replace('陆溪镇,','陌生镇,'),
  valid.replace('高铁岭镇,','陆溪镇,'),
  valid.replace('官桥镇,0.05','官桥镇,0.10'),
  valid.replace('鱼岳镇,0.05,0.35','鱼岳镇,0.05,0.45'),
  valid.replace('新街镇,0.05,0.35,GB18306-2015','新街镇,0.05,0.35,GB18306-2026'),
  valid.replace('渡普镇,0.05,0.35,GB18306-2015,C.17,126','渡普镇,0.05,0.35,GB18306-2015,C.17,125'),
  valid.split(String.fromCharCode(10)).filter(x=>!x.startsWith('簰洲湾镇,')).join(String.fromCharCode(10))
 ];
 bad.forEach((v,i)=>{let rejected=false;try{verify(v)}catch(e){rejected=true;}if(!rejected)throw Error('negative test '+i);});
 return {positive:1,negative:bad.length};
}
if(typeof module!=='undefined')module.exports={verify,selfTest};
if(typeof module!=='undefined'&&typeof require!=='undefined'&&require.main===module){
 const fs=require('node:fs');const p=process.argv[2];
 if(!p)throw Error('Usage: node s05_jiayu_c17_eight_town_gate.cjs table.csv');
 const data=fs.readFileSync(p,'utf8');
 console.log(JSON.stringify({result:verify(data),tests:selfTest(data)},null,2));
}
