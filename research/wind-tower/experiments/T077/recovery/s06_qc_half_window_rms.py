#!/usr/bin/env python3
"""Reproduce the 24-row half-window RMS diagnostic from the committed 744-row S06 CSV.
This is an exploratory source-data QC, not a stationarity hypothesis test or DLC1.2 PASS.
"""
import argparse
import csv
import hashlib
import io
from pathlib import Path

CASES = ('U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06')
CHANNELS = ('Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm')
SOURCE_SHA256 = '9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b'
HEAD = ('case','channel','n_gages','n_RMS_imbalance_gt20pct',
        'median_RMS_imbalance_pct','max_RMS_imbalance_pct','max_RMS_imbalance_gage',
        'DEL_m4_control_gage','DEL_m4_max','DEL_m10_control_gage','DEL_m10_max')

def summarize(source):
    raw = Path(source).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256, '744-row source SHA mismatch'
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    assert len(rows) == 744, '744-row cardinality mismatch'
    keys = [(r['case'],r['segment'],r['channel']) for r in rows]
    assert len(set(keys)) == 744, 'duplicate gage-channel'
    expected = {(c,f'CSEG_{i:02d}',ch) for c in CASES for i in range(1,32) for ch in CHANNELS}
    assert set(keys) == expected, '4x31x6 coverage mismatch'
    for r in rows:
        assert int(r['n_samples']) == 12001 and float(r['dt_s']) == 0.05
        assert float(r['duration_s']) == 600.0
        assert float(r['min']) <= float(r['mean']) <= float(r['max'])
        assert float(r['DEL_m4_Nref_1Hz']) >= 0 and float(r['DEL_m10_Nref_1Hz']) >= 0
    output = [HEAD]
    flagged = 0
    for c in CASES:
        for ch in CHANNELS:
            group = [r for r in rows if r['case'] == c and r['channel'] == ch]
            assert len(group) == 31
            diffs = []
            for r in group:
                a,b = float(r['rms_first_300s']),float(r['rms_last_300s'])
                assert a > 0 and b > 0
                diffs.append((r['segment'], 100*abs(a-b)/max(a,b)))
            diffs.sort(key=lambda x:x[1])
            nflag = sum(x[1] > 20 for x in diffs)
            flagged += nflag
            m4 = max(group,key=lambda r:float(r['DEL_m4_Nref_1Hz']))
            m10 = max(group,key=lambda r:float(r['DEL_m10_Nref_1Hz']))
            output.append((c,ch,'31',str(nflag),f'{diffs[15][1]:.6f}',
                           f'{diffs[-1][1]:.6f}',diffs[-1][0],m4['segment'],
                           f'{float(m4["DEL_m4_Nref_1Hz"]):.9f}',m10['segment'],
                           f'{float(m10["DEL_m10_Nref_1Hz"]):.9f}'))
    assert len(output) == 25 and flagged == 72, 'unexpected RMS diagnostic totals'
    buf=io.StringIO(newline='')
    csv.writer(buf,lineterminator='\n').writerows(output)
    return buf.getvalue()


# Source-level ETM seed sensitivity (not DLC1.2 convergence; 31 gages are not 31 seeds).
PAIR_A = 'U19p202140_ETM_S04'
PAIR_B = 'U19p202140_ETM_S06'
PAIR_HEAD = ('wind_speed_mps','turbulence','seed_A','seed_B','channel','m','n_paired_gages',
             'median_DEL_B_over_A','min_DEL_B_over_A','max_DEL_B_over_A',
             'n_B_greater_A','max_abs_pct_change','max_abs_pct_gage',
             'n_gage_z_nonidentical','max_gage_z_abs_diff_mm')

def paired_seed_summary(source):
    """Source-verified, same-U ETM S04/S06 paired DEL sensitivity, NOT seed convergence.

    Nominal segment labels match, but z coordinates differ in 26/31 gages.
    Do not silently call these the same physical stations or independent replicates.
    """
    import math
    import statistics
    raw = Path(source).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('744-row source SHA mismatch')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    if len(rows) != 744:
        raise ValueError('744-row cardinality mismatch')
    keyed = {}
    valid_segments = {f'CSEG_{i:02d}' for i in range(1,32)}
    for row in rows:
        key = (row['case'],row['segment'],row['channel'])
        if key in keyed:
            raise ValueError('duplicate case/segment/channel')
        if (row['case'] not in CASES or row['channel'] not in CHANNELS
            or row['segment'] not in valid_segments):
            raise ValueError('unrecognized case/segment/channel')
        if (int(row['n_samples']) != 12001 or float(row['dt_s']) != 0.05
            or float(row['duration_s']) != 600.0):
            raise ValueError('incompatible sampling')
        keyed[key] = row
    expected = {(c,f'CSEG_{i:02d}',ch) for c in CASES for i in range(1,32) for ch in CHANNELS}
    if set(keyed) != expected:
        raise ValueError('incomplete 4x31x6 source coverage')
    out = [PAIR_HEAD]
    for ch in CHANNELS:
        for m in (4,10):
            col = f'DEL_m{m}_Nref_1Hz'
            ratios = []
            dz_mm = []
            for i in range(1,32):
                seg = f'CSEG_{i:02d}'
                ra,rb = keyed[(PAIR_A,seg,ch)],keyed[(PAIR_B,seg,ch)]
                if ra['units'] != rb['units']:
                    raise ValueError('units identity mismatch')
                dz = 1000*abs(float(ra['gage_z_m'])-float(rb['gage_z_m']))
                if not math.isfinite(dz):
                    raise ValueError('invalid gage elevation')
                dz_mm.append(dz)
                a,b = float(ra[col]),float(rb[col])
                if not (math.isfinite(a) and math.isfinite(b) and a > 0 and b >= 0):
                    raise ValueError('invalid paired DEL')
                ratios.append((seg,b/a))
            values = [r for _,r in ratios]
            max_seg,max_ratio = max(ratios,key=lambda t:abs(t[1]-1))
            out.append(('19.202140','ETM','S04','S06',ch,str(m),'31',
                        f'{statistics.median(values):.9f}',f'{min(values):.9f}',
                        f'{max(values):.9f}',str(sum(v>1 for v in values)),
                        f'{100*abs(max_ratio-1):.6f}',max_seg,
                        str(sum(d>0 for d in dz_mm)),f'{max(dz_mm):.6f}'))
    buf = io.StringIO(newline='')
    csv.writer(buf,lineterminator='\n').writerows(out)
    return buf.getvalue()

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--qc',required=True,type=Path)
    p.add_argument('--paired-qc',type=Path,default=None,help='verify 12-row same-U ETM paired-seed sensitivity CSV')
    args=p.parse_args()
    got=summarize(args.source)
    expected=args.qc.read_text(encoding='utf-8')
    assert got==expected,'24-row QC table mismatch'
    if args.paired_qc is not None:
        paired = paired_seed_summary(args.source)
        assert paired == args.paired_qc.read_text(encoding='utf-8'), 'paired DEL QC table mismatch'
        print('S06 PASS: 12 paired-seed rows exact reproduction; 26/31 nominal gage z mismatches; NOT seed convergence')
    print('S06 PASS: 744 source rows SHA verified; 24 QC rows exact reproduction; 72/744 >20% RMS imbalance; NOT stationarity or material fatigue PASS')
