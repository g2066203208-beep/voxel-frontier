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
  lean: number;
  phase1: number;
  phase2: number;
  splitY: number;
  splitDir: number;
  split: boolean;
  breaks: [number, number];
};

type Knot = {
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  twist: number;
  scar: number;
};

function buildRibbons(seed: number, ridgeScale: number): BarkRibbon[] {
  const count = Math.max(8, Math.min(12, Math.round(10 * ridgeScale)));
  const out: BarkRibbon[] = [];
  for (let i = 0; i < count; i++) {
    out.push({
      cx: (i + 0.5 + (hash(seed, i, 0) - 0.5) * 0.22) / count,
      width: (0.52 + hash(seed, i, 6) * 0.22) / count,
      lift: 0.078 + hash(seed, i, 7) * 0.036,
      warm: hash(seed, i, 8),
      cool: hash(seed, i, 18),
      lean: (hash(seed, i, 19) - 0.5) * 0.018,
      phase1: hash(seed, i, 1) * TAU,
      phase2: hash(seed, i, 3) * TAU,
      splitY: hash(seed, i, 9),
      splitDir: hash(seed, i, 10) < 0.5 ? -1 : 1,
      split: hash(seed, i, 11) > 0.58,
      breaks: [hash(seed, i, 20), hash(seed, i, 21)],
    });
  }
  return out;
}

function ribbonCenter(v: number, ribbon: BarkRibbon, seed: number, id: number) {
  return (
    ribbon.cx +
    Math.sin(TAU * v + ribbon.phase1) * (0.01 + hash(seed, id, 2) * 0.01) +
    Math.sin(TAU * 2 * v + ribbon.phase2) * (0.005 + hash(seed, id, 4) * 0.006) +
    Math.sin(TAU * 3 * v + hash(seed, id, 5) * TAU) * 0.0035 +
    ribbon.lean * Math.sin(TAU * v)
  );
}

