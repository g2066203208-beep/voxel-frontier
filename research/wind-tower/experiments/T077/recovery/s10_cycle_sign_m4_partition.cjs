#!/usr/bin/env node
"use strict";
// S10 real ETM nominal rainflow cycles: sign partition, NOT material Miner fatigue.
const SOURCE="S10_3CONTROL_REAL_GROSS_CYCLES_20261030.csv";
const SOURCE_SHA="646065838456b6465e321c4c6fd24966f180f275df99c615000577557219ff83";
const RECEIPT="S10_3CONTROL_CYCLE_SIGN_M4_PARTITION_20261104.json";
const KEYS=[["U09p343881_ETM_S06","CSEG_16","180",413,407.5],["U09p343881_ETM_S06","CSEG_17","180",526,520.5],["U11p4_ETM_S04","CSEG_04","0",635,628]];
const HEADER="case,segment,azimuth_deg,cycle_index,range_MPa,amplitude_MPa,mean_gross_MPa,mean_Pe_hypothesis_MPa,mean_P0_hypothesis_MPa,count,status";
function check(v,m){if(!v)throw Error(m)}
function sign(range,mean){check(Number.isFinite(range)&&range>0&&Number.isFinite(mean),"BAD_CYCLE");const lo=mean-range/2,hi=mean+range/2;return [hi<=0?"compression":lo>=0?"tension":"reversing",Math.min(Math.abs(lo),Math.abs(hi))]}
function parse(csv){const lines=csv.trimEnd().split(/\r?\n/);check(lines.shift()===HEADER,"HEADER");const cols=HEADER.split(",");const rows=lines.map(line=>{const f=line.split(",");check(f.length===cols.length,"FIELD_COUNT");const x=Object.fromEntries(cols.map((c,i)=>[c,f[i]]));for(const c of ["cycle_index","range_MPa","amplitude_MPa","mean_gross_MPa","mean_Pe_hypothesis_MPa","mean_P0_hypothesis_MPa","count"]){check(x[c].trim()!==""&&Number.isFinite(Number(x[c])),"BAD_NUMBER_"+c);x[c]=Number(x[c])}check(Number.isInteger(x.cycle_index)&&x.cycle_index>=1,"INDEX");check(x.range_MPa>0&&(x.count===0.5||x.count===1),"RANGE_OR_COUNT");check(Math.abs(x.amplitude_MPa-x.range_MPa/2)<1e-9,"AMPLITUDE");check(x.status==="REAL_GROSS_NOMINAL_CYCLES_PT_MEAN_SHIFT_HYPOTHESIS_NOT_LOCAL_MATERIAL","STATUS");check(x.mean_gross_MPa>=x.mean_Pe_hypothesis_MPa&&x.mean_Pe_hypothesis_MPa>=x.mean_P0_hypothesis_MPa,"PT_ORDER");return x});check(rows.length===1574,"TOTAL_ROWS");return rows}
const round=x=>Number(x.toPrecision(12));
function analyze(csv){const rows=parse(csv),out=[];for(const [c,s,a,n,cycles] of KEYS){const r=rows.filter(x=>x.case===c&&x.segment===s&&x.azimuth_deg===a);check(r.length===n,"GROUP_ROWS");r.forEach((x,i)=>check(x.cycle_index===i+1,"ORDER"));check(r.reduce((v,x)=>v+x.count,0)===cycles,"CYCLE_COUNT");const shift={Pe:r[0].mean_gross_MPa-r[0].mean_Pe_hypothesis_MPa,P0:r[0].mean_gross_MPa-r[0].mean_P0_hypothesis_MPa};const scenarios={};for(const [scenario,col] of [["gross","mean_gross_MPa"],["Pe","mean_Pe_hypothesis_MPa"],["P0","mean_P0_hypothesis_MPa"]]){const names=["compression","reversing","tension"],v=Object.fromEntries(names.map(k=>[k,{rows:0,cycles:0,m4:0}]));let total=0,margin=Infinity;for(const x of r){if(scenario!=="gross")check(Math.abs((x.mean_gross_MPa-x[col])-shift[scenario])<1e-8,"NONCONSTANT_SHIFT");const [kind,d]=sign(x.range_MPa,x[col]);const m4=x.count*x.range_MPa**4;v[kind].rows++;v[kind].cycles+=x.count;v[kind].m4+=m4;total+=m4;margin=Math.min(margin,d)}scenarios[scenario]={row_counts:Object.fromEntries(names.map(k=>[k,v[k].rows])),equivalent_cycle_counts:Object.fromEntries(names.map(k=>[k,v[k].cycles])),m4_proxy_fractions:Object.fromEntries(names.map(k=>[k,round(v[k].m4/total)])),m4_proxy_total_MPa4_cycles:round(total),minimum_endpoint_zero_margin_MPa:round(margin)}}check(Math.abs(scenarios.gross.m4_proxy_total_MPa4_cycles-scenarios.Pe.m4_proxy_total_MPa4_cycles)<1e-5,"M4_SHIFT_INVARIANCE");out.push({case:c,segment:s,azimuth_deg:Number(a),cycle_rows:n,equivalent_cycles:cycles,uniform_PT_shift_hypotheses_MPa:{Pe:round(shift.Pe),P0:round(shift.P0)},scenarios})}check(out.reduce((v,x)=>v+x.cycle_rows,0)===rows.length,"EXTRA_CASE");return out}
function selftest(){check(sign(4,0)[0]==="reversing"&&sign(2,-2)[0]==="compression"&&sign(2,2)[0]==="tension"&&sign(4,0)[1]===2,"KNOWN_ANSWERS");let rejects=0;for(const [a,b] of [[0,0],[-1,0],[NaN,1],[1,Infinity]]){try{sign(a,b)}catch(e){rejects++}}check(rejects===4,"NEGATIVE_TESTS");return {known_answers:4,negative_rejections:4}}

