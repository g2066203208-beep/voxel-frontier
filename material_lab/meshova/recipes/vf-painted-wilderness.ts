import { makeTexture, type Material } from "../../src/index.js";
import { bakeVfBasalt } from "./vf-basalt.js";
import { bakeVfGranite } from "./vf-granite.js";
import { bakeVfDirt } from "./vf-dirt.js";
import { bakeVfBark } from "./vf-bark.js";
import { bakeVfSnow, bakeVfIce } from "./vf-world-surfaces.js";

type RGB=[number,number,number];
type Tex={width:number;height:number;channels:number;data:Float32Array};
type Baker=(size:number,params?:any)=>Material;
type Kind="basalt"|"granite"|"dirt"|"bark"|"snow"|"ice";
export type VfPaintedParams={seed?:number;paintScale?:number;normalStrength?:number;normalRadius?:number;wetness?:number;frost?:number;snowCoverage?:number;snowDepth?:number;[key:string]:unknown};
type Cfg={palette:RGB[];accent:RGB;lo:number;hi:number;source:number;relief:number;rough:[number,number,number];n:number;r:number;ao:number;accentAmt:number;stroke:number};
const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const W=(x:number)=>x-Math.floor(x);
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t);};
const Q=(x:number,n:number)=>Math.round(C(x)*(n-1))/(n-1);
const lum=(c:RGB)=>c[0]*.24+c[1]*.68+c[2]*.08;

// Strong storybook palettes: deliberately narrow, authored and non-photographic.
const CFG:Record<Kind,Cfg>={
  basalt:{palette:[[.040,.060,.100],[.075,.095,.135],[.145,.155,.165],[.275,.245,.205],[.390,.250,.165]],accent:[.500,.235,.120],lo:.020,hi:.250,source:8.5,relief:.92,rough:[.76,.82,.88],n:7.6,r:8,ao:1.06,accentAmt:.18,stroke:.17},
  granite:{palette:[[.100,.105,.145],[.180,.165,.185],[.315,.245,.225],[.500,.405,.340],[.650,.535,.430]],accent:[.660,.300,.255],lo:.045,hi:.475,source:8.0,relief:.88,rough:[.72,.80,.86],n:7.2,r:8,ao:1.05,accentAmt:.22,stroke:.16},
  dirt:{palette:[[.085,.065,.085],[.145,.075,.060],[.285,.125,.075],[.470,.245,.120],[.620,.360,.180]],accent:[.720,.390,.190],lo:.020,hi:.365,source:8.8,relief:.86,rough:[.80,.86,.91],n:6.8,r:9,ao:1.07,accentAmt:.16,stroke:.18},
  bark:{palette:[[.070,.050,.085],[.135,.075,.070],[.270,.120,.070],[.450,.235,.120],[.610,.350,.180]],accent:[.735,.400,.200],lo:.018,hi:.305,source:7.8,relief:.96,rough:[.78,.85,.91],n:8.0,r:7,ao:1.10,accentAmt:.18,stroke:.20},
  snow:{palette:[[.300,.475,.720],[.485,.630,.790],[.720,.790,.865],[.905,.900,.850],[.985,.960,.865]],accent:[.805,.590,.620],lo:.390,hi:.995,source:9.5,relief:.72,rough:[.82,.87,.92],n:5.8,r:10,ao:1.02,accentAmt:.10,stroke:.16},
  ice:{palette:[[.055,.155,.280],[.080,.285,.430],[.165,.455,.570],[.390,.650,.690],[.705,.795,.760]],accent:[.740,.510,.430],lo:.050,hi:.640,source:9.2,relief:.68,rough:[.18,.28,.40],n:5.4,r:10,ao:1.02,accentAmt:.11,stroke:.15},
};

function sample(t:Tex,u:number,v:number,ch:number){
  const x=W(u)*t.width,y=W(v)*t.height,x0=Math.floor(x)%t.width,y0=Math.floor(y)%t.height,x1=(x0+1)%t.width,y1=(y0+1)%t.height,tx=x-Math.floor(x),ty=y-Math.floor(y);
  const at=(xx:number,yy:number)=>t.data[(yy*t.width+xx)*t.channels+ch];
  return L(L(at(x0,y0),at(x1,y0),tx),L(at(x0,y1),at(x1,y1),tx),ty);
}

function broadNormal(h:Tex,strength:number,radius:number){
  const n=makeTexture(h.width,h.height,3),w=h.width,hh=h.height,r=Math.max(1,Math.round(radius));
  const at=(x:number,y:number)=>h.data[((y%hh+hh)%hh)*w+((x%w+w)%w)];
  for(let y=0;y<hh;y++)for(let x=0;x<w;x++){
    const dx=(at(x+r,y)-at(x-r,y))*strength,dy=(at(x,y+r)-at(x,y-r))*strength;
    let nx=-dx,ny=dy,nz=1;const q=Math.hypot(nx,ny,nz)||1;nx/=q;ny/=q;nz/=q;
    const i=(y*w+x)*3;n.data[i]=nx*.5+.5;n.data[i+1]=ny*.5+.5;n.data[i+2]=nz*.5+.5;
  }
  return n;
}

