"""Synthetic tests ONLY: not real T077 histories or physics validation."""
import csv
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from t08036_time_extent_gate import check

class TimeExtentGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'artifacts'
        self.root.mkdir()
        self.meta = self.base/'meta.json'
        self.meta.write_text(json.dumps({'load_cases':['A','B']}))
        self.manifest = self.base/'window.json'
        self.spec = dict(first_time_s=100, last_time_s=102, step_s=1,
                         samples_per_segment=3, tolerance_s=1e-8,
                         openfast_input_sha256='a'*64, exporter_sha256='b'*64,
                         source_note='SYNTHETIC TEST ONLY')
        self.manifest.write_text(json.dumps({'cases':{'A':self.spec,'B':self.spec}}))
        self.rows = [dict(case=c,segment=f'CSEG_{i:02d}',time_s=t)
                     for c in ('A','B') for i in range(1,32) for t in (100,101,102)]
    def write(self):
        with gzip.open(self.root/'data31seg.csv.gz','wt',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['case','segment','time_s']);w.writeheader();w.writerows(self.rows)
    def test_missing_manifest_holds(self):
        self.write();self.assertEqual(check(self.root,self.meta,None)['status'],'HOLD')
    def test_complete_synthetic_passes_source_only(self):
        self.write();r=check(self.root,self.meta,self.manifest)
        self.assertEqual(r['status'],'PASS-H-TIME-SOURCE-ONLY');self.assertEqual(r['case_results']['A']['segments_complete'],31)
    def test_missing_one_timestamp_holds(self):
        self.rows.pop();self.write();self.assertEqual(check(self.root,self.meta,self.manifest)['status'],'HOLD')
    def test_shifted_time_holds(self):
        self.rows[0]['time_s']=100.2;self.write();self.assertEqual(check(self.root,self.meta,self.manifest)['status'],'HOLD')
    def test_duplicate_index_holds(self):
        self.rows.append(dict(self.rows[0]));self.write();self.assertEqual(check(self.root,self.meta,self.manifest)['status'],'HOLD')
    def test_truncated_gzip_holds(self):
        self.write();p=self.root/'data31seg.csv.gz';p.write_bytes(p.read_bytes()[:-8]);self.assertEqual(check(self.root,self.meta,self.manifest)['status'],'HOLD')
    def test_inconsistent_manifest_holds(self):
        self.spec['last_time_s']=103;self.manifest.write_text(json.dumps({'cases':{'A':self.spec,'B':self.spec}}))
        self.write();self.assertEqual(check(self.root,self.meta,self.manifest)['status'],'HOLD')
    def test_missing_case_holds(self):
        self.rows=[r for r in self.rows if r['case']=='A'];self.write();self.assertEqual(check(self.root,self.meta,self.manifest)['status'],'HOLD')
    def test_bad_header_holds(self):
        with gzip.open(self.root/'data31seg.csv.gz','wt',newline='') as f:
            f.write('case,segment,time_s,time_s\nA,CSEG_01,100,100\n')
        self.assertEqual(check(self.root,self.meta,self.manifest)['status'],'HOLD')

if __name__=='__main__': unittest.main()
