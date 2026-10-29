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


# SHA-locked diagnostic R335/T057 and independently reconstructed D400/Pe maps.
# Neither map certifies ODB integration points, hotspots, or native equilibrium.
FROZEN_T057_SHA = 'c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db'
SOURCE_MAP_SHA = '502fe65c94a8d060611e6b4293790ed3a5f48174a41b7732a3b221a5195e66fd'
D400_PE_CHILD_SHA = '22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
D400_PE_SOURCE_MAP_SHA = '9850c1983a1bc69cc829f338260a31ff29b4e6ab86660749d453f9cc5791ff83'
SOURCE_MAP_BY_INP = {FROZEN_T057_SHA: SOURCE_MAP_SHA,
                     D400_PE_CHILD_SHA: D400_PE_SOURCE_MAP_SHA}
SOURCE_GROUP_CLASS = {
    'concrete': 'concrete', 'longitudinal_rebar': 'ordinary_rebar',
    'PT': 'prestressing_strand', 'steel_tower': 'structural_steel',
    'hoops_and_ties': 'ordinary_rebar'
}
SOURCE_FIELDS = ('source_part', 'source_group', 'native_instance_from_INP',
                 'native_elset_from_INP', 'section_material_from_INP',
                 'height_candidate_element_label', 'native_integration_point',
                 'native_stress_basis')


def validate_source_binding(card, raw, expected_sha=None,
                            expected_inp_sha=None, expected_rows=68,
                            verified_candidate=None):
    """Fail closed on exact model+map pair; height candidates are NOT hotspots."""
    validate_card(card)
    if expected_sha is None or expected_inp_sha is None:
        insist(card['inp_sha256'] in SOURCE_MAP_BY_INP,
               'S10_UNREGISTERED_MODEL_BRANCH')
        expected_inp_sha = card['inp_sha256']
        expected_sha = SOURCE_MAP_BY_INP[expected_inp_sha]
    insist(sha_bytes(raw) == expected_sha, 'S10_SOURCE_MAP_SHA256_MISMATCH')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    insist(len(rows) == expected_rows, 'S10_SOURCE_MAP_ROW_COUNT_MISMATCH')
    insist(rows and all(k in rows[0] for k in SOURCE_FIELDS),
           'S10_SOURCE_MAP_COLUMNS_MISSING')
    insist(len(set(r['source_part'] for r in rows)) == len(rows),
           'S10_SOURCE_MAP_DUPLICATE_PART')
    insist(card['inp_sha256'] == expected_inp_sha,
           'S10_SOURCE_MAP_WRONG_INP_BRANCH')
    matches = [r for r in rows if r['native_instance_from_INP'].upper() ==
               card['instance'].upper()]
    insist(len(matches) == 1, 'S10_SOURCE_INSTANCE_NOT_UNIQUE')
    row = matches[0]
    insist(row['source_group'] in SOURCE_GROUP_CLASS, 'S10_SOURCE_GROUP_UNKNOWN')
    insist(card['material_class'] == SOURCE_GROUP_CLASS[row['source_group']],
           'S10_MATERIAL_CLASS_NOT_FROM_INP')
    insist(card['material_id'] == row['section_material_from_INP'],
           'S10_MATERIAL_ID_NOT_FROM_INP')
    insist(card['element_set'].upper() == row['native_elset_from_INP'].upper(),
           'S10_ELEMENT_SET_NOT_FROM_INP')
    insist(row['height_candidate_element_label'].strip(),
           'S10_NO_REVIEWED_SOURCE_ELEMENT_CANDIDATE')
    if verified_candidate is None:
        insist(card['element_label'] == int(row['height_candidate_element_label']),
               'S10_ELEMENT_LABEL_NOT_IN_HEIGHT_CANDIDATE')
    else:
        # Only a row returned by SHA-locked candidate table validation may be
        # passed by the production path. This is still source-level, NOT ODB IP.
        insist(card['inp_sha256'] == D400_PE_CHILD_SHA and
               verified_candidate['source_part'] == row['source_part'] and
               verified_candidate['instance'] == card['instance'] and
               verified_candidate['element_set'] == card['element_set'] and
               verified_candidate['section_material'] == card['material_id'] and
               int(verified_candidate['element_label']) == card['element_label'],
               'S10_CANDIDATE_SOURCE_BINDING_MISMATCH')
    insist(not row['native_integration_point'] and not row['native_stress_basis'],
           'S10_SOURCE_MAP_MUST_NOT_CERTIFY_ODB_IP_OR_BASIS')
    # A source-level element label does NOT prove ODB integration-point existence,
    # material stress criterion, initial PT state, or the governing fatigue hotspot.
    return row


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


