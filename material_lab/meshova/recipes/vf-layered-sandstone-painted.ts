import { C,M,S,SM,hash,wrapDelta,periodicField,ridgeField,softSuperellipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfLayeredSandstoneParams={seed?:number;bands?:number;minSlabs?:number;maxSlabs?:number;crackChance?:number;chipStrength?:number;relief?:number;normalStrength?:number};
type Slab={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number;cool:number;tiltX:number;tiltY:number};
function build(seed:number){
  const out:Slab[]=[]; const hero=[[.15,.23,.22,.12],[.46,.22,.24,.13],[.77,.23,.22,.12],[.27,.48,.25,.15],[.64,.48,.28,.16],[.13,.72,.23,.13],[.43,.73,.23,.14],[.76,.72,.24,.14]];
  for(let i=0;i<hero.length;i++){const h=hero[i];out.push({cx:h[0]+(hash(seed,i,1)-.5)*.025,cy:h[1]+(hash(seed,i,2)-.5)*.025,rx:h[2]*(.92+hash(seed,i,3)*.18),ry:h[3]*(.92+hash(seed,i,4)*.18),angle:(hash(seed,i,5)-.5)*.34,lift:.085+hash(seed,i,6)*.070,warm:hash(seed,i,7),cool:hash(seed,i,8),tiltX:(hash(seed,i,9)-.5)*.050,tiltY:(hash(seed,i,10)-.5)*.036});}
  return out;
}
export function bakeVfLayeredSandstonePainted(size:number,p:VfLayeredSandstoneParams={}){
  const seed=Math.floor(p.seed??771231),relief=Math.max(.8,Math.min(1.8,p.relief??1.28)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??9.0)),slabs=build(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const deep:RGB=[.080,.044,.052],cool:RGB=[.115,.125,.180],mid:RGB=[.315,.120,.060],light:RGB=[.625,.315,.135],ochre:RGB=[.885,.555,.235],cream:RGB=[.965,.735,.365];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3,broad=periodicField(u,v,seed+700,3),strataA=ridgeField(u,v,seed+711,2.15,-.50),strataB=ridgeField(u,v,seed+719,1.05,-.48);
    let h=.430+broad*.010+(strataB-.5)*.012,bestMask=0,bestWarm=.5,bestCool=.5,plane=.5;
    for(let id=0;id<slabs.length;id++){
      const q=slabs[id],dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),x=dx*ca+dy*sa,y=-dx*sa+dy*ca;
      if(Math.abs(x)>q.rx*1.25||Math.abs(y)>q.ry*1.25)continue;
      const outer=softSuperellipse(x,y,q.rx,q.ry,3.4,.22),inner=softSuperellipse(x,y,q.rx*.78,q.ry*.76,3.8,.20),crown=softSuperellipse(x,y,q.rx*.54,q.ry*.52,4.2,.22);
      const mask=C(.46*outer+.34*inner+.20*crown);
      const local=.432+q.lift*(.46*outer+.34*inner+.20*crown)+(q.tiltX*(x/q.rx)+q.tiltY*(y/q.ry))*inner+(strataA-.5)*.014*inner;
      h=SM(h,local,.030);
      if(mask>bestMask){bestMask=mask;bestWarm=q.warm;bestCool=q.cool;plane=C(.5+q.tiltX*5-q.tiltY*4+(strataA-.5)*.30);}
    }
    h=C(.5+(h-.5)*relief);
    const ledge=S((bestMask-.28)/.58),shadow=C((1-bestMask)*.18+Math.max(0,-broad)*.08);
    let col=M(mid,light,C(.28+ledge*.38+plane*.10));col=M(col,ochre,C(bestWarm*.10+ledge*.18));col=M(col,cool,C(bestCool*.08+shadow*.22));col=M(col,cream,C(Math.pow(strataA,3.5)*ledge*.13));col=M(col,deep,C(shadow*.26));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.72+shadow*.10-ledger(ledge)*.02);ao.data[i]=C(.98-shadow*.20);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
function ledger(x:number){return x;}
