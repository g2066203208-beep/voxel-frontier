import { C, M, S, hash, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyStoneWallParams={seed?:number;normalStrength?:number;relief?:number;stoneScale?:number;mortarDepth?:number};
type Cell={boundary:number,face:number,warm:number,cool:number,light:number};
const W=(x:number)=>x-Math.round(x);
function cell(u:number,v:number,seed:number,scale:number):Cell{
  const nx=Math.max(3,Math.round(4*scale)),ny=Math.max(3,Math.round(4*scale));
  const gx=Math.floor(u*nx),gy=Math.floor(v*ny);let best=1e9,second=1e9,bx=0,by=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=((gx+ox)%nx+nx)%nx,iy=((gy+oy)%ny+ny)%ny;
    const stagger=(iy&1)?.34:0;
    const cx=(ix+.5+stagger+(hash(seed,ix,iy,1)-.5)*.34)/nx;
    const cy=(iy+.5+(hash(seed,ix,iy,2)-.5)*.26)/ny;
    const dx=W(u-cx)*nx*.68,dy=W(v-cy)*ny*1.08;
    const shear=(hash(seed,ix,iy,3)-.5)*.28;
    const d=Math.hypot(dx+dy*shear,dy);
    if(d<best){second=best;best=d;bx=ix;by=iy;}else if(d<second)second=d;
  }
  const boundary=1-S((second-best)/.22);
  const raw=periodicField(u*.95,v*.95,seed+bx*37+by*71,2);
  const face=Math.round(raw*3)/3;
  return{boundary,face,warm:hash(seed,bx,by,4),cool:hash(seed,bx,by,5),light:hash(seed,bx,by,6)};
}

export function bakeVfPainterlyStoneWall(size:number,p:VfPainterlyStoneWallParams={}){
  const seed=Math.floor(p.seed??634021),relief=Math.max(.8,Math.min(1.8,p.relief??1.35)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??13.0)),scale=Math.max(.75,Math.min(1.35,p.stoneScale??1)),mortarDepth=Math.max(.35,Math.min(1.5,p.mortarDepth??1));
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const mortar:RGB=[.075,.078,.084],shadow:RGB=[.12,.13,.16],cool:RGB=[.28,.32,.39],mid:RGB=[.43,.42,.38],warm:RGB=[.58,.50,.38],light:RGB=[.74,.68,.56];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,q=cell(u,v,seed,scale),interior=1-q.boundary,bevel=S((interior-.04)/.52),plane=C(.5+q.face*.34),wash=periodicField(u,v,seed+840,3);
    // Fewer, broader blocks: the wall reads as large hand-sculpted masses, not a field of small bricks.
    const stoneTop=.535+q.light*.070+q.face*.040;let h=.345*mortarDepth+(stoneTop-.345*mortarDepth)*bevel;h=.5+(h-.5)*relief;h=C(h);
    let sc=M(mid,warm,C(q.warm*.58+Math.max(0,wash)*.12));sc=M(sc,cool,C(q.cool*.24+Math.max(0,-wash)*.20));sc=M(sc,light,C(plane*.20+q.light*.14));
    let col=M(mortar,sc,bevel);col=M(col,shadow,q.boundary*.18);baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.77+q.boundary*.15+Math.abs(wash)*.025);ao.data[i]=C(.96-q.boundary*.30);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