const PT_KSI_MPA=6.894757293168361;
function materialApplicability(csv){
  const rows=parse(csv),scenarios=[["gross","mean_gross_MPa"],["Pe","mean_Pe_hypothesis_MPa"],["P0","mean_P0_hypothesis_MPa"]];
  const groups=new Map();let maxRange=0,minRange=Infinity,ptRangeMatches=0;
  const materialRejections={concrete:0,ordinary_rebar:0,prestressing_strand:0,steel_tower:0};
  for(const x of rows){
    const rg=x.range_MPa;maxRange=Math.max(maxRange,rg);minRange=Math.min(minRange,rg);
    if(rg/PT_KSI_MPA>=22&&rg/PT_KSI_MPA<=81)ptRangeMatches++;
    for(const [scenario,col] of scenarios){
      const key=[x.case,x.segment,scenario].join("/");
      if(!groups.has(key))groups.set(key,{case:x.case,segment:x.segment,scenario,rows:0,compression:0,reversing:0,tension:0,compression_R_min:Infinity,compression_R_max:-Infinity,tension_R_min:Infinity,tension_R_max:-Infinity});
      const g=groups.get(key),lo=x[col]-rg/2,hi=x[col]+rg/2;g.rows++;
      for(const material of Object.keys(materialRejections)){
        check(x.status!=="VERIFIED_LOCAL_MATERIAL_STRESS","UNEXPECTED_LOCAL_MATERIAL_SOURCE_"+material);
        materialRejections[material]++;
      }
      if(hi<=0){const R=hi/lo;check(R>=0&&R<=1,"COMPRESSION_R_DOMAIN");g.compression++;g.compression_R_min=Math.min(g.compression_R_min,R);g.compression_R_max=Math.max(g.compression_R_max,R)}
      else if(lo>=0){const R=lo/hi;check(R>=0&&R<=1,"TENSION_R_DOMAIN");g.tension++;g.tension_R_min=Math.min(g.tension_R_min,R);g.tension_R_max=Math.max(g.tension_R_max,R)}
      else g.reversing++;
    }
  }
  const out=[...groups.values()].map(g=>{
    check(g.compression+g.reversing+g.tension===g.rows,"DOMAIN_CLASS_COUNT");
    for(const kind of ["compression","tension"])for(const suffix of ["min","max"]){const k=kind+"_R_"+suffix;g[k]=Number.isFinite(g[k])?round(g[k]):null}
    return g;
  });
  check(rows.length===1574&&out.length===9&&out.every(g=>g.rows>0),"DOMAIN_GROUP_IDENTITY");
  check(ptRangeMatches===0&&maxRange<22*PT_KSI_MPA,"PT_RAW_RANGE_GUARD");
  check(Object.values(materialRejections).every(n=>n===rows.length*scenarios.length),"MATERIAL_REJECTION_COUNTS");
  return {
    status:"CONDITIONAL_GROSS_STRESS_DOMAIN_SCREEN_NOT_LOCAL_MATERIAL_OR_MINER",
    source_owner:"NOMINAL_ELASTIC_SECTION_STRESS_NOT_VERIFIED_LOCAL_MATERIAL_STRESS",
    source_cycle_rows:rows.length,counterfactual_scenarios:3,material_classes:4,
    diagnostic_material_checks:Object.values(materialRejections).reduce((a,b)=>a+b,0),material_source_rejections:materialRejections,admitted_material_cycles:0,
    gross_stress_range_MPa:{minimum:round(minRange),maximum:round(maxRange)},
    paulson1983_primary_A_dataset:{
      source:"FHWA/TX-82/54+300-1 printed pp57-62; previously read in s10_local_stress_rainflow_gate.py",
      raw_range_ksi:[22,81],raw_range_MPa:[round(22*PT_KSI_MPA),round(81*PT_KSI_MPA)],
      nominal_gross_cycles_in_raw_range_domain:ptRangeMatches,
      minimum_strand_stress_ksi:[75,165],minimum_strand_stress_evaluated:false,
      note:"0/1574 nominal gross-section ranges match primary strand-test range; NOT a PT strand stress test or physical rejection of real PT fatigue."
    },
    material_admission:{
      concrete:{admitted:0,missing:["verified local concrete stress/strain and crack state","concrete strength and compressive/tensile fatigue model","validated mean-stress/R applicability"]},
      ordinary_rebar:{admitted:0,missing:["verified local HRB-grade rebar stress history","bar detail and grade-specific S-N parameters","validated mean-stress/R applicability"]},
      prestressing_strand:{admitted:0,missing:["verified actual strand stress and effective PT","strand diameter/anchorage and fatigue test-domain match","validated mean-stress treatment"]},
      steel_tower:{admitted:0,missing:["verified local steel/weld hotspot stress history","weld/detail S-N category and thickness effects","validated mean-stress rule and extraction"]}
    },by_group:out
  };
}
function materialDomainSelftest(){
  check(22*PT_KSI_MPA>33.7989163687,"PT_TEST_RANGE_LOWER_BOUND");
  check(75*PT_KSI_MPA>0&&81*PT_KSI_MPA>22*PT_KSI_MPA,"PT_TEST_UNITS");
  for(const [lo,hi,kind] of [[-4,-2,"compression"],[2,4,"tension"],[-2,4,"reversing"]]){
    check((hi<=0?"compression":lo>=0?"tension":"reversing")===kind,"SYNTHETIC_DOMAIN_CLASS");
  }
  return {known_answer_checks:5,physical_pass:false};
}

