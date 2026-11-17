#!/usr/bin/env node
// S11: deterministic 8/8 angular holdout on historical T077 DEL4, NOT a material/physical validation.
'use strict';
const fs=require('node:fs'),path=require('node:path');
const source=process.argv[2]||path.resolve(__dirname,'../T077/recovery/S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv');
function evaluate(csv){
 const lines=csv.trim().split(/\r?\n/),head=lines.shift().split(',');
 const col=Object.fromEntries(head.map((v,i)=>[v,i]));
 for(const key of ['case','segment','azimuth_deg','DEL_m4_MPa'])if(!(key in col))throw Error('MISSING_COLUMN '+key);
 const groups=new Map();
 for(const line of lines){const a=line.split(','),k=a[col.case]+'|'+a[col.segment],angle=Number(a[col.azimuth_deg]),y=Number(a[col.DEL_m4_MPa]);if(!Number.isFinite(angle)||!Number.isFinite(y)||y<0)throw Error('BAD_VALUE');if(!groups.has(k))groups.set(k,[]);groups.get(k).push({angle,y})}
 const metrics=Object.fromEntries(['mean','linear','fourier'].map(x=>[x,{sum:0,max:0,negative:0,over10:0}]));
 let observations=0;
 for(const [key,v] of groups){
  v.sort((a,b)=>a.angle-b.angle);
  if(v.length!==16||v.some((x,i)=>Math.abs(x.angle-i*22.5)>1e-7))throw Error('BAD_GRID '+key);
  const scale=Math.max(...v.map(x=>x.y));if(!(scale>0))throw Error('ZERO_SCALE '+key);
  for(let parity=0;parity<2;parity++){
   const train=v.filter((_,i)=>i%2===parity),mu=train.reduce((s,x)=>s+x.y,0)/8;
   for(let i=0;i<16;i++)if(i%2!==parity){
    const theta=v[i].angle*Math.PI/180;let fourier=mu;
    for(let n=1;n<=3;n++){
     let c=0,s=0;for(const z of train){let t=z.angle*Math.PI/180;c+=z.y*Math.cos(n*t);s+=z.y*Math.sin(n*t)}
     fourier+=.25*(c*Math.cos(n*theta)+s*Math.sin(n*theta));
    }
    const pred={mean:mu,linear:(v[(i+15)%16].y+v[(i+1)%16].y)/2,fourier};
    for(const [method,y] of Object.entries(pred)){const e=Math.abs(y-v[i].y)/scale,m=metrics[method];m.sum+=e;m.max=Math.max(m.max,e);if(y<0)m.negative++;if(e>.1)m.over10++}
    observations++;
   }
  }
 }
 return {groups:groups.size,observations,metrics:Object.fromEntries(Object.entries(metrics).map(([k,v])=>[k,{mae_percent:100*v.sum/observations,max_percent:100*v.max,negative:v.negative,over10_percent_count:v.over10}]))};
}
if(require.main===module){
 if(process.argv.includes('--selftest')){
  const header='case,segment,azimuth_deg,DEL_m4_MPa';
  const fixture=[header,...Array.from({length:16},(_,i)=>'A,S,'+(i*22.5)+','+(2+Math.cos(i*Math.PI/8)))].join('\n');
  const q=evaluate(fixture);if(q.groups!==1||q.observations!==16||q.metrics.fourier.mae_percent>1e-10)throw Error('FOURIER_ORACLE');
  for(const bad of [fixture.replace('DEL_m4_MPa','bad'),fixture.replace('A,S,0,3','A,S,0,-3'),fixture.replace('A,S,22.5','A,S,23.5')]){let rejected=false;try{evaluate(bad)}catch{rejected=true}if(!rejected)throw Error('REJECTION_FAILED')}
  console.log('SELFTEST_PASS analytic harmonic and 3 rejects');
 }else console.log(JSON.stringify(evaluate(fs.readFileSync(source,'utf8')),null,2));
}
module.exports={evaluate};
