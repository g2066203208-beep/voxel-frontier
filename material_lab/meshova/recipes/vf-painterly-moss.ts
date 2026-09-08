import { C, M, S, hash, periodicField, ridgeField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyMossParams={seed?:number;normalStrength?:number;relief?:number;density?:number;tuftHeight?:number};
type Tex=ReturnType<typeof makeTexture>;
type Patch={cx:number;cy:number;rx:number;ry:number;lift:number;warm:number;light:number};
const W=(x:number)=>x-Math.round(x);
function patches(seed:number):Patch[]{const out:Patch[]=[];for(let i=0;i<9;i++)out.push({cx:hash(seed,i,1),cy:hash(seed,i,2),rx:.16+hash(seed,i,3)*.15,ry:.14+hash(seed,i,4)*.14,lift:.020+hash(seed,i,5)*.018,warm:hash(seed,i,6),light:hash(seed,i,7)});return out;}
export function bakeVfPainterlyMoss(size:number,p:VfPainterlyMossParams={}){
  const seed=Math.floor(p.seed??55109),relief=Math.max(.7,Math.min(1.8,p.relief??1.30)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??12.6)),density=C(p.density??.86),tuftHeight=C(p.tuftHeight??.90),ps=patches(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),mossDensity=makeTexture(size,size,1),mossHeight=makeTexture(size,size,1),tuftVariation=makeTexture(size,size,1);
  const deep:RGB=[.050,.100,.038],cool:RGB=[.070,.155,.078],mid:RGB=[.225,.370,.070],light:RGB=[.46,.56,.12],gold:RGB=[.65,.61,.17];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,broad=periodicField(u,v,seed+83,3),softFold=ridgeField(u,v,seed+127,2.05,.18);
    let best=0,second=0,warm=.5,lit=.5;
    for(const q of ps){const dx=W(u-q.cx)/q.rx,dy=W(v-q.cy)/q.ry,r=Math.hypot(dx,dy);if(r>1.35)continue;const outer=S((1.28-r)/.58),core=S((.70-r)/.34),local=q.lift*(.42*outer+.58*core);if(local>best){second=best;best=local;warm=q.warm;lit=q.light;}else if(local>second)second=local;}
    const blanket=C(best/.028),merge=C(second/Math.max(best,.001)),crown=S((blanket-.28)/.62),edge=S((blanket-.05)/.24)-S((blanket-.76)/.20);
    // Nine broad moss mats overlap into one painterly carpet. No grass-like micro strands.
    let h=.487+relief*(best+second*.28+(softFold-.5)*.018+broad*.012+crown*.014*tuftHeight-edge*.003);h=C(h);
    let col=M(deep,mid,C(.48+blanket*.28));col=M(col,light,C(crown*.28+lit*.06));col=M(col,gold,C(merge*.12+warm*.05));col=M(col,cool,C(edge*.10+Math.max(0,-broad)*.10));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.945-edge*.018-crown*.012);ao.data[i]=C(.99-edge*.065-merge*.030);mossDensity.data[i]=C(density*(.56+.44*blanket));mossHeight.data[i]=C(tuftHeight*(.50+.34*crown+.16*merge));tuftVariation.data[i]=C(.5+.5*broad);
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{mossDensity,mossHeight,tuftVariation}};
}
