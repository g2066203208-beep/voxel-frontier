import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { exportPBR, heightToNormal, textureToPNG, validateMaterial, type Material } from "../src/index.js";
import { bakeVfLayeredSandstonePainted, type VfLayeredSandstoneParams } from "./vf-recipes/vf-layered-sandstone-painted.js";
import { bakeVfPainterlyDirt, type VfPainterlyDirtParams } from "./vf-recipes/vf-painterly-dirt.js";
import { bakeVfPainterlyBark, type VfPainterlyBarkParams } from "./vf-recipes/vf-painterly-bark.js";
import { bakeVfPainterlyLeavesBundle, type VfPainterlyLeavesParams } from "./vf-recipes/vf-painterly-leaves.js";
import { bakeVfPainterlySnow, type VfPainterlySnowParams } from "./vf-recipes/vf-painterly-snow.js";
import { bakeVfPainterlyWater, type VfPainterlyWaterParams } from "./vf-recipes/vf-painterly-water.js";
import { bakeVfPainterlyStoneWall, type VfPainterlyStoneWallParams } from "./vf-recipes/vf-painterly-stone-wall.js";
import { bakeVfPainterlyMoss, type VfPainterlyMossParams } from "./vf-recipes/vf-painterly-moss.js";
import { bakeVfPainterlyWolfFur, type VfPainterlyWolfFurParams } from "./vf-recipes/vf-painterly-wolf-fur.js";
import {
  bakeVf3DGrass,
  bakeVf3DMoss,
  bakeVf3DFur,
  bakeVf3DFire,
  type Vf3DShowcaseParams,
} from "./vf-recipes/vf-3d-material-showcase.js";
import { applySurfaceLayers, type SurfaceLayerState } from "./vf-recipes/vf-surface-layers.js";
import {
  DEFAULT_SURFACE_CONTEXT,
  EMPTY_SURFACE_STATE,
  materialTraitsForPreset,
  resolveAdaptiveSurfaceState,
  type AdaptiveSurfaceState,
  type EnvironmentContext,
  type ExposureContext,
  type SurfaceContext,
  type SurfaceInteractionContext,
  type SurfaceMaterialTraits,
  type WeatherContext,
} from "./vf-recipes/vf-surface-context.js";

const PRODUCTION_STYLE_ID="VF_PAINTERLY_PLANETARY_V1";
const SAFE_NAME=/^[a-z0-9][a-z0-9_-]{1,79}$/;
const TAU=Math.PI*2;
const C=(x:number)=>Math.max(0,Math.min(1,x));
const S=(x:number)=>{const t=C(x);return t*t*(3-2*t);};
const W=(x:number)=>x-Math.round(x);
const MOD=(x:number,m:number)=>((x%m)+m)%m;
function H(seed:number,a:number,b=0,c=0){let h=(seed|0)^Math.imul((a|0)+0x9e3779b9,0x85ebca6b)^Math.imul((b|0)+0x7f4a7c15,0xc2b2ae35)^Math.imul((c|0)+0x165667b1,0x27d4eb2d);h=Math.imul(h^(h>>>16),0x7feb352d);h=Math.imul(h^(h>>>15),0x846ca68b);h^=h>>>16;return(h>>>0)/0xffffffff;}
type ProductionPreset="vfLayeredSandstonePainted"|"vfPainterlyDirt"|"vfPainterlyBark"|"vfPainterlyLeaves"|"vfPainterlySnow"|"vfPainterlyWater"|"vfPainterlyStoneWall"|"vfPainterlyMoss"|"vfPainterlyWolfFur"|"vf3DGrass"|"vf3DMoss"|"vf3DFur"|"vf3DFire";
type Profile="stylized"|"signature";
type SurfaceContextInput={weather?:Partial<WeatherContext>;exposure?:Partial<ExposureContext>;environment?:Partial<EnvironmentContext>;interaction?:Partial<SurfaceInteractionContext>;material?:Partial<SurfaceMaterialTraits>;};
type Request={name:string;resolution:number;preset:ProductionPreset;profile?:Profile;params:Record<string,unknown>;layers?:SurfaceLayerState;context?:SurfaceContextInput;previousLayers?:Partial<AdaptiveSurfaceState>;deltaSeconds?:number;};
type Envelope=Request|{materials:Request[]};
type BakeResult={material:Material;masks?:Readonly<Record<string,unknown>>};
type PresetBaker=(resolution:number,params:Record<string,unknown>)=>BakeResult;

