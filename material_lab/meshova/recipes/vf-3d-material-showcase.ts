import { makeTexture, heightToNormal, type Material } from "../../src/index.js";
import { C, L, M, S, TAU, hash, periodicField, ridgeField, type RGB } from "./vf-painterly-core.js";

type Tex = ReturnType<typeof makeTexture>;
export type Vf3DShowcaseParams = { seed?: number; density?: number; height?: number; wind?: number; };
export type Vf3DShowcaseBundle = { material: Material; masks: Readonly<Record<string, Tex>> };

function finish(size:number,baseColor:Tex,roughness:Tex,height:Tex,ao:Tex,normalStrength:number,emission?:Tex):Material{
  return {baseColor,metallic:makeTexture(size,size,1),roughness,normal:heightToNormal(height,normalStrength,true),ao,height,emission:emission??makeTexture(size,size,3)};
}
function setRGB(tex:Tex,i:number,c:RGB){const j=i*3;tex.data[j]=C(c[0]);tex.data[j+1]=C(c[1]);tex.data[j+2]=C(c[2]);}

export function bakeVf3DGrass(size:number,p:Vf3DShowcaseParams={}):Vf3DShowcaseBundle{
  const seed=Math.floor(Number(p.seed??73117)),density=C(Number(p.density??.82)),bladeHeight=C(Number(p.height??.78)),wind=C(Number(p.wind??.42));
  const baseColor=makeTexture(size,size,3),rough=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const bladeDensity=makeTexture(size,size,1),bladeLength=makeTexture(size,size,1),bladeBend=makeTexture(size,size,1);
  const soil:RGB=[.17,.105,.052],deep:RGB=[.105,.19,.045],mid:RGB=[.27,.44,.075],light:RGB=[.56,.66,.16];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const macro=periodicField(u,v,seed+11,3)*.5+.5,clump=periodicField(u*2,v*2,seed+67,4)*.5+.5,dir=ridgeField(u,v,seed+101,4,1.12);
    const grass=C(S((clump-(.34-.18*density))/.48));
    const c=M(M(soil,deep,grass),M(mid,light,C(.24+.70*macro)),grass*.88);
    setRGB(baseColor,i,c); rough.data[i]=L(.88,.69,grass); height.data[i]=C(.28+grass*(.10+.07*macro)+dir*.018); ao.data[i]=L(.72,.94,grass);
    bladeDensity.data[i]=C(grass*(.58+.42*macro)*density); bladeLength.data[i]=C(bladeHeight*(.48+.52*clump)); bladeBend.data[i]=C(wind*(.35+.65*dir));
  }
  return {material:finish(size,baseColor,rough,height,ao,7.5),masks:{bladeDensity,bladeLength,bladeBend}};
}

export function bakeVf3DMoss(size:number,p:Vf3DShowcaseParams={}):Vf3DShowcaseBundle{
  const seed=Math.floor(Number(p.seed??55109)),density=C(Number(p.density??.76)),mossHeight=C(Number(p.height??.62));
  const baseColor=makeTexture(size,size,3),rough=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const mossDensity=makeTexture(size,size,1),mossHeightMask=makeTexture(size,size,1),tuftVariation=makeTexture(size,size,1);
  const rock:RGB=[.18,.20,.17],dark:RGB=[.12,.25,.055],mid:RGB=[.31,.48,.085],light:RGB=[.63,.69,.18];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const rockField=periodicField(u,v,seed+3,4)*.5+.5,patch=periodicField(u*1.5,v*1.5,seed+41,4)*.5+.5,fuzz=periodicField(u*6,v*6,seed+93,3)*.5+.5;
    const moss=C(S((patch-(.43-.22*density))/.38));
    const mc=M(dark,M(mid,light,fuzz),.52+.32*rockField); const c=M(rock,mc,moss*.94);
    setRGB(baseColor,i,c);rough.data[i]=L(.84,.96,moss);height.data[i]=C(.30+rockField*.065+moss*(.055+.045*fuzz));ao.data[i]=L(.71,.90,moss);
    mossDensity.data[i]=C(moss*density);mossHeightMask.data[i]=C(mossHeight*(.35+.65*fuzz));tuftVariation.data[i]=fuzz;
  }
  return {material:finish(size,baseColor,rough,height,ao,8.2),masks:{mossDensity,mossHeight:mossHeightMask,tuftVariation}};
}

