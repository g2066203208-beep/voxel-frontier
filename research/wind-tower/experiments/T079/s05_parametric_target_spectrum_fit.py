#!/usr/bin/env python3
"""S05 real ESM RotD50 vs HYPOTHETICAL 6-degree/site-II/group-I target.

This is a reproducible shape/scale diagnostic, NOT GB/T50011 clause acceptance,
not a turbine-specific design spectrum, not a validated Jiayu site, and not an
Abaqus E/WE result. Public 2024 GB/T50011 clause 5.1.5 transcription suggests
Tg=.35s, alpha_max=.04, gamma=.9, eta1=.02 for the *illustrative* 5% case.
2024 official revision PDF and wind-specific applicability are NOT verified.
The building-spectrum 6s scope is enforced; periods 7/8/9/10s are EXCLUDED.
Python 3.10+ standard library; no production solver.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

SOURCE_SHA = "6f03869384193a4e00b27a11af6470ff3d11fcb73ebb08f0f19332b4edbe0205"
PERIODS = (.5,.75,1.,1.25,1.5,2.,2.5,3.,3.5,4.,5.,6.,7.,8.,9.,10.)
FIT_PERIODS = PERIODS[:12]
SOURCE_FIELD = "RotD50_psa_m_s2"
G = 9.80665
ALPHA_MAX = .04
TG = .35
GAMMA = .9
ETA1 = .02
HIGHPASS_HZ = .04
OUT = ("period_s","real_ESM_RotD50_psa_m_s2","hypothetical_target_psa_m_s2",
       "fitted_uniform_scale","scaled_real_psa_m_s2","scaled_over_target",
       "signed_log_ratio","f_over_0p04Hz_reported_highpass",
       "status")

def sha(b):
    return hashlib.sha256(b).hexdigest()

def rows_from_csv(raw):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    fields = reader.fieldnames or []
    if not fields or len(set(fields)) != len(fields):
        raise ValueError("HEADER_DUPLICATE_OR_MISSING")
    data = list(reader)
    if not data or any(None in row or any(v is None for v in row.values()) for row in data):
        raise ValueError("CSV_WIDTH_OR_EMPTY")
    return fields, data

def positive(v, name):
    try: n = float(v)
    except (ValueError, TypeError): raise ValueError("NONNUMERIC_"+name) from None
    if not math.isfinite(n) or n <= 0:
        raise ValueError("NONPOSITIVE_OR_NONFINITE_"+name)
    return n

def parse_source(raw, strict=True):
    if strict and sha(raw) != SOURCE_SHA:
        raise ValueError("ESM_ROT_D_SOURCE_SHA_MISMATCH")
    fields, data = rows_from_csv(raw)
    if "period_s" not in fields or SOURCE_FIELD not in fields or "status" not in fields:
        raise ValueError("SOURCE_COLUMNS")
    if len(data) != 16: raise ValueError("SOURCE_NOT_16_PERIODS")
    out = {}
    for i, row in enumerate(data):
        t = positive(row["period_s"], "PERIOD")
        if abs(t-PERIODS[i])>1e-12: raise ValueError("PERIOD_ORDER_OR_DUPLICATE")
        if row["status"]!="PROCESSED_RECORD_ORIENTATION_NUMERICAL_QC_NOT_DESIGN_WAVE":
            raise ValueError("SOURCE_DESIGN_STATUS_MISMATCH")
        out[t] = positive(row[SOURCE_FIELD], "ROTD50")
        if "frequency_over_0p04Hz_highpass" in fields:
            f = positive(row["frequency_over_0p04Hz_highpass"], "F_OVER_FC")
            if not math.isclose(f, 1/(t*HIGHPASS_HZ),rel_tol=1e-11):
                raise ValueError("FILTER_FREQUENCY_IDENTITY")
    return out

def provisional_shape(T, alpha_max=ALPHA_MAX, tg=TG):
    """5%-damped piecewise illustrative shape; no 6s extrapolation."""
    if not (math.isfinite(T) and .1<=T<=6 and alpha_max>0 and tg>.1 and 5*tg<6):
        raise ValueError("SPECTRUM_OUT_OF_DECLARED_DOMAIN")
    if T<=tg: alpha=alpha_max
    elif T<=5*tg: alpha=alpha_max*(tg/T)**GAMMA
    else: alpha=alpha_max*(.2**GAMMA-ETA1*(T-5*tg))
    if alpha<=0: raise ValueError("TARGET_NONPOSITIVE")
    return alpha*G

def parse_external_target(raw, expected_sha):
    if not expected_sha or sha(raw)!=expected_sha:
        raise ValueError("EXTERNAL_TARGET_SHA_REQUIRED_OR_MISMATCH")
    fields, data=rows_from_csv(raw)
    if set(fields)!= {"period_s","target_psa_m_s2"}:
        raise ValueError("EXTERNAL_TARGET_COLUMNS")
    if len(data)!=len(FIT_PERIODS): raise ValueError("TARGET_NOT_12_PERIODS")
    target={}
    for i,row in enumerate(data):
        t=positive(row["period_s"],"TARGET_PERIOD")
        if abs(t-FIT_PERIODS[i])>1e-12: raise ValueError("TARGET_PERIOD_ORDER")
        target[t]=positive(row["target_psa_m_s2"],"TARGET_PSA")
    return target

def fit(source,target):
    if set(source)!=set(PERIODS) or set(target)!=set(FIT_PERIODS):
        raise ValueError("SOURCE_TARGET_GRID_OR_DOMAIN")
    logs=[math.log(target[t]/source[t]) for t in FIT_PERIODS]
    # Closed-form minimizer of sum_i[ln(s*S_i/T_i)]^2; equal period weights.
    s=math.exp(sum(logs)/len(logs))
    table=[]
    for t in FIT_PERIODS:
        ratio=s*source[t]/target[t]
        table.append(dict(period_s=t,real_ESM_RotD50_psa_m_s2=source[t],
            hypothetical_target_psa_m_s2=target[t],fitted_uniform_scale=s,
            scaled_real_psa_m_s2=s*source[t],scaled_over_target=ratio,
            signed_log_ratio=math.log(ratio),
            f_over_0p04Hz_reported_highpass=1/(t*HIGHPASS_HZ),
            status="HYPOTHETICAL_TARGET_NUMERIC_FIT_NOT_SITE_DESIGN_OR_NATIVE"))
    log_rmse=math.sqrt(sum(r["signed_log_ratio"]**2 for r in table)/len(table))
    return table,dict(fitted_scale=s,log_rmse=log_rmse,
        maximum_absolute_log_residual=max(abs(r["signed_log_ratio"]) for r in table),
        minimum_scaled_over_target=min(r["scaled_over_target"] for r in table),
        maximum_scaled_over_target=max(r["scaled_over_target"] for r in table),
        periods_outside_illustrative_30pct_band=[
            r["period_s"] for r in table if abs(r["scaled_over_target"]-1)>.30],
        excluded_periods_over_6s=list(PERIODS[12:]),evaluated_period_count=len(table))

def render(table):
    buf=io.StringIO(newline="")
    w=csv.DictWriter(buf,fieldnames=OUT,lineterminator="\n")
    w.writeheader();w.writerows(table)
    return buf.getvalue().encode("utf-8")

def self_test():
    # Analytical shape continuity and strict 6s refusal.
    for t in (TG,5*TG):
        left=provisional_shape(t-1e-9)
        right=provisional_shape(t+1e-9)
        assert abs(left-right)<1e-8
    for bad in (6.0000001,10.,0.,float("nan")):
        try: provisional_shape(bad)
        except ValueError as e: assert str(e)=="SPECTRUM_OUT_OF_DECLARED_DOMAIN"
        else: raise AssertionError("ACCEPTED_OUT_OF_SCOPE_PERIOD")
    synthetic={t:0.2+1/(1+t) for t in PERIODS}
    doubled={t:2*synthetic[t] for t in FIT_PERIODS}
    table,stats=fit(synthetic,doubled)
    assert abs(stats["fitted_scale"]-2)<1e-14 and stats["log_rmse"]<1e-14
    altered=dict(doubled);altered[6.]=10*doubled[6.]
    _,miss=fit(synthetic,altered)
    assert miss["log_rmse"]>.1 and 6. in miss["periods_outside_illustrative_30pct_band"]
    try:fit(synthetic,{t:1 for t in FIT_PERIODS[:-1]})
    except ValueError as e: assert str(e)=="SOURCE_TARGET_GRID_OR_DOMAIN"
    else:raise AssertionError("ACCEPTED_MISSING_PERIOD")
    print("S05_PARAMETRIC_SHAPE_AND_SCALE_TESTS_PASS_NOT_DESIGN")
    print("S05_6S_DOMAIN_AND_4_LONG_PERIOD_EXCLUSIONS_PASS")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--real-rotd-csv",type=Path)
    p.add_argument("--target-csv",type=Path)
    p.add_argument("--expected-target-sha256")
    p.add_argument("--target-source-note")
    p.add_argument("--output",type=Path)
    p.add_argument("--receipt",type=Path)
    a=p.parse_args()
    if a.self_test:self_test()
    if a.real_rotd_csv:
        if not a.output or not a.receipt: p.error("--output and --receipt required")
        if len({str(x.resolve()) for x in (a.real_rotd_csv,a.output,a.receipt)})!=3:
            raise ValueError("SOURCE_OUTPUT_OVERLAP")
        raw=a.real_rotd_csv.read_bytes()
        source=parse_source(raw)
        if a.target_csv:
            if not a.target_source_note or not a.expected_target_sha256:
                p.error("external target requires SHA256 and provenance note")
            target=parse_external_target(a.target_csv.read_bytes(),a.expected_target_sha256)
            mode="EXTERNAL_UNVERIFIED_TARGET_INPUT"
        else:
            if a.expected_target_sha256 or a.target_source_note:
                p.error("target provenance supplied without target CSV")
            target={t:provisional_shape(t) for t in FIT_PERIODS}
            mode="PROVISIONAL_GBT50011_2024_5P1P5_SHAPE_ASSUMPTION"
        table,stats=fit(source,target)
        output=render(table)
        a.output.write_bytes(output)
        receipt=dict(status="S05_PARAMETRIC_NUMERIC_QC_ONLY_NO_SITE_DESIGN_PASS",
            input_rotd16_sha256=sha(raw),source_reading_level="ESM processed real 16-period RotD50 numeric table",
            input_record="ESM v3 IT-2012-0008/NVL/MP",source_record_si_sha256=
            "a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34",
            target_mode=mode,target_sha256=a.expected_target_sha256 if a.target_csv else None,
            target_source_note=a.target_source_note if a.target_csv else "assumed 6 degree, site II, group I, frequent event",
            alpha_max_assumed=ALPHA_MAX if not a.target_csv else None,
            tg_s_assumed=TG if not a.target_csv else None,
            damping_assumed=.05,shape_gamma_assumed=GAMMA,shape_eta1_assumed=ETA1,
            gravity_m_s2=G,fit_method="unweighted least squares of natural-log PSA ratios",
            diagnostic_30pct_band_is_NOT_a_standard_acceptance=True,
            **stats,output_csv_sha256=sha(output),output_csv_bytes=len(output),
            SOURCE="real ESM v3 processed RotD16 table, 16 periods, source SHA256 locked",
            REF="analytic minimization of squared logarithmic spectral residuals",
            STANDARD="GB/T50011-2010 (2024) 5.1.5 PUBLIC SECONDARY TRANSCRIPTION ONLY; official amendment PDF NOT READ",
            OFFICIAL="MOHURD announcement 2024 no.61 (effective 2024-08-01); not full official clauses",
            RUN="Python standard library real source-table fit, NOT Abaqus/OpenFAST",
            FIG="NONE",TAB="12-row provisional spectral-shape comparison",
            assumptions=["Tg=.35s and alpha_max=.04 for illustrative 6-degree/site-II/group-I frequent case only",
                         "5% SDOF damping, no building-to-wind-turbine applicability established",
                         "RotD50 is horizontal direction statistic, not arbitrary component or code-prescribed target",
                         "only 0.5–6s used; 7–10s excluded, not extrapolated"],
            error_budget="float64 algorithmic rounding negligible; target/site/instrument/structural uncertainties unbounded",
            failed_cases="self-test rejects periods >6s, missing target grid and shape mismatch",
            site_target_verified=False,authorized_clause_verified=False,
            E_WE_native_RUN=0,S05_PASS=False,S08_PASS=False)
        a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
        print("S05_REAL_ESM_ROTD50_VS_PROVISIONAL_TARGET_12_ROWS_HOLD",
              stats["fitted_scale"],stats["log_rmse"],stats["minimum_scaled_over_target"],
              stats["maximum_scaled_over_target"],sha(output))
    elif not a.self_test:p.error("provide --self-test and/or --real-rotd-csv")
if __name__=="__main__":main()
