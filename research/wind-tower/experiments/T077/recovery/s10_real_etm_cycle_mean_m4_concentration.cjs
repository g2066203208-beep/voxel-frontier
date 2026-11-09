#!/usr/bin/env node
"use strict";
/* Archived 1574 real ETM gross-nominal cycles. No material damage or DLC1.2 claim. */
const SOURCE_SHA="646065838456b6465e321c4c6fd24966f180f275df99c615000577557219ff83";
const HEADER="case,segment,azimuth_deg,cycle_index,range_MPa,amplitude_MPa,mean_gross_MPa,mean_Pe_hypothesis_MPa,mean_P0_hypothesis_MPa,count,status";
const STATUS="REAL_GROSS_NOMINAL_CYCLES_PT_MEAN_SHIFT_HYPOTHESIS_NOT_LOCAL_MATERIAL";
const CONTROLS=[
 ["U09p343881_ETM_S06/CSEG_16/180",413,407.5,7.05273183802,17.1088699574],
 ["U09p343881_ETM_S06/CSEG_17/180",526,520.5,7.03716180072,17.0407934127],
 ["U11p4_ETM_S04/CSEG_04/0",635,628,7.16908904914,14.5371179573]
];
function analyze(raw){
 const lines=raw.trimEnd().split(/\r?\n/);
 if(lines.shift()!==HEADER||lines.length!==1574)throw Error("SCHEMA_OR_ROWS");
 const groups=new Map(CONTROLS.map(c=>[c[0],[]]));
 for(const line of lines){
  const a=line.split(","),key=a.slice(0,3).join("/"),g=groups.get(key);
  if(a.length!==11||!g)throw Error("CONTROL_OR_WIDTH");
  const idx=+a[3],r=+a[4],amp=+a[5],mean=+a[6],pe=+a[7],p0=+a[8],n=+a[9];
  if(![idx,r,amp,mean,pe,p0,n].every(Number.isFinite)||idx!==g.length+1||r<=0||Math.abs(r-2*amp)>1e-8||!(n===0.5||n===1)||a[10]!==STATUS)throw Error("INVALID_CYCLE");
  g.push({r,mean,n});
 }
 return CONTROLS.map(c=>{
  const g=groups.get(c[0]),N=g.reduce((s,x)=>s+x.n,0);
  const M4=g.reduce((s,x)=>s+x.n*x.r**4,0),M10=g.reduce((s,x)=>s+x.n*x.r**10,0);
  const d4=(M4/600)**.25,d10=(M10/600)**.1;
  if(g.length!==c[1]||Math.abs(N-c[2])>1e-8||Math.abs(d4-c[3])>1e-7||Math.abs(d10-c[4])>1e-7)throw Error("HISTORICAL_DEL_ORACLE");
  const mu=g.reduce((s,x)=>s+x.n*x.mean,0)/N,mu4=g.reduce((s,x)=>s+x.n*x.r**4*x.mean,0)/M4;
  const mr=g.reduce((s,x)=>s+x.n*x.r,0)/N;
  const cov=g.reduce((s,x)=>s+x.n*(x.r-mr)*(x.mean-mu),0)/N;
  const vr=g.reduce((s,x)=>s+x.n*(x.r-mr)**2,0)/N,vm=g.reduce((s,x)=>s+x.n*(x.mean-mu)**2,0)/N;
  const sorted=[...g].sort((a,b)=>b.r-a.r);let remaining=.01*N,top4=0;
  for(const x of sorted){const n=Math.min(x.n,remaining);if(n<=0)break;top4+=n*x.r**4;remaining-=n}
  if(Math.abs(remaining)>1e-8)throw Error("TOP_ONE_PERCENT");
  const frac=q=>{const sel=g.filter(x=>x.mean+x.r/2>q);return [sel.reduce((s,x)=>s+x.n,0)/N,sel.reduce((s,x)=>s+x.n*x.r**4,0)/M4]};
  const [p0,p0m4]=frac(0),[p20,p20m4]=frac(20);
  return {key:c[0],rows:g.length,N,d4,d10,mu,mu4,corr:cov/Math.sqrt(vr*vm),top1:top4/M4,p0,p0m4,p20,p20m4,maxUpper:Math.max(...g.map(x=>x.mean+x.r/2))};
 });
}
function makeCSV(a){
 const cols="case,segment,azimuth_deg,cycle_rows,equivalent_cycles,DEL4_MPa,DEL10_MPa,count_weighted_cycle_mean_MPa,m4_weighted_cycle_mean_MPa,range_mean_Pearson,top1pct_count_m4_share,positive_upper_count_share,positive_upper_m4_share,upper_gt20_count_share,upper_gt20_m4_share,max_cycle_upper_MPa,source_level";
 const f=x=>Number(x).toFixed(9);
 return cols+"\n"+a.map(x=>[...x.key.split("/"),x.rows,f(x.N),...[x.d4,x.d10,x.mu,x.mu4,x.corr,x.top1,x.p0,x.p0m4,x.p20,x.p20m4,x.maxUpper].map(f),"ETM_GROSS_NOMINAL_NOT_MATERIAL"].join(",")).join("\n")+"\n";
}
function makeSVG(a){
 const L=90,R=660,B=490,H=330,colors=["#246e9b","#c97836","#3e866c"];
 let v=['<svg xmlns="http://www.w3.org/2000/svg" width="1190" height="640" viewBox="0 0 1190 640">',
 '<rect width="1190" height="640" fill="white"/>',
 '<text x="70" y="44" font-family="Arial" font-size="23" font-weight="bold" fill="#14283b">Archived ETM: fourth-moment concentration and cycle-mean exposure</text>',
 '<text x="70" y="73" font-family="Arial" font-size="14" fill="#536579">1,574 real gross-nominal rainflow cycles; count=0.5/1; m=4 diagnostic only</text>'];
 for(const [x,title] of [[L,"A  Largest 1% cycle weight: M4 share"],[R,"B  Upper reversal > 0: count / M4 shares"]]){
  v.push('<text x="'+x+'" y="119" font-family="Arial" font-size="17" font-weight="bold" fill="#243b53">'+title+'</text>');
  for(const p of [0,25,50,75,100]){let y=B-H*p/100;v.push('<line x1="'+x+'" y1="'+y+'" x2="'+(x+445)+'" y2="'+y+'" stroke="#e2e9ef"/>');v.push('<text x="'+(x-12)+'" y="'+(y+4)+'" text-anchor="end" font-family="Arial" font-size="12">'+p+'%</text>')}
 }
 a.forEach((x,i)=>{
  const label=x.key.split("/")[1],xa=L+63+i*138,ya=B-H*x.top1;
  v.push('<rect x="'+xa+'" y="'+ya.toFixed(2)+'" width="76" height="'+(B-ya).toFixed(2)+'" fill="'+colors[i]+'"/>');
  v.push('<text x="'+(xa+38)+'" y="'+(ya-8).toFixed(2)+'" text-anchor="middle" font-family="Arial" font-size="13">'+(100*x.top1).toFixed(2)+'%</text>');
  for(const [j,fraction,color] of [[0,x.p0,"#a1b9c9"],[1,x.p0m4,colors[i]]]){
   const xx=R+52+i*138+j*35,yy=B-H*fraction;
   if(fraction>0)v.push('<rect x="'+xx+'" y="'+yy.toFixed(2)+'" width="31" height="'+(B-yy).toFixed(2)+'" fill="'+color+'"/>');
   v.push('<text x="'+(xx+15)+'" y="'+Math.max(144,yy-8).toFixed(2)+'" text-anchor="middle" font-family="Arial" font-size="11">'+(100*fraction).toFixed(1)+'</text>');
  }
  v.push('<text x="'+(xa+38)+'" y="515" text-anchor="middle" font-family="Arial" font-size="12">'+label+'</text>');
  v.push('<text x="'+(R+85+i*138)+'" y="515" text-anchor="middle" font-family="Arial" font-size="12">'+label+'</text>');
 });
 v.push('<rect x="742" y="549" width="15" height="12" fill="#a1b9c9"/><text x="765" y="561" font-family="Arial" font-size="13">Count share</text>');
 v.push('<rect x="931" y="549" width="15" height="12" fill="#3e866c"/><text x="954" y="561" font-family="Arial" font-size="13">M4 share</text>');
 v.push('<text x="70" y="595" font-family="Arial" font-size="12" fill="#536579">A uses fractional count interpolation at exactly 1%. B: upper = cycle mean + range/2, no effective PT included.</text>');
 v.push('<text x="70" y="619" font-family="Arial" font-size="12" fill="#536579">Historical ETM screening only; not normal-operation DLC1.2, material stress, Miner damage or fatigue life.</text>','</svg>');
 return v.join("\n")+"\n";
}
module.exports={analyze,makeCSV,makeSVG};
if(require.main===module){
 const fs=require("fs"),path=require("path"),crypto=require("crypto"),dir=__dirname;
 const raw=fs.readFileSync(path.join(dir,"S10_3CONTROL_REAL_GROSS_CYCLES_20261030.csv"),"utf8");
 if(crypto.createHash("sha256").update(raw).digest("hex")!==SOURCE_SHA)throw Error("SOURCE_SHA256_MISMATCH");
 const a=analyze(raw),csv=makeCSV(a),svg=makeSVG(a),mode=process.argv[2]||"--verify";
 const cpath=path.join(dir,"S10_ETM3_CYCLE_MEAN_M4_CONCENTRATION_20261109.csv");
 const spath=path.join(dir,"../../../manuscript/final-thesis/figures/FIG4_S10_ETM_CYCLE_MEAN_M4_CONCENTRATION_20261109.svg");
 if(mode==="--write"){fs.writeFileSync(cpath,csv);fs.writeFileSync(spath,svg)}
 else if(mode==="--verify"){if(fs.readFileSync(cpath,"utf8")!==csv||fs.readFileSync(spath,"utf8")!==svg)throw Error("OUTPUT_MISMATCH")}
 else if(mode==="--self-test"){
  let rejects=0;
  for(const bad of [raw.replace(",0.5,REAL_GROSS",",0.7,REAL_GROSS"),raw.replace("CSEG_16,180,1,","CSEG_16,180,9,"),raw.replace("0.0513027430895","-0.0513027430895"),raw.split("\n").slice(0,-2).join("\n"),raw.replace("CSEG_16,180,1,","CSEG_99,180,1,")]){try{analyze(bad)}catch(_){rejects++}}
  if(rejects!==5||Math.abs(a[0].top1-.9791917930995657)>1e-10||Math.abs(a[2].top1-.8192389548331043)>1e-10)throw Error("NEGATIVE_OR_ORACLE_FAIL");
  console.log("S10_SELFTEST_PASS 5 rejected / 2 independent oracles");
 }else throw Error("UNKNOWN_MODE");
 console.log("S10_REAL_ETM_PASS 1574 source cycles, 3 controls; NOT MATERIAL LIFE");
}
