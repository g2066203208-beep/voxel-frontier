import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB=[number,number,number];
export type VfLayeredSandstoneParams={seed?:number;bands?:number;minSlabs?:number;maxSlabs?:number;crackChance?:number;chipStrength?:number;relief?:number;normalStrength?:number;};
type Slab={
  cx:number;cy:number;hw:number;hh:number;angle:number;base:number;bulge:number;
  tiltX:number;tiltY:number;hue:number;warm:number;supports:number[];facets:number[];
  crack:boolean;crackX:number;crackTilt:number;crackY0:number;crackY1:number;
  chipX:number;chipY:number;chip:number;strata:number[];macro:boolean;rubble:boolean;
  brushX:number;brushY:number;brushSign:number;
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
  const shadow:RGB=[.175,.060,.030];
  const mid:RGB=[.435,.190,.072];
  const light:RGB=[.735,.425,.175];
  const cream:RGB=[.955,.705,.355];
  let c=t<.50?M(shadow,mid,S(t/.50)):M(mid,light,S((t-.50)/.50));
  return M(c,cream,C(warm)*.28);
}

function makeSlab(
  seed:number,r:number,i:number,cx:number,cy:number,hw:number,hh:number,
  base:number,bulge:number,crackChance:number,macro:boolean,rubble=false,
):Slab{
  const supports:number[]=[];
  const count=10;
  for(let k=0;k<count;k++){
    const lo=macro?.57:rubble?.54:.64;
    const span=macro?.69:rubble?.72:.57;
    supports.push(lo+hash(seed,r,i,30+k)*span);
  }
  const facets:number[]=[];for(let k=0;k<8;k++)facets.push(hash(seed,r,i,50+k)-.5);
  const strataCount=rubble?0:1+Math.floor(hash(seed,r,i,70)*3);
  const strata:number[]=[];for(let k=0;k<strataCount;k++)strata.push(-.50+hash(seed,r,i,71+k)*1.00);
  return{
    cx:(cx+2)%1,cy:(cy+2)%1,hw,hh,
    angle:(hash(seed,r,i,10)-.5)*(macro?.30:rubble?.48:.18),
    base,bulge,
    tiltX:(hash(seed,r,i,11)-.5)*(macro?.080:.060),
    tiltY:(hash(seed,r,i,12)-.5)*(macro?.070:.050),
    hue:(hash(seed,r,i,13)-.5)*.15,warm:hash(seed,r,i,14),supports,facets,
    crack:!rubble&&hash(seed,r,i,15)<crackChance,
    crackX:(hash(seed,r,i,16)-.5)*.44,crackTilt:(hash(seed,r,i,17)-.5)*.22,
    crackY0:-.62+hash(seed,r,i,18)*.30,crackY1:.30+hash(seed,r,i,19)*.42,
    chipX:(hash(seed,r,i,20)<.5?-1:1)*(.54+hash(seed,r,i,21)*.30),
    chipY:(hash(seed,r,i,22)-.5)*1.35,chip:hash(seed,r,i,23),strata,macro,rubble,
    brushX:(hash(seed,r,i,24)-.5)*.55,brushY:(hash(seed,r,i,25)-.5)*.75,
    brushSign:hash(seed,r,i,26)<.5?-1:1,
  };
}

