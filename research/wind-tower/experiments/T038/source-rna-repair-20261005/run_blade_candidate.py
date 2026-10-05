"""Copy verified official inputs to D:, create candidate CAE, never submit solver."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, os, subprocess, time

ROOT = Path(__file__).resolve().parent
SOURCE = Path('D:/Codex-research-native/t026-rna-official-properties-20261004')
names = ['refblade_master.inp', 'refblade_mesh.inp', 'refblade_materials.inp', 'refblade_layup.inp', 'refblade_te_glue.inp', 'README.txt']


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4194304), b''):
            h.update(b)
    return h.hexdigest()


index = json.loads((SOURCE / 'source-index.json').read_text(encoding='utf-8'))
known = {r['repository_path']: r for r in index['records']}
run = Path('D:/Codex-research-native/source-rna-repair-20261005') / datetime.now().strftime('%Y%m%d_%H%M%S')
run.mkdir(parents=True, exist_ok=False)
src = run / 'official-source'; src.mkdir()
temp = run / 'temp'; temp.mkdir()
records = []
for name in names:
    rel = 'structural_models/ABAQUS/' + name
    p = SOURCE / rel
    digest = sha(p)
    assert digest == known[rel]['sha256'], (name, digest)
    copy = src / name; shutil.copy2(p, copy)
    assert sha(copy) == digest
    records.append({'original': str(p), 'copy': str(copy), 'sha256': digest, 'bytes': p.stat().st_size, 'source_repository_path': rel})
cfg = {'output_directory': str(run), 'source_directory': str(src), 'master': str(src / 'refblade_master.inp'), 'source_records': records}
config = run / 'config.json'; config.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
script = run / 'build_blade_candidate_native.py'; shutil.copyfile(ROOT / script.name, script)
env = os.environ.copy(); env['TEMP'] = str(temp); env['TMP'] = str(temp)
cmd = ['cmd.exe', '/d', '/c', 'D:/Abaqus/Commands/abaqus.bat', 'cae', 'noGUI=' + str(script), '--', str(config)]
record = {'started_utc': datetime.now(timezone.utc).isoformat(), 'command': cmd, 'run_directory': str(run), 'config': cfg, 'solver_submitted': False}
launch = ROOT / 'candidate-launch.json'
launch.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
start = time.monotonic()
with (run / 'execution.log').open('wb') as log:
    process = subprocess.Popen(cmd, cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    record['launcher_pid'] = process.pid
    rc = process.wait(timeout=300)
record.update({'return_code': rc, 'wall_seconds': time.monotonic() - start, 'finished_utc': datetime.now(timezone.utc).isoformat()})
for name in ['native-blade-candidate.json', 'execution.log']:
    p = run / name
    if p.exists(): shutil.copyfile(p, ROOT / name)
if (run / 'native-blade-candidate.json').exists():
    r = json.loads((run / 'native-blade-candidate.json').read_text(encoding='utf-8'))
    record['candidate_status'] = r['status']; record['sources_unchanged'] = r['sources_unchanged']
launch.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'return_code': rc, 'wall_seconds': record['wall_seconds'], 'run_directory': str(run), 'candidate_status': record.get('candidate_status')}))
raise SystemExit(rc or (1 if record.get('candidate_status') == 'failed' else 0))
