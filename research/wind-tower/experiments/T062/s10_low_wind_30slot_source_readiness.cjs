"use strict";
// S10 low-wind source-only readiness; NO native wind field, controller qualification or DLC1.2.
const INVENTORY={"read_date":"2026-11-04","tree_ref":"28bb857b95b89c1343daee75e37b41aade269a88","tree_api_sha256":"79fcc0fd4ad27d81ea1793519627f09e167910762ccc013f04418b0572bd894f","tree_entries":3278,"tree_truncated":false,"tree_lowwind_named_path_hits":0,"release_api_sha256":"89ed6a82bddc8f78786f66f26d50c13c59f60a6f6253158526d9c7f1edd24ccc","releases_count":2,"s06_draft_release_tag":"windtower-s06-t071-t072-source-archive-20261027","s06_draft_release_asset_count":17,"s06_original_ETM_ZIP_assets":16,"s06_release_lowwind_named_assets":0,"actions_recent_page_sha256":"aee0a6bb600a4bae93946f3658ddefd32c2eef84c42419e9a425245dd57b05a9","actions_recent_page_rows":100,"actions_total_reported":11756,"actions_recent_page_lowwind_named_runs":0,"actions_history_exhausted":false,"scope_note":"Git tree path names + both release asset name lists + only the latest 100 Actions run titles; does not inspect all 11756 run artifacts or archived ZIP members. Absence is scoped, NOT repository-wide proof."};

