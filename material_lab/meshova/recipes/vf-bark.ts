import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB=[number,number,number];
export type VfBarkParams={seed?:number;ridgeScale?:number;fissureScale?:number;age?:number;relief?:number;normalStrength?:number;};
const TAU=Math.PI*2;
const clamp01=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>x*x*(3-2*x);
const smoother=(x:number)=>{const t=clamp01(x);return t*t*t*(t*(t*6-15)+10);};
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const mix=(a:RGB,b:RGB,t:number):RGB=>[lerp(a[0],b[0],t),lerp(a[1],b[1],t),lerp(a[2],b[2],t)];
const wrap01=(x:number)=>x-Math.floor(x);
function hash01(x:number,y:number,seed:number,salt=0){let h=Math.imul(x|0,0x1f123bb5)^Math.imul(y|0,0x5f356495)^Math.imul(seed|0,0x2c9277b5)^Math.imul(salt|0,0x27d4eb2d);h=Math.imul(h^(h>>>15),0x2c1b3c6d);h=Math.imul(h^(h>>>12),0x297a2d39);h^=h>>>15;return(h>>>0)/0xffffffff;}
function pnoise(u:number,v:number,f:number,seed:number){f=Math.max(1,f|0);const px=u*f,py=v*f,x0=Math.floor(px),y0=Math.floor(py),tx=smoother(px-x0),ty=smoother(py-y0),w=(n:number)=>((n%f)+f)%f;const a=w(x0),b=w(x0+1),c=w(y0),d=w(y0+1);return lerp(lerp(hash01(a,c,seed),hash01(b,c,seed),tx),lerp(hash01(a,d,seed),hash01(b,d,seed),tx),ty);}
function pfbm(u:number,v:number,b:number,o:number,s:number){let sum=0,w=0,a=1;for(let i=0;i<o;i++){sum+=pnoise(u,v,Math.max(1,Math.round(b*2**i)),s+i*101)*a;w+=a;a*=.5;}return sum/Math.max(w,1e-6);}

function barkFissures(u:number,v:number,seed:number,scale:number){
  const lateralWarp=(pfbm(u,v,2,4,seed+11)-.5)*1.55+(pfbm(u,v,7,2,seed+17)-.5)*.34;
  const widthMod=.72+pfbm(u,v,5,3,seed+23)*.72;
  const phase=(u*scale+lateralWarp)*TAU;
  const s=Math.abs(Math.sin(phase));
  const main=1-smooth(clamp01((s-.025*widthMod)/(.105*widthMod)));
  const gate=.42+.58*smooth(clamp01((pfbm(u,v,3,3,seed+31)-.28)/.52));
  const broken=main*gate;
  const branchWave=Math.abs(Math.sin((u*(scale*.58)+v*1.75+(pfbm(u,v,4,3,seed+41)-.5)*1.4)*TAU));
  const branchGate=smooth(clamp01((pfbm(u,v,6,2,seed+47)-.59)/.27));
  const branch=(1-smooth(clamp01((branchWave-.018)/.095)))*branchGate*.58;
  return clamp01(Math.max(broken,branch));
}

export function bakeVfBark(size:number,p:VfBarkParams={}):Material{
  const seed=Math.round(p.seed??530602),ridgeScale=Math.max(5,p.ridgeScale??8.2),fissureScale=Math.max(2,p.fissureScale??4.0),age=clamp01(p.age??.68),relief=p.relief??1.24,normalStrength=p.normalStrength??11.6;
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);
  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size;
      const warpU=(pfbm(u,v,2,4,seed+71)-.5)*.075,warpV=(pfbm(u,v,2,3,seed+79)-.5)*.025;
      const du=wrap01(u+warpU),dv=wrap01(v+warpV);
      const fissure=barkFissures(du,dv,seed+101,fissureScale);
      const flowPhase=(du*ridgeScale + (pfbm(du,dv,3,4,seed+201)-.5)*1.45 + (pfbm(du,dv,9,2,seed+207)-.5)*.28)*TAU;
      const wave=.5+.5*Math.cos(flowPhase);
      const ridge=Math.pow(clamp01(wave),1.55);
      const plate=pfbm(du,dv,5,4,seed+301);
      const plateFine=pfbm(du,dv,13,3,seed+311);
      const fiber=pfbm(du,dv,48,2,seed+401);
      const micro=pnoise(du,dv,119,seed+409);

      const crossPhase=(dv*(3.2+pfbm(du,dv,2,2,seed+501)*2.4)+(pfbm(du,dv,4,3,seed+507)-.5)*1.2)*TAU;
      const crossBase=1-smooth(clamp01((Math.abs(Math.sin(crossPhase))-.030)/.115));
      const crossGate=smooth(clamp01((pfbm(du,dv,7,2,seed+513)-.61)/.28));
      const crossFissure=crossBase*crossGate*(.35+.65*age);
      const flakeGate=smooth(clamp01((plate-.55)/.30))*smooth(clamp01((plateFine-.48)/.32));
      const flake=flakeGate*(1-fissure)*(1-crossFissure)*age;
      const exposedEdge=smooth(clamp01((ridge-.43)/.36))*flake*.52;

      const h=clamp01(.42+(ridge-.46)*.20*relief+(plate-.5)*.17*relief+(plateFine-.5)*.075*relief+(fiber-.5)*.045*relief+(micro-.5)*.018-fissure*.31*relief-crossFissure*.17*relief+flake*.055+exposedEdge*.028);

      const tone=clamp01(.12+ridge*.34+plate*.31+plateFine*.16+fiber*.07);
      let c=mix([.070,.037,.021],[.285,.145,.064],tone);
      c=mix(c,[.40,.27,.145],flake*.30);
      c=mix(c,[.48,.34,.20],exposedEdge*.16);
      c=mix(c,[.025,.017,.013],fissure*.82);
      c=mix(c,[.040,.024,.016],crossFissure*.62);
      const greyAge=smooth(clamp01((pfbm(du,dv,3,3,seed+601)-.57)/.26))*age;
      c=mix(c,[.24,.225,.195],greyAge*.11);

      let rough=.77+(fiber-.5)*.13+(micro-.5)*.07+fissure*.16+crossFissure*.13+flake*.06-ridge*.055-exposedEdge*.08;
      rough=clamp01(rough);
      const occ=clamp01(1-fissure*.58-crossFissure*.34-(1-ridge)*.055-flake*.025);
      const idx=y*size+x,rgb=idx*3;
      baseColor.data[rgb]=c[0];baseColor.data[rgb+1]=c[1];baseColor.data[rgb+2]=c[2];
      height.data[idx]=h;roughness.data[idx]=rough;ao.data[idx]=occ;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
