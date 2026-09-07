import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import {
  BILIBILI_MATERIALS,
  bakeStylizedCellRock,
  exportPBR,
  heightToNormal,
  makeTexture,
  materialFromFields,
  textureToPNG,
  validateMaterial,
  type Material,
} from "../src/index.js";

type RGB = [number, number, number];
type Request = {
  name: string;
  resolution: number;
  preset: "stylizedCellRock" | "volcanicRock" | "simpleRock" | "vfBasalt";
  profile?: "realistic" | "stylized";
  params: Record<string, unknown>;
};

const TAU = Math.PI * 2;
const clamp01 = (value: number) => Math.max(0, Math.min(1, value));
const wrap01 = (value: number) => value - Math.floor(value);
const smoothstep = (edge0: number, edge1: number, value: number) => {
  const t = clamp01((value - edge0) / Math.max(1e-9, edge1 - edge0));
  return t * t * (3 - 2 * t);
};
const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const mixRGB = (a: RGB, b: RGB, t: number): RGB => [
  mix(a[0], b[0], t),
  mix(a[1], b[1], t),
  mix(a[2], b[2], t),
];

function numberParam(params: Record<string, unknown>, key: string, fallback: number): number {
  const value = params[key];
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

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

/** Integer-frequency Fourier FBM: deterministic and exactly periodic over UV 0..1. */
function periodicFbm(
  u: number,
  v: number,
  seed: number,
  baseFrequency: number,
  octaves: number,
): number {
  let sum = 0;
  let weight = 0;
  for (let octave = 0; octave < octaves; octave++) {
    const f = Math.max(1, Math.round(baseFrequency * 2 ** octave));
    const amplitude = 1 / 2 ** octave;
    for (let band = 0; band < 3; band++) {
      const spread = Math.max(2, Math.round(f * 0.55));
      const kx = Math.max(1, f + Math.floor(hash01(octave, band, seed, 11) * spread));
      const ky = Math.max(1, f + Math.floor(hash01(octave, band, seed, 17) * spread));
      const phase = hash01(octave, band, seed, 23) * TAU;
      const bandAmp = amplitude * (0.72 + hash01(octave, band, seed, 31) * 0.28);
      sum += Math.sin((u * kx + v * ky) * TAU + phase) * bandAmp;
      sum += Math.cos((u * ky - v * kx) * TAU + phase * 0.67) * bandAmp * 0.52;
      weight += bandAmp * 1.52;
    }
  }
  return clamp01(0.5 + 0.5 * sum / Math.max(weight, 1e-9));
}

function warpedUv(u: number, v: number, seed: number, amount: number): [number, number] {
  const wu = periodicFbm(u, v, seed + 101, 2, 4) - 0.5;
  const wv = periodicFbm(u, v, seed + 211, 2, 4) - 0.5;
  return [wrap01(u + wu * amount), wrap01(v + wv * amount)];
}

/** Curved, gated fracture families. Unlike Voronoi edges these do not form obvious polygon cells. */
function fractureMask(u: number, v: number, seed: number): number {
  const [wu, wv] = warpedUv(u, v, seed + 300, 0.075);
  const warpA = (periodicFbm(wu, wv, seed + 401, 2, 4) - 0.5) * 0.22;
  const warpB = (periodicFbm(wu, wv, seed + 503, 3, 3) - 0.5) * 0.18;
  const phaseA = hash01(1, 1, seed, 601) * TAU;
  const phaseB = hash01(2, 2, seed, 607) * TAU;
  const fieldA = Math.sin((wu * 2 + wv) * TAU + phaseA + warpA * TAU)
    + 0.48 * Math.sin((-wu + wv * 3) * TAU + phaseB + warpB * TAU);
  const fieldB = Math.sin((wu * 3 - wv * 2) * TAU + phaseB * 0.71 - warpB * TAU)
    + 0.42 * Math.cos((wu + wv * 4) * TAU + phaseA * 0.53 + warpA * TAU);
  const lineA = 1 - smoothstep(0.018, 0.095, Math.abs(fieldA));
  const lineB = 1 - smoothstep(0.014, 0.078, Math.abs(fieldB));
  const gateA = smoothstep(0.43, 0.68, periodicFbm(wu, wv, seed + 701, 1, 4));
  const gateB = smoothstep(0.46, 0.72, periodicFbm(wu, wv, seed + 809, 2, 3));
  return clamp01(Math.max(lineA * (0.28 + 0.72 * gateA), lineB * 0.72 * gateB));
}

/** Sparse, periodic vesicles; deliberately low density so basalt does not become pumice/asphalt. */
function sparsePores(u: number, v: number, seed: number, density: number): number {
  const cells = 18;
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
      if (hash01(wx, wy, seed, 901) > density) continue;
      const jx = 0.5 + (hash01(wx, wy, seed, 907) - 0.5) * 0.72;
      const jy = 0.5 + (hash01(wx, wy, seed, 911) - 0.5) * 0.72;
      const radius = 0.13 + hash01(wx, wy, seed, 919) * 0.16;
      const aspect = 0.58 + hash01(wx, wy, seed, 929) * 0.58;
      const angle = hash01(wx, wy, seed, 937) * TAU;
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);
      const dx = px - (cx + jx);
      const dy = py - (cy + jy);
      const rx = dx * cosine - dy * sine;
      const ry = dx * sine + dy * cosine;
      const d = Math.hypot(rx / radius, ry / (radius * aspect));
      mask = Math.max(mask, 1 - smoothstep(0.55, 1.02, d));
    }
  }
  return clamp01(mask);
}

