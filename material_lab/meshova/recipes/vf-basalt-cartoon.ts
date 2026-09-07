import { heightToNormal, makeTexture, type Material } from "../../src/index.js";
import { bakeVfBasalt, type VfBasaltParams } from "./vf-basalt.js";

type RGB = [number, number, number];
export type VfBasaltCartoonParams = VfBasaltParams & {
  paletteSteps?: number;
  blockiness?: number;
  stylizedNormalStrength?: number;
};

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const mix = (a: RGB, b: RGB, t: number): RGB => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];

function sample(tex: { width:number; height:number; channels:number; data:Float32Array }, u:number, v:number, ch:number) {
  const x = clamp01(u) * (tex.width - 1), y = clamp01(v) * (tex.height - 1);
  const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(tex.width - 1, x0 + 1), y1 = Math.min(tex.height - 1, y0 + 1);
  const tx = x - x0, ty = y - y0;
  const at = (xx:number, yy:number) => tex.data[(yy * tex.width + xx) * tex.channels + ch];
  return lerp(lerp(at(x0,y0), at(x1,y0), tx), lerp(at(x0,y1), at(x1,y1), tx), ty);
}

function paletteColor(c: RGB, height:number, ao:number, steps:number): RGB {
  const lum = c[0] * 0.24 + c[1] * 0.68 + c[2] * 0.08;
  const warm = c[0] > c[1] * 1.22 && c[0] > 0.09;
  if (warm) {
    const t = clamp01((lum - 0.05) / 0.16);
    return mix([0.11,0.045,0.025], [0.34,0.145,0.055], Math.round(t * 2) / 2);
  }
  const n = Math.max(3, Math.round(steps));
  const t = clamp01((lum - 0.025) / 0.235);
  const q = Math.round(t * (n - 1)) / (n - 1);
  const palettes: RGB[] = [
    [0.028,0.043,0.058],
    [0.060,0.078,0.094],
    [0.105,0.125,0.136],
    [0.165,0.183,0.184],
    [0.225,0.236,0.226],
  ];
  const pi = Math.min(palettes.length - 2, Math.floor(q * (palettes.length - 1)));
  const local = q * (palettes.length - 1) - pi;
  let out = mix(palettes[pi], palettes[pi + 1], local);
  const faceLift = (Math.round(height * 5) / 5 - 0.5) * 0.075;
  const cavity = (1 - ao) * 0.45;
  out = out.map((x) => clamp01(x + faceLift - cavity)) as RGB;
  return out;
}

export function bakeVfBasaltCartoon(size:number, params:VfBasaltCartoonParams = {}): Material {
  // Bake the SAME procedural geology at lower spatial frequency first. This keeps
  // fracture/pores placement from the same seed while intentionally suppressing
  // photographic micro-noise for a stylized read.
  const blockiness = Math.max(2, Math.min(10, params.blockiness ?? 6));
  const sourceSize = Math.max(192, Math.round(size / blockiness));
  const source = bakeVfBasalt(sourceSize, {
    ...params,
    normalStrength: 8.0,
    macroRelief: params.macroRelief ?? 1.42,
    mesoRelief: params.mesoRelief ?? 1.62,
    fractureStrength: params.fractureStrength ?? 0.64,
    poreDensity: params.poreDensity ?? 0.024,
    weathering: params.weathering ?? 0.26,
    roughnessBias: params.roughnessBias ?? 0.015,
    edgeBreakup: params.edgeBreakup ?? 1.30,
  });

  const baseColor = makeTexture(size,size,3);
  const metallic = makeTexture(size,size,1);
  const roughness = makeTexture(size,size,1);
  const ao = makeTexture(size,size,1);
  const height = makeTexture(size,size,1);
  const emission = makeTexture(size,size,3);
  const steps = params.paletteSteps ?? 4;

  for (let y=0; y<size; y++) {
    const v = y / Math.max(1,size-1);
    for (let x=0; x<size; x++) {
      const u = x / Math.max(1,size-1);
      const idx = y*size+x, rgb = idx*3;
      const srcColor:RGB = [sample(source.baseColor,u,v,0), sample(source.baseColor,u,v,1), sample(source.baseColor,u,v,2)];
      const srcH = sample(source.height!,u,v,0);
      const srcAO = sample(source.ao!,u,v,0);
      const srcR = sample(source.roughness,u,v,0);

      // Broad, deliberately stepped rock planes. Keep a little continuous signal
      // so it reads as designed rock rather than voxel stair-stepping.
      const hBand = Math.round(srcH * 12) / 12;
      const h = clamp01(0.5 + ((hBand * 0.74 + srcH * 0.26) - 0.5) * 1.18);
      height.data[idx] = h;

      const aoStrong = clamp01(1 - (1 - srcAO) * 1.55);
      ao.data[idx] = aoStrong;

      const c = paletteColor(srcColor, h, aoStrong, steps);
      baseColor.data[rgb] = c[0];
      baseColor.data[rgb+1] = c[1];
      baseColor.data[rgb+2] = c[2];

      // Three clearly readable material-response bands instead of noisy scalar roughness.
      let r = srcR < 0.63 ? 0.54 : srcR < 0.76 ? 0.70 : 0.84;
      if (aoStrong < 0.86) r = Math.min(0.90, r + 0.08);
      roughness.data[idx] = r;
      metallic.data[idx] = 0;
      emission.data[rgb] = emission.data[rgb+1] = emission.data[rgb+2] = 0;
    }
  }

  const normal = heightToNormal(height, Math.max(8, Math.min(20, params.stylizedNormalStrength ?? 16.5)), true);
  return { baseColor, metallic, roughness, normal, ao, height, emission };
}
