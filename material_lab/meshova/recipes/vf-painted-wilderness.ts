import { bakeStylizedCellRock, makeTexture, type Material } from "../../src/index.js";
import { bakeVfBark } from "./vf-bark.js";
import { bakeVfSnow, bakeVfIce } from "./vf-world-surfaces.js";

type RGB=[number,number,number];
export type VfPaintedParams={seed?:number;cells?:number;jitter?:number;heightLevels?:number;crackWidth?:number;crackDepth?:number;bevel?:number;distortion?:number;damage?:number;microDetail?:number;normalStrength?:number;[key:string]:unknown};
type RockKind="basalt"|"granite"|"dirt";
type Cfg={shadow:RGB;mid:RGB;light:RGB;edge:RGB;crack:RGB;chip:RGB;cool:RGB;roughBase:number;roughTop:number;roughCrack:number;defaults:{cells:number;jitter:number;heightLevels:number;crackWidth:number;crackDepth:number;bevel:number;distortion:number;damage:number;microDetail:number;normalStrength:number}};
const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t);};

const CFG:Record<RockKind,Cfg>={
  basalt:{shadow:[.035,.050,.078],mid:[.115,.130,.145],light:[.285,.250,.205],edge:[.620,.470,.300],crack:[.018,.027,.045],chip:[.455,.225,.125],cool:[.055,.085,.145],roughBase:.80,roughTop:.74,roughCrack:.91,defaults:{cells:7,jitter:.88,heightLevels:5,crackWidth:.095,crackDepth:.78,bevel:.145,distortion:.82,damage:.34,microDetail:.045,normalStrength:8.4}},
  granite:{shadow:[.105,.100,.135],mid:[.245,.205,.198],light:[.515,.425,.350],edge:[.790,.660,.500],crack:[.045,.045,.065],chip:[.600,.325,.255],cool:[.120,.135,.190],roughBase:.77,roughTop:.70,roughCrack:.88,defaults:{cells:7,jitter:.84,heightLevels:4,crackWidth:.082,crackDepth:.68,bevel:.165,distortion:.72,damage:.30,microDetail:.065,normalStrength:8.0}},
  dirt:{shadow:[.095,.050,.045],mid:[.245,.115,.060],light:[.500,.285,.135],edge:[.700,.470,.245],crack:[.060,.030,.030],chip:[.575,.300,.135],cool:[.125,.075,.095],roughBase:.86,roughTop:.81,roughCrack:.94,defaults:{cells:6,jitter:.90,heightLevels:4,crackWidth:.072,crackDepth:.58,bevel:.190,distortion:.88,damage:.24,microDetail:.035,normalStrength:7.2}}
};

function num(p:VfPaintedParams,key:string,fallback:number){const v=Number(p[key]);return Number.isFinite(v)?v:fallback;}
function palette(cfg:Cfg,t:number):RGB{const x=C(t);return x<.52?M(cfg.shadow,cfg.mid,S(x/.52)):M(cfg.mid,cfg.light,S((x-.52)/.48));}