function createVfBasaltSampler(params: Record<string, unknown>) {
  const seed = Math.round(numberParam(params, "seed", 240910));
  const fractureStrength = clamp01(numberParam(params, "fractureStrength", 0.72));
  const poreDensity = Math.max(0, Math.min(0.18, numberParam(params, "poreDensity", 0.035)));
  const weathering = clamp01(numberParam(params, "weathering", 0.34));
  const roughnessBias = Math.max(-0.2, Math.min(0.2, numberParam(params, "roughnessBias", 0)));
  const normalStrength = Math.max(0.2, Math.min(10, numberParam(params, "normalStrength", 4.8)));

  const sample = (u: number, v: number) => {
    const [du, dv] = warpedUv(u, v, seed + 1000, 0.045);
    const macro = periodicFbm(du, dv, seed + 1100, 1, 5);
    const meso = periodicFbm(du, dv, seed + 1200, 5, 4);
    const micro = periodicFbm(du, dv, seed + 1300, 28, 3);
    const grain = periodicFbm(du, dv, seed + 1400, 64, 2);
    const fracture = fractureMask(du, dv, seed + 1500) * fractureStrength;
    const pores = sparsePores(du, dv, seed + 1600, poreDensity);
    const pinholes = smoothstep(0.79, 0.92, periodicFbm(du, dv, seed + 1700, 46, 2)) * 0.38;
    const oxideGate = smoothstep(0.52, 0.73, periodicFbm(du, dv, seed + 1800, 3, 4));

    const height = clamp01(
      0.5
      + (macro - 0.5) * 0.34
      + (meso - 0.5) * 0.16
      + (micro - 0.5) * 0.045
      + (grain - 0.5) * 0.018
      - fracture * 0.24
      - pores * 0.31
      - pinholes * 0.035,
    );

    const tone = clamp01(0.24 + macro * 0.42 + meso * 0.22 + micro * 0.12);
    let color = mixRGB([0.047, 0.051, 0.055], [0.145, 0.151, 0.152], tone);
    const oxide = fracture * oxideGate * weathering + pores * weathering * 0.42;
    color = mixRGB(color, [0.235, 0.145, 0.085], clamp01(oxide * 0.32));
    const creviceDarkening = clamp01(1 - fracture * 0.35 - pores * 0.42 - pinholes * 0.08);
    const grainTone = 0.93 + grain * 0.12;
    color = [
      clamp01(color[0] * creviceDarkening * grainTone),
      clamp01(color[1] * creviceDarkening * grainTone),
      clamp01(color[2] * creviceDarkening * grainTone),
    ];

    const roughness = clamp01(
      0.73
      + roughnessBias
      + (micro - 0.5) * 0.16
      + fracture * 0.15
      + pores * 0.18
      + pinholes * 0.08
      - height * 0.045,
    );
    const ao = clamp01(1 - fracture * 0.36 - pores * 0.58 - pinholes * 0.12);
    return { color, height, roughness, ao };
  };
  return { sample, normalStrength };
}

