import { heightToNormal, makeTexture, type Material } from "../../src/index.js";
import { bakeVfBasalt } from "./vf-basalt.js";
import { bakeVfGranite } from "./vf-granite.js";
import { bakeVfDirt } from "./vf-dirt.js";
import { bakeVfBark } from "./vf-bark.js";
import {
  bakeVfSandstone,
  bakeVfLimestone,
  bakeVfGravel,
  bakeVfSand,
  bakeVfWetMud,
  bakeVfWoodPlank,
  bakeVfIronOre,
  bakeVfCopperOre,
  bakeVfCoal,
  bakeVfSnow,
  bakeVfIce,
} from "./vf-world-surfaces.js";

type RGB = [number, number, number];
type TextureLike = { width: number; height: number; channels: number; data: Float32Array };
type BaseBaker = (size: number, params?: any) => Material;
type CartoonKind =
  | "basalt" | "granite" | "dirt" | "bark" | "sandstone" | "limestone"
  | "gravel" | "sand" | "wetMud" | "woodPlank" | "ironOre" | "copperOre"
  | "coal" | "snow" | "ice";

export type VfCartoonParams = {
  seed?: number;
  blockiness?: number;
  paletteSteps?: number;
  stylizedNormalStrength?: number;
  [key: string]: unknown;
};

type StyleConfig = {
  palette: RGB[];
  lumLow: number;
  lumHigh: number;
  paletteSteps: number;
  huePreserve: number;
  blockiness: number;
  heightBands: number;
  heightMix: number;
  heightGain: number;
  normalStrength: number;
  roughBands: number[];
  aoContrast: number;
  cavityColor: number;
  faceColorLift: number;
};

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const mix = (a: RGB, b: RGB, t: number): RGB => [
  lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t),
];
const wrap01 = (x: number) => x - Math.floor(x);
const q = (x: number, bands: number) => bands <= 1 ? 0 : Math.round(clamp01(x) * (bands - 1)) / (bands - 1);

