#!/usr/bin/env python3
"""S01/S06 source-locked ElastoDyn mass/EA identity test; NOT physical validation.

Abaqus D400 provisional INP SHA256:
22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a
Its concrete section map (independently inspected): CSEG01-02 C70
(E=37 GPa); CSEG03-31 C65 (E=36.5 GPa); rho=2400 kg/m3.
These Abaqus values are a comparison assumption, NOT proof of the
OpenFAST tower generator's material/steel/PT mass ownership.
"""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

TOWER_SHA256 = "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983"
INP_SHA256 = "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"
HEIGHT_M = 158.0
RHO = 2400.0
FIELDS = ("segment", "z0_m", "z1_m", "material_comparison", "E_Pa",
          "TMassDen_kgpm", "TwEAStff_N", "mass_from_EA_if_plain_concrete_kgpm",
          "residual_kgpm", "residual_pct")

def parse_tower(raw):
    lines = raw.decode("utf-8").splitlines()
    numeric = re.compile(r"[+-]?\d+\.\d+e[+-]\d+", re.I)
    rows = []
    for line in lines:
        values = line.split()
        if len(values) == 10 and all(numeric.fullmatch(v) for v in values):
            rows.append(tuple(float(v) for v in values))
    if len(rows) != 70 or abs(rows[0][0]) > 1e-12 or abs(rows[-1][0]-1) > 1e-12:
        raise ValueError("Expected exactly 70 ElastoDyn tower stations, 0..1")
    if any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("Non-increasing station heights")
    if abs(rows[61][0] * HEIGHT_M - 111.999) > 0.002:
        raise ValueError("Unexpected concrete-to-steel interface")
    for i in range(31):
        a, b = rows[2*i], rows[2*i+1]
        if abs(a[1]-b[1]) > 1e-7 or abs(a[5]-b[5]) > 0.01:
            raise ValueError(f"Concrete segment {i+1}: nonconstant mass/EA")
    return rows

def E_for_concrete_station(index):
    if not 0 <= index < 62:
        raise ValueError("Steel station cannot use concrete modulus")
    return 37e9 if index < 4 else 36.5e9

def run(path, outdir):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != TOWER_SHA256:
        raise ValueError(f"Tower SHA256 mismatch: {digest} != {TOWER_SHA256}")
    rows = parse_tower(raw)
    output = []
    for i in range(31):
        a, b = rows[2*i], rows[2*i+1]
        E = E_for_concrete_station(2*i)
        mass_proxy = RHO*a[5]/E
        residual = a[1]-mass_proxy
        output.append(dict(zip(FIELDS, (
            i+1, a[0]*HEIGHT_M, b[0]*HEIGHT_M,
            "C70" if i < 2 else "C65", E, a[1], a[5],
            mass_proxy, residual, 100*residual/a[1]))))
    actual = proxy = 0.0
    # Integrate 0..111.999 m only: no interpolation through the steel interface.
    for i in range(61):
        a, b = rows[i], rows[i+1]
        dz = (b[0]-a[0])*HEIGHT_M
        actual += dz*(a[1]+b[1])/2
        proxy += dz*RHO*(a[5]/E_for_concrete_station(i)
                         + b[5]/E_for_concrete_station(i+1))/2
    residuals = [x["residual_pct"] for x in output]
    summary = {
        "gate": "S01/S06 PARTIAL/HOLD; STATIC SOURCE-CONSISTENCY ONLY",
        "source_tower_sha256": digest, "comparison_inp_sha256": INP_SHA256,
        "station_count": len(rows), "concrete_segment_count": 31,
        "material_assumptions": "C70 E=37GPa segments 1-2; C65 E=36.5GPa segments 3-31; rho=2400kg/m3 from provisional Abaqus INP",
        "integral_extent_m": [0, rows[61][0]*HEIGHT_M],
        "openfast_concrete_tmass_integral_kg": actual,
        "ea_equivalent_plain_concrete_mass_integral_kg": proxy,
        "openfast_minus_ea_proxy_kg": actual-proxy,
        "openfast_minus_ea_proxy_pct": 100*(actual-proxy)/actual,
        "segment_relative_residual_min_pct": min(residuals),
        "segment_relative_residual_max_pct": max(residuals),
        "segment_relative_residual_rms_pct": math.sqrt(sum(x*x for x in residuals)/31),
        "interpretation": "TMassDen and TwEAStff are approximately compatible with the Abaqus plain-concrete rho/E ratio; this DOES NOT identify whether OpenFAST already includes rebar/PT, nor prove geometry/model equivalence.",
        "physical_error_budget": "NEED-ESTIMATE: source generator, actual cross-section, reinforcement/PT mass and stiffness, joints, discretization, native mass/modal checks",
        "native_abaqus": "NOT RUN", "earthquake_runs": 0,
    }
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir/"S06_31SEG_MASS_EA_IDENTITY.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    (outdir/"S06_MASS_EA_IDENTITY_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("tower_dat")
    p.add_argument("--outdir", required=True)
    args = p.parse_args()
    run(args.tower_dat, args.outdir)
