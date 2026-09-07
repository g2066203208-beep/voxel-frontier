import { heightToNormal, type Material } from "../../src/index.js";
import { C, M, S, TAU, hash, periodicField, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyWaterMode = "calm" | "windy" | "foam" | "shallow";
export type VfPainterlyWaterParams = {
  seed?: number;
  normalStrength?: number;
  relief?: number;
  waveScale?: number;
  roughness?: number;
  mode?: VfPainterlyWaterMode;
  foam?: number;
  transparency?: number;
  refraction?: number;
  glint?: number;
};

type Tex = ReturnType<typeof makeTexture>;
export type VfPainterlyWaterBakeResult = {
  material: Material;
  masks: Readonly<Record<string, Tex>>;
};

type ModeCfg = {
  macroAmp: number;
  midAmp: number;
  rippleAmp: number;
  foam: number;
  transparency: number;
  refraction: number;
  glint: number;
  roughness: number;
  crestThreshold: number;
  depthTint: number;
};

const MODE: Record<VfPainterlyWaterMode, ModeCfg> = {
  calm:    { macroAmp: .62, midAmp: .23, rippleAmp: .055, foam: .06, transparency: .90, refraction: .48, glint: .62, roughness: .065, crestThreshold: .84, depthTint: .34 },
  windy:   { macroAmp: .78, midAmp: .36, rippleAmp: .095, foam: .32, transparency: .80, refraction: .72, glint: .88, roughness: .080, crestThreshold: .73, depthTint: .48 },
  foam:    { macroAmp: .86, midAmp: .46, rippleAmp: .125, foam: .92, transparency: .68, refraction: .82, glint: 1.00, roughness: .095, crestThreshold: .62, depthTint: .56 },
  shallow: { macroAmp: .66, midAmp: .27, rippleAmp: .070, foam: .17, transparency: .96, refraction: 1.00, glint: .74, roughness: .058, crestThreshold: .80, depthTint: .22 },
};

function wavePhase(u:number,v:number,fx:number,fy:number,phase:number,warp:number){
  return TAU*(fx*u+fy*v+warp)+phase;
}

export function bakeVfPainterlyWater(size:number,p:VfPainterlyWaterParams={}):VfPainterlyWaterBakeResult{
  const seed=Math.floor(p.seed??553819);
  const mode:VfPainterlyWaterMode=p.mode??"windy";
  const cfg=MODE[mode];
  const relief=Math.max(.30,Math.min(1.55,p.relief??1.0));
  const normalStrength=Math.max(2,Math.min(18,p.normalStrength??8.2));
  const scale=Math.max(.55,Math.min(1.8,p.waveScale??1));
  const baseRough=Math.max(.04,Math.min(.22,p.roughness??cfg.roughness));
  const foamAmount=C(p.foam??cfg.foam);
  const transparency=C(p.transparency??cfg.transparency);
  const refractionAmount=C(p.refraction??cfg.refraction);
  const glintAmount=C(p.glint??cfg.glint);

  const baseColor=makeTexture(size,size,3);
  const roughness=makeTexture(size,size,1);
  const height=makeTexture(size,size,1);
  const ao=makeTexture(size,size,1);
  const metallic=makeTexture(size,size,1);
  const emission=makeTexture(size,size,3);
  const foamMask=makeTexture(size,size,1);
  const transmissionMask=makeTexture(size,size,1);
  const refractionMask=makeTexture(size,size,1);
  const glintMask=makeTexture(size,size,1);
  const crestSignal=new Float32Array(size*size);
  const depthSignal=new Float32Array(size*size);

  const deep:RGB=[.010,.055,.095];
  const mid:RGB=[.015,.180,.245];
  const cyan:RGB=[.045,.360,.430];
  const shallow:RGB=[.115,.520,.555];
  const foamCol:RGB=[.835,.940,.935];
  const p1=hash(seed,1)*TAU,p2=hash(seed,2)*TAU,p3=hash(seed,3)*TAU,p4=hash(seed,4)*TAU;

  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size,i=y*size+x;
      const warp=periodicField(u,v,seed+41,3)*.035;
      const detail=C((scale-.55)/1.25);
      const a=wavePhase(u,v,1,1,p1,warp);
      const b=wavePhase(u,v,-1,2,p2,-warp*.6);
      const c=wavePhase(u,v,3,-1,p3,warp*.35);
      const d=wavePhase(u,v,6,3,p4,-warp*.20);
      const wa=Math.sin(a)+.22*Math.sin(2*a-.35);
      const wb=Math.sin(b)+.15*Math.sin(2*b+.60);
      const wc=Math.sin(c);
      const wd=Math.sin(d);
      const broad=periodicField(u,v,seed+83,4);
      const macro=wa*.62+wb*.38;
      const midWave=wc*.68+broad*.32;
      const ripple=wd*.72+periodicField(u,v,seed+111,3)*.28;
      const crestA=Math.pow(C(.5+.5*Math.sin(a)),5.0);
      const crestB=Math.pow(C(.5+.5*Math.sin(b)),6.0);
      const crestRidge=C(Math.max(crestA,crestB*.82)*(.72+.28*C(.5+.5*wc)));
      const midWeight=.72+.58*detail;
      const rippleWeight=.45+.95*detail;
      const combined=macro*cfg.macroAmp+midWave*cfg.midAmp*midWeight+ripple*cfg.rippleAmp*rippleWeight+(crestA+crestB*.55-.22)*.13;
      const h=C(.50+relief*combined*.135);
      height.data[i]=h;
      crestSignal[i]=crestRidge;
      depthSignal[i]=C(.50+.22*broad-.12*macro+.08*midWave);
    }
  }

  const at=(x:number,y:number)=>height.data[((y%size+size)%size)*size+((x%size+size)%size)];
  for(let y=0;y<size;y++){
    const v=1-(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size,i=y*size+x,j=i*3;
      const dx=(at(x+1,y)-at(x-1,y))*size*.50;
      const dy=(at(x,y+1)-at(x,y-1))*size*.50;
      const slope=C(Math.hypot(dx,dy)/9.0);
      const crest=crestSignal[i];
      const broken=C(.62+.38*periodicField(u,v,seed+151,3));
      const foamCore=S((crest-cfg.crestThreshold)/Math.max(.08,1-cfg.crestThreshold));
      const foam=C(foamAmount*Math.pow(foamCore,1.35)*(.30+.70*slope)*broken);
      const transmission=C(transparency*(1-foam)*(.78+.22*(1-slope)));
      const refraction=C(refractionAmount*transmission*(.34+.66*slope));
      const glint=C(glintAmount*(1-foam*.58)*S((crest-.50)/.42)*(.18+.82*slope));
      const depth=depthSignal[i];

      let col=M(deep,mid,C(.34+depth*cfg.depthTint));
      col=M(col,cyan,C(.28+(1-depth)*.34));
      if(mode==="shallow") col=M(col,shallow,C(.25+(1-depth)*.40));
      col=M(col,foamCol,foam*.92);
      baseColor.data[j]=C(col[0]); baseColor.data[j+1]=C(col[1]); baseColor.data[j+2]=C(col[2]);
      roughness.data[i]=C(baseRough+slope*.025+Math.abs(periodicField(u,v,seed+177,2))*.012+foam*.67);
      ao.data[i]=1;
      metallic.data[i]=0;
      foamMask.data[i]=foam;
      transmissionMask.data[i]=transmission;
      refractionMask.data[i]=refraction;
      glintMask.data[i]=glint;
      const e=glint*.035+foam*.010;
      emission.data[j]=e*.70; emission.data[j+1]=e*.94; emission.data[j+2]=e;
    }
  }

  const normal=heightToNormal(height,normalStrength,true);
  const material:Material={baseColor,metallic,roughness,normal,ao,height,emission};
  return {material,masks:{foam:foamMask,transmission:transmissionMask,refraction:refractionMask,glint:glintMask}};
}
