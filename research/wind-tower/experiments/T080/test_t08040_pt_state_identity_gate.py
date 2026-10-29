"""Synthetic regression fixtures; no original INP/native solver in these tests."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('gate', Path(__file__).with_name('t08040_pt_state_identity_gate.py'))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixtures():
    meta = {
        'source_identity': {'position_count_reconstructed':36, 'single_strand_area_mm2':140,
                            'sigma_initial_MPa':1280, 'Ep_MPa':195000},
        'registered_assumptions': {'anchorage':'one active clip anchorage without top pressure, 6 mm',
            'horizontal_joints':30, 'joint_compression_mm_each_adopted':2},
        'adopted_BF8': {'BF':8,'Ap_mm2':40320,'P0_MN':51.6096,
            'loss_friction_MPa':0, 'loss_anchor_joint_MPa':114.91071428571429,
            'loss_elastic_MPa':22.555242813844927,
            'loss_relaxation_MPa':30.10752688172044,
            'loss_shrink_creep_MPa':126.47515305705939,
            'loss_total_MPa':294.04863703833905,
            'sigma_pe_MPa':985.951362961661,
            'Pe_MN':39.75355895461417,'eta':0.7702745023137976}}
    raw = {'sha256':'c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db',
           'pt': {'element_count':36, 'element_length_min':112,'element_length_max':112,
                  'has_intermediate_nodes':False,'embedded_in_concrete':False},
           'prestress': {'initial_stress_block':['*Initial Conditions, type=STRESS',
                       'PT_36x15p2-1.SET_PT_ALL_ELEMS, 1.28e+09, ']}}
    t070={'parent_sha256':raw['sha256']}
    return meta,raw,t070

class TestPTGate(unittest.TestCase):
    def test_exact_source_values(self):
        result=gate.evaluate(*fixtures())
        self.assertEqual(result['status'],'PASS-STATIC-PT-IDENTITY-ONLY')
        self.assertEqual(result['native_equilibrium'],'HOLD-NO-ABAQUS-RUN')
        self.assertAlmostEqual(result['P0_minus_Pe_MN'],11.85604104538583,places=9)
        self.assertAlmostEqual(result['joint_1mm_sensitivity_MN'],2.106,places=9)
    def test_changed_pe_fails_closed(self):
        m,r,t=fixtures();m['adopted_BF8']['Pe_MN']+=0.1
        self.assertEqual(gate.evaluate(m,r,t)['status'],'HOLD-STATIC-INCONSISTENCY')
    def test_changed_parent_hash_fails_closed(self):
        m,r,t=fixtures();t['parent_sha256']='bad'
        self.assertEqual(gate.evaluate(m,r,t)['status'],'HOLD-STATIC-INCONSISTENCY')
    def test_missing_anchorage_value_fails_closed(self):
        m,r,t=fixtures();m['registered_assumptions']['anchorage']='not documented'
        with self.assertRaises(ValueError): gate.evaluate(m,r,t)

if __name__ == '__main__': unittest.main()
