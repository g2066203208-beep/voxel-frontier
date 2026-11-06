#!/usr/bin/env node
"use strict";
// S10 scenario priority, NOT a missing-load prediction or formal DLC1.2.
const N=184080,KNOWN=[9,11,19],QMAX=2;
const ERA_SHA="e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102",THR_SHA="69fe2ba8077df9cfe9122f1aafb03f315cd143f8313a557763954560b5870b60",M4_SHA="d43f963fb30e16a33e87acdf6e9571710826974eee89d1f3527ab6504d85f695";
function parse(s,label){
 const lines=s.replace(/^\uFEFF/,"").trimEnd().split(/\r?\n/),keys=lines.shift().split(",");
 if(lines.length===0||new Set(keys).size!==keys.length)throw Error(label+" header");
 return lines.map((l,i)=>{const a=l.split(",");if(a.length!==keys.length)throw Error(label+" width "+i);return Object.fromEntries(keys.map((k,j)=>[k,a[j]]));});
}
function num(x,label,zero=false){
 if(x===undefined||String(x).trim()==="")throw Error(label+" empty");
 const v=Number(x);if(!Number.isFinite(v)||(zero?v<0:v<=0))throw Error(label+" invalid");return v;
}
function integer(x,label){const v=num(x,label,true);if(!Number.isSafeInteger(v))throw Error(label+" integer");return v;}
function near(x,y,rel=1e-8){if(Math.abs(x-y)>rel*Math.max(1,Math.abs(y)))throw Error("mismatch "+x+" "+y);}
function analyse(era,thr,m4){
 const e=parse(era,"ERA"),t=parse(thr,"THR"),m=parse(m4,"M4");
 if(e.length!==31||t.length!==26||m.length!==6)throw Error("row counts");
 const hh=new Map();let total=0;
 for(const r of e){const b=integer(r.bin_lower_mps,"bin"),h=integer(r.hours,"h");if(b>30||hh.has(b))throw Error("ERA bin");
  near(num(r.p_all_hours,"p",true),h/N,1e-10);hh.set(b,h);total+=h;}
 if(total!==N||[...Array(31).keys()].some(b=>!hh.has(b)))throw Error("ERA hours");
 const op=[...hh].filter(([b])=>b>=4&&b<25);
 if(op.reduce((s,[,h])=>s+h,0)!==106900)throw Error("operating hours");
 const miss=op.filter(([b,h])=>!KNOWN.includes(b)&&h>0).map(([bin,h])=>({bin,h,u:bin+0.5}));
 if(miss.length!==13||miss.reduce((s,r)=>s+r.h,0)!==99736)throw Error("missing hours");
 const tm=new Map();
 for(const r of t){const b=integer(r.missing_bin_lower_mps,"thr bin"),h=integer(r.era5_hours_21y,"thr h"),id=r.channel+"|"+b;
  if(!["TwrBsMxt","TwrBsMyt"].includes(r.channel)||!miss.some(x=>x.bin===b)||tm.has(id)||h!==hh.get(b)||r.formal_DLC12_status!=="NOT_VALIDATED")throw Error("THR identity");
  const K=num(r.known_partial_M4_all_hours_MNm4,"K");
  near(num(r.p_all_hours,"thr p"),h/N,1e-10);
  const threshold=num(r.DEL_threshold_equal_all_3_known_bins_MNm,"threshold");
  near(threshold,Math.pow(K/(h/N),0.25),2e-8);tm.set(id,{K,threshold});
 }
 if(tm.size!==26)throw Error("threshold coverage");
 const mm=new Map();
 for(const r of m){const b=integer(r.wind_bin_mps,"M4 bin"),id=r.channel+"|"+b;
  if(!KNOWN.includes(b)||!["TwrBsMxt","TwrBsMyt"].includes(r.channel)||mm.has(id)||r.formal_DLC12_status!=="NOT_VALIDATED"||r.material_damage_status!=="NOT_COMPUTABLE")throw Error("M4 identity");
  if(integer(r.historic_era5_hours_21y,"M4 h")!==hh.get(b))throw Error("M4 hours");
  const del=num(r.six_seed_power_mean_DEL_m4_MNm,"DEL"),moment=num(r.six_seed_m4_mean_MNm4,"M4");
  near(del**4,moment,2e-8);mm.set(id,{weighted:moment*hh.get(b)/N,u:num(r.historical_wind_mps,"wind")});
 }
 if(mm.size!==6)throw Error("M4 coverage");
 for(const c of ["TwrBsMxt","TwrBsMyt"]){const K=KNOWN.reduce((s,b)=>s+mm.get(c+"|"+b).weighted,0);
  for(const r of miss)near(tm.get(c+"|"+r.bin).K,K,1e-8);}
 const ref=mm.get("TwrBsMyt|9").u;
 const score=(r,q)=>r.h*Math.pow(r.u/ref,4*q);
 const rank=q=>{if(!Number.isFinite(q)||q<0||q>QMAX)throw Error("q range");return miss.slice().sort((a,b)=>score(b,q)-score(a,q)||a.bin-b.bin);};
 const qStats=[0,1,2].map(q=>{const order=rank(q),den=order.reduce((s,r)=>s+score(r,q),0);
  return {q,top:order[0].bin,order:order.map(r=>r.bin),shares:new Map(order.map(r=>[r.bin,score(r,q)/den]))};});
 const cross=[0,QMAX];
 for(let i=0;i<miss.length;i++)for(let j=i+1;j<miss.length;j++){
  const a=miss[i],b=miss[j],q=Math.log(a.h/b.h)/(4*Math.log(b.u/a.u));
  if(q>0&&q<QMAX)cross.push(q);
 }
 cross.sort((a,b)=>a-b);
 const env=[];
 for(let i=1;i<cross.length;i++){const lo=cross[i-1],hi=cross[i];if(hi-lo<1e-12)continue;
  const bin=rank((lo+hi)/2)[0].bin;
  if(env.length&&env[env.length-1].bin===bin)env[env.length-1].hi=hi;else env.push({lo,hi,bin});}
 if(Math.abs(env[0].lo)>1e-12||Math.abs(env[env.length-1].hi-QMAX)>1e-12)throw Error("envelope incomplete");
 for(let i=1;i<env.length;i++){const x=env[i].lo,a=miss.find(r=>r.bin===env[i-1].bin),b=miss.find(r=>r.bin===env[i].bin);near(score(a,x),score(b,x),1e-10);}
 const topSet=new Set(env.map(x=>x.bin));
 const rows=miss.slice().sort((a,b)=>a.bin-b.bin).map(r=>({
  bin:r.bin,h:r.h,share:r.h/99736,thrMy:tm.get("TwrBsMyt|"+r.bin).threshold,
  ranks:qStats.map(z=>z.order.indexOf(r.bin)+1),shares:qStats.map(z=>z.shares.get(r.bin)),everTop:topSet.has(r.bin)
 }));
 return {rows,env,qStats};
}
function toCsv(a){
 const header="bin_lower_mps,era5_hours_21y,share_of_missing_hours,My_equal_K_threshold_MNm,rank_q0,rank_q1,rank_q2,scenario_share_q0,scenario_share_q1,scenario_share_q2,ever_rank1_for_q_in_0_to_2,formal_DLC12_status";
 return [header,...a.rows.map(r=>[r.bin,r.h,r.share.toFixed(9),r.thrMy.toFixed(9),...r.ranks,...r.shares.map(x=>x.toFixed(9)),r.everTop?"YES":"NO","NOT_VALIDATED"].join(","))].join("\n")+"\n";
}
function tests(e,t,m){
 const a=analyse(e,t,m);
 if(a.rows.length!==13||a.qStats.map(x=>x.top).join(",")!=="4,8,10"||a.env.map(x=>x.bin).join(",")!=="4,5,6,7,8,10")throw Error("envelope oracle");
 if(Math.abs(a.env[1].lo-0.1040717844111)>1e-10||Math.abs(a.env[5].lo-1.27419731923177)>1e-10)throw Error("analytic boundary");
 if(a.qStats.some(z=>Math.abs([...z.shares.values()].reduce((s,v)=>s+v,0)-1)>1e-12))throw Error("score normalization");
 const negative=[
 [e.replace("4,5,26927,","4,5,26926,"),t,m],
 [e,t.replace("TwrBsMyt,4,26927","TwrBsMyt,4,26926"),m],
 [e,t.replace("NOT_VALIDATED","VALIDATED"),m],
 [e,t.replace("34.583967380","35.583967380"),m],
 [e,t,m.replace("44.641262276","-44.641262276")],
 [e,t.trimEnd().split(/\r?\n/).slice(0,-1).join("\n")+"\n",m],
 [e,t,m.replace("TwrBsMyt,9,","TwrBsMyt,11,")],
 [e.replace("0.146278791830","0.946278791830"),t,m]
 ];
 negative.forEach(([x,y,z],i)=>{if(x===e&&y===t&&z===m)throw Error("negative fixture unchanged "+i);
  let rejected=false;try{analyse(x,y,z);}catch(_){rejected=true;}if(!rejected)throw Error("negative accepted "+i);});
 if(toCsv(a).trimEnd().split("\n").length!==14)throw Error("CSV count");
 return {positive_oracles:5,negative_rejections:negative.length,output_rows:13,segments:a.env.length};
}
if(require.main===module){
 const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
 const d=__dirname,files=["S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv","S10_MISSING_BIN_M4_IDENTIFIABILITY_20261107.csv","partial-annual-load-diagnostic-20261102/S10_REAL_18NTM_3BIN_PARTIAL_M4_BY_CHANNEL_20261102.csv"];
 const src=files.map(f=>fs.readFileSync(path.join(d,f),"utf8"));
 const sha=s=>crypto.createHash("sha256").update(s,"utf8").digest("hex");
 if([ERA_SHA,THR_SHA,M4_SHA].some((h,i)=>h!==sha(src[i])))throw Error("source SHA256 mismatch");
 const checks=tests(...src),a=analyse(...src),csv=toCsv(a);
 fs.writeFileSync(path.join(d,"S10_MISSING_BIN_SAMPLING_PRIORITY_20261107.csv"),csv,"utf8");
 console.log(JSON.stringify({status:"SCENARIO_ONLY_NOT_LOAD_PREDICTION",source_sha256:[ERA_SHA,THR_SHA,M4_SHA],checks,envelope:a.env,output_sha256:sha(csv)},null,2));
}
module.exports={analyse,toCsv,tests};
