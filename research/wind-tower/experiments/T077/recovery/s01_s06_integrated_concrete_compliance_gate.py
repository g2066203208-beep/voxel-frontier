#!/usr/bin/env python3
"""S01/S06 112m concrete-part integrated mass and elastic compliance proxy.
Read-only, source-Git-blob-locked. No Abaqus/OpenFAST run, no PT/contact/steel-tower model.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

FILES = {
    "geometry": ("S06_158M_TOWER_GROSS_SECTION_IDENTITY_31SEG_20261026.csv", "af3621453a7469d4dc66334e43563f8871c05e09"),
    "rebar": ("S01_D400_VS_FORMAL_158M_OPENFAST_31SEG_20261026.csv", "ac6caa2ed12f214f7b7558b9e49e602e5679e777"),
    "ea": ("S06_158M_TOWER_MASS_EA_31SEG_20261026.csv", "a54521e6679f4ff180b92b9a866f098cf87aaa5e"),
}
H = 158.0
FIELDS = ["segment", "z0_m", "z1_m", "length_m", "openfast_mass_kg", "d400_displaced_mass_kg",
          "openfast_EI_Nm2", "d400_displaced_EI_Nm2", "openfast_EA_N",
          "d400_displaced_EA_N", "openfast_lateral_compliance_m_per_N",
          "d400_lateral_compliance_m_per_N"]

def read_locked(folder, key):
    name, expected = FILES[key]
    data = (folder / name).read_bytes()
    blob = hashlib.sha1(("blob %d" % len(data)).encode() + bytes([0]) + data).hexdigest()
    if blob != expected:
        raise ValueError("SOURCE_GIT_BLOB_MISMATCH: " + name + " " + blob)
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig")))), hashlib.sha256(data).hexdigest()

def compute(folder):
    sources = {key: read_locked(folder, key) for key in FILES}
    geometry, rebar, ea = (sources[k][0] for k in ("geometry", "rebar", "ea"))
    if not (len(geometry) == len(rebar) == len(ea) == 31):
        raise ValueError("REQUIRE_31_SEGMENTS")
    totals = {k: 0.0 for k in ("length", "mass_of", "mass_d400", "moment_of",
                               "moment_d400", "flex_of", "flex_d400",
                               "ax_of", "ax_d400", "rot_of", "rot_d400")}
    rows = []
    last_z = 0.0
    for i, (g, r, e) in enumerate(zip(geometry, rebar, ea), 1):
        if (int(g["segment"]), int(r["segment"]), int(e["segment"])) != (i, i, i):
            raise ValueError("SEGMENT_ID_MISMATCH")
        z0, z1 = float(r["z_start_m"]), float(r["z_end_m"])
        if z0 < last_z - 1e-7 or z1 <= z0 or z1 > 112.00001:
            raise ValueError("INVALID_HEIGHT_ORDER")
        last_z = z1
        L = z1 - z0
        A, I = float(g["gross_area_m2"]), float(g["gross_I_m4"])
        As, Is = float(r["d400_rebar_As_m2"]), float(r["d400_rebar_Is_m4"])
        if not (0 < As < A and 0 < Is < I):
            raise ValueError("INVALID_REBAR_GEOMETRY")
        Ec = 37e9 if i <= 2 else 36.5e9
        Es, rhoc, rhos = 200e9, 2400.0, 7850.0
        m_of = float(r["openfast_tmassden_kgpm"])
        m_d = rhoc * (A - As) + rhos * As
        EI_of = float(r["openfast_ei_Nm2"])
        EI_d = Ec * (I - Is) + Es * Is
        EA_of = float(e["TwEAStff_N"])
        EA_d = Ec * (A - As) + Es * As
        if abs(m_of - float(e["TMassDen_kgpm"])) > 1e-6:
            raise ValueError("OPENFAST_MASS_IDENTITY_MISMATCH")
        weight = ((H - z0)**3 - (H - z1)**3) / 3.0
        f_of, f_d = weight / EI_of, weight / EI_d
        totals["length"] += L
        totals["mass_of"] += m_of * L
        totals["mass_d400"] += m_d * L
        totals["moment_of"] += m_of * L * (z0 + z1) / 2
        totals["moment_d400"] += m_d * L * (z0 + z1) / 2
        totals["flex_of"] += f_of
        totals["flex_d400"] += f_d
        totals["ax_of"] += L / EA_of
        totals["ax_d400"] += L / EA_d
        totals["rot_of"] += L / EI_of
        totals["rot_d400"] += L / EI_d
        rows.append([i, z0, z1, L, m_of * L, m_d * L, EI_of, EI_d, EA_of, EA_d, f_of, f_d])
    if abs(totals["length"] - 111.939) > 1e-4:
        raise ValueError("HEIGHT_GAP_UNEXPECTED")
    pct = lambda new, old: 100 * (new / old - 1)
    summary = {
        "evidence_class": "STATIC_ELASTIC_CONCRETE_PART_PROXY_NOT_SOLVER",
        "tower_top_height_m": H,
        "concrete_height_m": 112.0,
        "represented_length_m": totals["length"],
        "omitted_gap_length_m": 112.0 - totals["length"],
        "openfast_concrete_mass_kg": totals["mass_of"],
        "d400_displaced_concrete_mass_kg": totals["mass_d400"],
        "mass_change_pct": pct(totals["mass_d400"], totals["mass_of"]),
        "openfast_concrete_CG_y_m": totals["moment_of"] / totals["mass_of"],
        "d400_concrete_CG_y_m": totals["moment_d400"] / totals["mass_d400"],
        "concrete_CG_shift_m": totals["moment_d400"] / totals["mass_d400"] - totals["moment_of"] / totals["mass_of"],
        "openfast_concrete_contribution_tip_deflection_1MN_m": totals["flex_of"] * 1e6,
        "d400_concrete_contribution_tip_deflection_1MN_m": totals["flex_d400"] * 1e6,
        "tip_compliance_change_pct": pct(totals["flex_d400"], totals["flex_of"]),
        "axial_compliance_change_pct": pct(totals["ax_d400"], totals["ax_of"]),
        "rotation_compliance_change_pct": pct(totals["rot_d400"], totals["rot_of"]),
        "source_sha256": {FILES[k][0]: sources[k][1] for k in FILES},
        "underlying_d400_inp_sha256": "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a",
        "underlying_70station_tower_sha256": "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983",
        "limitations": "No 46m steel tower, RNA, PT, hoops/ties, joints, foundation, geometric/material nonlinearity or native dynamics. Not a total 158m deflection or frequency prediction."
    }
    return rows, summary

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--outdir", type=Path, required=True)
    args = p.parse_args()
    rows, summary = compute(args.base)
    args.outdir.mkdir(parents=True, exist_ok=True)
    csv_path = args.outdir / "S01_S06_112M_INTEGRATED_COMPLIANCE_31SEG_20261027.csv"
    json_path = args.outdir / "S01_S06_112M_INTEGRATED_COMPLIANCE_SUMMARY_20261027.json"
    if csv_path.exists() or json_path.exists():
        raise FileExistsError("REFUSE_OVERWRITE")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator=chr(10))
        w.writerow(FIELDS)
        for row in rows:
            w.writerow([row[0]] + [format(v, ".12g") for v in row[1:]])
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    print("STATIC ONLY; no native solver, no physical/standard PASS")

if __name__ == "__main__":
    main()
