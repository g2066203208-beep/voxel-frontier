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

# Independent published worked-example gate. JRC bridge reference, NOT site design.
# European Commission JRC, EUR 25193 EN (2012), printed pp.249-251,
# Bridge Design to Eurocodes, sec.8.4.3.1 and 8.4.3.3.
JRC_REPORT = "https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/Bridge_Design-Eurocodes-Worked_examples.pdf"
JRC_BEAM_T1 = 6.230957762865167  # conditional 35-element beam, NOT native Abaqus
JRC_FIT_PERIODS = tuple(t for t in PERIODS if .2*JRC_BEAM_T1 <= t <= 4.0)
JRC_COLUMNS = ("period_s","real_ESM_RotD50_psa_m_s2","JRC_bridge_example_elastic_psa_m_s2",
    "logfit_scale_shape_only","scaled_record_psa_m_s2","scaled_over_example",
    "signed_log_ratio","within_0p2T1_to_1p5T1","JRC_4s_formula_domain","status")

def jrc_example_spectrum(t):
    """JRC 2012 example: Type 1, soil B, ag=.40g, S=1.2, TB=.15, TC=.5, TD=2.5.
    The 5%-damped elastic acceleration branch is evaluated only at 0<T<=4s.
    Do NOT extrapolate to 6.23s; EN1998-1 points to long-period Annex A.
    """
    if not math.isfinite(t) or not 0 < t <= 4.0:
        raise ValueError("JRC_OUTSIDE_4S_ACCELERATION_FORMULA_DOMAIN")
    ag=.4*G; s=1.2; tb=.15; tc=.5; td=2.5
    if t <= tb: return ag*s*(1+t/tb*(2.5-1))
    if t <= tc: return ag*s*2.5
    if t <= td: return ag*s*2.5*(tc/t)
    return ag*s*2.5*(tc*td/t**2)

def jrc_shape_gate(source):
    if set(source)!=set(PERIODS) or len(JRC_FIT_PERIODS)!=7:
        raise ValueError("JRC_SOURCE_GRID_OR_FIT_PERIODS")
    scale=math.exp(sum(math.log(jrc_example_spectrum(t)/source[t])
                       for t in JRC_FIT_PERIODS)/len(JRC_FIT_PERIODS))
    rows=[]
    for t in PERIODS:
        within=.2*JRC_BEAM_T1 <= t <= 1.5*JRC_BEAM_T1
        if t<=4:
            target=jrc_example_spectrum(t); ratio=scale*source[t]/target
            rows.append(dict(period_s=t,real_ESM_RotD50_psa_m_s2=source[t],
                JRC_bridge_example_elastic_psa_m_s2=target,
                logfit_scale_shape_only=scale,scaled_record_psa_m_s2=scale*source[t],
                scaled_over_example=ratio,signed_log_ratio=math.log(ratio),
                within_0p2T1_to_1p5T1=within,JRC_4s_formula_domain=True,
                status="RESEARCH_SHAPE_FIT_NOT_DESIGN_ACCEPTANCE"))
        else:
            rows.append(dict(period_s=t,real_ESM_RotD50_psa_m_s2=source[t],
                JRC_bridge_example_elastic_psa_m_s2="",logfit_scale_shape_only="",
                scaled_record_psa_m_s2="",scaled_over_example="",signed_log_ratio="",
                within_0p2T1_to_1p5T1=within,JRC_4s_formula_domain=False,
                status="EXCLUDED_NEEDS_LONG_PERIOD_ANNEX_A_OR_SITE_TARGET"))
    ratios=[scale*source[t]/jrc_example_spectrum(t) for t in JRC_FIT_PERIODS]
    return rows,dict(fitted_shape_only_scale=scale,fitted_periods_s=list(JRC_FIT_PERIODS),
        fitted_log_rmse=math.sqrt(sum(math.log(x)**2 for x in ratios)/len(ratios)),
        min_ratio=min(ratios),max_ratio=max(ratios),
        band_0p2T1_to_1p5T1_s=[.2*JRC_BEAM_T1,1.5*JRC_BEAM_T1],
        sampled_periods_in_band_s=[t for t in PERIODS if .2*JRC_BEAM_T1<=t<=1.5*JRC_BEAM_T1],
        excluded_over_4s_s=[t for t in PERIODS if t>4],
        provisional_beam_T1_s=JRC_BEAM_T1,
        JRC_example_does_not_cover_T1_or_full_band=True,
        single_event_only=True,site_target_verified=False)

