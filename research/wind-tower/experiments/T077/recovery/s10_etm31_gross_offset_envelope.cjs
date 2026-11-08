"use strict";
// Source-level S10 sensitivity: NOT PT field, cycle mean, material Miner or DLC1.2.
const SOURCE_SHA="36c0a8a97db36885159fff79cc61daced9c939ab688f98ce1c6b860a89ac91d3";
const CASES=["U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06"];
const OFFSETS=[0,10,15,20,22.5,25];
const HEADER="case,segment,gage_z_m,max_DEL_m4_MPa,azimuth_at_max_DEL4_deg,max_DEL_m10_MPa,azimuth_at_max_DEL10_deg,max_sigma_tension_MPa,azimuth_at_max_tension_deg,time_at_max_tension_s,min_sigma_compression_MPa,azimuth_at_min_compression_deg";
function ok(b,m){if(!b)throw Error(m);}
function num(v,k){ok(v!==""&&v!==undefined&&Number.isFinite(Number(v)),"NONFINITE_"+k);return Number(v);}
function parse(s){
 ok(typeof s==="string"&&s.endsWith("\n"),"SOURCE_END");
 const lines=s.trimEnd().split(/\r?\n/);ok(lines.shift()===HEADER,"HEADER");ok(lines.length===124,"ROW_COUNT");
 const g=Object.fromEntries(CASES.map(k=>[k,[]])),seen=new Set();
 lines.forEach((line,i)=>{
  const v=line.split(",");ok(v.length===12,"WIDTH_"+i);
  const id=v[0],seg=v[1];ok(CASES.includes(id),"CASE");ok(/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(seg),"SEGMENT");
  const key=id+"|"+seg;ok(!seen.has(key),"DUPLICATE");seen.add(key);
  const z=num(v[2],"Z"),d4=num(v[3],"DEL4"),d10=num(v[5],"DEL10"),peak=num(v[7],"PEAK"),t=num(v[9],"TIME"),trough=num(v[10],"TROUGH");
  ok(z>0&&z<112&&d4>0&&d10>0&&t>=100&&t<=700&&peak>0&&trough<0,"SOURCE_DOMAIN");
  for(const j of [4,6,8,11]){const az=num(v[j],"AZ");ok(az>=0&&az<360&&Math.abs(az/22.5-Math.round(az/22.5))<1e-10,"AZ_GRID");}
  g[id].push({seg,z,peak,trough,span:peak-trough,d4,d10});
 });
 CASES.forEach(id=>ok(g[id].length===31,"CASE_31"));return g;
}
function compute(s){
 const groups=parse(s),summary=[],table=[];
 for(const id of CASES){
  const rows=groups[id],control=rows.reduce((a,b)=>a.peak>b.peak?a:b);
  const span=Math.max(...rows.map(r=>r.span));
  summary.push({id,critical:control.peak,segment:control.seg,z:control.z,maxSpan:span});
  for(const q of OFFSETS)table.push({id,q,n:rows.filter(r=>r.peak>q).length,residual:control.peak-q,critical:control.peak,segment:control.seg,z:control.z,span});
 }
 return {groups,summary,table};
}
function csv(a){return "case,assumed_uniform_compressive_offset_MPa,sections_with_positive_gross_peak_of_31,max_residual_signed_peak_MPa,zero_positive_threshold_MPa,threshold_control_section,control_gage_z_m,max_gross_extrema_span_MPa_NOT_SINGLE_CYCLE\n"+a.table.map(r=>[r.id,r.q.toFixed(3),r.n,r.residual.toFixed(9),r.critical.toFixed(9),r.segment,r.z.toFixed(6),r.span.toFixed(9)].join(",")).join("\n")+"\n";}
function svg(a){
 const x=q=>126+q*35.5,y=n=>565-n*13.3,colors=["#245b91","#c45b39","#13866c","#7956a8"];
 let s=['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="690" viewBox="0 0 1140 690">','<rect width="1140" height="690" fill="white"/>','<g font-family="Arial,Helvetica,sans-serif" fill="#1c3048">','<text x="65" y="46" font-size="25" font-weight="bold">Conditional compressive offset and gross-section tensile peaks</text>','<text x="65" y="73" font-size="14" fill="#516176">Four historical ETM cases x 31 sections; 16-azimuth gross elastic envelope; no actual PT stress</text>'];
 for(const q of [0,5,10,15,20,25])s.push('<line x1="'+x(q)+'" x2="'+x(q)+'" y1="135" y2="565" stroke="#e2e8f0"/>','<text x="'+x(q)+'" y="589" font-size="13" text-anchor="middle">'+q+'</text>');
 for(const n of [0,5,10,15,20,25,30])s.push('<line x1="126" x2="1050" y1="'+y(n)+'" y2="'+y(n)+'" stroke="#e2e8f0"/>','<text x="113" y="'+(y(n)+5)+'" font-size="13" text-anchor="end">'+n+'</text>');
 s.push('<path d="M126 135 V565 H1050" fill="none" stroke="#263849" stroke-width="2"/>','<line x1="'+x(20)+'" x2="'+x(20)+'" y1="135" y2="565" stroke="#8c98a8" stroke-dasharray="5 5"/>');
 a.summary.forEach((g,i)=>{
  let d="M"+x(0)+" "+y(31),n=31;
  for(const t of a.groups[g.id].map(r=>r.peak).sort((a,b)=>a-b)){d+=" H"+x(t);d+=" V"+y(--n);}
  d+=" H"+x(26);
  s.push('<path d="'+d+'" fill="none" stroke="'+colors[i]+'" stroke-width="3.2" stroke-linejoin="round"/>');
  const n20=a.table.find(r=>r.id===g.id&&r.q===20).n;
  s.push('<circle cx="'+x(20)+'" cy="'+y(n20)+'" r="5.5" fill="'+colors[i]+'" stroke="white" stroke-width="1.5"/>');
  const label=["U09 S06","U11 S04","U19 S04","U19 S06"][i],lx=145+i*240;
  s.push('<line x1="'+lx+'" x2="'+(lx+27)+'" y1="111" y2="111" stroke="'+colors[i]+'" stroke-width="4"/>','<text x="'+(lx+34)+'" y="116" font-size="14">'+label+'</text>');
 });
 s.push('<text x="580" y="632" font-size="17" text-anchor="middle">Hypothetical uniform compressive offset q (MPa): sigma* = sigma_gross - q</text>','<text x="34" y="352" font-size="16" text-anchor="middle" transform="rotate(-90 34 352)">Sections retaining positive peak (out of 31)</text>','<text x="65" y="665" font-size="12" fill="#516176">Additive-offset diagnostic only. Neither actual prestress nor cycle mean, Miner damage or serviceability acceptance.</text>','</g></svg>');
 return s.join("\n")+"\n";
}
function selfTest(s){
 const a=compute(s),expected=[24.9639842875,22.1285984992,16.2817081394,18.2613828723];
 a.summary.forEach((r,i)=>ok(Math.abs(r.critical-expected[i])<1e-9&&r.segment==="CSEG_17","REAL_ORACLE"));
 for(const [q,want] of [[0,"31,31,31,31"],[20,"27,22,0,0"],[22.5,"19,0,0,0"],[25,"0,0,0,0"]])ok(a.table.filter(r=>r.q===q).map(r=>r.n).join()===want,"COUNT_ORACLE");
 for(const id of CASES){let z=a.table.filter(r=>r.id===id);for(let i=1;i<z.length;i++)ok(z[i].n<=z[i-1].n,"MONOTONE");}
 const p=[-3,2,5,-1,4],q=17,range=v=>Math.max(...v)-Math.min(...v),mean=v=>v.reduce((a,b)=>a+b,0)/v.length;
 ok(range(p)===range(p.map(x=>x-q))&&Math.abs(mean(p.map(x=>x-q))-(mean(p)-q))<1e-12,"ADDITIVE_METHOD_ONLY");
 const lines=s.trimEnd().split(/\r?\n/);
 ok(csv(compute([lines[0],...lines.slice(1).reverse()].join("\n")+"\n"))===csv(a),"ORDER");
 const bad=[s.replace("max_sigma_tension_MPa","bad_header"),lines.slice(0,-1).join("\n")+"\n",[lines[0],...lines.slice(1,-1),lines[1]].join("\n")+"\n",s.replace("CSEG_01","CSEG_32"),s.replace("21.5422222781","NaN"),s.replace("6.83617569974","-1"),s.replace(",180,652.5",",13,652.5"),s.replace("U09p343881_ETM_S06","INVALID_CASE"),s.replace("1.76339291359","999")];
 let reject=0;for(const b of bad)try{compute(b);}catch(e){reject++;}
 ok(reject===bad.length,"REJECTION_COUNT");
 return {real_source_rows:124,real_case_oracles:4,count_oracles:4,negative_rejections:reject,output_rows:a.table.length};
}
module.exports={parse,compute,csv,svg,selfTest};
if(require.main===module){
 const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
 const b=fs.readFileSync(path.join(__dirname,"S10_4CASE_31SEG_SYNC_GROSS_CONTROL_20261030.csv"));
 ok(crypto.createHash("sha256").update(b).digest("hex")===SOURCE_SHA,"SOURCE_SHA_MISMATCH");
 const s=b.toString("utf8"),t=selfTest(s),a=compute(s);
 fs.writeFileSync(path.join(__dirname,"S10_ETM31_GROSS_COMPRESSION_OFFSET_SCREEN_20261108.csv"),csv(a));
 fs.writeFileSync(path.join(__dirname,"../../../manuscript/final-thesis/figures/FIG4_S10_ETM31_GROSS_OFFSET_SCREEN_20261108.svg"),svg(a));
 process.stdout.write(JSON.stringify(t)+"\n");
}
