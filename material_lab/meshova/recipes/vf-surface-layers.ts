import { heightToNormal, makeTexture, type Material } from "../../src/index.js";
import { C, L, M, S, TAU, hash, periodicField, wrapDelta, type RGB } from "./vf-painterly-core.js";

type Tex = ReturnType<typeof makeTexture>;
export type SurfaceLayerState = {
  snowCoverage?: number;
  snowDepth?: number;
  wetness?: number;
  rainIntensity?: number;
};
export type SurfaceLayerResult = {
  material: Material;
  masks: Record<string, Tex>;
};

function cloneTexture<T extends Tex>(src: T): T {
  const dst = makeTexture(src.width, src.height, src.channels) as T;
  dst.data.set(src.data);
  return dst;
}

function buildRainDrops(seed: number, intensity: number) {
  const count = Math.max(6, Math.round(8 + intensity * 14));
  const drops: { cx:number; cy:number; r:number; width:number; phase:number; strength:number }[] = [];
  for (let i = 0; i < count; i++) {
    drops.push({
      cx: hash(seed, i, 31),
      cy: hash(seed, i, 32),
      r: .025 + hash(seed, i, 33) * .085,
      width: .006 + hash(seed, i, 34) * .012,
      phase: hash(seed, i, 35) * TAU,
      strength: .55 + hash(seed, i, 36) * .45,
    });
  }
  return drops;
}

function rainRipple(u:number,v:number,drops:ReturnType<typeof buildRainDrops>) {
  let ripple = 0;
  let mask = 0;
  for (const d of drops) {
    const dx = wrapDelta(u - d.cx), dy = wrapDelta(v - d.cy);
    const r = Math.hypot(dx,dy);
    const dr = r - d.r;
    const envelope = Math.exp(-(dr*dr)/(2*d.width*d.width));
    ripple += envelope * Math.sin(dr * (90 + 28*d.strength) + d.phase) * d.strength;
    mask = Math.max(mask, envelope * d.strength);
  }
  return { ripple, mask:C(mask) };
}

