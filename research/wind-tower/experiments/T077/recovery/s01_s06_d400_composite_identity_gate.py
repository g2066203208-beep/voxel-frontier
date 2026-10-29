#!/usr/bin/env python3
"""S01/S06 D400 gross/embedded/displaced section proxies vs 158m OpenFAST.
STATIC INPUT COMPARISON ONLY; no native Abaqus/OpenFAST, no physical/standard PASS.
Underlying D400 INP SHA256: 22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a
Underlying 70-station tower SHA256: f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983
"""
import argparse
import csv
import hashlib
import io
import pathlib
import sys

FILES = {
    "gross": ("S06_158M_TOWER_GROSS_SECTION_IDENTITY_31SEG_20261026.csv", "af3621453a7469d4dc66334e43563f8871c05e09"),
    "rebar": ("S01_D400_VS_FORMAL_158M_OPENFAST_31SEG_20261026.csv", "ac6caa2ed12f214f7b7558b9e49e602e5679e777"),
    "ea": ("S06_158M_TOWER_MASS_EA_31SEG_20261026.csv", "a54521e6679f4ff180b92b9a866f098cf87aaa5e"),
}
FIELDS = ["segment","ec_GPa","openfast_mass_kgpm","openfast_EA_GN","openfast_EI_TNm2","gross_mass_diff_pct","embedded_mass_diff_pct","displaced_mass_diff_pct","gross_EA_diff_pct","embedded_EA_diff_pct","displaced_EA_diff_pct","gross_EI_diff_pct","embedded_EI_diff_pct","displaced_EI_diff_pct"]
def load(base, key):
    name, expected_blob = FILES[key]
    data = (base / name).read_bytes()
    blob = hashlib.sha1(("blob %d\0" % len(data)).encode("ascii") + data).hexdigest()
    if blob != expected_blob:
        raise ValueError("SOURCE_GIT_BLOB_MISMATCH " + name + " " + blob)
    print(name + " sha256=" + hashlib.sha256(data).hexdigest() + " git_blob=" + blob, file=sys.stderr)
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
def run(base):
    gross, rebar, ea = (load(base, k) for k in ("gross", "rebar", "ea"))
    if not (len(gross) == len(rebar) == len(ea) == 31):
        raise ValueError("Expected exactly 31 segments")
    result = []
    for i, (g, r, e) in enumerate(zip(gross, rebar, ea), 1):
        if (int(g["segment"]), int(r["segment"]), int(e["segment"])) != (i, i, i):
            raise ValueError("Segment misalignment")
        Ec, Es, rhoc, rhos = (37e9 if i <= 2 else 36.5e9), 200e9, 2400., 7850.
        A, I = float(g["gross_area_m2"]), float(g["gross_I_m4"])
        As, Is = float(r["d400_rebar_As_m2"]), float(r["d400_rebar_Is_m4"])
        mof, EAof, EIof = float(r["openfast_tmassden_kgpm"]), float(e["TwEAStff_N"]), float(r["openfast_ei_Nm2"])
        if abs(mof-float(e["TMassDen_kgpm"])) > 1e-6 or not (0 < As < A and 0 < Is < I):
            raise ValueError("Source consistency/geometry failure")
        m = [rhoc*A, rhoc*A+rhos*As, rhoc*(A-As)+rhos*As]
        ax = [Ec*A, Ec*A+Es*As, Ec*(A-As)+Es*As]
        bend = [Ec*I, Ec*I+Es*Is, Ec*(I-Is)+Es*Is]
        assert abs((bend[1]-bend[2])-Ec*Is) < 0.1 and abs((ax[1]-ax[2])-Ec*As) < 0.1
        assert abs((m[1]-m[2])-rhoc*As) < 1e-6
        result.append([str(i), f"{Ec/1e9:.1f}", f"{mof:.6f}", f"{EAof/1e9:.6f}", f"{EIof/1e12:.6f}"]
            + [f"{100*(v/mof-1):.6f}" for v in m]
            + [f"{100*(v/EAof-1):.6f}" for v in ax]
            + [f"{100*(v/EIof-1):.6f}" for v in bend])
    return result
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent)
    p.add_argument("--out", type=pathlib.Path)
    args = p.parse_args()
    rows = run(args.base)
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(FIELDS)
    w.writerows(rows)
    result = buf.getvalue()
    if args.out:
        if args.out.exists(): raise FileExistsError("REFUSE_OVERWRITE")
        args.out.write_text(result, encoding="utf-8", newline="")
    else: sys.stdout.write(result)
    print("31/31 STATIC SECTION PROXIES; NO SOLVER; NO STANDARD PASS", file=sys.stderr)
if __name__ == "__main__": main()
