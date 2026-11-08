#!/usr/bin/env node
'use strict';
// Real ESM two-horizontal E-only LINEAR BEAM PROXY. Not a wind/earthquake physical acceptance.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
// PURE_START
const SOURCE_SHA='c6763281ca366b16849321b7542024af111d78ebb6ee470c912dda060b51ba22';
const RECEIPT_SHA='02730b484864b02cf1d7c83826ac819ef768fd7979cb4723c2962fd0a85ed939';
function req(ok,msg){if(!ok)throw Error(msg);}
const qois=[
 ['top_relative_u_m','Top displacement','mm',1000,'peak_top_relative_displacement_m',1000],
 ['top_absolute_acc_m_s2','Top acceleration','m/s2',1,'peak_top_absolute_acceleration_m_s2',1],
 ['base_elastic_shear_N','Base elastic shear','kN',.001,'peak_base_elastic_shear_kN',1],
 ['base_elastic_moment_Nm','Base elastic moment','kN*m',.001,'peak_base_elastic_moment_kNm',1]
];
function analyze(csv,receipt,n=1602){
 const lines=csv.trim().split(/\r?\n/);
 req(lines.shift()==='direction,time_s,top_relative_u_m,top_absolute_acc_m_s2,base_elastic_shear_N,base_elastic_moment_Nm','HEADER');
 req(lines.length===2*n,'COUNT');
 req(receipt.classification==='NONPRODUCTION_CONDITIONAL_LINEAR_158M_BEAM_PROXY_NOT_ABAQUS_E','CLASS');
 req(receipt.source_tower_sha256==='f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983','TOWER');
 req(receipt.source_esm_sha256==='a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34','ESM');
 req(Array.isArray(receipt.peak_summary)&&receipt.peak_summary.length===2,'PEAK_RECEIPT');
 const d=[[],[]];
 lines.forEach((line,i)=>{
  const a=line.split(','),g=i<n?0:1,k=i%n;
  req(a.length===6&&a[0]===(g?'HNN':'HNE'),'DIRECTION_OR_FIELDS');
  req(a.slice(1).every(s=>s.trim()!==''),'BLANK');
  const v=a.slice(1).map(Number);
  req(v.every(Number.isFinite),'NONFINITE');
  req(Math.abs(v[0]-.1*k)<1e-8,'TIME_GRID');
  d[g].push(v);
 });
 const pk=Object.fromEntries(receipt.peak_summary.map(p=>[p.direction,p]));
 req(pk.HNE&&pk.HNN,'PEAK_NAMES');
 return qois.map(([key,label,unit,f,peakKey,ff],j)=>{
  let a=0,b=0,v=0,ta=0,tb=0,tv=0,vx=0,vy=0;
  for(let i=0;i<n;i++){
   const x=d[0][i][j+1]*f,y=d[1][i][j+1]*f,t=d[0][i][0];
   req(Math.abs(t-d[1][i][0])<1e-10,'PAIR_TIME');
   if(Math.abs(x)>a){a=Math.abs(x);ta=t;}
   if(Math.abs(y)>b){b=Math.abs(y);tb=t;}
   if(Math.hypot(x,y)>v){v=Math.hypot(x,y);tv=t;vx=x;vy=y;}
  }
  const fa=Number(pk.HNE[peakKey])*ff,fb=Number(pk.HNN[peakKey])*ff;
  req(Number.isFinite(fa)&&Number.isFinite(fb)&&fa>0&&fb>0,'FULLRATE_PEAK');
  req(a<=fa*(1+1e-8)&&b<=fb*(1+1e-8),'FULLRATE_CONFLICT');
  const rss=Math.hypot(a,b),lower=Math.max(v,fa,fb),upper=Math.hypot(fa,fb);
  req(lower<=upper*(1+1e-10),'BOUNDS');
  return {qoi:key,label,unit,HNE_sample:a,HNN_sample:b,HNE_peak_time_s:ta,HNN_peak_time_s:tb,
   max_single_sample:Math.max(a,b),vector_sample:v,vector_peak_time_s:tv,HNE_at_vector_peak:vx,HNN_at_vector_peak:vy,
   vector_gain_vs_single_pct:100*(v/Math.max(a,b)-1),rss_independent_sample:rss,
   rss_overestimate_pct:100*(rss/v-1),HNE_fullrate_peak:fa,HNN_fullrate_peak:fb,
   vector_fullrate_lower:lower,vector_fullrate_upper:upper,fullrate_bound_width_pct:100*(upper/lower-1)};
 });
}
function toCsv(rows){
 const keys=['qoi','unit','HNE_sample','HNN_sample','HNE_peak_time_s','HNN_peak_time_s','max_single_sample','vector_sample','vector_peak_time_s','HNE_at_vector_peak','HNN_at_vector_peak','vector_gain_vs_single_pct','rss_independent_sample','rss_overestimate_pct','HNE_fullrate_peak','HNN_fullrate_peak','vector_fullrate_lower','vector_fullrate_upper','fullrate_bound_width_pct','source_sha256','receipt_sha256'];
 const fmt=x=>typeof x==='number'?x.toPrecision(13):x;
 return keys.join(',')+'\n'+rows.map(r=>keys.map(k=>fmt(k==='source_sha256'?SOURCE_SHA:k==='receipt_sha256'?RECEIPT_SHA:r[k])).join(',')).join('\n')+'\n';
}
function toSvg(rows){
 let s='<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="640" viewBox="0 0 1180 640"><rect width="1180" height="640" fill="white"/>';
 s+='<text x="55" y="53" font-family="Arial" font-size="27" font-weight="bold" fill="#172a3c">Paired horizontal response: peak noncoincidence and bounds</text>';
 s+='<text x="55" y="82" font-family="Arial" font-size="15" fill="#526373">Real ESM HNE/HNN, 158 m linear E-only beam proxy, 0.1 s displayed samples; NOT wind-seismic design</text>';
 s+='<text x="55" y="137" font-family="Arial" font-size="19" font-weight="bold">A  Coincident vector / independent RSS</text>';
 s+='<text x="628" y="137" font-family="Arial" font-size="19" font-weight="bold">B  Full-rate peak: lower / upper bound</text>';
 rows.forEach((r,i)=>{
  const y=190+90*i,ra=100*r.vector_sample/r.rss_independent_sample,rb=100*r.vector_fullrate_lower/r.vector_fullrate_upper;
  s+='<text x="55" y="'+(y-9)+'" font-family="Arial" font-size="15" fill="#40546a">'+r.label+'</text>';
  s+='<rect x="55" y="'+y+'" width="420" height="25" fill="#e7edf1" rx="3"/>';
  s+='<rect x="55" y="'+y+'" width="'+(4.2*ra).toFixed(3)+'" height="25" fill="#227d93" rx="3"/>';
  s+='<text x="485" y="'+(y+19)+'" font-family="Arial" font-size="15">'+ra.toFixed(2)+'%</text>';
  s+='<text x="628" y="'+(y-9)+'" font-family="Arial" font-size="15" fill="#40546a">'+r.label+'</text>';
  s+='<rect x="628" y="'+y+'" width="420" height="25" fill="#e7edf1" rx="3"/>';
  s+='<rect x="628" y="'+y+'" width="'+(4.2*rb).toFixed(3)+'" height="25" fill="#c67b4d" rx="3"/>';
  s+='<text x="1058" y="'+(y+19)+'" font-family="Arial" font-size="15">'+rb.toFixed(2)+'%</text>';
 });
 s+='<text x="55" y="572" font-family="Arial" font-size="14" fill="#526373">A: gray is the extra peak implied by combining non-simultaneous maxima.</text>';
 s+='<text x="628" y="572" font-family="Arial" font-size="14" fill="#526373">B: gray is unresolved, not a statistical confidence interval.</text>';
 s+='<text x="55" y="611" font-family="Arial" font-size="13" fill="#526373">Full-rate individual peaks constrain but do not identify the not-yet-recomputed paired full-rate vector peak.</text></svg>\n';
 return s;
}
function selfTest(){
 const p={classification:'NONPRODUCTION_CONDITIONAL_LINEAR_158M_BEAM_PROXY_NOT_ABAQUS_E',source_tower_sha256:'f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983',source_esm_sha256:'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34',peak_summary:[{direction:'HNE',peak_top_relative_displacement_m:.005,peak_top_absolute_acceleration_m_s2:5,peak_base_elastic_shear_kN:5,peak_base_elastic_moment_kNm:5},{direction:'HNN',peak_top_relative_displacement_m:.004,peak_top_absolute_acceleration_m_s2:4,peak_base_elastic_shear_kN:4,peak_base_elastic_moment_kNm:4}]};
 const a=['direction,time_s,top_relative_u_m,top_absolute_acc_m_s2,base_elastic_shear_N,base_elastic_moment_Nm','HNE,0,0,0,0,0','HNE,0.1,0.003,3,3000,3000','HNE,0.2,0.004,4,4000,4000','HNN,0,0,0,0,0','HNN,0.1,0.004,4,4000,4000','HNN,0.2,0,0,0,0'];
 const c=a.join('\n')+'\n',r=analyze(c,p,3);
 req(r.length===4&&Math.abs(r[0].vector_sample-5)<1e-12&&r[0].vector_peak_time_s===.1,'3_4_5_ORACLE');
 let bad=0;
 for(const [i,z] of [[1,'HNE,0,NaN,0,0,0'],[4,'HNE,0,0,0,0,0'],[5,'HNN,0.13,0.004,4,4000,4000'],[2,'HNE,0.1,0.003,3,3000'],[3,'HNN,0.2,0,0,0,0']]){
  const b=a.slice();b[i]=z;try{analyze(b.join('\n'),p,3);}catch(e){bad++;}
 }
 try{analyze(a.slice(0,-1).join('\n'),p,3);}catch(e){bad++;}
 try{analyze(c,{...p,source_esm_sha256:'bad'},3);}catch(e){bad++;}
 try{analyze(c,{...p,peak_summary:p.peak_summary.map(x=>({...x,peak_top_relative_displacement_m:.001}))},3);}catch(e){bad++;}
 req(bad===8,'REJECT_'+bad);
 req(toCsv(r).split('\n').length===6&&toSvg(r).startsWith('<svg'),'RENDER');
 return 'SELFTEST_PASS synthetic 3-4-5; 8 expected refusals; CSV/SVG';
}
// PURE_END
function sha(b){return crypto.createHash('sha256').update(b).digest('hex');}
if(process.argv.includes('--self-test'))console.log(selfTest());
else{
 const dir=path.join(__dirname,'real-records');
 const c=fs.readFileSync(path.join(dir,'S08_158M_BEAM_PROXY_HISTORY_20261102.csv'));
 const r=fs.readFileSync(path.join(dir,'S08_158M_BEAM_PROXY_RECEIPT_20261102.json'));
 req(sha(c)===SOURCE_SHA&&sha(r)===RECEIPT_SHA,'SOURCE_SHA256');
 const rows=analyze(c.toString(),JSON.parse(r.toString()));
 const k=process.argv.indexOf('--out');
 if(k>=0){req(process.argv[k+1],'OUT');fs.mkdirSync(process.argv[k+1],{recursive:true});fs.writeFileSync(path.join(process.argv[k+1],'S08_ESM_PAIRED_VECTOR_4QOI_20261109.csv'),toCsv(rows));fs.writeFileSync(path.join(process.argv[k+1],'FIG_S08_ESM_PAIRED_VECTOR_BOUNDS_20261109.svg'),toSvg(rows));}
 console.log(JSON.stringify(rows,null,2));
}
