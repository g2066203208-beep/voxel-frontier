import { makeTexture, type Material } from "../../src/index.js";
import { bakeVfBasalt } from "./vf-basalt.js";
import { bakeVfGranite } from "./vf-granite.js";
import { bakeVfDirt } from "./vf-dirt.js";
import { bakeVfBark } from "./vf-bark.js";
import {
  bakeVfSandstone, bakeVfLimestone, bakeVfGravel, bakeVfSand, bakeVfWetMud,
  bakeVfWoodPlank, bakeVfIronOre, bakeVfCopperOre, bakeVfCoal, bakeVfSnow, bakeVfIce,
} from "./vf-world-surfaces.js";

type RGB=[number,number,number];
type Tex={width:number;height:number;channels:number;data:Float32Array};
type Baker=(size:number,params?:any)=>Material;
type Kind="basalt"|"granite"|"dirt"|"bark"|"sandstone"|"limestone"|"gravel"|"sand"|"wetMud"|"woodPlank"|"ironOre"|"copperOre"|"coal"|"snow"|"ice";
export type VfCartoonParams={seed?:number;blockiness?:number;paletteSteps?:number;stylizedNormalStrength?:number;normalRadius?:number;[key:string]:unknown};
type Cfg={palette:RGB[];lo:number;hi:number;hue:number;block:number;steps:number;hBands:number;hMix:number;hGain:number;n:number;nRad:number;rough:number[];ao:number;cavity:number;lift:number};
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const W=(x:number)=>x-Math.floor(x);
const Q=(x:number,n:number)=>n<=1?0:Math.round(C(x)*(n-1))/(n-1);
const lum=(c:RGB)=>c[0]*.24+c[1]*.68+c[2]*.08;

