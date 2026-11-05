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



def _validate_response_config(pre_filt, water_level, npts=NPTS):
    if len(pre_filt) != 4 or not all(math.isfinite(float(x)) for x in pre_filt):
        raise ValueError("BAD_PREFILT")
    if not (0 < pre_filt[0] < pre_filt[1] < pre_filt[2] < pre_filt[3] < 0.5 / DT):
        raise ValueError("BAD_PREFILT")
    if not math.isfinite(float(water_level)) or not (0 <= water_level <= 200):
        raise ValueError("BAD_WATER_LEVEL")
    if npts < 4001:
        raise ValueError("INSUFFICIENT_RESPONSE_WINDOW")


def sensitivity_self_test():
    _validate_response_config(PREFILT_HZ, WATER_LEVEL_DB)
    _validate_response_config((0.01, 0.02, 20.0, 25.0), 40)
    rejected = 0
    for filt, wl, n in (
        ((0.02, 0.02, 20, 25), 60, NPTS),
        ((0.04, 0.02, 20, 25), 60, NPTS),
        ((0.02, 0.04, 25, 20), 60, NPTS),
        ((0.02, 0.04, 20, 55), 60, NPTS),
        (PREFILT_HZ, float("nan"), NPTS),
        (PREFILT_HZ, -1, NPTS),
        (PREFILT_HZ, 60, 3000),
    ):
        try:
            _validate_response_config(filt, wl, n)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("INVALID_SENSITIVITY_CONFIG_ACCEPTED")
    assert rejected == 7
    return "2_POSITIVE_7_NEGATIVE_PASS"


