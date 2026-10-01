import { heightToNormal } from "../../src/index.js";
import { C,L,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPaperWorldGrassTurfParams={
  seed?:number;
  normalStrength?:number;
  relief?:number;
  fiberStrength?:number;
  pulpStrength?:number;
};

type Tex=ReturnType<typeof makeTexture>;
type RNG=()=>number;

function rng(seed:number):RNG{let s=seed>>>0;return()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296;};}
function mod(x:number,m:number){return((x%m)+m)%m;}
function hex(s:string):RGB{const n=parseInt(s.slice(1),16);return[((n>>16)&255)/255,((n>>8)&255)/255,(n&255)/255];}
function mixRGB(tex:Tex,x:number,y:number,c:RGB,a:number){
  const xx=mod(x,tex.width),yy=mod(y,tex.height),j=(yy*tex.width+xx)*3;
  tex.data[j]=L(tex.data[j],c[0],a);tex.data[j+1]=L(tex.data[j+1],c[1],a);tex.data[j+2]=L(tex.data[j+2],c[2],a);
}
function addHeight(tex:Tex,x:number,y:number,d:number,a=1){
  const i=mod(y,tex.height)*tex.width+mod(x,tex.width);
  tex.data[i]=C(tex.data[i]+d*a);
}
function fillRGB(tex:Tex,c:RGB){for(let i=0;i<tex.width*tex.height;i++){const j=i*3;tex.data[j]=c[0];tex.data[j+1]=c[1];tex.data[j+2]=c[2];}}
function distSeg(px:number,py:number,x0:number,y0:number,x1:number,y1:number){
  const vx=x1-x0,vy=y1-y0,wx=px-x0,wy=py-y0,vv=vx*vx+vy*vy,t=vv>1e-8?Math.max(0,Math.min(1,(wx*vx+wy*vy)/vv)):0;
  return Math.hypot(px-(x0+vx*t),py-(y0+vy*t));
}
function drawSoftIrregularPulp(color:Tex,height:Tex,cx:number,cy:number,rx:number,ry:number,verts:number,phase:number,tone:RGB,alpha:number,heightDelta:number){
  const rad=Math.ceil(Math.max(rx,ry)*1.15);
  for(let y=Math.floor(cy-rad);y<=Math.ceil(cy+rad);y++)for(let x=Math.floor(cx-rad);x<=Math.ceil(cx+rad);x++){
    const dx=x+.5-cx,dy=y+.5-cy,a=Math.atan2(dy,dx)-phase;
    const ca=Math.cos(a),sa=Math.sin(a);
    const ex=dx*Math.cos(phase)+dy*Math.sin(phase),ey=-dx*Math.sin(phase)+dy*Math.cos(phase);
    const base=Math.sqrt((ex*ex)/(rx*rx)+(ey*ey)/(ry*ry));
    // Low-frequency irregular edge; no hard island outline.
    const wobble=1+.075*Math.sin(a*verts+phase*3)+.035*Math.sin(a*(verts-3)-phase*5);
    const q=base/Math.max(.78,wobble);
    if(q<1.16){
      const edge=C((1.16-q)/.30);
      const soft=edge*edge*(3-2*edge);
      mixRGB(color,x,y,tone,alpha*soft);
      addHeight(height,x,y,heightDelta,soft);
    }
  }
}
function drawFiber(color:Tex,normalHeight:Tex,x0:number,y0:number,x1:number,y1:number,width:number,tone:RGB,alpha:number,h:number){
  const r=Math.max(.5,width*.5),xmin=Math.floor(Math.min(x0,x1)-r-1),xmax=Math.ceil(Math.max(x0,x1)+r+1),ymin=Math.floor(Math.min(y0,y1)-r-1),ymax=Math.ceil(Math.max(y0,y1)+r+1);
  for(let y=ymin;y<=ymax;y++)for(let x=xmin;x<=xmax;x++){
    const d=distSeg(x+.5,y+.5,x0,y0,x1,y1);
    if(d<=r+.4){
      const a=alpha*C((r+.4-d)/.62);
      mixRGB(color,x,y,tone,a);
      addHeight(normalHeight,x,y,h,C((r+.25-d)/.50));
    }
  }
}

