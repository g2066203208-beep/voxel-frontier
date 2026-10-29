#!/usr/bin/env python3
"""Pure-Python mock tests; not native Abaqus acceptance."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('peaware', str(Path(__file__).with_name('s01_peaware_g1_extract.py')))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def inp(stress='985951362.9616609', area='0.00112'):
    return ('*Solid Section, elset=SET_PT_ALL_GEOM, material=STRAND_1860\n%s,\n'
            '*Initial Conditions, type=STRESS\nPT_36x15p2-1.SET_PT_ALL_ELEMS, %s,\n' % (area, stress)).encode('utf8')


class Dummy(object):
    def __init__(self, **kw): self.__dict__.update(kw)


class Field(object):
    def __init__(self, values): self.values=values
    def getSubset(self, region): return self


def odb(stress=985951362.9616609, n=36, dup=False, missing_s=False, bad_nan=False):
    vals = [Dummy(instance=Dummy(name=m.PT_INSTANCE), elementLabel=(1 if dup else i+1),
                  data=(float('nan') if bad_nan and i==0 else stress,)) for i in range(n)]
    frame=Dummy(frameValue=1.0,fieldOutputs={} if missing_s else {'S':Field(vals)})
    instance=Dummy(elementSets={m.PT_SET:Dummy()})
    return Dummy(steps={'Gravity':Dummy(frames=[frame])},
                 rootAssembly=Dummy(instances={m.PT_INSTANCE:instance}))


class TestPeAware(unittest.TestCase):
    def setUp(self):
        self.raw=inp();self.sha=hashlib.sha256(self.raw).hexdigest()
        self.meta=m.parse_locked_inp(self.raw,self.sha)
    def test_four_separate_identities(self):
        rows,r=m.extract_from_odb(odb(),self.meta)
        self.assertEqual(len(rows),36)
        self.assertAlmostEqual(r['P0_design_jacking_MN'],51.6096)
        self.assertAlmostEqual(r['Pe_design_long_term_target_MN'],39.75355895461416)
        self.assertAlmostEqual(r['inp_initial_force_proxy_MN'],r['Pe_design_long_term_target_MN'])
        self.assertAlmostEqual(r['odb_last_frame_PT_force_MN'],r['Pe_design_long_term_target_MN'])
        self.assertNotEqual(r['P0_design_jacking_MN'],r['Pe_design_long_term_target_MN'])
        self.assertEqual(r['s03_equilibrium'],'HOLD')
        self.assertEqual(r['odb_inp_binding'],'UNVERIFIED_BY_ODB_EXTRACTION')
    def test_native_observation_can_differ(self):
        _,r=m.extract_from_odb(odb(stress=950000000.0),self.meta)
        self.assertLess(r['odb_minus_Pe_design_MN'],0)
        self.assertEqual(r['s03_equilibrium'],'HOLD')
    def test_inp_hash_reject(self):
        with self.assertRaisesRegex(ValueError,'SHA256_MISMATCH'):
            m.parse_locked_inp(self.raw+b'\n',self.sha)
    def test_changed_stress_reject(self):
        raw=inp(stress='1280000000.0')
        with self.assertRaisesRegex(ValueError,'unexpected PT initial stress'):
            m.parse_locked_inp(raw,hashlib.sha256(raw).hexdigest())
    def test_changed_area_reject(self):
        raw=inp(area='0.00224')
        with self.assertRaisesRegex(ValueError,'unexpected PT area'):
            m.parse_locked_inp(raw,hashlib.sha256(raw).hexdigest())
    def test_missing_stress_reject(self):
        raw=b'*Solid Section, elset=SET_PT_ALL_GEOM, material=STRAND_1860\n0.00112,\n'
        with self.assertRaisesRegex(ValueError,'PT initial stress assignment'):
            m.parse_locked_inp(raw,hashlib.sha256(raw).hexdigest())
    def test_missing_s_field_reject(self):
        with self.assertRaisesRegex(ValueError,'S missing'):
            m.extract_from_odb(odb(missing_s=True),self.meta)
    def test_missing_one_pt_reject(self):
        with self.assertRaisesRegex(ValueError,'count 35'):
            m.extract_from_odb(odb(n=35),self.meta)
    def test_duplicate_pt_reject(self):
        with self.assertRaisesRegex(ValueError,'duplicate PT'):
            m.extract_from_odb(odb(dup=True),self.meta)
    def test_nan_reject(self):
        with self.assertRaisesRegex(ValueError,'nonfinite'):
            m.extract_from_odb(odb(bad_nan=True),self.meta)
    def test_missing_gravity_reject(self):
        x=odb();x.steps={'Modal':Dummy(frames=[])}
        with self.assertRaisesRegex(ValueError,'Gravity'):
            m.extract_from_odb(x,self.meta)
    def test_empty_gravity_reject(self):
        x=odb();x.steps['Gravity'].frames=[]
        with self.assertRaisesRegex(ValueError,'no frames'):
            m.extract_from_odb(x,self.meta)


if __name__=='__main__': unittest.main(verbosity=2)
