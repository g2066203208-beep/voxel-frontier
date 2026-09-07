import { makeTexture, type Material } from "../../src/index.js";
import { bakeVfBark } from "./vf-bark.js";
import { bakeVfSnow, bakeVfIce } from "./vf-world-surfaces.js";

type RGB=[number,number,number];
export type VfPaintedParams={
  seed?:number;cells?:number;jitter?:number;heightLevels?:number;crackWidth?:number;crackDepth?:number;
  bevel?:number;distortion?:number;damage?:number;microDetail?:number;normalStrength?:number;
  anisotropy?:number;facetStrength?:number;strokeStrength?:number;[key:string]:unknown
};
type RockKind="basalt"|"granite"|"dirt";
type Cfg={
  shadow:RGB;mid:RGB;light:RGB;edge:RGB;crack:RGB;chip:RGB;cool:RGB;
  roughBase:number;roughTop:number;roughCrack:number;
  defaults:{cells:number;jitter:number;heightLevels:number;crackWidth:number;crackDepth:number;bevel:number;distortion:number;damage:number;microDetail:number;normalStrength:number;anisotropy:number;facetStrength:number;strokeStrength:number}
};
type CellSample={nearest:number;second:number;borderGap:number;localX:number;localY:number;random:number;random2:number;random3:number;random4:number;componentId:number;neighborId:number};

const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t);};
const wrap01=(x:number)=>x-Math.floor(x);
const wrapInt=(x:number,n:number)=>((x%n)+n)%n;

const CFG:Record<RockKind,Cfg>={
  basalt:{shadow:[.032,.046,.072],mid:[.105,.122,.142],light:[.275,.238,.195],edge:[.455,.350,.235],crack:[.014,.023,.038],chip:[.485,.245,.132],cool:[.050,.078,.132],roughBase:.80,roughTop:.73,roughCrack:.92,defaults:{cells:4,jitter:.76,heightLevels:4,crackWidth:.052,crackDepth:.76,bevel:.085,distortion:.20,damage:.42,microDetail:.010,normalStrength:9.4,anisotropy:.48,facetStrength:1.00,strokeStrength:.26}},
  granite:{shadow:[.100,.096,.128],mid:[.238,.202,.195],light:[.535,.438,.355],edge:[.675,.565,.445],crack:[.040,.042,.060],chip:[.640,.355,.275],cool:[.115,.132,.188],roughBase:.77,roughTop:.69,roughCrack:.89,defaults:{cells:4,jitter:.72,heightLevels:4,crackWidth:.048,crackDepth:.66,bevel:.095,distortion:.18,damage:.36,microDetail:.012,normalStrength:9.0,anisotropy:.42,facetStrength:.92,strokeStrength:.24}},
  dirt:{shadow:[.090,.047,.044],mid:[.235,.108,.057],light:[.505,.292,.140],edge:[.560,.365,.195],crack:[.055,.028,.028],chip:[.610,.320,.145],cool:[.118,.072,.091],roughBase:.87,roughTop:.81,roughCrack:.95,defaults:{cells:5,jitter:.80,heightLevels:4,crackWidth:.045,crackDepth:.50,bevel:.105,distortion:.24,damage:.22,microDetail:.010,normalStrength:8.0,anisotropy:.32,facetStrength:.66,strokeStrength:.21}}
};

function num(p:VfPaintedParams,key:string,fallback:number){const v=Number(p[key]);return Number.isFinite(v)?v:fallback;}
function hash01(x:number,y:number,seed:number,salt=0){
  let h=Math.imul(x,0x1f123bb5)^Math.imul(y,0x5f356495)^Math.imul(seed,0x2c9277b5)^Math.imul(salt,0x27d4eb2d);
  h=Math.imul(h^(h>>>15),0x2c1b3c6d);h=Math.imul(h^(h>>>12),0x297a2d39);h^=h>>>15;return (h>>>0)/0xffffffff;
}
function periodicNoise(u:number,v:number,seed:number,frequency:number){
  let sum=0,weight=0;
  for(let o=0;o<3;o++){
    const f=Math.max(1,Math.round(frequency*2**o));
    const kx=f+1+Math.floor(hash01(o,1,seed,11)*3),ky=f+1+Math.floor(hash01(o,2,seed,17)*3),phase=hash01(o,3,seed,23)*TAU,a=1/2**o;
    sum+=Math.sin((u*kx+v*ky)*TAU+phase)*a;
    sum+=Math.cos((u*ky-v*kx)*TAU+phase*.73)*a*.5;
    weight+=a*1.5;
  }
  return C(sum/Math.max(weight,1e-6)*.5+.5);
}

