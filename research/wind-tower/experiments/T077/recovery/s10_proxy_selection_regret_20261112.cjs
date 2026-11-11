#!/usr/bin/env node
"use strict";
// Source-paired ETM proxy-selection regret, 31 segments; no solver, no material Miner.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const INPUT_SHA="c9dcca1a582fd5343f181a7adb146d44f9ebeac164b4f5b2ea2d3f8f3ca19dbd";
const INPUT="S10_4ETM_31SEG_COMPONENT_RSS_VS_SYNC_124ROW_20261112.csv";
const OUTPUT="S10_4ETM_31SEG_PROXY_SELECTION_REGRET_31ROW_20261112.csv";
const MODES=[["dominant","dominant_MPa"],["rss","rss_MPa"],["sum","sum_MPa"]];
const COLUMNS=["case","segment","gage_z_m","sync_DEL4_MPa","sync_az_deg","Fz_DEL4_MPa","Mx_DEL4_MPa","My_DEL4_MPa","dominant_MPa","rss_MPa","sum_MPa","dominant_error_pct","rss_error_pct","sum_error_pct"];
function parse(raw){
 const lines=raw.trimEnd().split(/\r?\n/),header=lines.shift().split(",");
 assert.deepEqual(header,COLUMNS,"unexpected source columns");
 const data=lines.map(line=>{
  const parts=line.split(",");assert.equal(parts.length,COLUMNS.length,"bad CSV width");
  const r=Object.fromEntries(COLUMNS.map((key,i)=>[key,i<2?parts[i]:Number(parts[i])]));
  for(const k of COLUMNS.slice(2))assert(Number.isFinite(r[k]),"nonfinite "+k);
  assert(r.sync_DEL4_MPa>0&&r.gage_z_m>=0,"nonpositive DEL or height");
  const c=[r.Fz_DEL4_MPa,r.Mx_DEL4_MPa,r.My_DEL4_MPa];
  assert(Math.abs(Math.max(...c)-r.dominant_MPa)<3e-9,"dominant identity");
  assert(Math.abs(Math.hypot(...c)-r.rss_MPa)<3e-9,"RSS identity");
  assert(Math.abs(c.reduce((a,b)=>a+b,0)-r.sum_MPa)<3e-9,"sum identity");
  return r;
 });
 assert.equal(data.length,124,"need 4 ETM cases x 31 segments");
 const pairs=new Set();
 for(const r of data){const key=r.case+"|"+r.segment;assert(!pairs.has(key),"duplicate case-segment");pairs.add(key)}
 return data;
}
function select(rs,key){return [...rs].sort((a,b)=>(b[key]-a[key])||a.case.localeCompare(b.case))[0]}
function compute(rows){
 const out=[];
 for(let i=1;i<=31;i++){
  const seg="CSEG_"+String(i).padStart(2,"0"),rs=rows.filter(r=>r.segment===seg);
  assert.equal(rs.length,4,"missing segment "+seg);
  assert.equal(new Set(rs.map(r=>r.case)).size,4,"duplicate case "+seg);
  assert(Math.max(...rs.map(r=>r.gage_z_m))-Math.min(...rs.map(r=>r.gage_z_m))<1e-8,"gage identity");
  const best=select(rs,"sync_DEL4_MPa");
  const row={segment:seg,gage_z_m:best.gage_z_m,sync_best_case:best.case,sync_best_DEL4_MPa:best.sync_DEL4_MPa};
  for(const [name,key] of MODES){
   const chosen=select(rs,key),regret=best.sync_DEL4_MPa-chosen.sync_DEL4_MPa;
   assert(regret>=-1e-8,"negative selection regret");
   row[name+"_selected_case"]=chosen.case;
   row[name+"_selected_sync_DEL4_MPa"]=chosen.sync_DEL4_MPa;
   row[name+"_regret_MPa"]=regret;
   row[name+"_regret_pct"]=100*regret/best.sync_DEL4_MPa;
  }
  out.push(row);
 }
 return out;
}
const fields=["segment","gage_z_m","sync_best_case","sync_best_DEL4_MPa",...MODES.flatMap(([n])=>[n+"_selected_case",n+"_selected_sync_DEL4_MPa",n+"_regret_MPa",n+"_regret_pct"])];
function toCSV(rows){return fields.join(",")+"\n"+rows.map(r=>fields.map(k=>typeof r[k]==="number"?r[k].toFixed(9):r[k]).join(",")).join("\n")+"\n"}
function selftest(){
 const row=(caseName,seg,sync,dom,rss,sum)=>({case:caseName,segment:seg,gage_z_m:Number(seg.slice(-2)),sync_DEL4_MPa:sync,Fz_DEL4_MPa:0,Mx_DEL4_MPa:0,My_DEL4_MPa:dom,dominant_MPa:dom,rss_MPa:rss,sum_MPa:sum});
 const fixture=[];for(let i=1;i<=31;i++){const s="CSEG_"+String(i).padStart(2,"0");fixture.push(row("A",s,10,9,9,9),row("B",s,8,11,12,13),row("C",s,7,6,7,8),row("D",s,6,5,6,7))}
 const x=compute(fixture);assert.equal(x.length,31);assert.equal(x[0].sum_selected_case,"B");assert(Math.abs(x[0].sum_regret_pct-20)<1e-12);
 assert.throws(()=>compute(fixture.slice(1)),/missing segment/);
 assert.throws(()=>compute([...fixture.slice(0,-1),fixture[0]]),/duplicate case/);
 assert.throws(()=>compute(fixture.map((r,i)=>i===0?{...r,sync_DEL4_MPa:-1}:r)),/negative selection regret|/);
 console.log("SELFTEST_PASS:31 segment fixture; missing and duplicate rejection");
}
function main(){
 if(process.argv.includes("--selftest"))return selftest();
 const args=process.argv.slice(2),get=(name,def)=>{const i=args.indexOf(name);return i<0?def:args[i+1]};
 const input=get("--input",path.join(__dirname,INPUT)),output=get("--output",path.join(__dirname,OUTPUT));
 const bytes=fs.readFileSync(input),sha=crypto.createHash("sha256").update(bytes).digest("hex");
 assert.equal(sha,INPUT_SHA,"SOURCE_SHA256_MISMATCH");
 const out=compute(parse(bytes.toString("utf8")));
 fs.writeFileSync(output,toCSV(out),"utf8");
 const summary=Object.fromEntries(MODES.map(([n])=>{const a=out.map(r=>r[n+"_regret_pct"]),changed=out.filter(r=>r[n+"_selected_case"]!==r.sync_best_case);return [n,{changed:changed.length,max_pct:Math.max(...a),mean_pct:a.reduce((s,v)=>s+v,0)/a.length}]}));
 assert.equal(summary.rss.changed,2);assert.equal(summary.sum.changed,31);
 assert(Math.abs(summary.rss.max_pct-0.0742446067251565)<1e-8);
 assert(Math.abs(summary.sum.max_pct-18.61350436615383)<1e-8);
 console.log(JSON.stringify({source_sha256:sha,output,segments:out.length,summary},null,2));
}
main();
