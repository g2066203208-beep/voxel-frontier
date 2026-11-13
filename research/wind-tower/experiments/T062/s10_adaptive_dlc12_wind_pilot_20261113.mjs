#!/usr/bin/env node
// Source-locked source-level wind-bin pilot design; never claims physical fatigue or IEC certification.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, resolve } from "node:path";
const DATA_DIR=resolve(process.argv[2] ?? "research/wind-tower/experiments/T062");
const OUT_DIR=resolve(process.argv[3] ?? DATA_DIR);
const EXPECTED={
  "S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv":"e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102",
  "S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv":"d4e25023f343ea76f2de5ce90c7d24dd985df770ec9f4747d203391010431e67"
};
function readLocked(name){const b=readFileSync(join(DATA_DIR,name));const h=createHash("sha256").update(b).digest("hex");if(h!==EXPECTED[name])throw Error("SOURCE_SHA_MISMATCH: "+name+" "+h);return b.toString("utf8");}

const runDesign=function runDesign(binText,matrixText) {
  function parseCSV(text) {
    const rows=text.trim().split(/\r?\n/);const header=rows.shift().split(",");
    return rows.map((line,li)=>{const x=line.split(",");if(x.length!==header.length)throw Error("CSV_COLUMNS_"+li);return Object.fromEntries(header.map((key,i)=>[key,x[i]]));});
  }
  function fail(x){throw Error("SOURCE_CONTRACT_FAIL_"+x);}
  const all=parseCSV(binText), mat=parseCSV(matrixText);
  if(all.length!==31)fail("31_BIN_COUNT"); if(mat.length!==126)fail("126_MATRIX_COUNT");
  if(all.reduce((s,x)=>s+Number(x.hours),0)!==184080)fail("184080_TOTAL");
  const bins=all.filter(x=>+x.bin_lower_mps>=4&&+x.bin_lower_mps<25);
  const hours=bins.reduce((s,x)=>s+ +x.hours,0);
  if(hours!==106900)fail("106900_DIAGNOSTIC_HOURS");
  const sourceCases=[...new Set(mat.filter(x=>x.historical_case_id).map(x=>x.historical_case_id))];
  if(sourceCases.length!==18)fail("18_ARCHIVED_CASES");
  const historicalGroups=[8,10,18];
  const pList=[0,2,4,6,8,10];
  const denominator=Object.fromEntries(pList.map(p=>[p,bins.reduce((sum,z)=>sum+ +z.hours*Math.pow(+z.bin_lower_mps+0.5,p),0)]));
  const fnv=(s)=>{let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return 1+(h%2147483646)};
  const groups=[];
  for(let lo=4;lo<25;lo+=2){
    const up=Math.min(lo+2,25),members=bins.filter(z=>+z.bin_lower_mps>=lo&&+z.bin_lower_mps<up);
    const h=members.reduce((s,z)=>s+ +z.hours,0);
    const archive=[...new Set(mat.filter(z=>+z.bin_lower_mps>=lo&&+z.bin_lower_mps<up&&z.historical_case_id).map(z=>z.historical_case_id))];
    if(archive.length!==0&&archive.length!==6)fail("UNEXPECTED_ARCHIVE_"+lo);
    const row={bin_lower_mps:lo,bin_upper_exclusive_mps:up,planned_center_mps:(lo+up)/2,
      era5_21y_hours:h,conditional_hours_share:h/hours,annual_hours_8760:8760*h/184080,
      archived_historical_ntm_cases:archive.length,archive_is_formal_dlc12:false,
      scope:h>0?"OBSERVED_POSITIVE":"ZERO_OBSERVED_DESIGN_TAIL"};
    for(const p of pList){const v=members.reduce((s,z)=>s+ +z.hours*Math.pow(+z.bin_lower_mps+0.5,p),0);
      row["proxy_U_power_"+p+"_share"]=v/denominator[p];}
    groups.push(row);
  }
  if(groups.length!==11||groups.reduce((s,x)=>s+x.era5_21y_hours,0)!==hours)fail("GROUP_COVERAGE");
  if(groups.filter(x=>x.archived_historical_ntm_cases===6).map(x=>x.bin_lower_mps).join(",")!==historicalGroups.join(","))fail("HISTORY_GROUPS");
  const planned=[];
  const seen=new Set();
  for(const g of groups)if(g.archived_historical_ntm_cases===0){
    for(let index=1;index<=2;index++){
      const seed=fnv("DTU158|20261113|"+g.bin_lower_mps+"|"+index);
      if(seen.has(seed)||[104729,130363,155921,181081,206369,231701].includes(seed))fail("SEED_COLLISION");
      seen.add(seed);
      planned.push({stage:g.era5_21y_hours?"A_OBSERVED_POSITIVE_PILOT":"B_ZERO_OBSERVED_TAIL_CONDITIONAL",
        source_range_mps:g.bin_lower_mps+"-"+g.bin_upper_exclusive_mps,
        URef_mps:g.planned_center_mps,seed_label:"P0"+index,rand_seed1:seed,expected_usable_seconds:600,
        NTM_setting:"IEC_NTM_CONFIG_MUST_BE_VERIFIED",status:"PLANNED_NOT_RUN",
        formal_DLC12_status:"NOT_VALIDATED"});
    }
  }
  if(planned.length!==16||planned.filter(z=>z.stage.startsWith("A_")).length!==10)fail("PILOT_COUNTS");
  const rankings={};
  for(const p of pList)rankings[p]=[...groups].sort((x,y)=>y["proxy_U_power_"+p+"_share"]-x["proxy_U_power_"+p+"_share"]).map(x=>({range:x.bin_lower_mps+"-"+x.bin_upper_exclusive_mps,share:x["proxy_U_power_"+p+"_share"]})).slice(0,5);
  return {
    summary:{
      status:"SOURCE_LEVEL_RESEARCH_PILOT_DESIGN_ONLY",data_basis:"2005-2025 ERA5 derived 184080h / NTM historical identity",
      diagnostic_wind_range_mps:"[4,25) NOT_OFFICIAL_CUT_IN_OUT",
      bin_width_mps:"2 except [24,25)",observed_operating_hours:hours,total_era5_hours:184080,
      historical_NTM_count:18,original_1m_historical_coverage_hours:7164,
      original_1m_historical_coverage_share:7164/hours,
      observed_2m_groups:groups.filter(x=>x.era5_21y_hours>0).length,
      archived_anchor_2m_groups:3, missing_observed_2m_groups:5,
      zero_observed_tail_2m_groups:3,
      stage_A_positive_pilot_new_cases:10,stage_B_tail_conditional_pilot_new_cases:6,
      research_6_seed_complete_without_historical_reuse:66,
      research_6_seed_complete_with_all_18_historical_cases_qualified:48,
      historical_reuse_is_not_authorized:true,
      scenario_proxy_warning:"p=0/2/4/6/8/10 multiplies ERA5 hour count by U_mid^p; NOT material fatigue damage, bounds, IEC weights or evidence of fatigue risk",
      annual_Miner_status:"NOT_IDENTIFIABLE_WITH_THIS_SOURCE",
      new_wind_turbine_runs:0
    },groups,planned,rankings
  };
};
const result=runDesign(readLocked(Object.keys(EXPECTED)[0]),readLocked(Object.keys(EXPECTED)[1]));
const num=x=>typeof x==="number"?x.toFixed(Number.isInteger(x)?0:12):String(x);
function csv(rows){const cols=Object.keys(rows[0]);return cols.join(",")+"\n"+rows.map(r=>cols.map(k=>num(r[k])).join(",")).join("\n")+"\n"}
mkdirSync(OUT_DIR,{recursive:true});
writeFileSync(join(OUT_DIR,"S10_ADAPTIVE_WIND_11GROUP_CLIMATE_SCENARIO_20261113.csv"),csv(result.groups),"utf8");
writeFileSync(join(OUT_DIR,"S10_ADAPTIVE_WIND_16CASE_PILOT_MANIFEST_20261113.csv"),csv(result.planned),"utf8");
writeFileSync(join(OUT_DIR,"S10_ADAPTIVE_WIND_DESIGN_RECEIPT_20261113.json"),JSON.stringify({...result.summary,power_proxy_top5:result.rankings,input_sha256:EXPECTED},null,2)+"\n","utf8");
console.log(JSON.stringify({source_pass:true,...result.summary},null,2));