const S:Record<Kind,Cfg>={
  basalt:{palette:[[.028,.040,.052],[.060,.075,.088],[.100,.118,.128],[.150,.168,.170],[.210,.220,.212]],lo:.025,hi:.24,hue:.13,block:4.2,steps:5,hBands:12,hMix:.48,hGain:1.16,n:16,nRad:3,rough:[.58,.70,.82],ao:1.42,cavity:.30,lift:.10},
  granite:{palette:[[.060,.052,.052],[.130,.092,.088],[.215,.155,.145],[.325,.270,.245],[.470,.430,.390]],lo:.035,hi:.48,hue:.48,block:3.1,steps:6,hBands:13,hMix:.40,hGain:1.10,n:15,nRad:2,rough:[.52,.64,.76],ao:1.24,cavity:.18,lift:.08},
  dirt:{palette:[[.055,.022,.011],[.110,.046,.019],[.200,.086,.032],[.315,.150,.062],[.425,.240,.110]],lo:.025,hi:.34,hue:.18,block:4.0,steps:5,hBands:11,hMix:.46,hGain:1.15,n:15,nRad:3,rough:[.70,.81,.90],ao:1.32,cavity:.26,lift:.08},
  bark:{palette:[[.040,.016,.008],[.082,.031,.014],[.150,.058,.023],[.240,.108,.043],[.335,.178,.078]],lo:.018,hi:.29,hue:.20,block:3.5,steps:5,hBands:11,hMix:.50,hGain:1.17,n:16,nRad:2,rough:[.66,.78,.89],ao:1.44,cavity:.30,lift:.09},
  sandstone:{palette:[[.085,.036,.015],[.165,.075,.026],[.280,.138,.047],[.415,.240,.095],[.560,.365,.175]],lo:.045,hi:.48,hue:.16,block:3.8,steps:5,hBands:12,hMix:.40,hGain:1.13,n:15,nRad:3,rough:[.68,.78,.87],ao:1.28,cavity:.22,lift:.09},
  limestone:{palette:[[.105,.098,.085],[.195,.184,.160],[.315,.300,.265],[.445,.430,.380],[.590,.580,.525]],lo:.075,hi:.60,hue:.10,block:3.8,steps:5,hBands:12,hMix:.38,hGain:1.12,n:15,nRad:3,rough:[.64,.76,.86],ao:1.24,cavity:.18,lift:.07},
  gravel:{palette:[[.085,.080,.073],[.125,.122,.115],[.185,.184,.170],[.260,.250,.225],[.355,.335,.295]],lo:.035,hi:.43,hue:.38,block:3.3,steps:6,hBands:12,hMix:.42,hGain:1.22,n:18,nRad:2,rough:[.68,.80,.89],ao:1.34,cavity:.22,lift:.10},
  sand:{palette:[[.130,.080,.034],[.235,.155,.070],[.365,.260,.125],[.505,.395,.210],[.645,.540,.325]],lo:.10,hi:.64,hue:.08,block:4.2,steps:5,hBands:12,hMix:.28,hGain:1.12,n:15,nRad:4,rough:[.73,.82,.90],ao:1.14,cavity:.12,lift:.06},
  wetMud:{palette:[[.035,.017,.010],[.072,.034,.018],[.125,.062,.030],[.190,.103,.050],[.265,.162,.085]],lo:.018,hi:.25,hue:.14,block:3.8,steps:5,hBands:11,hMix:.40,hGain:1.15,n:16,nRad:3,rough:[.26,.45,.68],ao:1.36,cavity:.24,lift:.07},
  woodPlank:{palette:[[.060,.024,.010],[.125,.052,.019],[.220,.106,.040],[.335,.185,.075],[.455,.285,.130]],lo:.035,hi:.46,hue:.22,block:3.4,steps:6,hBands:12,hMix:.36,hGain:1.10,n:15,nRad:2,rough:[.56,.68,.80],ao:1.26,cavity:.20,lift:.08},
  ironOre:{palette:[[.030,.034,.038],[.062,.068,.073],[.110,.120,.124],[.175,.180,.178],[.255,.248,.230]],lo:.020,hi:.28,hue:.22,block:3.5,steps:5,hBands:12,hMix:.40,hGain:1.14,n:16,nRad:3,rough:[.56,.68,.80],ao:1.32,cavity:.24,lift:.09},
  copperOre:{palette:[[.032,.034,.036],[.065,.070,.068],[.115,.110,.090],[.185,.125,.074],[.300,.180,.095]],lo:.020,hi:.32,hue:.26,block:3.5,steps:5,hBands:12,hMix:.40,hGain:1.14,n:16,nRad:3,rough:[.52,.65,.78],ao:1.32,cavity:.24,lift:.09},
  coal:{palette:[[.015,.019,.024],[.030,.037,.044],[.052,.062,.070],[.082,.093,.100],[.125,.135,.138]],lo:.010,hi:.16,hue:.06,block:3.7,steps:5,hBands:12,hMix:.40,hGain:1.17,n:16,nRad:3,rough:[.64,.76,.86],ao:1.38,cavity:.28,lift:.09},
  snow:{palette:[[.475,.535,.610],[.620,.685,.750],[.770,.820,.865],[.895,.925,.952],[.975,.985,.995]],lo:.40,hi:.99,hue:.04,block:4.2,steps:4,hBands:12,hMix:.26,hGain:1.11,n:15,nRad:4,rough:[.72,.82,.90],ao:1.10,cavity:.09,lift:.05},
  ice:{palette:[[.065,.150,.210],[.100,.240,.315],[.155,.350,.425],[.255,.505,.575],[.435,.695,.740]],lo:.050,hi:.62,hue:.12,block:4.0,steps:5,hBands:12,hMix:.24,hGain:1.08,n:14,nRad:4,rough:[.10,.18,.30],ao:1.12,cavity:.10,lift:.06},
};

