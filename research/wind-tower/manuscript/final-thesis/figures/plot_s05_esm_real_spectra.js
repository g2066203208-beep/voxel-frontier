#!/usr/bin/env node
"use strict";
/** Reproducible S05 real ESM spectra figures. Node.js >=18, standard library only.
 * SOURCE: ESM v3 IT-2012-0008 / IT.NVL / MP, existing T079 CSV ledgers.
 * All plots are source-level numerical QC; NOT approved site spectra or 158m E/WE.
 */
const fs=require("node:fs"),crypto=require("node:crypto");
const EXPECTED_ROTD_SHA256="6f03869384193a4e00b27a11af6470ff3d11fcb73ebb08f0f19332b4edbe0205";
const EXPECTED_FIT_SHA256="704f8d9725b6a595c6ee8ba29358510a821e8e65701de58714d6c204021c9f5f";
const parseCSV=function parseCSV(s){const a=s.trim().split(/\r?\n/);const h=a.shift().split(",");return a.map(l=>Object.fromEntries(l.split(",").map((v,i)=>[h[i],v])));};
const render=function render(mode,rot,fit){
const check=(v,msg)=>{if(!v)throw Error(msg);};
check(rot.length===16 && fit.length===12,"ROW_COUNT_MISMATCH");
for(const rows of [rot,fit]){let prev=0;for(const r of rows){const t=+r.period_s;check(Number.isFinite(t)&&t>prev,"BAD_PERIOD_GRID");prev=t;}}
const P=[.5,.75,1,1.25,1.5,2,2.5,3,3.5,4,5,6,7,8,9,10];
check(rot.every((r,i)=>+r.period_s===P[i]),"ROTD_PERIOD_GRID");
check(fit.every((r,i)=>+r.period_s===P[i]),"FIT_PERIOD_GRID");
for(const r of rot){
 const vals=["HNE_psa_m_s2","HNN_psa_m_s2","RotD00_psa_m_s2","RotD50_psa_m_s2","RotD100_psa_m_s2"].map(k=>+r[k]);
 check(vals.every(x=>Number.isFinite(x)&&x>0),"INVALID_SPECTRUM_VALUE");
 check(vals[2]<=vals[3]+1e-12&&vals[3]<=vals[4]+1e-12,"INVALID_ROTD_ORDER");
}
let mismatch=0, sq=0;
for(let i=0;i<12;i++){
 const r=fit[i],src=rot[i],real=+r.real_ESM_RotD50_psa_m_s2,scaled=+r.scaled_real_psa_m_s2,target=+r.hypothetical_target_psa_m_s2,s=+r.fitted_uniform_scale,ratio=+r.scaled_over_target;
 check(Math.abs(real-(+src.RotD50_psa_m_s2))<1e-12,"FIT_REAL_SOURCE_DISAGREEMENT");
 check(Math.abs(scaled-real*s)<1e-12 && Math.abs(ratio-scaled/target)<1e-12,"FIT_ARITHMETIC_DISAGREEMENT");
 check(Number.isFinite(target)&&target>0,"BAD_TARGET");
 if(ratio<.7||ratio>1.3)mismatch++;sq+=Math.log(ratio)**2;
}
const rmse=Math.sqrt(sq/12),scale=+fit[0].fitted_uniform_scale;
check(mismatch===9 && Math.abs(rmse-0.5347074826605486)<1e-10 && Math.abs(scale-0.9803971950520918)<1e-12,"EXPECTED_FIT_SUMMARY_MISMATCH");
const W=1160,H=670,n=v=>Number(v).toFixed(2),log=Math.log;
const x0=108,x1=1085,y0=147,y1=505;
const X=t=>x0+(log(t)-log(.5))/(log(10)-log(.5))*(x1-x0);
const Y=(v,lo,hi)=>y1-(log(v)-log(lo))/(log(hi)-log(lo))*(y1-y0);
const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;");
const out=[`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${mode==="rotd"?"ESM measured processed spectral acceleration and RotD orientation statistics":"Real ESM RotD50 spectrum compared with hypothetical research reference spectrum, not site design"}">`,
`<rect width="${W}" height="${H}" fill="#fff"/>`,
`<text x="68" y="42" font-size="23" font-family="Arial,sans-serif" font-weight="700" fill="#172C42">${mode==="rotd"?"REAL ESM RECORD — ORIENTATION-DEPENDENT RESPONSE SPECTRA":"REAL ESM RotD50 vs HYPOTHETICAL RESEARCH SPECTRUM"}</text>`,
`<text x="68" y="69" font-size="14" font-family="Arial,sans-serif" fill="#4D6171">IT-2012-0008 / IT.NVL / MP processed record  |  5% damping  |  Δt = 0.005 s  |  32,040 samples</text>`,
`<text x="68" y="92" font-size="13" font-family="Arial,sans-serif" fill="#53687B">${mode==="rotd"?"Horizontal RotD00/50/100 computed from paired HNE/HNN; vertical excluded.":"Uniform log-LS fit: s = "+scale.toFixed(6)+"; 12 periods 0.5–6 s; RMS log residual = "+rmse.toFixed(6)+"."}</text>`,
`<line x1="68" y1="109" x2="1092" y2="109" stroke="#CCD4DC"/>`,
`<text x="${x0}" y="131" font-size="15" font-family="Arial,sans-serif" font-weight="600" fill="#2B4054">${mode==="rotd"?"Processed horizontal pseudo-spectral acceleration":"Pseudo-spectral acceleration: real record and assumed target"} (m/s²)</text>`];
const ymin=mode==="rotd"?.004:.015,ymax=mode==="rotd"?1:.8;
for(const y of mode==="rotd"?[.005,.01,.02,.05,.1,.2,.5,1]:[.02,.05,.1,.2,.5,.8]){
 const yy=Y(y,ymin,ymax);out.push(`<line x1="${x0}" x2="${x1}" y1="${n(yy)}" y2="${n(yy)}" stroke="#E5EBF0" stroke-width="1"/>`,`<text x="${x0-12}" y="${n(yy+4)}" text-anchor="end" font-size="12" font-family="Arial,sans-serif" fill="#44596B">${y}</text>`);
}
for(const t of [.5,.75,1,1.5,2,3,4,6,8,10]){
const xx=X(t);out.push(`<line x1="${n(xx)}" x2="${n(xx)}" y1="${y0}" y2="${y1}" stroke="#F0F2F5"/>`,`<text x="${n(xx)}" y="${y1+24}" text-anchor="middle" font-size="12" font-family="Arial,sans-serif" fill="#44596B">${t}</text>`);
}
out.push(`<line x1="${x0}" y1="${y0}" x2="${x0}" y2="${y1}" stroke="#718092" stroke-width="1.2"/>`,`<line x1="${x0}" y1="${y1}" x2="${x1}" y2="${y1}" stroke="#718092" stroke-width="1.2"/>`,`<text x="${n((x0+x1)/2)}" y="${y1+53}" text-anchor="middle" font-size="15" font-family="Arial,sans-serif" fill="#2A4053">Oscillator period T (s, logarithmic axis)</text>`);
const series=mode==="rotd"?[
["HNE","HNE_psa_m_s2","#687E96",1.7,"5 4"],["HNN","HNN_psa_m_s2","#B17A5B",1.7,"5 4"],["RotD00","RotD00_psa_m_s2","#8B68A8",2.5,""],["RotD50","RotD50_psa_m_s2","#186C92",3.4,""],["RotD100","RotD100_psa_m_s2","#268B72",2.5,""]]:[
["Real RotD50","real_ESM_RotD50_psa_m_s2","#6B879A",2,"5 4"],["Scaled real (s × RotD50)","scaled_real_psa_m_s2","#146D9B",3.4,""],["Hypothetical target","hypothetical_target_psa_m_s2","#B35B3E",3,""]];
const rows=mode==="rotd"?rot:fit;
for(const [label,key,color,width,dash] of series){
 const points=rows.map(r=>`${n(X(+r.period_s))},${n(Y(+r[key],ymin,ymax))}`).join(" ");
 out.push(`<polyline points="${points}" fill="none" stroke="${color}" stroke-width="${width}" ${dash?`stroke-dasharray="${dash}"`:""} stroke-linejoin="round" stroke-linecap="round"/>`);
 for(const r of rows)out.push(`<circle cx="${n(X(+r.period_s))}" cy="${n(Y(+r[key],ymin,ymax))}" r="${width>3?3.4:2.4}" fill="#fff" stroke="${color}" stroke-width="1.4"/>`);
}
let legendY=578,legendX=mode==="rotd"?86:108,step=mode==="rotd"?190:300;
series.forEach(([label,key,color,width,dash],i)=>{let xx=legendX+i*step;out.push(`<line x1="${xx}" x2="${xx+34}" y1="${legendY}" y2="${legendY}" stroke="${color}" stroke-width="${width}" ${dash?`stroke-dasharray="${dash}"`:""}/><text x="${xx+42}" y="${legendY+5}" font-size="13.5" font-family="Arial,sans-serif" fill="#34495A">${esc(label)}</text>`);});
out.push(`<line x1="68" x2="1092" y1="604" y2="604" stroke="#D4DCE4"/>`,
`<text x="68" y="627" font-size="12" font-family="Arial,sans-serif" fill="#506477">SOURCE: ESM v3 / IT-2012-0008 / IT.NVL / MP; CSV data archived in T079/real-records; plotted without smoothing.</text>`,
`<text x="68" y="648" font-size="12" font-family="Arial,sans-serif" font-weight="600" fill="#A24634">${mode==="rotd"?"SOURCE-QC ONLY: long-period instrument usability and official site target NOT verified; not 158 m E/WE response.":`HYPOTHETICAL TARGET ONLY: ${mismatch}/12 periods outside ±30% ILLUSTRATIVE guide; NOT a code tolerance or Jiayu design spectrum.`}</text>`,`</svg>\n`);
return {svg:out.join("\n"),meta:{mode,periods:rows.length,scale,rmse,mismatch,rot_min:+rot[15].RotD50_psa_m_s2,rot_max:+rot[0].RotD50_psa_m_s2}};
};
function main(){
const args=process.argv.slice(2);
if(args.length!==4)throw Error("usage: node plot_s05_esm_real_spectra.js RotD16.csv HypotheticalFit12.csv RotD.svg Fit.svg");
const [rotPath,fitPath,outA,outB]=args;
const r=fs.readFileSync(rotPath),f=fs.readFileSync(fitPath);
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
if(sha(r)!==EXPECTED_ROTD_SHA256)throw Error("ROTD_SOURCE_SHA256_MISMATCH");
if(sha(f)!==EXPECTED_FIT_SHA256)throw Error("FIT_SOURCE_SHA256_MISMATCH");
const rot=parseCSV(r.toString("utf8")),fit=parseCSV(f.toString("utf8"));
const a=render("rotd",rot,fit),b=render("fit",rot,fit);
fs.writeFileSync(outA,a.svg,"utf8");fs.writeFileSync(outB,b.svg,"utf8");
console.log("S05_REAL_ESM_FIGURES_NUMERICAL_QC_PASS",JSON.stringify({rot_sha:sha(r),fit_sha:sha(f),fig_rot_sha:sha(a.svg),fig_fit_sha:sha(b.svg),...b.meta,native_E_WE_runs:0,site_spectrum_pass:false}));
}
if(require.main===module)main();
