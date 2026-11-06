"use strict";
// T062 load-level ranking robustness; NOT a material fatigue or physical PASS.
const SOURCE_SHA256="12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2";
const FIELDS=["case","channel","outb_sha256","original_legacy_DEL_kNm","original_legacy_CSV_DEL_kNm","one_line_fixed_DEL_kNm","third_party_reference_DEL_kNm","independent_current_CSV_DEL_kNm","old_rows","fixed_rows","ref_rows","weighted_cycle_count","original_minus_corrected_DEL_kNm"];
function check(x,m){if(!x)throw Error(m)}
function parse(csv){
 const lines=csv.trimEnd().split(/\r?\n/);check(lines.length===73,"72_ROWS");
 check(lines[0]===FIELDS.join(","),"HEADER");const ids=new Set(),rows=[];
 for(const line of lines.slice(1)){
  const a=line.split(",");check(a.length===13,"COLUMNS");
  const r=Object.fromEntries(FIELDS.map((k,i)=>[k,a[i]]));
  check(/^U(09p343881|11p4|19p202140)_(NTM|ETM)_S0[1-6]$/.test(r.case),"CASE");
  check(["TwrBsMxt","TwrBsMyt"].includes(r.channel),"CHANNEL");
  check(/^[0-9a-f]{64}$/.test(r.outb_sha256),"OUTB_SHA");
  const id=r.case+"/"+r.channel;check(!ids.has(id),"DUPLICATE");ids.add(id);
  for(const k of FIELDS.slice(3)){check(r[k]!==""&&Number.isFinite(+r[k]),"FINITE");r[k]=+r[k]}
  const o=r.original_legacy_DEL_kNm,n=r.one_line_fixed_DEL_kNm;check(o>0&&n>0,"POSITIVE");
  check(Math.abs(o-r.original_legacy_CSV_DEL_kNm)<1e-5,"OLD_REFERENCE");
  check(Math.abs(n-r.third_party_reference_DEL_kNm)<1e-5,"THIRD_PARTY");
  check(Math.abs(n-r.independent_current_CSV_DEL_kNm)<1e-5,"NEW_REFERENCE");
  check(Math.abs(o-n-r.original_minus_corrected_DEL_kNm)<1e-5,"DIFFERENCE");
  rows.push(r);
 }
 for(const c of ["TwrBsMxt","TwrBsMyt"])check(rows.filter(r=>r.channel===c).length===36,"GROUP");
 return rows;
}
function median(a){a=[...a].sort((x,y)=>x-y);return (a[(a.length-1)>>1]+a[a.length>>1])/2}
function summarize(rows,channel){
 const a=rows.filter(r=>r.channel===channel);check(a.length===36,"GROUP_SIZE");
 const old=[...a].sort((x,y)=>y.original_legacy_DEL_kNm-x.original_legacy_DEL_kNm);
 const now=[...a].sort((x,y)=>y.one_line_fixed_DEL_kNm-x.one_line_fixed_DEL_kNm);
 const ro=new Map(old.map((r,i)=>[r.case,i+1])),rn=new Map(now.map((r,i)=>[r.case,i+1]));
 let inv=0,pairs=0,sq=0;
 for(let i=0;i<36;i++){sq+=(ro.get(a[i].case)-rn.get(a[i].case))**2;
  for(let j=i+1;j<36;j++){
   const x=a[i].original_legacy_DEL_kNm-a[j].original_legacy_DEL_kNm;
   const y=a[i].one_line_fixed_DEL_kNm-a[j].one_line_fixed_DEL_kNm;
   check(x!==0&&y!==0,"RANK_TIE");pairs++;if(x*y<0)inv++;
  }
 }
 const bias=a.map(r=>100*(r.original_legacy_DEL_kNm/r.one_line_fixed_DEL_kNm-1));
 const old5=new Set(old.slice(0,5).map(r=>r.case));
 const medType=t=>median(a.filter(r=>r.case.includes("_"+t+"_")).map(r=>100*(r.original_legacy_DEL_kNm/r.one_line_fixed_DEL_kNm-1)));
 return {channel,n:36,median_bias_pct:median(bias),min_bias_pct:Math.min(...bias),max_bias_pct:Math.max(...bias),
  old_above_corrected:bias.filter(x=>x>0).length,spearman_rho:1-6*sq/(36*(36*36-1)),
  discordant_pairs:inv,all_pairs:pairs,top5_overlap:now.slice(0,5).filter(r=>old5.has(r.case)).length,
  ntm_median_bias_pct:medType("NTM"),etm_median_bias_pct:medType("ETM"),
  old_top3:old.slice(0,3).map(r=>[r.case,r.original_legacy_DEL_kNm/1000]),
  corrected_top3:now.slice(0,3).map(r=>[r.case,r.one_line_fixed_DEL_kNm/1000])};
}
function selfTest(csv){
 const r=parse(csv),a=summarize(r,"TwrBsMxt"),b=summarize(r,"TwrBsMyt");
 check(a.discordant_pairs===12&&b.discordant_pairs===102,"REAL_INVERSIONS");
 check(a.top5_overlap===5&&b.top5_overlap===4,"REAL_TOP5");
 check(Math.abs(b.spearman_rho-0.8594594594594595)<1e-12,"REAL_SPEARMAN");
 const lines=csv.trimEnd().split(/\r?\n/);
 const bad=[lines.slice(0,-1).join("\n"),lines.concat(lines[1]).join("\n"),
  [lines[0],lines[1],lines[1],...lines.slice(3)].join("\n"),
  csv.replace("TwrBsMxt","INVALID"),csv.replace("original_legacy_DEL_kNm","OLD"),
  csv.replace("0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c","INVALID"),
  csv.replace("2279.867084652287,2279.867084652287","2279.867084652287,9999.867084652287"),
  csv.replace("2279.867084652287","NaN")];
 let refused=0;for(const x of bad){try{parse(x)}catch(_){refused++}}
 check(refused===8,"NEGATIVE_TESTS");return {real_rows:72,positive_oracles:3,negative_refusals:refused};
}
if(typeof module!=="undefined"&&module.exports)module.exports={parse,summarize,selfTest};
if(typeof require!=="undefined"&&require.main===module){
 const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
 const file=process.argv[2]&&process.argv[2]!=="--self-test"?process.argv[2]:path.join(__dirname,"legacy-primary-recovered-20261102","T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv");
 const bytes=fs.readFileSync(file),sha=crypto.createHash("sha256").update(bytes).digest("hex");
 check(sha===SOURCE_SHA256,"SOURCE_SHA256_MISMATCH");
 const csv=bytes.toString("utf8"),rows=parse(csv);
 process.stdout.write(JSON.stringify({source_sha256:sha,tests:selfTest(csv),results:["TwrBsMxt","TwrBsMyt"].map(c=>summarize(rows,c)),status:"SOURCE_LEVEL_LOAD_DEL_ONLY"},null,2)+"\n");
}