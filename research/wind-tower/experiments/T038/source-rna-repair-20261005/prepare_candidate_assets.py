"""Package actual candidate files, verifying every ZIP member after creation."""
from pathlib import Path
import hashlib, json, zipfile

ROOT = Path(__file__).resolve().parent
native = json.loads((ROOT / 'native-blade-candidate.json').read_text(encoding='utf-8'))
launch = json.loads((ROOT / 'candidate-launch.json').read_text(encoding='utf-8'))
assert native['status'].startswith('candidate-created/')
assert native['sources_unchanged'] and not native['solver_submitted']
run = Path(launch['run_directory'])
payload = {}
finalization = json.loads((ROOT / 'candidate-finalization.json').read_text(encoding='utf-8'))
assert finalization['status'] == 'final-closed-files-verified'
for output in finalization['outputs']:
    p = Path(output['path']); raw = p.read_bytes()
    assert len(raw) == output['bytes'] and hashlib.sha256(raw).hexdigest() == output['sha256']
    payload[p.name] = raw
for name in ['config.json', 'build_blade_candidate_native.py', 'native-blade-candidate.json', 'execution.log', 'saved-candidate-reopen.json', 'reopen-execution.log', 'verify_saved_candidate_native.py']:
    payload['execution/' + name] = (run / name).read_bytes()
payload['execution/candidate-finalization.json'] = (ROOT / 'candidate-finalization.json').read_bytes()
zip_path = run / 'candidate-assets.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for name, raw in payload.items(): z.writestr(name, raw)
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == set(payload)
    for name, raw in payload.items(): assert z.read(name) == raw
manifest = {
    'task': 'T038-S4', 'zip_local_path': str(zip_path),
    'zip_bytes': zip_path.stat().st_size, 'zip_sha256': hashlib.sha256(zip_path.read_bytes()).hexdigest(),
    'scope': 'Actual isolated Standard blade CAE and exported input; no solver validation or whole-RNA integration.',
    'members': [{'name': n, 'bytes': len(d), 'sha256': hashlib.sha256(d).hexdigest()} for n, d in payload.items()],
    'member_readback_verified': True,
}
(ROOT / 'candidate-assets-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'zip': str(zip_path), 'bytes': manifest['zip_bytes'], 'members': len(payload), 'verified': True}))
