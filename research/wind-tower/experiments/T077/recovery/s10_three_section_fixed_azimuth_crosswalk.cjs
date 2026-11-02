#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const NAMES={
  "fixed": "S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv",
  "envelope": "S10_4ETM_31SEG_CONTINUOUS_AZIMUTH_ENVELOPE_20261102.csv",
  "binding": "S10_4ETM_31SEG_NATIVE_ELEMENT_SPATIAL_BINDING_QC_20261031.csv"
};
const SHA256={
  "fixed": "16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b",
  "envelope": "6002f69286eb9941265697732ec7acd961ac6b5757d7472423d91e0374288f21",
  "binding": "05812d6211594bf6187cb68d214544e8fdcf91fc75d591475abc9d4460afe864"
};
function parseCsv(t){const [h,...lines]=t.trim().split(/\r?\n/);const keys=h.split(",");return lines.map(line=>{const v=line.split(",");if(v.length!==keys.length)throw Error("CSV_WIDTH");return Object.fromEntries(keys.map((k,i)=>[k,v[i]]))})}
function derive(fixed,envelopes,bindings){
 if(fixed.length!==1984||envelopes.length!==124||bindings.length!==372)throw Error("SOURCE_ROW_COUNT");
 const rows=[];
 for(const env of envelopes.filter(r=>["CSEG_16","CSEG_17","CSEG_28"].includes(r.segment))){
  const g=fixed.filter(r=>r.case===env.case&&r.segment===env.segment);
  if(g.length!==16||new Set(g.map(x=>x.azimuth_deg)).size!==16)throw Error("FIXED_ANGLE_SET");
  const at180=g.find(r=>Number(r.azimuth_deg)===180);
  const maxdel=g.reduce((p,q)=>Number(q.DEL_m4_MPa)>Number(p.DEL_m4_MPa)?q:p);
  const bind=bindings.find(r=>r.case===env.case&&r.segment===env.segment&&r.gross_control==="TENSION");
  if(!bind||Number(bind.target_local_az_deg)!==180)throw Error("MISSING_BINDING");
  const gap=Number(env.continuous_max_sigma_MPa)-Number(at180.sigma_max_MPa);
  if(gap<0||Math.abs(gap-Number(env.grid16_tension_gap_MPa))>2e-7)throw Error("PEAK_GAP_IDENTITY");
  const angDist=Math.abs(((Number(env.continuous_max_azimuth_deg)-180+540)%360)-180);
  if(angDist>11.25)throw Error("ANGLE_OUTSIDE_NEAREST_CELL");
  if(Number(bind.concrete_axial_gap_m)<=0.1)throw Error("UNEXPECTED_CONCRETE_GAP");
  rows.push([
   env.case,env.segment,env.gage_z_m,env.continuous_max_time_s,env.continuous_max_azimuth_deg,env.continuous_max_sigma_MPa,
   "180",at180.sigma_max_MPa,env.grid16_tension_gap_MPa,at180.DEL_m4_MPa,
   maxdel.azimuth_deg,maxdel.DEL_m4_MPa,String(Math.abs(((Number(maxdel.azimuth_deg)-180+540)%360)-180)),
   bind.d400_concrete_instance,bind.concrete_element_label,bind.concrete_axial_gap_m,
   bind.d400_rebar_instance,bind.d400_rebar_element_label,bind.rebar_axial_gap_m,bind.rebar_az_gap_deg,
   "HOLD_NO_EXACT_OPENFAST_TO_ABAQUS_DCM_NO_ODB_IP"
  ]);
 }
 if(rows.length!==12)throw Error("CONTROL_COUNT");
 return rows;
}
const HEADER="case,segment,gage_z_m,continuous_tension_time_s,continuous_tension_az_deg,continuous_tension_max_MPa,fixed_reference_az_deg,fixed_reference_tension_max_MPa,spatial_peak_gap_MPa,fixed_180deg_DEL4_MPa,max_fixed_DEL4_az_deg,max_fixed_DEL4_MPa,peak_vs_DEL_azimuth_separation_deg,concrete_instance,concrete_element_label,concrete_axial_gap_m,rebar_instance,rebar_element_180deg,rebar_axial_gap_m,rebar_az_gap_deg,admission_status";
function verifyFile(p,expectedHash){const got=crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");if(got!==expectedHash)throw Error("INPUT_SHA256_MISMATCH:"+path.basename(p));}
function selftest(){
 const tiny=parseCsv("a,b\\n1,2\\n3,4\\n".replace(/\\n/g,"\n"));
 assert.equal(tiny.length,2);assert.equal(tiny[1].b,"4");
 assert.throws(()=>parseCsv("a,b\n1,2,3\n"),/CSV_WIDTH/);
 assert.throws(()=>derive([],[],[]),/SOURCE_ROW_COUNT/);
 assert.throws(()=>verifyFile(__filename,"0".repeat(64)),/INPUT_SHA256_MISMATCH/);
 console.log("S10_FIXED_AZIMUTH_SELFTEST_PASS");
}
function main(){
 if(process.argv.includes("--selftest")){selftest();return;}
 const i=process.argv.indexOf("--input-dir"),o=process.argv.indexOf("--out");
 if(i<0||o<0||!process.argv[i+1]||!process.argv[o+1])throw Error("USAGE: --input-dir DIR --out CSV");
 const dir=process.argv[i+1],files=Object.keys(NAMES).map(k=>{const p=path.join(dir,NAMES[k]);verifyFile(p,SHA256[k]);return parseCsv(fs.readFileSync(p,"utf8"))});
 const rows=derive(...files);
 const output=HEADER+"\n"+rows.map(r=>r.join(",")).join("\n")+"\n";
 fs.writeFileSync(process.argv[o+1],output,{encoding:"utf8",flag:"w"});
 console.log(JSON.stringify({rows:rows.length,source_sha256:SHA256,output_sha256:crypto.createHash("sha256").update(output).digest("hex"),stage:"SOURCE_JOIN_ONLY_HOLD"}));
}
if(require.main===module){try{main()}catch(e){console.error(e.message);process.exitCode=1}}
