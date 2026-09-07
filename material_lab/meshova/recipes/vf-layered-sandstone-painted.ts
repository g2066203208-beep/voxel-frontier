import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB=[number,number,number];
export type VfLayeredSandstoneParams={
  seed?:number;
  bands?:number;
  minSlabs?:number;
  maxSlabs?:number;
  crackChance?:number;
  chipStrength?:number;
  relief?:number;
  normalStrength?:number;
};

type Slab={
  x0:number;x1:number;base:number;bulge:number;tiltX:number;tiltY:number;
  hue:number;warm:number;crackL:boolean;crackR:boolean;centerCrack:boolean;
  crackPos:number;chipL:number;chipR:number;strata:number[];
};
type Band={y0:number;y1:number;offset:number;slabs:Slab[]};

const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t)};

function hash(seed:number,a:number,b=0,c=0){
  let h=(seed|0)^Math.imul((a|0)+0x9e3779b9,0x85ebca6b)^Math.imul((b|0)+0x7f4a7c15,0xc2b2ae35)^Math.imul((c|0)+0x165667b1,0x27d4eb2d);
  h=Math.imul(h^(h>>>16),0x7feb352d);h=Math.imul(h^(h>>>15),0x846ca68b);h^=h>>>16;
  return (h>>>0)/0xffffffff;
}
function fbm(u:number,v:number,seed:number){
  let sum=0,amp=.55,norm=0,f=1;
  for(let i=0;i<3;i++){
    const x=Math.floor(u*f*17),y=Math.floor(v*f*17);
    sum+=(hash(seed,x,y,i)*2-1)*amp;norm+=amp;amp*=.5;f*=2.07;
  }
  return sum/Math.max(norm,1e-6);
}
function qBand(y:number,center:number,width:number){return Math.exp(-((y-center)/Math.max(width,1e-5))**2)}
function palette(t:number,warm:number):RGB{
  const shadow:RGB=[.31,.145,.085];
  const mid:RGB=[.62,.325,.155];
  const light:RGB=[.86,.585,.295];
  const cream:RGB=[.97,.785,.485];
  let c=t<.52?M(shadow,mid,S(t/.52)):M(mid,light,S((t-.52)/.48));
  c=M(c,cream,C(warm)*.30);
  return c;
}

function buildBands(seed:number,count:number,minSlabs:number,maxSlabs:number,crackChance:number):Band[]{
  const weights:number[]=[];let total=0;
  for(let i=0;i<count;i++){const w=.78+hash(seed,i,10)*.72;weights.push(w);total+=w;}
  const bands:Band[]=[];let y=0;
  for(let bi=0;bi<count;bi++){
    const h=weights[bi]/total;const y0=y,y1=bi===count-1?1:y+h;y=y1;
    const n=minSlabs+Math.floor(hash(seed,bi,11)*(maxSlabs-minSlabs+1));
    const widths:number[]=[];let sum=0;
    for(let si=0;si<n;si++){
      let w=.58+hash(seed,bi,si,12)*1.10;
      if((bi===Math.floor(count*.45)||bi===Math.floor(count*.58))&&si===Math.floor(n*.55))w*=1.65;
      widths.push(w);sum+=w;
    }
    let x=0;const slabs:Slab[]=[];
    for(let si=0;si<n;si++){
      const x0=x,x1=si===n-1?1:x+widths[si]/sum;x=x1;
      const strataCount=1+Math.floor(hash(seed,bi,si,20)*3);const strata:number[]=[];
      for(let k=0;k<strataCount;k++)strata.push(.20+hash(seed,bi,si,21+k)*.62);
      slabs.push({
        x0,x1,
        base:.47+(hash(seed,bi,si,30)-.5)*.075,
        bulge:.050+hash(seed,bi,si,31)*.085,
        tiltX:(hash(seed,bi,si,32)-.5)*.08,
        tiltY:(hash(seed,bi,si,33)-.5)*.055,
        hue:(hash(seed,bi,si,34)-.5)*.16,
        warm:hash(seed,bi,si,35),
        crackL:si>0&&hash(seed,bi,si,36)<crackChance,
        crackR:si<n-1&&hash(seed,bi,si,37)<crackChance*.70,
        centerCrack:(x1-x0)>.18&&hash(seed,bi,si,38)<crackChance*.72,
        crackPos:.36+hash(seed,bi,si,39)*.30,
        chipL:hash(seed,bi,si,40),chipR:hash(seed,bi,si,41),strata
      });
    }
    bands.push({y0,y1,offset:(hash(seed,bi,50)-.5)*.055 + (bi%3===1?.025:0),slabs});
  }
  return bands;
}

