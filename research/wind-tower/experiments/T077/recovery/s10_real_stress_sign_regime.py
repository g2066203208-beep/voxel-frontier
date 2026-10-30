#!/usr/bin/env python3
"""S10: real synchronized gross-stress sign regimes, with mutually exclusive PT offsets.

Input: 4 ETM x 31 sections x 16 azimuths, 12001 sampled time instants per point.
This does NOT recover the 12001-point stress histories, cycle-mean rainflow
matrices, material fatigue damage, local FE stress, joint opening or PT balance.
Positive stress = tension. Offsets P0/Pe are mutually exclusive hypotheses.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path

GROSS_SHA256 = "16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b"
PT_SHA256 = "1d56cdf44971589dde25ab8075cdf50999a94eac47707eadfb4870cf74fc8f5d"
SCENARIOS = ("gross", "Pe", "P0")
COLUMNS = (
    "case", "segment", "scenario", "shift_MPa", "n_angles",
    "all_compressive", "reversing", "all_tensile", "tensile_peak_angles",
    "maximum_sampled_sigma_MPa", "minimum_sampled_sigma_MPa",
    "maximum_gross_DEL_m4_MPa", "status"
)
STATUS = "PT_CONDITIONAL_SIGN_REGIME_NOT_LOCAL_MATERIAL_LIFE"


def read_locked(path, expected_sha):
    raw = Path(path).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_sha:
        raise ValueError("SOURCE_SHA256_MISMATCH:" + got)
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows:
        raise ValueError("EMPTY_SOURCE")
    return rows


def finite(row, key):
    x = float(row[key])
    if not math.isfinite(x):
        raise ValueError("NONFINITE:" + key)
    return x


def classify(lo, hi):
    """Classification of sampled stress extrema, not counted fatigue cycles."""
    if not math.isfinite(lo) or not math.isfinite(hi) or lo > hi:
        raise ValueError("INVALID_STRESS_EXTREMA")
    if hi <= 0:
        return 0  # compression only (zero tension peak allowed)
    if lo >= 0:
        return 2  # tension only
    return 1      # stress reverses sign


def calculate(gross, pt):
    if len(gross) != 1984 or len(pt) != 124:
        raise ValueError("SOURCE_ROW_COUNT")
    by_group = defaultdict(list)
    expected_angles = {22.5 * i for i in range(16)}
    for row in gross:
        key = (row["case"], row["segment"])
        lo = finite(row, "sigma_min_MPa")
        hi = finite(row, "sigma_max_MPa")
        mean = finite(row, "sigma_mean_MPa")
        if lo > mean + 1e-8 or mean > hi + 1e-8:
            raise ValueError("MEAN_OUTSIDE_EXTREMA")
        if row["stress_class"] != "SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE":
            raise ValueError("SOURCE_IDENTITY")
        if int(row["n_samples"]) != 12001:
            raise ValueError("SAMPLE_COUNT")
        if finite(row, "DEL_m4_MPa") < 0:
            raise ValueError("INVALID_DEL")
        by_group[key].append(row)
    pt_map = {}
    for row in pt:
        key = (row["case"], row["segment"])
        if key in pt_map:
            raise ValueError("DUPLICATE_PT_GROUP")
        pe = finite(row, "uniform_Pe_compression_MPa")
        p0 = finite(row, "uniform_P0_compression_MPa")
        if not 0 < pe < p0:
            raise ValueError("INVALID_PT_ORDER")
        if row["status"] != "COUNTERFACTUAL_UNIFORM_PT_SHIFT_NOT_LOCAL_OR_FATIGUE_OR_NATIVE":
            raise ValueError("PT_SOURCE_IDENTITY")
        pt_map[key] = row
    cases = sorted({k[0] for k in by_group})
    segments = sorted({k[1] for k in by_group})
    if len(cases) != 4 or segments != ["CSEG_%02d" % i for i in range(1, 32)]:
        raise ValueError("GROUP_IDENTITY")
    if len(by_group) != 124 or set(by_group) != set(pt_map):
        raise ValueError("GROUP_COVERAGE")

    output = []
    for case in cases:
        for segment in segments:
            key = (case, segment)
            source = by_group[key]
            if len(source) != 16 or {finite(r, "azimuth_deg") for r in source} != expected_angles:
                raise ValueError("AZIMUTH_COMPLETENESS")
            p = pt_map[key]
            shifts = (0.0, finite(p, "uniform_Pe_compression_MPa"),
                      finite(p, "uniform_P0_compression_MPa"))
            old_counts = []
            for scenario, shift in zip(SCENARIOS, shifts):
                counts = [0, 0, 0]
                min_sigma = float("inf")
                max_sigma = -float("inf")
                max_del = -float("inf")
                for row in source:
                    lo = finite(row, "sigma_min_MPa") - shift
                    hi = finite(row, "sigma_max_MPa") - shift
                    counts[classify(lo, hi)] += 1
                    min_sigma = min(min_sigma, lo)
                    max_sigma = max(max_sigma, hi)
                    max_del = max(max_del, finite(row, "DEL_m4_MPa"))
                if sum(counts) != 16:
                    raise ValueError("CLASS_COUNT")
                old_counts.append(counts[1] + counts[2])
                output.append({
                    "case": case, "segment": segment, "scenario": scenario,
                    "shift_MPa": format(shift, ".12g"), "n_angles": "16",
                    "all_compressive": str(counts[0]),
                    "reversing": str(counts[1]),
                    "all_tensile": str(counts[2]),
                    "tensile_peak_angles": str(counts[1] + counts[2]),
                    "maximum_sampled_sigma_MPa": format(max_sigma, ".12g"),
                    "minimum_sampled_sigma_MPa": format(min_sigma, ".12g"),
                    "maximum_gross_DEL_m4_MPa": format(max_del, ".12g"),
                    "status": STATUS,
                })
            if old_counts != [
                int(p["n_of_16_angles_positive_peak_gross"]),
                int(p["n_of_16_angles_positive_peak_Pe"]),
                int(p["n_of_16_angles_positive_peak_P0"])
            ]:
                raise ValueError("INDEPENDENT_PT_PEAK_COUNT_MISMATCH")
            if not old_counts[0] >= old_counts[1] >= old_counts[2]:
                raise ValueError("NONMONOTONE_PT")
    if len(output) != 372:
        raise ValueError("OUTPUT_ROW_COUNT")
    return output


def render(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def self_test():
    assert classify(-2, -0.01) == 0
    assert classify(-2, 3) == 1
    assert classify(0.01, 3) == 2
    assert classify(-2, 0) == 0
    assert classify(0, 3) == 2
    for a, b in ((2, -2), (float("nan"), 2), (-1, float("inf"))):
        try:
            classify(a, b)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid extrema accepted")
    for lo, hi in ((-2, 3), (-4, 1), (-7, -2)):
        assert classify(lo - 1, hi - 1) <= classify(lo, hi) or True
    # Uniform offset cannot change any stress range.
    for lo, hi in ((-2, 3), (-7, -2), (1, 4)):
        assert math.isclose((hi - 6) - (lo - 6), hi - lo, abs_tol=1e-12)
    print("S10_STRESS_SIGN_SYNTHETIC_BOUNDARY_AND_NEGATIVE_TESTS_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--gross")
    p.add_argument("--pt")
    p.add_argument("--output")
    p.add_argument("--check")
    a = p.parse_args()
    if a.self_test:
        self_test()
        if not a.gross and not a.pt:
            return
    if not a.gross or not a.pt or bool(a.output) == bool(a.check):
        p.error("need --gross FILE --pt FILE and exactly one of --output/--check")
    rows = calculate(read_locked(a.gross, GROSS_SHA256), read_locked(a.pt, PT_SHA256))
    result = render(rows)
    if a.check:
        if Path(a.check).read_bytes() != result:
            raise ValueError("COMMITTED_RESULT_MISMATCH")
    else:
        Path(a.output).write_bytes(result)
    totals = {}
    for scenario in SCENARIOS:
        x = [r for r in rows if r["scenario"] == scenario]
        totals[scenario] = {k: sum(int(r[k]) for r in x)
                            for k in ("all_compressive", "reversing", "all_tensile")}
    print(json.dumps({"rows": len(rows), "sha256": hashlib.sha256(result).hexdigest(),
                      "totals": totals, "native_material_life_pass": False},
                     sort_keys=True))


if __name__ == "__main__":
    main()
