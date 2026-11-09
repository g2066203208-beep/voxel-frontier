"use strict";
const fs=require("node:fs");
const C=["TwrBsFxt","TwrBsFyt","TwrBsFzt","TwrBsMxt","TwrBsMyt","TwrBsMzt"];
function ok(v,m){if(!v)throw Error(m);}
function parse(csv){
 const a=csv.trim().split(/\r?\n/),h=a.shift().split(","),ix=Object.fromEntries(h.map((x,i)=>[x,i]));
 for(const k of ["case","channel","outb_sha256","unit","n_samples","t0_s","t1_s","dt_s","DEL_m4_Nref600","DEL_m10_Nref600"])ok(k in ix,"HEADER "+k);
 ok(a.length===1080,"ROW_COUNT");const d=new Map(),seen=new Set();
 for(const s of a){const v=s.split(",");ok(v.length===h.length,"WIDTH");const c=v[ix.channel];if(!C.includes(c))continue;
 const id=v[ix.case],hash=v[ix.outb_sha256],key=id+"|"+c;
 ok(/^U(09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(id),"CASE");ok(/^[a-f0-9]{64}$/.test(hash),"HASH");ok(!seen.has(key),"DUP");seen.add(key);
 ok(+v[ix.n_samples]===12001&&+v[ix.t0_s]===100&&+v[ix.t1_s]===700&&+v[ix.dt_s]===.05,"TIME");
 ok(v[ix.unit]===(c[5]==="F"?"(kN)":"(kN-m)"),"UNIT");
 const m4=+v[ix.DEL_m4_Nref600],m10=+v[ix.DEL_m10_Nref600];ok(Number.isFinite(m4)&&m4>0&&Number.isFinite(m10)&&m10>0,"DEL");
 if(!d.has(id))d.set(id,{hash,ch:{}});ok(d.get(id).hash===hash,"HASH_DRIFT");d.get(id).ch[c]={m4,m10};
 }
 ok(d.size===18&&seen.size===108,"CASE_COVERAGE");
 for(const b of ["U09p343881","U11p4","U19p202140"])ok([...d.keys()].filter(id=>id.startsWith(b+"_")).length===6,"SEEDS");
 return d;
}
function calc(d,m){
 const ids=[...d.keys()].sort(),key="m"+m;
 const max=C.map(c=>Math.max(...ids.map(id=>d.get(id).ch[c][key])));
 const winners=C.map((c,j)=>ids.filter(id=>Math.abs(d.get(id).ch[c][key]-max[j])<1e-8));
 const dom=(a,b)=>C.every(c=>d.get(a).ch[c][key]>=d.get(b).ch[c][key])&&C.some(c=>d.get(a).ch[c][key]>d.get(b).ch[c][key]);
 const pareto=ids.filter(id=>!ids.some(b=>b!==id&&dom(b,id))),cover={};
 for(const q of [1,.95,.90]){
 const flags=ids.map(id=>C.reduce((s,c,j)=>s|(d.get(id).ch[c][key]>=q*max[j]-1e-8?1<<j:0),0));
 let min=99,count=0,example=[];
 for(let mask=1;mask<(1<<18);mask++){let n=0,cov=0;for(let i=0;i<18;i++)if(mask&(1<<i)){n++;if(n>min)break;cov|=flags[i];}if(n>min||cov!==63)continue;if(n<min){min=n;count=0;example=ids.filter((_,i)=>mask&(1<<i));}count++;}
 ok(min<99,"NO_COVER");cover[String(q)]={min,count,example};
 }
 return {ids,max,winners,pareto,cover};
}
function run(csv){const d=parse(csv);return {d,m4:calc(d,4),m10:calc(d,10)};}
function test(csv){
 const r=run(csv);ok(r.m4.pareto.join()==="U19p202140_NTM_S04","REAL_M4");
 ok(r.m10.pareto.length===3&&r.m10.cover["1"].min===2&&r.m10.winners[4].join()==="U11p4_NTM_S06","REAL_M10");
 const a=csv.trim().split(/\r?\n/),h=a[0].split(","),ix=Object.fromEntries(h.map((x,i)=>[x,i]));
 const change=(i,col,val)=>{const b=a.slice(),f=b[i].split(",");f[ix[col]]=val;b[i]=f.join(",");return b.join("\n")+"\n";};
 const bad=[csv.replace("DEL_m4_Nref600","NO_DEL"),a.slice(0,-1).join("\n"),change(1,"unit","(N)"),change(1,"DEL_m4_Nref600","-1"),change(1,"n_samples","12000"),change(1,"channel","TwrBsFyt"),change(1,"outb_sha256","0".repeat(64)),change(1,"case","U07_NTM_S01")];
 for(const b of bad){let rejected=false;try{run(b);}catch(e){rejected=true;}ok(rejected,"BAD_ACCEPTED");}
 const rev=run(a[0]+"\n"+a.slice(1).reverse().join("\n")+"\n");
 ok(JSON.stringify(rev.m4.pareto)===JSON.stringify(r.m4.pareto)&&JSON.stringify(rev.m10.cover)===JSON.stringify(r.m10.cover),"ORDER");
 return {positive:3,negative:bad.length,order:true};
}
module.exports={C,parse,calc,run,test};
if(require.main===module){const csv=fs.readFileSync(process.argv[2]||"research/wind-tower/experiments/T062/S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv","utf8");const r=run(csv);console.log(JSON.stringify({test:test(csv),m4:r.m4,m10:r.m10},null,2));}
