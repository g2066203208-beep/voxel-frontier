#!/usr/bin/env node
"use strict";
// SOURCE-QC only: proper rigid rotation conditional on aligned undeformed axes.
// OpenFAST tower cross-section (x,y), vertical z -> Abaqus cross-section (x,z), vertical y:
// [x_A,y_A,z_A]=[x_OF,z_OF,-y_OF], det=+1. Local deflected frames need native DCM.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");

const E248_SHA="e0e74585c07d8db2d8300bc6a64b9bcb0c829cdba2f9e854e53153a0d5796ccc";
const B372_SHA="2e9fb654ed081ec7a169a1ab81e0a3483dd64be404e28f57d659d43f5e9bb4f7";
const MODEL_SHA="22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a";
const MAP_SHA="9850c1983a1bc69cc829f338260a31ff29b4e6ab86660749d453f9cc5791ff83";
function assert(v,msg){if(!v)throw Error(msg)}
function parse(s){assert(!s.includes('"')&&!s.includes("\r"),"UNSUPPORTED_CSV_QUOTING");let ls=s.trimEnd().split("\n"),h=ls.shift().split(",");assert(new Set(h).size===h.length,"DUP_HEADER");return ls.map((l,i)=>{let v=l.split(",");assert(v.length===h.length,"BAD_WIDTH_"+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]))})}
function num(s){assert(s!==""&&s!==null&&s!==undefined,"EMPTY_NUMBER");let x=Number(s);assert(Number.isFinite(x),"NONFINITE_NUMBER");return x}
function az(x){return ((x%360)+360)%360}
function gap(a,b){let d=Math.abs(az(a)-az(b));return Math.min(d,360-d)}
function det3(R){return R[0][0]*(R[1][1]*R[2][2]-R[1][2]*R[2][1])-R[0][1]*(R[1][0]*R[2][2]-R[1][2]*R[2][0])+R[0][2]*(R[1][0]*R[2][1]-R[1][1]*R[2][0])}
const R=[[1,0,0],[0,0,1],[0,-1,0]],WRONG=[[1,0,0],[0,0,1],[0,1,0]];
function stressOF(Fz,Mx,My,x,y,A,I){return (Fz/A+(Mx*y-My*x)/I)*.001}
function stressAB(Fy,Mx,Mz,x,z,A,I){return (Fy/A+(Mz*x-Mx*z)/I)*.001}
function analyticTest(){
 assert(det3(R)===1&&det3(WRONG)===-1,"HANDEDNESS_DET");
 const Fz=-2000,Mx=300,My=-500,ri=3.5,ro=4,A=Math.PI*(ro*ro-ri*ri),I=Math.PI*(ro**4-ri**4)/4;
 let max=0;for(let k=0;k<64;k++){let t=2*Math.PI*k/64,x=ro*Math.cos(t),y=ro*Math.sin(t),z=-y;let a=stressOF(Fz,Mx,My,x,y,A,I),b=stressAB(Fz,Mx,-My,x,z,A,I);max=Math.max(max,Math.abs(a-b))}
 assert(max<1e-14,"STRESS_NOT_INVARIANT");
 let N=128,da=2*Math.PI/N,radial0=(ro*ro-ri*ri)/2,radial1=(ro**4-ri**4)/4;
 // Independently recover the exact force and bending moment by angular quadrature and exact radial integrals.
 let QF=0,QMx=0,QMz=0,r2=(ro**3-ri**3)/3;
 for(let j=0;j<N;j++){let t=(j+.5)*da,c=Math.cos(t),s=Math.sin(t);
  let c0=Fz/A, c1=(-My*c-Mx*s)/I;
  QF+=(c0*radial0+c1*r2)*da;
  QMx+=-(c0*r2+c1*radial1)*s*da;
  QMz+=(c0*r2+c1*radial1)*c*da;
 }
 const relative=Math.max(Math.abs(QF-Fz)/Math.abs(Fz),Math.abs(QMx-Mx)/Math.abs(Mx),Math.abs(QMz+My)/Math.abs(My));
 assert(relative<1e-12,"INDEPENDENT_ANNULAR_EQUILIBRIUM_FAILED_"+relative);
 let rejected=0;for(let fn of [()=>num("NaN"),()=>num(""),()=>parse("a,b\n1\n"),()=>parse("a,a\n1,2\n")]){try{fn()}catch(e){rejected++}}
 assert(rejected===4,"NEGATIVE_TEST");
 return{proper_rotation_det:det3(R),naive_reflection_det:det3(WRONG),stress_invariance_max_MPa:max,annulus_force_moment_relative_error:relative,synthetic_negative_tests:rejected};
}
function build(raw248,raw372){
 const g=parse(raw248),b=parse(raw372);assert(g.length===248&&b.length===372,"BAD_ROW_COUNT");
 const map=new Map();let ids=new Set();
 for(let e of g){
  assert(e.source_model_sha256===MODEL_SHA&&e.source_map_sha256===MAP_SHA,"WRONG_MODEL_MAP");
  assert(e.element_type==="C3D8R"&&e.odb_integration_point===""&&e.local_stress_MPa==="","FALSE_ODB");
  let k=[e.segment,e.radial_layer,e.requested_azimuth_deg].join("|");
  assert(!map.has(k),"DUP_ELEMENT");map.set(k,e);ids.add(e.segment);
 }
 assert(ids.size===31,"BAD_SEGMENTS");
 const controls=new Set(),controlAz=new Set();
 for(let x of b){
  assert(x.d400_model_sha256===MODEL_SHA&&x.status==="HOLD_SOURCE_CENTROID_NO_ODB","BINDING_IDENTITY");
  let k=[x.case,x.segment,x.gross_control].join("|");assert(!controls.has(k),"DUP_CONTROL");controls.add(k);
  assert(x.target_local_az_deg==="0"||x.target_local_az_deg==="180","UNEXPECTED_CONTROL_AZ");
  controlAz.add(x.target_local_az_deg);
  let same=map.get([x.segment,"INNER",x.target_local_az_deg].join("|"));
  assert(same&&same.element_label===x.inner_label,"CONTROL_INNER_LABEL_CHANGED");
  same=map.get([x.segment,"OUTER",x.target_local_az_deg].join("|"));
  assert(same&&same.element_label===x.outer_label,"CONTROL_OUTER_LABEL_CHANGED");
 }
 assert(controls.size===372&&controlAz.size===2,"CONTROL_372");
 const head=["segment","radial_layer","openfast_target_az_deg","proper_abaqus_target_az_deg","proper_element_label","proper_centroid_x_m","proper_centroid_y_m","proper_centroid_z_m","proper_centroid_r_m","proper_actual_model_az_deg","proper_actual_openfast_az_deg","proper_az_gap_deg","old_same_angle_label","old_same_angle_actual_openfast_az_deg","old_same_angle_az_gap_deg","requires_90_270_swap","model_sha256","status"];
 const lines=[head.join(",")];let count=0,swap=0,wrong90=0,maxProper=0,maxOld=0,radMin=Infinity,radMax=0;
 for(let i=1;i<=31;i++)for(let layer of ["INNER","OUTER"])for(let theta of [0,90,180,270]){
  let seg="CSEG_"+String(i).padStart(2,"0"),properTarget=az(-theta);
  let e=map.get([seg,layer,String(properTarget)].join("|")),old=map.get([seg,layer,String(theta)].join("|"));
  assert(e&&old,"MISSING_ELEMENT");
  let x=num(e.centroid_x_m),y=num(e.centroid_y_m),z=num(e.centroid_z_m),r=Math.hypot(x,z),thetaActual=az(Math.atan2(-z,x)*180/Math.PI);
  let oldAz=az(Math.atan2(-num(old.centroid_z_m),num(old.centroid_x_m))*180/Math.PI);
  let goodGap=gap(thetaActual,theta),badGap=gap(oldAz,theta),need=properTarget!==theta;
  assert(goodGap<2.50001,"CORRECTED_ANGLE_EXCEEDS_GEOMETRY_TOL");
  if(need){assert(badGap>177.49,"REFLECTION_NOT_CAUGHT");swap++;wrong90++}else assert(badGap<2.50001,"ZERO_180_WRONG");
  radMin=Math.min(radMin,r);radMax=Math.max(radMax,r);maxProper=Math.max(maxProper,goodGap);maxOld=Math.max(maxOld,badGap);
  lines.push([seg,layer,theta,properTarget,e.element_label,e.centroid_x_m,e.centroid_y_m,e.centroid_z_m,e.centroid_radius_m,
   e.actual_azimuth_deg,thetaActual.toFixed(9),goodGap.toFixed(9),old.element_label,oldAz.toFixed(9),badGap.toFixed(9),need?"YES":"NO",MODEL_SHA,"CONDITIONAL_STATIC_RIGHT_HANDED_MAPPING_NO_NATIVE_ALIGNMENT"].join(","));
  count++;
 }
 assert(count===248&&swap===124&&wrong90===124,"COVERAGE");
 return{csv:lines.join("\n")+"\n",stats:{rows:count,segments:31,radial_layers:2,openfast_cardinal_angles:4,old_same_angle_90_270_misbindings:swap,old_0_180_control_rows_unaffected:372,old_0_180_element_bindings_unaffected:744,maximum_proper_angle_gap_deg:maxProper,maximum_old_angle_gap_deg:maxOld,min_radius_m:radMin,max_radius_m:radMax},self_test:analyticTest()};
}
function negativeSourceTests(raw248,raw372){
 const edits=[
 [raw248.replace("22c29916","00000000"),raw372],
 [raw248.trimEnd().split("\n").slice(0,-1).join("\n")+"\n",raw372],
 [raw248,raw372.replace("HOLD_SOURCE_CENTROID_NO_ODB","PHYSICAL_PASS")],
 [raw248,raw372.trimEnd().split("\n").slice(0,-1).join("\n")+"\n"],
 [raw248.replace(",C3D8R,",",S4R,"),raw372],
 [raw248.replace(",,D400_PE_SOURCE",",1,D400_PE_SOURCE"),raw372]
 ];let n=0;for(let [a,b] of edits){try{build(a,b)}catch(e){n++}}assert(n===6,"NEGATIVE_SOURCE_TEST_FAILED");return n;
}