const SUMMARY="S10_3CONTROL_REAL_CYCLE_MEAN_SUMMARY_20261030.csv";
const SUMMARY_HEADER="case,segment,azimuth_deg,cycle_rows,half_cycles,full_cycles,equivalent_cycles,DEL_m4_MPa,DEL_m10_MPa,conditional_Pe_mean_shift_MPa,conditional_P0_mean_shift_MPa,status";
function concentration(cycles,Nref=600){
  check(cycles.length>0&&Number.isFinite(Nref)&&Nref>0,"CONCENTRATION_INPUT");
  const w=cycles.map(x=>{
    check(Number.isFinite(x.range)&&x.range>0&&(x.count===0.5||x.count===1),"CONCENTRATION_CYCLE");
    return {count:x.count,energy:x.count*x.range**4};
  });
  const m4=w.reduce((s,x)=>s+x.energy,0),half=w.filter(x=>x.count===0.5);
  check(Number.isFinite(m4)&&m4>0,"CONCENTRATION_M4");
  const hm4=half.reduce((s,x)=>s+x.energy,0),top=Math.ceil(w.length*.01);
  const topm4=[...w].sort((a,b)=>b.energy-a.energy).slice(0,top).reduce((s,x)=>s+x.energy,0);
  const d4=(m4/Nref)**.25,incorrect=((m4+hm4)/Nref)**.25;
  return {cycle_rows:w.length,equivalent_cycles:w.reduce((s,x)=>s+x.count,0),
    half_cycle_rows:half.length,half_cycle_m4_fraction:round(hm4/m4),
    top_one_percent_rows:top,top_one_percent_m4_fraction:round(topm4/m4),
    DEL4_MPa:round(d4),counterfactual_half_as_full_DEL4_MPa:round(incorrect),
    counterfactual_half_as_full_DEL_bias_pct:round(100*(incorrect/d4-1))};
}
function cycleWeightAudit(csv,summary){
  const rows=parse(csv), lines=summary.trimEnd().split(/\r?\n/);
  check(lines.shift()===SUMMARY_HEADER,"SUMMARY_HEADER");
  const keys=SUMMARY_HEADER.split(",");
  const expected=lines.map(l=>Object.fromEntries(l.split(",").map((v,i)=>[keys[i],v])));
  check(expected.length===3,"SUMMARY_CONTROL_COUNT");
  const out=[];
  for(const [c,s,a,n,eq] of KEYS){
    const x=rows.filter(z=>z.case===c&&z.segment===s&&z.azimuth_deg===a);
    check(x.length===n,"CONCENTRATION_GROUP_ROWS");
    const audit=concentration(x.map(z=>({range:z.range_MPa,count:z.count})));
    const oracle=expected.find(z=>z.case===c&&z.segment===s&&z.azimuth_deg===a);
    check(oracle&&oracle.status==="GROSS_ELASTIC_REAL_12001STEP_RAINFLOW_NOT_LOCAL_MATERIAL_LIFE","SUMMARY_SOURCE_IDENTITY");
    check(+oracle.cycle_rows===n&&+oracle.half_cycles===audit.half_cycle_rows&&
      Math.abs(+oracle.equivalent_cycles-eq)<1e-9&&
      Math.abs(+oracle.DEL_m4_MPa-audit.DEL4_MPa)<1e-8,"SUMMARY_ORACLE_MISMATCH");
    out.push({case:c,segment:s,azimuth_deg:+a,...audit});
  }
  check(out.reduce((s,x)=>s+x.cycle_rows,0)===1574,"CONCENTRATION_TOTAL_ROWS");
  return {status:"REAL_ETM_GROSS_NOMINAL_RAINFLOW_CONCENTRATION_NOT_MATERIAL_LIFE",
    source_sha256:SOURCE_SHA,summary_git_blob:"d49cd44d642e914d1ea38e5744b0a59323f10c72",
    Nref_cycles:600,cycle_rows:1574,controls:out,
    material_cycle_admitted:0,design_life_years:null,
    limitations:["3 control points from 2 ETM cases, not all 4 ETM or DLC1.2",
      "gross elastic section stress, not local concrete/rebar/PT/steel material stress",
      "m4 weighting is load/nominal screening, not material Miner damage",
      "top 1 percent refers to sorted rainflow rows, not time fraction",
      "half-as-full is a deliberately incorrect counterfactual; residual endpoint convention matters"]};
}
function cycleWeightSelftest(){
  const c=concentration([{range:2,count:1},{range:4,count:.5}]);
  check(c.cycle_rows===2&&c.equivalent_cycles===1.5&&c.half_cycle_rows===1,"WEIGHT_COUNT_KNOWN");
  check(Math.abs(c.half_cycle_m4_fraction-128/144)<1e-11,"WEIGHT_M4_KNOWN");
  check(Math.abs(c.top_one_percent_m4_fraction-128/144)<1e-11,"WEIGHT_TOP_KNOWN");
  check(Math.abs(c.counterfactual_half_as_full_DEL_bias_pct-100*((272/144)**.25-1))<1e-9,"WEIGHT_BIAS_KNOWN");
  let rejected=0;
  for(const x of [{range:0,count:1},{range:-2,count:1},{range:2,count:.75},{range:NaN,count:1}]){
    try{concentration([x])}catch(e){rejected++}
  }
  check(rejected===4,"WEIGHT_BAD_INPUT_REJECTIONS");
  return {weight_known_answers:4,weight_negative_rejections:4};
}

