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
  const lateralWarp=(pfbm(u,v,2,4,seed+11)-.5)*1.75+(pfbm(u,v,7,2,seed+17)-.5)*.42;
  const widthMod=.68+pfbm(u,v,5,3,seed+23)*.82;
  const phase=(u*scale+lateralWarp)*TAU;
  const s=Math.abs(Math.sin(phase));
  const main=1-smooth(clamp01((s-.022*widthMod)/(.105*widthMod)));
  const gate=.30+.70*smooth(clamp01((pfbm(u,v,3,3,seed+31)-.24)/.58));
  const broken=main*gate;
  const branchWave=Math.abs(Math.sin((u*(scale*.52)+v*1.95+(pfbm(u,v,4,3,seed+41)-.5)*1.65)*TAU));
  const branchGate=smooth(clamp01((pfbm(u,v,6,2,seed+47)-.56)/.31));
  const branch=(1-smooth(clamp01((branchWave-.016)/.090)))*branchGate*.66;
  return clamp01(Math.max(broken,branch));
}

export function bakeVfBark(size:number,p:VfBarkParams={}):Material{
  const seed=Math.round(p.seed??530603),ridgeScale=Math.max(4,p.ridgeScale??6.8),fissureScale=Math.max(2,p.fissureScale??3.4),age=clamp01(p.age??.72),relief=p.relief??1.34,normalStrength=p.normalStrength??13.2;
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);
  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size;
      const warpU=(pfbm(u,v,2,4,seed+71)-.5)*.095,warpV=(pfbm(u,v,2,3,seed+79)-.5)*.030;
      const du=wrap01(u+warpU),dv=wrap01(v+warpV);
      const fissure=barkFissures(du,dv,seed+101,fissureScale);
      const flowPhase=(du*ridgeScale+(pfbm(du,dv,3,4,seed+201)-.5)*1.70+(pfbm(du,dv,10,2,seed+207)-.5)*.38)*TAU;
      const ridge=Math.pow(clamp01(.5+.5*Math.cos(flowPhase)),1.72);
      const plate=pfbm(du,dv,5,4,seed+301);
      const plateFine=pfbm(du,dv,15,3,seed+311);
      const chip=pfbm(du,dv,31,2,seed+337);
      const fiber=pfbm(du,dv,61,2,seed+401);
      const micro=pnoise(du,dv,137,seed+409);
      const crossPhase=(dv*(4.4+pfbm(du,dv,2,2,seed+501)*3.1)+(pfbm(du,dv,4,3,seed+507)-.5)*1.45)*TAU;
      const crossBase=1-smooth(clamp01((Math.abs(Math.sin(crossPhase))-.024)/.105));
      const crossGate=smooth(clamp01((pfbm(du,dv,7,2,seed+513)-.54)/.34));
      const crossFissure=crossBase*crossGate*(.38+.62*age);
      const brokenPlate=smooth(clamp01((plate-.49)/.34))*smooth(clamp01((chip-.44)/.38));
      const flake=brokenPlate*(1-fissure)*(1-crossFissure)*age;
      const exposedEdge=smooth(clamp01((ridge-.36)/.42))*flake*.62;
      const pitted=smooth(clamp01((pnoise(du,dv,83,seed+541)-.84)/.12));

      const h=clamp01(.41+(ridge-.43)*.21*relief+(plate-.5)*.19*relief+(plateFine-.5)*.095*relief+(chip-.5)*.045*relief+(fiber-.5)*.052*relief+(micro-.5)*.024-fissure*.34*relief-crossFissure*.20*relief+flake*.075+exposedEdge*.038-pitted*.025);
      const tone=clamp01(.10+ridge*.30+plate*.31+plateFine*.17+chip*.08+fiber*.06);
      let c=mix([.060,.034,.022],[.235,.120,.060],tone);
      c=mix(c,[.34,.235,.145],flake*.28);
      c=mix(c,[.44,.315,.205],exposedEdge*.17);
      c=mix(c,[.020,.014,.011],fissure*.86);
      c=mix(c,[.032,.020,.014],crossFissure*.72);
      const greyAge=smooth(clamp01((pfbm(du,dv,3,3,seed+601)-.52)/.30))*age;
      c=mix(c,[.21,.205,.185],greyAge*.15);
      c=mix(c,[.018,.015,.012],pitted*.16);

      let rough=.80+(fiber-.5)*.14+(micro-.5)*.08+(chip-.5)*.06+fissure*.14+crossFissure*.13+flake*.05-ridge*.045-exposedEdge*.07;
      rough=clamp01(rough);
      const occ=clamp01(1-fissure*.62-crossFissure*.39-(1-ridge)*.05-flake*.03-pitted*.08);
      const idx=y*size+x,rgb=idx*3;
      baseColor.data[rgb]=c[0];baseColor.data[rgb+1]=c[1];baseColor.data[rgb+2]=c[2];
      height.data[idx]=h;roughness.data[idx]=rough;ao.data[idx]=occ;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
