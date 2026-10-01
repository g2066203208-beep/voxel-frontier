import { heightToNormal } from "../../src/index.js";
import { C, L, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPaperWorldGrassTurfParams={
  seed?:number;
  normalStrength?:number;
  relief?:number;
  fibreStrength?:number;
  patchStrength?:number;
};

type Tex=ReturnType<typeof makeTexture>;
type RNG=()=>number;

function rng(seed:number):RNG{
  let s=seed>>>0;
  return()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296;};
}
function mod(x:number,m:number){return ((x%m)+m)%m;}
function hex(s:string):RGB{
  const n=parseInt(s.slice(1),16);
  return[((n>>16)&255)/255,((n>>8)&255)/255,(n&255)/255];
}
function blendRGB(tex:Tex,x:number,y:number,c:RGB,a:number){
  const xx=mod(x,tex.width),yy=mod(y,tex.height),j=(yy*tex.width+xx)*3;
  tex.data[j]=L(tex.data[j],c[0],a);
  tex.data[j+1]=L(tex.data[j+1],c[1],a);
  tex.data[j+2]=L(tex.data[j+2],c[2],a);
}
function setHeight(tex:Tex,x:number,y:number,h:number){
  tex.data[mod(y,tex.height)*tex.width+mod(x,tex.width)]=C(h);
}
function fillBase(tex:Tex,c:RGB){
  for(let i=0;i<tex.width*tex.height;i++){const j=i*3;tex.data[j]=c[0];tex.data[j+1]=c[1];tex.data[j+2]=c[2];}
}
function fillScalar(tex:Tex,v:number){tex.data.fill(v);}

function drawEllipseColor(tex:Tex,cx:number,cy:number,rx:number,ry:number,angle:number,color:RGB,alpha:number){
  const ca=Math.cos(angle),sa=Math.sin(angle),rad=Math.ceil(Math.max(rx,ry));
  for(let yy=Math.floor(cy-rad);yy<=Math.ceil(cy+rad);yy++)for(let xx=Math.floor(cx-rad);xx<=Math.ceil(cx+rad);xx++){
    const dx=xx+.5-cx,dy=yy+.5-cy;
    const qx=dx*ca+dy*sa,qy=-dx*sa+dy*ca;
    if((qx*qx)/(rx*rx)+(qy*qy)/(ry*ry)<=1)blendRGB(tex,xx,yy,color,alpha);
  }
}
function drawRectColor(tex:Tex,x:number,y:number,w:number,h:number,color:RGB,alpha:number){
  for(let yy=Math.floor(y);yy<Math.ceil(y+h);yy++)for(let xx=Math.floor(x);xx<Math.ceil(x+w);xx++)blendRGB(tex,xx,yy,color,alpha);
}
function drawRectHeight(tex:Tex,x:number,y:number,w:number,h:number,value:number){
  for(let yy=Math.floor(y);yy<Math.ceil(y+h);yy++)for(let xx=Math.floor(x);xx<Math.ceil(x+w);xx++)setHeight(tex,xx,yy,value);
}
function distToSegment(px:number,py:number,x0:number,y0:number,x1:number,y1:number){
  const vx=x1-x0,vy=y1-y0,wx=px-x0,wy=py-y0;
  const vv=vx*vx+vy*vy;
  const t=vv>1e-8?Math.max(0,Math.min(1,(wx*vx+wy*vy)/vv)):0;
  return Math.hypot(px-(x0+vx*t),py-(y0+vy*t));
}
function drawLineColor(tex:Tex,x0:number,y0:number,x1:number,y1:number,width:number,color:RGB,alpha:number){
  const r=Math.max(.5,width*.5),xmin=Math.floor(Math.min(x0,x1)-r-1),xmax=Math.ceil(Math.max(x0,x1)+r+1),ymin=Math.floor(Math.min(y0,y1)-r-1),ymax=Math.ceil(Math.max(y0,y1)+r+1);
  for(let y=ymin;y<=ymax;y++)for(let x=xmin;x<=xmax;x++){
    const d=distToSegment(x+.5,y+.5,x0,y0,x1,y1);
    if(d<=r+.45){const aa=alpha*C((r+.45-d)/.65);blendRGB(tex,x,y,color,aa);}
  }
}
function drawLineHeight(tex:Tex,x0:number,y0:number,x1:number,y1:number,width:number,value:number){
  const r=Math.max(.5,width*.5),xmin=Math.floor(Math.min(x0,x1)-r-1),xmax=Math.ceil(Math.max(x0,x1)+r+1),ymin=Math.floor(Math.min(y0,y1)-r-1),ymax=Math.ceil(Math.max(y0,y1)+r+1);
  for(let y=ymin;y<=ymax;y++)for(let x=xmin;x<=xmax;x++){
    const d=distToSegment(x+.5,y+.5,x0,y0,x1,y1);
    if(d<=r+.25){
      const i=mod(y,tex.height)*tex.width+mod(x,tex.width);
      const a=C((r+.25-d)/.55);
      tex.data[i]=L(tex.data[i],value,a);
    }
  }
}