/** One procedural evaluation per texel writes all scalar/color channels, then normal derives from height. */
function bakeVfBasalt(size: number, params: Record<string, unknown>): Material {
  const { sample, normalStrength } = createVfBasaltSampler(params);
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
      const value = sample(u, v);
      const scalar = y * size + x;
      const rgb = scalar * 3;
      baseColor.data[rgb] = value.color[0];
      baseColor.data[rgb + 1] = value.color[1];
      baseColor.data[rgb + 2] = value.color[2];
      roughness.data[scalar] = value.roughness;
      ao.data[scalar] = value.ao;
      height.data[scalar] = value.height;
    }
  }

  const normal = heightToNormal(height, normalStrength, true);
  return { baseColor, metallic, roughness, normal, ao, height, emission };
}

const requestPath = process.argv[2] ?? "vf-request.json";
const req = JSON.parse(readFileSync(requestPath, "utf8")) as Request;
if (!Number.isInteger(req.resolution) || req.resolution < 16 || req.resolution > 4096) {
  throw new Error(`Invalid resolution: ${req.resolution}`);
}

let material;
let masks: Readonly<Record<string, unknown>> = {};
if (req.preset === "stylizedCellRock") {
  const result = bakeStylizedCellRock(req.resolution, req.params);
  material = result.material;
  masks = result.masks;
} else if (req.preset === "volcanicRock") {
  material = materialFromFields(req.resolution, BILIBILI_MATERIALS.volcanicRock(req.params));
} else if (req.preset === "simpleRock") {
  material = materialFromFields(req.resolution, BILIBILI_MATERIALS.simpleRock(req.params));
} else if (req.preset === "vfBasalt") {
  material = bakeVfBasalt(req.resolution, req.params);
} else {
  throw new Error(`Unsupported preset: ${String(req.preset)}`);
}

const problems = validateMaterial(material);
if (problems.length > 0) throw new Error(problems.join("; "));

const out = path.resolve(process.cwd(), "out", "vf-materials", req.name);
mkdirSync(out, { recursive: true });
const exported = exportPBR(material, req.name);
for (const [filename, bytes] of Object.entries(exported.files)) {
  writeFileSync(path.join(out, filename), bytes);
}
for (const [maskName, mask] of Object.entries(masks)) {
  writeFileSync(path.join(out, `${req.name}_mask-${maskName}.png`), textureToPNG(mask as never));
}
writeFileSync(path.join(out, "request.json"), JSON.stringify(req, null, 2));

const manifest = {
  generator: "wellingfeng/Meshova + voxel-frontier custom recipe",
  generatorCommit: process.env.MESHOVA_COMMIT ?? "unknown",
  deterministic: true,
  seamlessByConstruction: req.preset === "vfBasalt",
  singlePassCustomBake: req.preset === "vfBasalt",
  material: req.name,
  resolution: req.resolution,
  profile: req.profile ?? "unspecified",
  preset: req.preset,
  pbrFiles: Object.keys(exported.files).sort(),
  maskFiles: Object.keys(masks).map((name) => `${req.name}_mask-${name}.png`).sort(),
};
writeFileSync(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify({ ok: true, output: out, ...manifest }, null, 2));