export function bakeVf3DFur(size:number,p:Vf3DShowcaseParams={}):Vf3DShowcaseBundle{
  const seed=Math.floor(Number(p.seed??91007)),density=C(Number(p.density??.90)),furHeight=C(Number(p.height??.82)),wind=C(Number(p.wind??.30));
  const baseColor=makeTexture(size,size,3),rough=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const strandDensity=makeTexture(size,size,1),strandLength=makeTexture(size,size,1),strandBend=makeTexture(size,size,1),strandVariation=makeTexture(size,size,1);
  const dark:RGB=[.20,.105,.045],mid:RGB=[.58,.34,.14],light:RGB=[.91,.72,.42],cream:RGB=[.97,.86,.63];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const broad=periodicField(u,v,seed+15,3)*.5+.5,fine=periodicField(u*3,v*3,seed+72,4)*.5+.5,flow=ridgeField(u,v,seed+110,5,.36);
    const c=M(M(dark,mid,broad),M(light,cream,fine),.42+.34*flow);setRGB(baseColor,i,c);
    rough.data[i]=.82;height.data[i]=C(.34+.025*broad+.018*flow);ao.data[i]=.88;
    strandDensity.data[i]=C(density*(.72+.28*fine));strandLength.data[i]=C(furHeight*(.58+.42*broad));strandBend.data[i]=C(wind*(.35+.65*flow));strandVariation.data[i]=fine;
  }
  return {material:finish(size,baseColor,rough,height,ao,4.8),masks:{strandDensity,strandLength,strandBend,strandVariation}};
}

export function bakeVf3DFire(size:number,p:Vf3DShowcaseParams={}):Vf3DShowcaseBundle{
  const seed=Math.floor(Number(p.seed??44021)),density=C(Number(p.density??.88)),flameHeight=C(Number(p.height??.90)),wind=C(Number(p.wind??.34));
  const baseColor=makeTexture(size,size,3),rough=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),emission=makeTexture(size,size,3);
  const flameDensity=makeTexture(size,size,1),flameHeightMask=makeTexture(size,size,1),heatDistortion=makeTexture(size,size,1),smoke=makeTexture(size,size,1),sparks=makeTexture(size,size,1);
  const ember:RGB=[.20,.018,.003],red:RGB=[.85,.075,.006],orange:RGB=[1.0,.31,.018],yellow:RGB=[1.0,.86,.26];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const macro=periodicField(u,v,seed+4,3)*.5+.5,tongue=ridgeField(u,v,seed+28,5,1.34),fine=periodicField(u*4,v*4,seed+71,3)*.5+.5;
    const f=C(S((macro*.58+tongue*.42-.30)/.62)*density);
    const hot=C(f*(.40+.60*fine));const c=M(ember,M(red,M(orange,yellow,hot),.72),f);setRGB(baseColor,i,c);
    rough.data[i]=L(.60,.18,f);height.data[i]=C(.26+f*.06+tongue*.025);ao.data[i]=L(.72,1,f);
    const j=i*3;emission.data[j]=C(f*(1.2+2.6*hot));emission.data[j+1]=C(f*(.18+1.6*hot));emission.data[j+2]=C(f*(.01+.28*hot));
    flameDensity.data[i]=f;flameHeightMask.data[i]=C(flameHeight*(.42+.58*macro));heatDistortion.data[i]=C(f*(.25+.75*fine));smoke.data[i]=C(f*(1-hot)*(.35+.65*macro));sparks.data[i]=C(S((fine-.78)/.22)*f*(.55+.45*wind));
  }
  return {material:finish(size,baseColor,rough,height,ao,5.6,emission),masks:{flameDensity,flameHeight:flameHeightMask,heatDistortion,smoke,sparks}};
}
