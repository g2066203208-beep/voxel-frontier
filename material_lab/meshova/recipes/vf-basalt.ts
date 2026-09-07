import {
  heightToNormal,
  makeTexture,
  type Material,
} from "../../src/index.js";

type RGB = [number, number, number];
export type VfBasaltParams = {
  seed?: number;
  fractureStrength?: number;
  poreDensity?: number;
  weathering?: number;
  roughnessBias?: number;
  normalStrength?: number;
};

const TAU = Math.PI * 2;
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (x: number) => x * x * (3 - 2 * x);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const mixRgb = (a: RGB, b: RGB, t: number): RGB => [
  lerp(a[0], b[0], t),
  lerp(a[1], b[1], t),
  lerp(a[2], b[2], t),
];

function hash01(x: number, y: number, seed: number, salt = 0): number {
  let h = Math.imul(x | 0, 0x1f123bb5)
    ^ Math.imul(y | 0, 0x5f356495)
    ^ Math.imul(seed | 0, 0x2c9277b5)
    ^ Math.imul(salt | 0, 0x27d4eb2d);
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d);
  h = Math.imul(h ^ (h >>> 12), 0x297a2d39);
  h ^= h >>> 15;
  return (h >>> 0) / 0xffffffff;
}

function pnoise(u: number, v: number, frequency: number, seed: number): number {
  const f = Math.max(1, frequency | 0);
  const px = u * f;
  const py = v * f;
  const x0 = Math.floor(px);
  const y0 = Math.floor(py);
  const tx = smooth(px - x0);
  const ty = smooth(py - y0);
  const wrap = (n: number) => ((n % f) + f) % f;
  const ax = wrap(x0);
  const bx = wrap(x0 + 1);
  const ay = wrap(y0);
  const by = wrap(y0 + 1);
  const n00 = hash01(ax, ay, seed);
  const n10 = hash01(bx, ay, seed);
  const n01 = hash01(ax, by, seed);
  const n11 = hash01(bx, by, seed);
  return lerp(lerp(n00, n10, tx), lerp(n01, n11, tx), ty);
}

function pfbm(u: number, v: number, base: number, octaves: number, seed: number): number {
  let sum = 0;
  let weight = 0;
  let amplitude = 1;
  for (let octave = 0; octave < octaves; octave++) {
    const frequency = Math.max(1, Math.round(base * 2 ** octave));
    sum += pnoise(u, v, frequency, seed + octave * 101) * amplitude;
    weight += amplitude;
    amplitude *= 0.5;
  }
  return sum / weight;
}

function sparsePores(u: number, v: number, seed: number, density: number): number {
  const cells = 28;
  const px = u * cells;
  const py = v * cells;
  const baseX = Math.floor(px);
  const baseY = Math.floor(py);
  let mask = 0;
  for (let oy = -1; oy <= 1; oy++) {
    for (let ox = -1; ox <= 1; ox++) {
      const cx = baseX + ox;
      const cy = baseY + oy;
      const wx = ((cx % cells) + cells) % cells;
      const wy = ((cy % cells) + cells) % cells;
      if (hash01(wx, wy, seed, 1) >= density) continue;
      const jx = 0.5 + (hash01(wx, wy, seed, 2) - 0.5) * 0.76;
      const jy = 0.5 + (hash01(wx, wy, seed, 3) - 0.5) * 0.76;
      const radius = 0.075 + hash01(wx, wy, seed, 4) * 0.105;
      const aspect = 0.55 + hash01(wx, wy, seed, 5) * 0.5;
      const angle = hash01(wx, wy, seed, 6) * TAU;
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);
      const dx = px - cx - jx;
      const dy = py - cy - jy;
      const rx = dx * cosine - dy * sine;
      const ry = dx * sine + dy * cosine;
      const d = Math.hypot(rx / radius, ry / (radius * aspect));
      const pore = 1 - smooth(clamp01((d - 0.48) / 0.52));
      if (pore > mask) mask = pore;
    }
  }
  return mask;
}