function sampleAngularCell(u:number,v:number,cells:number,jitter:number,seed:number,distortion:number,anisotropy:number):CellSample{
  const warpF=Math.max(1,Math.floor(cells*.55));
  const wu=wrap01(u+(periodicNoise(u,v,seed+101,warpF)-.5)*distortion/cells);
  const wv=wrap01(v+(periodicNoise(u,v,seed+211,warpF)-.5)*distortion/cells);
  const px=wu*cells,py=wv*cells,bx=Math.floor(px),by=Math.floor(py);
  let nearest=Infinity,second=Infinity,nfx=0,nfy=0,ncx=0,ncy=0,scx=0,scy=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const rx=bx+ox,ry=by+oy,cx=wrapInt(rx,cells),cy=wrapInt(ry,cells);
    const fx=rx+.5+(hash01(cx,cy,seed,31)-.5)*jitter,fy=ry+.5+(hash01(cx,cy,seed,47)-.5)*jitter;
    const dx=px-fx,dy=py-fy;
    const ang=hash01(cx,cy,seed,53)*TAU,ca=Math.cos(ang),sa=Math.sin(ang);
    const ax=dx*ca+dy*sa,ay=-dx*sa+dy*ca;
    const stretch=1+anisotropy*(hash01(cx,cy,seed,59)*2-1);
    const sx=Math.max(.45,stretch),sy=Math.max(.55,stretch);
    const de=Math.hypot(ax/sx,ay*sy),dl=(Math.abs(ax)/sx+Math.abs(ay)*sy)*.78;
    const d=de*.52+dl*.48;
    if(d<nearest){second=nearest;scx=ncx;scy=ncy;nearest=d;nfx=fx;nfy=fy;ncx=cx;ncy=cy;}
    else if(d<second){second=d;scx=cx;scy=cy;}
  }
  return{
    nearest,second,borderGap:Math.max(0,second-nearest),localX:px-nfx,localY:py-nfy,
    random:hash01(ncx,ncy,seed,71),random2:hash01(ncx,ncy,seed,89),random3:hash01(ncx,ncy,seed,107),random4:hash01(ncx,ncy,seed,119),
    componentId:hash01(ncx,ncy,seed,131),neighborId:hash01(scx,scy,seed,131)
  };
}

function pairNoise(a:number,b:number,salt:number){
  const lo=Math.min(a,b),hi=Math.max(a,b);
  return wrap01(Math.sin((lo*173.17+hi*337.31+salt)*12.9898)*43758.5453123);
}

function palette(cfg:Cfg,t:number):RGB{const x=C(t);return x<.52?M(cfg.shadow,cfg.mid,S(x/.52)):M(cfg.mid,cfg.light,S((x-.52)/.48));}

function localStroke(cell:CellSample,seed:number,strength:number){
  const a=(cell.random2*.78+.11)*TAU,ca=Math.cos(a),sa=Math.sin(a);
  const along=cell.localX*ca+cell.localY*sa,cross=-cell.localX*sa+cell.localY*ca;
  const center=(cell.random3-.5)*.20,width=.030+.050*cell.random4,length=.24+.30*cell.random;
  const side=1-S((Math.abs(cross-center)-width*.45)/Math.max(width*.75,1e-4));
  const end=1-S((Math.abs(along)-length*.58)/Math.max(length*.42,1e-4));
  const breakup=.55+.45*periodicNoise(wrap01(cell.componentId+along*.13),wrap01(cell.random4+cross*.17),seed+701,5);
  return C(side*end*breakup*strength);
}

function normalFromHeight(height:ReturnType<typeof makeTexture>,strength:number){
  const out=makeTexture(height.width,height.height,3),w=height.width,h=height.height,d=height.data;
  const at=(x:number,y:number)=>d[((y%h+h)%h)*w+((x%w+w)%w)];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const dx=(at(x+1,y)-at(x-1,y))*strength,dy=(at(x,y+1)-at(x,y-1))*strength;
    let nx=-dx,ny=dy,nz=1,q=Math.hypot(nx,ny,nz)||1;nx/=q;ny/=q;nz/=q;
    const i=(y*w+x)*3;out.data[i]=nx*.5+.5;out.data[i+1]=ny*.5+.5;out.data[i+2]=nz*.5+.5;
  }
  return out;
}

