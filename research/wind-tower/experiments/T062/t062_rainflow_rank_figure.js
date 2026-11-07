"use strict";
/* Historical T062 rainflow rank-rank figure. LOAD DEL ONLY; not material fatigue. */
const SOURCE_SHA256="12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2";
const F=["case","channel","outb_sha256","original_legacy_DEL_kNm","original_legacy_CSV_DEL_kNm","one_line_fixed_DEL_kNm","third_party_reference_DEL_kNm","independent_current_CSV_DEL_kNm","old_rows","fixed_rows","ref_rows","weighted_cycle_count","original_minus_corrected_DEL_kNm"];
const channels=["TwrBsMxt","TwrBsMyt"],speeds=["U09p343881","U11p4","U19p202140"];
function assert(x,m){if(!x)throw Error(m)}
function parse(csv){
 const lines=csv.trimEnd().split(/\r?\n/);assert(lines.length===73,"ROW_COUNT");assert(lines[0]===F.join(","),"HEADER");
 const rows=[],ids=new Set(),hashes=new Map();
 for(const line of lines.slice(1)){
  const a=line.split(",");assert(a.length===13,"COLS");const r=Object.fromEntries(F.map((k,i)=>[k,a[i]]));
  assert(/^U(09p343881|11p4|19p202140)_(NTM|ETM)_S0[1-6]$/.test(r.case),"CASE");
  assert(channels.includes(r.channel),"CHANNEL");assert(/^[0-9a-f]{64}$/.test(r.outb_sha256),"OUTB_HASH");
  const key=r.case+"/"+r.channel;assert(!ids.has(key),"DUP");ids.add(key);
  if(hashes.has(r.case))assert(hashes.get(r.case)===r.outb_sha256,"HASH_PAIR");else hashes.set(r.case,r.outb_sha256);
  for(const k of F.slice(3)){assert(r[k]!==""&&Number.isFinite(+r[k]),"FINITE");r[k]=+r[k]}
  const old=r.original_legacy_DEL_kNm,now=r.one_line_fixed_DEL_kNm;
  assert(old>0&&now>0,"POSITIVE");
  assert(Math.abs(old-r.original_legacy_CSV_DEL_kNm)<1e-5,"OLD_REFERENCE");
  assert(Math.abs(now-r.third_party_reference_DEL_kNm)<1e-5,"THIRD_PARTY");
  assert(Math.abs(now-r.independent_current_CSV_DEL_kNm)<1e-5,"INDEPENDENT_REFERENCE");
  assert(Math.abs(old-now-r.original_minus_corrected_DEL_kNm)<1e-5,"DEL_DIFFERENCE");rows.push(r);
 }
 for(const s of speeds)for(const c of ["NTM","ETM"])for(let i=1;i<=6;i++)for(const ch of channels)
  assert(ids.has(s+"_"+c+"_S0"+i+"/"+ch),"MISSING");
 return rows;
}
function analyze(rows,channel){
 const a=rows.filter(x=>x.channel===channel);assert(a.length===36,"GROUP");
 const old=[...a].sort((x,y)=>y.original_legacy_DEL_kNm-x.original_legacy_DEL_kNm);
 const now=[...a].sort((x,y)=>y.one_line_fixed_DEL_kNm-x.one_line_fixed_DEL_kNm);
 for(const [arr,k] of [[old,"original_legacy_DEL_kNm"],[now,"one_line_fixed_DEL_kNm"]])
  for(let i=1;i<36;i++)assert(arr[i-1][k]!==arr[i][k],"TIE");
 const o=new Map(old.map((x,i)=>[x.case,i+1])),n=new Map(now.map((x,i)=>[x.case,i+1]));
 let inv=0,sq=0;
 for(let i=0;i<36;i++){sq+=(o.get(a[i].case)-n.get(a[i].case))**2;
  for(let j=i+1;j<36;j++)if((a[i].original_legacy_DEL_kNm-a[j].original_legacy_DEL_kNm)*(a[i].one_line_fixed_DEL_kNm-a[j].one_line_fixed_DEL_kNm)<0)inv++}
 return {channel,inversions:inv,rho:1-6*sq/(36*(36*36-1)),oldTop:old[0].case,newTop:now[0].case,
  top5:now.slice(0,5).filter(x=>old.slice(0,5).some(y=>y.case===x.case)).length,
  records:a.map(x=>({case:x.case,channel,cl:x.case.includes("_ETM_")?"ETM":"NTM",oldRank:o.get(x.case),newRank:n.get(x.case),
   oldDEL:x.original_legacy_DEL_kNm/1000,newDEL:x.one_line_fixed_DEL_kNm/1000}))};
}
function csvOutput(rs){
 const lines=["case,channel,class,legacy_rank,corrected_rank,rank_change,legacy_DEL_MNm,corrected_DEL_MNm"];
 for(const r of rs)for(const x of [...r.records].sort((a,b)=>a.newRank-b.newRank))
  lines.push([x.case,x.channel,x.cl,x.oldRank,x.newRank,x.newRank-x.oldRank,x.oldDEL.toFixed(9),x.newDEL.toFixed(9)].join(","));
 return lines.join("\n")+"\n";
}
function svgOutput(rs){
 assert(rs.length===2&&rs[0].channel===channels[0]&&rs[1].channel===channels[1],"CHANNEL_ORDER");
 const w=1320,h=700,sz=403,top=158,lefts=[122,754],color={NTM:"#267F94",ETM:"#C16934"},s=[];
 s.push('<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'" role="img" aria-labelledby="title desc">');
 s.push('<title id="title">Legacy versus corrected rainflow DEL ranking for 36 historical cases per channel</title>');
 s.push('<desc id="desc">Mx: 12 of 630 pairwise inversions; My: 102 of 630 inversions and a changed controlling realization. Load-level diagnostic, not fatigue life.</desc>');
 s.push('<rect width="'+w+'" height="'+h+'" fill="white"/>');
 s.push('<text x="65" y="53" font-family="Arial,sans-serif" font-size="25" font-weight="700" fill="#193145">Rainflow correction changes load-screening ranks</text>');
 s.push('<text x="65" y="82" font-family="Arial,sans-serif" font-size="15" fill="#566878">36 historical 600 s cases per channel · fourth-power load DEL · rank 1 is the highest</text>');
 s.push('<circle cx="935" cy="110" r="6" fill="'+color.NTM+'"/><text x="949" y="115" font-family="Arial,sans-serif" font-size="14" fill="#33495B">NTM</text>');
 s.push('<circle cx="1025" cy="110" r="6" fill="'+color.ETM+'"/><text x="1039" y="115" font-family="Arial,sans-serif" font-size="14" fill="#33495B">ETM</text>');
 s.push('<line x1="1114" y1="110" x2="1147" y2="110" stroke="#8899A9" stroke-width="2" stroke-dasharray="6 5"/><text x="1158" y="115" font-family="Arial,sans-serif" font-size="13" fill="#33495B">No shift</text>');
 for(let i=0;i<2;i++){
  const d=rs[i],x0=lefts[i],X=r=>x0+(r-1)*sz/35,Y=r=>top+(r-1)*sz/35;
  s.push('<text x="'+x0+'" y="135" font-family="Arial,sans-serif" font-size="19" font-weight="700" fill="#1A3449">'+(i===0?"(a) Tower-base Mx":"(b) Tower-base My")+'</text>');
  s.push('<rect x="'+x0+'" y="'+top+'" width="'+sz+'" height="'+sz+'" fill="#FAFCFE" stroke="#9EAFBE"/>');
  for(const t of [1,6,12,18,24,30,36]){
   s.push('<line x1="'+X(t).toFixed(2)+'" y1="'+top+'" x2="'+X(t).toFixed(2)+'" y2="'+(top+sz)+'" stroke="#E2E9F0"/>');
   s.push('<line x1="'+x0+'" y1="'+Y(t).toFixed(2)+'" x2="'+(x0+sz)+'" y2="'+Y(t).toFixed(2)+'" stroke="#E2E9F0"/>');
   s.push('<text x="'+X(t).toFixed(2)+'" y="'+(top+sz+22)+'" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#516376">'+t+'</text>');
   s.push('<text x="'+(x0-12)+'" y="'+(Y(t)+4).toFixed(2)+'" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#516376">'+t+'</text>');
  }
  s.push('<line x1="'+x0+'" y1="'+top+'" x2="'+(x0+sz)+'" y2="'+(top+sz)+'" stroke="#8899A9" stroke-width="2" stroke-dasharray="6 5"/>');
  for(const r of d.records){
   const mark=i===1&&["U11p4_ETM_S03","U11p4_ETM_S04"].includes(r.case);
   s.push('<circle class="case" cx="'+X(r.oldRank).toFixed(2)+'" cy="'+Y(r.newRank).toFixed(2)+'" r="'+(mark?8:5)+'" fill="'+color[r.cl]+'" fill-opacity="0.88" stroke="'+(mark?"#18364B":"white")+'" stroke-width="'+(mark?2.6:1)+'"><title>'+r.case+': '+r.oldRank+' to '+r.newRank+'</title></circle>');
  }
  s.push('<text x="'+(x0+sz/2)+'" y="'+(top+sz+53)+'" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" fill="#2E4558">Legacy DEL rank</text>');
  s.push('<text x="'+(x0-67)+'" y="'+(top+sz/2)+'" transform="rotate(-90 '+(x0-67)+' '+(top+sz/2)+')" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" fill="#2E4558">Corrected DEL rank</text>');
  s.push('<text x="'+x0+'" y="'+(top+sz+81)+'" font-family="Arial,sans-serif" font-size="14" fill="#2B4357">'+d.inversions+'/630 inverted pairs · ρ = '+d.rho.toFixed(5)+' · Top-5 '+d.top5+'/5</text>');
 }
 const my=rs[1],a=my.records.find(x=>x.case===my.oldTop),b=my.records.find(x=>x.case===my.newTop);
 s.push('<text x="754" y="678" font-family="Arial,sans-serif" font-size="13" fill="#9C4F2A">My control: '+my.oldTop+' (new rank '+a.newRank+') → '+my.newTop+' (old rank '+b.oldRank+')</text>');
 s.push('</svg>');return s.join("\n")+"\n";
}
function selfTest(source){
 const rows=parse(source),rs=channels.map(c=>analyze(rows,c));
 assert(rs[0].inversions===12&&rs[1].inversions===102,"INV_ORACLE");
 assert(Math.abs(rs[0].rho-0.9953667953667954)<1e-12&&Math.abs(rs[1].rho-0.8594594594594595)<1e-12,"RHO_ORACLE");
 assert(rs[0].top5===5&&rs[1].top5===4,"TOP5_ORACLE");
 assert(rs[0].oldTop===rs[0].newTop&&rs[1].oldTop==="U11p4_ETM_S03"&&rs[1].newTop==="U11p4_ETM_S04","TOP_ORACLE");
 const csv=csvOutput(rs),svg=svgOutput(rs);
 assert(csv.trimEnd().split("\n").length===73&&((svg.match(/class="case"/g)||[]).length===72),"OUTPUT_COUNTS");
 const lines=source.trimEnd().split(/\r?\n/);
 const bad=[lines.slice(0,-1).join("\n"),[lines[0],lines[1],lines[1],...lines.slice(3)].join("\n"),
 source.replace("case,channel","case,wrong"),source.replace("TwrBsMxt","BAD"),
 source.replace("0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c","INVALID"),
 source.replace("3091.616139149874,3091.616139149874","3091.616139149874,9999.616139149874"),
 source.replace("2279.867084652287","NaN"),source.replace("U09p343881_ETM_S01","U09p343881_ETM_S09"),
 source.replace("-811.749054497586","0.000000000000")];
 let refused=0;for(const b of bad){try{parse(b)}catch(_){refused++}}
 assert(refused===9,"REFUSAL_"+refused);
 const tied=parse(source),my=tied.filter(r=>r.channel==="TwrBsMyt");my[1].one_line_fixed_DEL_kNm=my[0].one_line_fixed_DEL_kNm;
 let tie=false;try{analyze(tied,"TwrBsMyt")}catch(_){tie=true}assert(tie,"TIE_REFUSAL");
 return {rs,csv,svg,positive:5,negative:10};
}
if(typeof module!=="undefined"&&module.exports)module.exports={parse,analyze,csvOutput,svgOutput,selfTest};
if(typeof require!=="undefined"&&require.main===module){
 const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
 const input=process.argv[2]||path.join(__dirname,"legacy-primary-recovered-20261102","T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv");
 const bytes=fs.readFileSync(input);assert(crypto.createHash("sha256").update(bytes).digest("hex")===SOURCE_SHA256,"SOURCE_SHA256");
 const x=selfTest(bytes.toString("utf8")),dir=process.argv[3]||__dirname;
 fs.writeFileSync(path.join(dir,"T062_72CASE_RAINFLOW_RANK_TRANSITIONS_20261107.csv"),x.csv);
 fs.writeFileSync(path.join(dir,"FIG_JOURNAL_T062_RAINFLOW_RANK_REVERSAL_20261107.svg"),x.svg);
 console.log(JSON.stringify({positive:x.positive,negative:x.negative,results:x.rs.map(r=>({channel:r.channel,inversions:r.inversions,rho:r.rho,oldTop:r.oldTop,newTop:r.newTop}))},null,2));
}
