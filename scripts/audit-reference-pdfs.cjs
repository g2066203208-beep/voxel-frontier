"use strict";
/* Availability audit only. Never treats PDF registry metadata as a successful document read. */
const fs=require("node:fs"),path=require("node:path");
const index=JSON.parse(fs.readFileSync("public/thesis-studio/data/reference-index.json","utf8"));
const result={checkedAt:new Date().toISOString(),count:index.entries.length,rows:[]};
const queue=index.entries.slice();let running=0;
async function probe(ref){
 const row={id:ref.id,title:ref.title,mode:ref.mode,indexStatus:ref.status,available:false,reason:""};
 if(ref.status!=="indexed"||!ref.url){row.reason="rights/source unavailable";return row}
 if(ref.url.startsWith("./")){
  const p=path.join("public/thesis-studio",decodeURI(ref.url.slice(2)));
  try{const fd=fs.openSync(p,"r"),b=Buffer.alloc(8);fs.readSync(fd,b,0,8,0);fs.closeSync(fd);row.available=b.toString("ascii").startsWith("%PDF-");row.reason=row.available?"local PDF header verified":"local bytes are not PDF"}catch(e){row.reason=e.message}
  return row;
 }
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),18000);
 try{
  const response=await fetch(ref.url,{headers:{"Range":"bytes=0-15"},redirect:"follow",signal:controller.signal});
  row.httpStatus=response.status;row.finalHost=new URL(response.url).hostname;
  row.contentType=response.headers.get("content-type");row.cors=response.headers.get("access-control-allow-origin");
  if(!response.ok){row.reason="HTTP "+response.status;return row}
  const reader=response.body?.getReader();
  const part=await reader?.read();
  const bytes=Buffer.from(part?.value??[]);
  row.signature=bytes.subarray(0,40).toString("ascii").replace(/[^\x20-\x7e]/g,".");
  row.available=bytes.subarray(0,8).toString("ascii").startsWith("%PDF-");
  row.reason=row.available?"remote PDF header verified":"non-PDF content or Git LFS pointer";
  await reader?.cancel().catch(()=>{});
 }catch(e){row.reason=String(e.message||e)}
 finally{clearTimeout(timer);controller.abort()}
 return row;
}
async function next(){
 while(queue.length){
  const ref=queue.shift(),row=await probe(ref);
  result.rows.push(row);
  console.log(ref.id,row.available?"PDF":"FAIL",row.reason);
 }
}
Promise.all(Array.from({length:7},next)).then(()=>{
 result.rows.sort((a,b)=>a.id.localeCompare(b.id));
 result.available=result.rows.filter(x=>x.available).length;
 result.unavailable=result.rows.filter(x=>!x.available).length;
 fs.mkdirSync("artifacts",{recursive:true});
 fs.writeFileSync("artifacts/studio-reference-availability.json",JSON.stringify(result,null,2));
 console.log(JSON.stringify({count:result.count,available:result.available,unavailable:result.unavailable,failures:result.rows.filter(x=>!x.available).map(x=>({id:x.id,reason:x.reason}))}));
 if(result.available<index.entries.filter(x=>x.status==="indexed").length)process.exitCode=1;
}).catch(e=>{console.error(e);process.exitCode=1});
