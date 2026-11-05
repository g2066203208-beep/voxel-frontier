#!/usr/bin/env python3
"""S05: real CI.CLC miniSEED + StationXML full-response removal, research QC only.

Reproduce on the PR branch:
 python s05_clc_full_response_waveform_qc.py --self-test
 python s05_clc_full_response_waveform_qc.py --source-dir real-records/USGS_ci38457511/CI_CLC --output report.json
Requires ObsPy 1.5.x, NumPy and SciPy. Does not perform site matching or a structural run.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

PERIODS = (4.0, 6.0, 6.230957762865167, 8.0, 10.0)
PREFILT_HZ = (0.02, 0.04, 20.0, 25.0)
WATER_LEVEL_DB = 60.0
NPTS = 20001
DT = 0.01


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spectrum(a, period: float, dt: float = DT) -> float:
    """5%-damped zero-initial-state pseudo-Sa, Newmark average acceleration."""
    if len(a) < 2 or period <= 0 or dt <= 0 or not all(math.isfinite(float(x)) for x in a):
        raise ValueError("BAD_SPECTRUM_INPUT")
    w = 2.0 * math.pi / period
    k, c = w * w, 0.1 * w
    den = 1.0 + 0.5 * dt * c + 0.25 * dt * dt * k
    u = v = 0.0
    q = -float(a[0])
    peak = 0.0
    for i in range(1, len(a)):
        up = u + dt * v + 0.25 * dt * dt * q
        vp = v + 0.5 * dt * q
        nq = (-float(a[i]) - c * vp - k * up) / den
        u = up + 0.25 * dt * dt * nq
        v = vp + 0.5 * dt * nq
        q = nq
        peak = max(peak, abs(u))
    return k * peak


def pre20(a):
    if len(a) < 2000:
        raise ValueError("INSUFFICIENT_PREWINDOW")
    mean = sum(float(x) for x in a[:2000]) / 2000
    return [float(x) - mean for x in a], mean


def load_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        if next(r) != ["time_s", "accel"]:
            raise ValueError("CSV_HEADER")
        rows = [(float(t), float(v)) for t, v in r]
    if len(rows) != NPTS:
        raise ValueError("CSV_NPTS")
    for i, (t, v) in enumerate(rows):
        if not math.isfinite(v) or abs(t - i * DT) > 1e-7:
            raise ValueError("CSV_GRID")
    return [v for _, v in rows]


def self_test():
    a = [math.sin(i * .05) + .3 for i in range(2001)]
    b, m = pre20(a)
    bb, mm = pre20([v + 7 for v in a])
    assert abs(mm - m - 7) < 1e-12
    assert max(abs(x - y) for x, y in zip(b, bb)) < 1e-12
    assert spectrum([0] * 201, 6) == 0
    assert abs(spectrum([v * 2 for v in b], 6) / spectrum(b, 6) - 2) < 1e-12
    for bad in ([0], [0, float("nan")]):
        try:
            spectrum(bad, 6)
            raise AssertionError("NEGATIVE_ACCEPTED")
        except ValueError as e:
            assert str(e) == "BAD_SPECTRUM_INPUT"
    try:
        pre20([0] * 100)
        raise AssertionError("NEGATIVE_ACCEPTED")
    except ValueError as e:
        assert str(e) == "INSUFFICIENT_PREWINDOW"
    return "3_POSITIVE_3_NEGATIVE_PASS"


def process(source_dir: Path):
    import numpy as np
    from obspy import UTCDateTime, read, read_inventory
    receipt_path = source_dir / "source_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("station") != "CLC" or receipt.get("station_network") != "CI" or "ci38457511" not in receipt.get("event_catalog", ""):
        raise ValueError("EVENT_IDENTITY")
    for rel in ("original/CI_station_response.xml", "original/CI_waveform_counts.mseed",
                "CI_CLC_HNE_accel_mps2.csv", "CI_CLC_HNN_accel_mps2.csv"):
        expected = receipt["files_SHA256"][rel]
        if sha256(source_dir / rel) != expected:
            raise ValueError("SOURCE_SHA256_MISMATCH:" + rel)
    inv = read_inventory(str(source_dir / "original/CI_station_response.xml"))
    st = read(str(source_dir / "original/CI_waveform_counts.mseed"))
    t0 = UTCDateTime(receipt["common_start_utc"])
    rows = []
    for axis in ("HNE", "HNN"):
        csv_a = load_csv(source_dir / f"CI_CLC_{axis}_accel_mps2.csv")
        candidates = []
        for tr in st.select(network="CI", station="CLC", channel=axis, location=""):
            if abs(float(tr.stats.delta) - DT) > 1e-9:
                continue
            offset = int(round(float(t0 - tr.stats.starttime) / DT))
            if offset >= 0 and offset + NPTS <= int(tr.stats.npts):
                if abs(float(tr.stats.starttime + offset * DT - t0)) < 1e-5:
                    candidates.append((tr, offset))
        if len(candidates) != 1:
            raise ValueError(f"AMBIGUOUS_OR_MISSING_RAW_TRACE:{axis}:{len(candidates)}")
        tr, offset = candidates[0]
        if np.ma.isMaskedArray(tr.data) and np.ma.getmaskarray(tr.data).any():
            raise ValueError("MASKED_RAW_TRACE")
        sens = float(inv.get_response(tr.id, tr.stats.starttime).instrument_sensitivity.value)
        raw_a = np.asarray(tr.data[offset:offset + NPTS], dtype=np.float64) / sens
        csv_array = np.asarray(csv_a, dtype=np.float64)
        max_raw_diff = float(np.max(np.abs(raw_a - csv_array)))
        if not np.allclose(raw_a, csv_array, rtol=5e-8, atol=1e-8):
            raise ValueError("RAW_CSV_COUNTS_MISMATCH")
        # Full frequency-dependent deconvolution on the complete raw trace.
        # No implicit ObsPy demeaning/taper; explicit FFT pre-filter and water level.
        corrected = tr.copy()
        corrected.remove_response(inventory=inv, output="ACC", pre_filt=PREFILT_HZ,
                                  water_level=WATER_LEVEL_DB, zero_mean=False, taper=False)
        full = np.asarray(corrected.data[offset:offset + NPTS], dtype=np.float64)
        if full.size != NPTS or not np.isfinite(full).all():
            raise ValueError("INVALID_CORRECTED_WAVEFORM")
        old, old_offset = pre20(csv_a)
        new, new_offset = pre20(full)
        spectral = []
        for T in PERIODS:
            old_psa = spectrum(old, T)
            new_psa = spectrum(new, T)
            spectral.append({"period_s": T, "sensitivity_only_psa_m_s2": old_psa,
                             "full_response_psa_m_s2": new_psa,
                             "relative_change_percent": 100 * (new_psa / old_psa - 1) if old_psa else None})
        rows.append({"channel": axis, "raw_trace_id": tr.id, "raw_trace_npts": int(tr.stats.npts),
                     "aligned_start_utc": str(t0), "aligned_index": offset,
                     "sensitivity_counts_per_m_s2": sens,
                     "raw_vs_csv_max_abs_m_s2": max_raw_diff,
                     "pre20_sensitivity_offset_m_s2": old_offset,
                     "pre20_full_response_offset_m_s2": new_offset,
                     "full_response_pre20_pga_m_s2": max(abs(x) for x in new),
                     "full_response_candidate_samples_sha256": hashlib.sha256(
                         np.asarray(new, dtype="<f8").tobytes()).hexdigest(),
                     "spectra": spectral})
    return {
        "status": "S05_REAL_MINISEED_FULL_RESPONSE_REMOVAL_NUMERICAL_QC_NOT_SITE_PASS",
        "event_id": "ci38457511", "station": "CI.CLC",
        "source_level": "Original raw miniSEED and StationXML bytes, hash-matched to existing official SCEDC receipts",
        "SOURCE": {"mseed_sha256": receipt["raw_mseed_sha256"],
                   "stationxml_sha256": receipt["stationxml_sha256"],
                   "csv_sha256": {c["seed_id"]: c["csv_sha256"] for c in receipt["channels"]}},
        "REF": "ObsPy Trace.remove_response output=ACC, FFT frequency-domain inverse instrument transfer; Newmark beta=1/4 gamma=1/2 PSA",
        "STANDARD": "2025 IEC/GB/NB licensed clauses not checked; no site spectrum",
        "OFFICIAL": "SCEDC FDSN originals stored under T079",
        "RUN": "Native Python/ObsPy real waveform response removal and two-component numerical PSA; no structural solver",
        "FIG": 0, "TAB": "2 horizontal channels x 5 periods",
        "parameters": {"pre_filt_hz": PREFILT_HZ, "water_level_db": WATER_LEVEL_DB,
                       "output_units": "m/s^2", "damping": 0.05, "prewindow_s": 20,
                       "npts": NPTS, "dt_s": DT, "response_zero_mean": False,
                       "response_taper": False},
        "assumptions": ["200s stored window, not complete event", "First 20s is a candidate baseline only",
                        "FFT response removal affected by edges and pre-filter; no low-frequency noise PSD",
                        "No time-shift correction or site spectrum matching"],
        "error_budget": "Raw counts CSV equivalence <= 1e-8 m/s2 + 5e-8 relative; floating point double; deconvolution regularization and 200s window edge error unbounded; instrument low-frequency SNR unknown",
        "HOLD": "Pre-filter/water-level sensitivity, noise and low-frequency usable band, event onset and Jiayu target spectrum not validated; S05 PARTIAL, E/WE=0, 0/12 stage PASS",
        "test": self_test(), "channels": rows,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--source-dir", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.self_test:
        print(self_test())
        return
    if not args.source_dir or not args.output:
        p.error("--source-dir and --output required")
    result = process(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "test": result["test"],
                      "rows": [(x["channel"], x["raw_vs_csv_max_abs_m_s2"],
                                [round(s["relative_change_percent"], 6) for s in x["spectra"]])
                               for x in result["channels"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