def jrc_shape_self_test():
    assert abs(jrc_example_spectrum(.5)-11.76798)<1e-9
    for t in (.15,.5,2.5):
        assert abs(jrc_example_spectrum(t-1e-10)-jrc_example_spectrum(t+1e-10))<1e-7
    for bad in (0.,-1.,4.0000001,JRC_BEAM_T1,float("nan")):
        try:jrc_example_spectrum(bad)
        except ValueError as e:assert str(e)=="JRC_OUTSIDE_4S_ACCELERATION_FORMULA_DOMAIN"
        else:raise AssertionError("ACCEPTED_OUT_OF_SCOPE")
    synthetic={t:1/(1+t) for t in PERIODS}
    rows,stat=jrc_shape_gate(synthetic)
    assert len(rows)==16 and sum(r["JRC_4s_formula_domain"] for r in rows)==10
    assert len(stat["sampled_periods_in_band_s"])==12
    assert abs(sum(math.log(stat["fitted_shape_only_scale"]*synthetic[t]/
        jrc_example_spectrum(t)) for t in JRC_FIT_PERIODS))<1e-12
    try:jrc_shape_gate({t:1 for t in PERIODS[:-1]})
    except ValueError:pass
    else:raise AssertionError("ACCEPTED_MISSING_SOURCE_PERIOD")
    print("JRC_BRIDGE_16PERIOD_4S_DOMAIN_7FIT_TESTS_PASS_NOT_DESIGN")

def jrc_cli(argv):
    parser=argparse.ArgumentParser(description="JRC bridge example: source-backed S05 shape-only QC")
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--real-rotd-csv",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--receipt",type=Path)
    a=parser.parse_args(argv)
    if a.self_test:jrc_shape_self_test()
    if a.real_rotd_csv:
        if not a.output or not a.receipt:parser.error("output and receipt required")
        if len({str(p.resolve()) for p in (a.real_rotd_csv,a.output,a.receipt)})!=3:
            raise ValueError("JRC_SOURCE_OUTPUT_PATH_COLLISION")
        raw=a.real_rotd_csv.read_bytes();source=parse_source(raw,strict=True)
        rows,stats=jrc_shape_gate(source)
        buf=io.StringIO(newline="")
        writer=csv.DictWriter(buf,fieldnames=JRC_COLUMNS,lineterminator="\n")
        writer.writeheader();writer.writerows(rows)
        table=buf.getvalue().encode("utf-8")
        a.output.write_bytes(table)
        receipt=dict(classification="S05_PUBLISHED_JRC_BRIDGE_EXAMPLE_SHAPE_QC_NOT_SITE_DESIGN",
            SOURCE={"real_rotd16_sha256":sha(raw),
                "record":"ESM v3 IT-2012-0008/IT.NVL/HN/MP processed RotD50",
                "processed_acceleration_sha256":"a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34"},
            REF={"report":"European Commission JRC EUR 25193 EN (2012), Bridge Design to Eurocodes",
                 "url":JRC_REPORT,"printed_pages":"249-251, sec.8.4.3.1, Fig.8.51, sec.8.4.3.3",
                 "reading_level":"Official JRC public PDF text, not licensed EN standard full text"},
            STANDARD="JRC quotes EN1998-1/2, no authorized GB/IEC/EN clause acceptance",
            OFFICIAL="European Commission JRC worked example public PDF",
            RUN="Python 3 standard library; existing real RotD50 16-period table; no native E/WE",
            FIG="JRC Fig.8.51 is reference only; no new Abaqus figure",
            TAB="16 rows: 10 research comparison, 6 >4s explicitly excluded",
            published_example={"ag_g":.4,"S":1.2,"TB_s":.15,"TC_s":.5,"TD_s":2.5,
                "damping_ratio":.05,"ground_type":"B (bridge, NOT IT.NVL C or Jiayu)"},
            **stats,
            assumptions=["Bridge worked example only; 0.4g NOT Jiayu hazard",
                "5% damping, provisional beam T1 not native PT/contact T1",
                "single Italian event not an ensemble, log-fit is NOT wave matching",
                "no long-period extrapolation beyond 4s"],
            error_budget={"arithmetic":"float64, continuity and missing-source negative tests",
                "sampling":"16 discrete periods only, no continuous-band proof",
                "long_period":"Annex A NOT READ; T1=6.23s outside JRC comparison domain",
                "site_and_physics":"unbounded pending site target and native PT/contact modes"},
            failure_tests=["reject T>4s","reject missing period","reject source SHA mismatch"],
            output_csv_sha256=sha(table),S05_PASS=False,S08_PASS=False,native_Abaqus_E_WE=0,
            HOLD="no site-specific validated long-period spectrum and no native structural modes")
        a.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("S05_JRC_SHAPE_GATE_REAL_ESM",stats["fitted_shape_only_scale"],
              stats["fitted_log_rmse"],stats["min_ratio"],stats["max_ratio"],sha(table))
    elif not a.self_test:parser.error("provide --self-test and/or --real-rotd-csv")

if __name__=="__main__":
    import sys
    if "--jrc-example" in sys.argv:
        jrc_cli([v for v in sys.argv[1:] if v!="--jrc-example"])
    else: main()
