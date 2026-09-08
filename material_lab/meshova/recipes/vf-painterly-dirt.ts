import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams={seed?:number;normalStrength?:number;relief?:number;moisture?:number};
type SoilClod={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number};
function buildClods(seed:number):SoilClod[]{const out:SoilClod[]=[];for(let i=0;i<13;i++)out.push({cx:hash(seed,i,11),cy:hash(seed,i,12),rx:.045+hash(seed,i,13)*.060,ry:.035+hash(seed,i,14)*.050,angle:(hash(seed,i,15)-.5)*1.2,lift:.014+hash(seed,i,16)*.021,warm:hash(seed,i,17)});return out;}

export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.34)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??12.6)),moisture=C(p.moisture??.14),clods=buildClods(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.036,.024,.029],deep:RGB=[.080,.046,.038],cool:RGB=[.155,.145,.175],mid:RGB=[.305,.145,.070],light:RGB=[.52,.285,.125],ochre:RGB=[.69,.43,.18],dust:RGB=[.64,.46,.27];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3;
    const broad=periodicField(u,v,seed+80,3),medium=periodicField(u*2.5,v*2.5,seed+112,3),grain=periodicField(u*6.0,v*6.0,seed+151,3),micro=periodicField(u*13.0,v*12.0,seed+181,3),brush=periodicField(u,v,seed+204,3);
    let clodLift=0,clodEdge=0,clodWarm=0;
    for(const q of clods){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),rx=(dx*ca+dy*sa)/q.rx,ry=(-dx*sa+dy*ca)/q.ry,shape=Math.max(Math.abs(rx)*.94,Math.abs(ry)*.98,(Math.abs(rx)+Math.abs(ry))*.72);if(shape>1.12)continue;const outer=C((1.12-shape)/.32),core=C((.66-shape)/.22),local=q.lift*(.62*outer+.38*core);if(local>clodLift){clodLift=local;clodEdge=1-core;clodWarm=q.warm;}}
    const crumb=Math.pow(C(.5+.5*grain),4.2)*S((micro+.35)/1.2);
    const pebble=Math.pow(C(.5+.5*micro),10)*S((grain+.20)/1.15);
    const pitA=Math.pow(C(.5-.5*periodicField(u*7.5,v*8.0,seed+260,3)),8);
    const pitB=Math.pow(C(.5-.5*periodicField(u*15,v*14,seed+267,2)),13);
    const pit=C(pitA*.72+pitB*.28);
    const hairline=Math.pow(C(.5+.5*Math.sin(TAU*(3*u+2*v)+periodicField(u,v,seed+290,2)*.50)),38)*(1-moisture)*S((grain+.05)/.92);
    // Broad form stays shallow: soil should feel broken and granular, not like orange rock slabs.
    let h=.490+relief*(broad*.014+medium*.012+grain*.010+micro*.006+clodLift+crumb*.013+pebble*.010-pit*.017-hairline*.0035);h=C(h);
    const cavity=C(pit*.55+hairline*.24+Math.max(0,-grain)*.07);
    let col=M(deep,mid,C(.50+broad*.16+medium*.08));
    col=M(col,light,C(.10+Math.max(0,grain)*.16+crumb*.12));
    col=M(col,ochre,C(.06+Math.max(0,medium)*.10+clodWarm*clodLift*4.0));
    col=M(col,cool,C(.08+Math.max(0,-broad)*.17+Math.max(0,-grain)*.12));
    col=M(col,dust,C(pebble*.17+crumb*.06+clodEdge*.035));
    col=M(col,ink,C(hairline*.20+pit*.15));
    col=M(col,[col[0]*.61,col[1]*.62,col[2]*.67],moisture*(.27+cavity*.22));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.91-moisture*.22+cavity*.038+pebble*.030+Math.abs(micro)*.020);ao.data[i]=C(.985-cavity*.24-pit*.08);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