function buildKnots(seed: number): Knot[] {
  return [
    { cx: 0.235, cy: 0.335, rx: 0.075, ry: 0.062, twist: 1, scar: 0.78 },
    { cx: 0.715, cy: 0.675, rx: 0.087, ry: 0.074, twist: -1, scar: 0.88 },
    { cx: 0.485, cy: 0.865, rx: 0.062, ry: 0.052, twist: hash(seed, 901) < 0.5 ? -1 : 1, scar: 0.66 },
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

  const fissureCol: RGB = [0.032, 0.009, 0.012];
  const deep: RGB = [0.082, 0.024, 0.022];
  const shadow: RGB = [0.145, 0.047, 0.038];
  const mid: RGB = [0.34, 0.112, 0.052];
  const light: RGB = [0.61, 0.285, 0.105];
  const gold: RGB = [0.83, 0.48, 0.19];
  const cool: RGB = [0.14, 0.055, 0.092];
  const scarLight: RGB = [0.74, 0.39, 0.145];

  for (let py = 0; py < size; py++) {
    const v = 1 - (py + 0.5) / size;
    for (let px = 0; px < size; px++) {
      const u = (px + 0.5) / size;
      const i = py * size + px;
      const j = i * 3;

      let knotWarp = 0;
      let knotRing = 0;
      let knotCore = 0;
      let knotScar = 0;
      for (const knot of knots) {
        const dx = wrapDelta(u - knot.cx);
        const dy = wrapDelta(v - knot.cy);
        const r = Math.sqrt((dx / knot.rx) ** 2 + (dy / knot.ry) ** 2);
        const mask = S((1 - r) / 0.45);
        const angle = Math.atan2(dy / Math.max(knot.ry, 1e-6), dx / Math.max(knot.rx, 1e-6));
        knotWarp += mask * Math.sin(angle) * 0.032 * knot.twist;
        knotRing = Math.max(knotRing, G((r - 0.72) / 0.15) * S((1.22 - r) / 0.28));
        knotCore = Math.max(knotCore, G(r / 0.34));
        knotScar = Math.max(knotScar, G((r - 0.47) / 0.17) * knot.scar);
      }

      let best = -1;
      let second = -1;
      let bestId = 0;
      let bestQ = 99;
      let bestDx = 0;
      let bestWidth = 1;
      let bestBreak = 0;
      let bestRibbon = ribbons[0];

      for (let id = 0; id < ribbons.length; id++) {
        const ribbon = ribbons[id];
        const center = ribbonCenter(v, ribbon, seed, id) + knotWarp;
        const width =
          ribbon.width *
          (0.84 + 0.20 * (0.5 + 0.5 * Math.sin(TAU * (2 * v + hash(seed, id, 12)))));
        const dx = wrapDelta(u - center);
        const q0 = Math.abs(dx) / Math.max(width, 1e-6);
        const edgeNoise = periodicField(u, v, seed + 310 + id * 19, 3);
        const q = Math.max(0, q0 + edgeNoise * 0.075 * (0.35 + q0));
        const plate = S((1.10 - q) / 0.21);
        const crown = G(q / 0.58);
        let score = 0.68 * plate + 0.32 * crown;

        let crossBreak = 0;
        for (let bi = 0; bi < ribbon.breaks.length; bi++) {
          const widthY = 0.015 + hash(seed, id, bi, 32) * 0.007;
          crossBreak = Math.max(crossBreak, G(wrapDelta(v - ribbon.breaks[bi]) / widthY));
        }
        crossBreak *= G(q / 0.80);

        if (ribbon.split) {
          const splitMask = G(wrapDelta(v - ribbon.splitY) / 0.095);
          const branchCenter = center + ribbon.splitDir * width * 0.82 * splitMask;
          const branchQ = Math.abs(wrapDelta(u - branchCenter)) / Math.max(width * 0.58, 1e-6);
          const branch = S((1.0 - branchQ) / 0.20) * splitMask * 0.62;
          score = Math.max(score, branch);
        }

        if (score > best) {
          second = best;
          best = score;
          bestId = id;
          bestQ = q;
          bestDx = dx;
          bestWidth = width;
          bestBreak = crossBreak;
          bestRibbon = ribbon;
        } else if (score > second) {
          second = score;
        }
      }

      const seam = (1 - S((best - second) / 0.055)) * S((0.64 - best) / 0.24);
      const side = C(0.5 - bestDx / Math.max(bestWidth * 1.35, 1e-6));
      const fiberPhase =
        TAU * (42 * u + 4 * v + hash(seed, bestId, 13)) +
        periodicField(u, v, seed + 590 + bestId * 11, 2) * 0.7;
      const fiber = (0.5 + 0.5 * Math.sin(fiberPhase) - 0.5) * best;
      const grain = periodicField(u, v, seed + 710 + bestId * 17, 4);
      const planeWash = periodicField(u, v, seed + 830 + bestId * 23, 2);

      let h =
        0.435 +
        relief *
          (best * bestRibbon.lift +
            best * best * 0.022 -
            seam * 0.042 -
            bestBreak * 0.032 +
            fiber * 0.009 +
            (side - 0.5) * best * 0.006 +
            knotRing * 0.022 -
            knotCore * 0.014);
      h = C(h);

      let col = M(shadow, mid, C(0.22 + best * 0.72));
      col = M(col, light, C(best * 0.48 + side * best * 0.16));
      col = M(col, gold, C((side - 0.48) * 0.22 * best + bestRibbon.warm * 0.055 * best));
      col = M(col, cool, C((0.54 - side) * 0.16 * best + bestRibbon.cool * 0.035 * best));
      col = M(col, deep, C(bestBreak * 0.38 + seam * 0.34));
      col = M(col, fissureCol, C(seam * 0.88 + (1 - best) * 0.24));
      col = M(col, scarLight, C(knotScar * 0.34 + knotRing * 0.10));
      col = M(col, grain > 0 ? gold : cool, Math.abs(grain) * 0.035 * best);
      col = M(col, planeWash > 0 ? [0.67, 0.31, 0.11] : [0.17, 0.045, 0.035], Math.abs(planeWash) * 0.045 * best);

      const dryFiber = Math.pow(C(0.5 + 0.5 * Math.sin(fiberPhase + bestRibbon.warm * TAU)), 7) * best;
      col = M(col, [0.79, 0.43, 0.17], dryFiber * 0.045);

      baseColor.data[j] = C(col[0]);
      baseColor.data[j + 1] = C(col[1]);
      baseColor.data[j + 2] = C(col[2]);
      height.data[i] = h;
      roughness.data[i] = C(0.79 + seam * 0.13 + bestBreak * 0.07 + knotCore * 0.04 - best * 0.035 + Math.abs(grain) * 0.025);
      ao.data[i] = C(1 - seam * 0.42 - bestBreak * 0.18 - knotCore * 0.16);
    }
  }

  return finalize(size, baseColor, roughness, height, ao, normalStrength);
}
