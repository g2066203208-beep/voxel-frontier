'use strict';
// S05: historical real ESM pseudo-spectrum only; no structural solver.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const INPUT=path.join(__dirname,'real-records/S05_ESM_IT2012_NVL_DENSE_LONGPERIOD_ROTD_20261102.csv');
const OUTPUT=path.join(__dirname,'real-records/S05_ESM_NVL_PSA_PSD_46PERIOD_20261107.csv');
const FIG=path.join(__dirname,'../../manuscript/final-thesis/figures/FIG_S05_05_ESM_PSA_PSD_PERIOD_GATE_20261107.svg');
const HASH='31fea6aa2064abbd042e4a1b1a15b9aee90a598a7d1991bc0869bcd63177dd8c';
function calc(raw){
 const lines=raw.trim().split(/\r?\n/),keys=lines.shift().split(",");
 const need=["period_s","frequency_Hz","HNE_psa_m_s2","HNN_psa_m_s2","RotD00_psa_m_s2","RotD50_psa_m_s2","RotD100_psa_m_s2","f_over_official_snr_reported_0p09Hz","is_conditional_beam_T1","status"];
 if(lines.length!==46||need.some(k=>!keys.includes(k)))throw Error("COUNT_SCHEMA");
 let prev=0,t1count=0;
 const rows=lines.map(line=>{
  const v=line.split(",");if(v.length!==keys.length)throw Error("COLUMN_COUNT");const o=Object.fromEntries(keys.map((k,i)=>[k,v[i]]));
  const T=+o.period_s,f=+o.frequency_Hz,h=+o.HNE_psa_m_s2,n=+o.HNN_psa_m_s2,a=+o.RotD00_psa_m_s2,b=+o.RotD50_psa_m_s2,c=+o.RotD100_psa_m_s2,margin=+o.f_over_official_snr_reported_0p09Hz;
  if(![T,f,h,n,a,b,c,margin].every(Number.isFinite)||T<=prev||Math.abs(f*T-1)>1e-10||Math.abs(margin-f/.09)>1e-9)throw Error("PERIOD_FREQ");
  if(Math.min(h,n,a,b,c)<=0||a>b+1e-12||b>c+1e-12||c<Math.max(h,n)-1e-12)throw Error("ROTD_ORDER");
  if(o.status!=="REAL_ESM_NUMERIC_SPECTRUM_ONLY_NOT_SITE_DESIGN_OR_ABAQUS")throw Error("STATUS");
  if(o.is_conditional_beam_T1==="True")t1count++;else if(o.is_conditional_beam_T1!=="False")throw Error("T1_FLAG");
  prev=T;const w=2*Math.PI/T;
  return {T,f,psa50:b,psa100:c,psv50:b/w,psd50:b/(w*w),psd100:c/(w*w),psdHNE:h/(w*w),psdHNN:n/(w*w),margin,center:o.is_conditional_beam_T1==="True"};
 });
 if(t1count!==1)throw Error("T1_COUNT");
 const center=rows.find(r=>r.center),long=rows.filter(r=>r.T>=4&&r.T<=10),near=rows.filter(r=>r.T>=center.T*.9&&r.T<=center.T*1.1);
 if(long.length!==21||near.length!==6)throw Error("BAND_COUNT");
 const peak=(arr,key)=>arr.reduce((a,b)=>a[key]>b[key]?a:b);
 const p=peak(long,"psa50"),d=peak(long,"psd50"),np=peak(near,"psa50"),nd=peak(near,"psd50");
 return {rows,summary:{center,p,d,np,nd,ratio:d.psd50/p.psd50,nearGain:100*(nd.psd50/center.psd50-1),slope:Math.log(d.psa50/p.psa50)/Math.log(d.T/p.T)}};
}
function csvOut(data){
 const keys=["period_s","frequency_Hz","RotD50_PSA_m_s2","RotD100_PSA_m_s2","RotD50_PSV_m_s","RotD50_PSD_m","RotD100_PSD_m","HNE_PSD_m","HNN_PSD_m","f_over_reported_SNR_0p09Hz","in_4_to_10_s","in_conditional_T1_pm10pct","status"];
 const fmt=x=>Number(x).toPrecision(13),t1=data.summary.center.T;
 return keys.join(",")+"\n"+data.rows.map(r=>[fmt(r.T),fmt(r.f),fmt(r.psa50),fmt(r.psa100),fmt(r.psv50),fmt(r.psd50),fmt(r.psd100),fmt(r.psdHNE),fmt(r.psdHNN),fmt(r.margin),+(r.T>=4&&r.T<=10),+(r.T>=t1*.9&&r.T<=t1*1.1),"REAL_ESM_DERIVED_SDOF_PSEUDO_SPECTRUM_NOT_TOWER_RESPONSE"].join(",")).join("\n")+"\n";
}
function svgOut(data){
 const s=data.summary,rs=data.rows,x0=85,x1=1150,x=t=>x0+(t-1.2)/(9.5-1.2)*(x1-x0);
 let a=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="690" viewBox="0 0 1200 690">','<rect width="1200" height="690" fill="white"/>','<text x="85" y="40" font-size="23" font-family="Arial,Noto Sans CJK SC" fill="#203445" font-weight="bold">Real ESM NVL: acceleration versus displacement spectral peaks</text>','<text x="85" y="66" font-size="14" font-family="Arial" fill="#536878">IT-2012-0008 · processed HNE/HNN · 5% damping · 46 sampled periods · NOT a design spectrum</text>'];
 for(const q of [{top:107,bottom:283,max:.32,key:"psa",title:"(a) Pseudo-spectral acceleration / 伪加速度",unit:"m/s²",scale:1},{top:348,bottom:526,max:35,key:"psd",title:"(b) Pseudo-spectral displacement / 伪位移",unit:"mm",scale:1000}]){
  const y=v=>q.bottom-v/q.max*(q.bottom-q.top),key50=q.key==="psa"?"psa50":"psd50",key100=q.key==="psa"?"psa100":"psd100",p=q.key==="psa"?s.p:s.d;
  a.push(`<rect x="${x(s.center.T*.9).toFixed(2)}" y="${q.top}" width="${(x(s.center.T*1.1)-x(s.center.T*.9)).toFixed(2)}" height="${q.bottom-q.top}" fill="#e8f2f7"/>`);
  for(let i=0;i<=4;i++){const v=i*q.max/4;a.push(`<line x1="${x0}" x2="${x1}" y1="${y(v).toFixed(2)}" y2="${y(v).toFixed(2)}" stroke="#dce5e9"/><text x="73" y="${(y(v)+4).toFixed(2)}" text-anchor="end" font-family="Arial" font-size="12" fill="#526575">${v.toFixed(q.key==="psa"?2:0)}</text>`)}
  a.push(`<line x1="${x0}" y1="${q.top}" x2="${x0}" y2="${q.bottom}" stroke="#637584"/><line x1="${x0}" y1="${q.bottom}" x2="${x1}" y2="${q.bottom}" stroke="#637584"/>`);
  a.push(`<line x1="${x(s.center.T).toFixed(2)}" x2="${x(s.center.T).toFixed(2)}" y1="${q.top}" y2="${q.bottom}" stroke="#758896" stroke-dasharray="5,5"/>`);
  for(const [key,color] of [[key100,"#b17650"],[key50,"#116783"]])a.push(`<polyline points="${rs.map(r=>`${x(r.T).toFixed(2)},${y(r[key]*q.scale).toFixed(2)}`).join(" ")}" fill="none" stroke="${color}" stroke-width="${key===key50?2.8:2}"/>`);
  a.push(`<circle cx="${x(p.T).toFixed(2)}" cy="${y(p[key50]*q.scale).toFixed(2)}" r="5" fill="#116783" stroke="white" stroke-width="2"/>`);
  a.push(`<text x="85" y="${q.top-13}" font-family="Arial,Noto Sans CJK SC" font-size="16" font-weight="bold" fill="#203445">${q.title} (${q.unit})</text>`);
 }
 for(let t=2;t<=9;t++)a.push(`<text x="${x(t).toFixed(2)}" y="546" font-family="Arial" font-size="12" text-anchor="middle" fill="#526575">${t}</text>`);
 a.push('<text x="620" y="570" text-anchor="middle" font-family="Arial" font-size="14" fill="#203445">Oscillator period T (s)</text>');
 a.push('<line x1="85" x2="117" y1="597" y2="597" stroke="#116783" stroke-width="3"/><text x="125" y="602" font-family="Arial" font-size="13">RotD50</text>');
 a.push('<line x1="236" x2="268" y1="597" y2="597" stroke="#b17650" stroke-width="3"/><text x="276" y="602" font-family="Arial" font-size="13">RotD100</text>');
 a.push('<rect x="391" y="588" width="18" height="18" fill="#e8f2f7"/><text x="418" y="602" font-family="Arial" font-size="13">conditional T1 ±10% (not a measured modal uncertainty)</text>');
 a.push(`<text x="85" y="638" font-family="Arial" font-size="12" fill="#526575">4–10 s sampled peaks: PSA50 at ${s.p.T.toFixed(3)} s; PSD50 at ${s.d.T.toFixed(3)} s, ${(s.d.psd50*1000).toFixed(3)} mm versus ${(s.p.psd50*1000).toFixed(3)} mm at PSA peak.</text>`);
 a.push('<text x="85" y="659" font-family="Arial" font-size="12" fill="#526575">ESM reported 0.09 Hz SNR lower bound is not an acceptance cutoff. Low-frequency reliability and site target remain HOLD.</text>','</svg>');
 return a.join("\n")+"\n";
}
function main(){const raw=fs.readFileSync(INPUT,'utf8'),h=crypto.createHash('sha256').update(raw).digest('hex');if(h!==HASH)throw Error('SOURCE_SHA256');const d=calc(raw),s=d.summary;if(Math.abs(s.p.psa50-.040060288158533255)>1e-13||Math.abs(s.d.psd50-.027521234500971038)>1e-13)throw Error('NUMERIC_ORACLE');const bad=[raw.replace('0.802444855235363','0.72'),raw.replace('0.21338108047846494','-0.21338108047846494'),raw.replace('0.21338108047846494','NaN'),raw.replace('1.3271819529294313','1.25'),raw.replace('1.783210789411918,True,False','1.783210789411918,False,False'),raw.replace('REAL_ESM_NUMERIC_SPECTRUM_ONLY_NOT_SITE_DESIGN_OR_ABAQUS','BAD_STATUS'),raw.trim().split(String.fromCharCode(10)).slice(0,-1).join(String.fromCharCode(10))];let rejects=0;for(const v of bad){try{calc(v)}catch(e){rejects++}}if(rejects!==7)throw Error('REJECTION_TESTS:'+rejects);const csv=csvOut(d),svg=svgOut(d);if(process.argv.includes('--write')){fs.writeFileSync(OUTPUT,csv);fs.writeFileSync(FIG,svg)}console.log(JSON.stringify({input_sha256:h,program_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),csv_sha256:crypto.createHash('sha256').update(csv).digest('hex'),svg_sha256:crypto.createHash('sha256').update(svg).digest('hex'),peak_psa_period:s.p.T,peak_psd_period:s.d.T,psd_ratio:s.ratio,negative_tests:rejects},null,2));}
if(require.main===module)main();
