import { C, M, S, TAU, periodicField, ridgeField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyWolfFurParams={seed?:number;normalStrength?:number;relief?:number;density?:number;guardLength?:number};

export function bakeVfPainterlyWolfFur(size:number,p:VfPainterlyWolfFurParams={}){
  const seed=Math.floor(p.seed??91007),relief=Math.max(.7,Math.min(1.8,p.relief??1.24)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??12.4)),density=C(p.density??.94),guardLength=C(p.guardLength??.90);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),underfur=makeTexture(size,size,1),guardHair=makeTexture(size,size,1),strandDirection=makeTexture(size,size,1),strandLength=makeTexture(size,size,1);
  const charcoal:RGB=[.060,.065,.075],deep:RGB=[.115,.112,.112],cool:RGB=[.225,.235,.245],mid:RGB=[.37,.35,.32],warm:RGB=[.54,.47,.38],cream:RGB=[.77,.73,.65];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3;
    // Wolves read as two layers: a dense, soft undercoat and longer coarse guard hairs.
    // Keep the macro body nearly flat; all visible volume comes from narrow directional tufts.
    const broad=periodicField(u,v,seed+17,3),underNoise=periodicField(u*4.0,v*5.0,seed+43,4),breakup=periodicField(u*6.0,v*7.0,seed+71,3);
    const flowA=ridgeField(u,v,seed+101,10.5,.33),flowB=ridgeField(u,v,seed+119,19.0,.29),flowC=ridgeField(u,v,seed+137,25.0,.36);
    const underMask=C(density*(.76+.15*underNoise+.09*broad));
    const tuftGate=S((flowA*.54+breakup*.24+.22-.28)/.66);
    const guardCore=Math.pow(C(flowB*.76+flowC*.24),7.0);
    const guard=C(density*tuftGate*guardCore*(.58+.42*C(.5+.5*breakup)));
    const fineStrand=Math.pow(C(flowC),10.0)*tuftGate;
    const rake=.5+.5*Math.sin(TAU*(u*15.0+v*4.2+periodicField(u,v,seed+179,2)*.18));
    const underRelief=underNoise*.010+(rake-.5)*.005;
    const guardRelief=guard*.032+fineStrand*.013;
    let h=.492+relief*(broad*.006+underRelief+guardRelief);h=C(h);

    const band=C(.46+.22*broad+.13*underNoise);
    let col=M(charcoal,mid,band);
    col=M(col,warm,C(.10+Math.max(0,broad)*.16));
    col=M(col,cool,C(.13+Math.max(0,-broad)*.18+Math.max(0,-underNoise)*.10));
    col=M(col,cream,C(guard*.42+fineStrand*.20));
    col=M(col,deep,C((1-tuftGate)*.13));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
    height.data[i]=h;roughness.data[i]=C(.87+underMask*.07-guard*.055);ao.data[i]=C(.97-(1-underMask)*.06-guard*.045);
    underfur.data[i]=underMask;guardHair.data[i]=guard;
    strandDirection.data[i]=C(.5+.5*Math.sin(TAU*(v*.42+periodicField(u,v,seed+223,2)*.055)));
    strandLength.data[i]=C(guardLength*(.54+.30*tuftGate+.16*guard));
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{underfur,guardHair,strandDirection,strandLength}};
}