const STYLE: Record<CartoonKind, StyleConfig> = {
  basalt: {
    palette: [[0.025,0.038,0.052],[0.055,0.071,0.088],[0.092,0.112,0.126],[0.145,0.164,0.168],[0.205,0.218,0.210]],
    lumLow: 0.025, lumHigh: 0.24, paletteSteps: 5, huePreserve: 0.14, blockiness: 5.8,
    heightBands: 12, heightMix: 0.76, heightGain: 1.18, normalStrength: 16.0,
    roughBands: [0.56,0.70,0.84], aoContrast: 1.48, cavityColor: 0.34, faceColorLift: 0.11,
  },
  granite: {
    palette: [[0.045,0.044,0.047],[0.115,0.085,0.082],[0.205,0.145,0.135],[0.315,0.265,0.245],[0.455,0.425,0.385]],
    lumLow: 0.035, lumHigh: 0.48, paletteSteps: 5, huePreserve: 0.42, blockiness: 4.8,
    heightBands: 11, heightMix: 0.68, heightGain: 1.12, normalStrength: 14.5,
    roughBands: [0.48,0.62,0.78], aoContrast: 1.30, cavityColor: 0.24, faceColorLift: 0.10,
  },
  dirt: {
    palette: [[0.050,0.020,0.010],[0.105,0.043,0.018],[0.195,0.083,0.030],[0.305,0.145,0.060],[0.420,0.235,0.105]],
    lumLow: 0.025, lumHigh: 0.34, paletteSteps: 5, huePreserve: 0.18, blockiness: 5.5,
    heightBands: 10, heightMix: 0.72, heightGain: 1.16, normalStrength: 15.0,
    roughBands: [0.68,0.80,0.90], aoContrast: 1.36, cavityColor: 0.30, faceColorLift: 0.09,
  },
  bark: {
    palette: [[0.035,0.014,0.008],[0.075,0.028,0.013],[0.145,0.055,0.022],[0.235,0.105,0.042],[0.330,0.175,0.075]],
    lumLow: 0.018, lumHigh: 0.29, paletteSteps: 5, huePreserve: 0.20, blockiness: 4.6,
    heightBands: 10, heightMix: 0.74, heightGain: 1.18, normalStrength: 15.8,
    roughBands: [0.64,0.78,0.90], aoContrast: 1.50, cavityColor: 0.34, faceColorLift: 0.10,
  },
  sandstone: {
    palette: [[0.080,0.033,0.014],[0.160,0.072,0.025],[0.275,0.135,0.045],[0.410,0.235,0.090],[0.555,0.360,0.170]],
    lumLow: 0.045, lumHigh: 0.48, paletteSteps: 5, huePreserve: 0.18, blockiness: 5.2,
    heightBands: 10, heightMix: 0.70, heightGain: 1.14, normalStrength: 14.2,
    roughBands: [0.66,0.78,0.88], aoContrast: 1.34, cavityColor: 0.28, faceColorLift: 0.10,
  },
  limestone: {
    palette: [[0.095,0.088,0.075],[0.185,0.174,0.150],[0.300,0.286,0.250],[0.435,0.420,0.365],[0.585,0.575,0.515]],
    lumLow: 0.075, lumHigh: 0.60, paletteSteps: 5, huePreserve: 0.10, blockiness: 5.0,
    heightBands: 10, heightMix: 0.68, heightGain: 1.10, normalStrength: 13.8,
    roughBands: [0.62,0.76,0.88], aoContrast: 1.30, cavityColor: 0.24, faceColorLift: 0.08,
  },
  gravel: {
    palette: [[0.045,0.050,0.055],[0.095,0.103,0.105],[0.165,0.170,0.162],[0.265,0.255,0.230],[0.370,0.350,0.305]],
    lumLow: 0.035, lumHigh: 0.43, paletteSteps: 5, huePreserve: 0.32, blockiness: 4.4,
    heightBands: 9, heightMix: 0.76, heightGain: 1.24, normalStrength: 17.0,
    roughBands: [0.66,0.80,0.91], aoContrast: 1.44, cavityColor: 0.34, faceColorLift: 0.12,
  },
  sand: {
    palette: [[0.120,0.074,0.032],[0.230,0.150,0.067],[0.360,0.255,0.120],[0.500,0.390,0.205],[0.640,0.535,0.320]],
    lumLow: 0.10, lumHigh: 0.64, paletteSteps: 5, huePreserve: 0.10, blockiness: 6.0,
    heightBands: 9, heightMix: 0.64, heightGain: 1.08, normalStrength: 12.0,
    roughBands: [0.70,0.82,0.91], aoContrast: 1.18, cavityColor: 0.16, faceColorLift: 0.07,
  },
  wetMud: {
    palette: [[0.028,0.014,0.009],[0.060,0.029,0.016],[0.110,0.055,0.027],[0.175,0.095,0.045],[0.250,0.155,0.080]],
    lumLow: 0.018, lumHigh: 0.25, paletteSteps: 5, huePreserve: 0.14, blockiness: 5.2,
    heightBands: 9, heightMix: 0.72, heightGain: 1.15, normalStrength: 14.5,
    roughBands: [0.24,0.46,0.72], aoContrast: 1.42, cavityColor: 0.30, faceColorLift: 0.08,
  },
  woodPlank: {
    palette: [[0.055,0.022,0.010],[0.120,0.050,0.018],[0.220,0.105,0.038],[0.340,0.190,0.075],[0.470,0.300,0.135]],
    lumLow: 0.035, lumHigh: 0.46, paletteSteps: 5, huePreserve: 0.20, blockiness: 4.8,
    heightBands: 10, heightMix: 0.68, heightGain: 1.12, normalStrength: 14.5,
    roughBands: [0.54,0.68,0.82], aoContrast: 1.32, cavityColor: 0.25, faceColorLift: 0.09,
  },
  ironOre: {
    palette: [[0.025,0.029,0.034],[0.055,0.062,0.068],[0.100,0.112,0.118],[0.170,0.175,0.172],[0.255,0.245,0.225]],
    lumLow: 0.020, lumHigh: 0.28, paletteSteps: 5, huePreserve: 0.26, blockiness: 4.8,
    heightBands: 10, heightMix: 0.72, heightGain: 1.16, normalStrength: 15.0,
    roughBands: [0.36,0.55,0.76], aoContrast: 1.38, cavityColor: 0.30, faceColorLift: 0.10,
  },
  copperOre: {
    palette: [[0.028,0.031,0.034],[0.060,0.067,0.065],[0.110,0.105,0.085],[0.185,0.120,0.070],[0.300,0.175,0.090]],
    lumLow: 0.020, lumHigh: 0.32, paletteSteps: 5, huePreserve: 0.30, blockiness: 4.8,
    heightBands: 10, heightMix: 0.72, heightGain: 1.16, normalStrength: 15.0,
    roughBands: [0.32,0.52,0.74], aoContrast: 1.38, cavityColor: 0.30, faceColorLift: 0.10,
  },
  coal: {
    palette: [[0.012,0.016,0.021],[0.025,0.032,0.040],[0.050,0.060,0.069],[0.085,0.096,0.101],[0.135,0.142,0.140]],
    lumLow: 0.010, lumHigh: 0.16, paletteSteps: 5, huePreserve: 0.08, blockiness: 5.0,
    heightBands: 10, heightMix: 0.76, heightGain: 1.20, normalStrength: 15.8,
    roughBands: [0.40,0.58,0.76], aoContrast: 1.48, cavityColor: 0.35, faceColorLift: 0.11,
  },
  snow: {
    palette: [[0.440,0.500,0.575],[0.600,0.665,0.735],[0.755,0.805,0.855],[0.885,0.915,0.945],[0.970,0.980,0.990]],
    lumLow: 0.40, lumHigh: 0.99, paletteSteps: 4, huePreserve: 0.05, blockiness: 6.5,
    heightBands: 8, heightMix: 0.70, heightGain: 1.07, normalStrength: 11.5,
    roughBands: [0.70,0.82,0.92], aoContrast: 1.12, cavityColor: 0.12, faceColorLift: 0.06,
  },
  ice: {
    palette: [[0.060,0.145,0.205],[0.095,0.235,0.310],[0.150,0.345,0.420],[0.250,0.500,0.570],[0.430,0.690,0.735]],
    lumLow: 0.050, lumHigh: 0.62, paletteSteps: 5, huePreserve: 0.14, blockiness: 6.0,
    heightBands: 9, heightMix: 0.60, heightGain: 1.06, normalStrength: 10.8,
    roughBands: [0.08,0.16,0.30], aoContrast: 1.16, cavityColor: 0.13, faceColorLift: 0.07,
  },
};

