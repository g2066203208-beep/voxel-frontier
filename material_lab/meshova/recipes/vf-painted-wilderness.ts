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
export type VfPaintedParams={seed?:number;paintScale?:number;normalStrength?:number;normalRadius?:number;[key:string]:unknown};
type Cfg={shadow:RGB;mid:RGB;light:RGB;accent:RGB;lo:number;hi:number;paint:number;hGain:number;rough:[number,number,number];n:number;r:number;ao:number;accentAmt:number};
const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const W=(x:number)=>x-Math.floor(x);
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t);};
const lum=(c:RGB)=>c[0]*.24+c[1]*.68+c[2]*.08;

const CFG:Record<Kind,Cfg>={
  basalt:{shadow:[.035,.050,.070],mid:[.105,.115,.120],light:[.220,.205,.175],accent:[.270,.135,.075],lo:.025,hi:.245,paint:4.8,hGain:1.08,rough:[.70,.78,.86],n:10.5,r:5,ao:1.12,accentAmt:.10},
  granite:{shadow:[.090,.085,.100],mid:[.205,.175,.165],light:[.430,.390,.330],accent:[.500,.245,.195],lo:.050,hi:.470,paint:4.4,hGain:1.04,rough:[.66,.76,.84],n:9.8,r:5,ao:1.10,accentAmt:.14},
  dirt:{shadow:[.075,.045,.035],mid:[.215,.105,.055],light:[.425,.245,.120],accent:[.520,.315,.165],lo:.025,hi:.360,paint:4.6,hGain:1.05,rough:[.76,.84,.90],n:9.5,r:5,ao:1.14,accentAmt:.09},
  bark:{shadow:[.050,.035,.040],mid:[.165,.080,.045],light:[.330,.185,.095],accent:[.470,.250,.120],lo:.020,hi:.300,paint:4.2,hGain:1.08,rough:[.74,.82,.89],n:10.8,r:4,ao:1.18,accentAmt:.10},
  snow:{shadow:[.430,.540,.680],mid:[.735,.800,.860],light:[.965,.955,.905],accent:[.760,.620,.610],lo:.400,hi:.995,paint:5.2,hGain:1.03,rough:[.76,.84,.91],n:7.8,r:6,ao:1.06,accentAmt:.035},
  ice:{shadow:[.055,.165,.245],mid:[.150,.355,.455],light:[.545,.705,.730],accent:[.660,.510,.430],lo:.055,hi:.630,paint:5.0,hGain:1.02,rough:[.18,.28,.42],n:7.2,r:6,ao:1.05,accentAmt:.04},
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

function palette(cfg:Cfg,t:number){
  const x=C(t);
  return x<.52?M(cfg.shadow,cfg.mid,S(x/.52)):M(cfg.mid,cfg.light,S((x-.52)/.48));
}

function painterField(u:number,v:number,scale:number){
  const a=Math.sin((u*3+v*2)*TAU+.7)*.5+.5;
  const b=Math.sin((u*5-v*3)*TAU+1.8)*.5+.5;
  const c=Math.sin((u*2+v*5)*TAU+2.5)*.5+.5;
  return C((a*.46+b*.34+c*.20-.5)*(.22*scale)+.5);
}

function stylize(k:Kind,size:number,p:VfPaintedParams,b:Baker):Material{
  const cfg=CFG[k],paintScale=Math.max(.65,Math.min(1.5,Number(p.paintScale??1))),ss=Math.max(224,Math.round(size/cfg.paint));
  const src=b(ss,{...p,normalStrength:7});if(!src.height)throw new Error(`${k}: no height`);
  const bc=makeTexture(size,size,3),met=makeTexture(size,size,1),rough=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),em=makeTexture(size,size,3);
  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size,i=y*size+x,j=i*3;
      const sc:RGB=[sample(src.baseColor,u,v,0),sample(src.baseColor,u,v,1),sample(src.baseColor,u,v,2)];
      const sh=sample(src.height,u,v,0),sa=src.ao?sample(src.ao,u,v,0):1,sr=sample(src.roughness,u,v,0);
      const h0=(sample(src.height,u+.010,v,0)+sample(src.height,u-.010,v,0)+sample(src.height,u,v+.010,0)+sample(src.height,u,v-.010,0)+sh*2)/6;
      const h=C(.5+(h0-.5)*cfg.hGain);height.data[i]=h;
      const a=C(1-(1-sa)*cfg.ao);ao.data[i]=a;
      const pf=painterField(u,v,paintScale);
      const localLum=lum(sc);let t=C((localLum-cfg.lo)/Math.max(1e-5,cfg.hi-cfg.lo));
      t=C(t+(h-.5)*.23+(pf-.5)*.10-(1-a)*.08);
      let col=palette(cfg,t);
      const sourceHueScale=Math.max(.0001,localLum);const targetLum=Math.max(.02,lum(col));
      const hue:RGB=[C(sc[0]/sourceHueScale*targetLum),C(sc[1]/sourceHueScale*targetLum),C(sc[2]/sourceHueScale*targetLum)];
      col=M(col,hue,k==="granite"?.22:.10);
      const accentGate=S(C((pf-.62)/.28))*S(C((h-.46)/.34));
      col=M(col,cfg.accent,accentGate*cfg.accentAmt);
      if(k==="snow")col=M(col,[.975,.985,.995],S(C((h-.55)/.30))*.32);
      if(k==="ice")col=M(col,[.070,.285,.390],S(C((1-a-.03)/.30))*.25);
      const cav=(1-a);col=col.map(q=>C(q*(1-cav*(k==="bark"?.22:.12)))) as RGB;
      bc.data[j]=col[0];bc.data[j+1]=col[1];bc.data[j+2]=col[2];
      met.data[i]=0;
      let r=sr<.55?cfg.rough[0]:sr<.76?cfg.rough[1]:cfg.rough[2];
      if(k==="ice")r=sr<.28?cfg.rough[0]:sr<.50?cfg.rough[1]:cfg.rough[2];
      rough.data[i]=r;
      em.data[j]=em.data[j+1]=em.data[j+2]=0;
    }
  }
  const normal=broadNormal(height,Math.max(5,Math.min(16,Number(p.normalStrength??cfg.n))),Math.max(2,Math.min(8,Number(p.normalRadius??cfg.r))));
  return{baseColor:bc,metallic:met,roughness:rough,normal,ao,height,emission:em};
}

export const bakeVfBasaltPainted=(s:number,p:VfPaintedParams={})=>stylize("basalt",s,p,bakeVfBasalt);
export const bakeVfGranitePainted=(s:number,p:VfPaintedParams={})=>stylize("granite",s,p,bakeVfGranite);
export const bakeVfDirtPainted=(s:number,p:VfPaintedParams={})=>stylize("dirt",s,p,bakeVfDirt);
export const bakeVfBarkPainted=(s:number,p:VfPaintedParams={})=>stylize("bark",s,p,bakeVfBark);
export const bakeVfSnowPainted=(s:number,p:VfPaintedParams={})=>stylize("snow",s,p,bakeVfSnow);
export const bakeVfIcePainted=(s:number,p:VfPaintedParams={})=>stylize("ice",s,p,bakeVfIce);
