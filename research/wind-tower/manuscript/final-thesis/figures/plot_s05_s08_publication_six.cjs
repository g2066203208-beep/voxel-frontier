#!/usr/bin/env node
"use strict";
/* Reproducible T079 six-panel publication group. No external packages; do not mistake SDOF for tower. */
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const map={"rotd":"S05_ESM_IT2012_NVL_MP_RotD_16PERIOD_20261030.csv","fit":"S05_ESM_ROTD50_VS_HYPOTHETICAL_6DEG_12PERIOD_20261030.csv","five":"S05_THREE_EVENT_FIVE_PAIR_20ROW_SOURCE_SCREEN_20261030.csv","event":"S05_THREE_EVENT_FIVE_PAIR_EVENT_BALANCE_20261029.csv","arias":"S08_ESM_IT2012_NVL_ARIAS_HUSID_3COMP_20261029.csv","sdof":"S08_ESM_SDOF_EXACT_VS_NEWMARK_18ROW_20261030.csv"};
function build(inp){
 const csv=s=>{let z=s.trim().split(/\r?\n/),h=z.shift().split(",");return z.map(l=>{let v=l.split(",");if(v.length!==h.length)throw Error("Bad CSV");return Object.fromEntries(h.map((k,i)=>[k,v[i]]))})};
 const d=Object.fromEntries(Object.entries(inp).map(([k,s])=>[k,csv(s)]));
 if(Object.values(d).map(a=>a.length).join(",")!=="16,12,20,4,3,18")throw Error("Source counts");
 const val=(r,k)=>{const v=Number(r[k]);if(!Number.isFinite(v))throw Error("NaN "+k);return v};
 const pal=["#256a85","#bc6d52","#378372","#8067a2","#8b969e"];
 const fmt=x=>(+x).toFixed(2), esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;");
 function fig(title,description,note,charts){
  let o=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="690" viewBox="0 0 1280 690">','<style>text{font-family:"Noto Sans CJK SC","Microsoft YaHei",Arial,sans-serif;fill:#26303b}</style>','<rect width="1280" height="690" fill="#fff"/>'];
  function T(x,y,s,size=14,opt=""){o.push(`<text x="${fmt(x)}" y="${fmt(y)}" font-size="${size}" ${opt}>${esc(s)}</text>`)}
  function L(x,y,xx,yy,col="#3b4651",w=1,ext=""){o.push(`<line x1="${fmt(x)}" y1="${fmt(y)}" x2="${fmt(xx)}" y2="${fmt(yy)}" stroke="${col}" stroke-width="${w}" ${ext}/>`)}
  T(67,46,title,24,'font-weight="600"');T(67,75,description,14);L(67,99,1213,99,"#dfe5e9");
  for(let j=0;j<2;j++){
   let c=charts[j],x0=j?696:105,y0=180,w=440,h=330;
   let fx=c.logx?Math.log:x=>x,fy=c.logy?Math.log:y=>y;
   let X=x=>x0+(fx(x)-fx(c.x[0]))/(fx(c.x[1])-fx(c.x[0]))*w;
   let Y=y=>y0+h-(fy(y)-fy(c.y[0]))/(fy(c.y[1])-fy(c.y[0]))*h;
   T(x0-16,136,`${j?"(b)":"(a)"} ${c.title}`,17,'font-weight="600"');
   for(let y of c.yticks){L(x0,Y(y),x0+w,Y(y),"#e6e9ec");T(x0-13,Y(y)+4,y,12,'text-anchor="end"')}
   for(let x of c.xticks){L(X(x),y0,X(x),y0+h,"#edf0f1");T(X(x),y0+h+24,x,12,'text-anchor="middle"')}
   L(x0,y0,x0,y0+h);L(x0,y0+h,x0+w,y0+h);T(x0+w/2,y0+h+59,c.xlabel,14,'text-anchor="middle"');
   o.push(`<text x="${fmt(x0-60)}" y="${fmt(y0+h/2)}" transform="rotate(-90 ${fmt(x0-60)} ${fmt(y0+h/2)})" text-anchor="middle" font-size="14">${esc(c.ylabel)}</text>`);
   if(c.band){o.push(`<rect x="${fmt(x0)}" y="${fmt(Y(c.band[1]))}" width="${w}" height="${fmt(Y(c.band[0])-Y(c.band[1]))}" fill="#edf0f2" opacity=".9"/>`)}
   for(let i=0;i<c.series.length;i++){
    let s=c.series[i],pts=s.rows.map(r=>[X(val(r,s.x)),Y(val(r,s.y))]),col=pal[i%pal.length];
    o.push(`<polyline points="${pts.map(p=>p.map(fmt).join(",")).join(" ")}" fill="none" stroke="${col}" stroke-width="${s.thin?1.2:2.7}" ${s.dash?'stroke-dasharray="5 4"':""} stroke-linejoin="round"/>`);
    if(!s.noPoints)for(let [x,y]of pts)o.push(`<circle cx="${fmt(x)}" cy="${fmt(y)}" r="2.4" fill="white" stroke="${col}" stroke-width="1.4"/>`);
    let lx=x0+(i%3)*151,ly=579+Math.floor(i/3)*21;L(lx,ly,lx+19,ly,col,3);T(lx+25,ly+4,s.name,12);
   }
  }
  L(67,644,1213,644,"#dfe5e9");T(67,669,note,12);o.push("</svg>\n");return o.join("\n");
 }
 const xy=(rows,x,y,name,extra={})=>({rows,x,y,name,...extra});
 const common={xticks:[.5,1,2,4,6,10],x:[.5,10],xlabel:"周期 T (s)"};
 const out={};
 out["FIG_S05_03_ROTD_PUBLICATION.svg"]=fig("图 S05-03  真实地震动方向反应谱","IT-2012-0008 · NVL · 5%阻尼 · 16离散周期","ESM真实处理记录；低频有效范围及设计谱适配性未验收。",[
 {...common,logx:true,logy:true,y:[.004,1],yticks:[.005,.01,.02,.05,.1,.2,.5,1],title:"RotD00/50/100谱",ylabel:"PSA (m/s²)",series:[xy(d.rotd,"period_s","RotD00_psa_m_s2","RotD00"),xy(d.rotd,"period_s","RotD50_psa_m_s2","RotD50"),xy(d.rotd,"period_s","RotD100_psa_m_s2","RotD100")]},
 {...common,logx:true,y:[.8,1.5],yticks:[.8,1,1.2,1.4],title:"方向性谱比",ylabel:"幅值比 (—)",series:[xy(d.rotd,"period_s","RotD100_over_RotD50","100/50"),xy(d.rotd,"period_s","RotD50_over_GM","50/GM")]}
 ]);
 if(d.fit.filter(r=>val(r,"scaled_over_target")<.7||val(r,"scaled_over_target")>1.3).length!==9)throw Error("fit count");
 out["FIG_S05_04_HYPOTHETICAL_SPECTRUM_PUBLICATION.svg"]=fig("图 S05-04  记录谱与假定目标谱失配","12周期(0.5–6s) · 最佳统一缩放系数0.980397","假定研究目标谱，不是嘉鱼设计谱；±30%仅为可视化诊断带。",[
 {x:[.5,6],y:[.02,.8],xticks:[.5,1,2,3,4,6],yticks:[.02,.05,.1,.2,.5],logx:true,logy:true,xlabel:"周期 T (s)",ylabel:"PSA (m/s²)",title:"缩放记录与假定谱",series:[xy(d.fit,"period_s","scaled_real_psa_m_s2","缩放RotD50"),xy(d.fit,"period_s","hypothetical_target_psa_m_s2","假定目标")]},
 {x:[.5,6],y:[0,2.1],xticks:[.5,1,2,3,4,6],yticks:[0,.5,1,1.5,2],logx:true,xlabel:"周期 T (s)",ylabel:"谱比 (—)",title:"周期点失配 9/12",band:[.7,1.3],series:[xy(d.fit,"period_s","scaled_over_target","记录/目标")]}
 ]);
 const groups={};for(const r of d.five){let k=r.event_id+"/"+r.station;(groups[k]??=[]).push(r)}if(Object.keys(groups).length!==5)throw Error("pair groups");
 out["FIG_S05_05_EVENT_LOW_FREQUENCY_SCREEN.svg"]=fig("图 S05-05  多事件长周期源数据筛查","三独立事件 · 五台站 · 周期4–10s","记录处理不统一、低频质量未验收；不能直接用作设计选波。",[
 {x:[4,10],y:[.0005,1],xticks:[4,6,8,10],yticks:[.001,.01,.1,1],logy:true,xlabel:"周期 T (s)",ylabel:"双水平PSA均值 (m/s²)",title:"候选台站谱形",series:Object.values(groups).map((r,i)=>xy(r,"period_s","gm_psa_m_s2","台站"+(i+1)))},
 {x:[4,10],y:[.1,500],xticks:[4,6,8,10],yticks:[.1,1,10,100,500],logy:true,xlabel:"周期 T (s)",ylabel:"基线敏感性比 (—)",title:"美国记录去均值影响",series:Object.values(groups).filter(r=>r.every(z=>z.raw_vs_pre20_rel!=="NA")).map((r,i)=>xy(r,"period_s","raw_vs_pre20_rel","US台站"+(i+1)))}
 ]);
 out["FIG_S05_06_EVENT_WEIGHTING_PUBLICATION.svg"]=fig("图 S05-06  台站与事件权重差异","三独立事件、五组水平分量；同一地震的不同台站并非独立事件","仅展示候选源样本统计；处理链不同，不作地震危险性结论。",[
 {x:[4,10],y:[0,.055],xticks:[4,6,8,10],yticks:[0,.01,.02,.03,.04,.05],xlabel:"周期 T (s)",ylabel:"平均PSA (m/s²)",title:"不同加权谱",series:[xy(d.event,"period_s","pair_weighted_gm_m_s2","按台站"),xy(d.event,"period_s","event_weighted_gm_m_s2","按事件")]},
 {x:[4,10],y:[0,1],xticks:[4,6,8,10],yticks:[0,.2,.4,.6,.8,1],xlabel:"周期 T (s)",ylabel:"比值 (—)",title:"事件/台站均值",series:[xy(d.event,"period_s","event_over_pair_ratio","事件/台站")]}
 ]);
 const arow=d.arias.map((r,i)=>({...r,index:i+1}));
 out["FIG_S08_02_ARIAS_DURATION_PUBLICATION.svg"]=fig("图 S08-02  三向加速度强度与持续时间","ESM IT-2012-0008 / NVL · 32040点 · Δt=0.005s","PGA及Arias显著持续时间仅用于输入表征，非158m混塔地震响应。",[
 {x:[.8,3.2],y:[0,.6],xticks:[1,2,3],yticks:[0,.1,.2,.3,.4,.5,.6],xlabel:"1 HNE / 2 HNN / 3 HNZ",ylabel:"PGA (m/s²)",title:"三分量峰值",series:[xy(arow,"index","pga_m_s2","PGA")]},
 {x:[.8,3.2],y:[20,60],xticks:[1,2,3],yticks:[20,30,40,50,60],xlabel:"1 HNE / 2 HNN / 3 HNZ",ylabel:"记录时刻 (s)",title:"5%和95%能量到时",series:[xy(arow,"index","t5_s","Arias 5%"),xy(arow,"index","t95_s","Arias 95%")]}
 ]);
 const sample=d.sdof.map(r=>({...r,err_percent:100*val(r,"newmark_vs_exact_relative_error")}));
 out["FIG_S08_03_SDOF_ORACLE_PUBLICATION.svg"]=fig("图 S08-03  单自由度数值积分交叉核验","实际三向地震输入 · 分段线性解析解 vs Newmark平均加速度 · 阻尼5%","仅SDOF算法一致性，不是塔架真实E/W/WE或Abaqus原生求解。",[
 {x:[.5,10],y:[0,.032],xticks:[.5,1,2,4,6,10],yticks:[0,.005,.01,.015,.02,.025,.03],xlabel:"单自由度周期 (s)",ylabel:"相对位移峰值 (m)",title:"解析解与Newmark",series:[...["HNE","HNN","HNZ"].map(c=>xy(sample.filter(r=>r.component.startsWith(c)),"period_s","exact_peak_rel_displacement_m",c+"精确")),...["HNE","HNN","HNZ"].map(c=>xy(sample.filter(r=>r.component.startsWith(c)),"period_s","newmark_peak_rel_displacement_m",c+"数值",{thin:true,noPoints:true}))]},
 {x:[.5,10],y:[.0001,.1],xticks:[.5,1,2,4,6,10],yticks:[.0001,.001,.01,.1],logy:true,xlabel:"单自由度周期 (s)",ylabel:"相对误差 (%)",title:"数值误差",series:["HNE","HNN","HNZ"].map(c=>xy(sample.filter(r=>r.component.startsWith(c)),"period_s","err_percent",c))}
 ]);
 for(const [name,s] of Object.entries(out))if(s.length<5500||!s.endsWith("</svg>\n"))throw Error("SVG source "+name);
 return out;
}
if(require.main===module){
const [src,dest]=process.argv.slice(2);if(!src||!dest)throw Error("Need <real-records-dir> <figures-dir>");
const input=Object.fromEntries(Object.entries(map).map(([k,n])=>[k,fs.readFileSync(path.join(src,n),"utf8")]));
const figures=build(input),SHA=s=>crypto.createHash("sha256").update(s).digest("hex");
fs.mkdirSync(dest,{recursive:true});
const manifest={input_sha256:Object.fromEntries(Object.entries(input).map(([k,v])=>[k,SHA(v)])),figures_sha256:{}};
for(const [k,v]of Object.entries(figures)){fs.writeFileSync(path.join(dest,k),v);manifest.figures_sha256[k]=SHA(v)}
fs.writeFileSync(path.join(dest,"S05_S08_SIX_FIGURE_RECEIPT.json"),JSON.stringify(manifest,null,2)+"\n");
console.log("S05_S08_SIX_REAL_SOURCE_FIGURES_PASS",JSON.stringify(manifest));
}