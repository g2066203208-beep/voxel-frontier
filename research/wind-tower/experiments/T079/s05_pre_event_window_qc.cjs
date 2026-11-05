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

/* S05 independent numerical/input-decimation sensitivity, NOT design-wave QC.
   The 0.005s reference is linearly interpolated from 0.01s measured samples:
   it adds NO new instrumental bandwidth. 0.02/0.04s use raw phase-zero
   decimation WITHOUT anti-alias filtering; deviations combine forcing
   representation/aliasing and Newmark integration, NOT pure solver error. */
function strideSamples(a,factor) {
 if(!Array.isArray(a)||a.length<2||!a.every(Number.isFinite)||!Number.isInteger(factor)||factor<1||(a.length-1)%factor!==0)throw Error("DECIMATION_INPUT");
 return a.filter((_,i)=>i%factor===0);
}
function linearHalfStep(a) {
 if(!Array.isArray(a)||a.length<2||!a.every(Number.isFinite))throw Error("INTERPOLATION_INPUT");
 const out=new Array(2*a.length-1);
 for(let i=0;i<a.length;i++){out[2*i]=a[i];if(i+1<a.length)out[2*i+1]=(a[i]+a[i+1])/2;}
 return out;
}
function timeStepQC(rawMap) {
 const rows=[],sources=[];
 for(const [event,axis,sha] of SOURCES){
  const a=parse(rawMap[event+"_"+axis]);
  const b=corrected(a,20);
  const fine=linearHalfStep(b.a),coarse2=strideSamples(b.a,2),coarse4=strideSamples(b.a,4);
  sources.push({event_id:event,component:axis,source_sha256_inherited:sha,npts:a.length,pre20_offset_m_s2:b.offset});
  for(const T of PERIODS){
   const s005=spectrum(fine,T,.005),s01=spectrum(b.a,T,.01),s02=spectrum(coarse2,T,.02),s04=spectrum(coarse4,T,.04);
   if(!(s005>0))throw Error("REFERENCE_ZERO");
   rows.push({event_id:event,component:axis,period_s:T,psa_005_m_s2:s005,psa_01_m_s2:s01,psa_02_m_s2:s02,psa_04_m_s2:s04,
    relative_01_vs_005:Math.abs(s01/s005-1),relative_02_vs_005:Math.abs(s02/s005-1),relative_04_vs_005:Math.abs(s04/s005-1)});
  }
 }
 const max={};
 for(const key of ["relative_01_vs_005","relative_02_vs_005","relative_04_vs_005"])
  max[key]=rows.reduce((a,b)=>a[key]>=b[key]?a:b);
 return {sources,rows,max};
}
function selfTestTimeStep(){
 const ramp=[0,1,2,3,4,5,6,7,8];
 if(JSON.stringify(linearHalfStep(ramp))!==JSON.stringify(Array.from({length:17},(_,i)=>i/2)))throw Error("MIDPOINT_ORACLE");
 if(JSON.stringify(strideSamples(ramp,2))!==JSON.stringify([0,2,4,6,8]))throw Error("STRIDE_ORACLE");
 if(spectrum(linearHalfStep(Array(9).fill(0)),6,.005)!==0)throw Error("ZERO_ORACLE");
 const bad=[[()=>strideSamples(ramp,0),"DECIMATION_INPUT"],[()=>strideSamples(ramp,3),"DECIMATION_INPUT"],[()=>strideSamples([0,NaN,2],2),"DECIMATION_INPUT"],[()=>linearHalfStep([0,Infinity]),"INTERPOLATION_INPUT"]];
 for(const [fn,expected] of bad){try{fn();throw Error("NEGATIVE_ACCEPTED")}catch(e){if(e.message!==expected)throw e}}
 return "S05_DT_QC_SELFTEST_PASS_3_POSITIVE_4_NEGATIVE";
}


/* S05 anti-alias diagnostic on original 0.01 s samples. Fixed 201-tap
   symmetric Blackman-windowed sinc low-pass, cutoff 9 Hz at fs=100 Hz;
   DC-normalized, reflection at endpoints, centered zero-phase convolution.
   Decimate 4:1 at original t=0 phase to dt=0.04 s, no extrapolation.
   This is a sensitivity experiment, NOT a verified instrument correction. */
