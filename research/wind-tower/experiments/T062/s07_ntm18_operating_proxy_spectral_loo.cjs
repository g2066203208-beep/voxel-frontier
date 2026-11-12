#!/usr/bin/env node
"use strict";
// S07: historical 18 NTM case-matched operating-state vs tower-base My spectral RMS.
// NO new OpenFAST run; NOT aerodynamic force, material fatigue, IEC DLC1.2 or causal control effect.
// Usage: node s07_ntm18_operating_proxy_spectral_loo.cjs spectral36.csv operating18.csv [summary.csv]
const fs=require("node:fs"),crypto=require("node:crypto");
const EXPECT={
 spectral:"c3de99d45c70675f6a95a767e73dcfc50d57d07b4f33438ee705690b694ae622",
 operating:"0f577f3197870a1350c740c2e0c118073fb9b6f796b4c471765c6f616d5a1b04"
};
const BINS=["U09p343881","U11p4","U19p202140"];
function check(p,m){if(!p)throw Error(m);}
function parseCsv(s){
 const lines=s.trim().split(/\r?\n/),headers=lines.shift().split(",");
 check(headers.length===new Set(headers).size,"DUPLICATE_COLUMN");
 return lines.map(line=>{
  const fields=line.split(",");check(fields.length===headers.length,"CSV_WIDTH");
  return Object.fromEntries(headers.map((h,i)=>[h,fields[i]]));
 });
}
function number(x){const n=Number(x);check(x!==""&&Number.isFinite(n),"NONFINITE");return n;}
function mean(a){return a.reduce((s,x)=>s+x,0)/a.length;}
function corr(a,b){
 check(a.length===b.length&&a.length>=3,"CORR_LENGTH");
 const x=mean(a),y=mean(b),ssx=a.reduce((s,v)=>s+(v-x)**2,0),ssy=b.reduce((s,v)=>s+(v-y)**2,0);
 check(ssx>1e-16&&ssy>1e-16,"CORR_DEGENERATE");
 return a.reduce((s,v,i)=>s+(v-x)*(b[i]-y),0)/Math.sqrt(ssx*ssy);
}
function loo(a,key){
 let base=0,model=0;
 for(let i=0;i<a.length;i++){
  const tr=a.filter((_,j)=>i!==j),xm=mean(tr.map(r=>r[key])),ym=mean(tr.map(r=>r.rms));
  const den=tr.reduce((s,r)=>s+(r[key]-xm)**2,0);
  check(den>1e-16,"LOO_SINGULAR");
  const slope=tr.reduce((s,r)=>s+(r[key]-xm)*(r.rms-ym),0)/den;
  const predicted=ym+slope*(a[i][key]-xm);
  base+=(a[i].rms-ym)**2;model+=(a[i].rms-predicted)**2;
 }
 return {baseline_rmse:Math.sqrt(base/a.length),model_rmse:Math.sqrt(model/a.length),rmse_ratio:Math.sqrt(model/base)};
}
function exactPerm(a,b){
 check(a.length===6&&b.length===6,"PERM_6");
 const observed=Math.abs(corr(a,b)),used=Array(6).fill(false),perm=[],out={total:0,extreme:0};
 function rec(){
  if(perm.length===6){out.total++;if(Math.abs(corr(a,perm))>=observed-1e-12)out.extreme++;return;}
  for(let i=0;i<6;i++)if(!used[i]){used[i]=true;perm.push(b[i]);rec();perm.pop();used[i]=false;}
 }
 rec();check(out.total===720,"PERM_COUNT");return out;
}
function analyze(spectral,operating){
 check(spectral.length===36&&operating.length===18,"SOURCE_ROWS");
 const om=new Map();for(const x of operating){check(!om.has(x.case),"DUP_OPERATING");om.set(x.case,x);}
 const by=new Map(BINS.map(b=>[b,[]])),seen=new Set();
 for(const x of spectral){
  check(["TwrBsMxt","TwrBsMyt"].includes(x.channel),"SPECTRAL_CHANNEL");
  const k=x.case+"|"+x.channel;check(!seen.has(k),"DUP_SPECTRAL");seen.add(k);
  const m=/^(U09p343881|U11p4|U19p202140)_NTM_S(0[1-6])$/.exec(x.case);
  check(m&&m[1]===x.wind_bin,"CASE_BIN_ID");
  if(x.channel!=="TwrBsMyt")continue;
  const o=om.get(x.case);check(o&&o.source_outb_sha256&&/^[a-f0-9]{64}$/.test(o.source_outb_sha256),"UNMATCHED_ORIGINAL_OUTB_ID");
  check(number(o.n_samples)===12001&&number(o.first_time_s)===100&&number(o.last_time_s)===700&&number(o.dt_s)===0.05,"TIME_ID");
  check(number(o.power_rotor_active_fraction)===1,"OPERATING_HEURISTIC");
  const r={case:x.case,bin:m[1],pitch:number(o.BldPitch1_mean),power:number(o.GenPwr_mean),rms:number(x.band_rms_kNm),reaction_mean:number(x.mean_kNm)};
  check(r.rms>0,"RMS_POSITIVE");by.get(m[1]).push(r);
 }
 check(om.size===18&&[...by.values()].every(a=>a.length===6),"SEED_COMPLETENESS");
 const results=[];
 for(const bin of BINS){
  const a=by.get(bin).sort((x,y)=>x.case.localeCompare(y.case));
  check(a.every((r,i)=>r.case.endsWith("_S0"+(i+1))),"SEED_ID");
  const pr=corr(a.map(r=>r.pitch),a.map(r=>r.rms)),gr=corr(a.map(r=>r.power),a.map(r=>r.rms));
  const pp=exactPerm(a.map(r=>r.pitch),a.map(r=>r.rms)),gp=exactPerm(a.map(r=>r.power),a.map(r=>r.rms));
  results.push({bin,n:6,pitch_mean_deg:mean(a.map(r=>r.pitch)),power_mean_kW:mean(a.map(r=>r.power)),
   reaction_mean_kNm:mean(a.map(r=>r.reaction_mean)),band_rms_mean_kNm:mean(a.map(r=>r.rms)),
   pitch_r:pr,pitch_permutation_p:pp.extreme/pp.total,pitch_extreme:pp.extreme,
   pitch_loo_rmse_ratio:loo(a,"pitch").rmse_ratio,
   power_r:gr,power_permutation_p:gp.extreme/gp.total,power_extreme:gp.extreme,
   power_loo_rmse_ratio:loo(a,"power").rmse_ratio});
 }
 return results;
}
function test(){
 const a=[{rms:1,pitch:1,power:1},{rms:2,pitch:2,power:2},{rms:3,pitch:3,power:3},{rms:4,pitch:4,power:4},{rms:5,pitch:5,power:5},{rms:6,pitch:6,power:6}];
 check(Math.abs(corr(a.map(x=>x.pitch),a.map(x=>x.rms))-1)<1e-12,"CORR_ORACLE");
 check(loo(a,"pitch").model_rmse<1e-12,"LOO_ORACLE");
 check(exactPerm(a.map(x=>x.pitch),a.map(x=>x.rms)).extreme===2,"PERM_ORACLE");
 for(const f of [()=>number("NaN"),()=>parseCsv("a,a\n1,2"),()=>corr([1,1,1],[1,2,3])]){
  let rejected=false;try{f();}catch(e){rejected=true;}check(rejected,"NEGATIVE_TEST_FAILED");
 }
}
function main(args){
 test();check(args.length>=2&&args.length<=3,"USAGE: spectral36.csv operating18.csv [summary.csv]");
 const raw=args.slice(0,2).map(p=>fs.readFileSync(p)),actual=raw.map(b=>crypto.createHash("sha256").update(b).digest("hex"));
 check(actual[0]===EXPECT.spectral&&actual[1]===EXPECT.operating,"SOURCE_SHA256_MISMATCH");
 const rows=analyze(parseCsv(raw[0].toString("utf8")),parseCsv(raw[1].toString("utf8")));
 const fields=Object.keys(rows[0]),csv=[fields.join(","),...rows.map(r=>fields.map(k=>typeof r[k]==="number"?Number.isInteger(r[k])?String(r[k]):r[k].toFixed(9):r[k]).join(","))].join("\n")+"\n";
 if(args[2])fs.writeFileSync(args[2],csv);
 process.stdout.write(csv);process.stderr.write("PASS: 18 source-paired cases, 3x720 exact permutations, 36 leave-one-out predictions, 3 rejection tests; no physical PASS\\n");
}
if(require.main===module)main(process.argv.slice(2));
module.exports={analyze,parseCsv,corr,loo,exactPerm,test};
