'use strict';
// Original R5 Word Table 3-3; ERA5 100 m; H = V100 >= P95 (8.385 m/s).
// CLI: node s06_era5_highwind_direction_bayes.cjs source.csv output.csv output.svg
// Tests: node s06_era5_highwind_direction_bayes.cjs --self-test
// P(H)=0.05 is a SCENARIO, not a verified exact event fraction.
const fs=require('node:fs'), crypto=require('node:crypto');
const SOURCE_SHA256='53417a3d0223beb07a24fa372eaa5662067eb5780836ea4106100cc325942b96';
const DIR=['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
function need(ok,msg){if(!ok)throw Error(msg);}
function parse(t){
 const ls=t.trim().split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
 need(ls[0]==='sector,all_pct,high_v100_ge_p95_pct','invalid header');
 need(ls.length===17,'expected 16 directions');
 const seen=new Set(), rows=ls.slice(1).map(s=>{
  const a=s.split(',');need(a.length===3,'bad width');
  const d=a[0],all=Number(a[1]),high=Number(a[2]);
  need(DIR.includes(d)&&!seen.has(d),'duplicate/unknown direction');
  need(a[1].trim()!==''&&a[2].trim()!==''&&Number.isFinite(all)&&Number.isFinite(high),'nonfinite input');
  need(all>0&&all<=100&&high>=0&&high<=100,'invalid frequency');
  seen.add(d);return {d,all,high};
 });
 need(DIR.every(d=>seen.has(d)),'missing direction');
 const A=rows.reduce((s,r)=>s+r.all,0),H=rows.reduce((s,r)=>s+r.high,0);
 need(Math.abs(A-100)<=0.080001&&Math.abs(H-100)<=0.080001,'rounding total violated');
 return {rows,A,H};
}
function analyze(t,pH=0.05){
 need(Number.isFinite(pH)&&pH>0&&pH<1,'invalid high-wind event fraction');
 const {rows,A,H}=parse(t);
 const out=rows.map(r=>{
  const pAll=r.all/A,pHighDir=r.high/H,enrich=pHighDir/pAll;
  return {...r,pAll,pHighDir,enrich,post:pH*enrich,
   lower:Math.max(0,r.high-0.005)/(r.all+0.005),
   upper:(r.high+0.005)/(r.all-0.005)};
 });
 need(out.every(r=>r.post<=1),'scenario infeasible');
 const sorted=[...out].sort((a,b)=>b.pHighDir-a.pHighDir||DIR.indexOf(a.d)-DIR.indexOf(b.d));
 let c=0;sorted.forEach((r,i)=>{c+=r.pHighDir;r.rank=i+1;r.cum=c;});
 const budget=[0.5,0.75,0.9,0.95].map(t=>({target:t,k:sorted.find(r=>r.cum>=t).rank}));
 need(Math.abs(out.reduce((s,r)=>s+r.pAll*r.post,0)-pH)<1e-12,'Bayes closure failed');
 return {out,sorted,budget,A,H,pH};
}
function toCsv(r){
 const f=x=>x.toFixed(6);
 const header='sector,all_pct_printed,high_given_H_pct_printed,enrichment_normalized,P_H_given_sector_pct_if_P_H_5pct,rounding_enrichment_lower,rounding_enrichment_upper,high_share_rank,cumulative_high_pct_by_rank';
 return header+'\n'+r.out.map(x=>[x.d,f(x.all),f(x.high),f(x.enrich),f(100*x.post),f(x.lower),f(x.upper),x.rank,f(100*x.cum)].join(',')).join('\n')+'\n';
}
function toSvg(r){
 let v=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="690" viewBox="0 0 1120 690">',
 '<rect width="1120" height="690" fill="#fff"/>',
 '<text x="52" y="43" font-family="Arial" font-size="24" font-weight="bold" fill="#173045">High-wind direction: Bayes inversion of ERA5 source frequencies</text>',
 '<text x="52" y="68" font-family="Arial" font-size="14" fill="#566b7a">100 m; 2005–2025; H: V100 ≥ P95 = 8.385 m/s. Scenario P(H) = 5% (not verified exact count).</text>',
 '<text x="52" y="110" font-family="Arial" font-size="17" font-weight="bold" fill="#203d50">A  Directional high-wind enrichment: P(d | H) / P(d)</text>'];
 const y0=361,h=215,x0=78,dx=59;
 for(let i=0;i<=3;i++){const y=y0-h*i/3;v.push('<line x1="'+x0+'" y1="'+y+'" x2="1060" y2="'+y+'" stroke="'+(i===1?'#bf693b':'#dce5e9')+'" stroke-dasharray="'+(i===1?'6 5':'2 4')+'"/>');v.push('<text x="44" y="'+(y+4)+'" font-family="Arial" font-size="12">'+i+'</text>');}
 r.out.forEach((x,i)=>{const bx=x0+12+i*dx,bh=h*x.enrich/3;
  v.push('<rect x="'+bx+'" y="'+(y0-bh).toFixed(3)+'" width="32" height="'+bh.toFixed(3)+'" rx="3" fill="'+(['N','NNE','SSW'].includes(x.d)?'#cf7045':'#5089aa')+'"/>');
  v.push('<text x="'+(bx+16)+'" y="384" font-family="Arial" font-size="12" text-anchor="middle">'+x.d+'</text>');
 });
 v.push('<text x="75" y="414" font-family="Arial" font-size="12" fill="#99603e">Dashed reference = 1; orange = three most frequent high-wind sectors.</text>');
 v.push('<text x="52" y="453" font-family="Arial" font-size="17" font-weight="bold" fill="#203d50">B  Cumulative high-wind directional exposure (top k sectors)</text>');
 r.sorted.slice(0,8).forEach((x,i)=>{const bx=105+i*120,bh=115*x.cum;
  v.push('<rect x="'+bx+'" y="'+(612-bh).toFixed(3)+'" width="67" height="'+bh.toFixed(3)+'" rx="3" fill="#5b9b8d"/>');
  v.push('<text x="'+(bx+33)+'" y="'+(601-bh).toFixed(3)+'" font-family="Arial" font-size="12" text-anchor="middle">'+(100*x.cum).toFixed(1)+'%</text>');
  v.push('<text x="'+(bx+33)+'" y="634" font-family="Arial" font-size="12" text-anchor="middle">k='+ (i+1) +'</text>');
 });
 v.push('<text x="52" y="669" font-family="Arial" font-size="12" fill="#586d7d">R5 Table 3-3 printed frequencies; directional exposure only, not turbine load, local stress or fatigue damage.</text>','</svg>');
 return v.join('\n')+'\n';
}
function selfTest(){
 const good='sector,all_pct,high_v100_ge_p95_pct\n'+DIR.map(d=>d+',6.25,6.25').join('\n')+'\n';
 const x=analyze(good);need(x.out.every(r=>Math.abs(r.enrich-1)<1e-12),'uniform Bayes failed');
 need(x.budget[0].k===8,'uniform coverage failed');
 const bad=[good.replace('N,6.25,6.25','N,NaN,6.25'),good.replace('N,6.25,6.25','N,-6.25,6.25'),
  good.replace('NNE,6.25,6.25','N,6.25,6.25'),good.replace('NNE,6.25,6.25',''),
  good.replace('NNE,6.25,6.25','NNE,12.50,6.25'),
  good.replace('sector,all_pct,high_v100_ge_p95_pct','sector,wrong,high_v100_ge_p95_pct')];
 for(const s of bad){let rejected=false;try{analyze(s);}catch(_){rejected=true;}need(rejected,'failed to reject corrupted source');}
 let rejected=false;try{analyze(good,1);}catch(_){rejected=true;}need(rejected,'invalid event fraction not rejected');
 return 'PASS uniform/closure + 7 rejection cases';
}
module.exports={parse,analyze,toCsv,toSvg,selfTest,SOURCE_SHA256};
if(require.main===module){
 if(process.argv[2]==='--self-test'){console.log(selfTest());process.exit(0);}
 need(process.argv.length===5,'usage: node SCRIPT source.csv output.csv output.svg');
 const t=fs.readFileSync(process.argv[2],'utf8');
 need(crypto.createHash('sha256').update(t).digest('hex')===SOURCE_SHA256,'source SHA256 mismatch');
 const r=analyze(t);
 fs.writeFileSync(process.argv[3],toCsv(r));fs.writeFileSync(process.argv[4],toSvg(r));
 console.log(JSON.stringify({source_sha256:SOURCE_SHA256,budget:r.budget,
  top:r.sorted.slice(0,3).map(x=>({sector:x.d,enrichment:x.enrich,conditional_high_pct_if_5pct:100*x.post}))},null,2));
}