"use strict";
// S10 original-NTM nominal stress: fixed-location vs adaptive/max-seed DEL aggregation.
// Source-only statistical study; not material fatigue or a new wind/structural run.
const fs=require("node:fs"),crypto=require("node:crypto");
const SOURCE="research/wind-tower/experiments/T062/S10_18NTM_10NEARBASE_16AZ_GROSS_RAINFLOW_20261031.csv";
const CONTROL="research/wind-tower/experiments/T062/S10_18NTM_6SEED_GROSS_STRESS_CONTROL_20261031.csv";
const EXPECTED="d45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b";
const BINS=["U09p343881_NTM","U11p4_NTM","U19p202140_NTM"],ST=["BASE","G01","G02","G03","G04","G05","G06","G07","G08","G09"],AZ=Array.from({length:16},(_,i)=>i*22.5);
function ok(x,msg){if(!x)throw Error(msg);}
function hash(s){return crypto.createHash("sha256").update(s,"utf8").digest("hex");}
function parse(csv,verify=true){
 if(verify)ok(hash(csv)===EXPECTED,"SHA256");
 const a=csv.trim().split(/\r?\n/),h=a.shift().split(","),ix=Object.fromEntries(h.map((k,i)=>[k,i]));
 for(const k of ["case","wind_bin","seed","station","z_m","local_azimuth_deg","DEL_m4_MPa","DEL_m10_MPa","rainflow_equivalent_cycles","source_outb_sha256","stress_class"])ok(k in ix,"HEADER");
 ok(a.length===2880,"ROWS");
 const groups=new Map(),seen=new Set(),hashes=new Map();
 for(const line of a){
  const v=line.split(",");ok(v.length===h.length,"WIDTH");
  const b=v[ix.wind_bin],st=v[ix.station],sd=+v[ix.seed],az=+v[ix.local_azimuth_deg],z=+v[ix.z_m],id=v[ix.case],src=v[ix.source_outb_sha256];
  ok(BINS.includes(b)&&ST.includes(st),"IDENTITY");
  ok(Number.isInteger(sd)&&sd>=1&&sd<=6&&id===b+"_S0"+sd,"SEED");
  ok(AZ.includes(az)&&Number.isFinite(z)&&z>=0&&z<3,"COORD");
  ok(/^[a-f0-9]{64}$/.test(src),"OUTB_HASH");
  ok(v[ix.stress_class]==="ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE","CLASS");
  if(hashes.has(id))ok(hashes.get(id)===src,"HASH_DRIFT");hashes.set(id,src);
  const d4=+v[ix.DEL_m4_MPa],d10=+v[ix.DEL_m10_MPa],n=+v[ix.rainflow_equivalent_cycles];
  ok([d4,d10,n].every(x=>Number.isFinite(x)&&x>0),"VALUE");
  const key=b+"|"+st,uniq=key+"|"+sd+"|"+az;ok(!seen.has(uniq),"DUP");seen.add(uniq);
  if(!groups.has(key))groups.set(key,{b,st,z,seeds:new Map()});
  const g=groups.get(key);ok(Math.abs(g.z-z)<1e-10,"Z_DRIFT");
  if(!g.seeds.has(sd))g.seeds.set(sd,new Map());
  g.seeds.get(sd).set(az,{4:d4,10:d10});
 }
 ok(groups.size===30&&seen.size===2880&&hashes.size===18,"COVERAGE");
 for(const g of groups.values()){ok(g.seeds.size===6,"SEED_COUNT");for(let sd=1;sd<=6;sd++)ok(g.seeds.has(sd)&&g.seeds.get(sd).size===16&&AZ.every(a=>g.seeds.get(sd).has(a)),"AZ_COVER");}
 return groups;
}
function pmean(a,m){ok(a.length&&a.every(v=>Number.isFinite(v)&&v>0),"PMEAN");return (a.reduce((s,x)=>s+x**m,0)/a.length)**(1/m);}
function analyze(csv,verify=true){
 const groups=parse(csv,verify),out=[];
 for(const b of BINS)for(const st of ST)for(const m of [4,10]){
  const g=groups.get(b+"|"+st);
  const fixed=AZ.map(az=>{const d=Array.from({length:6},(_,i)=>g.seeds.get(i+1).get(az)[m]);return {az,p:pmean(d,m),arith:d.reduce((s,x)=>s+x,0)/6};}).sort((x,y)=>y.p-x.p||x.az-y.az)[0];
  const seedMax=Array.from({length:6},(_,i)=>AZ.map(az=>({az,d:g.seeds.get(i+1).get(az)[m]})).sort((x,y)=>y.d-x.d||x.az-y.az)[0]);
  const adapt=pmean(seedMax.map(x=>x.d),m),max=Math.max(...seedMax.map(x=>x.d));
  ok(fixed.arith<=fixed.p+1e-10&&fixed.p<=adapt+1e-10&&adapt<=max+1e-10,"ORDER");
  out.push({wind_bin:b,station:st,z_m:g.z,m,fixed_az_deg:fixed.az,
   fixed_power_MPa:fixed.p,arithmetic_MPa:fixed.arith,adaptive_MPa:adapt,max_seed_MPa:max,
   arithmetic_DEL_under_pct:100*(1-fixed.arith/fixed.p),
   arithmetic_mmoment_under_pct:100*(1-(fixed.arith/fixed.p)**m),
   adaptive_DEL_over_pct:100*(adapt/fixed.p-1),
   max_seed_DEL_over_pct:100*(max/fixed.p-1),
   max_seed_mmoment_over_pct:100*((max/fixed.p)**m-1),
   seed_az_count:new Set(seedMax.map(x=>x.az)).size,seed_az_deg:seedMax.map(x=>x.az).join("/")});
 }
 return out;
}
const KEYS=["wind_bin","station","z_m","m","fixed_az_deg","fixed_power_MPa","arithmetic_MPa","adaptive_MPa","max_seed_MPa","arithmetic_DEL_under_pct","arithmetic_mmoment_under_pct","adaptive_DEL_over_pct","max_seed_DEL_over_pct","max_seed_mmoment_over_pct","seed_az_count","seed_az_deg"];
function csv(rows,base=false){const keys=base?KEYS.filter(k=>!["station","z_m","seed_az_count","seed_az_deg"].includes(k)):KEYS;return keys.join(",")+"\n"+rows.filter(r=>!base||r.station==="BASE").map(r=>keys.map(k=>typeof r[k]==="number"?r[k].toFixed(9):r[k]).join(",")).join("\n")+"\n";}
function svg(rows){
 const base=rows.filter(r=>r.station==="BASE"),s=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="570" viewBox="0 0 1200 570">','<rect width="1200" height="570" fill="white"/>','<text x="40" y="44" font-family="Arial" font-size="24" font-weight="bold" fill="#22313d">Six-seed nominal DEL: aggregation operator bias</text>','<text x="40" y="69" font-family="Arial" font-size="14" fill="#536475">BASE 0 m | three archived NTM wind bins | reference = fixed-azimuth power mean</text>'];
 for(const [m,x] of [[4,40],[10,630]]){
  const zero=x+190,scale=10,y=105;s.push('<rect x="'+x+'" y="'+y+'" width="535" height="360" rx="8" fill="#f7fafb" stroke="#dbe3e9"/>');
  s.push('<text x="'+(x+18)+'" y="'+(y+32)+'" font-family="Arial" font-size="20" font-weight="bold" fill="#22313d">m = '+m+'</text>');
  for(const tick of [-10,-5,0,5,10,15,20]){let xx=zero+tick*scale;s.push('<line x1="'+xx+'" x2="'+xx+'" y1="'+(y+46)+'" y2="'+(y+325)+'" stroke="'+(tick===0?"#778994":"#e0e6ea")+'"/>');s.push('<text x="'+xx+'" y="'+(y+347)+'" font-family="Arial" font-size="12" text-anchor="middle">'+tick+'%</text>');}
  base.filter(r=>r.m===m).forEach((r,i)=>{
   const yy=y+98+i*83;s.push('<text x="'+(x+12)+'" y="'+(yy+9)+'" font-family="Arial" font-size="13" fill="#304653">'+["9.344","11.400","19.202"][i]+' m/s</text>');
   [{v:-r.arithmetic_DEL_under_pct,c:"#b65347"},{v:r.adaptive_DEL_over_pct,c:"#3c9580"},{v:r.max_seed_DEL_over_pct,c:"#365e96"}].forEach((d,j)=>{
    const py=yy-12+j*16,xx=zero+d.v*scale;
    s.push('<line x1="'+Math.min(xx,zero)+'" x2="'+Math.max(xx,zero)+'" y1="'+py+'" y2="'+py+'" stroke="'+d.c+'" stroke-width="6"/>');
    s.push('<circle cx="'+xx+'" cy="'+py+'" r="4" fill="'+d.c+'"/>');
    if(j!==1)s.push('<text x="'+(xx+(d.v<0?-6:6))+'" y="'+(py+4)+'" font-family="Arial" font-size="12" text-anchor="'+(d.v<0?"end":"start")+'" fill="'+d.c+'">'+d.v.toFixed(3)+'%</text>');
   });
  });
 }
 s.push('<text x="40" y="510" font-family="Arial" font-size="14" fill="#b65347">● Arithmetic at fixed azimuth</text>','<text x="410" y="510" font-family="Arial" font-size="14" fill="#3c9580">● Per-seed adaptive azimuth</text>','<text x="805" y="510" font-family="Arial" font-size="14" fill="#365e96">● Maximum single seed</text>','<text x="40" y="545" font-family="Arial" font-size="13" fill="#536475">Percent relative to fixed-location six-seed power mean; not local material stress, Miner damage or formal DLC1.2.</text>','</svg>');
 return s.join("\n")+"\n";
}
function control(rows,text){
 const a=text.trim().split(/\r?\n/),h=a.shift().split(","),ix=Object.fromEntries(h.map((k,i)=>[k,i]));ok(a.length===30,"CONTROL_ROWS");let max=0;
 for(const line of a){const v=line.split(","),b=v[ix.wind_bin],st=v[ix.station];for(const m of [4,10]){const r=rows.find(x=>x.wind_bin===b&&x.station===st&&x.m===m);ok(r,"CONTROL_KEY");const e=Math.abs(r.fixed_power_MPa-+v[ix["six_seed_power_DEL_m"+m+"_MPa"]]);max=Math.max(max,e);ok(e<1e-9,"CONTROL_VALUE");}}
 return max;
}
function test(text,ctrl){
 const rows=analyze(text),base=rows.filter(x=>x.station==="BASE");
 ok(Math.abs(base[0].fixed_power_MPa-3.24107173356)<1e-9&&Math.abs(base[3].fixed_power_MPa-9.48905821632)<1e-9,"REAL");
 ok(Math.abs(base[3].arithmetic_mmoment_under_pct-59.120381559)<1e-6,"MOMENT");
 ok(Math.abs(pmean([1,3],4)-41**.25)<1e-12,"TOY");
 const oracle=control(rows,ctrl),lines=text.trim().split(/\r?\n/),h=lines[0].split(","),ix=Object.fromEntries(h.map((k,i)=>[k,i]));
 const change=(col,val)=>{const a=lines.slice(),v=a[1].split(",");v[ix[col]]=val;a[1]=v.join(",");return a.join("\n")+"\n";};
 const bad=[change("seed","9"),change("local_azimuth_deg","17"),change("DEL_m4_MPa","NaN"),change("DEL_m10_MPa","-1"),change("case","U11p4_NTM_S01"),change("source_outb_sha256","0".repeat(64)),change("stress_class","MATERIAL"),change("z_m","-1"),lines.slice(0,-1).join("\n")+"\n"];
 for(const b of bad){let rejected=false;try{analyze(b,false);}catch(e){rejected=true;}ok(rejected,"BAD_ACCEPTED");}
 let rejected=false;try{analyze(change("DEL_m4_MPa","9.9"),true);}catch(e){rejected=true;}ok(rejected,"SHA_BAD_ACCEPTED");
 ok(csv(rows)===csv(analyze(lines[0]+"\n"+lines.slice(1).reverse().join("\n")+"\n",false)),"ORDER");
 return {source_sha256:hash(text),control_rows:30,max_control_abs_MPa:oracle,real_anchors:3,analytic_oracle:1,rejections:10,order_invariant:true};
}
module.exports={parse,pmean,analyze,csv,svg,control,test};
if(require.main===module){
 const text=fs.readFileSync(process.argv[2]||SOURCE,"utf8"),ctl=fs.readFileSync(process.argv[3]||CONTROL,"utf8"),rows=analyze(text),result=test(text,ctl);
 if(process.argv.includes("--emit")){
  fs.writeFileSync("research/wind-tower/experiments/T062/S10_NTM18_FIXED_VS_ADAPTIVE_SEED_AGG_60ROW_20261110.csv",csv(rows));
  fs.writeFileSync("research/wind-tower/experiments/T062/S10_NTM18_SEED_AGGREGATION_BASE_6ROW_20261110.csv",csv(rows,true));
  fs.writeFileSync("research/wind-tower/manuscript/final-thesis/figures/FIG4_S10_NTM18_SEED_AGGREGATION_BIAS_20261110.svg",svg(rows));
 }
 console.log(JSON.stringify(result,null,2));
}
