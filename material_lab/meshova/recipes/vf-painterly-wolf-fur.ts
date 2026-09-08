import { C, M, S, TAU, periodicField, ridgeField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyWolfFurParams={seed?:number;normalStrength?:number;relief?:number;density?:number;guardLength?:number};

export function bakeVfPainterlyWolfFur(size:number,p:VfPainterlyWolfFurParams={}){
  const seed=Math.floor(p.seed??91007),relief=Math.max(.7,Math.min(1.8,p.relief??1.24)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??12.4)),density=C(p.density??.94),guardLength=C(p.guardLength??.90);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),underfur=makeTexture(size,size,1),guardHair=makeTexture(size,size,1),strandDirection=makeTexture(size,size,1),strandLength=makeTexture(size,size,1);
  // Broad charcoal / blue-grey / muted warm planes.  The Long Dark-style read comes
  // from a handful of large value masses; individual hair colour noise is forbidden.
  const charcoal:RGB=[.040,.050,.060],deep:RGB=[.082,.092,.102],cool:RGB=[.175,.215,.255],mid:RGB=[.285,.300,.305],warm:RGB=[.395,.345,.285],cream:RGB=[.585,.575,.535];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3;
    // Painterly wolf coat grammar: a few broad overlapping coat sheets carry the form.
    // Fine individual hairs are intentionally forbidden as the primary read.
    const broad=periodicField(u,v,seed+17,3),mass=periodicField(u*1.15,v*1.10,seed+43,3),breakup=periodicField(u*1.8,v*1.6,seed+71,3);
    const sheetA=ridgeField(u,v,seed+101,2.15,.28),sheetB=ridgeField(u,v,seed+119,3.10,.22),sheetC=ridgeField(u,v,seed+137,1.45,-.20);
    const plateA=S((sheetA-.22)/.70),plateB=S((sheetB-.28)/.62),plateC=S((sheetC-.18)/.72);
    const underMask=C(density*(.74+.15*broad+.11*mass));
    const coatSheet=C(Math.max(plateA*.88,plateB*.72,plateC*.62)*(.84+.16*breakup));
    const overlap=C(Math.min(plateA,plateB)*.55+Math.min(plateA,plateC)*.35);
    const guard=C(density*(coatSheet*.82+overlap*.18));
    const shoulder=S((coatSheet-.30)/.66),edge=S((coatSheet-.08)/.30)-S((coatSheet-.72)/.22);
    let h=.490+relief*(broad*.014+mass*.010+(sheetC-.5)*.018+shoulder*.042+overlap*.018-edge*.006);h=C(h);

    const band=C(.43+.20*broad+.12*mass);
    let col=M(charcoal,mid,band);
    col=M(col,warm,C(.07+Math.max(0,broad)*.12+plateA*.065));
    col=M(col,cool,C(.14+Math.max(0,-broad)*.18+plateC*.11));
    col=M(col,cream,C(shoulder*.22+overlap*.08));
    col=M(col,deep,C((1-coatSheet)*.18+edge*.08));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
    height.data[i]=h;roughness.data[i]=C(.89+underMask*.050-shoulder*.035);ao.data[i]=C(.975-edge*.060-overlap*.030);
    underfur.data[i]=underMask;guardHair.data[i]=guard;
    strandDirection.data[i]=C(.5+.5*Math.sin(TAU*(v*.20+periodicField(u,v,seed+223,2)*.045)));
    strandLength.data[i]=C(guardLength*(.58+.28*shoulder+.14*overlap));
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{underfur,guardHair,strandDirection,strandLength}};
}
