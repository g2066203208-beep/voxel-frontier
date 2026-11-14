"use strict";
(function(){
const S={data:null,promise:null,mounted:false,tab:"pdf",category:"",topic:"",query:"",page:0,imagePage:0,imageGroup:"",imageQuery:"",perPage:18,imagesPerPage:24};
const $=id=>document.getElementById(id);
const E=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n;};
const src=f=>"./figures/"+f.p.split("/").map(encodeURIComponent).join("/");
async function load(){
 if(S.data)return S.data;
 if(!S.promise)S.promise=fetch("./data/reference-index.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("reference-index "+r.status);return r.json()}).then(d=>{if(d.total!==81||d.images.length!==395)throw Error("reference index incomplete");return S.data=d}).catch(e=>{S.promise=null;throw e});
 return S.promise;
}
const listDocs=()=>S.data.entries.filter(x=>(!S.category||x.category===S.category)&&(!S.topic||x.topic===S.topic)&&(!S.query||[x.title,x.name,x.author,x.doi,x.id,x.topic].join(" ").toLowerCase().includes(S.query)));
const listImages=()=>S.data.images.filter(x=>(!S.imageGroup||x.g===S.imageGroup)&&(!S.imageQuery||(x.p+" "+x.n+" "+x.g).toLowerCase().includes(S.imageQuery)));
function row(doc){
 const el=E("article","reference-row"),info=E("div","reference-info");
 const meta=E("div","reference-item-meta");
 meta.append(E("span","reference-label",doc.category),E("span","",doc.year||"—"),E("span","",doc.id));
 const name=E("strong","reference-item-title",doc.title);name.title=doc.name;
 const bottom=E("div","reference-item-bottom");
 bottom.append(E("span","",doc.topic),E("span","",doc.doi?"DOI "+doc.doi:""),E("span","",doc.size>1024*1024?(doc.size/1048576).toFixed(1)+" MB":""));
 info.append(meta,name,bottom);
 const side=E("div","reference-row-action");
 if(doc.status==="indexed"){const b=E("button","reference-read","原文阅读");b.type="button";b.addEventListener("click",()=>window.JYFigures?.focusReference(doc));side.append(b);}
 else side.append(E("small","reference-restricted",doc.mode==="metadata-only"?"元数据及原页":"原件待核"));
 el.append(info,side);return el;
}
function renderDocs(){
 if(!S.data)return;
 const docs=listDocs(),pages=Math.max(1,Math.ceil(docs.length/S.perPage));S.page=Math.max(0,Math.min(S.page,pages-1));
 const display=docs.slice(S.page*S.perPage,(S.page+1)*S.perPage);
 $("reference-doc-count").textContent=docs.length+" 份文献";
 $("reference-doc-list").replaceChildren(...display.map(row));
 $("reference-doc-page").textContent=(S.page+1)+" / "+pages;
 $("reference-doc-prev").disabled=S.page===0;$("reference-doc-next").disabled=S.page===pages-1;
}
function imageCard(f){
 const card=E("article","reference-scan"),button=E("button","reference-scan-preview");
 button.type="button";button.title=f.n;button.setAttribute("aria-label","放大原页 "+f.n);
 const img=E("img");img.loading="lazy";img.decoding="async";img.src=src(f);img.alt=f.n;
 img.onerror=()=>{img.hidden=true;button.append(E("small","","原图读取失败"))};
 button.append(img);button.addEventListener("click",()=>openImage(f));
 const label=E("div","reference-scan-caption");
 label.append(E("strong","",f.n),E("small","",f.g));
 card.append(button,label);return card;
}
function renderImages(){
 if(!S.data)return;
 const imgs=listImages(),pages=Math.max(1,Math.ceil(imgs.length/S.imagesPerPage));S.imagePage=Math.max(0,Math.min(S.imagePage,pages-1));
 $("reference-image-list").replaceChildren(...imgs.slice(S.imagePage*S.imagesPerPage,(S.imagePage+1)*S.imagesPerPage).map(imageCard));
 $("reference-image-count").textContent=imgs.length+" 张原页";
 $("reference-image-page").textContent=(S.imagePage+1)+" / "+pages;
 $("reference-image-prev").disabled=S.imagePage===0;$("reference-image-next").disabled=S.imagePage===pages-1;
}
function openImage(f){
 $("ref-zoom-title").textContent=f.n;$("ref-zoom-category").textContent=f.g;
 const img=$("ref-zoom-img");img.src=src(f);img.alt=f.n;
 const a=$("ref-zoom-download");a.href=src(f);a.download=f.n;
 $("ref-zoom-dialog").showModal();
}
function changeTab(tab){
 S.tab=tab;
 for(const b of document.querySelectorAll("[data-reference-tab]")){const active=b.dataset.referenceTab===tab;b.classList.toggle("selected",active);b.setAttribute("aria-selected",String(active))}
 $("reference-pdfs").hidden=tab!=="pdf";$("reference-scans").hidden=tab!=="images";
 if(tab==="images")renderImages();else renderDocs();
}
function mount(root){
 const section=E("section","references-library");section.id="reference-library";
 section.innerHTML=[
 "<header class='reference-header'><div><span class='section-kicker'>LITERATURE & ORIGINAL SOURCES</span><h2>参考文献原始资料</h2></div><span id='reference-summary'></span></header>",
 "<div class='reference-tabs' role='tablist' aria-label='文献与原图'><button type='button' data-reference-tab='pdf' class='selected' role='tab' aria-selected='true'>参考文献 PDF</button><button type='button' data-reference-tab='images' role='tab' aria-selected='false'>原始页图</button></div>",
 "<section id='reference-pdfs'><div class='reference-controls'><input type='search' id='reference-search' placeholder='检索作者、题名、DOI、REF编号…' aria-label='文献检索'><select id='reference-category' aria-label='文献来源'><option value=''>全部来源</option></select><select id='reference-topic' aria-label='研究专题'><option value=''>全部专题</option></select></div><div class='reference-counter' id='reference-doc-count'></div><div id='reference-doc-list' class='reference-doc-list'></div><div class='reference-pager'><button type='button' id='reference-doc-prev'>上一页</button><span id='reference-doc-page'></span><button type='button' id='reference-doc-next'>下一页</button></div></section>",
 "<section id='reference-scans' hidden><div class='reference-controls'><input type='search' id='reference-image-search' placeholder='检索原页名称、页码…' aria-label='原始页图检索'><select id='reference-image-group' aria-label='页图来源'><option value=''>全部来源</option></select></div><div class='reference-counter' id='reference-image-count'></div><div id='reference-image-list' class='reference-scan-grid'></div><div class='reference-pager'><button type='button' id='reference-image-prev'>上一页</button><span id='reference-image-page'></span><button type='button' id='reference-image-next'>下一页</button></div></section>"
 ].join("");
 root.prepend(section);
 const dialog=E("dialog","ref-zoom-dialog");dialog.id="ref-zoom-dialog";
 dialog.innerHTML="<header><div><small id='ref-zoom-category'></small><strong id='ref-zoom-title'></strong></div><button type='button' id='ref-zoom-close' aria-label='关闭'>×</button></header><div class='ref-zoom-body'><img id='ref-zoom-img' alt=''></div><footer><a id='ref-zoom-download' download>下载原页 ↓</a></footer>";
 document.body.append(dialog);
 $("ref-zoom-close").addEventListener("click",()=>dialog.close());
 dialog.addEventListener("click",e=>{if(e.target===dialog)dialog.close()});
 for(const b of document.querySelectorAll("[data-reference-tab]"))b.addEventListener("click",()=>changeTab(b.dataset.referenceTab));
 const cat=$("reference-category"),topic=$("reference-topic"),group=$("reference-image-group");
 for(const k of Object.keys(S.data.groups)){const o=E("option","",k);o.value=k;cat.append(o);}
 for(const k of [...new Set(S.data.entries.map(x=>x.topic))].sort((a,b)=>a.localeCompare(b,"zh"))){const o=E("option","",k);o.value=k;topic.append(o);}
 for(const [k,v] of Object.entries(S.data.imageGroups)){const o=E("option","",k+" · "+v);o.value=k;group.append(o);}
 $("reference-summary").textContent=S.data.total+" PDF · "+S.data.originalImageCount+" 原页";
 $("reference-search").addEventListener("input",e=>{S.query=e.target.value.toLowerCase();S.page=0;renderDocs()});
 cat.addEventListener("change",e=>{S.category=e.target.value;S.page=0;renderDocs()});
 topic.addEventListener("change",e=>{S.topic=e.target.value;S.page=0;renderDocs()});
 $("reference-doc-prev").addEventListener("click",()=>{S.page--;renderDocs();section.scrollIntoView({block:"start"})});
 $("reference-doc-next").addEventListener("click",()=>{S.page++;renderDocs();section.scrollIntoView({block:"start"})});
 $("reference-image-search").addEventListener("input",e=>{S.imageQuery=e.target.value.toLowerCase();S.imagePage=0;renderImages()});
 group.addEventListener("change",e=>{S.imageGroup=e.target.value;S.imagePage=0;renderImages()});
 $("reference-image-prev").addEventListener("click",()=>{S.imagePage--;renderImages();section.scrollIntoView({block:"start"})});
 $("reference-image-next").addEventListener("click",()=>{S.imagePage++;renderImages();section.scrollIntoView({block:"start"})});
 S.mounted=true;renderDocs();
}
async function show(root){
 try{await load();if(!S.mounted)mount(root);else if($("reference-library").parentElement!==root)root.prepend($("reference-library"))}
 catch(e){console.error(e);root.prepend(E("p","reference-error","文献索引载入失败"))}
}
window.JYReferences={show,all:()=>S.data?.entries||[]};
})();