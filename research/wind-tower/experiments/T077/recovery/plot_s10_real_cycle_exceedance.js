#!/usr/bin/env node
/* S10 true archived ETM gross nominal cycles -> vector FIG and 3-row table.
 * NO Abaqus/ODB, material S-N, design-life fatigue or DLC1.2 claims.
 * Source SHA256: 646065838456b6465e321c4c6fd24966f180f275df99c615000577557219ff83
 * Usage: node plot_s10_real_cycle_exceedance.js --verify | --write | --self-test
 */
"use strict";
const fs=require("fs"),path=require("path"),crypto=require("crypto");
const INPUT="S10_3CONTROL_REAL_GROSS_CYCLES_20261030.csv";
const EXPECTED="646065838456b6465e321c4c6fd24966f180f275df99c615000577557219ff83";
const FIG="FIG4_S10_REAL_CONTROL_RANGE_EXCEEDANCE_20261030.svg";
const TABLE="S10_3CONTROL_REAL_CYCLE_EXCEEDANCE_SUMMARY_20261030.csv";
const build=function build(raw){
  const rows=raw.trimEnd().split(/\r?\n/),header=rows.shift().split(",");
  const expectedHeader=["case","segment","azimuth_deg","cycle_index","range_MPa","amplitude_MPa","mean_gross_MPa","mean_Pe_hypothesis_MPa","mean_P0_hypothesis_MPa","count","status"];
  if(header.join("|")!==expectedHeader.join("|")||rows.length!==1574)throw Error("S10_SCHEMA_OR_1574_ROWS");
  const controls=[
    {case:"U09p343881_ETM_S06",segment:"CSEG_16",az:"180",label:"U09 S06 / CSEG16 / 180 deg",rows:413,n:407.5,d4:7.05273183802,d10:17.1088699574,color:"#2474A6"},
    {case:"U09p343881_ETM_S06",segment:"CSEG_17",az:"180",label:"U09 S06 / CSEG17 / 180 deg",rows:526,n:520.5,d4:7.03716180072,d10:17.0407934127,color:"#CE6F2B"},
    {case:"U11p4_ETM_S04",segment:"CSEG_04",az:"0",label:"U11 S04 / CSEG04 / 0 deg",rows:635,n:628,d4:7.16908904914,d10:14.5371179573,color:"#368064"}
  ];
  const grouped=new Map(controls.map(c=>[[c.case,c.segment,c.az].join("/"),[]]));
  for(const line of rows){
    const r=line.split(",");if(r.length!==11)throw Error("S10_ROW_WIDTH");
    const key=[r[0],r[1],r[2]].join("/"),g=grouped.get(key);
    if(!g)throw Error("UNEXPECTED_CONTROL");
    const rng=Number(r[4]),amp=Number(r[5]),mean=Number(r[6]),pe=Number(r[7]),p0=Number(r[8]),n=Number(r[9]),idx=Number(r[3]);
    if(![rng,amp,mean,pe,p0,n,idx].every(Number.isFinite)||rng<=0||!([.5,1].includes(n))||idx!==g.length+1||Math.abs(rng-2*amp)>1e-8||r[10]!=="REAL_GROSS_NOMINAL_CYCLES_PT_MEAN_SHIFT_HYPOTHESIS_NOT_LOCAL_MATERIAL")throw Error("INVALID_REAL_CYCLE");
    g.push({rng,mean,n});
  }
  const fmt=x=>Number(x).toFixed(9),out=[];
  function quant(g,q){const s=[...g].sort((a,b)=>a.rng-b.rng);const total=s.reduce((a,b)=>a+b.n,0),target=total*q;let acc=0;for(const p of s){acc+=p.n;if(acc>=target-1e-12)return p.rng}return s[s.length-1].rng}
  for(const c of controls){
    const g=grouped.get([c.case,c.segment,c.az].join("/"));
    const n=g.reduce((s,v)=>s+v.n,0),d4=(g.reduce((s,v)=>s+v.n*v.rng**4,0)/600)**.25,d10=(g.reduce((s,v)=>s+v.n*v.rng**10,0)/600)**.1;
    if(g.length!==c.rows||Math.abs(n-c.n)>1e-8||Math.abs(d4-c.d4)>1e-7||Math.abs(d10-c.d10)>1e-7)throw Error("PRIOR_RAINFLOW_ORACLE_MISMATCH");
    const exceed=x=>g.reduce((s,v)=>s+(v.rng>=x?v.n:0),0)/n;
    out.push({...c,g,p50:quant(g,.5),p90:quant(g,.9),p99:quant(g,.99),max:Math.max(...g.map(v=>v.rng)),ex5:exceed(5),ex10:exceed(10),d4,d10,exceed});
  }
  const cols=["case","segment","azimuth_deg","cycle_rows","equivalent_cycles","p50_range_MPa","p90_range_MPa","p99_range_MPa","max_range_MPa","exceedance_ge_5MPa","exceedance_ge_10MPa","DEL_m4_MPa","DEL_m10_MPa","source_level"];
  const csv=[cols.join(","),...out.map(c=>[c.case,c.segment,c.az,c.rows,c.n,...[c.p50,c.p90,c.p99,c.max,c.ex5,c.ex10,c.d4,c.d10].map(fmt),"REAL_ETM_GROSS_NOMINAL_NOT_MATERIAL"].join(","))].join("\n")+"\n";
  const W=1110,H=660,x0=120,y0=100,pw=835,ph=450;
  const X=x=>x0+pw*x/35,Y=p=>y0+ph*(-Math.log10(p))/3;
  const esc=s=>String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
  let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Cycle-count weighted stress-range exceedance for three real ETM gross nominal control points">
<rect width="${W}" height="${H}" fill="#ffffff"/>
<text x="120" y="39" font-family="Arial, sans-serif" font-size="23" font-weight="700" fill="#17263a">Real ETM control-point rainflow range exceedance</text>
<text x="120" y="65" font-family="Arial, sans-serif" font-size="14" fill="#526579">600 s per case | 0.5/1.0 rainflow counts | gross nominal stress only</text>`;
  for(const p of [1,.1,.01,.001]){
    const y=Y(p);svg+=`\n<line x1="${x0}" y1="${y.toFixed(2)}" x2="${x0+pw}" y2="${y.toFixed(2)}" stroke="#dce4eb" stroke-width="1"/><text x="${x0-15}" y="${(y+5).toFixed(2)}" text-anchor="end" font-family="Arial, sans-serif" font-size="14" fill="#455466">${p}</text>`;
  }
  for(let x=0;x<=35;x+=5){svg+=`\n<line x1="${X(x).toFixed(2)}" y1="${y0}" x2="${X(x).toFixed(2)}" y2="${y0+ph}" stroke="#eef2f6"/><text x="${X(x).toFixed(2)}" y="${y0+ph+27}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#455466">${x}</text>`}
  svg+=`\n<line x1="${x0}" y1="${y0}" x2="${x0}" y2="${y0+ph}" stroke="#435568" stroke-width="1.6"/><line x1="${x0}" y1="${y0+ph}" x2="${x0+pw}" y2="${y0+ph}" stroke="#435568" stroke-width="1.6"/>`;
  for(const c of out){
    let pts=[];for(let t=0;t<=175;t++){const x=t*.2,p=c.exceed(x);if(p>=.001)pts.push(`${X(x).toFixed(2)},${Y(p).toFixed(2)}`)}
    svg+=`\n<polyline points="${pts.join(" ")}" fill="none" stroke="${c.color}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>`;
  }
  svg+=`\n<text x="${x0+pw/2}" y="${H-50}" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" fill="#1e3449">Nominal stress range, MPa</text>
<text transform="translate(35 ${y0+ph/2}) rotate(-90)" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" fill="#1e3449">Cycle-count weighted exceedance probability</text>`;
  for(let i=0;i<out.length;i++){const c=out[i],x=620,y=78+i*23;svg+=`\n<line x1="${x}" y1="${y-4}" x2="${x+30}" y2="${y-4}" stroke="${c.color}" stroke-width="4"/><text x="${x+40}" y="${y}" font-family="Arial, sans-serif" font-size="13" fill="#253648">${esc(c.label)} (n=${c.n})</text>`}
  svg+=`\n<text x="120" y="641" font-family="Arial, sans-serif" font-size="12" fill="#67788a">Source: T077 archived OpenFAST-derived 1,574 rainflow cycles. Diagnostic ETM only; NOT DLC 1.2, local stress or fatigue life.</text>\n</svg>\n`;
  return {summary:csv,svg,stats:out.map(c=>({case:c.case,segment:c.segment,az:c.az,n:c.n,p90:c.p90,p99:c.p99,max:c.max,ex5:c.ex5,ex10:c.ex10,d4:c.d4,d10:c.d10}))};
};
const dir=__dirname,raw=fs.readFileSync(path.join(dir,INPUT),"utf8");
const sha=crypto.createHash("sha256").update(raw,"utf8").digest("hex");
if(sha!==EXPECTED)throw Error("REAL_INPUT_SHA256_MISMATCH "+sha);
const result=build(raw);
const mode=process.argv[2]||"--verify";
if(mode==="--self-test"){
  for(const bad of [raw.replace(",0.5,REAL_GROSS",",0.7,REAL_GROSS"),raw.replace("U09p343881_ETM_S06,CSEG_16,180,1,","U09p343881_ETM_S06,CSEG_16,180,3,"),raw.split("\n").slice(0,-2).join("\n")]){
    let failed=false;try{build(bad)}catch(e){failed=true}
    if(!failed)throw Error("INVALID_INPUT_ACCEPTED");
  }
}else if(mode==="--write"){
  fs.writeFileSync(path.join(dir,FIG),result.svg);
  fs.writeFileSync(path.join(dir,TABLE),result.summary);
}else if(mode==="--verify"){
  if(fs.readFileSync(path.join(dir,FIG),"utf8")!==result.svg||fs.readFileSync(path.join(dir,TABLE),"utf8")!==result.summary)throw Error("COMMITTED_OUTPUT_MISMATCH");
}else throw Error("UNKNOWN_MODE");
for(const [name,value] of [[FIG,result.svg],[TABLE,result.summary]])console.log(name,crypto.createHash("sha256").update(value).digest("hex"));
console.log("S10_REAL_ETM_CCDF_"+mode.replace("--","").toUpperCase()+"_PASS 1574 rows, 3 controls, 3 negative tests available; NOT MATERIAL LIFE");
