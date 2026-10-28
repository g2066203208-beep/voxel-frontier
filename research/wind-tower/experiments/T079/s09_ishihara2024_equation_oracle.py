#!/usr/bin/env python3
"""Ishihara, Iida & Wang (2024), Structures 60:105886: Eqs 1–6 oracle.

Page numbers: original PDF physical pp.6 (Eq1), 9 (Eqs2–3), 12 (Eq4),
16 (Eqs5–6); PDF SHA256 registered in T079 download receipt.
These are *reference-paper algebraic examples*, not Jiayu spectra, not
IEC 2025 rules, not wind-earthquake coupled simulation, not Abaqus output.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

DOI = '10.1016/j.istruc.2024.105886'
REGISTERED_PDF_SHA256 = '3ba73647db2b158f94c18c6dca0350489dc5c36e7826a298e754bd8a7f2d5238'
TABLE5 = {
    'FA': {'AEM_Hz': (0.358, 2.674, 3.964), 'SLM_Hz': (0.360, 2.960, 3.777)},
    'SS': {'AEM_Hz': (0.356, 2.314, 3.964), 'SLM_Hz': (0.356, 2.278, 3.931)},
}
TABLE9_BASE = {'wind_only_kNm': 23850, 'WE_0deg_kNm': 85017,
               'WE_45deg_kNm': 92375, 'WE_90deg_kNm': 105893}


def finite(*values):
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError('NONFINITE')


def jsce_level2_bedrock_sa(period_s, a0_m_s2=3.2):
    """Paper Eq(1), JSCE Japan 5%-damped BEDROCK target; NOT Jiayu design."""
    finite(period_s, a0_m_s2)
    if period_s < 0 or a0_m_s2 <= 0:
        raise ValueError('PERIOD_OR_A0')
    if period_s <= .16:
        return a0_m_s2*(1+9.375*period_s)
    if period_s < .64:
        return 2.5*a0_m_s2
    return 1.6*a0_m_s2/period_s


def resultant_xy(x, y):
    """Paper Eq(2): synchronized horizontal resultant at one instant."""
    finite(x, y)
    return math.hypot(x, y)


def mean_of_record_maxima(synchronous_xy_by_record):
    """Paper Eq(3): mean of *per-record* maxima; no cross-time mixing."""
    if not synchronous_xy_by_record:
        raise ValueError('NO_RECORDS')
    peaks=[]
    for series in synchronous_xy_by_record:
        if not series:
            raise ValueError('EMPTY_RECORD')
        peaks.append(max(resultant_xy(x,y) for x,y in series))
    return math.fsum(peaks)/len(peaks)


def paper_f85_normal_approx(record_peaks):
    """Paper Eq(4) Fave+1.04 sigma; population SD chosen explicitly here.

    This is an approximate normal-model 85th-percentile statistic, NOT
    the empirical sample quantile and NOT a code acceptance threshold.
    """
    if len(record_peaks) < 2:
        raise ValueError('INSUFFICIENT_RECORDS')
    finite(*record_peaks)
    avg=math.fsum(record_peaks)/len(record_peaks)
    sigma=math.sqrt(math.fsum((x-avg)**2 for x in record_peaks)/len(record_peaks))
    return avg+1.04*sigma


def vector_sum_normal_or_park(fs, fw_fa, fw_ss, theta_deg):
    """Paper Eq(5): scalar peak seismic FS projected relative to wind axes.

    Input F can be shear or bending, but do not mix them; maxima are
    not a synchronized W+E history. Angle in degrees.
    """
    finite(fs, fw_fa, fw_ss, theta_deg)
    if not 0 <= theta_deg <= 90:
        raise ValueError('ANGLE_OUTSIDE_PAPER_DOMAIN')
    th=math.radians(theta_deg)
    return math.hypot(fs*math.cos(th)+fw_fa, fs*math.sin(th)+fw_ss)


def srss_emergency(fs, fes):
    """Paper Eq(6): emergency-stop load peak and seismic load peak."""
    finite(fs, fes)
    return math.hypot(fs, fes)


def self_test():
    # Eq1 piecewise continuity at 0.16 and 0.64 seconds.
    for t,expected in ((0.,3.2),(.16,8.),(.4,8.),(.64,8.),(1.,5.12),(10.,.512)):
        assert math.isclose(jsce_level2_bedrock_sa(t),expected,rel_tol=1e-13)
    eps=1e-10
    assert abs(jsce_level2_bedrock_sa(.16-eps)-jsce_level2_bedrock_sa(.16+eps))<1e-7
    assert abs(jsce_level2_bedrock_sa(.64-eps)-jsce_level2_bedrock_sa(.64+eps))<1e-7
    # Eq2/3 must combine same-time components first, then take each record peak.
    assert resultant_xy(3,4)==5
    assert mean_of_record_maxima([[(3,4),(0,6)],[(5,12),(0,0)]])==9.5
    assert math.isclose(paper_f85_normal_approx([2,4,6]),4+1.04*math.sqrt(8/3))
    # Eq5: at theta=0, FS adds only to FA; at 90 deg only to SS.
    assert vector_sum_normal_or_park(10,3,4,0)==math.hypot(13,4)
    assert math.isclose(vector_sum_normal_or_park(10,3,4,90),math.hypot(3,14))
    assert math.isclose(vector_sum_normal_or_park(10,0,0,45),10)
    assert srss_emergency(3,4)==5
    # Source Table 5 explicitly shows higher-mode mismatch despite 1st mode match.
    ratios={axis:[100*(s/a-1) for a,s in zip(d['AEM_Hz'],d['SLM_Hz'])]
            for axis,d in TABLE5.items()}
    assert 10.6 < ratios['FA'][1] < 10.8
    assert abs(ratios['FA'][0]) < 1
    # Negative tests fail closed.
    bad=[lambda:jsce_level2_bedrock_sa(-1),
         lambda:jsce_level2_bedrock_sa(1,0),
         lambda:vector_sum_normal_or_park(1,2,3,100),
         lambda:vector_sum_normal_or_park(1,2,float('nan'),45),
         lambda:mean_of_record_maxima([]),
         lambda:mean_of_record_maxima([[]]),
         lambda:paper_f85_normal_approx([1])]
    for fn in bad:
        try:fn()
        except ValueError:pass
        else:raise AssertionError('FAIL_CLOSED_NEGATIVE_TEST')
    return {'status':'PASS_REFERENCE_EQUATIONS_SYNTHETIC_ONLY',
            'source_DOI':DOI,'registered_PDF_SHA256_NOT_REHASHED_THIS_RUN':REGISTERED_PDF_SHA256,
            'equations_checked':[1,2,3,4,5,6], 'negative_tests':len(bad),
            'paper_Table5_SLM_minus_AEM_frequency_pct':ratios,
            'paper_Table9_base_moment_kNm':TABLE9_BASE,
            'reference_sa_T6_m_s2':jsce_level2_bedrock_sa(6),
            'S05_site_spectrum_PASS':False,'S09_W_E_WE_RUN':0,
            'Abaqus_RUN':0,'physical_PASS':False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if not a.self_test:p.error('use --self-test')
    r=self_test()
    r['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
