import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams={seed?:number;normalStrength?:number;relief?:number;moisture?:number};

type Furrow={phase:number;lean:number;width:number;depth:number;warm:number};
function buildFurrows(seed:number):Furrow[]{
  const out:Furrow[]=[];
  for(let i=0;i<3;i++)out.push({
    phase:hash(seed,i,1),lean:(hash(seed,i,2)-.5)*.16,width:.018+hash(seed,i,3)*.016,depth:.007+hash(seed,i,4)*.006,warm:hash(seed,i,5),
  });
  return out;
}

export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.24)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??10.4)),moisture=C(p.moisture??.14);
  const furrows=buildFurrows(seed),baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.040,.025,.030],deep:RGB=[.105,.060,.043],cool:RGB=[.145,.125,.140],mid:RGB=[.34,.165,.075],light:RGB=[.58,.34,.145],ochre:RGB=[.72,.48,.205];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      const broad=periodicField(u,v,seed+80,3);
      const secondary=periodicField(u,v,seed+112,2);
      const brush=periodicField(u,v,seed+151,4);
      const broadPlane=Math.round((broad*.58+secondary*.30)*6)/6;
      const lowMound=Math.max(0,broad*.62+secondary*.30);

      let furrow=0,furrowWarm=0;
      for(let k=0;k<furrows.length;k++){
        const f=furrows[k];
        const center=(f.phase+f.lean*Math.sin(TAU*v)+Math.sin(TAU*(v*(k+1))+hash(seed,k,9)*TAU)*.020)%1;
        const d=Math.abs(wrapDelta(u-center));
        const gate=.42+.58*S((Math.sin(TAU*(v*(k+1)+hash(seed,k,10)))+.2)/1.2);
        const q=G(d/f.width)*gate;
        if(q>furrow){furrow=q;furrowWarm=f.warm;}
      }
      const hairline=Math.pow(C(.5+.5*Math.sin(TAU*(3*u+2*v)+periodicField(u,v,seed+230,2)*.42)),28)*(1-moisture);
      const pebblePress=G(wrapDelta(u-(.17+hash(seed,301)*.66))/.026)*G(wrapDelta(v-(.19+hash(seed,302)*.62))/.021);

      let h=.492+relief*(broad*.045+secondary*.018+broadPlane*.025+lowMound*.016-furrow*.008-hairline*.004-pebblePress*.006);
      h=C(h);
      const cavity=C(furrow*.42+hairline*.25+pebblePress*.20+Math.max(0,-broad)*.09);
      let col=M(deep,mid,C(.42+(h-.46)*1.95));
      col=M(col,light,C(.15+Math.max(0,broad)*.24+Math.max(0,brush)*.060));
      col=M(col,ochre,C(Math.max(0,secondary)*.13+furrowWarm*furrow*.030));
      col=M(col,cool,C(Math.max(0,-broad)*.16+Math.max(0,-brush)*.060));
      col=M(col,ink,C(furrow*.28+hairline*.22));
      col=M(col,[col[0]*.62,col[1]*.64,col[2]*.68],moisture*(.27+cavity*.24));

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=h;roughness.data[i]=C(.89-moisture*.22+cavity*.035+Math.abs(brush)*.016);ao.data[i]=C(1-cavity*.22);
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
