"use strict";
// Exact finite-sample seed-subset enumeration on historical 158m NTM tower-base load DEL.
// This is a conditional six-seed load screening diagnostic, NOT IEC DLC1.2, local stress or Miner damage.
const SOURCE_SHA256="12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2";
const FIELDS=["case","channel","outb_sha256","original_legacy_DEL_kNm","original_legacy_CSV_DEL_kNm","one_line_fixed_DEL_kNm","third_party_reference_DEL_kNm","independent_current_CSV_DEL_kNm","old_rows","fixed_rows","ref_rows","weighted_cycle_count","original_minus_corrected_DEL_kNm"];
const SPEEDS=["09p343881","11p4","19p202140"];
const CHANNELS=["TwrBsMxt","TwrBsMyt"];
const M=4;
function check(v,msg){if(!v)throw Error(msg)}
function parse(csv){
 const lines=csv.trimEnd().split(/\r?\n/);
 check(lines.length===73,"ROW_COUNT");
 check(lines[0]===FIELDS.join(","),"HEADER");
 const ids=new Set(),rows=[],shaByCase=new Map();
 for(const line of lines.slice(1)){
  const a=line.split(",");check(a.length===FIELDS.length,"COLUMNS");
  const r=Object.fromEntries(FIELDS.map((k,i)=>[k,a[i]]));
  check(/^U(09p343881|11p4|19p202140)_(NTM|ETM)_S0[1-6]$/.test(r.case),"CASE");
  check(CHANNELS.includes(r.channel),"CHANNEL");
  check(/^[0-9a-f]{64}$/.test(r.outb_sha256),"OUTB_SHA");
  const id=r.case+"/"+r.channel;check(!ids.has(id),"DUPLICATE");ids.add(id);
  if(shaByCase.has(r.case))check(shaByCase.get(r.case)===r.outb_sha256,"OUTB_CROSS_CHANNEL");
  shaByCase.set(r.case,r.outb_sha256);
  for(const k of FIELDS.slice(3)){check(r[k]!==""&&Number.isFinite(+r[k]),"FINITE_"+k);r[k]=+r[k]}
  check(r.one_line_fixed_DEL_kNm>0&&r.original_legacy_DEL_kNm>0,"POSITIVE");
  check(Math.abs(r.one_line_fixed_DEL_kNm-r.third_party_reference_DEL_kNm)<1e-5,"THIRD_PARTY");
  check(Math.abs(r.one_line_fixed_DEL_kNm-r.independent_current_CSV_DEL_kNm)<1e-5,"INDEPENDENT");
  check(Math.abs(r.original_legacy_DEL_kNm-r.original_legacy_CSV_DEL_kNm)<1e-5,"LEGACY");
  check(Math.abs(r.original_legacy_DEL_kNm-r.one_line_fixed_DEL_kNm-r.original_minus_corrected_DEL_kNm)<1e-5,"DIFFERENCE");
  rows.push(r);
 }
 for(const ch of CHANNELS){
  check(rows.filter(r=>r.channel===ch).length===36,"CHANNEL_SIZE");
  for(const sp of SPEEDS)for(let i=1;i<=6;i++)
   check(rows.some(r=>r.case==="U"+sp+"_NTM_S0"+i&&r.channel===ch),"MISSING_NTM");
 }
 return rows;
}
function combinations(a,k){
 if(k===0)return [[]];
 if(a.length<k)return [];
 const out=[];for(let i=0;i<=a.length-k;i++)
  for(const tail of combinations(a.slice(i+1),k-1))out.push([a[i],...tail]);
 return out;
}
function aggregate(v,indices){
 check(indices.length>0,"EMPTY_SUBSET");
 return (indices.reduce((s,i)=>s+Math.pow(v[i],M),0)/indices.length)**(1/M);
}
function oneChannel(rows,channel){
 const values=SPEEDS.map(sp=>Array.from({length:6},(_,i)=>{
  const r=rows.find(x=>x.case==="U"+sp+"_NTM_S0"+(i+1)&&x.channel===channel);
  check(r,"MISSING_NTM");return r.one_line_fixed_DEL_kNm;
 }));
 const all=[0,1,2,3,4,5],full=values.map(v=>aggregate(v,all));
 const winner=full.indexOf(Math.max(...full));
 check(full.filter(v=>v===full[winner]).length===1,"FULL_TIE");
 const ordered=[...full].sort((a,b)=>b-a);
 const results=[];
 for(let k=1;k<=5;k++){
  const sets=combinations(all,k),a=values.map(v=>sets.map(s=>aggregate(v,s)));
  let independentN=0,independentMiss=0,pairedMiss=0,maxWinnerAbsError=0;
  const counts=[0,0,0];
  for(let i=0;i<sets.length;i++){
   const z=[a[0][i],a[1][i],a[2][i]],w=z.indexOf(Math.max(...z));
   if(w!==winner)pairedMiss++;
  }
  for(let i=0;i<sets.length;i++)for(let j=0;j<sets.length;j++)for(let h=0;h<sets.length;h++){
   const z=[a[0][i],a[1][j],a[2][h]],w=z.indexOf(Math.max(...z));
   check(z.filter(v=>v===z[w]).length===1,"SUBSET_TIE");
   counts[w]++;independentN++;if(w!==winner)independentMiss++;
   maxWinnerAbsError=Math.max(maxWinnerAbsError,Math.abs(z[winner]/full[winner]-1));
  }
  check(independentN===sets.length**3,"ENUM_COUNT");
  results.push({k,independent_n:independentN,independent_miss:independentMiss,
   independent_miss_fraction:independentMiss/independentN,
   independent_winner_counts:counts,paired_n:sets.length,paired_miss:pairedMiss,
   paired_miss_fraction:pairedMiss/sets.length,
   max_abs_reference_winner_error_pct:100*maxWinnerAbsError});
 }
 return {channel,unit:"kN*m",exponent:M,wind_speeds_mps:[9.343881,11.4,19.202140],
  six_seed_equivalent_moment_kNm:full,reference_winner_speed_mps:[9.343881,11.4,19.202140][winner],
  reference_margin_over_runner_up_pct:100*(ordered[0]/ordered[1]-1),
  results};
}
function analyze(csv){
 const rows=parse(csv);
 return {scope:"18 historical NTM cases; 3 wind speeds x 6 seeds; load DEL only",
  interpretation:"exact conditional finite-six-seed subset enumeration; NOT an out-of-sample probability or IEC rule",
  source_sha256:SOURCE_SHA256,channels:CHANNELS.map(c=>oneChannel(rows,c))};
}
function renderSvg(report){
 const xs=[160,310,460,610,760],y=v=>390-300*v/35;
 const line=(c,field,color,dash)=>'<polyline fill="none" stroke="'+color+'" stroke-width="3"'+(dash?' stroke-dasharray="9 7"':'')+' points="'+c.results.map((r,i)=>xs[i]+','+y(100*r[field]).toFixed(2)).join(' ')+'"/>';
 const mx=report.channels[0],my=report.channels[1];
 const ticks=[0,5,10,15,20,25,30,35].map(v=>'<line x1="95" y1="'+y(v)+'" x2="790" y2="'+y(v)+'" stroke="#dddddd"/><text x="82" y="'+(y(v)+5)+'" text-anchor="end" font-size="14">'+v+'</text>').join("");
 const xt=xs.map((x,i)=>'<text x="'+x+'" y="417" text-anchor="middle" font-size="16">'+(i+1)+'</text>').join("");
 return '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="535" viewBox="0 0 960 535"><rect width="960" height="535" fill="white"/><g font-family="Arial, sans-serif" fill="#222">'+
 '<text x="95" y="38" font-size="22" font-weight="bold">Historical NTM: six-seed subset selection stability</text>'+
 '<text x="95" y="63" font-size="14">Exact enumeration; reference = all six seeds per wind speed; m=4 load-DEL aggregation</text>'+
 ticks+'<line x1="95" y1="90" x2="95" y2="390" stroke="#333"/><line x1="95" y1="390" x2="790" y2="390" stroke="#333"/>'+xt+
 '<text x="442" y="452" font-size="16">Number of selected seeds per wind-speed bin (k)</text>'+
 '<text x="25" y="245" transform="rotate(-90 25 245)" font-size="16">Reference wind-speed misidentification (%)</text>'+
 line(my,"independent_miss_fraction","#165a9c",false)+line(my,"paired_miss_fraction","#d07328",true)+
 line(mx,"independent_miss_fraction","#777777",false)+
 '<text x="805" y="120" font-size="14" fill="#165a9c">My independent</text>'+
 '<text x="805" y="143" font-size="14" fill="#d07328">My paired labels</text>'+
 '<text x="805" y="166" font-size="14" fill="#777777">Mx both: 0%</text>'+
 '<text x="95" y="488" font-size="13">Independent: C(6,k)^3 subsets; paired: C(6,k) shared seed labels. Not population risk.</text>'+
 '<text x="95" y="510" font-size="12">Source: T062 corrected 18 NTM 600-s DEL; SHA256 '+SOURCE_SHA256.slice(0,20)+'...</text>'+
 '</g></svg>\n';
}
function renderCsv(report){
 const h="channel,k,reference_winner_mps,reference_m4_DEL_kNm,reference_margin_pct,independent_miss,independent_n,independent_miss_pct,paired_miss,paired_n,paired_miss_pct,max_abs_reference_winner_error_pct";
 const rows=[h];
 for(const c of report.channels)for(const r of c.results)
  rows.push([c.channel,r.k,c.reference_winner_speed_mps,
   Math.max(...c.six_seed_equivalent_moment_kNm).toFixed(9),
   c.reference_margin_over_runner_up_pct.toFixed(9),
   r.independent_miss,r.independent_n,(100*r.independent_miss_fraction).toFixed(9),
   r.paired_miss,r.paired_n,(100*r.paired_miss_fraction).toFixed(9),
   r.max_abs_reference_winner_error_pct.toFixed(9)].join(","));
 return rows.join("\n")+"\n";
}
function selfTest(csv){
 const r=analyze(csv),mx=r.channels[0],my=r.channels[1];
 const near=(x,y)=>Math.abs(x-y)<1e-8;
 check(near(mx.six_seed_equivalent_moment_kNm[2],6596.210774993784),"REAL_MX_ORACLE");
 check(near(my.six_seed_equivalent_moment_kNm[2],17157.449055466677),"REAL_MY_ORACLE");
 check(my.results[2].independent_miss===760&&my.results[2].independent_n===8000,"REAL_K3");
 check(my.results[3].independent_miss===105&&my.results[3].independent_n===3375,"REAL_K4");
 check(my.results[0].paired_miss===1&&my.results[1].paired_miss===0,"PAIRED");
 check(mx.results.every(z=>z.independent_miss===0&&z.paired_miss===0),"MX_ZERO");
 check(combinations([0,1,2,3,4,5],3).length===20,"COMBINATORICS");
 check(near(aggregate([7,7,7,7,7,7],[0,2,5]),7),"CONSTANT_ORACLE");
 const lines=csv.trimEnd().split(/\r?\n/);
 const replaceLine=(i,fn)=>lines.map((x,j)=>j===i?fn(x):x).join("\n");
 const bad=[
  lines.slice(0,-1).join("\n"),
  replaceLine(72,()=>lines[1]),
  replaceLine(0,x=>x.replace("one_line_fixed_DEL_kNm","BROKEN")),
  replaceLine(1,x=>x.replace("TwrBsMxt","WRONG")),
  replaceLine(1,x=>x.replace("S01","S07")),
  replaceLine(1,x=>x.replace("3091.616139149874","NaN")),
  replaceLine(1,x=>x.replace("3091.616139149874","-3091.616139149874")),
  replaceLine(1,x=>x.replace("3091.616139149874","3191.616139149874")),
  replaceLine(1,x=>x.replace("0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c","xxxxxxxx")),
  replaceLine(1,x=>x.replace("0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c","1d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c")),
  replaceLine(1,x=>x.replace(",", ";"))
 ];
 let refused=0;for(const v of bad){try{parse(v)}catch(_){refused++}}
 check(refused===bad.length,"NEGATIVE_REFUSALS_"+refused);
 check(renderSvg(r).includes("<svg"),"SVG_RENDER");
 check(renderCsv(r).trimEnd().split("\n").length===11,"CSV_RENDER");
 return {real_oracles:8,negative_refusals:refused,svg_render:1,independent_enumerations_per_channel:15182,paired_enumerations_per_channel:62};
}
if(typeof module!=="undefined"&&typeof require!=="undefined"&&require.main===module){
 const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
 const file=process.argv.find(x=>x.endsWith(".csv"))||path.join(__dirname,"legacy-primary-recovered-20261102","T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv");
 const bytes=fs.readFileSync(file),sha=crypto.createHash("sha256").update(bytes).digest("hex");
 check(sha===SOURCE_SHA256,"SOURCE_SHA256_MISMATCH");
 const csv=bytes.toString("utf8"),report=analyze(csv),tests=selfTest(csv);
 if(process.argv.includes("--svg"))process.stdout.write(renderSvg(report));
 else if(process.argv.includes("--table"))process.stdout.write(renderCsv(report));
 else process.stdout.write(JSON.stringify({report,tests},null,2)+"\n");
}
if(typeof module!=="undefined")module.exports={parse,analyze,selfTest,renderSvg,renderCsv,combinations,aggregate};
