# -*- coding: utf-8 -*-
"""Create an isolated Standard blade replacement candidate from official inputs.

No source CAE is opened or changed and no solver job is submitted.
"""
from abaqus import Mdb
from abaqusConstants import *
import part, material, section, assembly, step, interaction, load, mesh, job
import os, sys, json, hashlib, traceback, datetime
from collections import Counter

cfg = json.load(open(sys.argv[-1], 'r', encoding='utf-8'))
out = cfg['output_directory']
report = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'solver_submitted': False, 'source_cae_opened': False,
          'scope': 'Independent official detailed blade candidate; not integrated into user RNA or M2.',
          'source_records': cfg['source_records']}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(4194304), b''):
            h.update(b)
    return h.hexdigest()


def serial(v):
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (tuple, list)):
        return [serial(x) for x in v]
    if isinstance(v, dict):
        return {str(k): serial(x) for k, x in v.items()}
    return str(v)


def attrs(obj, names):
    d = {}
    for n in names:
        try:
            d[n] = serial(getattr(obj, n))
        except Exception:
            pass
    return d


def region_labels(p, raw):
    if hasattr(raw, 'elements'):
        return sorted(int(e.label) for e in raw.elements)
    if isinstance(raw, (tuple, list)):
        for key in ['sets', 'allSets', 'allInternalSets']:
            repo = getattr(p, key, {})
            if raw[0] in repo:
                return sorted(int(e.label) for e in repo[raw[0]].elements)
    raise RuntimeError('Cannot resolve native section region: ' + str(raw))


def flush():
    with open(os.path.join(out, 'native-blade-candidate.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


db = None
try:
    for rec in cfg['source_records']:
        assert sha(rec['copy']) == rec['sha256'] == sha(rec['original'])
    db = Mdb()
    os.chdir(cfg['source_directory'])
    model_name = 'DTU10MW_BLADE_STANDARD_CANDIDATE'
    m = db.ModelFromInputFile(name=model_name, inputFileName=cfg['master'])
    if 'Model-1' in db.models:
        del db.models['Model-1']
    # Model.description is read-only in this Abaqus release; keep scope in report.
    report['model'] = model_name
    report['parts'] = {}
    report['sections'] = {}
    report['materials'] = {}
    for name, sec in m.sections.items():
        rec = {'class': type(sec).__name__, 'properties': attrs(sec, ['material', 'thickness', 'symmetric'])}
        try:
            rec['plies'] = [attrs(ply, ['thickness', 'material', 'orientAngle', 'numIntPts', 'plyName']) for ply in sec.layup]
        except Exception:
            pass
        report['sections'][name] = rec
    for name, mat in m.materials.items():
        rec = {}
        for prop in ['density', 'elastic']:
            try:
                rec[prop] = attrs(getattr(mat, prop), ['table', 'type'])
            except Exception:
                pass
        report['materials'][name] = rec
    for name, p in m.parts.items():
        rec = {'nodes': len(p.nodes), 'elements': len(p.elements),
               'element_types': dict(Counter(str(e.type) for e in p.elements)),
               'sections': [], 'composite_layups': {}, 'material_orientations': []}
        covered = set()
        for assignment in p.sectionAssignments:
            labels = region_labels(p, assignment.region)
            covered.update(labels)
            rec['sections'].append({'section': assignment.sectionName,
                                    'class': type(m.sections[assignment.sectionName]).__name__,
                                    'elements': len(labels), 'element_labels': labels,
                                    'suppressed': bool(assignment.suppressed)})
        for n, layup in p.compositeLayups.items():
            rec['composite_layups'][n] = {'suppressed': bool(layup.suppressed), 'plies': len(layup.plies)}
        for orient in p.materialOrientations:
            rec['material_orientations'].append(attrs(orient, ['orientationType', 'axis', 'angle', 'stackDirection', 'localCsys', 'region']))
        rec['section_assigned_element_labels'] = sorted(covered)
        rec['all_elements_have_section_assignment'] = covered == set(int(e.label) for e in p.elements)
        report['parts'][name] = rec
    report['instances'] = {n: {'part': i.partName, 'nodes': len(i.nodes), 'elements': len(i.elements),
                                'element_types': dict(Counter(str(e.type) for e in i.elements))}
                           for n, i in m.rootAssembly.instances.items()}
    report['constraints'] = {n: {'class': type(c).__name__, 'properties': attrs(c, ['suppressed', 'couplingType', 'u1', 'u2', 'u3', 'ur1', 'ur2', 'ur3', 'surface', 'controlPoint'])}
                             for n, c in m.constraints.items()}
    report['steps'] = {n: {'class': type(s).__name__, 'properties': attrs(s, ['numEigen', 'eigensolver', 'timePeriod', 'nlgeom'])}
                       for n, s in m.steps.items()}
    report['boundary_conditions'] = {n: {'class': type(b).__name__, 'properties': attrs(b, ['suppressed', 'region', 'u1', 'u2', 'u3', 'ur1', 'ur2', 'ur3'])}
                                    for n, b in m.boundaryConditions.items()}
    os.chdir(out)
    job_name = 'RNA_REPAIR_S1_DTU_BLADE_STANDARD'
    db.Job(name=job_name, model=model_name, type=ANALYSIS)
    db.jobs[job_name].writeInput(consistencyChecking=ON)
    report['exported_input'] = os.path.join(out, job_name + '.inp')
    report['cae'] = os.path.join(out, job_name + '.cae')
    db.saveAs(pathName=report['cae'])
    report['outputs'] = [{'path': p, 'bytes': os.path.getsize(p), 'sha256': sha(p)}
                         for p in [report['exported_input'], report['cae']]]
    report['status'] = 'candidate-created/roundtrip-audit-pending/not-solver-validated'
except Exception:
    report['status'] = 'failed'
    report['error'] = traceback.format_exc()
finally:
    report['sources_unchanged'] = all(sha(r['original']) == r['sha256'] == sha(r['copy']) for r in cfg['source_records'])
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    flush()
    if db is not None:
        try:
            db.close()
        except Exception:
            pass
    print(json.dumps({'status': report['status'], 'sources_unchanged': report['sources_unchanged'], 'solver_submitted': False}))
if report['status'] == 'failed' or not report['sources_unchanged']:
    raise SystemExit(1)
