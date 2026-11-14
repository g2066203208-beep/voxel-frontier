"use strict";
/* Accessible Jiayu source reader: PDF.js 5.4.530 (pinned), native PDF fallback. */
(function(){
const $=id=>document.getElementById(id);
const element=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n;};
const R={documents:[],id:null,lib:null,libPromise:null,pdf:null,loading:null,page:1,count:0,zoom:"fit",ratio:1,rotation:0,token:0,searchToken:0,renderTask:null,outline:[],thumbLimit:12,sidebar:"outline",textMode:false,bound:false,timer:0};
const CDN=[
 "https://cdn.jsdelivr.net/npm/pdfjs-dist@5.4.530/build/pdf.mjs",
 "https://unpkg.com/pdfjs-dist@5.4.530/build/pdf.mjs"
];
const WORKER=[
 "https://cdn.jsdelivr.net/npm/pdfjs-dist@5.4.530/build/pdf.worker.mjs",
 "https://unpkg.com/pdfjs-dist@5.4.530/build/pdf.worker.mjs"
];
function status(text){if($("reader-status"))$("reader-status").textContent=text;}
function readProgress(id){try{return Math.max(1,parseInt(localStorage.getItem("jy-read-page:"+id),10)||1);}catch{return 1;}}
function saveProgress(){try{if(R.id)localStorage.setItem("jy-read-page:"+R.id,String(R.page));}catch{}}
async function library(){
 if(R.lib)return R.lib;
 if(!R.libPromise)R.libPromise=(async()=>{
  for(let i=0;i<CDN.length;i++){
   try{
    const m=await import(CDN[i]);
    if(!m.getDocument)throw Error("PDF.js module");
    m.GlobalWorkerOptions.workerSrc=WORKER[i];
    R.lib=m;return m;
   }catch(error){console.warn("Reader PDF.js source unavailable",i,error);}
  }
  throw Error("PDF engine unavailable");
 })().catch(e=>{R.libPromise=null;throw e;});
 return R.libPromise;
}
function docById(id){return R.documents.find(d=>d.id===id);}
function updateDocs(){
 const box=$("reader-doc-list");if(!box)return;
 box.replaceChildren();
 for(const d of R.documents){
  const b=element("button","reader-doc"+(d.id===R.id?" selected":""),d.title);
  b.type="button";b.dataset.id=d.id;
  b.addEventListener("click",()=>select(d.id));
  box.append(b);
 }
}
function toolbar(){
 $("reader-page").value=R.page;
 $("reader-page").max=Math.max(1,R.count);
 $("reader-total").textContent="/ "+(R.count||"—");
 $("reader-prev").disabled=R.page<=1;
 $("reader-next").disabled=R.page>=R.count;
 $("reader-zoom-label").textContent=R.zoom==="fit"?"适合宽度":Math.round(R.ratio*100)+"%";
 $("reader-text-mode").classList.toggle("active",R.textMode);
}
async function closeCurrent(){
 R.token++;R.searchToken++;
 if(R.renderTask){try{R.renderTask.cancel();}catch{}R.renderTask=null;}
 if(R.loading){try{R.loading.destroy();}catch{}R.loading=null;}
 if(R.pdf){try{await R.pdf.destroy();}catch{}R.pdf=null;}
}
function showFallback(doc,why){
 $("reader-fallback").hidden=false;
 $("reader-sheet").hidden=true;
 $("reader-reflow").hidden=true;
 $("reader-fallback-frame").src=doc.url+"#view=FitH";
 $("reader-next").disabled=true;$("reader-prev").disabled=true;
 status(why+" · 使用浏览器内置 PDF 阅读器");
 $("reader-fallback-note").textContent=why;
}
async function select(id){
 const doc=docById(id);if(!doc)return;
 if(R.id===id && R.pdf){return;}
 await closeCurrent();
 const token=R.token;
 R.id=id;R.page=readProgress(id);R.count=0;R.zoom="fit";R.rotation=0;R.textMode=false;
 R.outline=[];R.thumbLimit=12;
 $("reader-fallback").hidden=true;$("reader-sheet").hidden=false;
 $("reader-reflow").hidden=true;
 $("reader-title").textContent=doc.title;
 $("reader-subtitle").textContent=doc.type+" · PDF 原件";
 $("reader-download").href=doc.url;$("reader-download").download=doc.name;
 $("reader-search-results").replaceChildren();
 $("reader-query").value="";
 $("reader-nav-content").replaceChildren();
 updateDocs();toolbar();status("正在载入文献…");
 try{
  const lib=await library();
  if(token!==R.token)return;
  const task=lib.getDocument({url:doc.url,rangeChunkSize:65536});
  R.loading=task;
  task.onProgress=e=>{if(token===R.token&&e.total)status("正在载入："+Math.min(100,Math.floor(100*e.loaded/e.total))+"%");};
  const pdf=await task.promise;
  if(token!==R.token){try{await pdf.destroy();}catch{}return;}
  R.loading=null;R.pdf=pdf;R.count=pdf.numPages;
  R.page=Math.max(1,Math.min(R.page,R.count));
  status("已加载 · "+R.count+" 页");
  toolbar();
  renderPage();
  loadOutline(token);
 }catch(error){
  if(token!==R.token)return;
  console.error("Reader fallback",error);
  showFallback(doc,"高级阅读器不可用");
 }
}
async function renderPage(){
 const pdf=R.pdf;
 if(!pdf||R.count<1)return;
 const token=R.token,pageNumber=R.page;
 if(R.renderTask){try{R.renderTask.cancel();}catch{}R.renderTask=null;}
 toolbar();saveProgress();
 if(R.textMode){renderText();return;}
 $("reader-reflow").hidden=true;
 $("reader-sheet").hidden=false;
 $("reader-fallback").hidden=true;
 $("reader-loading").hidden=false;
 status("正在呈现第 "+pageNumber+" 页");
 try{
  const page=await pdf.getPage(pageNumber);
  if(token!==R.token||pageNumber!==R.page||R.textMode)return;
  const original=page.getViewport({scale:1,rotation:R.rotation});
  const stage=$("reader-stage");
  const space=Math.max(260,stage.clientWidth-70);
  const ratio=R.zoom==="fit"?Math.max(0.5,Math.min(2.4,space/original.width)):R.ratio;
  R.ratio=ratio;
  const viewport=page.getViewport({scale:ratio,rotation:R.rotation});
  const canvas=$("reader-canvas"),ctx=canvas.getContext("2d",{alpha:false});
  if(!ctx)throw Error("Canvas unsupported");
  const dpr=Math.min(2,window.devicePixelRatio||1);
  canvas.width=Math.max(1,Math.floor(viewport.width*dpr));
  canvas.height=Math.max(1,Math.floor(viewport.height*dpr));
  canvas.style.width=Math.round(viewport.width)+"px";
  canvas.style.height=Math.round(viewport.height)+"px";
  $("reader-sheet").style.width=Math.ceil(viewport.width)+"px";
  $("reader-sheet").style.minHeight=Math.ceil(viewport.height)+"px";
  const task=page.render({canvasContext:ctx,viewport,transform:dpr!==1?[dpr,0,0,dpr,0,0]:undefined});
  R.renderTask=task;
  await task.promise;
  if(token!==R.token||pageNumber!==R.page)return;
  $("reader-loading").hidden=true;
  status("第 "+pageNumber+" / "+R.count+" 页");
  toolbar();
 }catch(error){
  if(error?.name==="RenderingCancelledException")return;
  console.error(error);
  status("此页呈现失败，请重试或切换原生预览");
 }finally{R.renderTask=null;}
}
async function renderText(){
 if(!R.pdf)return;
 const token=R.token,pageNumber=R.page;
 $("reader-sheet").hidden=true;$("reader-reflow").hidden=false;
 const box=$("reader-reflow");
 box.replaceChildren(element("div","reader-text-loading","正在提取文字…"));
 try{
  const page=await R.pdf.getPage(pageNumber);
  const content=await page.getTextContent();
  if(token!==R.token||pageNumber!==R.page||!R.textMode)return;
  box.replaceChildren();
  const p=element("div","reader-text-body");
  const buffer=[];
  for(const item of content.items){if(typeof item.str!=="string")continue;buffer.push(item.str+(item.hasEOL?"\n":" "));}
  const text=buffer.join("").replace(/[ \t]+\n/g,"\n").trim();
  if(!text){
   box.append(element("p","reader-text-empty","此页没有可提取文字；请切换到原始版式查看扫描页。"));
  }else{
   p.textContent=text;box.append(p);
  }
  status("文本阅读 · 第 "+pageNumber+" 页");
 }catch(e){box.replaceChildren(element("p","reader-text-empty","此页文字提取失败"));console.error(e);}
}
function jump(number){
 if(!R.pdf)return;
 const n=Number(number);
 if(!Number.isFinite(n))return;
 R.page=Math.max(1,Math.min(Math.round(n),R.count));
 $("reader-stage").scrollTop=0;renderPage();
}
function changeScale(amount){
 R.textMode=false;
 R.zoom="custom";
 R.ratio=Math.max(.6,Math.min(3,R.ratio+amount));
 renderPage();
}
function activateSidebar(mode){
 R.sidebar=mode;
 document.querySelectorAll("[data-reader-side]").forEach(b=>b.classList.toggle("active",b.dataset.readerSide===mode));
 if(mode==="outline")renderOutline();
 else if(mode==="thumbs")renderThumbs();
 else renderSearchArea();
}
async function loadOutline(token){
 try{
  const outline=await R.pdf.getOutline();
  if(token!==R.token)return;
  R.outline=Array.isArray(outline)?outline:[];
  if(R.sidebar==="outline")renderOutline();
 }catch(e){R.outline=[];renderOutline();}
}
async function resolveDest(dest){
 if(typeof dest==="string")dest=await R.pdf.getDestination(dest);
 if(!Array.isArray(dest)||!dest.length)return null;
 const ref=dest[0];if(typeof ref==="number")return ref+1;
 return 1+await R.pdf.getPageIndex(ref);
}
function renderOutline(){
 const box=$("reader-nav-content");box.replaceChildren();
 if(!R.outline.length){box.append(element("div","reader-nav-empty","文档未包含书签目录，可用页码跳转。"));return;}
 const list=element("div","reader-outline-list");
 let count=0;
 const visit=(items,depth)=>{
  for(const it of items){
   if(count++>=150)return;
   const b=element("button","reader-outline-item",it.title||"未命名章节");
   b.type="button";b.style.paddingLeft=(10+Math.min(depth,4)*14)+"px";
   b.addEventListener("click",async()=>{try{const p=await resolveDest(it.dest);if(p)jump(p);}catch(e){console.error(e);}});
   list.append(b);
   if(it.items?.length)visit(it.items,depth+1);
  }
 };
 visit(R.outline,0);box.append(list);
}
async function renderThumbs(){
 const box=$("reader-nav-content");box.replaceChildren();
 if(!R.pdf)return;
 const token=R.token;
 const grid=element("div","reader-thumbs");
 box.append(grid);
 for(let i=1;i<=Math.min(R.count,R.thumbLimit);i++){
  const number=i;
  const b=element("button","reader-thumb"+(number===R.page?" active":""),String(number));
  b.type="button";b.addEventListener("click",()=>jump(number));
  const canvas=element("canvas","reader-thumb-canvas");b.prepend(canvas);grid.append(b);
  // Yield to the browser; avoid hundreds of simultaneous page rasterizations.
  try{
   const page=await R.pdf.getPage(number);
   if(token!==R.token||R.sidebar!=="thumbs")return;
   const view=page.getViewport({scale:.2});
   canvas.width=Math.floor(view.width);canvas.height=Math.floor(view.height);
   canvas.style.width=Math.round(view.width)+"px";
   canvas.style.height=Math.round(view.height)+"px";
   await page.render({canvasContext:canvas.getContext("2d"),viewport:view}).promise;
  }catch(e){console.warn("Thumbnail",number,e);}
 }
 if(R.thumbLimit<R.count){
  const more=element("button","reader-load-more","显示更多页面");
  more.type="button";more.addEventListener("click",()=>{R.thumbLimit+=12;renderThumbs();});
  box.append(more);
 }
}
function renderSearchArea(){
 const box=$("reader-nav-content");
 box.replaceChildren();
 const results=$("reader-search-results");
 box.append(results);
}
async function searchDocument(){
 const q=$("reader-query").value.trim();
 R.searchToken++;const current=R.searchToken;
 activateSidebar("search");
 const box=$("reader-search-results");
 box.replaceChildren();
 if(!R.pdf||!q){box.append(element("p","reader-nav-empty","输入关键词检索PDF文字"));return;}
 box.append(element("p","reader-nav-empty","检索中…"));
 let matches=0;const list=element("div","reader-search-list");
 const needle=q.toLocaleLowerCase();
 const doc=R.pdf;
 for(let p=1;p<=R.count;p++){
  if(current!==R.searchToken||doc!==R.pdf)return;
  try{
   const page=await doc.getPage(p);
   const txt=await page.getTextContent();
   if(current!==R.searchToken)return;
   const content=txt.items.map(i=>typeof i.str==="string"?i.str:"").join(" ").replace(/\s+/g," ");
   const lower=content.toLocaleLowerCase();
   let at=lower.indexOf(needle),inPage=0;
   while(at!==-1&&matches<90&&inPage<4){
    const b=element("button","reader-search-result");
    b.type="button";
    b.append(element("strong","", "第 "+p+" 页"),element("small","",content.slice(Math.max(0,at-25),Math.min(content.length,at+needle.length+55))));
    b.addEventListener("click",()=>jump(p));
    list.append(b);matches++;inPage++;
    at=lower.indexOf(needle,at+needle.length);
   }
   if(p%8===0){box.replaceChildren(element("p","reader-nav-empty","检索 "+p+" / "+R.count+" 页…"),list);}
   if(matches>=90)break;
  }catch(e){console.warn("PDF search page",p,e);}
 }
 if(current!==R.searchToken)return;
 box.replaceChildren();
 if(!matches)box.append(element("p","reader-nav-empty","未找到可检索文字。扫描版PDF可能没有文字层。"));
 else{box.append(element("p","reader-search-summary",matches+" 个结果"),list);}
}
function bind(){
 if(R.bound)return;R.bound=true;
 $("reader-prev").addEventListener("click",()=>jump(R.page-1));
 $("reader-next").addEventListener("click",()=>jump(R.page+1));
 $("reader-page").addEventListener("change",e=>jump(e.target.value));
 $("reader-fit").addEventListener("click",()=>{R.zoom="fit";R.textMode=false;renderPage();});
 $("reader-zoom-out").addEventListener("click",()=>changeScale(-.2));
 $("reader-zoom-in").addEventListener("click",()=>changeScale(.2));
 $("reader-text-mode").addEventListener("click",()=>{
  R.textMode=!R.textMode;
  if(R.textMode)renderText();else renderPage();
  toolbar();
 });
 $("reader-rotate").addEventListener("click",()=>{R.rotation=(R.rotation+90)%360;renderPage();});
 $("reader-fullscreen").addEventListener("click",()=>{
  const shell=$("reader-shell");
  if(document.fullscreenElement)document.exitFullscreen();else shell.requestFullscreen?.();
 });
 document.querySelectorAll("[data-reader-side]").forEach(b=>b.addEventListener("click",()=>activateSidebar(b.dataset.readerSide)));
 $("reader-query").addEventListener("keydown",e=>{if(e.key==="Enter")searchDocument();});
 $("reader-search-button").addEventListener("click",searchDocument);
 $("reader-stage").addEventListener("keydown",e=>{
  if(["INPUT","TEXTAREA"].includes(e.target.tagName))return;
  if(e.key==="ArrowRight"||e.key==="PageDown"){e.preventDefault();jump(R.page+1);}
  if(e.key==="ArrowLeft"||e.key==="PageUp"){e.preventDefault();jump(R.page-1);}
 });
 window.addEventListener("resize",()=>{
  if(R.zoom!=="fit"||!R.pdf||R.textMode)return;
  clearTimeout(R.timer);R.timer=setTimeout(()=>{if(!$("original-documents").hidden)renderPage();},200);
 });
}
async function attach(docs){
 if(!Array.isArray(docs)||!docs.length)return;
 R.documents=docs;bind();updateDocs();
 if(!R.id)await select(docs[0].id);
}
function toggleDoc(id){return select(id);}
window.JYReader={attach,select:toggleDoc};
})();