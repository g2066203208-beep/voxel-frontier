// Reproducible historical 4 ETM x 31 segment nominal gross-elastic screening; NOT DLC1.2/material fatigue.
function analyse(raw){
 const cases=["U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06"];
 const cols=["case","segment","gage_z_m","max_DEL_m4_MPa","max_DEL_m10_MPa"];
 const lines=raw.trim().split(/\r?\n/),h=lines.shift().split(",");
 for(const c of cols)if(!h.includes(c))throw Error("MISSING_COLUMN:"+c);
 if(lines.length!==124)throw Error("ROW_COUNT");
 const groups=Array.from({length:31},()=>new Map());
 for(const line of lines){
  const f=line.split(",");if(f.length!==h.length)throw Error("FIELD_COUNT");
  const row=Object.fromEntries(h.map((x,i)=>[x,f[i]]));
  const m=/^CSEG_(\d{2})$/.exec(row.segment);
  if(!m||+m[1]<1||+m[1]>31)throw Error("SEGMENT");
  if(!cases.includes(row.case))throw Error("CASE");
  const g=groups[+m[1]-1];if(g.has(row.case))throw Error("DUPLICATE");
  const z=+row.gage_z_m,d4=+row.max_DEL_m4_MPa,d10=+row.max_DEL_m10_MPa;
  if(![z,d4,d10].every(Number.isFinite)||z<=0||d4<=0||d10<=0)throw Error("BAD_NUMBER");
  g.set(row.case,{case:row.case,z,d4,d10});
 }
 const rows=[],cross=[];
 for(let i=0;i<31;i++){
  const g=groups[i];if(g.size!==4)throw Error("MISSING_CASE");
  const a=cases.map(c=>g.get(c));
  if(Math.max(...a.map(x=>x.z))-Math.min(...a.map(x=>x.z))>0.001)throw Error("HEIGHT_MISMATCH");
  const z=a.reduce((s,x)=>s+x.z,0)/4;if(i&&z<=rows[i-1].z)throw Error("HEIGHT_ORDER");
  const r4=[...a].sort((x,y)=>y.d4-x.d4),r10=[...a].sort((x,y)=>y.d10-x.d10);
  if(r4[0].d4===r4[1].d4||r10[0].d10===r10[1].d10)throw Error("TIE");
  const delta=(x,y)=>100*(x-y)/(x+y);
  rows.push({segment:"CSEG_"+String(i+1).padStart(2,"0"),z,win4:r4[0].case,runner4:r4[1].case,del4:r4[0].d4,runnerDel4:r4[1].d4,deltaStar4:delta(r4[0].d4,r4[1].d4),win10:r10[0].case,runner10:r10[1].case,del10:r10[0].d10,runnerDel10:r10[1].d10,deltaStar10:delta(r10[0].d10,r10[1].d10),ambiguous4:delta(r4[0].d4,r4[1].d4)<=0.5,ambiguous10:delta(r10[0].d10,r10[1].d10)<=0.5,values:a});
  if(i&&rows[i].win4!==rows[i-1].win4)cross.push({lower:rows[i-1].segment,upper:rows[i].segment,zLower:rows[i-1].z,zUpper:z});
 }
 return {rows,cross,cases};
}
function makeCsv(d){
 const head="segment,gage_z_m,m4_winner,m4_runner_up,m4_winner_DEL_MPa,m4_runner_DEL_MPa,m4_delta_star_percent,m4_ambiguous_if_pm0p5pct,m10_winner,m10_runner_up,m10_winner_DEL_MPa,m10_runner_DEL_MPa,m10_delta_star_percent,m10_ambiguous_if_pm0p5pct";
 return head+"\n"+d.rows.map(x=>[x.segment,x.z.toFixed(9),x.win4,x.runner4,x.del4.toFixed(9),x.runnerDel4.toFixed(9),x.deltaStar4.toFixed(6),x.ambiguous4?1:0,x.win10,x.runner10,x.del10.toFixed(9),x.runnerDel10.toFixed(9),x.deltaStar10.toFixed(6),x.ambiguous10?1:0].join(",")).join("\n")+"\n";
}
function makeSvg(d){
 const W=1260,H=820,colors=["#146B91","#C45B32","#777E89","#8D6AAB"],panels=[{x:88,max:8.5,key:"d4",title:"(a) m = 4 nominal-stress DEL"},{x:685,max:19,key:"d10",title:"(b) m = 10 nominal-stress DEL"}],top=125,bottom=687,plotH=bottom-top;
 let s=[`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`,`<rect width="${W}" height="${H}" fill="#ffffff"/>`,`<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202934}.title{font-size:22px;font-weight:700}.sub{font-size:16px;font-weight:700}.axis{font-size:13px}.note{font-size:12px;fill:#475467}</style>`,`<text x="50" y="42" class="title">ETM 31-section control-case switching: four historical cases</text>`,`<text x="50" y="69" class="note">Synchronous gross-annulus elastic stress; 16 azimuths; 600 s; diagnostic exponents only (not material fatigue)</text>`];
 for(const p of panels){
  const x0=p.x,x1=x0+470,xx=v=>x0+v/p.max*(x1-x0),yy=z=>bottom-z/112*plotH;
  s.push(`<text x="${x0}" y="102" class="sub">${p.title}</text>`);
  for(let z=0;z<=110;z+=10){let y=yy(z);s.push(`<line x1="${x0}" y1="${y.toFixed(2)}" x2="${x1}" y2="${y.toFixed(2)}" stroke="#E4E8EE"/>`,`<text x="${x0-12}" y="${(y+4).toFixed(2)}" text-anchor="end" class="axis">${z}</text>`)}
  for(let v=0;v<=p.max+0.00001;v+=p.key==="d4"?2:5){let x=xx(v);s.push(`<line x1="${x.toFixed(2)}" y1="${top}" x2="${x.toFixed(2)}" y2="${bottom}" stroke="#EEF1F4"/>`,`<text x="${x.toFixed(2)}" y="${bottom+24}" text-anchor="middle" class="axis">${v}</text>`)}
  s.push(`<rect x="${x0}" y="${top}" width="${x1-x0}" height="${plotH}" fill="none" stroke="#7C8895"/>`,`<text x="${(x0+x1)/2}" y="${bottom+48}" text-anchor="middle" class="axis">Equivalent nominal stress (MPa)</text>`,`<text x="${x0-55}" y="${(top+bottom)/2}" transform="rotate(-90 ${x0-55} ${(top+bottom)/2})" text-anchor="middle" class="axis">Height above base (m)</text>`);
  if(p.key==="d4")for(const c of d.cross){let y=(yy(c.zLower)+yy(c.zUpper))/2;s.push(`<line x1="${x0}" y1="${y.toFixed(2)}" x2="${x1}" y2="${y.toFixed(2)}" stroke="#B64747" stroke-width="1.3" stroke-dasharray="5 5"/>`)}
  for(let j=0;j<d.cases.length;j++){let c=d.cases[j],pts=d.rows.map(r=>{let o=r.values.find(x=>x.case===c);return `${xx(o[p.key]).toFixed(2)},${yy(r.z).toFixed(2)}`}).join(" ");s.push(`<polyline points="${pts}" fill="none" stroke="${colors[j]}" stroke-width="${j<2?3:1.8}" stroke-linejoin="round"/>`)}
 }
 let legend=["9.344 m/s ETM S06","11.4 m/s ETM S04","19.202 m/s ETM S04","19.202 m/s ETM S06"];
 for(let i=0;i<4;i++){let x=90+(i%2)*285,y=762+Math.floor(i/2)*23;s.push(`<line x1="${x}" y1="${y-5}" x2="${x+27}" y2="${y-5}" stroke="${colors[i]}" stroke-width="3"/>`,`<text x="${x+35}" y="${y}" class="axis">${legend[i]}</text>`)}
 s.push(`<text x="692" y="762" class="note">m4 transitions: CSEG05/06 and CSEG23/24.</text>`,`<text x="692" y="782" class="note">Six m4 segments fail hypothetical symmetric +/-0.5% rank stability.</text>`,`<text x="692" y="802" class="note">ETM screening; not DLC1.2, local stress, PT or Miner damage.</text>`,`</svg>`);
 return s.join("\n")+"\n";
}

