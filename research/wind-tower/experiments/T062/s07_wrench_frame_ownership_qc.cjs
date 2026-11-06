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

function historyBoundAudit(d){
 ck(d&&d.stage==="S07_REAL_ORIGINAL_ETM_9GAGE_SYNCHRONOUS_SOURCE_FRAME_CANDIDATE_QC","HISTORY_STAGE");
 ck(d.case==="U09p343881_ETM_S01"&&d.source_outb_sha256==="0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c","HISTORY_SOURCE_SHA");
 ck(d.time_grid&&d.time_grid.n===12001&&d.time_grid.dt_s===0.05&&d.time_grid.start_s===100&&d.time_grid.end_s===700&&d.gage_count===9,"HISTORY_GRID");
 ck(Array.isArray(d.summary)&&d.summary.length===9&&Array.isArray(d.selected_native_samples)&&d.selected_native_samples.length===6,"HISTORY_ROWS");
 const maxRp=Math.max(...d.summary.map((s,i)=>{ck(s.gage===i+1&&Number.isFinite(s.max_RP_abs_deg)&&s.max_RP_abs_deg>=0,"HISTORY_RP_SUMMARY");return s.max_RP_abs_deg;}));
 const rows=d.selected_native_samples.map((r,i)=>{
  ck(r.gage===(i<3?1:9)&&r.time_s===[100,400,700][i%3],"HISTORY_SAMPLE_ID");
  for(const k of ["native_F_N","native_M_Nm","native_TP_m","native_RP_deg","candidate_F_global_N","candidate_M_at_origin_Nm"])vec(r[k]);
  const rpRad=norm(r.native_RP_deg)*Math.PI/180;
  ck(rpRad<=0.4,"HISTORY_RP_DOMAIN");
  // Conditional SmllRotTrans353 candidate: angle=atan(||RP_rad||), not an independently measured DCM.
  const factor=2*Math.sin(Math.atan(rpRad)/2);
  const F=r.native_F_N,M=r.native_M_Nm,lever=r.native_TP_m;
  const identityM=add(M,cross(lever,F));
  const driftF=norm(sub(r.candidate_F_global_N,F));
  const driftM=norm(sub(r.candidate_M_at_origin_Nm,identityM));
  const forceBound=factor*norm(F),momentBound=factor*(norm(M)+norm(lever)*norm(F));
  ck(driftF<=forceBound+0.001&&driftM<=momentBound+0.001,"HISTORY_SO3_BOUND");
  return {gage:r.gage,time_s:r.time_s,RP_norm_deg:norm(r.native_RP_deg),
   candidate_force_rotation_delta_N:driftF,candidate_force_rotation_bound_N:forceBound,
   candidate_origin_moment_rotation_delta_Nm:driftM,candidate_origin_moment_rotation_bound_Nm:momentBound,
   force_bound_utilization:forceBound===0?0:driftF/forceBound,
   moment_bound_utilization:momentBound===0?0:driftM/momentBound};
 });
 ck(maxRp<0.4*180/Math.PI,"HISTORY_RP_MAX_DOMAIN");
 return {status:"SIX_ORIGINAL_SAMPLES_CONDITIONAL_SO3_BOUND_PASS_PHYSICAL_HOLD",
  case:d.case,source_outb_sha256:d.source_outb_sha256,
  source_read_level:"EXISTING_SHA_LOCKED_FULL_OUTB_QC_RECEIPT__SIX_ROUNDED_NATIVE_SAMPLES_NOT_NEW_OUTB_BYTE_READ",
  nine_gage_full_history_max_RP_norm_deg:maxRp,
  hypothetical_half_degree_to_max_native_RP_ratio:0.5/maxRp,
  samples_checked:rows.length,rows,physical_pass:false,
  limitation:"RP->t-axis remains a candidate; original nine gages are near-base, not 31-station DLC1.2; sectional FL/ML include gravity and inertia."};
}
function historyBoundSelftest(d){
 const ok=historyBoundAudit(d);
 ck(ok.rows.length===6&&ok.rows.every(x=>x.force_bound_utilization<=1.0001&&x.moment_bound_utilization<=1.0001),"HISTORY_TEST_PASS");
 const copy=()=>JSON.parse(JSON.stringify(d));
 const rejects=[
  x=>{x.source_outb_sha256="0".repeat(64);},
  x=>{x.time_grid.n=12000;},
  x=>{x.selected_native_samples[0].native_RP_deg[0]=NaN;},
  x=>{x.selected_native_samples[0].native_RP_deg[0]=30;},
  x=>{x.selected_native_samples[0].candidate_F_global_N[0]+=10000;},
  x=>{x.selected_native_samples[0].candidate_M_at_origin_Nm[0]+=1000000;},
  x=>{x.selected_native_samples.pop();},
  x=>{x.summary[0].gage=2;}
 ];
 let caught=0;
 for(const mutate of rejects){let x=copy();mutate(x);try{historyBoundAudit(x);}catch(e){caught++;continue;}throw Error("HISTORY_BAD_INPUT_ACCEPTED");}
 ck(caught===rejects.length,"HISTORY_NEGATIVE_COUNT");
 return {positive:1,negative_rejections:caught,real_samples:ok.samples_checked};
}