function sample(t:Tex,u:number,v:number,ch:number){const x=W(u)*t.width,y=W(v)*t.height,x0=Math.floor(x)%t.width,y0=Math.floor(y)%t.height,x1=(x0+1)%t.width,y1=(y0+1)%t.height,tx=x-Math.floor(x),ty=y-Math.floor(y);const at=(xx:number,yy:number)=>t.data[(yy*t.width+xx)*t.channels+ch];return L(L(at(x0,y0),at(x1,y0),tx),L(at(x0,y1),at(x1,y1),tx),ty);}
function pal(p:RGB[],t:number){const x=C(t)*(p.length-1),i=Math.min(p.length-2,Math.floor(x));return M(p[i],p[i+1],x-i);}
function nearest(v:number,b:number[]){let z=b[0],d=Math.abs(v-z);for(let i=1;i<b.length;i++){const q=Math.abs(v-b[i]);if(q<d){z=b[i];d=q;}}return z;}

function colorFor(k:Kind,src:RGB,h:number,ao:number,m:number,cfg:Cfg,steps:number):RGB{
  const l=lum(src);let t=C((l-cfg.lo)/Math.max(1e-5,cfg.hi-cfg.lo));t=Q(C(t+(h-.5)*cfg.lift-(1-ao)*.14),steps);let out=pal(cfg.palette,t);
  const sl=Math.max(1e-4,l),tl=Math.max(.01,lum(out));const hue:RGB=[C(src[0]/sl*tl),C(src[1]/sl*tl),C(src[2]/sl*tl)];out=M(out,hue,cfg.hue);const cav=1-ao;out=out.map(x=>C(x*(1-cav*cfg.cavity))) as RGB;
  if(k==="granite"){const mica=l<.070,feld=src[0]>src[1]*1.08&&src[0]>src[2]*1.05;if(mica)out=M(out,[.032,.034,.038],.72);else if(feld)out=M(out,[.345,.195,.180],.42);else if(l>.28)out=M(out,[.520,.490,.445],.28);}
  else if(k==="ironOre"&&m>.10){const rust=src[0]>src[2]*1.30;out=rust?M(out,[.285,.095,.035],.46):M(out,[.250,.270,.285],.52);}
  else if(k==="copperOre"&&m>.08){const pat=src[1]>src[0]*1.12;out=pat?M(out,[.060,.285,.225],.58):M(out,[.440,.165,.060],.58);}
  else if(k==="wetMud"&&cav>.12)out=M(out,[.034,.017,.010],C(cav*1.25));
  else if(k==="snow")out=M(out,[.850,.910,.970],.24);
  else if(k==="ice")out=M(out,[.080,.335,.445],.16);
  return out;
}

function broadNormal(h:Tex,strength:number,radius:number){const n=makeTexture(h.width,h.height,3),w=h.width,hh=h.height,r=Math.max(1,Math.round(radius));const at=(x:number,y:number)=>h.data[((y%hh+hh)%hh)*w+((x%w+w)%w)];for(let y=0;y<hh;y++)for(let x=0;x<w;x++){const dx=(at(x+r,y)-at(x-r,y))*strength,dy=(at(x,y+r)-at(x,y-r))*strength;let nx=-dx,ny=dy,nz=1;const l=Math.hypot(nx,ny,nz)||1;nx/=l;ny/=l;nz/=l;const i=(y*w+x)*3;n.data[i]=nx*.5+.5;n.data[i+1]=ny*.5+.5;n.data[i+2]=nz*.5+.5;}return n;}

