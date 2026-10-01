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
  const grid=28;
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
    const halfLen=.15+hash(seed,ix,iy,5)*.30;
    const width=.030+hash(seed,ix,iy,6)*.038;
    const taper=S((halfLen+.075-Math.abs(along))/.11);
    const cross=Math.exp(-Math.pow(across/width,2));
    const m=taper*cross;
    if(m>best){best=m;tone=hash(seed,ix,iy,7);}
  }
  return{mask:C(best),tone};
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
  const normalStrength=Math.max(2,Math.min(18,p.normalStrength??8.4));
  const pulpRelief=Math.max(.45,Math.min(1.8,p.pulpRelief??1.0));
  const fiberDensity=C(p.fiberDensity??.70);
  const fiberLift=C(p.fiberLift??.58);
  const fleckAmount=C(p.fleckAmount??.72);
  const pressWrinkle=C(p.pressWrinkle??.16);

  const baseColor=makeTexture(size,size,3);
  const roughness=makeTexture(size,size,1);
  const height=makeTexture(size,size,1);
  const ao=makeTexture(size,size,1);

  // Muted olive handmade-paper palette sampled by eye from PaperWorld v12.14.
  const deep:RGB=[.205,.270,.125];
  const cool:RGB=[.285,.365,.170];
  const mid:RGB=[.365,.445,.205];
  const light:RGB=[.500,.555,.270];
  const warm:RGB=[.455,.455,.205];
  const paleFiber:RGB=[.625,.605,.345];
  const darkFiber:RGB=[.215,.285,.135];

  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size,i=y*size+x,j=i*3;

      // Three paper-pulp scales: broad dyed cloud, meso felt mass, fine compressed grain.
      const macro=periodicField(u,v,seed+11,3)*.5+.5;
      const meso=periodicField(u*2,v*2,seed+37,4)*.5+.5;
      const fine=periodicField(u*8,v*8,seed+73,3)*.5+.5;
      const cloud=C(.56*macro+.31*meso+.13*fine);

      // Very weak press wrinkles: structural accent only, never the dominant read.
      const wr1=ridgeField(u,v,seed+101,2,0.22);
      const wr2=ridgeField(u,v,seed+139,3,1.68);
      const pressed=(1-Math.abs(wr1*2-1))*.58+(1-Math.abs(wr2*2-1))*.42;

      const fib=fiberField(u,v,seed+211,.30+.55*fiberDensity);
      const fleck=fleckField(u,v,seed+331,fleckAmount);

      let col=M(deep,mid,S((cloud-.18)/.66));
      col=M(col,light,C(Math.max(0,macro-.54)*.43+Math.max(0,meso-.60)*.19));
      col=M(col,cool,C(Math.max(0,.47-macro)*.20));
      col=M(col,warm,C(Math.max(0,meso-.55)*.105+pressed*.020));
      const fiberTint=fib.tone>.58?paleFiber:darkFiber;
      col=M(col,fiberTint,fib.mask*(fib.tone>.58?.18:.085));
      col=M(col,paleFiber,fleck*.14);

      // Height is mostly soft pulp thickness. Fibres are micro relief; wrinkles remain shallow.
      let h=.500;
      h+=(macro-.5)*.026*pulpRelief;
      h+=(meso-.5)*.014*pulpRelief;
      h+=(fine-.5)*.0045*pulpRelief;
      h+=(pressed-.5)*.0038*pressWrinkle;
      h+=fib.mask*.0032*fiberLift;
      h+=(fleck-.25)*.0015;
      h=C(h);

      baseColor.data[j]=C(col[0]);
      baseColor.data[j+1]=C(col[1]);
      baseColor.data[j+2]=C(col[2]);
      height.data[i]=h;

      // Dry absorbent paper: consistently rough, with fibres slightly rougher.
      roughness.data[i]=C(.945+(fine-.5)*.025+fib.mask*.022+fleck*.010-(macro-.5)*.010);
      const lowPocket=C((.505-h)*22);
      ao.data[i]=C(.992-lowPocket*.055-fleck*.012);
    }
  }

  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
