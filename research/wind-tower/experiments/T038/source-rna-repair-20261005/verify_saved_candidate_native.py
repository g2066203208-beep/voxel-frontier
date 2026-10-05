"""Reopen the final, closed candidate through auxiliary Mdb; never save/submit."""
from abaqus import Mdb
import part, material, section, assembly, step, interaction, load, mesh
import json, os, sys, hashlib, traceback
from collections import Counter
cfg = json.load(open(sys.argv[-1], 'r', encoding='utf-8'))
run = cfg['output_directory']
path = os.path.join(run, 'RNA_REPAIR_S1_DTU_BLADE_STANDARD.cae')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(4194304), b''): h.update(b)
    return h.hexdigest()


report = {'path': path, 'before_sha256': sha(path), 'models': {}, 'solver_submitted': False}
db = None
try:
    db = Mdb(); db.openAuxMdb(pathName=path)
    report['model_names'] = list(db.getAuxMdbModelNames())
    for name in report['model_names']:
        db.copyAuxMdbModel(fromName=name, toName='verify_saved')
        m = db.models['verify_saved']
        report['models'][name] = {
            'parts': {n: {'nodes': len(p.nodes), 'elements': len(p.elements),
                          'element_types': dict(Counter(str(e.type) for e in p.elements)),
                          'layups': {k: len(v.plies) for k, v in p.compositeLayups.items()}}
                      for n, p in m.parts.items()},
            'materials': list(m.materials.keys()), 'constraints': len(m.constraints),
            'steps': {n: {'class': type(s).__name__, 'numEigen': getattr(s, 'numEigen', None)} for n, s in m.steps.items()},
        }
        del db.models['verify_saved']
    db.closeAuxMdb(); report['status'] = 'reopened-successfully'
except Exception:
    report['status'] = 'failed'; report['error'] = traceback.format_exc()
finally:
    if db is not None:
        try: db.close()
        except Exception: pass
    report['after_sha256'] = sha(path)
    report['unchanged'] = report['before_sha256'] == report['after_sha256']
    with open(os.path.join(run, 'saved-candidate-reopen.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
print(json.dumps({'status': report['status'], 'unchanged': report['unchanged']}))
