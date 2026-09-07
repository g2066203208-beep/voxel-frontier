import { C, M, S, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";
export type VfPainterlyDirtParams = { seed?: number; normalStrength?: number; relief?: number; moisture?: number };
type Clod = { cx:number; cy:number; rx:number; ry:number; base:number; warm:number; tiltX:number; tiltY:number };
function buildClods(seed:number):Clod[]{
  const out:Clod[]=[]; const gx=4, gy=4;
  for(let y=0;y<gy;y++) for(let x=0;x<gx;x++) out.push({
    cx:(x+.5+(hash(seed,x,y,1)-.5)*.72)/gx,
    cy:(y+.5+(hash(seed,x,y,2)-.5)*.72)/gy,
    rx:(.78+hash(seed,x,y,3)*.38)/gx,
    ry:(.70+hash(seed,x,y,4)*.34)/gy,
    base:.455+hash(seed,x,y,5)*.045,
    warm:hash(seed,x,y,6),
    tiltX:(hash(seed,x,y,7)-.5)*.020,
    tiltY:(hash(seed,x,y,8)-.5)*.018,
  });
  return out;
}
export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031), relief=Math.max(.6,Math.min(1.7,p.relief??1.16)), normalStrength=Math.max(2,Math.min(18,p.normalStrength??9.2)), moisture=C(p.moisture??.14);
  const clods=buildClods(seed); const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const dark:RGB=[.070,.026,.014], mid:RGB=[.220,.083,.034], light:RGB=[.425,.205,.082], warm:RGB=[.545,.292,.118], cool:RGB=[.105,.050,.047];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3;
    const ground=.445+periodicField(u,v,seed+81,4)*.022;
    let best=ground,second=ground-.018,bestEdge=.55,bestWarm=.5;
    for(const q of clods){
      const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy);if(Math.abs(dx)>q.rx*1.18||Math.abs(dy)>q.ry*1.18)continue;
      const lx=dx/q.rx,ly=dy/q.ry;const r=Math.sqrt(lx*lx*.88+ly*ly);if(r>1.08)continue;
      const edge=S((1-r)/.30),dome=Math.max(0,1-r*r);
      const local=q.base+relief*(dome*.052+edge*.012+q.tiltX*lx+q.tiltY*ly);
      if(local>best){second=best;best=local;bestEdge=edge;bestWarm=q.warm}else if(local>second)second=local;
    }
    const erosion=Math.pow(1-Math.abs(Math.sin(Math.PI*2*(1.25*u+.44*v+periodicField(u,v,seed+101,2)*.055))),13)*.012;
    best=C(best-erosion);
    const overlap=C((best-second)/.055),cavity=C((1-overlap)*.26+(1-bestEdge)*.12+erosion*7.0);
    const broad=periodicField(u,v,seed+125,4),dry=C(.52+broad*.58);
    let col=M(dark,mid,C(.42+(best-.43)*3.1));
    col=M(col,light,bestEdge*.48);
    col=M(col,warm,(.05+bestWarm*.07)*bestEdge*dry);
    col=M(col,cool,cavity*.20);
    col=M(col,[col[0]*.63,col[1]*.59,col[2]*.56],moisture*(.30+cavity*.30));
    col=M(col,broad>0?light:cool,Math.abs(broad)*.025);
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
    height.data[i]=best;roughness.data[i]=C(.88-moisture*.20+cavity*.035);ao.data[i]=C(1-cavity*.24);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