export function bakeVfPaperWorldGrassTurf(size:number,p:VfPaperWorldGrassTurfParams={}){
  const seed=Math.floor(Number(p.seed??128731)),r=rng(seed);
  const normalStrength=Math.max(1,Math.min(20,Number(p.normalStrength??10.5)));
  const relief=Math.max(.1,Math.min(1.6,Number(p.relief??.75)));
  const fiberStrength=C(Number(p.fiberStrength??1));
  const pulpStrength=C(Number(p.pulpStrength??1));
  const scale=size/256;

  const baseColor=makeTexture(size,size,3),height=makeTexture(size,size,1),normalHeight=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1),metallic=makeTexture(size,size,1),emission=makeTexture(size,size,3);

  // v12.14 terrain-top palette, slightly exposure-compensated for the PBR material-sphere rig.
  const base:RGB=[.405,.505,.255];
  const pulp:RGB[]=[
    [.470,.565,.315],
    [.330,.430,.235],
    [.445,.535,.295],
    [.355,.455,.245]
  ];
  fillRGB(baseColor,base);height.data.fill(.5);normalHeight.data.fill(.5);

  // 26 low-contrast handmade-paper pulp patches from v12.14's visible terrain texture.
  for(let i=0;i<26;i++){
    const cx=r()*size,cy=r()*size,rx=(18+r()*48)*scale,ry=(12+r()*34)*scale,verts=12+(r()*7|0);
    const alpha=(.035+r()*.055)*pulpStrength;
    const light=r()>.48;
    const dh=(light?1:-1)*(.0030+r()*.0028)*relief;
    drawSoftIrregularPulp(baseColor,height,cx,cy,rx,ry,verts,r()*Math.PI,pulp[(r()*pulp.length)|0],alpha,dh);
  }

  // Five huge, almost invisible pulp density clouds stop tiling from looking procedural.
  for(let i=0;i<5;i++){
    const cx=r()*size,cy=r()*size,rx=(45+r()*80)*scale,ry=(36+r()*68)*scale;
    const light=r()>.5;
    drawSoftIrregularPulp(baseColor,height,cx,cy,rx,ry,9+r()*4|0,r()*Math.PI,light?[.515,.555,.360]:[.285,.350,.205],light?.020:.017,(light?.0018:-.0015)*relief);
  }

  // 760 broken cellulose fibres: the strongest close-up cue in v12.14.
  for(let i=0;i<760;i++){
    const x=r()*size,y=r()*size,a=r()*Math.PI,len=(.7+r()*4.8)*scale,w=(.28+r()*.52)*scale,light=r()>.52;
    const tone=light?[.610,.650,.470] as RGB:[.250,.315,.205] as RGB;
    const alpha=(.055+r()*.085)*fiberStrength;
    const x1=x+Math.cos(a)*len,y1=y+Math.sin(a)*len;
    drawFiber(baseColor,normalHeight,x,y,x1,y1,w,tone,alpha,(light?.0060:-.0042)*fiberStrength);
  }

  // Sparse tiny pulp flecks.
  for(let i=0;i<145;i++){
    const q=Math.max(1,Math.round((.35+r()*1.25)*scale)),x=Math.floor(r()*size),y=Math.floor(r()*size),light=r()>.5;
    const tone=light?[.610,.635,.465] as RGB:[.255,.315,.205] as RGB;
    const alpha=(.035+r()*.075)*.78;
    for(let yy=0;yy<q;yy++)for(let xx=0;xx<q;xx++){
      mixRGB(baseColor,x+xx,y+yy,tone,alpha);
      addHeight(normalHeight,x+xx,y+yy,(light?.0024:-.0018));
    }
  }

  // Macro geometry remains soft; Normal receives the same macro plus stronger embedded fibre relief.
  for(let i=0;i<size*size;i++)normalHeight.data[i]=C(normalHeight.data[i]+(height.data[i]-.5)*1.25);
  const normal=heightToNormal(normalHeight,normalStrength,true);

  // Dry, absorbent handmade paper. Roughness variation follows pulp density, never random glitter.
  const H=height.data;
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const i=y*size+x,h=H[i],xm=mod(x-2,size),xp=mod(x+2,size),ym=mod(y-2,size),yp=mod(y+2,size);
    const around=(H[y*size+xm]+H[y*size+xp]+H[ym*size+x]+H[yp*size+x])*.25;
    const cavity=C((around-h)*6+(.497-h)*7);
    roughness.data[i]=C(.958-(h-.5)*.70);
    ao.data[i]=C(1-cavity*.16);
  }
  return{baseColor,metallic,roughness,normal,ao,height,emission};
}
