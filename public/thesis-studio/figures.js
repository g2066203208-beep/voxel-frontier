"use strict";
/* Curated Jiayu gallery: source-faithful images, paginated without hiding originals. */
(function(){
const S={data:null,promise:null,category:"",query:"",includeScans:false,page:0,perPage:24,selected:null,heReady:false,bound:false,doc:null};
const $=id=>document.getElementById(id);
const E=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=String(text);return e;};
const encode=p=>p.split("/").map(encodeURIComponent).join("/");
const original=f=>"./figures/"+encode(f.p);
const shortName=f=>f.n.replace(/\.(png|jpe?g|svg|webp|gif)$/i,"").replace(/_\d{8}$/,"");
const curated={
 "figure2-1-word-zh.png":"混塔结构几何",
 "mesh-convergence-zh.png":"网格收敛分析",
 "FIG_S05_03_ROTD_PUBLICATION.svg":"地震动方向响应谱",
 "FIG3_S12_ERA5_SHEAR_160M_CROSSCHECK_20261109.svg":"ERA5轮毂高度风环境",
 "FIG4_S10_ETM4_TENSION_DEL4_AZIMUTH_TRADEOFF_20261109.svg":"疲劳响应与方向效应",
 "FIG3_S07_REAL_NTM18_MULTILOAD_COINCIDENCE_20261111.svg":"真实风载同期性",
 "FIG_S08_ESM_FULLRATE_PAIRED_VECTOR_20261109.svg":"地震分量矢量组合"
};
async function ready(){
 if(S.data)return S.data;
 if(!S.promise)S.promise=fetch("./data/figure-index.json",{cache:"no-store"}).then(r=>{
  if(!r.ok)throw Error("Original image index HTTP "+r.status);
  return r.json();
 }).then(d=>{
  if(!Array.isArray(d.images)||d.images.length!==541||d.documents.length!==3)throw Error("Original image registry mismatch");
  S.data=d;return d;
 }).catch(e=>{S.promise=null;throw e;});
 return S.promise;
}
function download(f){
 const a=E("a");a.href=original(f);a.download=f.n;a.hidden=true;
 document.body.append(a);a.click();a.remove();
}
function zoom(f){
 S.selected=f;
 const dialog=$("figure-lightbox");if(!dialog)return;
 $("figure-zoom-name").textContent=curated[f.n]||shortName(f);
 $("figure-zoom-topic").textContent=f.c;
 $("figure-zoom-path").textContent=f.p;
 const img=$("figure-zoom-image");img.alt=f.n;img.src=original(f);
 dialog.showModal();
}
function card(f,compact=false){
 const article=E("article","figure-card"+(compact?" compact":""));
 const button=E("button","figure-preview");button.type="button";
 button.setAttribute("aria-label","查看原图 "+f.n);
 const photo=E("div","figure-photo");
 const img=E("img");img.src=original(f);img.loading="lazy";img.decoding="async";img.alt=curated[f.n]||f.n;
 img.onerror=()=>{img.hidden=true;photo.append(E("span","figure-error","原图读取失败"));};
 photo.append(img);button.append(photo);button.addEventListener("click",()=>zoom(f));
 const body=E("div","figure-card-body");
 const title=E("strong","figure-file",curated[f.n]||shortName(f));title.title=f.n;
 body.append(title,E("span","figure-card-category",f.c));
 const actions=E("div","figure-actions");
 const view=E("button","","预览");view.type="button";view.addEventListener("click",()=>zoom(f));
 const save=E("button","","下载");save.type="button";save.addEventListener("click",()=>download(f));
 actions.append(view,save);body.append(actions);
 article.append(button,body);return article;
}
function filtered(){
 if(!S.data)return [];
 const q=S.query.trim().toLowerCase();
 return S.data.images.filter(f=>
  (S.includeScans||f.c!=="文献与来源图像")&&
  (!S.category||f.c===S.category)&&
  (!q||(f.p+" "+f.n+" "+(curated[f.n]||"")+" "+f.c).toLowerCase().includes(q))
 );
}
function renderGrid(){
 if(!S.data)return;
 const list=filtered(),max=Math.max(1,Math.ceil(list.length/S.perPage));
 S.page=Math.max(0,Math.min(S.page,max-1));
 const visible=list.slice(S.page*S.perPage,(S.page+1)*S.perPage);
 const grid=$("figure-grid");grid.replaceChildren(...visible.map(f=>card(f)));
 if(!visible.length)grid.append(E("div","figure-empty","没有匹配的图片"));
 $("figure-count").textContent=list.length+" 张";
 $("figure-pageinfo").textContent=(S.page+1)+" / "+max;
 $("figure-prev").disabled=S.page===0;$("figure-next").disabled=S.page>=max-1;
 const toggle=$("figure-show-all");toggle.classList.toggle("selected",S.includeScans);
 toggle.setAttribute("aria-pressed",String(S.includeScans));
 toggle.textContent=S.includeScans?"仅研究图":"包含文献扫描";
}
function renderHe(){
 if(S.heReady||!S.data)return;
 S.heReady=true;
 const found=new Map(S.data.images.map(f=>[f.p,f]));
 const figs=S.data.hePages.map(p=>found.get(p)).filter(Boolean);
 $("he-original-grid").replaceChildren(...figs.map(f=>card(f,true)));
 $("he-page-count").textContent=figs.length+" 张";
}
function bind(){
 if(S.bound||!S.data)return;S.bound=true;
 const select=$("figure-category");
 for(const k of Object.keys(S.data.categories)){
  const opt=E("option","",k);opt.value=k;select.append(opt);
 }
 select.addEventListener("change",e=>{S.category=e.target.value;S.page=0;if(S.category==="文献与来源图像")S.includeScans=true;renderGrid();});
 $("figure-search").addEventListener("input",e=>{S.query=e.target.value;S.page=0;renderGrid();});
 $("figure-show-all").addEventListener("click",()=>{
  S.includeScans=!S.includeScans;S.page=0;
  if(!S.includeScans && S.category==="文献与来源图像"){$("figure-category").value="";S.category="";}
  renderGrid();
 });
 $("figure-prev").addEventListener("click",()=>{S.page--;renderGrid();$("figure-grid").scrollIntoView({block:"start"});});
 $("figure-next").addEventListener("click",()=>{S.page++;renderGrid();$("figure-grid").scrollIntoView({block:"start"});});
 $("figure-close").addEventListener("click",()=>$("figure-lightbox").close());
 $("figure-download").addEventListener("click",()=>{if(S.selected)download(S.selected);});
 $("figure-lightbox").addEventListener("click",e=>{if(e.target===$("figure-lightbox"))$("figure-lightbox").close();});
 $("he-original-pages").addEventListener("toggle",()=>{if($("he-original-pages").open)renderHe();});
}
async function show(){
 try{
  const d=await ready();bind();renderGrid();
  await window.JYReader?.attach(d.documents,S.doc||undefined);
  if($("he-original-pages").open)renderHe();
 }catch(e){console.error(e);$("figure-grid").replaceChildren(E("p","figure-empty","资料目录载入失败"));}
}
async function overview(){
 const box=$("featured-figures");if(!box)return;
 try{
  const d=await ready();
  const names=["figure2-1-word-zh.png","FIG3_S12_ERA5_SHEAR_160M_CROSSCHECK_20261109.svg","FIG_S05_03_ROTD_PUBLICATION.svg"];
  const picked=names.map(name=>d.images.find(f=>f.n===name)).filter(Boolean);
  box.replaceChildren(...picked.map(f=>card(f,true)));
 }catch(e){console.error(e);}
}
const modulePics={
 structure:["figure2-1-word-zh.png"],
 windResource:["FIG3_S12_ERA5_SHEAR_160M_CROSSCHECK_20261109.svg"],
 windLoad:["FIG3_S07_REAL_NTM18_MULTILOAD_COINCIDENCE_20261111.svg"],
 seismic:["FIG_S05_03_ROTD_PUBLICATION.svg"],
 coupling:["FIG_S08_ESM_FULLRATE_PAIRED_VECTOR_20261109.svg"],
 fatigue:["FIG4_S10_ETM4_TENSION_DEL4_AZIMUTH_TRADEOFF_20261109.svg"],
 optimization:["FIG1_2026_PUBLISHED_PT_DISPLACEMENT_TRADEOFF_20261108.svg"]
};
const moduleDocs={field:"jiayu-gov",structure:"he-thesis",literature:"he-thesis"};
async function moduleFigures(id,target){
 try{
  const d=await ready();
  const pics=(modulePics[id]||[]).map(n=>d.images.find(f=>f.n===n)).filter(Boolean);
  if(pics.length){
   const block=E("section","detail-panel detail-figures");block.append(E("h2","","研究原图"));
   const grid=E("div","figure-detail-grid");pics.forEach(f=>grid.append(card(f,true)));block.append(grid);
   target.append(block);
  }
  if(moduleDocs[id]){
   const doc=d.documents.find(x=>x.id===moduleDocs[id]);
   if(doc){
    const block=E("section","detail-panel related-document"),button=E("button","related-document-button","阅读："+doc.title);
    button.type="button";button.addEventListener("click",()=>focusDoc(doc.id));
    block.append(E("h2","","相关原始文献"),button);target.append(block);
   }
  }
 }catch(e){console.error(e);}
}
async function focusDoc(id){
 S.doc=id;
 if(location.hash!=="#figures")location.hash="#figures";
 await show();
 await window.JYReader?.select(id);
 $("original-documents")?.scrollIntoView({block:"start",behavior:"smooth"});
}
window.JYFigures={show,overview,moduleFigures,focusDoc};
})();