function buildSlabs(seed:number,rows:number,minSlabs:number,maxSlabs:number,crackChance:number):Slab[]{
  const slabs:Slab[]=[];const rowStep=1/rows;
  // Low-profile support slabs: these provide strata but stay behind the hero boulders.
  for(let r=0;r<rows;r++){
    const n=minSlabs+Math.floor(hash(seed,r,100)*(maxSlabs-minSlabs+1));
    const raw:number[]=[];let total=0;
    for(let i=0;i<n;i++){const w=.68+hash(seed,r,i,101)*1.10;raw.push(w);total+=w;}
    let cursor=hash(seed,r,102)*.20-.10;
    for(let i=0;i<n;i++){
      const frac=raw[i]/total;const cx=cursor+frac*.5;cursor+=frac;
      const hh=rowStep*(.48+hash(seed,r,i,103)*.25);
      slabs.push(makeSlab(
        seed,r,i,cx,(r+.5)/rows+(hash(seed,r,i,104)-.5)*rowStep*.44,
        (frac+.035)*.56,hh,
        .385+(hash(seed,r,i,105)-.5)*.050+(r%3===1?.008:0),
        .036+hash(seed,r,i,106)*.050,crackChance*.55,false,false,
      ));
    }
  }

  // Hero boulders deliberately placed around the front-facing UV region.
  const hero:[number,number,number,number,number,number][]=[
    [.575,.505,.245,.145,.575,.145],
    [.305,.455,.175,.135,.535,.125],
    [.815,.440,.170,.145,.525,.120],
    [.420,.680,.205,.125,.535,.128],
    [.725,.690,.190,.130,.520,.120],
    [.190,.650,.145,.142,.505,.110],
    [.585,.290,.175,.105,.510,.110],
    [.405,.270,.145,.100,.485,.095],
  ];
  for(let m=0;m<hero.length;m++){
    const [ax,ay,hw,hh,base,bulge]=hero[m];
    slabs.push(makeSlab(
      seed,90,m,
      ax+(hash(seed,90,m,1)-.5)*.045,
      ay+(hash(seed,90,m,2)-.5)*.045,
      hw*(.90+hash(seed,90,m,3)*.22),hh*(.88+hash(seed,90,m,4)*.25),
      base+(hash(seed,90,m,5)-.5)*.040,
      bulge*(.86+hash(seed,90,m,6)*.28),
      crackChance*(m===0?1.40:.90),true,false,
    ));
  }

  // Small rubble clusters at top/bottom echo the reference silhouette without filling the middle.
  for(let side=0;side<2;side++){
    for(let k=0;k<9;k++){
      const cy=(side===0?.10:.90)+(hash(seed,120+side,k,1)-.5)*.12;
      const cx=(k+.35+hash(seed,120+side,k,2)*.55)/9;
      slabs.push(makeSlab(
        seed,120+side,k,cx,cy,.040+hash(seed,120+side,k,3)*.050,
        .035+hash(seed,120+side,k,4)*.055,
        .455+hash(seed,120+side,k,5)*.070,
        .050+hash(seed,120+side,k,6)*.060,0,false,true,
      ));
    }
  }
  return slabs;
}

function slabShape(x:number,y:number,s:Slab){
  let q=-99;const count=s.supports.length;
  for(let k=0;k<count;k++){
    const a=k*TAU/count;
    const d=(x*Math.cos(a)+y*Math.sin(a))/s.supports[k];
    if(d>q)q=d;
  }
  return q;
}

