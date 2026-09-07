import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfPainterlyBarkParams = {
  seed?: number;
  normalStrength?: number;
  relief?: number;
  ridgeScale?: number;
};

type BarkRibbon = {
  cx: number;
  width: number;
  lift: number;
  warm: number;
  cool: number;
  phase1: number;
  phase2: number;
  lean: number;
  splitY: number;
  splitDir: number;
  split: boolean;
  breakY: number;
  breakX: number;
  peelY: number;
  peelSide: number;
};

type Knot = {
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  twist: number;
};

function buildRibbons(seed: number, ridgeScale: number): BarkRibbon[] {
  const count = Math.max(12, Math.min(17, Math.round(14 * ridgeScale)));
  const out: BarkRibbon[] = [];
  for (let i = 0; i < count; i++) {
    out.push({
      cx: (i + 0.5 + (hash(seed, i, 0) - 0.5) * 0.18) / count,
      width: (0.47 + hash(seed, i, 6) * 0.13) / count,
      lift: 0.027 + hash(seed, i, 7) * 0.018,
      warm: hash(seed, i, 8),
      cool: hash(seed, i, 18),
      phase1: hash(seed, i, 1) * TAU,
      phase2: hash(seed, i, 3) * TAU,
      lean: (hash(seed, i, 19) - 0.5) * 0.014,
      splitY: hash(seed, i, 9),
      splitDir: hash(seed, i, 10) < 0.5 ? -1 : 1,
      split: hash(seed, i, 11) > 0.64,
      breakY: hash(seed, i, 20),
      breakX: (hash(seed, i, 21) - 0.5) * 0.9,
      peelY: hash(seed, i, 22),
      peelSide: hash(seed, i, 23) < 0.5 ? -1 : 1,
    });
  }
  return out;
}

function ribbonCenter(v: number, ribbon: BarkRibbon, seed: number, id: number) {
  return (
    ribbon.cx +
    Math.sin(TAU * v + ribbon.phase1) * (0.007 + hash(seed, id, 2) * 0.007) +
    Math.sin(TAU * 2 * v + ribbon.phase2) * (0.003 + hash(seed, id, 4) * 0.004) +
    Math.sin(TAU * 3 * v + hash(seed, id, 5) * TAU) * 0.0025 +
    ribbon.lean * Math.sin(TAU * v)
  );
}

function buildKnots(seed: number): Knot[] {
  return [
    { cx: 0.235, cy: 0.34, rx: 0.070, ry: 0.057, twist: 1 },
    { cx: 0.72, cy: 0.68, rx: 0.080, ry: 0.066, twist: -1 },
    { cx: 0.49, cy: 0.87, rx: 0.057, ry: 0.047, twist: hash(seed, 901) < 0.5 ? -1 : 1 },
  ];
}

