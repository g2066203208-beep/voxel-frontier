import assert from "node:assert/strict";
import {
  DEFAULT_SURFACE_CONTEXT,
  EMPTY_SURFACE_STATE,
  SURFACE_TRAITS,
  resolveAdaptiveSurfaceState,
  type SurfaceContext,
} from "../meshova/recipes/vf-surface-context.js";

const ctx=(patch:Partial<SurfaceContext>):SurfaceContext=>({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,...(patch.weather??{})},
  exposure:{...DEFAULT_SURFACE_CONTEXT.exposure,...(patch.exposure??{})},
  environment:{...DEFAULT_SURFACE_CONTEXT.environment,...(patch.environment??{})},
  interaction:{...DEFAULT_SURFACE_CONTEXT.interaction,...(patch.interaction??{})},
  material:{...DEFAULT_SURFACE_CONTEXT.material,...(patch.material??{})},
});
const step=(initial=EMPTY_SURFACE_STATE,c=ctx({}),seconds=30)=>resolveAdaptiveSurfaceState(initial,c,seconds);

const openSnow=step(EMPTY_SURFACE_STATE,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,precipitationType:"snow",precipitationRate:1,temperatureC:-8,humidity:.9,solarExposure:.1},
  exposure:{...DEFAULT_SURFACE_CONTEXT.exposure,outdoors:1,skyVisibility:1,shelter:0},
  material:{...SURFACE_TRAITS.rock},
}),120);
const indoorSnow=step(EMPTY_SURFACE_STATE,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,precipitationType:"snow",precipitationRate:1,temperatureC:-8,humidity:.9,solarExposure:.1},
  exposure:{...DEFAULT_SURFACE_CONTEXT.exposure,outdoors:0,skyVisibility:0,shelter:1},
  material:{...SURFACE_TRAITS.rock},
}),120);
assert(openSnow.snowCoverage>.35,"open sky should accumulate snow");
assert(indoorSnow.snowCoverage<.01,"indoor surface must not receive direct snowfall");

const shelteredSnow=step(EMPTY_SURFACE_STATE,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,precipitationType:"snow",precipitationRate:1,temperatureC:-8},
  exposure:{...DEFAULT_SURFACE_CONTEXT.exposure,outdoors:1,skyVisibility:.35,shelter:.75},
  material:{...SURFACE_TRAITS.rock},
}),120);
assert(shelteredSnow.snowCoverage<openSnow.snowCoverage,"shelter must reduce snow accumulation");

const rainRock=step(EMPTY_SURFACE_STATE,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,precipitationType:"rain",precipitationRate:.9,temperatureC:10,humidity:.95,solarExposure:.05},
  environment:{...DEFAULT_SURFACE_CONTEXT.environment,slope:.05,drainage:.10,groundSaturation:.8},
  material:{...SURFACE_TRAITS.rock},
}),60);
assert(rainRock.wetness>.35,"rain should wet exposed rock");
assert(rainRock.puddleLevel>.05,"flat poorly drained rock should form puddles");
assert.equal(rainRock.rainIntensity,0,"solid rock should not generate water-surface rain ripples");

const rainWater=step(EMPTY_SURFACE_STATE,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,precipitationType:"rain",precipitationRate:.8,temperatureC:14},
  material:{...SURFACE_TRAITS.water},
}),10);
assert(rainWater.rainIntensity>.6,"rain on water should drive ripple intensity");

const dryStart={...EMPTY_SURFACE_STATE,wetness:1,puddleLevel:.7};
const dryEnd=step(dryStart,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,precipitationType:"none",precipitationRate:0,temperatureC:29,humidity:.18,windSpeedMps:12,solarExposure:1},
  exposure:{...DEFAULT_SURFACE_CONTEXT.exposure,outdoors:1,skyVisibility:1,windExposure:1},
  material:{...SURFACE_TRAITS.rock},
}),180);
assert(dryEnd.wetness<dryStart.wetness,"sun/wind/low humidity must dry a wet surface");
assert(dryEnd.puddleLevel<dryStart.puddleLevel,"puddles must drain/evaporate");

const snowy={...EMPTY_SURFACE_STATE,snowCoverage:.9,snowDepth:.85,snowCompaction:.05};
const footprint=step(snowy,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,temperatureC:-4},
  interaction:{...DEFAULT_SURFACE_CONTEXT.interaction,playerContact:1,compression:1},
  material:{...SURFACE_TRAITS.rock},
}),1);
assert(footprint.snowCompaction>snowy.snowCompaction,"player contact should compact snow");
assert(footprint.snowDepth<snowy.snowDepth,"footprint compression should reduce local snow depth");

const heated=step(snowy,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,temperatureC:-2,solarExposure:.1},
  exposure:{...DEFAULT_SURFACE_CONTEXT.exposure,localHeatC:18},
  interaction:{...DEFAULT_SURFACE_CONTEXT.interaction,propContact:1,heat:1},
  material:{...SURFACE_TRAITS.rock},
}),45);
assert(heated.snowDepth<snowy.snowDepth,"hot props/local heat should melt snow");

const steep=step(EMPTY_SURFACE_STATE,ctx({
  weather:{...DEFAULT_SURFACE_CONTEXT.weather,precipitationType:"rain",precipitationRate:1,humidity:1},
  environment:{...DEFAULT_SURFACE_CONTEXT.environment,slope:.9,drainage:.95,groundSaturation:.2},
  material:{...SURFACE_TRAITS.rock},
}),90);
assert(steep.puddleLevel<rainRock.puddleLevel,"steep well-drained surfaces must puddle less than flat poor-drainage surfaces");

console.log(JSON.stringify({ok:true,openSnow,indoorSnow,shelteredSnow,rainRock,rainWater,dryEnd,footprint,heated,steep},null,2));
