#!/usr/bin/env node
"use strict";
// S10: source-locked partial identification of missing wind-bin load M4.
// NOT formal DLC1.2, annual load-DEL, local stress or material Miner.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const SOURCE_ERA_SHA256="e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102";
const SOURCE_M4_SHA256="d43f963fb30e16a33e87acdf6e9571710826974eee89d1f3527ab6504d85f695";

function parseCsv(src,label){
 const lines=src.replace(/^\uFEFF/,"").trimEnd().split(/\r?\n/);
 if(lines.length<2)throw Error(label+" empty");
 const keys=lines.shift().split(",");
 if(new Set(keys).size!==keys.length)throw Error(label+" duplicate header");
 return lines.map((line,i)=>{const a=line.split(",");if(a.length!==keys.length)throw Error(label+" column count "+i);return Object.fromEntries(keys.map((k,j)=>[k,a[j]]));});
}
function integer(x,label){const n=Number(x);if(!Number.isSafeInteger(n)||n<0)throw Error(label+" not nonnegative integer");return n;}
function positive(x,label){const n=Number(x);if(!Number.isFinite(n)||n<=0)throw Error(label+" not positive finite");return n;}
function close(x,y,tol,label){if(Math.abs(x-y)>tol)throw Error(label+" mismatch "+x+" vs "+y);}
function analysis(eraCsv,m4Csv){
 const e=parseCsv(eraCsv,"ERA5"),m=parseCsv(m4Csv,"M4");
 if(e.length!==31||m.length!==6)throw Error("source row count");
 const em=new Map();let total=0;
 for(const r of e){
  const bin=integer(r.bin_lower_mps,"bin"),h=integer(r.hours,"hours");
  if(bin>30||em.has(bin))throw Error("ERA bin identity");
  em.set(bin,{bin,h});
  const prob=Number(r.p_all_hours);
  if(!Number.isFinite(prob)||prob<0)throw Error("ERA probability nonnegative finite");
  close(prob,h/184080,1e-11,"ERA probability");
  total+=h;
 }
 if(total!==184080||em.size!==31||[...Array(31).keys()].some(i=>!em.has(i)))throw Error("ERA total/coverage");
 const op=[...em.values()].filter(r=>r.bin>=4&&r.bin<25);
 const opHours=op.reduce((s,r)=>s+r.h,0);
 if(opHours!==106900)throw Error("operating-window hours");
 const knownBins=[9,11,19],knownHours=knownBins.reduce((s,i)=>s+em.get(i).h,0);
 if(knownHours!==7164)throw Error("known-bin hours");
 const missing=op.filter(r=>!knownBins.includes(r.bin));
 const positiveMissing=missing.filter(r=>r.h>0),missingHours=missing.reduce((s,r)=>s+r.h,0);
 if(missingHours!==99736||positiveMissing.length!==13||missing.filter(r=>r.h===0).length!==5)throw Error("missing-bin identity");
 const pOp=opHours/184080,pMissing=missingHours/184080;
 const byChannel={},seen=new Set(),channels=["TwrBsMxt","TwrBsMyt"];
 for(const r of m){
  if(!channels.includes(r.channel))throw Error("unexpected channel");
  const bin=integer(r.wind_bin_mps,"M4 bin"),id=r.channel+"|"+bin;
  if(!knownBins.includes(bin)||seen.has(id))throw Error("duplicate/missing M4 identity");
  seen.add(id);
  if(integer(r.historic_era5_hours_21y,"M4 hours")!==em.get(bin).h)throw Error("M4 ERA hours mismatch");
  if(r.formal_DLC12_status!=="NOT_VALIDATED"||r.material_damage_status!=="NOT_COMPUTABLE")throw Error("false physical status");
  const moment=positive(r.six_seed_m4_mean_MNm4,"M4 moment"),del=positive(r.six_seed_power_mean_DEL_m4_MNm,"M4 DEL");
  close(Math.pow(del,4),moment,Math.max(1e-4,moment*1e-8),"M4/DEL");
  const weighted=moment*em.get(bin).h/184080;
  close(weighted,positive(r.known_bin_contribution_p_all_times_m4_MNm4,"weighted M4"),Math.max(1e-6,weighted*1e-9),"weighted source");
  (byChannel[r.channel]??=[]).push({bin,moment,del,weighted});
 }
 if(seen.size!==6)throw Error("missing M4 row");
 const summaries=[],detailRows=[];
 for(const channel of channels){
  const obs=byChannel[channel].sort((a,b)=>a.bin-b.bin);
  if(obs.length!==3)throw Error("M4 incomplete channel");
  const K=obs.reduce((s,r)=>s+r.weighted,0);
  const d50=Math.pow(K/pMissing,.25),d10=Math.pow(9*K/pMissing,.25),d90=Math.pow(K/(9*pMissing),.25);
  const share=d=>K/(K+pMissing*Math.pow(d,4));
  close(share(d50),.5,1e-12,"50pct");close(share(d10),.1,1e-12,"10pct");close(share(d90),.9,1e-12,"90pct");
  const lowHours=[4,5,6,7,8].reduce((s,i)=>s+em.get(i).h,0),lowThreshold=Math.pow(K/(lowHours/184080),.25);
  summaries.push({channel,K_all:K,K_cond:K/pOp,pMissing,pMissingCond:pMissing/pOp,d50,d10,d90,lowThreshold,observed9:obs[0].del});
  for(const r of positiveMissing){const p=r.h/184080,threshold=Math.pow(K/p,.25);detailRows.push({channel,bin:r.bin,hours:r.h,p_all:p,threshold,ratio_to_9mps:threshold/obs[0].del,K_all:K});}
 }
 return {totalHours:total,opHours,knownHours,missingHours,positiveMissingBins:positiveMissing.length,zeroMissingBins:5,summaries,detailRows};
}
function makeCsv(a){
 const header="channel,missing_bin_lower_mps,era5_hours_21y,p_all_hours,DEL_threshold_equal_all_3_known_bins_MNm,threshold_over_observed_9mps_DEL,known_partial_M4_all_hours_MNm4,formal_DLC12_status";
 return [header,...a.detailRows.map(r=>[r.channel,r.bin,r.hours,r.p_all.toFixed(12),r.threshold.toFixed(9),r.ratio_to_9mps.toFixed(9),r.K_all.toFixed(9),"NOT_VALIDATED"].join(","))].join("\n")+"\n";
}
function tests(eraCsv,m4Csv){
 const a=analysis(eraCsv,m4Csv);
 if(a.detailRows.length!==26||a.knownHours!==7164||a.missingHours!==99736)throw Error("positive oracle");
 const expected={TwrBsMxt:125.606637743,TwrBsMyt:209257.299448};
 for(const s of a.summaries)close(s.K_all,expected[s.channel],1e-5,"historical K");
 const altered=[
  [eraCsv.trimEnd().split(/\r?\n/).slice(0,-1).join("\n")+"\n",m4Csv],
  [eraCsv.replace("26927,0.146278791830","26926,0.146278791830"),m4Csv],
  [eraCsv,m4Csv.replace("TwrBsMxt,11,","TwrBsMxt,9,")],
  [eraCsv,m4Csv.replace("2276.587585619","-1")],
  [eraCsv,m4Csv.replace("NOT_VALIDATED","VALIDATED")],
  [eraCsv,m4Csv.replace("70.9393002559","71.9393002559")],
  [eraCsv.replace("0.146278791830","0.999999999999"),m4Csv],
  [eraCsv.replace("5736,0.031160365059","NaN,0.031160365059"),m4Csv],
  [eraCsv,m4Csv.trimEnd().split(/\r?\n/).slice(0,-1).join("\n")+"\n"]
 ];
 for(let i=0;i<altered.length;i++){
  if(altered[i][0]===eraCsv&&altered[i][1]===m4Csv)throw Error("negative fixture unchanged "+i);
  let rejected=false;try{analysis(altered[i][0],altered[i][1])}catch(e){rejected=true}
  if(!rejected)throw Error("negative fixture accepted "+i);
 }
 if(makeCsv(a).trimEnd().split("\n").length!==27)throw Error("26 rows");
 return {positive_oracles:8,negative_rejections:altered.length,output_rows:26,source_rows:37};
}

