#!/usr/bin/env node
"use strict";
/* SOURCE: T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv
   Identity checks are strict. Outputs are descriptive ETM screening figures only.
   No synthetic samples, no Abaqus/Origin execution, no fatigue-life claim. */
const fs=require("node:fs"),crypto=require("node:crypto"),path=require("node:path");
function generateFigures(csv) {
  const lines=csv.replace(/\r/g,"").trimEnd().split("\n");
  const hdr=lines.shift().split(",");
  const expected=["case","segment","gage_z_m","channel","units","n_samples","dt_s","duration_s","mean","std","min","max","p2p","rms_first_300s","rms_last_300s","rainflow_equivalent_cycles","rainflow_half_cycles","rainflow_full_cycles","DEL_m4_Nref_1Hz","DEL_m10_Nref_1Hz"];
  if(hdr.join("|")!==expected.join("|"))throw Error("Unexpected source header");
  const rows=lines.map(s=>{const vals=s.split(",");if(vals.length!==hdr.length)throw Error("CSV width");return Object.fromEntries(vals.map((v,i)=>[hdr[i],v]));});
  const cases=["U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06"];
  const labels=["9.34 m/s · S06","11.4 m/s · S04","19.2 m/s · S04","19.2 m/s · S06"];
  const channels=["Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm"];
  if(rows.length!==744)throw Error("Expected exactly 744 rows");
  const index=new Map();
  for(const r of rows){
    const k=`${r.case}|${r.segment}|${r.channel}`;
    if(index.has(k))throw Error("Duplicate: "+k);
    if(!cases.includes(r.case)||!channels.includes(r.channel)||!/CSEG_\d\d/.test(r.segment))throw Error("Unknown identity");
    if(+r.n_samples!==12001||Math.abs(+r.dt_s-.05)>1e-10||Math.abs(+r.duration_s-600)>1e-9)throw Error("Sampling mismatch");
    for(const a of ["gage_z_m","DEL_m4_Nref_1Hz","DEL_m10_Nref_1Hz","rms_first_300s","rms_last_300s"])if(!Number.isFinite(+r[a]))throw Error("Nonfinite:"+a);
    if(+r.gage_z_m<0||+r.gage_z_m>112||+r.DEL_m4_Nref_1Hz<0)throw Error("Out of domain");
    index.set(k,r);
  }
  const point=(c,s,ch)=>{const v=index.get(`${c}|CSEG_${String(s).padStart(2,"0")}|${ch}`);if(!v)throw Error("Missing "+c+s+ch);return v;};
  for(const c of cases)for(let s=1;s<=31;s++)for(const ch of channels)point(c,s,ch);
  const fmt=(x,d=0)=>Number(x).toLocaleString("en-US",{maximumFractionDigits:d,minimumFractionDigits:d});
  const esc=x=>String(x).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  const P={ink:"#202d3a",muted:"#607185",grid:"#e3eaf0",blue:"#174e75",orange:"#be7043",teal:"#337f77",purple:"#776b93",bg:"#ffffff"};
  const colors=[P.blue,P.orange,P.teal,P.purple];
  const W=1160,H=720;
  const txt=(x,y,s,sz=15,opts="")=>`<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${sz}" fill="${P.ink}" ${opts}>${esc(s)}</text>`;
  const lin=(x1,y1,x2,y2,col=P.grid,width=1,dash="")=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="${width}" ${dash?`stroke-dasharray="${dash}"`:""}/>`;
  const root=(title,subtitle,body,note)=>`<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)}"><rect width="${W}" height="${H}" fill="white"/>${txt(78,56,title,27,'font-weight="700"')}${txt(78,86,subtitle,15)}${body}${lin(78,655,1080,655,"#bccad5",1)}${txt(78,682,note,13)}${txt(1053,684,"S06 / SCREEN",12,'text-anchor="end" font-weight="700" style="fill:#9a613f"')}</svg>\n`;
  const seriesChart=(title,subtitle,perCase,yField,yTitle,yLimit,step,note,withThreshold=false)=>{
    const L=120,R=1080,T=148,B=566;
    let out="";
    for(let t=0;t<=yLimit+1e-9;t+=step){const y=B-(t/yLimit)*(B-T);out+=lin(L,y,R,y)+txt(L-13,y+5,fmt(t,0),13,'text-anchor="end"');}
    for(let t=0;t<=112;t+=20){const x=L+(t/112)*(R-L);out+=lin(x,T,x,B,P.grid,1)+txt(x,B+25,t,13,'text-anchor="middle"');}
    out+=lin(L,T,L,B,P.ink,1.7)+lin(L,B,R,B,P.ink,1.7);
    if(withThreshold){const y=B-(20/yLimit)*(B-T);out+=lin(L,y,R,y,"#ac4f48",1.5,"8 5")+txt(R-4,y-8,"20% visual QC guide (not a code limit)",12,'text-anchor="end" style="fill:#ac4f48"');}
    for(let ci=0;ci<cases.length;ci++){
      const pts=[];let last=0;
      for(let s=1;s<=31;s++){
        const r=point(cases[ci],s,"My_kNm");
        const x=L+(+r.gage_z_m/112)*(R-L);
        const value=perCase?perCase(r):+r[yField];
        if(!Number.isFinite(value)||value<0)throw Error("Bad value");
        const y=B-(value/yLimit)*(B-T);
        if(y<T-2||y>B+2)throw Error("Axis overflow");
        if(x<=last)throw Error("Nonmonotonic z");last=x;
        pts.push([x,y]);
      }
      out+=`<polyline points="${pts.map(p=>p.map(q=>q.toFixed(2)).join(",")).join(" ")}" fill="none" stroke="${colors[ci]}" stroke-width="2.9" stroke-linejoin="round" stroke-linecap="round" ${ci===3?'stroke-dasharray="7 4"':""}/>`;
      for(let i=0;i<31;i+=5){const p=pts[i];out+=`<circle cx="${p[0].toFixed(2)}" cy="${p[1].toFixed(2)}" r="3.1" fill="white" stroke="${colors[ci]}" stroke-width="1.7"/>`;}
    }
    out+=txt((L+R)/2,625,"Tower-gage elevation, z (m); concrete portion 0–112 m",16,'text-anchor="middle"');
    out+=`<text x="33" y="${(T+B)/2}" transform="rotate(-90 33 ${(T+B)/2})" fill="${P.ink}" font-family="Arial,Helvetica,sans-serif" font-size="16" text-anchor="middle">${esc(yTitle)}</text>`;
    for(let i=0;i<4;i++){const x=115+i*248;out+=lin(x,119,x+33,119,colors[i],3,i===3?"7 4":"")+txt(x+42,124,labels[i],14);}
    return root(title,subtitle,out,note);
  };
  const one=seriesChart("My load-DEL along the concrete tower","Four archived ETM screening cases · 31 reconstructed gages · m = 4, Nref = 1 Hz",null,"DEL_m4_Nref_1Hz","My load-DEL (kN·m)",100000,20000,"Historical screening only · not DLC1.2 lifetime material fatigue.");
  const vQc=r=>100*Math.abs(+r.rms_first_300s-+r.rms_last_300s)/((+r.rms_first_300s+ +r.rms_last_300s)/2);
  let maxQc=0;
  for(const c of cases)for(let s=1;s<=31;s++)maxQc=Math.max(maxQc,vQc(point(c,s,"My_kNm")));
  const qcCeil=Math.max(30,Math.ceil(maxQc/10)*10);
  const three=seriesChart("My half-window RMS contrast by gage","First 300 s vs last 300 s · absolute contrast / two-window mean",vQc,null,"RMS half-window contrast (%)",qcCeil,10,"Diagnostic only · window contrast does not prove stationarity.",true);
  // Three panels with separate physical moment axes to avoid scaling away Mx/Mz.
  const panelSpecs=[{name:"Mx",ch:"Mx_kNm"},{name:"My",ch:"My_kNm"},{name:"Mz",ch:"Mz_kNm"}];
  let bdy="";
  for(let k=0;k<3;k++){
    const spec=panelSpecs[k],start=77+k*365,pW=320,left=start+37,right=start+pW-13,top=170,bottom=547;
    const vals=cases.map(c=>+point(c,1,spec.ch).DEL_m4_Nref_1Hz),max=Math.max(...vals);
    const div=Math.pow(10,Math.floor(Math.log10(max)));
    const ymax=Math.ceil(max/div*1.15/2)*2*div;
    bdy+=txt(start+7,148,`${spec.name} at CSEG_01`,18,'font-weight="700"')+
         txt(start+7,167,"Load-DEL, kN·m",12);
    for(let t=0;t<=4;t++){const v=ymax*t/4,y=bottom-(t/4)*(bottom-top);bdy+=lin(left,y,right,y)+txt(left-8,y+4,fmt(v),12,'text-anchor="end"');}
    bdy+=lin(left,top,left,bottom,P.ink,1.5)+lin(left,bottom,right,bottom,P.ink,1.5);
    const bw=41,gap=17,startX=left+16;
    for(let j=0;j<4;j++){
      const x=startX+j*(bw+gap),h=vals[j]/ymax*(bottom-top),y=bottom-h;
      bdy+=`<rect x="${x}" y="${y.toFixed(2)}" width="${bw}" height="${h.toFixed(2)}" rx="2" fill="${colors[j]}"/>`;
      bdy+=txt(x+bw/2,bottom+21,`${j+1}`,14,'text-anchor="middle"');
      bdy+=txt(x+bw/2,Math.max(top+20,y-8),fmt(vals[j]/1000,2)+"k",11,'text-anchor="middle"');
    }
  }
  for(let i=0;i<4;i++){const x=90+i*256;bdy+=`<rect x="${x}" y="601" width="15" height="15" fill="${colors[i]}"/>`+txt(x+22,614,`${i+1}. ${labels[i]}`,14);}
  const two=root("Base-gage load-DEL of three moment channels","CSEG_01 · separate scales per panel · m = 4, Nref = 1 Hz",bdy,"Moments are sectional load indicators, not material stresses or fatigue lives.");
  const csvHead="case,segment,gage_z_m,My_DEL_m4_kNm,Mx_DEL_m4_kNm,Mz_DEL_m4_kNm,My_RMS_first_300s_kNm,My_RMS_last_300s_kNm,My_RMS_halfwindow_contrast_pct\n";
  const csvRows=[];
  for(const c of cases)for(let s=1;s<=31;s++){
    const a=point(c,s,"My_kNm"),b=point(c,s,"Mx_kNm"),d=point(c,s,"Mz_kNm");
    csvRows.push([c,a.segment,a.gage_z_m,a.DEL_m4_Nref_1Hz,b.DEL_m4_Nref_1Hz,d.DEL_m4_Nref_1Hz,a.rms_first_300s,a.rms_last_300s,vQc(a).toFixed(9)].join(","));
  }
  const sample=cases.map(c=>{const r=point(c,1,"My_kNm");return {case:c,baseMyM4:Number(r.DEL_m4_Nref_1Hz),maxMyM4:Math.max(...Array.from({length:31},(_,j)=>+point(c,j+1,"My_kNm").DEL_m4_Nref_1Hz))};});
  return {figures:{"FIG3_S06_01_MY_M4_HEIGHT_SCREEN.svg":one,"FIG3_S06_02_BASE_MOMENTS_M4_SCREEN.svg":two,"FIG3_S06_03_MY_HALF_WINDOW_RMS_SCREEN.svg":three},points_csv:csvHead+csvRows.join("\n")+"\n",stats:{rows:rows.length,plotRows:csvRows.length,cases:cases.length,segments:31,maxRmsContrastPct:maxQc,caseSamples:sample}};
}
const root=path.resolve(__dirname,"../../..");
const input=path.join(root,"experiments/T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv");
const output=__dirname;
const raw=fs.readFileSync(input);
const inputSha=crypto.createHash("sha256").update(raw).digest("hex");
if(inputSha!=="9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b")throw Error("SOURCE SHA256 mismatch: "+inputSha);
const result=generateFigures(raw.toString("utf8"));
let changed=false;
for(const [n,s] of Object.entries({...result.figures,"FIG3_S06_PLOT_POINTS_124.csv":result.points_csv})){
 const p=path.join(output,n);
 if(process.argv.includes("--check")){
   if(!fs.existsSync(p)||fs.readFileSync(p,"utf8")!==s)throw Error("Output mismatch: "+n);
 }else {
   fs.writeFileSync(p,s,"utf8"); changed=true;
 }
}
console.log(JSON.stringify({status:process.argv.includes("--check")?"RENDER_REPRO_PASS":"RENDER_WRITTEN",source_sha256:inputSha,...result.stats},null,2));
