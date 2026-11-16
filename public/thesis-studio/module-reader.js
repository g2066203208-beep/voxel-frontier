"use strict";
/* Source-first academic reading: renders existing, unaltered repository content in place. */
(function(){
const rootOwner="g2066203208-beep",repo="voxel-frontier";
const subjectGroups={
 windResource:["风环境与风荷载"],windLoad:["风环境与风荷载"],
 seismic:["地震与动力响应"],structure:["混塔结构与有限元"],
 foundation:["混塔结构与有限元"],coupling:["地震与动力响应","混塔结构与有限元"],
 fatigue:["疲劳与优化"],optimization:["疲劳与优化"],
 manuscript:["论文与科研图表"],reports:["论文与科研图表"]
};
const E=(tag,cls,text)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=String(text);return x};
const srcFigure=f=>"./figures/"+f.p.split("/").map(encodeURIComponent).join("/");
function sourceSpec(url){
 let u;try{u=new URL(url)}catch{return null}
 if(u.hostname!=="github.com"||u.protocol!=="https:")return null;
 const bits=u.pathname.split("/").filter(Boolean);
 if(bits[0]!==rootOwner||bits[1]!==repo||bits[2]!=="blob")return null;
 let branch,parts;
 if(bits[3]==="main"){branch="main";parts=bits.slice(4)}
 else if(bits[3]==="research"&&bits[4]==="t080-seismic-integration-gates-20261022"){
  branch="research/t080-seismic-integration-gates-20261022";parts=bits.slice(5)
 }else return null;
 if(!parts.length||parts.some(x=>x===".."||x==="."))return null;
 const path=parts.join("/"),extension=path.split(".").pop().toLowerCase();
 if(!["md","txt","csv","tsv","json","svg"].includes(extension))return null;
 return {path,extension,url:"https://raw.githubusercontent.com/"+rootOwner+"/"+repo+"/"+branch+"/"+parts.map(encodeURIComponent).join("/")};
}
function heading(title,detail){
 const h=E("header","record-heading");h.append(E("h2","",title));
 if(detail)h.append(E("span","record-detail",detail));
 return h;
}
function sourceTable(text,container,separator){
 const rows=text.replace(/^\uFEFF/,"").split(/\r?\n/).filter(Boolean);
 if(!rows.length){container.append(E("p","record-failed","原表为空"));return}
 function parse(line){if(separator==="\t")return line.split("\t");
  const cells=[];let field="",quoted=false;
  for(let i=0;i<line.length;i++){const c=line[i];
   if(c==='"'){if(quoted&&line[i+1]==='"'){field+='"';i++}else quoted=!quoted}
   else if(c===","&&!quoted){cells.push(field);field=""}else field+=c;
  }cells.push(field);return cells;
 }
 const cols=parse(rows.shift()),body=rows.map(parse),box=E("div","record-data-table");
 const status=E("span","record-detail",body.length.toLocaleString()+" 行 · "+cols.length+" 列");
 const search=E("input","record-data-search");search.type="search";search.placeholder="在全部行检索";
 const toolbar=E("div","record-data-toolbar");toolbar.append(search,status);
 const viewport=E("div","record-data-scroll"),table=E("table","record-table"),thead=E("thead"),tr=E("tr");
 cols.forEach(v=>tr.append(E("th","",v)));thead.append(tr);table.append(thead);
 const tbody=E("tbody");table.append(tbody);viewport.append(table);
 const more=E("div","record-data-sentinel");
 box.append(toolbar,viewport,more);container.append(box);
 let matched=body,rendered=0,token=0;
 function appendBatch(){
  const block=document.createDocumentFragment();
  matched.slice(rendered,rendered+120).forEach(line=>{
   const tr=E("tr");cols.forEach((_,i)=>tr.append(E("td","",line[i]??"")));block.append(tr);
  });
  tbody.append(block);rendered=Math.min(rendered+120,matched.length);
  more.textContent=rendered<matched.length?(rendered+" / "+matched.length+" 行已显示 · 向下滚动继续"):(matched.length+" 行全部可见");
  if(rendered===matched.length)observer.unobserve(more);
 }
 const observer=new IntersectionObserver(entries=>{if(entries.some(x=>x.isIntersecting)&&rendered<matched.length)appendBatch()},{rootMargin:"900px"});
 function reset(){
  token++;const q=search.value.trim().toLowerCase();matched=q?body.filter(c=>c.some(v=>String(v).toLowerCase().includes(q))):body;
  tbody.replaceChildren();rendered=0;status.textContent=matched.length.toLocaleString()+" / "+body.length.toLocaleString()+" 行";
  appendBatch();observer.observe(more);
 }
 search.addEventListener("input",reset);reset();
}
async function rawDocument(record,host){
 const doc=E("article","record-document"),spec=sourceSpec(record.url);
 if(!spec)return;
 host.append(doc);
 const caption=heading(record.label,"研究仓库原文 · "+spec.path);doc.append(caption);
 const content=E("div","record-document-body");
 content.append(E("p","record-loading","读取原始文件…"));doc.append(content);
 try{
  const response=await fetch(spec.url,{cache:"force-cache"});
  if(!response.ok)throw Error("HTTP "+response.status);
  const size=Number(response.headers.get("content-length")||0);
  if(size>15*1024*1024)throw Error("超出单文档浏览器渲染限制");
  const text=await response.text();
  if(text.length>15*1024*1024)throw Error("原文长度超出浏览器渲染限制");
  content.replaceChildren();
  if(spec.extension==="md"){
   const article=E("div","thesis-full-article");
   const render=window.JYThesisInline?.renderMarkdown;
   if(typeof render!=="function")throw Error("论文排版组件不可用");
   render(text,article);content.append(article);
  }else if(spec.extension==="csv"||spec.extension==="tsv"){
   sourceTable(text,content,spec.extension==="tsv"?"\t":",");
  }else if(spec.extension==="svg"){
   const figure=E("figure","record-original-figure"),img=E("img");img.src=spec.url;img.alt=record.label;
   figure.append(img,E("figcaption","",record.label));content.append(figure);
  }else if(spec.extension==="json"){
   let v;try{v=JSON.stringify(JSON.parse(text),null,2)}catch{v=text}
   content.append(E("pre","record-raw",v));
  }else content.append(E("pre","record-raw",text));
  doc.dataset.source="loaded";doc.dataset.sourceLength=String(text.length);
 }catch(e){content.replaceChildren(E("p","record-failed","原件读取失败："+e.message));doc.dataset.source="failed";}
}
let pdfLib=null;
async function pdfEngine(){
 if(pdfLib)return pdfLib;
 const lib=await import("./vendor/pdf.mjs");
 lib.GlobalWorkerOptions.workerSrc="./vendor/pdf.worker.mjs";
 return pdfLib=lib;
}
async function pdfOriginal(record,host){
 const card=E("article","record-document record-pdf");
 card.append(heading(record.title,record.id+" · 原版PDF · 逐页按需显示"));
 const status=E("p","record-detail","读取原始PDF…"),pages=E("div","record-pdf-pages");
 card.append(status,pages);host.append(card);
 try{
  const lib=await pdfEngine();
  const task=lib.getDocument({url:record.url,withCredentials:false});
  const pdf=await task.promise;
  status.textContent=record.id+" · "+pdf.numPages+" 页 · 原始文件未改写";
  const queue=[];let active=0;const onscreen=new Map();
  async function pump(){
   if(active>=2||!queue.length)return;
   const holder=queue.shift();if(holder.dataset.rendered==="true"||holder.dataset.rendering==="true")return pump();
   active++;holder.dataset.rendering="true";
   try{
    const page=await pdf.getPage(Number(holder.dataset.page)),raw=page.getViewport({scale:1});
    const width=Math.max(280,Math.min(860,holder.clientWidth||760));
    const viewport=page.getViewport({scale:width/raw.width}),dpr=Math.min(window.devicePixelRatio||1,1.6);
    const canvas=document.createElement("canvas");canvas.width=Math.ceil(viewport.width*dpr);canvas.height=Math.ceil(viewport.height*dpr);
    canvas.style.width="100%";canvas.style.height="auto";
    const ctx=canvas.getContext("2d");
    await page.render({canvasContext:ctx,viewport,transform:dpr!==1?[dpr,0,0,dpr,0,0]:undefined}).promise;
    holder.replaceChildren(canvas,E("small","record-pdf-page-caption","原PDF 第"+holder.dataset.page+"页"));
    holder.dataset.rendered="true";onscreen.delete(holder);onscreen.set(holder,Date.now());
    if(onscreen.size>10){const old=onscreen.keys().next().value;if(old!==holder){
      old.querySelector("canvas")?.remove();old.dataset.rendered="false";old.replaceChildren(E("span","record-page-wait","第"+old.dataset.page+"页"));onscreen.delete(old);
    }}
   }catch(e){holder.textContent="第"+holder.dataset.page+"页渲染失败："+e.message;holder.dataset.rendered="failed"}
   finally{holder.dataset.rendering="false";active--;pump()}
  }
  const observer=new IntersectionObserver(entries=>{
   entries.forEach(e=>{if(e.isIntersecting&&e.target.dataset.rendered!=="true"&&e.target.dataset.rendered!=="failed"&&!queue.includes(e.target)){queue.push(e.target)}});
   pump();
  },{rootMargin:"650px"});
  const frag=document.createDocumentFragment();
  for(let i=1;i<=pdf.numPages;i++){
   const holder=E("div","record-pdf-page");holder.dataset.page=String(i);
   holder.append(E("span","record-page-wait","第"+i+"页"));frag.append(holder);observer.observe(holder);
  }pages.append(frag);
 }catch(e){status.textContent="原件未能读取："+e.message;card.dataset.pdf="failed"}
}
async function figureGallery(module,host){
 const names=subjectGroups[module.id];if(!names)return;
 const box=E("section","record-figures");
 box.append(heading("原始科研图","按归档原始文件直接显示"));const list=E("div","record-figure-list");box.append(list);host.append(box);
 try{
  const r=await fetch("./data/figure-index.json",{cache:"force-cache"});if(!r.ok)throw Error("HTTP "+r.status);
  const d=await r.json(),used=new Set();
  const images=d.images.filter(f=>names.includes(f.c)&&!used.has(f.p)&&used.add(f.p));
  const frag=document.createDocumentFragment();
  for(const f of images){
   const fig=E("figure","record-figure"),img=E("img");img.src=srcFigure(f);img.alt=f.n;img.loading="lazy";img.decoding="async";
   const caption=E("figcaption","",f.n+" · "+f.c+" · 源Git SHA "+f.sha);
   img.addEventListener("error",()=>{fig.dataset.failed="true";caption.textContent=f.n+" · 原始图不可读取（未替换）"});
   fig.append(img,caption);frag.append(fig);
  }list.replaceChildren(frag);box.dataset.count=String(images.length);
 }catch(e){list.append(E("p","record-failed","原始图目录读取失败："+e.message))}
}
async function show(module,root){
 if(!module||!root)return;
 const scope=E("div","record-source-workspace");root.append(scope);
 const token=module.id;scope.dataset.module=token;
 if(module.id==="field"){
  const pdfBox=E("section","record-pdfs");
  pdfBox.append(heading("嘉鱼官方项目资料","已归档的公开原版PDF，连续阅读"));
  scope.append(pdfBox);
  try{
   const response=await fetch("./data/reference-index.json",{cache:"force-cache"}),data=await response.json();
   const docs=data.entries.filter(d=>["SRC004","SRC003"].includes(d.id)&&d.status==="indexed"&&d.url);
   for(const record of docs)pdfOriginal(record,pdfBox);
  }catch(e){pdfBox.append(E("p","record-failed",e.message))}
 }
 const sources=(module.links||[]).filter(x=>sourceSpec(x.url));
 if(sources.length){
  const records=E("section","record-sources");records.append(heading("研究报告与原始数据",sources.length+" 份已登记源码文档"));
  scope.append(records);
  for(const item of sources)rawDocument(item,records);
 }
 await figureGallery(module,scope);
}
window.JYModuleReader={show,sourceSpec,sourceTable,pdfOriginal};
})();