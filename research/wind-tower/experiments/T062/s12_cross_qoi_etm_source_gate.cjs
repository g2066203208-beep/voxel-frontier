'use strict';
// Source-level cross-archive case-label comparison. NOT a physical same-state pairing.
const CASES=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
const SHA_DEL='1bf750ba3ea33153dbe4b23e87a1b973ca73ab41e446b2d9d5f3fac2881238a9';
const SHA_STRESS='6002f69286eb9941265697732ec7acd961ac6b5757d7472423d91e0374288f21';
function check(v,msg){if(!v)throw Error(msg);}
function parse(text){
  check(typeof text==='string'&&text.length>0,'empty source');
  const lines=text.trim().split(/\r?\n/),heads=lines.shift().split(',');
  check(new Set(heads).size===heads.length,'duplicate headers');
  return lines.map((line,i)=>{const cells=line.split(',');check(cells.length===heads.length,'row width '+(i+2));const r={};heads.forEach((h,j)=>r[h]=cells[j]);return r;});
}
function number(v,name){check(v!==''&&v!==undefined&&Number.isFinite(Number(v)), 'nonfinite '+name);return Number(v);}
function compute(delText,stressText){
  const del=parse(delText),stress=parse(stressText);
  check(del.length===72&&stress.length===124,'expected 72 DEL and 124 section rows');
  const rows=[];
  for(const id of CASES){
    const dr=del.filter(x=>x.case===id&&x.channel==='TwrBsMyt'&&x.class==='ETM');
    const sr=stress.filter(x=>x.case===id);
    check(dr.length===1&&sr.length===31,'missing/duplicate case '+id);
    check(new Set(sr.map(x=>x.segment)).size===31,'duplicate section '+id);
    for(let k=1;k<=31;k++)check(sr.some(x=>x.segment==='CSEG_'+String(k).padStart(2,'0')),'missing section');
    check(sr.every(x=>x.status==='CONDITIONAL_GROSS_ELASTIC_SOURCE_ENVELOPE_NOT_MATERIAL_POINT'&&number(x.n_samples,'n')===12001),'invalid stress identity');
    const sorted=sr.map(x=>({...x,peak:number(x.continuous_max_sigma_MPa,'sigma')})).sort((a,b)=>b.peak-a.peak);
    check(sorted[0].peak>sorted[1].peak,'stress peak tie');
    const row=sorted[0];
    const value=number(dr[0].corrected_DEL_MNm,'DEL');
    check(value>0&&row.peak>0,'nonpositive value');
    rows.push({case:id,del:value,stress:row.peak,segment:row.segment,z:number(row.gage_z_m,'z'),t:number(row.continuous_max_time_s,'t')});
  }
  const dsort=[...rows].sort((a,b)=>b.del-a.del),ssort=[...rows].sort((a,b)=>b.stress-a.stress);
  check(dsort.every((r,i)=>i===0||r.del!==dsort[i-1].del),'DEL ties');
  check(ssort.every((r,i)=>i===0||r.stress!==ssort[i-1].stress),'stress ties');
  rows.forEach(r=>{r.delRank=dsort.indexOf(r)+1;r.stressRank=ssort.indexOf(r)+1;});
  let reversals=0;
  for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++)
    if((rows[i].del-rows[j].del)*(rows[i].stress-rows[j].stress)<0)reversals++;
  return {rows,reversals,pairs:6,tau:1-2*reversals/6};
}
function csv(o){return 'case,corrected_My_DEL_MNm,max_positive_gross_nominal_stress_MPa,control_segment,control_z_m,stress_peak_time_s,My_DEL_rank_within_4,stress_peak_rank_within_4\n'+o.rows.map(r=>[r.case,r.del.toFixed(9),r.stress.toFixed(9),r.segment,r.z.toFixed(6),r.t.toFixed(2),r.delRank,r.stressRank].join(',')).join('\n')+'\n';}
function svg(o){
  const x=v=>110+(v-22)*115,y=v=>480-(v-14)*25;
  const labs={'U09p343881_ETM_S06':'U09 ETM S06','U11p4_ETM_S04':'U11 ETM S04','U19p202140_ETM_S04':'U19 ETM S04','U19p202140_ETM_S06':'U19 ETM S06'};
  let a=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="590" viewBox="0 0 960 590">','<rect width="960" height="590" fill="white"/>','<text x="80" y="40" font-family="Arial" font-size="22" font-weight="bold" fill="#172b4d">Cross-archive ETM control ranking: different QoIs</text>','<text x="80" y="66" font-family="Arial" font-size="14" fill="#475569">Four identical case labels; model-state equality across archives NOT independently verified</text>','<path d="M110 130 V480 H800" fill="none" stroke="#1f2937" stroke-width="2"/>'];
  for(let v=22;v<=28;v+=2)a.push('<line x1="'+x(v)+'" y1="480" x2="'+x(v)+'" y2="486" stroke="#475569"/><text x="'+x(v)+'" y="505" text-anchor="middle" font-family="Arial" font-size="14">'+v+'</text>');
  for(let v=14;v<=26;v+=4)a.push('<line x1="104" y1="'+y(v)+'" x2="110" y2="'+y(v)+'" stroke="#475569"/><text x="96" y="'+(y(v)+5)+'" text-anchor="end" font-family="Arial" font-size="14">'+v+'</text>');
  a.push('<text x="455" y="550" text-anchor="middle" font-family="Arial" font-size="16">Corrected tower-base My load DEL (MN m)</text>','<text x="24" y="306" text-anchor="middle" transform="rotate(-90 24 306)" font-family="Arial" font-size="16">Max positive gross-section nominal stress (MPa)</text>');
  o.rows.forEach((r,i)=>{const dx=[-8,10,-7,8][i],dy=[-19,24,24,-15][i];a.push('<circle cx="'+x(r.del).toFixed(2)+'" cy="'+y(r.stress).toFixed(2)+'" r="7" fill="'+(i<2?'#0f766e':'#334155')+'" stroke="white" stroke-width="1.5"/>','<text x="'+(x(r.del)+dx).toFixed(2)+'" y="'+(y(r.stress)+dy).toFixed(2)+'" font-family="Arial" font-size="13" text-anchor="'+(dx<0?'end':'start')+'" fill="#1f2937">'+labs[r.case]+'</text>');});
  a.push('<rect x="620" y="88" width="288" height="95" fill="#f1f5f9" stroke="#cbd5e1"/>','<text x="636" y="116" font-family="Arial" font-size="17" font-weight="bold">2 / 6 pairwise reversals</text>','<text x="636" y="143" font-family="Arial" font-size="14">Kendall tau = '+o.tau.toFixed(6)+'</text>','<text x="636" y="166" font-family="Arial" font-size="12">All 4 gross-stress maxima: CSEG17</text>','<text x="80" y="575" font-family="Arial" font-size="11" fill="#475569">Historical derived CSVs; ETM is not formal DLC1.2; positive stress envelope is not local material stress or Miner damage.</text>','</svg>');
  return a.join('\n')+'\n';
}
if(typeof require==='function'&&require.main===module){
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 const inputs=[path.join(__dirname,'T062_72CASE_RAINFLOW_RANK_TRANSITIONS_20261107.csv'),path.join(__dirname,'../T077/recovery/S10_4ETM_31SEG_CONTINUOUS_AZIMUTH_ENVELOPE_20261102.csv')];
 const bytes=inputs.map(p=>fs.readFileSync(p));
 [SHA_DEL,SHA_STRESS].forEach((want,i)=>check(crypto.createHash('sha256').update(bytes[i]).digest('hex')===want,'source SHA mismatch'));
 const result=compute(bytes[0].toString('utf8'),bytes[1].toString('utf8'));
 check(result.reversals===2&&result.rows.every(r=>r.segment==='CSEG_17'),'source oracle');
 if(process.argv.includes('--write')){
   fs.writeFileSync(path.join(__dirname,'S12_4ETM_CROSS_QOI_RANK_20261108.csv'),csv(result));
   fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG_JOURNAL_S12_CROSS_QOI_ETM_RANK_20261108.svg'),svg(result));
 }
 console.log(JSON.stringify({rows:result.rows,reversals:result.reversals,pairs:result.pairs,tau:result.tau,source_hashes:[SHA_DEL,SHA_STRESS]},null,2));
}
if(typeof module!=='undefined')module.exports={compute,csv,svg,parse};
