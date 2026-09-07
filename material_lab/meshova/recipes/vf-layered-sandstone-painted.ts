import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB=[number,number,number];
export type VfLayeredSandstoneParams={seed?:number;bands?:number;minSlabs?:number;maxSlabs?:number;crackChance?:number;chipStrength?:number;relief?:number;normalStrength?:number;};
type Slab={
  cx:number;cy:number;hw:number;hh:number;angle:number;base:number;bulge:number;
  tiltX:number;tiltY:number;hue:number;warm:number;supports:number[];facets:number[];
  crack:boolean;crackX:number;crackTilt:number;crackY0:number;crackY1:number;
  chipX:number;chipY:number;chipX2:number;chipY2:number;chip:number;strata:number[];
  macro:boolean;rubble:boolean;brushX:number;brushY:number;brushSign:number;
};

const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t)};
const G=(x:number)=>Math.exp(-(x*x));
function wrapDelta(x:number){return x-Math.round(x)}
function hash(seed:number,a:number,b=0,c=0){
  let h=(seed|0)^Math.imul((a|0)+0x9e3779b9,0x85ebca6b)^Math.imul((b|0)+0x7f4a7c15,0xc2b2ae35)^Math.imul((c|0)+0x165667b1,0x27d4eb2d);
  h=Math.imul(h^(h>>>16),0x7feb352d);h=Math.imul(h^(h>>>15),0x846ca68b);h^=h>>>16;
  return(h>>>0)/0xffffffff;
}
function fbm(u:number,v:number,seed:number){
  let sum=0,amp=.55,norm=0,f=1;
  for(let i=0;i<3;i++){
    const x=Math.floor(u*f*13),y=Math.floor(v*f*13);
    sum+=(hash(seed,x,y,i)*2-1)*amp;norm+=amp;amp*=.5;f*=2.03;
  }
  return sum/Math.max(norm,1e-6);
}
function qBand(y:number,center:number,width:number){return G((y-center)/Math.max(width,1e-5))}
function palette(t:number,warm:number):RGB{
  const shadow:RGB=[.155,.052,.026];
  const mid:RGB=[.400,.165,.062];
  const light:RGB=[.675,.365,.145];
  const cream:RGB=[.910,.625,.300];
  let c=t<.50?M(shadow,mid,S(t/.50)):M(mid,light,S((t-.50)/.50));
  return M(c,cream,C(warm)*.27);
}

function makeSlab(
  seed:number,r:number,i:number,cx:number,cy:number,hw:number,hh:number,
  base:number,bulge:number,crackChance:number,macro:boolean,rubble=false,
):Slab{
  const supports:number[]=[];
  const count=12;
  for(let k=0;k<count;k++){
    const lo=macro?.58:rubble?.53:.66;
    const span=macro?.66:rubble?.76:.54;
    supports.push(lo+hash(seed,r,i,30+k)*span);
  }
  const facets:number[]=[];for(let k=0;k<8;k++)facets.push(hash(seed,r,i,50+k)-.5);
  const strataCount=rubble?0:1+Math.floor(hash(seed,r,i,70)*3);
  const strata:number[]=[];for(let k=0;k<strataCount;k++)strata.push(-.48+hash(seed,r,i,71+k)*.96);
  return{
    cx:(cx+2)%1,cy:(cy+2)%1,hw,hh,
    angle:(hash(seed,r,i,10)-.5)*(macro?.22:rubble?.48:.16),
    base,bulge,
    tiltX:(hash(seed,r,i,11)-.5)*(macro?.085:.055),
    tiltY:(hash(seed,r,i,12)-.5)*(macro?.075:.048),
    hue:(hash(seed,r,i,13)-.5)*.14,warm:hash(seed,r,i,14),supports,facets,
    crack:!rubble&&hash(seed,r,i,15)<crackChance,
    crackX:(hash(seed,r,i,16)-.5)*.42,crackTilt:(hash(seed,r,i,17)-.5)*.23,
    crackY0:-.65+hash(seed,r,i,18)*.31,crackY1:.31+hash(seed,r,i,19)*.43,
    chipX:(hash(seed,r,i,20)<.5?-1:1)*(.52+hash(seed,r,i,21)*.31),
    chipY:(hash(seed,r,i,22)-.5)*1.35,
    chipX2:(hash(seed,r,i,27)<.5?-1:1)*(.57+hash(seed,r,i,28)*.26),
    chipY2:(hash(seed,r,i,29)-.5)*1.28,
    chip:hash(seed,r,i,23),strata,macro,rubble,
    brushX:(hash(seed,r,i,24)-.5)*.52,brushY:(hash(seed,r,i,25)-.5)*.70,
    brushSign:hash(seed,r,i,26)<.5?-1:1,
  };
}

