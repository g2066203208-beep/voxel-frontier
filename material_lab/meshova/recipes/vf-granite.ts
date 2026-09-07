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

const TAU = Math.PI * 2;
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (x: number) => x * x * (3 - 2 * x);
const smoother = (x: number) => { const t = clamp01(x); return t*t*t*(t*(t*6-15)+10); };
const lerp = (a: number, b: number, t: number) => a + (b-a)*t;
const mix = (a: RGB, b: RGB, t: number): RGB => [lerp(a[0],b[0],t), lerp(a[1],b[1],t), lerp(a[2],b[2],t)];
const wrap01 = (x: number) => x - Math.floor(x);

function hash01(x:number,y:number,seed:number,salt=0){
  let h=Math.imul(x|0,0x1f123bb5)^Math.imul(y|0,0x5f356495)^Math.imul(seed|0,0x2c9277b5)^Math.imul(salt|0,0x27d4eb2d);
  h=Math.imul(h^(h>>>15),0x2c1b3c6d); h=Math.imul(h^(h>>>12),0x297a2d39); h^=h>>>15;
  return (h>>>0)/0xffffffff;
}
function pnoise(u:number,v:number,f:number,seed:number){
  f=Math.max(1,f|0); const px=u*f, py=v*f, x0=Math.floor(px), y0=Math.floor(py);
  const tx=smoother(px-x0), ty=smoother(py-y0), w=(n:number)=>((n%f)+f)%f;
  const a=w(x0), b=w(x0+1), c=w(y0), d=w(y0+1);
  return lerp(lerp(hash01(a,c,seed),hash01(b,c,seed),tx),lerp(hash01(a,d,seed),hash01(b,d,seed),tx),ty);
}
function pfbm(u:number,v:number,base:number,oct:number,seed:number){
  let s=0,w=0,a=1; for(let i=0;i<oct;i++){s+=pnoise(u,v,Math.max(1,Math.round(base*2**i)),seed+i*101)*a;w+=a;a*=0.5;} return s/Math.max(w,1e-6);
}

function sparseFlakes(u:number,v:number,seed:number,density:number){
  const cells=34, px=u*cells, py=v*cells, bx=Math.floor(px), by=Math.floor(py); let mask=0, value=0;
  for(let oy=-1;oy<=1;oy++) for(let ox=-1;ox<=1;ox++){
    const cx=bx+ox,cy=by+oy,wx=((cx%cells)+cells)%cells,wy=((cy%cells)+cells)%cells;
    if(hash01(wx,wy,seed,1)>density) continue;
    const jx=.16+hash01(wx,wy,seed,2)*.68, jy=.16+hash01(wx,wy,seed,3)*.68;
    const rx=px-cx-jx, ry=py-cy-jy, ang=hash01(wx,wy,seed,4)*TAU, ca=Math.cos(ang), sa=Math.sin(ang);
    const ex=rx*ca-ry*sa, ey=rx*sa+ry*ca;
    const major=.15+hash01(wx,wy,seed,5)*.23, minor=major*(.20+hash01(wx,wy,seed,6)*.28);
    const d=Math.hypot(ex/major,ey/minor), m=1-smooth(clamp01((d-.48)/.52));
    if(m>mask){mask=m;value=hash01(wx,wy,seed,7);}
  }
  return {mask,value};
}

export function bakeVfGranite(size:number,params:VfGraniteParams={}):Material{
  const seed=Math.round(params.seed??310402);
  const grainScale=Math.max(10,Math.round(params.grainScale??23));
  const relief=params.relief??1.18;
  const normalStrength=params.normalStrength??11.5;
  const q=clamp01(params.quartz??0.29), f=clamp01(params.feldspar??0.49), mica=clamp01(params.mica??0.10);
  const baseColor=makeTexture(size,size,3),metallic=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),height=makeTexture(size,size,1),emission=makeTexture(size,size,3);

  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size;
      const warpU=(pfbm(u,v,3,3,seed+11)-.5)*.055;
      const warpV=(pfbm(u,v,3,3,seed+23)-.5)*.055;
      const du=wrap01(u+warpU), dv=wrap01(v+warpV);
      const macro=pfbm(du,dv,2,4,seed+101);
      const coarse=pfbm(du,dv,grainScale,2,seed+201);
      const fine=pfbm(du,dv,grainScale*2.15,2,seed+211);
      const crystal=pnoise(du,dv,grainScale*3.8,seed+223);
      const qField=pfbm(du+.071,dv-.039,grainScale*.82,2,seed+301);
      const fField=pfbm(du-.047,dv+.063,grainScale*.95,2,seed+313);
      const qMask=smooth(clamp01((qField-(.60-q*.18))/.19));
      const fMask=(1-qMask)*smooth(clamp01((fField-(.52-f*.12))/.23));
      const matrix=clamp01(1-qMask-fMask);
      const flakes=sparseFlakes(du,dv,seed+701,.23+mica*.55);

      let c:RGB=mix([.29,.30,.30],[.42,.42,.40],clamp01(.25+coarse*.52+fine*.18));
      const feldspar:RGB=mix([.43,.31,.29],[.68,.49,.43],clamp01(.25+fField*.72));
      const quartz:RGB=mix([.55,.56,.55],[.76,.74,.70],clamp01(.18+qField*.76));
      c=mix(c,feldspar,fMask*.88);
      c=mix(c,quartz,qMask*.82);
      c=mix(c,[.055,.055,.060],flakes.mask*(.82+.12*flakes.value));
      const warmVeil=smooth(clamp01((pfbm(du,dv,5,3,seed+401)-.50)/.28));
      c=mix(c,[.49,.35,.32],warmVeil*.08);
      const exposure=.90+macro*.18;
      c=[clamp01(c[0]*exposure),clamp01(c[1]*exposure),clamp01(c[2]*exposure)];

      const crystalRelief=(crystal-.5)*.058 + (fine-.5)*.047;
      const quartzLift=qMask*(.018+(qField-.5)*.024);
      const feldLift=fMask*(.012+(fField-.5)*.019);
      const micaCut=flakes.mask*.028;
      const boundaryTexture=(Math.abs(qField-.56)<.045?1:0)*qMask + (Math.abs(fField-.54)<.038?1:0)*fMask;
      const h=clamp01(.49+(macro-.5)*.20*relief+(coarse-.5)*.085*relief+crystalRelief*relief+quartzLift+feldLift-micaCut-boundaryTexture*.010);

      let rough=.67 + (fine-.5)*.12 + matrix*.035;
      rough=lerp(rough,.48,qMask*.72);
      rough=lerp(rough,.61,fMask*.70);
      rough=lerp(rough,.40,flakes.mask*.78);
      rough=clamp01(rough);
      const cavity=clamp01(flakes.mask*.22 + boundaryTexture*.06);
      const occ=clamp01(1-cavity);

      const idx=y*size+x,rgb=idx*3;
      baseColor.data[rgb]=c[0];baseColor.data[rgb+1]=c[1];baseColor.data[rgb+2]=c[2];
      height.data[idx]=h;roughness.data[idx]=rough;ao.data[idx]=occ;
    }
  }
  const normal=heightToNormal(height,normalStrength,true);
  return {baseColor,metallic,roughness,normal,ao,height,emission};
}
