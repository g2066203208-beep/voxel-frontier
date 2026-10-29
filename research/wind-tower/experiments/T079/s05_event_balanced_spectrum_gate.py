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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--us-csv", type=Path)
    p.add_argument("--esm-csv", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    if not (args.us_csv and args.esm_csv and args.output):
        p.error("require --us-csv --esm-csv --output")
    result = calculate(args.us_csv.read_bytes(), args.esm_csv.read_bytes())
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print("S05_REAL_SOURCE_EVENT_BALANCED_DIAGNOSTIC_NOT_DESIGN_PASS",
          result["us_csv_sha256"], result["esm_csv_sha256"])
    for row in result["rows"]:
        print("S05_REAL_PERIOD", row)


if __name__ == "__main__":
    main()
