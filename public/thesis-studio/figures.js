"use strict";
/* Jiayu original archive: full in-site PDFs and 541 original images. */
(function(){
const S={data:null,promise:null,category:"",query:"",active:null,doc:"jiayu-gov",bound:false,painted:false};
const $=s=>document.querySelector(s);
function E(tag,cls,text){const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=String(text);return el;}
const encoded=p=>p.split("/").map(encodeURIComponent).join("/");
function sourceImg(fig){return "./figures/"+encoded(fig.p);}
function sourcePDF(doc){return doc.url;}
async function ready(){
 if(S.data)return S.data;
 if(!S.promise)S.promise=fetch("./data/figure-index.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("图片资料未加载");return r.json();}).then(d=>{
 if(!Array.isArray(d.images)||d.images.length!==541||d.hosted!==d.images.length)throw Error("原图目录不完整");
 if(!Array.isArray(d.documents)||d.documents.length!==3||d.hePages.length!==11)throw Error("文献原件不完整");
 S.data=d;return d;
 }).catch(e=>{S.promise=null;throw e;});
 return S.promise;
}
function filename(fig){return fig.n;}
async function download(url,name){
 try {
   const r=await fetch(url);if(!r.ok)throw Error("HTTP "+r.status);
   const b=await r.blob(),src=URL.createObjectURL(b),a=E("a");
   a.href=src;a.download=name;a.hidden=true;document.body.append(a);a.click();a.remove();
   setTimeout(()=>URL.revokeObjectURL(src),7000);
 }catch(e){console.error(e);alert("原件下载失败，请稍后重试");}
}
function card(fig,small=false){
 const el=E("article","figure-card"+(small?" compact":""));
 const button=E("button","figure-preview");button.type="button";
 button.setAttribute("aria-label","放大原图 "+fig.n);
 const photo=E("div","figure-photo"),img=E("img");
 img.src=sourceImg(fig);img.alt=fig.n;img.loading="lazy";img.decoding="async";
 img.onerror=()=>{photo.classList.add("broken");img.remove();photo.append(E("span","figure-error","原图载入失败"));};
 photo.append(img);button.append(photo);button.addEventListener("click",()=>zoom(fig));
 const body=E("div","figure-card-body");
 body.append(E("span","figure-card-category",fig.c));
 const name=E("strong","figure-file",filename(fig));name.title=fig.n;body.append(name);
 const actions=E("div","figure-actions");
 const view=E("button","","放大");view.type="button";view.addEventListener("click",()=>zoom(fig));
 const dl=E("button","","下载原图");dl.type="button";dl.addEventListener("click",()=>download(sourceImg(fig),fig.n));
 actions.append(view,dl);body.append(actions);el.append(button,body);return el;
}
function zoom(fig){
 const dialog=$("#figure-lightbox");if(!dialog)return;S.active=fig;
 $("#figure-zoom-name").textContent=fig.n;$("#figure-zoom-topic").textContent=fig.c+" · 原始文件";
 $("#figure-zoom-path").textContent="research/wind-tower/"+fig.p;
 const img=$("#figure-zoom-image");img.src=sourceImg(fig);img.alt=fig.n;dialog.showModal();
}
function renderGrid(){
 if(!S.data)return;
 const q=S.query.toLowerCase(),items=S.data.images.filter(f=>
 (!S.category||f.c===S.category)&&(!q||(f.n+" "+f.p+" "+f.c).toLowerCase().includes(q)));
 $("#figure-count").textContent=items.length+" / "+S.data.images.length+" 张原图";
 const grid=$("#figure-grid");grid.replaceChildren();
 const fragment=document.createDocumentFragment();
 for(const f of items)fragment.append(card(f));
 grid.append(fragment);
 if(!items.length)grid.append(E("div","figure-empty","没有匹配的原图"));
}
function renderHe(){
 const box=$("#he-original-grid");if(!box||!S.data)return;
 const index=new Map(S.data.images.map(f=>[f.p,f]));
 box.replaceChildren(...S.data.hePages.map(p=>index.get(p)).filter(Boolean).map(f=>card(f,true)));
 $("#he-page-count").textContent=S.data.hePages.length+" 张论文原始页图";
}
function renderDocs(){
 const tabs=$("#original-document-tabs");
 if(!tabs||!S.data)return;
 tabs.replaceChildren();
 for(const item of S.data.documents){
  const button=E("button","original-doc-tab"+(item.id===S.doc?" active":""),item.title);
  button.type="button";button.dataset.document=item.id;
  button.addEventListener("click",()=>selectDoc(item.id));
  tabs.append(button);
 }
 selectDoc(S.doc);
}
function selectDoc(id){
 if(!S.data)return;
 const doc=S.data.documents.find(x=>x.id===id);if(!doc)return;
 S.doc=id;
 const frame=$("#original-pdf-frame");
 const source=sourcePDF(doc);
 if(frame && frame.dataset.document!==doc.id){
    frame.src=source+"#toolbar=1&navpanes=0&view=FitH";
    frame.dataset.document=doc.id;
    frame.title=doc.title+" PDF原文";
 }
 $("#original-doc-name").textContent=doc.title;
 $("#original-doc-meta").textContent=doc.type+" · "+(doc.size/1048576).toFixed(1)+" MB · 原始PDF";
 document.querySelectorAll(".original-doc-tab").forEach(b=>b.classList.toggle("active",b.dataset.document===id));
 const btn=$("#original-doc-download");
 btn.onclick=()=>download(source,doc.name);
}
function bind(){
 if(S.bound)return;S.bound=true;
 const select=$("#figure-category");
 for(const c of Object.keys(S.data.categories)){
  const o=E("option","",c);o.value=c;select.append(o);
 }
 select.addEventListener("change",e=>{S.category=e.target.value;renderGrid();});
 $("#figure-search").addEventListener("input",e=>{S.query=e.target.value;renderGrid();});
 $("#figure-close").addEventListener("click",()=>$("#figure-lightbox").close());
 $("#figure-download").addEventListener("click",()=>{if(S.active)download(sourceImg(S.active),S.active.n);});
 $("#figure-lightbox").addEventListener("click",e=>{if(e.target===$("#figure-lightbox"))$("#figure-lightbox").close();});
}
async function show(){
 try {
   await ready();
   bind();
   renderDocs();
   if(!S.painted){renderHe();S.painted=true;}
   renderGrid();
 }catch(e){console.error(e);$("#figure-grid").replaceChildren(E("p","figure-empty","原始资料载入失败"));}
}
async function overview(){
 const preview=$("#featured-figures");if(!preview)return;
 try{
  const d=await ready();
  const wanted=[
  "figure2-1-word-zh.png","mesh-convergence-zh.png",
  "FIG3_S06_ERA5_DIRECTION_BAYES_20261110.svg",
  "FIG_S05_03_ROTD_PUBLICATION.svg",
  "FIG4_S10_ETM4_TENSION_DEL4_AZIMUTH_TRADEOFF_20261109.svg",
  "FIG_S08_06_158M_REAL_ESM_ELASTIC_BEAM_PROXY_NOT_ABAQUS.svg"
  ];
  const found=wanted.map(n=>d.images.find(f=>f.n===n)).filter(Boolean);
  preview.replaceChildren(...found.map(f=>card(f,true)));
 }catch(e){console.error(e);}
}
const themes={windResource:"风环境与风荷载",windLoad:"风环境与风荷载",seismic:"地震与动力响应",coupling:"地震与动力响应",structure:"混塔结构与有限元",foundation:"混塔结构与有限元",fatigue:"疲劳与优化",optimization:"疲劳与优化",manuscript:"论文与科研图表",reports:"论文与科研图表"};
const pdfModules={field:"jiayu-gov",structure:"he-thesis",literature:"he-thesis"};
async function moduleFigures(mod,target){
 try{
  const d=await ready();
  const theme=themes[mod];
  if(theme){
   const found=d.images.filter(f=>f.c===theme).slice(0,3);
   if(found.length){
    const section=E("section","detail-panel detail-figures");
    section.append(E("span","panel-kicker","SOURCE FIGURES"),E("h2","","科研原图"));
    const grid=E("div","figure-detail-grid");
    found.forEach(f=>grid.append(card(f,true)));
    section.append(grid);target.append(section);
   }
  }
  if(pdfModules[mod]){
   const doc=d.documents.find(x=>x.id===pdfModules[mod]);
   const section=E("section","detail-panel module-original-pdf");
   section.append(E("span","panel-kicker","ORIGINAL DOCUMENT"),E("h2","",doc.title));
   const iframe=E("iframe","module-pdf-frame");iframe.loading="lazy";iframe.src=doc.url+"#page=1&view=FitH";
   iframe.title=doc.title;section.append(iframe);target.append(section);
  }
 }catch(e){console.error(e);}
}
function focusDoc(id){S.doc=id;location.hash="#figures";show().then(()=>$("#original-documents").scrollIntoView({block:"start"}));}
window.JYFigures={show,overview,moduleFigures,focusDoc};
})();
