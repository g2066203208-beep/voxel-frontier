import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

type RGB = [number, number, number];
export type VfPainterlyCommonParams = { seed?: number; normalStrength?: number; relief?: number };
export type VfPainterlyDirtParams = VfPainterlyCommonParams & { moisture?: number };
export type VfPainterlyBarkParams = VfPainterlyCommonParams & { ridgeScale?: number };
export type VfPainterlyLeavesParams = VfPainterlyCommonParams & { density?: number };
export type VfPainterlySnowParams = VfPainterlyCommonParams & { windStrength?: number };
export type VfPainterlyWaterParams = VfPainterlyCommonParams & { waveScale?: number; roughness?: number };

const TAU = Math.PI * 2;
const C = (x: number) => Math.max(0, Math.min(1, x));
const L = (a: number, b: number, t: number) => a + (b - a) * t;
const M = (a: RGB, b: RGB, t: number): RGB => [L(a[0], b[0], t), L(a[1], b[1], t), L(a[2], b[2], t)];
const S = (x: number) => { const t = C(x); return t * t * (3 - 2 * t); };
const G = (x: number) => Math.exp(-(x * x));
function hash(seed: number, a: number, b = 0, c = 0) {
  let h = (seed | 0) ^ Math.imul((a | 0) + 0x9e3779b9, 0x85ebca6b) ^ Math.imul((b | 0) + 0x7f4a7c15, 0xc2b2ae35) ^ Math.imul((c | 0) + 0x165667b1, 0x27d4eb2d);
  h = Math.imul(h ^ (h >>> 16), 0x7feb352d); h = Math.imul(h ^ (h >>> 15), 0x846ca68b); h ^= h >>> 16;
  return (h >>> 0) / 0xffffffff;
}
function wrapDelta(x: number) { return x - Math.round(x); }
function periodicField(u: number, v: number, seed: number, octaves = 4) {
  let sum = 0, amp = .56, norm = 0;
  for (let i = 0; i < octaves; i++) {
    const fx = 1 << i;
    const fy = Math.max(1, Math.round(fx * (.73 + hash(seed, i, 1) * .54)));
    const p1 = hash(seed, i, 2) * TAU, p2 = hash(seed, i, 3) * TAU;
    const a = Math.sin(TAU * (fx * u + fy * v) + p1);
    const b = Math.cos(TAU * (fy * u - fx * v) + p2);
    sum += (a * .58 + b * .42) * amp; norm += amp; amp *= .49;
  }
  return sum / Math.max(norm, 1e-6);
}
function ridgeField(u: number, v: number, seed: number, freq: number, angle: number) {
  const ca = Math.cos(angle), sa = Math.sin(angle);
  const x = u * ca + v * sa;
  const warp = periodicField(u, v, seed + 91, 3) * .10;
  return .5 + .5 * Math.sin(TAU * freq * (x + warp) + hash(seed, 88) * TAU);
}
function zeroEmission(size: number) { return makeTexture(size, size, 3); }
function finalize(size: number, baseColor: ReturnType<typeof makeTexture>, roughness: ReturnType<typeof makeTexture>, height: ReturnType<typeof makeTexture>, ao: ReturnType<typeof makeTexture>, normalStrength: number): Material {
  const metallic = makeTexture(size, size, 1);
  const normal = heightToNormal(height, normalStrength, true);
  return { baseColor, metallic, roughness, normal, ao, height, emission: zeroEmission(size) };
}

