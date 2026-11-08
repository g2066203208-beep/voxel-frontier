#!/usr/bin/env node
'use strict';
// S12: source-locked real ESM event-to-event spectral-shape rejection, not design-spectrum admission.

const SOURCE_SHA256='c668e62e023b9f39029f412ae8f173968416cce78d71fd5033eb0a438c303abe';
const EXPECTED_PERIODS=[4,6,6.2309577628652,8];
function demand(b,m){if(!b)throw Error(m);}
function parse(csv){
  const lines=csv.trim().split(/\r?\n/),header=lines.shift().split(',');
  const needed=['period_s','gm_0008_m_s2','gm_0009_m_s2','gm_ratio_0008_over_0009','status'];
  demand(needed.every(k=>header.includes(k)),'missing column');
  demand(lines.length===4,'four common periods required');
  const rows=lines.map((line,i)=>{
    const cells=line.split(',');demand(cells.length===header.length,'CSV width');
    const obj=Object.fromEntries(header.map((k,j)=>[k,cells[j]]));
    const T=Number(obj.period_s),a=Number(obj.gm_0008_m_s2),b=Number(obj.gm_0009_m_s2),r=Number(obj.gm_ratio_0008_over_0009);
    demand([T,a,b,r].every(Number.isFinite)&&a>0&&b>0&&r>0,'finite positive PSA');
    demand(Math.abs(T-EXPECTED_PERIODS[i])<1e-9,'period identity/order');
    demand(Math.abs(a/b/r-1)<1e-9,'derived ratio mismatch');
    demand(obj.status==='PROCESSED_ESM_SAME_STATION_COMPARISON_NOT_DESIGN','provenance status');
    return {T,a,b,r};
  });
  return rows;
}
function minimax(rows){
  demand(rows.length>=2,'at least two periods');
  const ratios=rows.map(x=>x.r);demand(ratios.every(x=>Number.isFinite(x)&&x>0),'positive ratios');
  const lo=Math.min(...ratios),hi=Math.max(...ratios);
  const scale=2*lo*hi/(lo+hi),lowerBound=(hi-lo)/(hi+lo);
  const errors=rows.map(x=>scale/x.r-1);
  demand(Math.abs(Math.max(...errors.map(Math.abs))-lowerBound)<1e-12,'analytic minimax identity');
  function admission(tol){demand(Number.isFinite(tol)&&tol>=0&&tol<1,'tolerance must be 0<=tol<1');
    const low=Math.max(...ratios.map(r=>r*(1-tol))),high=Math.min(...ratios.map(r=>r*(1+tol)));
    return {tol,lower:low,upper:high,feasible:low<=high+1e-12};}
  return {lo,hi,scale,lowerBound,errors,admissions:[.1,.2,.25].map(admission)};
}
function csvOut(rows,m){
  const f=x=>x.toFixed(12);
  return 'period_s,gm_0008_m_s2,gm_0009_m_s2,raw_ratio_0008_over_0009,minimax_scale_0009_to_0008,scaled_0009_over_0008,relative_error_percent,illustrative_20pct_pointwise_pass,source_status\n'
    +rows.map((r,i)=>[f(r.T),f(r.a),f(r.b),f(r.r),f(m.scale),f(m.scale/r.r),f(100*m.errors[i]),Math.abs(m.errors[i])<=.2?'true':'false','REAL_ESM_DERIVED_PSA_NOT_DESIGN_TARGET'].join(',')).join('\n')+'\n';
}
function svgOut(rows,m){
  const X=t=>125+(t-4)*115,Y1=r=>340-(r-10)*17,Y2=e=>350-e*420;
  const poly=(arr,xf,yf)=>arr.map((v,i)=>(i?'L':'M')+xf(rows[i].T).toFixed(1)+' '+yf(v).toFixed(1)).join(' ');
  const labels=rows.map((r,i)=>'<text x="'+X(r.T).toFixed(1)+'" y="395" font-size="13" text-anchor="middle">'+(i===2?'6.231':r.T.toFixed(0))+'</text>').join('');
  const dots=rows.map((r,i)=>'<circle cx="'+X(r.T).toFixed(1)+'" cy="'+Y1(r.r).toFixed(1)+'" r="5" fill="#087b91"/><circle cx="'+(X(r.T)+610).toFixed(1)+'" cy="'+Y2(100*m.errors[i]).toFixed(1)+'" r="5" fill="#c35128"/>').join('');
  const L='<line x1="125" y1="340" x2="560" y2="340" stroke="#666"/><line x1="125" y1="85" x2="125" y2="340" stroke="#666"/><line x1="735" y1="85" x2="735" y2="340" stroke="#666"/><line x1="735" y1="340" x2="1170" y2="340" stroke="#666"/>';
  return '<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="500" viewBox="0 0 1240 500">\n<rect width="1240" height="500" fill="white"/><style>text{font-family:Arial,sans-serif;fill:#1d2936}</style>\n'
  +'<text x="55" y="37" font-size="22" font-weight="bold">Two real ESM events: exact minimax constant-scale incompatibility</text>'
  +'<text x="55" y="62" font-size="13">IT.NVL, 4 common periods, 5% SDOF GM pseudo-acceleration; NOT a design-spectrum fit</text>'
  +'<text x="105" y="96" font-size="15">(a) Event 0008 / 0009 PSA ratio</text><text x="735" y="96" font-size="15">(b) Best-scaled 0009 error relative to 0008 (%)</text>'
  +L+'<path d="'+poly(rows, X,Y1,r=>r.r)+'" stroke="#087b91" stroke-width="3" fill="none"/>'
  +'<line x1="125" y1="'+Y1(m.scale).toFixed(1)+'" x2="560" y2="'+Y1(m.scale).toFixed(1)+'" stroke="#7a50a3" stroke-width="2" stroke-dasharray="7 4"/>'
  +'<path d="'+poly(rows,t=>X(t)+610,Y2,m.errors.map(e=>100*e))+'" stroke="#c35128" stroke-width="3" fill="none"/>'
  +[-20,0,20].map(v=>'<line x1="735" y1="'+Y2(v).toFixed(1)+'" x2="1170" y2="'+Y2(v).toFixed(1)+'" stroke="'+(v?'#cc8888':'#999')+'" stroke-dasharray="5 4"/><text x="698" y="'+(Y2(v)+4).toFixed(1)+'" font-size="12">'+v+'</text>').join('')
  +dots+labels+rows.map((r,i)=>'<text x="'+(X(r.T)+610).toFixed(1)+'" y="395" font-size="13" text-anchor="middle">'+(i===2?'6.231':r.T.toFixed(0))+'</text>').join('')
  +'<text x="260" y="420" font-size="14">Period (s)</text><text x="885" y="420" font-size="14">Period (s)</text>'
  +'<text x="55" y="457" font-size="14">Optimal scale = '+m.scale.toFixed(6)+'; irreducible maximum error = '+(100*m.lowerBound).toFixed(6)+'% (> illustrative 20% band).</text>'
  +'<text x="55" y="480" font-size="12">Same 2012 Emilia sequence; four correlated periods; processing low-cut and SNR limits remain; no site target spectrum available.</text>\n</svg>\n';
}
function selfTest(){
  const mk=(ratios)=>ratios.map((r,i)=>({T:i+1,r}));
  const z=minimax(mk([2,2,2,2]));demand(z.lowerBound===0&&Math.abs(z.scale-2)<1e-12,'proportional control');
  const a=minimax(mk([1,2]));demand(Math.abs(a.scale-4/3)<1e-12&&Math.abs(a.lowerBound-1/3)<1e-12,'two-point exact oracle');
  const b=minimax(mk([2,1]));demand(Math.abs(a.scale-b.scale)<1e-12,'row permutation invariance');
  const c=minimax(mk([11.219431908032,17.711977969388,16.598556538748,12.858183463447]));
  demand(Math.abs(c.lowerBound-.224411671911752)<1e-12,'real-source numerical oracle');
  demand(!c.admissions[0].feasible&&!c.admissions[1].feasible&&c.admissions[2].feasible,'10/20/25% rejection');
  let rejected=0;const bad=[
    ()=>minimax(mk([0,1])),()=>minimax(mk([1,NaN])),()=>minimax(mk([1])),
    ()=>c.admissions[0]&&minimax(mk([-1,1])),
    ()=>parse('period_s,gm_0008_m_s2,gm_0009_m_s2,gm_ratio_0008_over_0009,status\n4,1,2,2,PROCESSED_ESM_SAME_STATION_COMPARISON_NOT_DESIGN'),
    ()=>minimax(mk([1,Infinity]))];
  bad.forEach(fn=>{try{fn();}catch{rejected++;}});
  demand(rejected===bad.length,'six malformed-input rejections');
  return {positive:5,rejected,real_bound:c.lowerBound};
}
module.exports={parse,minimax,csvOut,svgOut,selfTest};