function towerSourceSignAudit(officialExcerpt,gravityCSV){
 ck(typeof officialExcerpt==="string"&&officialExcerpt.length>200,"OFFICIAL_SOURCE_EMPTY");
 const signatures=[
  ["base_Fz_a2","m%AllOuts( TwrBsFzt) =  DOT_PRODUCT( FrcT0Trb, m%CoordSys%a2 )"],
  ["base_Mx_a1","m%AllOuts( TwrBsMxt) =  DOT_PRODUCT( MomX0Trb, m%CoordSys%a1 )"],
  ["base_My_minus_a3","m%AllOuts( TwrBsMyt) = -DOT_PRODUCT( MomX0Trb, m%CoordSys%a3 )"],
  ["local_Fx_t1","m%AllOuts( TwHtFLxt(I) ) =     DOT_PRODUCT( FrcFGagT, m%CoordSys%t1(p%TwrGagNd(I),:) )"],
  ["local_Fy_minus_t3","m%AllOuts( TwHtFLyt(I) ) = -1.*DOT_PRODUCT( FrcFGagT, m%CoordSys%t3(p%TwrGagNd(I),:) )"],
  ["local_Fz_t2","m%AllOuts( TwHtFLzt(I) ) =     DOT_PRODUCT( FrcFGagT, m%CoordSys%t2(p%TwrGagNd(I),:) )"],
  ["local_Mx_t1","m%AllOuts( TwHtMLxt(I) ) =     DOT_PRODUCT( MomFGagT, m%CoordSys%t1(p%TwrGagNd(I),:) )"],
  ["local_My_minus_t3","m%AllOuts( TwHtMLyt(I) ) = -1.*DOT_PRODUCT( MomFGagT, m%CoordSys%t3(p%TwrGagNd(I),:) )"],
  ["local_Mz_t2","m%AllOuts( TwHtMLzt(I) ) =     DOT_PRODUCT( MomFGagT, m%CoordSys%t2(p%TwrGagNd(I),:) )"],
  ["yaw_mass_gravity","FrcFGagT = FrcONcRt - p%YawBrMass*( p%Gravity*m%CoordSys%z2 + LinAccEO )"],
  ["tower_mass_gravity","TmpVec2  = FTTower(:,J) - p%MassT(J)*( p%Gravity*m%CoordSys%z2 + LinAccET(:,J) )"],
  ["half_element_gravity","TmpVec2  = FTTower(:,p%TwrGagNd(I)) - p%MassT(p%TwrGagNd(I))*( p%Gravity*m%CoordSys%z2 + LinAccET(:,p%TwrGagNd(I)))"]
 ];
 for(const [name,signature] of signatures)ck(officialExcerpt.includes(signature),"OFFICIAL_SIGNATURE_"+name);
 const lines=gravityCSV.trim().split(/\r?\n/),header=lines.shift().split(",");
 ck(header.join(",")==="segment,gage_z_m,Fx_kN,Fx_kN_range,Fy_kN,Fy_kN_range,Fz_kN,Fz_kN_range,Mx_kNm,Mx_kNm_range,My_kNm,My_kNm_range,Mz_kNm,Mz_kNm_range","GRAVITY_HEADER");
 ck(lines.length===31,"GRAVITY_COUNT");
 let previous=-Infinity,firstMy=null,values=[];
 for(let i=0;i<31;i++){
  const c=lines[i].split(",");ck(c.length===14,"GRAVITY_WIDTH");
  ck(c[0]==="CSEG_"+String(i+1).padStart(2,"0"),"GRAVITY_SEGMENT_ID");
  const v=c.slice(1).map(Number);ck(v.every(Number.isFinite),"GRAVITY_NAN");
  const [z,fx,fxr,fy,fyr,fz,fzr,mx,mxr,my,myr,mz,mzr]=v;
  ck(z>0&&z<112,"GRAVITY_HEIGHT");
  ck(fz<0&&fz>previous,"GRAVITY_AXIAL_NEGATIVE_MONOTONE");
  ck([fx,fxr,fy,fyr,fzr,mx,mxr,myr,mz,mzr].every(x=>Math.abs(x)<1e-9),"GRAVITY_STATIC_COMPONENTS");
  if(firstMy===null)firstMy=my;
  ck(Math.abs(my-firstMy)<1e-9,"GRAVITY_MY_CONSISTENCY");
  previous=fz;values.push(fz);
 }
 return {status:"SOURCE_CODE_PROJECTION_AND_DERIVED_GRAVITY_SIGN_QC_PASS_PHYSICAL_HOLD",official_signature_checks:signatures.length,gravity_rows:31,negative_axial_rows:values.filter(x=>x<0).length,monotone_axial_pairs:30,gravity_Fz_min_kN:Math.min(...values),gravity_Fz_max_kN:Math.max(...values),gravity_My_kNm:firstMy,
  channel_map:{FLxt:"dot(F,t1)",FLyt:"-dot(F,t3)",FLzt:"dot(F,t2)",MLxt:"dot(M,t1)",MLyt:"-dot(M,t3)",MLzt:"dot(M,t2)"},
  interpretation:"Negative historical derived Fz is consistent with downward gravity under upward local t2, NOT an independently proven native sign convention or pure wind force.",physical_pass:false};
}
function towerSourceSignSelftest(source,csv){
 const good=towerSourceSignAudit(source,csv);
 const replacements=[
  [source.replace("m%AllOuts( TwHtFLzt(I) ) =     DOT_PRODUCT","m%AllOuts( TwHtFLzt(I) ) = -1.*DOT_PRODUCT"),csv],
  [source.replace("m%AllOuts( TwHtMLyt(I) ) = -1.*DOT_PRODUCT","m%AllOuts( TwHtMLyt(I) ) =     DOT_PRODUCT"),csv],
  [source.replace("FrcFGagT = FrcONcRt - p%YawBrMass*","FrcFGagT = FrcONcRt + p%YawBrMass*"),csv],
  [source,csv.replace("-25192.602388144347","25192.602388144347")],
  [source,csv.replace("CSEG_02,","CSEG_01,")],
  [source,csv.replace("-24549.807646600373","-26000")],
  [source,csv.replace("CSEG_31,110.53063726502562,","CSEG_31,110.53063726502562,1,")],
  [source,csv.replace("CSEG_31,110.53063726502562,","CSEG_31,NaN,")]
 ];
 let caught=0;
 for(const [s,c] of replacements){try{towerSourceSignAudit(s,c)}catch(e){caught++;continue}throw Error("SOURCE_SIGN_BAD_INPUT_ACCEPTED_"+caught);}
 ck(caught===replacements.length,"SOURCE_SIGN_NEGATIVE_COUNT");
 return {positive:1,negative_rejections:caught,gravity_rows:good.gravity_rows,source_signatures:good.official_signature_checks};
}