export function bakeVfPainterlyDirt(size: number, p: VfPainterlyDirtParams = {}): Material {
  const seed = Math.floor(p.seed ?? 182031);
  const relief = Math.max(.6, Math.min(1.7, p.relief ?? 1.18));
  const normalStrength = Math.max(2, Math.min(18, p.normalStrength ?? 9.4));
  const moisture = C(p.moisture ?? .16);
  const baseColor = makeTexture(size, size, 3), roughness = makeTexture(size, size, 1), height = makeTexture(size, size, 1), ao = makeTexture(size, size, 1);
  const dark: RGB = [.105, .048, .026], mid: RGB = [.315, .145, .065], light: RGB = [.565, .315, .145], warm: RGB = [.690, .410, .195], cool: RGB = [.150, .085, .070];
  for (let y = 0; y < size; y++) {
    const v = 1 - (y + .5) / size;
    for (let x = 0; x < size; x++) {
      const u = (x + .5) / size, i = y * size + x, j = i * 3;
      const macro = periodicField(u, v, seed + 2, 4);
      const clod = periodicField(u, v, seed + 13, 3);
      const compression = ridgeField(u, v, seed + 31, 2.0, -.38);
      const erosionLine = Math.pow(1 - Math.abs(Math.sin(TAU * (2.0 * u + .72 * v + periodicField(u, v, seed + 44, 2) * .08))), 9);
      const h = C(.49 + relief * (macro * .080 + clod * .052 + (compression - .5) * .025 - erosionLine * .050));
      const cavity = C((.50 - macro) * .55 + erosionLine * .55);
      const face = S(C(.48 + macro * .55 + clod * .20));
      let col = M(dark, mid, face);
      col = M(col, light, S(C((face - .42) / .58)) * .72);
      col = M(col, warm, S(C((macro - .15) / .55)) * .12);
      col = M(col, cool, cavity * .24);
      col = M(col, [col[0] * .62, col[1] * .58, col[2] * .54], moisture * (.38 + cavity * .36));
      const wash = periodicField(u, v, seed + 79, 4);
      col = M(col, wash > 0 ? warm : cool, Math.abs(wash) * .045);
      baseColor.data[j] = C(col[0]); baseColor.data[j + 1] = C(col[1]); baseColor.data[j + 2] = C(col[2]);
      height.data[i] = h;
      roughness.data[i] = C(.86 - moisture * .22 + cavity * .07 + Math.abs(wash) * .025);
      ao.data[i] = C(1 - cavity * .30);
    }
  }
  return finalize(size, baseColor, roughness, height, ao, normalStrength);
}

export function bakeVfPainterlyBark(size: number, p: VfPainterlyBarkParams = {}): Material {
  const seed = Math.floor(p.seed ?? 275903);
  const relief = Math.max(.7, Math.min(1.8, p.relief ?? 1.34));
  const normalStrength = Math.max(3, Math.min(20, p.normalStrength ?? 11.3));
  const ridgeScale = Math.max(.65, Math.min(1.5, p.ridgeScale ?? 1));
  const baseColor = makeTexture(size, size, 3), roughness = makeTexture(size, size, 1), height = makeTexture(size, size, 1), ao = makeTexture(size, size, 1);
  const crack: RGB = [.055, .018, .014], shadow: RGB = [.105, .042, .030], mid: RGB = [.305, .125, .060], light: RGB = [.585, .305, .135], ochre: RGB = [.735, .430, .195], cool: RGB = [.155, .075, .080];
  const knots = [[.22, .31, .10, .08], [.68, .62, .12, .095], [.47, .82, .09, .07], [.84, .20, .075, .06]];
  for (let y = 0; y < size; y++) {
    const v = 1 - (y + .5) / size;
    for (let x = 0; x < size; x++) {
      const u = (x + .5) / size, i = y * size + x, j = i * 3;
      const warp = periodicField(u, v, seed + 5, 3) * .055;
      const phase = TAU * (7.0 * ridgeScale * (u + warp) + periodicField(u, v, seed + 7, 2) * .055);
      const plate = .5 + .5 * Math.cos(phase);
      const plateBroad = Math.pow(plate, .70);
      const fissure = Math.pow(1 - plate, 7.5);
      const cross = periodicField(u, v, seed + 23, 4);
      let knot = 0;
      for (let k = 0; k < knots.length; k++) {
        const [cx, cy, rx, ry] = knots[k];
        const dx = wrapDelta(u - cx), dy = wrapDelta(v - cy);
        const r = Math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2);
        knot = Math.max(knot, G((r - .56) / .22) * (1 - G(r / .28)));
      }
      const chip = Math.pow(C(.5 + periodicField(u, v, seed + 61, 3) * .5), 3) * fissure;
      const h = C(.47 + relief * ((plateBroad - .5) * .145 + cross * .028 + knot * .052 - fissure * .085 - chip * .030));
      const face = S(C((plateBroad - .16) / .84));
      let col = M(shadow, mid, face);
      col = M(col, light, face * .66);
      col = M(col, ochre, S(C((cross + .18) / .70)) * .10 * face);
      col = M(col, cool, C(-cross) * .10);
      col = M(col, crack, C(fissure * .92 + knot * .50));
      const brush = Math.pow(C(.5 + .5 * Math.sin(TAU * (2.1 * v + .35 * u) + hash(seed, 91) * TAU)), 6) * face;
      col = M(col, [.770, .445, .210], brush * .07);
      baseColor.data[j] = C(col[0]); baseColor.data[j + 1] = C(col[1]); baseColor.data[j + 2] = C(col[2]);
      height.data[i] = h;
      roughness.data[i] = C(.80 + fissure * .10 + knot * .05 - face * .035);
      ao.data[i] = C(1 - fissure * .43 - knot * .18);
    }
  }
  return finalize(size, baseColor, roughness, height, ao, normalStrength);
}

