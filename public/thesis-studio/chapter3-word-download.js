"use strict";
(function(){
  const button=document.getElementById("download-docx");
  const progress=document.getElementById("word-download-status");
  if(!button||!progress)return;
  const filename="10MW混塔论文_第三章风场与载荷学术精修版_20261121.docx";
  const expectedBytes=40665813;
  const expectedSHA="4441c083c5f0e8a1a313de04383c7e9a171d0be01560114d262f086e08c2f3b1";
  const parts=15;
  const urlOf=i=>"./downloads/10MW-thesis-academic-revision-20261121.part"+String(i+1).padStart(2,"0")+".bin";
  function message(s){progress.textContent=s;progress.setAttribute("role","status");}
  button.addEventListener("click",async()=>{
    if(button.disabled)return;
    button.disabled=true;
    const chunks=new Array(parts);
    let done=0;
    try{
      if(!globalThis.crypto?.subtle)throw new Error("当前浏览器不支持SHA-256校验，请使用新版浏览器");
      message("正在下载原格式Word：0 / 15片");
      for(let start=0;start<parts;start+=3){
        await Promise.all(Array.from({length:Math.min(3,parts-start)},(_,offset)=>start+offset).map(async i=>{
          const response=await fetch(urlOf(i),{cache:"no-store"});
          if(!response.ok)throw new Error("分片"+(i+1)+"请求失败，HTTP "+response.status);
          chunks[i]=new Uint8Array(await response.arrayBuffer());
          done++;
          message("正在下载原格式Word："+done+" / "+parts+"片");
        }));
      }
      const n=chunks.reduce((sum,chunk)=>sum+chunk.byteLength,0);
      if(n!==expectedBytes)throw new Error("Word文件大小不匹配："+n);
      const joined=new Uint8Array(n);let pos=0;
      for(const chunk of chunks){joined.set(chunk,pos);pos+=chunk.byteLength;}
      message("全部分片已下载，正在核验SHA-256…");
      const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",joined))).map(x=>x.toString(16).padStart(2,"0")).join("");
      if(hash!==expectedSHA)throw new Error("SHA-256不一致，拒绝下载损坏文件");
      const blob=new Blob([joined],{type:"application/vnd.openxmlformats-officedocument.wordprocessingml.document"});
      const href=URL.createObjectURL(blob);
      const a=document.createElement("a");
      a.href=href;a.download=filename;document.body.append(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(href),60000);
      message("原件SHA-256校验通过，已触发Word下载（40.67 MB）");
    }catch(error){message("下载失败："+String(error.message||error)+"。可使用下方备份链接。");}
    finally{button.disabled=false;}
  });
})();
