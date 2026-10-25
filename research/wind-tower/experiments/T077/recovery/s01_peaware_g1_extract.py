#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01 diagnostic-only Pe-aware G1 ODB PT extractor.

Run ONLY after a separately authorized native Abaqus G0/G1 pilot:
  abaqus python s01_peaware_g1_extract.py --inp S01_D400_Pe_G1_INSTRUMENTED_DIAGNOSTIC_ONLY.inp \
    --odb <native-job>.odb --out <new-output-directory>

This script cannot establish that the ODB came from the supplied INP. A signed
RUN card, native logs, and provenance remain mandatory. All scientific gates HOLD.
No Abaqus run is launched by this script.
"""
from __future__ import print_function
import argparse
import csv
import hashlib
import json
import math
import os
import re

INP_SHA256 = '4c84c61ea07138428d4c0a8f742a9ab6e55725c49d16a94f5d9eaa8f7d9d3d29'
PARENT_INP_SHA256 = '0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217'
P0_PA = 1280000000.0
PE_DESIGN_PA = 985951362.9616609
EXPECTED_PT_COUNT = 36
PT_INSTANCE = 'PT_36x15p2-1'
PT_SET = 'SET_PT_ALL_ELEMS'
PT_SECTION = 'SET_PT_ALL_GEOM'


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def ci_key(mapping, name):
    found = [k for k in mapping.keys() if str(k).upper() == name.upper()]
    check(len(found) == 1, 'missing or ambiguous ODB key %s' % name)
    return found[0]


def parse_locked_inp(raw, expected_sha=INP_SHA256):
    actual = sha256_bytes(raw)
    check(actual == expected_sha, 'INP_SHA256_MISMATCH: expected %s got %s' % (expected_sha, actual))
    s = raw.decode('utf-8')
    # PT input is an Abaqus initial-stress assignment, not a verified effective force.
    init = re.findall(r'^\*Initial Conditions,\s*type=STRESS\s*\n\s*PT_36x15p2-1\.SET_PT_ALL_ELEMS,\s*([^,\s]+)', s, re.I | re.M)
    check(len(init) == 1, 'PT initial stress assignment missing/ambiguous')
    section = re.findall(r'^\*Solid Section,\s*elset=SET_PT_ALL_GEOM,\s*material=STRAND_1860\s*\n\s*([^,\s]+)', s, re.I | re.M)
    check(len(section) == 1, 'PT section area missing/ambiguous')
    stress = float(init[0]); area = float(section[0])
    check(math.isfinite(stress) and math.isfinite(area) and stress > 0 and area > 0,
          'PT input stress or area invalid')
    check(abs(stress - PE_DESIGN_PA) <= 1e-4, 'unexpected PT initial stress; stop')
    check(abs(area - 0.00112) <= 1e-12, 'unexpected PT area; stop')
    return {'inp_sha256': actual, 'pt_initial_stress_Pa': stress,
            'pt_section_area_m2': area,
            'pt_initial_total_force_MN': EXPECTED_PT_COUNT * stress * area / 1e6}


def s11_scalar(value):
    data = value.data
    if isinstance(data, (float, int)):
        ans = float(data)
    else:
        check(len(data) == 1, 'PT S11 field not scalar / single component')
        ans = float(data[0])
    check(math.isfinite(ans), 'nonfinite PT S11')
    return ans


def extract_from_odb(odb, inp_meta):
    step = odb.steps[ci_key(odb.steps, 'Gravity')]
    check(len(step.frames) > 0, 'Gravity has no frames')
    frame = step.frames[-1]
    inst = odb.rootAssembly.instances[ci_key(odb.rootAssembly.instances, PT_INSTANCE)]
    region = inst.elementSets[ci_key(inst.elementSets, PT_SET)]
    check('S' in frame.fieldOutputs, 'S missing from last Gravity frame')
    vals = frame.fieldOutputs['S'].getSubset(region=region).values
    rows = []
    for v in vals:
        check(str(v.instance.name).upper() == PT_INSTANCE.upper(), 'unexpected PT instance')
        label = int(v.elementLabel)
        check(label > 0, 'invalid PT element label')
        s11 = s11_scalar(v)
        rows.append({'element_label': label, 'S11_Pa': s11,
                     'axial_force_N': s11 * inp_meta['pt_section_area_m2']})
    check(len(rows) == EXPECTED_PT_COUNT, 'PT S11 field count %d != %d' % (len(rows), EXPECTED_PT_COUNT))
    check(len(set(r['element_label'] for r in rows)) == EXPECTED_PT_COUNT,
          'duplicate PT element labels / integration point ambiguity')
    rows.sort(key=lambda x: x['element_label'])
    total = sum(r['axial_force_N'] for r in rows)
    measured = total / 1e6
    design_p0 = EXPECTED_PT_COUNT * inp_meta['pt_section_area_m2'] * P0_PA / 1e6
    design_pe = EXPECTED_PT_COUNT * inp_meta['pt_section_area_m2'] * PE_DESIGN_PA / 1e6
    input_force = inp_meta['pt_initial_total_force_MN']
    contact_keys = [str(k) for k in frame.fieldOutputs.keys()
                    if str(k).upper().startswith(('CPRESS', 'COPEN', 'CSHEAR', 'CSLIP'))]
    return rows, {
        'status': 'NATIVE_ODB_VALUES_IF_AUTHENTIC__NO_SCIENTIFIC_PASS',
        's01_stage': 'PARTIAL/HOLD', 's02_data_check': 'NOT_ASSESSED_BY_THIS_SCRIPT',
        's03_equilibrium': 'HOLD', 'odb_inp_binding': 'UNVERIFIED_BY_ODB_EXTRACTION',
        'inp_sha256': inp_meta['inp_sha256'],
        'parent_d400_pe_sha256': PARENT_INP_SHA256,
        'step': 'Gravity', 'last_frame_value': float(frame.frameValue),
        'pt_elements': len(rows), 'pt_section_area_m2': inp_meta['pt_section_area_m2'],
        'P0_design_jacking_MN': design_p0,
        'Pe_design_long_term_target_MN': design_pe,
        'inp_initial_stress_Pa': inp_meta['pt_initial_stress_Pa'],
        'inp_initial_force_proxy_MN': input_force,
        'odb_last_frame_PT_force_MN': measured,
        'odb_minus_Pe_design_MN': measured - design_pe,
        'odb_minus_INP_input_MN': measured - input_force,
        'odb_over_Pe_design': measured / design_pe,
        'min_S11_MPa': min(r['S11_Pa'] for r in rows)/1e6,
        'max_S11_MPa': max(r['S11_Pa'] for r in rows)/1e6,
        'contact_field_keys_observed': contact_keys,
        'native_equilibrium_residual': 'NOT_EVALUATED',
        'physical_error_budget': 'NEED-ESTIMATE: contact, anchorage, mass, equilibrium, mesh and target stage',
        'interpretation': 'P0 is a jacking design value; Pe is a long-term design target; '
                          'INP initial stress is a prescribed input; ODB last-frame force is observed '
                          'only if native job provenance is independently established. '
                          'Do not compare measured Pe against P0 as an acceptance gate.',
        'warnings': ['ODB cannot be cryptographically linked to INP from this extractor',
                     'G1 force observation does not prove target-time, reactions or contact equilibrium',
                     'No acceptance threshold authorized; never emit physics PASS']
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inp', required=True)
    ap.add_argument('--odb', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    check(os.path.isfile(args.inp), 'input INP does not exist')
    check(os.path.isfile(args.odb), 'ODB does not exist')
    check(not os.path.exists(args.out), 'refuse overwrite of output directory')
    with open(args.inp, 'rb') as f:
        inp_meta = parse_locked_inp(f.read())
    try:
        from odbAccess import openOdb
    except ImportError as exc:
        raise SystemExit('Abaqus Python with odbAccess required: %s' % exc)
    odb = openOdb(args.odb, readOnly=True)
    try:
        rows, summary = extract_from_odb(odb, inp_meta)
    finally:
        odb.close()
    os.mkdir(args.out)
    with open(os.path.join(args.out, 'PT_S11_PE_AWARE.csv'), 'w') as f:
        w = csv.DictWriter(f, fieldnames=['element_label', 'S11_Pa', 'axial_force_N'])
        w.writeheader(); w.writerows(rows)
    with open(os.path.join(args.out, 'G1_PE_AWARE_SUMMARY.json'), 'w') as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
