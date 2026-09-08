const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const gaussian = (x, c, s) => Math.exp(-0.5 * ((x - c) / s) ** 2);
const smooth01 = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const smoothRange = (x, a, b) => smooth01((x - a) / (b - a));

export const MASTER_URL = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2/3dobjs/base.obj';

export const DEFAULT_PARAMS = Object.freeze({
  heightCm: 172,
  sex: 0,
  shoulderWidth: 0,
  chest: 0,
  waist: 0,
  hips: 0,
  torsoLength: 0,
  legLength: 0,
  armLength: 0,
  bodyFat: 0,
  muscle: 0,
  thigh: 0,
  calf: 0,
  headScale: 0,
  neckWidth: 0,
  chestDepth: 0,
  hipDepth: 0
});

export const PRESETS = Object.freeze({
  male: {
    heightCm: 180, sex: 0.92, shoulderWidth: 0.12, chest: 0.05, waist: 0.00,
    hips: -0.03, torsoLength: 0.04, legLength: 0.03, armLength: 0.04,
    bodyFat: -0.08, muscle: 0.28, thigh: 0.03, calf: 0.04,
    headScale: -0.02, neckWidth: 0.08, chestDepth: 0.04, hipDepth: -0.02
  },
  female: {
    heightCm: 166, sex: -0.92, shoulderWidth: -0.05, chest: 0.02, waist: -0.06,
    hips: 0.08, torsoLength: -0.02, legLength: 0.05, armLength: -0.01,
    bodyFat: 0.08, muscle: -0.08, thigh: 0.06, calf: 0.01,
    headScale: 0.01, neckWidth: -0.06, chestDepth: 0.05, hipDepth: 0.05
  }
});

function triangulateFace(line) {
  const ids = line.slice(2).trim().split(/\s+/).map(tok => Number(tok.split('/')[0]) - 1);
  const tris = [];
  for (let i = 1; i + 1 < ids.length; i++) tris.push([ids[0], ids[i], ids[i + 1]]);
  return tris;
}

function compactTopology(vertices, faces) {
  const remap = new Map();
  const compactVertices = [];
  const sourceVertexIds = [];
  const compactFaces = faces.map(face => face.map(oldId => {
    if (!remap.has(oldId)) {
      remap.set(oldId, compactVertices.length);
      sourceVertexIds.push(oldId);
      compactVertices.push(vertices[oldId]);
    }
    return remap.get(oldId);
  }));
  return { vertices: compactVertices, faces: compactFaces, sourceVertexIds };
}

export function parseOBJ(text) {
  const vertices = [];
  const allFaces = [];
  const bodyFaces = [];
  let group = '';

  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line[0] === '#') continue;
    if (line.startsWith('v ')) {
      const p = line.split(/\s+/);
      vertices.push([Number(p[1]), Number(p[2]), Number(p[3])]);
    } else if (line.startsWith('g ')) {
      group = line.slice(2).trim().split(/\s+/)[0] || '';
    } else if (line.startsWith('f ')) {
      const tris = triangulateFace(line);
      allFaces.push(...tris);
      if (group === 'body') bodyFaces.push(...tris);
    }
  }

  const selectedFaces = bodyFaces.length >= 100 ? bodyFaces : allFaces;
  if (vertices.length < 100 || selectedFaces.length < 100) {
    throw new Error('Master OBJ does not look like a human body mesh.');
  }
  return compactTopology(vertices, selectedFaces);
}

function axisFrame(vertices) {
  const mins = [Infinity, Infinity, Infinity];
  const maxs = [-Infinity, -Infinity, -Infinity];
  for (const v of vertices) for (let a = 0; a < 3; a++) {
    mins[a] = Math.min(mins[a], v[a]); maxs[a] = Math.max(maxs[a], v[a]);
  }
  const ranges = maxs.map((v, a) => v - mins[a]);
  const order = [0, 1, 2].sort((a, b) => ranges[b] - ranges[a]);
  const up = order[0], depth = order[2], width = order[1];
  return { mins, maxs, ranges, up, depth, width };
}

export function canonicalize(parsed) {
  const frame = axisFrame(parsed.vertices);
  const H = frame.ranges[frame.up];
  const cw = (frame.mins[frame.width] + frame.maxs[frame.width]) / 2;
  const cd = (frame.mins[frame.depth] + frame.maxs[frame.depth]) / 2;
  const verts = parsed.vertices.map(v => [
    (v[frame.width] - cw) / H,
    (v[frame.up] - frame.mins[frame.up]) / H,
    (v[frame.depth] - cd) / H
  ]);
  const sourceToCompact = new Map(parsed.sourceVertexIds.map((id,i)=>[id,i]));
  return {
    vertices: verts,
    faces: parsed.faces.map(f => [...f]),
    sourceVertexIds: [...parsed.sourceVertexIds],
    sourceToCompact,
    sourceFrame: frame,
    phenotypeBasis: null
  };
}

