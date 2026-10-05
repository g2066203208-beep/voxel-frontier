"""Compare current M2 with the R2 frozen native operator under a stated axis map.

Python 3.10+ / numpy. No model edits, network or solver calls.
Usage: python compare_rna_properties.py --abaqus abaqus-results/abaqus-rna-properties.json
       --openfast openfast-rna-current.json --out comparison-results
This is a conditional model-representation comparison, not physical validation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def skew(r):
    x, y, z = r
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def matrix(m, r, j):
    s = skew(r)
    return np.block([[m*np.eye(3), -m*s], [m*s, j+m*s.T@s]])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--abaqus', type=Path, required=True)
    p.add_argument('--openfast', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    abq = json.loads(a.abaqus.read_text(encoding='utf-8-sig'))
    of = json.loads(a.openfast.read_text(encoding='utf-8-sig'))
    if abq['input_sha256'] != '428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1':
        raise ValueError('This comparison is scoped to current T026 M2.')
    if of['ref'] != '7c05ea7355fa623f863a3cf11d0908a83cb94f41':
        raise ValueError('Unexpected R2 input snapshot.')
    source = of['frozen_native_operator']
    current = abq['components']['rna_total']
    discrete = current['models']['b31_endpoint_lumped_exact_section']
    continuous = current['models']['continuous_uniform_circular_rods']
    R = np.array([[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]])
    T = np.zeros((6, 6)); T[:3, :3] = R; T[3:, 3:] = R
    O = np.array([0., 158., 0.])
    old_m = current['mass_kg']; target_m = source['mass_kg']
    old_r = np.array(current['cg_global_m'])-O
    target_r = R@np.array(source['rG_from_tower_top_m'])
    old_j = np.array(discrete['J_cg_tensor_kg_m2'])
    cont_j = np.array(continuous['J_cg_tensor_kg_m2'])
    target_j = R@np.array(source['JG_kgm2'])@R.T
    old_M = np.array(discrete['references']['tower_top']['M6'])
    target_M = T@np.array(source['M6_mixed_SI'])@T.T
    old_jt = old_M[3:, 3:]; target_jt = target_M[3:, 3:]
    checks = {
        'rotation_is_right_handed': bool(np.allclose(R.T@R, np.eye(3)) and abs(np.linalg.det(R)-1)<1e-14),
        'M2_M6_reconstructs': bool(np.allclose(matrix(old_m, old_r, old_j), old_M, rtol=1e-12, atol=1e-7)),
        'R2_M6_reconstructs_after_rotation': bool(np.allclose(matrix(target_m, target_r, target_j), target_M, rtol=1e-12, atol=1e-7)),
        'R2_M6_is_symmetric': bool(np.allclose(target_M, target_M.T, rtol=1e-12, atol=1e-7)),
        'both_centroid_tensors_positive_definite': bool(min(np.linalg.eigvalsh(target_j))>0 and min(np.linalg.eigvalsh(old_j))>0),
        'both_M6_positive_definite': bool(min(np.linalg.eigvalsh(target_M))>0 and min(np.linalg.eigvalsh(old_M))>0),
    }
    partitions = [('nacelle', 'nacelle_kg'), ('hub', 'hub_kg'), ('blades_all', 'three_blades_kg')]
    masses = []
    for name, field in partitions:
        old = abq['components'][name]['mass_kg']; new = of['mass_chain'][field]
        masses.append({'component': name, 'M2_kg': old, 'R2_float64_kg': new, 'R2_minus_M2_kg': new-old})
    delta_m = target_m-old_m
    checks['component_mass_difference_closes'] = bool(abs(sum(x['R2_minus_M2_kg'] for x in masses)-delta_m)<1e-8)
    if not all(checks.values()):
        raise AssertionError(checks)
    blocks = [
        ('translation_translation', 'kg', slice(0, 3), slice(0, 3)),
        ('translation_rotation', 'kg*m', slice(0, 3), slice(3, 6)),
        ('rotation_rotation', 'kg*m^2', slice(3, 6), slice(3, 6)),
    ]
    block_differences = []
    for name, unit, i, j in blocks:
        delta = target_M[i, j]-old_M[i, j]
        block_differences.append({'block': name, 'unit': unit,
                                  'max_abs_difference': float(np.max(np.abs(delta))),
                                  'frobenius_difference': float(np.linalg.norm(delta))})
    report = {
        'schema': 'T038-M2-versus-R2-conditional-comparison-v1',
        'scope': 'undeformed M2 B31 versus independent float64 frozen native R2 operator; not operating validation',
        'provenance': [{'file': a.abaqus.name, 'sha256': sha(a.abaqus)}, {'file': a.openfast.name, 'sha256': sha(a.openfast)},
                       {'file': Path(__file__).name, 'sha256': sha(Path(__file__))}],
        'alignment': {'R_OF_IEC_to_ABQ': R.tolist(), 'common_point_ABQ_m': O.tolist(),
                      'status': 'defined geometric candidate at zero yaw; historical wind/load mapping is still unverified'},
        'mass': {'M2_kg': old_m, 'R2_float64_kg': target_m, 'R2_minus_M2_kg': delta_m,
                 'M2_deficit_relative_to_R2_percent': 100*delta_m/target_m,
                 'increase_relative_to_M2_percent': 100*delta_m/old_m,
                 'R2_archived_printed_kg': of['archive_summary']['RNA_mass_kg']['value'],
                 'float64_minus_archived_printed_kg': of['mass_chain']['delta_vs_archived_EDsum_kg']},
        'component_mass_difference': masses,
        'centroid': {'M2_global_ABQ_m': current['cg_global_m'], 'R2_global_ABQ_m': (O+target_r).tolist(),
                     'R2_minus_M2_m': (target_r-old_r).tolist(), 'distance_m': float(np.linalg.norm(target_r-old_r))},
        'inertia': {'M2_JG_kgm2': old_j.tolist(), 'R2_JG_in_ABQ_kgm2': target_j.tolist(),
                    'M2_JT_kgm2': old_jt.tolist(), 'R2_JT_in_ABQ_kgm2': target_jt.tolist(),
                    'M2_minus_R2_JG_diagonal_percent_relative_R2': (100*(np.diag(old_j)/np.diag(target_j)-1)).tolist(),
                    'JG_frobenius_difference_relative_R2_percent': float(100*np.linalg.norm(old_j-target_j)/np.linalg.norm(target_j)),
                    'B31_minus_continuous_JG_diagonal_percent_relative_continuous': (100*(np.diag(old_j)/np.diag(cont_j)-1)).tolist()},
        'R2_frozen_target_M6_at_tower_top_ABQ_mixed_SI': target_M.tolist(),
        'M6_difference_by_unit_block_only': block_differences,
        'proposed_validation_copy_only': {'MASS_kg': target_m, 'CG_global_ABQ_m': (O+target_r).tolist(),
            'ROTARYI_at_CG_order_I11_I22_I33_I12_I13_I23_kgm2': [float(target_j[0,0]), float(target_j[1,1]), float(target_j[2,2]), float(target_j[0,1]), float(target_j[0,2]), float(target_j[1,2])],
            'implementation': 'mass and full centroid tensor at CG, rigidly offset to tower-top reference; not generated or applied'},
        'verification': checks,
        'limits': ['No single mixed-unit M6 relative norm is used.',
                   'R2 native omissions are implementation assumptions, not physical zero inertias.',
                   'Float64 reconstruction differs from archived finite-precision ED.sum; no exact solver matrix was exported.',
                   'Axis map is a proposed geometric alignment; it does not validate historical load transfer.',
                   'D08 remains OPEN; flexible, rotating and operating response equivalence is not shown.'],
        'solver_executed': False, 'model_modified': False,
    }
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out/'rna-comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (a.out/'component-mass-difference.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(masses[0])); w.writeheader(); w.writerows(masses)
    with (a.out/'R2-frozen-target-M6-ABQ.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['DOF', 'U1', 'U2', 'U3', 'UR1', 'UR2', 'UR3'])
        for name, row in zip(['U1','U2','U3','UR1','UR2','UR3'], target_M): w.writerow([name]+row.tolist())
    print(json.dumps({k: report[k] for k in ['mass', 'centroid', 'inertia', 'verification']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