def response_sensitivity(source_dir: Path, baseline: dict):
    """Sensitivity of real waveform PSA, not a low-frequency or site validation.

    Full-record pre-filter and water-level variations share the same input.
    Edge experiment compares full-record response trimmed to [10s,190s] with
    response removal performed on that identical 180.01s raw-data window.
    """
    import numpy as np
    from obspy import UTCDateTime, read, read_inventory

    sensitivity_self_test()
    inv = read_inventory(str(source_dir / "original/CI_station_response.xml"))
    stream = read(str(source_dir / "original/CI_waveform_counts.mseed"))
    receipt = json.loads((source_dir / "source_receipt.json").read_text(encoding="utf-8"))
    t0 = UTCDateTime(receipt["common_start_utc"])
    variants = (
        ("baseline", PREFILT_HZ, WATER_LEVEL_DB),
        ("prefilter_lower_corner", (0.01, 0.02, 20.0, 25.0), WATER_LEVEL_DB),
        ("prefilter_higher_corner", (0.04, 0.08, 20.0, 25.0), WATER_LEVEL_DB),
        ("water_level_40dB", PREFILT_HZ, 40.0),
        ("water_level_80dB", PREFILT_HZ, 80.0),
    )
    result_rows = []
    for base_channel in baseline["channels"]:
        axis = base_channel["channel"]
        candidates = []
        for tr in stream.select(network="CI", station="CLC", channel=axis, location=""):
            offset = int(round(float(t0 - tr.stats.starttime) / DT))
            if abs(float(tr.stats.delta) - DT) < 1e-9 and offset >= 0 and offset + NPTS <= int(tr.stats.npts):
                if abs(float(tr.stats.starttime + offset * DT - t0)) < 1e-5:
                    candidates.append((tr, offset))
        if len(candidates) != 1:
            raise ValueError("SENSITIVITY_TRACE_IDENTITY:" + axis)
        tr, offset = candidates[0]
        series = {}
        for label, filt, water in variants:
            _validate_response_config(filt, water)
            corrected = tr.copy()
            corrected.remove_response(inventory=inv, output="ACC",
                                      pre_filt=filt, water_level=water,
                                      zero_mean=False, taper=False)
            x = np.asarray(corrected.data[offset:offset + NPTS], dtype=np.float64)
            if x.size != NPTS or not np.isfinite(x).all():
                raise ValueError("INVALID_SENSITIVITY_WAVEFORM:" + label)
            series[label] = x
        reference, _ = pre20(series["baseline"])
        reference_psa = [spectrum(reference, T) for T in PERIODS]
        for j, original in enumerate(base_channel["spectra"]):
            if abs(reference_psa[j] - original["full_response_psa_m_s2"]) > 1e-9 * max(1.0, reference_psa[j]):
                raise ValueError("BASELINE_REGRESSION_MISMATCH:" + axis)
        for label, filt, water in variants:
            corrected, _ = pre20(series[label])
            psa = [spectrum(corrected, T) for T in PERIODS]
            changes = [100 * (v / ref - 1) if ref > 1e-12 else None
                       for v, ref in zip(psa, reference_psa)]
            result_rows.append({
                "channel": axis, "scenario": label, "pre_filt_hz": list(filt),
                "water_level_db": water, "npts": NPTS,
                "reference": "same original full-record baseline",
                "periods_s": list(PERIODS), "psa_m_s2": psa,
                "baseline_psa_m_s2": reference_psa,
                "relative_change_percent": changes,
                "max_abs_change_percent": max(abs(x) for x in changes if x is not None),
            })

        # Edge effect: identical evaluation interval, different deconvolution
        # input length. This isolates a processing-window dependence, not SNR.
        edge_n = 1000
        short = tr.copy()
        short.data = np.asarray(tr.data[offset + edge_n:offset + NPTS - edge_n]).copy()
        short.stats.starttime = t0 + edge_n * DT
        _validate_response_config(PREFILT_HZ, WATER_LEVEL_DB, int(short.stats.npts))
        short.remove_response(inventory=inv, output="ACC",
                              pre_filt=PREFILT_HZ, water_level=WATER_LEVEL_DB,
                              zero_mean=False, taper=False)
        x_short = np.asarray(short.data, dtype=np.float64)
        x_full_common = series["baseline"][edge_n:-edge_n]
        if x_short.size != NPTS - 2 * edge_n or not np.isfinite(x_short).all():
            raise ValueError("EDGE_WINDOW_INVALID")
        short_pre, _ = pre20(x_short)
        common_pre, _ = pre20(x_full_common)
        short_psa = [spectrum(short_pre, T) for T in PERIODS]
        common_psa = [spectrum(common_pre, T) for T in PERIODS]
        changes = [100 * (v / ref - 1) if ref > 1e-12 else None
                   for v, ref in zip(short_psa, common_psa)]
        result_rows.append({
            "channel": axis, "scenario": "edge_trim_10s_each_side",
            "pre_filt_hz": list(PREFILT_HZ), "water_level_db": WATER_LEVEL_DB,
            "npts": NPTS - 2 * edge_n, "edge_trim_s_each_side": 10.0,
            "reference": "full-record deconvolution evaluated on identical 10s..190s interval",
            "periods_s": list(PERIODS), "psa_m_s2": short_psa,
            "baseline_psa_m_s2": common_psa, "relative_change_percent": changes,
            "max_abs_change_percent": max(abs(x) for x in changes if x is not None),
        })
    return {
        "status": "S05_REAL_WAVEFORM_PROCESSING_PARAMETER_SENSITIVITY_NOT_SITE_PASS",
        "SOURCE": baseline["SOURCE"],
        "REF": "ObsPy 1.5.1 remove_response + Newmark 5% PSA; shared real miniSEED and StationXML",
        "STANDARD": "No new licensed IEC/GB/NB clause read; no Jiayu site spectrum",
        "OFFICIAL": "SCEDC source bytes hash-verified by parent process",
        "RUN": "Native original-waveform non-production QC (requires CI execution)",
        "FIG": 0, "TAB": "2 channels x 6 scenarios x 5 periods = 60 PSA",
        "parameters": {
            "baseline_prefilt_hz": list(PREFILT_HZ),
            "baseline_water_level_db": WATER_LEVEL_DB,
            "sensitivity_prefilt_hz": [[0.01, 0.02, 20, 25], [0.04, 0.08, 20, 25]],
            "sensitivity_water_level_db": [40, 80],
            "edge_trim_s_each_side": 10, "dt_s": DT, "damping": 0.05,
            "prewindow_s": 20, "response_zero_mean": False, "response_taper": False,
        },
        "assumptions": [
            "20s prewindow is an unvalidated baseline candidate; full event onset not established",
            "Edge experiment uses the same 10..190s evaluation samples; deconvolution window differs",
            "Relative changes are processing sensitivity, not instrument calibration error",
            "Water level and pre-filter sweeps do not establish usable long-period SNR",
        ],
        "error_budget": "64-bit numeric; exact source hash via parent process; baseline regression tolerance 1e-9*max(1,PSA) m/s2; parameter/edge variation quantified but no physical uncertainty threshold preapproved",
        "HOLD": "No long-period noise/SNR, event-onset, station/site transfer, target-spectrum or structural verification; S05 PARTIAL, E/WE=0, 0/12",
        "test": sensitivity_self_test(),
        "rows": result_rows,
        "max_abs_prefilter_percent": max(r["max_abs_change_percent"] for r in result_rows if r["scenario"].startswith("prefilter_")),
        "max_abs_water_level_percent": max(r["max_abs_change_percent"] for r in result_rows if r["scenario"].startswith("water_level_")),
        "max_abs_edge_percent": max(r["max_abs_change_percent"] for r in result_rows if r["scenario"].startswith("edge_trim_")),
    }