function makeSampler(params: VfBasaltParams) {
  const seed = Math.round(params.seed ?? 240911);
  const fractureStrength = clamp01(params.fractureStrength ?? 0.42);
  const poreDensity = Math.max(0, Math.min(0.1, params.poreDensity ?? 0.015));
  const weathering = clamp01(params.weathering ?? 0.22);
  const roughnessBias = Math.max(-0.18, Math.min(0.18, params.roughnessBias ?? 0.015));
  const normalStrength = Math.max(0.2, Math.min(10, params.normalStrength ?? 5.0));

  const sample = (u: number, v: number) => {
    const warpU = (pfbm(u, v, 2, 3, seed + 11) - 0.5) * 0.095;
    const warpV = (pfbm(u, v, 2, 3, seed + 23) - 0.5) * 0.095;
    const du = u + warpU;
    const dv = v + warpV;

    const macro = pfbm(du, dv, 2, 4, seed + 101);
    const meso = pfbm(du, dv, 8, 3, seed + 211);
    const micro = pfbm(du, dv, 36, 2, seed + 307);
    const grain = pnoise(du, dv, 112, seed + 401);
    const fineGrain = pnoise(du, dv, 181, seed + 409);

    // Shorter, thinner, more fragmented cracks than V04's long mathematical curves.
    const bendA = (pnoise(du, dv, 7, seed + 503) - 0.5) * 2.15;
    const bendB = (pnoise(du, dv, 11, seed + 509) - 0.5) * 1.85;
    const phaseA = hash01(1, 1, seed, 10) * TAU;
    const phaseB = hash01(2, 2, seed, 11) * TAU;
    const fieldA = Math.sin((du * 4.2 + dv * 2.35) * TAU + phaseA + bendA)
      + 0.32 * Math.sin((-du * 2.1 + dv * 5.4) * TAU + phaseB);
    const fieldB = Math.sin((du * 6.1 - dv * 3.65) * TAU + phaseB * 0.73 + bendB);
    const rawA = 1 - smooth(clamp01((Math.abs(fieldA) - 0.008) / 0.058));
    const rawB = 1 - smooth(clamp01((Math.abs(fieldB) - 0.006) / 0.045));
    const gateA = smooth(clamp01((pnoise(du, dv, 6, seed + 601) - 0.52) / 0.21));
    const gateB = smooth(clamp01((pnoise(du, dv, 9, seed + 607) - 0.56) / 0.2));

    // Fine discontinuous weathering fissures follow a noisy contour instead of a periodic sine.
    const contour = Math.abs(pfbm(du, dv, 14, 2, seed + 613) - 0.5);
    const rawC = 1 - smooth(clamp01((contour - 0.004) / 0.026));
    const gateC = smooth(clamp01((pnoise(du, dv, 10, seed + 617) - 0.62) / 0.18));
    const fracture = clamp01(
      Math.max(rawA * gateA, rawB * gateB * 0.62, rawC * gateC * 0.32) * fractureStrength,
    );

    const pores = sparsePores(du, dv, seed + 701, poreDensity);
    const pinholes = smooth(clamp01((pnoise(du, dv, 90, seed + 809) - 0.86) / 0.1)) * 0.18;

    const height = clamp01(
      0.5
      + (macro - 0.5) * 0.4
      + (meso - 0.5) * 0.17
      + (micro - 0.5) * 0.06
      + (grain - 0.5) * 0.022
      + (fineGrain - 0.5) * 0.008
      - fracture * 0.14
      - pores * 0.2
      - pinholes * 0.018,
    );

    const tone = clamp01(0.22 + macro * 0.5 + meso * 0.2 + micro * 0.08);
    let color = mixRgb([0.06, 0.064, 0.067], [0.195, 0.2, 0.195], tone);
    const oxideGate = smooth(clamp01((pnoise(du, dv, 6, seed + 907) - 0.56) / 0.23));
    const oxide = clamp01((fracture * oxideGate + pores * 0.22) * weathering * 0.25);
    color = mixRgb(color, [0.255, 0.15, 0.082], oxide);
    const dark = clamp01(1 - fracture * 0.22 - pores * 0.32 - pinholes * 0.05);
    const mineral = 0.94 + grain * 0.08 + fineGrain * 0.035;
    color = [
      clamp01(color[0] * dark * mineral),
      clamp01(color[1] * dark * mineral),
      clamp01(color[2] * dark * mineral),
    ];

    const roughness = clamp01(
      0.7 + roughnessBias
      + (micro - 0.5) * 0.15
      + (grain - 0.5) * 0.08
      + fracture * 0.11
      + pores * 0.15
      + pinholes * 0.05
      - height * 0.035,
    );
    const ao = clamp01(1 - fracture * 0.25 - pores * 0.48 - pinholes * 0.08);
    return { color, height, roughness, ao };
  };
  return { sample, normalStrength };
}

export function bakeVfBasalt(size: number, params: VfBasaltParams = {}): Material {
  const { sample, normalStrength } = makeSampler(params);
  const baseColor = makeTexture(size, size, 3);
  const metallic = makeTexture(size, size, 1);
  const roughness = makeTexture(size, size, 1);
  const ao = makeTexture(size, size, 1);
  const height = makeTexture(size, size, 1);
  const emission = makeTexture(size, size, 3);

  for (let y = 0; y < size; y++) {
    const v = 1 - (y + 0.5) / size;
    for (let x = 0; x < size; x++) {
      const u = (x + 0.5) / size;
      const s = sample(u, v);
      const scalar = y * size + x;
      const rgb = scalar * 3;
      baseColor.data[rgb] = s.color[0];
      baseColor.data[rgb + 1] = s.color[1];
      baseColor.data[rgb + 2] = s.color[2];
      roughness.data[scalar] = s.roughness;
      ao.data[scalar] = s.ao;
      height.data[scalar] = s.height;
    }
  }

  const normal = heightToNormal(height, normalStrength, true);
  return { baseColor, metallic, roughness, normal, ao, height, emission };
}
