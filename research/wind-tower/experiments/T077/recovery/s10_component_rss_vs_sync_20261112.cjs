#!/usr/bin/env node
"use strict";
// Source-locked 4 ETM x 31 sections: marginal component vs synchronized
// 16-azimuth gross nominal-stress rainflow DEL4; not material Miner.
const COMP_SHA="7ca2dd4fa683b6f3c4534528bd0bcad7b2039c94ea37398e42941987f9580df4",SYNC_SHA="16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b";
const CASES=["U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06"];
const FIELDS=["case","segment","gage_z_m","sync_DEL4_MPa","sync_az_deg","Fz_DEL4_MPa","Mx_DEL4_MPa","My_DEL4_MPa","dominant_MPa","rss_MPa","sum_MPa","dominant_error_pct","rss_error_pct","sum_error_pct"];
function die(s){throw Error(s)}
function parse(text){let l=text.trim().split(/\r?\n/),h=l.shift().split(",");if(h.length!==new Set(h).size)die("DUPLICATE_HEADER");return l.map((s,i)=>{let a=s.split(",");if(a.length!==h.length)die("CSV_WIDTH_"+i);return Object.fromEntries(h.map((k,j)=>[k,a[j]]))})}
function number(s){if(s===""||!Number.isFinite(Number(s)))die("NONFINITE");return Number(s)}
function compute(component,synchronous){
 if(component.length!==124||synchronous.length!==1984)die("ROW_COUNT");
 const groups=new Map(),seen=new Set();
 for(const r of synchronous){
  if(!CASES.includes(r.case)||!/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(r.segment))die("BAD_SYNC_ID");
  const key=r.case+"|"+r.segment,az=number(r.azimuth_deg),i=Math.round(az/22.5),v=number(r.DEL_m4_MPa);
  if(i<0||i>=16||Math.abs(az-i*22.5)>1e-7||v<0)die("BAD_AZIMUTH_OR_DEL");
  if(number(r.n_samples)!==12001||r.stress_class!=="SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE")die("SYNC_CLASS");
  if(seen.has(key+"|"+i))die("DUPLICATE_AZIMUTH");seen.add(key+"|"+i);
  let g=groups.get(key)||{n:0,max:-1,az:0,z:number(r.gage_z_m)};
  if(Math.abs(g.z-number(r.gage_z_m))>1e-6)die("SYNC_GAGE");
  g.n++;if(v>g.max){g.max=v;g.az=az}groups.set(key,g);
 }
 if(groups.size!==124||[...groups.values()].some(g=>g.n!==16))die("INCOMPLETE_AZIMUTH_GRID");
 const out=[],keys=new Set();
 for(const r of component){
  if(!CASES.includes(r.case)||!/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(r.segment))die("BAD_COMPONENT_ID");
  let key=r.case+"|"+r.segment;if(keys.has(key))die("DUPLICATE_COMPONENT");keys.add(key);
  let g=groups.get(key);if(!g)die("MISSING_SYNC");
  let z=number(r.gage_z_m);if(Math.abs(z-g.z)>1e-6)die("GAGE_MISMATCH");
  let f=number(r.Fz_component_sigma_DEL_m4_MPa),x=number(r.Mx_component_sigma_DEL_m4_MPa),y=number(r.My_component_sigma_DEL_m4_MPa);
  if(Math.min(f,x,y)<0||g.max<=0)die("INVALID_DEL");
  let dom=Math.max(f,x,y),rss=Math.hypot(f,x,y),sum=f+x+y,err=v=>100*(v/g.max-1);
  out.push({case:r.case,segment:r.segment,z,sync:g.max,az:g.az,f,x,y,dom,rss,sum,ed:err(dom),er:err(rss),es:err(sum)});
 }
 return out.sort((a,b)=>CASES.indexOf(a.case)-CASES.indexOf(b.case)||a.segment.localeCompare(b.segment));
}
function csv(rows){const f=v=>typeof v==="number"?v.toFixed(9):v;return FIELDS.join(",")+"\n"+rows.map(r=>[r.case,r.segment,r.z,r.sync,r.az,r.f,r.x,r.y,r.dom,r.rss,r.sum,r.ed,r.er,r.es].map(f).join(",")).join("\n")+"\n"}
function summary(rows){let flips={dom:0,rss:0,sum:0};for(let i=1;i<=31;i++){let seg="CSEG_"+String(i).padStart(2,"0"),r=rows.filter(x=>x.segment===seg);if(r.length!==4)die("BAD_SEGMENT_GRID");let winner=k=>r.slice().sort((a,b)=>b[k]-a[k])[0].case;for(let k of Object.keys(flips))if(winner(k)!==winner("sync"))flips[k]++}let range=k=>[Math.min(...rows.map(x=>x[k])),Math.max(...rows.map(x=>x[k]))];return {rows:rows.length,flips,rssError:range("er"),sumError:range("es"),dominantError:range("ed")}}
function svg(rows){const W=1000,H=540,L=90,R=30,T=88,B=72,X=z=>L+z/112*(W-L-R),Y=e=>H-B-e/8*(H-T-B),colors=["#1768A0","#C66D33","#19866B","#8545A1"];let grid="",legend="",lines="";for(let v=0;v<=8;v+=2)grid+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#dce2e8"/><text x="'+(L-12)+'" y="'+(Y(v)+5)+'" text-anchor="end">'+v+'</text>';for(let v=0;v<=110;v+=20)grid+='<text x="'+X(v)+'" y="'+(H-B+24)+'" text-anchor="middle">'+v+'</text>';CASES.forEach((c,i)=>{let r=rows.filter(x=>x.case===c);lines+='<path d="'+r.map((q,j)=>(j?"L":"M")+X(q.z).toFixed(2)+","+Y(q.er).toFixed(2)).join(" ")+'" fill="none" stroke="'+colors[i]+'" stroke-width="3"/>';legend+='<line x1="'+(L+i*220)+'" x2="'+(L+23+i*220)+'" y1="65" y2="65" stroke="'+colors[i]+'" stroke-width="3"/><text x="'+(L+28+i*220)+'" y="70" font-size="12">'+c.replace("_ETM_"," / ")+'</text>'});return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 540" width="1000" height="540"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#273647"><text x="90" y="32" font-size="20" font-weight="bold">RSS of marginal DEL4 versus synchronized gross-stress DEL4</text>'+grid+legend+'<text x="500" y="510" text-anchor="middle" font-size="17">Gauge height z (m)</text><text transform="translate(24,275) rotate(-90)" text-anchor="middle" font-size="17">RSS overestimate (%)</text></g><line x1="90" x2="970" y1="468" y2="468" stroke="#273647"/>'+lines+'<text x="90" y="530" font-family="sans-serif" font-size="12">Historical ETM screening only; no PT, material fatigue, DLC1.2 or seismic claim.</text></svg>\n'}
function selftest(){const assert=require("assert");assert.strictEqual(Math.hypot(3,4,0),5);assert.throws(()=>parse("a,a\n1,2"),/DUPLICATE_HEADER/);assert.throws(()=>parse("a,b\n1"),/CSV_WIDTH/);assert.throws(()=>compute([],[]),/ROW_COUNT/);assert.throws(()=>number("NaN"),/NONFINITE/);console.log("S10_COMPONENT_SYNC_SELFTEST_PASS_SYNTHETIC_ONLY")}
function cli(){const fs=require("fs"),crypto=require("crypto"),a=process.argv.slice(2);if(a.includes("--self-test")){selftest();if(a.length===1)return}const opt=k=>{let i=a.indexOf(k);if(i<0||!a[i+1])die("MISSING_ARG_"+k);return a[i+1]},raw1=fs.readFileSync(opt("--component")),raw2=fs.readFileSync(opt("--sync")),hash=b=>crypto.createHash("sha256").update(b).digest("hex");if(hash(raw1)!==COMP_SHA||hash(raw2)!==SYNC_SHA)die("SOURCE_SHA256_MISMATCH");let rows=compute(parse(raw1.toString("utf8")),parse(raw2.toString("utf8")));fs.writeFileSync(opt("--csv"),csv(rows));fs.writeFileSync(opt("--svg"),svg(rows));console.log(JSON.stringify({status:"SOURCE_LEVEL_PASS_NOT_MATERIAL",summary:summary(rows)}))}
if(typeof require!=="undefined"&&require.main===module)cli();
