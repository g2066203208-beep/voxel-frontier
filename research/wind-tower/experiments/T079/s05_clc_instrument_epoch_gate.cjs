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
if(typeof require==="function"&&typeof module!=="undefined"&&require.main===module){console.log(JSON.stringify({test:selfTest(),result:compute()},null,2));}
