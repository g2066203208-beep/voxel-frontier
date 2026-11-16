"use strict";
/* T091: full six-chapter manuscript text displayed within same study workspace. */
(function(){
const S={manifest:null,current:"01"};
function E(t,c,value){let el=document.createElement(t);if(c)el.className=c;if(value!==undefined)el.textContent=String(value);return el}
function safeInline(text,container){
 text=text.replace(/\\\x60/g,String.fromCharCode(96));
 const quote=String.fromCharCode(96);
 const parts=new RegExp("(\\*\\*[^*]+\\*\\*|\\*[^*\\n]+\\*|"+quote+"[^"+quote+"]+"+quote+"|\\[[^\\]]+\\]\\([^)]+\\))","g");
 let offset=0,m;
 while((m=parts.exec(text))!==null){
  if(m.index>offset)container.append(document.createTextNode(text.slice(offset,m.index)));
  const token=m[0];let n;
  if(token.startsWith("**"))n=E("strong","",token.slice(2,-2));
  else if(token.startsWith("*"))n=E("em","",token.slice(1,-1));
  else if(token.startsWith(quote))n=E("code","",token.slice(1,-1));
  else{const at=token.indexOf("]("),label=token.slice(1,at),url=token.slice(at+2,-1);
   n=E("span","thesis-source-reference",label);n.title=url;
  }
  container.append(n);offset=parts.lastIndex;
 }
 if(offset<text.length)container.append(document.createTextNode(text.slice(offset)));
}
function figFromLine(text, seen, fragment){
 const regex=/!?\[([^\]]+)\]\(\.\.\/figures\/([A-Za-z0-9_.-]+\.svg)\)/g;let m;
 while((m=regex.exec(text))!==null){
  if(seen.has(m[2]))continue;seen.add(m[2]);
  const figure=E("figure","thesis-inline-figure");
  const image=E("img");image.src="./figures/manuscript/final-thesis/figures/"+encodeURIComponent(m[2]);
  image.alt=m[1];image.loading="lazy";image.decoding="async";
  const caption=E("figcaption","",m[1]+" · 原研究分支SVG / 本站原始图集");
  image.addEventListener("error",()=>{image.hidden=true;caption.textContent=m[1]+" · 原图未入当前主站图库，不能使用替代图"});
  figure.append(image,caption);fragment.append(figure);
 }
}
function markdown(text,host){
 const lines=text.replace(/\r/g,"").split("\n"),result=document.createDocumentFragment(),seen=new Set();
 const codeFence=String.fromCharCode(96).repeat(3);
 let i=0;
 function para(s){const p=E("p");safeInline(s,p);result.append(p);figFromLine(s,seen,result)}
 while(i<lines.length){
  let t=lines[i].trim();
  if(!t){i++;continue}
  if(t.startsWith(codeFence)||t.startsWith("~~~")){
   const fence=t.slice(0,3),body=[];i++;
   while(i<lines.length&&!lines[i].trim().startsWith(fence)){body.push(lines[i]);i++}
   if(i<lines.length)i++;
   const pre=E("pre","thesis-code");pre.append(E("code","",body.join("\n")));result.append(pre);continue
  }
  if(t==="\\["||t==="$$"){
   const until=t==="\\["?"\\]":"$$",content=[];i++;
   while(i<lines.length&&lines[i].trim()!==until){content.push(lines[i]);i++}
   if(i<lines.length)i++;
   result.append(E("pre","thesis-equation",content.join("\n")));continue
  }
  const heading=t.match(/^(#{1,6})\s+(.+)/);
  if(heading){const lvl=Math.min(6,heading[1].length+1),h=E("h"+lvl,"thesis-h"+lvl);
   safeInline(heading[2],h);result.append(h);i++;continue}
  if(/^([-_*])\1{2,}$/.test(t)){result.append(E("hr"));i++;continue}
  if(t.startsWith("|")&&i+1<lines.length&&/^\|?[\s:|-]+\|?$/.test(lines[i+1].trim())){
   const wrap=E("div","thesis-table-wrap"),table=E("table","thesis-table"),head=E("thead"),tr=E("tr");
   const split=x=>x.trim().replace(/^\||\|$/g,"").split("|");
   split(t).forEach(x=>{const cell=E("th");safeInline(x.trim(),cell);tr.append(cell)});
   head.append(tr);table.append(head);i+=2;const body=E("tbody");
   while(i<lines.length&&lines[i].trim().startsWith("|")){
    const row=E("tr");split(lines[i]).forEach(x=>{const cell=E("td");safeInline(x.trim(),cell);row.append(cell)});
    body.append(row);i++
   }table.append(body);wrap.append(table);result.append(wrap);continue
  }
  if(/^>\s?/.test(t)){
   const blocks=[];while(i<lines.length&&lines[i].trim().startsWith(">")){blocks.push(lines[i].trim().replace(/^>\s?/,""));i++}
   const block=E("blockquote","thesis-quote");safeInline(blocks.join(" "),block);result.append(block);continue
  }
  if(/^[-*]\s+/.test(t)||/^\d+\.\s+/.test(t)){
   const ordered=/^\d+\.\s+/.test(t),list=E(ordered?"ol":"ul");
   while(i<lines.length&&(/^[-*]\s+/.test(lines[i].trim())||/^\d+\.\s+/.test(lines[i].trim()))){
    const li=E("li");safeInline(lines[i].trim().replace(/^([-*]|\d+\.)\s+/,""),li);list.append(li);i++
   }result.append(list);continue
  }
  const group=[t];i++;
  while(i<lines.length&&lines[i].trim()&&!/^(#|>|[-*]\s|\d+\.\s|\||\\\[|\$\$)/.test(lines[i].trim())&&
   !lines[i].trim().startsWith(codeFence)){group.push(lines[i].trim());i++}
  para(group.join(" "));
 }
 host.replaceChildren(result);
 window.JYMathTypeset?.typeset(host);
}
async function show(container){
 if(!container)return;
 container.replaceChildren(E("p","thesis-loading","读取六章真实原文中…"));
 try{
  if(!S.manifest){
   const r=await fetch("./primary-data/manifest.json",{cache:"no-store"});if(!r.ok)throw Error("全文目录不可读");
   S.manifest=await r.json();if(S.manifest.chapters.length!==6)throw Error("论文六章来源不完整");
  }
  const m=S.manifest,toolbar=E("div","thesis-chapter-tabs"),meta=E("p","thesis-source-line");
  const article=E("article","thesis-full-article");
  async function choose(id){
   S.current=id;
   toolbar.querySelectorAll("button").forEach(b=>b.classList.toggle("selected",b.dataset.chapter===id));
   const d=m.chapters.find(x=>x.id===id);if(!d)return;
   meta.textContent="原文 "+d.provenance.path+" · SHA256 "+d.provenance.sha256+" · 版本 "+m.research_commit.slice(0,12);
   article.replaceChildren(E("p","thesis-loading","读取本章完整原始文字和内嵌科研图…"));
   try{
    const r=await fetch(d.src,{cache:"no-store"});if(!r.ok)throw Error("原文HTTP "+r.status);
    markdown(await r.text(),article);
   }catch(e){article.replaceChildren(E("p","evidence-error","原文不可读取："+e.message))}
  }
  m.chapters.forEach(d=>{
   const b=E("button","thesis-chapter-tab",d.id+" · "+d.title);b.type="button";b.dataset.chapter=d.id;
   b.addEventListener("click",()=>choose(d.id));toolbar.append(b)
  });
  container.replaceChildren(toolbar,meta,article);
  await choose(S.current);
 }catch(e){container.replaceChildren(E("p","evidence-error","论文原文加载失败："+e.message))}
}
window.JYThesisInline={show,renderMarkdown:markdown};
})();