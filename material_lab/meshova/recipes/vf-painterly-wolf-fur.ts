import { C,M,S,SM,TAU,hash,wrapDelta,periodicField,softEllipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPainterlyWolfFurParams={seed?:number;normalStrength?:number;relief?:number;density?:number;guardLength?:number};
type Sheet={cx:number;cy:number;rx:number;ry:number;lift:number;warm:number;cool:number;flow:number};
function build(seed:number){const out:Sheet[]=[];const fixed=[[.18,.22,.25,.16],[.55,.20,.27,.17],[.82,.36,.21,.17],[.32,.55,.28,.19],[.68,.57,.29,.20],[.48,.82,.25,.16]];for(let i=0;i<fixed.length;i++){const f=fixed[i];out.push({cx:f[0]+(hash(seed,i,1)-.5)*.025,cy:f[1]+(hash(seed,i,2)-.5)*.025,rx:f[2]*(.94+hash(seed,i,3)*.12),ry:f[3]*(.94+hash(seed,i,4)*.12),lift:.035+hash(seed,i,5)*.034,warm:hash(seed,i,6),cool:hash(seed,i,7),flow:(hash(seed,i,8)-.5)*.10});}return out;}
export function bakeVfPainterlyWolfFur(size:number,p:VfPainterlyWolfFurParams={}){
  const seed=Math.floor(p.seed??91007),relief=Math.max(.7,Math.min(1.8,p.relief??1.16)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??6.8)),density=C(p.density??.94),guardLength=C(p.guardLength??.90),sheets=build(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),underfur=makeTexture(size,size,1),guardHair=makeTexture(size,size,1),strandDirection=makeTexture(size,size,1),strandLength=makeTexture(size,size,1);
  const charcoal:RGB=[.040,.050,.060],deep:RGB=[.082,.092,.102],cool:RGB=[.175,.215,.255],mid:RGB=[.285,.300,.305],warm:RGB=[.395,.345,.285],cream:RGB=[.585,.575,.535];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,broad=periodicField(u,v,seed+17,3),mass=periodicField(u*1.10,v*1.05,seed+43,2);let h=.487+broad*.010+mass*.008,best=0,second=0,bw=.5,bc=.5,flow=.5;
    for(const q of sheets){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),outer=softEllipse(dx,dy,q.rx,q.ry,.34),inner=softEllipse(dx+dy*q.flow,dy,q.rx*.68,q.ry*.70,.30),m=.54*outer+.46*inner,local=.487+q.lift*(.56*outer+.44*inner)+broad*.005*outer;h=SM(h,local,.022);if(m>best){second=best;best=m;bw=q.warm;bc=q.cool;flow=C(.5+q.flow*3)}else if(m>second)second=m;}
    const coat=S((best-.06)/.80),overlap=C(second),shoulder=S((coat-.20)/.70);h=C(.5+(h-.5)*relief);const underMask=C(density*(.70+.18*broad+.12*mass)),guard=C(density*(.62*coat+.38*overlap));
    let col=M(charcoal,mid,C(.38+.28*broad+.18*coat));col=M(col,warm,C(.06+bw*.05+shoulder*.10));col=M(col,cool,C(.12+bc*.08+Math.max(0,-broad)*.14));col=M(col,cream,C(shoulder*.20+overlap*.08));col=M(col,deep,C((1-coat)*.14));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.90+underMask*.035-shoulder*.025);ao.data[i]=C(.98-(1-coat)*.035-overlap*.030);underfur.data[i]=underMask;guardHair.data[i]=guard;strandDirection.data[i]=C(.5+.5*Math.sin(TAU*(v*.16+flow*.08)));strandLength.data[i]=C(guardLength*(.58+.26*shoulder+.16*overlap));
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{underfur,guardHair,strandDirection,strandLength}};
}
