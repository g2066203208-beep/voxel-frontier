#!/usr/bin/env python3
"""Read-only S10 Abaqus ODB integration-point stress export; NEVER grants physics PASS.

Use Abaqus Python (odbAccess) with an independently reviewed RUN card. Output
is a provisional CSV plus manifest; it is deliberately rejected by the S10
rainflow/Miner production gates until separate native/physical sign-off.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

CLASSES = {'concrete', 'ordinary_rebar', 'prestressing_strand', 'structural_steel'}
FIELDS = ('time_s', 'stress_MPa')
REQUIRED = ('run_id', 'inp_sha256', 'odb_sha256', 'step', 'instance', 'element_set',
            'element_label', 'integration_point', 'material_class', 'material_id',
            'stress_component', 'stress_basis', 'stress_location', 'expected_frames',
            'dt_s', 'native_log_sha256')


def insist(ok, message):
    if not ok:
        raise ValueError(message)


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def is_sha(s):
    return isinstance(s, str) and len(s) == 64 and all(c in '0123456789abcdef' for c in s)


def unique_key(mapping, requested):
    matches = [k for k in mapping.keys() if str(k).upper() == str(requested).upper()]
    insist(len(matches) == 1, 'MISSING_OR_AMBIGUOUS_ODB_KEY: ' + str(requested))
    return matches[0]


def validate_card(card):
    insist(isinstance(card, dict), 'RUN_CARD_NOT_OBJECT')
    for k in REQUIRED:
        insist(k in card and card[k] not in ('', None), 'MISSING_RUN_CARD_FIELD: ' + k)
    insist(card['material_class'] in CLASSES, 'INVALID_MATERIAL_CLASS')
    insist(card['stress_component'] == 'S11', 'ONLY_S11_SUPPORTED_NO_PRINCIPAL_OR_HOTSPOT')
    insist(card['stress_basis'] in ('ODB_GLOBAL_S11', 'ODB_ELEMENT_LOCAL_S11', 'TRUSS_AXIAL_S11'),
           'UNDECLARED_STRESS_COORDINATES')
    insist(card['stress_basis'] != 'TRUSS_AXIAL_S11' or
           card['material_class'] in ('ordinary_rebar', 'prestressing_strand'),
           'TRUSS_BASIS_WRONG_MATERIAL')
    for k in ('inp_sha256', 'odb_sha256'):
        insist(is_sha(card[k]), 'INVALID_SHA256: ' + k)
    logs = card['native_log_sha256']
    insist(isinstance(logs, dict) and set(logs) == {'dat', 'msg', 'sta', 'log'},
           'NATIVE_LOG_PROVENANCE_INCOMPLETE')
    insist(all(is_sha(s) for s in logs.values()), 'INVALID_NATIVE_LOG_SHA256')
    for k in ('element_label', 'integration_point', 'expected_frames'):
        insist(type(card[k]) is int and card[k] > 0, 'INVALID_POSITIVE_INT: ' + k)
    if 'section_point' in card:
        insist(type(card['section_point']) is int and card['section_point'] > 0,
               'INVALID_SECTION_POINT')
    dt = float(card['dt_s'])
    insist(math.isfinite(dt) and dt > 0, 'INVALID_DT')
    insist(card['expected_frames'] >= 3, 'INSUFFICIENT_FRAMES')
    insist(card.get('initial_state_review', 'UNVERIFIED') == 'UNVERIFIED',
           'THIS_EXTRACTOR_MUST_NOT_CERTIFY_INITIAL_STATE')
    return card


def scalar_s11(v):
    d = v.data
    if isinstance(d, (int, float)):
        return float(d)
    insist(len(d) >= 1, 'EMPTY_S_TENSOR')
    return float(d[0])


def extract(odb, card):
    """Mockable, read-only ODB adapter; checks exact point in every frame."""
    validate_card(card)
    step = odb.steps[unique_key(odb.steps, card['step'])]
    inst = odb.rootAssembly.instances[unique_key(odb.rootAssembly.instances, card['instance'])]
    region = inst.elementSets[unique_key(inst.elementSets, card['element_set'])]
    frames = step.frames
    insist(len(frames) == card['expected_frames'], 'FRAME_COUNT_MISMATCH')
    times, stresses = [], []
    for frame in frames:
        t = float(frame.frameValue)
        insist(math.isfinite(t), 'NONFINITE_FRAME_TIME')
        insist('S' in frame.fieldOutputs, 'MISSING_S_FIELD')
        candidates = frame.fieldOutputs['S'].getSubset(region=region).values
        selected = []
        for v in candidates:
            if str(v.instance.name).upper() != str(inst.name).upper():
                continue
            if int(v.elementLabel) != card['element_label']:
                continue
            if int(getattr(v, 'integrationPoint', 0) or 0) != card['integration_point']:
                continue
            section = getattr(v, 'sectionPoint', None)
            section_no = int(getattr(section, 'number', 0) or 0)
            if section_no != card.get('section_point', 0):
                continue
            insist(str(getattr(v, 'position', 'INTEGRATION_POINT')) == 'INTEGRATION_POINT',
                   'NOT_INTEGRATION_POINT')
            selected.append(scalar_s11(v))
        insist(len(selected) == 1, 'MISSING_OR_DUPLICATE_STRESS_POINT')
        s = selected[0]
        insist(math.isfinite(s), 'NONFINITE_LOCAL_STRESS')
        times.append(t)
        stresses.append(s / 1e6)  # ODB stress unit is Pa ONLY for SI (m,kg,s,N) model.
    dt = float(card['dt_s'])
    for i, (a, b) in enumerate(zip(times, times[1:])):
        insist(b > a, 'NONMONOTONIC_FRAME_TIME')
        insist(abs((b-a)-dt) <= max(1e-9, 1e-7*dt), 'NONUNIFORM_OR_MISSING_FRAMES')
    insist(card.get('odb_stress_unit') == 'Pa', 'UNVERIFIED_ODB_STRESS_UNIT')
    insist(card.get('odb_time_unit') == 's', 'UNVERIFIED_ODB_TIME_UNIT')
    return times, stresses


def csv_bytes(times, stresses):
    out = io.StringIO(newline='')
    w = csv.writer(out, lineterminator='\n')
    w.writerow(FIELDS)
    for t, s in zip(times, stresses):
        w.writerow((format(t, '.17g'), format(s, '.17g')))
    return out.getvalue().encode('utf-8')


def self_test():
    class Obj:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
    def mock(times=(0, 0.1, 0.2), values=(1e6, 3e6, 1e6), duplicate=False):
        inst = Obj(name='STEEL-1', elementSets={'SET_A': object()})
        frames = []
        for t, s in zip(times, values):
            val = Obj(instance=inst, elementLabel=17, integrationPoint=1,
                      sectionPoint=None, position='INTEGRATION_POINT', data=(s, 0, 0, 0, 0, 0))
            vals = [val, val] if duplicate else [val]
            field = Obj(getSubset=lambda region, vals=vals: Obj(values=vals))
            frames.append(Obj(frameValue=t, fieldOutputs={'S': field}))
        return Obj(steps={'Wind': Obj(frames=frames)},
                   rootAssembly=Obj(instances={'STEEL-1': inst}))
    card = dict(run_id='SYNTHETIC_NO_NATIVE', inp_sha256='a'*64,
                odb_sha256='b'*64, step='Wind', instance='STEEL-1', element_set='SET_A',
                element_label=17, integration_point=1, material_class='structural_steel',
                material_id='TEST', stress_component='S11', stress_basis='ODB_GLOBAL_S11',
                stress_location='SYNTHETIC', expected_frames=3, dt_s=0.1,
                native_log_sha256={k:'c'*64 for k in ('dat','msg','sta','log')},
                odb_stress_unit='Pa', odb_time_unit='s')
    times, stress = extract(mock(), card)
    assert times == [0, 0.1, 0.2] and stress == [1, 3, 1]
    raw = csv_bytes(times, stress)
    assert raw.startswith(b'time_s,stress_MPa\n')
    cases = [
        (mock(), dict(card, material_class='unknown')),
        (mock(), dict(card, stress_component='MISES')),
        (mock(), dict(card, stress_basis='TRUSS_AXIAL_S11')),
        (mock(), dict(card, odb_stress_unit='MPa')),
        (mock(), dict(card, native_log_sha256={})),
        (mock(), dict(card, element_label=18)),
        (mock(), dict(card, integration_point=2)),
        (mock(), dict(card, expected_frames=4)),
        (mock(times=(0, 0.1, 0.1)), card),
        (mock(times=(0, 0.1, 0.3)), card),
        (mock(values=(1e6, float('nan'), 1e6)), card),
        (mock(duplicate=True), card),
        (mock(), dict(card, initial_state_review='VERIFIED')),
        (mock(), dict(card, inp_sha256='UNBOUND')),
    ]
    for i, (odb, meta) in enumerate(cases):
        try: extract(odb, meta)
        except ValueError: pass
        else: raise AssertionError('negative test accepted: %d' % i)
    return {'status':'PASS_MOCK_ONLY', 'positive_tests':1,
            'negative_tests':len(cases), 'synthetic_csv_sha256':sha_bytes(raw),
            'native_odb_runs':0, 'physical_pass':False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--run-card', type=Path)
    ap.add_argument('--inp', type=Path)
    ap.add_argument('--odb', type=Path)
    ap.add_argument('--logs-dir', type=Path)
    ap.add_argument('--out-dir', type=Path)
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return
    if not all((args.run_card, args.inp, args.odb, args.logs_dir, args.out_dir)):
        ap.error('require --run-card --inp --odb --logs-dir --out-dir or --self-test')
    insist(not args.out_dir.exists(), 'REFUSE_OVERWRITE_OUTPUT')
    card_raw = args.run_card.read_bytes()
    card = validate_card(json.loads(card_raw.decode('utf-8')))
    insist(sha_file(args.inp) == card['inp_sha256'], 'INP_SHA256_MISMATCH')
    insist(sha_file(args.odb) == card['odb_sha256'], 'ODB_SHA256_MISMATCH')
    for suffix, expected in card['native_log_sha256'].items():
        path = args.logs_dir / (args.odb.stem + '.' + suffix)
        insist(path.is_file() and sha_file(path) == expected,
               'MISSING_OR_MISMATCHED_NATIVE_LOG: ' + suffix)
    try:
        from odbAccess import openOdb
    except ImportError as exc:
        raise SystemExit('NEED_NATIVE_ABAQUS_PYTHON: ' + str(exc))
    odb = openOdb(str(args.odb), readOnly=True)
    try:
        times, stresses = extract(odb, card)
    finally:
        odb.close()
    raw = csv_bytes(times, stresses)
    manifest = {
        'status': 'NATIVE_EXTRACTION_QC_ONLY_PHYSICS_HOLD',
        'stress_owner': 'UNVERIFIED_NATIVE_LOCAL_STRESS',
        'initial_state': 'NEED_INDEPENDENT_NATIVE_REVIEW',
        'source_sha256': sha_bytes(raw),
        'run_card_sha256': sha_bytes(card_raw),
        'run_id': card['run_id'], 'step': card['step'],
        'instance': card['instance'], 'element_set': card['element_set'],
        'element_label': card['element_label'],
        'integration_point': card['integration_point'],
        'section_point': card.get('section_point', 0),
        'odb_stress_unit': card['odb_stress_unit'], 'odb_time_unit': card['odb_time_unit'],
        'time_start_s': times[0], 'time_end_s': times[-1],
        'inp_sha256': card['inp_sha256'], 'odb_sha256': card['odb_sha256'],
        'native_log_sha256': card['native_log_sha256'],
        'material_class': card['material_class'], 'material_id': card['material_id'],
        'stress_location': card['stress_location'],
        'stress_component': card['stress_component'], 'stress_basis': card['stress_basis'],
        'n_samples': len(times), 'dt_s': card['dt_s'],
        'physical_error_budget': 'NEED_ESTIMATE_MESH_STRESS_BASIS_PT_STATE_AND_RUN_QC',
        'material_model_ref': 'NEED_MATERIAL_SPECIFIC_S_N_AND_VALIDATION',
        'mean_stress_rule': 'NONE_KEEP_MEAN',
        'warning': 'No physical PASS; do not promote to VERIFIED_LOCAL_MATERIAL_STRESS without independent S01-S04/S07 and RUN review.'}
    args.out_dir.mkdir(parents=True)
    (args.out_dir / 'local_stress.csv').write_bytes(raw)
    (args.out_dir / 'local_stress_manifest.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'status':manifest['status'], 'csv_sha256':manifest['source_sha256'],
                      'frames':len(times)}, sort_keys=True))


if __name__ == '__main__':
    main()
