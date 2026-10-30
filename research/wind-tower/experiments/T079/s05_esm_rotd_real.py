#!/usr/bin/env python3
"""ESM IT-2012-0008 NVL processed record: real 16-period RotD00/50/100,
HNE/HNN/vertical 5%-damped PSA. Numerical QC only: NOT design/physics PASS.
NumPy required; time-history Newmark average acceleration, no extra filtering.
"""
import argparse,csv,hashlib,io,json,math
from pathlib import Path
import numpy as np

SRC_SHA="a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34"
REF_SHA="a2e2ea94d81ef1cfff63863148518cf2159bb821161577a67b5c4b7705143bc6"
PERIODS=(.5,.75,1.,1.25,1.5,2.,2.5,3.,3.5,4.,5.,6.,7.,8.,9.,10.)
HEAD=["time_s","HNE_acc_m_s2","HNN_acc_m_s2","HNZ_acc_m_s2"]

def sha(raw):return hashlib.sha256(raw).hexdigest()

def load(raw, strict=True):
    if strict and sha(raw)!=SRC_SHA:raise ValueError("SOURCE_SHA256_MISMATCH")
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig")))
    if next(rd,None)!=HEAD:raise ValueError("SOURCE_COLUMNS")
    rows=[]
    for i,row in enumerate(rd):
        if len(row)!=4:raise ValueError("SOURCE_COLUMN_COUNT")
        try: vals=[float(v) for v in row]
        except ValueError:raise ValueError("SOURCE_NONNUMERIC") from None
        if not all(math.isfinite(v) for v in vals):raise ValueError("SOURCE_NONFINITE")
        if abs(vals[0]-.005*i)>2e-10:raise ValueError("SOURCE_TIME_GRID")
        rows.append(vals)
    if len(rows)<2 or (strict and len(rows)!=32040):raise ValueError("SOURCE_NPTS")
    return np.asarray(rows,dtype=np.float64)

def response_history(acc,T,dt=.005,damping=.05):
    if len(acc)<2 or T<=0 or dt<=0 or not 0<=damping<1:raise ValueError("SDOF_INVALID")
    w=2*math.pi/T;k=w*w;c=2*damping*w
    u=v=0.;q=-float(acc[0]);den=1+.5*dt*c+.25*dt*dt*k
    disp=np.zeros(len(acc))
    for i in range(1,len(acc)):
        up=u+dt*v+.25*dt*dt*q;vp=v+.5*dt*q
        nq=(-float(acc[i])-c*vp-k*up)/den
        u=up+.25*dt*dt*nq;v=vp+.5*dt*nq;q=nq;disp[i]=u
    return disp

def angle_psa(ue,un,T,deg):
    k=(2*math.pi/T)**2
    return np.asarray([k*float(np.max(np.abs(
        ue*math.cos(math.radians(i*deg))+un*math.sin(math.radians(i*deg)))))
        for i in range(round(180/deg))])

def calculate(raw,reference):
    src=load(raw)
    if sha(reference)!=REF_SHA:raise ValueError("REFERENCE_SHA256_MISMATCH")
    refs=list(csv.DictReader(io.StringIO(reference.decode("utf-8-sig"))))
    if len(refs)!=16:raise ValueError("REFERENCE_ROWS")
    out=[]
    for T,ref in zip(PERIODS,refs):
        if abs(float(ref["period_s"])-T)>1e-12:raise ValueError("REFERENCE_PERIOD")
        ue,un,uz=[response_history(src[:,j],T) for j in (1,2,3)]
        k=(2*math.pi/T)**2
        e,n,z=[k*float(np.max(np.abs(u))) for u in (ue,un,uz)]
        for x,name in ((e,"HNE_pseudoSa_m_s2"),(n,"HNN_pseudoSa_m_s2")):
            if not math.isclose(x,float(ref[name]),rel_tol=2e-9,abs_tol=1e-12):
                raise ValueError("COMPONENT_SPECTRUM_MISMATCH")
        one=angle_psa(ue,un,T,1.);half=angle_psa(ue,un,T,.5)
        r00=float(np.min(half));r50=float(np.median(half));r100=float(np.max(half))
        gm=math.sqrt(e*n)
        out.append(dict(period_s=T,HNE_psa_m_s2=e,HNN_psa_m_s2=n,
            HNZ_psa_m_s2_DIAGNOSTIC=z,horizontal_GM_psa_m_s2=gm,
            RotD00_psa_m_s2=r00,RotD50_psa_m_s2=r50,RotD100_psa_m_s2=r100,
            RotD50_over_GM=r50/gm,RotD100_over_RotD50=r100/r50,
            RotD50_1deg_vs_halfdeg_relative=abs(float(np.median(one))-r50)/r50,
            RotD100_1deg_vs_halfdeg_relative=abs(float(np.max(one))-r100)/r100,
            frequency_over_0p04Hz_highpass=1/(.04*T),
            status="PROCESSED_RECORD_ORIENTATION_NUMERICAL_QC_NOT_DESIGN_WAVE"))
    return out