const AA_CUTOFF_HZ=9,AA_TAPS=201,AA_FS_HZ=100;
function firKernel(cutoff=AA_CUTOFF_HZ,taps=AA_TAPS){
 if(!Number.isFinite(cutoff)||cutoff<=0||cutoff>=AA_FS_HZ/8||!Number.isInteger(taps)||taps<3||taps%2!==1)throw Error("FIR_PARAMETERS");
 const w=[],M=taps-1;let sum=0;
 for(let i=0;i<taps;i++){
  const x=i-M/2,sinc=x===0?2*cutoff/AA_FS_HZ:Math.sin(2*Math.PI*cutoff*x/AA_FS_HZ)/(Math.PI*x);
  const win=.42-.5*Math.cos(2*Math.PI*i/M)+.08*Math.cos(4*Math.PI*i/M);
  w.push(sinc*win);sum+=sinc*win;
 }
 return w.map(x=>x/sum);
}
function firGain(h,f){
 if(!Array.isArray(h)||h.length<3||!Number.isFinite(f)||f<0||f>AA_FS_HZ/2)throw Error("FIR_GAIN_INPUT");
 const H=(h.length-1)/2;let re=0,im=0;
 for(let j=0;j<h.length;j++){const a=2*Math.PI*f*(j-H)/AA_FS_HZ;re+=h[j]*Math.cos(a);im-=h[j]*Math.sin(a)}
 return Math.hypot(re,im);
}
function zeroPhaseFIR(a,h){
 if(!Array.isArray(a)||a.length<2||!a.every(Number.isFinite)||!Array.isArray(h)||h.length<3||h.length%2!==1||!h.every(Number.isFinite))throw Error("FIR_INPUT");
 const n=a.length,H=(h.length-1)/2,out=new Array(n);
 for(let i=0;i<n;i++){
  let sum=0;
  for(let j=-H;j<=H;j++){
   let k=i+j;
   while(k<0||k>=n){if(k<0)k=-k;if(k>=n)k=2*n-2-k}
   sum+=h[j+H]*a[k];
  }
  out[i]=sum;
 }
 return out;
}
function antiAliasQC(rawMap){
 const h=firKernel(),rows=[],src=[];
 for(const [ev,axis,sha] of SOURCES){
  const a=parse(rawMap[ev+"_"+axis]),base=corrected(a,20);
  const filtered01=zeroPhaseFIR(base.a,h);
  const filtered04=strideSamples(filtered01,4),unfiltered04=strideSamples(base.a,4);
  src.push({event_id:ev,component:axis,source_sha256_inherited:sha,npts:a.length,dt_s:DT,
   pre20_offset_m_s2:base.offset,filtered_npts:filtered04.length});
  for(const T of PERIODS){
   const p01=spectrum(base.a,T,.01),pf01=spectrum(filtered01,T,.01),
         pf04=spectrum(filtered04,T,.04),pu04=spectrum(unfiltered04,T,.04);
   if(!(p01>0&&pf01>0))throw Error("NONPOSITIVE_PSA");
   rows.push({event_id:ev,component:axis,period_s:T,
    psa_unfiltered_01_m_s2:p01,psa_filtered_01_m_s2:pf01,
    psa_filtered_04_m_s2:pf04,psa_unfiltered_04_m_s2:pu04,
    filter_effect_relative:Math.abs(pf01/p01-1),
    filtered04_vs_filtered01_relative:Math.abs(pf04/pf01-1),
    unfiltered04_vs_unfiltered01_relative:Math.abs(pu04/p01-1)});
  }
 }
 const max={};
 for(const key of ["filter_effect_relative","filtered04_vs_filtered01_relative","unfiltered04_vs_unfiltered01_relative"])
  max[key]=rows.reduce((a,b)=>a[key]>=b[key]?a:b);
 return {source:src,method:{fs_hz:AA_FS_HZ,cutoff_hz:AA_CUTOFF_HZ,taps:AA_TAPS,
  window:"Blackman",kernel:"symmetric DC-normalized sinc",boundary:"reflect",phase:"centered zero-phase",
  decimation_factor:4,dt_original_s:.01,dt_decimated_s:.04,
  gain_2hz:firGain(h,2),gain_4hz:firGain(h,4),gain_9hz:firGain(h,9),
  gain_12p5hz:firGain(h,12.5),gain_20hz:firGain(h,20)},rows,max};
}
function selfTestAntiAlias(){
 const h=firKernel();
 if(Math.abs(h.reduce((a,b)=>a+b,0)-1)>1e-12)throw Error("DC_GAIN_ORACLE");
 if(Math.abs(firGain(h,2)-1)>1e-3||firGain(h,12.5)>1e-3||firGain(h,20)>1e-4)throw Error("FREQUENCY_GAIN_ORACLE");
 const n=1001,constant=Array(n).fill(2.75),f=zeroPhaseFIR(constant,h);
 if(f.some(x=>Math.abs(x-2.75)>1e-11))throw Error("REFLECTION_DC_ORACLE");
 const low=Array.from({length:n},(_,i)=>Math.sin(2*Math.PI*2*i/AA_FS_HZ));
 const high=Array.from({length:n},(_,i)=>Math.sin(2*Math.PI*20*i/AA_FS_HZ));
 const ratio=(x,y)=>Math.sqrt(x.slice(200,800).reduce((s,v,i)=>s+v*v,0)/
  y.slice(200,800).reduce((s,v)=>s+v*v,0));
 if(Math.abs(ratio(zeroPhaseFIR(low,h),low)-1)>1e-3)throw Error("PASSBAND_TIME_ORACLE");
 if(ratio(zeroPhaseFIR(high,h),high)>1e-3)throw Error("STOPBAND_TIME_ORACLE");
 if(spectrum(Array(5001).fill(0),6,.04)!==0)throw Error("ZERO_SPECTRUM_ORACLE");
 const bad=[[()=>firKernel(12.5,201),"FIR_PARAMETERS"],[()=>firKernel(9,200),"FIR_PARAMETERS"],
 [()=>zeroPhaseFIR([1,NaN],h),"FIR_INPUT"],[()=>zeroPhaseFIR([1],h),"FIR_INPUT"],
 [()=>firGain(h,-1),"FIR_GAIN_INPUT"],[()=>antiAliasQC({}),"SOURCE_TYPE"]];
 for(const [fn,expected] of bad){try{fn();throw Error("NEGATIVE_ACCEPTED")}catch(e){if(e.message!==expected)throw e}}
 return "S05_ANTIALIAS_SELFTEST_PASS_5_POSITIVE_6_NEGATIVE";
}