if(require.main===module){
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 const here=__dirname,root=path.join(here,'real-records');
 const inputPath=path.join(root,'S05_ESM_TWO_EVENT_NVL_NORMALIZED_SHAPE_20261108.csv');
 const outputPath=path.join(root,'S12_ESM_TWO_EVENT_MINIMAX_SCALE_20261108.csv');
 const figurePath=path.join(here,'../../manuscript/final-thesis/figures/FIG_S12_ESM_TWO_EVENT_MINIMAX_SCALE_20261108.svg');
 const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
 if(process.argv.includes('--self-test')){console.log(JSON.stringify(module.exports.selfTest()));process.exit(0);}
 const source=fs.readFileSync(inputPath,'utf8');
 if(sha(source)!==SOURCE_SHA256)throw Error('SHA256_SOURCE_MISMATCH');
 const rows=module.exports.parse(source),m=module.exports.minimax(rows);
 const files=[[outputPath,module.exports.csvOut(rows,m)],[figurePath,module.exports.svgOut(rows,m)]];
 if(process.argv.includes('--write'))files.forEach(([p,s])=>fs.writeFileSync(p,s));
 else if(process.argv.includes('--check'))files.forEach(([p,s])=>{if(fs.readFileSync(p,'utf8')!==s)throw Error('OUTPUT_MISMATCH '+p);});
 else throw Error('Use --self-test, --write, or --check; no implicit overwrite');
 console.log(JSON.stringify({source_sha256:sha(source),rows:rows.length,scale:m.scale,minimax_error_pct:100*m.lowerBound,admission:m.admissions,output_sha256:files.map(([p,s])=>[path.basename(p),sha(s)])}));
}
