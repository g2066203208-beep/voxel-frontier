import { C,G,M,S,hash,wrapDelta,periodicField,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

type Tex=ReturnType<typeof makeTexture>;
export type VfPainterlyLeavesParams={seed?:number;normalStrength?:number;relief?:number;density?:number};
type Leaf={cx:number;cy:number;rx:number;ry:number;angle:number;base:number;hue:number};
function build(seed:number,density:number){const out:Leaf[]=[];const gx=Math.max(3,Math.round(4*density)),gy=Math.max(3,Math.round(4*density));for(let y=0;y<gy;y++)for(let x=0;x<gx;x++)out.push({cx:(x+.5+(hash(seed,x,y,1)-.5)*.50)/gx,cy:(y+.5+(hash(seed,x,y,2)-.5)*.50)/gy,rx:(.68+hash(seed,x,y,3)*.32)/gx,ry:(.86+hash(seed,x,y,4)*.36)/gy,angle:(hash(seed,x,y,5)-.5)*2.2,base:.44+hash(seed,x,y,6)*.14,hue:hash(seed,x,y,7)});return out;}
export function bakeVfPainterlyLeavesBundle(size:number,p:VfPainterlyLeavesParams={}){
  const seed=Math.floor(p.seed??391477),relief=Math.max(.5,Math.min(1.6,p.relief??1.02)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??6.0)),density=Math.max(.72,Math.min(1.35,p.density??1)),leaves=build(seed,density);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),opacity=makeTexture(size,size,1);
  const deep:RGB=[.020,.070,.035],dark:RGB=[.040,.145,.060],mid:RGB=[.095,.285,.095],light:RGB=[.280,.455,.145],warm:RGB=[.430,.485,.165],cool:RGB=[.045,.145,.115];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3;let bestH=.332,second=.326,best:Leaf|null=null,bestInside=0,bestVein=0;
    for(const leaf of leaves){const dx=wrapDelta(u-leaf.cx),dy=wrapDelta(v-leaf.cy);if(Math.abs(dx)>leaf.rx*1.18||Math.abs(dy)>leaf.ry*1.18)continue;const ca=Math.cos(leaf.angle),sa=Math.sin(leaf.angle),x=(dx*ca+dy*sa)/leaf.rx,y=(-dx*sa+dy*ca)/leaf.ry,ay=Math.abs(y),taper=Math.max(.18,1-ay*.66),q=Math.pow(Math.pow(Math.abs(x)/taper,2.6)+Math.pow(ay,2.35),1/2.35);if(q>1.08)continue;const inside=S((1.08-q)/.30),dome=Math.max(0,1-Math.min(1,q*q)),vein=G(x/.11)*S((1-ay)/.30),shoulder=S((inside-.10)/.78),h=leaf.base+relief*(dome*.075+shoulder*.035+vein*.006);if(h>bestH){second=bestH;bestH=h;best=leaf;bestInside=inside;bestVein=vein}else if(h>second)second=h;}
    const overlap=C((bestH-second)/.12),cavity=C(1-overlap);let col:RGB;if(best){const variation=best.hue;col=M(dark,mid,.38+variation*.36);col=M(col,light,bestInside*(.30+variation*.16));col=M(col,warm,C(variation-.64)*.11);col=M(col,cool,C(.36-variation)*.11);col=M(col,[.52,.57,.235],bestVein*.05);col=M(col,deep,cavity*.27);}else col=deep;const wash=periodicField(u,v,seed+701,2);col=M(col,wash>0?light:cool,Math.abs(wash)*.018);
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=C(bestH);roughness.data[i]=C(best?.75+cavity*.06:.92);ao.data[i]=best?C(1-cavity*.28):1;opacity.data[i]=best?C(S((bestInside-.02)/.76)):0;
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{opacity}};
}
export function bakeVfPainterlyLeaves(size:number,p:VfPainterlyLeavesParams={}){return bakeVfPainterlyLeavesBundle(size,p).material;}
