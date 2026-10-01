import { C,L,M,S,hash,wrapDelta,periodicField,ridgeField,finalize,makeTexture,type RGB } from "./vf-painterly-core.js";

export type VfPaperWorldGrassTurfParams={
  seed?:number;
  normalStrength?:number;
  pulpRelief?:number;
  fiberDensity?:number;
  fiberLift?:number;
  fleckAmount?:number;
  pressWrinkle?:number;
};

type FiberSample={mask:number;tone:number};

const MOD=(x:number,m:number)=>((x%m)+m)%m;

function fiberField(u:number,v:number,seed:number,density:number):FiberSample{
  const grid=36;
  const gx=Math.floor(u*grid),gy=Math.floor(v*grid);
  let best=0,tone=.5;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=MOD(gx+ox,grid),iy=MOD(gy+oy,grid);
    const alive=hash(seed,ix,iy,1);
    if(alive>density)continue;
    const cx=(ix+.5+(hash(seed,ix,iy,2)-.5)*.78)/grid;
    const cy=(iy+.5+(hash(seed,ix,iy,3)-.5)*.78)/grid;
    const dx=wrapDelta(u-cx)*grid,dy=wrapDelta(v-cy)*grid;
    const angle=hash(seed,ix,iy,4)*Math.PI*2;
    const ca=Math.cos(angle),sa=Math.sin(angle);
    const along=dx*ca+dy*sa,across=-dx*sa+dy*ca;
    const halfLen=.10+hash(seed,ix,iy,5)*.22;
    const width=.018+hash(seed,ix,iy,6)*.024;
    const taper=S((halfLen+.055-Math.abs(along))/.080);
    const cross=Math.exp(-Math.pow(across/width,2));
    const m=taper*cross;
    if(m>best){best=m;tone=hash(seed,ix,iy,7);}
  }
  return{mask:C(best),tone};
}

function pulpPatchField(u:number,v:number,seed:number){
  const grid=6;
  const gx=Math.floor(u*grid),gy=Math.floor(v*grid);
  let best=0,second=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=MOD(gx+ox,grid),iy=MOD(gy+oy,grid);
    const cx=(ix+.5+(hash(seed,ix,iy,1)-.5)*.70)/grid;
    const cy=(iy+.5+(hash(seed,ix,iy,2)-.5)*.70)/grid;
    const dx=wrapDelta(u-cx)*grid,dy=wrapDelta(v-cy)*grid;
    const angle=hash(seed,ix,iy,3)*Math.PI*2,ca=Math.cos(angle),sa=Math.sin(angle);
    const x=dx*ca+dy*sa,y=-dx*sa+dy*ca;
    const rx=.40+hash(seed,ix,iy,4)*.34,ry=.32+hash(seed,ix,iy,5)*.30;
    const q=Math.pow(Math.pow(Math.abs(x)/rx,3.2)+Math.pow(Math.abs(y)/ry,3.2),1/3.2);
    const m=S((1-q)/.46);
    if(m>best){second=best;best=m}else if(m>second)second=m;
  }
  return C(best*.78+second*.22);
}

function fleckField(u:number,v:number,seed:number,amount:number){
  const grid=19;
  const gx=Math.floor(u*grid),gy=Math.floor(v*grid);
  let best=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=MOD(gx+ox,grid),iy=MOD(gy+oy,grid);
    if(hash(seed,ix,iy,1)>.18*amount)continue;
    const cx=(ix+.5+(hash(seed,ix,iy,2)-.5)*.82)/grid;
    const cy=(iy+.5+(hash(seed,ix,iy,3)-.5)*.82)/grid;
    const dx=wrapDelta(u-cx)*grid,dy=wrapDelta(v-cy)*grid;
    const angle=hash(seed,ix,iy,4)*Math.PI*2,ca=Math.cos(angle),sa=Math.sin(angle);
    const x=dx*ca+dy*sa,y=-dx*sa+dy*ca;
    const rx=.050+hash(seed,ix,iy,5)*.055,ry=.025+hash(seed,ix,iy,6)*.035;
    const q=Math.sqrt((x*x)/(rx*rx)+(y*y)/(ry*ry));
    best=Math.max(best,S((1-q)/.55));
  }
  return C(best);
}

