import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
type Knot={cx:number;cy:number;rx:number;ry:number;twist:number};
function knots(seed:number):Knot[]{return[
  {cx:.20,cy:.34,rx:.070,ry:.058,twist:1},
  {cx:.72,cy:.69,rx:.082,ry:.066,twist:-1},
  {cx:.47,cy:.87,rx:.056,ry:.046,twist:hash(seed,900)<.5?-1:1},
];}

export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
  const seed=Math.floor(p.seed??275903),relief=Math.max(.8,Math.min(1.8,p.relief??1.32)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??13.4)),ridgeScale=Math.max(.82,Math.min(1.2,p.ridgeScale??1)),ridgeCount=Math.max(10,Math.min(15,Math.round(12.0*ridgeScale))),ks=knots(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const deep:RGB=[.070,.028,.024],cool:RGB=[.115,.075,.088],mid:RGB=[.255,.090,.040],light:RGB=[.50,.215,.078],gold:RGB=[.68,.355,.11],scar:RGB=[.57,.245,.088];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3;let knotWarp=0,knotRing=0,knotCore=0;
    for(const k of ks){const dx=wrapDelta(u-k.cx),dy=wrapDelta(v-k.cy),r=Math.sqrt((dx/k.rx)**2+(dy/k.ry)**2),mask=S((1-r)/.42),ang=Math.atan2(dy/k.ry,dx/k.rx);knotWarp+=mask*Math.sin(ang)*.014*k.twist;knotRing=Math.max(knotRing,G((r-.78)/.14)*S((1.18-r)/.22));knotCore=Math.max(knotCore,G(r/.34));}
    const warp=periodicField(u,v,seed+120,3)*.030+Math.sin(TAU*(v*.74+hash(seed,7)))*.011+Math.sin(TAU*(v*1.53+hash(seed,8)))*.005+knotWarp;
    const phase=TAU*(ridgeCount*(u+warp))+hash(seed,12)*TAU;
    const raw=.5+.5*Math.sin(phase),raw2=.5+.5*Math.sin(phase*2.07+TAU*(v*.68)+hash(seed,13)*TAU),rough=periodicField(u*3.0,v*5.0,seed+180,4),micro=periodicField(u*8.0,v*11.0,seed+211,3);
    const ridge=S((raw-.14)/.78),flat=Math.round((ridge*.72+raw2*.18+rough*.10)*5)/5;
    const shallowGroove=Math.pow(C(1-raw),7.5),cross=G(wrapDelta(v-(.18+hash(seed,31)*.64))/.014)*S((rough+.35)/.85),peel=Math.pow(C(.5+.5*periodicField(u*2.2,v*2.7,seed+330,3)),5)*S((ridge-.50)/.50);
    let h=.495+relief*((flat-.48)*.030+(rough*.013)+(micro*.006)-shallowGroove*.004-cross*.003+peel*.005+knotRing*.010-knotCore*.004);h=C(h);
    const wash=periodicField(u,v,seed+520,3),ridgeLight=C((flat-.18)/.76);
    let col=M(deep,mid,C(.44+flat*.34));col=M(col,light,C(ridgeLight*.28+Math.max(0,rough)*.09));col=M(col,gold,C(peel*.15+ridgeLight*.08));col=M(col,cool,C(Math.max(0,-rough)*.10+Math.max(0,-wash)*.07));col=M(col,scar,C(knotRing*.28+peel*.08));col=M(col,deep,C(shallowGroove*.20+cross*.10));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.87+shallowGroove*.028-peel*.020+Math.abs(micro)*.020);ao.data[i]=C(.98-shallowGroove*.07-knotCore*.045);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