def _band_power_20s(values, fs=100.0):
    """One 20 s Hann periodogram; 0.05 Hz bin spacing, NOT a calibrated noise PSD."""
    import numpy as np
    from scipy.signal import periodogram
    a = np.asarray(values, dtype=np.float64)
    if a.size != 2000 or not np.isfinite(a).all():
        raise ValueError("BAD_BAND_WINDOW")
    freq, psd = periodogram(a, fs=fs, window="hann", detrend="linear",
                            scaling="density", nfft=a.size)
    mask = (freq >= 0.1 - 1e-12) & (freq <= 0.25 + 1e-12)
    if int(mask.sum()) != 4:
        raise ValueError("BAD_BAND_BINS")
    power = float(psd[mask].sum() * (fs / a.size))
    if not math.isfinite(power) or power < 0:
        raise ValueError("BAD_BAND_POWER")
    return power


def _snr_ratio(noise_power, signal_powers):
    if not math.isfinite(float(noise_power)) or noise_power <= 0:
        raise ValueError("NO_NOISE_POWER")
    if not signal_powers or not all(math.isfinite(float(v)) and v >= 0 for v in signal_powers):
        raise ValueError("BAD_SIGNAL_POWER")
    ratio = float(sum(signal_powers) / len(signal_powers) / noise_power)
    if ratio <= 0:
        raise ValueError("NO_SIGNAL_POWER")
    return ratio, 10.0 * math.log10(ratio)


def snr_self_test():
    import numpy as np
    t = np.arange(2000, dtype=float) * DT
    base = np.sin(2 * np.pi * 0.2 * t)
    p = _band_power_20s(base)
    assert p > 0
    ratio, db = _snr_ratio(p, [4*p, 4*p, 4*p])
    assert abs(ratio - 4) < 1e-12 and abs(db - 6.020599913279624) < 1e-12
    assert _band_power_20s(base + 10) > 0  # linear detrend removes constant offset
    rejected = 0
    for bad in (np.zeros(100), np.full(2000, np.nan), np.full(2000, np.inf)):
        try:
            _band_power_20s(bad)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("BAD_BAND_ACCEPTED")
    for noise, signal in ((0, [1]), (-1, [1]), (1, [float("nan")]), (1, [])):
        try:
            _snr_ratio(noise, signal)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("BAD_SNR_ACCEPTED")
    assert rejected == 7
    return "3_POSITIVE_7_NEGATIVE_PASS"


