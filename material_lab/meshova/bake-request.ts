import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import {
  BILIBILI_MATERIALS,
  bakeStylizedCellRock,
  exportPBR,
  materialFromFields,
  textureToPNG,
  validateMaterial,
} from "../src/index.js";
import { bakeVfBasalt } from "./vf-recipes/vf-basalt.js";

type Request = {
  name: string;
  resolution: number;
  preset: "stylizedCellRock" | "volcanicRock" | "simpleRock" | "vfBasalt";
  profile?: "realistic" | "stylized";
  params: Record<string, unknown>;
};

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
  generator: "wellingfeng/Meshova + voxel-frontier modular recipes",
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