function remapHeight(y, p) {
  const src = [0.00, 0.055, 0.285, 0.500, 0.610, 0.820, 0.885, 1.000];
  const leg = clamp(p.legLength, -1, 1);
  const torso = clamp(p.torsoLength, -1, 1);
  const dst = [
    0.00,
    0.055 + leg * 0.003,
    0.285 + leg * 0.018,
    0.500 + leg * 0.042,
    0.610 + leg * 0.030 + torso * 0.010,
    0.820 + leg * 0.012 + torso * 0.032,
    0.885 + torso * 0.018,
    1.000
  ];
  for (let i = 0; i < src.length - 1; i++) {
    if (y <= src[i + 1]) return lerp(dst[i], dst[i + 1], (y - src[i]) / (src[i + 1] - src[i]));
  }
  return y;
}

function deformVertex(v0, p, maxAbsX, phenotypeDriven) {
  let [x, y, z] = v0;
  y = remapHeight(y, p);

  const sex = phenotypeDriven ? 0 : clamp(p.sex, -1, 1);
  const fat = phenotypeDriven ? 0 : clamp(p.bodyFat, -1, 1);
  const muscle = phenotypeDriven ? 0 : clamp(p.muscle, -1, 1);

  const shoulder = gaussian(y, 0.815, 0.075);
  const chest = gaussian(y, 0.710, 0.105);
  const waist = gaussian(y, 0.595, 0.080);
  const hip = gaussian(y, 0.505, 0.090);
  const thigh = gaussian(y, 0.370, 0.120);
  const calf = gaussian(y, 0.175, 0.090);
  const neck = gaussian(y, 0.855, 0.035);
  const trunk = gaussian(y, 0.610, 0.230);

  let sx = 1;
  sx += shoulder * (0.115 * p.shoulderWidth + 0.040 * sex + 0.030 * muscle);
  sx += chest * (0.090 * p.chest + 0.020 * sex + 0.030 * muscle + 0.030 * fat);
  sx += waist * (0.105 * p.waist + 0.020 * sex + 0.070 * fat);
  sx += hip * (0.135 * p.hips - 0.040 * sex + 0.055 * fat);
  sx += thigh * (0.090 * p.thigh - 0.010 * sex + 0.050 * fat + 0.025 * muscle);
  sx += calf * (0.080 * p.calf + 0.025 * muscle + 0.020 * fat);
  sx += neck * (0.100 * p.neckWidth + 0.025 * sex + 0.030 * muscle);

  let sz = 1;
  sz += chest * (0.110 * p.chestDepth + 0.035 * fat + 0.025 * muscle);
  sz += waist * (0.090 * p.waist + 0.095 * fat);
  sz += hip * (0.120 * p.hipDepth + 0.060 * fat);
  sz += thigh * (0.055 * p.thigh + 0.040 * fat + 0.020 * muscle);
  sz += calf * (0.045 * p.calf + 0.020 * muscle);
  sz += trunk * 0.020 * fat;

  x *= sx;
  z *= sz;

  const lateral = Math.abs(v0[0]) / Math.max(maxAbsX, 1e-6);
  const armW = smoothRange(lateral, 0.48, 0.72) * gaussian(y, 0.690, 0.190);
  if (armW > 1e-4) {
    const sign = Math.sign(x) || 1;
    const ax = sign * maxAbsX * 0.33;
    const ay = 0.795;
    const s = 1 + 0.085 * clamp(p.armLength, -1, 1) * armW;
    x = lerp(x, ax + (x - ax) * s, armW);
    y = lerp(y, ay + (y - ay) * s, armW);
  }

  const headW = smoothRange(y, 0.865, 0.925);
  if (headW > 0) {
    const hs = 1 + 0.075 * clamp(p.headScale, -1, 1);
    const cy = 0.935;
    x = lerp(x, x * hs, headW);
    z = lerp(z, z * hs, headW);
    y = lerp(y, cy + (y - cy) * hs, headW);
  }
  return [x, y, z];
}

