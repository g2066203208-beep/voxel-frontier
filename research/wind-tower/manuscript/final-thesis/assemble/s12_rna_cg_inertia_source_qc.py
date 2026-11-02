#!/usr/bin/env python3
"""S12 non-solver source-only RNA mass, CG and inertia reconstruction.
Reads 155 OpenFAST R2 mass points and the T038 archived intrinsic tensor.
Not a physical inertia measurement, dynamic validation or operating M6.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

JSON_SHA = "cf60ca9d6d2e65f24d9e0037ec8f66bde8010002bc6050e1bccccad70f9db71e"
POINTS_SHA = "dcb26756018f94c99b499ced52002cd0c5d3d51b8371cb83f42af9b2b6600566"

def check_sha(path, expected):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("SHA256 mismatch: %s expected %s got %s" % (path, expected, actual))
    return actual

def compute(source, points):
    frozen = source["frozen_native_operator"]
    if source.get("solver_run") is not False:
        raise ValueError("unexpected source level")
    if len(points) != 155 or any(p[0] <= 0 for p in points):
        raise ValueError("expected 155 positive-mass source points")
    m = sum(p[0] for p in points)
    g = [sum(p[0]*p[k+1] for p in points)/m for k in range(3)]
    J = [[0.0]*3 for _ in range(3)]
    for p in points:
        r = [p[k+1]-g[k] for k in range(3)]
        rr = sum(x*x for x in r)
        for i in range(3):
            for j in range(3):
                J[i][j] += p[0]*((rr if i==j else 0.0)-r[i]*r[j])
    intrinsic = frozen["native_intrinsic_kgm2"]
    for i in range(3):
        for j in range(3):
            J[i][j] += intrinsic[i][j]
    rr = sum(x*x for x in g)
    JT = [[J[i][j]+m*((rr if i==j else 0.0)-g[i]*g[j])
           for j in range(3)] for i in range(3)]
    differences = [abs(m-frozen["mass_kg"])]
    differences += [abs(g[i]-frozen["rG_from_tower_top_m"][i]) for i in range(3)]
    differences += [abs(J[i][j]-frozen["JG_kgm2"][i][j]) for i in range(3) for j in range(3)]
    differences += [abs(JT[i][j]-frozen["JT_kgm2"][i][j]) for i in range(3) for j in range(3)]
    if abs(m-source["mass_chain"]["RNA_kg"]) > 1e-7 or max(differences) > 2e-6:
        raise ValueError("R2 point reconstruction and archived source identity diverge")
    specs = [("mass_kg","kg",m,frozen["mass_kg"])]
    specs += [("CG_"+axis+"_from_tower_top_m","m",g[i],frozen["rG_from_tower_top_m"][i])
              for i,axis in enumerate("xyz")]
    for name,calc,ref in (("JG",J,frozen["JG_kgm2"]),("JT",JT,frozen["JT_kgm2"])):
        for i in range(3):
            for j in range(i,3):
                specs.append((name+"_"+"xyz"[i]+"xyz"[j],"kg*m^2",calc[i][j],ref[i][j]))
    return specs, max(differences)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-json",type=Path,required=True)
    ap.add_argument("--mass-points",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--expected-json-sha256",default=JSON_SHA)
    ap.add_argument("--expected-points-sha256",default=POINTS_SHA)
    args=ap.parse_args()
    check_sha(args.source_json,args.expected_json_sha256)
    check_sha(args.mass_points,args.expected_points_sha256)
    source=json.loads(args.source_json.read_text(encoding="utf-8-sig"))
    with args.mass_points.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        points=[(float(r["mass_kg"]),float(r["x_m"]),float(r["y_m"]),float(r["z_m"])) for r in reader]
    specs,residual=compute(source,points)
    def fmt(v):
        return "0.000000" if abs(v)<5e-7 else "%.6f"%v
    with args.output.open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f,lineterminator="\n")
        writer.writerow(["metric","unit","recomputed","archived_T038","scope"])
        for k,u,a,b in specs:
            writer.writerow([k,u,fmt(a),fmt(b),"R2_frozen_IEC_zero_yaw_not_operating"])
    print("SOURCE-LEVEL PASS: 155 points, %d scalars; max absolute source identity residual %.12g (mixed SI units)"%(len(specs),residual))
    print("NOT physical/dynamic/operating-state PASS")

if __name__=="__main__":
    main()
