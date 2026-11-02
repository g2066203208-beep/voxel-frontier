#!/usr/bin/env node
// S10 conditional component-wise nominal stress load-DEL screening.
// No Abaqus, no joint stress, no material fatigue life, no DLC1.2 acceptance.
"use strict";
import fs from "node:fs";
import crypto from "node:crypto";
const EXPECTED={
 load:"9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b",
 gross:"8ae262435e13c0f10326acef7270b9962c943bb5f212171d830fe834f3a364ed"
};
const CASES=["U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06"];
const CHANNELS=["Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm"];
const COLS=["case","segment","gage_z_m","A_m2","I_m4","Ro_m","Ri_m","W_m3","Fz_component_sigma_DEL_m4_MPa","Mx_component_sigma_DEL_m4_MPa","My_component_sigma_DEL_m4_MPa"];
function must(ok,msg){if(!ok)throw Error(msg)}
function digest(s){return crypto.createHash("sha256").update(s).digest("hex")}
function parse(s){
 const rows=s.trimEnd().split(/\r?\n/),heads=rows.shift().split(",");
 must(!heads.some(x=>!x||x.includes('"')),"BAD_HEADER");
 return rows.map(line=>{
  must(!line.includes('"')&&line.split(",").length===heads.length,"BAD_CSV");
  return Object.fromEntries(line.split(",").map((v,i)=>[heads[i],v]));
 });
}
function section(a,i){
 must(Number.isFinite(a)&&a>0&&Number.isFinite(i)&&i>0,"BAD_GEOMETRY");
 const ro2=(4*i/a+a/Math.PI)/2,ri2=(4*i/a-a/Math.PI)/2;
 must(ri2>0&&ro2>ri2,"NON_ANNULAR_SECTION");
 const ro=Math.sqrt(ro2),ri=Math.sqrt(ri2),W=i/ro;
 must(Math.abs(Math.PI*(ro*ro-ri*ri)-a)/a<1e-11,"AREA_IDENTITY");
 must(Math.abs(Math.PI*(ro**4-ri**4)/4-i)/i<1e-11,"INERTIA_IDENTITY");
 return {ro,ri,W};
}
function stressDel(d,denom){must(Number.isFinite(d)&&d>=0&&denom>0,"BAD_DEL_OR_SECTION");return d/denom*0.001}
function build(loadText,grossText){
 const loads=parse(loadText),gross=parse(grossText);
 must(loads.length===744&&gross.length===31,"SOURCE_ROW_COUNT");
 const geom=new Map();
 for(const r of gross){const idx=Number(r.segment);must(Number.isInteger(idx)&&idx>=1&&idx<=31&&!geom.has(idx),"BAD_SEGMENT");const a=Number(r.gross_area_m2),i=Number(r.gross_I_m4);geom.set(idx,{a,i,...section(a,i)})}
 const groups=new Map(),seen=new Set();
 for(const r of loads){
  must(CASES.includes(r.case)&&CHANNELS.includes(r.channel),"CASE_OR_CHANNEL");
  const idx=Number(r.segment.replace("CSEG_",""));
  must(r.segment==="CSEG_"+String(idx).padStart(2,"0")&&geom.has(idx),"SEGMENT_IDENTITY");
  must(+r.n_samples===12001&&Math.abs(+r.dt_s-.05)<1e-12&&Math.abs(+r.duration_s-600)<1e-9,"TIME_CONTRACT");
  must(r.units===(r.channel.startsWith("M")?"kNm":"kN"),"UNIT_CONTRACT");
  const d=Number(r.DEL_m4_Nref_1Hz);must(Number.isFinite(d)&&d>=0,"DEL_INVALID");
  const k=r.case+"|"+r.segment,identity=k+"|"+r.channel;must(!seen.has(identity),"DUPLICATE_CHANNEL");seen.add(identity);
  const g=groups.get(k)||{};g[r.channel]={d,z:Number(r.gage_z_m)};groups.set(k,g);
 }
 must(groups.size===124&&seen.size===744,"GROUP_COVERAGE");
 const out=[COLS.join(",")];
 for(const c of CASES)for(let idx=1;idx<=31;idx++){
  const seg="CSEG_"+String(idx).padStart(2,"0"),g=groups.get(c+"|"+seg),geo=geom.get(idx);
  must(g&&CHANNELS.every(k=>g[k]),"INCOMPLETE_CHANNEL_SET");
  must(CHANNELS.every(k=>Math.abs(g[k].z-g.Fz_kN.z)<1e-8),"GAGE_Z_CONFLICT");
  const fmt=n=>n.toFixed(9);
  out.push([c,seg,fmt(g.Fz_kN.z),fmt(geo.a),fmt(geo.i),fmt(geo.ro),fmt(geo.ri),fmt(geo.W),
    fmt(stressDel(g.Fz_kN.d,geo.a)),fmt(stressDel(g.Mx_kNm.d,geo.W)),fmt(stressDel(g.My_kNm.d,geo.W))].join(","));
 }
 return out.join("\n")+"\n";
}
function selftest(){
 const x=section(Math.PI*(25-16),Math.PI*(625-256)/4);
 must(Math.abs(x.ro-5)<1e-10&&Math.abs(x.ri-4)<1e-10,"ANNULUS_TEST");
 must(Math.abs(stressDel(1000,2)-.5)<1e-12,"FORCE_UNIT_TEST");
 must(Math.abs(stressDel(1000,5)-.2)<1e-12,"MOMENT_UNIT_TEST");
 for(const bad of [-1,NaN,Infinity]){let ok=false;try{stressDel(bad,1)}catch(e){ok=true}must(ok,"BAD_DEL_NOT_REJECTED")}
 return "SELFTEST_PASS";
}
if(process.argv[1] && process.argv[1].endsWith("s10_nominal_component_stress_del_screen.js")){
 try{
  console.log(selftest());
  if(process.argv.includes("--selftest"))process.exit(0);
  must(process.argv.length===5,"USAGE: node script.js LOAD.csv GROSS.csv OUTPUT.csv");
  const load=fs.readFileSync(process.argv[2]),gross=fs.readFileSync(process.argv[3]);
  must(digest(load)===EXPECTED.load&&digest(gross)===EXPECTED.gross,"INPUT_SHA256_MISMATCH");
  const result=build(load.toString("utf8"),gross.toString("utf8"));
  fs.writeFileSync(process.argv[4],result);
  console.log("REAL_SOURCE_PASS rows=124 sha256="+digest(result));
 }catch(e){console.error(e.message);process.exitCode=1}
}
export {build,section,stressDel,selftest,EXPECTED};