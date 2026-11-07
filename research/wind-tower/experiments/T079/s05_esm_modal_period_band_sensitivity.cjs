"use strict";
// S05 sampled-period sensitivity of processed REAL ESM data. NOT site hazard or structural response.
const SOURCE_SHA256="31fea6aa2064abbd042e4a1b1a15b9aee90a598a7d1991bc0869bcd63177dd8c";
const T1=6.230957762865167;
const H="period_s,frequency_Hz,HNE_psa_m_s2,HNN_psa_m_s2,RotD00_psa_m_s2,RotD50_psa_m_s2,RotD100_psa_m_s2,RotD50_1deg_vs_halfdeg_relative,RotD100_1deg_vs_halfdeg_relative,f_over_processing_0p04Hz,f_over_official_snr_reported_0p09Hz,is_conditional_beam_T1,is_legacy_16period_overlap,status".split(",");
function need(ok,code){if(!ok)throw Error(code)}
function parse(src){
 const lines=src.trim().split(/\r?\n/);need(lines.length===47,"46_ROWS");need(lines[0]===H.join(","),"HEADER");
 let previous=0,nom=0,overlap=0;const rows=[];
 for(const line of lines.slice(1)){
  const v=line.split(",");need(v.length===14,"COLS");const r=Object.fromEntries(H.map((h,i)=>[h,v[i]]));
  for(const k of H.slice(0,11)){need(r[k]!==""&&Number.isFinite(+r[k]),"FINITE");r[k]=+r[k]}
  need(r.period_s>previous,"PERIOD_ORDER");previous=r.period_s;
  need(Math.abs(r.frequency_Hz*r.period_s-1)<1e-10,"FREQUENCY");
  need(r.HNE_psa_m_s2>0&&r.HNN_psa_m_s2>0&&r.RotD00_psa_m_s2>0,"POSITIVE");
  need(r.RotD00_psa_m_s2<=r.RotD50_psa_m_s2&&r.RotD50_psa_m_s2<=r.RotD100_psa_m_s2,"ROTD_ORDER");
  need(r.RotD50_1deg_vs_halfdeg_relative>=0&&r.RotD50_1deg_vs_halfdeg_relative<.01&&r.RotD100_1deg_vs_halfdeg_relative>=0&&r.RotD100_1deg_vs_halfdeg_relative<.01,"ANGLE");
  need(Math.abs(r.f_over_processing_0p04Hz-25/r.period_s)<1e-8,"PROCESSING_BAND");
  need(Math.abs(r.f_over_official_snr_reported_0p09Hz-1/(.09*r.period_s))<1e-8,"SNR_BAND");
  need(["True","False"].includes(r.is_conditional_beam_T1)&&["True","False"].includes(r.is_legacy_16period_overlap),"FLAG");
  need(r.status==="REAL_ESM_NUMERIC_SPECTRUM_ONLY_NOT_SITE_DESIGN_OR_ABAQUS","SOURCE_STATUS");
  if(r.is_conditional_beam_T1==="True"){need(Math.abs(r.period_s-T1)<1e-10,"T1_FLAG");nom++}
  if(r.is_legacy_16period_overlap==="True")overlap++;
  rows.push(r);
 }
 need(nom===1&&overlap===12,"ANCHOR_COUNTS");return rows;
}
function analyze(rows){
 const band=rows.filter(r=>r.period_s>=T1*.9&&r.period_s<=T1*1.1);
 need(band.length===6,"BAND_COUNT");
 const at=band.find(r=>Math.abs(r.period_s-T1)<1e-10);need(!!at,"NOMINAL");
 const v=band.map(r=>r.RotD50_psa_m_s2),min=Math.min(...v),max=Math.max(...v),ref=at.RotD50_psa_m_s2;
 need(band.some(r=>r.HNE_psa_m_s2<r.HNN_psa_m_s2)&&band.some(r=>r.HNE_psa_m_s2>r.HNN_psa_m_s2),"AXIS_SWITCH");
 return {band,min,max,ref,at,up:100*(max/ref-1),down:100*(min/ref-1),spread:100*(max/min-1),
  rotMin:Math.min(...band.map(r=>r.RotD100_psa_m_s2/r.RotD50_psa_m_s2)),
  rotMax:Math.max(...band.map(r=>r.RotD100_psa_m_s2/r.RotD50_psa_m_s2)),
  angleMax:Math.max(...band.flatMap(r=>[r.RotD50_1deg_vs_halfdeg_relative,r.RotD100_1deg_vs_halfdeg_relative]))};
}
function csv(z){
 const head="period_s,frequency_Hz,HNE_PSA_m_s2,HNN_PSA_m_s2,RotD50_PSA_m_s2,RotD100_PSA_m_s2,RotD100_over_RotD50,HNE_over_HNN,RotD50_vs_T1_percent,f_over_reported_0p09Hz";
 return head+"\n"+z.band.map(r=>[r.period_s,r.frequency_Hz,r.HNE_psa_m_s2,r.HNN_psa_m_s2,r.RotD50_psa_m_s2,r.RotD100_psa_m_s2,r.RotD100_psa_m_s2/r.RotD50_psa_m_s2,r.HNE_psa_m_s2/r.HNN_psa_m_s2,100*(r.RotD50_psa_m_s2/z.ref-1),r.f_over_official_snr_reported_0p09Hz].map(n=>n.toPrecision(13)).join(",")).join("\n")+"\n";
}
function svg(z){
 const x0=125,y0=135,w=810,h=385,lo=T1*.9,hi=T1*1.1;
 const X=t=>x0+(t-lo)/(hi-lo)*w,Y=a=>y0+h-(a-.01)/.027*h;
 const series=[["HNE","HNE_psa_m_s2","#386CB0"],["HNN","HNN_psa_m_s2","#2E8B73"],["RotD50","RotD50_psa_m_s2","#BE593F"],["RotD100","RotD100_psa_m_s2","#713DA6"]];
 const out=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="660" viewBox="0 0 1080 660" role="img" aria-labelledby="title desc">','<title id="title">Conditional period-band directional sensitivity of real processed ESM record</title>','<desc id="desc">Six sampled periods, 5% damping, plus or minus 10% around provisional beam T1; not site hazard, design spectrum, continuous envelope or structural response.</desc>','<rect width="1080" height="660" fill="white"/>','<text x="70" y="45" font-family="Arial,sans-serif" font-size="24" font-weight="bold">Conditional period-band sensitivity of real ESM spectra</text>','<text x="70" y="76" font-family="Arial,sans-serif" font-size="15">IT-2012-0008 · IT.NVL · processed HNE/HNN · 5% damping · unscaled PSA</text>','<rect x="'+x0+'" y="'+y0+'" width="'+w+'" height="'+h+'" fill="#FAFCFE" stroke="#B6C2CA"/>'];
 for(let v=.01;v<.038;v+=.005){let y=Y(v);out.push('<line x1="'+x0+'" y1="'+y.toFixed(2)+'" x2="'+(x0+w)+'" y2="'+y.toFixed(2)+'" stroke="#E3E9EF"/><text x="'+(x0-13)+'" y="'+(y+5).toFixed(2)+'" text-anchor="end" font-family="Arial,sans-serif" font-size="13">'+v.toFixed(3)+'</text>')}
 for(const r of z.band){let x=X(r.period_s);out.push('<line x1="'+x.toFixed(2)+'" y1="'+y0+'" x2="'+x.toFixed(2)+'" y2="'+(y0+h)+'" stroke="#EDF0F3"/><text x="'+x.toFixed(2)+'" y="'+(y0+h+24)+'" text-anchor="middle" font-family="Arial,sans-serif" font-size="12">'+r.period_s.toFixed(3)+'</text>')}
 out.push('<line x1="'+X(T1).toFixed(2)+'" y1="'+y0+'" x2="'+X(T1).toFixed(2)+'" y2="'+(y0+h)+'" stroke="#596875" stroke-width="2" stroke-dasharray="5 5"/>');
 for(const [name,key,color] of series){out.push('<polyline fill="none" stroke="'+color+'" stroke-width="2.6" points="'+z.band.map(r=>X(r.period_s).toFixed(2)+","+Y(r[key]).toFixed(2)).join(" ")+'"/>');for(const r of z.band)out.push('<circle cx="'+X(r.period_s).toFixed(2)+'" cy="'+Y(r[key]).toFixed(2)+'" r="4" fill="'+color+'"><title>'+name+' T='+r.period_s.toFixed(6)+'s PSA='+r[key].toPrecision(8)+'m/s2</title></circle>')}
 series.forEach(([name,k,color],i)=>{let x=125+i*190;out.push('<line x1="'+x+'" y1="107" x2="'+(x+30)+'" y2="107" stroke="'+color+'" stroke-width="4"/><text x="'+(x+36)+'" y="112" font-family="Arial,sans-serif" font-size="14">'+name+'</text>')});
 out.push('<text x="530" y="583" text-anchor="middle" font-family="Arial,sans-serif" font-size="16">Oscillator period T (s) — sampled ±10% provisional T1 band</text>');
 out.push('<text x="36" y="330" transform="rotate(-90 36 330)" text-anchor="middle" font-family="Arial,sans-serif" font-size="16">Pseudo spectral acceleration (m/s²)</text>');
 out.push('<text x="70" y="618" font-family="Arial,sans-serif" font-size="14">Sampled RotD50 '+z.min.toFixed(6)+'–'+z.max.toFixed(6)+' m/s²; nominal '+z.ref.toFixed(6)+'; HNE/HNN dominance changes.</text>');
 out.push('<text x="70" y="643" font-family="Arial,sans-serif" font-size="12" fill="#76545B">Not a continuous-period bound; long-period SNR, site hazard and physical T1 remain unverified.</text></svg>');
 return out.join("\n")+"\n";
}
function selfTest(src){
 const z=analyze(parse(src)),eq=(a,b)=>Math.abs(a-b)<1e-11;
 need(eq(z.ref,.02641699587560876),"T1_ORACLE");
 need(eq(z.min,.023344907612266555),"MIN_ORACLE");
 need(eq(z.max,.030581918192687033),"MAX_ORACLE");
 need(eq(z.at.RotD100_psa_m_s2,.030612978353458383),"ROTD100_ORACLE");
 need(z.up>15&&z.down< -11&&z.band.length===6,"BAND_ORACLE");
 need(z.rotMax>z.rotMin&&z.rotMin>1,"DIRECTION_ORACLE");
 const bad=[
 src.replace("period_s,frequency_Hz","period_bad,frequency_Hz"),
 src.trim().split(/\r?\n/).slice(0,-1).join("\n"),
 src.replace("0.802444855235363","NaN"),
 src.replace("0.802444855235363","9.802444855235363"),
 src.replace("0.11342276417950979","0.99942276417950979"),
 src.replace("0.0013887863035274572","0.9993887863035275"),
 src.replace("20.061121380884074","100.06112138088407"),
 src.replace("REAL_ESM_NUMERIC_SPECTRUM_ONLY_NOT_SITE_DESIGN_OR_ABAQUS","SITE_DESIGN_APPROVED"),
 src.replace(",True,False,REAL_ESM",",False,False,REAL_ESM"),
 src.replace("0.24311493933969297","-0.24311493933969297")];
 let rejected=0;for(const b of bad){try{analyze(parse(b))}catch(e){rejected++}}
 need(rejected===bad.length,"NEGATIVE_"+rejected);return {z,positive:6,negative:rejected,csv:csv(z),svg:svg(z)};
}
if(typeof module!=="undefined")module.exports={parse,analyze,csv,svg,selfTest};
if(typeof require!=="undefined"&&require.main===module){
 const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
 const input=process.argv[2]||path.join(__dirname,"real-records","S05_ESM_IT2012_NVL_DENSE_LONGPERIOD_ROTD_20261102.csv");
 const bytes=fs.readFileSync(input);need(crypto.createHash("sha256").update(bytes).digest("hex")===SOURCE_SHA256,"SOURCE_SHA256");
 const r=selfTest(bytes.toString("utf8")),dir=process.argv[3]||__dirname;
 fs.writeFileSync(path.join(dir,"S05_ESM_NVL_T1_PM10_PERCENT_SPECTRAL_BAND_20261107.csv"),r.csv);
 fs.writeFileSync(path.join(dir,"FIG_S05_03_ESM_T1_BAND_DIRECTIONAL_SENSITIVITY_20261107.svg"),r.svg);
 console.log(JSON.stringify({positive:r.positive,negative:r.negative,points:r.z.band.length,min:r.z.min,max:r.z.max,up_pct:r.z.up,down_pct:r.z.down,axis_switch:true}));
}