function sample(tex: TextureLike, u: number, v: number, channel: number): number {
  const x = wrap01(u) * tex.width;
  const y = wrap01(v) * tex.height;
  const x0 = Math.floor(x) % tex.width;
  const y0 = Math.floor(y) % tex.height;
  const x1 = (x0 + 1) % tex.width;
  const y1 = (y0 + 1) % tex.height;
  const tx = x - Math.floor(x), ty = y - Math.floor(y);
  const at = (xx: number, yy: number) => tex.data[(yy * tex.width + xx) * tex.channels + channel];
  return lerp(lerp(at(x0,y0), at(x1,y0), tx), lerp(at(x0,y1), at(x1,y1), tx), ty);
}

function luminance(c: RGB): number { return c[0] * 0.24 + c[1] * 0.68 + c[2] * 0.08; }

function paletteAt(palette: RGB[], t: number): RGB {
  const x = clamp01(t) * (palette.length - 1);
  const i = Math.min(palette.length - 2, Math.floor(x));
  return mix(palette[i], palette[i + 1], x - i);
}

function stylizedColor(kind: CartoonKind, src: RGB, height: number, ao: number, metal: number, cfg: StyleConfig, steps: number): RGB {
  const lum = luminance(src);
  let tone = clamp01((lum - cfg.lumLow) / Math.max(1e-5, cfg.lumHigh - cfg.lumLow));
  tone = q(clamp01(tone + (height - 0.5) * cfg.faceColorLift - (1 - ao) * 0.18), steps);
  let out = paletteAt(cfg.palette, tone);

  // Preserve only broad material identity hues, never raw photographic micro-noise.
  const srcScale = Math.max(1e-4, lum);
  const targetLum = Math.max(0.01, luminance(out));
  const hue: RGB = [
    clamp01(src[0] / srcScale * targetLum),
    clamp01(src[1] / srcScale * targetLum),
    clamp01(src[2] / srcScale * targetLum),
  ];
  out = mix(out, hue, cfg.huePreserve);

  const cavity = 1 - ao;
  out = out.map((c) => clamp01(c * (1 - cavity * cfg.cavityColor))) as RGB;

  if (kind === "granite") {
    const mica = lum < 0.075;
    const feldspar = src[0] > src[1] * 1.08 && src[0] > src[2] * 1.05;
    if (mica) out = mix(out, [0.030,0.032,0.036], 0.70);
    else if (feldspar) out = mix(out, [0.335,0.190,0.175], 0.46);
    else if (lum > 0.28) out = mix(out, [0.520,0.485,0.430], 0.30);
  } else if (kind === "ironOre" && metal > 0.08) {
    const rust = src[0] > src[2] * 1.28;
    out = rust ? mix(out, [0.300,0.100,0.038], 0.62) : mix(out, [0.260,0.285,0.300], 0.70);
  } else if (kind === "copperOre" && metal > 0.06) {
    const patina = src[1] > src[0] * 1.12;
    out = patina ? mix(out, [0.055,0.300,0.235], 0.72) : mix(out, [0.470,0.175,0.060], 0.74);
  } else if (kind === "wetMud" && cavity > 0.10) {
    out = mix(out, [0.028,0.014,0.008], clamp01(cavity * 1.6));
  } else if (kind === "snow") {
    out = mix(out, [0.840,0.900,0.965], 0.28);
  } else if (kind === "ice") {
    out = mix(out, [0.075,0.330,0.440], 0.20);
  }
  return out;
}

function nearestRoughBand(value: number, bands: number[]): number {
  let best = bands[0], dist = Math.abs(value - best);
  for (let i = 1; i < bands.length; i++) {
    const d = Math.abs(value - bands[i]);
    if (d < dist) { best = bands[i]; dist = d; }
  }
  return best;
}

