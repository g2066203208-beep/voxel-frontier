#!/usr/bin/env node
'use strict';
// S06/S12: finite-archive held-out proxy assessment; no physics or production runs.
// Usage: node s06_ntm_proxy_holdout_gate.cjs source.csv summary.csv figure.svg
const EXPECTED_SHA256='4abf76252fa34b2c12635d409e5abc23c4a7d6f759b66dbec12b1932379f4bea';
const HEADER='case,wind_bin,source_outb_sha256,mean_power_MW,mean_rotor_rpm,mean_pitch_deg,TwrBsMyt_DEL_MNm,TwrBsMxt_DEL_MNm,bin_centered_power_MW,bin_centered_My_DEL_MNm';
const SPECS=[['My','mean_power_MW','TwrBsMyt_DEL_MNm'],['Mx','mean_pitch_deg','TwrBsMxt_DEL_MNm']];
const MODELS=['bin_mean','bin_plus_within_slope','pooled_linear'];
function fail(code){throw new Error('S06_HOLDOUT_REJECT_'+code)}
function parseCSV(s){
 if(typeof s!=='string')fail('TYPE');
 const lines=s.trim().split(/\r?\n/);if(lines.shift()!==HEADER)fail('HEADER');
 if(lines.length!==18)fail('COUNT');
 const names=HEADER.split(','),seen=new Set(),bins=new Map(),rows=[];
 for(const line of lines){
  const cells=line.split(',');if(cells.length!==names.length)fail('FIELDS');
  const r=Object.fromEntries(cells.map((v,i)=>[names[i],v]));
  if(!/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(r.case))fail('CASE');
  if(r.case.split('_NTM_')[0]!==r.wind_bin)fail('BIN_ID');
  if(!/^[0-9a-f]{64}$/.test(r.source_outb_sha256))fail('SOURCE_HASH');
  if(seen.has(r.case))fail('DUPLICATE');seen.add(r.case);
  r.seed=r.case.slice(-3);
  for(const k of names.slice(3)){r[k]=Number(r[k]);if(!Number.isFinite(r[k])||cells[names.indexOf(k)].trim()==='')fail('NONFINITE')}
  if(r.mean_power_MW<0||r.mean_rotor_rpm<0||r.TwrBsMyt_DEL_MNm<=0||r.TwrBsMxt_DEL_MNm<=0)fail('UNPHYSICAL_INPUT');
  bins.set(r.wind_bin,(bins.get(r.wind_bin)||0)+1);rows.push(r);
 }
 if(bins.size!==3||[...bins.values()].some(v=>v!==6))fail('BIN_COUNT');
 for(const bin of bins.keys()){const q=rows.filter(r=>r.wind_bin===bin);if(new Set(q.map(r=>r.seed)).size!==6)fail('SEEDS')}
 return rows;
}
function avg(xs){return xs.reduce((s,x)=>s+x,0)/xs.length}
function predict(train,test,model,x,y){
 if(!MODELS.includes(model))fail('MODEL');
 const b=train.filter(r=>r.wind_bin===test.wind_bin);
 if(b.length<2)fail('TRAIN_BIN');
 const my=avg(b.map(r=>r[y]));
 if(model==='bin_mean')return my;
 let num=0,den=0,meanX=0,meanY=0;
 if(model==='bin_plus_within_slope'){
  meanX=avg(b.map(r=>r[x]));
  for(const bin of new Set(train.map(r=>r.wind_bin))){
   const q=train.filter(r=>r.wind_bin===bin),bx=avg(q.map(r=>r[x])),by=avg(q.map(r=>r[y]));
   for(const r of q){num+=(r[x]-bx)*(r[y]-by);den+=(r[x]-bx)**2}
  }
  if(den<=1e-16)fail('ZERO_VARIANCE');
  return my+num/den*(test[x]-meanX);
 }
 meanX=avg(train.map(r=>r[x]));meanY=avg(train.map(r=>r[y]));
 for(const r of train){num+=(r[x]-meanX)*(r[y]-meanY);den+=(r[x]-meanX)**2}
 if(den<=1e-16)fail('ZERO_VARIANCE');
 return meanY+num/den*(test[x]-meanX);
}
function evaluate(rows){
 const out=[];
 for(const [channel,x,y] of SPECS){
  for(const holdout of ['case','seed_label']){
   for(const model of MODELS){
    const errs=[];
    for(const test of rows){
     const train=rows.filter(r=>holdout==='case'?r.case!==test.case:r.seed!==test.seed);
     if(train.length!==(holdout==='case'?17:15))fail('SPLIT');
     errs.push(predict(train,test,model,x,y)-test[y]);
    }
    out.push({channel,holdout,model,n_cases:18,n_folds:holdout==='case'?18:6,
      rmse:Math.sqrt(avg(errs.map(e=>e*e))),mae:avg(errs.map(Math.abs)),max_abs:Math.max(...errs.map(Math.abs))});
   }
  }
 }
 return out;
}
function summaryCSV(out){
 const lines=['channel,holdout,model,n_cases,n_folds,RMSE_MNm,MAE_MNm,max_abs_error_MNm,RMSE_ratio_to_bin_mean'];
 for(const r of out){
  const b=out.find(t=>t.channel===r.channel&&t.holdout===r.holdout&&t.model==='bin_mean');
  lines.push([r.channel,r.holdout,r.model,r.n_cases,r.n_folds,r.rmse.toFixed(9),r.mae.toFixed(9),r.max_abs.toFixed(9),(r.rmse/b.rmse).toFixed(9)].join(','));
 }
 return lines.join('\n')+'\n';
}
function svg(out){
 const W=1160,H=610,groups=[['My','case'],['My','seed_label'],['Mx','case'],['Mx','seed_label']];
 const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
 const a=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="610" viewBox="0 0 1160 610">',
 '<rect width="1160" height="610" fill="white"/>',
 '<text x="54" y="44" font-size="23" font-family="Arial" fill="#17243c" font-weight="bold">Held-out operating-state proxy error: 18 historical NTM cases</text>',
 '<text x="54" y="71" font-size="14" font-family="Arial" fill="#46546a">Lower RMSE is better. Every prediction excludes its test case or all three cases with the same seed label.</text>'];
 const colors=['#486a92','#d28a38','#3d9b8a'];
 for(let i=0;i<4;i++){
  const [ch,hold]=groups[i],x0=54+(i%2)*557,y0=105+Math.floor(i/2)*228,panel=out.filter(r=>r.channel===ch&&r.holdout===hold);
  const max=Math.max(...panel.map(r=>r.rmse))*1.25;
  a.push('<rect x="'+x0+'" y="'+y0+'" width="527" height="208" rx="7" fill="#f8fafc" stroke="#cbd5e1"/>');
  a.push('<text x="'+(x0+18)+'" y="'+(y0+27)+'" font-family="Arial" font-size="17" font-weight="bold" fill="#17243c">'+ch+' / '+(hold==='case'?'leave-one-case-out (18 folds)':'leave-one-seed-label-out (6 folds)')+'</text>');
  const baseY=y0+164,topY=y0+49,scale=110/max;
  a.push('<line x1="'+(x0+38)+'" y1="'+baseY+'" x2="'+(x0+500)+'" y2="'+baseY+'" stroke="#64748b"/>');
  panel.forEach((r,j)=>{const bx=x0+70+j*142,bh=r.rmse*scale;
   a.push('<rect x="'+bx+'" y="'+(baseY-bh).toFixed(2)+'" width="64" height="'+bh.toFixed(2)+'" fill="'+colors[j]+'" rx="3"/>');
   a.push('<text x="'+(bx+32)+'" y="'+(baseY-bh-7).toFixed(2)+'" text-anchor="middle" font-family="Arial" font-size="13" fill="#17243c">'+r.rmse.toFixed(3)+'</text>');
   a.push('<text x="'+(bx+32)+'" y="'+(baseY+19)+'" text-anchor="middle" font-family="Arial" font-size="12" fill="#334155">'+['Bin mean','Bin+slope','Pooled'][j]+'</text>');
  });
  a.push('<text x="'+(x0+17)+'" y="'+(y0+194)+'" font-family="Arial" font-size="12" fill="#64748b">RMSE (MN m); diagnostic load DEL, not material damage</text>');
 }
 a.push('<text x="54" y="584" font-family="Arial" font-size="13" fill="#475569">Source: archived 18 NTM cases (3 bins × 6 seeds); 100–700 s; no new simulation. Seed labels are reused across bins.</text>','</svg>');
 return a.join('\n')+'\n';
}
function selfTest(rows){
 const base=summaryCSV(evaluate(rows)),rev=summaryCSV(evaluate([...rows].reverse()));
 if(base!==rev)fail('ORDER_INVARIANCE');
 const s=rows.map(r=>HEADER.split(',').map(k=>r[k]).join(',')).join('\n');
 // Explicit invalid-data rejection is handled by parseCSV; verify the numerical gates independently.
 const v=evaluate(rows);
 const get=(ch,hold,m)=>v.find(r=>r.channel===ch&&r.holdout===hold&&r.model===m).rmse;
 if(Math.abs(get('My','case','bin_mean')-6.16015551126)>1e-8)fail('ORACLE_MY');
 if(Math.abs(get('Mx','seed_label','bin_plus_within_slope')-2.32013655708)>1e-8)fail('ORACLE_MX');
 if(!(get('My','seed_label','bin_plus_within_slope')>get('My','seed_label','bin_mean')))fail('EXPECTED_COMPARISON');
 return true;
}
if(typeof require!=='undefined'&&require.main===module){
 const fs=require('fs'),crypto=require('crypto');
 const [input,output,figure]=process.argv.slice(2);
 if(!input||!output||!figure)fail('ARGS');
 const bytes=fs.readFileSync(input);
 if(crypto.createHash('sha256').update(bytes).digest('hex')!==EXPECTED_SHA256)fail('INPUT_SHA256');
 const rows=parseCSV(bytes.toString('utf8'));selfTest(rows);const r=evaluate(rows);
 fs.writeFileSync(output,summaryCSV(r),'utf8');fs.writeFileSync(figure,svg(r),'utf8');
 console.log(JSON.stringify({source_sha256:EXPECTED_SHA256,summary_sha256:crypto.createHash('sha256').update(fs.readFileSync(output)).digest('hex'),figure_sha256:crypto.createHash('sha256').update(fs.readFileSync(figure)).digest('hex'),rows:r.length,pass:true}));
}
