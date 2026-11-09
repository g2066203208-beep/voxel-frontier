#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path");
const names=["01_绪论.md","02_研究对象_精细有限元模型与分层验证.md","03_场址风环境与整机随机风控制载荷.md","04_10MW混合塔架风致疲劳性能分析.md","05_疲劳控制参数敏感性与结构优化.md","06_结论与展望.md"];
function verify(ch,bib,registry){
 const order=[...new Set([...ch.join("\n").matchAll(/\bREF\d{3}\b/g)].map(m=>m[0]).filter(id=>id!=="REF131"))];
 const entries=[...bib.matchAll(/^(\d+)\. \[(REF\d{3})\] /gm)];
 if(order.length!==30||entries.length!==30||entries.some((m,i)=>+m[1]!==i+1||m[2]!==order[i]))throw Error("FIRST_USE_MISMATCH");
 const r=new Map(registry.trim().split(/\r?\n/).slice(1).map(x=>{let p=x.split("\t");return[p[0],p[5]];}));
 for(const id of order){const s=r.get(id);if(!s||(/^10\./.test(s)&&!bib.includes("DOI:"+s)))throw Error("DOI_OR_REGISTRY "+id);}
 if(!bib.includes("356:122441")||bib.includes("356:122381"))throw Error("R5_YANG_ID");
 if(!bib.includes("IEC 61400-1:2019")||!bib.includes("IEC 61400-1:2019+AMD1:2025"))throw Error("IEC_VERSIONS");
 return order;
}
if(require.main===module){
 const root=path.resolve(__dirname,"..");
 const ch=names.map(n=>fs.readFileSync(path.join(root,"chapters",n),"utf8"));
 const bib=fs.readFileSync(path.join(__dirname,"S12_ACTIVE_REFERENCES_20261110.md"),"utf8");
 const reg=fs.readFileSync(path.resolve(__dirname,"../../../registry/literature_master.tsv"),"utf8");
 const order=verify(ch,bib,reg);
 if(process.argv.includes("--self-test")){
  const bad=[bib.replace("356:122441","356:122381"),bib.replace("[REF001]","[REF008]"),bib.replace("DOI:10.1016/j.engstruct.2025.120295","DOI:10.1016/j.engstruct.2025.120296")];
  for(const x of bad){let fail=false;try{verify(ch,x,reg)}catch{fail=true;}if(!fail)throw Error("BAD_SOURCE_ACCEPTED");}
 }
 console.log("PASS",order.length,"first-use citations; HOLD REF131, versions, physical results");
}
module.exports={verify};
