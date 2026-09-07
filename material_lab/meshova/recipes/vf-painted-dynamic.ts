import { makeTexture, type Material } from "../../src/index.js";
import { bakeVfBasaltPainted, type VfPaintedParams } from "./vf-painted-wilderness.js";

type RGB=[number,number,number];
type Tex={width:number;height:number;channels:number;data:Float32Array};

export type VfDynamicPaintedParams = VfPaintedParams & {
  wetness?: number;
  frost?: number;
  snowCoverage?: number;
  snowDepth?: number;
};

const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const L=(a:number,b:number,t:number)=>a+(b-a)*t;
const M=(a:RGB,b:RGB,t:number):RGB=>[L(a[0],b[0],t),L(a[1],b[1],t),L(a[2],b[2],t)];
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t);};

function periodicField(u:number,v:number){
  const a=Math.sin((u*2+v*3)*TAU+0.65)*.5+.5;
  const b=Math.sin((u*5-v*2)*TAU+1.70)*.5+.5;
  const c=Math.sin((u*3+v*5)*TAU+2.35)*.5+.5;
  return C(a*.48+b*.32+c*.20);
}

function broadNormal(h:Tex,strength:number,radius:number){
  const n=makeTexture(h.width,h.height,3),w=h.width,hh=h.height,r=Math.max(1,Math.round(radius));
  const at=(x:number,y:number)=>h.data[((y%hh+hh)%hh)*w+((x%w+w)%w)];
  for(let y=0;y<hh;y++)for(let x=0;x<w;x++){
    const dx=(at(x+r,y)-at(x-r,y))*strength;
    const dy=(at(x,y+r)-at(x,y-r))*strength;
    let nx=-dx,ny=dy,nz=1;
    const q=Math.hypot(nx,ny,nz)||1; nx/=q; ny/=q; nz/=q;
    const i=(y*w+x)*3;
    n.data[i]=nx*.5+.5; n.data[i+1]=ny*.5+.5; n.data[i+2]=nz*.5+.5;
  }
  return n;
}

export function bakeVfBasaltPaintedDynamic(size:number,p:VfDynamicPaintedParams={}):Material{
  const wet=C(Number(p.wetness??0));
  const frost=C(Number(p.frost??0));
  const snow=C(Number(p.snowCoverage??0));
  const snowDepth=C(Number(p.snowDepth??0.45));

  const base=bakeVfBasaltPainted(size,p);
  if(!base.height) throw new Error("vf painted dynamic basalt requires height");

  const bc=makeTexture(size,size,3);
  const met=makeTexture(size,size,1);
  const rough=makeTexture(size,size,1);
  const ao=makeTexture(size,size,1);
  const height=makeTexture(size,size,1);
  const em=makeTexture(size,size,3);

  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size;
      const i=y*size+x,j=i*3;
      const c0:RGB=[base.baseColor.data[j],base.baseColor.data[j+1],base.baseColor.data[j+2]];
      const h0=base.height.data[i];
      const a0=base.ao?base.ao.data[i]:1;
      const r0=base.roughness.data[i];
      const pf=periodicField(u,v);
      const cavity=C(1-a0);

      // Wetness gathers preferentially in cavities and broad low fields.
      const wetPool=C(wet*(.58+.42*S(C((cavity-.02)/.24)))*(.76+.24*(1-pf)));
      const wetTint:RGB=[.030,.050,.070];
      let col=M(c0,wetTint,wetPool*.34);
      let r=L(r0,.24,wetPool*.78);
      let h=h0;
      let a=a0;

      // Frost starts on exposed/high painted faces, while some damp cavities remain dark.
      const frostMask=C(frost*S(C((h0-.42)/.36))*(.64+.36*pf)*(1-wetPool*.35));
      col=M(col,[.625,.745,.840],frostMask*.72);
      col=M(col,[.790,.835,.865],frostMask*S(C((pf-.58)/.30))*.22);
      r=L(r,.86,frostMask*.82);
      h=C(h+frostMask*.018);
      a=C(L(a,1,frostMask*.22));

      // Snow accumulates in broad coherent regions; coverage is continuous, not a texture swap.
      const snowField=C(pf*.58+(h0)*.42);
      const threshold=L(.86,.20,snow);
      const snowMask=C(S(C((snowField-threshold)/.22))*snow);
      const deep=S(C((snowMask-.24)/.60));
      const snowShadow:RGB=[.405,.575,.745];
      const snowLight:RGB=[.955,.950,.905];
      const snowColor=M(snowShadow,snowLight,C(.36+h0*.46+pf*.18));
      col=M(col,snowColor,snowMask*.96);
      r=L(r,.88,snowMask*.90);
      h=C(h+snowMask*(.028+.070*snowDepth)*(.72+.28*deep));
      a=C(L(a,1,snowMask*.68));

      bc.data[j]=C(col[0]); bc.data[j+1]=C(col[1]); bc.data[j+2]=C(col[2]);
      met.data[i]=0;
      rough.data[i]=C(r);
      ao.data[i]=C(a);
      height.data[i]=C(h);
      em.data[j]=em.data[j+1]=em.data[j+2]=0;
    }
  }

  const normal=broadNormal(height,10.2,6);
  return{baseColor:bc,metallic:met,roughness:rough,normal,ao,height,emission:em};
}