type Leaf = { cx: number; cy: number; rx: number; ry: number; angle: number; base: number; hue: number; id: number };
function buildLeaves(seed: number, density: number): Leaf[] {
  const leaves: Leaf[] = [];
  const gx = Math.max(5, Math.round(6 * density)), gy = Math.max(5, Math.round(6 * density));
  let id = 0;
  for (let y = 0; y < gy; y++) for (let x = 0; x < gx; x++) {
    const cx = (x + .5 + (hash(seed, x, y, 1) - .5) * .62) / gx;
    const cy = (y + .5 + (hash(seed, x, y, 2) - .5) * .62) / gy;
    leaves.push({ cx, cy, rx: (.58 + hash(seed, x, y, 3) * .44) / gx, ry: (.78 + hash(seed, x, y, 4) * .55) / gy, angle: (hash(seed, x, y, 5) - .5) * 2.5, base: .45 + hash(seed, x, y, 6) * .18, hue: hash(seed, x, y, 7), id: id++ });
  }
  return leaves;
}

export function bakeVfPainterlyLeaves(size: number, p: VfPainterlyLeavesParams = {}): Material {
  const seed = Math.floor(p.seed ?? 391477);
  const relief = Math.max(.5, Math.min(1.6, p.relief ?? 1.06));
  const normalStrength = Math.max(2, Math.min(18, p.normalStrength ?? 8.5));
  const density = Math.max(.72, Math.min(1.35, p.density ?? 1));
  const leaves = buildLeaves(seed, density);
  const baseColor = makeTexture(size, size, 3), roughness = makeTexture(size, size, 1), height = makeTexture(size, size, 1), ao = makeTexture(size, size, 1);
  const deep: RGB = [.028, .095, .045], dark: RGB = [.050, .180, .075], mid: RGB = [.125, .350, .120], light: RGB = [.345, .535, .185], warm: RGB = [.505, .555, .205], cool: RGB = [.055, .175, .135];
  for (let py = 0; py < size; py++) {
    const v = 1 - (py + .5) / size;
    for (let px = 0; px < size; px++) {
      const u = (px + .5) / size, i = py * size + px, j = i * 3;
      let bestH = .365, secondH = .345, best: Leaf | null = null, bestInside = 0, bestVein = 0;
      for (const leaf of leaves) {
        const dx = wrapDelta(u - leaf.cx), dy = wrapDelta(v - leaf.cy);
        if (Math.abs(dx) > leaf.rx * 1.15 || Math.abs(dy) > leaf.ry * 1.15) continue;
        const ca = Math.cos(leaf.angle), sa = Math.sin(leaf.angle);
        const lx = (dx * ca + dy * sa) / leaf.rx, ly = (-dx * sa + dy * ca) / leaf.ry;
        const taper = Math.max(.18, 1 - Math.abs(ly) * .72);
        const q = Math.sqrt((lx / taper) ** 2 + ly * ly);
        if (q > 1) continue;
        const inside = S((1 - q) / .18);
        const dome = Math.max(0, 1 - q * q);
        const vein = G(lx / .075) * S((1 - Math.abs(ly)) / .18);
        const serration = Math.sin(TAU * (6 * Math.abs(ly) + leaf.id * .17)) * .005 * inside;
        const h = leaf.base + relief * (dome * .085 + inside * .018 + vein * .010 + serration);
        if (h > bestH) { secondH = bestH; bestH = h; best = leaf; bestInside = inside; bestVein = vein; }
        else if (h > secondH) secondH = h;
      }
      const overlap = C((bestH - secondH) / .10), cavity = C(1 - overlap);
      let col: RGB;
      if (best) {
        const variation = best.hue;
        col = M(dark, mid, .38 + variation * .38);
        col = M(col, light, bestInside * (.28 + variation * .24));
        col = M(col, warm, C(variation - .64) * .18);
        col = M(col, cool, C(.36 - variation) * .16);
        col = M(col, [.620, .655, .300], bestVein * .09);
        col = M(col, deep, cavity * .34);
      } else col = deep;
      const wash = periodicField(u, v, seed + 701, 3);
      col = M(col, wash > 0 ? light : cool, Math.abs(wash) * .045);
      baseColor.data[j] = C(col[0]); baseColor.data[j + 1] = C(col[1]); baseColor.data[j + 2] = C(col[2]);
      height.data[i] = C(bestH);
      roughness.data[i] = C(.72 + cavity * .10 - (best ? bestInside : 0) * .035);
      ao.data[i] = C(1 - cavity * .40);
    }
  }
  return finalize(size, baseColor, roughness, height, ao, normalStrength);
}

