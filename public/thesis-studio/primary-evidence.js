"use strict";
/* T091: source-preserving, no-redirect scientific charts and full in-page records. */
(function(){
const S={manifest:null,promise:null,cache:new Map(),group:"全部",selected:"era5-wind-bins",window:160,start:0};
const NS="http://www.w3.org/2000/svg";
function E(t,c,x){const n=document.createElement(t);if(c)n.className=c;if(x!==undefined)n.textContent=String(x);return n}
function G(t,p={},val){const n=document.createElementNS(NS,t);Object.entries(p).forEach(([k,v])=>n.setAttribute(k,String(v)));if(val!==undefined)n.textContent=String(val);return n}
function f(n){const x=Number(n);if(!Number.isFinite(x))return String(n);if(x===0)return "0";if(Math.abs(x)<.0001)return x.toExponential(2);return x.toLocaleString("en-US",{maximumSignificantDigits:5})}
function err(host,s){host.append(E("p","evidence-error",s))}
async function load(){
 if(S.manifest)return S.manifest;
 if(!S.promise)S.promise=fetch("./primary-data/manifest.json",{cache:"no-store"})
  .then(r=>{if(!r.ok)throw Error("原始证据索引 HTTP "+r.status);return r.json()})
  .then(d=>{if(d.schema!==1||d.datasets?.length!==9||d.chapters?.length!==6)throw Error("原始证据源表不完整");return S.manifest=d})
  .catch(e=>{S.promise=null;throw e});
 return S.promise;
}
function csv(text){
 const lines=text.replace(/^\uFEFF/,"").split(/\r?\n/).filter(Boolean);
 function row(line){let a=[],v="",quote=false;for(let i=0;i<line.length;i++){let c=line[i];if(c==='"'){if(quote&&line[i+1]==='"'){v+='"';i++}else quote=!quote}else if(c===","&&!quote){a.push(v);v=""}else v+=c}a.push(v);return a}
 const keys=row(lines.shift()||"");
 const records=lines.map(line=>{let fields=row(line);if(fields.length!==keys.length)throw Error("CSV字段列宽有误");let obj={};keys.forEach((k,i)=>obj[k]=fields[i]);return obj});
 return {keys,records};
}
async function read(id,src,count){
 if(S.cache.has(id))return S.cache.get(id);
 const r=await fetch(src,{cache:"no-store"});if(!r.ok)throw Error("数据不可读取 "+id+" (HTTP "+r.status+")");
 const o=csv(await r.text());if(o.records.length!==count)throw Error("数据条数不符："+id);
 S.cache.set(id,o);return o;
}
function head(t,subtitle){
 const el=E("header","evidence-reader-head");
 el.append(E("span","section-kicker","ORIGINAL SCIENTIFIC DATA / SOURCE LOCK"),E("h2","",t),E("p","",subtitle));return el
}
function src(d){
 const block=E("div","evidence-provenance");
 block.append(E("span","","原始文件 "+d.provenance.path),
 E("span","","Git blob "+d.provenance.git_blob_sha.slice(0,16)+" · SHA256 "+d.provenance.sha256));
 return block;
}
function plot(records,d){
 if(!d.x||!d.y)return E("p","evidence-hint","原表没有指定唯一有效的图表轴，全部字段见下方完整数据表。");
 const values=records.map((r,i)=>({x:r[d.x],a:Number(r[d.y]),b:d.y2?Number(r[d.y2]):null,i})).filter(r=>Number.isFinite(r.a)&&(!d.y2||Number.isFinite(r.b)));
 if(!values.length)return E("p","evidence-hint","来源中没有可绘制的数值。");
 const width=940,height=280,L=66,T=18,RIGHT=20,BOT=43,cw=width-L-RIGHT,ch=height-T-BOT;
 const isNumber=values.every(r=>r.x!==""&&Number.isFinite(Number(r.x)));
 const xarr=values.map(r=>Number(r.x)),xmin=isNumber?Math.min(...xarr):0,xmax=isNumber?Math.max(...xarr):Math.max(1,values.length-1);
 const x=(o,i)=>L+(isNumber?(Number(o.x)-xmin)/(xmax-xmin||1):(i+.5)/values.length)*cw;
 const all=values.flatMap(o=>d.y2?[o.a,o.b]:[o.a]);
 const lo=Math.min(0,...all),hi=Math.max(.00000001,...all),p=(hi-lo)*.07||1;
 const y=v=>T+(hi+p-v)/(hi-lo+2*p)*ch,baseline=y(0);
 const svg=G("svg",{class:"evidence-plot",viewBox:"0 0 "+width+" "+height,role:"img","aria-label":d.title+" 原始数值图"});
 for(let i=0;i<=4;i++){const value=lo-p+(hi-lo+2*p)*i/4,yy=y(value);
  svg.append(G("line",{x1:L,y1:yy,x2:width-RIGHT,y2:yy,stroke:"#e2ebea"}),G("text",{x:L-8,y:yy+4,"text-anchor":"end",class:"evidence-tick"},f(value)))}
 svg.append(G("line",{x1:L,y1:T,x2:L,y2:height-BOT,stroke:"#94aba7"}));
 const colors=["#137a80","#c98545"],lineMode=isNumber&&values.length>25;
 [d.y,d.y2].filter(Boolean).forEach((key,j)=>{
  if(lineMode){const points=values.map((o,i)=>(i?"L":"M")+x(o,i).toFixed(2)+","+y(j?o.b:o.a).toFixed(2)).join(" ");
   svg.append(G("path",{d:points,stroke:colors[j],fill:"none","stroke-width":"2.6","stroke-linejoin":"round"}));
  }else values.forEach((o,i)=>{
   const val=j?o.b:o.a,xx=x(o,i),ww=Math.max(2,cw/values.length/(d.y2?2.8:1.5));
   const yv=y(val),rect=G("rect",{x:xx+(j-(d.y2?.5:0))*ww-ww*.44,y:Math.min(yv,baseline),width:ww*.86,
    height:Math.max(1,Math.abs(yv-baseline)),fill:colors[j],rx:"1"});
   rect.append(G("title",{},o.x+" / "+key+": "+val));svg.append(rect);
  });
 });
 for(let i=0;i<values.length;i+=Math.max(1,Math.ceil(values.length/8))){
  let o=values[i];svg.append(G("text",{x:x(o,i),y:height-BOT+18,class:"evidence-tick","text-anchor":"middle"},String(o.x).slice(0,12)))}
 const legend=E("div","evidence-legend");[d.y,d.y2].filter(Boolean).forEach((k,i)=>{
  const a=E("span","",k);a.style.setProperty("--series",colors[i]);legend.append(a)});
 const wrap=E("div","evidence-chart");wrap.append(svg,legend);return wrap
}
function fullTable(data,host,pageSize=100){
 const {keys,records}=data;let page=0,term="";
 const area=E("div","evidence-table-wrap"),toolbar=E("div","evidence-table-toolbar");
 const search=E("input");search.type="search";search.placeholder="检索此原表全部记录";search.setAttribute("aria-label","检索来源表格");
 const text=E("span","evidence-page-count"),prev=E("button","evidence-pager","前一页"),next=E("button","evidence-pager","后一页");
 const scroll=E("div","evidence-table-scroll"),table=E("table","evidence-table");
 function render(){
  let found=term?records.filter(r=>keys.some(k=>String(r[k]).toLowerCase().includes(term))):records;
  page=Math.min(page,Math.max(0,Math.ceil(found.length/pageSize)-1));
  const first=page*pageSize,slice=found.slice(first,first+pageSize);
  const thead=E("thead"),hrow=E("tr");keys.forEach(k=>hrow.append(E("th","",k)));thead.append(hrow);
  const body=E("tbody");slice.forEach(r=>{let row=E("tr");keys.forEach(k=>row.append(E("td","",r[k])));body.append(row)});
  table.replaceChildren(thead,body);
  text.textContent=found.length.toLocaleString()+"条 · 显示 "+(found.length?first+1:0)+"—"+Math.min(found.length,first+pageSize);
  prev.disabled=page===0;next.disabled=first+pageSize>=found.length;
 }
 search.addEventListener("input",()=>{term=search.value.trim().toLowerCase();page=0;render()});
 prev.addEventListener("click",()=>{page--;render()});next.addEventListener("click",()=>{page++;render()});
 toolbar.append(search,text,prev,next);scroll.append(table);area.append(toolbar,scroll);host.append(area);render()
}
async function dataset(d,host){
 host.replaceChildren(head(d.title,d.note));
 try{
  const o=await read(d.id,d.src,d.n);host.append(src(d),plot(o.records,d));fullTable(o,host)
 }catch(e){err(host,"原始表格校验失败："+e.message)}
}
async function wave(w,host){
 host.replaceChildren(head("ESM原始三分量地震加速度时程",
  "IT-2012-0008 / NVL · HNE、HNN、HNZ同步 · 单位m/s²；未经场址目标谱匹配，不能视为正式设计地震波。"));
 if(!w.src){
  const original=E("figure","thesis-inline-figure"),img=E("img");
  img.src="./figures/manuscript/final-thesis/figures/FIG_S08_04_ESM_REAL_3COMP_ACCELERATION_SOURCE_QC.svg";
  img.alt="已归档ESM源级真实HNE HNN HNZ三分量加速度原始质控图";img.loading="lazy";
  img.decoding="async";
  const note=E("figcaption","",
  "已归档的真实ESM三分量处理波源级QC原始SVG · 原图SHA256对应研究证据台账；并非设计地震波或158m结构响应");
  img.addEventListener("error",()=>{img.hidden=true;note.textContent="源级原图加载失败，拒绝使用替代图"});
  original.append(img,note);
  host.append(original);
  err(host,"32,040×3全量原始数值目前尚未完成严格SHA一致性归档："+w.warning);
  return
 }
 host.append(E("p","evidence-wave-note",w.source+" · "+w.license+" · "+w.status+" · SHA256 "+w.csv_sha256));
 try{
  const data=await read("full-esm-wave",w.src,w.rows);
  const panel=E("div","evidence-wave-plot"),controls=E("div","evidence-wave-controls"),duration=E("select"),start=E("input"),readout=E("span");
  [160,40,20,10,5,2].forEach(a=>{let o=E("option","",a+"秒观察范围");o.value=a;duration.append(o)});
  duration.value=String(S.window);start.type="range";start.min="0";start.max=String(Math.max(0,160-S.window));start.step=".5";start.value=S.start;
  controls.append(duration,start,readout);
  function repaint(){
   S.window=Number(duration.value);S.start=Math.min(Number(start.value),Math.max(0,160-S.window));
   start.max=String(Math.max(0,160-S.window));start.value=S.start;
   readout.textContent=S.start.toFixed(1)+"—"+(S.start+S.window).toFixed(1)+"s";
   const w=950,h=280,L=64,R=12,TOP=17,BOT=36,ww=w-L-R,hh=h-TOP-BOT;
   const part=data.records.filter(r=>Number(r.time_s)>=S.start&&Number(r.time_s)<=S.start+S.window);
   const keys=["HNE_acc_m_s2","HNN_acc_m_s2","HNZ_acc_m_s2"];
   const ymax=Math.max(.000001,...part.flatMap(r=>keys.map(k=>Math.abs(Number(r[k])))));
   const y=v=>TOP+hh*(ymax-v)/(2*ymax);
   const image=G("svg",{class:"evidence-plot",viewBox:"0 0 "+w+" "+h,role:"img","aria-label":"源记录三分量同步加速度包络"});
   image.append(G("line",{x1:L,y1:y(0),x2:w-R,y2:y(0),stroke:"#9caaa9","stroke-dasharray":"4 4"}));
   for(let j=0;j<=4;j++)image.append(G("text",{x:L-7,y:TOP+hh*j/4+4,class:"evidence-tick","text-anchor":"end"},f(ymax*(1-2*j/4))));
   const colors=["#16818a","#d28b42","#8970b9"];
   keys.forEach((key,index)=>{
    const groups=Array.from({length:750},()=>({min:Infinity,max:-Infinity}));
    part.forEach(r=>{const i=Math.min(749,Math.max(0,Math.floor((Number(r.time_s)-S.start)/S.window*750)));
      const val=Number(r[key]);groups[i].min=Math.min(groups[i].min,val);groups[i].max=Math.max(groups[i].max,val)});
    groups.forEach((b,i)=>{if(!Number.isFinite(b.min))return;const x=L+ww*(i+.5)/750;
     image.append(G("line",{x1:x,y1:y(b.min),x2:x,y2:y(b.max),stroke:colors[index],"stroke-width":.9,opacity:.78}))});
   });
   for(let i=0;i<=5;i++)image.append(G("text",{x:L+ww*i/5,y:h-BOT+18,class:"evidence-tick","text-anchor":"middle"},f(S.start+S.window*i/5)+"s"));
   panel.replaceChildren(image);const leg=E("div","evidence-legend");keys.forEach((k,i)=>{let t=E("span","",k);t.style.setProperty("--series",colors[i]);leg.append(t)});panel.append(leg);
  }
  duration.addEventListener("change",repaint);start.addEventListener("input",repaint);repaint();
  host.append(controls,panel,E("h3","evidence-complete-heading","32,040行真实原始采样 · 全部可在本页检索查看"));
  fullTable(data,host,100);
 }catch(e){err(host,"原始加速度数据加载失败："+e.message)}
}
async function model(d,host){
 host.replaceChildren(head("BF1历史工程92项设置全集","2026-11-14 Codex转录快照；不是R6当前原始模型。"));
 try{
  const response=await fetch(d.src);if(!response.ok)throw Error("HTTP "+response.status);
  const x=await response.json();if(x.sections.length!==9)throw Error("模型参数分组数不符");
  x.sections.forEach(s=>{
   const group=E("section","evidence-model-section");group.append(E("h3","",s.title));
   const table=E("table","evidence-table"),head=E("thead"),tr=E("tr");
   ["参数","历史记录","适用边界"].forEach(k=>tr.append(E("th","",k)));head.append(tr);
   const body=E("tbody");s.rows.forEach(r=>{let tr=E("tr");
    [r.parameter,r.value,r.qualification].forEach(t=>tr.append(E("td","",t)));body.append(tr)});
   table.append(head,body);const scroll=E("div","evidence-table-scroll");scroll.append(table);group.append(scroll);host.append(group);
  });
 }catch(e){err(host,e.message)}
}
async function selected(host,m){
 const d=m.datasets.find(x=>x.id===S.selected);
 if(S.selected==="esm-full")return wave(m.waveform,host);
 if(S.selected==="model-92")return model(m.model_settings,host);
 return dataset(d||m.datasets[0],host);
}
async function show(){
 const root=document.getElementById("evidence-reader");
 if(!root)return;
 root.replaceChildren(E("p","evidence-hint","读取科研原件中…"));
 try{
  const m=await load();
  function paint(){
   const stats=E("div","evidence-stats");
   ["21年 · 184,080小时 ERA5衍生统计","18组NTM · 31段参数","46周期地震谱 · "+(m.waveform.src?"32,040点×3真实波形":"源级时程待核验"),"6章论文全文"].forEach(s=>stats.append(E("div","",s)));
   const filters=E("div","evidence-filter-row");
   ["全部","风资源","地震源","风荷载","结构历史"].forEach(g=>{
    const b=E("button","evidence-filter"+(S.group===g?" active":""),g);b.type="button";
    b.addEventListener("click",()=>{S.group=g;S.selected=m.datasets.find(x=>g==="全部"||x.group===g)?.id||"era5-wind-bins";paint()});filters.append(b);
   });
   const grid=E("div","evidence-dataset-grid");
   let entries=m.datasets.filter(x=>S.group==="全部"||x.group===S.group);
   if(S.group==="全部"||S.group==="地震源")entries=[{id:"esm-full",title:"ESM三分量同步加速度全时程",group:"地震源",n:m.waveform.rows,note:m.waveform.warning},...entries];
   if(S.group==="全部"||S.group==="结构历史")entries.push({id:"model-92",title:"完整92项BF1历史模型设置",group:"结构历史",n:92,note:"原始工程设置快照，不是当前R6"});
   entries.forEach(d=>{const b=E("button","evidence-dataset-card"+(S.selected===d.id?" selected":"" ));b.type="button";
    b.append(E("small","",d.group+" · "+d.n+"条"),E("strong","",d.title),E("span","",d.note));b.addEventListener("click",()=>{S.selected=d.id;paint()});grid.append(b)});
   const target=E("section","evidence-detail");root.replaceChildren(stats,filters,grid,target);selected(target,m);
  }paint()
 }catch(e){root.replaceChildren(E("p","evidence-error","原始科研数据无法加载："+e.message))}
}
async function showModule(id,root){
 const map={windResource:["era5-wind-bins","era5-direction"],windLoad:["ntm18-load-summary","ntm18-annual-clock"],seismic:["esm-spectrum","esm-component-peaks"],structure:["bf1-30-frequencies","bf1-rebar-31"],fatigue:["ntm18-load-summary"]};
 if(!map[id]||!root)return;
 const area=E("section","evidence-module-inline");
 area.append(head("本专题真实科研原始数据","完整数值和科研图表直接在当前工作室阅读，不必打开外部文件。"));
 root.prepend(area);
 if(id==="structure"){
  const hold=E("div","evidence-local-handoff");
  hold.append(E("p","evidence-wave-note","本机Codex阶段进度 · 2026-11-16 16:32 · 用户转录，尚非原始日志核验"));
  const steps=E("div","evidence-handoff-steps");
  for(const [name,status] of [["L1 混凝土","报告通过"],["L2 配筋","报告通过"],["L3 两段接触","报告失败"],["L4 真实PT","未验证"],["R7","已中断"]]){
   const entry=E("span","evidence-handoff-step",name+" · "+status);steps.append(entry);
  }
  hold.append(steps,E("p","evidence-hint","L3当前边界条件失败不能等同于已证明唯一根因。真实原生INP/MSG/STA/ODB尚未由本次对话上传。"));
  area.append(hold);
 }
 try{
  const m=await load();
  for(const id of map[id]){
   if(!area.isConnected)return;
   const d=m.datasets.find(x=>x.id===id),section=E("article","evidence-module-source");area.append(section);
   await dataset(d,section);
  }
  if(id==="seismic"){const section=E("article","evidence-module-source");area.append(section);await wave(m.waveform,section)}
 }catch(e){err(area,"数据源加载失败："+e.message)}
}
window.JYPrimaryEvidence={show,showModule};
})();