function bakePaintedFacetedRock(kind:RockKind,size:number,p:VfPaintedParams={}):Material{
  const cfg=CFG[kind],d=cfg.defaults,seed=Math.floor(num(p,"seed",kind==="basalt"?240914:kind==="granite"?310402:420503));
  const cells=Math.max(3,Math.floor(num(p,"cells",d.cells))),jitter=C(num(p,"jitter",d.jitter)),levels=Math.max(2,Math.floor(num(p,"heightLevels",d.heightLevels)));
  const crackWidth=C(num(p,"crackWidth",d.crackWidth)),crackDepth=C(num(p,"crackDepth",d.crackDepth)),bevel=C(num(p,"bevel",d.bevel));
  const distortion=Math.max(0,Math.min(1.5,num(p,"distortion",d.distortion))),damage=C(num(p,"damage",d.damage)),micro=C(num(p,"microDetail",d.microDetail));
  const normalStrength=Math.max(0,num(p,"normalStrength",d.normalStrength)),anisotropy=C(num(p,"anisotropy",d.anisotropy)),facetStrength=C(num(p,"facetStrength",d.facetStrength)),strokeStrength=C(num(p,"strokeStrength",d.strokeStrength));

  const bc=makeTexture(size,size,3),met=makeTexture(size,size,1),rough=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),em=makeTexture(size,size,3);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x,j=i*3;
    const cell=sampleAngularCell(u,v,cells,jitter,seed,distortion,anisotropy);
    const rawCrack=1-S((cell.borderGap-crackWidth*.38)/Math.max(crackWidth*.62,1e-5));
    const rawEdge=1-S((cell.borderGap-crackWidth)/Math.max(bevel,1e-5));
    const edgeChoice=pairNoise(cell.componentId,cell.neighborId,1.7);
    const threshold=kind==="basalt"?.56:kind==="granite"?.61:.50;
    const fractureGate=edgeChoice>threshold?1:0;
    const crack=rawCrack*fractureGate;
    const crease=rawEdge*(1-fractureGate);
    const damageNoise=periodicNoise(u,v,seed+401,cells*2.1);
    const damageGate=fractureGate*(cell.random3>.42?1:0);
    const chipped=C(rawEdge*damageGate*S((damageNoise-.54)/.26)*damage);

    const a1=cell.random2*TAU,a2=(cell.random4*.73+.19)*TAU;
    const p1=(cell.localX*Math.cos(a1)+cell.localY*Math.sin(a1))*.125;
    const p2=(cell.localX*Math.cos(a2)+cell.localY*Math.sin(a2))*.095-.014;
    const p3=(-cell.localX*Math.sin(a1)+cell.localY*Math.cos(a1))*.070+.010;
    const face=Math.max(p1,p2,p3)*facetStrength;
    const band=Math.round(cell.random*(levels-1))/(levels-1);
    const base=.465+(band-.5)*.070+(cell.random4-.5)*.018;
    const topFace=C(.50+face*4.8+(band-.5)*.12);
    const microBreak=(periodicNoise(u,v,seed+503,cells*7)-.5)*.010*micro;
    let h=C(base+face+microBreak-crack*crackDepth*.23-crease*.006-chipped*.075);
    const cavity=C(crack*.82+crease*.055+chipped*.16);
    const aoV=C(1-cavity*.44);

    const idWarm=.5+.5*Math.sin((cell.componentId*1.61+.13)*TAU);
    let col=palette(cfg,C((h-.19)/.58+(cell.random-.5)*.10));
    col=M(col,idWarm>.5?cfg.light:cfg.cool,Math.abs(idWarm-.5)*.13);

    const stroke=localStroke(cell,seed,strokeStrength)*(1-crack)*(1-chipped*.45);
    col=M(col,cfg.light,stroke*(.28+.42*topFace));
    const coolWash=C((1-topFace)*.34+cavity*.28);
    col=M(col,cfg.cool,coolWash*.20);

    const highlightGate=pairNoise(cell.componentId,cell.neighborId,5.3)>.72?1:0;
    const edgeHighlight=C((rawEdge-rawCrack*.94)*(0.16+.58*topFace)*(1-chipped*.70)*highlightGate);
    col=M(col,cfg.edge,edgeHighlight*.34);
    col=M(col,cfg.chip,chipped*.30);
    col=M(col,cfg.crack,crack*.68);

    if(kind==="granite"){
      const quartz=C(S((cell.componentId-.30)/.38)*(1-crack)),feld=C(S((.66-cell.componentId)/.42)*(1-crack));
      col=M(col,[.735,.650,.535],quartz*.15);col=M(col,[.610,.330,.285],feld*.11);
    }else if(kind==="dirt"){
      const dry=C(S((topFace-.58)/.28)*(1-crack));col=M(col,[.610,.375,.185],dry*.08);
    }

    let r=L(cfg.roughBase,cfg.roughTop,topFace*.72);r=L(r,cfg.roughCrack,crack*.90);r=C(r-chipped*.020+stroke*.012);
    bc.data[j]=C(col[0]);bc.data[j+1]=C(col[1]);bc.data[j+2]=C(col[2]);met.data[i]=0;rough.data[i]=Math.max(.04,r);ao.data[i]=aoV;height.data[i]=h;em.data[j]=em.data[j+1]=em.data[j+2]=0;
  }
  const normal=normalFromHeight(height,normalStrength);
  return{baseColor:bc,metallic:met,roughness:rough,normal,ao,height,emission:em};
}

export const bakeVfBasaltPainted=(s:number,p:VfPaintedParams={})=>bakePaintedFacetedRock("basalt",s,p);
export const bakeVfGranitePainted=(s:number,p:VfPaintedParams={})=>bakePaintedFacetedRock("granite",s,p);
export const bakeVfDirtPainted=(s:number,p:VfPaintedParams={})=>bakePaintedFacetedRock("dirt",s,p);
export const bakeVfBarkPainted=(s:number,p:VfPaintedParams={})=>bakeVfBark(s,p);
export const bakeVfSnowPainted=(s:number,p:VfPaintedParams={})=>bakeVfSnow(s,p);
export const bakeVfIcePainted=(s:number,p:VfPaintedParams={})=>bakeVfIce(s,p);