def self_test():
    t=np.arange(4000)*.005;T=1.2
    a=np.sin(2*math.pi*t/.9);b=np.cos(2*math.pi*t/.7)
    u=response_history(a,T);z=np.zeros_like(u)
    x=angle_psa(u,z,T,.5)
    assert abs(float(np.median(x))/float(np.max(x))-2**-.5)<2e-5
    v=response_history(b,T);theta=math.radians(31)
    rotated=response_history(a*math.cos(theta)+b*math.sin(theta),T)
    assert float(np.max(np.abs(rotated-u*math.cos(theta)-v*math.sin(theta))))<1e-10
    template=b"time_s,HNE_acc_m_s2,HNN_acc_m_s2,HNZ_acc_m_s2\n0,0,0,0\n"
    negatives=[("SOURCE_COLUMNS",b"bad\n0,0,0,0\n"),
        ("SOURCE_COLUMN_COUNT",template+b"0.005,0,0\n"),
        ("SOURCE_TIME_GRID",template+b"0.008,1,1,1\n"),
        ("SOURCE_NONFINITE",template+b"0.005,nan,1,1\n")]
    for error,raw in negatives:
        try:load(raw,strict=False)
        except ValueError as exc:assert str(exc)==error,(error,str(exc))
        else:raise AssertionError("INVALID_INPUT_ACCEPTED_"+error)
    print("S05_ROTD_SELFTEST_PASS angle-analytic linear-superposition 4 negative")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--source-csv",type=Path)
    ap.add_argument("--reference-csv",type=Path)
    ap.add_argument("--output-csv",type=Path)
    ap.add_argument("--output-receipt",type=Path)
    a=ap.parse_args()
    if a.self_test:self_test()
    if a.source_csv:
        if not(a.reference_csv and a.output_csv and a.output_receipt):
            ap.error("source/reference/output-csv/output-receipt required")
        rows=calculate(a.source_csv.read_bytes(),a.reference_csv.read_bytes())
        with a.output_csv.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        receipt=dict(status="REAL_ESM_ROTATION_SPECTRUM_NUMERICAL_QC_ONLY",
            event_id="IT-2012-0008",station="IT.NVL",components="HNE HNN HNZ",
            npts=32040,dt_s=.005,damping_ratio=.05,angle_grid_deg=.5,
            angle_range_deg="[0,180)",numpy_version=np.__version__,
            source_csv_sha256=SRC_SHA,reference_dense_csv_sha256=REF_SHA,
            source_processing="ESM MP 0.040Hz highpass; original instrument usability NOT established",
            method="linear Newmark average-acceleration; rotate relative displacement histories before taking peak",
            site_target_spectrum="MISSING",Abaqus_E_WE_RUN=0,S05_PASS=False)
        a.output_receipt.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print("REAL_ESM_ROTD_16_PERIOD_RECOMPUTED",len(rows),"S05_PASS",False)
    elif not a.self_test:ap.error("choose --self-test or real input")
if __name__=="__main__":main()
