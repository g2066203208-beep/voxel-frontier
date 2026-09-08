import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
type Ridge={cx:number;cy:number;rx:number;ry:number;tilt:number;lift:number;warm:number;cool:number};
type Knot={cx:number;cy:number;rx:number;ry:number};
function ridges(seed:number,scale:number):Ridge[]{const out:Ridge[]=[];for(let i=0;i<28;i++)out.push({cx:hash(seed,i,1),cy:hash(seed,i,2),rx:(.030+hash(seed,i,3)*.040)*scale,ry:.105+hash(seed,i,4)*.145,tilt:(hash(seed,i,5)-.5)*.22,lift:.020+hash(seed,i,6)*.027,warm:hash(seed,i,7),cool:hash(seed,i,8)});return out;}
function knots(seed:number):Knot[]{return[{cx:.20,cy:.34,rx:.070,ry:.058},{cx:.72,cy:.69,rx:.082,ry:.066},{cx:.47,cy:.87,rx:.056,ry:.046}];}

export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
  const seed=Math.floor(p.seed??275903),relief=Math.max(.8,Math.min(1.8,p.relief??1.32)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??13.4)),scale=Math.max(.82,Math.min(1.2,p.ridgeScale??1)),rs=ridges(seed,scale),ks=knots(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const deep:RGB=[.078,.030,.025],cool:RGB=[.118,.077,.088],mid:RGB=[.260,.094,.041],light:RGB=[.50,.215,.080],gold:RGB=[.67,.35,.11],scar:RGB=[.57,.25,.090];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3,rough=periodicField(u*3.0,v*5.0,seed+180,4),micro=periodicField(u*8.0,v*12.0,seed+211,3),wash=periodicField(u,v,seed+520,3);
    let ridgeLift=0,ridgeBody=0,ridgeEdge=0,ridgeWarm=.5,ridgeCool=.5,ridgeLocalY=0;
    for(const q of rs){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),x=(dx+dy*q.tilt)/q.rx,y=dy/q.ry,r=Math.sqrt(x*x+y*y);if(r>1.25)continue;const outer=S((1.20-r)/.52),core=S((.72-r)/.30),facet=Math.round((.58*outer+.42*core)*4)/4,local=q.lift*(.46*outer+.54*facet);if(local>ridgeLift){ridgeLift=local;ridgeBody=outer;ridgeEdge=1-core;ridgeWarm=q.warm;ridgeCool=q.cool;ridgeLocalY=y;}}
    let knotRing=0,knotCore=0;for(const k of ks){const dx=wrapDelta(u-k.cx),dy=wrapDelta(v-k.cy),r=Math.sqrt((dx/k.rx)**2+(dy/k.ry)**2);knotRing=Math.max(knotRing,G((r-.78)/.14)*S((1.18-r)/.22));knotCore=Math.max(knotCore,G(r/.34));}
    // Fine fibers run mostly vertical, but the main relief is local and interlocking rather than one pole-to-pole sine wave.
    const fiberPhase=TAU*(u*21.0+v*1.8+periodicField(u,v,seed+360,2)*.16),fiber=(Math.sin(fiberPhase)*.5+.5),fiberCut=Math.pow(fiber,8)*(.45+.55*ridgeBody);
    const peel=Math.pow(C(.5+.5*periodicField(u*2.2,v*2.7,seed+330,3)),5)*ridgeBody;
    const shallowValley=C((1-ridgeBody)*.55+ridgeEdge*.18);
    let h=.492+relief*(ridgeLift+rough*.010+micro*.005+fiberCut*.006+peel*.004+knotRing*.009-knotCore*.003-shallowValley*.003);h=C(h);
    const ridgeLight=C(ridgeBody*.68+Math.max(0,rough)*.18+fiberCut*.14);
    let col=M(deep,mid,C(.42+ridgeBody*.38));col=M(col,light,C(ridgeLight*.28+ridgeWarm*.055));col=M(col,gold,C(peel*.13+fiberCut*.09+Math.max(0,ridgeLocalY)*.025));col=M(col,cool,C(Math.max(0,-rough)*.10+Math.max(0,-wash)*.07+ridgeCool*.035));col=M(col,scar,C(knotRing*.28+peel*.07));col=M(col,deep,C(shallowValley*.10));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.87+shallowValley*.020-peel*.018+Math.abs(micro)*.020);ao.data[i]=C(.985-shallowValley*.045-knotCore*.040-ridgeEdge*.020);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
