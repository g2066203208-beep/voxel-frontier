import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";
export type VfPainterlyBarkParams={seed?:number;normalStrength?:number;relief?:number;ridgeScale?:number};
export function bakeVfPainterlyBark(size:number,p:VfPainterlyBarkParams={}){
 const seed=Math.floor(p.seed??275903),relief=Math.max(.7,Math.min(1.8,p.relief??1.30)),normalStrength=Math.max(3,Math.min(20,p.normalStrength??11.0)),ridgeScale=Math.max(.7,Math.min(1.45,p.ridgeScale??1));
 const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);const crack:RGB=[.045,.014,.011],shadow:RGB=[.095,.034,.025],mid:RGB=[.285,.105,.050],light:RGB=[.555,.265,.110],ochre:RGB=[.720,.405,.170],cool:RGB=[.130,.060,.070];
 const knots=[[.22,.31,.10,.08],[.68,.62,.12,.095],[.47,.82,.09,.07],[.84,.20,.075,.06]];
 for(let py=0;py<size;py++){const v=1-(py+.5)/size;for(let px=0;px<size;px++){
  const u=(px+.5)/size,i=py*size+px,j=i*3;const warp=periodicField(u,v,seed+5,3)*.045;const phase=TAU*(6.4*ridgeScale*(u+warp)+periodicField(u,v,seed+7,2)*.035);const raw=.5+.5*Math.cos(phase);const plate=Math.pow(raw,.62);
  const breakField=periodicField(u,v,seed+27,3);const fissureMask=.35+.65*S(C(.52+breakField*.68));const fissure=Math.pow(1-raw,7.2)*fissureMask;const horizontal=Math.pow(1-Math.abs(Math.sin(TAU*(2.7*v+.22*u+periodicField(u,v,seed+39,2)*.055))),10)*S(C(.50+periodicField(u,v,seed+41,3)*.75));
  let knot=0;for(const q of knots){const dx=wrapDelta(u-q[0]),dy=wrapDelta(v-q[1]),r=Math.sqrt((dx/q[2])**2+(dy/q[3])**2);knot=Math.max(knot,G((r-.58)/.22)*(1-G(r/.30)));}
  const faceNoise=periodicField(u,v,seed+55,4);const h=C(.48+relief*((plate-.5)*.130+faceNoise*.020-fissure*.075-horizontal*.035+knot*.040));const face=S(C((plate-.12)/.88))*(1-horizontal*.55);
  let col=M(shadow,mid,face);col=M(col,light,face*.58);col=M(col,ochre,S(C(.48+faceNoise*.7))*.09*face);col=M(col,cool,C(-faceNoise)*.08);col=M(col,crack,C(fissure*.90+horizontal*.70+knot*.42));const dry=Math.pow(C(.5+.5*Math.sin(TAU*(1.9*v+.18*u)+hash(seed,91)*TAU)),7)*face;col=M(col,[.760,.420,.185],dry*.055);
  baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);height.data[i]=h;roughness.data[i]=C(.79+fissure*.11+horizontal*.07+knot*.04-face*.025);ao.data[i]=C(1-fissure*.38-horizontal*.23-knot*.16);
 }}return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