export function bakeVfPainterlySnow(size: number, p: VfPainterlySnowParams = {}): Material {
  const seed = Math.floor(p.seed ?? 447101);
  const relief = Math.max(.4, Math.min(1.5, p.relief ?? .98));
  const normalStrength = Math.max(1.5, Math.min(15, p.normalStrength ?? 6.7));
  const wind = Math.max(.25, Math.min(1.4, p.windStrength ?? .85));
  const baseColor = makeTexture(size, size, 3), roughness = makeTexture(size, size, 1), height = makeTexture(size, size, 1), ao = makeTexture(size, size, 1);
  const cold: RGB = [.355, .535, .745], blue: RGB = [.570, .700, .845], mid: RGB = [.805, .865, .910], light: RGB = [.975, .970, .925], warm: RGB = [.980, .895, .800];
  for (let y = 0; y < size; y++) {
    const v = 1 - (y + .5) / size;
    for (let x = 0; x < size; x++) {
      const u = (x + .5) / size, i = y * size + x, j = i * 3;
      const broad = periodicField(u, v, seed + 4, 4);
      const windWave = ridgeField(u, v, seed + 11, 2.2, -.52);
      const lee = ridgeField(u, v, seed + 19, 1.15, -.52);
      const softRidge = Math.pow(windWave, 2.2);
      const carved = Math.pow(1 - windWave, 4.2) * .55 + Math.pow(1 - lee, 5.0) * .25;
      const h = C(.53 + relief * (broad * .060 + (softRidge - .38) * .070 * wind - carved * .030 * wind));
      const shadow = C((.52 - broad) * .72 + carved * .42);
      const ridge = S(C((softRidge - .45) / .55));
      let col = M(blue, mid, C(.52 + broad * .52));
      col = M(col, light, ridge * .60);
      col = M(col, cold, shadow * .42);
      col = M(col, warm, ridge * .08);
      baseColor.data[j] = C(col[0]); baseColor.data[j + 1] = C(col[1]); baseColor.data[j + 2] = C(col[2]);
      height.data[i] = h;
      roughness.data[i] = C(.88 + shadow * .035 - ridge * .025);
      ao.data[i] = C(1 - shadow * .16);
    }
  }
  return finalize(size, baseColor, roughness, height, ao, normalStrength);
}

export function bakeVfPainterlyWater(size: number, p: VfPainterlyWaterParams = {}): Material {
  const seed = Math.floor(p.seed ?? 553819);
  const relief = Math.max(.15, Math.min(.9, p.relief ?? .42));
  const normalStrength = Math.max(1, Math.min(12, p.normalStrength ?? 5.2));
  const scale = Math.max(.55, Math.min(1.7, p.waveScale ?? 1));
  const baseRough = Math.max(.035, Math.min(.34, p.roughness ?? .085));
  const baseColor = makeTexture(size, size, 3), roughness = makeTexture(size, size, 1), height = makeTexture(size, size, 1), ao = makeTexture(size, size, 1);
  const deep: RGB = [.018, .090, .145], mid: RGB = [.025, .235, .315], cyan: RGB = [.085, .420, .470], crest: RGB = [.300, .650, .665], sky: RGB = [.185, .435, .610];
  const p1 = hash(seed, 1) * TAU, p2 = hash(seed, 2) * TAU, p3 = hash(seed, 3) * TAU;
  for (let y = 0; y < size; y++) {
    const v = 1 - (y + .5) / size;
    for (let x = 0; x < size; x++) {
      const u = (x + .5) / size, i = y * size + x, j = i * 3;
      const w1 = Math.sin(TAU * scale * (3.0 * u + 1.25 * v) + p1);
      const w2 = Math.sin(TAU * scale * (-1.1 * u + 4.2 * v) + p2);
      const w3 = Math.sin(TAU * scale * (6.1 * u - 2.4 * v) + p3);
      const broad = periodicField(u, v, seed + 44, 3);
      const wave = w1 * .48 + w2 * .32 + w3 * .15 + broad * .12;
      const sharp = Math.pow(C(.5 + wave * .45), 2.1);
      const h = C(.50 + relief * (wave * .043 + sharp * .014));
      let col = M(deep, mid, C(.48 + broad * .22 + wave * .13));
      col = M(col, cyan, C(sharp - .58) * .25);
      col = M(col, crest, C(sharp - .78) * .16);
      col = M(col, sky, C(.5 + w2 * .5) * .06);
      baseColor.data[j] = C(col[0]); baseColor.data[j + 1] = C(col[1]); baseColor.data[j + 2] = C(col[2]);
      height.data[i] = h;
      roughness.data[i] = C(baseRough + Math.abs(w3) * .018 + C(-wave) * .018);
      ao.data[i] = 1;
    }
  }
  return finalize(size, baseColor, roughness, height, ao, normalStrength);
}