function stylize(k:Kind,size:number,p:VfCartoonParams,b:Baker):Material{
  const cfg=S[k],block=Math.max(2.4,Math.min(8,Number(p.blockiness??cfg.block))),ss=Math.max(256,Math.round(size/block)),src=b(ss,{...p,normalStrength:8});if(!src.height)throw new Error(`${k}: no height`);
  const bc=makeTexture(size,size,3),met=makeTexture(size,size,1),rough=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),em=makeTexture(size,size,3),steps=Math.max(3,Math.min(6,Math.round(Number(p.paletteSteps??cfg.steps))));
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){const u=(x+.5)/size,i=y*size+x,j=i*3,scol:RGB=[sample(src.baseColor,u,v,0),sample(src.baseColor,u,v,1),sample(src.baseColor,u,v,2)],sh=sample(src.height,u,v,0),sa=src.ao?sample(src.ao,u,v,0):1,sr=sample(src.roughness,u,v,0),sm=sample(src.metallic,u,v,0);const terr=Q(sh,cfg.hBands);let h=C(.5+((terr*cfg.hMix+sh*(1-cfg.hMix))-.5)*cfg.hGain),a=C(1-(1-sa)*cfg.ao);h=C(h-(1-a)*(k==="bark"||k==="gravel"?.035:.018));height.data[i]=h;ao.data[i]=Q(a,8);
    let m=0;if(k==="ironOre"||k==="copperOre")m=sm>.22?.86:sm>.085?.42:0;met.data[i]=m;const c=colorFor(k,scol,h,ao.data[i],sm,cfg,steps);bc.data[j]=c[0];bc.data[j+1]=c[1];bc.data[j+2]=c[2];let r=nearest(sr,cfg.rough);if(k==="wetMud"&&ao.data[i]<.80)r=.20;if((k==="ironOre"||k==="copperOre")&&m>.5)r=k==="copperOre"?.38:.42;if(k==="ice"&&ao.data[i]<.88)r=.12;rough.data[i]=C(r);em.data[j]=em.data[j+1]=em.data[j+2]=0;}}
  const normal=broadNormal(height,Math.max(8,Math.min(24,Number(p.stylizedNormalStrength??cfg.n))),Math.max(1,Math.min(6,Number(p.normalRadius??cfg.nRad))));return{baseColor:bc,metallic:met,roughness:rough,normal,ao,height,emission:em};
}

export const bakeVfBasaltCartoonWorld=(s:number,p:VfCartoonParams={})=>stylize("basalt",s,p,bakeVfBasalt);
export const bakeVfGraniteCartoon=(s:number,p:VfCartoonParams={})=>stylize("granite",s,p,bakeVfGranite);
export const bakeVfDirtCartoon=(s:number,p:VfCartoonParams={})=>stylize("dirt",s,p,bakeVfDirt);
export const bakeVfBarkCartoon=(s:number,p:VfCartoonParams={})=>stylize("bark",s,p,bakeVfBark);
export const bakeVfSandstoneCartoon=(s:number,p:VfCartoonParams={})=>stylize("sandstone",s,p,bakeVfSandstone);
export const bakeVfLimestoneCartoon=(s:number,p:VfCartoonParams={})=>stylize("limestone",s,p,bakeVfLimestone);
export const bakeVfGravelCartoon=(s:number,p:VfCartoonParams={})=>stylize("gravel",s,p,bakeVfGravel);
export const bakeVfSandCartoon=(s:number,p:VfCartoonParams={})=>stylize("sand",s,p,bakeVfSand);
export const bakeVfWetMudCartoon=(s:number,p:VfCartoonParams={})=>stylize("wetMud",s,p,bakeVfWetMud);
export const bakeVfWoodPlankCartoon=(s:number,p:VfCartoonParams={})=>stylize("woodPlank",s,p,bakeVfWoodPlank);
export const bakeVfIronOreCartoon=(s:number,p:VfCartoonParams={})=>stylize("ironOre",s,p,bakeVfIronOre);
export const bakeVfCopperOreCartoon=(s:number,p:VfCartoonParams={})=>stylize("copperOre",s,p,bakeVfCopperOre);
export const bakeVfCoalCartoon=(s:number,p:VfCartoonParams={})=>stylize("coal",s,p,bakeVfCoal);
export const bakeVfSnowCartoon=(s:number,p:VfCartoonParams={})=>stylize("snow",s,p,bakeVfSnow);
export const bakeVfIceCartoon=(s:number,p:VfCartoonParams={})=>stylize("ice",s,p,bakeVfIce);