function bakePaintedFacetedRock(kind:RockKind,size:number,p:VfPaintedParams={}):Material{
  const cfg=CFG[kind],d=cfg.defaults;
  const baked=bakeStylizedCellRock(size,{
    seed:Math.floor(num(p,"seed",kind==="basalt"?240914:kind==="granite"?310402:420503)),
    cells:Math.max(3,Math.floor(num(p,"cells",d.cells))),jitter:C(num(p,"jitter",d.jitter)),heightLevels:Math.max(2,Math.floor(num(p,"heightLevels",d.heightLevels))),
    crackWidth:C(num(p,"crackWidth",d.crackWidth)),crackDepth:C(num(p,"crackDepth",d.crackDepth)),bevel:C(num(p,"bevel",d.bevel)),distortion:Math.max(0,Math.min(1.5,num(p,"distortion",d.distortion))),
    damage:C(num(p,"damage",d.damage)),moss:0,topMoss:0,microDetail:C(num(p,"microDetail",d.microDetail)),normalStrength:Math.max(0,num(p,"normalStrength",d.normalStrength)),
  });
  const m=baked.material;if(!m.height)throw new Error(`${kind}: stylized cell rock returned no height`);
  const bc=makeTexture(size,size,3),rough=makeTexture(size,size,1);rough.data.set(m.roughness.data);
  const cracks=baked.masks.cracks.data,edges=baked.masks.edges.data,damaged=baked.masks.damagedEdges.data,top=baked.masks.topFaces.data,ids=baked.masks.componentId.data;
  const h=m.height.data,ao=m.ao.data;
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const i=y*size+x,j=i*3,u=(x+.5)/size,v=(y+.5)/size;
    const cr=C(Number.isFinite(cracks[i])?cracks[i]:0),ed=C(Number.isFinite(edges[i])?edges[i]:0),dm=C(Number.isFinite(damaged[i])?damaged[i]:0),tp=C(Number.isFinite(top[i])?top[i]:0),id=C(Number.isFinite(ids[i])?ids[i]:.5),hh=C(Number.isFinite(h[i])?h[i]:.5),cavity=C(1-(Number.isFinite(ao[i])?ao[i]:1));
    const idWarm=.5+.5*Math.sin((id*1.73+.17)*TAU);let value=C((hh-.22)/.62+(id-.5)*.10);let col=palette(cfg,value);
    col=M(col,idWarm>.5?cfg.light:cfg.cool,Math.abs(idWarm-.5)*.16);
    const stroke=.5+.5*Math.sin((u*1.65+v*.95+id*.72)*TAU),broken=.5+.5*Math.sin((u*4.1-v*2.6+id*1.37)*TAU+1.15),paintAmt=(stroke-.5)*.065+(broken-.5)*.025;
    if(paintAmt>0)col=M(col,cfg.edge,C(paintAmt)*tp*.38);else col=M(col,cfg.cool,C(-paintAmt)*tp*.26);
    const edgeHighlight=C((ed-cr*.76)*(0.26+.74*tp));col=M(col,cfg.edge,edgeHighlight*.62);col=M(col,cfg.chip,dm*.32);col=M(col,cfg.cool,cavity*.14*(1-cr));col=M(col,cfg.crack,cr*.84);
    if(kind==="granite"){
      const quartz=C(S((id-.38)/.42)*tp*(1-cr)),feld=C(S((.63-id)/.38)*tp*(1-cr));col=M(col,[.720,.635,.525],quartz*.14);col=M(col,[.590,.315,.285],feld*.10);
    }
    bc.data[j]=C(col[0]);bc.data[j+1]=C(col[1]);bc.data[j+2]=C(col[2]);
    let r=L(cfg.roughBase,cfg.roughTop,tp*.70);r=L(r,cfg.roughCrack,cr*.88);r=r-dm*.025+edgeHighlight*.015;if(!Number.isFinite(r))r=cfg.roughBase;rough.data[i]=Math.max(.04,Math.min(1,r));
  }
  return{baseColor:bc,metallic:m.metallic,roughness:rough,normal:m.normal,ao:m.ao,height:m.height,emission:m.emission};
}

export const bakeVfBasaltPainted=(s:number,p:VfPaintedParams={})=>bakePaintedFacetedRock("basalt",s,p);
export const bakeVfGranitePainted=(s:number,p:VfPaintedParams={})=>bakePaintedFacetedRock("granite",s,p);
export const bakeVfDirtPainted=(s:number,p:VfPaintedParams={})=>bakePaintedFacetedRock("dirt",s,p);
export const bakeVfBarkPainted=(s:number,p:VfPaintedParams={})=>bakeVfBark(s,p);
export const bakeVfSnowPainted=(s:number,p:VfPaintedParams={})=>bakeVfSnow(s,p);
export const bakeVfIcePainted=(s:number,p:VfPaintedParams={})=>bakeVfIce(s,p);
