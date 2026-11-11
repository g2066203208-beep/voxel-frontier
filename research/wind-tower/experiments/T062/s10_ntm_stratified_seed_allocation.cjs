#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),crypto=require("node:crypto"),path=require("node:path");
const EXPECTED_LOAD_SHA256="12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2";
const EXPECTED_ERA_SHA256="e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102";
function parseCsv(s){const [header,...lines]=s.trim().split(/\r?\n/);const keys=header.split(",");return lines.map(line=>{const vs=line.split(",");if(vs.length!==keys.length)throw Error("CSV_WIDTH");return Object.fromEntries(keys.map((k,i)=>[k,vs[i]]))})}

function sampleVariance(xs){if(xs.length<2||xs.some(x=>!Number.isFinite(x)))throw Error("BAD_SAMPLE");let m=xs.reduce((a,b)=>a+b,0)/xs.length;return xs.reduce((a,b)=>a+(b-m)**2,0)/(xs.length-1)}

function choices(N=18,min=2){const out=[];for(let a=min;a<=N-2*min;a++)for(let b=min;b<=N-a-min;b++){let c=N-a-b;if(c>=min)out.push([a,b,c])}return out}

function compute(loadRows,eraRows){
 const bins=[{key:"U09p343881_NTM",low:9},{key:"U11p4_NTM",low:11},{key:"U19p202140_NTM",low:19}],channels=["TwrBsMxt","TwrBsMyt"];
 const total=eraRows.reduce((s,r)=>s+Number(r.hours),0);if(total!==184080||eraRows.length!==31)throw Error("ERA5_TOTAL");
 if(loadRows.length!==72)throw Error("LOAD_ROWS");
 const data=bins.map(b=>{const e=eraRows.find(x=>Number(x.bin_lower_mps)===b.low);if(!e)throw Error("MISSING_BIN");const values={};for(const ch of channels){const entries=loadRows.filter(r=>r.case.startsWith(b.key+"_")&&r.channel===ch).sort((a,b)=>a.case.localeCompare(b.case));if(entries.length!==6)throw Error("SIX_SEEDS");let seen=new Set();values[ch]=entries.map(r=>{if(!/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(r.case)||seen.has(r.case))throw Error("SEED_ID");seen.add(r.case);const d=Number(r.one_line_fixed_DEL_kNm),ref=Number(r.third_party_reference_DEL_kNm);if(!Number.isFinite(d)||d<=0||Math.abs(d-ref)>1e-7)throw Error("DEL_IDENTITY");return (d/1000)**4})}return {key:b.key,low:b.low,p:Number(e.hours)/total,values}});
 const allocs=choices(),uniform=[6,6,6];
 function vari(ns,ch,removed){return data.reduce((sum,b,i)=>sum+b.p*b.p*sampleVariance(removed?b.values[ch].filter((_,j)=>j!==removed[i]):b.values[ch])/ns[i],0)}
 function evalAlloc(ns,removed){let vx0=vari(uniform,channels[0],removed),vy0=vari(uniform,channels[1],removed);let rx=vari(ns,channels[0],removed)/vx0,ry=vari(ns,channels[1],removed)/vy0;return {ns,rx,ry,worst:Math.max(rx,ry)}}
 function best(kind,removed){return allocs.map(ns=>evalAlloc(ns,removed)).sort((a,b)=>a[kind]-b[kind]||a.ns[0]-b.ns[0]||a.ns[1]-b.ns[1])[0]}
 const results=[{design:"uniform",...evalAlloc(uniform)},{design:"Mx_opt",...best("rx")},{design:"My_opt",...best("ry")},{design:"joint_minimax",...best("worst")}];
 const loo=[];for(let i=0;i<6;i++)for(let j=0;j<6;j++)for(let k=0;k<6;k++){let x=best("worst",[i,j,k]);loo.push({removed:[i+1,j+1,k+1],...x})}
 return {data,results,loo,uniformVariance:channels.map(ch=>vari(uniform,ch)),choices:allocs.length}
}

