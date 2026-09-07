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

type CrackSegment = {
  cx: number;
  cy: number;
  dx: number;
  dy: number;
  halfLength: number;
  width: number;
  strength: number;
};

const TAU = Math.PI * 2;
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (x: number) => x * x * (3 - 2 * x);
const smootherstep = (x: number) => {
  const t = clamp01(x);
  return t * t * t * (t * (t * 6 - 15) + 10);
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const wrap01 = (x: number) => x - Math.floor(x);
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
  const tx = smootherstep(px - x0);
  const ty = smootherstep(py - y0);
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
  return sum / Math.max(weight, 1e-6);
}

function sparsePores(u: number, v: number, seed: number, density: number): number {
  const cells = 24;
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
      const jx = 0.5 + (hash01(wx, wy, seed, 2) - 0.5) * 0.78;
      const jy = 0.5 + (hash01(wx, wy, seed, 3) - 0.5) * 0.78;
      const radius = 0.10 + hash01(wx, wy, seed, 4) * 0.18;
      const aspect = 0.48 + hash01(wx, wy, seed, 5) * 0.52;
      const angle = hash01(wx, wy, seed, 6) * TAU;
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);
      const dx = px - cx - jx;
      const dy = py - cy - jy;
      const rx = dx * cosine - dy * sine;
      const ry = dx * sine + dy * cosine;
      const d = Math.hypot(rx / radius, ry / (radius * aspect));
      const pore = 1 - smooth(clamp01((d - 0.42) / 0.58));
      if (pore > mask) mask = pore;
    }
  }
  return mask;
}

function makeSegment(cx: number, cy: number, angle: number, halfLength: number, width: number, strength: number): CrackSegment {
  return {
    cx: wrap01(cx),
    cy: wrap01(cy),
    dx: Math.cos(angle),
    dy: Math.sin(angle),
    halfLength,
    width,
    strength,
  };
}

function buildFractures(seed: number): CrackSegment[] {
  const segments: CrackSegment[] = [];
  const primary: CrackSegment[] = [];

  // Basalt commonly shows preferred joint families rather than an isotropic closed-cell web.
  for (let i = 0; i < 7; i++) {
    const familyAngle = i % 2 === 0 ? 0.30 : 1.83;
    const jitter = (hash01(i, 1, seed, 100) - 0.5) * 0.62;
    const angle = familyAngle + jitter;
    const segment = makeSegment(
      hash01(i, 2, seed, 101),
      hash01(i, 3, seed, 102),
      angle,
      0.085 + hash01(i, 4, seed, 103) * 0.085,
      0.0018 + hash01(i, 5, seed, 104) * 0.0021,
      0.72 + hash01(i, 6, seed, 105) * 0.28,
    );
    primary.push(segment);
    segments.push(segment);
  }

  // Branches start near primary endpoints and diverge at realistic angles.
  for (let i = 0; i < 9; i++) {
    const parent = primary[i % primary.length];
    const side = hash01(i, 7, seed, 110) < 0.5 ? -1 : 1;
    const attach = 0.58 + hash01(i, 8, seed, 111) * 0.34;
    const px = parent.cx + parent.dx * parent.halfLength * side * attach;
    const py = parent.cy + parent.dy * parent.halfLength * side * attach;
    const parentAngle = Math.atan2(parent.dy, parent.dx);
    const diverge = (0.42 + hash01(i, 9, seed, 112) * 0.55) * (hash01(i, 10, seed, 113) < 0.5 ? -1 : 1);
    segments.push(makeSegment(
      px + (hash01(i, 11, seed, 114) - 0.5) * 0.018,
      py + (hash01(i, 12, seed, 115) - 0.5) * 0.018,
      parentAngle + diverge,
      0.030 + hash01(i, 13, seed, 116) * 0.052,
      0.0010 + hash01(i, 14, seed, 117) * 0.0012,
      0.38 + hash01(i, 15, seed, 118) * 0.34,
    ));
  }

  // Very fine isolated fissures enrich close-up normal/height without dominating the tile.
  for (let i = 0; i < 10; i++) {
    const familyAngle = i % 2 === 0 ? 0.28 : 1.88;
    const angle = familyAngle + (hash01(i, 16, seed, 120) - 0.5) * 0.95;
    segments.push(makeSegment(
      hash01(i, 17, seed, 121),
      hash01(i, 18, seed, 122),
      angle,
      0.018 + hash01(i, 19, seed, 123) * 0.035,
      0.00055 + hash01(i, 20, seed, 124) * 0.00070,
      0.16 + hash01(i, 21, seed, 125) * 0.18,
    ));
  }
  return segments;
}

