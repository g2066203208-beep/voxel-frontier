"use strict";
/* S05: official NSF SAGE CI.CLC response metadata, hand-transcribed from MDA/RESP.
 * SOURCE LEVEL: published channel summary and RESP text; StationXML bytes not acquired.
 * This computes ONLY relative stage-1 analog pole/zero response, NOT full instrument
 * response or a verified lowest usable frequency. No seismic solver is executed.
 */
const CHANGE="2019-09-26T14:00:00Z";
const P=[[-981,1009],[-981,-1009],[-3290,1263],[-3290,-1263]];
const CHANNELS={
 HNE:{azimuth_deg:90,pre:{sensitivity:213945.4273635581,ref_hz:0.03},post:{sensitivity:214077.95043858353,ref_hz:1}},
 HNN:{azimuth_deg:0,pre:{sensitivity:213808.5679825483,ref_hz:0.03},post:{sensitivity:213941.0062834973,ref_hz:1}}
};
const EVENTS=[{id:"ci38457511",utc:"2019-07-06T00:00:00Z"},{id:"ci39493944",utc:"2020-06-24T00:00:00Z"}];
function epoch(date){const t=Date.parse(date);if(!Number.isFinite(t))throw Error("BAD_DATE");return t<Date.parse(CHANGE)?"pre":"post";}
function channel(name){if(!Object.hasOwn(CHANNELS,name))throw Error("BAD_CHANNEL");return CHANNELS[name];}
function stage1Ratio(f,referenceHz=1){
 if(!Number.isFinite(f)||f<=0||!Number.isFinite(referenceHz)||referenceHz<=0)throw Error("BAD_FREQUENCY");
 const mag=x=>-P.reduce((s,[re,im])=>s+Math.log(Math.hypot(re,2*Math.PI*x-im)),0);
 return Math.exp(mag(f)-mag(referenceHz));
}
function compute(){
 const table=EVENTS.flatMap(e=>Object.keys(CHANNELS).map(axis=>{
  const c=channel(axis),which=epoch(e.utc),d=c[which];
  return {event_id:e.id,station:"CI.CLC",axis,azimuth_deg:c.azimuth_deg,epoch:which,
   epoch_boundary_utc:CHANGE,sensitivity_counts_per_m_s2:d.sensitivity,
   sensitivity_reference_hz:d.ref_hz,sample_rate_hz:100};
 }));
 const frequency_hz=[0.1,1/6.230957762865167,0.25,1];
 return {status:"STAGE1_ANALOG_RESPONSE_METADATA_QC_NOT_LOWFREQ_CERTIFICATION",
  source_level:"Official MDA channel summary and FDSN RESP text directly read; raw StationXML/RESP bytes NOT saved or SHA256-verified",
  epoch_table:table,
  sensitivity_change_percent:Object.fromEntries(Object.entries(CHANNELS).map(([axis,c])=>[axis,100*(c.post.sensitivity/c.pre.sensitivity-1)])),
  stage1_poles_rad_s:P,stage1_zeros:0,
  stage1_analog_relative_gain_vs_1hz:frequency_hz.map(f=>({frequency_hz:f,period_s:1/f,ratio:stage1Ratio(f),relative_percent:100*(stage1Ratio(f)-1)})),
  limits:["0.03/0.05 Hz in RESP is a gain-reference frequency, not a demonstrated low-frequency cutoff",
   "Stage-1 analog PZ is not the full digitizer/FIR response or a record-specific noise and usable-bandwidth assessment",
   "Event-specific response epoch must be selected; do not rescale already corrected m/s2 CSV by sensitivity ratio",
   "No authorized site response spectrum, stationxml raw SHA256, or original waveform deconvolution audit"]};
}
function selfTest(){
 if(epoch("2019-07-06T00:00:00Z")!=="pre"||epoch("2020-06-24T00:00:00Z")!=="post"||epoch(CHANGE)!=="post")throw Error("EPOCH_BOUNDARY");
 if(channel("HNE").azimuth_deg!==90||channel("HNN").azimuth_deg!==0)throw Error("AZIMUTH");
 if(Math.abs(stage1Ratio(1)-1)>1e-12||Math.abs(stage1Ratio(.1)-1)>1e-4)throw Error("PZ_SANITY");
 for(const [fn,label] of [[()=>epoch("nonsense"),"BAD_DATE"],[()=>channel("HNZ"),"BAD_CHANNEL"],
  [()=>stage1Ratio(0),"BAD_FREQUENCY"],[()=>stage1Ratio(-1),"BAD_FREQUENCY"],[()=>stage1Ratio(NaN),"BAD_FREQUENCY"],
  [()=>stage1Ratio(1,0),"BAD_FREQUENCY"]]){
  try{fn();throw Error("NEGATIVE_ACCEPTED")}catch(e){if(e.message!==label)throw e}
 }
 return "S05_CLC_EPOCH_STAGE1_QC_PASS_3_POSITIVE_6_NEGATIVE_NOT_BANDWIDTH_PASS";
}
if(typeof module!=="undefined")module.exports={epoch,channel,stage1Ratio,compute,selfTest};

