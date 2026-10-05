"""Hash outputs after Abaqus closure and verify saved CAE can be reopened."""
from pathlib import Path
import hashlib, json, shutil, os, subprocess, time
ROOT = Path(__file__).resolve().parent
launch = json.loads((ROOT / 'candidate-launch.json').read_text(encoding='utf-8'))
native = json.loads((ROOT / 'native-blade-candidate.json').read_text(encoding='utf-8'))
run = Path(launch['run_directory'])
script = run / 'verify_saved_candidate_native.py'; shutil.copyfile(ROOT / script.name, script)
cmd = ['cmd.exe', '/d', '/c', 'D:/Abaqus/Commands/abaqus.bat', 'cae', 'noGUI=' + str(script), '--', str(run / 'config.json')]
env = os.environ.copy(); env['TEMP'] = str(run / 'temp'); env['TMP'] = str(run / 'temp')
start = time.monotonic()
with (run / 'reopen-execution.log').open('wb') as log:
    p = subprocess.run(cmd, cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT,
                       timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
reopen = json.loads((run / 'saved-candidate-reopen.json').read_text(encoding='utf-8'))
assert p.returncode == 0 and reopen['status'] == 'reopened-successfully' and reopen['unchanged']
assert reopen['model_names'] == [native['model']]
m = reopen['models'][native['model']]
assert set(m['parts']) == set(native['parts'])
for name, part_data in m['parts'].items():
    original = native['parts'][name]
    for key in ['nodes', 'elements', 'element_types']: assert part_data[key] == original[key]
    assert part_data['layups'] == {k: v['plies'] for k, v in original['composite_layups'].items()}
assert set(m['materials']) == set(native['materials']) and m['constraints'] == len(native['constraints'])
outputs = []
for o in native['outputs']:
    path = Path(o['path']); raw = path.read_bytes()
    outputs.append({'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'pre_close_record': o, 'pre_close_identity_same': len(raw) == o['bytes'] and hashlib.sha256(raw).hexdigest() == o['sha256']})
report = {'status': 'final-closed-files-verified', 'outputs': outputs,
          'note': 'The native report hashed the CAE before Mdb.close; the database file finalizes on close. Use these post-close fingerprints.',
          'reopen': reopen, 'reopen_return_code': p.returncode, 'reopen_wall_seconds': time.monotonic() - start,
          'command': cmd, 'no_solver_submitted': True}
(ROOT / 'candidate-finalization.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
for name in ['saved-candidate-reopen.json', 'reopen-execution.log']: shutil.copyfile(run / name, ROOT / name)
print(json.dumps({'status': report['status'], 'outputs': [{'bytes': o['bytes'], 'sha256': o['sha256']} for o in outputs]}))