function segmentMask(u: number, v: number, segment: CrackSegment): number {
  let rx = u - segment.cx;
  let ry = v - segment.cy;
  rx -= Math.round(rx);
  ry -= Math.round(ry);

  const along = rx * segment.dx + ry * segment.dy;
  const cross = Math.abs(-rx * segment.dy + ry * segment.dx);
  const endStart = segment.halfLength * 0.72;
  const endFade = Math.max(segment.halfLength - endStart, 1e-5);
  const alongMask = 1 - smooth(clamp01((Math.abs(along) - endStart) / endFade));
  const crossMask = 1 - smooth(clamp01((cross - segment.width * 0.18) / (segment.width * 0.82)));
  return clamp01(alongMask * crossMask * segment.strength);
}

function makeSampler(params: VfBasaltParams) {
  const seed = Math.round(params.seed ?? 240912);
  const fractureStrength = clamp01(params.fractureStrength ?? 0.50);
  const poreDensity = Math.max(0, Math.min(0.12, params.poreDensity ?? 0.020));
  const weathering = clamp01(params.weathering ?? 0.22);
  const roughnessBias = Math.max(-0.18, Math.min(0.18, params.roughnessBias ?? 0.015));
  const normalStrength = Math.max(0.2, Math.min(10, params.normalStrength ?? 5.2));
  const fractures = buildFractures(seed + 5000);

  const sample = (u: number, v: number) => {
    const warpU = (pfbm(u, v, 2, 3, seed + 11) - 0.5) * 0.075;
    const warpV = (pfbm(u, v, 2, 3, seed + 23) - 0.5) * 0.075;
    const du = wrap01(u + warpU);
    const dv = wrap01(v + warpV);

    const macro = pfbm(du, dv, 2, 4, seed + 101);
    const meso = pfbm(du, dv, 8, 3, seed + 211);
    const micro = pfbm(du, dv, 30, 2, seed + 307);
    const grain = pnoise(du, dv, 92, seed + 401);
    const microGrain = pnoise(du, dv, 157, seed + 409);

    let fracture = 0;
    for (const segment of fractures) {
      const value = segmentMask(du, dv, segment);
      if (value > fracture) fracture = value;
    }
    fracture = clamp01(fracture * fractureStrength);

    const pores = sparsePores(du, dv, seed + 701, poreDensity);
    const microPitA = smooth(clamp01((pnoise(du, dv, 73, seed + 809) - 0.835) / 0.10));
    const microPitB = smooth(clamp01((pnoise(du, dv, 137, seed + 811) - 0.885) / 0.075));
    const pinholes = clamp01(microPitA * 0.30 + microPitB * 0.22);

    const brightMineral = smooth(clamp01((grain - 0.84) / 0.13))
      * smooth(clamp01((microGrain - 0.58) / 0.30));
    const darkMineral = smooth(clamp01((0.17 - grain) / 0.14)) * 0.75;

    const height = clamp01(
      0.50
      + (macro - 0.5) * 0.42
      + (meso - 0.5) * 0.20
      + (micro - 0.5) * 0.065
      + (grain - 0.5) * 0.022
      + (microGrain - 0.5) * 0.009
      + brightMineral * 0.010
      - darkMineral * 0.008
      - fracture * 0.30
      - pores * 0.30
      - pinholes * 0.030,
    );

    const tone = clamp01(0.11 + macro * 0.50 + meso * 0.24 + micro * 0.10 + grain * 0.05);
    let color = mixRgb([0.034, 0.038, 0.042], [0.180, 0.186, 0.182], tone);
    color = mixRgb(color, [0.255, 0.262, 0.252], brightMineral * 0.16);
    color = mixRgb(color, [0.018, 0.022, 0.026], darkMineral * 0.30);

    const oxideGate = smooth(clamp01((pnoise(du, dv, 5, seed + 907) - 0.50) / 0.25));
    const oxide = clamp01((fracture * oxideGate + pores * 0.22) * weathering * 0.28);
    color = mixRgb(color, [0.245, 0.132, 0.066], oxide);

    const cavityDark = clamp01(1 - fracture * 0.34 - pores * 0.50 - pinholes * 0.09);
    const grainTone = 0.955 + grain * 0.075 + microGrain * 0.025;
    color = [
      clamp01(color[0] * cavityDark * grainTone),
      clamp01(color[1] * cavityDark * grainTone),
      clamp01(color[2] * cavityDark * grainTone),
    ];

    const roughness = clamp01(
      0.70 + roughnessBias
      + (micro - 0.5) * 0.17
      + (microGrain - 0.5) * 0.08
      + fracture * 0.18
      + pores * 0.21
      + pinholes * 0.09
      + darkMineral * 0.05
      - brightMineral * 0.10
      - height * 0.035,
    );
    const ao = clamp01(1 - fracture * 0.42 - pores * 0.62 - pinholes * 0.13);
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
