"use strict";
/* T092 — all 81 archived references + 163 cited works + 395 original source sheets.
   No new copies of publisher PDFs, no paywall bypass, no fabricated full texts.
   Original PDFs are read from pre-existing public source paths only, using
   the pinned local PDF.js distribution already used by this workspace. */
(function(){
const S={data:null,loading:null,root:null,query:"",category:"",topic:"",masterQuery:"",
 current:null,pdf:null,pdfLoading:null,library:null,token:0,observer:null,queue:[],
 busy:0,rendered:new Map(),visited:0,openTab:"files",scanQuery:"",scanGroup:"",ready:false};
const $=id=>document.getElementById(id);
function E(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n}
function safe(s){return String(s??"").toLowerCase()}
const encoded=p=>p.split("/").map(encodeURIComponent).join("/");
function label(ref){
 if(ref.status!=="indexed")return ref.mode==="lfs-pointer"?"Git LFS仅指针 · 原文件未取得":"元数据 · 未收录原文";
 return "PDF已归档 · 点击逐页阅读";
}
async function load(){
 if(S.data)return S.data;
 if(!S.loading)S.loading=fetch("./data/reference-index.json",{cache:"no-store"})
  .then(r=>{if(!r.ok)throw Error("参考原始索引 HTTP "+r.status);return r.json()})
  .then(d=>{
    if(d.total!==81||d.entries?.length!==81||d.master?.length!==163||d.images?.length!==395)
      throw Error("参考文献原始索引未满足81/163/395源级约束");
    if(d.entries.filter(x=>x.status==="indexed").length!==79)
      throw Error("本库PDF可读证据数不符");
    if(new Set(d.entries.map(x=>x.id)).size!==81)throw Error("档案REF编号重复");
    return S.data=d;
  }).catch(e=>{S.loading=null;throw e});
 return S.loading;
}
function summary(d){
 const el=E("div","corpus-summary");
 [["81","GitHub已登记PDF档案"],["79","标记有原文的PDF"],["2","缺失原件/受限"],["163","学术参考书目"],["395","来源原始页图"],["40","另有授权期刊完整页"]].forEach(([n,t])=>{
   const card=E("div","corpus-count");card.append(E("strong","",n),E("span","",t));el.append(card)
 });
 return el;
}
function matches(row){
 const s=[row.id,row.title,row.name,row.doi,row.author,row.topic,row.category].join(" ").toLowerCase();
 return (!S.query||s.includes(S.query))&&(!S.category||row.category===S.category)&&(!S.topic||row.topic===S.topic);
}
function control(root,d){
 const bar=E("div","corpus-controls");
 const find=E("input","corpus-search");find.type="search";find.placeholder="检索全部81份原文：REF、作者、题名、DOI";find.setAttribute("aria-label","检索81份PDF原文");
 find.addEventListener("input",()=>{S.query=safe(find.value).trim();paintFiles()});
 const category=E("select","corpus-select");category.setAttribute("aria-label","筛选资料类别");
 const all=E("option","","全部来源");all.value="";category.append(all);
 Object.keys(d.groups).forEach(k=>{const o=E("option","",k);o.value=k;category.append(o)});
 category.addEventListener("change",()=>{S.category=category.value;paintFiles()});
 const topic=E("select","corpus-select");topic.setAttribute("aria-label","筛选研究专题");
 const any=E("option","","全部主题");any.value="";topic.append(any);
 [...new Set(d.entries.map(x=>x.topic))].sort().forEach(k=>{const o=E("option","",k);o.value=k;topic.append(o)});
 topic.addEventListener("change",()=>{S.topic=topic.value;paintFiles()});
 bar.append(find,category,topic);root.append(bar);
}
function paperRow(doc,i){
 const card=E("article","corpus-file");
 card.dataset.ref=doc.id;
 const left=E("div","corpus-file-info"),top=E("div","corpus-file-top");
 top.append(E("span","corpus-ref-id",doc.id),E("span","",doc.category),E("span","",doc.year||"年份待核"),E("span","",doc.topic));
 left.append(top,E("h3","",doc.title));
 const sub=E("p","corpus-file-sub");
 sub.textContent=(doc.doi?"DOI "+doc.doi+" · ":"")+(doc.license||"许可未标注，保持原始归档")+" · "+(doc.size?(doc.size/1048576).toFixed(2)+" MiB · ":"")+doc.mode;
 left.append(sub);
 const right=E("div","corpus-file-actions");
 if(doc.status==="indexed"&&doc.url){
  const open=E("button","corpus-open","站内阅读全文");open.type="button";open.dataset.openPdf=doc.id;
  open.addEventListener("click",()=>readDoc(doc));
  right.append(open);
 }else right.append(E("span","corpus-missing",label(doc)));
 card.append(left,right);return card;
}
function paintFiles(){
 const d=S.data;if(!d)return;
 const rows=d.entries.filter(matches);
 $("corpus-file-count").textContent=rows.length+" / 81份档案 · "+rows.filter(x=>x.status==="indexed").length+"份有原文件";
 $("corpus-file-grid").replaceChildren(...rows.map(paperRow));
}
function matchingRef(master){
 return S.data.entries.find(x=>x.id===master.archiveId)||S.data.entries.find(x=>x.name===master.archiveName);
}
function masterRow(ref){
 const item=E("article","corpus-master-row");
 item.append(E("span","corpus-master-code",ref.id),E("div","corpus-master-body"));
 const info=item.lastChild;
 info.append(E("strong","",ref.title),E("small","",ref.year+" · "+ref.theme+" · "+ref.doiOrSource));
 const mapped=matchingRef(ref);
 if(mapped?.status==="indexed"){
  const b=E("button","corpus-inline-small","原文逐页");b.type="button";
  b.addEventListener("click",()=>readDoc(mapped));item.append(b)
 }else item.append(E("span","corpus-missing",ref.hasFile?"档案暂不可用":"仅参考文献条目"));
 return item;
}
function paintMaster(){
 const q=S.masterQuery,items=S.data.master.filter(x=>!q||[x.id,x.title,x.theme,x.doiOrSource,x.year].join(" ").toLowerCase().includes(q));
 $("corpus-master-count").textContent=items.length+" / 163条学术参考书目 · "+items.filter(x=>matchingRef(x)?.status==="indexed").length+"条关联已归档PDF";
 $("corpus-master-grid").replaceChildren(...items.map(masterRow))
}
function photo(f){
 const figure=E("figure","corpus-scan-card"),image=E("img");
 image.src="./figures/"+encoded(f.p);image.loading="lazy";image.decoding="async";image.alt=f.n;
 const caption=E("figcaption","",f.n+" · "+f.g);
 image.addEventListener("error",()=>{image.hidden=true;caption.textContent+=" · 原始图无法读取"});
 figure.append(image,caption);return figure
}
function paintScans(){
 const rows=S.data.images.filter(f=>(!S.scanGroup||f.g===S.scanGroup)&&(!S.scanQuery||safe(f.g+" "+f.n+" "+f.p).includes(S.scanQuery)));
 $("corpus-scan-count").textContent=rows.length+" / 395张原始证据页 · 连续显示，不分页";
 $("corpus-scan-grid").replaceChildren(...rows.map(photo));
}
function setStatus(value,failed=false){
 const el=$("corpus-pdf-status");if(el){el.textContent=value;el.classList.toggle("corpus-error",failed)}
}
async function engine(){
 if(S.library)return S.library;
 const sources=[
  ["./vendor/pdf.mjs","./vendor/pdf.worker.mjs"],
  ["https://cdn.jsdelivr.net/npm/pdfjs-dist@5.4.530/build/pdf.mjs",
   "https://cdn.jsdelivr.net/npm/pdfjs-dist@5.4.530/build/pdf.worker.mjs"],
  ["https://unpkg.com/pdfjs-dist@5.4.530/build/pdf.mjs",
   "https://unpkg.com/pdfjs-dist@5.4.530/build/pdf.worker.mjs"]
 ];
 const errors=[];
 for(const [uri,worker] of sources){
  try{
   const module=await import(uri);
   if(typeof module.getDocument!=="function")throw Error("Invalid PDF.js module");
   module.GlobalWorkerOptions.workerSrc=worker;
   return S.library=module;
  }catch(e){errors.push(uri+": "+e.message)}
 }
 throw Error("PDF.js引擎不可读取："+errors.join(" | "));
}
function teardown(){
 S.token++;
 S.observer?.disconnect();S.observer=null;S.queue.length=0;S.rendered.clear();
 const old=S.pdf;const loading=S.pdfLoading;S.pdf=null;S.pdfLoading=null;S.busy=0;
 if(loading){try{loading.destroy()}catch{}}
 if(old){try{old.destroy()}catch{}}
}
function pagePlaceholder(pageNumber){
 const page=E("figure","corpus-pdf-page");page.id="corpus-pdf-page-"+pageNumber;page.dataset.page=String(pageNumber);
 const holder=E("div","corpus-pdf-holder");
 holder.append(E("span","corpus-page-wait","第 "+pageNumber+" 页 · 滚动至此自动呈现原始PDF"));
 page.append(holder,E("figcaption","corpus-pdf-caption","原PDF第 "+pageNumber+"页 · 原样渲染，未重新编辑"));
 return page;
}
function trim(token){
 if(token!==S.token)return;
 while(S.rendered.size>9){
  const [key,old]=S.rendered.entries().next().value;
  S.rendered.delete(key);
  const holder=old.querySelector(".corpus-pdf-holder");
  if(holder)holder.replaceChildren(E("span","corpus-page-wait","第 "+key+" 页 · 按需重新呈现"));
  old.dataset.rendered="false";
  S.observer?.observe(old);
 }
}
function schedule(node){
 if(!node||!S.pdf||node.dataset.rendered==="true"||node.dataset.rendering==="true")return;
 if(S.queue.includes(node))return;
 S.queue.push(node);pump();
}
function pump(){
 if(S.busy>=2||!S.queue.length||!S.pdf)return;
 const node=S.queue.shift(),pdf=S.pdf,token=S.token;
 if(node.dataset.rendered==="true"){pump();return}
 S.busy++;node.dataset.rendering="true";
 (async()=>{
  const number=Number(node.dataset.page),page=await pdf.getPage(number);
  if(token!==S.token)return;
  const viewportBase=page.getViewport({scale:1});
  const target=Math.max(260,Math.min(950,$("corpus-pdf-pages").clientWidth-32));
  const scale=Math.min(2.0,target/viewportBase.width);
  const view=page.getViewport({scale});
  const canvas=E("canvas","corpus-pdf-canvas");
  const ratio=Math.min(1.5,window.devicePixelRatio||1);
  canvas.width=Math.floor(view.width*ratio);canvas.height=Math.floor(view.height*ratio);
  canvas.style.width="100%";canvas.style.height="auto";
  const ctx=canvas.getContext("2d",{alpha:false});
  if(!ctx)throw Error("Canvas context unavailable");
  await page.render({canvasContext:ctx,viewport:view,transform:ratio!==1?[ratio,0,0,ratio,0,0]:undefined}).promise;
  if(token!==S.token)return;
  const holder=node.querySelector(".corpus-pdf-holder");
  holder.replaceChildren(canvas);
  node.dataset.rendered="true";S.observer?.unobserve(node);
  S.rendered.delete(number);S.rendered.set(number,node);trim(token);
 })().catch(e=>{
   if(token===S.token){
    node.querySelector(".corpus-pdf-holder").replaceChildren(E("p","corpus-error","原始PDF第 "+node.dataset.page+" 页渲染失败："+e.message));
    node.dataset.rendered="failed";S.observer?.unobserve(node)
   }
 }).finally(()=>{
  if(token===S.token){node.dataset.rendering="false";S.busy--;pump()}
 });
 if(S.busy<2)pump()
}
function seek(number){
 const node=$("corpus-pdf-page-"+number);
 if(!node)return;
 node.scrollIntoView({behavior:"smooth",block:"start"});
 schedule(node)
}
async function readDoc(doc){
 if(doc.status!=="indexed"||!doc.url)return;
 teardown();const token=S.token;
 S.current=doc;
 const reader=$("corpus-fulltext-reader"),pages=$("corpus-pdf-pages"),heading=$("corpus-pdf-title");
 if(!reader||!pages)return;
 reader.hidden=false;heading.textContent=doc.title;
 pages.replaceChildren(E("p","corpus-loading","正在载入已归档PDF字节及其真实页面…"));
 $("corpus-pdf-identity").textContent=doc.id+" · "+(doc.license||"许可未标注")+" · 存档路径："+doc.path+" · 源Git SHA："+doc.sha;
 setStatus("原始PDF载入中");
 reader.scrollIntoView({behavior:"smooth",block:"start"});
 try{
  const lib=await engine();
  if(token!==S.token)return;
  const task=lib.getDocument({url:doc.url,rangeChunkSize:65536});
  S.pdfLoading=task;
  const pdf=await task.promise;
  if(token!==S.token){pdf.destroy();return}
  S.pdf=pdf;S.pdfLoading=null;
  const count=pdf.numPages;
  $("corpus-pdf-pagecount").textContent="共 "+count+" 页 · 全部页在下方按需呈现";
  const chooser=$("corpus-jump");chooser.max=count;chooser.value=1;
  const frag=document.createDocumentFragment();
  for(let i=1;i<=count;i++)frag.append(pagePlaceholder(i));
  pages.replaceChildren(frag);
  S.observer=new IntersectionObserver(entries=>{
    if(token!==S.token)return;
    entries.forEach(entry=>{if(entry.isIntersecting)schedule(entry.target)})
  },{root:null,rootMargin:"1100px 0px",threshold:0.01});
  for(const node of pages.children)S.observer.observe(node);
  setStatus("PDF.js已读取真实原始PDF · "+count+"页；逐页按需呈现，不下载、不离开工作室");
  schedule(pages.firstElementChild)
 }catch(e){
  if(token===S.token){pages.replaceChildren(E("p","corpus-error","原件无法在本机浏览器直接读取；未提供伪造截图。原因："+e.message));setStatus("原文加载失败 · "+e.message,true)}
 }
}
function mount(root,d){
 const view=E("section","corpus-atlas");view.id="all-reference-corpus";
 const heading=E("header","corpus-heading");
 heading.append(E("span","section-kicker","COMPLETE ORIGINAL REFERENCE CORPUS"),
  E("h2","","GitHub全部参考文献 · 原文逐页阅读"),
  E("p","","81份PDF全部列出，79份档案标记有原始文件，163条学术书目一条不漏，395张来源原页直接展示。已存在的PDF从原始归档读取，逐页按需渲染；不存在的全文与版权状态如实标明。"));
 view.append(heading,summary(d));
 const reader=E("section","corpus-reader");reader.id="corpus-fulltext-reader";reader.hidden=true;
 const head=E("header","corpus-reader-heading");
 head.append(E("span","section-kicker","FULL DOCUMENT · PAGE BY PAGE"),E("h3","", ""));
 const title=head.querySelector("h3");title.id="corpus-pdf-title";
 const info=E("p","corpus-pdf-identity");info.id="corpus-pdf-identity";
 const bar=E("div","corpus-reader-toolbar");const status=E("span","corpus-pdf-status","未选择文献");status.id="corpus-pdf-status";
 const pagecount=E("span","corpus-pdf-pagecount");pagecount.id="corpus-pdf-pagecount";
 const label=E("label","", "跳至原文页");const num=E("input","corpus-pdf-jump");num.id="corpus-jump";num.type="number";num.min="1";num.value="1";
 num.addEventListener("change",()=>seek(Math.max(1,Math.min(Number(num.max)||1,Math.floor(Number(num.value)||1)))));
 label.append(num);
 const close=E("button","corpus-close","收起全文");close.type="button";close.addEventListener("click",()=>{teardown();reader.hidden=true});
 bar.append(status,pagecount,label,close);
 const pages=E("div","corpus-pdf-pages");pages.id="corpus-pdf-pages";
 reader.append(head,info,bar,pages);view.append(reader);
 const tabs=E("div","corpus-index-head");
 tabs.append(E("h3","","原始PDF档案全集"));
 const count=E("p","corpus-index-count");count.id="corpus-file-count";tabs.append(count);
 view.append(tabs);control(view,d);
 const files=E("div","corpus-file-grid");files.id="corpus-file-grid";view.append(files);
 const bibliography=E("section","corpus-master");
 bibliography.append(E("h3","","163篇学术参考文献 · 完整书目索引"),
   E("p","corpus-note","163条是参考文献总条目，不表示163篇全文全部已获得。已对应归档原PDF的可直接展开完整论文；其余保留真实学术元数据。"));
 const searching=E("input","corpus-search");searching.type="search";searching.placeholder="检索163条：REF、标题、作者、DOI、研究主题";
 searching.setAttribute("aria-label","检索全部163条参考文献");
 searching.addEventListener("input",()=>{S.masterQuery=safe(searching.value).trim();paintMaster()});bibliography.append(searching);
 const mc=E("p","corpus-index-count");mc.id="corpus-master-count";bibliography.append(mc);
 const mg=E("div","corpus-master-grid");mg.id="corpus-master-grid";bibliography.append(mg);view.append(bibliography);
 const scans=E("section","corpus-scan-collection");
 scans.append(E("h3","","395张文献原始证据页 · 连续原图"),
  E("p","corpus-note","全部图像来自GitHub原始资料归档。已获版权使用许可的完整期刊正文见上方40页专区；这里的截图仅代表已有来源证据，不宣称包含81篇完整PDF的所有页面。"));
 const sc=E("div","corpus-scan-controls"),find=E("input","corpus-search");
 find.type="search";find.placeholder="按原件标题/页码检索395张原图";
 find.addEventListener("input",()=>{S.scanQuery=safe(find.value).trim();paintScans()});
 const group=E("select","corpus-select");const none=E("option","","全部来源");none.value="";group.append(none);
 Object.keys(d.imageGroups).sort().forEach(k=>{const o=E("option","",k);o.value=k;group.append(o)});
 group.addEventListener("change",()=>{S.scanGroup=group.value;paintScans()});
 sc.append(find,group);scans.append(sc);
 const ic=E("p","corpus-index-count");ic.id="corpus-scan-count";scans.append(ic);
 const ig=E("div","corpus-scan-grid");ig.id="corpus-scan-grid";scans.append(ig);view.append(scans);
 root.prepend(view);
 S.root=view;S.ready=true;paintFiles();paintMaster();paintScans();
}
async function show(root){
 if(!root)return;
 try{
  const d=await load();
  if(!S.ready||!S.root||!S.root.isConnected)mount(root,d);
  else if(S.root.parentElement!==root)root.prepend(S.root)
 }catch(e){console.error(e);root.prepend(E("p","corpus-error","文献全集原始索引读取失败："+e.message))}
}
window.JYFullReferences={show,all:()=>S.data?.entries||[]};
})();