function sha(s){return crypto.createHash("sha256").update(s).digest("hex")}
function main(){const d=__dirname,a=fs.readFileSync(path.join(d,"S10_D400_PE_31SEG_4AZ_2RAD_MIDPLANE_ELEMENTS_20261031.csv")),b=fs.readFileSync(path.join(d,"S10_4ETM_31SEG_MIDPLANE_2RAD_CONTROL_BINDING_20261031.csv"));
 if(sha(a)!==E248_SHA||sha(b)!==B372_SHA)throw Error("SOURCE_SHA256_MISMATCH");
 const r=build(a.toString("utf8"),b.toString("utf8"));const n=negativeSourceTests(a.toString("utf8"),b.toString("utf8"));
 const p=path.join(d,"S10_31SEG_4AZ_2RAD_HANDEDNESS_CORRECTED_CANDIDATES_20261031.csv");
 if(process.argv.includes("--check")){if(fs.readFileSync(p,"utf8")!==r.csv)throw Error("OUTPUT_MISMATCH")}else if(process.argv.includes("--emit"))fs.writeFileSync(p,r.csv,{flag:"wx"});else throw Error("USE_--check_OR_--emit");
 console.log("S10_REAL_248_GEOMETRY_HANDEDNESS_SOURCE_QC_PASS",JSON.stringify({stats:r.stats,analytic:r.self_test,negative_source_rejections:n,output_sha256:sha(r.csv),physical_pass:false}));}
if(require.main===module)main();
