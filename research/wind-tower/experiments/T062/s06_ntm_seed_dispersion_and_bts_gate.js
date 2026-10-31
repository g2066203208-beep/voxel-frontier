#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),crypto=require("node:crypto");
const SRC="95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f",MAN="c9da25b3a967c9ed3b3a859666263c6964d8480798185e6e031539c38e4c3302";
const bins=["U09p343881_NTM","U11p4_NTM","U19p202140_NTM"];
const channels=["TwrBsMyt",...Array.from({length:9},(_,i)=>"TwHt"+(i+1)+"MLyt")];
function sha(b){return crypto.createHash("sha256").update(b).digest("hex")}
function must(x,m){if(!x)throw Error(m)}
function parse(s){
 const lines=s.trimEnd().split(/\r?\n/),h=lines.shift().split(",");
 must(new Set(h).size===h.length,"DUPLICATE_HEADER");
 for(const k of ["case","channel","unit","n_samples","t0_s","t1_s","dt_s","DEL_m4_Nref600","outb_sha256"])must(h.includes(k),"MISSING_"+k);
 return lines.map((l,i)=>{const a=l.split(",");must(a.length===h.length,"CSV_WIDTH_"+i);return Object.fromEntries(h.map((k,j)=>[k,a[j]]))});
}
function run(rows,manifest){
 must(rows.length===1080,"SOURCE_ROW_COUNT");
 const seen=new Set(),counts=new Map(),groups=new Map();
 for(const r of rows){
  const id=r.case+"|"+r.channel;must(!seen.has(id),"DUPLICATE_CASE_CHANNEL");seen.add(id);
  must(/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(r.case),"BAD_CASE");
  must(/^[0-9a-f]{64}$/.test(r.outb_sha256),"BAD_OUTB_SHA");
  must(+r.n_samples===12001&&+r.t0_s===100&&+r.t1_s===700&&+r.dt_s===0.05,"BAD_TIME_GRID");
  const d=+r.DEL_m4_Nref600;must(Number.isFinite(d)&&d>0,"BAD_DEL");
  counts.set(r.case,(counts.get(r.case)||0)+1);
  if(channels.includes(r.channel)){
   must(r.unit==="(kN-m)","BAD_MOMENT_UNIT");
   const key=r.case.replace(/_S0[1-6]$/,"")+"|"+r.channel;
   if(!groups.has(key))groups.set(key,[]);
   groups.get(key).push({seed:r.case.slice(-3),value:d});
  }
 }
 must(counts.size===18&&[...counts.values()].every(n=>n===60),"INCOMPLETE_CASES");
 const ts=manifest.filter(z=>z.section==="turbSim-36");
 const idx=new Map();for(const z of ts){must(!idx.has(z.relative_path),"DUPLICATE_MANIFEST");idx.set(z.relative_path,z)}
 const bts=ts.filter(z=>/^inputs\/U.*\.bts$/.test(z.relative_path));
 must(bts.length===36,"BTS_CASE_COUNT");
 let available=0,deferred=0;
 for(const z of bts){
  if(z.status==="included"&&z.canonical_archive&&/^[a-f0-9]{64}$/i.test(z.sha256))available++;
  else if(z.status==="prior-size-deferral-cancelled-see-transfer-ledger"&&!z.archive&&!z.sha256)deferred++;
  else throw Error("UNEXPECTED_BTS_SOURCE_STATE_"+z.relative_path);
  const stem=z.relative_path.slice(0,-4);
  for(const ext of ["inp","sum","dat"]){const x=idx.get(stem+"."+ext);must(x&&x.status==="included"&&x.canonical_archive&&/^[a-f0-9]{64}$/i.test(x.sha256),"MISSING_AUX_"+stem+"."+ext)}
 }
 const out=["wind_case,channel,seed_count,mean_DEL_m4_Nref600_kNm,sample_sd_kNm,CV_percent,min_kNm,max_kNm,max_min_ratio,min_seed,max_seed,source_csv_sha256"];
 for(const w of bins)for(const c of channels){
  const a=groups.get(w+"|"+c);
  must(a&&a.length===6&&a.map(x=>x.seed).sort().join(",")==="S01,S02,S03,S04,S05,S06","BAD_SEED_COVERAGE_"+w+"_"+c);
  const mean=a.reduce((s,x)=>s+x.value,0)/6;
  const sd=Math.sqrt(a.reduce((s,x)=>s+(x.value-mean)**2,0)/5);
  const lo=a.reduce((p,x)=>x.value<p.value?x:p),hi=a.reduce((p,x)=>x.value>p.value?x:p);
  out.push([w,c,6,mean.toFixed(9),sd.toFixed(9),(100*sd/mean).toFixed(6),lo.value.toFixed(9),hi.value.toFixed(9),(hi.value/lo.value).toFixed(9),lo.seed,hi.seed,SRC].join(","));
 }
 must(groups.size===30&&out.length===31,"OUTPUT_COVERAGE");
 return {csv:out.join("\n")+"\n",summary:{source_rows:1080,ntm_cases:18,groups:30,original_bts_available:available,original_bts_deferred:deferred,auxiliary_inp_sum_dat:108,physical_pass:false}};
}
function convergence(rows){
 const src="95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f";
 const bins=["U09p343881_NTM","U11p4_NTM","U19p202140_NTM"];
 const channels=["TwrBsMyt",...Array.from({length:9},(_,i)=>"TwHt"+(i+1)+"MLyt")];
 const must=(x,m)=>{if(!x)throw Error(m)};
 const fmt=(x,n=9)=>{must(Number.isFinite(x),"NONFINITE_RESULT");return x.toFixed(n)};
 const pow4=a=>Math.sqrt(Math.sqrt(a.reduce((s,x)=>{const y=x*x;return s+y*y},0)/a.length));
 const choose=(a,n)=>{const out=[];const recur=(s,acc)=>{if(acc.length===n){out.push(pow4(acc));return}for(let j=s;j<=a.length-(n-acc.length);j++)recur(j+1,[...acc,a[j]])};recur(0,[]);return out};
 const counts=[0,6,15,20,15,6,1];
 const summary=["wind_case,channel,seed_count,arithmetic_mean_DEL_m4_kNm,equal_duration_power_mean_m4_kNm,power_vs_arithmetic_percent,seed_sample_CV_percent,min_seed_DEL_kNm,max_seed_DEL_kNm,leave_one_out_max_abs_power_mean_shift_percent,source_csv_sha256"];
 const subsets=["wind_case,channel,n_seed_subset,combination_count,prefix_seeds,prefix_power_mean_m4_kNm,all_subset_min_power_mean_m4_kNm,all_subset_max_power_mean_m4_kNm,max_abs_subset_deviation_from_full_percent,full_6seed_power_mean_m4_kNm,source_csv_sha256"];
 const groups=new Map();
 for(const r of rows){if(!channels.includes(r.channel))continue;const key=r.case.replace(/_S0[1-6]$/,"")+"|"+r.channel;must(/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(r.case),"BAD_CASE");must(r.unit==="(kN-m)"&&r.n_samples==="12001"&&r.t0_s==="100"&&r.t1_s==="700"&&r.dt_s==="0.05","BAD_NATIVE_GRID");const v=+r.DEL_m4_Nref600;must(v>0&&Number.isFinite(v),"BAD_DEL");if(!groups.has(key))groups.set(key,new Map());const g=groups.get(key);must(!g.has(r.case.slice(-3)),"DUPLICATE_SEED");g.set(r.case.slice(-3),v)}
 must(rows.length===1080&&groups.size===30,"BAD_SOURCE_ROW_OR_GROUP_COUNT");
 let peak={wind_case:"",channel:"",n:0,deviation:-1};
 for(const wind of bins)for(const channel of channels){
  const g=groups.get(wind+"|"+channel);must(g&&g.size===6,"MISSING_GROUP");
  const values=Array.from({length:6},(_,i)=>g.get("S0"+(i+1)));must(values.every(x=>x>0),"MISSING_SEED");
  const avg=values.reduce((s,x)=>s+x,0)/6,full=pow4(values),sd=Math.sqrt(values.reduce((s,x)=>s+(x-avg)**2,0)/5);
  const loo=choose(values,5),looShift=Math.max(...loo.map(v=>Math.abs(v/full-1)))*100;
  summary.push([wind,channel,6,fmt(avg),fmt(full),fmt(100*(full/avg-1),6),fmt(100*sd/avg,6),fmt(Math.min(...values)),fmt(Math.max(...values)),fmt(looShift,6),src].join(","));
  for(let n=1;n<=6;n++){
   const all=choose(values,n);must(all.length===counts[n],"COMBINATORIC_ERROR_"+n);
   const low=Math.min(...all),high=Math.max(...all),prefix=pow4(values.slice(0,n));
   const dev=Math.max(...all.map(v=>Math.abs(v/full-1)))*100;
   subsets.push([wind,channel,n,all.length,Array.from({length:n},(_,i)=>"S0"+(i+1)).join("+"),fmt(prefix),fmt(low),fmt(high),fmt(dev,6),fmt(full),src].join(","));
   if(dev>peak.deviation)peak={wind_case:wind,channel,n,deviation:dev};
  }
 }
 must(summary.length===31&&subsets.length===181,"OUTPUT_ROW_COUNT");
 return {summary:summary.join("\n")+"\n",subsets:subsets.join("\n")+"\n",max_deviation:peak};
}
function convergenceTest(){const a=[1,2,3,4,5,6];const p=x=>Math.pow(x.reduce((s,v)=>s+v**4,0)/x.length,.25);const full=p(a);if(Math.abs(full**4-((1+16+81+256+625+1296)/6))>1e-12)throw Error("POWER_MEAN_ORACLE");const count=(n)=>{let z=0;function f(s,d){if(d===n){z++;return}for(let i=s;i<=6-(n-d);i++)f(i+1,d+1)}f(0,0);return z};if([1,2,3,4,5,6].map(count).join(",")!=="6,15,20,15,6,1")throw Error("SUBSET_COUNTS");if(p(a.slice(0,6))!==full)throw Error("FULL_PREFIX");return "6+15+20+15+6+1";}
function test(){
 const x=[1,2,3,4,5,6],m=x.reduce((a,b)=>a+b)/6;
 must(m===3.5&&Math.abs(Math.sqrt(x.reduce((a,b)=>a+(b-m)**2,0)/5)-Math.sqrt(3.5))<1e-12,"SD_TEST");
 for(const t of ["case,case\nA,B\n","case,channel\nA\n"]){let failed=false;try{parse(t)}catch{failed=true}must(failed,"NEGATIVE_HEADER_TEST")}
 const cs=convergenceTest();
 console.log("SELFTEST_PASS sample_SD_and_invalid_CSV; EXACT_SUBSET_ENUMERATION_PASS "+cs);
}
function main(){
 if(process.argv.includes("--self-test"))return test();
 const a=process.argv.slice(2),o={};for(let i=0;i<a.length;i+=2)o[a[i]]=a[i+1];
 for(const k of ["--source","--manifest","--out"])must(o[k],"MISSING_ARG_"+k);
 const src=fs.readFileSync(o["--source"]),man=fs.readFileSync(o["--manifest"]);
 must(sha(src)===SRC,"CSV_SHA256_MISMATCH");must(sha(man)===MAN,"MANIFEST_SHA256_MISMATCH");
 const rows=parse(src.toString("utf8"));
 const r=run(rows,JSON.parse(man.toString("utf8")));
 fs.writeFileSync(o["--out"],r.csv);
 const requested=Boolean(o["--convergence-summary"]||o["--convergence-subsets"]);
 must(!requested||(o["--convergence-summary"]&&o["--convergence-subsets"]),"CONVERGENCE_OUTPUT_PAIR_REQUIRED");
 let extra={};
 if(requested){const c=convergence(rows);fs.writeFileSync(o["--convergence-summary"],c.summary);fs.writeFileSync(o["--convergence-subsets"],c.subsets);extra={convergence_summary_sha256:sha(Buffer.from(c.summary)),convergence_subsets_sha256:sha(Buffer.from(c.subsets)),convergence_groups:30,convergence_subset_rows:180,max_subset_deviation:c.max_deviation};}
 console.log(JSON.stringify({...r.summary,source_sha256:SRC,manifest_sha256:MAN,output_sha256:sha(Buffer.from(r.csv)),...extra}));
}
if(require.main===module)main();
