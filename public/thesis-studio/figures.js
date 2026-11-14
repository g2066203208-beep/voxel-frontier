"use strict";
/* Research figures: original Git objects published locally; evidence scans linked to public repository. */
(function () {
  const S = { data:null, load:null, all:false, category:"", query:"", page:0, perPage:18, active:null };
  const $ = q => document.querySelector(q);
  const node = (tag, cls, text) => {
    const el = document.createElement(tag);
    if(cls) el.className=cls;
    if(text!==undefined) el.textContent=String(text);
    return el;
  };
  const encode = path => path.split("/").map(encodeURIComponent).join("/");
  const source = fig => {
    const d=S.data.source;
    return "https://github.com/"+d.repository+"/blob/"+d.sha+"/"+encode(d.path+"/"+fig.p);
  };
  const image = fig => {
    const d=S.data.source;
    return fig.h ? d.assetPrefix+encode(fig.p):
      "https://raw.githubusercontent.com/"+d.repository+"/"+d.sha+"/"+encode(d.path+"/"+fig.p);
  };
  async function ready() {
    if(S.data) return S.data;
    if(!S.load) S.load=fetch("./data/figure-index.json",{cache:"no-store"}).then(r=>{
      if(!r.ok) throw Error("Figure catalog HTTP "+r.status);
      return r.json();
    }).then(d=>{
      if(!Array.isArray(d.images) || d.images.length!==d.total) throw Error("Figure index incomplete");
      S.data=d; return d;
    }).catch(e=>{S.load=null;throw e;});
    return S.load;
  }
  function badgeFor(f){return f.h?"科研原图":"来源影像";}
  function thumbnail(fig,compact=false) {
    const card=node("article","figure-card"+(compact?" compact":""));
    const btn=node("button","figure-preview");
    btn.type="button";
    btn.setAttribute("aria-label","预览原图："+fig.n);
    const photo=node("div","figure-photo");
    const im=node("img");
    im.src=image(fig);im.loading="lazy";im.decoding="async";im.alt=fig.n;
    im.onerror=()=>{photo.classList.add("broken");im.hidden=true;photo.append(node("span","figure-error","无法加载 · 查看源文件"));};
    photo.append(im);
    btn.append(photo);
    btn.addEventListener("click",()=>open(fig));
    const body=node("div","figure-card-body");
    body.append(node("span","figure-card-category",fig.c+" · "+badgeFor(fig)));
    const name=node("strong","figure-file",fig.n);
    name.title=fig.n;body.append(name);
    const actions=node("div","figure-actions");
    const view=node("button","","查看大图");view.type="button";view.addEventListener("click",()=>open(fig));
    const dl=node("button","","下载原图");dl.type="button";dl.addEventListener("click",()=>download(fig));
    actions.append(view,dl);body.append(actions);
    card.append(btn,body);return card;
  }
  function items() {
    const q=S.query.trim().toLowerCase();
    return S.data.images.filter(f=>
      (S.all || f.h) &&
      (!S.category || f.c===S.category) &&
      (!q || (f.n+" "+f.p+" "+f.c).toLowerCase().includes(q))
    );
  }
  function render() {
    const grid=$("#figure-grid");
    if(!grid || !S.data) return;
    const selected=items();
    const pages=Math.max(1,Math.ceil(selected.length/S.perPage));
    S.page=Math.min(Math.max(0,S.page),pages-1);
    const shown=selected.slice(S.page*S.perPage,(S.page+1)*S.perPage);
    grid.replaceChildren(...shown.map(f=>thumbnail(f)));
    if(!shown.length)grid.append(node("p","figure-empty","没有匹配的科研图像"));
    $("#figure-count").textContent=selected.length+" 张 / 第 "+(S.page+1)+" 页";
    $("#figure-prev").disabled=S.page===0;
    $("#figure-next").disabled=S.page===pages-1;
    $("#figure-hosted").classList.toggle("selected",!S.all);
    $("#figure-all").classList.toggle("selected",S.all);
  }
  function bindControls() {
    const filters=$("#figure-category");
    if(!filters || filters.dataset.ready) return;
    filters.dataset.ready="1";
    for(const c of Object.keys(S.data.categories)){
      const opt=node("option","",c);
      opt.value=c;filters.append(opt);
    }
    filters.addEventListener("change",e=>{S.category=e.target.value;S.page=0;render();});
    $("#figure-search").addEventListener("input",e=>{S.query=e.target.value;S.page=0;render();});
    $("#figure-hosted").addEventListener("click",()=>{S.all=false;S.page=0;render();});
    $("#figure-all").addEventListener("click",()=>{S.all=true;S.page=0;render();});
    $("#figure-prev").addEventListener("click",()=>{S.page--;render();});
    $("#figure-next").addEventListener("click",()=>{S.page++;render();});
    $("#figure-close").addEventListener("click",()=>$("#figure-lightbox").close());
    $("#figure-download").addEventListener("click",()=>{if(S.active)download(S.active);});
    $("#figure-lightbox").addEventListener("click",e=>{if(e.target===$("#figure-lightbox"))$("#figure-lightbox").close();});
  }
  async function show() {
    try {await ready();bindControls();render();}
    catch(e){const grid=$("#figure-grid");if(grid)grid.replaceChildren(node("p","figure-empty","原图目录加载失败"));console.error(e);}
  }
  function open(fig) {
    const modal=$("#figure-lightbox");
    if(!modal)return;
    S.active=fig;
    $("#figure-zoom-name").textContent=fig.n;
    $("#figure-zoom-topic").textContent=fig.c+" · "+(fig.h?"工作室原图":"GitHub来源影像");
    $("#figure-zoom-path").textContent="research/wind-tower/"+fig.p;
    const img=$("#figure-zoom-image");img.src=image(fig);img.alt=fig.n;
    $("#figure-source").href=source(fig);
    modal.showModal();
  }
  async function download(fig) {
    try {
      const url=image(fig);
      const response=await fetch(url);
      if(!response.ok)throw Error("HTTP "+response.status);
      const blob=await response.blob();
      const blobUrl=URL.createObjectURL(blob);
      const a=node("a");a.href=blobUrl;a.download=fig.n;
      document.body.append(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(blobUrl),7000);
    }catch(e) {
      window.open(source(fig),"_blank","noopener,noreferrer");
      console.warn("Fallback to original GitHub source",e);
    }
  }
  function insertFeatured(root,figures) {
    root.replaceChildren(...figures.map(f=>thumbnail(f,true)));
  }
  async function overview() {
    const target=$("#featured-figures");if(!target)return;
    try {
      const d=await ready();
      const focus=[
        "figure2-1-word-zh.png",
        "mesh-convergence-zh.png",
        "FIG3_S06_ERA5_DIRECTION_BAYES_20261110.svg",
        "FIG_S05_03_ROTD_PUBLICATION.svg",
        "FIG4_S10_ETM4_TENSION_DEL4_AZIMUTH_TRADEOFF_20261109.svg",
        "FIG_S08_06_158M_REAL_ESM_ELASTIC_BEAM_PROXY_NOT_ABAQUS.svg"
      ];
      const figs=focus.map(n=>d.images.find(x=>x.n===n&&x.h)).filter(Boolean);
      insertFeatured(target,figs);
    }catch(e){console.error(e);}
  }
  const moduleThemes={
    windResource:"风环境与风荷载",windLoad:"风环境与风荷载",
    seismic:"地震与动力响应",coupling:"地震与动力响应",
    structure:"混塔结构与有限元",foundation:"混塔结构与有限元",
    fatigue:"疲劳与优化",optimization:"疲劳与优化",
    manuscript:"论文与科研图表",
    reports:"论文与科研图表"
  };
  async function moduleFigures(mod, target) {
    const theme=moduleThemes[mod];
    if(!theme)return;
    try {
      const data=await ready();
      const chosen=data.images.filter(x=>x.h&&x.c===theme).slice(0,3);
      if(!chosen.length)return;
      const panel=node("section","detail-panel detail-figures");
      panel.append(node("span","panel-kicker","ORIGINAL FIGURES"),node("h2","","研究原图"));
      const grid=node("div","figure-detail-grid");
      chosen.forEach(f=>grid.append(thumbnail(f,true)));
      panel.append(grid);
      const a=node("button","figure-more","浏览全部原图 ↗");
      a.type="button";a.addEventListener("click",()=>{location.hash="#figures";});
      panel.append(a);target.append(panel);
    }catch(e){console.error(e);}
  }
  window.JYFigures={show,overview,moduleFigures};
})();