function formatResults(z){const head="design,n9,n11,n19,Mx_variance_ratio,My_variance_ratio,max_variance_ratio,Mx_SE_reduction_pct,My_SE_reduction_pct,scope";return head+"\n"+z.results.map(r=>[r.design,...r.ns,r.rx.toFixed(9),r.ry.toFixed(9),r.worst.toFixed(9),(100*(1-Math.sqrt(r.rx))).toFixed(6),(100*(1-Math.sqrt(r.ry))).toFixed(6),"HISTORICAL_3BIN_CONDITIONAL_NOT_DLC12"].join(",")).join("\n")+"\n"}

function formatLoo(z){return "removed_seed_9,removed_seed_11,removed_seed_19,optimal_n9,optimal_n11,optimal_n19,max_variance_ratio\n"+z.loo.map(r=>[...r.removed,...r.ns,r.worst.toFixed(9)].join(",")).join("\n")+"\n"}

function formatSvg(z){const rs=z.results,colors=["#5c6b79","#2f718e","#9b704b","#357e67"],W=920,H=380;let s=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="#fff"/><text x="34" y="37" font-family="sans-serif" font-size="21" font-weight="bold">Observed-bin fourth-moment allocation (N=18)</text><text x="34" y="59" font-family="sans-serif" font-size="13" fill="#555">Relative plug-in variance vs uniform 6/6/6; three historical NTM bins only</text>`;rs.forEach((r,i)=>{let y=94+i*66;s+=`<text x="34" y="${y+15}" font-family="sans-serif" font-size="14">${r.design} (${r.ns.join("/")})</text>`;for(let k=0;k<2;k++){let v=k?r.ry:r.rx;let yy=y+k*22;s+=`<rect x="285" y="${yy}" width="${(v*490).toFixed(2)}" height="16" fill="${colors[i]}" opacity="${k?0.62:0.95}"/><text x="${(292+v*490).toFixed(2)}" y="${yy+13}" font-family="sans-serif" font-size="12">${k?"My":"Mx"} ${v.toFixed(3)}</text>`}});s+=`<text x="34" y="360" font-family="sans-serif" font-size="12" fill="#555">No missing-bin uncertainty, material fatigue, or IEC DLC1.2 certification is represented.</text></svg>\n`;return s}

function selfTest(){if(choices().length!==91)throw Error("ALLOC_COUNT");if(Math.abs(sampleVariance([1,2,3])-1)>1e-12)throw Error("VAR");let bad=0;for(const f of [()=>sampleVariance([1]),()=>sampleVariance([1,NaN]),()=>parseCsv("a,b\n1"),()=>{let x=choices(5,2);if(x.length)throw Error("BAD_ALLOC")}]){try{f()}catch(e){bad++}}if(bad!==3)throw Error("NEGATIVE_TESTS");return "SELFTEST_PASS 91 allocations, sample variance, 3 negative rejections"}

function readLocked(p,sha){const bytes=fs.readFileSync(p);if(crypto.createHash("sha256").update(bytes).digest("hex")!==sha)throw Error("SOURCE_SHA256");return parseCsv(bytes.toString("utf8"))}
function main(){
 if(process.argv.includes("--self-test")){console.log(selfTest());return}
 if(process.argv.length!==5)throw Error("Usage: node script.cjs <72row-load.csv> <31row-era5.csv> <output-dir>");
 const z=compute(readLocked(process.argv[2],EXPECTED_LOAD_SHA256),readLocked(process.argv[3],EXPECTED_ERA_SHA256));
 const dir=process.argv[4];fs.mkdirSync(dir,{recursive:true});
 fs.writeFileSync(path.join(dir,"S10_NTM18_STRATIFIED_ALLOC_4ROW_20261112.csv"),formatResults(z));
 fs.writeFileSync(path.join(dir,"S10_NTM18_STRATIFIED_ALLOC_LOO_216ROW_20261112.csv"),formatLoo(z));
 fs.writeFileSync(path.join(dir,"FIG3_S10_NTM18_STRATIFIED_ALLOC_20261112.svg"),formatSvg(z));
 console.log("SOURCE_NUMERIC_PASS 36 NTM channel rows, 3 bins, 216 leave-one-out, 91 integer allocations; NOT DLC1.2");
}
try{main()}catch(e){console.error("REFUSE:",e.message);process.exitCode=2}
