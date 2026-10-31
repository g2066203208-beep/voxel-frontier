#!/usr/bin/env node
"use strict";

const NAMES=["S10_4CASE_31SEG_SYNC_GROSS_CONTROL_20261030.csv","S10_D400_PE_AZIMUTH_HEIGHT_CANDIDATES_20261028.csv","S10_D400_PE_68PART_INP_METADATA_20261028.csv","S10_T057_68PART_INP_METADATA_20261028.csv","S10_18NTM_6SEED_GROSS_STRESS_CONTROL_20261031.csv"];
const LOCKS=["36c0a8a97db36885159fff79cc61daced9c939ab688f98ce1c6b860a89ac91d3","9052f70b39544c8fbd27b0813face4eecf2dcace3efdbd7c3cebbc896b395595","9850c1983a1bc69cc829f338260a31ff29b4e6ab86660749d453f9cc5791ff83","502fe65c94a8d060611e6b4293790ed3a5f48174a41b7732a3b221a5195e66fd","619e28d6ae2b76292224df999efc04e0650dcf4e001353647e75b9536d7cecd6"];
const OUT="S10_4ETM_31SEG_NATIVE_ELEMENT_SPATIAL_BINDING_QC_20261031.csv",RECEIPT="S10_4ETM_31SEG_NATIVE_ELEMENT_SPATIAL_BINDING_RECEIPT_20261031.json";
const COL=["case","segment","gage_z_m","gross_control","gross_value_MPa","target_local_az_deg","d400_concrete_instance","concrete_material","concrete_element_label","concrete_axial_plane","concrete_centroid_z_m","concrete_axial_gap_m","concrete_az_gap_deg","concrete_height_only_alt_element","concrete_height_only_alt_gap_m","d400_rebar_instance","d400_rebar_material","t057_rebar_material","d400_rebar_element_label","rebar_centroid_z_m","rebar_axial_gap_m","rebar_az_gap_deg","odb_ip","local_stress_MPa","local_over_gross","status"];
function die(s){throw Error(s)}
function parse(s,n){if(typeof s!=="string"||s.includes('"')||s.includes("\r"))die("BAD_CSV_FORMAT:"+n);let l=s.trimEnd().split("\n"),h=l.shift().split(",");if(h.length<3||new Set(h).size!==h.length)die("BAD_HEADER:"+n);return l.map((v,i)=>{let a=v.split(",");if(a.length!==h.length)die("BAD_WIDTH:"+n+":"+(i+2));return Object.fromEntries(h.map((x,j)=>[x,a[j]]))})}
function num(x,n){if(x===""||x===undefined||!Number.isFinite(Number(x)))die("BAD_NUMBER:"+n);return Number(x)}
function pair(r){return r.source_part+"|"+r.source_group}
function compute(raw,sha,verify=true){
 let h=NAMES.map((n,i)=>{if(!(n in raw))die("MISSING_INPUT:"+n);let x=sha(raw[n]);if(verify&&x!==LOCKS[i])die("SHA_MISMATCH:"+n);return x});
 let [g,c,d,t,ntm]=NAMES.map(n=>parse(raw[n],n));
 if(g.length!==124||c.length!==372||d.length!==68||t.length!==68||ntm.length!==30)die("ROW_COUNT");
 let dm=new Map(),tm=new Map(),cm=new Map(),seen=new Set();
 for(let x of d){if(dm.has(pair(x)))die("D400_DUPLICATE");dm.set(pair(x),x)}
 for(let x of t){if(tm.has(pair(x)))die("T057_DUPLICATE");tm.set(pair(x),x)}
 if(dm.size!==68||tm.size!==68||[...dm.keys()].some(k=>!tm.has(k)))die("68PART_MISMATCH");
 for(let x of c){if(x.model_sha256!=="22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"||x.source_map_sha256!==LOCKS[2])die("MODEL_SHA_MISMATCH");
 if(x.odb_integration_point||x.stress_basis)die("CANDIDATE_IS_NOT_SOURCE_ONLY");
 let k=pair(x)+"|"+x.requested_azimuth_deg+"|"+x.axial_plane;if(seen.has(k))die("DUPLICATE_ELEMENT_CANDIDATE");seen.add(k);cm.set(pair(x),[...(cm.get(pair(x))||[]),x])}
 if(cm.size!==62)die("NOT_62_CANDIDATE_PARTS");
 let cases=new Set(),ids=new Set(),rows=[],cg=[],rg=[],mg=[],ag=[],f=x=>Number(x).toFixed(6);
 for(let x of g){let id=x.case+"|"+x.segment;if(ids.has(id))die("DUPLICATE_CASE_SEG");ids.add(id);cases.add(x.case);
 if(!/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(x.segment))die("BAD_SEGMENT");
 let z=num(x.gage_z_m,"gage"),idx=x.segment.slice(-2),conc=cm.get("CSEG_"+idx+"|concrete"),reb=cm.get("RBLONG_"+idx+"|longitudinal_rebar"),dc=dm.get("CSEG_"+idx+"|concrete"),dr=dm.get("RBLONG_"+idx+"|longitudinal_rebar"),tr=tm.get("RBLONG_"+idx+"|longitudinal_rebar");
 if(!conc||conc.length!==8||!reb||reb.length!==4||!dc||!dr||!tr||dr.section_material_from_INP!=="HRB400_D400_DIAGNOSTIC"||tr.section_material_from_INP!=="HRB335_T057")die("BRANCH_OR_POINT_MISMATCH");
 if(dc.section_material_from_INP!==conc[0].section_material||dr.section_material_from_INP!==reb[0].section_material)die("D400_MATERIAL_MISMATCH");
 for(let [kind,vcol,acol] of [["DEL4","max_DEL_m4_MPa","azimuth_at_max_DEL4_deg"],["TENSION","max_sigma_tension_MPa","azimuth_at_max_tension_deg"],["COMPRESSION","min_sigma_compression_MPa","azimuth_at_min_compression_deg"]]){
 let az=num(x[acol],"az"),value=num(x[vcol],"gross");if(![0,90,180,270].includes(az))die("NO_MATCHING_AZIMUTH");
 let concrete=conc.filter(r=>num(r.requested_azimuth_deg,"caz")===az).sort((a,b)=>Math.abs(num(a.centroid_y_m,"a")-z)-Math.abs(num(b.centroid_y_m,"b")-z)||num(a.element_label,"label")-num(b.element_label,"label"))[0],rebar=reb.find(r=>num(r.requested_azimuth_deg,"raz")===az);
 if(!concrete||!rebar)die("MISSING_ELEMENT");
 let cgap=Math.abs(num(concrete.centroid_y_m,"cz")-z),rgap=Math.abs(num(rebar.centroid_y_m,"rz")-z),mgap=Math.abs(num(dc.height_candidate_mid_y_m,"mid")-z),agap=num(concrete.azimuth_gap_deg,"azgap");
 cg.push(cgap);rg.push(rgap);mg.push(mgap);ag.push(agap);
 rows.push([x.case,x.segment,x.gage_z_m,kind,value,az,concrete.instance,concrete.section_material,concrete.element_label,concrete.axial_plane,concrete.centroid_y_m,f(cgap),f(agap),dc.height_candidate_element_label,f(mgap),rebar.instance,rebar.section_material,tr.section_material_from_INP,rebar.element_label,rebar.centroid_y_m,f(rgap),f(num(rebar.azimuth_gap_deg,"ragap")),"","","","HOLD_SOURCE_ELEMENT_NOT_ODB_IP"].join(","));
 }}
 if(cases.size!==4||ids.size!==124||rows.length!==372)die("4CASE_31SEG_INCOMPLETE");
 for(let x of ntm){if(!["BASE",...Array.from({length:9},(_,i)=>"G"+String(i+1).padStart(2,"0"))].includes(x.station)||num(x.z_m,"ntm_z")<0||num(x.z_m,"ntm_z")>2.751)die("NTM_SCOPE_VIOLATION")}
 let stats=a=>({min:Math.min(...a),max:Math.max(...a),mean:a.reduce((p,q)=>p+q,0)/a.length});
 let csv=COL.join(",")+"\n"+rows.join("\n")+"\n";
 let receipt={SOURCE:"4 ETM x31 source-derived gross stress controls; D400 PE INP static element candidates; D400/T057 68-part source metadata; 18 NTM six-seed near-base scope table",SOURCE_READING:"actual GitHub CSV text bytes; SHA256 locked; no ODB read",input_sha256:Object.fromEntries(NAMES.map((n,i)=>[n,h[i]])),model_sha256:"22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a",REF:"REF018 Huang2025 Eq1-2 and Kenna2019 local strain method; research/wind-tower/experiments/T079/PRIMARY_PAPER_FIGURE_TO_158M_METHOD_MATRIX_20261031.tsv",STANDARD:"No new IEC/GB/NB authorized clause reading",OFFICIAL:"Abaqus source INP element instance/section identity only; no native ODB or material stress",RUN:"Node.js SHA-locked CSV join and fail-closed negative tests, zero Abaqus/OpenFAST production",FIG:"none, no invented local stress cloud plot",TAB:"372 ETM segment/criterion-to-D400 source-element candidates; 30 NTM nearbase rows scoped but NOT falsely mapped to 31 segments",cases:[...cases].sort(),source_rows:{etm:g.length,candidate:c.length,d400_metadata:d.length,t057_metadata:t.length,ntm_nearbase:ntm.length,output:rows.length},concrete_axial_gap_m:stats(cg),rebar_axial_gap_m:stats(rg),concrete_height_only_gap_m:stats(mg),concrete_azimuth_gap_deg:stats(ag),concrete_over_0p1m:cg.filter(v=>v>0.1).length,output_sha256:sha(csv),assumptions:["ETM DEL4/tension/compression are separate extrema, not synchronous states","Concrete azimuth candidates cover only LOWEST/HIGHEST centroid planes; mid-height-only label has no verified azimuth","D400/T057 rebar grade and element label identity cannot be interchanged","OpenFAST local azimuth not yet independently mapped to Abaqus global frame"],error_budget:"Source candidate axial and angular offsets explicit in each row; 6-digit output gaps round <5e-7m; local stress, PT, gravity, contact, ODB integration point, frame and material errors unbounded",negative_tests:"tamper SHA; duplicate candidate; wrong T057 grade; NTM out of CSEG01; missing source; no matching azimuth",physical_pass:false,stage:"0/12",seismic_native_runs:0,HOLD:"ALL_372_CONCRETE_AZIMUTH_CANDIDATES_HAVE_GT_0p1M_AXIAL_GAP; NO_ODB_IP/PT/CONTACT/NATIVE_LOCAL_STRESS; NTM only CSEG01; steel/PT not bound"};
 return {csv,receipt,text:JSON.stringify(receipt,null,2)+"\n"};
}
function tests(raw,sha){
 let bad=(name,expected,mutate,lock)=>{let x={...raw};mutate(x);try{compute(x,sha,lock)}catch(e){if(!String(e.message).startsWith(expected))die("NEGATIVE_WRONG_ERROR:"+name+":"+e.message);return}die("NEGATIVE_ACCEPTED:"+name)};
 bad("tamper","SHA_MISMATCH",x=>x[NAMES[0]]=x[NAMES[0]].replace("U09p343881_ETM_S06","Z09p343881_ETM_S06"),true);
 bad("duplicate","ROW_COUNT",x=>x[NAMES[1]]+=x[NAMES[1]].split("\n")[1]+"\n",false);
 bad("grade","BRANCH_OR_POINT_MISMATCH",x=>x[NAMES[3]]=x[NAMES[3]].replace("HRB335_T057","HRB500_T077"),false);
 bad("scope","NTM_SCOPE_VIOLATION",x=>x[NAMES[4]]=x[NAMES[4]].replace(",2.75089285714,",",112.75089285714,"),false);
 bad("missing","MISSING_INPUT",x=>delete x[NAMES[2]],true);
 bad("azimuth","NO_MATCHING_AZIMUTH",x=>x[NAMES[0]]=x[NAMES[0]].replace(",6.83617569974,0,",",6.83617569974,22.5,"),false);
 return 6;
}

