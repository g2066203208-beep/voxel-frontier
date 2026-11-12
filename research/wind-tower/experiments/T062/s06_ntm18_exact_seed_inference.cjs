#!/usr/bin/env node
"use strict";
// S06 real historical 36-row NTM base reaction: exact 924 label permutations and 6^6 paired bootstrap.
// No physical solver. Node >=18; SHA256 locked source.
const fs=require("node:fs"),crypto=require("node:crypto"),path=require("node:path");
const EXPECTED="c3de99d45c70675f6a95a767e73dcfc50d57d07b4f33438ee705690b694ae622";
const core=function core(csv){
 const lines=csv.trim().split(/\r?\n/),keys=lines.shift().split(",");
 const rows=lines.map(line=>{let v=line.split(",");if(v.length!==keys.length)throw Error("BAD_COLUMNS");return Object.fromEntries(keys.map((k,i)=>[k,v[i]]));});
 if(rows.length!==36)throw Error("BAD_ROWS");
 const unique=new Set();
 for(let r of rows){let k=r.case+"|"+r.channel;if(unique.has(k))throw Error("DUPLICATE");unique.add(k);for(let f of ["mean_kNm","band_rms_kNm","share_005_025"])if(!r[f]||!Number.isFinite(+r[f]))throw Error("NONFINITE");if(+r.share_005_025<0||+r.share_005_025>1||+r.band_rms_kNm<0)throw Error("RANGE");}
 let out=[],choose=[];function rec(s,a){if(a.length===6){choose.push(a);return;}for(let i=s;i<12;i++)rec(i+1,[...a,i]);}rec(0,[]);
 const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
 for(let ch of ["TwrBsMxt","TwrBsMyt"]){for(let wind of ["U09p343881","U11p4","U19p202140"]){let a=rows.filter(r=>r.channel===ch&&r.wind_bin===wind);if(a.length!==6||new Set(a.map(r=>r.case.match(/S\d\d$/)?.[0])).size!==6)throw Error("SEEDS");}
 for(let metric of ["share_005_025","band_rms_kNm","mean_kNm"]){
  let get=w=>rows.filter(r=>r.channel===ch&&r.wind_bin===w).sort((a,b)=>a.case.localeCompare(b.case)).map(r=>+r[metric]);
  let x=get("U11p4"),y=get("U19p202140"),v=x.concat(y),mx=mean(x),my=mean(y),d=my-mx,eps=1e-10*Math.max(1,Math.abs(d)),count=0;
  for(let ix of choose){let sum=ix.reduce((s,i)=>s+v[i],0),other=v.reduce((s,z)=>s+z,0)-sum;if(Math.abs((other-sum)/6)>=Math.abs(d)-eps)count++;}
  let bs=[];for(let q=0;q<46656;q++){let t=q,sx=0,sy=0;for(let i=0;i<6;i++){let j=t%6;t=Math.floor(t/6);sx+=x[j];sy+=y[j];}bs.push(sy/sx);}bs.sort((a,b)=>a-b);
  let diffs=x.map((z,i)=>y[i]-z),sign=0;for(let mask=0;mask<64;mask++){let s=diffs.reduce((z,u,i)=>z+(((mask>>i)&1)?-u:u),0);if(Math.abs(s)>=Math.abs(d*6)-eps)sign++;}
  out.push({channel:ch,metric,n:6,mean11:mx,mean19:my,ratio:my/mx,delta:d,lo:bs[Math.floor(.025*(bs.length-1))],hi:bs[Math.ceil(.975*(bs.length-1))],perm_count:count,perm_p:count/924,sign_count:sign,sign_p:sign/64,strict_sep:Math.min(...y)>Math.max(...x)||Math.max(...y)<Math.min(...x)});
 }}
 return out;
};
function run(){
 const input=process.argv[2]||path.join(__dirname,"S06_NTM18_BASE_REACTION_SPECTRAL_36ROW_20261112.csv");
 const bytes=fs.readFileSync(input),sha=crypto.createHash("sha256").update(bytes).digest("hex");
 if(sha!==EXPECTED)throw Error("SOURCE_SHA256_MISMATCH");
 const out=core(bytes.toString("utf8")),fields=Object.keys(out[0]);
 const csv=fields.join(",")+"\n"+out.map(r=>fields.map(f=>typeof r[f]==="number"?r[f].toFixed(12):r[f]).join(",")).join("\n")+"\n";
 fs.writeFileSync(process.argv[3]||path.join(__dirname,"S06_NTM18_SPECTRAL_SEED_INFERENCE_6ROW_20261112.csv"),csv);
 const bad=[bytes.toString("utf8").replace("U09p343881_NTM_S01","U09p343881_NTM_S02"),bytes.toString("utf8").replace("0.2056762729","NaN"),bytes.toString("utf8").replace("0.2056762729","1.2056762729"),bytes.toString("utf8").trim().split(/\r?\n/).slice(0,-1).join("\n")];
 if(bad.filter(s=>{try{core(s);return false;}catch(e){return true;}}).length!==4)throw Error("REJECTION_FAILURE");
 if(out.length!==6||out.find(r=>r.channel==="TwrBsMyt"&&r.metric==="band_rms_kNm").perm_count!==6)throw Error("ORACLE_FAILURE");
 console.log("PASS 36 source rows, 6 outcomes, 924 exact permutations, 46656 paired bootstrap, 4 negative tests; SHA256 "+sha);
}
if(require.main===module)run();
module.exports={core};