def low_frequency_snr(source_dir: Path, baseline: dict):
    """Pre-origin chronology + observed 0.1-0.25 Hz window power ratios.

    The first 20 s contains only 2 cycles at 0.1 Hz and is ONE noise sample.
    Ratios are observed signal-plus-noise/noise, NOT intrinsic SNR or usable-band PASS.
    Sensitivity-only original CSV is used to avoid deconvolution prefilter leakage.
    """
    import numpy as np
    from datetime import datetime, timedelta, timezone
    receipt = json.loads((source_dir / "source_receipt.json").read_text(encoding="utf-8"))
    def utc(s):
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            raise ValueError("NAIVE_UTC")
        return d.astimezone(timezone.utc)
    origin = utc(receipt["event_utc"])
    start = utc(receipt["common_start_utc"])
    origin_from_start_s = (origin - start).total_seconds()
    pre_event_margin_s = (origin - (start + timedelta(seconds=20))).total_seconds()
    if pre_event_margin_s <= 0 or not (20 < origin_from_start_s < 40):
        raise ValueError("PREWINDOW_NOT_PREORIGIN")
    if baseline.get("event_id") != "ci38457511" or receipt.get("station") != "CLC":
        raise ValueError("SNR_EVENT_IDENTITY")
    rows = []
    for ch in baseline["channels"]:
        axis = ch["channel"]
        a = np.asarray(load_csv(source_dir / f"CI_CLC_{axis}_accel_mps2.csv"), dtype=float)
        noise = _band_power_20s(a[0:2000])
        signal = [_band_power_20s(a[i:i+2000]) for i in (4000, 6000, 8000)]
        late = [_band_power_20s(a[i:i+2000]) for i in (12000, 14000, 16000)]
        signal_ratio, signal_db = _snr_ratio(noise, signal)
        late_ratio, late_db = _snr_ratio(noise, late)
        rows.append({
            "channel": axis,
            "noise_window_s": [0, 20], "signal_windows_s": [[40, 60], [60, 80], [80, 100]],
            "late_windows_s": [[120, 140], [140, 160], [160, 180]],
            "noise_bandpower_m2_s4": noise,
            "signal_bandpowers_m2_s4": signal, "late_bandpowers_m2_s4": late,
            "observed_signal_plus_noise_over_pre_event_power_ratio": signal_ratio,
            "observed_signal_plus_noise_over_pre_event_power_db": signal_db,
            "observed_late_over_pre_event_power_ratio": late_ratio,
            "observed_late_over_pre_event_power_db": late_db,
            "pre20_rms_m_s2": float(np.sqrt(np.mean(a[:2000]**2))),
            "signal40_100_rms_m_s2": float(np.sqrt(np.mean(a[4000:10000]**2))),
        })
    return {
        "status": "S05_REAL_PREORIGIN_CHRONOLOGY_AND_LOW_FREQ_POWER_QC_NOT_BAND_PASS",
        "SOURCE": baseline["SOURCE"], "OFFICIAL": "SCEDC source event origin and raw CSV SHA-verified by process()",
        "REF": "SciPy Hann periodogram 20s, linear detrend, 0.05Hz bin width, 0.1/0.15/0.2/0.25Hz; ObsPy waveform source identity",
        "STANDARD": "No IEC/GB/NB licensed clause or Jiayu site spectrum verified",
        "RUN": "Native non-production numerical PSD QC only; no structural E/WE",
        "FIG": 0, "TAB": "2 channels x (1 pre-event + 3 shaking + 3 late) 20s windows",
        "event_origin_utc": receipt["event_utc"], "record_start_utc": receipt["common_start_utc"],
        "origin_from_start_s": origin_from_start_s, "pre20_end_before_origin_s": pre_event_margin_s,
        "chronology": "0..20s is before catalog origin, not independently verified stationary noise or onset",
        "frequency_hz": [0.1, 0.15, 0.2, 0.25], "bin_width_hz": 0.05,
        "parameters": {"sample_dt_s": DT, "segment_length_s": 20, "window": "Hann",
                       "detrend": "linear", "source": "sensitivity-only original acceleration CSV"},
        "assumptions": [
            "Catalog origin precedes local arrivals; origin chronology does not prove pre-event stationarity",
            "Only two 0.1Hz cycles per 20s segment; 0.05Hz resolution and single pre-event sample",
            "40..100s windows are fixed in advance, not peak-picked; power includes background noise",
            "No deconvolution applied to this spectral-power comparison; low-frequency instrument self-noise unverified"
        ],
        "error_budget": "Double precision and 0.05Hz frequency bins; single 20s noise periodogram has high statistical variance; no approved SNR acceptance threshold",
        "test": snr_self_test(), "channels": rows,
        "HOLD": "Cannot infer reliable 4-10s signal band from a single 20s pre-event window; site target spectrum and instrument self-noise still absent; S05 PARTIAL, E/WE=0, 0/12"
    }



