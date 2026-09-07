import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB=[number,number,number];
export type VfDirtParams={seed?:number;clodScale?:number;pebbleDensity?:number;moisture?:number;relief?:number;normalStrength?:number;};
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

function scatteredStones(u:number,v:number,seed:number,density:number){
  const cells=21,px=u*cells,py=v*cells,bx=Math.floor(px),by=Math.floor(py);let mask=0,kind=0,edge=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const cx=bx+ox,cy=by+oy,wx=((cx%cells)+cells)%cells,wy=((cy%cells)+cells)%cells;
    if(hash01(wx,wy,seed,1)>density)continue;
    const jx=.16+hash01(wx,wy,seed,2)*.68,jy=.16+hash01(wx,wy,seed,3)*.68;
    const ang=hash01(wx,wy,seed,4)*TAU,ca=Math.cos(ang),sa=Math.sin(ang);
    const rx=px-cx-jx,ry=py-cy-jy,ex=rx*ca-ry*sa,ey=rx*sa+ry*ca;
    const major=.12+hash01(wx,wy,seed,5)*.19,minor=major*(.52+hash01(wx,wy,seed,6)*.36);
    const d=Math.hypot(ex/major,ey/minor);
    const m=1-smooth(clamp01((d-.48)/.52));
    const e=(1-smooth(clamp01((Math.abs(d-.82)-.06)/.20)))*m;
    if(m>mask){mask=m;kind=hash01(wx,wy,seed,7);edge=e;}
  }
  return{mask,kind,edge};
}

export function bakeVfDirt(size:number,p:VfDirtParams={}):Material{
  const seed=Math.round(p.seed??420503),clodScale=Math.max(5,p.clodScale??9),pebbleDensity=clamp01(p.pebbleDensity??.20),moisture=clamp01(p.moisture??.08),relief=p.relief??1.24,normalStrength=p.normalStrength??14.0;
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);
  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size;
      const warpU=(pfbm(u,v,2,3,seed+11)-.5)*.065,warpV=(pfbm(u,v,2,3,seed+23)-.5)*.065;
      const du=wrap01(u+warpU),dv=wrap01(v+warpV);
      const macro=pfbm(du,dv,2,4,seed+101);
      const clod=pfbm(du,dv,clodScale,3,seed+201);
      const aggregate=pfbm(du,dv,28,3,seed+251);
      const grain=pfbm(du,dv,62,2,seed+301);
      const grit=pnoise(du,dv,137,seed+311);
      const dust=pnoise(du,dv,219,seed+317);
      const crumb=pnoise(du,dv,173,seed+323);
      const clodPeak=Math.pow(clamp01((clod-.28)/.72),1.45);
      const valley=smooth(clamp01((.43-clod)/.20));
      const creviceGate=.25+.75*smooth(clamp01((pfbm(du,dv,11,2,seed+233)-.47)/.34));
      const clodCrevice=valley*creviceGate;
      const microPit=smooth(clamp01((pnoise(du,dv,79,seed+401)-.81)/.15));
      const stones=scatteredStones(du,dv,seed+500,pebbleDensity);
      const h=clamp01(.43+(macro-.5)*.18*relief+(clodPeak-.48)*.19*relief+(aggregate-.5)*.090*relief+(grain-.5)*.058*relief+(grit-.5)*.032+(crumb-.5)*.020+(dust-.5)*.012-clodCrevice*.062-microPit*.035+stones.mask*.095-stones.edge*.016);

      const tone=clamp01(.18+macro*.36+clod*.26+aggregate*.14+grain*.06);
      let c=mix([.120,.066,.034],[.31,.188,.088],tone);
      const clayPatch=smooth(clamp01((pfbm(du,dv,5,3,seed+601)-.56)/.25));
      c=mix(c,[.34,.165,.073],clayPatch*.13);
      const damp=moisture*smooth(clamp01((.52-h)/.20));
      c=mix(c,[.060,.042,.028],damp*.70);
      if(stones.mask>0){
        const pc:RGB=stones.kind<.34?[.31,.29,.25]:stones.kind<.70?[.19,.18,.16]:[.40,.34,.26];
        c=mix(c,pc,stones.mask*.80);
      }
      const organic=smooth(clamp01((pnoise(du,dv,113,seed+707)-.91)/.07));
      c=mix(c,[.050,.045,.031],organic*.32);

      let rough=.86+(grain-.5)*.12+(grit-.5)*.08+(crumb-.5)*.05+clodCrevice*.06-damp*.27;
      rough=lerp(rough,.62,stones.mask*.78);
      rough=lerp(rough,.75,clayPatch*.14);
      rough=clamp01(rough);
      const occ=clamp01(1-clodCrevice*.22-microPit*.24-(1-clodPeak)*.045-stones.edge*.05);
      const idx=y*size+x,rgb=idx*3;
      baseColor.data[rgb]=c[0];baseColor.data[rgb+1]=c[1];baseColor.data[rgb+2]=c[2];
      height.data[idx]=h;roughness.data[idx]=rough;ao.data[idx]=occ;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
