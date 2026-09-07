import { heightToNormal, makeTexture, type Material } from "../../src/index.js";

export type RGB = [number, number, number];
export const TAU = Math.PI * 2;
export const C = (x: number) => Math.max(0, Math.min(1, x));
export const L = (a: number, b: number, t: number) => a + (b - a) * t;
export const M = (a: RGB, b: RGB, t: number): RGB => [L(a[0], b[0], t), L(a[1], b[1], t), L(a[2], b[2], t)];
export const S = (x: number) => { const t = C(x); return t * t * (3 - 2 * t); };
export const G = (x: number) => Math.exp(-(x * x));
export function hash(seed: number, a: number, b = 0, c = 0) {
  let h = (seed | 0) ^ Math.imul((a | 0) + 0x9e3779b9, 0x85ebca6b) ^ Math.imul((b | 0) + 0x7f4a7c15, 0xc2b2ae35) ^ Math.imul((c | 0) + 0x165667b1, 0x27d4eb2d);
  h = Math.imul(h ^ (h >>> 16), 0x7feb352d); h = Math.imul(h ^ (h >>> 15), 0x846ca68b); h ^= h >>> 16;
  return (h >>> 0) / 0xffffffff;
}
export function wrapDelta(x: number) { return x - Math.round(x); }
export function periodicField(u: number, v: number, seed: number, octaves = 4) {
  let sum = 0, amp = .56, norm = 0;
  for (let i = 0; i < octaves; i++) {
    const fx = 1 << i;
    const fy = Math.max(1, Math.round(fx * (.73 + hash(seed, i, 1) * .54)));
    const p1 = hash(seed, i, 2) * TAU, p2 = hash(seed, i, 3) * TAU;
    sum += (Math.sin(TAU * (fx * u + fy * v) + p1) * .58 + Math.cos(TAU * (fy * u - fx * v) + p2) * .42) * amp;
    norm += amp; amp *= .49;
  }
  return sum / Math.max(norm, 1e-6);
}
export function ridgeField(u: number, v: number, seed: number, freq: number, angle: number) {
  const ca = Math.cos(angle), sa = Math.sin(angle);
  const x = u * ca + v * sa;
  const warp = periodicField(u, v, seed + 91, 3) * .10;
  return .5 + .5 * Math.sin(TAU * freq * (x + warp) + hash(seed, 88) * TAU);
}
export function finalize(size: number, baseColor: ReturnType<typeof makeTexture>, roughness: ReturnType<typeof makeTexture>, height: ReturnType<typeof makeTexture>, ao: ReturnType<typeof makeTexture>, normalStrength: number): Material {
  const metallic = makeTexture(size, size, 1);
  const normal = heightToNormal(height, normalStrength, true);
  return { baseColor, metallic, roughness, normal, ao, height, emission: makeTexture(size, size, 3) };
}
export { makeTexture };
