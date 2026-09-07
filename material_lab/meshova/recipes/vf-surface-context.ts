export type PrecipitationType = "none" | "rain" | "snow" | "sleet";

export type WeatherContext = {
  precipitationType: PrecipitationType;
  precipitationRate: number;      // 0..1
  temperatureC: number;
  humidity: number;               // 0..1
  windSpeedMps: number;
  solarExposure: number;          // 0..1
};

export type ExposureContext = {
  outdoors: number;               // 0..1; 0 = fully indoors
  skyVisibility: number;          // 0..1
  shelter: number;                // 0..1; roof/canopy/overhang
  windExposure: number;           // 0..1
  localHeatC: number;             // additive local heat from fires/machines/etc.
};

export type EnvironmentContext = {
  slope: number;                  // 0 flat .. 1 vertical
  drainage: number;               // 0 poor .. 1 excellent
  groundSaturation: number;       // 0..1
  waterContact: number;           // 0..1 splashing / shoreline contact
  submerged: number;              // 0..1
};

export type SurfaceInteractionContext = {
  playerContact: number;          // 0..1
  propContact: number;            // 0..1
  compression: number;            // footprints / wheels / placed props
  splash: number;                 // 0..1
  heat: number;                   // 0..1
  wash: number;                   // 0..1
  scrape: number;                 // 0..1
};

export type SurfaceMaterialTraits = {
  waterAbsorption: number;        // porous materials get wet quickly
  evaporationRate: number;        // ability to dry
  snowRetention: number;          // foliage low, rough rock high
  snowInsulation: number;         // slows melt
  drainage: number;               // material-local drainage
  puddleAffinity: number;         // flat impermeable surfaces high
  thermalResponse: number;        // how strongly ambient/local heat affects state
  rainRippleResponse: number;     // water surfaces ~1, solids 0
};

export type AdaptiveSurfaceState = {
  snowCoverage: number;
  snowDepth: number;
  snowCompaction: number;
  wetness: number;
  puddleLevel: number;
  rainIntensity: number;
};

export type SurfaceContext = {
  weather: WeatherContext;
  exposure: ExposureContext;
  environment: EnvironmentContext;
  interaction: SurfaceInteractionContext;
  material: SurfaceMaterialTraits;
};

const C=(x:number)=>Math.max(0,Math.min(1,x));
const expApproach=(value:number,target:number,rate:number,dt:number)=>{
  const k=1-Math.exp(-Math.max(0,rate)*Math.max(0,dt));
  return value+(target-value)*k;
};

export const EMPTY_SURFACE_STATE:AdaptiveSurfaceState={
  snowCoverage:0,
  snowDepth:0,
  snowCompaction:0,
  wetness:0,
  puddleLevel:0,
  rainIntensity:0,
};

export const DEFAULT_SURFACE_CONTEXT:SurfaceContext={
  weather:{precipitationType:"none",precipitationRate:0,temperatureC:15,humidity:.5,windSpeedMps:1,solarExposure:.5},
  exposure:{outdoors:1,skyVisibility:1,shelter:0,windExposure:1,localHeatC:0},
  environment:{slope:.25,drainage:.5,groundSaturation:.2,waterContact:0,submerged:0},
  interaction:{playerContact:0,propContact:0,compression:0,splash:0,heat:0,wash:0,scrape:0},
  material:{waterAbsorption:.6,evaporationRate:.55,snowRetention:.7,snowInsulation:.55,drainage:.5,puddleAffinity:.45,thermalResponse:.5,rainRippleResponse:0},
};

export const SURFACE_TRAITS={
  rock:{waterAbsorption:.48,evaporationRate:.62,snowRetention:.82,snowInsulation:.42,drainage:.55,puddleAffinity:.58,thermalResponse:.62,rainRippleResponse:0},
  dirt:{waterAbsorption:.96,evaporationRate:.36,snowRetention:.78,snowInsulation:.66,drainage:.28,puddleAffinity:.72,thermalResponse:.38,rainRippleResponse:0},
  bark:{waterAbsorption:.73,evaporationRate:.58,snowRetention:.54,snowInsulation:.52,drainage:.76,puddleAffinity:.08,thermalResponse:.48,rainRippleResponse:0},
  leaves:{waterAbsorption:.42,evaporationRate:.82,snowRetention:.32,snowInsulation:.25,drainage:.94,puddleAffinity:.02,thermalResponse:.72,rainRippleResponse:0},
  snow:{waterAbsorption:.88,evaporationRate:.18,snowRetention:1,snowInsulation:.92,drainage:.18,puddleAffinity:.55,thermalResponse:.30,rainRippleResponse:0},
  water:{waterAbsorption:0,evaporationRate:.12,snowRetention:0,snowInsulation:0,drainage:1,puddleAffinity:0,thermalResponse:.85,rainRippleResponse:1},
} as const satisfies Record<string,SurfaceMaterialTraits>;