function stylizeFromBase(kind: CartoonKind, size: number, params: VfCartoonParams, baker: BaseBaker): Material {
  const cfg = STYLE[kind];
  const blockiness = Math.max(2.5, Math.min(9, Number(params.blockiness ?? cfg.blockiness)));
  const sourceSize = Math.max(192, Math.round(size / blockiness));
  const source = baker(sourceSize, { ...params, normalStrength: Math.min(9, Number(params.normalStrength ?? 8)) });
  if (!source.height) throw new Error(`${kind}: source material has no height map`);

  const baseColor = makeTexture(size, size, 3);
  const metallic = makeTexture(size, size, 1);
  const roughness = makeTexture(size, size, 1);
  const ao = makeTexture(size, size, 1);
  const height = makeTexture(size, size, 1);
  const emission = makeTexture(size, size, 3);
  const steps = Math.max(3, Math.min(6, Math.round(Number(params.paletteSteps ?? cfg.paletteSteps))));

  for (let y = 0; y < size; y++) {
    const v = 1 - (y + 0.5) / size;
    for (let x = 0; x < size; x++) {
      const u = (x + 0.5) / size;
      const idx = y * size + x, rgb = idx * 3;
      const src: RGB = [
        sample(source.baseColor, u, v, 0),
        sample(source.baseColor, u, v, 1),
        sample(source.baseColor, u, v, 2),
      ];
      const srcH = sample(source.height, u, v, 0);
      const srcAO = source.ao ? sample(source.ao, u, v, 0) : 1;
      const srcR = sample(source.roughness, u, v, 0);
      const srcM = sample(source.metallic, u, v, 0);

      const terraced = q(srcH, cfg.heightBands);
      let h = clamp01(0.5 + ((terraced * cfg.heightMix + srcH * (1 - cfg.heightMix)) - 0.5) * cfg.heightGain);
      const aoStrong = clamp01(1 - (1 - srcAO) * cfg.aoContrast);
      h = clamp01(h - (1 - aoStrong) * (kind === "gravel" || kind === "bark" ? 0.055 : 0.025));
      height.data[idx] = h;
      ao.data[idx] = q(aoStrong, 6);

      let m = 0;
      if (kind === "ironOre" || kind === "copperOre") {
        m = srcM > 0.11 ? 0.92 : srcM > 0.035 ? 0.58 : 0;
      }
      metallic.data[idx] = m;

      const c = stylizedColor(kind, src, h, ao.data[idx], srcM, cfg, steps);
      baseColor.data[rgb] = c[0];
      baseColor.data[rgb + 1] = c[1];
      baseColor.data[rgb + 2] = c[2];

      let r = nearestRoughBand(srcR, cfg.roughBands);
      if (kind === "wetMud") r = ao.data[idx] < 0.82 ? 0.18 : r;
      if ((kind === "ironOre" || kind === "copperOre") && m > 0.5) r = 0.28;
      if (kind === "ice") r = ao.data[idx] < 0.88 ? 0.12 : r;
      roughness.data[idx] = clamp01(r);
      emission.data[rgb] = emission.data[rgb + 1] = emission.data[rgb + 2] = 0;
    }
  }

  const normalStrength = Math.max(8, Math.min(20, Number(params.stylizedNormalStrength ?? cfg.normalStrength)));
  const normal = heightToNormal(height, normalStrength, true);
  return { baseColor, metallic, roughness, normal, ao, height, emission };
}

export const bakeVfBasaltCartoonWorld = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("basalt", size, p, bakeVfBasalt);
export const bakeVfGraniteCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("granite", size, p, bakeVfGranite);
export const bakeVfDirtCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("dirt", size, p, bakeVfDirt);
export const bakeVfBarkCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("bark", size, p, bakeVfBark);
export const bakeVfSandstoneCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("sandstone", size, p, bakeVfSandstone);
export const bakeVfLimestoneCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("limestone", size, p, bakeVfLimestone);
export const bakeVfGravelCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("gravel", size, p, bakeVfGravel);
export const bakeVfSandCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("sand", size, p, bakeVfSand);
export const bakeVfWetMudCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("wetMud", size, p, bakeVfWetMud);
export const bakeVfWoodPlankCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("woodPlank", size, p, bakeVfWoodPlank);
export const bakeVfIronOreCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("ironOre", size, p, bakeVfIronOre);
export const bakeVfCopperOreCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("copperOre", size, p, bakeVfCopperOre);
export const bakeVfCoalCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("coal", size, p, bakeVfCoal);
export const bakeVfSnowCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("snow", size, p, bakeVfSnow);
export const bakeVfIceCartoon = (size: number, p: VfCartoonParams = {}) => stylizeFromBase("ice", size, p, bakeVfIce);
