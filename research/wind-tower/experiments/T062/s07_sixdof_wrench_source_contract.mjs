#!/usr/bin/env node
"use strict";
import fs from "node:fs";
import crypto from "node:crypto";

const SOURCE_SHA="95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f";
const KEYS=["Fx","Fy","Fz","Mx","My","Mz"];
function must(v,m){if(!v)throw Error(m)}
function dot(a,b){return a.reduce((s,x,i)=>s+x*b[i],0)}
function cross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]}
function mv(R,x){return R.map(row=>dot(row,x))}
function tr(R){return R[0].map((_,i)=>R.map(row=>row[i]))}
function det(R){return dot(R[0],cross(R[1],R[2]))}
function checkRotation(R){
 must(Array.isArray(R)&&R.length===3&&R.every(x=>Array.isArray(x)&&x.length===3&&x.every(Number.isFinite)),"BAD_ROTATION_SHAPE");
 const Rt=tr(R);for(let i=0;i<3;i++)for(let j=0;j<3;j++)must(Math.abs(dot(R[i],R[j])-(i===j?1:0))<1e-10,"NONORTHOGONAL_ROTATION");
 must(Math.abs(det(R)-1)<1e-10,"REFLECTION_OR_BAD_DETERMINANT");
 return Rt;
}
// r_A = vector from original reference point P to target Q in frame A.
// [F_B; M_B(Q)] = [R F_A; R (M_A(P) - r_A x F_A)].
// This is a free-body wrench, not a nodal load or an inertial-force correction.
function transform(F,M,R,r){
 checkRotation(R);must(F.length===3&&M.length===3&&r.length===3&&[...F,...M,...r].every(Number.isFinite),"BAD_VECTOR");
 const arm=cross(r,F);
 return {F:mv(R,F),M:mv(R,M.map((x,i)=>x-arm[i]))};
}
function approx(a,b,eps){must(a.length===b.length&&a.every((v,i)=>Math.abs(v-b[i])<=eps*Math.max(1,Math.abs(v),Math.abs(b[i]))),"NUMERIC_MISMATCH")}
function parseCSV(s){
 const lines=s.trimEnd().split(/\r?\n/),h=lines.shift().split(",");
 must(new Set(h).size===h.length,"DUPLICATE_HEADER");
 for(const k of ["case","source_archive","outb_sha256","channel","unit","n_samples","t0_s","t1_s","dt_s","mean","quantization_half_step_unit"])must(h.includes(k),"MISSING_"+k);
 return lines.map((line,i)=>{const v=line.split(",");must(v.length===h.length,"BAD_CSV_WIDTH_"+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]))});
}
function build(rows){
 must(rows.length===1080,"BAD_SOURCE_ROWS");
 const seen=new Set(),cases=new Map();
 for(const x of rows){
  const key=x.case+"|"+x.channel;must(!seen.has(key),"DUPLICATE_CHANNEL");seen.add(key);
  must(/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(x.case),"BAD_CASE");
  must(/^[a-f0-9]{64}$/.test(x.outb_sha256),"BAD_OUTB_SHA");
  must(+x.n_samples===12001&&+x.t0_s===100&&+x.t1_s===700&&+x.dt_s===0.05,"BAD_GRID");
  must(Number.isFinite(+x.mean)&&x.mean.trim()!==""&&Number.isFinite(+x.quantization_half_step_unit)&&+x.quantization_half_step_unit>=0,"BAD_MEAN_OR_QUANTIZATION");
  if(!cases.has(x.case))cases.set(x.case,[]);
  cases.get(x.case).push(x);
 }
 must(cases.size===18&&[...cases.values()].every(a=>a.length===60),"CASE_COVERAGE");
 const header=["case","station","native_frame","source_outb_sha256","source_archive",...KEYS.map(k=>k+"_SI"),...KEYS.map(k=>k+"_halfLSB_SI"),"time_window_s","status"];
 const lines=[header.join(",")],I=[[1,0,0],[0,1,0],[0,0,1]],r=[0,0,0];
 let maxResidual=0;
 for(const [caseName,a] of [...cases].sort((x,y)=>x[0].localeCompare(y[0]))){
  const m=new Map(a.map(x=>[x.channel,x]));must(new Set(a.map(x=>x.outb_sha256)).size===1,"INCONSISTENT_CASE_OUTB");
  for(let g=0;g<10;g++){
   const prefix=g===0?"TwrBs":"TwHt"+g, suffixes=g===0?["Fxt","Fyt","Fzt","Mxt","Myt","Mzt"]:["FLxt","FLyt","FLzt","MLxt","MLyt","MLzt"];
   const vals=[],err=[];
   for(let k=0;k<6;k++){
    const x=m.get(prefix+suffixes[k]);must(x,"MISSING_SIX_COMPONENT_"+caseName+"_"+prefix);
    must(x.unit===(k<3?"(kN)":"(kN-m)"),"WRONG_COMPONENT_UNIT");
    vals.push(+x.mean*1000);err.push(+x.quantization_half_step_unit*1000);
   }
   const t=transform(vals.slice(0,3),vals.slice(3),I,r);
   for(let k=0;k<3;k++)maxResidual=Math.max(maxResidual,Math.abs(t.F[k]-vals[k]),Math.abs(t.M[k]-vals[k+3]));
   const row=[caseName,g===0?"TwrBs":"TwHt"+g,"OpenFAST_output_native_UNVERIFIED_COORDINATE_BASIS",a[0].outb_sha256,a[0].source_archive,
    ...vals.map(x=>x.toFixed(6)),...err.map(x=>x.toFixed(6)),"100-700","SOURCE_MEAN_ONLY_NO_TIME_SERIES_NO_PHYSICAL_MAPPING"];
   lines.push(row.join(","));
  }
 }
 must(lines.length===181&&maxResidual===0,"IDENTITY_INVARIANCE_FAILED");
 return {csv:lines.join("\n")+"\n",stats:{input_rows:rows.length,cases:cases.size,stations_per_case:10,output_vectors:180,identity_max_residual_SI:0,source_sha256:SOURCE_SHA,physical_pass:false}};
}
function selfTest(){
 const I=[[1,0,0],[0,1,0],[0,0,1]],R=[[0,-1,0],[1,0,0],[0,0,1]],r=[0,2,0];
 const v=transform([100,0,0],[0,0,0],R,r);
 approx(v.F,[0,100,0],1e-12);approx(v.M,[0,0,200],1e-12);
 const rinv=mv(R,r).map(x=>-x),back=transform(v.F,v.M,tr(R),rinv);
 approx(back.F,[100,0,0],1e-12);approx(back.M,[0,0,0],1e-12);
 const a=transform([11,-13,17],[19,-23,29],R,[2,-3,5]);
 const b=transform(a.F,a.M,tr(R),mv(R,[2,-3,5]).map(x=>-x));
 approx(b.F,[11,-13,17],1e-12);approx(b.M,[19,-23,29],1e-12);
 let rejected=0;
 for(const fn of [()=>transform([1,2,3],[4,5,6],[[1,0,0],[0,2,0],[0,0,1]],[0,0,0]),
 ()=>transform([1,2,3],[4,5,6],[[-1,0,0],[0,1,0],[0,0,1]],[0,0,0]),
 ()=>parseCSV("case,case\nA,B\n"),()=>parseCSV("case,mean\nA\n")]){try{fn()}catch{rejected++}}
 must(rejected===4,"NEGATIVE_TEST_FAILED");
 return {analytic_arm_Nm:200,round_trip_max_relative_tolerance:1e-12,negative_rejections:4};
}


