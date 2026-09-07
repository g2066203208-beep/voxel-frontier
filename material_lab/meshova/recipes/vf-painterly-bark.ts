import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};

type Knot={cx:number;cy:number;rx:number;ry:number;twist:number};
function knots(seed:number):Knot[]{return[
  {cx:.22,cy:.33,rx:.072,ry:.060,twist:1},
  {cx:.72,cy:.69,rx:.082,ry:.067,twist:-1},
  {cx:.47,cy:.88,rx:.055,ry:.046,twist:hash(seed,900)<.5?-1:1},
];}

export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
  const seed=Math.floor(p.seed??275903),relief=Math.max(.75,Math.min(1.8,p.relief??1.44)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??12.0)),ridgeScale=Math.max(.82,Math.min(1.2,p.ridgeScale??1));
  const ridgeCount=Math.max(10,Math.min(15,Math.round(12*ridgeScale))),ks=knots(seed);
  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.018,.008,.012],deep:RGB=[.050,.019,.020],cool:RGB=[.080,.052,.067],mid:RGB=[.19,.068,.034],light:RGB=[.40,.17,.065],gold:RGB=[.60,.31,.105],scar:RGB=[.50,.23,.085];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      let knotWarp=0,knotRing=0,knotCore=0;
      for(const k of ks){
        const dx=wrapDelta(u-k.cx),dy=wrapDelta(v-k.cy),r=Math.sqrt((dx/k.rx)**2+(dy/k.ry)**2);
        const mask=S((1-r)/.38),ang=Math.atan2(dy/k.ry,dx/k.rx);
        knotWarp+=mask*Math.sin(ang)*.013*k.twist;
        knotRing=Math.max(knotRing,G((r-.72)/.13)*S((1.18-r)/.22));
        knotCore=Math.max(knotCore,G(r/.34));
      }
      const warp=periodicField(u*.34,v*.55,seed+120,3)*.018+Math.sin(TAU*v*1.15+hash(seed,7)*TAU)*.010+knotWarp;
      const coord=(u+warp)*ridgeCount;
      const cellId=((Math.floor(coord)%ridgeCount)+ridgeCount)%ridgeCount;
      const local=coord-Math.floor(coord)-.5;
      const side=Math.abs(local)*2;
      const triangular=C(1-side);
      const plateau=S((triangular-.12)/.40);
      const leftFacet=C((-.02-local)/.48),rightFacet=C((local+.02)/.48);
      const asym=(hash(seed,cellId,3)-.5)*.010;
      const crown=plateau*(.036+hash(seed,cellId,4)*.017)+leftFacet*.006-rightFacet*.004+asym;
      const seam=G((side-.985)/.040);
      const splitCenter=(hash(seed,cellId,5)-.5)*.30;
      const splitGate=hash(seed,cellId,6)>.58?G((local-splitCenter)/.025)*G(wrapDelta(v-hash(seed,cellId,7))/.22):0;
      const peel=hash(seed,cellId,8)>.54?G((local-(hash(seed,cellId,9)<.5?-.31:.31))/.085)*G(wrapDelta(v-hash(seed,cellId,10))/.10)*plateau:0;
      const fiberPhase=TAU*(ridgeCount*2.8*u+2.2*v)+periodicField(u,v,seed+300+cellId*7,2)*.55;
      const fiber=Math.sin(fiberPhase)*plateau;
      const micro=Math.pow(C(.5+.5*Math.sin(fiberPhase*1.61+hash(seed,cellId,11)*TAU)),23)*plateau;
      const wash=periodicField(u*.62,v*.45,seed+520+cellId*11,2);

      let h=.492+relief*(crown-seam*.034-splitGate*.020+peel*.016+knotRing*.012-knotCore*.007+fiber*.0035-micro*.003);
      h=C(h);
      const cavity=C(seam*.82+splitGate*.62+micro*.18+knotCore*.12);
      const edgeGold=G((side-.72)/.16)*plateau;
      let col=M(deep,mid,C(.28+plateau*.58));
      col=M(col,light,C(plateau*.28+rightFacet*.08));
      col=M(col,gold,C(edgeGold*.13+peel*.18+hash(seed,cellId,12)*plateau*.030));
      col=M(col,cool,C(leftFacet*.075+Math.max(0,-wash)*.06));
      col=M(col,ink,C(seam*.78+splitGate*.64+micro*.18));
      col=M(col,scar,C(knotRing*.24+peel*.10));
      col=M(col,wash>0?light:cool,Math.abs(wash)*.038*plateau);

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=h;roughness.data[i]=C(.84+cavity*.075-peel*.025+Math.abs(wash)*.018);ao.data[i]=C(1-cavity*.25-knotCore*.06);
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
