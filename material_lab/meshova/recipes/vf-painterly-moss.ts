import { C, G, M, S, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyMossParams={seed?:number;normalStrength?:number;relief?:number;density?:number;tuftHeight?:number};
type Tex=ReturnType<typeof makeTexture>;
type Tuft={cx:number,cy:number,rx:number,ry:number,lift:number,warm:number};
function buildTufts(seed:number):Tuft[]{const out:Tuft[]=[];for(let i=0;i<14;i++)out.push({cx:hash(seed,i,1),cy:hash(seed,i,2),rx:.055+hash(seed,i,3)*.070,ry:.045+hash(seed,i,4)*.060,lift:.035+hash(seed,i,5)*.045,warm:hash(seed,i,6)});return out;}
export function bakeVfPainterlyMoss(size:number,p:VfPainterlyMossParams={}){
  const seed=Math.floor(p.seed??55109),relief=Math.max(.7,Math.min(1.8,p.relief??1.30)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??11.5)),density=C(p.density??.82),tuftHeight=C(p.tuftHeight??.82),tufts=buildTufts(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),mossDensity=makeTexture(size,size,1),mossHeight=makeTexture(size,size,1),tuftVariation=makeTexture(size,size,1);
  const soil:RGB=[.095,.085,.070],deep:RGB=[.055,.115,.045],cool:RGB=[.095,.175,.090],mid:RGB=[.245,.355,.085],light:RGB=[.49,.54,.13],gold:RGB=[.66,.60,.18];
  for(let y=0;y<size;y++){const v=1-(y+.5)/size;for(let x=0;x<size;x++){
    const u=(x+.5)/size,i=y*size+x,j=i*3,broad=periodicField(u,v,seed+40,3),fine=periodicField(u*4,v*4,seed+82,3),patch=S((broad*.52+fine*.18+.34-(.28-.18*density))/.58);let tuft=0,edge=0,warmth=0;
    for(const q of tufts){const dx=wrapDelta(u-q.cx)/q.rx,dy=wrapDelta(v-q.cy)/q.ry,r=Math.hypot(dx,dy);if(r>1.25)continue;const body=S((1.18-r)/.72),crown=G(r/.46),h=q.lift*(.58*body+.42*crown);if(h>tuft){tuft=h;edge=1-body;warmth=q.warm;}}
    const micro=Math.pow(C(.5+.5*Math.sin((u*17+v*13+periodicField(u,v,seed+160,2)*.9)*Math.PI*2)),10)*patch;
    let h=.445+relief*(patch*(.030+.018*fine)+tuft*tuftHeight+micro*.008);h=C(h);const cavity=C((1-patch)*.22+edge*.12);
    let mc=M(deep,mid,C(.42+patch*.34+Math.max(0,fine)*.12));mc=M(mc,light,C(.12+micro*.26+warmth*tuft*2.2));mc=M(mc,gold,C(Math.max(0,broad)*.06+micro*.09));mc=M(mc,cool,C(Math.max(0,-fine)*.11+edge*.06));let col=M(soil,mc,C(patch*.88+tuft*5.0));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.91+patch*.045-micro*.018);ao.data[i]=C(.95-cavity*.24-tuft*.45);mossDensity.data[i]=C(patch*density);mossHeight.data[i]=C(tuftHeight*(.35+patch*.38+tuft*4.0));tuftVariation.data[i]=C(.5+.5*fine);
  }}
  return {material:finalize(size,baseColor,roughness,height,ao,normalStrength),masks:{mossDensity,mossHeight,tuftVariation}};
}
