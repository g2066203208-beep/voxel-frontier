import { C,M,S,SM,hash,wrapDelta,periodicField,softEllipse,softSuperellipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams={seed?:number;normalStrength?:number;relief?:number;moisture?:number};
type Clod={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number};
type Pit={cx:number;cy:number;rx:number;ry:number;depth:number};
function clods(seed:number){const out:Clod[]=[];for(let i=0;i<8;i++)out.push({cx:hash(seed,i,1),cy:hash(seed,i,2),rx:.10+hash(seed,i,3)*.10,ry:.075+hash(seed,i,4)*.09,angle:(hash(seed,i,5)-.5)*1.0,lift:.030+hash(seed,i,6)*.034,warm:hash(seed,i,7)});return out;}
function pits(seed:number){const out:Pit[]=[];for(let i=0;i<5;i++)out.push({cx:hash(seed,80+i,1),cy:hash(seed,80+i,2),rx:.055+hash(seed,80+i,3)*.045,ry:.045+hash(seed,80+i,4)*.040,depth:.010+hash(seed,80+i,5)*.010});return out;}
export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.20)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??7.4)),moisture=C(p.moisture??.14),cs=clods(seed),ps=pits(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.036,.024,.029],deep:RGB=[.080,.046,.038],cool:RGB=[.155,.145,.175],mid:RGB=[.305,.145,.070],light:RGB=[.52,.285,.125],ochre:RGB=[.69,.43,.18];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3,broad=periodicField(u,v,seed+80,3),medium=periodicField(u*1.45,v*1.45,seed+112,3);
    let h=.487+broad*.015+medium*.010,best=0,warm=.5;
    for(const q of cs){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),x=dx*ca+dy*sa,y=-dx*sa+dy*ca;const outer=softSuperellipse(x,y,q.rx,q.ry,3.0,.28),inner=softSuperellipse(x,y,q.rx*.68,q.ry*.67,3.4,.26),m=.58*outer+.42*inner;const local=.487+q.lift*m+broad*.006*outer;h=SM(h,local,.018);if(m>best){best=m;warm=q.warm;}}
    let pit=0;for(const q of ps){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),m=softEllipse(dx,dy,q.rx,q.ry,.30);pit=Math.max(pit,m*q.depth);}h-=pit;
    h=C(.5+(h-.5)*relief);const cavity=C(pit*28+(1-best)*.06),clod=S((best-.12)/.76);
    let col=M(deep,mid,C(.48+broad*.15+medium*.08));col=M(col,light,C(clod*.22+Math.max(0,broad)*.08));col=M(col,ochre,C(warm*.06+clod*.08));col=M(col,cool,C(Math.max(0,-broad)*.14+cavity*.10));col=M(col,ink,C(cavity*.14));col=M(col,[col[0]*.64,col[1]*.65,col[2]*.69],moisture*(.26+cavity*.18));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.90-moisture*.20+cavity*.035);ao.data[i]=C(.988-cavity*.18);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