type SupportCell={distance:number;boundary:number;heightBias:number;warm:number;light:number;};
function supportCell(u:number,v:number,seed:number):SupportCell{
  const gxCount=4,gyCount=5;
  const gx=Math.floor(u*gxCount),gy=Math.floor(v*gyCount);
  let best=1e9,second=1e9,bx=0,by=0;
  for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
    const ix=MOD(gx+ox,gxCount),iy=MOD(gy+oy,gyCount);
    const cx=(ix+.5+(H(seed,ix,iy,1)-.5)*.62)/gxCount;
    const cy=(iy+.5+(H(seed,ix,iy,2)-.5)*.58)/gyCount;
    const dx=W(u-cx)*gxCount;
    const dy=W(v-cy)*gyCount*.82;
    const d=Math.sqrt(dx*dx+dy*dy);
    if(d<best){second=best;best=d;bx=ix;by=iy;}else if(d<second)second=d;
  }
  const boundary=1-S((second-best)/.135);
  return{distance:best,boundary,heightBias:H(seed,bx,by,3),warm:H(seed,bx,by,4),light:H(seed,bx,by,5)};
}

/**
 * Converts the low backing field into a raised, continuous sandstone mass while
 * preserving the authored near-black fissures inside primary boulders.
 * Signature rule: read one thick cliff skin first, then hero blocks, then thin cracks.
 */
function closeSandstoneShell(material:Material,size:number,seed:number,normalStrength:number):Material{
  const height=material.height.data;
  const base=material.baseColor.data;
  const rough=material.roughness.data;
  const ao=material.ao.data;
  for(let y=0;y<size;y++){
    const v=(y+.5)/size;
    for(let x=0;x<size;x++){
      const u=(x+.5)/size;
      const i=y*size+x,j=i*3;
      const originalH=height[i];
      const r=base[j],g=base[j+1],b=base[j+2];
      const notTrueCrack=r>.11&&g>.028;
      if(notTrueCrack){
        const closure=C((.525-originalH)/.080);
        if(closure>0){
          const cell=supportCell(u,v,seed+811);
          const interior=1-cell.boundary;
          const strata=.5+.5*Math.sin(TAU*(9*v+u*.55+cell.warm*.37));
          const blockPlane=.5+.5*Math.sin(TAU*(2*u-v*.35+cell.light*.27));
          const supportH=.535+cell.heightBias*.060+interior*.030-cell.boundary*.004+strata*.004+blockPlane*.006;
          height[i]=Math.max(originalH,originalH*(1-closure)+supportH*closure);
          const sr=.41+cell.light*.17+cell.warm*.045;
          const sg=.155+cell.light*.105+cell.warm*.045;
          const sb=.050+cell.light*.040+cell.warm*.020;
          const seamShade=1-cell.boundary*.16;
          const strataLift=strata*.025;
          const planeLift=(blockPlane-.5)*.035;
          const targetR=(sr+strataLift+planeLift)*seamShade;
          const targetG=(sg+strataLift*.55+planeLift*.55)*seamShade;
          const targetB=(sb+strataLift*.22+planeLift*.18)*seamShade;
          const colorMix=closure*.92;
          base[j]=r*(1-colorMix)+targetR*colorMix;
          base[j+1]=g*(1-colorMix)+targetG*colorMix;
          base[j+2]=b*(1-colorMix)+targetB*colorMix;
          rough[i]=rough[i]*(1-closure*.78)+(.68+cell.boundary*.10+strata*.025)*(closure*.78);
          ao[i]=Math.max(ao[i],.86-cell.boundary*.075);
        }
        const lifted=height[i];
        const hero=C((lifted-.49)/.31);
        height[i]=C(lifted+hero*hero*.105);
      }
    }
  }
  return{...material,normal:heightToNormal(material.height,Math.max(1,Math.min(20,normalStrength)),true)};
}

