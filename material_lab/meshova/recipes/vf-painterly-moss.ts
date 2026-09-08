import { C,M,S,SM,hash,wrapDelta,periodicField,softEllipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPainterlyMossParams={seed?:number;normalStrength?:number;relief?:number;density?:number;tuftHeight?:number};
type Tex=ReturnType<typeof makeTexture>;type Patch={cx:number;cy:number;rx:number;ry:number;lift:number;warm:number;light:number};
function build(seed:number){const out:Patch[]=[];const fixed=[[.18,.24,.21,.17],[.53,.22,.24,.18],[.82,.31,.19,.17],[.29,.57,.25,.20],[.67,.58,.27,.21],[.48,.82,.24,.16]];for(let i=0;i<fixed.length;i++){const f=fixed[i];out.push({cx:f[0]+(hash(seed,i,1)-.5)*.025,cy:f[1]+(hash(seed,i,2)-.5)*.025,rx:f[2]*(.94+hash(seed,i,3)*.12),ry:f[3]*(.94+hash(seed,i,4)*.12),lift:.038+hash(seed,i,5)*.032,warm:hash(seed,i,6),light:hash(seed,i,7)});}return out;}
export function bakeVfPainterlyMoss(size:number,p:VfPainterlyMossParams={}){
  const seed=Math.floor(p.seed??55109),relief=Math.max(.7,Math.min(1.8,p.relief??1.18)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??7.0)),density=C(p.density??.86),tuftHeight=C(p.tuftHeight??.90),ps=build(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),mossDensity=makeTexture(size,size,1),mossHeight=makeTexture(size,size,1),tuftVariation=makeTexture(size,size,1);
  const deep:RGB=[.050,.100,.038],cool:RGB=[.070,.155,.078],mid:RGB=[.225,.370,.070],light:RGB=[.46,.56,.12],gold:RGB=[.65,.61,.17];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,broad=periodicField(u,v,seed+83,3);let h=.486+broad*.010,best=0,second=0,warm=.5,lit=.5;
    for(const q of ps){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),outer=softEllipse(dx,dy,q.rx,q.ry,.34),inner=softEllipse(dx,dy,q.rx*.68,q.ry*.68,.32),m=.58*outer+.42*inner,local=.486+q.lift*(.60*outer+.40*inner)+broad*.006*outer;h=SM(h,local,.022);if(m>best){second=best;best=m;warm=q.warm;lit=q.light}else if(m>second)second=m;}
    const blanket=S((best-.06)/.80),merge=C(second),crown=S((blanket-.22)/.68);h=C(.5+(h-.5)*relief);
    let col=M(deep,mid,C(.42+blanket*.34));col=M(col,light,C(crown*.30+lit*.055));col=M(col,gold,C(merge*.09+warm*.045));col=M(col,cool,C((1-blanket)*.10+Math.max(0,-broad)*.08));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.94-crown*.022);ao.data[i]=C(.99-(1-blanket)*.035-merge*.035);mossDensity.data[i]=C(density*(.48+.52*blanket));mossHeight.data[i]=C(tuftHeight*(.48+.36*crown+.16*merge));tuftVariation.data[i]=C(.5+.5*broad);
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{mossDensity,mossHeight,tuftVariation}};
}
