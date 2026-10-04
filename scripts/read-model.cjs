const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');

async function main() {
  const source = 'research/wind-tower/geometry/DTU158_TOWER_RNA_FULL_ASSEMBLY.step';
  const bytes = fs.readFileSync(source);
  if (!bytes.subarray(0, 100).toString().includes('ISO-10303-21')) throw Error('STEP signature absent (possibly an LFS pointer)');
  const manifest = JSON.parse(fs.readFileSync('research/wind-tower/manifest.json', 'utf8'));
  const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
  const expected = manifest.files.find(file => file.path === source);
  if (!expected || expected.sha256 !== sha256 || expected.bytes !== bytes.length) throw Error('Input does not match registered manifest');
  const occt = await require('occt-import-js')();
  const parameters = { linearUnit: 'meter', linearDeflectionType: 'absolute_value', linearDeflection: 0.0002, angularDeflection: 0.35 };
  const result = occt.ReadStepFile(bytes, parameters);
  if (!result.success || !result.meshes?.length) throw Error('OpenCascade did not produce geometry');
  const bounds = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
  let vertices = 0, triangles = 0, invalidIndices = 0, nonfinite = 0, degenerate = 0;
  const parts = result.meshes.map((mesh, id) => {
    const p = mesh.attributes.position.array, indices = mesh.index.array;
    vertices += p.length / 3; triangles += indices.length / 3;
    for (let i = 0; i < p.length; i++) {
      if (!Number.isFinite(p[i])) nonfinite++;
      bounds.min[i % 3] = Math.min(bounds.min[i % 3], p[i]);
      bounds.max[i % 3] = Math.max(bounds.max[i % 3], p[i]);
    }
    for (let i = 0; i < indices.length; i += 3) {
      const ids = indices.slice(i, i + 3);
      if (ids.some(v => !Number.isInteger(v) || v < 0 || v >= p.length / 3)) { invalidIndices++; continue; }
      const a = ids[0] * 3, b = ids[1] * 3, c = ids[2] * 3;
      const u = [p[b]-p[a], p[b+1]-p[a+1], p[b+2]-p[a+2]];
      const v = [p[c]-p[a], p[c+1]-p[a+1], p[c+2]-p[a+2]];
      const cross = [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
      if (cross.reduce((s,x)=>s+x*x,0) < 1e-24) degenerate++;
    }
    return { id, name: mesh.name || `Part ${id + 1}`, vertices: p.length / 3, triangles: indices.length / 3 };
  });
  if (nonfinite || invalidIndices) throw Error(`Invalid geometry: ${nonfinite} nonfinite values, ${invalidIndices} invalid triangles`);
  const report = { schema: 1, source, sha256, bytes: bytes.length, generatedAt: new Date().toISOString(), reader: 'occt-import-js / OpenCascade', readerVersion: require('occt-import-js/package.json').version, unit: 'm', parameters, bounds, dimensions: bounds.max.map((v,i)=>v-bounds.min[i]), vertices, triangles, checks: { nonfinite, invalidIndices, degenerate }, parts, limitations: ['CAD tessellation is not a finite-element mesh.', 'No material, constraint, stress or solver validation is inferred from geometric checks.'], inputManifest: manifest };
  report.warnings = Math.max(...report.dimensions) < 1 ? ['STEP declares MILLIMETRE; decoded assembly extent is below 1 metre. This conflicts with the research tower scale. Confirm export units before dimensional or engineering use. No silent scale correction applied.'] : [];
  const destination = 'public/research'; fs.mkdirSync(destination, { recursive: true });
  fs.writeFileSync(path.join(destination, 'geometry.json.gz'), zlib.gzipSync(JSON.stringify(result), {level:9}));
  fs.writeFileSync(path.join(destination, 'geometry-report.json'), JSON.stringify(report, null, 2));
  for (const name of fs.readdirSync('research/wind-tower/inspection')) {
    if (name.endsWith('.audit.json.gz')) fs.copyFileSync(path.join('research/wind-tower/inspection',name),path.join(destination,name));
  }
  console.log(JSON.stringify({sha256,parts:parts.length,vertices,triangles,bounds,checks:report.checks}));
}
main().catch(error=>{console.error(error); process.exitCode=1;});
