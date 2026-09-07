import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB = [number, number, number];

export type VfLayeredSandstoneParams = {
  seed?: number;
  bands?: number;
  minSlabs?: number;
  maxSlabs?: number;
  crackChance?: number;
  chipStrength?: number;
  relief?: number;
  normalStrength?: number;
};

type Slab = {
  cx: number;
  cy: number;
  hw: number;
  hh: number;
  angle: number;
  base: number;
  bulge: number;
  tiltX: number;
  tiltY: number;
  hue: number;
  warm: number;
  supports: number[];
  facets: number[];
  crack: boolean;
  crackX: number;
  crackTilt: number;
  crackY0: number;
  crackY1: number;
  chipX: number;
  chipY: number;
  chipX2: number;
  chipY2: number;
  chip: number;
  strata: number[];
  macro: boolean;
  brushX: number;
  brushY: number;
  brushSign: number;
};

const TAU = Math.PI * 2;
const C = (x: number) => Math.max(0, Math.min(1, x));
const L = (a: number, b: number, t: number) => a + (b - a) * t;
const M = (a: RGB, b: RGB, t: number): RGB => [
  L(a[0], b[0], t),
  L(a[1], b[1], t),
  L(a[2], b[2], t),
];
const S = (x: number) => {
  const t = C(x);
  return t * t * (3 - 2 * t);
};
const G = (x: number) => Math.exp(-(x * x));

function wrapDelta(x: number) {
  return x - Math.round(x);
}

function hash(seed: number, a: number, b = 0, c = 0) {
  let h =
    (seed | 0) ^
    Math.imul((a | 0) + 0x9e3779b9, 0x85ebca6b) ^
    Math.imul((b | 0) + 0x7f4a7c15, 0xc2b2ae35) ^
    Math.imul((c | 0) + 0x165667b1, 0x27d4eb2d);
  h = Math.imul(h ^ (h >>> 16), 0x7feb352d);
  h = Math.imul(h ^ (h >>> 15), 0x846ca68b);
  h ^= h >>> 16;
  return (h >>> 0) / 0xffffffff;
}

function fbm(u: number, v: number, seed: number) {
  let sum = 0;
  let amp = 0.55;
  let norm = 0;
  let f = 1;
  for (let i = 0; i < 3; i++) {
    const x = Math.floor(u * f * 13);
    const y = Math.floor(v * f * 13);
    sum += (hash(seed, x, y, i) * 2 - 1) * amp;
    norm += amp;
    amp *= 0.5;
    f *= 2.03;
  }
  return sum / Math.max(norm, 1e-6);
}

function qBand(y: number, center: number, width: number) {
  return G((y - center) / Math.max(width, 1e-5));
}

function palette(t: number, warm: number): RGB {
  const shadow: RGB = [0.155, 0.052, 0.026];
  const mid: RGB = [0.4, 0.165, 0.062];
  const light: RGB = [0.675, 0.365, 0.145];
  const cream: RGB = [0.91, 0.625, 0.3];
  const c = t < 0.5 ? M(shadow, mid, S(t / 0.5)) : M(mid, light, S((t - 0.5) / 0.5));
  return M(c, cream, C(warm) * 0.27);
}

function makeSlab(
  seed: number,
  row: number,
  index: number,
  cx: number,
  cy: number,
  hw: number,
  hh: number,
  base: number,
  bulge: number,
  crackChance: number,
  macro: boolean,
): Slab {
  const supports: number[] = [];
  const supportCount = 12;
  for (let k = 0; k < supportCount; k++) {
    const lo = macro ? 0.58 : 0.66;
    const span = macro ? 0.66 : 0.54;
    supports.push(lo + hash(seed, row, index, 30 + k) * span);
  }

  const facets: number[] = [];
  for (let k = 0; k < 8; k++) facets.push(hash(seed, row, index, 50 + k) - 0.5);

  const strataCount = 1 + Math.floor(hash(seed, row, index, 70) * 3);
  const strata: number[] = [];
  for (let k = 0; k < strataCount; k++) {
    strata.push(-0.48 + hash(seed, row, index, 71 + k) * 0.96);
  }

  return {
    cx: (cx + 2) % 1,
    cy: (cy + 2) % 1,
    hw,
    hh,
    angle: (hash(seed, row, index, 10) - 0.5) * (macro ? 0.22 : 0.16),
    base,
    bulge,
    tiltX: (hash(seed, row, index, 11) - 0.5) * (macro ? 0.085 : 0.055),
    tiltY: (hash(seed, row, index, 12) - 0.5) * (macro ? 0.075 : 0.048),
    hue: (hash(seed, row, index, 13) - 0.5) * 0.14,
    warm: hash(seed, row, index, 14),
    supports,
    facets,
    crack: hash(seed, row, index, 15) < crackChance,
    crackX: (hash(seed, row, index, 16) - 0.5) * 0.42,
    crackTilt: (hash(seed, row, index, 17) - 0.5) * 0.23,
    crackY0: -0.65 + hash(seed, row, index, 18) * 0.31,
    crackY1: 0.31 + hash(seed, row, index, 19) * 0.43,
    chipX: (hash(seed, row, index, 20) < 0.5 ? -1 : 1) * (0.52 + hash(seed, row, index, 21) * 0.31),
    chipY: (hash(seed, row, index, 22) - 0.5) * 1.35,
    chipX2: (hash(seed, row, index, 27) < 0.5 ? -1 : 1) * (0.57 + hash(seed, row, index, 28) * 0.26),
    chipY2: (hash(seed, row, index, 29) - 0.5) * 1.28,
    chip: hash(seed, row, index, 23),
    strata,
    macro,
    brushX: (hash(seed, row, index, 24) - 0.5) * 0.52,
    brushY: (hash(seed, row, index, 25) - 0.5) * 0.7,
    brushSign: hash(seed, row, index, 26) < 0.5 ? -1 : 1,
  };
}

