"use strict";
/** Academic publication navigator. All text from catalog is inserted as textContent. */
const state={catalog:null,view:"overview",group:"全部",query:""};
const $=s=>document.querySelector(s);
function E(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=text;return x;}
function link(url,text,cls){const a=E("a",cls,text);try{const u=new URL(url);if(!["https:","http:"].includes(u.protocol))throw Error("Unsafe link");a.href=u.href;}catch{a.href="#";}a.rel="noopener noreferrer";a.target="_blank";return a;}
function clear(el){el.replaceChildren();}
function statusClass(s){return /现行|已|持续|历史|框架/.test(s)?"good":/待|制定中|需核/.test(s)?"pending":"neutral";}
function go(id){
if(!state.catalog)return;
const modules=state.catalog.modules;
const ordinary=modules.some(m=>m.id===id);
if(!ordinary&&id!=="library"&&id!=="notes"&&id!=="figures")id="overview";
state.view=id;
$("#overview-view").hidden=id!=="overview";
$("#module-view").hidden=!ordinary||id==="overview";
$("#library-view").hidden=id!=="library";
$("#figures-view").hidden=id!=="figures";
$("#notes-view").hidden=id!=="notes";
$("#search-panel").hidden=true;
$("#global-search").value="";
state.query="";
$("#page-title").textContent=id==="figures"?"科研原图":id==="library"?"文件资料":id==="notes"?"论文写作与研究记录":id==="overview"?"科研总览":modules.find(m=>m.id===id)?.title||"科研总览";
$("#nav").querySelectorAll("[data-view]").forEach(b=>{
 b.classList.toggle("active",b.dataset.view===id);
 if(b.dataset.view===id)b.setAttribute("aria-current","page");else b.removeAttribute("aria-current");
});
if(ordinary&&id!=="overview")renderDetail(modules.find(m=>m.id===id));
if(id==="figures")window.JYFigures?.show();
if(id==="library"){const frame=$("#library-frame");if(!frame.getAttribute("src"))frame.src="./library.html?embedded=1#remote";}
if(id==="notes"){const frame=$("#notes-frame");if(!frame.getAttribute("src"))frame.src="../research-notes.html#workflow";}
if(location.hash!=="#"+id)location.hash=id;
closeSidebar();
window.scrollTo({top:0,behavior:"auto"});
}
function closeSidebar(){const sb=$("#sidebar");sb.classList.remove("open");$("#overlay").hidden=true;$("#menu-toggle").setAttribute("aria-expanded","false");}
function renderNav(){const nav=$("#nav");clear(nav);const groups=["总控","研究准备","荷载环境","结构与耦合","学术成果"];for(const g of groups){const sec=E("div","nav-group");sec.append(E("div","nav-heading",g));for(const m of state.catalog.modules.filter(x=>x.group===g)){const b=E("button","nav-link");b.type="button";b.dataset.view=m.id;b.append(E("span","nav-number",m.short),E("span","",m.title));b.addEventListener("click",()=>go(m.id));sec.append(b);}nav.append(sec);}
const tools=E("div","nav-group");tools.append(E("div","nav-heading","资料与写作"));
for(const [id,no,title] of [["figures","16","科研原图 · 图集"],["library","17","文件资料 · 上传下载"],["notes","18","论文写作 · 科研记录"]]){
 const button=E("button","nav-link");button.type="button";button.dataset.view=id;
 button.append(E("span","nav-number",no),E("span","",title));
 button.addEventListener("click",()=>go(id));tools.append(button);
}
nav.append(tools);
}
function renderCounters(){const m=state.catalog.meta;$("#release-version").textContent=m.version;}

