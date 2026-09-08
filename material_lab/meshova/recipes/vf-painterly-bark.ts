import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
type Knot={cx:number;cy:number;rx:number;ry:number;twist:number};
function knots(seed:number):Knot[]{return[
  {cx:.20,cy:.34,rx:.078,ry:.064,twist:1},
  {cx:.72,cy:.69,rx:.090,ry:.072,twist:-1},
  {cx:.47,cy:.87,rx:.060,ry:.050,twist:hash(seed,900)<.5?-1:1},
];}

export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
  const seed=Math.floor(p.seed??275903),relief=Math.max(.8,Math.min(1.8,p.relief??1.34)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??13.0)),ridgeScale=Math.max(.82,Math.min(1.2,p.ridgeScale??1)),ridgeCount=Math.max(7,Math.min(11,Math.round(8.4*ridgeScale))),ks=knots(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const deep:RGB=[.075,.028,.024],cool:RGB=[.105,.072,.085],mid:RGB=[.235,.083,.038],light:RGB=[.47,.205,.078],gold:RGB=[.66,.345,.105],scar:RGB=[.55,.245,.090];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3;let knotWarp=0,knotRing=0,knotCore=0;
    for(const k of ks){const dx=wrapDelta(u-k.cx),dy=wrapDelta(v-k.cy),r=Math.sqrt((dx/k.rx)**2+(dy/k.ry)**2),mask=S((1-r)/.42),ang=Math.atan2(dy/k.ry,dx/k.rx);knotWarp+=mask*Math.sin(ang)*.022*k.twist;knotRing=Math.max(knotRing,G((r-.76)/.13)*S((1.18-r)/.22));knotCore=Math.max(knotCore,G(r/.34));}
    const warp=periodicField(u,v,seed+120,3)*.040+Math.sin(TAU*(v*.76+hash(seed,7)))*.016+Math.sin(TAU*(v*1.61+hash(seed,8)))*.006+knotWarp;
    const a=.5+.5*Math.sin(TAU*(ridgeCount*(u+warp))+hash(seed,12)*TAU),b=.5+.5*Math.sin(TAU*((ridgeCount*1.93)*(u+warp*.72)+v*.84)+hash(seed,13)*TAU),c=.5+.5*Math.sin(TAU*((ridgeCount*3.75)*u+v*1.45)+periodicField(u,v,seed+211,2)*.55);
    const ridge=Math.pow(a,1.55),secondary=(Math.pow(b,2.0)-.35)*.42,fiber=(c-.5)*.16;
    const branch=G(wrapDelta(v-hash(seed,31))/.11)*(.5+.5*Math.sin(TAU*(u*ridgeCount*.5+hash(seed,32))));
    const shallowGroove=Math.pow(C(1-a),4.5)*(.55+.45*S((b-.20)/.65));
    const peel=Math.pow(C(.5+.5*periodicField(u*2.0,v*2.0,seed+330,3)),4)*S((a-.42)/.58);
    let h=.492+relief*((ridge-.52)*.050+secondary*.020+fiber*.008+branch*.010+knotRing*.012-knotCore*.006-shallowGroove*.008+peel*.006);h=C(h);
    const wash=periodicField(u,v,seed+520,3),shade=C(shallowGroove*.34+knotCore*.08),ridgeLight=C((ridge-.38)/.62);
    let col=M(deep,mid,C(.38+ridge*.46));col=M(col,light,C(ridgeLight*.30+Math.max(0,wash)*.07));col=M(col,gold,C(peel*.16+ridgeLight*.10));col=M(col,cool,C(Math.max(0,-wash)*.10+shallowGroove*.08));col=M(col,scar,C(knotRing*.30+peel*.08));col=M(col,deep,shade*.34);
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.86+shallowGroove*.035-peel*.022+Math.abs(wash)*.018);ao.data[i]=C(.97-shallowGroove*.10-knotCore*.06);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