const {sha256}=require("./s10_dlc12_bin_seed_source_coverage.cjs");
function ok(x,m){if(!x)throw Error(m);}
function parseCsv(s){const l=s.trimEnd().split(/\r?\n/),h=l.shift().split(",");return l.map((x,i)=>{const c=x.split(",");ok(c.length===h.length,"CSV_FIELDS_"+i);return Object.fromEntries(h.map((k,j)=>[k,c[j]]));});}
const HASH={
 era:"e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102",
 coverage:"d4e25023f343ea76f2de5ce90c7d24dd985df770ec9f4747d203391010431e67",
 controller:"be58d33306e6ac101d42b42c7f4d24ea5743662d1a9355aff9862b5a7e0aad45",
 identity:"d57ff9e71b58b531b1aaa357ad7a57a86daf529e061f9d8996cf2453b04a7da5"
};
function build(eraText,coverageText,ctrlText,idText,expectedHashes=HASH,extras=null){
 const input={era:eraText,coverage:coverageText,controller:ctrlText,identity:idText};
 for(const k of Object.keys(HASH))ok(sha256(input[k])===expectedHashes[k],"SOURCE_SHA256_MISMATCH_"+k);
 const era=parseCsv(eraText),coverage=parseCsv(coverageText),ctrl=parseCsv(ctrlText),ids=parseCsv(idText);
 ok(era.length===31&&coverage.length===126&&ctrl.length===18&&ids.length===18,"SOURCE_COUNTS");
 const eraBy=new Map(era.map(x=>[Number(x.bin_lower_mps),x]));
 const ctrlBy=new Map(ctrl.map(x=>[x.case,x]));
 const idBy=new Map(ids.map(x=>[x.case,x]));
 ok(ctrlBy.size===18&&idBy.size===18,"DUPLICATE_SOURCE_CASE");
 const speeds=["U09p343881","U11p4","U19p202140"],seeds=new Map(),configs=new Set();
 for(const sp of speeds){
  for(let s=1;s<=6;s++){
   const label="S"+String(s).padStart(2,"0"),key=sp+"_NTM_"+label,c=ctrlBy.get(key),id=idBy.get(key);
   ok(c&&id,"SOURCE_CASE_MISSING_"+key);
   ok(c.fst_sha256===id.fst_sha256&&c.inflow_sha256===id.inflowwind_sha256,"INPUT_IDENTITY_MISMATCH_"+key);
   ok(c.turb_model==="IECKAI"&&c.turb_IEC_WindType==="NTM","TURB_MODEL_MISMATCH_"+key);
   ok(c.turb_grid_z==="51"&&c.turb_grid_y==="51"&&c.turb_dt_s==="0.025"&&c.turb_analysis_s==="700.0","TURB_GRID_OR_DURATION_MISMATCH_"+key);
   ok(c.fst_TMax_s==="700"&&c.fst_DT_s==="0.0125"&&c.fst_DT_Out_s==="0.05","FST_TIMING_MISMATCH_"+key);
   ok(c.servo_PCMode==="5"&&c.servo_VSContrl==="5"&&c.servo_DLL_FileName==="libdiscon.dll","CONTROLLER_CARD_MISMATCH_"+key);
   ok(!c.bts_archived_sha256&&c.formal_DLC12_reuse_verdict==="HOLD_NOT_VERIFIED","FALSE_BTS_OR_FORMAL_REUSE_"+key);
   ok(id.gage_count==="9"&&id.outb_samples==="12001"&&/^[a-f0-9]{64}$/.test(id.outb_sha256),"ORIGINAL_OUTB_IDENTITY_"+key);
   if(!seeds.has(label))seeds.set(label,c.turb_seed1);
   else ok(seeds.get(label)===c.turb_seed1,"SEED_MISMATCH_ACROSS_BINS_"+label);
   configs.add([c.fst_sha256,c.servo_sha256,c.discon_sha256,c.turb_IECstandard,c.turb_IECturbc,c.turb_IEC_WindType,c.turb_hub_m].join("|"));
  }
 }
 ok(new Set(seeds.values()).size===6&&configs.size===1,"INHERITED_CONFIG_NOT_UNIFORM");
 const header=["candidate_case_NOT_RUN","bin_lower_mps","bin_center_mps_NONNORMATIVE","era5_21y_hours","era5_p_conditional_4_to_25","seed_label","historical_seed1_CANDIDATE_ONLY","inherited_turb_model","inherited_grid","inherited_turb_dt_s","inherited_analysis_s","inherited_fst_dt_s","inherited_fst_output_dt_s","source_OUTB_sha256","new_TurbSim_input_sha256","new_BTS_sha256","new_OUTB_sha256","readiness_status"];
 const rows=[],data=[],expectedHours={4:26927,5:24769,6:19994,7:14467,8:9245};
 for(let lo=4;lo<=8;lo++){
  const e=eraBy.get(lo),items=coverage.filter(x=>Number(x.bin_lower_mps)===lo);
  ok(e&&Number(e.hours)===expectedHours[lo]&&items.length===6,"LOW_WIND_BIN_SOURCE_"+lo);
  for(let s=1;s<=6;s++){
   const label="S"+String(s).padStart(2,"0"),x=items.find(x=>x.seed_id===label);
   ok(x&&x.source_coverage_status==="NO_ARCHIVED_NTM_SOURCE"&&x.formal_DLC12_status==="NOT_VALIDATED"&&!x.outb_sha256&&!x.fst_sha256&&!x.historical_case_id,"UNVERIFIED_ARCHIVE_ASSERTION_"+lo+"_"+label);
   ok(Number(x.era5_21y_hours)===Number(e.hours)&&Number(x.planned_bin_center_mps_NONNORMATIVE)===lo+0.5,"BIN_OR_HOUR_JOIN_"+lo+"_"+label);
   const row=["U"+String(lo).padStart(2,"0")+"p5_NTM_"+label,lo,(lo+0.5).toFixed(1),e.hours,e.p_conditional_4_to_25,label,seeds.get(label),"IECKAI","51x51","0.025","700.0","0.0125","0.05","","","","","NEED_TURBSIM_BTS_CONTROLLER_CUTIN_AND_DLC12_VALIDATION"];
   data.push(row);rows.push(row.join(","));
  }
 }
 ok(rows.length===30&&Object.values(expectedHours).reduce((a,b)=>a+b,0)===95402,"LOW_WIND_COUNT_OR_HOURS");
 const csv=header.join(",")+"\n"+rows.join("\n")+"\n";
 const receipt={
  SOURCE:"Direct GitHub-branch ERA5 derived 31-bin CSV, 126-slot source matrix, original 18 NTM controller/input CSV and original 18 NTM FST/OUTB identity CSV; scoped REST Git tree/release/Actions metadata inventory",
  READING_LEVEL:"Derived CSV direct bytes and inherited original-OUTB SHA receipts; Git tree path names, release asset names and recent 100 Actions run titles only. No 4-8m/s original BTS/OUTB read or recovered; full historical Actions artifact scan NOT DONE.",
  REF:"T062 original 18NTM source contract; 12-stage critical path and prior S10 conditional-load-m4 diagnostic",
  STANDARD:"IEC 61400-1/6 2025 licensed text NOT READ; 1m/s centers, six seeds, cut-in and operating regime are candidate research design NOT clause acceptance",
  OFFICIAL:"GitHub REST repository tree, releases and Actions metadata; OpenFAST/TurbSim source identities inherited, NOT native controller or formal IEC validation",
  RUN:"Node source-only deterministic 30-slot construction with 6 tamper rejection tests; no TurbSim, OpenFAST or Abaqus production run",
  FIG:"0",TAB:"30 proposed source-missing low-wind NTM slots; no wind-field or material response figures",
  input_sha256:extras?{...HASH,discon_receipt:CONTROLLER_AUDIT_HASH.discon_receipt,reference_servo:CONTROLLER_AUDIT_HASH.reference_servo}:HASH,inventory_snapshot:INVENTORY,
  results:{bins:[4,5,6,7,8],slot_count:30,unique_candidate_seed1:[...seeds.values()],era5_21y_hours:95402,diagnostic_operating_hours:106900,share_of_diagnostic_operating_hours:95402/106900,original_lowwind_outb_found_in_checked_sources:0,formal_dlc12_verified_slots:0,original_controller_source_configs_checked:18,original_18ntm_gage_count:9},
  controller_cutin_evidence:extras?controllerCutInAudit(eraText,ctrlText,extras.disconReceiptText,extras.referenceServoText):undefined,
   cut_in_sensitivity:{status:"SCENARIO_ONLY_NOT_ACTUAL_CONTROLLER_CUT_IN",bin_policy:"Whole 1m/s ERA5 bins with hypothetical integer cut-in k=4..9; no within-bin interpolation, no controller or IEC approval",scenarios:cutInSensitivity(era)},
  assumptions:"Candidate lowwind centers 4.5..8.5m/s; historical seed1 reused across speeds ONLY as a proposed paired design; original 51x51/0.025s/700s and FST 0.0125s/0.05s settings are historical metadata, not approved lowwind inputs. Controller binary and below/near cut-in operating state unverified.",
  ERROR_BUDGET:"Integer ERA5 hours exact; conditional probability prior 12-digit decimal rounded <=0.5e-12 per bin; proposed wind centers differ from physical turbulent realizations; physical/control/turbulence model errors NOT ESTIMATED. Git tree/release/Actions name search cannot prove missing archive members.",
  HOLD:"No verified 4-8m/s 158m NTM original OUTB/BTS, original BTS bytes unarchived even for 18 prior cases; lowwind controller cut-in, wind-bin IEC2025, source input versions, 31-segment full time series, material stress and DLC1.2 unresolved.",
  tests:{negative_rejections:extras?10:6,source_locked:true,physical_pass:false,material_fatigue_pass:false},stage_passed:0
 };
 return {csv,receipt:JSON.stringify(receipt,null,2)+"\n"};
}
function cutInSensitivity(era){
 const expectedEligible=[106900,79973,55204,35210,20743,11498];
 const expectedMissing=[95402,68475,43706,23712,9245,0];
 const result=[];
 for(let k=4;k<=9;k++){
  const eligible=era.filter(r=>Number(r.bin_lower_mps)>=k&&Number(r.bin_lower_mps)<25).reduce((s,r)=>s+Number(r.hours),0);
  const missing=era.filter(r=>Number(r.bin_lower_mps)>=k&&Number(r.bin_lower_mps)<=8).reduce((s,r)=>s+Number(r.hours),0);
  ok(eligible===expectedEligible[k-4]&&missing===expectedMissing[k-4],"CUT_IN_SOURCE_HOURS_ORACLE_"+k);
  ok(eligible>0&&missing<=eligible,"CUT_IN_DENOMINATOR_"+k);
  result.push({hypothetical_cut_in_mps_NONNORMATIVE:k,eligible_era5_hours_4_to_25:eligible,uncovered_lowwind_hours_4_to_8:missing,uncovered_share_of_eligible:missing/eligible,uncovered_candidate_slots:6*Math.max(0,9-k)});
 }
 ok(result.length===6&&result[0].uncovered_share_of_eligible>result[5].uncovered_share_of_eligible,"CUT_IN_SCENARIO_ORDER");
 return result;
}

