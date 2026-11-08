'use strict';
// S08 real ESM archive: E-only NONPRODUCTION linear-beam proxy, not wind/seismic acceptance.
const fs=require('fs'),crypto=require('crypto'),path=require('path');
const H='direction,time_s,top_relative_u_m,top_absolute_acc_m_s2,base_elastic_shear_N,base_elastic_moment_Nm';
const SOURCE_SHA='bab269897640e91d11da3ad02f8a0f3cf537c5e5aaf0f173bba6b1244a3591e0';
const TOWER_SHA='f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983';
const ESM_SHA='a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34';
const Q=[['top_relative_u_m','Tower-top displacement','mm',1000],['top_absolute_acc_m_s2','Tower-top acceleration','m/s2',1],['base_elastic_shear_N','Base elastic shear','kN',.001],['base_elastic_moment_Nm','Base elastic moment','kN*m',.001]];
const check=(ok,msg)=>{if(!ok)throw Error(msg)};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function parse(s,n=32040){
 const a=s.trimEnd().split(/\r?\n/);check(a.shift()===H,'HEADER');check(a.length===2*n,'ROW_COUNT');
 const d=[[],[]];
 for(let i=0;i<2*n;i++){
  const v=a[i].split(','),g=Math.floor(i/n),j=i%n;
  check(v.length===6&&v[0]===(g?'HNN':'HNE'),'DIRECTION_OR_FIELDS');
  check(v.slice(1).every(x=>x.trim()!==''),'BLANK');
  const r=v.slice(1).map(Number);check(r.every(Number.isFinite),'NONFINITE');
  check(Math.abs(r[0]-j*.005)<1e-8,'TIME_GRID');d[g].push(r);
 }
 return d;
}
function analyze(d){
 check(d.length===2&&d[0].length===d[1].length&&d[0].length>=3,'PAIR_COUNT');
 const n=d[0].length,rows=[];
 for(let q=0;q<4;q++){
  let full=-1,coarse=-1,idx=0,ic=0,ax=0,ay=0,ix=0,iy=0;
  const f=Q[q][3];
  for(let i=0;i<n;i++){
   const a=d[0][i],b=d[1][i];check(Math.abs(a[0]-b[0])<1e-10,'TIME_MISMATCH');
   const x=a[q+1]*f,y=b[q+1]*f,v=Math.hypot(x,y);
   if(Math.abs(x)>ax){ax=Math.abs(x);ix=i;}
   if(Math.abs(y)>ay){ay=Math.abs(y);iy=i;}
   if(v>full){full=v;idx=i;}if(i%20===0&&v>coarse){coarse=v;ic=i;}
  }
  check(coarse>0&&full>=coarse&&full>=Math.max(ax,ay)-1e-9,'PEAK_BOUNDS');
  const rss=Math.hypot(ax,ay);check(rss>=full-1e-9,'RSS_BOUND');
  rows.push({qoi:Q[q][0],unit:Q[q][2],fullrate_vector_peak:full,fullrate_peak_time_s:d[0][idx][0],
   HNE_at_fullrate_peak:d[0][idx][q+1]*f,HNN_at_fullrate_peak:d[1][idx][q+1]*f,
   HNE_independent_peak:ax,HNN_independent_peak:ay,HNE_peak_time_s:d[0][ix][0],HNN_peak_time_s:d[1][iy][0],
   max_single_fullrate:Math.max(ax,ay),independent_peak_RSS:rss,coarse_0p1_vector_peak:coarse,
   coarse_0p1_peak_time_s:d[0][ic][0],fullrate_vs_coarse_pct:100*(full/coarse-1),
   fullrate_vs_max_single_pct:100*(full/Math.max(ax,ay)-1),independent_RSS_over_fullrate_pct:100*(rss/full-1)});
 }
 return rows;
}
const KEYS=['qoi','unit','fullrate_vector_peak','fullrate_peak_time_s','HNE_at_fullrate_peak','HNN_at_fullrate_peak','HNE_independent_peak','HNN_independent_peak','HNE_peak_time_s','HNN_peak_time_s','max_single_fullrate','independent_peak_RSS','coarse_0p1_vector_peak','coarse_0p1_peak_time_s','fullrate_vs_coarse_pct','fullrate_vs_max_single_pct','independent_RSS_over_fullrate_pct','fullrate_source_sha256'];
function csv(rows){return KEYS.join(',')+'\n'+rows.map(r=>KEYS.map(k=>k==='fullrate_source_sha256'?SOURCE_SHA:typeof r[k]==='number'?r[k].toPrecision(15):r[k]).join(',')).join('\n')+'\n';}
function svg(rows){
 let s='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720"><rect width="1200" height="720" fill="white"/>';
 s+='<text x="50" y="49" font-family="Arial" font-size="26" font-weight="bold">Full-rate coincident horizontal response | E-only beam proxy</text>';
 s+='<text x="50" y="77" font-family="Arial" font-size="15">Real ESM HNE/HNN; 0.005 s, 32040 samples/axis; not structural design</text>';
 s+='<text x="55" y="132" font-family="Arial" font-size="19">A  Coarse-sample miss vs 0.005 s peak</text>';
 s+='<text x="635" y="132" font-family="Arial" font-size="19">B  Independent-peak RSS excess</text>';
 rows.forEach((r,i)=>{
  const y=187+i*105,p=r.fullrate_vs_coarse_pct,k=r.independent_RSS_over_fullrate_pct,label=Q[i][1];
  s+='<text x="55" y="'+(y-12)+'" font-family="Arial" font-size="15">'+label+'</text>';
  s+='<rect x="55" y="'+y+'" width="440" height="25" fill="#eaf0f3"/>';
  s+='<rect x="55" y="'+y+'" width="'+(440*p/2).toFixed(3)+'" height="25" fill="#267e98"/>';
  s+='<text x="506" y="'+(y+19)+'" font-family="Arial" font-size="15">'+p.toFixed(3)+'%</text>';
  s+='<text x="635" y="'+(y-12)+'" font-family="Arial" font-size="15">'+label+'</text>';
  s+='<rect x="635" y="'+y+'" width="440" height="25" fill="#eaf0f3"/>';
  s+='<rect x="635" y="'+y+'" width="'+(440*k/25).toFixed(3)+'" height="25" fill="#d07846"/>';
  s+='<text x="1085" y="'+(y+19)+'" font-family="Arial" font-size="15">'+k.toFixed(3)+'%</text>';
 });
 return s+'<text x="55" y="630" font-family="Arial" font-size="14">A: 0.1 s decimation misses maxima (2% scale). B: asynchronous RSS excess (25% scale).</text><text x="55" y="661" font-family="Arial" font-size="14">Shear/moment are elastic restoring components, NOT total dynamic reactions.</text></svg>\n';
}
function test(){
 const mk=(d,rows)=>rows.map((r,i)=>[d,i*.005].concat(r).join(',')).join('\n');
 const a=[[.001,0,0,0],[.003,3,3000,3000],[.004,4,4000,4000]],b=[[0,0,0,0],[.004,4,4000,4000],[0,0,0,0]];
 const s=H+'\n'+mk('HNE',a)+'\n'+mk('HNN',b)+'\n';
 const r=analyze(parse(s,3));check(Math.abs(r[0].fullrate_vector_peak-5)<1e-10,'3_4_5_ORACLE');
 const bad=[s.replace('HNE,0.005','HNE,0.006'),s.replace('HNN,0.005','HNN,0.006'),s.replace('HNE,0.005,0.003','HNE,0.005,NaN'),s.replace('HNE,0.005,0.003','HNE,0.005,'),s.replace('HNN,0.01,0,0,0,0','HNE,0.01,0,0,0,0'),s.replace('HNE,0.005,0.003,3,3000,3000','HNE,0.005,0.003,3,3000'),s.slice(0,-18),s.replace(H,'bad')];
 bad.forEach((z,i)=>{let rejected=false;try{parse(z,3)}catch(e){rejected=true}check(rejected,'REJECTION_'+i)});
 check(csv(r).includes('fullrate_vector_peak')&&svg(r).startsWith('<svg'),'RENDER');
 return 'SELFTEST_PASS 3-4-5 and 8 invalid inputs rejected';
}
if(process.argv.includes('--self-test'))console.log(test());
else{
 const [input,receipt,out]=process.argv.slice(2);check(input&&receipt&&out,'USAGE: node script fullrate.csv receipt.json output_dir');
 const bytes=fs.readFileSync(input);check(hash(bytes)===SOURCE_SHA,'FULLRATE_SHA256');
 const r=JSON.parse(fs.readFileSync(receipt,'utf8'));
 check(r.full_rate_history?.file_sha256===SOURCE_SHA&&r.full_rate_history.n_rows===64080&&r.full_rate_history.dt_s===.005,'RECEIPT_IDENTITY');
 check(r.source_tower_sha256===TOWER_SHA&&r.source_esm_sha256===ESM_SHA&&!r.full_rate_history.admissible_for_S09_four_scenario_comparison,'MODEL_IDENTITY');
 const rows=analyze(parse(bytes.toString()));fs.mkdirSync(out,{recursive:true});
 fs.writeFileSync(path.join(out,'S08_ESM_FULLRATE_PAIRED_VECTOR_4QOI_20261109.csv'),csv(rows));
 fs.writeFileSync(path.join(out,'FIG_S08_ESM_FULLRATE_PAIRED_VECTOR_20261109.svg'),svg(rows));
 console.log(JSON.stringify(rows,null,2));
}