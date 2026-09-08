import { C,M,S,SM,hash,wrapDelta,periodicField,softEllipse,softSuperellipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams={seed?:number;normalStrength?:number;relief?:number;moisture?:number};
type Clod={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number};
type Pit={cx:number;cy:number;rx:number;ry:number;depth:number};
function clods(seed:number){const out:Clod[]=[];for(let i=0;i<9;i++)out.push({cx:hash(seed,i,1),cy:hash(seed,i,2),rx:.115+hash(seed,i,3)*.090,ry:.050+hash(seed,i,4)*.045,angle:(hash(seed,i,5)-.5)*1.15,lift:.016+hash(seed,i,6)*.018,warm:hash(seed,i,7)});return out;}
function pits(seed:number){const out:Pit[]=[];for(let i=0;i<5;i++)out.push({cx:hash(seed,80+i,1),cy:hash(seed,80+i,2),rx:.060+hash(seed,80+i,3)*.050,ry:.040+hash(seed,80+i,4)*.035,depth:.007+hash(seed,80+i,5)*.008});return out;}
export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.12)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??6.8)),moisture=C(p.moisture??.14),cs=clods(seed),ps=pits(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.040,.027,.028],deep:RGB=[.105,.060,.042],cool:RGB=[.165,.145,.155],mid:RGB=[.335,.165,.075],light:RGB=[.540,.310,.145],ochre:RGB=[.680,.430,.200];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3,broad=periodicField(u,v,seed+80,3),medium=periodicField(u*1.35,v*1.35,seed+112,2);let h=.488+broad*.012+medium*.008,best=0,warm=.5;
    for(const q of cs){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),x=dx*ca+dy*sa,y=-dx*sa+dy*ca,outer=softSuperellipse(x,y,q.rx,q.ry,3.6,.30),inner=softSuperellipse(x,y,q.rx*.72,q.ry*.62,4.0,.28),m=.62*outer+.38*inner,local=.488+q.lift*m+broad*.004*outer;h=SM(h,local,.016);if(m>best){best=m;warm=q.warm;}}
    let pit=0;for(const q of ps){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),m=softEllipse(dx,dy,q.rx,q.ry,.34);pit=Math.max(pit,m*q.depth);}h-=pit;h=C(.5+(h-.5)*relief);const cavity=C(pit*34+(1-best)*.045),clod=S((best-.10)/.78);
    let col=M(deep,mid,C(.48+broad*.15+medium*.07));col=M(col,light,C(clod*.20+Math.max(0,broad)*.07));col=M(col,ochre,C(warm*.055+clod*.07));col=M(col,cool,C(Math.max(0,-broad)*.12+cavity*.08));col=M(col,ink,C(cavity*.12));col=M(col,[col[0]*.66,col[1]*.66,col[2]*.70],moisture*(.24+cavity*.16));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.90-moisture*.20+cavity*.030);ao.data[i]=C(.990-cavity*.15);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