export function bakeVfPaperWorldGrassTurf(size:number,p:VfPaperWorldGrassTurfParams={}){
  const seed=Math.floor(p.seed??314159);
  const normalStrength=Math.max(2,Math.min(18,p.normalStrength??9.2));
  const pulpRelief=Math.max(.45,Math.min(1.8,p.pulpRelief??1.0));
  const fiberDensity=C(p.fiberDensity??.70);
  const fiberLift=C(p.fiberLift??.58);
  const fleckAmount=C(p.fleckAmount??.72);
  const pressWrinkle=C(p.pressWrinkle??.08);

  const baseColor=makeTexture(size,size,3);
  const roughness=makeTexture(size,size,1);
  const height=makeTexture(size,size,1);
  const ao=makeTexture(size,size,1);

  // Muted olive handmade-paper palette sampled by eye from PaperWorld v12.14.
  const deep:RGB=[.175,.215,.105];
  const cool:RGB=[.245,.285,.145];
  const mid:RGB=[.305,.345,.165];
  const light:RGB=[.405,.430,.215];
  const warm:RGB=[.365,.345,.165];
  const paleFiber:RGB=[.505,.485,.285];
  const darkFiber:RGB=[.175,.225,.115];

  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size,i=y*size+x,j=i*3;

      // Three paper-pulp scales: broad dyed cloud, meso felt mass, fine compressed grain.
      const macroA=periodicField(u,v,seed+11,3)*.5+.5;
      const macroB=periodicField(v,u,seed+23,3)*.5+.5;
      const macro=C(macroA*.62+macroB*.38);
      const mesoA=periodicField(u*3,v*3,seed+37,4)*.5+.5;
      const mesoB=periodicField(v*4,u*4,seed+51,3)*.5+.5;
      const meso=C(mesoA*.58+mesoB*.42);
      const fine=periodicField(u*11,v*11,seed+73,3)*.5+.5;
      const micro=periodicField(u*32,v*32,seed+89,3)*.5+.5;
      const pulpPatch=pulpPatchField(u,v,seed+157);
      const cloud=C(.36*macro+.24*meso+.30*pulpPatch+.10*fine);

      // Very weak press wrinkles: structural accent only, never the dominant read.
      const wr1=ridgeField(u,v,seed+101,2,0.22);
      const wr2=ridgeField(u,v,seed+139,3,1.68);
      const pressed=(1-Math.abs(wr1*2-1))*.58+(1-Math.abs(wr2*2-1))*.42;

      const fib=fiberField(u,v,seed+211,.48+.48*fiberDensity);
      const fleck=fleckField(u,v,seed+331,fleckAmount);

      let col=M(deep,mid,S((cloud-.18)/.66));
      col=M(col,light,C(Math.max(0,pulpPatch-.50)*.20+Math.max(0,macro-.58)*.16));
      col=M(col,cool,C(Math.max(0,.46-macro)*.15));
      col=M(col,warm,C(Math.max(0,meso-.57)*.065+pressed*.010));
      const fiberTint=fib.tone>.58?paleFiber:darkFiber;
      col=M(col,fiberTint,fib.mask*(fib.tone>.58?.085:.050));
      col=M(col,paleFiber,fleck*.095);

      // Height is mostly soft pulp thickness. Fibres are micro relief; wrinkles remain shallow.
      let h=.500;
      h+=(macro-.5)*.016*pulpRelief;
      h+=(meso-.5)*.010*pulpRelief;
      h+=(pulpPatch-.5)*.011*pulpRelief;
      h+=(fine-.5)*.0038*pulpRelief;
      h+=(micro-.5)*.0022*pulpRelief;
      h+=(pressed-.5)*.0022*pressWrinkle;
      h+=fib.mask*.0017*fiberLift;
      h+=(fleck-.25)*.0010;
      h=C(h);

      baseColor.data[j]=C(col[0]);
      baseColor.data[j+1]=C(col[1]);
      baseColor.data[j+2]=C(col[2]);
      height.data[i]=h;

      // Dry absorbent paper: consistently rough, with fibres slightly rougher.
      roughness.data[i]=C(.958+(micro-.5)*.026+(fine-.5)*.012+fib.mask*.014+fleck*.008-(pulpPatch-.5)*.007);
      const lowPocket=C((.505-h)*22);
      ao.data[i]=C(.992-lowPocket*.055-fleck*.012);
    }
  }

  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
