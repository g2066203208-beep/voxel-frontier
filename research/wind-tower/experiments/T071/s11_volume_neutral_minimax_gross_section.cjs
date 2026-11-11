"use strict";
// S11: fixed historical N/M, elastic annular section, volume-neutral scenario.
// NOT a dynamic wind/earthquake response, local stress, Miner life or design optimization.
const INPUT_SHA256="fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800";
const LO=.95, HI=1.05;
function check(ok,msg){if(!ok)throw Error(msg)}
function area(r,t){return Math.PI*(r.D*t-t*t)}
function inertia(r,t){return Math.PI/64*(r.D**4-(r.D-2*t)**4)}
function stress(r,t){return (r.M*r.D/(2*inertia(r,t))-r.N/area(r,t))/1e6}
function volume(r,t){return area(r,t)*r.h}
function parse(raw){
 const ls=raw.replace(/^\uFEFF/,"").trim().split(/\r?\n/),hs=ls[0].split(",");
 for(const k of ["segment","top_height_m","D_m","di_m","N_kN","M_bend_kNm","A_m2","I_m4","sigma_N_MPa","sigma_M_MPa","status"])check(hs.includes(k),"missing "+k);
 check(ls.length===32,"not 31 segments");
 let prev=0;
 return ls.slice(1).map((line,i)=>{
  const a=line.split(","),o=Object.fromEntries(hs.map((h,j)=>[h,a[j]]));
  const n=k=>{check(o[k]!==""&&Number.isFinite(+o[k]),"invalid "+k);return +o[k]};
  check(o.segment==="CSEG_"+String(i+1).padStart(2,"0"),"segment identity");
  const D=n("D_m"),di=n("di_m"),top=n("top_height_m"),N=n("N_kN")*1000,M=n("M_bend_kNm")*1000;
  check(D>di&&di>0&&top>prev&&N<0&&M>0,"geometry/load");
  check(o.status==="elastic screening; no factors or prestress","source status");
  const r={id:o.segment,D,t:(D-di)/2,h:top-prev,N:-N,M};prev=top;
  check(Math.abs(area(r,r.t)-n("A_m2"))<1e-8,"area mismatch");
  check(Math.abs(inertia(r,r.t)-n("I_m4"))<1e-8,"I mismatch");
  check(Math.abs(r.N/area(r,r.t)/1e6-n("sigma_N_MPa"))<1e-8,"N stress mismatch");
  check(Math.abs(r.M*r.D/(2*inertia(r,r.t))/1e6-n("sigma_M_MPa"))<1e-8,"M stress mismatch");
  return r;
 });
}
function monotonicMargin(r){
 const R=r.D/2,inner=R-HI*r.t;
 return (8*R*inner*inner/(R*R+inner*inner)**2)/(r.N/r.M);
}
function solve(raw){
 const r=parse(raw);
 check(Math.abs(r.reduce((s,x)=>s+x.h,0)-112)<1e-8,"height");
 const margin=Math.min(...r.map(monotonicMargin));
 check(margin>1,"monotonicity unproven");
 const V0=r.reduce((s,x)=>s+volume(x,x.t),0),S0=Math.max(...r.map(x=>stress(x,x.t)));
 const t=r.map(x=>x.t),S=stress(r[26],HI*r[26].t);t[26]=HI*r[26].t;
 check(stress(r[27],HI*r[27].t)<=S,"CSEG28 cannot reach bound");
 let a=LO*r[27].t,b=HI*r[27].t;
 for(let j=0;j<70;j++){let m=(a+b)/2;if(stress(r[27],m)>S)a=m;else b=m}t[27]=b;
 const vol=ts=>r.reduce((s,x,i)=>s+volume(x,ts[i]),0);
 const vAt=k=>{let ts=t.slice();for(let i=0;i<5;i++)ts[i]=r[i].t*k;return vol(ts)};
 check(vAt(LO)<=V0&&vAt(1)>=V0,"no volume compensation");
 let kl=LO,kh=1;
 for(let j=0;j<75;j++){let m=(kl+kh)/2;if(vAt(m)>V0)kh=m;else kl=m}
 const k=(kl+kh)/2;for(let i=0;i<5;i++)t[i]=r[i].t*k;
 const max=Math.max(...r.map((x,i)=>stress(x,t[i])));
 check(Math.abs(vol(t)-V0)<1e-9,"volume mismatch");
 check(Math.abs(max-S)<1e-8,"minimax lower bound not attained");
 check(t.every((x,i)=>x>=LO*r[i].t-1e-12&&x<=HI*r[i].t+1e-12),"bound");
 let z=0;
 const rows=r.map((x,i)=>{z+=x.h;return {segment:x.id,z_top_m:z,t_base_mm:1000*x.t,t_candidate_mm:1000*t[i],change_pct:100*(t[i]/x.t-1),sigma_base_MPa:stress(x,x.t),sigma_candidate_MPa:stress(x,t[i]),volume_change_m3:volume(x,t[i])-volume(x,x.t)}});
 return {rows,V0,S0,S,max,margin,k,improvement:100*(1-S/S0)};
}
function csv(x){
 const hs=["segment","z_top_m","t_base_mm","t_candidate_mm","change_pct","sigma_base_MPa","sigma_candidate_MPa","volume_change_m3"];
 return hs.join(",")+"\n"+x.rows.map(r=>hs.map(h=>h==="segment"?r[h]:r[h].toFixed(12)).join(",")).join("\n")+"\n";
}
function svg(x){
 const W=1100,H=500,L=88,T=70,B=70,R=25,Y=v=>T+(60-v)*(H-T-B)/45,X=i=>L+i*(W-L-R)/30;
 const line=k=>x.rows.map((r,i)=>(i?"L":"M")+X(i).toFixed(2)+" "+Y(r[k]).toFixed(2)).join(" ");
 const grids=[20,30,40,50,60].map(v=>'<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#e2e8f0"/><text x="'+(L-10)+'" y="'+(Y(v)+5)+'" text-anchor="end" font-size="15">'+v+'</text>').join("");
 const ticks=[1,5,10,15,20,25,27,28,31].map(n=>'<text x="'+X(n-1)+'" y="'+(H-B+22)+'" text-anchor="middle" font-size="14">'+n+'</text>').join("");
 return '<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'"><rect width="100%" height="100%" fill="white"/><text x="'+L+'" y="28" font-size="21" font-weight="bold">Volume-neutral 31-segment fixed-load minimax certificate</text><text x="'+L+'" y="51" font-size="13">T071 historical elastic N/M; gross section; +/-5% thickness; NOT physical fatigue optimization</text>'+grids+'<path d="M'+L+' '+T+' V'+(H-B)+' H'+(W-R)+'" fill="none" stroke="#64748b"/>'+ticks+'<path d="'+line("sigma_base_MPa")+'" fill="none" stroke="#dc2626" stroke-width="3"/><path d="'+line("sigma_candidate_MPa")+'" fill="none" stroke="#0d9488" stroke-width="3"/><text x="'+(W-340)+'" y="94" fill="#dc2626" font-size="16">Baseline max '+x.S0.toFixed(3)+' MPa</text><text x="'+(W-340)+'" y="118" fill="#0d9488" font-size="16">Conditional lower bound '+x.S.toFixed(3)+' MPa</text><text x="'+(W/2)+'" y="'+(H-14)+'" text-anchor="middle" font-size="16">Segment index</text><text transform="translate(24 '+H/2+') rotate(-90)" text-anchor="middle" font-size="15">Tensile-side stress proxy (MPa)</text></svg>\n';
}
function selfTest(raw){
 const x=solve(raw);check(x.rows.length===31,"rows");
 check(Math.abs(x.S0-53.140995684550575)<1e-9,"baseline");
 check(Math.abs(x.S-50.98730153855519)<1e-9,"optimum");
 check(Math.abs(x.improvement-4.052792233664382)<1e-9,"improvement");
 check(Math.abs(x.k-.9871079311866364)<1e-10,"compensation");
 check(x.margin>6,"monotonicity");
 const reject=s=>{let ok=false;try{solve(s)}catch(e){ok=true}check(ok,"bad input accepted")};
 reject(raw.replace("CSEG_01","CSEG_99"));
 reject(raw.replace("elastic screening; no factors or prestress","wrong status"));
 reject(raw.replace("8.249999587604677","8.1"));
 reject(raw.replace(/CSEG_31[^\n]*\n?/,""));
 const q={D:4,t:.2,h:2,N:1e5,M:1e6};
 check(Math.abs(area(q,.2)-Math.PI*(.8-.04))<1e-12,"ring area");
 check(stress(q,.95*.2)>stress(q,1.05*.2),"stress derivative");
 return {result:"PASS",negative:4,analytic:2,source_rows:31};
}
if(typeof module!=="undefined"){
 module.exports={parse,solve,csv,svg,selfTest,monotonicMargin};
 if(require.main===module){
  const fs=require("fs"),path=require("path"),crypto=require("crypto");
  const raw=fs.readFileSync(path.join(__dirname,"T071_input_geometry_31_segments.csv"));
  check(crypto.createHash("sha256").update(raw).digest("hex")===INPUT_SHA256,"SOURCE_SHA256_MISMATCH");
  const text=raw.toString("utf8"),result=solve(text);
  if(process.argv.includes("--self-test"))console.log(JSON.stringify(selfTest(text)));
  if(process.argv.includes("--emit")){
   fs.writeFileSync(path.join(__dirname,"S11_T071_31SEG_VOLUME_NEUTRAL_MINIMAX_20261112.csv"),csv(result));
   fs.writeFileSync(path.join(__dirname,"../../manuscript/final-thesis/figures/FIG5_S11_VOLUME_NEUTRAL_MINIMAX_20261112.svg"),svg(result));
  }
  console.log(JSON.stringify({input_sha256:INPUT_SHA256,baseline_MPa:result.S0,conditional_minimax_MPa:result.S,volume_m3:result.V0,improvement_pct:result.improvement,monotonic_margin:result.margin,status:"METHOD_SCREEN_ONLY"}));
 }
}
