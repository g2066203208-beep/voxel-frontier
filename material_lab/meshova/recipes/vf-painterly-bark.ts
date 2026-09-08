import { C,M,S,SM,hash,wrapDelta,periodicField,ridgeField,softSuperellipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
type Plate={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number;cool:number};
function build(seed:number,scale:number){const out:Plate[]=[];for(let i=0;i<14;i++)out.push({cx:hash(seed,i,1),cy:hash(seed,i,2),rx:(.055+hash(seed,i,3)*.055)*scale,ry:.14+hash(seed,i,4)*.16,angle:(hash(seed,i,5)-.5)*.34,lift:.035+hash(seed,i,6)*.035,warm:hash(seed,i,7),cool:hash(seed,i,8)});return out;}
export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
  const seed=Math.floor(p.seed??275903),relief=Math.max(.8,Math.min(1.8,p.relief??1.24)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??8.2)),scale=Math.max(.82,Math.min(1.2,p.ridgeScale??1)),plates=build(seed,scale);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const deep:RGB=[.085,.034,.027],cool:RGB=[.125,.082,.090],mid:RGB=[.265,.098,.043],light:RGB=[.50,.220,.082],gold:RGB=[.66,.35,.11];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3,broad=periodicField(u,v,seed+180,3),flow=ridgeField(u,v,seed+205,3.2,.03),wash=periodicField(u,v,seed+520,2);
    let h=.485+broad*.010+(flow-.5)*.012,best=0,warm=.5,cool=.5;
    for(const q of plates){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),x=dx*ca+dy*sa,y=-dx*sa+dy*ca;if(Math.abs(x)>q.rx*1.22||Math.abs(y)>q.ry*1.22)continue;const outer=softSuperellipse(x,y,q.rx,q.ry,3.0,.25),inner=softSuperellipse(x,y,q.rx*.58,q.ry*.88,3.3,.24),taper=C(1-Math.abs(y)/Math.max(q.ry,1e-6));const local=.485+q.lift*(.56*outer+.44*inner)*(.82+.18*taper)+(flow-.5)*.010*outer;h=SM(h,local,.020);const score=.58*outer+.42*inner;if(score>best){best=score;warm=q.warm;cool=q.cool;}}
    const seam=C(1-best),ridge=S((best-.18)/.72),highlight=C(ridge*.52+Math.max(0,broad)*.18+Math.max(0,flow-.5)*.18);
    h=C(.5+(h-.5)*relief);
    let col=M(deep,mid,C(.46+ridge*.28));col=M(col,light,C(highlight*.32+warm*.05));col=M(col,gold,C(ridge*.10+warm*.04));col=M(col,cool,C(seam*.16+Math.max(0,-wash)*.10+cool*.035));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.87+seam*.025-ridge*.018);ao.data[i]=C(.985-seam*.085);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
