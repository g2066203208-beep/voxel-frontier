"""Synthetic-only regression tests for the T077 source-grid preflight."""
import csv
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from t08034_history_preflight import audit, FIELDS


class HistoryGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'artifacts'
        self.root.mkdir()
        self.meta = self.base / 'meta.json'
        self.meta.write_text(json.dumps({'load_cases': ['A', 'B']}))
        self.rows = [dict(case=case, segment=f'CSEG_{seg:02d}', time_s=t,
                          **{field: '1' for field in FIELDS})
                     for case in ('A', 'B') for seg in range(1, 32) for t in (0, 1)]

    def write(self):
        with gzip.open(self.root / 'batch31seg.csv.gz', 'wt', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=['case','segment','time_s',*FIELDS])
            writer.writeheader()
            writer.writerows(self.rows)

    def test_missing_source_holds(self):
        self.assertEqual(audit(self.root, self.meta)['status'], 'HOLD')

    def test_complete_synthetic_grid_passes_source_only(self):
        self.write()
        result = audit(self.root, self.meta)
        self.assertEqual(result['status'], 'PASS-SOURCE-GRID-ONLY')
        self.assertEqual(result['unique_rows'], 124)

    def test_conflicting_duplicate_holds(self):
        self.rows.append(dict(self.rows[0], Mx_kNm='999'))
        self.write()
        result = audit(self.root, self.meta)
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(result['conflicting_duplicate_rows'], 1)

    def test_truncated_gzip_returns_hold_not_exception(self):
        # Missing gzip trailer raises EOFError, not OSError, in Python gzip.
        self.write()
        path = self.root / 'batch31seg.csv.gz'
        path.write_bytes(path.read_bytes()[:-8])
        result = audit(self.root, self.meta)
        self.assertEqual(result['status'], 'HOLD')
        self.assertTrue(any('CORRUPT-SOURCE:' in x for x in result['issues']))

    def test_surplus_csv_cell_holds(self):
        self.write()
        path = self.root / 'batch31seg.csv.gz'
        with gzip.open(path, 'rt', newline='') as fh:
            lines = fh.readlines()
        lines[1] = lines[1].rstrip('\r\n') + ',UNACCOUNTED\n'
        with gzip.open(path, 'wt', newline='') as fh:
            fh.writelines(lines)
        result = audit(self.root, self.meta)
        self.assertEqual(result['status'], 'HOLD')
        self.assertTrue(any('BAD-ROW-WIDTH:' in x for x in result['issues']))

    def test_duplicate_six_component_header_holds(self):
        # DictReader would otherwise keep the LAST Mx_kNm and silently
        # overwrite the first one even when every row has valid width.
        self.write()
        path = self.root / 'batch31seg.csv.gz'
        with gzip.open(path, 'rt', newline='') as fh:
            lines = fh.readlines()
        lines[0] = lines[0].rstrip('\\r\\n') + ',Mx_kNm\\n'
        lines[1:] = [line.rstrip('\\r\\n') + ',999\\n' for line in lines[1:]]
        with gzip.open(path, 'wt', newline='') as fh:
            fh.writelines(lines)
        result = audit(self.root, self.meta)
        self.assertEqual(result['status'], 'HOLD')
        self.assertTrue(any('DUPLICATE-HEADER:' in x for x in result['issues']))
        self.assertEqual(result['unique_rows'], 0)

    def test_missing_time_grid_holds(self):
        self.rows.pop()
        self.write()
        result = audit(self.root, self.meta)
        self.assertEqual(result['status'], 'HOLD')
        self.assertTrue(any('TIME-GRID-MISMATCH' in x for x in result['issues']))


if __name__ == '__main__':
    unittest.main()