function buildSlabs(seed:number,rows:number,minSlabs:number,maxSlabs:number,crackChance:number):Slab[]{
  const slabs:Slab[]=[];const rowStep=1/rows;

  // Quiet support layer. Its only job is to close gaps behind the hero boulders.
  for(let r=0;r<rows;r++){
    const n=minSlabs+Math.floor(hash(seed,r,100)*(maxSlabs-minSlabs+1));
    const raw:number[]=[];let total=0;
    for(let i=0;i<n;i++){const w=.75+hash(seed,r,i,101)*1.05;raw.push(w);total+=w;}
    let cursor=hash(seed,r,102)*.16-.08;
    for(let i=0;i<n;i++){
      const frac=raw[i]/total;const cx=cursor+frac*.5;cursor+=frac;
      const hh=rowStep*(.43+hash(seed,r,i,103)*.20);
      slabs.push(makeSlab(
        seed,r,i,cx,(r+.5)/rows+(hash(seed,r,i,104)-.5)*rowStep*.38,
        (frac+.030)*.56,hh,
        .400+(hash(seed,r,i,105)-.5)*.035,
        .030+hash(seed,r,i,106)*.035,crackChance*.35,false,false,
      ));
    }
  }

  // Thick, reference-driven hero boulders. These dominate the visible hemisphere.
  const hero:[number,number,number,number,number,number][]=[
    [.575,.500,.205,.165,.585,.155],
    [.315,.445,.165,.150,.545,.135],
    [.805,.440,.155,.155,.535,.128],
    [.405,.665,.175,.145,.545,.135],
    [.705,.675,.170,.145,.535,.128],
    [.175,.625,.125,.155,.515,.115],
    [.570,.295,.160,.120,.530,.120],
    [.350,.270,.125,.110,.500,.100],
    [.790,.255,.120,.105,.495,.100],
    [.560,.820,.155,.105,.500,.105],
    [.285,.800,.115,.095,.485,.095],
    [.805,.805,.115,.095,.490,.095],
  ];
  for(let m=0;m<hero.length;m++){
    const [ax,ay,hw,hh,base,bulge]=hero[m];
    slabs.push(makeSlab(
      seed,90,m,
      ax+(hash(seed,90,m,1)-.5)*.035,
      ay+(hash(seed,90,m,2)-.5)*.035,
      hw*(.91+hash(seed,90,m,3)*.18),hh*(.91+hash(seed,90,m,4)*.18),
      base+(hash(seed,90,m,5)-.5)*.030,
      bulge*(.91+hash(seed,90,m,6)*.20),
      crackChance*(m===0?1.55:.92),true,false,
    ));
  }

  // v9 cleanup: no independent polar rubble slabs. The reference silhouette is now
  // produced only by attached hero/support boulders, eliminating tiny floating chips.
  return slabs;
}