if(require.main===module){
 const p1=process.argv[2]||path.join(__dirname,"S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv");
 const p2=process.argv[3]||path.join(__dirname,"partial-annual-load-diagnostic-20261102/S10_REAL_18NTM_3BIN_PARTIAL_M4_BY_CHANNEL_20261102.csv");
 const out=process.argv[4]||path.join(__dirname,"S10_MISSING_BIN_M4_IDENTIFIABILITY_20261107.csv");
 const s1=fs.readFileSync(p1,"utf8"),s2=fs.readFileSync(p2,"utf8");
 const sha=s=>crypto.createHash("sha256").update(s,"utf8").digest("hex");
 if(sha(s1)!==SOURCE_ERA_SHA256||sha(s2)!==SOURCE_M4_SHA256)throw Error("source SHA256 mismatch");
 const checks=tests(s1,s2),a=analysis(s1,s2),csv=makeCsv(a);
 fs.writeFileSync(out,csv,"utf8");
 console.log(JSON.stringify({status:"PARTIAL_IDENTIFICATION_NOT_ANNUAL_DEL_OR_MINER",source_sha256:{era:sha(s1),m4:sha(s2)},tests:checks,summary:a.summaries,output_sha256:sha(csv)},null,2));
}
module.exports={analysis,tests,makeCsv};
