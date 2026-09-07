import { makeTexture, heightToNormal, type Material } from "../../src/index.js";
import { C, L, M, S, periodicField, ridgeField, type RGB } from "./vf-painterly-core.js";

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
  const soil:RGB=[.145,.095,.052],deep:RGB=[.095,.165,.044],mid:RGB=[.205,.355,.060],light:RGB=[.405,.515,.115];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const macro=periodicField(u,v,seed+11,3)*.5+.5,clump=periodicField(u*2,v*2,seed+67,4)*.5+.5,dir=ridgeField(u,v,seed+101,4,1.12);
    const grass=C(S((clump-(.36-.17*density))/.46));
    const c=M(M(soil,deep,grass),M(mid,light,C(.20+.66*macro)),grass*.84);
    setRGB(baseColor,i,c);rough.data[i]=L(.89,.73,grass);height.data[i]=C(.28+grass*(.075+.055*macro)+dir*.014);ao.data[i]=L(.70,.93,grass);
    bladeDensity.data[i]=C(grass*(.55+.45*macro)*density);bladeLength.data[i]=C(bladeHeight*(.46+.54*clump));bladeBend.data[i]=C(wind*(.30+.70*dir));
  }
  return {material:finish(size,baseColor,rough,height,ao,7.0),masks:{bladeDensity,bladeLength,bladeBend}};
}

export function bakeVf3DMoss(size:number,p:Vf3DShowcaseParams={}):Vf3DShowcaseBundle{
  const seed=Math.floor(Number(p.seed??55109)),density=C(Number(p.density??.76)),mossHeight=C(Number(p.height??.62));
  const baseColor=makeTexture(size,size,3),rough=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const mossDensity=makeTexture(size,size,1),mossHeightMask=makeTexture(size,size,1),tuftVariation=makeTexture(size,size,1);
  const rock:RGB=[.16,.18,.16],dark:RGB=[.10,.22,.045],mid:RGB=[.25,.40,.070],light:RGB=[.48,.56,.13];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const rockField=periodicField(u,v,seed+3,4)*.5+.5,patch=(periodicField(u,v,seed+41,3)*.5+.5)*.68+(periodicField(u*2,v*2,seed+43,3)*.5+.5)*.32,fuzz=periodicField(u*6,v*6,seed+93,3)*.5+.5;
    const moss=C(S((patch-(.43-.21*density))/.37));
    const mc=M(dark,M(mid,light,fuzz),.50+.30*rockField),c=M(rock,mc,moss*.92);
    setRGB(baseColor,i,c);rough.data[i]=L(.84,.97,moss);height.data[i]=C(.30+rockField*.055+moss*(.040+.032*fuzz));ao.data[i]=L(.70,.91,moss);
    mossDensity.data[i]=C(moss*density);mossHeightMask.data[i]=C(mossHeight*(.30+.70*fuzz));tuftVariation.data[i]=fuzz;
  }
  return {material:finish(size,baseColor,rough,height,ao,7.8),masks:{mossDensity,mossHeight:mossHeightMask,tuftVariation}};
}

export function bakeVf3DFur(size:number,p:Vf3DShowcaseParams={}):Vf3DShowcaseBundle{
  const seed=Math.floor(Number(p.seed??91007)),density=C(Number(p.density??.90)),furHeight=C(Number(p.height??.82)),wind=C(Number(p.wind??.30));
  const baseColor=makeTexture(size,size,3),rough=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const strandDensity=makeTexture(size,size,1),strandLength=makeTexture(size,size,1),strandBend=makeTexture(size,size,1),strandVariation=makeTexture(size,size,1);
  const dark:RGB=[.17,.085,.035],mid:RGB=[.48,.27,.11],light:RGB=[.78,.59,.30],cream:RGB=[.91,.80,.58];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const broad=periodicField(u,v,seed+15,3)*.5+.5,fine=periodicField(u*3,v*3,seed+72,4)*.5+.5,flow=ridgeField(u,v,seed+110,5,.36);
    const c=M(M(dark,mid,broad),M(light,cream,fine),.39+.30*flow);setRGB(baseColor,i,c);
    rough.data[i]=.85;height.data[i]=C(.34+.020*broad+.014*flow);ao.data[i]=.89;
    strandDensity.data[i]=C(density*(.70+.30*fine));strandLength.data[i]=C(furHeight*(.56+.44*broad));strandBend.data[i]=C(wind*(.28+.72*flow));strandVariation.data[i]=fine;
  }
  return {material:finish(size,baseColor,rough,height,ao,4.4),masks:{strandDensity,strandLength,strandBend,strandVariation}};
}

export function bakeVf3DFire(size:number,p:Vf3DShowcaseParams={}):Vf3DShowcaseBundle{
  const seed=Math.floor(Number(p.seed??44021)),density=C(Number(p.density??.88)),flameHeight=C(Number(p.height??.90)),wind=C(Number(p.wind??.34));
  const baseColor=makeTexture(size,size,3),rough=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1),emission=makeTexture(size,size,3);
  const flameDensity=makeTexture(size,size,1),flameHeightMask=makeTexture(size,size,1),heatDistortion=makeTexture(size,size,1),smoke=makeTexture(size,size,1),sparks=makeTexture(size,size,1);
  const ember:RGB=[.13,.012,.002],red:RGB=[.60,.035,.003],orange:RGB=[.98,.20,.008],yellow:RGB=[1.0,.69,.14];
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size,v=1-(y+.5)/size,i=y*size+x;
    const macro=periodicField(u,v,seed+4,3)*.5+.5,tongue=ridgeField(u,v,seed+28,4,1.34),fine=periodicField(u*4,v*4,seed+71,3)*.5+.5;
    const f=C(S((macro*.62+tongue*.38-.33)/.58)*density),hot=C(f*(.38+.62*fine));
    setRGB(baseColor,i,M(ember,M(red,M(orange,yellow,hot),.70),f));rough.data[i]=L(.62,.16,f);height.data[i]=C(.26+f*.05+tongue*.018);ao.data[i]=L(.70,1,f);
    const j=i*3;emission.data[j]=C(f*(1.0+2.9*hot));emission.data[j+1]=C(f*(.12+1.7*hot));emission.data[j+2]=C(f*(.005+.22*hot));
    flameDensity.data[i]=f;flameHeightMask.data[i]=C(flameHeight*(.44+.56*macro));heatDistortion.data[i]=C(f*(.22+.78*fine));smoke.data[i]=C(f*(1-hot)*(.28+.72*macro));sparks.data[i]=C(S((fine-.82)/.18)*f*(.45+.55*wind));
  }
  return {material:finish(size,baseColor,rough,height,ao,5.2,emission),masks:{flameDensity,flameHeight:flameHeightMask,heatDistortion,smoke,sparks}};
}