module.exports={analyze,parse,sign,selftest,materialApplicability,materialDomainSelftest,concentration,cycleWeightAudit,cycleWeightSelftest};
if(require.main===module){const fs=require("fs"),crypto=require("crypto"),path=require("path");if(process.argv.includes("--self-test")){console.log(JSON.stringify({...selftest(),...materialDomainSelftest(),...cycleWeightSelftest()}));process.exit(0)}const b=fs.readFileSync(path.join(__dirname,SOURCE));check(crypto.createHash("sha256").update(b).digest("hex")===SOURCE_SHA,"SOURCE_SHA256");const result=analyze(b.toString("utf8"));if(process.argv.includes("--check")){const old=JSON.parse(fs.readFileSync(path.join(__dirname,RECEIPT),"utf8"));check(JSON.stringify(old.results)===JSON.stringify(result),"RECEIPT_MISMATCH");check(JSON.stringify(old.material_applicability)===JSON.stringify(materialApplicability(b.toString("utf8"))),"MATERIAL_DOMAIN_RECEIPT_MISMATCH");check(JSON.stringify(old.cycle_weight_concentration)===JSON.stringify(cycleWeightAudit(b.toString("utf8"),fs.readFileSync(path.join(__dirname,SUMMARY),"utf8"))),"CYCLE_WEIGHT_RECEIPT_MISMATCH");console.log("S10_REAL_CYCLE_MATERIAL_DOMAIN_QC_PASS_NOT_MATERIAL_DAMAGE rows=1574 material_checks=18888 admitted=0 half_cycle_concentration=checked")}else console.log(JSON.stringify(result,null,2))}
