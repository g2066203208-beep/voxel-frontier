#!/usr/bin/env python3
"""Analytical counterexample, NOT a tower stress or fatigue-life prediction."""
import csv, math, pathlib, hashlib
BASE=(1.,0.,-1.,0.)
def calc(shift,m=4.,kx=1.,ky=1.):
    if type(shift)!=int or shift not in range(4): raise ValueError("shift")
    if not math.isfinite(m) or m<=0 or not all(math.isfinite(v) for v in (kx,ky)): raise ValueError("parameters")
    x=BASE; y=[BASE[(i-shift)%4] for i in range(4)]
    s=[kx*a+ky*b for a,b in zip(x,y)]
    r=max(s)-min(s)
    return [shift,2.,2.,r,r**m,";".join(str(v) for v in s)]
def main():
    rows=[calc(i) for i in range(4)]
    assert [r[3] for r in rows]==[4.,2.,0.,2.]
    assert [r[4] for r in rows]==[256.,16.,0.,16.]
    assert all(r[1:3]==[2.,2.] for r in rows)
    for v in (-1,4,1.5,"2"):
        try:calc(v)
        except ValueError:pass
        else:raise AssertionError("invalid shift accepted")
    for v in (0,-1,float("nan"),float("inf")):
        try:calc(1,m=v)
        except ValueError:pass
        else:raise AssertionError("invalid exponent accepted")
    for v in (float("nan"),float("inf")):
        try:calc(1,ky=v)
        except ValueError:pass
        else:raise AssertionError("invalid gain accepted")
    out=pathlib.Path(__file__).with_name("S10_BIAXIAL_PHASE_NONIDENTIFIABILITY_4ROW.csv")
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["phase_samples","Mx_range","My_range","local_stress_range","normalized_range_power_m","local_series"]);w.writerows(rows)
    print("PASS: four analytical cases; 10 rejection tests; SHA256="+hashlib.sha256(out.read_bytes()).hexdigest())
if __name__=="__main__":main()
