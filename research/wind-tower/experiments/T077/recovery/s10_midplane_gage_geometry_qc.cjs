#!/usr/bin/env node
"use strict";
// Source-only annulus identity: OpenFAST segment-midpoint A/I versus actual gage height.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const FILES={
 seg:["S01_PT_AXIAL_31SEG_SOURCE_20261026.csv","d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e"],
 gross:["S06_158M_TOWER_GROSS_SECTION_IDENTITY_31SEG_20261026.csv","8ae262435e13c0f10326acef7270b9962c943bb5f212171d830fe834f3a364ed"],
 cross:["S10_4ETM_31SEG_PT_GROSS_SOURCE_CROSSWALK_20261106.csv","6cf715a3624e479681086c31db25f01dd9c86f42eaa81bd56402d716d4298b43"]
};
const fail=m=>{throw Error(m)};
function rows(s){const [head,...lines]=s.trimEnd().split(/\r?\n/),keys=head.split(",");return lines.map(line=>{const values=line.split(",");if(values.length!==keys.length)fail("CSV_WIDTH");return Object.fromEntries(keys.map((k,i)=>[k,values[i]]))})}
function num(v){if(v===undefined||String(v).trim()===""||!Number.isFinite(Number(v)))fail("BAD_NUMBER");return Number(v)}
function geo(x,z){const y0=num(x.y0_m),y1=num(x.y1_m),t=(z-y0)/(y1-y0);
 if(!(y1>y0&&t>=-1e-8&&t<=1+1e-8))fail("BAD_HEIGHT");
 const ro=num(x.ro0_m)+(num(x.ro1_m)-num(x.ro0_m))*t,ri=num(x.ri0_m)+(num(x.ri1_m)-num(x.ri0_m))*t;
 if(!(ro>ri&&ri>0))fail("BAD_RADII");
 return [Math.PI*(ro*ro-ri*ri),Math.PI*(ro**4-ri**4)/4]}
function derive(src){
 const s=rows(src.seg),g=rows(src.gross),c=rows(src.cross);
 if(s.length!==31||g.length!==31||c.length!==124)fail("SOURCE_ROW_COUNT");
 const header="segment,mid_z_m,gage_z_m,gage_minus_mid_m,mid_A_m2,openfast_A_m2,mid_A_delta_pct,gage_A_delta_pct,mid_I_m4,openfast_I_m4,mid_I_delta_pct,gage_I_delta_pct,status";
 let out=[header],maxA=0,maxI=0,maxDz=0,maxReA=0,maxReI=0,seen=new Set();
 for(let i=0;i<31;i++){
  const x=s[i],y=g[i],n=i+1;
  if(x.segment!=="CSEG_"+String(n).padStart(2,"0")||num(y.segment)!==n)fail("SEGMENT_IDENTITY");
  const mid=(num(x.y0_m)+num(x.y1_m))/2,[A,I]=geo(x,mid),Ao=num(y.gross_area_m2),Io=num(y.gross_I_m4);
  if(!(Ao>0&&Io>0))fail("GROSS_NONPOSITIVE");
  const dA=100*(A/Ao-1),dI=100*(I/Io-1);
  if(Math.abs(dA)>=0.001||Math.abs(dI)>=0.001)fail("MIDPOINT_IDENTITY");
  maxA=Math.max(maxA,Math.abs(dA));maxI=Math.max(maxI,Math.abs(dI));
  const cc=c.filter(v=>v.segment===x.segment);
  if(cc.length!==4||new Set(cc.map(v=>v.case)).size!==4)fail("CASE_COUNT");
  for(const v of cc){
   const key=v.case+"/"+v.segment;if(seen.has(key))fail("DUP_CASE");seen.add(key);
   const z=num(v.gage_z_m),[Ag,Ig]=geo(x,z);
   maxReA=Math.max(maxReA,Math.abs(Ag-num(v.area_joint_m2)));
   maxReI=Math.max(maxReI,Math.abs(Ig-num(v.I_joint_m4)));
   maxDz=Math.max(maxDz,Math.abs(z-mid));
  }
  const v=cc.find(v=>v.case==="U09p343881_ETM_S06");if(!v)fail("REP_CASE");
  out.push([n,mid,num(v.gage_z_m),num(v.gage_z_m)-mid,A,Ao,dA,num(v.area_difference_pct),I,Io,dI,num(v.I_difference_pct),"MIDPOINT_SOURCE_ONLY"].map((v,j)=>typeof v==="number"?(j===0?String(v):v.toFixed(9)):v).join(","));
 }
 if(seen.size!==124||maxReA>=1e-9||maxReI>=1e-9)fail("GAGE_RECONSTRUCTION");
 return {csv:out.join("\n")+"\n",summary:{midpoint_rows:31,gage_rows:124,max_mid_A_pct:maxA,max_mid_I_pct:maxI,max_gage_mid_offset_m:maxDz,max_gage_A_error_m2:maxReA,max_gage_I_error_m4:maxReI,physical_pass:false}}
}
function read(){const x={};for(const [k,[file,sha]] of Object.entries(FILES)){const b=fs.readFileSync(path.join(__dirname,file));if(crypto.createHash("sha256").update(b).digest("hex")!==sha)fail("SHA_"+k);x[k]=b.toString("utf8")}return x}
if(require.main===module){
 const o=derive(read()),file=path.join(__dirname,"S10_31SEG_MIDPLANE_VS_GAGE_GEOMETRY_20261106.csv");
 if(process.argv.includes("--check")&&fs.readFileSync(file,"utf8")!==o.csv)fail("COMMITTED_CSV_MISMATCH");
 console.log(JSON.stringify(o.summary));
}
module.exports={derive,geo};
