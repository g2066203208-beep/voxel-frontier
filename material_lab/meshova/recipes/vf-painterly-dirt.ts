import { C, M, S, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";
export type VfPainterlyDirtParams = { seed?: number; normalStrength?: number; relief?: number; moisture?: number };
type Clod = { cx:number; cy:number; rx:number; ry:number; base:number; warm:number; tilt:number };
function buildClods(seed:number):Clod[]{
  const out:Clod[]=[]; const gx=5, gy=5;
  for(let y=0;y<gy;y++) for(let x=0;x<gx;x++) out.push({
    cx:(x+.5+(hash(seed,x,y,1)-.5)*.55)/gx,
    cy:(y+.5+(hash(seed,x,y,2)-.5)*.55)/gy,
    rx:(.48+hash(seed,x,y,3)*.30)/gx,
    ry:(.44+hash(seed,x,y,4)*.32)/gy,
    base:.44+hash(seed,x,y,5)*.10,
    warm:hash(seed,x,y,6), tilt:(hash(seed,x,y,7)-.5)*.05,
  });
  return out;
}
export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031), relief=Math.max(.6,Math.min(1.7,p.relief??1.22)), normalStrength=Math.max(2,Math.min(18,p.normalStrength??9.8)), moisture=C(p.moisture??.14);
  const clods=buildClods(seed); const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const dark:RGB=[.090,.038,.020], mid:RGB=[.285,.118,.050], light:RGB=[.555,.285,.125], warm:RGB=[.690,.390,.170], cool:RGB=[.135,.070,.060];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3; let best=.405,second=.395,bestEdge=0,bestWarm=.5;
    for(const q of clods){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy);if(Math.abs(dx)>q.rx*1.2||Math.abs(dy)>q.ry*1.2)continue;const lx=dx/q.rx,ly=dy/q.ry;const r=Math.sqrt(lx*lx*.82+ly*ly);if(r>1.05)continue;const edge=S((1-r)/.24);const dome=Math.max(0,1-r*r);const local=q.base+relief*(dome*.100+edge*.025+q.tilt*lx);if(local>best){second=best;best=local;bestEdge=edge;bestWarm=q.warm}else if(local>second)second=local;}
    const compressed=periodicField(u,v,seed+90,3)*.018;const erosion=Math.pow(1-Math.abs(Math.sin(Math.PI*2*(1.6*u+.55*v+periodicField(u,v,seed+101,2)*.06))),11)*.022;
    best=C(best+compressed-erosion);const overlap=C((best-second)/.075),cavity=C((1-overlap)*.55+(1-bestEdge)*.18+erosion*9);
    let col=M(dark,mid,C(.36+(best-.40)*2.3));col=M(col,light,bestEdge*.62);col=M(col,warm,bestWarm*.10*bestEdge);col=M(col,cool,cavity*.25);col=M(col,[col[0]*.62,col[1]*.58,col[2]*.55],moisture*(.35+cavity*.35));const wash=periodicField(u,v,seed+130,4);col=M(col,wash>0?warm:cool,Math.abs(wash)*.035);
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=best;roughness.data[i]=C(.86-moisture*.22+cavity*.055);ao.data[i]=C(1-cavity*.30);
  }}return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
