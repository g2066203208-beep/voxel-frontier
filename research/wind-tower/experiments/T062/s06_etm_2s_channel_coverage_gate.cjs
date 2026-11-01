#!/usr/bin/env node
"use strict";
// Native OpenFAST S06 2s ETM channel inventory; NOT physics verification.
const NODES=[220,426,633],SFX=["FLxt","FLyt","FLzt","MLxt","MLyt","MLzt","TPzi"];
const BASE=["TwrBsFxt","TwrBsFyt","TwrBsFzt","TwrBsMxt","TwrBsMyt","TwrBsMzt"];
function ck(v,s){if(!v)throw Error(s)}
function audit(r){
 ck(r.stage==="S06_2S_REAL_ETM_FOUR_BATCH_NATIVE_OVERLAP_DIAGNOSTIC"&&r.case==="U09p343881_ETM_S06","SOURCE");
 ck(r.TMax_s===2&&r.samples===41&&r.dt_out_s===0.05&&r.status==="NUMERICAL_PARITY_PASS"&&r.failure_count===0&&!r.physical_pass,"GRID_OR_STATUS");
 ck(r.bts_sha256==="ad68a83a63f197c528c07502db8adff883e9c737863ef3c4cab99cfa76052147","BTS");
 const hash=/^[0-9a-f]{64}$/;
 ck(r.outb_sha256.length===4&&r.outb_sha256.every(s=>hash.test(s))&&new Set(r.outb_sha256).size===4,"OUTB_HASHES");
 ck(r.derived_input_sha256.length===4&&r.derived_input_sha256.every(o=>Object.keys(o).length>=5&&Object.values(o).every(s=>hash.test(s))),"INPUT_HASHES");
 ck(r.common_table.length===106&&r.common_channel_count===106,"COMMON_COUNT");
 const m=new Map();
 for(const x of r.common_table){
   ck(!m.has(x.channel)&&!/^TwHt\d+/.test(x.channel)&&typeof x.unit==="string"&&Number.isFinite(x.max_abs_delta)&&x.max_abs_delta>=0&&Number.isFinite(x.max_quant_budget)&&x.max_quant_budget>=0,"COMMON_ROW");
   m.set(x.channel,x.unit);
 }
 for(const x of BASE)ck(m.get(x)===(x.includes("F")?"(kN)":"(kN-m)"),"BASE_"+x);
 const disp=["x","y","z"].flatMap(a=>["i","p","t"].map(b=>"YawBrTD"+a+b));
 const accel=["x","y","z"].map(a=>"YawBrTA"+a+"p");
 for(const x of disp)ck(m.get(x)==="(m)","YAW_DISP_"+x);
 for(const x of accel)ck(m.get(x)==="(m/s^2)","YAW_ACCEL_"+x);
 ck(m.get("YawPos")==="(deg)"&&m.get("YawRate")==="(deg/s)"&&m.get("YawAccel")==="(deg/s^2)","YAW_ROT");
 ck(r.overlap_table.length===21,"OVERLAP_COUNT");
 const seen=new Set();
 for(const x of r.overlap_table){
   const i=NODES.indexOf(x.node),key=x.node+":"+x.suffix;
   ck(i>=0&&x.pair===["1-2","2-3","3-4"][i]&&SFX.includes(x.suffix)&&!seen.has(key),"OVERLAP_TOPOLOGY");
   seen.add(key);
   ck(x.unit===(x.suffix==="TPzi"?"(m)":x.suffix.startsWith("FL")?"(kN)":"(kN-m)")&&Number.isFinite(x.max_abs_delta)&&x.max_abs_delta>=0&&Number.isFinite(x.max_quant_budget)&&x.max_quant_budget>=0,"OVERLAP_UNITS");
 }
 ck(r.common_comparisons===13038&&r.overlap_comparisons===861&&r.max_common_delta===0&&r.max_overlap_delta===0,"PARITY_COUNTS");
 return {stage:"S06/S07",status:"CHANNEL_INVENTORY_PASS_PHYSICAL_HOLD",case:r.case,bts_sha256:r.bts_sha256,outb_sha256:r.outb_sha256,
 observed:{common_non_gage:106,tower_base_six_wrench:BASE,yaw_bearing_displacement_nine:disp,yaw_bearing_acceleration_three:accel,yaw_kinematics:["YawPos","YawRate","YawAccel"],overlap_nodes:NODES,overlap_suffixes:SFX,overlap_TPzi_scalar_count:3,samples:41,common_pair_comparisons:13038,overlap_pair_comparisons:861,max_decoded_difference:0},
 absent:["31-station 3D position","31-station 3D rotation","31-station 3x3 DCM","31-station 3D acceleration","section inertia ownership","100-700s full-state proof"],
 boundary:"Three overlap nodes have one scalar TPzi each; NOT full TP/DCM. YawBrTD/TA and YawPos do NOT provide each tower section orientation. Names and units only, not source-code semantics.",
 next:"Inspect OpenFAST v3.5.3 ElastoDyn OutList and internal coordinate transforms; add only supported verified RP/TP/AL/DCM instrumentation or reconstruction. Test one interface with wrench transport/inertia before production.",
 SOURCE:"Four-OUTB native JSON receipt, raw OUTB not re-read in this audit",REF:"T062 31-gage contract; no new paper",STANDARD:"No new authorized IEC/GB/NB clauses",OFFICIAL:"OpenFAST v3.5.3 native receipt; semantics not revalidated",RUN:"V8 JS audit, not new solver run",FIG:"none",TAB:"106+21 rows",assumptions:"Receipt matches native header, startup 0-2s only",error_budget:"Exact counts/units/topology and inherited packed half-LSB; physical mapping NEED-ESTIMATE",HOLD:"No per-gage full pose/DCM, no inertia attribution, no 100-700s sync or S03/S04 reconciliation",physical_pass:false};
}
function selftest(r){
 audit(r);let rejected=0;
 for(const f of [x=>x.common_table.pop(),x=>x.common_table[0].channel=x.common_table[1].channel,x=>x.common_table.find(z=>z.channel==="TwrBsFxt").unit="(N)",x=>x.common_table.find(z=>z.channel==="YawBrTDxp").channel="BAD",x=>x.overlap_table[0].node=999,x=>x.overlap_table.find(z=>z.suffix==="TPzi").unit="(deg)",x=>x.outb_sha256[1]=x.outb_sha256[0],x=>x.bts_sha256="0".repeat(64),x=>x.physical_pass=true,x=>x.samples=40,x=>x.common_comparisons--,x=>x.max_overlap_delta=.1]){
 const x=JSON.parse(JSON.stringify(r));f(x);try{audit(x)}catch(e){rejected++;continue}throw Error("NEGATIVE_ACCEPTED");
 }
 ck(rejected===12,"TEST_COUNT");return {positive:"PASS",negative_rejections:rejected};
}
module.exports={audit,selftest};
if(require.main===module){
 const fs=require("fs"),crypto=require("crypto"),a=process.argv.slice(2);
 ck(a.length===2&&["--input","--self-test"].includes(a[0]),"USAGE --input|--self-test receipt.json");
 const b=fs.readFileSync(a[1]),r=JSON.parse(b.toString("utf8"));
 console.log(JSON.stringify(a[0]==="--self-test"?selftest(r):{...audit(r),source_receipt_sha256:crypto.createHash("sha256").update(b).digest("hex")},null,2));
}
