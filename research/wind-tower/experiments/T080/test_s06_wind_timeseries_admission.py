#!/usr/bin/env python3
"""Independent source-schema refusal tests; synthetic fixtures are not physical evidence."""
import csv,json,pathlib,tempfile,unittest
from s06_wind_timeseries_admission import admit,REQUIRED,META
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.csv=pathlib.Path(self.tmp.name)/'history.csv'
        self.meta=pathlib.Path(self.tmp.name)/'meta.json'
        self.rows=[[str(i*.05),'1','2','3','4','5','6'] for i in range(4)]
        self.metadata={k:('a'*64 if k.endswith('sha256') else 'fixture') for k in META}
        self.metadata['units']='N,Nm,s'
        self.save()
    def save(self):
        with self.csv.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(REQUIRED);w.writerows(self.rows)
        self.meta.write_text(json.dumps(self.metadata))
    def test_valid(self):
        self.assertEqual(admit(self.csv,self.meta,.05)['n'],4)
    def refuse(self,code):
        self.save()
        with self.assertRaisesRegex(ValueError,code):admit(self.csv,self.meta,.05)
    def test_missing_sample(self):
        self.rows.pop(2);self.refuse('MISSING_OR_IRREGULAR_SAMPLE')
    def test_duplicate_time(self):
        self.rows[2][0]=self.rows[1][0];self.refuse('NONMONOTONIC_TIME')
    def test_bad_metadata(self):
        self.metadata['model_sha256']='bad';self.refuse('INVALID_SHA')
    def test_bad_units(self):
        self.metadata['units']='kN,kNm,s';self.refuse('UNITS_NOT_CANONICAL')
    def test_nonfinite(self):
        self.rows[2][1]='nan';self.refuse('NONFINITE_ROW')
    def test_wrong_dt(self):
        self.save()
        with self.assertRaisesRegex(ValueError,'DT_EXPECTATION_MISMATCH'):admit(self.csv,self.meta,.1)
if __name__=='__main__':unittest.main()
