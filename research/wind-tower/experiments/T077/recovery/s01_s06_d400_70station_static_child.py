#!/usr/bin/env python3
"""D400 70-station OpenFAST *non-production* identity child.

Inputs: SHA-locked recovered historical 70-station tower, 31-segment
FE gross-embedded mass ledger, and 31-segment elastic displaced-section
EA/EI proxy. Output: comparison CSV, deliberately NOT a runnable .dat.

Never use as production: TwGJStff, TwFAIner, TwSSIner, mode shapes,
PT effective tangent stiffness, joint compliance and dynamic V&V are HOLD.
"""
import argparse, csv, hashlib, io, pathlib, re, sys

BASE = pathlib.Path(__file__).resolve().parent
SOURCES = {
 "tower": ("S06_C02R3R2_158M_Tower_RECOVERED_20261026.dat",
           "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983"),
 "sections": ("S01_S06_112M_INTEGRATED_COMPLIANCE_31SEG_20261027.csv", None),
 "mass": ("S01_D400_31SEG_FE_MASS_ALLOCATION_20261027.csv", None),
}
HEIGHT = 158.0
TARGET_MASS = 1971921.4722881948
def load(base, key):
    name, expected = SOURCES[key]
    data = (base / name).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if expected and sha != expected: raise ValueError("INPUT_SHA256_MISMATCH: "+name+" "+sha)
    print("SOURCE", name, sha, file=sys.stderr)
    return data.decode("utf-8-sig")
def tower_rows(raw):
    rows = []
    for line in raw.splitlines():
        tokens = line.split()
        if len(tokens) == 10:
            try: row = [float(t) for t in tokens]
            except ValueError: continue
            rows.append(row)
    if len(rows) != 70: raise ValueError("EXPECTED_70_STATIONS")
    if any(rows[i+1][0] <= rows[i][0] for i in range(69)): raise ValueError("BAD_STATION_ORDER")
    if abs(rows[0][0]) > 1e-10 or abs(rows[-1][0]-1) > 1e-10:
        raise ValueError("BAD_TOWER_HEIGHT")
    return rows
def integrate(rows, field, z0, z1):
    ans=0.
    for a,b in zip(rows,rows[1:]):
        x,y=a[0]*HEIGHT,b[0]*HEIGHT
        if y <= z0 or x >= z1: continue
        lo,hi=max(x,z0),min(y,z1)
        va=a[field]+(b[field]-a[field])*(lo-x)/(y-x)
        vb=a[field]+(b[field]-a[field])*(hi-x)/(y-x)
        ans+=(va+vb)*(hi-lo)/2
    return ans
def generate(base):
    original=tower_rows(load(base,"tower"))
    sections=list(csv.DictReader(io.StringIO(load(base,"sections"))))
    masses=list(csv.DictReader(io.StringIO(load(base,"mass"))))
    if len(sections)!=31 or len(masses)!=31: raise ValueError("EXPECTED_31_SEGMENTS")
    child=[r.copy() for r in original]
    for i,(s,m) in enumerate(zip(sections,masses)):
        if int(s["segment"])!=i+1 or int(m["segment"])!=i+1:
            raise ValueError("SEGMENT_ORDER_MISMATCH")
        z0,z1=float(s["z0_m"]),float(s["z1_m"])
        a,b=original[2*i][0]*HEIGHT,original[2*i+1][0]*HEIGHT
        if abs(z0-a)>1e-5 or abs(z1-b)>1e-5:
            raise ValueError("SEGMENT_HEIGHT_MISMATCH")
        length=b-a
        if length<=0: raise ValueError("BAD_SEGMENT_LENGTH")
        mass=float(m["total_kg"])
        if abs(mass-sum(float(m[k]) for k in
                       ("solid_kg","long_kg","hoop_kg","tie_kg","pt_kg")))>0.01:
            raise ValueError("MASS_COMPONENT_MISMATCH")
        for j in (2*i,2*i+1):
            child[j][1]=mass/length
            child[j][2]=float(s["d400_displaced_EI_Nm2"])
            child[j][3]=float(s["d400_displaced_EI_Nm2"])
            child[j][5]=float(s["d400_displaced_EA_N"])
    target=sum(float(m["total_kg"]) for m in masses)
    if abs(target-TARGET_MASS)>0.01: raise ValueError("FE_MASS_LEDGER_MISMATCH")
    # Account for 2mm inter-segment gaps under OpenFAST linear interpolation.
    scale=target/integrate(child,1,0,112)
    for i in range(62):child[i][1]*=scale
    if abs(integrate(child,1,0,112)-target)>0.02:
        raise ValueError("112M_INTEGRAL_NOT_CLOSED")
    if any(child[i][k]!=original[i][k] for i in range(70)
           for k in (0,4,6,7,8,9)):
        raise ValueError("UNAUTHORIZED_FIELD_CHANGE")
    if any(child[i]!=original[i] for i in range(62,70)):
        raise ValueError("STEEL_STATION_CHANGED")
    fields=["station","z_m","source_mass_kgpm","child_mass_kgpm",
            "source_FA_EI_Nm2","child_FA_EI_Nm2",
            "source_SS_EI_Nm2","child_SS_EI_Nm2",
            "source_EA_N","child_EA_N",
            "source_GJ_UNCHANGED_HOLD_Nm2","source_FAIner_UNCHANGED_HOLD_kgm",
            "source_SSIner_UNCHANGED_HOLD_kgm"]
    out=io.StringIO(newline="")
    writer=csv.writer(out,lineterminator="\n")
    writer.writerow(fields)
    for i,(a,b) in enumerate(zip(original,child),1):
        vals=[i,a[0]*HEIGHT,a[1],b[1],a[2],b[2],a[3],b[3],
              a[5],b[5],a[4],a[6],a[7]]
        writer.writerow([str(vals[0])]+[f"{v:.12e}" for v in vals[1:]])
    stats={
      "status":"NONPRODUCTION_STATIC_CHILD_S01_S06_HOLD",
      "stations":len(child),"concrete_stations":62,"steel_stations":8,
      "source_112_mass_kg":integrate(original,1,0,112),
      "child_112_mass_kg":integrate(child,1,0,112),
      "fe_112_mass_kg":target,
      "source_158_mass_kg":integrate(original,1,0,158),
      "child_158_mass_kg":integrate(child,1,0,158),
      "fe_158_mass_kg":2163015.6403167234,
      "concrete_mass_normalization":scale,
      "unresolved":"GJ, rotary inertia, mode shapes, PT/connection tangent, S01 material/construction, native modal/Flex",
    }
    return out.getvalue(),stats
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=pathlib.Path,default=BASE)
    ap.add_argument("--out",type=pathlib.Path)
    args=ap.parse_args()
    data,stats=generate(args.base)
    if args.out:
        if args.out.exists(): raise FileExistsError("REFUSE_OVERWRITE")
        args.out.write_text(data,encoding="utf-8",newline="")
    else:sys.stdout.write(data)
    print("STATS",stats,"CSV_SHA256",hashlib.sha256(data.encode()).hexdigest(),file=sys.stderr)
if __name__=="__main__":main()