export function bakeVfLayeredSandstonePainted(size:number,p:VfLayeredSandstoneParams={}):Material{
  const seed=Math.floor(p.seed??771204);
  const count=Math.max(5,Math.min(10,Math.floor(p.bands??8)));
  const minSlabs=Math.max(2,Math.floor(p.minSlabs??3));
  const maxSlabs=Math.max(minSlabs,Math.floor(p.maxSlabs??5));
  const crackChance=C(p.crackChance??.22);
  const chipStrength=C(p.chipStrength??.58);
  const relief=Math.max(.4,Math.min(1.8,p.relief??1.15));
  const normalStrength=Math.max(1,Math.min(20,p.normalStrength??9.4));
  const bands=buildBands(seed,count,minSlabs,maxSlabs,crackChance);

  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);

  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    let bi=0;while(bi<bands.length-1&&v>=bands[bi].y1)bi++;
    const band=bands[bi];const bh=Math.max(band.y1-band.y0,1e-5);const vy=C((v-band.y0)/bh);
    for(let x=0;x<size;x++){
      const u=(x+.5)/size;
      let si=0;while(si<band.slabs.length-1&&u>=band.slabs[si].x1)si++;
      const slab=band.slabs[si];const sw=Math.max(slab.x1-slab.x0,1e-5);const ux=C((u-slab.x0)/sw);
      const dx=Math.min(ux,1-ux),dy=Math.min(vy,1-vy);
      const edgeDist=Math.min(dx,dy*.82);
      const bevel=S(edgeDist/.155);
      const topLip=qBand(vy,.13,.055),lowerLip=qBand(vy,.82,.050);
      const plane=slab.base+band.offset+slab.tiltX*(ux-.5)+slab.tiltY*(vy-.5);
      let h=plane + slab.bulge*(.18+.82*bevel) - (1-bevel)*(.040+.026*chipStrength);
      h+=topLip*.012+lowerLip*.004;

      let crack=0;
      if(slab.crackL)crack+=Math.exp(-((ux-.018)/.010)**2)*S((.95-vy)/.82);
      if(slab.crackR)crack+=Math.exp(-((ux-.982)/.010)**2)*S((.90-vy)/.80);
      if(slab.centerCrack){
        const wobble=(fbm(u*1.7,v*1.3,seed+bi*47+si*79))*0.030;
        crack+=Math.exp(-((ux-(slab.crackPos+wobble))/.011)**2)*S((vy-.10)/.24)*S((.95-vy)/.25);
      }
      const seamU=Math.min(u,1-u),seamV=Math.min(v,1-v);
      const tileCrack=Math.max(Math.exp(-(seamU/.010)**2)*.72,Math.exp(-(seamV/.010)**2)*.72);
      crack=Math.max(crack,tileCrack);

      let strata=0;
      for(let k=0;k<slab.strata.length;k++){
        const pos=slab.strata[k]+Math.sin((u*1.7+bi*.23+k*.37)*TAU)*.012;
        strata+=qBand(vy,pos,.010+.004*k);
      }
      const chipL=slab.chipL>.64?Math.exp(-((ux-.07)/.055)**2)*Math.exp(-((vy-.84)/.11)**2):0;
      const chipR=slab.chipR>.67?Math.exp(-((ux-.93)/.060)**2)*Math.exp(-((vy-.18)/.12)**2):0;
      const chip=(chipL+chipR)*chipStrength;
      h-=crack*.085*relief+chip*.030*relief;
      h+=(strata*.0035 + fbm(u*2.6,v*2.0,seed+401)*.006)*relief;
      h=.50+(h-.50)*relief;

      const cavity=C(crack*.78+(1-bevel)*.30+chip*.28);
      let t=C(.48+slab.hue+(h-.47)*1.25+(1-vy)*.10);
      let col=palette(t,slab.warm*.62+topLip*.35);
      const faceWarm=C(bevel*.32+topLip*.24+(1-vy)*.08);
      col=M(col,[.985,.80,.49],faceWarm*.22);
      col=M(col,[.33,.145,.075],C((1-bevel)*.48+cavity*.48));
      col=M(col,[.995,.855,.595],C(strata*.13));
      col=M(col,[.22,.095,.055],C(crack*.88));
      const wash=fbm(u*.72+bi*.13,v*.66+si*.17,seed+701);
      col=M(col,wash>0?[.92,.60,.33]:[.48,.235,.135],Math.abs(wash)*.055*bevel);

      const i=y*size+x,j=i*3;
      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=C(h);
      roughness.data[i]=Math.max(.04,Math.min(1,.69+(1-bevel)*.13+crack*.17+Math.abs(wash)*.025-strata*.025));
      ao.data[i]=C(1-cavity*.34-strata*.015);
      metallic.data[i]=0;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
