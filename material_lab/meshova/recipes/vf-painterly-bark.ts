import { C, G, M, S, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";
export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
type Plate={cx:number;cy:number;rx:number;ry:number;base:number;tiltX:number;tiltY:number;warm:number;id:number};
function buildPlates(seed:number,scale:number):Plate[]{
  const out:Plate[]=[];const gx=5,gy=6;let id=0;
  for(let y=0;y<gy;y++)for(let x=0;x<gx;x++)out.push({
    cx:(x+.5+(hash(seed,x,y,1)-.5)*.58)/gx,
    cy:(y+.5+(hash(seed,x,y,2)-.5)*.52)/gy,
    rx:((.64+hash(seed,x,y,3)*.38)/gx)*scale,
    ry:(.74+hash(seed,x,y,4)*.42)/gy,
    base:.455+hash(seed,x,y,5)*.095,
    tiltX:(hash(seed,x,y,6)-.5)*.050,
    tiltY:(hash(seed,x,y,7)-.5)*.040,
    warm:hash(seed,x,y,8),id:id++,
  });
  return out;
}
export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
 const seed=Math.floor(p.seed??275903),relief=Math.max(.7,Math.min(1.8,p.relief??1.30)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??11.0)),scale=Math.max(.82,Math.min(1.25,p.ridgeScale??1));
 const plates=buildPlates(seed,scale),baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
 const fissureCol:RGB=[.040,.012,.010],shadow:RGB=[.085,.030,.022],mid:RGB=[.255,.092,.044],light:RGB=[.525,.245,.100],ochre:RGB=[.700,.390,.160],cool:RGB=[.115,.052,.062];
 const knotCenters=[[.24,.34,.075,.065],[.72,.67,.085,.072],[.48,.86,.060,.052]];
 for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
  const u=(px+.5)/size,i=py*size+px,j=i*3;let best=.380,second=.365,bestEdge=0,bestWarm=.5,bestId=0,bestLx=0,bestLy=0;
  for(const q of plates){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy);if(Math.abs(dx)>q.rx*1.18||Math.abs(dy)>q.ry*1.18)continue;const lx=dx/q.rx,ly=dy/q.ry;const superQ=Math.pow(Math.abs(lx),3.1)+Math.pow(Math.abs(ly),2.5);if(superQ>1.10)continue;const edge=S((1-superQ)/.28),dome=Math.max(0,1-superQ);const faceNoise=periodicField(u+q.id*.013,v-q.id*.017,seed+80+q.id,3);const h=q.base+relief*(dome*.070+edge*.022+q.tiltX*lx+q.tiltY*ly+faceNoise*.010);if(h>best){second=best;best=h;bestEdge=edge;bestWarm=q.warm;bestId=q.id;bestLx=lx;bestLy=ly}else if(h>second)second=h;}
  let knot=0;for(const q of knotCenters){const dx=wrapDelta(u-q[0]),dy=wrapDelta(v-q[1]),r=Math.sqrt((dx/q[2])**2+(dy/q[3])**2);knot=Math.max(knot,G((r-.62)/.20)*(1-G(r/.28)));}
  best=C(best-knot*.020);const overlap=C((best-second)/.075),fissure=C((1-overlap)*.78+(1-bestEdge)*.28+knot*.55);const grain=periodicField(u,v,seed+130+bestId,4);
  let col=M(shadow,mid,C(.35+(best-.38)*2.7));col=M(col,light,bestEdge*.58);col=M(col,ochre,bestWarm*.10*bestEdge);col=M(col,cool,C(-grain)*.07);col=M(col,fissureCol,fissure*.67);
  const dry=Math.pow(C(.5+.5*Math.sin(Math.PI*2*(1.7*bestLy+.18*bestLx)+hash(seed,bestId,9)*Math.PI*2)),7)*bestEdge;col=M(col,[.735,.400,.168],dry*.050);
  baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=best;roughness.data[i]=C(.80+fissure*.10+knot*.04-bestEdge*.025);ao.data[i]=C(1-fissure*.36-knot*.12);
 }}return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