def self_test(source_map=None, d400_source_map=None):
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

    # Independent synthetic source-identity whitelist: no ODB needed.
    headers = list(SOURCE_FIELDS)
    synthetic = io.StringIO(newline='')
    writer = csv.DictWriter(synthetic, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerow(dict(source_part='CSEG_01', source_group='concrete',
                         native_instance_from_INP='CSEG_01-1',
                         native_elset_from_INP='SET_ALL',
                         section_material_from_INP='C70',
                         height_candidate_element_label='3',
                         native_integration_point='', native_stress_basis=''))
    source_raw = synthetic.getvalue().encode()
    scard = dict(card, inp_sha256='d'*64, instance='CSEG_01-1',
                 element_set='SET_ALL', element_label=3, material_class='concrete',
                 material_id='C70', stress_basis='ODB_GLOBAL_S11')
    validate_source_binding(scard, source_raw, sha_bytes(source_raw), 'd'*64, 1)
    source_negatives = [
        (dict(scard, material_id='HRB500_BASELINE'), source_raw, sha_bytes(source_raw)),
        (dict(scard, material_class='ordinary_rebar'), source_raw, sha_bytes(source_raw)),
        (dict(scard, element_set='WRONG'), source_raw, sha_bytes(source_raw)),
        (dict(scard, element_label=4), source_raw, sha_bytes(source_raw)),
        (dict(scard, instance='CSEG_02-1'), source_raw, sha_bytes(source_raw)),
        (dict(scard, inp_sha256='e'*64), source_raw, sha_bytes(source_raw)),
        (scard, source_raw+b'\n', sha_bytes(source_raw)),
    ]
    for i, (meta, data, digest) in enumerate(source_negatives):
        try: validate_source_binding(meta, data, digest, 'd'*64, 1)
        except ValueError: pass
        else: raise AssertionError('source binding negative accepted: %d' % i)
    real_tests = 0
    if source_map is not None:
        real_source_raw = Path(source_map).read_bytes()
        real = dict(card, inp_sha256=FROZEN_T057_SHA, instance='CSEG_01-1',
                    element_set='SET_ALL', element_label=3, material_class='concrete',
                    material_id='C70', stress_basis='ODB_GLOBAL_S11')
        validate_source_binding(real, real_source_raw)
        real_tests += 1
        for changed in (dict(real, material_id='HRB500_BASELINE'),
                        dict(real, element_label=4),
                        dict(real, instance='SSEG_01-1', element_label=1,
                             material_id='Q345_T057', material_class='structural_steel')):
            try: validate_source_binding(changed, real_source_raw)
            except ValueError: real_tests += 1
            else: raise AssertionError('real map wrong identity accepted')
    if d400_source_map is not None:
        d400_raw = Path(d400_source_map).read_bytes()
        d400 = dict(card, inp_sha256=D400_PE_CHILD_SHA,
                    instance='RBLONG_01-1', element_set='SET_ALL',
                    material_class='ordinary_rebar',
                    material_id='HRB400_D400_DIAGNOSTIC',
                    stress_basis='TRUSS_AXIAL_S11')
        entries = list(csv.DictReader(io.StringIO(d400_raw.decode('utf-8-sig'))))
        source = next(r for r in entries if r['source_part'] == 'RBLONG_01')
        d400['element_label'] = int(source['height_candidate_element_label'])
        validate_source_binding(d400, d400_raw)
        real_tests += 1
        for meta, source_bytes in (
            (dict(d400, material_id='HRB335_T057'), d400_raw),
            (dict(d400, inp_sha256=FROZEN_T057_SHA), d400_raw),
            (dict(d400), real_source_raw if source_map is not None else b'wrong-map'),
            (dict(d400, element_label=d400['element_label'] + 1), d400_raw),
        ):
            try:
                validate_source_binding(meta, source_bytes)
            except ValueError:
                real_tests += 1
            else:
                raise AssertionError('D400 model/source negative accepted')
    return {'status':'PASS_MOCK_ONLY', 'positive_tests':1,
            'negative_tests':len(cases), 'source_binding_negative_tests':len(source_negatives),
            'source_binding_real_map_tests':real_tests,
            'synthetic_csv_sha256':sha_bytes(raw),
            'native_odb_runs':0, 'physical_pass':False}



def inventory_native_odb(odb, max_names=80):
    """Inspect ODB directory/field metadata only; never read stress values or certify physics."""
    insist(type(max_names) is int and max_names > 0, 'INVALID_INVENTORY_LIMIT')
    instances = odb.rootAssembly.instances
    instance_names = sorted(str(k) for k in instances.keys())
    instance_rows = []
    for name in instance_names[:max_names]:
        inst = instances[name]
        sets = sorted(str(k) for k in inst.elementSets.keys())
        instance_rows.append({
            'instance': name,
            'element_set_count': len(sets),
            'element_sets_sample': sets[:max_names],
            'element_sets_truncated': len(sets) > max_names,
            'element_count': len(inst.elements),
            'node_count': len(inst.nodes)})
    step_rows = []
    for step_name in sorted(str(k) for k in odb.steps.keys()):
        frames = odb.steps[step_name].frames
        n = len(frames)
        s_frames = 0
        times = []
        for frame in frames:
            t = float(frame.frameValue)
            insist(math.isfinite(t), 'NONFINITE_ODB_FRAME_TIME')
            times.append(t)
            if 'S' in frame.fieldOutputs:
                s_frames += 1
        samples = []
        for i in sorted(set((0, n // 2, n - 1))) if n else []:
            frame = frames[i]
            has_s = 'S' in frame.fieldOutputs
            labels = (list(getattr(frame.fieldOutputs['S'], 'componentLabels', ()))
                      if has_s else [])
            samples.append({'frame_index': i, 'time_s_unverified': times[i],
                            'has_S': has_s, 'S_components': labels})
        step_rows.append({
            'step': step_name, 'frame_count': n, 'S_frame_count': s_frames,
            'S_present_every_frame': n > 0 and s_frames == n,
            'frame_time_monotonic': all(b > a for a, b in zip(times, times[1:])),
            'first_frame_time_unverified': times[0] if n else None,
            'last_frame_time_unverified': times[-1] if n else None,
            'sampled_frames': samples})
    return {
        'status': 'NATIVE_READ_ONLY_DIRECTORY_INVENTORY_NOT_PHYSICS_PASS',
        'instance_count': len(instance_names),
        'instances_truncated': len(instance_names) > max_names,
        'instances_sample': instance_rows,
        'step_count': len(step_rows), 'steps': step_rows,
        'total_frames': sum(r['frame_count'] for r in step_rows),
        'any_S_field': any(r['S_frame_count'] for r in step_rows),
        'stress_values_read': 0, 'native_equilibrium_verified': False,
        'local_material_stress_verified': False, 'fatigue_life_verified': False}


def self_test_inventory():
    class Obj:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
    inst = Obj(elements=[1, 2], nodes=[1, 2, 3], elementSets={'SET_A': object()})
    frames = [
        Obj(frameValue=0.0, fieldOutputs={'S': Obj(componentLabels=('S11', 'S22'))}),
        Obj(frameValue=0.1, fieldOutputs={'U': object()}),
        Obj(frameValue=0.2, fieldOutputs={'S': Obj(componentLabels=('S11', 'S22'))})]
    odb = Obj(rootAssembly=Obj(instances={'STEEL-1': inst}),
              steps={'Wind': Obj(frames=frames), 'Empty': Obj(frames=[])})
    r = inventory_native_odb(odb)
    assert r['step_count'] == 2 and r['total_frames'] == 3
    assert r['instance_count'] == 1 and r['instances_sample'][0]['element_count'] == 2
    wind = next(row for row in r['steps'] if row['step'] == 'Wind')
    assert wind['S_frame_count'] == 2 and not wind['S_present_every_frame']
    assert wind['frame_time_monotonic'] and wind['sampled_frames'][1]['has_S'] is False
    assert r['stress_values_read'] == 0 and r['fatigue_life_verified'] is False
    bad = Obj(rootAssembly=odb.rootAssembly,
              steps={'Wind': Obj(frames=[frames[0], Obj(frameValue=float('nan'),
                    fieldOutputs={'S': Obj(componentLabels=('S11',))})])})
    try: inventory_native_odb(bad)
    except ValueError as exc: assert str(exc) == 'NONFINITE_ODB_FRAME_TIME'
    else: raise AssertionError('nonfinite ODB time accepted')
    try: inventory_native_odb(odb, max_names=0)
    except ValueError as exc: assert str(exc) == 'INVALID_INVENTORY_LIMIT'
    else: raise AssertionError('invalid inventory bound accepted')
    return {'status': 'SYNTHETIC_DIRECTORY_INVENTORY_PASS_NOT_NATIVE',
            'positive_tests': 1, 'negative_tests': 2,
            'stress_values_read': 0, 'physical_pass': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--inventory-only', action='store_true', help='native ODB metadata only; no stress values')
    ap.add_argument('--expected-odb-sha256', help='required whole-file SHA256 for inventory')
    ap.add_argument('--expected-odb-bytes', type=int, help='required exact byte count for inventory')
    ap.add_argument('--inventory-json', type=Path, help='optional new receipt path; never overwrite')
    ap.add_argument('--source-map', type=Path)
    ap.add_argument('--d400-source-map', type=Path)
    ap.add_argument('--candidate-table', type=Path,
                    help='SHA-locked 372-row D400 mesh candidate whitelist (mandatory for D400)')
    ap.add_argument('--run-card', type=Path)
    ap.add_argument('--inp', type=Path)
    ap.add_argument('--odb', type=Path)
    ap.add_argument('--logs-dir', type=Path)
    ap.add_argument('--out-dir', type=Path)
    args = ap.parse_args()
    if args.self_test:
        report = self_test(args.source_map, args.d400_source_map)
        report['directory_inventory'] = self_test_inventory()
        print(json.dumps(report, sort_keys=True))
        return
    if args.inventory_only:
        insist(args.odb is not None and args.odb.is_file(), 'INVENTORY_REQUIRES_REAL_ODB_FILE')
        insist(is_sha(args.expected_odb_sha256), 'INVENTORY_REQUIRES_SHA256')
        insist(type(args.expected_odb_bytes) is int and args.expected_odb_bytes > 0,
               'INVENTORY_REQUIRES_EXPECTED_BYTES')
        insist(args.odb.stat().st_size == args.expected_odb_bytes,
               'INVENTORY_ODB_SIZE_MISMATCH')
        digest = sha_file(args.odb)
        insist(digest == args.expected_odb_sha256, 'INVENTORY_ODB_SHA256_MISMATCH')
        try:
            from odbAccess import openOdb
        except ImportError as exc:
            raise SystemExit('NEED_NATIVE_ABAQUS_PYTHON: ' + str(exc))
        odb = openOdb(str(args.odb), readOnly=True)
        try:
            report = inventory_native_odb(odb)
        finally:
            odb.close()
        report.update({'odb_sha256': digest, 'odb_bytes': args.expected_odb_bytes,
                       'odb_path': str(args.odb.resolve()),
                       'software': 'Abaqus odbAccess readOnly=True',
                       'native_execution': True, 'physical_pass': False})
        payload = json.dumps(report, sort_keys=True, indent=2) + '\n'
        if args.inventory_json:
            insist(args.inventory_json.parent.is_dir() and
                   not args.inventory_json.exists(), 'REFUSE_OVERWRITE_INVENTORY_RECEIPT')
            args.inventory_json.write_text(payload, encoding='utf-8')
        else:
            print(payload)
        return
    if not all((args.run_card, args.inp, args.odb, args.logs_dir, args.out_dir, args.source_map)):
        ap.error('require --run-card --inp --odb --logs-dir --out-dir --source-map or --self-test')
    insist(not args.out_dir.exists(), 'REFUSE_OVERWRITE_OUTPUT')
    card_raw = args.run_card.read_bytes()
    card = validate_card(json.loads(card_raw.decode('utf-8')))
    insist(sha_file(args.inp) == card['inp_sha256'], 'INP_SHA256_MISMATCH')
    insist(sha_file(args.odb) == card['odb_sha256'], 'ODB_SHA256_MISMATCH')
    source_map_raw = args.source_map.read_bytes()
    candidate_raw = None
    verified_candidate = None
    if card['inp_sha256'] == D400_PE_CHILD_SHA:
        insist(args.candidate_table is not None,
               'D400_REQUIRES_SHA_LOCKED_372_CANDIDATE_TABLE')
        from s10_candidate_run_card_gate import select
        candidate_raw = args.candidate_table.read_bytes()
        verified_candidate = select(card, candidate_raw, source_map_raw)
    else:
        insist(args.candidate_table is None,
               'T057_MUST_NOT_USE_D400_CANDIDATE_TABLE')
    validate_source_binding(card, source_map_raw,
                            verified_candidate=verified_candidate)
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
        'source_map_sha256': sha_bytes(source_map_raw),
        'candidate_table_sha256': (sha_bytes(candidate_raw) if candidate_raw is not None
                                   else None),
        'candidate_plane': (verified_candidate['axial_plane']
                            if verified_candidate is not None else None),
        'candidate_azimuth_deg': (int(verified_candidate['requested_azimuth_deg'])
                                  if verified_candidate is not None else None),
        'candidate_status': ('SOURCE_ELEMENT_ONLY_NO_NATIVE_IP_CERTIFICATION'
                             if verified_candidate is not None else None),
        'source_map_status': ('T057_HEIGHT_ONLY' if card['inp_sha256'] == FROZEN_T057_SHA
                              else 'D400_PE_372_AZIMUTH_SOURCE_ONLY') + '_NOT_HOTSPOT_OR_IP',
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