export function bakeVfPainterlyBark(size: number, p: VfPainterlyBarkParams = {}) {
  const seed = Math.floor(p.seed ?? 275903);
  const relief = Math.max(0.75, Math.min(1.8, p.relief ?? 1.38));
  const normalStrength = Math.max(3, Math.min(20, p.normalStrength ?? 11.7));
  const ridgeScale = Math.max(0.82, Math.min(1.2, p.ridgeScale ?? 1));
  const ribbons = buildRibbons(seed, ridgeScale);
  const knots = buildKnots(seed);

  const baseColor = makeTexture(size, size, 3);
  const roughness = makeTexture(size, size, 1);
  const height = makeTexture(size, size, 1);
  const ao = makeTexture(size, size, 1);

  const ink: RGB = [0.016, 0.004, 0.006];
  const deep: RGB = [0.052, 0.014, 0.015];
  const shadow: RGB = [0.075, 0.023, 0.019];
  const mid: RGB = [0.19, 0.058, 0.028];
  const light: RGB = [0.39, 0.155, 0.052];
  const gold: RGB = [0.57, 0.285, 0.085];
  const cool: RGB = [0.072, 0.024, 0.043];
  const scar: RGB = [0.49, 0.22, 0.068];

  for (let py = 0; py < size; py++) {
    const v = 1 - (py + 0.5) / size;
    for (let px = 0; px < size; px++) {
      const u = (px + 0.5) / size;
      const i = py * size + px;
      const j = i * 3;

      let knotWarp = 0;
      let knotRing = 0;
      let knotCore = 0;
      for (const knot of knots) {
        const dx = wrapDelta(u - knot.cx);
        const dy = wrapDelta(v - knot.cy);
        const r = Math.sqrt((dx / knot.rx) ** 2 + (dy / knot.ry) ** 2);
        const mask = S((1 - r) / 0.42);
        const angle = Math.atan2(dy / Math.max(knot.ry, 1e-6), dx / Math.max(knot.rx, 1e-6));
        knotWarp += mask * Math.sin(angle) * 0.016 * knot.twist;
        knotRing = Math.max(knotRing, G((r - 0.70) / 0.14) * S((1.18 - r) / 0.26));
        knotCore = Math.max(knotCore, G(r / 0.33));
      }

      let d1 = 99;
      let d2 = 99;
      let bestId = 0;
      let bestDx = 0;
      let bestWidth = 1;
      let bestCenter = 0;
      for (let id = 0; id < ribbons.length; id++) {
        const ribbon = ribbons[id];
        let center = ribbonCenter(v, ribbon, seed, id) + knotWarp;
        if (ribbon.split) {
          const splitMask = G(wrapDelta(v - ribbon.splitY) / 0.085);
          center += ribbon.splitDir * ribbon.width * 0.45 * splitMask;
        }
        const dx = wrapDelta(u - center);
        const d = Math.abs(dx);
        if (d < d1) {
          d2 = d1;
          d1 = d;
          bestId = id;
          bestDx = dx;
          bestWidth = ribbon.width;
          bestCenter = center;
        } else if (d < d2) {
          d2 = d;
        }
      }

      const ribbon = ribbons[bestId];
      const q = d1 / Math.max(bestWidth, 1e-6);
      const face = S((1.08 - q) / 0.40);
      const crown = G(q / 0.73);
      const ridge = C(face * 0.68 + crown * 0.32);
      const seam = G((d2 - d1) / 0.0048);
      const signed = bestDx / Math.max(bestWidth, 1e-6);

      const breakMask =
        G(wrapDelta(v - ribbon.breakY) / 0.014) *
        G((signed - ribbon.breakX) / 0.32) *
        ridge;
      const peel =
        G(wrapDelta(v - ribbon.peelY) / 0.105) *
        G((signed - ribbon.peelSide * 0.70) / 0.20) *
        ridge *
        (hash(seed, bestId, 24) > 0.48 ? 1 : 0);

      const fiberPhase =
        TAU * (36 * u + 3 * v + hash(seed, bestId, 30)) +
        periodicField(u, v, seed + 500 + bestId * 13, 2) * 0.62;
      const fiber = Math.sin(fiberPhase) * ridge;
      const microFissure =
        Math.pow(C(0.5 + 0.5 * Math.sin(fiberPhase * 1.73 + hash(seed, bestId, 31) * TAU)), 22) *
        ridge;
      const grain = periodicField(u, v, seed + 700 + bestId * 17, 4);
      const broadWash = periodicField(u, v, seed + 820 + bestId * 19, 2);
      const edgeGold = G((Math.abs(signed) - 0.68) / 0.22) * ridge;

      let h =
        0.493 +
        relief *
          (ridge * ribbon.lift +
            crown * 0.010 +
            (signed * ridge) * 0.0045 -
            seam * 0.020 -
            breakMask * 0.010 -
            microFissure * 0.0035 +
            peel * 0.010 +
            knotRing * 0.010 -
            knotCore * 0.006 +
            fiber * 0.0035);
      h = C(h);

      let col = M(shadow, mid, C(0.26 + ridge * 0.64));
      col = M(col, light, C(ridge * 0.34 + C(signed * 0.5 + 0.5) * ridge * 0.10));
      col = M(col, gold, C(edgeGold * 0.10 + ribbon.warm * ridge * 0.035 + peel * 0.16));
      col = M(col, cool, C((0.5 - signed * 0.5) * ridge * ribbon.cool * 0.055));
      col = M(col, deep, C(breakMask * 0.28 + microFissure * 0.28));
      col = M(col, ink, C(seam * 0.78 + microFissure * 0.22));
      col = M(col, scar, C(knotRing * 0.22 + peel * 0.10));
      col = M(col, broadWash > 0 ? [0.43, 0.15, 0.045] : [0.095, 0.025, 0.026], Math.abs(broadWash) * 0.040 * ridge);
      col = M(col, grain > 0 ? gold : cool, Math.abs(grain) * 0.022 * ridge);

      const dryFiber = Math.pow(C(0.5 + 0.5 * Math.sin(fiberPhase + ribbon.warm * TAU)), 9) * ridge;
      col = M(col, [0.61, 0.29, 0.084], dryFiber * 0.024);

      baseColor.data[j] = C(col[0]);
      baseColor.data[j + 1] = C(col[1]);
      baseColor.data[j + 2] = C(col[2]);
      height.data[i] = h;
      roughness.data[i] = C(0.84 + seam * 0.08 + breakMask * 0.045 + microFissure * 0.025 + knotCore * 0.025 - ridge * 0.022 + Math.abs(grain) * 0.018);
      ao.data[i] = C(1 - seam * 0.24 - breakMask * 0.08 - microFissure * 0.035 - knotCore * 0.08);
    }
  }

  return finalize(size, baseColor, roughness, height, ao, normalStrength);
}