const CONTROLLER_AUDIT_HASH={
 discon_receipt:"953d64614acca6278bba3cf79279c31c9adff8137734c190e29f2e376381e6c6",
 reference_servo:"266fed7bd2ab3084594fab29c6aae437f8e244154fd6b1c3e3c48e8b5f969654"
};
function controllerCutInAudit(eraText,ctrlText,disconReceiptText,referenceServoText,locks=CONTROLLER_AUDIT_HASH){
 ok(sha256(disconReceiptText)===locks.discon_receipt,"DISCON_RECEIPT_SHA");
 ok(sha256(referenceServoText)===locks.reference_servo,"REFERENCE_SERVO_SHA");
 ok(sha256(eraText)===HASH.era&&sha256(ctrlText)===HASH.controller,"SOURCE_CSV_SHA");
 const d=JSON.parse(disconReceiptText),params=d.parsed_discon_parameters||{};
 const cases=parseCsv(ctrlText),era=parseCsv(eraText);
 ok(d.recognized_parameter_count===26&&Object.keys(params).length===26,"DISCON_PARSED_KEY_COUNT");
 ok(cases.length===18&&era.length===31,"SOURCE_ROWS");
 const ids=new Set(cases.map(x=>x.case));
 ok(ids.size===18&&new Set(cases.map(x=>x.discon_sha256)).size===1,"DISCON_CASE_UNIQUENESS");
 ok(cases.every(x=>x.discon_sha256===d.input_sha256.original_discon),"DISCON_SOURCE_MISMATCH");
 ok(new Set(cases.map(x=>x.servo_sha256)).size===1&&new Set(cases.map(x=>x.fst_sha256)).size===1,"FST_SERVO_IDENTITY");
 ok(cases.every(x=>x.servo_PCMode==="5"&&x.servo_VSContrl==="5"),"HISTORICAL_DLL_MODE");
 ok(params.VS_MinOMSpd.raw==="36.60000000000"&&/rad\/s/.test(params.VS_MinOMSpd.comment),"MIN_OM_SPD_UNIT");
 ok(params.WE_GearboxRatio.raw==="50.0"&&params.VS_TSRopt.raw==="7.50","REGION2_IDENTITY");
 const knownCutInKeys=Object.keys(params).filter(k=>/cut.?in|cut.?out|wind.?start|wind.?stop/i.test(k));
 ok(knownCutInKeys.length===0,"CUT_IN_KEY_IN_PARSED_SUBSET");
 const ref={};
 for(const line of referenceServoText.split(/\r?\n/)){
  const m=line.match(/^\s*(\S+)\s+(PCMode|VSContrl|GenTiStr|GenTiStp|TimGenOn|TimGenOf)\b/);
  if(m){ok(!(m[2] in ref),"REFERENCE_DUPLICATE_"+m[2]);ref[m[2]]=m[1];}
 }
 ok(ref.PCMode==="0"&&ref.VSContrl==="1"&&ref.GenTiStr==="True"&&ref.GenTiStp==="True"&&ref.TimGenOn==="0"&&ref.TimGenOf==="9999.9","REFERENCE_NOT_HISTORICAL_DLL_MODE");
 const expected=[26927,24769,19994,14467,9245],bins=[];
 for(let i=0;i<5;i++){
  const row=era.find(x=>x.bin_lower_mps===String(i+4));
  ok(row&&Number(row.hours)===expected[i],"ERA_LOW_BIN_"+i);
  bins.push({bin_mps:String(i+4)+"-"+String(i+5),hours_2005_2025:expected[i],share_of_missing_lowwind_hours:expected[i]/95402,source_BTS_OUTB:"MISSING"});
 }
 ok(bins.reduce((s,x)=>s+x.hours_2005_2025,0)===95402,"LOW_BIN_SUM");
 return {
  verdict:"ACTUAL_CUT_IN_NOT_IDENTIFIED_FROM_ARCHIVED_18_CASE_INPUT_SUBSET",
  source_reading_level:"Current GitHub derived ERA5 CSV + 18 original-input SHA receipt CSV + prior original 17600-byte DISCON parsed receipt (original DISCON bytes not reread this run) + direct DIFFERENT v3.3 reference ServoDyn text; no historical 18 ServoDyn raw ZIP bytes or controller DLL executed",
  original_discon_sha256:d.input_sha256.original_discon,
  original_18case_fst_sha256:cases[0].fst_sha256,
  original_18case_servodyn_sha256:cases[0].servo_sha256,
  original_18case_controller_mode:{PCMode:5,VSContrl:5},
  original_discon_parsed_keys:26,explicit_wind_cut_in_keys_in_parsed_subset:knownCutInKeys,
  VS_MinOMSpd_rad_s:Number(params.VS_MinOMSpd.raw),
  WE_GearboxRatio:Number(params.WE_GearboxRatio.raw),
  VS_TSRopt:Number(params.VS_TSRopt.raw),
  WARNING:"VS_MinOMSpd is generator angular speed in an optimal-mode region, NOT wind-speed cut-in. No wind-speed cut-in, hysteresis, startup/shutdown threshold, or verified runtime state is established by these 26 parsed keys.",
  different_reference_v330_servo_sha256:sha256(referenceServoText),
  different_reference_modes:ref,
  reference_identity_warning:"Archived v3.3 linearization reference has PCMode=0, VSContrl=1; historical v3.5 NTM has 5/5. Reference startup/shutdown timers MUST NOT be copied to historical NTM.",
  missing_lowwind_bins_ranked_by_ERA5_hours:bins,
  top_2_bin_hours:51696,top_2_share_of_missing:51696/95402,
  top_3_bin_hours:71690,top_3_share_of_missing:71690/95402,
  formal_DLC12_slots_passed:0,stage_passed:0,
  HOLD:"Actual historical 158m ServoDyn generator startup/stop settings and DLL runtime wind-speed transition are not in available extracted fields; original 4-8m/s BTS/OUTB missing; no licensed IEC2025 clauses read."
 };
}
function controllerNegativeTests(era,ctrl,discon,reference){
 const mutate=(f)=>{const d=JSON.parse(discon);f(d);return JSON.stringify(d);};
 const c1=mutate(d=>d.input_sha256.original_discon="0".repeat(64));
 const c2=mutate(d=>d.parsed_discon_parameters.VS_MinOMSpd.raw="4.00000000000");
 const c3=reference.replace(/^0(\s+PCMode\b)/m,"5$1").replace(/^1(\s+VSContrl\b)/m,"5$1");
 const trials=[
  ()=>controllerCutInAudit(era,ctrl,c1,reference,{discon_receipt:sha256(c1),reference_servo:sha256(reference)}),
  ()=>controllerCutInAudit(era,ctrl,c2,reference,{discon_receipt:sha256(c2),reference_servo:sha256(reference)}),
  ()=>controllerCutInAudit(era,ctrl,discon,c3,{discon_receipt:sha256(discon),reference_servo:sha256(c3)}),
  ()=>controllerCutInAudit(era.replace("4,5,26927,","4,5,26928,"),ctrl,discon,reference)
 ];
 trials.forEach((f,i)=>{let rejected=false;try{f();}catch(e){rejected=true;}ok(rejected,"CONTROLLER_NEGATIVE_ACCEPTED_"+i);});
 return trials.length;
}

