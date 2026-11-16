"use strict";
/* T091: original GitHub research text and tables opened inside ONE studio view. */
(function(){
const ALLOWED_EXT=/\.(md|txt|csv|tsv|json|svg)$/i;
function E(t,c,x){const z=document.createElement(t);if(c)z.className=c;if(x!==undefined)z.textContent=String(x);return z}
function sourceUrl(url){
 let o;try{o=new URL(url)}catch{return null}
 if(o.protocol!=="https:"||o.hostname!=="github.com")return null;
 const bits=o.pathname.split("/").filter(Boolean);
 if(bits[0]!=="g2066203208-beep"||bits[1]!=="voxel-frontier"||bits[2]!=="blob")return null;
 let branch,path;
 if(bits[3]==="main"){branch="main";path=bits.slice(4)}
 else if(bits[3]==="research"&&bits[4]==="t080-seismic-integration-gates-20261022"){
  branch="research/t080-seismic-integration-gates-20261022";path=bits.slice(5)
 }else return null;
 if(!path.length||!ALLOWED_EXT.test(path[path.length-1])||path.some(s=>s===".."))return null;
 return {url:"https://raw.githubusercontent.com/g2066203208-beep/voxel-frontier/"+branch+"/"+path.map(encodeURIComponent).join("/"),
  path:branch+":"+path.join("/"),ext:path[path.length-1].split(".").pop().toLowerCase()};
}
function tabulate(content,separator,host){
 const lines=content.replace(/^\uFEFF/,"").split(/\r?\n/).filter(Boolean);
 const parse=(line)=>{
  if(separator==="\t")return line.split("\t");
  let parts=[],field="",inside=false;
  for(let i=0;i<line.length;i++){const x=line[i];
   if(x==='"'){if(inside&&line[i+1]==='"'){field+='"';i++}else inside=!inside}
   else if(x===","&&!inside){parts.push(field);field=""}else field+=x
  }parts.push(field);return parts
 };
 const names=parse(lines.shift()||""),rows=lines.map(parse);
 const main=E("div","evidence-table-wrap"),toolbar=E("div","evidence-table-toolbar");
 const input=E("input");input.placeholder="检索原文全部行";input.type="search";
 const count=E("span","evidence-page-count"),prev=E("button","evidence-pager","上一页"),next=E("button","evidence-pager","下一页");
 const scroll=E("div","evidence-table-scroll"),table=E("table","evidence-table");
 let term="",page=0;
 function paint(){
  const q=rows.filter(r=>!term||r.some(v=>v.toLowerCase().includes(term)));const n=80;
  page=Math.min(page,Math.max(0,Math.ceil(q.length/n)-1));
  const from=page*n,part=q.slice(from,from+n);
  const h=E("thead"),tr=E("tr");names.forEach(x=>tr.append(E("th","",x)));h.append(tr);
  const b=E("tbody");part.forEach(r=>{const tr=E("tr");names.forEach((_,j)=>tr.append(E("td","",r[j]||"")));b.append(tr)});
  table.replaceChildren(h,b);count.textContent=q.length+"行 · "+(from+1)+"—"+Math.min(q.length,from+n);
  prev.disabled=page===0;next.disabled=from+n>=q.length;
 }
 input.addEventListener("input",()=>{page=0;term=input.value.toLowerCase();paint()});
 prev.addEventListener("click",()=>{page--;paint()});next.addEventListener("click",()=>{page++;paint()});
 toolbar.append(input,count,prev,next);scroll.append(table);main.append(toolbar,scroll);
 host.replaceChildren(main);paint();
}
async function open(url,title,root){
 const spec=sourceUrl(url);if(!spec)return false;
 if(!root)return false;
 let shell=document.getElementById("original-source-inline-reader");
 if(!shell){shell=E("section","source-inline-detail");shell.id="original-source-inline-reader";}
 if(shell.parentElement!==root)root.prepend(shell);
 shell.replaceChildren(E("p","evidence-hint","正在核对并读取原始研究文档…"));
 try{
  const r=await fetch(spec.url,{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);
  if(Number(r.headers.get("content-length")||0)>6*1024*1024)throw Error("文件过大，仅限6MB内的原文");
  const content=await r.text();
  if(content.length>6*1024*1024)throw Error("原文件超出浏览器内联阅读上限");
  const head=E("header","evidence-reader-head");
  head.append(E("span","section-kicker","ORIGINAL REPOSITORY DOCUMENT · INLINE"),
    E("h2","",title),E("p","",spec.path));
  const body=E("div","source-inline-body");
  if(spec.ext==="md"){
   const article=E("article","thesis-full-article");
   const render=window.JYThesisInline?.renderMarkdown;
   if(!render)throw Error("论文原文阅读器尚未加载");
   render(content,article);body.append(article);
  }else if(spec.ext==="csv"||spec.ext==="tsv"){
   tabulate(content,spec.ext==="tsv"?"\t":",",body);
  }else if(spec.ext==="json"){
   try{body.append(E("pre","thesis-code",JSON.stringify(JSON.parse(content),null,2)))}
   catch{body.append(E("pre","thesis-code",content))}
  }else if(spec.ext==="svg"){
   const figure=E("figure","thesis-inline-figure"),img=E("img");
   img.src=spec.url;img.alt=title;img.loading="lazy";
   figure.append(img,E("figcaption","",spec.path));body.append(figure);
  }else body.append(E("pre","thesis-code",content));
  shell.replaceChildren(head,body);shell.scrollIntoView({behavior:"smooth",block:"start"});
 }catch(e){shell.replaceChildren(E("p","evidence-error",title+"：站内原文暂时无法读取（"+e.message+"）。"))}
 return true;
}
window.JYSourceInline={supports:url=>!!sourceUrl(url),open};
})();