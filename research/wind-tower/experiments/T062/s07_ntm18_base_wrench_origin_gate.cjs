"use strict";
/* S07: conservative same-frame tower-base wrench origin-shift bound.
 * Real data: S06 18NTM original OUTB-derived synchronous extrema, source SHA-locked.
 * This is a response-transport sensitivity, NOT external loading, force decomposition,
 * B/W/E/WE pairing, material fatigue, or a structural acceptance calculation.
 */
const SOURCE_SHA256="ec1d5153635547c0ea24dba6ac62f65325dc50716b61e4c5c767ba489ec7444c";
const HEADER="case,outb_sha256,xy_peak_kNm,xy_independent_kNm,xy_ratio,xy_peak_time_s,xyz_force_peak_kN,xyz_force_independent_kN,xyz_force_ratio,xyz_peak_time_s,xy_quantization_bound_kNm,xyz_quantization_bound_kN";
const OUT_HEADER="case,outb_sha256,mxy_peak_kNm,force_peak_kN,characteristic_length_m,origin_1pct_guarantee_m,origin_5pct_guarantee_m,origin_0p1m_worst_pct,peak_time_separation_s";
function ck(ok,why){if(!ok)throw Error(why);}
function num(x){ck(/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(x),"NON_NUMERIC");let y=Number(x);ck(Number.isFinite(y),"NONFINITE");return y;}
function calc(r){
 const m=r.xy_peak_kNm,f=r.xyz_force_peak_kN,qm=r.xy_quantization_bound_kNm,qf=r.xyz_quantization_bound_kN;
 ck([m,f,qm,qf,r.xy_peak_time_s,r.xyz_peak_time_s].every(Number.isFinite),"CALC_NONFINITE");
 ck(m>qm&&f>0&&qm>=0&&qf>=0,"INVALID_BOUNDS");
 const lowM=m-qm,highF=f+qf;
 const d1=.01*lowM/highF,d5=.05*lowM/highF;
 ck(d1*highF<=.01*lowM*(1+1e-12),"BOUND_IDENTITY");
 return {length_m:m/f,origin_1pct_m:d1,origin_5pct_m:d5,origin_0p1m_pct:10*highF/lowM,lag_s:Math.abs(r.xy_peak_time_s-r.xyz_peak_time_s)};
}
function parse(s){
 ck(typeof s==="string"&&s.endsWith("\n")&&!s.includes("\r"),"CSV_LINE_ENDING");
 const lines=s.slice(0,-1).split("\n");
 ck(lines.length===19&&lines[0]===HEADER,"CSV_SHAPE");
 const keys=HEADER.split(","),cases=new Set(),out=[];
 for(const line of lines.slice(1)){
   const v=line.split(",");ck(v.length===keys.length,"CSV_WIDTH");
   const r=Object.fromEntries(keys.map((k,i)=>[k,k==="case"||k==="outb_sha256"?v[i]:num(v[i])]));
   ck(/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(r.case),"CASE_ID");
   ck(!cases.has(r.case),"DUPLICATE_CASE");cases.add(r.case);
   ck(/^[a-f0-9]{64}$/.test(r.outb_sha256),"OUTB_SHA");
   ck(r.xy_peak_kNm>0&&r.xy_independent_kNm>=r.xy_peak_kNm-1e-5&&r.xy_ratio>0&&r.xy_ratio<=1&&Math.abs(r.xy_ratio-r.xy_peak_kNm/r.xy_independent_kNm)<2e-9,"MOMENT_ENVELOPE");
   ck(r.xyz_force_peak_kN>0&&r.xyz_force_independent_kN>=r.xyz_force_peak_kN-1e-5&&r.xyz_force_ratio>0&&r.xyz_force_ratio<=1&&Math.abs(r.xyz_force_ratio-r.xyz_force_peak_kN/r.xyz_force_independent_kN)<2e-9,"FORCE_ENVELOPE");
   for(const t of [r.xy_peak_time_s,r.xyz_peak_time_s])
     ck(t>=100&&t<=700&&Math.abs((t-100)/.05-Math.round((t-100)/.05))<1e-6,"TIME_GRID");
   const z=calc(r);out.push({...r,...z});
 }
 ck(cases.size===18,"CASE_COUNT");
 for(const b of ["U09p343881","U11p4","U19p202140"])
   for(let i=1;i<=6;i++)ck(cases.has(b+"_NTM_S0"+i),"MISSING_SEED");
 return out;
}
function table(rows){
 return OUT_HEADER+"\n"+rows.map(r=>[
 r.case,r.outb_sha256,r.xy_peak_kNm.toFixed(6),r.xyz_force_peak_kN.toFixed(7),
 r.length_m.toFixed(9),r.origin_1pct_m.toFixed(9),r.origin_5pct_m.toFixed(9),
 r.origin_0p1m_pct.toFixed(9),r.lag_s.toFixed(2)].join(",")).join("\n")+"\n";
}
function svg(rows){
 const W=980,H=445,x=i=>90+i*45,y=cm=>345-(cm-7.5)*47;
 let a=['<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">',
 '<rect width="980" height="445" fill="#ffffff"/>',
 '<text x="90" y="32" font-family="Arial,sans-serif" font-size="19" font-weight="bold" fill="#20252b">Tower-base moment-origin sensitivity | 18 original NTM cases</text>',
 '<text x="90" y="55" font-family="Arial,sans-serif" font-size="12" fill="#59616a">Maximum unverified origin offset guaranteeing &lt;1% change in peak horizontal moment (same frame, conservative)</text>'];
 for(let cm=8;cm<=12;cm++){
  a.push('<line x1="90" y1="'+y(cm)+'" x2="870" y2="'+y(cm)+'" stroke="#e1e5e8"/>');
  a.push('<text x="56" y="'+(y(cm)+4)+'" font-family="Arial" font-size="12" fill="#3d4955">'+cm+' cm</text>');
 }
 a.push('<line x1="90" y1="110" x2="90" y2="345" stroke="#333c45"/>');
 a.push('<line x1="90" y1="345" x2="870" y2="345" stroke="#333c45"/>');
 a.push('<line x1="90" y1="'+y(10)+'" x2="870" y2="'+y(10)+'" stroke="#a64d39" stroke-dasharray="7,5" stroke-width="1.6"/>');
 a.push('<text x="878" y="'+(y(10)+4)+'" font-family="Arial" font-size="11" fill="#a64d39">10 cm</text>');
 for(let i=0;i<rows.length;i++){
   let cx=x(i),cy=y(rows[i].origin_1pct_m*100);
   a.push('<circle cx="'+cx+'" cy="'+cy.toFixed(2)+'" r="5.3" fill="#226c8a"/>');
   a.push('<text x="'+cx+'" y="366" text-anchor="middle" font-family="Arial" font-size="10" fill="#414c55">S0'+(i%6+1)+'</text>');
 }
 for(let g=0;g<3;g++){
   let center=x(g*6+2.5);
   a.push('<text x="'+center+'" y="391" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#27313b">'+["9.343881 m/s","11.4 m/s","19.202140 m/s"][g]+'</text>');
   if(g<2)a.push('<line x1="'+(x(g*6+5)+23)+'" y1="100" x2="'+(x(g*6+5)+23)+'" y2="345" stroke="#c1c8cf" stroke-dasharray="3,4"/>');
 }
 a.push('<text x="90" y="424" font-family="Arial" font-size="11" fill="#5a626c">SOURCE: 18 original OUTB-derived maxima; includes int16 half-step error bounds. Not an actual frame error or applied load.</text></svg>\n');
 return a.join("\n");
}
function selftest(real){
 let r={xy_peak_kNm:100,xyz_force_peak_kN:10,xy_quantization_bound_kNm:0,xyz_quantization_bound_kN:0,xy_peak_time_s:100,xyz_peak_time_s:105};
 let a=calc(r);ck(Math.abs(a.origin_1pct_m-.1)<1e-14&&Math.abs(a.origin_0p1m_pct-1)<1e-14&&a.lag_s===5,"ANALYTIC");
 r.xy_quantization_bound_kNm=2;r.xyz_quantization_bound_kN=1;
 a=calc(r);ck(Math.abs(a.origin_1pct_m-.01*98/11)<1e-14,"QUANTIZATION");
 let rejects=0;const lines=real.trimEnd().split("\n");
 const bad=[
  "",real.replace("case,outb_sha256","case,case"),
  lines.slice(0,-1).join("\n")+"\n",
  [lines[0],lines[1],lines[1],...lines.slice(3)].join("\n")+"\n",
  real.replace(/f2d5d236038f67f5/,"BAD_SHA"),
  real.replace("288494.847317","NaN"),
  real.replace("1.82186347906","-1"),
  real.replace("0.998951731049","1.5"),
  real.replace("207.55","207.551"),
  real.replace("25800.4429627","0"),
  real.replace("U09p343881_NTM_S01","U99p999999_NTM_S01"),
  real.replace("\n","\r\n")
 ];
 for(const s of bad){try{parse(s);}catch(_){rejects++;continue;}throw Error("BAD_ACCEPTED");}
 ck(rejects===bad.length,"REJECTION_COUNT");
 const rows=parse(real),out=table(rows);
 ck(rows.length===18&&out.split("\n").length===20,"REAL_ROWS");
 ck(rows.every(x=>x.origin_1pct_m>0&&x.origin_1pct_m<x.origin_5pct_m),"REAL_BOUNDS");
 return {positive:2,negative:rejects,cases:rows.length,
  min_d1_m:Math.min(...rows.map(x=>x.origin_1pct_m)),
  max_d1_m:Math.max(...rows.map(x=>x.origin_1pct_m)),
  min_length_m:Math.min(...rows.map(x=>x.length_m)),
  max_length_m:Math.max(...rows.map(x=>x.length_m)),
  noncoincident:rows.filter(x=>x.lag_s>0).length,
  max_lag_s:Math.max(...rows.map(x=>x.lag_s))};
}
module.exports={parse,calc,table,svg,selftest,SOURCE_SHA256};
if(require.main===module){
 const fs=require("fs"),crypto=require("crypto"),path=require("path"),args=process.argv.slice(2);
 if(args.length!==4||args[0]!=="--input"||args[2]!=="--out-dir")throw Error("USAGE --input SOURCE_CSV --out-dir DIR");
 const b=fs.readFileSync(args[1]);const got=crypto.createHash("sha256").update(b).digest("hex");
 ck(got===SOURCE_SHA256,"SOURCE_SHA_MISMATCH");
 const s=b.toString("utf8"),check=selftest(s),rows=parse(s);fs.mkdirSync(args[3],{recursive:true});
 const csv=table(rows),fig=svg(rows);
 const cp=path.join(args[3],"S07_NTM18_BASE_WRENCH_ORIGIN_GATE_18ROW_20261111.csv");
 const fp=path.join(args[3],"FIG3_S07_W_BASE_ORIGIN_TOLERANCE_20261111.svg");
 fs.writeFileSync(cp,csv);fs.writeFileSync(fp,fig);
 console.log(JSON.stringify({check,source_sha256:got,csv_sha256:crypto.createHash("sha256").update(csv).digest("hex"),svg_sha256:crypto.createHash("sha256").update(fig).digest("hex"),physical_pass:false}));
}
