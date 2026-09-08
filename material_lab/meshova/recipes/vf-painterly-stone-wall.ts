import { C,M,S,SM,hash,wrapDelta,periodicField,softSuperellipse,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPainterlyStoneWallParams={seed?:number;normalStrength?:number;relief?:number;stoneScale?:number;mortarDepth?:number};
type Stone={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number;cool:number;light:number};
function build(seed:number,scale:number){const out:Stone[]=[];const rows=4,cols=3;for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){const id=y*cols+x,stagger=(y&1)?.16:0;out.push({cx:(x+.5)/cols+stagger,cy:(y+.5)/rows,rx:(.145+hash(seed,id,1)*.035)/scale,ry:(.090+hash(seed,id,2)*.025)/scale,angle:(hash(seed,id,3)-.5)*.22,lift:.075+hash(seed,id,4)*.035,warm:hash(seed,id,5),cool:hash(seed,id,6),light:hash(seed,id,7)});}return out;}
export function bakeVfPainterlyStoneWall(size:number,p:VfPainterlyStoneWallParams={}){
  const seed=Math.floor(p.seed??634021),relief=Math.max(.8,Math.min(1.8,p.relief??1.24)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??8.6)),scale=Math.max(.75,Math.min(1.35,p.stoneScale??1)),mortarDepth=Math.max(.35,Math.min(1.5,p.mortarDepth??1)),stones=build(seed,scale);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const mortar:RGB=[.075,.078,.084],shadow:RGB=[.12,.13,.16],cool:RGB=[.28,.32,.39],mid:RGB=[.43,.42,.38],warm:RGB=[.58,.50,.38],light:RGB=[.74,.68,.56];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,wash=periodicField(u,v,seed+840,2);let h=.405-.045*mortarDepth,best=0,bw=.5,bc=.5,bl=.5;
    for(const q of stones){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),rx=dx*ca+dy*sa,ry=-dx*sa+dy*ca,outer=softSuperellipse(rx,ry,q.rx,q.ry,4.0,.22),inner=softSuperellipse(rx,ry,q.rx*.78,q.ry*.72,4.4,.20),crown=softSuperellipse(rx,ry,q.rx*.56,q.ry*.50,4.8,.22),m=.46*outer+.34*inner+.20*crown,local=.405+q.lift*m+(q.light-.5)*.020*inner+wash*.006*outer;h=SM(h,local,.018);if(m>best){best=m;bw=q.warm;bc=q.cool;bl=q.light;}}
    const stone=S((best-.08)/.78),joint=C(1-stone);h=C(.5+(h-.5)*relief);
    let sc=M(mid,warm,C(.16+bw*.28+Math.max(0,wash)*.08));sc=M(sc,cool,C(bc*.18+Math.max(0,-wash)*.14));sc=M(sc,light,C(stone*.18+bl*.14));let col=M(mortar,sc,stone);col=M(col,shadow,joint*.20);
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.78+joint*.14+Math.abs(wash)*.018);ao.data[i]=C(.97-joint*.27);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
