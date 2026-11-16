"use strict";
/* T088: in-page original-figure reader; no navigation, download button, iframe or fabricated figures. */
(function(){
const S={promise:null,data:null,bound:false,query:"",category:"",rendered:false,literatureRoot:null};
const el=(tag,klass,value)=>{
 const node=document.createElement(tag);if(klass)node.className=klass;
 if(value!==undefined)node.textContent=String(value);
 return node;
};
const byId=id=>document.getElementById(id);
const encodedPath=path=>path.split("/").map(encodeURIComponent).join("/");
const localSource=figure=>"./figures/"+encodedPath(figure.p);
async function load(){
 if(S.data)return S.data;
 if(!S.promise)S.promise=Promise.all([
  fetch("./data/inline-atlas.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("期刊图源索引HTTP "+r.status);return r.json();}),
  fetch("./data/figure-index.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("研究图索引HTTP "+r.status);return r.json();})
 ]).then(([sources,archive])=>{
  if(sources.schema!==1||!Array.isArray(sources.figures)||sources.figures.length!==5||!Array.isArray(sources.papers)||sources.papers.length!==24)throw Error("期刊证据目录不完整");
  if(!Array.isArray(archive.images)||archive.images.length<541)throw Error("研究原图索引不完整");
  if(new Set(archive.images.map(f=>f.p)).size!==archive.images.length)throw Error("归档路径有重复");
  S.data={sources,archive};return S.data;
 }).catch(e=>{S.promise=null;throw e;});
 return S.promise;
}
function statusText(node,message,failed=false){
 node.textContent=message;node.classList.toggle("atlas-error",failed);
}
function publisherFigure(f){
 const card=el("figure","atlas-journal-card");
 const heading=el("div","atlas-journal-heading");
 heading.append(el("span","atlas-source-no",f.ref+" / "+f.figure),el("span","atlas-source-kind",f.kind));
 const imageWrap=el("div","atlas-journal-image-wrap");
 const image=el("img","atlas-journal-img");
 image.loading="lazy";image.decoding="async";image.src=f.src;
 image.alt=f.author+" "+f.figure+"："+f.title;
 const loading=el("div","atlas-image-status","原始图像加载中");
 image.addEventListener("load",()=>statusText(loading,"原始图像已直接显示"));
 image.addEventListener("error",()=>statusText(loading,"原出版方图像暂不能内嵌显示；未用替代图冒充原件",true));
 imageWrap.append(image,loading);
 const caption=el("figcaption","atlas-caption");
 caption.append(el("strong","",f.title));
 caption.append(el("p","",f.author+"（"+f.year+"） · "+f.journal+" · "+f.figure));
 caption.append(el("p","atlas-source-doi","DOI "+f.doi+" · "+f.license));
 caption.append(el("p","atlas-source-description",f.description));
 if(f.sha256)caption.append(el("small","atlas-source-hash","原始字节 SHA256："+f.sha256));
 card.append(heading,imageWrap,caption);return card;
}
function paperCard(p){
 const item=el("article","atlas-paper");
 const top=el("div","atlas-paper-top");
 top.append(el("span","atlas-paper-id",p.id+" / "+p.year));
 const n=S.data.sources.figures.filter(f=>f.ref===p.id).length;
 top.append(el("span","atlas-paper-availability",n?n+"张论文原图直接显示":"暂无可合法直显的原图"));
 item.append(top,el("h3","",p.title),el("p","atlas-paper-meta",p.authors+" · "+p.journal));
 item.append(el("p","atlas-paper-note",p.claim));
 if(p.doi.startsWith("10."))item.append(el("small","atlas-paper-doi","DOI "+p.doi));
 return item;
}
function renderJournal(host){
 if(!host||!S.data)return;
 host.replaceChildren(...S.data.sources.figures.map(publisherFigure));
}
function renderPapers(host){
 if(!host||!S.data)return;
 const fragment=document.createDocumentFragment();
 S.data.sources.papers.forEach(p=>fragment.append(paperCard(p)));
 host.replaceChildren(fragment);
}
function fileCard(f){
 const card=el("figure","atlas-file-card");
 const image=el("img","atlas-file-image");
 image.src=localSource(f);image.loading="lazy";image.decoding="async";
 image.alt=(f.c||"归档研究图")+"："+f.n;
 const bad=el("div","atlas-file-error","图片暂不可读");
 bad.hidden=true;
 image.addEventListener("error",()=>{image.hidden=true;bad.hidden=false});
 const caption=el("figcaption","atlas-file-caption");
 caption.append(el("strong","",f.n),el("span","",f.c));
 card.append(image,bad,caption);
 return card;
}
function renderComplete(){
 if(!S.data)return;
 const grid=byId("atlas-complete-grid"),summary=byId("atlas-complete-count");
 if(!grid||!summary)return;
 const q=S.query.toLowerCase(),category=S.category;
 const list=S.data.archive.images.filter(f=>(!category||f.c===category)&&(!q||(f.n+" "+f.p+" "+f.c).toLowerCase().includes(q)));
 const fragment=document.createDocumentFragment();
 list.forEach(f=>fragment.append(fileCard(f)));
 grid.replaceChildren(fragment);
 summary.textContent=list.length+" / "+S.data.archive.images.length+" 张已归档图片直接阅读 · 不分页";
 if(!list.length)grid.append(el("p","atlas-empty","未匹配到已归档原图"));
}
function bind(){
 if(S.bound)return;
 const search=byId("atlas-complete-search"),category=byId("atlas-complete-category");
 if(!search||!category)return;
 for(const [label,count] of Object.entries(S.data.archive.categories||{})){
  const option=el("option","",label+" · "+count);option.value=label;category.append(option);
 }
 search.addEventListener("input",()=>{S.query=search.value.trim();renderComplete()});
 category.addEventListener("change",()=>{S.category=category.value;renderComplete()});
 S.bound=true;
}
async function show(){
 try{
  await load();
  renderJournal(byId("joint-atlas-gallery"));
  renderPapers(byId("joint-atlas-papers"));
  if(!S.rendered){bind();renderComplete();S.rendered=true;}
 }catch(error){
  const target=byId("joint-atlas-gallery");
  if(target)target.replaceChildren(el("p","atlas-error","原始图索引载入失败："+error.message));
  console.error(error);
 }
}
async function showLiterature(root){
 if(!root)return;
 try{
  await load();
  let section=byId("literature-inline-atlas");
  if(!section){
   section=el("section","inline-atlas literature-atlas");
   section.id="literature-inline-atlas";
   section.append(el("span","section-kicker","ORIGINAL FIGURES · SCIENTIFIC SOURCES"));
   section.append(el("h2","","水平接缝期刊原图 · 直接阅读"));
   section.append(el("p","atlas-intro","5张已确认授权的论文图源：3张GitHub存档原版、2张出版方直显。其余文献的原始图片未取得公开镜像许可，不以示意图冒充。"));
   const images=el("div","atlas-journal-list");images.id="literature-journal-gallery";section.append(images);
   const papers=el("details","atlas-bibliography");
   const summary=el("summary","","24篇水平接缝核心文献 · 文内完整索引");
   const list=el("div","atlas-paper-grid");list.id="literature-atlas-papers";
   papers.open=true;papers.append(summary,list);section.append(papers);
  }
  if(section.parentElement!==root)root.prepend(section);
  renderJournal(byId("literature-journal-gallery"));
  renderPapers(byId("literature-atlas-papers"));
 }catch(error){console.error("文献原图直显失败",error);}
}
window.JYAtlas={show,showLiterature};
})();