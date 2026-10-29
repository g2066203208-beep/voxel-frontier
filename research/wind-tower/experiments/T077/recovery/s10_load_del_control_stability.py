#!/usr/bin/env python3
"""S10 preparation: source-locked ETM load-DEL control-case sensitivity, NOT material fatigue.

No S-N curves, site probabilities, stress histories or native Abaqus are inferred.
Inputs: committed 744-row S06 load-rainflow CSV; stdlib only.
"""
import argparse
import csv
import hashlib
import io
import math
from pathlib import Path

SOURCE_SHA256 = '9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b'
CASES = ('U09p343881_ETM_S06', 'U11p4_ETM_S04', 'U19p202140_ETM_S04', 'U19p202140_ETM_S06')
CHANNELS = ('Fx_kN', 'Fy_kN', 'Fz_kN', 'Mx_kNm', 'My_kNm', 'Mz_kNm')
DETAILED = ('segment','channel','units','m4_case','m4_DEL','m4_margin_over_second_pct',
            'm10_case','m10_DEL','m10_margin_over_second_pct','control_switch_m4_to_m10')
SUMMARY = ('channel','units','n_gages','n_control_switch','n_m4_near_tie_lt5pct',
           'n_m10_near_tie_lt5pct','n_controlled_by_U19_S04_m4',
           'n_controlled_by_U19_S06_m4','n_controlled_by_U19_S04_m10',
           'n_controlled_by_U19_S06_m10')


def compute(raw):
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('S06 744-row source SHA256 mismatch')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if len(rows) != 744:
        raise ValueError('Expected 744 source rows')
    keyed = {}
    for row in rows:
        key = (row['case'], row['segment'], row['channel'])
        if key in keyed:
            raise ValueError('Duplicate source case/segment/channel')
        if (row['case'] not in CASES or row['channel'] not in CHANNELS
            or row['segment'] not in {f'CSEG_{i:02d}' for i in range(1,32)}):
            raise ValueError('Unrecognized source key')
        if int(row['n_samples']) != 12001 or abs(float(row['dt_s'])-0.05) > 1e-10:
            raise ValueError('Time grid mismatch')
        if abs(float(row['duration_s'])-600.0) > 1e-8:
            raise ValueError('Duration mismatch')
        for m in (4, 10):
            val = float(row[f'DEL_m{m}_Nref_1Hz'])
            if not math.isfinite(val) or val < 0:
                raise ValueError('Invalid DEL')
        keyed[key] = row
    expected = {(c, f'CSEG_{i:02d}', ch) for c in CASES
                for i in range(1,32) for ch in CHANNELS}
    if set(keyed) != expected:
        raise ValueError('Incomplete source coverage')
    detail = []
    summary = []
    for channel in CHANNELS:
        channel_rows = []
        for i in range(1,32):
            segment = f'CSEG_{i:02d}'
            subset = [keyed[(c,segment,channel)] for c in CASES]
            units = {r['units'] for r in subset}
            if units != ({'kNm'} if 'Nm' in channel else {'kN'}):
                raise ValueError('Mixed or unexpected units')
            ranked = {}
            for m in (4,10):
                col = f'DEL_m{m}_Nref_1Hz'
                ranked[m] = sorted(subset, key=lambda r: (-float(r[col]), CASES.index(r['case'])))
            a,b = ranked[4][0],ranked[10][0]
            def margin(m):
                top = float(ranked[m][0][f'DEL_m{m}_Nref_1Hz'])
                second = float(ranked[m][1][f'DEL_m{m}_Nref_1Hz'])
                return 100*(top-second)/top if top else 0.0
            row = (segment,channel,subset[0]['units'],a['case'],
                   f"{float(a['DEL_m4_Nref_1Hz']):.9f}",f'{margin(4):.6f}',
                   b['case'],f"{float(b['DEL_m10_Nref_1Hz']):.9f}",
                   f'{margin(10):.6f}',int(a['case']!=b['case']))
            detail.append(row)
            channel_rows.append(row)
        summary.append((channel,channel_rows[0][2],31,
                        sum(r[9] for r in channel_rows),
                        sum(float(r[5]) < 5 for r in channel_rows),
                        sum(float(r[8]) < 5 for r in channel_rows),
                        sum(r[3]==CASES[2] for r in channel_rows),
                        sum(r[3]==CASES[3] for r in channel_rows),
                        sum(r[6]==CASES[2] for r in channel_rows),
                        sum(r[6]==CASES[3] for r in channel_rows)))
    def csv_bytes(header, records):
        buf = io.StringIO(newline='')
        writer = csv.writer(buf,lineterminator='\n')
        writer.writerow(header)
        writer.writerows(records)
        return buf.getvalue().encode('utf-8')
    return csv_bytes(DETAILED,detail),csv_bytes(SUMMARY,summary)


def self_test(raw):
    a,b = compute(raw)
    assert len(list(csv.DictReader(io.StringIO(a.decode())))) == 186
    assert len(list(csv.DictReader(io.StringIO(b.decode())))) == 6
    # Negative test: the source SHA lock must reject even a one-byte mutation.
    corrupted = bytearray(raw); corrupted[-3] ^= 1
    try:
        compute(bytes(corrupted))
    except ValueError as exc:
        assert 'SHA256' in str(exc)
    else:
        raise AssertionError('SHA mutation was not rejected')
    for case in CASES:
        assert case in a.decode()
    return a,b


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--detail',type=Path,required=True)
    parser.add_argument('--summary',type=Path,required=True)
    parser.add_argument('--write',action='store_true',help='Write results; default compares existing files')
    args=parser.parse_args()
    detail,summary=self_test(args.source.read_bytes())
    for path,output in ((args.detail,detail),(args.summary,summary)):
        if args.write:
            path.write_bytes(output)
        elif path.read_bytes()!=output:
            raise ValueError(f'Committed output differs: {path}')
    print('S10 LOAD-LEVEL QC PASS: 744 source rows, 186 gage-channel controls, 6 summaries; NOT material fatigue')
    print('detail_sha256='+hashlib.sha256(detail).hexdigest())
    print('summary_sha256='+hashlib.sha256(summary).hexdigest())
