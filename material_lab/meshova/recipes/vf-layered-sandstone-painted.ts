import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB=[number,number,number];
export type VfLayeredSandstoneParams={seed?:number;bands?:number;minSlabs?:number;maxSlabs?:number;crackChance?:number;chipStrength?:number;relief?:number;normalStrength?:number;};
type Slab={cx:number;cy:number;hw:number;hh:number;base:number;bulge:number;tiltX:number;tiltY:number;hue:number;warm:number;supports:number[];facets:number[];crack:boolean;crackX:number;crackTilt:number;crackY0:number;crackY1:number;chipX:number;chipY:number;chip:number;strata:number[];};

const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t)};
const G=(x:number)=>Math.exp(-(x*x));
function wrapDelta(x:number){return x-Math.round(x)}
function hash(seed:number,a:number,b=0,c=0){let h=(seed|0)^Math.imul((a|0)+0x9e3779b9,0x85ebca6b)^Math.imul((b|0)+0x7f4a7c15,0xc2b2ae35)^Math.imul((c|0)+0x165667b1,0x27d4eb2d);h=Math.imul(h^(h>>>16),0x7feb352d);h=Math.imul(h^(h>>>15),0x846ca68b);h^=h>>>16;return(h>>>0)/0xffffffff;}
function fbm(u:number,v:number,seed:number){let sum=0,amp=.55,norm=0,f=1;for(let i=0;i<3;i++){const x=Math.floor(u*f*13),y=Math.floor(v*f*13);sum+=(hash(seed,x,y,i)*2-1)*amp;norm+=amp;amp*=.5;f*=2.03;}return sum/Math.max(norm,1e-6);}
function qBand(y:number,center:number,width:number){return G((y-center)/Math.max(width,1e-5))}
function palette(t:number,warm:number):RGB{const shadow:RGB=[.29,.13,.075],mid:RGB=[.60,.30,.145],light:RGB=[.84,.55,.275],cream:RGB=[.97,.77,.46];let c=t<.50?M(shadow,mid,S(t/.50)):M(mid,light,S((t-.50)/.50));return M(c,cream,C(warm)*.32);}

function buildSlabs(seed:number,rows:number,minSlabs:number,maxSlabs:number,crackChance:number):Slab[]{
  const slabs:Slab[]=[];
  const rowStep=1/rows;
  for(let r=0;r<rows;r++){
    const n=minSlabs+Math.floor(hash(seed,r,10)*(maxSlabs-minSlabs+1));
    const raw:number[]=[];let total=0;
    for(let i=0;i<n;i++){let w=.62+hash(seed,r,i,11)*1.15;if((r===Math.floor(rows*.42)||r===Math.floor(rows*.57))&&i===Math.floor(n*.55))w*=1.55;raw.push(w);total+=w;}
    const overlap=.035+hash(seed,r,12)*.035;
    let cursor=hash(seed,r,13)*.18-0.09;
    for(let i=0;i<n;i++){
      const frac=raw[i]/total;
      const w=frac+overlap;
      const cx=cursor+frac*.5;
      cursor+=frac;
      const central=1-Math.min(1,Math.abs((r+.5)/rows-.5)*1.75);
      const hh=rowStep*(.64+hash(seed,r,i,14)*.32);
      const supports:number[]=[];for(let k=0;k<8;k++)supports.push(.78+hash(seed,r,i,30+k)*.34);
      const facets:number[]=[];for(let k=0;k<6;k++)facets.push((hash(seed,r,i,50+k)-.5));
      const strataCount=1+Math.floor(hash(seed,r,i,60)*3);const strata:number[]=[];for(let k=0;k<strataCount;k++)strata.push(-.48+hash(seed,r,i,61+k)*.96);
      slabs.push({
        cx:cx-Math.floor(cx),
        cy:((r+.5)/rows+(hash(seed,r,i,15)-.5)*rowStep*.34+1)%1,
        hw:w*.58,
        hh,
        base:.455+(hash(seed,r,i,16)-.5)*.055+central*.035+(r%3===1?.014:0),
        bulge:.060+hash(seed,r,i,17)*.075,
        tiltX:(hash(seed,r,i,18)-.5)*.055,
        tiltY:(hash(seed,r,i,19)-.5)*.045,
        hue:(hash(seed,r,i,20)-.5)*.15,
        warm:hash(seed,r,i,21),
        supports,facets,
        crack:hash(seed,r,i,22)<crackChance,
        crackX:(hash(seed,r,i,23)-.5)*.48,
        crackTilt:(hash(seed,r,i,24)-.5)*.18,
        crackY0:-.55+hash(seed,r,i,25)*.28,
        crackY1:.30+hash(seed,r,i,26)*.35,
        chipX:(hash(seed,r,i,27)<.5?-1:1)*(.63+hash(seed,r,i,28)*.18),
        chipY:(hash(seed,r,i,29)-.5)*1.2,
        chip:hash(seed,r,i,31),
        strata
      });
    }
  }
  return slabs;
}