function buildSlabs(
  seed: number,
  rows: number,
  minSlabs: number,
  maxSlabs: number,
  crackChance: number,
): Slab[] {
  const slabs: Slab[] = [];
  const rowStep = 1 / rows;

  // Attached support slabs close background gaps without creating detached debris.
  for (let row = 0; row < rows; row++) {
    const count = minSlabs + Math.floor(hash(seed, row, 100) * (maxSlabs - minSlabs + 1));
    const raw: number[] = [];
    let total = 0;
    for (let i = 0; i < count; i++) {
      const w = 0.75 + hash(seed, row, i, 101) * 1.05;
      raw.push(w);
      total += w;
    }

    let cursor = hash(seed, row, 102) * 0.16 - 0.08;
    for (let i = 0; i < count; i++) {
      const fraction = raw[i] / total;
      const cx = cursor + fraction * 0.5;
      cursor += fraction;
      const hh = rowStep * (0.43 + hash(seed, row, i, 103) * 0.2);
      slabs.push(
        makeSlab(
          seed,
          row,
          i,
          cx,
          (row + 0.5) / rows + (hash(seed, row, i, 104) - 0.5) * rowStep * 0.38,
          (fraction + 0.03) * 0.56,
          hh,
          0.4 + (hash(seed, row, i, 105) - 0.5) * 0.035,
          0.03 + hash(seed, row, i, 106) * 0.035,
          crackChance * 0.35,
          false,
        ),
      );
    }
  }

  // Primary boulders define the macro silhouette and sculpted plane hierarchy.
  const primary: [number, number, number, number, number, number][] = [
    [0.575, 0.5, 0.205, 0.165, 0.585, 0.155],
    [0.315, 0.445, 0.165, 0.15, 0.545, 0.135],
    [0.805, 0.44, 0.155, 0.155, 0.535, 0.128],
    [0.405, 0.665, 0.175, 0.145, 0.545, 0.135],
    [0.705, 0.675, 0.17, 0.145, 0.535, 0.128],
    [0.175, 0.625, 0.125, 0.155, 0.515, 0.115],
    [0.57, 0.295, 0.16, 0.12, 0.53, 0.12],
    [0.35, 0.27, 0.125, 0.11, 0.5, 0.1],
    [0.79, 0.255, 0.12, 0.105, 0.495, 0.1],
    [0.56, 0.82, 0.155, 0.105, 0.5, 0.105],
    [0.285, 0.8, 0.115, 0.095, 0.485, 0.095],
    [0.805, 0.805, 0.115, 0.095, 0.49, 0.095],
  ];

  for (let i = 0; i < primary.length; i++) {
    const [ax, ay, hw, hh, base, bulge] = primary[i];
    slabs.push(
      makeSlab(
        seed,
        90,
        i,
        ax + (hash(seed, 90, i, 1) - 0.5) * 0.035,
        ay + (hash(seed, 90, i, 2) - 0.5) * 0.035,
        hw * (0.91 + hash(seed, 90, i, 3) * 0.18),
        hh * (0.91 + hash(seed, 90, i, 4) * 0.18),
        base + (hash(seed, 90, i, 5) - 0.5) * 0.03,
        bulge * (0.91 + hash(seed, 90, i, 6) * 0.2),
        crackChance * (i === 0 ? 1.55 : 0.92),
        true,
      ),
    );
  }

  return slabs;
}