function slabShape(x:number,y:number,s:Slab,seed:number,index:number){
  let polygon=-99;const count=s.supports.length;
  for(let k=0;k<count;k++){
    const a=k*TAU/count;
    const d=(x*Math.cos(a)+y*Math.sin(a))/s.supports[k];
    if(d>polygon)polygon=d;
  }
  // Intersect the chiseled polygon with a soft ellipse and perturb the boundary slightly.
  const radial=Math.sqrt(x*x*.70+y*y*.92);
  return Math.max(polygon,radial*.82)+fbm(x*.72+index*.09,y*.72-index*.07,seed+index*19)*.028;
}

export function bakeVfLayeredSandstonePainted(size:number,p:VfLayeredSandstoneParams={}):Material{
  const seed=Math.floor(p.seed??771231);
  const rows=Math.max(5,Math.min(8,Math.floor(p.bands??5)));
  const minSlabs=Math.max(2,Math.floor(p.minSlabs??2));
  const maxSlabs=Math.max(minSlabs,Math.floor(p.maxSlabs??3));
  const crackChance=C(p.crackChance??.20),chipStrength=C(p.chipStrength??.88);
  const relief=Math.max(.5,Math.min(1.75,p.relief??1.46));
  const normalStrength=Math.max(1,Math.min(20,p.normalStrength??11.5));
  const slabs=buildSlabs(seed,rows,minSlabs,maxSlabs,crackChance);
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size;
      let bestH=.395+fbm(u*.35,v*.35,seed+701)*.008,secondH=.375,best=-1;
      let bestEdge=0,bestCrack=0,bestChip=0,bestStrata=0,bx=0,by=0,bestFacetTone=0,bestRidge=0,bestUnder=0;

      for(let si=0;si<slabs.length;si++){
        const s=slabs[si];
        const dx=wrapDelta(u-s.cx),dy=wrapDelta(v-s.cy);
        const ca=Math.cos(s.angle),sa=Math.sin(s.angle);
        const rx=dx*ca+dy*sa,ry=-dx*sa+dy*ca;
        if(Math.abs(rx)>s.hw*1.35||Math.abs(ry)>s.hh*1.38)continue;
        const x=rx/Math.max(s.hw,1e-5),y=ry/Math.max(s.hh,1e-5);
        const q=slabShape(x,y,s,seed,si);if(q>1.045)continue;

        const bevelWidth=s.macro?.245:s.rubble?.26:.19;
        const edge=S((1-q)/bevelWidth);
        const dome=Math.max(0,1-Math.sqrt(x*x*.52+y*y*.78));
        const planes=[
          s.facets[0]*x+s.facets[1]*y+.030,
          s.facets[2]*x+s.facets[3]*y-.018,
          s.facets[4]*x+s.facets[5]*y+.052,
          s.facets[6]*x+s.facets[7]*y-.046,
        ];
        let pTop=-99,pSecond=-99;
        for(const qv of planes){if(qv>pTop){pSecond=pTop;pTop=qv}else if(qv>pSecond)pSecond=qv}
        const facetAmp=s.macro?.105:s.rubble?.050:.045;
        const facet=pTop*facetAmp;
        const ridge=1-S((pTop-pSecond)/(s.macro?.085:.065));
        const topLip=G((y-.58)/.20)*edge;
        const under=G((y+.67)/.15)*edge;
        const broadUndulation=fbm(x*.34+s.cx,y*.34+s.cy,seed+si*43)*(.012+(s.macro?.010:0));
        let surf=s.base+s.bulge*(.12+.65*edge+.23*dome)+s.tiltX*x+s.tiltY*y+facet+broadUndulation;
        surf+=topLip*(s.macro?.025:.010);
        surf-=under*(s.macro?.058:s.rubble?.020:.024);
        surf-=(1-edge)*(s.macro?.040:s.rubble?.032:.022);

        let crack=0;
        if(s.crack){
          const lineX=s.crackX+s.crackTilt*y+fbm(u*1.2,v*1.2,seed+si*31)*.018;
          const yr=S((y-s.crackY0)/.18)*S((s.crackY1-y)/.18);
          // v9 cleanup: a single naturally meandering crack only. The old artificial
          // cross-branch was removed because it created the visible '+' engraving.
          crack=G((x-lineX)/(s.macro?.023:.030))*yr;
          surf-=crack*(s.macro?.112:.065)*relief;
        }

        const chip1=s.chip>.42?G((x-s.chipX)/(s.macro?.15:.18))*G((y-s.chipY)/(s.macro?.18:.22)):0;
        const chip2=s.chip>.72?G((x-s.chipX2)/(s.macro?.13:.17))*G((y-s.chipY2)/(s.macro?.16:.20)):0;
        // Keep edge wear, but soften the secondary notch so it cannot sever a tiny island.
        const chip=(chip1+chip2*.42)*chipStrength;
        surf-=chip*(s.macro?.078:s.rubble?.060:.045);

        let strata=0;
        for(let k=0;k<s.strata.length;k++){
          const pos=s.strata[k]+Math.sin((x*.42+k*.31+s.warm)*TAU)*.018;
          const gate=G((x-(hash(seed,si,k,300)-.5)*.30)/.78);
          strata+=qBand(y,pos,.013+.004*k)*gate;
        }
        surf+=strata*.0035;

        // v9 cleanup: remove the pair of crossing decorative cut equations entirely.
        // Facet boundaries + geological cracks now provide all linework.

        surf=.50+(surf-.50)*relief;
        if(surf>bestH){
          secondH=bestH;bestH=surf;best=si;bestEdge=edge;bestCrack=crack;bestChip=chip;
          bestStrata=strata;bx=x;by=y;bestFacetTone=pTop;bestRidge=ridge;bestUnder=under;
        }else if(surf>secondH)secondH=surf;
      }

      let col:RGB=[.285,.105,.040],r=.88,a=.80;
      if(best>=0){
        const s=slabs[best];
        const overlap=C((bestH-secondH)/.085);
        const cavity=C((1-bestEdge)*.40+bestCrack*.94+bestChip*.52+(1-overlap)*.10+bestUnder*.46);
        const t=C(.43+s.hue+(bestH-.43)*1.00+(1-by)*.040+bestFacetTone*.28);
        col=palette(t,s.warm*.38+bestEdge*.12);

        // Paint each sculpted plane differently: this makes the form read at thumbnail size.
        const planeWarm=C(.50+bestFacetTone*1.9-by*.28);
        col=M(col,[.940,.665,.325],planeWarm*.11*bestEdge);
        col=M(col,[.235,.082,.032],C(.50-planeWarm)*.13*bestEdge);
        col=M(col,[.975,.750,.420],bestRidge*.055*bestEdge);
        col=M(col,[.105,.022,.008],cavity*.70);
        col=M(col,[.985,.815,.515],C(bestStrata*.10));
        col=M(col,[.065,.010,.004],bestCrack*.97);

        // Finite hand-painted streaks on individual faces, never global stripes.
        const brush=G((bx-s.brushX)/.62)*G((by-s.brushY)/.095)*bestEdge;
        col=M(col,s.brushSign>0?[.91,.55,.245]:[.275,.075,.025],brush*.060);
        const wash=fbm((u+s.cx)*.53,(v+s.cy)*.41,seed+907+best*13);
        col=M(col,wash>0?[.69,.325,.115]:[.28,.075,.026],Math.abs(wash)*.055*bestEdge);

        r=Math.max(.04,Math.min(1,.68+(1-bestEdge)*.12+bestCrack*.22+bestChip*.10+Math.abs(wash)*.023-bestStrata*.020));
        a=C(1-cavity*.43-bestUnder*.10-bestStrata*.010);
      }

      const i=py*size+px,j=i*3;
      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=C(bestH);roughness.data[i]=r;ao.data[i]=a;metallic.data[i]=0;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
