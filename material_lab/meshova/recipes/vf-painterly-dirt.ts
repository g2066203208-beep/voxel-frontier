import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams = { seed?: number; normalStrength?: number; relief?: number; moisture?: number };
type SoilCell={distance:number;boundary:number;id:number;heightBias:number;warm:number;cool:number};
function soilCell(u:number,v:number,seed:number):SoilCell{
  const gxCount=5,gyCount=4;const gx=Math.floor(u*gxCount),gy=Math.floor(v*gyCount);
  let best=99,second=99,bestId=0,bx=0,by=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=((gx+ox)%gxCount+gxCount)%gxCount,iy=((gy+oy)%gyCount+gyCount)%gyCount;
    const cx=(ix+.5+(hash(seed,ix,iy,1)-.5)*.58)/gxCount;
    const cy=(iy+.5+(hash(seed,ix,iy,2)-.5)*.58)/gyCount;
    const dx=wrapDelta(u-cx)*gxCount,dy=wrapDelta(v-cy)*gyCount*.88;
    const d=Math.sqrt(dx*dx+dy*dy);
    const id=iy*gxCount+ix;
    if(d<best){second=best;best=d;bestId=id;bx=ix;by=iy;}else if(d<second)second=d;
  }
  const boundary=1-S((second-best)/.15);
  return{distance:best,boundary,id:bestId,heightBias:hash(seed,bx,by,3),warm:hash(seed,bx,by,4),cool:hash(seed,bx,by,5)};
}

export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.32)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??10.4)),moisture=C(p.moisture??.14);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.035,.020,.026],deep:RGB=[.075,.038,.030],cool:RGB=[.105,.075,.075],mid:RGB=[.255,.115,.052],light:RGB=[.49,.27,.105],ochre:RGB=[.64,.39,.15];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      const cell=soilCell(u,v,seed+40);
      const broad=periodicField(u*.62,v*.54,seed+80,3);
      const directional=periodicField(u*.30+v*.06,v*.34,seed+112,2);
      const seam=Math.pow(C(cell.boundary),1.65);
      const cellPlate=(cell.heightBias-.5)*.050;
      const compressed=S((.62-cell.distance)/.28);
      const terrace=Math.round((broad*.5+directional*.35)*5)/5*.012;
      const erosionLine=Math.pow(C(.5+.5*Math.sin(TAU*(1.55*u+.33*v+periodicField(u,v,seed+210,2)*.12))),18);
      const dryCrack=erosionLine*S((broad+.22)/.55)*(1-moisture);
      const pebbleEmbed=G(wrapDelta(u-(.18+hash(seed,301)*.64))/.025)*G(wrapDelta(v-(.20+hash(seed,302)*.62))/.020);

      let h=.492+relief*(cellPlate+broad*.030+directional*.014+compressed*.012+terrace-seam*.034-dryCrack*.010-pebbleEmbed*.009);
      h=C(h);
      const cavity=C(seam*.72+dryCrack*.46+pebbleEmbed*.28+C(-broad)*.08);
      let col=M(deep,mid,C(.42+(h-.46)*2.2));
      col=M(col,light,C(.20+cell.warm*.13+Math.max(0,broad)*.16));
      col=M(col,ochre,C(Math.max(0,directional)*.10+cell.warm*.045));
      col=M(col,cool,C(cell.cool*.045+Math.max(0,-broad)*.12));
      col=M(col,ink,C(seam*.48+dryCrack*.34));
      col=M(col,[col[0]*.58,col[1]*.60,col[2]*.64],moisture*(.32+cavity*.26));

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=h;roughness.data[i]=C(.89-moisture*.22+cavity*.045+Math.abs(broad)*.018);ao.data[i]=C(1-cavity*.28);
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