function pal(p:RGB[],t:number){
  const x=C(t)*(p.length-1),i=Math.min(p.length-2,Math.floor(x)),f=x-i;
  // Hold a lot of each authored color; transition only near band boundaries.
  const soft=S(C((f-.32)/.36));
  return M(p[i],p[i+1],soft);
}

// Large painted value masses. Frequencies are intentionally very low.
function massField(u:number,v:number,k:Kind){
  const phase=k==="snow"?1.1:k==="ice"?2.0:k==="bark"?.35:.7;
  const a=Math.sin((u*1.35+v*.92)*TAU+phase)*.5+.5;
  const b=Math.sin((u*.72-v*1.28)*TAU+phase+1.7)*.5+.5;
  const c=Math.sin((u*2.05+v*.45)*TAU+phase+2.8)*.5+.5;
  return C(a*.48+b*.32+c*.20);
}

// Directional brush language, different per material family.
function brushField(u:number,v:number,k:Kind){
  let dir:number;
  if(k==="bark") dir=v*7.0+Math.sin(u*TAU*1.6)*.42;
  else if(k==="snow") dir=u*3.2+v*.65+Math.sin(v*TAU*.72)*.30;
  else if(k==="ice") dir=u*2.2-v*2.9+Math.sin((u+v)*TAU*.6)*.26;
  else if(k==="dirt") dir=u*2.8+v*1.6+Math.sin(v*TAU)*.22;
  else dir=u*2.35+v*1.85+Math.sin((u-v)*TAU*.8)*.24;
  const wide=Math.sin(dir*TAU)*.5+.5;
  const broken=Math.sin((dir*.47+u*.38-v*.21)*TAU+1.4)*.5+.5;
  return C(wide*.70+broken*.30);
}

function faceField(u:number,v:number,k:Kind){
  const a=Math.sin((u*1.12+v*1.42)*TAU+.4)*.5+.5;
  const b=Math.sin((u*1.75-v*.82)*TAU+2.15)*.5+.5;
  const raw=C(a*.57+b*.43);
  // Broad planar grouping; not a micro-noise posterization.
  return Q(raw,k==="snow"||k==="ice"?4:5);
}

function weatherField(u:number,v:number){
  const sweep=Math.sin((u*.72+v*1.08+Math.sin((u+.17)*TAU)*.075)*TAU+.45)*.5+.5;
  const cross=Math.sin((u*1.18-v*.44)*TAU+1.55)*.5+.5;
  const broad=Math.sin((u*.48+v*.62)*TAU+2.20)*.5+.5;
  return C(sweep*.62+cross*.23+broad*.15);
}