function slabShape(x: number, y: number, slab: Slab, seed: number, index: number) {
  let polygon = -99;
  const count = slab.supports.length;
  for (let k = 0; k < count; k++) {
    const angle = (k * TAU) / count;
    const d = (x * Math.cos(angle) + y * Math.sin(angle)) / slab.supports[k];
    if (d > polygon) polygon = d;
  }
  const radial = Math.sqrt(x * x * 0.7 + y * y * 0.92);
  return (
    Math.max(polygon, radial * 0.82) +
    fbm(x * 0.72 + index * 0.09, y * 0.72 - index * 0.07, seed + index * 19) * 0.028
  );
}

export function bakeVfLayeredSandstonePainted(
  size: number,
  p: VfLayeredSandstoneParams = {},
): Material {
  const seed = Math.floor(p.seed ?? 771231);
  const rows = Math.max(5, Math.min(8, Math.floor(p.bands ?? 5)));
  const minSlabs = Math.max(2, Math.floor(p.minSlabs ?? 2));
  const maxSlabs = Math.max(minSlabs, Math.floor(p.maxSlabs ?? 3));
  const crackChance = C(p.crackChance ?? 0.2);
  const chipStrength = C(p.chipStrength ?? 0.88);
  const relief = Math.max(0.5, Math.min(1.75, p.relief ?? 1.46));
  const normalStrength = Math.max(1, Math.min(20, p.normalStrength ?? 11.5));
  const slabs = buildSlabs(seed, rows, minSlabs, maxSlabs, crackChance);

  const baseColor = makeTexture(size, size, 3);
  const metallic = makeTexture(size, size, 1);
  const roughness = makeTexture(size, size, 1);
  const ao = makeTexture(size, size, 1);
  const height = makeTexture(size, size, 1);
  const emission = makeTexture(size, size, 3);

  for (let py = 0; py < size; py++) {
    const v = 1 - (py + 0.5) / size;
    for (let px = 0; px < size; px++) {
      const u = (px + 0.5) / size;
      let bestH = 0.395 + fbm(u * 0.35, v * 0.35, seed + 701) * 0.008;
      let secondH = 0.375;
      let best = -1;
      let bestEdge = 0;
      let bestCrack = 0;
      let bestChip = 0;
      let bestStrata = 0;
      let bx = 0;
      let by = 0;
      let bestFacetTone = 0;
      let bestRidge = 0;
      let bestUnder = 0;

      for (let si = 0; si < slabs.length; si++) {
        const slab = slabs[si];
        const dx = wrapDelta(u - slab.cx);
        const dy = wrapDelta(v - slab.cy);
        const ca = Math.cos(slab.angle);
        const sa = Math.sin(slab.angle);
        const rx = dx * ca + dy * sa;
        const ry = -dx * sa + dy * ca;
        if (Math.abs(rx) > slab.hw * 1.35 || Math.abs(ry) > slab.hh * 1.38) continue;

        const x = rx / Math.max(slab.hw, 1e-5);
        const y = ry / Math.max(slab.hh, 1e-5);
        const q = slabShape(x, y, slab, seed, si);
        if (q > 1.045) continue;

        const bevelWidth = slab.macro ? 0.245 : 0.19;
        const edge = S((1 - q) / bevelWidth);
        const dome = Math.max(0, 1 - Math.sqrt(x * x * 0.52 + y * y * 0.78));
        const planes = [
          slab.facets[0] * x + slab.facets[1] * y + 0.03,
          slab.facets[2] * x + slab.facets[3] * y - 0.018,
          slab.facets[4] * x + slab.facets[5] * y + 0.052,
          slab.facets[6] * x + slab.facets[7] * y - 0.046,
        ];

        let pTop = -99;
        let pSecond = -99;
        for (const plane of planes) {
          if (plane > pTop) {
            pSecond = pTop;
            pTop = plane;
          } else if (plane > pSecond) {
            pSecond = plane;
          }
        }

        const facetAmp = slab.macro ? 0.105 : 0.045;
        const facet = pTop * facetAmp;
        const ridge = 1 - S((pTop - pSecond) / (slab.macro ? 0.085 : 0.065));
        const topLip = G((y - 0.58) / 0.2) * edge;
        const under = G((y + 0.67) / 0.15) * edge;
        const broadUndulation =
          fbm(x * 0.34 + slab.cx, y * 0.34 + slab.cy, seed + si * 43) *
          (0.012 + (slab.macro ? 0.01 : 0));

        let surf =
          slab.base +
          slab.bulge * (0.12 + 0.65 * edge + 0.23 * dome) +
          slab.tiltX * x +
          slab.tiltY * y +
          facet +
          broadUndulation;
        surf += topLip * (slab.macro ? 0.025 : 0.01);
        surf -= under * (slab.macro ? 0.058 : 0.024);
        surf -= (1 - edge) * (slab.macro ? 0.04 : 0.022);

        let crack = 0;
        if (slab.crack) {
          const lineX =
            slab.crackX + slab.crackTilt * y + fbm(u * 1.2, v * 1.2, seed + si * 31) * 0.018;
          const yr = S((y - slab.crackY0) / 0.18) * S((slab.crackY1 - y) / 0.18);
          crack = G((x - lineX) / (slab.macro ? 0.023 : 0.03)) * yr;
          surf -= crack * (slab.macro ? 0.112 : 0.065) * relief;
        }

        const chip1 =
          slab.chip > 0.42
            ? G((x - slab.chipX) / (slab.macro ? 0.15 : 0.18)) *
              G((y - slab.chipY) / (slab.macro ? 0.18 : 0.22))
            : 0;
        const chip2 =
          slab.chip > 0.72
            ? G((x - slab.chipX2) / (slab.macro ? 0.13 : 0.17)) *
              G((y - slab.chipY2) / (slab.macro ? 0.16 : 0.2))
            : 0;
        const chip = (chip1 + chip2 * 0.42) * chipStrength;
        surf -= chip * (slab.macro ? 0.078 : 0.045);

        let strata = 0;
        for (let k = 0; k < slab.strata.length; k++) {
          const pos = slab.strata[k] + Math.sin((x * 0.42 + k * 0.31 + slab.warm) * TAU) * 0.018;
          const gate = G((x - (hash(seed, si, k, 300) - 0.5) * 0.3) / 0.78);
          strata += qBand(y, pos, 0.013 + 0.004 * k) * gate;
        }
        surf += strata * 0.0035;

        surf = 0.5 + (surf - 0.5) * relief;
        if (surf > bestH) {
          secondH = bestH;
          bestH = surf;
          best = si;
          bestEdge = edge;
          bestCrack = crack;
          bestChip = chip;
          bestStrata = strata;
          bx = x;
          by = y;
          bestFacetTone = pTop;
          bestRidge = ridge;
          bestUnder = under;
        } else if (surf > secondH) {
          secondH = surf;
        }
      }

      let col: RGB = [0.285, 0.105, 0.04];
      let r = 0.88;
      let a = 0.8;

      if (best >= 0) {
        const slab = slabs[best];
        const overlap = C((bestH - secondH) / 0.085);
        const cavity = C(
          (1 - bestEdge) * 0.4 +
            bestCrack * 0.94 +
            bestChip * 0.52 +
            (1 - overlap) * 0.1 +
            bestUnder * 0.46,
        );
        const t = C(0.43 + slab.hue + (bestH - 0.43) + (1 - by) * 0.04 + bestFacetTone * 0.28);
        col = palette(t, slab.warm * 0.38 + bestEdge * 0.12);

        const planeWarm = C(0.5 + bestFacetTone * 1.9 - by * 0.28);
        col = M(col, [0.94, 0.665, 0.325], planeWarm * 0.11 * bestEdge);
        col = M(col, [0.235, 0.082, 0.032], C(0.5 - planeWarm) * 0.13 * bestEdge);
        col = M(col, [0.975, 0.75, 0.42], bestRidge * 0.055 * bestEdge);
        col = M(col, [0.105, 0.022, 0.008], cavity * 0.7);
        col = M(col, [0.985, 0.815, 0.515], C(bestStrata * 0.1));
        col = M(col, [0.065, 0.01, 0.004], bestCrack * 0.97);

        const brush = G((bx - slab.brushX) / 0.62) * G((by - slab.brushY) / 0.095) * bestEdge;
        col = M(
          col,
          slab.brushSign > 0 ? [0.91, 0.55, 0.245] : [0.275, 0.075, 0.025],
          brush * 0.06,
        );
        const wash = fbm((u + slab.cx) * 0.53, (v + slab.cy) * 0.41, seed + 907 + best * 13);
        col = M(
          col,
          wash > 0 ? [0.69, 0.325, 0.115] : [0.28, 0.075, 0.026],
          Math.abs(wash) * 0.055 * bestEdge,
        );

        r = Math.max(
          0.04,
          Math.min(
            1,
            0.68 +
              (1 - bestEdge) * 0.12 +
              bestCrack * 0.22 +
              bestChip * 0.1 +
              Math.abs(wash) * 0.023 -
              bestStrata * 0.02,
          ),
        );
        a = C(1 - cavity * 0.43 - bestUnder * 0.1 - bestStrata * 0.01);
      }

      const i = py * size + px;
      const j = i * 3;
      baseColor.data[j] = C(col[0]);
      baseColor.data[j + 1] = C(col[1]);
      baseColor.data[j + 2] = C(col[2]);
      height.data[i] = C(bestH);
      roughness.data[i] = r;
      ao.data[i] = a;
      metallic.data[i] = 0;
    }
  }

  const normal = heightToNormal(height, normalStrength, true);
  return { baseColor, metallic, roughness, normal, ao, height, emission };
}
