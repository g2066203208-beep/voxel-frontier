"use strict";
// Original R5 DOCX SHA256: da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9
// Word Table 3-2/3-4; original figure 3-4(a) image45.png SHA256 19cbb41a754fce0eb3a98a6ea3c2b216737ec2317dae2c08288f369e71e072ae
// Original figure 3-4(b) image46.png SHA256 4c931c7ec41663fbbab6ef26a57ff3e0d9047ca231a1e516adfead243c56553f
// This program does not recover a histogram from quantiles or reprocess ERA5 hours.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const INPUT_SHA="b120c50b8e62d1c04c339a0d073c3775e43132ee2ba751766a0dccb1afc5e25c";
const KEYS=["n_total","n_valid","v10_mean","v100_mean","alpha_mean_ratio","alpha_p05","alpha_p25","alpha_p50","alpha_p75","alpha_p95","v160_mean_ratio","v160_hourly","eia_v160","era5_wpd","eia_wpd_text","eia_wpd_table"];
function parse(raw){
 const ls=raw.trimEnd().split(/\r?\n/);
 if(ls.shift()!=="key,value,unit,source"||ls.length!==16)throw Error("HEADER_OR_ROW_COUNT");
 const o={};
 for(let i=0;i<ls.length;i++){
  const a=ls[i].split(",");
  if(a.length!==4||a[0]!==KEYS[i]||a[3]!==("n_total v10_mean v100_mean".split(" ").includes(a[0])?"R5_table_3_2":"R5_table_3_4"))throw Error("IDENTITY_OR_SOURCE");
  const unit=(a[0].startsWith("n_")?"h":a[0].startsWith("alpha_")?"1":a[0].includes("wpd")?"W/m2":"m/s");
  if(a[2]!==unit||!/^\d+(?:\.\d+)?$/.test(a[1]))throw Error("UNIT_OR_NUMBER");
  o[a[0]]=Number(a[1]);
  if(!Number.isFinite(o[a[0]])||o[a[0]]<=0)throw Error("NONPOSITIVE");
 }
 if(!Number.isInteger(o.n_total)||!Number.isInteger(o.n_valid)||o.n_valid>o.n_total)throw Error("HOURS");
 for(let i=0;i<4;i++)if(!(o[["alpha_p05","alpha_p25","alpha_p50","alpha_p75","alpha_p95"][i]]<o[["alpha_p05","alpha_p25","alpha_p50","alpha_p75","alpha_p95"][i+1]]))throw Error("QUANTILE_ORDER");
 return o;
}
function analyze(v){
 const a=Math.log(v.v100_mean/v.v10_mean)/Math.log(10),check=v.v100_mean*Math.pow(1.6,v.alpha_mean_ratio);
 if(Math.abs(a-v.alpha_mean_ratio)>0.0002||Math.abs(check-v.v160_mean_ratio)>0.002)throw Error("SHEAR_RECONSTRUCTION");
 const excluded=v.n_total-v.n_valid,delta=v.v160_hourly-v.v160_mean_ratio;
 return {alpha_from_means:a,v160_from_rounded_means:check,excluded_hours:excluded,excluded_fraction_pct:100*excluded/v.n_total,
 delta_mps:delta,delta_rel_fixed_pct:100*delta/v.v160_mean_ratio,
 fixed_minus_eia_pct:100*(v.v160_mean_ratio/v.eia_v160-1),hourly_minus_eia_pct:100*(v.v160_hourly/v.eia_v160-1),
 wpd_vs_103_pct:100*(v.era5_wpd/v.eia_wpd_text-1),wpd_vs_104_pct:100*(v.era5_wpd/v.eia_wpd_table-1)};
}
function summary(v,d){
 const rows=[
 ["alpha_from_mean_winds",d.alpha_from_means,"1"],
 ["v160_from_rounded_means",d.v160_from_rounded_means,"m/s"],
 ["excluded_alpha_hours",d.excluded_hours,"h"],
 ["excluded_alpha_fraction",d.excluded_fraction_pct,"%"],
 ["hourly_minus_fixed_v160",d.delta_mps,"m/s"],
 ["hourly_minus_fixed_relative",d.delta_rel_fixed_pct,"%"],
 ["fixed_vs_eia_mean",d.fixed_minus_eia_pct,"%"],
 ["hourly_vs_eia_mean",d.hourly_minus_eia_pct,"%"],
 ["era5_wpd_vs_eia_text",d.wpd_vs_103_pct,"%"],
 ["era5_wpd_vs_eia_table",d.wpd_vs_104_pct,"%"]
 ];
 return "metric,value,unit\n"+rows.map(r=>r[0]+","+r[1].toFixed(9)+","+r[2]).join("\n")+"\n";
}
function render(v,d){
 const A=x=>(160+(x-0.05)/(0.42-0.05)*990).toFixed(1),V=x=>(160+(x-4.68)/(4.92-4.68)*990).toFixed(1),W=x=>(160+(x-98)/(135-98)*990).toFixed(1);
 const s=[
 '<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="930" viewBox="0 0 1320 930" role="img" aria-label="R5 ERA5 shear quantiles, 160m mean wind comparison and wind power density cross-check">',
 '<rect width="1320" height="930" fill="#ffffff"/>',
 '<text x="75" y="52" font-size="29" font-weight="700" font-family="Arial,sans-serif" fill="#18364a">ERA5 shear and 160 m extrapolation: source-recovered diagnostics</text>',
 '<text x="75" y="81" font-size="15" font-family="Arial,sans-serif" fill="#536a79">2005–2025 | R5 original Word Table 3-4 | quantile schematic, NOT a reconstructed histogram</text>',
 '<text x="75" y="121" font-size="21" font-weight="700" font-family="Arial,sans-serif" fill="#18364a">A  Hourly 10–100 m shear exponent: five reported quantiles</text>'
 ];
 const q=[["P05",v.alpha_p05],["P25",v.alpha_p25],["P50",v.alpha_p50],["P75",v.alpha_p75],["P95",v.alpha_p95]];
 for(let i=0;i<q.length;i++){const y=165+i*44;s.push('<text x="105" y="'+(y+5)+'" font-size="16" font-family="Arial,sans-serif" fill="#35546b">'+q[i][0]+'</text>','<line x1="160" y1="'+y+'" x2="1150" y2="'+y+'" stroke="#e4ebf0"/>','<circle cx="'+A(q[i][1])+'" cy="'+y+'" r="9" fill="#347ba4"/>','<text x="'+(Number(A(q[i][1]))+14)+'" y="'+(y+5)+'" font-size="15" font-family="Arial,sans-serif" fill="#285b79">'+q[i][1].toFixed(3)+'</text>');}
 const ax=A(v.alpha_mean_ratio);s.push('<line x1="'+ax+'" y1="147" x2="'+ax+'" y2="357" stroke="#d48132" stroke-dasharray="6 5" stroke-width="2"/>','<text x="'+(Number(ax)+10)+'" y="363" font-size="14" font-family="Arial,sans-serif" fill="#a05c21">ratio-of-means alpha = '+v.alpha_mean_ratio.toFixed(4)+'</text>',
 '<text x="75" y="413" font-size="21" font-weight="700" font-family="Arial,sans-serif" fill="#18364a">B  Mean wind speed at 160 m (m/s)</text>');
 const winds=[["ERA5 fixed ratio alpha",v.v160_mean_ratio,"#347ba4"],["Project EIA published",v.eia_v160,"#6a7b85"],["ERA5 hourly alpha(t)",v.v160_hourly,"#d48132"]];
 for(let i=0;i<winds.length;i++){let y=454+i*49,x=V(winds[i][1]);s.push('<text x="110" y="'+(y+5)+'" font-size="15" font-family="Arial,sans-serif" fill="#344e5f">'+winds[i][0]+'</text>','<line x1="160" y1="'+(y+13)+'" x2="1150" y2="'+(y+13)+'" stroke="#e4ebf0"/>','<circle cx="'+x+'" cy="'+(y+13)+'" r="10" fill="'+winds[i][2]+'"/>','<text x="'+(Number(x)+14)+'" y="'+(y+18)+'" font-size="16" font-family="Arial,sans-serif" fill="'+winds[i][2]+'">'+winds[i][1].toFixed(3)+'</text>');}
 s.push('<text x="75" y="626" font-size="15" font-family="Arial,sans-serif" fill="#4c6474">Hourly minus fixed = '+d.delta_mps.toFixed(3)+' m/s ('+d.delta_rel_fixed_pct.toFixed(2)+'% of fixed); sample handling for excluded hours is unresolved.</text>',
 '<text x="75" y="666" font-size="21" font-weight="700" font-family="Arial,sans-serif" fill="#18364a">C  Wind power density cross-check (W/m²; not a calibration)</text>');
 const powers=[["EIA text",v.eia_wpd_text,"#6a7b85"],["EIA table",v.eia_wpd_table,"#6a7b85"],["ERA5 hourly-alpha proxy",v.era5_wpd,"#d48132"]];
 for(let i=0;i<powers.length;i++){let y=704+i*49,x=W(powers[i][1]);s.push('<text x="110" y="'+(y+5)+'" font-size="15" font-family="Arial,sans-serif" fill="#344e5f">'+powers[i][0]+'</text>','<line x1="160" y1="'+(y+13)+'" x2="1150" y2="'+(y+13)+'" stroke="#e4ebf0"/>','<circle cx="'+x+'" cy="'+(y+13)+'" r="10" fill="'+powers[i][2]+'"/>','<text x="'+(Number(x)+14)+'" y="'+(y+18)+'" font-size="16" font-family="Arial,sans-serif" fill="'+powers[i][2]+'">'+powers[i][1].toFixed(1)+'</text>');}
 s.push('<line x1="75" y1="870" x2="1240" y2="870" stroke="#d7e3e9"/>',
 '<text x="75" y="897" font-size="13" font-family="Arial,sans-serif" fill="#627888">SOURCE: R5 Word Table 3-2/3-4; original figures 3-4(a,b). Values transcribed from printed source, not ERA5 hourly reprocessing.</text>',
 '<text x="75" y="916" font-size="13" font-family="Arial,sans-serif" fill="#627888">The 160 m comparison must not be mixed with the separate 161.368806 m hub-height workflow; EIA is a different evidence class.</text>',
 '</svg>');
 return s.join("\n")+"\n";
}
function selftest(raw){
 const v=parse(raw),d=analyze(v);
 if(d.excluded_hours!==3312||Math.abs(d.delta_mps-0.106)>1e-12||Math.abs(d.alpha_from_means-0.215563722477)>1e-9||Math.abs(d.wpd_vs_104_pct-24.3269230769)>1e-9)throw Error("REAL_ORACLE");
 const bad=[raw.replace("n_valid,180768","n_valid,184081"),raw.replace("v100_mean,4.299","v100_mean,NaN"),raw.replace("alpha_p75,0.297","alpha_p75,0.050"),raw.replace("eia_v160,4.790","eia_v160,-1"),raw.replace("n_total,184080","n_total,184080.5"),raw.replace("v10_mean,2.617,m/s","v10_mean,2.617,km/h"),raw+"extra,1,m/s,R5_table_3_4\n",raw.replace("v160_mean_ratio,4.757","v160_mean_ratio,5.757")];
 for(const b of bad){let fail=false;try{analyze(parse(b));}catch(e){fail=true;}if(!fail)throw Error("INVALID_ACCEPTED");}
 return "SELFTEST_PASS real=4 rejects=8";
}
function main(){
 const input=path.join(__dirname,"S12_R5_ERA5_SHEAR_160M_SOURCE_20261109.csv");
 const summaryPath=path.join(__dirname,"S12_R5_ERA5_SHEAR_160M_DIAGNOSTICS_20261109.csv");
 const figurePath=path.join(__dirname,"../../manuscript/final-thesis/figures/FIG3_S12_ERA5_SHEAR_160M_CROSSCHECK_20261109.svg");
 const raw=fs.readFileSync(input,"utf8");
 if(crypto.createHash("sha256").update(raw).digest("hex")!==INPUT_SHA)throw Error("SOURCE_SHA_MISMATCH");
 const v=parse(raw),d=analyze(v),a=summary(v,d),b=render(v,d);
 if(process.argv.includes("--write")){fs.writeFileSync(summaryPath,a,"utf8");fs.writeFileSync(figurePath,b,"utf8");}
 if(process.argv.includes("--check")&&(fs.readFileSync(summaryPath,"utf8")!==a||fs.readFileSync(figurePath,"utf8")!==b))throw Error("OUTPUT_DRIFT");
 console.log(selftest(raw),JSON.stringify(d),crypto.createHash("sha256").update(a).digest("hex"),crypto.createHash("sha256").update(b).digest("hex"));
}
if(require.main===module)main();
module.exports={parse,analyze,summary,render,selftest};