export function generateHuman(master, params = {}) {
  const p = { ...DEFAULT_PARAMS, ...params };
  const phenotype = master.phenotypeBasis?.evaluate?.(p) || null;
  const phenotypeDriven = !!phenotype;
  const basisVertices = master.vertices.map((v,i)=> phenotype ? [
    v[0]+phenotype[i*3], v[1]+phenotype[i*3+1], v[2]+phenotype[i*3+2]
  ] : v);

  let maxAbsX = 0;
  for (const v of basisVertices) maxAbsX = Math.max(maxAbsX, Math.abs(v[0]));
  let vertices = basisVertices.map(v => deformVertex(v, p, maxAbsX, phenotypeDriven));

  let minY = Infinity, maxY = -Infinity;
  for (const v of vertices) { minY = Math.min(minY, v[1]); maxY = Math.max(maxY, v[1]); }
  const currentH = maxY - minY;
  const targetH = clamp(p.heightCm, 120, 220) / 100;
  const s = targetH / Math.max(currentH, 1e-6);
  vertices = vertices.map(v => [v[0] * s, (v[1] - minY) * s, v[2] * s]);

  const result = { vertices, faces: master.faces, params: p, phenotypeDriven };
  result.measurements = measureHuman(result);
  return result;
}

function percentile(sorted, q) {
  if (!sorted.length) return 0;
  const i = clamp((sorted.length - 1) * q, 0, sorted.length - 1);
  const lo = Math.floor(i), hi = Math.ceil(i);
  return lerp(sorted[lo], sorted[hi], i - lo);
}

function section(vertices, yTarget, tol, torsoLimit) {
  let pts = vertices.filter(v => Math.abs(v[1] - yTarget) <= tol && Math.abs(v[0]) <= torsoLimit);
  if (pts.length < 20) pts = vertices.filter(v => Math.abs(v[1] - yTarget) <= tol * 1.8 && Math.abs(v[0]) <= torsoLimit * 1.05);
  const xs = pts.map(v => v[0]).sort((a,b) => a-b);
  const zs = pts.map(v => v[2]).sort((a,b) => a-b);
  return { width: percentile(xs,0.98)-percentile(xs,0.02), depth: percentile(zs,0.98)-percentile(zs,0.02) };
}

function edgePlanePoint(a,b,y){
  const da=a[1]-y, db=b[1]-y;
  if((da>0&&db>0)||(da<0&&db<0)||Math.abs(da-db)<1e-12) return null;
  const t=da/(da-db);
  if(t<-1e-8||t>1+1e-8) return null;
  return [lerp(a[0],b[0],t),lerp(a[2],b[2],t)];
}

function meshPlaneCircumference(model,y,torsoLimit){
  let length=0;
  for(const f of model.faces){
    const a=model.vertices[f[0]],b=model.vertices[f[1]],c=model.vertices[f[2]];
    const pts=[];
    for(const e of [[a,b],[b,c],[c,a]]){
      const p=edgePlanePoint(e[0],e[1],y);
      if(p && !pts.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<1e-7)) pts.push(p);
    }
    if(pts.length!==2) continue;
    const mx=(pts[0][0]+pts[1][0])/2;
    if(Math.abs(mx)>torsoLimit) continue;
    length+=Math.hypot(pts[1][0]-pts[0][0],pts[1][1]-pts[0][1]);
  }
  return length;
}

export function measureHuman(model) {
  const vs = model.vertices;
  let minY=Infinity,maxY=-Infinity,minX=Infinity,maxX=-Infinity;
  for (const v of vs) {
    minY=Math.min(minY,v[1]); maxY=Math.max(maxY,v[1]);
    minX=Math.min(minX,v[0]); maxX=Math.max(maxX,v[0]);
  }
  const H = maxY - minY;
  const chestY=minY+H*0.710, waistY=minY+H*0.595, hipY=minY+H*0.505;
  const shoulder = section(vs, minY + H*0.805, H*0.010, H*0.185);

  return {
    heightCm: H * 100,
    shoulderWidthCm: shoulder.width * 100,
    chestCm: meshPlaneCircumference(model,chestY,H*0.165) * 100,
    waistCm: meshPlaneCircumference(model,waistY,H*0.145) * 100,
    hipCm: meshPlaneCircumference(model,hipY,H*0.180) * 100,
    overallSpanCm: (maxX - minX) * 100
  };
}

export function toOBJ(model, name='ProceduralHuman') {
  const out = [`# ${name}`, '# Generated by voxel-frontier Procedural Human'];
  for (const v of model.vertices) out.push(`v ${v[0].toFixed(7)} ${v[1].toFixed(7)} ${v[2].toFixed(7)}`);
  for (const f of model.faces) out.push(`f ${f[0]+1} ${f[1]+1} ${f[2]+1}`);
  return out.join('\n');
}
