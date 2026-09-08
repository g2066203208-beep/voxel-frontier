import { C, M, S, hash, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyMossParams={seed?:number;normalStrength?:number;relief?:number;density?:number;tuftHeight?:number};
type Tex=ReturnType<typeof makeTexture>;
type Cushion={boundary:number,center:number,warm:number,light:number};
const W=(x:number)=>x-Math.round(x);
function cushion(u:number,v:number,seed:number):Cushion{
  const nx=16,ny=14,gx=Math.floor(u*nx),gy=Math.floor(v*ny);let best=1e9,second=1e9,bx=0,by=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=((gx+ox)%nx+nx)%nx,iy=((gy+oy)%ny+ny)%ny,cx=(ix+.5+(hash(seed,ix,iy,1)-.5)*.70)/nx,cy=(iy+.5+(hash(seed,ix,iy,2)-.5)*.70)/ny,dx=W(u-cx)*nx,dy=W(v-cy)*ny,d=Math.hypot(dx,dy);
    if(d<best){second=best;best=d;bx=ix;by=iy;}else if(d<second)second=d;
  }
  return{boundary:1-S((second-best)/.14),center:C((1.03-best)/.82),warm:hash(seed,bx,by,4),light:hash(seed,bx,by,5)};
}
export function bakeVfPainterlyMoss(size:number,p:VfPainterlyMossParams={}){
  const seed=Math.floor(p.seed??55109),relief=Math.max(.7,Math.min(1.8,p.relief??1.30)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??12.6)),density=C(p.density??.86),tuftHeight=C(p.tuftHeight??.90);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),mossDensity=makeTexture(size,size,1),mossHeight=makeTexture(size,size,1),tuftVariation=makeTexture(size,size,1);
  const deep:RGB=[.050,.100,.038],cool:RGB=[.070,.155,.078],mid:RGB=[.225,.370,.070],light:RGB=[.46,.56,.12],gold:RGB=[.65,.61,.17];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,q=cushion(u,v,seed),fine=periodicField(u*7,v*7,seed+83,3),micro=periodicField(u*17,v*16,seed+127,3),body=C(.48+.52*q.center),tuft=Math.pow(C(.5+.5*fine),4.2)*body,tip=Math.pow(C(.5+.5*micro),10)*body;
    // Cushions stay shallow enough to read as vegetation mats rather than green stones.
    let h=.486+relief*((q.center-.46)*.020+tuft*.012*tuftHeight+tip*.007-q.boundary*.0015+micro*.003);h=C(h);
    let col=M(deep,mid,C(.48+q.center*.30));col=M(col,light,C(q.center*.12+tuft*.22+q.light*.05));col=M(col,gold,C(tip*.15+q.warm*.035));col=M(col,cool,C(q.boundary*.055+Math.max(0,-fine)*.09));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.94+q.boundary*.015-tip*.020);ao.data[i]=C(.99-q.boundary*.055-(1-q.center)*.035);mossDensity.data[i]=C(density*(.80+.20*q.center));mossHeight.data[i]=C(tuftHeight*(.42+.30*q.center+.28*tuft));tuftVariation.data[i]=C(.5+.5*fine);
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{mossDensity,mossHeight,tuftVariation}};
}
