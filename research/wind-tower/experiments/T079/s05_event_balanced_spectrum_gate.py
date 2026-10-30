#!/usr/bin/env python3
"""S05 diagnostic: event-balanced vs station-balanced long-period PSA.
REAL source tables are precomputed source spectra; this does NOT validate
record low-frequency reliability, design target, site applicability, or Abaqus.
Python 3 stdlib only. Refuse missing/changed input identities and bad data.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

PERIODS = (4.0, 6.0, 8.0, 10.0)
EXPECTED_PAIRS = {
    ("ci38457511", "CI.CLC"), ("ci38457511", "CI.PASC"),
    ("ci38457511", "CI.RVR"), ("ci39493944", "CI.CLC"),
    ("IT-2012-0008", "IT.NVL"),
}
US_COLUMNS = ("event_id", "station", "period_s", "pre20_pair_gm_psa_m_s2",
              "source_HNE_sha256", "source_HNN_sha256", "decision")
ESM_COLUMNS = ("event_id", "station", "period_s", "damping_ratio",
               "HNE_pseudoSa_m_s2", "HNN_pseudoSa_m_s2",
               "pair_gm_pseudoSa_m_s2", "HNE_numeric_sha256",
               "HNN_numeric_sha256", "status")
EXPECTED_US_DECISION = "REJECT_RAW__HOLD_PRE20_NO_LOWFREQ_TARGET"
EXPECTED_ESM_STATUS = "SOURCE_SPECTRUM_DIAGNOSTIC_NOT_JIAYU_DESIGN_PASS"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _positive(value, label):
    try:
        v = float(value)
    except (ValueError, TypeError):
        raise ValueError("NONNUMERIC_" + label) from None
    if not math.isfinite(v) or v <= 0:
        raise ValueError("NONPOSITIVE_OR_NONFINITE_" + label)
    return v


def _hash(s):
    if len(s) != 64 or any(c not in "0123456789abcdef" for c in s):
        raise ValueError("SOURCE_SHA256_FORMAT")
    return s


def _rows(raw, required):
    if not raw.strip():
        raise ValueError("ROWS_INVALID")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("HEADER_DUPLICATE")
    if any(k not in reader.fieldnames for k in required):
        raise ValueError("HEADER_MISSING")
    rows = list(reader)
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("ROWS_INVALID")
    return rows


def _parse(us_bytes, esm_bytes):
    spectra = {}
    provenance = {}
    for row in _rows(us_bytes, US_COLUMNS):
        if row["decision"] != EXPECTED_US_DECISION:
            raise ValueError("US_PROCESSING_IDENTITY")
        key = (row["event_id"], row["station"])
        if key not in EXPECTED_PAIRS - {("IT-2012-0008", "IT.NVL")}:
            raise ValueError("US_EVENT_STATION")
        t = _positive(row["period_s"], "PERIOD")
        if t not in PERIODS or (key, t) in spectra:
            raise ValueError("PERIOD_OR_DUPLICATE")
        hashes = (_hash(row["source_HNE_sha256"]), _hash(row["source_HNN_sha256"]))
        if key in provenance and provenance[key] != hashes:
            raise ValueError("PAIR_SHA_INCONSISTENT")
        provenance[key] = hashes
        spectra[key, t] = _positive(row["pre20_pair_gm_psa_m_s2"], "PSA")
    for row in _rows(esm_bytes, ESM_COLUMNS):
        key = (row["event_id"], row["station"])
        if key != ("IT-2012-0008", "IT.NVL"):
            raise ValueError("ESM_EVENT_STATION")
        if row["status"] != EXPECTED_ESM_STATUS:
            raise ValueError("ESM_PROCESSING_IDENTITY")
        if abs(_positive(row["damping_ratio"], "DAMPING") - .05) > 1e-12:
            raise ValueError("DAMPING_NOT_5_PERCENT")
        t = _positive(row["period_s"], "PERIOD")
        if t not in PERIODS or (key, t) in spectra:
            raise ValueError("PERIOD_OR_DUPLICATE")
        hashes = (_hash(row["HNE_numeric_sha256"]), _hash(row["HNN_numeric_sha256"]))
        if key in provenance and provenance[key] != hashes:
            raise ValueError("PAIR_SHA_INCONSISTENT")
        provenance[key] = hashes
        a = _positive(row["HNE_pseudoSa_m_s2"], "HNE_PSA")
        b = _positive(row["HNN_pseudoSa_m_s2"], "HNN_PSA")
        v = _positive(row["pair_gm_pseudoSa_m_s2"], "ESM_PAIR_PSA")
        if not math.isclose(math.sqrt(a * b), v, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError("ESM_GEOMETRIC_MEAN_MISMATCH")
        spectra[key, t] = v
    if set(provenance) != EXPECTED_PAIRS or set(spectra) != {
        (pair, t) for pair in EXPECTED_PAIRS for t in PERIODS
    }:
        raise ValueError("INCOMPLETE_3_EVENT_5_PAIR_4_PERIOD")
    return spectra, provenance


def calculate(us_bytes, esm_bytes):
    spectra, provenance = _parse(us_bytes, esm_bytes)
    event_ids = sorted({event for event, station in provenance})
    rows = []
    for t in PERIODS:
        vals = [spectra[pair, t] for pair in sorted(provenance)]
        station_gm = math.exp(sum(math.log(v) for v in vals) / len(vals))
        per_event = {}
        for event in event_ids:
            vv = [spectra[pair, t] for pair in sorted(provenance) if pair[0] == event]
            per_event[event] = math.exp(sum(math.log(v) for v in vv) / len(vv))
        event_gm = math.exp(sum(math.log(per_event[e]) for e in event_ids) / len(event_ids))
        ridge = [spectra[pair, t] for pair in sorted(provenance) if pair[0] == "ci38457511"]
        rows.append({
            "period_s": t,
            "pair_weighted_gm_m_s2": station_gm,
            "event_weighted_gm_m_s2": event_gm,
            "event_over_pair_ratio": event_gm / station_gm,
            "ridgecrest_station_max_over_min": max(ridge) / min(ridge),
            "independent_events": len(event_ids),
            "horizontal_pairs": len(provenance),
            "interpretation": "HETEROGENEOUS_PROCESSING_DIAGNOSTIC_NOT_DESIGN_TARGET",
        })
    return {
        "status": "INPUT_DIAGNOSTIC_ONLY_HOLD",
        "us_csv_sha256": digest(us_bytes),
        "esm_csv_sha256": digest(esm_bytes),
        "independent_event_ids": event_ids,
        "pair_count": len(provenance),
        "periods_s": list(PERIODS),
        "provenance_sha256": {
            event + "/" + station: list(provenance[(event, station)])
            for event, station in sorted(provenance)
        },
        "processing_warning": (
            "US uses unvalidated pre-event 20s mean removal; Italy uses ESM MP "
            "0.04Hz high-pass; cross-event PSA aggregations are descriptive only."
        ),
        "target_spectrum": "MISSING_NO_MATCH_METRIC",
        "usable_long_period_band": "NOT_VERIFIED",
        "independent_events_sufficient_for_design": "NOT_ASSESSED_NO_AUTHORIZED_CRITERION",
        "S05_PASS": False,
        "Abaqus_E_WE_RUN": 0,
        "rows": rows,
    }


def _fixture():
    u = io.StringIO()
    w = csv.DictWriter(u, fieldnames=US_COLUMNS)
    w.writeheader()
    for event, station in sorted(EXPECTED_PAIRS - {("IT-2012-0008", "IT.NVL")}):
        for t in PERIODS:
            w.writerow(dict(event_id=event, station=station, period_s=t,
                pre20_pair_gm_psa_m_s2="0.5",
                source_HNE_sha256="a"*64, source_HNN_sha256="b"*64,
                decision=EXPECTED_US_DECISION))
    e = io.StringIO()
    w = csv.DictWriter(e, fieldnames=ESM_COLUMNS)
    w.writeheader()
    for t in PERIODS:
        w.writerow(dict(event_id="IT-2012-0008", station="IT.NVL",
            period_s=t, damping_ratio="0.05", HNE_pseudoSa_m_s2="0.25",
            HNN_pseudoSa_m_s2="1", pair_gm_pseudoSa_m_s2="0.5",
            HNE_numeric_sha256="c"*64, HNN_numeric_sha256="d"*64,
            status=EXPECTED_ESM_STATUS))
    return u.getvalue().encode(), e.getvalue().encode()


def self_test():
    u, e = _fixture()
    x = calculate(u, e)
    assert len(x["rows"]) == 4 and x["pair_count"] == 5
    assert len(x["independent_event_ids"]) == 3
    for row in x["rows"]:
        assert math.isclose(row["event_weighted_gm_m_s2"], .5, rel_tol=1e-12)
        assert math.isclose(row["pair_weighted_gm_m_s2"], .5, rel_tol=1e-12)
        assert row["event_over_pair_ratio"] == 1
    checks = [
        (u.replace(b"0.5", b"nan", 1), e, "NONPOSITIVE_OR_NONFINITE_PSA"),
        (u.replace(b"ci39493944", b"ci38457511"), e, "PERIOD_OR_DUPLICATE"),
        (u.replace(b"REJECT_RAW__", b"ACCEPT_RAW__", 1), e, "US_PROCESSING_IDENTITY"),
        (u.replace(b"a"*64, b"z"*64, 1), e, "SOURCE_SHA256_FORMAT"),
        (u.replace(b"4.0", b"12.0", 1), e, "PERIOD_OR_DUPLICATE"),
        (u, e.replace(b"0.5", b"0.6", 1), "ESM_GEOMETRIC_MEAN_MISMATCH"),
        (u, e.replace(b"0.05", b"0.10", 1), "DAMPING_NOT_5_PERCENT"),
        (u, b"", "ROWS_INVALID"),
    ]
    for uu, ee, expected in checks:
        try:
            calculate(uu, ee)
        except ValueError as err:
            if str(err) != expected:
                raise AssertionError((expected, str(err)))
        else:
            raise AssertionError("accepted corrupted input: " + expected)
    print("S05_EVENT_BALANCE_SYNTHETIC_SELFTEST_PASS 4 positive + 8 negative")



# This reference-paper spectrum is NOT a China/Jiayu target and is never an S05 gate.
# DOI 10.1016/j.istruc.2024.105886, Ishihara et al. 2024, Eq.(1), PDF p.6.
REFERENCE_US_CSV_SHA256 = "45c71c29677dd0918e68c281e6552cedf6d1370a13f6abbf319349cdc1f5fc80"
REFERENCE_ESM_CSV_SHA256 = "4fd1ecf5f3010524e2c5c54dae4072e1187718344f3a64bec46490e9ec617def"
REFERENCE_DOI = "10.1016/j.istruc.2024.105886"


def reference_paper_spectrum_diagnostic(us_bytes, esm_bytes, enforce_source_sha=True):
    """Log-spectrum amplitude-only oracle; NOT wave scaling or code matching.

    Four discrete T=4/6/8/10s periods only, five pairs/three earthquakes,
    with heterogeneous preprocessing and unverified low-frequency fidelity.
    A post-scale residual is purely an algebraic best-fit diagnostic.
    """
    from s09_ishihara2024_equation_oracle import jsce_level2_bedrock_sa
    if enforce_source_sha and (digest(us_bytes) != REFERENCE_US_CSV_SHA256 or
                               digest(esm_bytes) != REFERENCE_ESM_CSV_SHA256):
        raise ValueError("REFERENCE_SOURCE_SHA256_CHANGED")
    spectra, provenance = _parse(us_bytes, esm_bytes)
    rows = []
    for event, station in sorted(provenance):
        residual = [math.log(spectra[((event, station), t)] /
                             jsce_level2_bedrock_sa(t)) for t in PERIODS]
        mean_log = math.fsum(residual) / len(residual)
        scale = math.exp(-mean_log)
        post = [v - mean_log for v in residual]
        rows.append({
            "event_id": event,
            "station": station,
            "source_HNE_sha256": provenance[(event, station)][0],
            "source_HNN_sha256": provenance[(event, station)][1],
            "period_count": len(PERIODS),
            "pre_scale_log_rmse": math.sqrt(math.fsum(v*v for v in residual)/len(residual)),
            "least_squares_amplitude_scale_DIAGNOSTIC": scale,
            "post_scale_log_rmse": math.sqrt(math.fsum(v*v for v in post)/len(post)),
            "max_abs_post_log_residual": max(abs(v) for v in post),
            "decision": "REJECT_DESIGN_USE_REFERENCE_PAPER_ONLY",
        })
    return {
        "status": "REFERENCE_PAPER_ALGEBRA_ONLY_NOT_DESIGN_SPECTRUM",
        "reference_DOI": REFERENCE_DOI,
        "reference_eq": "Ishihara_2024_Eq1_JSCE_Level2_bedrock_5pct_a0_3.2",
        "reference_sa_m_s2": {str(t): jsce_level2_bedrock_sa(t) for t in PERIODS},
        "us_csv_sha256": digest(us_bytes),
        "esm_csv_sha256": digest(esm_bytes),
        "source_US_csv_sha256": digest(us_bytes),
        "source_ESM_csv_sha256": digest(esm_bytes),
        "source_read_level": "previously archived 20 precomputed PSA rows; not raw waveforms",
        "source_processing": "US pre20 mean removal NOT low-frequency verified; ESM MP highpass 0.04Hz",
        "fit_definition": "ln(obs/target), unweighted 4-point RMSE; scale exp(-mean ln(obs/target))",
        "design_site_spectrum_PASS": False,
        "record_low_frequency_PASS": False,
        "actual_scaled_waveforms": 0,
        "Abaqus_E_WE_RUN": 0,
        "rows": rows,
    }


def reference_paper_self_test():
    from s09_ishihara2024_equation_oracle import jsce_level2_bedrock_sa
    u, e = _fixture()
    out = reference_paper_spectrum_diagnostic(u, e, enforce_source_sha=False)
    assert len(out["rows"]) == 5 and len(out["reference_sa_m_s2"]) == 4
    assert math.isclose(out["reference_sa_m_s2"]["10.0"], .512, rel_tol=1e-13)
    assert math.isclose(out["reference_sa_m_s2"]["4.0"], 1.28, rel_tol=1e-13)
    assert all(row["period_count"] == 4 and row["post_scale_log_rmse"] >= 0
               and row["post_scale_log_rmse"] <= row["pre_scale_log_rmse"]
               for row in out["rows"])
    expected_scale = math.exp(math.fsum(math.log(
        jsce_level2_bedrock_sa(t)/.5) for t in PERIODS)/4)
    assert all(math.isclose(row["least_squares_amplitude_scale_DIAGNOSTIC"],
                            expected_scale, rel_tol=1e-13) for row in out["rows"])
    for fn, error in [
        (lambda: reference_paper_spectrum_diagnostic(u, e), "REFERENCE_SOURCE_SHA256_CHANGED"),
        (lambda: reference_paper_spectrum_diagnostic(u.replace(b"0.5", b"nan", 1), e, False),
         "NONPOSITIVE_OR_NONFINITE_PSA"),
        (lambda: reference_paper_spectrum_diagnostic(u, e.replace(b"0.05", b"0.1", 1), False),
         "DAMPING_NOT_5_PERCENT"),
    ]:
        try: fn()
        except ValueError as exc:
            if str(exc) != error: raise AssertionError((error, str(exc))) from exc
        else: raise AssertionError("failed closed: " + error)
    print("S05_REFERENCE_PAPER_SYNTHETIC_PASS 4 positive + 3 negative; NOT DESIGN PASS")



# Source-derived per-record long-period triage. All five pairs remain HOLD.
SCREEN_COLUMNS = ("event_id","station","period_s","event_pair_count","gm_psa_m_s2",
    "HNE_sha256","HNN_sha256","processing","raw_vs_pre20_rel",
    "pre20_vs_linear_rel","pre20_end_displacement_m","original_receipt",
    "reported_highpass_Hz","f_over_fc","low_frequency_verified",
    "site_target_verified","design_wave","decision")


def candidate_screen(us_bytes, esm_bytes, enforce_source_sha=True):
    if enforce_source_sha and (digest(us_bytes) != REFERENCE_US_CSV_SHA256 or
                               digest(esm_bytes) != REFERENCE_ESM_CSV_SHA256):
        raise ValueError("SCREEN_SOURCE_SHA_CHANGED")
    spectra, hashes = _parse(us_bytes, esm_bytes)
    source_rows = _rows(us_bytes, US_COLUMNS) + _rows(esm_bytes, ESM_COLUMNS)
    out = []
    for row in source_rows:
        event, station = row["event_id"], row["station"]
        t = _positive(row["period_s"], "PERIOD")
        pair = (event, station)
        is_esm = event == "IT-2012-0008"
        if is_esm:
            fc = _positive(row["filter_low_Hz"], "FILTER")
            ratio = _positive(row["period_to_corner_ratio"], "PERIOD_CORNER")
            if not math.isclose(ratio, t*fc, rel_tol=1e-9):
                raise ValueError("ESM_FILTER_PERIOD_MISMATCH")
            _hash(row["source_zip_sha256"])
            raw_rel, lin_rel, drift, receipt = "NA", "NA", "NA", "processed_zip_only"
            processing = "ESM_MP_REPORTED_0p04HZ_HIGH_PASS"
            decision = "HOLD_ESM_INSTRUMENT_LOW_FREQ_AND_SITE_TARGET"
            fc_out, freq_ratio = fc, 1.0/(t*fc)
        else:
            raw = _positive(row["raw_pair_gm_psa_m_s2"], "RAW")
            pre = spectra[pair, t]
            linear = _positive(row["linear_pair_gm_psa_m_s2"], "LINEAR")
            raw_rel = float(row["raw_vs_pre20_pair_relative_change"])
            if not math.isfinite(raw_rel) or raw_rel < 0 or not math.isclose(
                    raw_rel, abs(raw/pre-1), rel_tol=1e-8, abs_tol=1e-9):
                raise ValueError("US_BASELINE_RATIO_MISMATCH")
            drift = float(row["max_abs_pre20_end_displacement_m"])
            if not math.isfinite(drift) or drift < 0:
                raise ValueError("US_DRIFT_INVALID")
            receipt = row["original_source_receipt_available"].lower()
            if receipt not in ("true","false"):
                raise ValueError("US_RECEIPT_INVALID")
            lin_rel = abs(linear/pre-1)
            processing = "US_20S_MEAN_REMOVAL_UNVERIFIED"
            decision = ("HOLD_US_BASELINE_LOW_FREQ_AND_SITE_TARGET" if receipt == "true"
                else "HOLD_US_ORIGINAL_RECEIPT_BASELINE_LOW_FREQ_TARGET")
            fc_out, freq_ratio = "NA", "NA"
        out.append(dict(event_id=event,station=station,period_s=t,
            event_pair_count=3 if event=="ci38457511" else 1,
            gm_psa_m_s2=spectra[pair,t],HNE_sha256=hashes[pair][0],
            HNN_sha256=hashes[pair][1],processing=processing,
            raw_vs_pre20_rel=raw_rel,pre20_vs_linear_rel=lin_rel,
            pre20_end_displacement_m=drift,original_receipt=receipt,
            reported_highpass_Hz=fc_out,f_over_fc=freq_ratio,
            low_frequency_verified="false",site_target_verified="false",
            design_wave="false",decision=decision))
    out.sort(key=lambda x:(x["event_id"],x["station"],x["period_s"]))
    if len(out)!=20 or len({x["event_id"] for x in out})!=3:
        raise ValueError("SCREEN_3EVENT_5PAIR_20PERIOD")
    return out


def screen_negative_tests(us_bytes, esm_bytes):
    assert len(candidate_screen(us_bytes,esm_bytes))==20
    checks = [
        (us_bytes.replace(b"true",b"unknown",1),esm_bytes,"US_RECEIPT_INVALID"),
        (us_bytes.replace(b",3.68462941064,true",b",-1,true",1),esm_bytes,"US_DRIFT_INVALID"),
        (us_bytes,esm_bytes.replace(b",0.040,0.160000",b",0.050,0.160000",1),
         "ESM_FILTER_PERIOD_MISMATCH"),
    ]
    for u,e,err in checks:
        try: candidate_screen(u,e,False)
        except ValueError as exc:
            if str(exc)!=err: raise AssertionError((err,str(exc))) from exc
        else: raise AssertionError("accepted invalid source: "+err)
    try: candidate_screen(us_bytes+b"\n",esm_bytes)
    except ValueError as exc:
        if str(exc)!="SCREEN_SOURCE_SHA_CHANGED": raise
    else: raise AssertionError("accepted changed source SHA")
    print("S05_REAL_FIVE_PAIR_SCREEN_PASS 20 rows + 4 negative; NO DESIGN PASS")



def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--reference-paper-benchmark", action="store_true")
    p.add_argument("--screen-csv", type=Path)
    p.add_argument("--us-csv", type=Path)
    p.add_argument("--esm-csv", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        reference_paper_self_test()
        return
    if not (args.us_csv and args.esm_csv and args.output):
        p.error("require --us-csv --esm-csv --output")
    if args.screen_csv:
        u,e=args.us_csv.read_bytes(),args.esm_csv.read_bytes()
        screen_negative_tests(u,e)
        rows=candidate_screen(u,e)
        with args.screen_csv.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=SCREEN_COLUMNS,lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        args.output.write_text(json.dumps({"status":"REAL_FIVE_PAIR_SCREEN_HOLD","US_SHA256":digest(u),"ESM_SHA256":digest(e),"rows":rows,"S05_PASS":False,"Abaqus_E_WE_RUN":0},indent=2)+"\n",encoding="utf-8")
        print("S05_REAL_3EVENT_5PAIR_20ROW_SCREEN_NOT_DESIGN_PASS")
        return
    result = (reference_paper_spectrum_diagnostic(args.us_csv.read_bytes(), args.esm_csv.read_bytes())
              if args.reference_paper_benchmark else
              calculate(args.us_csv.read_bytes(), args.esm_csv.read_bytes()))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print("S05_REFERENCE_PAPER_NOT_DESIGN_PASS" if args.reference_paper_benchmark else
          "S05_REAL_SOURCE_EVENT_BALANCED_DIAGNOSTIC_NOT_DESIGN_PASS",
          result["us_csv_sha256"], result["esm_csv_sha256"])
    for row in result["rows"]:
        print("S05_REFERENCE_PAPER_PAIR" if args.reference_paper_benchmark else "S05_REAL_PERIOD", row)


if __name__ == "__main__":
    main()
