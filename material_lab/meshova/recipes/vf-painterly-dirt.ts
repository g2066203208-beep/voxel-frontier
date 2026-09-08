import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams={seed?:number;normalStrength?:number;relief?:number;moisture?:number};
type SoilPlate={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number};
function buildPlates(seed:number):SoilPlate[]{
  const out:SoilPlate[]=[];
  for(let i=0;i<6;i++)out.push({cx:hash(seed,i,11),cy:hash(seed,i,12),rx:.15+hash(seed,i,13)*.12,ry:.12+hash(seed,i,14)*.10,angle:(hash(seed,i,15)-.5)*.85,lift:.012+hash(seed,i,16)*.020,warm:hash(seed,i,17)});
  return out;
}

export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.27)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??11.0)),moisture=C(p.moisture??.14);
  const plates=buildPlates(seed),baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.034,.022,.030],deep:RGB=[.075,.039,.034],cool:RGB=[.165,.145,.195],mid:RGB=[.390,.165,.060],light:RGB=[.675,.350,.120],ochre:RGB=[.850,.535,.190],dust:RGB=[.735,.505,.255];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      const broad=periodicField(u,v,seed+80,3),secondary=periodicField(u,v,seed+112,2),brush=periodicField(u,v,seed+151,4),shoulder=periodicField(u,v,seed+174,2);
      const planeRaw=broad*.58+secondary*.30+brush*.12,planeStep=Math.round(planeRaw*4.0)/4.0;
      let plateLift=0,plateEdge=0,plateWarm=0;
      for(let k=0;k<plates.length;k++){
        const q=plates[k],dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),rx=(dx*ca+dy*sa)/q.rx,ry=(-dx*sa+dy*ca)/q.ry;
        const shape=Math.max(Math.abs(rx)*.92,Math.abs(ry)*.96,(Math.abs(rx)+Math.abs(ry))*.70);
        if(shape>1.10)continue;
        const outer=C((1.10-shape)/.28),inner=C((.72-shape)/.18),profile=.58*outer+.42*inner,local=q.lift*profile;
        if(local>plateLift){plateLift=local;plateEdge=1-inner;plateWarm=q.warm;}
      }
      const seamA=G(wrapDelta(u-(.18+.08*Math.sin(TAU*v)+hash(seed,401)*.52))/.009)*G(wrapDelta(v-(.24+hash(seed,402)*.50))/.24);
      const seamB=G(wrapDelta(v-(.62+.05*Math.sin(TAU*u)+hash(seed,403)*.12))/.010)*G(wrapDelta(u-(.66+hash(seed,404)*.12))/.22);
      const seam=Math.max(seamA,seamB)*(1-moisture*.45),press=G(wrapDelta(u-(.14+hash(seed,301)*.68))/.030)*G(wrapDelta(v-(.16+hash(seed,302)*.66))/.023);
      const crumb=Math.pow(C(.5+.5*Math.sin(TAU*(4*u+3*v)+periodicField(u,v,seed+230,2)*.50)),34)*(1-moisture)*S((Math.abs(brush)-.12)/.70);
      let h=.487+relief*(planeRaw*.030+planeStep*.026+shoulder*.010+plateLift-seam*.005-press*.005+crumb*.0022);h=C(h);
      const cavity=C(seam*.42+press*.20+crumb*.11+Math.max(0,-planeRaw)*.07);
      let col=M(deep,mid,C(.54+broad*.18+(h-.48)*1.35));
      col=M(col,light,C(.20+Math.max(0,broad)*.30+Math.max(0,brush)*.075));
      col=M(col,ochre,C(.075+Math.max(0,secondary)*.20+plateWarm*plateLift*6.2));
      col=M(col,cool,C(.070+Math.max(0,-broad)*.23+Math.max(0,-brush)*.085));
      col=M(col,dust,C(plateEdge*.060+Math.max(0,brush)*.040));
      col=M(col,ink,C(seam*.32+crumb*.11));
      col=M(col,[col[0]*.60,col[1]*.61,col[2]*.66],moisture*(.27+cavity*.22));
      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.89-moisture*.23+cavity*.030+plateEdge*.010+Math.abs(brush)*.013);ao.data[i]=C(1-cavity*.19);
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