const fs=require("node:fs"),crypto=require("node:crypto"),path=require("node:path");
const SOURCE_SHA256="36c0a8a97db36885159fff79cc61daced9c939ab688f98ce1c6b860a89ac91d3";
const IN=path.join(__dirname,"S10_4CASE_31SEG_SYNC_GROSS_CONTROL_20261030.csv");
const OUT_CSV=path.join(__dirname,"S10_4ETM_31SEG_M4_M10_HEIGHT_CONTROL_SWITCH_20261107.csv");
const OUT_SVG=path.resolve(__dirname,"../../manuscript/final-thesis/figures/FIG4_S10_ETM31_HEIGHT_CONTROL_SWITCH_20261107.svg");
function selfTest(raw){
 const d=analyse(raw),ok=(x,m)=>{if(!x)throw Error("SELF_TEST:"+m)};
 ok(d.rows.length===31,"31");ok(d.cross.length===2&&d.cross[0].lower==="CSEG_05"&&d.cross[1].lower==="CSEG_23","crossings");
 ok(d.rows.filter(x=>x.win4===d.cases[0]).length===18&&d.rows.filter(x=>x.win4===d.cases[1]).length===13,"m4 cases");
 ok(d.rows.every(x=>x.win10===d.cases[0]),"m10");ok(d.rows.filter(x=>x.ambiguous4).length===6&&d.rows.every(x=>!x.ambiguous10),"stability");
 ok(Math.abs(Math.max(...d.rows.map(x=>x.del4))-7.16908904914)<1e-9,"peak4");
 ok(Math.abs(Math.max(...d.rows.map(x=>x.del10))-17.1260721731)<1e-9,"peak10");
 const bad=[s=>s.trim().split("\n").slice(0,-1).join("\n"),s=>s.replace("6.83617569974","-3"),s=>s.replace("6.83617569974","nan"),s=>s.replace("U09p343881_ETM_S06","INVALID"),s=>{let a=s.split("\n");a[2]=a[1];return a.join("\n")},s=>s.replace("1.76339291359","9999")];
 for(const mutate of bad){let rejected=false;try{analyse(mutate(raw))}catch(e){rejected=true}ok(rejected,"bad input rejected")}
 return d;
}
if(require.main===module){
 const input=process.argv[2]&&process.argv[2]!=="--self-test"?process.argv[2]:IN,raw=fs.readFileSync(input,"utf8");
 const hash=crypto.createHash("sha256").update(raw).digest("hex");
 if(hash!==SOURCE_SHA256)throw Error("SOURCE_SHA256_MISMATCH:"+hash);
 const d=selfTest(raw);
 if(process.argv.includes("--self-test"))console.log("PASS: 7 positive and 6 negative assertions; nonphysical screening");
 else{
  const csvPath=process.argv[3]||OUT_CSV,svgPath=process.argv[4]||OUT_SVG;
  fs.writeFileSync(csvPath,makeCsv(d),"utf8");fs.writeFileSync(svgPath,makeSvg(d),"utf8");
  console.log(JSON.stringify({source_sha256:hash,rows:d.rows.length,cross:d.cross,physical_pass:false},null,2));
 }
}
