#!/usr/bin/env python3
"""S01/S06 inverse identity check: historical 158m OpenFAST vs R335 phi25 + PT.
SOURCE-LOCKED STATIC RECONSTRUCTION ONLY. No original generator, no native solver.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

SOURCES = {
    "gross": ("S06_158M_TOWER_GROSS_SECTION_IDENTITY_31SEG_20261026.csv",
              "af3621453a7469d4dc66334e43563f8871c05e09"),
    "counts": ("S01_D400_D500_31SEG_LONGITUDINAL_STEEL_RATIO_20261027.csv",
               "d09a754bbef1926dcafaac2e4f4e4080bbbac2b0"),
    "ea": ("S06_158M_TOWER_MASS_EA_31SEG_20261026.csv",
           "a54521e6679f4ff180b92b9a866f098cf87aaa5e"),
    "rebar": ("S01_D400_VS_FORMAL_158M_OPENFAST_31SEG_20261026.csv",
              "ac6caa2ed12f214f7b7558b9e49e602e5679e777"),
}
FIELDS = ["segment", "z0_m", "z1_m", "bar_count", "As_phi25_m2",
          "Is_phi25_proxy_m4", "EA_openfast_N", "EA_phi25_proxy_N", "EA_error_pct",
          "EI_openfast_Nm2", "EI_phi25_proxy_Nm2", "EI_error_pct",
          "mass_openfast_kgpm", "mass_phi25_PT_proxy_kgpm", "mass_error_pct",
          "mass_phi25_noPT_proxy_kgpm", "mass_noPT_error_pct"]

def load(folder, key):
    name, expected = SOURCES[key]
    raw = (folder / name).read_bytes()
    blob = hashlib.sha1(("blob %d\0" % len(raw)).encode("ascii") + raw).hexdigest()
    if blob != expected:
        raise ValueError("SOURCE_GIT_BLOB_MISMATCH: " + name + ": " + blob)
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(rows) != 31:
        raise ValueError("REQUIRE_31_SEGMENTS: " + name)
    return rows, hashlib.sha256(raw).hexdigest()

def rms(xs):
    return math.sqrt(sum(x*x for x in xs) / len(xs))

def compute(folder):
    inputs = {key: load(folder, key) for key in SOURCES}
    gross, counts, ea, rebar = (inputs[k][0] for k in SOURCES)
    error = {"EA": [], "EI": [], "mass_PT": [], "mass_noPT": [],
             "EA_gross": [], "EI_gross": [], "mass_gross": []}
    totals = {k: 0.0 for k in ("L", "m_OF", "m_PT", "m_noPT", "m_gross",
                               "flex_OF", "flex_PT", "flex_gross")}
    records = []
    for j, (g, c, e, r) in enumerate(zip(gross, counts, ea, rebar), 1):
        if (int(g["segment"]), int(c["segment"].split("_")[-1]),
                int(e["segment"]), int(r["segment"])) != (j, j, j, j):
            raise ValueError("SEGMENT_ALIGNMENT")
        z0, z1 = float(r["z_start_m"]), float(r["z_end_m"])
        L = z1-z0
        if not 0 < L < 4 or not 0 <= z0 < z1 <= 112.001:
            raise ValueError("HEIGHT_ORDER")
        A, I = float(g["gross_area_m2"]), float(g["gross_I_m4"])
        N, d400 = int(c["bar_count"]), float(c["d400_mm"])
        if N <= 0 or d400 <= 0:
            raise ValueError("REBAR_IDENTITY")
        # R335 is the historic equivalent phi25 branch; bar counts are the same.
        As25 = N * math.pi * 0.025**2 / 4
        # D400 positions were re-laid out: scaling Is by area is only a radius proxy.
        Is25 = float(r["d400_rebar_Is_m4"]) * (25.0/d400)**2
        Ec = (37.0 if j <= 2 else 36.5)*1e9
        Es, rho_c, rho_s, A_PT = 200e9, 2400., 7850., 0.04032
        EA_OF, EI_OF = float(e["TwEAStff_N"]), float(r["openfast_ei_Nm2"])
        m_OF = float(e["TMassDen_kgpm"])
        if abs(m_OF-float(r["openfast_tmassden_kgpm"])) > 1e-6:
            raise ValueError("TOWER_MASS_COLUMN_MISMATCH")
        EA25, EI25 = Ec*A+Es*As25, Ec*I+Es*Is25
        m25PT = rho_c*A + rho_s*(As25+A_PT)
        m25 = rho_c*A + rho_s*As25
        pct = lambda x, y: 100*(x/y-1)
        for key, value in (
            ("EA", pct(EA25,EA_OF)), ("EI",pct(EI25,EI_OF)),
            ("mass_PT",pct(m25PT,m_OF)), ("mass_noPT",pct(m25,m_OF)),
            ("EA_gross",pct(Ec*A,EA_OF)), ("EI_gross",pct(Ec*I,EI_OF)),
            ("mass_gross",pct(rho_c*A,m_OF))):
            error[key].append(value)
        w = ((158-z0)**3-(158-z1)**3)/3
        for key, delta in (
            ("L",L),("m_OF",m_OF*L),("m_PT",m25PT*L),("m_noPT",m25*L),
            ("m_gross",rho_c*A*L),("flex_OF",w/EI_OF),
            ("flex_PT",w/EI25),("flex_gross",w/(Ec*I))):
            totals[key] += delta
        records.append([j,z0,z1,N,As25,Is25,EA_OF,EA25,error["EA"][-1],
                        EI_OF,EI25,error["EI"][-1],m_OF,m25PT,
                        error["mass_PT"][-1],m25,error["mass_noPT"][-1]])
    if abs(totals["L"]-111.939) > 1e-4:
        raise ValueError("31SEG_LENGTH_MISMATCH")
    summary = {
        "classification": "STATIC_INVERSE_CONSISTENCY_ONLY_NOT_GENERATOR_PROOF",
        "hypothesis": "OpenFAST historical 158m concrete-section columns are numerically consistent with gross concrete + R335 equivalent phi25 stiffness, and phi25 + 0.04032m2 PT mass.",
        "assumptions": {"Ec_GPa": "37 for segments 1-2; 36.5 for 3-31",
                        "Es_GPa": 200, "rho_concrete_kgm3": 2400,
                        "rho_steel_kgm3": 7850, "PT_total_area_m2": 0.04032,
                        "R335_diameter_mm": 25,
                        "Is_note": "D400 Is scaled by (25/d400)^2, not original R335 radius"},
        "segment_count": 31,
        "error_rms_percent": {k: rms(v) for k,v in error.items()},
        "error_max_abs_percent": {k: max(map(abs,v)) for k,v in error.items()},
        "represented_length_m": totals["L"],
        "mass_OF_kg": totals["m_OF"],
        "mass_phi25_PT_proxy_kg": totals["m_PT"],
        "mass_phi25_noPT_proxy_kg": totals["m_noPT"],
        "mass_PT_proxy_difference_percent": 100*(totals["m_PT"]/totals["m_OF"]-1),
        "PT_mass_if_distributed_kg": 7850*.04032*totals["L"],
        "openfast_concrete_contribution_tip_deflection_1MN_m": totals["flex_OF"]*1e6,
        "phi25_proxy_contribution_tip_deflection_1MN_m": totals["flex_PT"]*1e6,
        "phi25_proxy_tip_compliance_difference_percent":
            100*(totals["flex_PT"]/totals["flex_OF"]-1),
        "source_sha256": {SOURCES[k][0]:inputs[k][1] for k in SOURCES},
        "underlying_tower_sha256": "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983",
        "underlying_d400_inp_sha256": "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a",
        "limitations": "Not a proof of original ElastoDyn generation formulas, not a complete 158m structure or RNA/connection model. No Abaqus/OpenFAST RUN; PT stiffness may be omitted from hypothesized EI; 0.061m gaps and real R335 radii are unrepresented. S01/S06 HOLD."
    }
    return records, summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,default=Path(__file__).resolve().parent)
    p.add_argument("--csv",type=Path)
    p.add_argument("--json",type=Path)
    args=p.parse_args()
    records, summary=compute(args.base)
    if args.csv:
        if args.csv.exists(): raise FileExistsError("REFUSE_OVERWRITE_CSV")
        with args.csv.open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,lineterminator="\n")
            w.writerow(FIELDS)
            for row in records:
                w.writerow([row[0]]+[format(v,".12g") if isinstance(v,float) else v
                                       for v in row[1:]])
    if args.json:
        if args.json.exists(): raise FileExistsError("REFUSE_OVERWRITE_JSON")
        args.json.write_text(json.dumps(summary,ensure_ascii=False,indent=2,
                                        sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True))
    print("STATIC SOURCE-LOCKED INVERSE ONLY; S01/S06 HOLD; NO NATIVE PASS")

if __name__=="__main__":
    main()
