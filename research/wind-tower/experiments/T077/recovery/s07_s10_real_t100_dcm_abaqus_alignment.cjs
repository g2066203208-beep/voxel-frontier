#!/usr/bin/env node
"use strict";
// 2026-10-31 real t=100s source DCM + original-INP-derived CSEG01 centroid cross-model QC.
// Fixed-platform and initial axes are conditional; NOT native Abaqus, NOT fatigue life.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");

const ED_SHA="a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3",OUTB_SHA="0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c",MODEL_SHA="22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a",CSV_SHA="bae37eeb07144db0f26c25a60a0698f4073ea878941e565c03e24154af17888f";
function must(q,m){if(!q)throw Error(m)}
function num(x){let v=Number(x);must(x!==""&&Number.isFinite(v),"BAD_NUMBER");return v}
function rad(x){return x*Math.PI/180}
function dcm(rp){must(rp.length===3&&rp.every(Number.isFinite)&&Math.abs(rp[2])<1e-10,"INVALID_RP");let a=rad(rp[0]),b=-rad(rp[1]);must(Math.max(Math.abs(a),Math.abs(b))<.4,"RP_OUT_OF_DOMAIN");let d=Math.sqrt(1+a*a+b*b),v=1/d,k=1/(d*(d+1)),t11=v+k*a*a,t12=b*v,t13=k*a*b,t21=-b*v,t22=v,t23=a*v,t31=k*a*b,t32=-a*v,t33=v+k*b*b;return [[t11,-t31,t21],[-t13,t33,-t23],[t12,-t32,t22]]}
function sm(a,b,c){let d=Math.sqrt(1+a*a+b*b+c*c),v=1/d,k=1/(d*(d+1));return [[v+k*a*a,c*v+k*a*b,-b*v+k*a*c],[-c*v+k*a*b,v+k*b*b,a*v+k*b*c],[b*v+k*a*c,-a*v+k*b*c,v+k*c*c]]}
function tr(R){return R.map((_,i)=>R.map(row=>row[i]))}
function mv(R,v){return R.map(row=>row.reduce((s,x,j)=>s+x*v[j],0))}
function diff(A,B){return Math.max(...A.flatMap((row,i)=>row.map((x,j)=>Math.abs(x-B[i][j]))))}
function ortho(R){let T=tr(R);return Math.max(...R.flatMap((row,i)=>T[0].map((_,j)=>Math.abs(row.reduce((s,x,k)=>s+x*T[k][j],0)-(i===j?1:0)))))}
function az(x,y){return ((Math.atan2(y,x)*180/Math.PI)%360+360)%360}
function wrap(x){return ((x+180)%360+360)%360-180}
function csv(text){must(!text.includes('"')&&!text.includes("\r"),"BAD_CSV");let lines=text.trimEnd().split("\n"),h=lines.shift().split(",");must(new Set(h).size===h.length,"DUP_HEADER");return lines.map(l=>{let v=l.split(",");must(v.length===h.length,"BAD_WIDTH");return Object.fromEntries(h.map((k,j)=>[k,v[j]]))})}
function build(receiptText,csvText,contractText){
 const s=JSON.parse(receiptText),c=JSON.parse(contractText),rows=csv(csvText);
 must(s.SOURCE.outb_sha256===OUTB_SHA&&s.OFFICIAL.elastodyn_sha256===ED_SHA,"BAD_ED_OR_OUTB");
 must(s.RUN.transforms===108009&&s.RUN.synchronous_time_steps===12001&&s.RUN.gages===9,"BAD_HISTORY_COVERAGE");
 must(Object.values(s.RUN.platform_dof_flags).length===6&&Object.values(s.RUN.platform_dof_flags).every(x=>x===false),"PLATFORM_NOT_FIXED");
 must(c.SOURCE.ed_sha256===s.SOURCE.elastodyn_input_sha256&&c.ElastoDyn.TowerHt_m===158&&c.ElastoDyn.TwrNodes===1120,"ED_INPUT_NOT_158M");
 const gages=c.ElastoDyn.original_TwrGagNd;must(gages.join(",")==="1,3,5,7,9,13,15,17,20","BAD_GAGES");
 must(rows.length===248&&rows.every(r=>r.model_sha256===MODEL_SHA&&r.status==="CONDITIONAL_STATIC_RIGHT_HANDED_MAPPING_NO_NATIVE_ALIGNMENT"),"BAD_248_ELEMENTS");
 const samples=s.TAB.first_sample;must(samples.length===9&&samples.every((r,i)=>r.gage===i+1),"BAD_REAL_SAMPLES");
 let delta=0,orth=0,ferr=0,rpmax=0;const frame=[];
 for(let r of samples){let R=dcm(r.RP_deg),candidate=tr(sm(...r.RP_deg.map(rad)));let d=diff(R,candidate),q=ortho(R),fg=mv(R,r.local_force_kN),e=Math.max(...fg.map((v,i)=>Math.abs(v-r.global_force_kN[i])));delta=Math.max(delta,d);orth=Math.max(orth,q);ferr=Math.max(ferr,e);rpmax=Math.max(rpmax,Math.hypot(r.RP_deg[0],r.RP_deg[1]));frame.push({gage:r.gage,RP_deg:r.RP_deg,max_candidate_matrix_delta:d,global_force_reconstruction_max_abs_kN:e})}
 must(delta<2e-14&&orth<2e-14&&ferr<2e-7,"DCM_NUMERIC_FAILED");
 const first=rows.filter(r=>r.segment==="CSEG_01");must(first.length===8&&new Set(first.map(r=>r.proper_element_label)).size===8,"BAD_CSEG01");
 const y=num(first[0].proper_centroid_y_m),dz=158/1120;
 const near=gages.map((node,i)=>({gage:i+1,node,z:(node-.5)*dz,d:Math.abs((node-.5)*dz-y)})).sort((a,b)=>a.d-b.d)[0];
 must(near.gage===6&&near.node===13&&near.d<.08,"NOT_NEAREST_GAGE6");
 const R=dcm(samples[near.gage-1].RP_deg),C=[[1,0,0],[0,0,1],[0,-1,0]],projected=[];let tilt=0,azshift=0,rshift=0;
 for(let r of first){let x=num(r.proper_centroid_x_m),z=num(r.proper_centroid_z_m),radius=Math.hypot(x,z),p=mv(C,mv(R,[x,-z,0])),oldAz=az(x,-z),newAz=az(p[0],-p[2]),da=wrap(newAz-oldAz),dr=Math.hypot(p[0],p[2])-radius;must(Math.abs(wrap(oldAz-num(r.proper_actual_openfast_az_deg)))<2e-6,"SOURCE_AZ_ERROR");tilt=Math.max(tilt,Math.abs(p[1]));azshift=Math.max(azshift,Math.abs(da));rshift=Math.max(rshift,Math.abs(dr));projected.push({layer:r.radial_layer,target_az_deg:num(r.openfast_target_az_deg),element_label:num(r.proper_element_label),initial_az_deg:oldAz,projected_global_az_deg:newAz,projected_az_drift_deg:da,vertical_tilt_mm:p[1]*1000,radial_projection_delta_mm:dr*1000})}
 must(tilt>0&&tilt<.002&&azshift<.01&&rshift<.002,"PROJECTION_RANGE_FAIL");
 return {stage:"S07_S10_REAL_T100_CSEG01_SOURCE_FRAME_GEOMETRY_QC_NOT_PHYSICS_PASS",
 SOURCE:{original_ETM_outb_sha256:OUTB_SHA,original_FST_sha256:s.SOURCE.fst_sha256,original_ED_input_sha256:s.SOURCE.elastodyn_input_sha256,official_ED_v353_sha256:ED_SHA,source_DCM_receipt_git_blob:"e3149c26a66adb184b5c5803b4ace5f7b70b6dff",corrected_element_csv_sha256:CSV_SHA,source_Abaqus_INP_sha256:MODEL_SHA,reading_level:"This turn reads complete previously native-derived 9-gage t100 source receipt and 248 original-INP-derived element CSV, NOT original OUTB or INP bytes"},
 REF:"OpenFAST v3.5.3 ElastoDyn.f90 L937-943,1704-1717,6004-6034,6856-6860; T077 source DCM 2026-10-28 and 248 real centroids 2026-10-31",
 STANDARD:"No newly read authorized IEC2025/GB/NB clauses; 0.08m is only source diagnostic",
 OFFICIAL:"Original source-verified fixed-base DCM and original-INP-derived C3D8R centroids, not independent native TowerLn2Mesh dump/ODB",
 RUN:"JavaScript V8 real-source numeric test and 6 negative mutations, no new native OpenFAST/Abaqus solver",
 FIG:"none",TAB:"9 real RP/DCM/force samples and 8 CSEG01 source element projections",
 stats:{real_time_s:100,real_gages:9,inherited_full_series_DCM_count:108009,max_source_vs_candidate_matrix_delta:delta,max_DCM_orthogonality_abs:orth,max_real_force_reconstruction_error_kN:ferr,max_real_RP_norm_deg:rpmax,nearest_gage:near.gage,nearest_node:near.node,gage_to_CSEG01_centroid_gap_m:near.d,projected_elements:8,max_projected_az_drift_deg:azshift,max_vertical_tilt_mm:tilt*1000,max_projected_radius_change_mm:rshift*1000},
 frame_samples:frame,projected_CSEG01_elements:projected,
 assumptions:["Abaqus undeformed vertical y and radial x/z; OpenFAST vertical z, conditional proper mapping [xA,yA,zA]=[xOF,zOF,-yOF]","All 6 platform DOFs false as verified in 2026-10-28 original ED input; RP inverse is source-derived not independent native mesh export","Nearest source gage6 z≈1.7634m approximates CSEG01 source centroid y≈1.8200m; no interpolation of true DCM","Projection of rotated radius into global x/z is NOT local strain, ODB deformation or actual stress"],
 error_budget:"Source RP packing uncertainty inherited from T077; 2.5deg static mesh azimuth sampling, ~0.0566m gage-centroid height gap; unbounded spatial gradient, yaw, local stress, PT/contact and load ownership",
 failure:"6 bad-source mutation rejections required; no native solver run or new standards",HOLD:"Independent native TowerLn2Mesh orientation dump and Abaqus initial datum/ODB stress still unavailable; only fixed-base source/conditional static-axis interface is numerically tested",
 physical_pass:false,native_E_WE:0,formal_stage_pass:"0/12"};
}
function negatives(s,c,k){let cases=[
 [s.replace('"PtfmRDOF": false','"PtfmRDOF": true'),c,k],
 [s.replace('"outb_sha256": "0d6f0d9d','"outb_sha256": "deadbeef'),c,k],
 [s.replace('"RP_deg": [','"RP_deg": [999,'),c,k],
 [s,c.replace("22c29916aa78","000000000000"),k],
 [s,c.trimEnd().split("\n").slice(0,-1).join("\n")+"\n",k],
 [s,c,k.replace('"TwrNodes": 1120','"TwrNodes": 1119')]
 ];let n=0;for(let a of cases){try{build(...a)}catch(e){n++}}must(n===6,"NEGATIVE_TESTS_"+n);return n}

