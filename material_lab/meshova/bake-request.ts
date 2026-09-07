import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import {
  exportPBR,
  textureToPNG,
  validateMaterial,
  type Material,
} from "../src/index.js";
import {
  bakeVfLayeredSandstonePainted,
  type VfLayeredSandstoneParams,
} from "./vf-recipes/vf-layered-sandstone-painted.js";

const PRODUCTION_STYLE_ID = "VF_PAINTERLY_PLANETARY_V1";
const SAFE_NAME = /^[a-z0-9][a-z0-9_-]{1,79}$/;

type ProductionPreset = "vfLayeredSandstonePainted";
type Profile = "stylized" | "signature";

type Request = {
  name: string;
  resolution: number;
  preset: ProductionPreset;
  profile?: Profile;
  params: Record<string, unknown>;
};
type Envelope = Request | { materials: Request[] };
type BakeResult = {
  material: Material;
  masks?: Readonly<Record<string, unknown>>;
};
type PresetBaker = (resolution: number, params: Record<string, unknown>) => BakeResult;

const PRODUCTION_PRESETS: Readonly<Record<ProductionPreset, PresetBaker>> = {
  vfLayeredSandstonePainted: (resolution, params) => ({
    material: bakeVfLayeredSandstonePainted(
      resolution,
      params as VfLayeredSandstoneParams,
    ),
  }),
};

function validateRequest(req: Request) {
  if (!SAFE_NAME.test(req.name)) {
    throw new Error(`Unsafe material name: ${String(req.name)}`);
  }
  if (!Number.isInteger(req.resolution) || req.resolution < 64 || req.resolution > 4096) {
    throw new Error(`Invalid resolution for ${req.name}: ${req.resolution}`);
  }
  if (!(req.preset in PRODUCTION_PRESETS)) {
    throw new Error(`Preset is not production-approved: ${String(req.preset)}`);
  }
  if (req.profile && req.profile !== "stylized" && req.profile !== "signature") {
    throw new Error(`Invalid profile for ${req.name}: ${String(req.profile)}`);
  }
  if (!req.params || typeof req.params !== "object" || Array.isArray(req.params)) {
    throw new Error(`Invalid params for ${req.name}`);
  }
}

function bakeOne(req: Request) {
  validateRequest(req);
  const baker = PRODUCTION_PRESETS[req.preset];
  const { material, masks = {} } = baker(req.resolution, req.params);

  const problems = validateMaterial(material);
  if (problems.length > 0) {
    throw new Error(`${req.name}: ${problems.join("; ")}`);
  }

  const out = path.resolve(process.cwd(), "out", "vf-materials", req.name);
  mkdirSync(out, { recursive: true });

  const exported = exportPBR(material, req.name);
  for (const [filename, bytes] of Object.entries(exported.files)) {
    writeFileSync(path.join(out, filename), bytes);
  }
  for (const [maskName, mask] of Object.entries(masks)) {
    writeFileSync(
      path.join(out, `${req.name}_mask-${maskName}.png`),
      textureToPNG(mask as never),
    );
  }

  writeFileSync(path.join(out, "request.json"), JSON.stringify(req, null, 2));
  const manifest = {
    generator: "wellingfeng/Meshova + voxel-frontier production recipes",
    generatorCommit: process.env.MESHOVA_COMMIT ?? "unknown",
    styleId: PRODUCTION_STYLE_ID,
    deterministic: true,
    proceduralSourceOnly: true,
    seamlessByConstruction: true,
    material: req.name,
    resolution: req.resolution,
    profile: req.profile ?? "signature",
    preset: req.preset,
    pbrFiles: Object.keys(exported.files).sort(),
    maskFiles: Object.keys(masks)
      .map((name) => `${req.name}_mask-${name}.png`)
      .sort(),
  };
  writeFileSync(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 2));
  console.log(JSON.stringify({ ok: true, output: out, ...manifest }, null, 2));
  return manifest;
}

const requestPath = process.argv[2] ?? "vf-request.json";
const envelope = JSON.parse(readFileSync(requestPath, "utf8")) as Envelope;
const requests = "materials" in envelope ? envelope.materials : [envelope];
if (!Array.isArray(requests) || requests.length === 0) {
  throw new Error("No materials requested");
}

const names = new Set<string>();
for (const req of requests) {
  if (!req.name || names.has(req.name)) {
    throw new Error(`Invalid or duplicate material name: ${String(req.name)}`);
  }
  names.add(req.name);
}

const manifests = requests.map(bakeOne);
console.log(
  JSON.stringify(
    {
      ok: true,
      styleId: PRODUCTION_STYLE_ID,
      materialCount: manifests.length,
      materials: manifests.map((m) => m.material),
    },
    null,
    2,
  ),
);
