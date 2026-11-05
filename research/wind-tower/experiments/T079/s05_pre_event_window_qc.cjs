"use strict";
/* S05 research diagnostic: 5/10/20-second pre-event DC removal sensitivity.
   Input: official FDSN-derived acceleration CSVs, not approved site records.
   Node: node s05_pre_event_window_qc.cjs /path/to/T079/real-records
   V8: pure exports can be independently executed without Node. */
const PERIODS=[4,6,6.230957762865167,8,10], WINDOWS=[5,10,20], DT=.01, N=20001;
const SOURCES=[
["ci38457511","HNE","fb0c91fe588ccb4f6bed3d4ac77c4bc148231d8e5df6be19aa9cf3bc3d4c25ef"],
["ci38457511","HNN","d6250274d578b87e4310eadcca5a910dd38cd69ad639dbca435af8e8a0d81e30"],
["ci39493944","HNE","60a1201a67da19c30c2bfc1e2889b6c492c03d0a5133c296dc4fc68bee3426ae"],
["ci39493944","HNN","e54bc509e573daecb31254cdc694d7678aa3460dab5460882e8d1abf97e91e12"]];
function parse(raw) {
 if(typeof raw!=="string")throw Error("SOURCE_TYPE");
 const lines=raw.trimEnd().split(/\r?\n/);
 if(lines[0]!=="time_s,accel")throw Error("HEADER");
 if(lines.length!==N+1)throw Error("NPTS");
 const a=[];
 for(let i=1;i<lines.length;i++){
  const s=lines[i].split(",");if(s.length!==2)throw Error("COLUMN_COUNT");
  const t=Number(s[0]),v=Number(s[1]);
  if(!Number.isFinite(t)||!Number.isFinite(v))throw Error("NONFINITE");
  if(Math.abs(t-(i-1)*DT)>1e-7)throw Error("TIME_GRID");
  a.push(v);
 }
 return a;
}
function corrected(a,sec) {
 const n=Math.round(sec/DT);
 if(n<2||n>=a.length||!Number.isInteger(n))throw Error("PREWINDOW");
 const mean=a.slice(0,n).reduce((x,y)=>x+y,0)/n;
 return {offset:mean,a:a.map(x=>x-mean)};
}
function spectrum(a,T,dt=DT) {
 if(a.length<2||!(T>0)||!(dt>0)||!a.every(Number.isFinite))throw Error("SDOF_INPUT");
 const w=2*Math.PI/T,k=w*w,c=.1*w,den=1+.5*dt*c+.25*dt*dt*k;
 let u=0,v=0,q=-a[0],peak=0;
 for(let i=1;i<a.length;i++){
  const up=u+dt*v+.25*dt*dt*q,vp=v+.5*dt*q;
  const nq=(-a[i]-c*vp-k*up)/den;
  u=up+.25*dt*dt*nq;v=vp+.5*dt*nq;q=nq;
  if(Math.abs(u)>peak)peak=Math.abs(u);
 }
 return k*peak;
}
function drift(a) {
 let u=0,v=0;
 for(let i=1;i<a.length;i++){
  const nv=v+.5*(a[i-1]+a[i])*DT;
  u+=.5*(v+nv)*DT;v=nv;
 }
 return {end_velocity_m_s:v,end_displacement_m:u};
}
function compute(rawMap) {
 const out=[];
 for(const [event,axis,sha] of SOURCES){
  const key=event+"_"+axis,raw=rawMap[key];
  const a=parse(raw);
  const cases={raw:{offset:0,a}};
  for(const sec of WINDOWS)cases["pre"+sec]=corrected(a,sec);
  const spectral=PERIODS.map(T=>{
   const v={period_s:T};
   for(const [label,datum] of Object.entries(cases))v[label+"_psa_m_s2"]=spectrum(datum.a,T);
   const base=v.pre20_psa_m_s2;
   for(const label of ["raw","pre5","pre10"])v[label+"_vs_pre20_relative"]=base>0?Math.abs(v[label+"_psa_m_s2"]-base)/base:null;
   return v;
  });
  out.push({event_id:event,station:"CI.CLC",component:axis,source_sha256_inherited:sha,
   npts:a.length,dt_s:DT,baseline_offsets_m_s2:Object.fromEntries(Object.entries(cases).map(([k,v])=>[k,v.offset])),
   end_drift:Object.fromEntries(Object.entries(cases).map(([k,v])=>[k,drift(v.a)])),spectra:spectral});
 }
 const pairT1=out.filter(x=>x.component==="HNE").map(x=>{
  const y=out.find(z=>z.event_id===x.event_id&&z.component==="HNN");
  const i=2;const gm={event_id:x.event_id,period_s:PERIODS[i]};
  for(const label of ["raw","pre5","pre10","pre20"])
   gm[label+"_gm_psa_m_s2"]=Math.sqrt(x.spectra[i][label+"_psa_m_s2"]*y.spectra[i][label+"_psa_m_s2"]);
  gm.pre5_vs_pre20_relative=Math.abs(gm.pre5_gm_psa_m_s2/gm.pre20_gm_psa_m_s2-1);
  gm.pre10_vs_pre20_relative=Math.abs(gm.pre10_gm_psa_m_s2/gm.pre20_gm_psa_m_s2-1);
  return gm;
 });
 return {components:out,conditional_proxy_T1_pair_gm:pairT1};
}
function selfTest(){
 const a=Array.from({length:N},(_,i)=>Math.sin(i*.031)+.25);
 const p=corrected(a,5),q=corrected(a.map(v=>v+3),5);
 if(Math.abs(q.offset-p.offset-3)>1e-12)throw Error("SHIFT_INVARIANT");
 if(Math.max(...p.a.map((v,i)=>Math.abs(v-q.a[i])))>1e-12)throw Error("DC_INVARIANT");
 if(spectrum(Array(N).fill(0),6)!==0)throw Error("ZERO_SPECTRUM");
 for(const [bad,expected] of [["time_s,accel\n0,1\n","NPTS"],["bad\n","HEADER"]]){
  try{parse(bad);throw Error("NEGATIVE_ACCEPTED")}catch(e){if(e.message!==expected)throw e}
 }
 try{corrected(a,300);throw Error("NEGATIVE_ACCEPTED")}catch(e){if(e.message!=="PREWINDOW")throw e}
 return "S05_PREWINDOW_SELFTEST_PASS_SHIFT_ZERO_3_NEGATIVE";
}
if(typeof module!=="undefined"&&module.exports)module.exports={parse,corrected,spectrum,drift,compute,selfTest,SOURCES,PERIODS};
if(typeof require==="function"&&typeof module!=="undefined"&&require.main===module){
 const fs=require("fs"),path=require("path"),crypto=require("crypto");
 if(process.argv.includes("--self-test")){console.log(selfTest());process.exit(0)}
 const root=process.argv[2];if(!root)throw Error("USAGE_NODE_SCRIPT_REAL_RECORDS_ROOT");
 const map={};
 for(const [ev,axis,expected] of SOURCES){
  const file=path.join(root,"USGS_"+ev,"CI_CLC","CI_CLC_"+axis+"_accel_mps2.csv");
  const bytes=fs.readFileSync(file),actual=crypto.createHash("sha256").update(bytes).digest("hex");
  if(actual!==expected)throw Error("SOURCE_SHA256_MISMATCH_"+ev+"_"+axis);
  map[ev+"_"+axis]=bytes.toString("utf8");
 }
 console.log(JSON.stringify({test:selfTest(),result:compute(map)},null,2));
}
