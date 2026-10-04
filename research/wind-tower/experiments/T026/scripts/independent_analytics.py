"""Independent algebraic preflight only. Never imports Abaqus or starts a solver.

JSON inputs are copied actual parameter data, not reconstructed official curves.
Use --self-check for synthetic analytical checks (not production verification).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def skew(r):
    x, y, z = np.asarray(r, dtype=float)
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def spatial_inertia(mass, r, inertia_cg, rotation=None):
    """r points from tower-top T to CG; qdot=[v_T, omega]."""
    m = float(mass)
    r = np.asarray(r, dtype=float)
    j = np.asarray(inertia_cg, dtype=float)
    R = np.eye(3) if rotation is None else np.asarray(rotation, dtype=float)
    if m <= 0 or r.shape != (3,) or j.shape != (3, 3) or R.shape != (3, 3):
        raise ValueError('mass>0, r[3], inertia_cg[3,3], rotation[3,3] required')
    if not np.all(np.isfinite(np.r_[m, r, j.ravel(), R.ravel()])):
        raise ValueError('nonfinite RNA data')
    if not np.allclose(R.T @ R, np.eye(3), rtol=0, atol=1e-10) or np.linalg.det(R) <= 0:
        raise ValueError('rotation must be proper orthogonal; check axis conventions')
    if not np.allclose(j, j.T, rtol=0, atol=1e-10*max(1., np.linalg.norm(j))):
        raise ValueError('inertia_cg must be symmetric; verify product-inertia signs')
    jg = R @ j @ R.T
    s = skew(r)
    jt = jg + m * ((r @ r) * np.eye(3) - np.outer(r, r))
    return np.block([[m*np.eye(3), -m*s], [m*s, jt]]), jg


def rna_diagnostics(data):
    """Energy agreement is identity preflight; not a solver or flexible-RNA validation."""
    m = float(data['mass'])
    r = np.asarray(data['r_T_to_CG'], dtype=float)
    M, jg = spatial_inertia(m, r, data['inertia_cg'], data.get('rotation'))
    principal = np.linalg.eigvalsh(jg)
    rounding = float(data.get('inertia_absolute_rounding', 0.0))
    physical = bool(principal.min() >= -rounding and 2*principal.max() <= principal.sum()+3*rounding)
    rng = np.random.default_rng(0)
    errors = []
    for q in rng.standard_normal((20, 6)):
        vg = q[:3] + np.cross(q[3:], r)
        direct = 0.5*(m*(vg @ vg) + q[3:] @ jg @ q[3:])
        via_matrix = 0.5*(q @ M @ q)
        errors.append(abs(direct-via_matrix)/max(abs(direct), np.finfo(float).tiny))
    report = {'M6': M.tolist(), 'principal_inertia_cg': principal.tolist(),
              'principal_inertia_physical_with_supplied_rounding': physical,
              'energy_identity_max_relative_error': max(errors),
              'note': 'Algebraic identity only; actual solver matrix/reactions still required.'}
    if 'implemented_M6' in data:
        actual = np.asarray(data['implemented_M6'], dtype=float)
        if actual.shape != (6,6):
            raise ValueError('implemented_M6 must be 6x6 at same T and axes')
        errors = {}
        for name, sl in {'mass': (slice(0,3),slice(0,3)),
                         'coupling_upper': (slice(0,3),slice(3,6)),
                         'coupling_lower': (slice(3,6),slice(0,3)),
                         'inertia_T': (slice(3,6),slice(3,6))}.items():
            delta = np.linalg.norm((actual-M)[sl])
            reference = np.linalg.norm(M[sl])
            errors[name] = {'absolute_frobenius_error': float(delta),
                            'relative_error_if_nonzero_reference': float(delta/reference) if reference else None}
        report['implementation_block_errors'] = errors
    return report


def material_diagnostics(data):
    """rows contain actual sigma/eps_in_or_ck/damage at aligned strain nodes.

    Caller must interpolate actual damage and behavior tables onto common nodes.
    Total engineering strain inferred here is not an experimental measurement.
    """
    E = float(data['E0'])
    if E <= 0:
        raise ValueError('E0 must be positive and share units with sigma')
    tol = float(data.get('absolute_strain_rounding', 0.0))
    rows, errors = [], []
    previous_in = previous_pl = previous_damage = None
    for i, x in enumerate(data['rows']):
        stress = float(x['sigma_absolute'])
        e_in = float(x['eps_in_or_ck'])
        d = float(x['damage'])
        if not np.all(np.isfinite([stress,e_in,d])) or stress < 0 or not 0 <= d < 1:
            errors.append({'row': i, 'kind': 'nonfinite/negative_stress/damage_out_of_range'})
            continue
        e_pl = e_in - (d/(1-d))*stress/E
        e_total = e_in + stress/E
        local_tol = max(tol, 100*np.finfo(float).eps*max(abs(e_in),abs(e_pl),np.finfo(float).tiny))
        if e_in < -local_tol or e_pl < -local_tol:
            errors.append({'row': i, 'kind': 'negative_inelastic_or_plastic_strain', 'eps_pl': e_pl})
        if previous_in is not None and e_in < previous_in-local_tol:
            errors.append({'row': i, 'kind': 'decreasing_inelastic_strain'})
        if previous_pl is not None and e_pl < previous_pl-local_tol:
            errors.append({'row': i, 'kind': 'decreasing_plastic_strain'})
        if previous_damage is not None and d < previous_damage:
            errors.append({'row': i, 'kind': 'decreasing_damage_table_requires_review'})
        rows.append({'row': i, 'sigma_absolute': stress, 'eps_in_or_ck': e_in,
                     'eps_total_reconstructed': e_total, 'damage': d,
                     'eps_pl_software_conversion': e_pl,
                     'ideal_unloading_E': (1-d)*E})
        previous_in, previous_pl, previous_damage = e_in, e_pl, d
    return {'rows': rows, 'issues': errors, 'input_legality_diagnostic': 'issues_found' if errors else 'no_issues_in_supplied_rows',
            'mu_from_actual_card': data.get('mu'),
            'note': 'No new material curve/calibration generated; viscosity and solver path not verified by algebra.'}


def prestress_expected(E, A, L, sigma0, host_stiffness=None):
    E, A, L, sigma0 = map(float, (E,A,L,sigma0))
    if min(E,A,L) <= 0:
        raise ValueError('E,A,L must be positive in consistent units')
    n0, kbar = sigma0*A, E*A/L
    if host_stiffness is None:
        return {'N0': n0, 'N_expected': n0, 'host_shortening_expected': 0., 'kbar': kbar}
    kh = float(host_stiffness)
    if kh <= 0:
        raise ValueError('host_stiffness must be positive')
    n = n0/(1+kbar/kh)
    return {'N0': n0, 'N_expected': n, 'host_shortening_expected': n/kh, 'kbar': kbar,
            'assumption': 'linear shortening releases an initial contraction mismatch; not all load-controlled processes'}


def truss_small_strain_tangent(E, A, L, N, direction):
    n = np.asarray(direction, dtype=float)
    n = n/np.linalg.norm(n)
    k_mat = float(E)*float(A)/float(L)*np.outer(n,n)
    k_geo = float(N)/float(L)*(np.eye(3)-np.outer(n,n))
    return {'material': k_mat.tolist(), 'initial_stress_geometric': k_geo.tolist(),
            'total': (k_mat+k_geo).tolist(),
            'assumption': 'small axial prestrain; same current length/direction and conjugate measures'}


def self_check():
    M, _ = spatial_inertia(2., [1.,2.,0.], np.diag([1.,2.,3.]))
    assert np.allclose(M[3:,3:], [[9.,-4.,0.],[-4.,4.,0.],[0.,0.,13.]])
    q = np.array([1.,0.,0.,0.,0.,1.])
    assert abs(0.5*q @ M @ q-3.5) < 1e-12
    good = material_diagnostics({'E0':1000.,'rows':[{'sigma_absolute':1.,'eps_in_or_ck':0.,'damage':0.},
                                                  {'sigma_absolute':1.,'eps_in_or_ck':0.009,'damage':0.5}]})
    assert not good['issues'] and abs(good['rows'][1]['eps_pl_software_conversion']-0.008) < 1e-12
    bad = material_diagnostics({'E0':1000.,'rows':[{'sigma_absolute':1.,'eps_in_or_ck':0.,'damage':0.5}]})
    assert bad['issues']
    pt = prestress_expected(10000., 2., 100., 100., 500.)
    assert abs(pt['N_expected']-1000/7) < 1e-10
    tangent = truss_small_strain_tangent(10000.,2.,100.,200.,[1.,0.,0.])
    assert np.allclose(tangent['total'], np.diag([200.,2.,2.]))
    print('Analytical utility checks passed using synthetic values. No solver or production-model evidence created.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check', action='store_true')
    parser.add_argument('--input', type=Path, help='JSON with kind=material or rna and actual parameter data')
    parser.add_argument('--output', type=Path, help='Separate derived JSON; source is never changed')
    args = parser.parse_args()
    if args.self_check:
        self_check()
    if args.input:
        data = json.loads(args.input.read_text(encoding='utf-8-sig'))
        report = material_diagnostics(data) if data['kind']=='material' else rna_diagnostics(data) if data['kind']=='rna' else None
        if report is None:
            raise ValueError('kind must be material or rna')
        out = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            if args.output.resolve() == args.input.resolve():
                raise ValueError('Refusing to overwrite parameter source')
            args.output.write_text(out, encoding='utf-8')
        else:
            print(out)
    elif not args.self_check:
        parser.error('--input or --self-check is required')


if __name__ == '__main__':
    main()