function renderCards(){const d=state.catalog;const box=$("#module-grid");clear(box);const filtered=d.modules.filter(x=>state.group==="全部"||x.group===state.group);for(const m of filtered){const card=E("button","module-card");card.type="button";const h=E("div","mod-card-head");h.append(E("span","mod-no",m.short+" / "+m.group),E("span","mod-arrow","↗"));const body=E("div");body.append(E("div","mod-name",m.title),E("div","mod-en",m.en));card.append(h,body);card.addEventListener("click",()=>go(m.id));box.append(card);}}
function renderFilters(){const box=$("#discipline-filters");clear(box);for(const g of ["全部","研究准备","荷载环境","结构与耦合","学术成果"]){const b=E("button","filter-chip"+(g===state.group?" active":""));b.type="button";b.textContent=g;b.addEventListener("click",()=>{state.group=g;renderFilters();renderCards();});box.append(b);}}
function renderRoadmap(){const box=$("#roadmap-grid");clear(box);for(const r of state.catalog.roadmap){const b=E("button","roadmap-card");b.type="button";const top=E("div","roadmap-top");top.append(E("span","roadmap-num",r.n));b.append(top,E("h3","",r.title),E("p","",r.text));b.addEventListener("click",()=>go(r.module));box.append(b);}}
function renderOverviewData(){const data=$("#featured-data");clear(data);for(const d of state.catalog.datasets){const row=E("div","evidence-item"),copy=E("div");copy.append(E("strong","",d.name),E("small","",d.domain+" · "+d.status));row.append(copy,link(d.url,"↗"));data.append(row);}const reports=$("#featured-reports");clear(reports);for(const [i,r] of state.catalog.reports.entries()){const a=link(r.url,"","report-link");a.append(E("span","",String(i+1).padStart(2,"0")),E("strong","",r.name));reports.append(a);}}
function makePanel(title,kicker){const panel=E("section","detail-panel");panel.append(E("span","panel-kicker",kicker),E("h2","",title));return panel;}
function rows(panel,arr){arr.forEach((s,i)=>{const p=E("div","bullet-block");p.append(E("span","bullet-number",String(i+1).padStart(2,"0")),E("span","",s));panel.append(p);});}
function sourceList(panel,arr){for(const x of arr){const row=E("div","source-item");row.append(link(x.url,x.label),E("span","",({official:"官方来源",standard:"规范索引",template:"报告模板",evidence:"研究资料"})[x.kind]||"资料"));panel.append(row);}}
function renderDetail(m){$("#module-tag").textContent=m.group+" / "+m.scope;const s=$("#module-stage");s.className="stage-chip "+statusClass(m.stage);s.textContent=m.stage;$("#module-english").textContent=m.en;$("#module-title").textContent=m.title;$("#module-description").textContent=m.brief;$("#module-code").textContent=m.short;const body=$("#module-body");clear(body);const left=E("div","module-column"),right=E("div","module-column");
const q=makePanel("研究问题","RESEARCH QUESTIONS");rows(q,m.questions);left.append(q);
const checks=makePanel("研究方法与指标","METHOD & QUALITY GATES");rows(checks,m.checks);left.append(checks);
const sources=makePanel("研究资料","PRIMARY LINKS");sourceList(sources,m.links);right.append(sources);
const outs=makePanel("成果文件","DELIVERABLES");for(const s of m.outputs)outs.append(E("div","deliverable-item",s));right.append(outs);
body.append(left,right);
window.JYFigures?.moduleFigures(m.id,left);
if(m.id==="literature"){const p=makePanel("现行标准与制订项目","OFFICIAL STANDARDS");for(const n of state.catalog.standards){const item=E("div","source-item");const name=link(n.url,n.name+" · "+n.sub);item.append(name,E("span","",n.kind));p.append(item);}left.append(p);}
if(m.id==="library"){const p=makePanel("数据与原始证据目录","SOURCE REGISTRY");sourceList(p,state.catalog.datasets.map(x=>({label:x.name,url:x.url,kind:"evidence"})));left.append(p);}
if(m.id==="reports"){const p=makePanel("学术报告模板库","ACADEMIC REPORT TEMPLATES");sourceList(p,state.catalog.reports.map(x=>({...x,label:x.name,kind:"template"})));left.append(p);}
}
function search(){const q=$("#global-search").value.trim().toLowerCase();state.query=q;const box=$("#search-panel");if(!q){box.hidden=true;if(state.view==="overview")$("#overview-view").hidden=false;else if(state.view==="figures")$("#figures-view").hidden=false;else if(state.view==="library")$("#library-view").hidden=false;else if(state.view==="notes")$("#notes-view").hidden=false;else $("#module-view").hidden=false;return;}$("#overview-view").hidden=true;$("#module-view").hidden=true;$("#library-view").hidden=true;$("#notes-view").hidden=true;$("#figures-view").hidden=true;box.hidden=false;clear(box);box.append(E("span","section-kicker","GLOBAL RESEARCH SEARCH"),E("h2","search-title","资料检索"));const matches=[];for(const m of state.catalog.modules){if((m.title+" "+m.en+" "+m.brief+" "+m.checks.join(" ")).toLowerCase().includes(q))matches.push({title:m.title,sub:m.brief,kind:"专题",action:()=>go(m.id)});}
for(const r of state.catalog.reports){if(r.name.toLowerCase().includes(q))matches.push({title:r.name,sub:"报告模板 · GitHub Markdown",kind:"模板",url:r.url});}
for(const x of [...state.catalog.datasets,...state.catalog.standards]){if((x.name+" "+(x.sub||"")+" "+(x.desc||"")+" "+(x.domain||"")).toLowerCase().includes(q))matches.push({title:x.name,sub:x.desc||x.sub||"",kind:"证据",url:x.url});}
if(!matches.length){box.append(E("div","empty-results","未找到相关资料。"));return;}
for(const match of matches.slice(0,28)){const row=E(match.url?"a":"button","search-result");if(!match.url)row.type="button";const content=E("span");content.append(E("strong","",match.title),E("small","",match.sub));row.append(content,E("span","right",match.kind+" ↗"));if(match.url){try{row.href=new URL(match.url).href;row.target="_blank";row.rel="noopener noreferrer";}catch{row.href="#";}}else row.addEventListener("click",match.action);box.append(row);}
}
function bind(){const menu=$("#menu-toggle");menu.addEventListener("click",()=>{const open=!$("#sidebar").classList.contains("open");$("#sidebar").classList.toggle("open",open);$("#overlay").hidden=!open;menu.setAttribute("aria-expanded",String(open));});$("#overlay").addEventListener("click",closeSidebar);$("#start-modules").addEventListener("click",()=>$("#module-directory").scrollIntoView({behavior:"smooth"}));$("#global-search").addEventListener("input",search);document.addEventListener("keydown",e=>{if(e.key==="/"&&!["INPUT","TEXTAREA"].includes(document.activeElement.tagName)){e.preventDefault();$("#global-search").focus();}if(e.key==="Escape"){if($("#sidebar").classList.contains("open"))closeSidebar();else{$("#global-search").value="";search();$("#global-search").blur();}}});document.querySelectorAll('[data-unified-view]').forEach(a=>a.addEventListener("click",e=>{e.preventDefault();go(a.dataset.unifiedView);}));
document.querySelectorAll("[data-open-document]").forEach(b=>b.addEventListener("click",()=>window.JYFigures?.focusDoc(b.dataset.openDocument)));

document.querySelectorAll("[data-notes-section]").forEach(b=>b.addEventListener("click",()=>{
 const page=b.dataset.notesSection;
 document.querySelectorAll("[data-notes-section]").forEach(item=>item.classList.toggle("selected",item===b));
 const frame=$("#notes-frame");frame.src="../research-notes.html#"+page;
}));
window.addEventListener("hashchange",()=>{const id=decodeURIComponent(location.hash.slice(1)||"overview");if(state.catalog&&id!==state.view)go(id);});}
async function init(){bind();try{const res=await fetch("./data/catalog.json",{cache:"no-store"});if(!res.ok)throw Error("HTTP "+res.status);const c=await res.json();if(!c||!Array.isArray(c.modules)||!Array.isArray(c.datasets)||!Array.isArray(c.reports))throw Error("Invalid catalog");state.catalog=c;$("#command-link").href=c.meta.command;renderNav();renderCounters();renderFilters();renderCards();window.JYFigures?.overview();go(decodeURIComponent(location.hash.slice(1)||"overview"));}catch(err){const main=$("#overview-view");clear(main);const section=E("div","empty-results","资料目录加载失败。");main.append(section);console.error("Catalog unavailable",err);}}
init();