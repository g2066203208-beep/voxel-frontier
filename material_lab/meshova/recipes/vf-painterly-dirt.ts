import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyDirtParams={seed?:number;normalStrength?:number;relief?:number;moisture?:number};
type SoilPlate={cx:number;cy:number;rx:number;ry:number;angle:number;lift:number;warm:number};
function buildPlates(seed:number):SoilPlate[]{const out:SoilPlate[]=[];for(let i=0;i<7;i++)out.push({cx:hash(seed,i,11),cy:hash(seed,i,12),rx:.12+hash(seed,i,13)*.12,ry:.10+hash(seed,i,14)*.10,angle:(hash(seed,i,15)-.5)*.90,lift:.014+hash(seed,i,16)*.023,warm:hash(seed,i,17)});return out;}

export function bakeVfPainterlyDirt(size:number,p:VfPainterlyDirtParams={}){
  const seed=Math.floor(p.seed??182031),relief=Math.max(.7,Math.min(1.7,p.relief??1.34)),normalStrength=Math.max(2,Math.min(18,p.normalStrength??12.2)),moisture=C(p.moisture??.14),plates=buildPlates(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.042,.026,.030],deep:RGB=[.090,.046,.034],cool:RGB=[.18,.15,.19],mid:RGB=[.39,.17,.065],light:RGB=[.68,.36,.13],ochre:RGB=[.86,.55,.20],dust:RGB=[.75,.51,.25];
  for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
    const u=(px+.5)/size,i=py*size+px,j=i*3,broad=periodicField(u,v,seed+80,3),secondary=periodicField(u*2,v*2,seed+112,3),grain=periodicField(u*5,v*5,seed+151,3),grain2=periodicField(u*9,v*9,seed+181,2),brush=periodicField(u,v,seed+204,3);
    const planeRaw=broad*.52+secondary*.29+brush*.11,planeStep=Math.round(planeRaw*5)/5;let plateLift=0,plateEdge=0,plateWarm=0;
    for(const q of plates){const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy),ca=Math.cos(q.angle),sa=Math.sin(q.angle),rx=(dx*ca+dy*sa)/q.rx,ry=(-dx*sa+dy*ca)/q.ry,shape=Math.max(Math.abs(rx)*.92,Math.abs(ry)*.96,(Math.abs(rx)+Math.abs(ry))*.70);if(shape>1.12)continue;const outer=C((1.12-shape)/.30),inner=C((.72-shape)/.18),profile=.56*outer+.44*inner,local=q.lift*profile;if(local>plateLift){plateLift=local;plateEdge=1-inner;plateWarm=q.warm;}}
    const clod=Math.pow(C(.5+.5*grain),3.4)*S((grain2+.25)/1.1),pebble=Math.pow(C(.5+.5*grain2),8),pit=Math.pow(C(.5-.5*periodicField(u*7,v*7,seed+260,3)),7),hairline=Math.pow(C(.5+.5*Math.sin(TAU*(3*u+2*v)+periodicField(u,v,seed+290,2)*.50)),34)*(1-moisture);
    let h=.485+relief*(planeRaw*.031+planeStep*.023+plateLift+(clod-.30)*.022+pebble*.014-pit*.013-hairline*.004);h=C(h);const cavity=C(pit*.42+hairline*.30+plateEdge*.08+Math.max(0,-grain)*.05);
    let col=M(deep,mid,C(.50+broad*.19+(h-.48)*1.30));col=M(col,light,C(.18+Math.max(0,broad)*.25+Math.max(0,grain)*.12));col=M(col,ochre,C(.08+Math.max(0,secondary)*.16+clod*.10+plateWarm*plateLift*4.8));col=M(col,cool,C(.06+Math.max(0,-broad)*.20+Math.max(0,-grain)*.10));col=M(col,dust,C(pebble*.12+plateEdge*.05));col=M(col,ink,C(hairline*.24+pit*.12));col=M(col,[col[0]*.62,col[1]*.63,col[2]*.67],moisture*(.26+cavity*.22));
    baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.90-moisture*.23+cavity*.035+pebble*.025+Math.abs(grain2)*.018);ao.data[i]=C(.98-cavity*.22-pit*.10);
  }}
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
