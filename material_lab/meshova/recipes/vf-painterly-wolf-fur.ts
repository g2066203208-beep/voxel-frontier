import { C, M, S, TAU, hash, periodicField, ridgeField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyWolfFurParams={seed?:number;normalStrength?:number;relief?:number;density?:number;guardLength?:number};
export function bakeVfPainterlyWolfFur(size:number,p:VfPainterlyWolfFurParams={}){
  const seed=Math.floor(p.seed??91007),relief=Math.max(.7,Math.min(1.8,p.relief??1.28)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??10.8)),density=C(p.density??.92),guardLength=C(p.guardLength??.86);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),underfur=makeTexture(size,size,1),guardHair=makeTexture(size,size,1),strandDirection=makeTexture(size,size,1),strandLength=makeTexture(size,size,1);
  const charcoal:RGB=[.085,.090,.100],deep:RGB=[.145,.135,.125],cool:RGB=[.24,.25,.27],mid:RGB=[.39,.37,.33],warm:RGB=[.57,.49,.38],cream:RGB=[.76,.70,.59];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,broad=periodicField(u,v,seed+14,3),under=periodicField(u*3,v*3,seed+47,4),flow=ridgeField(u,v,seed+91,7.5,.38),flow2=ridgeField(u,v,seed+103,13.0,.31),breakup=periodicField(u*5,v*5,seed+131,3);
    const tuft=S((flow*.62+flow2*.23+breakup*.15-.28)/.66),guard=Math.pow(C(flow2*.72+.28*(.5+.5*breakup)),4.0)*tuft*density,underMask=C(.68+.22*under+.10*broad);
    const rake=.5+.5*Math.sin(TAU*(u*11.0+v*3.2+periodicField(u,v,seed+177,2)*.20));
    let h=.478+relief*(broad*.018+under*.014+(tuft-.45)*.055+guard*.030+(rake-.5)*.008);h=C(h);
    const band=C(.5+.34*broad+.16*under);let col=M(charcoal,mid,band);col=M(col,warm,C(.18+Math.max(0,broad)*.20));col=M(col,cream,C(guard*.24+Math.max(0,under)*.08));col=M(col,cool,C(Math.max(0,-broad)*.22+Math.max(0,-under)*.08));col=M(col,deep,C((1-tuft)*.18));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.82+underMask*.09-guard*.04);ao.data[i]=C(.94-(1-tuft)*.12-guard*.04);underfur.data[i]=underMask;guardHair.data[i]=C(guard);strandDirection.data[i]=C(.5+.5*Math.sin(TAU*(v*.45+periodicField(u,v,seed+211,2)*.06)));strandLength.data[i]=C(guardLength*(.58+.42*tuft));
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{underfur,guardHair,strandDirection,strandLength}};
}
