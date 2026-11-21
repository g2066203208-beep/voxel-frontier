"use strict";
(function(){
  const $=id=>document.getElementById(id);
  const state={data:null,pair:0,view:"pair",heText:false,pdf:null,pdfPromise:null,renderTask:null,renderSerial:0,observer:null};
  const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;};
  const pdfUrl="./documents/He_Zeyu_2024_hybrid_tower_thesis.pdf";
  const pageFor=(side,index)=>side==="ours"?22+index:18+index;
  function setStatus(id,message){$(id).textContent=message;$(id).hidden=!message;}
  function pageText(side,index){return state.data?.pages?.[side]?.[index]?.text||"";}
  function appendHighlighted(host,text,query){
    host.replaceChildren();
    if(!query){host.append(document.createTextNode(text));return;}
    const source=text.toLocaleLowerCase(),needle=query.toLocaleLowerCase();let at=0,found=source.indexOf(needle);
    while(found!==-1){if(found>at)host.append(document.createTextNode(text.slice(at,found)));host.append(el("mark","",text.slice(found,found+query.length)));at=found+query.length;found=source.indexOf(needle,at);}
    if(at<text.length)host.append(document.createTextNode(text.slice(at)));
  }
  function searchTerm(){return $("query").value.trim();}
  function selectOptions(){
    for(const side of ["ours","he"]){const sel=$(side+"-select");for(const obj of state.data.pages[side]){const op=el("option","",String(obj.page)+" / PDF");op.value=String(obj.page);sel.append(op);}}
  }
  async function loadPdf(){
    if(state.pdf)return state.pdf;
    if(state.pdfPromise)return state.pdfPromise;
    state.pdfPromise=(async()=>{
      const lib=await import("./vendor/pdf.mjs");
      lib.GlobalWorkerOptions.workerSrc="./vendor/pdf.worker.mjs";
      const task=lib.getDocument({url:pdfUrl,rangeChunkSize:65536});
      return await task.promise;
    })();
    try{state.pdf=await state.pdfPromise;return state.pdf;}catch(e){state.pdfPromise=null;throw e;}
  }
  async function renderPdf(canvas,pageNumber,isMain){
    const token=++state.renderSerial;
    if(isMain&&state.renderTask){try{state.renderTask.cancel();}catch(e){}state.renderTask=null;}
    try{
      const pdf=await loadPdf();
      if(isMain&&token!==state.renderSerial)return;
      const page=await pdf.getPage(pageNumber);
      if(isMain&&token!==state.renderSerial)return;
      const first=page.getViewport({scale:1});
      const maxWidth=Math.max(240,canvas.parentElement.clientWidth-(isMain?10:22));
      const scale=Math.min(2,Math.max(.55,maxWidth/first.width));
      const v=page.getViewport({scale});
      const dpr=Math.min(1.7,window.devicePixelRatio||1);
      canvas.width=Math.floor(v.width*dpr);canvas.height=Math.floor(v.height*dpr);
      canvas.style.width=Math.round(v.width)+"px";canvas.style.height=Math.round(v.height)+"px";
      const ctx=canvas.getContext("2d",{alpha:false});
      const task=page.render({canvasContext:ctx,viewport:v,transform:dpr!==1?[dpr,0,0,dpr,0,0]:undefined});
      if(isMain)state.renderTask=task;
      await task.promise;
      if(isMain&&token!==state.renderSerial)return;
      canvas.hidden=false;
      if(isMain)setStatus("he-status","");
    }catch(e){
      if(e?.name==="RenderingCancelledException")return;
      if(isMain){setStatus("he-status","PDF原页暂时无法渲染，可下方打开完整原PDF");$("he-canvas").hidden=true;}
      else{const note=canvas.parentElement.querySelector(".all-page-photo-status");if(note)note.textContent="PDF页图加载失败；可在上方完整原PDF中查看";}
      console.error("Chapter 2 original page render",e);
    }finally{if(isMain)state.renderTask=null;}
  }
  function showMainPair(){
    if(!state.data)return;
    const i=state.pair,ours=state.data.pages.ours[i],he=state.data.pages.he[i];
    $("progress").textContent=(i+1)+" / "+state.data.pages.ours.length;
    $("previous").disabled=i===0;$("next").disabled=i===state.data.pages.ours.length-1;
    $("ours-select").value=String(ours.page);
    if(he)$("he-select").value=String(he.page);
    const body=$("ours-page");body.replaceChildren();
    const head=el("span","paper-page-number","本论文 · PDF第 "+ours.page+" 页 / 第22–39页");
    const pageBody=el("div","actual-body");
    appendHighlighted(pageBody,ours.text,searchTerm());
    body.append(head,pageBody);setStatus("ours-status","");
    $("he-unavailable").hidden=true;
    if(!he){
      $("he-canvas").hidden=true;$("he-transcript").hidden=true;
      state.renderSerial++;if(state.renderTask)try{state.renderTask.cancel();}catch(e){}
      $("he-unavailable").replaceChildren(el("strong","","何泽瑜第二章已结束"),el("p","","何泽瑜第二章只有9页（PDF第18–26页）。本论文后续页面仍属于第二章，不能拿其第三章强行配对。"));
      $("he-unavailable").hidden=false;setStatus("he-status","");return;
    }
    if(state.heText){
      $("he-canvas").hidden=true;state.renderSerial++;if(state.renderTask)try{state.renderTask.cancel();}catch(e){}
      appendHighlighted($("he-transcript"),he.text,searchTerm());$("he-transcript").hidden=false;setStatus("he-status","");
    }else{
      $("he-transcript").hidden=true;$("he-canvas").hidden=true;setStatus("he-status","正在渲染何泽瑜原始PDF第 "+he.page+" 页…");
      renderPdf($("he-canvas"),he.page,true);
    }
  }
  function changePair(i){
    state.pair=Math.max(0,Math.min(state.data.pages.ours.length-1,i));
    if(state.view!=="pair")switchMode("pair");
    showMainPair();
  }
  function makeWholeCard(side,record){
    const card=el("article","all-page-card");card.id="all-"+side+"-"+record.page;
    const title=el("h4","",(side==="ours"?"本论文":"何泽瑜")+" · PDF第"+record.page+"页");card.append(title);
    if(side==="ours"){const pre=el("pre");pre.textContent=record.text;card.append(pre);}
    else{
      const desc=el("p","page-description","PDF原始图像 · 保留图表与公式版式");card.append(desc);
      const canvas=el("canvas");canvas.dataset.pdfPage=String(record.page);canvas.hidden=true;card.append(canvas);
      const note=el("div","all-page-photo-status","原页在滚动到此处时加载");card.append(note);
      const btn=el("button","","查看本页文字转录");btn.type="button";
      const pre=el("pre");pre.hidden=true;pre.textContent=record.text;btn.addEventListener("click",()=>{pre.hidden=!pre.hidden;btn.textContent=pre.hidden?"查看本页文字转录":"收起文字转录"});card.append(btn,pre);
    }
    return card;
  }
  function renderAll(){
    if($("all-ours").children.length)return;
    for(const x of state.data.pages.ours)$("all-ours").append(makeWholeCard("ours",x));
    for(const x of state.data.pages.he)$("all-he").append(makeWholeCard("he",x));
    const canvases=[...document.querySelectorAll("#all-he canvas[data-pdf-page]")];
    if("IntersectionObserver" in window){
      state.observer=new IntersectionObserver(entries=>{
        for(const entry of entries){if(!entry.isIntersecting)continue;const card=entry.target;const canvas=card.querySelector("canvas[data-pdf-page]");state.observer.unobserve(card);
          const n=Number(canvas.dataset.pdfPage);const status=canvas.parentElement.querySelector(".all-page-photo-status");if(status)status.textContent="正在加载原始PDF第"+n+"页…";
          renderPdf(canvas,n,false).then(()=>{if(!canvas.hidden&&status)status.textContent="原始PDF第"+n+"页";});
        }
      },{rootMargin:"650px 0px"});
      for(const canvas of canvases)state.observer.observe(canvas.parentElement);
    }else{for(const canvas of canvases)renderPdf(canvas,Number(canvas.dataset.pdfPage),false);}
  }
  function switchMode(mode){
    state.view=mode;
    $("mode-pair").classList.toggle("selected",mode==="pair");$("mode-all").classList.toggle("selected",mode==="all");
    $("mode-pair").setAttribute("aria-pressed",String(mode==="pair"));$("mode-all").setAttribute("aria-pressed",String(mode==="all"));
    $("comparison").hidden=mode!=="pair";$("all-pages").hidden=mode!=="all";
    document.querySelector(".page-stepper").hidden=mode!=="pair";
    if(mode==="all")renderAll();else showMainPair();
  }
  function search(){
    const query=searchTerm();const result=$("search-results");
    if(!query){result.hidden=true;result.replaceChildren();if(state.view==="pair")showMainPair();return;}
    result.hidden=false;result.replaceChildren();
    const hits=[];
    for(const side of ["ours","he"])for(const p of state.data.pages[side]){
      const lowered=p.text.toLocaleLowerCase(),needle=query.toLocaleLowerCase();
      let pos=lowered.indexOf(needle),found=0;
      while(pos>=0&&found<3){hits.push({side,page:p.page,excerpt:p.text.slice(Math.max(0,pos-26),Math.min(p.text.length,pos+query.length+38)).replace(/\s+/g," ")});found++;pos=lowered.indexOf(needle,pos+needle.length);}
    }
    result.append(el("div","search-summary",hits.length?hits.length+" 处匹配（每页最多显示3处）":"两章提取文字中未找到匹配"));
    for(const hit of hits.slice(0,65)){
      const btn=el("button","search-result");btn.type="button";
      btn.append(el("b","",(hit.side==="ours"?"本论文":"何泽瑜")+" / PDF第"+hit.page+"页"),document.createTextNode(hit.excerpt));
      btn.addEventListener("click",()=>{
        changePair(hit.side==="ours"?hit.page-22:hit.page-18);
        document.querySelector(".reader").scrollIntoView({behavior:"smooth",block:"start"});
      });
      result.append(btn);
    }
    if(state.view==="pair")showMainPair();
  }
  async function init(){
    const response=await fetch("./data/chapter2-27-pages.json",{cache:"no-store"});
    if(!response.ok)throw Error("第二章全文文件 HTTP "+response.status);
    state.data=await response.json();
    const a=state.data.pages.ours,b=state.data.pages.he;
    if(a.length!==18||b.length!==9||a[0].page!==22||a.at(-1).page!==39||b[0].page!==18||b.at(-1).page!==26)throw Error("原文页次不完整");
    selectOptions();
    $("mode-pair").addEventListener("click",()=>switchMode("pair"));
    $("mode-all").addEventListener("click",()=>switchMode("all"));
    $("previous").addEventListener("click",()=>changePair(state.pair-1));
    $("next").addEventListener("click",()=>changePair(state.pair+1));
    $("ours-select").addEventListener("change",()=>changePair(Number($("ours-select").value)-22));
    $("he-select").addEventListener("change",()=>changePair(Number($("he-select").value)-18));
    $("show-he-text").addEventListener("click",()=>{state.heText=!state.heText;$("show-he-text").setAttribute("aria-pressed",String(state.heText));$("show-he-text").textContent=state.heText?"PDF原页":"文字对照";showMainPair();});
    $("query").addEventListener("input",search);
    $("clear-search").addEventListener("click",()=>{$("query").value="";search();});
    $("copy-ours").addEventListener("click",async()=>{try{await navigator.clipboard.writeText(pageText("ours",state.pair));const b=$("copy-ours");b.textContent="已复制";setTimeout(()=>b.textContent="复制本页文本",1200);}catch(e){$("copy-ours").textContent="复制失败";}});
    document.addEventListener("keydown",event=>{if(state.view!=="pair"||["INPUT","TEXTAREA","SELECT"].includes(document.activeElement?.tagName))return;
      if(event.key==="ArrowRight"){event.preventDefault();changePair(state.pair+1);}
      if(event.key==="ArrowLeft"){event.preventDefault();changePair(state.pair-1);}
    });
    showMainPair();
    const requested=new URL(location.href).searchParams.get("page");
    if(requested&&Number(requested)>=22&&Number(requested)<=39)changePair(Number(requested)-22);
  }
  init().catch(error=>{
    setStatus("ours-status","原文读取失败："+error.message);
    setStatus("he-status","请通过“原始文献库”打开原PDF。");
    console.error("Chapter 2 compare initialization",error);
  });
})();
