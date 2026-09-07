import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB = [number, number, number];
export type VfGraniteParams = {
  seed?: number;
  grainScale?: number;
  quartz?: number;
  feldspar?: number;
  mica?: number;
  relief?: number;
  normalStrength?: number;
};

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (x: number) => x*x*(3-2*x);
const lerp = (a: number,b: number,t: number) => a+(b-a)*t;
const mix = (a: RGB,b: RGB,t: number): RGB => [lerp(a[0],b[0],t),lerp(a[1],b[1],t),lerp(a[2],b[2],t)];
function hash01(x:number,y:number,seed:number,salt=0){let h=Math.imul(x|0,0x1f123bb5)^Math.imul(y|0,0x5f356495)^Math.imul(seed|0,0x2c9277b5)^Math.imul(salt|0,0x27d4eb2d);h=Math.imul(h^(h>>>15),0x2c1b3c6d);h=Math.imul(h^(h>>>12),0x297a2d39);h^=h>>>15;return (h>>>0)/0xffffffff;}
function pnoise(u:number,v:number,f:number,seed:number){f=Math.max(1,f|0);const px=u*f,py=v*f,x0=Math.floor(px),y0=Math.floor(py),tx=smooth(px-x0),ty=smooth(py-y0),w=(n:number)=>((n%f)+f)%f;const a=w(x0),b=w(x0+1),c=w(y0),d=w(y0+1);return lerp(lerp(hash01(a,c,seed),hash01(b,c,seed),tx),lerp(hash01(a,d,seed),hash01(b,d,seed),tx),ty);}
function pfbm(u:number,v:number,base:number,oct:number,seed:number){let s=0,w=0,a=1;for(let i=0;i<oct;i++){s+=pnoise(u,v,Math.max(1,Math.round(base*2**i)),seed+i*101)*a;w+=a;a*=0.5;}return s/w;}

function mineralField(u:number,v:number,cells:number,seed:number){
  const px=u*cells,py=v*cells,bx=Math.floor(px),by=Math.floor(py);let d1=99,d2=99,kind=0,rv=0;
  for(let oy=-1;oy<=1;oy++) for(let ox=-1;ox<=1;ox++){
    const cx=bx+ox,cy=by+oy,wx=((cx%cells)+cells)%cells,wy=((cy%cells)+cells)%cells;
    const jx=0.15+hash01(wx,wy,seed,1)*0.7,jy=0.15+hash01(wx,wy,seed,2)*0.7;
    const dx=px-cx-jx,dy=py-cy-jy,d=Math.hypot(dx,dy);
    if(d<d1){d2=d1;d1=d;kind=hash01(wx,wy,seed,3);rv=hash01(wx,wy,seed,4);}else if(d<d2)d2=d;
  }
  const boundary=clamp01((d2-d1)*2.2);
  return {d:d1,boundary,kind,rv};
}

export function bakeVfGranite(size:number,params:VfGraniteParams={}):Material{
  const seed=Math.round(params.seed??310401),cells=Math.round(params.grainScale??19),relief=params.relief??1.0,normalStrength=params.normalStrength??7.0;
  const q=params.quartz??0.30,f=params.feldspar??0.47,m=params.mica??0.12;
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);
  for(let y=0;y<size;y++){const v=1-(y+0.5)/size;for(let x=0;x<size;x++){const u=(x+0.5)/size;const warpU=(pfbm(u,v,2,3,seed+11)-0.5)*0.035,warpV=(pfbm(u,v,2,3,seed+23)-0.5)*0.035,du=u+warpU,dv=v+warpV;const g=mineralField(du,dv,cells,seed+1000);const macro=pfbm(du,dv,2,4,seed+101),micro=pfbm(du,dv,34,2,seed+201);let c:RGB;let mineralLift=0,rough=0.74;const k=g.kind;if(k<q){c=mix([0.62,0.59,0.56],[0.80,0.77,0.72],g.rv);mineralLift=0.020;rough=0.54;}else if(k<q+f){c=mix([0.38,0.31,0.30],[0.62,0.47,0.42],g.rv);mineralLift=0.010;rough=0.66;}else if(k<q+f+m){c=mix([0.045,0.048,0.052],[0.14,0.13,0.14],g.rv);mineralLift=-0.012;rough=0.42;}else{c=mix([0.28,0.29,0.29],[0.48,0.49,0.47],g.rv);rough=0.70;}
      const boundary=1-g.boundary;const speck=smooth(clamp01((pnoise(du,dv,97,seed+311)-0.82)/0.14));const h=clamp01(0.50+(macro-0.5)*0.23*relief+(micro-0.5)*0.045*relief+mineralLift-boundary*0.025+speck*0.007);c=[clamp01(c[0]*(0.90+macro*0.18)),clamp01(c[1]*(0.90+macro*0.18)),clamp01(c[2]*(0.90+macro*0.18))];const idx=y*size+x,rgb=idx*3;baseColor.data[rgb]=c[0];baseColor.data[rgb+1]=c[1];baseColor.data[rgb+2]=c[2];height.data[idx]=h;roughness.data[idx]=clamp01(rough+(micro-0.5)*0.12+boundary*0.08-speck*0.08);ao.data[idx]=clamp01(1-boundary*0.16);}}
  const normal=heightToNormal(height,normalStrength,true);return {baseColor,metallic,roughness,normal,ao,height,emission};
}
