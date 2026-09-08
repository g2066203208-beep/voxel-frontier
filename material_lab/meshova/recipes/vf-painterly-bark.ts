import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
type Knot={cx:number;cy:number;rx:number;ry:number;twist:number};
function knots(seed:number):Knot[]{return[
  {cx:.20,cy:.34,rx:.075,ry:.060,twist:1},
  {cx:.73,cy:.68,rx:.086,ry:.070,twist:-1},
  {cx:.48,cy:.87,rx:.058,ry:.048,twist:hash(seed,900)<.5?-1:1},
];}

export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
  const seed=Math.floor(p.seed??275903),relief=Math.max(.8,Math.min(1.8,p.relief??1.42)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??12.6)),ridgeScale=Math.max(.82,Math.min(1.2,p.ridgeScale??1));
  const ridgeCount=Math.max(7,Math.min(11,Math.round(8.5*ridgeScale))),ks=knots(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.016,.007,.012],deep:RGB=[.046,.017,.021],cool:RGB=[.073,.050,.071],mid:RGB=[.185,.062,.030],light:RGB=[.405,.165,.060],gold:RGB=[.625,.315,.095],scar:RGB=[.50,.215,.080];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      let knotWarp=0,knotRing=0,knotCore=0;
      for(const k of ks){
        const dx=wrapDelta(u-k.cx),dy=wrapDelta(v-k.cy),r=Math.sqrt((dx/k.rx)**2+(dy/k.ry)**2),mask=S((1-r)/.40),ang=Math.atan2(dy/k.ry,dx/k.rx);
        knotWarp+=mask*Math.sin(ang)*.020*k.twist;
        knotRing=Math.max(knotRing,G((r-.74)/.12)*S((1.17-r)/.21));
        knotCore=Math.max(knotCore,G(r/.32));
      }

      const longWarp=periodicField(u,v,seed+120,3)*.035+periodicField(u,v,seed+127,2)*.018;
      const lateral=Math.sin(TAU*(v*.77+hash(seed,7)))*.016+Math.sin(TAU*(v*1.63+hash(seed,8)))*.007;
      const raw=(u+longWarp+lateral+knotWarp)*ridgeCount;
      const baseCell=Math.floor(raw),cellId=((baseCell%ridgeCount)+ridgeCount)%ridgeCount;

      // Local branch/merge events offset only a portion of a ridge, breaking the pumpkin-like continuity.
      const branchV=hash(seed,cellId,20),branchSign=hash(seed,cellId,21)<.5?-1:1;
      const branchMask=G(wrapDelta(v-branchV)/(.095+hash(seed,cellId,22)*.050));
      const branchShift=(hash(seed,cellId,23)>.42?branchSign*(.10+hash(seed,cellId,24)*.12)*branchMask:0);
      const coord=raw+branchShift;
      const local=coord-Math.floor(coord)-.5;

      const widthPulse=.88+.16*Math.sin(TAU*(v*(.72+hash(seed,cellId,30)*.78)+hash(seed,cellId,31)))+.11*periodicField(u,v,seed+330+cellId*9,2);
      const widthScale=(.76+hash(seed,cellId,32)*.44)*widthPulse;
      const side=Math.abs(local)*2/Math.max(.42,widthScale);
      const shoulder=C((1.16-side)/.44),table=C((.78-side)/.20),crown=C((.48-side)/.18);
      const profile=.42*shoulder+.38*table+.20*crown;

      const lean=(hash(seed,cellId,3)-.5)*.014;
      const leftFacet=C((-.01-local)/(.42*widthScale)),rightFacet=C((local+.01)/(.42*widthScale));
      const ridgeLift=(.036+hash(seed,cellId,4)*.030)*(.88+.22*Math.sin(TAU*(v*(1.1+hash(seed,cellId,5))+.2*hash(seed,cellId,6))));
      const crownHeight=profile*ridgeLift+leftFacet*.006-rightFacet*.004+lean;

      const groove=G((side-1.06)/.040);
      const splitCenter=(hash(seed,cellId,40)-.5)*.28;
      const splitSpan=.12+hash(seed,cellId,41)*.18;
      const splitGate=hash(seed,cellId,42)>.48?G((local-splitCenter)/.014)*G(wrapDelta(v-hash(seed,cellId,43))/splitSpan)*table:0;
      const crossBreak=hash(seed,cellId,44)>.63?G(wrapDelta(v-hash(seed,cellId,45))/.020)*G((side-.62)/.18)*shoulder:0;
      const peel=hash(seed,cellId,46)>.54?G((local-(hash(seed,cellId,47)<.5?-.31:.31))/.065)*G(wrapDelta(v-hash(seed,cellId,48))/.080)*table:0;

      const fiberPhase=TAU*(ridgeCount*2.3*u+1.4*v)+periodicField(u,v,seed+360+cellId*7,2)*.62;
      const fiber=Math.sin(fiberPhase)*table;
      const micro=Math.pow(C(.5+.5*Math.sin(fiberPhase*1.73+hash(seed,cellId,49)*TAU)),26)*table;
      const wash=periodicField(u,v,seed+520+cellId*11,2);

      let h=.485+relief*(crownHeight-groove*.014-splitGate*.014-crossBreak*.010+peel*.014+knotRing*.012-knotCore*.006+fiber*.0027-micro*.0020);
      h=C(h);
      const cavity=C(groove*.46+splitGate*.56+crossBreak*.30+micro*.13+knotCore*.09);
      const edgeGold=G((side-.68)/.16)*table;
      let col=M(deep,mid,C(.24+table*.61));
      col=M(col,light,C(table*.30+rightFacet*.09));
      col=M(col,gold,C(edgeGold*.18+peel*.22+hash(seed,cellId,50)*table*.034));
      col=M(col,cool,C(leftFacet*.095+Math.max(0,-wash)*.072));
      col=M(col,ink,C(groove*.54+splitGate*.72+crossBreak*.34+micro*.13));
      col=M(col,scar,C(knotRing*.29+peel*.12));
      col=M(col,wash>0?light:cool,Math.abs(wash)*.052*table);

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=h;roughness.data[i]=C(.845+cavity*.065-peel*.028+Math.abs(wash)*.018);ao.data[i]=C(1-cavity*.22-knotCore*.052);
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
