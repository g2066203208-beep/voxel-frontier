import { C, M, S, hash, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyMossParams={seed?:number;normalStrength?:number;relief?:number;density?:number;tuftHeight?:number};
type Tex=ReturnType<typeof makeTexture>;
type Cushion={boundary:number,center:number,warm:number,light:number};
const W=(x:number)=>x-Math.round(x);
function cushion(u:number,v:number,seed:number):Cushion{
  const nx=9,ny=8,gx=Math.floor(u*nx),gy=Math.floor(v*ny);let best=1e9,second=1e9,bx=0,by=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=((gx+ox)%nx+nx)%nx,iy=((gy+oy)%ny+ny)%ny,cx=(ix+.5+(hash(seed,ix,iy,1)-.5)*.62)/nx,cy=(iy+.5+(hash(seed,ix,iy,2)-.5)*.62)/ny,dx=W(u-cx)*nx,dy=W(v-cy)*ny,d=Math.hypot(dx,dy);
    if(d<best){second=best;best=d;bx=ix;by=iy;}else if(d<second)second=d;
  }
  return{boundary:1-S((second-best)/.17),center:C((1.05-best)/.78),warm:hash(seed,bx,by,4),light:hash(seed,bx,by,5)};
}
export function bakeVfPainterlyMoss(size:number,p:VfPainterlyMossParams={}){
  const seed=Math.floor(p.seed??55109),relief=Math.max(.7,Math.min(1.8,p.relief??1.30)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??12.4)),density=C(p.density??.86),tuftHeight=C(p.tuftHeight??.90);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),mossDensity=makeTexture(size,size,1),mossHeight=makeTexture(size,size,1),tuftVariation=makeTexture(size,size,1);
  const deep:RGB=[.055,.105,.040],cool:RGB=[.075,.155,.080],mid:RGB=[.245,.385,.075],light:RGB=[.49,.57,.12],gold:RGB=[.69,.64,.17];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,q=cushion(u,v,seed),fine=periodicField(u*5,v*5,seed+83,3),micro=periodicField(u*11,v*11,seed+127,2),body=C(.34+.66*q.center),tuft=Math.pow(C(.5+.5*fine),3.2)*body,tip=Math.pow(C(.5+.5*micro),7)*body;
    let h=.475+relief*((q.center-.42)*.046+tuft*.018*tuftHeight+tip*.008-q.boundary*.004);h=C(h);
    let col=M(deep,mid,C(.46+q.center*.38));col=M(col,light,C(q.center*.18+tuft*.18+q.light*.07));col=M(col,gold,C(tip*.12+q.warm*.05));col=M(col,cool,C(q.boundary*.10+Math.max(0,-fine)*.08));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.93+q.boundary*.025-tip*.018);ao.data[i]=C(.98-q.boundary*.12-(1-q.center)*.06);mossDensity.data[i]=C(density*(.72+.28*q.center));mossHeight.data[i]=C(tuftHeight*(.46+.36*q.center+.18*tuft));tuftVariation.data[i]=C(.5+.5*fine);
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{mossDensity,mossHeight,tuftVariation}};
}