const PRODUCTION_PRESETS:Readonly<Record<ProductionPreset,PresetBaker>>={
  vfLayeredSandstonePainted:(resolution,params)=>{
    const p=params as VfLayeredSandstoneParams;
    const raw=bakeVfLayeredSandstonePainted(resolution,p);
    const seed=Number(p.seed??771231);
    const strength=Number(p.normalStrength??12.4);
    return{material:closeSandstoneShell(raw,resolution,Number.isFinite(seed)?seed:771231,Number.isFinite(strength)?strength:12.4)};
  },
  vfPainterlyDirt:(resolution,params)=>({material:bakeVfPainterlyDirt(resolution,params as VfPainterlyDirtParams)}),
  vfPainterlyBark:(resolution,params)=>({material:bakeVfPainterlyBark(resolution,params as VfPainterlyBarkParams)}),
  vfPainterlyLeaves:(resolution,params)=>bakeVfPainterlyLeavesBundle(resolution,params as VfPainterlyLeavesParams),
  vfPainterlySnow:(resolution,params)=>({material:bakeVfPainterlySnow(resolution,params as VfPainterlySnowParams)}),
  vfPainterlyWater:(resolution,params)=>bakeVfPainterlyWater(resolution,params as VfPainterlyWaterParams),
  vfPainterlyStoneWall:(resolution,params)=>({material:bakeVfPainterlyStoneWall(resolution,params as VfPainterlyStoneWallParams)}),
  vfPainterlyMoss:(resolution,params)=>bakeVfPainterlyMoss(resolution,params as VfPainterlyMossParams),
  vfPainterlyWolfFur:(resolution,params)=>bakeVfPainterlyWolfFur(resolution,params as VfPainterlyWolfFurParams),
  vf3DGrass:(resolution,params)=>bakeVf3DGrass(resolution,params as Vf3DShowcaseParams),
  vf3DMoss:(resolution,params)=>bakeVf3DMoss(resolution,params as Vf3DShowcaseParams),
  vf3DFur:(resolution,params)=>bakeVf3DFur(resolution,params as Vf3DShowcaseParams),
  vf3DFire:(resolution,params)=>bakeVf3DFire(resolution,params as Vf3DShowcaseParams),
};

