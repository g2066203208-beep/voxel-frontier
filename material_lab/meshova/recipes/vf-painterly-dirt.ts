import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams={seed?:number;normalStrength?:number;relief?:number;moisture?:number};

type Furrow={phase:number;lean:number;width:number;depth:number;warm:number};
function buildFurrows(seed:number):Furrow[]{
  const out:Furrow[]=[];
  for(let i=0;i<5;i++)out.push({
    phase:hash(seed,i,1),lean:(hash(seed,i,2)-.5)*.18,width:.022+hash(seed,i,3)*.020,depth:.012+hash(seed,i,4)*.014,warm:hash(seed,i,5),
  });
  return out;
}

export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.34)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??10.4)),moisture=C(p.moisture??.14);
  const furrows=buildFurrows(seed),baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.036,.020,.024],deep:RGB=[.080,.040,.030],cool:RGB=[.115,.080,.078],mid:RGB=[.255,.112,.050],light:RGB=[.48,.255,.102],ochre:RGB=[.64,.39,.155];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      const broad=periodicField(u,v,seed+80,3);
      const secondary=periodicField(u,v,seed+112,2);
      const brush=periodicField(u,v,seed+151,4);
      const broadPlane=Math.round((broad*.55+secondary*.28)*5)/5;
      const lowMound=Math.max(0,broad*.65+secondary*.25);

      let furrow=0,furrowWarm=0;
      for(let k=0;k<furrows.length;k++){
        const f=furrows[k];
        const center=(f.phase+f.lean*Math.sin(TAU*v)+Math.sin(TAU*(v*(k%2+1))+hash(seed,k,9)*TAU)*.025)%1;
        const d=Math.abs(wrapDelta(u-center));
        const gate=.56+.44*S((Math.sin(TAU*(v*(k+1)+hash(seed,k,10)))+.2)/1.2);
        const q=G(d/f.width)*gate;
        if(q>furrow){furrow=q;furrowWarm=f.warm;}
      }
      const hairline=Math.pow(C(.5+.5*Math.sin(TAU*(3*u+2*v)+periodicField(u,v,seed+230,2)*.42)),25)*(1-moisture);
      const pebblePress=G(wrapDelta(u-(.17+hash(seed,301)*.66))/.030)*G(wrapDelta(v-(.19+hash(seed,302)*.62))/.024);

      let h=.492+relief*(broad*.033+secondary*.014+broadPlane*.014+lowMound*.010-furrow*.018-hairline*.006-pebblePress*.008);
      h=C(h);
      const cavity=C(furrow*.66+hairline*.34+pebblePress*.24+Math.max(0,-broad)*.10);
      let col=M(deep,mid,C(.42+(h-.46)*2.15));
      col=M(col,light,C(.12+Math.max(0,broad)*.21+Math.max(0,brush)*.055));
      col=M(col,ochre,C(Math.max(0,secondary)*.10+furrowWarm*furrow*.035));
      col=M(col,cool,C(Math.max(0,-broad)*.14+Math.max(0,-brush)*.055));
      col=M(col,ink,C(furrow*.42+hairline*.30));
      col=M(col,[col[0]*.58,col[1]*.60,col[2]*.64],moisture*(.30+cavity*.28));

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=h;roughness.data[i]=C(.90-moisture*.23+cavity*.040+Math.abs(brush)*.016);ao.data[i]=C(1-cavity*.27);
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
