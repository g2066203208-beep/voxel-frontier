#!/usr/bin/env python3
"""Independent full-rate archive oracle check; structural response, NOT external aero force."""
import csv, gzip, hashlib, math, collections, argparse, statistics
p=argparse.ArgumentParser();p.add_argument("gzip_csv");p.add_argument("oracle_csv");a=p.parse_args()
expected="45cc308625ead8411d1565adc66c99e7ee8d0a979e5c3c6c18f23e744ba74dd1"
assert hashlib.sha256(open(a.gzip_csv,"rb").read()).hexdigest()==expected,"source SHA mismatch"
with gzip.open(a.gzip_csv,"rt",newline="") as f:
    cases=collections.defaultdict(list)
    for row in csv.DictReader(f):cases[row["case"]].append(row)
with open(a.oracle_csv,newline="") as f: oracle={r["case"]:r for r in csv.DictReader(f)}
assert len(cases)==18 and set(cases)==set(oracle)
gaps=[]
for case,rows in sorted(cases.items()):
    assert len(rows)==12001
    ts=[float(r["time_s"]) for r in rows]
    assert all(abs(t-(100+0.05*i))<1e-6 for i,t in enumerate(ts))
    def peak(cols):
        v=[math.sqrt(sum(float(r[c])**2 for c in cols)) for r in rows]
        k=max(range(len(v)),key=v.__getitem__)
        ind=math.sqrt(sum(max(abs(float(r[c])) for r in rows)**2 for c in cols))
        return v[k],ind,ts[k]
    m,mi,mt=peak(["TwrBsMxt","TwrBsMyt"])
    f,fi,ft=peak(["TwrBsFxt","TwrBsFyt","TwrBsFzt"])
    for value,key in [(m,"xy_peak_kNm"),(mi,"xy_independent_kNm"),(mt,"xy_peak_time_s"),(f,"xyz_force_peak_kN"),(fi,"xyz_force_independent_kN"),(ft,"xyz_peak_time_s")]:
        assert abs(value-float(oracle[case][key]))<1e-5,(case,key)
    gaps.append(abs(mt-ft))
assert len(gaps)==18
print("PASS 18/18, 216018 full-rate rows; gap median",statistics.median(gaps),"max",max(gaps),"gt60s",sum(g>60 for g in gaps))