const MEAN_SHA="ee051cdc35ef3bfdc1ec2f9e053353ca6ba10f9f27079253830736fac9315f97";
// Local tower gage axes rotate with tower deflection; transform EACH sample,
// not the average in a possibly moving local frame. NUMERIC CONTRACT ONLY.
function transformHistory(samples){
 must(Array.isArray(samples)&&samples.length>=2,"MISSING_SYNCHRONOUS_HISTORY");
 let prev=null,dt=null;const SF=[0,0,0],SM=[0,0,0];
 for(const s of samples){
  must(s&&Number.isFinite(s.t_s),"BAD_TIME");
  must(typeof s.frame_source==="string"&&s.frame_source.length>0&&typeof s.point_source==="string"&&s.point_source.length>0,"MISSING_FRAME_OR_POINT_PROVENANCE");
  if(prev!==null){const step=s.t_s-prev;must(step>0,"NONMONOTONIC_TIME");
   if(dt===null)dt=step;else must(Math.abs(step-dt)<=1e-10*Math.max(1,dt),"UNSYNCED_TIME_GRID");}
  prev=s.t_s;
  must(Array.isArray(s.F_SI)&&Array.isArray(s.M_SI)&&Array.isArray(s.R_A_to_B)&&Array.isArray(s.r_PQ_A_m),"MISSING_PER_SAMPLE_WRENCH_OR_ROTATION");
  const w=transform(s.F_SI,s.M_SI,s.R_A_to_B,s.r_PQ_A_m);
  for(let k=0;k<3;k++){SF[k]+=w.F[k];SM[k]+=w.M[k]}
 }
 return {n:samples.length,dt_s:dt,mean_F_SI:SF.map(x=>x/samples.length),mean_M_SI:SM.map(x=>x/samples.length),physical_pass:false};
}
function meanGate(s){
 const lines=s.trimEnd().split(/\r?\n/),h=lines.shift().split(",");
 must(new Set(h).size===h.length,"MEAN_DUPLICATE_HEADER");
 for(const k of ["case","station","native_frame","status","source_outb_sha256"])must(h.includes(k),"MEAN_MISSING_"+k);
 const ix=k=>h.indexOf(k),seen=new Set();let refused=0;
 for(const [i,line] of lines.entries()){
  const a=line.split(",");must(a.length===h.length,"MEAN_BAD_WIDTH_"+i);
  const id=a[ix("case")]+"|"+a[ix("station")];must(!seen.has(id),"MEAN_DUPLICATE_STATION");seen.add(id);
  must(/^[a-f0-9]{64}$/.test(a[ix("source_outb_sha256")]),"MEAN_BAD_OUTB_SHA");
  must(a[ix("native_frame")]==="OpenFAST_output_native_UNVERIFIED_COORDINATE_BASIS"&&
       a[ix("status")]==="SOURCE_MEAN_ONLY_NO_TIME_SERIES_NO_PHYSICAL_MAPPING","MEAN_UNEXPECTED_PHYSICAL_CLAIM");
  refused++;
 }
 must(refused===180,"MEAN_EXPECTED_180_UNVERIFIED");
 return {real_source_vectors:180,physical_mapping_refused:refused,physical_pass:false,reason:"NO_PER_SAMPLE_LOCAL_FRAME_AND_REFERENCE_POINT"};
}
function frameSelfTest(){
 const c=Math.cos(Math.PI/6),s=Math.sin(Math.PI/6);
 const R1=[[c,-s,0],[s,c,0],[0,0,1]],R2=[[c,s,0],[-s,c,0],[0,0,1]];
 const sample=(t,R)=>({t_s:t,F_SI:[100,0,0],M_SI:[0,0,0],R_A_to_B:R,r_PQ_A_m:[0,2,0],frame_source:"SYNTHETIC_ONLY",point_source:"SYNTHETIC_ONLY"});
 const a=sample(0,R1),b=sample(0.05,R2),v=transformHistory([a,b]);
 must(Math.abs(v.mean_F_SI[0]-100*c)<1e-10&&Math.abs(v.mean_F_SI[1])<1e-10,"ROTATING_FRAME_MEAN_FAILED");
 must(Math.abs(v.mean_M_SI[2]-200)<1e-10,"MOMENT_ARM_MEAN_FAILED");
 let rejected=0;
 for(const bad of [
  [{...a,R_A_to_B:null},b],[a,{...b,t_s:0}],[a,{...b,frame_source:""}],
  [a,{...b,R_A_to_B:[[1,0,0],[0,2,0],[0,0,1]]}],[a,b,{...b,t_s:0.11}]
 ]){try{transformHistory(bad)}catch{rejected++}}
 must(rejected===5,"FRAME_NEGATIVE_TEST_FAILED");
 return {synthetic_samples:2,dt_s:0.05,correct_mean_global_Fx_N:v.mean_F_SI[0],
  invalid_fixed_identity_mean_Fx_N:100,bias_if_fixed_identity_N:100-v.mean_F_SI[0],
  correct_mean_Mz_Nm:v.mean_M_SI[2],negative_rejections:rejected,physical_pass:false};
}