function negativeTests(era,coverage,controller,identity){
 const cases=[
  [era.replace("4,5,26927,","4,5,26928,"),coverage,controller,identity],
  [era,coverage.replace("NO_ARCHIVED_NTM_SOURCE","ARCHIVED_NTM_SCREEN_ONLY"),controller,identity],
  [era,coverage,controller.replace(",104729,RanLux,",",104730,RanLux,"),identity],
  [era,coverage,controller.replace(",51,51,0.025,",",41,51,0.025,"),identity],
  [era,coverage,controller,identity.replace(",12001,9,",",12000,9,")],
  [era,coverage.split("\n").filter(x=>!x.startsWith("4,5,4.5,26927,0.146278791830,0.251889616464,1281.402216428,S06,")).join("\n"),controller,identity]
 ];
 cases.forEach((x,i)=>{ok(x.some((s,j)=>s!==[era,coverage,controller,identity][j]),"MUTATION_NOOP_"+i);let rejected=false;try{if(i===0)build(...x);else{const keys=["era","coverage","controller","identity"],unlocked=Object.fromEntries(keys.map((k,j)=>[k,sha256(x[j])]));build(...x,unlocked);}}catch(e){rejected=true;}ok(rejected,"NEGATIVE_ACCEPTED_"+i);});
 return cases.length;
}
module.exports={build,negativeTests,controllerCutInAudit,controllerNegativeTests};
if(require.main===module){
 const fs=require("fs"),path=require("path"),dir=__dirname;
 const names=["S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv","S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv","S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv","S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv"];
 const inputs=names.map(n=>fs.readFileSync(path.join(dir,n),"utf8"));
  const disconReceiptText=fs.readFileSync(path.join(dir,"S07_18NTM_DISCON_VS_OPERATING_RECEIPT_20261101.json"),"utf8");
  const referenceServoText=fs.readFileSync(path.join(dir,"../../references/baselines-and-site-20261004/openfast-v330-adaptation/0Linearization/Campbell_Servo/Control/DTU_10MW_RWT_ServoDyn_ws14.0.dat"),"utf8");
  const v=build(...inputs,HASH,{disconReceiptText,referenceServoText});
  const n=negativeTests(...inputs),cn=controllerNegativeTests(inputs[0],inputs[2],disconReceiptText,referenceServoText);
  ok(cn===4,"CONTROLLER_NEGATIVE_COUNT");
 ok(n===6,"NEGATIVE_COUNT");
 if(process.argv.includes("--check")){
  ok(fs.readFileSync(path.join(dir,"S10_LOW_WIND_30SLOT_SOURCE_READINESS_20261104.csv"),"utf8")===v.csv,"COMMITTED_CSV_MISMATCH");
  ok(fs.readFileSync(path.join(dir,"S10_LOW_WIND_30SLOT_SOURCE_READINESS_20261104.json"),"utf8")===v.receipt,"COMMITTED_RECEIPT_MISMATCH");
 }else{process.stdout.write(v.csv);}
 console.log("S10_LOW_WIND_30SLOT_SOURCE_READINESS_QC_PASS_NOT_DLC12 negative_tests="+(n+cn)+" source_missing=30");
}