export function applySurfaceLayers(
  src: Material,
  state: SurfaceLayerState = {},
  seed = 1,
  preset = "",
): SurfaceLayerResult {
  if (!src.height) throw new Error("Surface layers require Height.");
  const baseColor = cloneTexture(src.baseColor);
  const metallic = cloneTexture(src.metallic);
  const roughness = cloneTexture(src.roughness);
  const height = cloneTexture(src.height);
  const ao = cloneTexture(src.ao);
  const emission = cloneTexture(src.emission);

  const snowCoverage = C(Number(state.snowCoverage ?? 0));
  const snowDepth = C(Number(state.snowDepth ?? .55));
  const wetness = C(Number(state.wetness ?? 0));
  const rainIntensity = C(Number(state.rainIntensity ?? 0));
  const size = height.width;

  const snowMask = makeTexture(size,size,1);
  const wetMask = makeTexture(size,size,1);
  const puddleMask = makeTexture(size,size,1);
  const rainMask = makeTexture(size,size,1);

  let hMin = Infinity, hMax = -Infinity;
  for (const h of height.data) { if (h < hMin) hMin = h; if (h > hMax) hMax = h; }
  const hSpan = Math.max(.04, hMax - hMin);
  const rainDrops = rainIntensity > 0 && preset === "vfPainterlyWater"
    ? buildRainDrops(seed + 7717, rainIntensity)
    : [];

  for (let y=0;y<size;y++) {
    const v = 1 - (y+.5)/size;
    for (let x=0;x<size;x++) {
      const u=(x+.5)/size, i=y*size+x, j=i*3;
      const h0 = height.data[i];
      const hn = C((h0-hMin)/hSpan);
      const n0z = src.normal.data[j+2]*2-1;
      const flat = C((n0z-.45)/.52);
      const terrainNoise = periodicField(u,v,seed+1901,3)*.5+.5;

      let snow = 0;
      if (snowCoverage > 0 && preset !== "vfPainterlyWater") {
        const accumulation = hn*.42 + flat*.42 + terrainNoise*.16;
        const threshold = L(1.04,.18,snowCoverage);
        snow = S((accumulation-threshold)/.20);
        if (snowCoverage > .82) snow = Math.max(snow, S((snowCoverage-.82)/.18)*(.52+.48*flat));
        snow = C(snow * (0.72 + snowCoverage*.38));
        snowMask.data[i]=snow;

        const coolShadow:RGB=[.46,.62,.80], snowMid:RGB=[.78,.86,.92], snowLight:RGB=[.985,.98,.94];
        const snowTone=M(coolShadow,snowMid,C(.38+hn*.42+terrainNoise*.20));
        const snowCol=M(snowTone,snowLight,C(.38+flat*.50));
        baseColor.data[j]=L(baseColor.data[j],snowCol[0],snow);
        baseColor.data[j+1]=L(baseColor.data[j+1],snowCol[1],snow);
        baseColor.data[j+2]=L(baseColor.data[j+2],snowCol[2],snow);
        roughness.data[i]=L(roughness.data[i],.91,snow*.88);
        height.data[i]=C(height.data[i]+snow*(.020+.075*snowDepth)*(0.62+.38*flat));
        ao.data[i]=L(ao.data[i],1,snow*.55);
      }

      let wet = 0, puddle = 0;
      if (wetness > 0 && preset !== "vfPainterlyWater") {
        wet = C(wetness * (.72 + terrainNoise*.28) * (1-snow*.72));
        const low = C(1-hn);
        puddle = C(wetness * S((flat-.56)/.35) * S((low-.42)/.48) * (.55+.45*terrainNoise));
        wetMask.data[i]=wet;
        puddleMask.data[i]=puddle;

        const srcCol:RGB=[baseColor.data[j],baseColor.data[j+1],baseColor.data[j+2]];
        const dark:RGB=[srcCol[0]*.48,srcCol[1]*.52,srcCol[2]*.58];
        const cool:RGB=[.025,.050,.065];
        let c=M(srcCol,dark,wet*.58);
        c=M(c,cool,puddle*.20);
        baseColor.data[j]=C(c[0]); baseColor.data[j+1]=C(c[1]); baseColor.data[j+2]=C(c[2]);
        roughness.data[i]=L(roughness.data[i],.24,wet*.72);
        roughness.data[i]=L(roughness.data[i],.055,puddle*.92);
        ao.data[i]=C(ao.data[i]*(1-.05*wet));
      }

      if (rainDrops.length) {
        const rr = rainRipple(u,v,rainDrops);
        const rain = C(rr.mask*rainIntensity);
        rainMask.data[i]=rain;
        height.data[i]=C(height.data[i]+rr.ripple*(.0035+.0075*rainIntensity));
        roughness.data[i]=C(L(roughness.data[i],.13,rain*.42));
        const cyan:RGB=[.08,.32,.42];
        baseColor.data[j]=L(baseColor.data[j],cyan[0],rain*.035);
        baseColor.data[j+1]=L(baseColor.data[j+1],cyan[1],rain*.035);
        baseColor.data[j+2]=L(baseColor.data[j+2],cyan[2],rain*.035);
      }
    }
  }

  const layerNormal = heightToNormal(height, preset === "vfPainterlyWater" ? 8.0 : 10.0, true);
  const normal = cloneTexture(src.normal);
  for (let i=0;i<size*size;i++) {
    const j=i*3;
    const amount = C(Math.max(snowMask.data[i]*.90, rainMask.data[i]*.82));
    normal.data[j]=L(src.normal.data[j],layerNormal.data[j],amount);
    normal.data[j+1]=L(src.normal.data[j+1],layerNormal.data[j+1],amount);
    normal.data[j+2]=L(src.normal.data[j+2],layerNormal.data[j+2],amount);
  }

  const masks:Record<string,Tex> = {};
  if (snowCoverage>0) masks.snowCoverage=snowMask;
  if (wetness>0) { masks.wetness=wetMask; masks.puddles=puddleMask; }
  if (rainIntensity>0 && preset==="vfPainterlyWater") masks.rainRipples=rainMask;

  return { material:{baseColor,metallic,roughness,normal,ao,height,emission}, masks };
}
