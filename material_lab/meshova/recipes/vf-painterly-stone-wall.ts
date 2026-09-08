import { C,M,S,SM,hash,wrapDelta,periodicField,softSuperellipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPainterlyStoneWallParams={seed?:number;normalStrength?:number;relief?:number;stoneScale?:number;mortarDepth?:number};
type Stone={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number;cool:number;light:number};
function build(seed:number,scale:number){const out:Stone[]=[];const rows=4,cols=3;for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){const id=y*cols+x,stagger=(y&1)?.16:0;out.push({cx:(x+.5)/cols+stagger,cy:(y+.5)/rows,rx:(.145+hash(seed,id,1)*.035)/scale,ry:(.090+hash(seed,id,2)*.025)/scale,angle:(hash(seed,id,3)-.5)*.18,lift:.045+hash(seed,id,4)*.025,warm:hash(seed,id,5),cool:hash(seed,id,6),light:hash(seed,id,7)});}return out;}
export function bakeVfPainterlyStoneWall(size:number,p:VfPainterlyStoneWallParams={}){
  const seed=Math.floor(p.seed??634021),relief=Math.max(.8,Math.min(1.8,p.relief??1.14)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??7.6)),scale=Math.max(.75,Math.min(1.35,p.stoneScale??1)),mortarDepth=Math.max(.35,Math.min(1.5,p.mortarDepth??1)),stones=build(seed,scale);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const mortar:RGB=[.155,.145,.132],shadow:RGB=[.210,.205,.200],cool:RGB=[.300,.335,.385],mid:RGB=[.430,.420,.390],warm:RGB=[.555,.490,.400],light:RGB=[.675,.635,.560];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,wash=periodicField(u,v,seed+840,2);let h=.430-.020*mortarDepth,best=0,bw=.5,bc=.5,bl=.5;
    for(const q of stones){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),rx=dx*ca+dy*sa,ry=-dx*sa+dy*ca,outer=softSuperellipse(rx,ry,q.rx,q.ry,4.1,.24),inner=softSuperellipse(rx,ry,q.rx*.80,q.ry*.74,4.5,.22),crown=softSuperellipse(rx,ry,q.rx*.58,q.ry*.52,4.8,.24),m=.48*outer+.34*inner+.18*crown,local=.430+q.lift*m+(q.light-.5)*.012*inner+wash*.004*outer;h=SM(h,local,.020);if(m>best){best=m;bw=q.warm;bc=q.cool;bl=q.light;}}
    const stone=S((best-.06)/.82),joint=C(1-stone);h=C(.5+(h-.5)*relief);
    let sc=M(mid,warm,C(.14+bw*.24+Math.max(0,wash)*.06));sc=M(sc,cool,C(bc*.16+Math.max(0,-wash)*.12));sc=M(sc,light,C(stone*.15+bl*.11));let col=M(mortar,sc,stone);col=M(col,shadow,joint*.08);
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.80+joint*.10+Math.abs(wash)*.014);ao.data[i]=C(.985-joint*.17);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