export function bakeVfLayeredSandstonePainted(size:number,p:VfLayeredSandstoneParams={}):Material{
  const seed=Math.floor(p.seed??771231);
  const rows=Math.max(5,Math.min(9,Math.floor(p.bands??6)));
  const minSlabs=Math.max(2,Math.floor(p.minSlabs??2));
  const maxSlabs=Math.max(minSlabs,Math.floor(p.maxSlabs??4));
  const crackChance=C(p.crackChance??.19),chipStrength=C(p.chipStrength??.82);
  const relief=Math.max(.5,Math.min(1.75,p.relief??1.42));
  const normalStrength=Math.max(1,Math.min(20,p.normalStrength??11.0));
  const slabs=buildSlabs(seed,rows,minSlabs,maxSlabs,crackChance);
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size;
      let bestH=.315+fbm(u*.40,v*.40,seed+701)*.008,secondH=.295,best=-1;
      let bestEdge=0,bestCrack=0,bestChip=0,bestStrata=0,bx=0,by=0,bestFacet=0,bestUnder=0;

      for(let si=0;si<slabs.length;si++){
        const s=slabs[si];
        const dx=wrapDelta(u-s.cx),dy=wrapDelta(v-s.cy);
        const ca=Math.cos(s.angle),sa=Math.sin(s.angle);
        const rx=dx*ca+dy*sa,ry=-dx*sa+dy*ca;
        if(Math.abs(rx)>s.hw*1.30||Math.abs(ry)>s.hh*1.34)continue;
        const x=rx/Math.max(s.hw,1e-5),y=ry/Math.max(s.hh,1e-5);
        const q=slabShape(x,y,s);if(q>1.045)continue;

        const bevelWidth=s.macro?.22:s.rubble?.26:.18;
        const edge=S((1-q)/bevelWidth);
        const dome=Math.max(0,1-Math.sqrt(x*x*.48+y*y*.82));
        const f0=s.facets[0]*x+s.facets[1]*y+.025;
        const f1=s.facets[2]*x+s.facets[3]*y-.020;
        const f2=s.facets[4]*x+s.facets[5]*y+.055;
        const f3=s.facets[6]*x+s.facets[7]*y-.050;
        const facet=Math.max(f0,f1,f2,f3)*(s.macro?.075:s.rubble?.045:.042);
        const topLip=G((y-.62)/.20)*edge;
        const under=G((y+.72)/.16)*edge;
        let surf=s.base+s.bulge*(.10+.70*edge+.20*dome)+s.tiltX*x+s.tiltY*y+facet;
        surf+=topLip*(s.macro?.022:.010);
        surf-=under*(s.macro?.050:s.rubble?.018:.025);
        surf-=(1-edge)*(s.macro?.035:s.rubble?.030:.022);

        let crack=0;
        if(s.crack){
          const lineX=s.crackX+s.crackTilt*y+(fbm(u*1.2,v*1.2,seed+si*31)*.018);
          const yr=S((y-s.crackY0)/.18)*S((s.crackY1-y)/.18);
          crack=G((x-lineX)/(s.macro?.025:.030))*yr;
          // small branch on hero fractures
          if(s.macro&&crack>.05){
            const branch=G((y-.05-x*.48)/.055)*G((x-(s.crackX+.08))/.30);
            crack=Math.max(crack,branch*.42);
          }
          surf-=crack*(s.macro?.100:.066)*relief;
        }

        const chip=s.chip>.48?G((x-s.chipX)/(s.macro?.16:.18))*G((y-s.chipY)/(s.macro?.18:.22))*chipStrength:0;
        surf-=chip*(s.macro?.085:s.rubble?.070:.050);

        let strata=0;
        for(let k=0;k<s.strata.length;k++){
          const pos=s.strata[k]+Math.sin((x*.48+k*.31+s.warm)*TAU)*.020;
          const gate=G((x-(hash(seed,si,k,300)-.5)*.35)/.92);
          strata+=qBand(y,pos,.014+.004*k)*gate;
        }
        surf+=strata*.0035;

        // Sparse face cuts make the hero rocks read as sculpted boulders rather than flat plaques.
        const cutA=G((x*.72+y*.42-.18)/.10)*G((x+.18)/.70);
        const cutB=G((x*.58-y*.55+.24)/.12)*G((x-.12)/.76);
        const faceCut=(cutA*.55+cutB*.38)*(s.macro?.1:.32);
        surf-=faceCut*(s.macro?.030:.010);

        surf=.50+(surf-.50)*relief;
        if(surf>bestH){
          secondH=bestH;bestH=surf;best=si;bestEdge=edge;bestCrack=crack;bestChip=chip;
          bestStrata=strata;bx=x;by=y;bestFacet=facet;bestUnder=under;
        }else if(surf>secondH)secondH=surf;
      }

      let col:RGB=[.205,.060,.026],r=.90,a=.68;
      if(best>=0){
        const s=slabs[best];
        const overlap=C((bestH-secondH)/.080);
        const cavity=C((1-bestEdge)*.45+bestCrack*.94+bestChip*.55+(1-overlap)*.12+bestUnder*.40);
        const t=C(.44+s.hue+(bestH-.42)*1.18+(1-by)*.045+bestFacet*.55);
        col=palette(t,s.warm*.42+bestEdge*.12);

        const warmTop=C(.48-by*.42+s.tiltY*2.5+bestFacet*2.0);
        col=M(col,[.975,.735,.405],warmTop*.11*bestEdge);
        col=M(col,[.125,.030,.012],cavity*.72);
        col=M(col,[.985,.825,.535],C(bestStrata*.095));
        col=M(col,[.085,.016,.008],bestCrack*.96);

        // A finite, directional paint stroke lives inside each rock face instead of global stripes.
        const brush=G((bx-s.brushX)/.68)*G((by-s.brushY)/.11)*bestEdge;
        col=M(col,s.brushSign>0?[.94,.61,.30]:[.32,.105,.045],brush*.055);
        const wash=fbm((u+s.cx)*.55,(v+s.cy)*.43,seed+907+best*13);
        col=M(col,wash>0?[.77,.39,.145]:[.34,.105,.042],Math.abs(wash)*.052*bestEdge);

        r=Math.max(.04,Math.min(1,.66+(1-bestEdge)*.13+bestCrack*.23+bestChip*.10+Math.abs(wash)*.025-bestStrata*.020));
        a=C(1-cavity*.46-bestUnder*.08-bestStrata*.010);
      }

      const i=py*size+px,j=i*3;
      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=C(bestH);roughness.data[i]=r;ao.data[i]=a;metallic.data[i]=0;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