if(typeof module!=="undefined"&&module.exports)module.exports={parse,corrected,spectrum,drift,compute,selfTest,timeStepQC,selfTestTimeStep,antiAliasQC,selfTestAntiAlias,firKernel,firGain,zeroPhaseFIR,SOURCES,PERIODS};
if(typeof require==="function"&&typeof module!=="undefined"&&require.main===module){
 const fs=require("fs"),path=require("path"),crypto=require("crypto");
 if(process.argv.includes("--self-test")){console.log(selfTest(),selfTestTimeStep());process.exit(0)}
 const root=process.argv[2];if(!root)throw Error("USAGE_NODE_SCRIPT_REAL_RECORDS_ROOT");
 const map={};
 for(const [ev,axis,expected] of SOURCES){
  const file=path.join(root,"USGS_"+ev,"CI_CLC","CI_CLC_"+axis+"_accel_mps2.csv");
  const bytes=fs.readFileSync(file),actual=crypto.createHash("sha256").update(bytes).digest("hex");
  if(actual!==expected)throw Error("SOURCE_SHA256_MISMATCH_"+ev+"_"+axis);
  map[ev+"_"+axis]=bytes.toString("utf8");
 }
 console.log(JSON.stringify(process.argv.includes("--anti-alias-qc")?{test:selfTestAntiAlias(),result:antiAliasQC(map)}:process.argv.includes("--dt-qc")?{test:selfTestTimeStep(),result:timeStepQC(map)}:{test:selfTest(),result:compute(map)},null,2));
}
