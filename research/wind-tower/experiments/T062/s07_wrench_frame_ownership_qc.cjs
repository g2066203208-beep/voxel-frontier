"use strict";
// S07 conditional rigid-wrench transport and source-ownership gate.
// Real inputs: SHA-locked OpenFAST v3.5.3 native 2 s ETM OUTB-derived JSON.
// Rotation matrices here are HYPOTHETICAL sensitivity scenarios, NOT recovered ElastoDyn t-axes.
// FL/ML are sectional resultants INCLUDING gravity and inertial contributions:
// official ElastoDyn.f90 v3.5.3 L1165-1206 (FTTower - MassT*(Gravity*z2+LinAccET)).
// No Abaqus loading, fatigue life, earthquake result, or standards PASS follows from this test.
const SOURCE_SHA="a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3";
const OUTB_SHA="c3f40b400f827fbcdd49e9a63f5bb2295a5c0f368a9644b90b591d66b7bb0242";
const ZIP_SHA="7fcae2bf57be571cacc6d3d9b82f1a254257ce59fdb946a1cfb56d3639eb9f1b";
function ck(x,m){if(!x)throw Error(m);}
function vec(x){ck(Array.isArray(x)&&x.length===3&&x.every(Number.isFinite),"INVALID_VECTOR");return x;}
function dot(a,b){return a.reduce((s,v,i)=>s+v*b[i],0);}
function cross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
function add(a,b){return a.map((v,i)=>v+b[i]);}
function sub(a,b){return a.map((v,i)=>v-b[i]);}
function norm(a){return Math.sqrt(dot(a,a));}
function mul(Q,v){return Q.map(row=>dot(row,v));}
function transpose(Q){return Q[0].map((_,i)=>Q.map(row=>row[i]));}
function det(Q){return dot(Q[0],cross(Q[1],Q[2]));}
function orthogonal(Q){
 ck(Array.isArray(Q)&&Q.length===3&&Q.every(row=>Array.isArray(row)&&row.length===3&&row.every(Number.isFinite)),"DCM_SHAPE");
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)
  ck(Math.abs(dot(Q[i],Q[j])-(i===j?1:0))<1e-10,"DCM_ORTHOGONAL");
 ck(Math.abs(det(Q)-1)<1e-10,"DCM_RIGHT_HANDED");
 return true;
}
function Ry(deg){
 ck(Number.isFinite(deg)&&Math.abs(deg)<=180,"ANGLE_DOMAIN");
 const t=deg*Math.PI/180,c=Math.cos(t),s=Math.sin(t);
 return [[c,0,s],[0,1,0],[-s,0,c]];
}
function transport(F,M,rA,rB,Q){
 vec(F);vec(M);vec(rA);vec(rB);orthogonal(Q);
 const f=mul(Q,F),m=add(mul(Q,M),cross(sub(rA,rB),f));
 return {F:f,M:m,delta_moment:cross(sub(rA,rB),f)};
}
// Rigorous algebraic upper bound for a hypothetical global-y frame rotation.
// ||(Ry(theta)-I)v|| = 2 sin(|theta|/2) hypot(v_x,v_z).
// Delta M_B = (Ry-I)M + (rA-rB) cross (Ry-I)F, so triangle inequality
// bounds moment drift. TP origins are in a common inertial frame.
function rotationBoundY(F,M,rA,rB,deg){
 vec(F);vec(M);vec(rA);vec(rB);Ry(deg);
 const q=2*Math.sin(Math.abs(deg)*Math.PI/360);
 const f=q*Math.hypot(F[0],F[2]);
 const m=q*Math.hypot(M[0],M[2])+norm(sub(rA,rB))*f;
 return {force_bound_kN:f,moment_bound_kNm:m};
}
function back(result,rA,rB,Q){
 orthogonal(Q);
 const inv=transpose(Q),f=mul(inv,result.F);
 const m=mul(inv,sub(result.M,cross(sub(rA,rB),result.F)));
 return {F:f,M:m};
}
function close(a,b,tol=1e-8){return a.every((v,i)=>Math.abs(v-b[i])<=tol*Math.max(1,Math.abs(v),Math.abs(b[i])));}
function gate(data){
 ck(data&&data.stage==="S06/S07"&&data.case==="U09p343881_ETM_S06","SOURCE_CASE");
 ck(data.bts_sha256==="ad68a83a63f197c528c07502db8adff883e9c737863ef3c4cab99cfa76052147","BTS_SHA");
 ck(data.pose_outlist_correction&&data.pose_outlist_correction.original_artifact_sha256===ZIP_SHA,"ORIGINAL_ZIP_SHA");
 ck(data.pose_outlist_correction.original_outb_sha256[0]===OUTB_SHA,"ORIGINAL_OUTB_SHA");
 ck(data.original_outb_node220_three_instant_examples&&data.original_outb_node220_three_instant_examples.read_level==="RAW_FILEID4_PACKED_NATIVE_OUTB_ALL_295_CHANNELS","NATIVE_READ_LEVEL");
 const rows=data.original_outb_node220_three_instant_examples.rows;
 ck(Array.isArray(rows)&&rows.length===3&&rows.every((r,i)=>r.time_s===i),"TIME_ROWS");
 for(const r of rows){
  for(const k of ["TPxi","TPyi","TPzi","RPxi","RPyi","RPzi","FLxt","FLyt","FLzt","MLxt","MLyt","MLzt"])
   ck(Number.isFinite(r[k]),"MISSING_NATIVE_"+k);
  ck(r.TPzi>30&&r.TPzi<32,"NODE220_POSITION");
 }
 return rows;
}
function audit(data){
 const rows=gate(data), angles=[0,-0.5,-0.25,0.25,0.5], out=[], summaries=[];
 for(const row of rows){
  const F=[row.FLxt,row.FLyt,row.FLzt],M=[row.MLxt,row.MLyt,row.MLzt];
  const rA=[row.TPxi,row.TPyi,row.TPzi],rB=[0,0,0];
  const base=transport(F,M,rA,rB,Ry(0));
  for(const deg of angles){
   const Q=Ry(deg),v=transport(F,M,rA,rB,Q),rev=back(v,rA,rB,Q);
   const bound=rotationBoundY(F,M,rA,rB,deg);
   const driftF=norm(sub(v.F,base.F)),driftM=norm(sub(v.M,base.M));
   ck(driftF<=bound.force_bound_kN+1e-8,"ROTATION_FORCE_BOUND");
   ck(driftM<=bound.moment_bound_kNm+1e-8,"ROTATION_MOMENT_BOUND");
   ck(close(rev.F,F)&&close(rev.M,M),"ROUNDTRIP");
   ck(Math.abs(norm(v.F)-norm(F))<1e-8,"FORCE_NORM");
   ck(Math.abs(dot(v.F,v.M)-dot(F,M))<1e-5,"WRENCH_PITCH");
   out.push({time_s:row.time_s,hypothetical_Ry_deg:deg,force_global_kN:v.F,moment_origin_kNm:v.M,
    delta_force_vs_identity_kN:norm(sub(v.F,base.F)),
    delta_moment_vs_identity_kNm:driftM,
    analytic_force_upper_kN:bound.force_bound_kN,
    analytic_moment_upper_kNm:bound.moment_bound_kNm,
    moment_bound_utilization:bound.moment_bound_kNm===0?0:driftM/bound.moment_bound_kNm});
  }
  summaries.push({time_s:row.time_s,force_local_norm_kN:norm(F),moment_local_norm_kNm:norm(M),
   transport_only_delta_moment_norm_kNm:norm(base.delta_moment),
   moment_origin_identity_kNm:base.M,
   max_half_degree_force_delta_kN:Math.max(...out.filter(x=>x.time_s===row.time_s).map(x=>x.delta_force_vs_identity_kN)),
   max_half_degree_moment_delta_kNm:Math.max(...out.filter(x=>x.time_s===row.time_s).map(x=>x.delta_moment_vs_identity_kNm)),
   half_degree_force_upper_kN:rotationBoundY(F,M,rA,rB,0.5).force_bound_kN,
   half_degree_moment_upper_kNm:rotationBoundY(F,M,rA,rB,0.5).moment_bound_kNm,
   max_moment_bound_utilization:Math.max(...out.filter(x=>x.time_s===row.time_s).map(x=>x.moment_bound_utilization))});
 }
 return {stage:"S06/S07",status:"REAL_NATIVE_INPUT_CONDITIONAL_MATH_QC_PASS__PHYSICAL_HOLD",
  native_source:{original_artifact_sha256:ZIP_SHA,original_outb_batch1_sha256:OUTB_SHA,
   bts_sha256:data.bts_sha256,pose_receipt_git_blob_sha1:"0121256cde457417a10d4635e299d6b16608e02c",
   official_elastodyn_f90_sha256:SOURCE_SHA,official_source_lines:"L1165-L1206",read_level:"RAW_OUTB_DERIVED_3_NATIVE_SNAPSHOTS_PLUS_OFFICIAL_SOURCE_LINES"},
  test_scope:"3 real native 0/1/2 s node220 snapshots x 5 assumed Ry frames = 15 conditional scenarios",
  bound_derivation:"For Ry(theta), norm((R-I)v)=2sin(abs(theta)/2)*hypot(vx,vz); deltaM=(R-I)M+r cross (R-I)F. Moment bound=2sin(abs(theta)/2)*(hypot(Mx,Mz)+norm(r)*hypot(Fx,Fz)). Valid only for specified hypothetical global-y rotation and fixed inertial lever.",
  summary:summaries,scenarios:out,
  SOURCE:"OpenFAST native FileID4 OUTB snapshots in existing SHA-locked T062 receipt; no new solver run",
  REF:"Existing T062 method and T071/T072 source, no new journal pages",
  STANDARD:"No IEC/GB/NB authorized clauses reviewed; no standards acceptance",
  OFFICIAL:"OpenFAST v3.5.3 ElastoDyn.f90 L1165-1206: tower-section FL/ML includes yaw-bearing and tower-node gravity/inertia; axes t1,-t3,t2",
  RUN:"V8/Node arithmetic on actual 3 native snapshots; 15 hypothetical rotations, 15 inverse and invariant checks; no OpenFAST/Abaqus RUN",
  FIG:"None",TAB:"3 real rows, 15 conditional rotation/transport scenarios",
  assumptions:"Q=Ry(angle) is an arbitrary right-handed scenario; NOT ElastoDyn exact DCM and NOT derived from RP angles. rA=measured TP inertial position, rB=origin.",
  error_budget:"Floating-point algebra <1e-8 relative for invariants; native OUTB packed quantization retained from source; true DCM, nodal inertia, load ownership and 100-700s errors UNBOUNDED",
  HOLD:"FL/ML already include mass/gravity/inertia, and exact t1/-t3/t2 DCM and all nodal terms are unavailable. DO NOT apply sectional FL/ML as pure external wind.",
  physical_pass:false,earthquake_runs:0,material_life_results:0};
}
function selftest(){
 const I=Ry(0),R=Ry(90),a=transport([2,-3,5],[7,11,13],[0,0,10],[0,0,4],I);
 ck(close(a.M,[25,23,13]),"TRANSPORT_SIGN");
 ck(close(mul(R,[1,0,0]),[0,0,-1]),"ROTATION_ORIENTATION");
 ck(close(back(a,[0,0,10],[0,0,4],I).M,[7,11,13]),"INVERSE");
 const pure=rotationBoundY([1,0,0],[0,0,0],[0,0,0],[0,0,0],90);
 ck(Math.abs(pure.force_bound_kN-Math.SQRT2)<1e-12&&pure.moment_bound_kNm===0,"ANALYTIC_90DEG");
 const axis=rotationBoundY([0,2,0],[0,5,0],[0,0,0],[0,0,0],45);
 ck(axis.force_bound_kN===0&&axis.moment_bound_kNm===0,"AXIS_ALIGNED_ZERO");
 const zero=rotationBoundY([3,4,5],[6,7,8],[0,0,2],[0,0,0],0);
 ck(zero.force_bound_kN===0&&zero.moment_bound_kNm===0,"ZERO_ROTATION_BOUND");
 let rejects=0;
 const bad=[
 ()=>orthogonal([[1,0,0],[0,1,0],[0,0,-1]]),
 ()=>orthogonal([[1,0,0],[0,1,0],[0.01,0,1]]),
 ()=>transport([NaN,0,0],[0,0,0],[0,0,0],[0,0,0],I),
 ()=>Ry(Infinity),()=>gate({}),()=>gate({stage:"S06/S07",case:"U09p343881_ETM_S06",bts_sha256:"wrong"}),
 ()=>transport([0,0,0],[0,0,0],[0,0,0],[0,0,0],[[1,0,0],[0,0,1],[0,1,0]]),
 ()=>rotationBoundY([1,0,0],[0,0,0],[0,0,0],[0,0,0],NaN),
 ()=>rotationBoundY([1,0,0],[0,0,0],[0,0,0],[0,0,0],181)
 ];
 for(const fn of bad){try{fn()}catch(e){rejects++;continue}throw Error("BAD_INPUT_ACCEPTED");}
 ck(rejects===bad.length,"NEGATIVE_COUNT");
 return {status:"SYNTHETIC_MATH_TEST_PASS",positive:3,negative_rejections:rejects,physical_pass:false};
}
function main(argv){
 const fs=require("fs");
 if(argv.length===1&&argv[0]==="--selftest"){console.log(JSON.stringify(selftest()));return;}
 ck(argv.length===2&&argv[0]==="--qc","USAGE: --selftest | --qc existing_pose_receipt.json");
 const input=JSON.parse(fs.readFileSync(argv[1],"utf8"));
 console.log(JSON.stringify(audit(input),null,2));
}
module.exports={audit,selftest,transport,back,Ry,gate,rotationBoundY};
if(typeof require!=="undefined"&&require.main===module)main(process.argv.slice(2));