const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const root=__dirname;
const input={};
for(const n of NAMES){const p=path.join(n.includes("18NTM")?path.join(root,"../../T062"):root,n);input[n]=fs.readFileSync(p,"utf8")}
const hash=s=>crypto.createHash("sha256").update(s,"utf8").digest("hex");
const argc=process.argv.slice(2),allow=["--check","--emit","--self-test"];
if(argc.some(x=>!allow.includes(x)))die("UNKNOWN_ARG");
if(argc.includes("--self-test")){console.log("S10_NATIVE_BINDING_NEGATIVE_TESTS_PASS",tests(input,hash))}
const o=compute(input,hash);
if(argc.includes("--emit")){fs.writeFileSync(path.join(root,OUT),o.csv);fs.writeFileSync(path.join(root,RECEIPT),o.text)}
if(argc.includes("--check")||(!argc.includes("--emit")&&!argc.includes("--self-test"))){
 if(fs.readFileSync(path.join(root,OUT),"utf8")!==o.csv)die("OUTPUT_CSV_REGEN_MISMATCH");
 if(fs.readFileSync(path.join(root,RECEIPT),"utf8")!==o.text)die("OUTPUT_JSON_REGEN_MISMATCH");
}
console.log("S10_NATIVE_BINDING_SOURCE_QC_PASS",o.receipt.source_rows,"concrete_gap_m",o.receipt.concrete_axial_gap_m,"NO_ODB_NO_PHYSICS_PASS");
