import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
type Ridge={cx:number;cy:number;rx:number;ry:number;tilt:number;lift:number;warm:number;cool:number};
type Scar={cx:number;cy:number;rx:number;ry:number;depth:number};
function ridges(seed:number,scale:number):Ridge[]{const out:Ridge[]=[];for(let i=0;i<42;i++)out.push({cx:hash(seed,i,1),cy:hash(seed,i,2),rx:(.024+hash(seed,i,3)*.034)*scale,ry:.060+hash(seed,i,4)*.085,tilt:(hash(seed,i,5)-.5)*.86,lift:.014+hash(seed,i,6)*.022,warm:hash(seed,i,7),cool:hash(seed,i,8)});return out;}
function scars(seed:number):Scar[]{const out:Scar[]=[];for(let i=0;i<3;i++)out.push({cx:hash(seed,700+i,1),cy:hash(seed,700+i,2),rx:.035+hash(seed,700+i,3)*.035,ry:.025+hash(seed,700+i,4)*.035,depth:.004+hash(seed,700+i,5)*.004});return out;}

export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
  const seed=Math.floor(p.seed??275903),relief=Math.max(.8,Math.min(1.8,p.relief??1.32)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??13.4)),scale=Math.max(.82,Math.min(1.2,p.ridgeScale??1)),rs=ridges(seed,scale),ss=scars(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const deep:RGB=[.085,.034,.027],cool:RGB=[.125,.082,.090],mid:RGB=[.265,.098,.043],light:RGB=[.50,.220,.082],gold:RGB=[.66,.35,.11],scarCol:RGB=[.18,.060,.036];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3,rough=periodicField(u*3.0,v*4.0,seed+180,4),micro=periodicField(u*10.0,v*13.0,seed+211,3),wash=periodicField(u,v,seed+520,3);
    let best=0,second=0,edge=0,warm=.5,cool=.5,localY=0;
    for(const q of rs){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),x=(dx+dy*q.tilt)/q.rx,y=dy/q.ry,r=Math.sqrt(x*x+y*y);if(r>1.28)continue;const outer=S((1.24-r)/.50),core=S((.70-r)/.28),facet=Math.round((.50*outer+.50*core)*5)/5,local=q.lift*(.42*outer+.58*facet);if(local>best){second=best;best=local;edge=1-core;warm=q.warm;cool=q.cool;localY=y;}else if(local>second)second=local;}
    const merge=C(second/Math.max(best,.001)),fiberA=.5+.5*Math.sin(TAU*(17*u+2*v+periodicField(u,v,seed+330,2)*.12)),fiberB=.5+.5*Math.sin(TAU*(29*u-3*v+periodicField(u,v,seed+341,2)*.09)),fibers=Math.pow(fiberA,9)*.62+Math.pow(fiberB,12)*.38;
    let scar=0;for(const q of ss){const dx=wrapDelta(u-q.cx)/q.rx,dy=wrapDelta(v-q.cy)/q.ry,r=Math.hypot(dx,dy);scar=Math.max(scar,G(r/.70)*q.depth);}
    const shallow=C(edge*.38+(1-C(best/.020))*.16),peel=Math.pow(C(.5+.5*periodicField(u*2.5,v*3.0,seed+390,3)),6)*C(best/.022);
    let h=.493+relief*(best+rough*.009+micro*.004+fibers*.005+merge*.004+peel*.004-shallow*.0025-scar);h=C(h);
    const form=C(best/.030),ridgeLight=C(form*.58+Math.max(0,rough)*.18+fibers*.20);
    let col=M(deep,mid,C(.54+form*.22));col=M(col,light,C(ridgeLight*.27+warm*.040));col=M(col,gold,C(peel*.12+fibers*.075+Math.max(0,localY)*.018));col=M(col,cool,C(Math.max(0,-rough)*.10+Math.max(0,-wash)*.075+cool*.030));col=M(col,scarCol,C(scar*10.0));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.875+shallow*.020-peel*.016+Math.abs(micro)*.020);ao.data[i]=C(.988-shallow*.040-scar*5.0-edge*.018);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
