#!/usr/bin/env node
// Reproduce source-availability figure; Node.js 20+ standard library only, no physical simulation.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
function rows(s){
 const lines=s.replace(/^\uFEFF/,"").trimEnd().split(/\r?\n/);const cols=lines.shift().split(",");
 return lines.map((l,i)=>{const a=l.split(",");if(a.length!==cols.length)throw Error("CSV shape "+i);const o={};cols.forEach((k,j)=>o[k]=a[j]);return o});
}
function analyze(s1,s2){
 const b=rows(s1),m=rows(s2);if(b.length!==31||m.length!==126)throw Error("row count");
 let nt=0,no=0,covered=0,slots=0;const display=[];
 for(let i=0;i<31;i++){
  const r=b[i],h=Number(r.hours);if(Number(r.bin_lower_mps)!==i||!Number.isInteger(h)||h<0||Math.abs(Number(r.p_all_hours)-h/184080)>1e-12)throw Error("bin mismatch "+i);
  nt+=h;if(i<4||i>24)continue;no+=h;
  const group=m.filter(x=>Number(x.bin_lower_mps)===i);
  if(group.length!==6||new Set(group.map(x=>x.seed_id)).size!==6||[1,2,3,4,5,6].some(k=>!group.some(x=>x.seed_id==="S0"+k)))throw Error("six-seed contract "+i);
  const n=group.filter(x=>x.source_coverage_status==="ARCHIVED_NTM_SCREEN_ONLY").length;
  if(![0,6].includes(n))throw Error("partial source coverage "+i);
  for(const x of group){
   if(x.formal_DLC12_status!=="NOT_VALIDATED"||Number(x.era5_21y_hours)!==h)throw Error("false status/weight "+i);
   if(n){if(!x.historical_case_id||!/^[0-9a-f]{64}$/i.test(x.outb_sha256)||!/^[0-9a-f]{64}$/i.test(x.fst_sha256))throw Error("missing original identity "+i)}
   else if(x.source_coverage_status!=="NO_ARCHIVED_NTM_SOURCE"||x.historical_case_id)throw Error("source status "+i);
  }
  if(n){covered+=h;slots+=n}
  display.push({bin:i,hours:h,annual:h*8760/184080,present:n===6});
 }
 if(nt!==184080||no!==106900||covered!==7164||slots!==18)throw Error("source totals");
 if(display.filter(d=>!d.present&&d.hours>0).length!==13||display.filter(d=>d.hours===0).length!==5)throw Error("bin composition");
 return {nt,no,covered,slots,missing:no-covered,share:covered/no,display};
}
function makeSvg(d){
 const txt=(x,y,s,size=14,fill="#273e4c",weight=400,anchor="start")=>`<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}">${String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")}</text>`;
 const arr=['<?xml version="1.0" encoding="UTF-8"?>','<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="790" viewBox="0 0 1180 790" role="img" aria-label="ERA5 observed wind-bin annual exposure and archived NTM source coverage">','<rect width="1180" height="790" fill="#ffffff"/>'];
 arr.push(txt(72,55,"ERA5 operating-bin exposure and archived NTM sources",28,"#16364b",700));
 arr.push(txt(72,86,"2005–2025 · 184,080 hourly samples · 161.369 m hub · diagnostic 4–25 m/s window",16,"#516e83"));
 arr.push(txt(72,114,"Source availability only: NOT formal DLC 1.2, not material fatigue and not a design hazard ranking.",15,"#a06425",600));
 const left=107,right=1092,bottom=549,top=173,height=bottom-top,pitch=(right-left)/21;
 arr.push(txt(left,153,"ERA5 equivalent annual hours per 1 m/s wind-speed bin",15,"#344a5b",600));
 for(let y=0;y<=1500;y+=300){const py=bottom-y/1500*height;arr.push(`<line x1="${left}" y1="${py.toFixed(2)}" x2="${right}" y2="${py.toFixed(2)}" stroke="#d9e3e9"/>`);arr.push(txt(left-12,py+5,y,13,"#617589",400,"end"));}
 for(let k=0;k<d.display.length;k++){
  const v=d.display[k],x=left+k*pitch+8,w=pitch-16,rh=v.annual/1500*height,yy=bottom-rh;
  arr.push(`<rect x="${x.toFixed(2)}" y="${yy.toFixed(2)}" width="${w.toFixed(2)}" height="${rh.toFixed(3)}" rx="2" fill="${v.present?"#d58c38":"#acc9d9"}"/>`);
  arr.push(txt((x+w/2).toFixed(2),bottom+25,v.bin,12,"#394f60",400,"middle"));
  if(v.present)arr.push(`<circle cx="${(x+w/2).toFixed(2)}" cy="${bottom+38}" r="3.3" fill="#cf7722"/>`);
 }
 arr.push(txt((left+right)/2,616,"Wind-speed bin lower bound (m/s); each bin has width 1 m/s",15,"#354f61",500,"middle"));
 arr.push('<rect x="108" y="647" width="21" height="14" rx="2" fill="#acc9d9"/>');arr.push(txt(140,661,"No archived NTM case (18 bins)",14));
 arr.push('<rect x="450" y="647" width="21" height="14" rx="2" fill="#d58c38"/>');arr.push(txt(483,661,"Archived screening cases only (9, 11, 19 m/s; 6 seeds/bin)",14));
 arr.push('<line x1="105" y1="685" x2="1092" y2="685" stroke="#bbcdd8"/>');
 arr.push(txt(107,721,(100*d.share).toFixed(2)+"%",27,"#1d5c77",700));
 arr.push(txt(228,721,"of diagnostic operating hours have archived NTM source bins",14));
 arr.push(txt(737,721,`${d.slots}/126`,27,"#a96927",700));
 arr.push(txt(866,721,"screening slots; 0 formal verified",14));
 arr.push(txt(107,758,"Input: 31-bin ERA5-derived CSV + 126-slot NTM source table. Zero observed hours above 20 m/s ≠ zero design hazard.",12,"#687f90"));
 arr.push('<!-- SOURCE SHA256: ERA5=e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102; NTM matrix=d4e25023f343ea76f2de5ce90c7d24dd985df770ec9f4747d203391010431e67 -->');
 return arr.join("\n")+'\n</svg>\n';
}
function selfTest(s1,s2){
 const a=analyze(s1,s2);if(a.display.length!==21||a.missing!==99736)throw Error("positive oracle");
 const tests=[
  [s1.replace("0,1,6438,","0,1,6437,"),s2],
  [s1,s2.replace("NOT_VALIDATED","VALIDATED")],
  [s1,s2.replace("S01,,,,,,NO_ARCHIVED_NTM_SOURCE","S02,,,,,,NO_ARCHIVED_NTM_SOURCE")],
  [s1,s2.trimEnd().split(/\r?\n/).slice(0,-1).join("\n")+'\n'],
  [s1,s2.replace("NO_ARCHIVED_NTM_SOURCE","ARCHIVED_NTM_SCREEN_ONLY")],
  [s1.replace("26927,0.146278791830","26927,0.111111111111"),s2]
 ];
 for(let i=0;i<tests.length;i++){let failed=false;try{analyze(tests[i][0],tests[i][1])}catch(e){failed=true}if(!failed)throw Error("negative test "+i+" not rejected")}
 const svg=makeSvg(a);if(!svg.includes("6.70%")||!svg.includes("0 formal verified"))throw Error("figure QA failed");
 return{positive:1,negative:tests.length,figureCharacters:svg.length};
}
const here=dirname(fileURLToPath(import.meta.url));
const p1=process.argv[2]||join(here,'../../../experiments/T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv');
const p2=process.argv[3]||join(here,'../../../experiments/T062/S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv');
const out=process.argv[4]||join(here,'FIG3_S10_ERA5_NTM_SOURCE_COVERAGE_20261107.svg');
const s1=readFileSync(p1,'utf8'), s2=readFileSync(p2,'utf8');
const sha=s=>createHash('sha256').update(s,'utf8').digest('hex');
if(sha(s1)!=='e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102')throw Error('ERA5 SHA mismatch');
if(sha(s2)!=='d4e25023f343ea76f2de5ce90c7d24dd985df770ec9f4747d203391010431e67')throw Error('matrix SHA mismatch');
const checks=selfTest(s1,s2),a=analyze(s1,s2),svg=makeSvg(a);
writeFileSync(out,svg,'utf8');
console.log(JSON.stringify({status:'SOURCE_ONLY_NOT_DLC12',checks,summary:{total:a.nt,operating:a.no,screening_bin_hours:a.covered,missing_bin_hours:a.missing,screening_slots:a.slots,formal_verified:0},figure_sha256:sha(svg)},null,2));
