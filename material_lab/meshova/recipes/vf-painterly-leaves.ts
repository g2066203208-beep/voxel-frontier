import { C,G,M,S,hash,wrapDelta,periodicField,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

type Tex = ReturnType<typeof makeTexture>;
export type VfPainterlyLeavesParams={seed?:number;normalStrength?:number;relief?:number;density?:number};
type Leaf={cx:number;cy:number;rx:number;ry:number;angle:number;base:number;hue:number;id:number};

function build(seed:number,density:number){
  const out:Leaf[]=[];const gx=Math.max(4,Math.round(5*density)),gy=Math.max(4,Math.round(5*density));let id=0;
  for(let y=0;y<gy;y++)for(let x=0;x<gx;x++)out.push({
    cx:(x+.5+(hash(seed,x,y,1)-.5)*.62)/gx,
    cy:(y+.5+(hash(seed,x,y,2)-.5)*.62)/gy,
    rx:(.56+hash(seed,x,y,3)*.38)/gx,
    ry:(.78+hash(seed,x,y,4)*.46)/gy,
    angle:(hash(seed,x,y,5)-.5)*2.45,
    base:.45+hash(seed,x,y,6)*.18,
    hue:hash(seed,x,y,7),id:id++});
  return out;
}

export function bakeVfPainterlyLeavesBundle(size:number,p:VfPainterlyLeavesParams={}){
  const seed=Math.floor(p.seed??391477),relief=Math.max(.5,Math.min(1.6,p.relief??1.06)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??7.2)),density=Math.max(.72,Math.min(1.35,p.density??1)),leaves=build(seed,density);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),opacity=makeTexture(size,size,1);
  const deep:RGB=[.020,.070,.035],dark:RGB=[.040,.145,.060],mid:RGB=[.095,.285,.095],light:RGB=[.280,.455,.145],warm:RGB=[.430,.485,.165],cool:RGB=[.045,.145,.115];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      let bestH=.332,second=.326,best:Leaf|null=null,bestInside=0,bestVein=0;
      for(const leaf of leaves){
        const dx=wrapDelta(u-leaf.cx),dy=wrapDelta(v-leaf.cy);
        if(Math.abs(dx)>leaf.rx*1.18||Math.abs(dy)>leaf.ry*1.18)continue;
        const ca=Math.cos(leaf.angle),sa=Math.sin(leaf.angle),x=(dx*ca+dy*sa)/leaf.rx,y=(-dx*sa+dy*ca)/leaf.ry;
        const ay=Math.abs(y),taper=Math.max(.16,1-ay*.72);
        // Smooth superellipse/lens contour: no serration, no pixel-scale teeth.
        const q=Math.pow(Math.pow(Math.abs(x)/taper,2.35)+Math.pow(ay,2.15),1/2.15);
        if(q>1.08)continue;
        const inside=S((1.08-q)/.26),dome=Math.max(0,1-Math.min(1,q*q));
        const vein=G(x/.085)*S((1-ay)/.24);
        const shoulder=S((inside-.18)/.68);
        const h=leaf.base+relief*(dome*.082+shoulder*.024+vein*.008);
        if(h>bestH){second=bestH;bestH=h;best=leaf;bestInside=inside;bestVein=vein}
        else if(h>second)second=h;
      }

      const overlap=C((bestH-second)/.11),cavity=C(1-overlap);
      let col:RGB;
      if(best){
        const variation=best.hue;
        col=M(dark,mid,.38+variation*.38);
        col=M(col,light,bestInside*(.28+variation*.18));
        col=M(col,warm,C(variation-.64)*.13);
        col=M(col,cool,C(.36-variation)*.13);
        col=M(col,[.520,.570,.235],bestVein*.07);
        col=M(col,deep,cavity*.30);
      }else col=deep;
      const wash=periodicField(u,v,seed+701,3);
      col=M(col,wash>0?light:cool,Math.abs(wash)*.022);

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=C(bestH);
      roughness.data[i]=C(best?.74+cavity*.07:.92);
      ao.data[i]=best?C(1-cavity*.32):1;
      opacity.data[i]=best?C(S((bestInside-.05)/.70)):0;
    }
  }
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{opacity}};
}

export function bakeVfPainterlyLeaves(size:number,p:VfPainterlyLeavesParams={}){
  return bakeVfPainterlyLeavesBundle(size,p).material;
}