function validateRequest(req:Request){
  if(!SAFE_NAME.test(req.name))throw new Error(`Unsafe material name: ${String(req.name)}`);
  if(!Number.isInteger(req.resolution)||req.resolution<64||req.resolution>4096)throw new Error(`Invalid resolution for ${req.name}: ${req.resolution}`);
  if(!(req.preset in PRODUCTION_PRESETS))throw new Error(`Preset is not production-approved: ${String(req.preset)}`);
  if(req.profile&&req.profile!=="stylized"&&req.profile!=="signature")throw new Error(`Invalid profile for ${req.name}`);
  if(!req.params||typeof req.params!=="object"||Array.isArray(req.params))throw new Error(`Invalid params for ${req.name}`);
  if(req.layers&&(typeof req.layers!=="object"||Array.isArray(req.layers)))throw new Error(`Invalid layers for ${req.name}`);
  if(req.context&&(typeof req.context!=="object"||Array.isArray(req.context)))throw new Error(`Invalid context for ${req.name}`);
  if(req.context&&req.layers)throw new Error(`${req.name}: use either adaptive context or direct layers, not both`);
  if(req.previousLayers&&!req.context)throw new Error(`${req.name}: previousLayers requires adaptive context`);
  if(req.deltaSeconds!==undefined&&(!Number.isFinite(req.deltaSeconds)||req.deltaSeconds<0))throw new Error(`${req.name}: invalid deltaSeconds`);
}
function buildContext(req:Request):SurfaceContext{const input=req.context??{};return{weather:{...DEFAULT_SURFACE_CONTEXT.weather,...(input.weather??{})},exposure:{...DEFAULT_SURFACE_CONTEXT.exposure,...(input.exposure??{})},environment:{...DEFAULT_SURFACE_CONTEXT.environment,...(input.environment??{})},interaction:{...DEFAULT_SURFACE_CONTEXT.interaction,...(input.interaction??{})},material:{...materialTraitsForPreset(req.preset),...(input.material??{})}};}
function resolveLayers(req:Request):SurfaceLayerState{if(!req.context)return req.layers??{};const previous:AdaptiveSurfaceState={...EMPTY_SURFACE_STATE,...(req.previousLayers??{})};return resolveAdaptiveSurfaceState(previous,buildContext(req),req.deltaSeconds??1);}
function bakeOne(req:Request){
  validateRequest(req);const baker=PRODUCTION_PRESETS[req.preset],base=baker(req.resolution,req.params),seed=Number(req.params.seed??1),resolvedLayers=resolveLayers(req);
  const layered=applySurfaceLayers(base.material,resolvedLayers,Number.isFinite(seed)?seed:1,req.preset),material=layered.material,masks={...(base.masks??{}),...layered.masks};
  const problems=validateMaterial(material);if(problems.length>0)throw new Error(`${req.name}: ${problems.join("; ")}`);
  const out=path.resolve(process.cwd(),"out","vf-materials",req.name);mkdirSync(out,{recursive:true});const exported=exportPBR(material,req.name);
  for(const[filename,bytes]of Object.entries(exported.files))writeFileSync(path.join(out,filename),bytes);
  for(const[maskName,mask]of Object.entries(masks))writeFileSync(path.join(out,`${req.name}_mask-${maskName}.png`),textureToPNG(mask as never));
  writeFileSync(path.join(out,"request.json"),JSON.stringify(req,null,2));
  const manifest={generator:"wellingfeng/Meshova + voxel-frontier production recipes",generatorCommit:process.env.MESHOVA_COMMIT??"unknown",styleId:PRODUCTION_STYLE_ID,deterministic:true,proceduralSourceOnly:true,seamlessByConstruction:true,material:req.name,resolution:req.resolution,profile:req.profile??"signature",preset:req.preset,sandstoneContinuousShellClosure:req.preset==="vfLayeredSandstonePainted",sandstoneSupportGeometry:req.preset==="vfLayeredSandstonePainted"?"raised-periodic-jittered-voronoi":null,adaptiveSurfaceContext:Boolean(req.context),surfaceContext:req.context??null,deltaSeconds:req.context?(req.deltaSeconds??1):null,resolvedLayers,pbrFiles:Object.keys(exported.files).sort(),maskFiles:Object.keys(masks).map(name=>`${req.name}_mask-${name}.png`).sort()};
  writeFileSync(path.join(out,"manifest.json"),JSON.stringify(manifest,null,2));console.log(JSON.stringify({ok:true,output:out,...manifest},null,2));return manifest;
}
const requestPath=process.argv[2]??"vf-request.json",envelope=JSON.parse(readFileSync(requestPath,"utf8")) as Envelope,requests="materials" in envelope?envelope.materials:[envelope];
if(!Array.isArray(requests)||requests.length===0)throw new Error("No materials requested");const names=new Set<string>();for(const req of requests){if(!req.name||names.has(req.name))throw new Error(`Invalid or duplicate material name: ${String(req.name)}`);names.add(req.name);}const manifests=requests.map(bakeOne);console.log(JSON.stringify({ok:true,styleId:PRODUCTION_STYLE_ID,materialCount:manifests.length,materials:manifests.map(m=>m.material)},null,2));