function main(argv){
 const fs=require("fs");
 if(argv.length===3&&argv[0]==="--tower-sign"){const source=fs.readFileSync(argv[1],"utf8"),gravity=fs.readFileSync(argv[2],"utf8");const out=towerSourceSignAudit(source,gravity);out.tests=towerSourceSignSelftest(source,gravity);console.log(JSON.stringify(out,null,2));return;}
 if(argv.length===1&&argv[0]==="--selftest"){console.log(JSON.stringify(selftest()));return;}
 if(argv.length===2&&argv[0]==="--history"){const d=JSON.parse(fs.readFileSync(argv[1],"utf8"));const out=historyBoundAudit(d);out.tests=historyBoundSelftest(d);console.log(JSON.stringify(out,null,2));return;}
 ck(argv.length===2&&argv[0]==="--qc","USAGE: --selftest | --qc existing_pose_receipt.json | --history existing_9gage_receipt.json");
 const input=JSON.parse(fs.readFileSync(argv[1],"utf8"));
 console.log(JSON.stringify(audit(input),null,2));
}
module.exports={audit,selftest,transport,back,Ry,gate,rotationBoundY,historyBoundAudit,historyBoundSelftest,towerSourceSignAudit,towerSourceSignSelftest};
if(typeof require!=="undefined"&&require.main===module)main(process.argv.slice(2));
