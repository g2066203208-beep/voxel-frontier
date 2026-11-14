#!/usr/bin/env node
// SOURCE-level gate only. Four archived A/B/C/D CSV streams do NOT establish
// exact same-state 600s operation; reaction resultants are NOT pure wind forces.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dir, "../../../../..");
const rel = {
  manifest:"research/wind-tower/experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv",
  phase:"research/wind-tower/experiments/T077/recovery/S06_S07_4ETM_CROSS_BATCH_PHASE_FINGERPRINT_SUMMARY_20261105.csv",
  inventory:"research/wind-tower/experiments/T062/recomputed-load-fatigue/CHANNEL_INVENTORY.txt",
  short:"research/wind-tower/experiments/T062/S06_ETM_NATIVE_2S_OVERLAP_QC_20261101.json",
  release:"research/wind-tower/experiments/T077/recovery/S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json",
  c0:"research/wind-tower/experiments/T077/recovery/S06_U09p343881_ETM_S06_31GAGE_BATCH_TIMEWISE_RECEIPT_20261101.json",
  c1:"research/wind-tower/experiments/T077/recovery/S06_U11p4_ETM_S04_31GAGE_BATCH_TIMEWISE_RECEIPT_20261102.json",
  c2:"research/wind-tower/experiments/T077/recovery/S06_U19p202140_ETM_S04_31GAGE_BATCH_TIMEWISE_RECEIPT_20261102.json",
  c3:"research/wind-tower/experiments/T077/recovery/S06_U19p202140_ETM_S06_31GAGE_BATCH_TIMEWISE_RECEIPT_20261102.json"
};
const raw=Object.fromEntries(Object.entries(rel).map(([k,p])=>[k,fs.readFileSync(path.join(root,p),"utf8")]));
function gate(s) {
 const a=(v,m)=>{if(!v)throw new Error("SOURCE_REJECT:"+m);};
 const csv=(x)=>{const lines=x.trim().split(/\r?\n/),h=lines.shift().split(",");
   return lines.map(line=>{const vals=line.split(",");a(vals.length===h.length,"CSV_COL");return Object.fromEntries(h.map((key,i)=>[key,vals[i]]));});};
 const names=["U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06"];
 const man=csv(s.manifest),phase=csv(s.phase),short=JSON.parse(s.short),release=JSON.parse(s.release);
 const channels=s.inventory.trim().split(/\r?\n/);
 a(man.length===16&&phase.length===12&&channels.length===296,"COUNTS");
 const map=new Map();
 for(const x of man){const k=x.case+"|"+x.batch;
   a(names.includes(x.case)&&["A","B","C","D"].includes(x.batch)&&!map.has(k),"CASE_BATCH");
   a(Number(x.rows)===(x.batch==="D"?48004:108009)&&/^[a-f0-9]{64}$/.test(x.zip_sha256),"HASH_COUNT");
   map.set(k,x);}
 a(map.size===16,"ALL_BATCHES");
 const rk=["r_diff_Fx_kN","r_diff_Fy_kN","r_diff_Fz_kN","r_diff_Mx_kNm","r_diff_My_kNm","r_diff_Mz_kNm"];
 const seen=new Set(); let lo=1,hi=-1,lagZero=0;
 for(const x of phase){const id=x.case+"|"+x.boundary;
   a(names.includes(x.case)&&["J09","J18","J27"].includes(x.boundary)&&!seen.has(id),"BOUNDARY");
   seen.add(id);a(x.best_lag_zero_6of6==="1","LAG_NOT_ZERO");
   const r=rk.map(k=>Number(x[k]));a(r.every(v=>Number.isFinite(v)&&v>=-1&&v<=1),"INVALID_R");
   lo=Math.min(lo,...r);hi=Math.max(hi,...r);lagZero+=6;}
 a(seen.size===12&&lagZero===72,"SIX_COMPONENT_LAGS");
 a(release.draft===true&&release.asset_count===17&&release.source_level.includes("not original OpenFAST OUTB"),"RELEASE_ONLY_DERIVED");
 a(short.status==="NUMERICAL_PARITY_PASS"&&short.TMax_s===2&&short.samples===41&&short.common_channel_count===106&&short.overlap_comparisons===861&&short.max_common_delta===0&&short.max_overlap_delta===0,"SHORT_NATIVE_ONLY");
 a(channels.some(k=>k.startsWith("RotThrust_"))&&channels.some(k=>k.startsWith("RtAeroCt_")),"ROTOR_CHANNELS");
 a(!channels.some(k=>/^(?:RtAeroF[xyz]|RtAeroM[xyz]|TwrAero|TwrAer|AD_Twr)/.test(k)),"DIRECT_AERO_CHANNEL_FOUND_RECHECK");
 let fullRows=0,within=0;
 for(let i=0;i<names.length;i++){const x=JSON.parse(s["c"+i]);
   a(x.case===names[i]&&x.rows===372031&&x.segments===31&&x.time_start_s===100&&x.time_end_s===700&&x.dt_s===0.05,"FULL_WINDOW");
   a(x.cross_batch_joints_unverified===3&&x.within_batch_joints===27&&x.within_batch_joint_time_samples===324027,"CROSS_BATCH_NOT_CLOSED");
   for(const b of x.source_archives){const y=map.get(x.case+"|"+b.batch);
     a(y&&y.zip_sha256===b.zip_sha256&&y.gzip_sha256===b.gzip_sha256&&Number(y.rows)===b.rows,"ARCHIVE_JOIN");}
   fullRows+=x.rows;within+=x.within_batch_joint_time_samples;}
 a(fullRows===1488124&&within===1296108,"FULL_ROW_CONSERVATION");
 return {status:"SOURCE_RECEIPT_PASS_PHYSICAL_HOLD",cases:4,batches:16,full_history_rows:fullRows,
   within_batch_joint_samples:within,cross_batch_joints:12,cross_batch_lag_zero_components:lagZero,
   observed_corr_min:lo,observed_corr_max:hi,native_2s_common_channels:106,
   native_2s_overlap_sample_comparisons:861,original_wind_output_channels:295,
   exact_600s_same_state_crossbatch_certified:false,full_distributed_aerodynamic_wrench_available:false,
   external_wind_load_physics_admitted:false,formal_DLC12_admitted:false,physical_pass:false};
}
const result=gate(raw);
if(process.argv.includes("--self-test")){
 const tests=[
  ["manifest","U09p343881_ETM_S06,A,","U09p343881_ETM_S06,X,"],
  ["phase",",1,-0.000000000550",",0,-0.000000000550"],
  ["short",'"samples": 41','"samples": 42'],
  ["c0",'"cross_batch_joints_unverified": 3','"cross_batch_joints_unverified": 0'],
  ["release",'"draft": true','"draft": false'],
  ["inventory","RtAeroCp_[-]","RtAeroFxh_[kN]"]
 ];
 for(const [field,oldVal,newVal] of tests){const s={...raw,[field]:raw[field].replace(oldVal,newVal)};
   if(s[field]===raw[field])throw new Error("MUTATION_NOT_APPLIED_"+field);
   let rejected=false;try{gate(s);}catch(err){rejected=String(err).includes("SOURCE_REJECT:");}
   if(!rejected)throw new Error("UNSAFE_ACCEPTANCE_"+field);
 }
 result.negative_mutations_rejected=tests.length;
}
const out=process.argv.indexOf("--output");
if(out>=0){if(!process.argv[out+1])throw new Error("OUTPUT_PATH_MISSING");
 fs.writeFileSync(process.argv[out+1],JSON.stringify(result,null,2)+"\n");}
console.log(JSON.stringify(result,null,2));