def _noise_window_metrics(values):
    """Pre-event variability and heuristic transient trigger, NOT seismic phase picking."""
    import numpy as np
    from scipy.signal import periodogram
    x = np.asarray(values, dtype=np.float64)
    if x.size != NPTS or not np.isfinite(x).all():
        raise ValueError("BAD_NOISE_WINDOW_INPUT")
    rms5 = [float(np.std(x[i:i+500])) for i in (0,500,1000,1500)]
    cv5 = float(np.std(rms5, ddof=1)/np.mean(rms5)) if np.mean(rms5)>0 else None
    power10 = []
    for i in (0,500,1000):
        f,p = periodogram(x[i:i+1000],fs=100,window="hann",detrend="linear",scaling="density")
        mask = np.isclose(f,0.1) | np.isclose(f,0.2)
        if int(mask.sum()) != 2: raise ValueError("BAD_TEN_SECOND_FREQUENCY_GRID")
        power10.append(float(np.sum(p[mask])*0.1))
    p20 = _band_power_20s(x[:2000])
    shake = [_band_power_20s(x[i:i+2000]) for i in (4000,5000,6000,7000,8000)]
    db = [10*math.log10(v/p20) if v>0 and p20>0 else None for v in shake]
    # Difference-energy trigger: 1s moving RMS >= 8x first-20s RMS for 0.5s.
    dx = np.diff(x,prepend=x[0])
    baseline = float(np.sqrt(np.mean(dx[:2000]**2)))
    moving = np.sqrt(np.convolve(dx**2,np.ones(100)/100,mode="valid"))
    hold = np.convolve((moving>=max(8*baseline,1e-12)).astype(int),np.ones(50,dtype=int),mode="valid")
    hits = np.flatnonzero(hold[2000:]>=50)
    trigger = float((int(hits[0])+2000)*DT) if hits.size else None
    return {"pre5s_demeaned_rms_m_s2":rms5,"pre5s_rms_cv":cv5,
            "pre10s_overlapping_power_m2_s4":power10,
            "pre10s_power_max_min_ratio":max(power10)/min(power10) if min(power10)>0 else None,
            "pre20s_bandpower_m2_s4":p20,
            "shaking_20s_overlapping_power_m2_s4":shake,
            "shaking_over_pre20_db":db,
            "shaking_db_min_max":[min(v for v in db if v is not None),max(v for v in db if v is not None)]
                if any(v is not None for v in db) else None,
            "difference_baseline_rms_m_s2_per_sample":baseline,
            "trigger_threshold_m_s2_per_sample":max(8*baseline,1e-12),
            "candidate_1s_window_start_trigger_s":trigger,
            "candidate_trigger_is_confirmed_phase":False}


def noise_window_self_test():
    import numpy as np
    t=np.arange(NPTS)*DT
    x=0.0001*np.sin(2*np.pi*3*t)
    x[t>=45]+=0.3*np.sin(2*np.pi*3*t[t>=45])
    q=_noise_window_metrics(x)
    assert 43<=q["candidate_1s_window_start_trigger_s"]<=46
    r=_noise_window_metrics(x+5)
    assert abs(q["pre5s_rms_cv"]-r["pre5s_rms_cv"])<1e-8
    assert _noise_window_metrics(np.zeros(NPTS))["candidate_1s_window_start_trigger_s"] is None
    for bad in (np.zeros(100),np.full(NPTS,np.nan),np.full(NPTS,np.inf)):
        try:_noise_window_metrics(bad)
        except ValueError as e:assert str(e)=="BAD_NOISE_WINDOW_INPUT"
        else:raise AssertionError("BAD_NOISE_WINDOW_ACCEPTED")
    return "3_POSITIVE_3_NEGATIVE_PASS"