function stylize(k:Kind,size:number,p:VfPaintedParams,b:Baker):Material{
  const cfg=CFG[k],paintScale=Math.max(.70,Math.min(1.45,Number(p.paintScale??1))),ss=Math.max(128,Math.round(size/cfg.source));
  const src=b(ss,{...p,normalStrength:5});if(!src.height)throw new Error(`${k}: no height`);
  const bc=makeTexture(size,size,3),met=makeTexture(size,size,1),rough=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),em=makeTexture(size,size,3);
  const wet=C(Number(p.wetness??0)),frost=C(Number(p.frost??0)),snow=C(Number(p.snowCoverage??0)),snowDepth=C(Number(p.snowDepth??.45));

  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size,i=y*size+x,j=i*3;
      const sc:RGB=[sample(src.baseColor,u,v,0),sample(src.baseColor,u,v,1),sample(src.baseColor,u,v,2)];
      const sh=sample(src.height,u,v,0),sa=src.ao?sample(src.ao,u,v,0):1;

      // A very wide source blur plus broad authored fields. No micro surface survives.
      const h0=(
        sample(src.height,u+.028,v,0)+sample(src.height,u-.028,v,0)+
        sample(src.height,u,v+.028,0)+sample(src.height,u,v-.028,0)+
        sample(src.height,u+.018,v+.018,0)+sample(src.height,u-.018,v-.018,0)+sh*2
      )/8;
      const mass=massField(u,v,k),brush=brushField(u,v,k),face=faceField(u,v,k);
      let h=C(.5+(h0-.5)*cfg.relief+(mass-.5)*.075+(face-.5)*.055+(brush-.5)*.018);
      let a=C(1-(1-sa)*cfg.ao);

      // Real material contributes only semantic value placement; the visible color is authored.
      const l=lum(sc);
      let t=C((l-cfg.lo)/Math.max(1e-5,cfg.hi-cfg.lo));
      t=C(t*.34+h*.24+mass*.21+face*.15+brush*.06);
      // Strong painted value groups: 5 authored zones maximum.
      t=Q(t,5);
      let col=pal(cfg.palette,t);

      // Brush tint: broad warm/cool strokes, never high-frequency grain.
      const cool:RGB=k==="snow"?[.275,.470,.710]:k==="ice"?[.040,.205,.350]:[.070,.085,.130];
      const warm:RGB=k==="snow"?[.975,.925,.835]:k==="ice"?[.690,.530,.445]:cfg.accent;
      col=M(col,brush>.52?warm:cool,Math.abs(brush-.5)*cfg.stroke*1.65*paintScale);

      // Designed accents on selected exposed masses.
      const accentMask=S(C((mass-.58)/.30))*S(C((h-.46)/.32));
      col=M(col,cfg.accent,accentMask*cfg.accentAmt);

      if(k==="granite"){
        // Large mineral islands, not photographic speckles.
        const quartz=S(C((face-.52)/.36))*S(C((mass-.44)/.42));
        const feld=S(C((brush-.55)/.32))*(1-quartz*.45);
        col=M(col,[.660,.590,.500],quartz*.24);
        col=M(col,[.620,.335,.305],feld*.18);
      } else if(k==="bark") {
        const groove=S(C((.43-brush)/.30));
        col=M(col,[.055,.040,.070],groove*.24);
        h=C(h-groove*.025);
      } else if(k==="snow") {
        const shadow=S(C((.55-h)/.22))+S(C((.48-mass)/.24))*.38;
        col=M(col,[.245,.455,.720],C(shadow)*.34);
        col=M(col,[.995,.965,.875],S(C((h-.55)/.28))*.30);
      } else if(k==="ice") {
        const deep=S(C((.52-h)/.30));
        col=M(col,[.025,.145,.300],deep*.30);
        col=M(col,[.720,.555,.455],S(C((brush-.66)/.25))*accentMask*.18);
      }

      const cav=1-a;
      col=col.map(q=>C(q*(1-cav*(k==="bark"?.13:.07)))) as RGB;

      // Very few roughness tiers: painted, matte and intentionally quiet.
      let r=cfg.rough[1];
      if(face<.34)r=cfg.rough[2]; else if(face>.66)r=cfg.rough[0];
      if(k==="ice")r=face>.66?cfg.rough[0]:face<.34?cfg.rough[2]:cfg.rough[1];

      if(k==="basalt"&&(wet>0||frost>0||snow>0)){
        const wf=weatherField(u,v),cavity=C(1-a);
        const wetPool=C(wet*(.66+.34*S(C((cavity-.015)/.22)))*(.88+.12*(1-wf)));
        col=M(col,[.018,.034,.052],wetPool*.50);r=L(r,.14,wetPool*.84);
        const exposed=.48+.52*S(C((h-.34)/.50));
        const frostMask=C(frost*exposed*(.88+.12*wf)*(1-wetPool*.28));
        col=M(col,[.455,.610,.735],frostMask*.48);r=L(r,.82,frostMask*.70);h=C(h+frostMask*.010);a=C(L(a,1,frostMask*.16));
        const drift=C(h*.56+wf*.44),threshold=L(.76,.36,snow),thick=C(S(C((drift-threshold)/.18))*snow),dust=C(S(C((snow-.52)/.34))*.24),snowMask=C(dust+(1-dust)*thick);
        const snowCol=M([.390,.555,.720],[.955,.945,.895],C(.32+h*.48+wf*.20));
        col=M(col,snowCol,snowMask*.94);r=L(r,.89,snowMask*.88);h=C(h+snowMask*(.020+.058*snowDepth)*(.72+.28*thick));a=C(L(a,1,snowMask*.58));
      }

      bc.data[j]=C(col[0]);bc.data[j+1]=C(col[1]);bc.data[j+2]=C(col[2]);
      met.data[i]=0;rough.data[i]=C(r);ao.data[i]=C(a);height.data[i]=C(h);
      em.data[j]=em.data[j+1]=em.data[j+2]=0;
    }
  }

  const normal=broadNormal(height,Math.max(4,Math.min(12,Number(p.normalStrength??cfg.n))),Math.max(5,Math.min(12,Number(p.normalRadius??cfg.r))));
  return{baseColor:bc,metallic:met,roughness:rough,normal,ao,height,emission:em};
}

export const bakeVfBasaltPainted=(s:number,p:VfPaintedParams={})=>stylize("basalt",s,p,bakeVfBasalt);
export const bakeVfGranitePainted=(s:number,p:VfPaintedParams={})=>stylize("granite",s,p,bakeVfGranite);
export const bakeVfDirtPainted=(s:number,p:VfPaintedParams={})=>stylize("dirt",s,p,bakeVfDirt);
export const bakeVfBarkPainted=(s:number,p:VfPaintedParams={})=>stylize("bark",s,p,bakeVfBark);
export const bakeVfSnowPainted=(s:number,p:VfPaintedParams={})=>stylize("snow",s,p,bakeVfSnow);
export const bakeVfIcePainted=(s:number,p:VfPaintedParams={})=>stylize("ice",s,p,bakeVfIce);
