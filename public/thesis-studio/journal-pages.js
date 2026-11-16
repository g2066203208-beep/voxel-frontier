"use strict";
/* Original page gallery: only byte-identical authorized article pages produced by documented CI. */
(function(){
const S={data:null,loading:null};
const E=(tag,cls,text)=>{
 const x=document.createElement(tag);
 if(cls)x.className=cls;
 if(text!==undefined)x.textContent=String(text);
 return x;
};
function displayStatus(p){
 if(p.pages.length)return p.pages.length+"页原文 · 逐页显示";
 if(p.status==="licensed_pending_pages")return "已确认CC BY 许可 · 原版整页图未归档成功";
 if(p.status==="restricted_fulltext")return "出版全文版权受限 · 不公开整页截图";
 if(p.status==="open_text_pdf_unverified")return "出版方开放获取 · 原版PDF和许可仍需核对";
 return "全文可读 · 公开再发布许可未确认";
}
async function load(){
 if(S.data)return S.data;
 if(!S.loading)S.loading=fetch("./data/development-paper-pages.json",{cache:"no-store"})
  .then(r=>{if(!r.ok)throw Error("原文页图目录HTTP "+r.status);return r.json();})
  .then(d=>{
    if(d.schema!==1||!Array.isArray(d.articles)||d.articles.length!==8)
       throw Error("原文页图证据索引不完整");
    if(d.articles.some(p=>!p.id||!p.title||!p.doi||!Array.isArray(p.pages)))
       throw Error("原文页图元数据缺失");
    for(const a of d.articles){
      if(a.pages.length&&!a.license.startsWith("CC BY"))
        throw Error("未授权页面不得公开图像:"+a.id);
      for(const path of a.pages)
        if(!/^\.\/journal-pages\/[a-z0-9-]+\/page-\d{3}\.jpg$/.test(path))
          throw Error("原文图片路径身份异常:"+path);
    }
    return S.data=d;
  }).catch(e=>{S.loading=null;throw e;});
 return S.loading;
}
function paper(p){
 const item=E("article","journal-paper");
 const head=E("div","journal-paper-head");
 head.append(E("span","journal-paper-code",p.id.toUpperCase()+" · "+p.year),
             E("span","journal-paper-state",displayStatus(p)));
 item.append(head,E("h3","",p.title));
 item.append(E("p","journal-paper-meta",p.authors+" · "+p.journal));
 item.append(E("p","journal-paper-method",p.method));
 item.append(E("p","journal-paper-license","DOI "+p.doi+" · "+p.license));
 if(p.pages.length){
   const gallery=E("div","journal-page-stream");
   p.pages.forEach((source,i)=>{
     const page=E("figure","journal-page");
     const image=E("img","journal-original-sheet");
     image.src=source;image.loading="lazy";image.decoding="async";
     image.alt=p.authors+" 论文原始第"+(i+1)+"页，完整页面截图";
     const err=E("p","journal-page-error","第"+(i+1)+"页原图加载失败，请核对静态归档");
     err.hidden=true;image.addEventListener("error",()=>{image.hidden=true;err.hidden=false});
     const caption=E("figcaption","journal-page-caption",p.id+" · 原始PDF第 "+(i+1)+" / "+p.pages.length+" 页 · "+p.license);
     page.append(image,err,caption);
     gallery.append(page);
   });
   item.append(gallery);
 }else{
   item.append(E("p","journal-no-pages","该论文尚无获授权并验证来源的整页图像，未使用伪造或替代截图。"));
 }
 return item;
}
async function show(root){
 if(!root)return;
 let section=document.getElementById("journal-original-pages");
 if(!section){
  section=E("section","journal-original-pages");
  section.id="journal-original-pages";
  const heading=E("header","journal-page-intro");
  heading.append(E("span","section-kicker","JOURNAL ORIGINAL PAGE ATLAS"),
                 E("h2","","接缝与二次开发参考文献 · 原文逐页阅读"),
                 E("p","","已取得公开再发布许可且通过原版PDF校验的论文会在这里连续显示每一页。其他论文保留精确作者、DOI、算法与许可状态；不会把付费/受限整篇文章截图公开上传。"));
  section.append(heading);
  const list=E("div","journal-paper-list");list.id="journal-paper-list";section.append(list);
 }
 if(section.parentElement!==root)root.prepend(section);
 try {
  const d=await load();
  section.querySelector("#journal-paper-list").replaceChildren(...d.articles.map(paper));
 }catch(e){
  section.querySelector("#journal-paper-list").replaceChildren(E("p","journal-page-error","原始文献索引加载失败："+e.message));
  console.error(e);
 }
}
window.JYOriginalPages={show};
})();