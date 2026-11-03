"use strict";
// S10 non-solver source-locked acquisition priority; NOT material Miner damage.
const {sha256}=require("./s10_dlc12_bin_seed_source_coverage.cjs");
function ok(v,s){if(!v)throw Error(s);}
function q(v){ok(Number.isFinite(v),"NONFINITE");return Number(v.toFixed(6));}
function calculate(binCsv,loadJson){
 const r=JSON.parse(loadJson);
 ok(sha256(binCsv)===r.SOURCE.era5_31bin_sha256,"ERA5_HASH");
 ok(r.SOURCE_OBSERVATIONS.era5_hours===184080&&r.SOURCE_OBSERVATIONS.operating_hours_4_to_25_DIAGNOSTIC===106900&&r.SOURCE_OBSERVATIONS.archived_NTM_cases===18&&r.SOURCE_OBSERVATIONS.formal_verified_DLC12_slots===0,"SOURCE_SCOPE");
 const lines=binCsv.trim().split(/\r?\n/);
 ok(lines.length===32&&lines[0].startsWith("bin_lower_mps,bin_upper_mps_exclusive,hours,"),"CSV_SCHEMA");
 const bins=lines.slice(1).map(s=>s.split(",")).map(v=>({bin:+v[0],hours:+v[2]}));
 ok(bins.every((x,i)=>x.bin===i&&Number.isSafeInteger(x.hours)&&x.hours>=0),"BIN_ID");
 ok(bins.reduce((s,x)=>s+x.hours,0)===184080&&bins.slice(4,25).reduce((s,x)=>s+x.hours,0)===106900,"HOUR_SUM");
 const speeds=[9.343881,11.4,19.20214],missing=bins.filter(x=>x.bin>=4&&x.bin<25&&x.hours>0&&![9,11,19].includes(x.bin));
 const noExtrap=missing.filter(x=>x.bin+.5<speeds[0]),interpolated=missing.filter(x=>x.bin+.5>=speeds[0]&&x.bin+.5<=speeds[2]);
 ok(missing.length===13&&noExtrap.length===5&&interpolated.length===8&&noExtrap.reduce((s,x)=>s+x.hours,0)===95402,"GAP_SCOPE");
 const results={};
 for(const channel of ["TwrBsMxt","TwrBsMyt"]){
   const src=r.LOAD_M4_SPEED_EXPONENT_DIAGNOSTIC[channel];
   ok(src&&src.wind_speed_mps.length===3&&src.intervals.length===2&&src.six_seed_power_mean_DEL_MNm.length===3,"CHANNEL_SCHEMA");
   speeds.forEach((v,i)=>ok(Math.abs(src.wind_speed_mps[i]-v)<1e-8,"SPEED_ID"));
   const ranking=interpolated.map(x=>{
     const u=x.bin+.5,j=u<speeds[1]?0:1,a=speeds[j],b=speeds[j+1],L=src.six_seed_power_mean_DEL_MNm[j],s=src.intervals[j];
     const p=s.effective_p_for_load_DEL_fourth_moment,lo=s["3of6_subset_p_min"],hi=s["3of6_subset_p_max"];
     ok(L>0&&lo<=p&&p<=hi&&Math.abs(s.wind_speed_start_mps-a)<1e-8&&Math.abs(s.wind_speed_end_mps-b)<1e-8,"SLOPE_SCHEMA");
     ok(Math.abs(4*Math.log(src.six_seed_power_mean_DEL_MNm[j+1]/L)/Math.log(b/a)-p)<1e-6,"SLOPE_DEL_MISMATCH");
     const w=z=>x.hours/184080*Math.pow(L,4)*Math.pow(u/a,z);
     return {bin:x.bin,hours:x.hours,center_mps_NONNORMATIVE:u,source_bracket_mps:[a,b],
       nominal_load_m4_weighted:q(w(p)),slope_sensitivity_min:q(w(lo)),slope_sensitivity_max:q(w(hi))};
   }).sort((a,b)=>b.nominal_load_m4_weighted-a.nominal_load_m4_weighted||a.bin-b.bin);
   ok(ranking.length===8&&ranking[0].bin===10&&ranking[1].bin===12,"PRIORITY_REGRESSION");
   const robust=ranking[0].slope_sensitivity_min>ranking[1].slope_sensitivity_max&&ranking[1].slope_sensitivity_min>ranking[2].slope_sensitivity_max;
   ok(robust,"FIRST_TWO_SLOPE_ENVELOPES_OVERLAP");
   results[channel]={interpolated_missing_bins_ranked:ranking,first_two_separated_under_conditional_slope_variation:robust,
     bin13_above_bin14_under_conditional_slope_variation:ranking[2].slope_sensitivity_min>ranking[3].slope_sensitivity_max};
 }
 return {status:"S10_SOURCE_RECOVERY_PRIORITY_ONLY_NOT_FATIGUE",SOURCE:{era5_31bin_sha256:sha256(binCsv),load_18ntm_receipt_sha256:sha256(loadJson),archived_outb_derived_del_csv_sha256:r.SOURCE.original_18NTM_1080rows_sha256},
  READING_LEVEL:"Direct derived ERA5 31-bin CSV and 18-NTM six-seed load-DEL receipt; original ERA5 workbook and OUTB not reread in this calculation",
  REF:"Existing T062 load-DEL source-locked study and finite 3-of-6 seed subset sensitivity; no new full-paper read",
  STANDARD:"IEC 61400-1/6 2025 licensed clauses unavailable; 1m/s centers and [4,25) m/s are nonnormative planning assumptions",
  OFFICIAL:"Inherited original OpenFAST v3.5.3 OUTB and ERA5 workbook provenance, not a new native solver run",
  RUN:"Deterministic Node.js standard-library calculation and five tamper-rejection tests; no production solver",
  FIG:"none",TAB:"13 missing positive-hour bins; 5 NO-EXTRAPOLATION low bins and two channel-specific 8-bin interpolation ranks",
  ASSUMPTIONS:"Piecewise DEL^4 power interpolation ONLY inside actual three speeds 9.343881/11.4/19.20214 m/s; 6-seed DEL anchor, bin-center speed, ERA5 hours/184080. This is NOT a material damage model",
  ERROR_BUDGET:"Reported moments rounded to 6 decimals (<=0.5e-6 MNm^4); 3-of-6 slope envelope is NOT a confidence interval; anchor DEL, nonlinear controller, ERA5 bias, wind-bin representativeness and model-form errors NOT bounded",
  HOLD:"4-8 m/s covers 95402/106900 diagnostic operating hours but has NO observed load-DEL anchor; 13 positive-hour missing bins; local material stress, IEC2025 DLC1.2, physical baseline and E/WE unavailable",
  no_extrapolation_bins:noExtrap.map(x=>({...x,load_m4:"NOT_ESTIMATED"})),interpolated_missing_bins:8,positive_missing_bins:13,
  results,physical_pass:false,material_fatigue_pass:false,formal_dlc12_verified_slots:0,earthquake_native_results:0};
}
function negativeTests(b,r){
 const mutations=[[b.replace("4,5,26927,","4,5,26928,"),r],[b,r.replace('"era5_hours": 184080','"era5_hours": 184079')],
 [b,r.replace('"effective_p_for_load_DEL_fourth_moment": 7.412566056','"effective_p_for_load_DEL_fourth_moment": 99.412566056')],
 [b,r.replace('"six_seed_power_mean_DEL_MNm": [','"six_seed_power_mean_DEL_MNm": [-1,')],
 [b,r.replace('"wind_speed_mps": [','"wind_speed_mps": [0,')]];
 mutations.forEach(([x,y],i)=>{ok(x!==b||y!==r,"MUTATION_NOOP_"+i);let rejected=false;try{calculate(x,y);}catch(e){rejected=true;}ok(rejected,"NEGATIVE_ACCEPTED_"+i);});
 return mutations.length;
}
if(typeof module!=="undefined")module.exports={calculate,negativeTests};
if(typeof require!=="undefined"&&require.main===module){
 const fs=require("fs"),path=require("path"),dir=__dirname;
 const b=fs.readFileSync(path.join(dir,"S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv"),"utf8");
 const r=fs.readFileSync(path.join(dir,"partial-annual-load-diagnostic-20261102/S10_REAL_18NTM_3BIN_PARTIAL_M4_RECEIPT_20261102.json"),"utf8");
 const v=calculate(b,r),n=negativeTests(b,r);ok(n===5,"NEGATIVE_COUNT");
 if(process.argv.includes("--check")){
  const saved=JSON.parse(fs.readFileSync(path.join(dir,"S10_CHANNEL_AWARE_M4_INTERPOLATION_PRIORITY_20261104.json"),"utf8"));
  function same(a,b){if(typeof a==="number"&&typeof b==="number")return Math.abs(a-b)<1e-6;
   if(Array.isArray(a))return Array.isArray(b)&&a.length===b.length&&a.every((x,i)=>same(x,b[i]));
   if(a&&typeof a==="object")return b&&typeof b==="object"&&Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>same(a[k],b[k]));
   return a===b;}
  ok(same(v,saved),"COMMITTED_RECEIPT_MISMATCH");
 }else process.stdout.write(JSON.stringify(v,null,2)+"\n");
 console.log("S10_CHANNEL_AWARE_M4_PRIORITY_SOURCE_QC_PASS_NOT_MATERIAL_DAMAGE negative_tests="+n);
}