export function bakeVfPaperWorldGrassTurf(size:number,p:VfPaperWorldGrassTurfParams={}){
  const seed=Math.floor(Number(p.seed??731));
  const normalStrength=Math.max(1,Math.min(20,Number(p.normalStrength??8.0)));
  const relief=Math.max(.15,Math.min(1.8,Number(p.relief??.68)));
  const fibreStrength=C(Number(p.fibreStrength??1.0));
  const patchStrength=C(Number(p.patchStrength??1.0));
  const r=rng(seed);

  const color=makeTexture(size,size,3),height=makeTexture(size,size,1),roughness=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const metallic=makeTexture(size,size,1),emission=makeTexture(size,size,3);
  const scale=size/256;

  // Exact v12.14 green paper family, now baked as real PBR fields.
  const base=hex("#a9c974");
  const patches=[hex("#bfd987"),hex("#91b75f"),hex("#b5d379"),hex("#9ec16a")];
  fillBase(color,base);fillScalar(height,.5);

  // v12.14 broad low-frequency pulp clouds.
  for(let i=0;i<34;i++){
    const x=r()*size,y=r()*size,rx=(18+r()*54)*scale,ry=(12+r()*38)*scale;
    const alpha=(.055+r()*.075)*patchStrength;
    drawEllipseColor(color,x,y,rx,ry,r()*Math.PI,patches[(r()*patches.length)|0],alpha);
  }

  // v12.14 pressed-paper blocks. The same masks drive albedo + Height.
  for(let i=0;i<30;i++){
    const w=Math.round((11+r()*34)*scale);
    const h=Math.round(w*(.72+r()*.56));
    const x=Math.floor(r()*size-w*.35),y=Math.floor(r()*size-h*.35);
    const raised=r()>.48;
    const alpha=(.060+r()*.075)*patchStrength;
    const blockColor=raised?[224/255,239/255,167/255] as RGB:[64/255,92/255,48/255] as RGB;
    drawRectColor(color,x,y,w,h,blockColor,alpha);
    const outer=(raised?(168+(r()*14|0)):(88-(r()*10|0)))/255;
    const inner=(raised?(218+(r()*24|0)):(40-(r()*18|0)))/255;
    const currentOuter=.5+(outer-.5)*relief;
    const currentInner=.5+(inner-.5)*relief;
    drawRectHeight(height,x,y,w,h,currentOuter);
    const inset=Math.max(1,Math.round(Math.min(w,h)*.12));
    drawRectHeight(height,x+inset,y+inset,Math.max(2,w-inset*2),Math.max(2,h-inset*2),currentInner);
  }

  // v12.14 visible cellulose fibres: short, broken, randomly oriented.
  for(let i=0;i<620;i++){
    const x=r()*size,y=r()*size,a=r()*Math.PI,len=(1+r()*7)*scale,w=(.28+r()*.52)*scale;
    const light=r()>.48;
    const fibreColor=light?[245/255,250/255,215/255] as RGB:[61/255,42/255,31/255] as RGB;
    const alpha=(light?.20:.13)*fibreStrength;
    const x1=x+Math.cos(a)*len,y1=y+Math.sin(a)*len;
    drawLineColor(color,x,y,x1,y1,w,fibreColor,alpha);
    const hv=(light?150+(r()*18|0):105+(r()*18|0))/255;
    const target=.5+(hv-.5)*(.42+.58*fibreStrength)*relief;
    drawLineHeight(height,x,y,x1,y1,w,target);
  }

  // Tiny non-uniform pulp flecks from the target-era terrain stock.
  for(let i=0;i<145;i++){
    const q=(.35+r()*1.25)*scale,x=r()*size,y=r()*size;
    const light=r()>.5;
    const fc=light?hex("#edf1d6"):hex("#536946");
    const alpha=(.035+r()*.075)*.72;
    drawRectColor(color,x,y,q,q,fc,alpha);
  }

  // A few almost invisible large pulp sheets break mathematical repetition.
  for(let i=0;i<5;i++){
    const cx=r()*size,cy=r()*size,rx=(45+r()*80)*scale,ry=(36+r()*68)*scale;
    const light=r()>.5;
    drawEllipseColor(color,cx,cy,rx,ry,0,light?hex("#dae6b8"):hex("#576f46"),light?.030:.026);
  }

  // PBR channels derived from the SAME height field, preserving the v12.14 structure.
  const normal=heightToNormal(height,normalStrength,true);
  const H=height.data;
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const i=y*size+x,h=H[i];
    const xm=mod(x-2,size),xp=mod(x+2,size),ym=mod(y-2,size),yp=mod(y+2,size);
    const around=(H[y*size+xm]+H[y*size+xp]+H[ym*size+x]+H[yp*size+x])*.25;
    const cavity=C((around-h)*2.2+(.48-h)*1.45);
    roughness.data[i]=C(.942-(h-.5)*.085);
    ao.data[i]=C(1-cavity*.28);
  }

  return{baseColor:color,metallic,roughness,normal,ao,height,emission};
}