function sha(s){return crypto.createHash("sha256").update(s).digest("hex")}
function main(){
 const a=process.argv.slice(2);
 if(a.includes("--self-test")){console.log("S07_SELFTEST_PASS "+JSON.stringify({...selfTest(),frame_test:frameSelfTest()}));return}
 const get=k=>{const i=a.indexOf(k);must(i>=0&&i+1<a.length,"MISSING_ARG_"+k);return a[i+1]};
 if(a.includes("--frame-gate")){const bytes=fs.readFileSync(get("--mean-csv"));must(sha(bytes)===MEAN_SHA,"MEAN_SOURCE_SHA256_MISMATCH");console.log("S07_REAL_MEAN_FRAME_HOLD "+JSON.stringify({...meanGate(bytes.toString("utf8")),frame_test:frameSelfTest()}));return}
 const source=fs.readFileSync(get("--source"));
 must(sha(source)===SOURCE_SHA,"SOURCE_SHA256_MISMATCH");
 const result=build(parseCSV(source.toString("utf8")));
 const out=get("--out");fs.writeFileSync(out,result.csv);
 console.log("S07_SOURCE_MEAN_QC_PASS "+JSON.stringify({...result.stats,output_sha256:sha(Buffer.from(result.csv)),self_test:selfTest()}));
}
main();