function slabShape(x:number,y:number,s:Slab){
  let q=-99;
  for(let k=0;k<8;k++){
    const a=k*TAU/8;const d=(x*Math.cos(a)+y*Math.sin(a))/s.supports[k];if(d>q)q=d;
  }
  return q;
}

export function bakeVfLayeredSandstonePainted(size:number,p:VfLayeredSandstoneParams={}):Material{
  const seed=Math.floor(p.seed??771204),rows=Math.max(5,Math.min(10,Math.floor(p.bands??7))),minSlabs=Math.max(2,Math.floor(p.minSlabs??3)),maxSlabs=Math.max(minSlabs,Math.floor(p.maxSlabs??5));
  const crackChance=C(p.crackChance??.20),chipStrength=C(p.chipStrength??.65),relief=Math.max(.5,Math.min(1.7,p.relief??1.20)),normalStrength=Math.max(1,Math.min(20,p.normalStrength??9.8));
  const slabs=buildSlabs(seed,rows,minSlabs,maxSlabs,crackChance);
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size;
      let bestH=.365+fbm(u*.45,v*.45,seed+701)*.006,secondH=.34,best=-1,bestEdge=0,bestCrack=0,bestChip=0,bestStrata=0,bx=0,by=0;
      for(let si=0;si<slabs.length;si++){
        const s=slabs[si];
        const dx=wrapDelta(u-s.cx),dy=wrapDelta(v-s.cy);
        if(Math.abs(dx)>s.hw*1.16||Math.abs(dy)>s.hh*1.18)continue;
        const x=dx/Math.max(s.hw,1e-5),y=dy/Math.max(s.hh,1e-5),q=slabShape(x,y,s);
        if(q>1.04)continue;
        const edge=S((1-q)/.16);
        const f0=s.facets[0]*x+s.facets[1]*y;
        const f1=s.facets[2]*x+s.facets[3]*y+.055;
        const f2=s.facets[4]*x+s.facets[5]*y-.045;
        const facet=Math.max(f0,f1,f2)*.030;
        let surf=s.base+s.bulge*(.12+.88*edge)+s.tiltX*x+s.tiltY*y+facet-(1-edge)*.020;
        let crack=0;
        if(s.crack){const lineX=s.crackX+s.crackTilt*y;const yr=S((y-s.crackY0)/.18)*S((s.crackY1-y)/.18);crack=G((x-lineX)/.027)*yr;surf-=crack*.070*relief;}
        const chip=s.chip>.62?G((x-s.chipX)/.18)*G((y-s.chipY)/.22)*chipStrength:0;surf-=chip*.050;
        let strata=0;for(let k=0;k<s.strata.length;k++){const pos=s.strata[k]+Math.sin((x*.55+k*.31+s.warm)*TAU)*.025;strata+=qBand(y,pos,.018+.004*k);}surf+=strata*.003;
        surf=.50+(surf-.50)*relief;
        if(surf>bestH){secondH=bestH;bestH=surf;best=si;bestEdge=edge;bestCrack=crack;bestChip=chip;bestStrata=strata;bx=x;by=y;}else if(surf>secondH)secondH=surf;
      }

      let col:RGB=[.36,.17,.09],r=.86,a=.78;
      if(best>=0){
        const s=slabs[best];const overlap=C((bestH-secondH)/.08);const cavity=C((1-bestEdge)*.42+bestCrack*.82+bestChip*.45+(1-overlap)*.08);
        const t=C(.50+s.hue+(bestH-.45)*1.25+(1-by)*.055);
        col=palette(t,s.warm*.60+bestEdge*.16);
        // painterly face hierarchy: warm top/convex planes, red-brown recesses
        const topFace=C(.50-by*.38+s.tiltY*2.5);col=M(col,[.98,.79,.48],topFace*.12*bestEdge);
        col=M(col,[.34,.15,.075],cavity*.48);
        col=M(col,[.985,.84,.58],C(bestStrata*.11));
        col=M(col,[.205,.085,.045],bestCrack*.88);
        const wash=fbm((u+s.cx)*.60,(v+s.cy)*.48,seed+907+best*13);col=M(col,wash>0?[.89,.54,.28]:[.47,.21,.115],Math.abs(wash)*.050*bestEdge);
        r=Math.max(.04,Math.min(1,.67+(1-bestEdge)*.12+bestCrack*.20+bestChip*.08+Math.abs(wash)*.025-bestStrata*.025));
        a=C(1-cavity*.33-bestStrata*.012);
      }
      const i=py*size+px,j=i*3;baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=C(bestH);roughness.data[i]=r;ao.data[i]=a;metallic.data[i]=0;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