def noise_window_qc(source_dir:Path,baseline:dict):
    from datetime import datetime,timezone
    r=json.loads((source_dir/"source_receipt.json").read_text(encoding="utf-8"))
    origin=datetime.fromisoformat(r["event_utc"].replace("Z","+00:00"))
    start=datetime.fromisoformat(r["common_start_utc"].replace("Z","+00:00"))
    if origin.tzinfo is None or start.tzinfo is None:raise ValueError("NOISE_NAIVE_TIME")
    origin_s=(origin.astimezone(timezone.utc)-start.astimezone(timezone.utc)).total_seconds()
    if baseline.get("event_id")!="ci38457511" or not 20<origin_s<40:
        raise ValueError("NOISE_EVENT_IDENTITY")
    rows=[]
    for c in baseline["channels"]:
        axis=c["channel"]
        q=_noise_window_metrics(load_csv(source_dir/f"CI_CLC_{axis}_accel_mps2.csv"))
        q["channel"]=axis
        t=q["candidate_1s_window_start_trigger_s"]
        q["trigger_relative_to_catalog_origin_s"]=t-origin_s if t is not None else None
        rows.append(q)
    return {"status":"S05_PRE_EVENT_VARIABILITY_CANDIDATE_TRIGGER_NOT_SITE_PASS",
            "SOURCE":baseline["SOURCE"],"OFFICIAL":"SCEDC original SHA-checked by parent process",
            "REF":"Hann periodogram; demeaned short-window RMS; 1s first-difference energy heuristic",
            "STANDARD":"IEC2025/GB/NB licensed clauses and Jiayu site spectrum not checked",
            "RUN":"Native source-level QC, no structural E/WE","FIG":0,
            "TAB":"2 channels x 4 pre-5s + 3 overlapping pre-10s + 5 overlapping shaking-20s",
            "event_origin_from_record_start_s":origin_s,
            "parameters":{"dt_s":DT,"band_hz":[0.1,0.25],"pre10s_resolution_hz":0.1,
                          "pre20s_resolution_hz":0.05,"trigger_rms_window_s":1,
                          "trigger_threshold_ratio":8,"trigger_sustain_s":0.5,
                          "trigger_search_start_s":20},
            "assumptions":["Only 20s pre-origin; 10s windows overlap, 0.1Hz has ONE cycle",
                           "Shaking windows overlap, their range is NOT a confidence interval",
                           "Difference trigger is NOT verified P/S phase onset",
                           "Sensitivity-only CSV, not fully deconvolved; self-noise unverified"],
            "error_budget":"Double precision; 10s 0.1Hz bin spacing; inadequate low-frequency degrees of freedom; no approved acceptance threshold",
            "test":noise_window_self_test(),"channels":rows,
            "HOLD":"Noise stationarity and usable 4-10s band unproven; no Jiayu target spectrum; S05 PARTIAL E/WE=0 0/12"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--sensitivity", action="store_true", help="run original miniSEED response parameter/edge QC")
    p.add_argument("--snr", action="store_true", help="pre-origin chronology and observed 0.1-0.25Hz power QC")
    p.add_argument("--noise-qc", action="store_true", help="pre-event variability and candidate transient trigger")
    p.add_argument("--source-dir", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.self_test:
        print(self_test(), snr_self_test(), noise_window_self_test())
        return
    if not args.source_dir or not args.output:
        p.error("--source-dir and --output required")
    result = process(args.source_dir)
    if args.sensitivity:
        result["parameter_sensitivity"] = response_sensitivity(args.source_dir, result)
    if args.snr:
        result["low_frequency_snr"] = low_frequency_snr(args.source_dir, result)
    if args.noise_qc:
        result["noise_window_qc"] = noise_window_qc(args.source_dir, result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "test": result["test"],
                      "sensitivity": result.get("parameter_sensitivity", {}).get("status"),
                      "rows": [(x["channel"], x["raw_vs_csv_max_abs_m_s2"],
                                [round(s["relative_change_percent"], 6) for s in x["spectra"]])
                               for x in result["channels"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