const files=[
 path.join(__dirname,"S07_V353_FIXED_BASE_FRAME_RECEIPT_20261028.json"),
 path.join(__dirname,"S10_31SEG_4AZ_2RAD_HANDEDNESS_CORRECTED_CANDIDATES_20261031.csv"),
 path.resolve(__dirname,"../../T062/S06_NTM_ORIGINAL_FST_ED_31GAGE_CONTRACT_20261031.json")];
function sha(b){return crypto.createHash("sha256").update(b).digest("hex")}
function gitblob(b){return crypto.createHash("sha1").update(Buffer.from("blob "+b.length+" ")).update(Buffer.from([0])).update(b).digest("hex")}
function main(){
 const raw=files.map(f=>fs.readFileSync(f));
 must(gitblob(raw[0])==="e3149c26a66adb184b5c5803b4ace5f7b70b6dff","S07_RECEIPT_BLOB_MISMATCH");
 must(sha(raw[1])===CSV_SHA,"S10_CSV_SHA256_MISMATCH");
 must(gitblob(raw[2])==="19972eeff0df48aae609a8c3372f29978d904efd","CONTRACT_BLOB_MISMATCH");
 const txt=raw.map(b=>b.toString("utf8")),res=build(...txt);res.negative_source_rejections=negatives(...txt);
 const body=JSON.stringify(res,null,2)+String.fromCharCode(10);
 const dst=path.join(__dirname,"S07_S10_REAL_T100_CSEG01_DCM_ABAQUS_ALIGNMENT_20261031.json");
 if(process.argv.includes("--check"))must(fs.readFileSync(dst,"utf8")===body,"RECEIPT_BYTE_REPRO_FAILURE");
 else if(process.argv.includes("--emit"))fs.writeFileSync(dst,body,{flag:"wx"});
 else throw Error("USE_--check_OR_--emit");
 console.log("S07_S10_REAL_T100_SOURCE_QC_PASS",JSON.stringify({stats:res.stats,negative:res.negative_source_rejections,input_sha256:Object.fromEntries(files.map((f,i)=>[path.basename(f),sha(raw[i])])),output_sha256:sha(Buffer.from(body)),physics_pass:false}));
}
if(require.main===module)main();