export function resolveAdaptiveSurfaceState(previous:AdaptiveSurfaceState,ctx:SurfaceContext,deltaSeconds:number):AdaptiveSurfaceState{
  const dt=Math.max(0,deltaSeconds);
  const w=ctx.weather,e=ctx.exposure,g=ctx.environment,i=ctx.interaction,m=ctx.material;

  const openSky=C(e.outdoors)*C(e.skyVisibility)*(1-C(e.shelter));
  const precipExposure=C(w.precipitationRate)*openSky;
  const rainShare=w.precipitationType==="rain"?1:w.precipitationType==="sleet"?.55:0;
  const snowShare=w.precipitationType==="snow"?1:w.precipitationType==="sleet"?.45:0;
  const effectiveTemp=w.temperatureC+e.localHeatC*C(m.thermalResponse)+i.heat*18*C(m.thermalResponse);
  const windDry=C((w.windSpeedMps/16)*C(e.windExposure));
  const sunDry=C(w.solarExposure)*openSky;

  const rainInput=precipExposure*rainShare;
  const splashInput=C(g.waterContact*.45+i.splash*.75+g.submerged);
  const wetTarget=C((rainInput*.92+splashInput)*(0.30+0.70*C(m.waterAbsorption)) + g.groundSaturation*.25*C(m.waterAbsorption));
  const evaporation=C((1-C(w.humidity))*.42+windDry*.32+sunDry*.35+C(Math.max(0,effectiveTemp)/32)*.30)*C(m.evaporationRate);
  let wetness=expApproach(C(previous.wetness),wetTarget,0.10+wetTarget*1.9,dt);
  wetness=expApproach(wetness,0,evaporation*.32,dt);
  wetness=C(wetness + i.splash*.10 + g.submerged*.30 - i.wash*.02);

  const freezing=C((1.5-effectiveTemp)/5.5);
  const snowfall=precipExposure*snowShare*freezing*C(m.snowRetention);
  const retention=C(m.snowRetention)*(1-C(g.slope)*.72)*(0.72+0.28*(1-windDry));
  const snowTarget=C(snowfall*retention*1.55);
  let snowCoverage=expApproach(C(previous.snowCoverage),snowTarget,0.18+snowfall*1.7,dt);
  let snowDepth=expApproach(C(previous.snowDepth),snowTarget,0.10+snowfall*.95,dt);

  const meltHeat=C(Math.max(0,effectiveTemp)/12 + sunDry*.45 + rainInput*.25 + i.heat*.90);
  const meltRate=meltHeat*(1-C(m.snowInsulation)*.64);
  snowCoverage=expApproach(snowCoverage,0,meltRate*.25,dt);
  snowDepth=expApproach(snowDepth,0,meltRate*.40,dt);

  const contact=C(i.playerContact*.62+i.propContact*.38);
  const compression=C(Math.max(i.compression,contact*.35));
  let snowCompaction=expApproach(C(previous.snowCompaction),compression,compression*2.4,dt);
  snowCompaction=expApproach(snowCompaction,0,(snowfall*.12+meltRate*.18),dt);
  snowDepth=C(snowDepth*(1-compression*.28));
  snowCoverage=C(snowCoverage*(1-i.scrape*.50-i.wash*.18));

  if(snowCoverage>0){
    wetness=C(wetness + meltRate*snowCoverage*.10);
  }

  const flatness=1-C(g.slope);
  const drainage=C((C(g.drainage)+C(m.drainage))*.5);
  const puddleTarget=C(wetness*flatness*C(m.puddleAffinity)*(1-drainage*.72)*(0.55+g.groundSaturation*.45));
  let puddleLevel=expApproach(C(previous.puddleLevel),puddleTarget,.28+puddleTarget*1.4,dt);
  puddleLevel=expApproach(puddleLevel,0,(evaporation*.18+drainage*.12),dt);

  const rainIntensity=C(rainInput*C(m.rainRippleResponse));

  return {
    snowCoverage:C(snowCoverage),
    snowDepth:C(snowDepth),
    snowCompaction:C(snowCompaction),
    wetness:C(wetness),
    puddleLevel:C(puddleLevel),
    rainIntensity,
  };
}

export function materialTraitsForPreset(preset:string):SurfaceMaterialTraits{
  switch(preset){
    case "vfLayeredSandstonePainted": return {...SURFACE_TRAITS.rock};
    case "vfPainterlyDirt": return {...SURFACE_TRAITS.dirt};
    case "vfPainterlyBark": return {...SURFACE_TRAITS.bark};
    case "vfPainterlyLeaves": return {...SURFACE_TRAITS.leaves};
    case "vfPainterlySnow": return {...SURFACE_TRAITS.snow};
    case "vfPainterlyWater": return {...SURFACE_TRAITS.water};
    default:return {...DEFAULT_SURFACE_CONTEXT.material};
  }
}