/* S05: full response from immutable original SCEDC StationXML; no seismic solver.
 * Relative gain/phase is normalized to 1 Hz. NOT a sensor bandwidth/noise PASS.
 */
function xmlTag(s,t){const m=s.match(new RegExp("<"+t+"(?:\\s[^>]*)?>([^<]+)</"+t+">"));if(!m)throw Error("XML_MISSING_"+t);return m[1].trim()}
function xmlChannel(xml,axis,utc){
 if(!["HNE","HNN"].includes(axis))throw Error("XML_BAD_AXIS");
 const matches=[...xml.matchAll(new RegExp('<Channel code="'+axis+'"([^>]*)>([\\s\\S]*?)</Channel>','g'))].filter(m=>/locationCode=""/.test(m[1]));
 if(matches.length!==1)throw Error("XML_LOCATION_AMBIGUOUS");
 const attr=matches[0][1],c=matches[0][2],start=attr.match(/startDate="([^"]+)"/),end=attr.match(/endDate="([^"]+)"/);
 if(!start||!end||!Number.isFinite(Date.parse(utc))||!(Date.parse(start[1])<=Date.parse(utc)&&Date.parse(utc)<Date.parse(end[1])))throw Error("XML_EPOCH_MISMATCH");
 const stages=[...c.matchAll(/<Stage number="(\d+)">([\s\S]*?)<\/Stage>/g)],by=Object.fromEntries(stages.map(m=>[+m[1],m[2]]));
 if(stages.length!==4||[1,2,3,4].some(i=>!by[i]))throw Error("XML_STAGE_COUNT");
 const poles=[...by[1].matchAll(/<Pole number="(\d+)">([\s\S]*?)<\/Pole>/g)].map(m=>({i:+m[1],re:+xmlTag(m[2],"Real"),im:+xmlTag(m[2],"Imaginary")}));
 const coeff=[...by[4].matchAll(/<NumeratorCoefficient i="(\d+)">([^<]+)<\/NumeratorCoefficient>/g)].map(m=>({i:+m[1],v:+m[2]}));
 if(poles.length!==4||poles.some((p,i)=>p.i!==i||!Number.isFinite(p.re)||!Number.isFinite(p.im))||
    coeff.length<2||coeff.some((p,i)=>p.i!==i||!Number.isFinite(p.v)))throw Error("XML_COEFFICIENT_INDEX");
 if(xmlTag(by[4],"Symmetry")!=="NONE")throw Error("XML_UNSUPPORTED_FIR_SYMMETRY");
 if(+xmlTag(by[4],"InputSampleRate")!==100||+xmlTag(by[4],"Factor")!==1)throw Error("XML_BAD_DECIMATION");
 if(/<Numerator>|<Denominator>/.test(by[3]))throw Error("XML_STAGE3_NONUNITY");
 const gains=[1,2,3,4].map(i=>+xmlTag(by[i],"Value"));
 if(gains.some(x=>!Number.isFinite(x)||x<=0))throw Error("XML_BAD_GAIN");
 const sens=c.match(/<InstrumentSensitivity>([\s\S]*?)<\/InstrumentSensitivity>/);
 if(!sens)throw Error("XML_NO_SENSITIVITY");
 return {axis,start:start[1],end:end[1],poles,coeff:coeff.map(x=>x.v),fs:100,gains,
  delay:+xmlTag(by[4],"Delay"),correction:+xmlTag(by[4],"Correction"),
  sensitivity:+xmlTag(sens[1],"Value"),reference_hz:+xmlTag(sens[1],"Frequency")};
}
function xmlTransfer(x,f){
 if(!Number.isFinite(f)||f<=0||f>=x.fs/2)throw Error("XML_BAD_FREQUENCY");
 const w=2*Math.PI*f;let logmag=0,phase=0;
 for(const p of x.poles){const re=-p.re,im=w-p.im;logmag-=Math.log(Math.hypot(re,im));phase-=Math.atan2(im,re)}
 let re=0,im=0;for(let k=0;k<x.coeff.length;k++){const a=-w*k/x.fs;re+=x.coeff[k]*Math.cos(a);im+=x.coeff[k]*Math.sin(a)}
 const fir=Math.hypot(re,im);if(!(fir>0))throw Error("XML_ZERO_FIR");
 return {logmag:logmag+Math.log(fir),phase:phase+Math.atan2(im,re),fir};
}
function wrap(x){return Math.atan2(Math.sin(x),Math.cos(x))}
function xmlSpectrum(x){
 const ref=xmlTransfer(x,1);
 return {axis:x.axis,epoch_start:x.start,epoch_end:x.end,fir_taps:x.coeff.length,
  gains:x.gains,stage4_delay_s:x.delay,stage4_correction_s:x.correction,
  sensitivity:x.sensitivity,sensitivity_reference_hz:x.reference_hz,
  frequencies:[0.1,1/6.230957762865167,0.25,1].map(f=>{const h=xmlTransfer(x,f);
   return {frequency_hz:f,period_s:1/f,full_relative_gain_percent:100*Math.expm1(h.logmag-ref.logmag),
    full_relative_phase_deg:wrap(h.phase-ref.phase)*180/Math.PI,
    fir_relative_gain_percent:100*(h.fir/ref.fir-1),
    phase_with_stage4_correction_deg:wrap(h.phase-ref.phase+2*Math.PI*(f-1)*x.correction)*180/Math.PI};
  })};
}
function xmlSelfTest(xml,axis,utc){
 const x=xmlChannel(xml,axis,utc),v=xmlSpectrum(x).frequencies[3];
 if(Math.abs(v.full_relative_gain_percent)>1e-10||Math.abs(v.full_relative_phase_deg)>1e-10)throw Error("XML_REFERENCE_IDENTITY");
 const bad=[
  [()=>xmlChannel(xml,"HNZ",utc),"XML_BAD_AXIS"],
  [()=>xmlChannel(xml,axis,"2000-01-01T00:00:00Z"),"XML_EPOCH_MISMATCH"],
  [()=>xmlTransfer(x,0),"XML_BAD_FREQUENCY"],
  [()=>xmlTransfer(x,50),"XML_BAD_FREQUENCY"]
 ];
 for(const [fn,code] of bad){try{fn();throw Error("NEGATIVE_ACCEPTED")}catch(e){if(e.message!==code)throw e}}
 return "3_POSITIVE_4_NEGATIVE_PASS_NOT_BANDWIDTH_PASS";
}
if(typeof module!=="undefined")Object.assign(module.exports,{xmlChannel,xmlTransfer,xmlSpectrum,xmlSelfTest});
if(typeof require==="function"&&typeof module!=="undefined"&&require.main===module){
 if(process.argv.includes("--full-xml")){
  const fs=require("fs"),crypto=require("crypto"),path=require("path"),root=process.argv[process.argv.indexOf("--full-xml")+1];
  if(!root)throw Error("NEED_REPO_ROOT");
  const records=[];
  for(const id of ["ci38457511","ci39493944"]){
   const dir=path.join(root,"research/wind-tower/experiments/T079/real-records","USGS_"+id,"CI_CLC");
   const bytes=fs.readFileSync(path.join(dir,"original/CI_station_response.xml"));
   const receipt=JSON.parse(fs.readFileSync(path.join(dir,"source_receipt.json"),"utf8"));
   const sha=crypto.createHash("sha256").update(bytes).digest("hex");
   if(sha!==receipt.files_SHA256["original/CI_station_response.xml"])throw Error("SOURCE_SHA256_MISMATCH");
   for(const axis of ["HNE","HNN"]){const xml=bytes.toString("latin1");
    records.push({event_id:id,axis,source_sha256:sha,test:xmlSelfTest(xml,axis,receipt.event_utc),
     response:xmlSpectrum(xmlChannel(xml,axis,receipt.event_utc))});}
  }
  console.log(JSON.stringify({status:"S05_FULL_STATIONXML_QC_NOT_LOWFREQ_PASS",records},null,2));
 }else console.log(JSON.stringify({test:selfTest(),result:compute()},null,2));
}
