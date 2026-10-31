#!/usr/bin/env python3
"""S10 original 18 NTM: synchronized Fz/Mx/My -> gross annular stress, 10 near-base
stations x 16 local azimuths x six seeds x three wind speeds. SOURCE-ONLY screening.
NO Abaqus, PT equilibrium, material fatigue, IEC DLC1.2 or full-height inference.
"""
import argparse
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import zipfile

from s06_historical_outb_source_gate import outb_header
from s06_ntm_18case_original_outb_gate import CASES, entries, unpack_columns, rainflow, sha

ANGLES = tuple(22.5*i for i in range(16))
NREF = 600.0
STATIONS = ("BASE",) + tuple(f"G{i:02d}" for i in range(1, 10))
FIELDS = ("case","wind_bin","seed","station","z_m","local_azimuth_deg",
          "mean_MPa","min_MPa","max_MPa","peak_time_s","peak_to_peak_MPa",
          "DEL_m4_MPa","DEL_m10_MPa","rainflow_equivalent_cycles",
          "quantization_sample_bound_MPa","source_outb_sha256","stress_class")
SUMMARY = ("wind_bin","station","z_m","controlling_local_azimuth_deg",
           "six_seed_power_DEL_m4_MPa","six_seed_power_DEL_m10_MPa",
           "six_seed_arithmetic_mean_DEL_m4_MPa","six_seed_sample_CV_m4_pct",
           "worst_3of6_abs_shift_pct","worst_3of6_seed_ids","source_csv_sha256")
CLASS = "ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE"
ED_SHA = "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65"
FST_SHA = "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605"
ORACLE_SHA = "95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f"

def csv_bytes(rows, columns):
    b=io.StringIO(newline="")
    w=csv.DictWriter(b, fieldnames=columns, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k:format(r[k], ".12g") if isinstance(r[k],float) else r[k] for k in columns})
    return b.getvalue().encode("utf-8")

def finite(x):
    y=float(x)
    if not math.isfinite(y):
        raise ValueError("NONFINITE")
    return y

def load_geom(path, gage_receipt):
    rows=list(csv.DictReader(path.open(encoding="utf-8-sig",newline="")))
    if len(rows)!=31 or [r["segment"] for r in rows]!=[f"CSEG_{i:02d}" for i in range(1,32)]:
        raise ValueError("NOT_31SEG_GEOMETRY")
    first=rows[0]
    z0,z1=finite(first["y0_m"]),finite(first["y1_m"])
    radii=tuple(finite(first[k]) for k in ("ri0_m","ro0_m","ri1_m","ro1_m"))
    if not (z0==0 and z1>2.75 and 0<radii[0]<radii[1] and 0<radii[2]<radii[3]):
        raise ValueError("CSEG01_GEOMETRY_INVALID")
    r=json.loads(gage_receipt.read_text(encoding="utf-8"))
    if r["SOURCE"]["elastodyn_sha256"]!=ED_SHA or r["SOURCE"]["fst_sha256"]!=FST_SHA:
        raise ValueError("GAGE_RECEIPT_ED_IDENTITY")
    if r["TAB"]["TwrGagNd"]!=[1,3,5,7,9,13,15,17,20]:
        raise ValueError("GAGE_NODE_IDENTITY")
    g={"BASE":0.0}
    for i,entry in enumerate(r["TAB"]["rows"],1):
        if entry["gage"]!=i or abs(finite(entry["observed_TPzi_m"])-finite(entry["predicted_midnode_z_m"]))>1e-5:
            raise ValueError("GAGE_HEIGHT_SOURCE_IDENTITY")
        g[f"G{i:02d}"]=finite(entry["predicted_midnode_z_m"])
    if len(g)!=10 or max(g.values())>=z1:
        raise ValueError("NEAR_BASE_STATION_RANGE")
    result={}
    for station,z in g.items():
        t=(z-z0)/(z1-z0)
        ri=radii[0]+t*(radii[2]-radii[0])
        ro=radii[1]+t*(radii[3]-radii[1])
        area=math.pi*(ro*ro-ri*ri)
        inertia=math.pi*(ro**4-ri**4)/4
        if not 0<ri<ro or not area>0 or not inertia>0:
            raise ValueError("INVALID_ANNULAR_SECTION")
        result[station]=(z,area,inertia,ro)
    return result

def load_oracle(path):
    raw=path.read_bytes()
    if sha(raw)!=ORACLE_SHA:
        raise ValueError("LOAD_ORACLE_SHA_MISMATCH")
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    if len(rows)!=1080:
        raise ValueError("ORACLE_NOT_1080")
    out={}
    for r in rows:
        key=(r["case"],r["channel"])
        if key in out:
            raise ValueError("ORACLE_DUPLICATE")
        out[key]=(finite(r["DEL_m4_Nref600"]),finite(r["DEL_m10_Nref600"]),
                  r["outb_sha256"])
    return out

def channel_triplet(station):
    if station=="BASE":
        return ("TwrBsFzt","TwrBsMxt","TwrBsMyt")
    n=int(station[1:])
    return (f"TwHt{n}FLzt",f"TwHt{n}MLxt",f"TwHt{n}MLyt")

def gross_stress(fz,mx,my,area,inertia,radius,angle):
    if len(fz)!=len(mx) or len(fz)!=len(my) or not fz:
        raise ValueError("MISMATCHED_SYNCHRONOUS_SERIES")
    t=math.radians(angle)
    a=.001/area
    b=.001*radius/inertia*math.sin(t)
    c=-.001*radius/inertia*math.cos(t)
    out=[a*x+b*y+c*z for x,y,z in zip(fz,mx,my)]
    if not all(math.isfinite(x) for x in out):
        raise ValueError("NONFINITE_GROSS_STRESS")
    return out,(abs(a),abs(b),abs(c))

def del_pair(x):
    cyc=rainflow(x)
    return ((math.fsum(n*r**4 for r,n in cyc)/NREF)**.25,
            (math.fsum(n*r**10 for r,n in cyc)/NREF)**.1,
            math.fsum(n for _,n in cyc))

def powermean(xs,m):
    if len(xs)!=6 or not all(math.isfinite(x) and x>=0 for x in xs):
        raise ValueError("SIX_SEED_REQUIRED")
    return (math.fsum(x**m for x in xs)/6)**(1/m)

def self_test():
    assert rainflow([0,1,0])==[(1,.5),(1,.5)]
    a,b,c=[0,100,0],[0,0,0],[0,0,0]
    x,k=gross_stress(a,b,c,2,3,4,0)
    assert x==[0,.05,0] and k[0]==.0005
    y,_=gross_stress([0,0],[0,0],[100,100],2,3,4,0)
    assert math.isclose(y[0],-.001*4*100/3,rel_tol=1e-13)
    assert math.isclose(del_pair([0,1,0])[0],600**(-.25),rel_tol=1e-13)
    assert math.isclose(powermean([1]*6,4),1,rel_tol=1e-14)
    for bad in [([0],[0,1],[0]),([0,float("nan")],[0,0],[0,0])]:
        try:gross_stress(*bad,2,3,4,0)
        except ValueError:pass
        else:raise AssertionError("BAD_INPUT_ACCEPTED")
    try:powermean([1]*5,4)
    except ValueError:pass
    else:raise AssertionError("BAD_SEED_COUNT_ACCEPTED")
    print("S10_NTM_GROSS_KNOWN_ANSWER_AND_NEGATIVE_TESTS_PASS")

def run(a):
    src,manifest_sha=entries(a.manifest)
    geom=load_geom(a.geometry,a.gage_receipt)
    oracle=load_oracle(a.oracle)
    ids=list(csv.DictReader(a.identity.open(encoding="utf-8",newline="")))
    identity={r["case"]:r for r in ids}
    if set(identity)!=set(CASES) or any(r["elastodyn_sha256"]!=ED_SHA or r["fst_sha256"]!=FST_SHA for r in ids):
        raise ValueError("NTM_FST_ED_IDENTITY_NOT_COMMON")
    rows=[]; checked=0; max_oracle_err=0.0; sources=[]
    for case in CASES:
        e=src[case]
        zpath=a.zip_dir/Path(e["archive"]).name
        zbytes=zpath.read_bytes()
        if sha(zbytes)!=e["archive_sha256"] if "archive_sha256" in e else False:
            raise ValueError("ARCHIVE_SHA_MISMATCH")
        with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
            raw=z.read(e["relative_path"])
        if len(raw)!=int(e["bytes"]) or sha(raw)!=e["sha256"] or sha(raw)!=identity[case]["outb_sha256"]:
            raise ValueError("NTM_ORIGINAL_OUTB_SHA_MISMATCH:"+case)
        h=outb_header(raw)
        names,units=h.pop("channel_names"),h.pop("channel_units")
        scales,offsets=h.pop("column_scales"),h.pop("column_offsets")
        all_ch={name:(unit,v,q) for name,unit,v,q in unpack_columns(raw,h,names,units,scales,offsets)}
        for station in STATIONS:
            z,area,inertia,radius=geom[station]
            ch=channel_triplet(station)
            vals=[]
            for j,name in enumerate(ch):
                if name not in all_ch or (case,name) not in oracle:
                    raise ValueError("CHANNEL_OR_ORACLE_MISSING:"+name)
                unit,series,q=all_ch[name]
                want="(kN)" if j==0 else "(kN-m)"
                if unit.replace(" ","")!=want:
                    raise ValueError("UNEXPECTED_OPENFAST_UNIT:"+name+":"+unit)
                d4,d10,_=del_pair(series)
                o4,o10,osrc=oracle[case,name]
                if osrc!=sha(raw) or not math.isclose(d4,o4,rel_tol=5e-10,abs_tol=5e-8) or not math.isclose(d10,o10,rel_tol=5e-10,abs_tol=5e-8):
                    raise ValueError("INDEPENDENT_LOAD_DEL_ORACLE_MISMATCH:"+case+":"+name)
                max_oracle_err=max(max_oracle_err,abs(d4-o4),abs(d10-o10))
                checked+=1
                vals.append((series,q))
            for angle in ANGLES:
                stress,k=gross_stress(vals[0][0],vals[1][0],vals[2][0],area,inertia,radius,angle)
                d4,d10,cyc=del_pair(stress)
                peak=max(range(len(stress)),key=stress.__getitem__)
                bound=math.fsum(k[j]*vals[j][1] for j in range(3))
                rows.append(dict(case=case,wind_bin=case.rsplit("_S",1)[0],
                    seed=int(case.rsplit("_S",1)[1]),station=station,z_m=z,
                    local_azimuth_deg=angle,mean_MPa=math.fsum(stress)/len(stress),
                    min_MPa=min(stress),max_MPa=stress[peak],peak_time_s=100+.05*peak,
                    peak_to_peak_MPa=max(stress)-min(stress),DEL_m4_MPa=d4,
                    DEL_m10_MPa=d10,rainflow_equivalent_cycles=cyc,
                    quantization_sample_bound_MPa=bound,source_outb_sha256=sha(raw),
                    stress_class=CLASS))
        sources.append(dict(case=case,archive=zpath.name,archive_sha256=sha(zbytes),
                            outb_sha256=sha(raw),native_samples=h["num_samples"]))
        print("S10_REAL_NTM_ORIGINAL_OUTB_GROSS_PASS",case,sha(raw),flush=True)
    if checked!=540 or len(rows)!=2880 or len(sources)!=18:
        raise ValueError("INCOMPLETE_REAL_SOURCE_COVERAGE")
    by={}
    for r in rows:
        key=(r["wind_bin"],r["station"],r["local_azimuth_deg"])
        by.setdefault(key,[]).append(r)
    summ=[]
    for wind in ("U09p343881_NTM","U11p4_NTM","U19p202140_NTM"):
        for station in STATIONS:
            candidates=[]
            for angle in ANGLES:
                rr=sorted(by[(wind,station,angle)],key=lambda x:x["seed"])
                if [x["seed"] for x in rr]!=list(range(1,7)):
                    raise ValueError("SIX_SEED_MISSING")
                d4=[x["DEL_m4_MPa"] for x in rr]
                d10=[x["DEL_m10_MPa"] for x in rr]
                candidates.append((powermean(d4,4),angle,powermean(d10,10),d4))
            best=max(candidates,key=lambda x:x[0])
            mean4,angle,mean10,d4=best
            subset=[(abs((math.fsum(d4[i]**4 for i in inds)/3)**.25/mean4-1)*100,
                     "-".join(str(i+1) for i in inds)) for inds in itertools.combinations(range(6),3)]
            worst=max(subset)
            arith=math.fsum(d4)/6
            cv=(math.fsum((x-arith)**2 for x in d4)/5)**.5/arith*100 if arith else 0.0
            summ.append(dict(wind_bin=wind,station=station,z_m=geom[station][0],
                controlling_local_azimuth_deg=angle,six_seed_power_DEL_m4_MPa=mean4,
                six_seed_power_DEL_m10_MPa=mean10,
                six_seed_arithmetic_mean_DEL_m4_MPa=arith,
                six_seed_sample_CV_m4_pct=cv,
                worst_3of6_abs_shift_pct=worst[0],
                worst_3of6_seed_ids=worst[1],source_csv_sha256=ORACLE_SHA))
    if len(summ)!=30:
        raise ValueError("SUMMARY_NOT_30")
    full=csv_bytes(rows,FIELDS)
    short=csv_bytes(summ,SUMMARY)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(full)
    a.summary.write_bytes(short)
    receipt=dict(
        status="REAL_18_NTM_10_NEAR_BASE_STATION_16_AZ_SYNCHRONOUS_GROSS_STRESS_NUMERIC_ONLY",
        source_reading_level="18 original OUTB bytes SHA-checked, 12001 simultaneous samples per case; common FST/ED SHA via identity manifest; nine source gage heights from original ETM matched common ED",
        original_outb_count=18,source_records=sources,source_case_count=18,
        source_samples_per_case=12001,source_station_count=10,source_azimuth_count=16,
        output_rows=2880,summary_rows=30,oracle_load_DEL_checked=checked,
        oracle_max_abs_DEL_error=max_oracle_err,
        source_manifest_sha256=manifest_sha,oracle_sha256=sha(a.oracle.read_bytes()),
        geometry_sha256=sha(a.geometry.read_bytes()),gage_receipt_sha256=sha(a.gage_receipt.read_bytes()),
        identity_sha256=sha(a.identity.read_bytes()),script_sha256=sha(Path(__file__).read_bytes()),
        full_sha256=sha(full),summary_sha256=sha(short),
        assumptions={"section":"CSEG01 linear outer/inner radius interpolation at true original ED gage z; base z=0",
            "stress_MPa":"0.001*(Fz_kN/A_m2 + R_m/I_m4*(Mx_kNm*sin(theta)-My_kNm*cos(theta)))",
            "reference_cycles":600,"diagnostic_exponents":[4,10],
            "wind_bins":"3 original NTM wind-speed samples, NOT 20-year IEC DLC1.2",
            "azimuth":"local gage frame candidate, not globally certified structural azimuth",
            "six_seed":"power-mean DEL for identical fixed azimuth; exact 20 three-seed subsets"},
        numerical_error_budget="each sample gross stress absolute quantization bound recorded per row using original packed channel half steps; output CSV 12 significant digits; oracle load DEL agreement 5e-10 relative and 5e-8 absolute; rainflow cycle rearrangement/DEL uncertainty NOT bounded by sample amplitude bound",
        SOURCE="18 original SHA-verified NTM OUTB, original source manifest, source gage height receipt and CSEG01 geometry",
        REF="T077 S10 4 ETM x31 gross stress method; T062 original load rainflow",
        STANDARD="IEC/GB/NB authorized DLC1.2/material fatigue clauses NOT checked",
        OFFICIAL="OpenFAST v3.5.3 native OUTB data and common source ED identity, not design certification",
        RUN="source postprocessing Python only, no new OpenFAST/Abaqus solve",
        FIG="none: full source CSV can support a source-only near-base seed dispersion plot",
        TAB="2880 stress/angle/case/station rows and 30 six-seed control rows",
        native_abaqus_runs=0,physical_pass=False,material_fatigue_life=None,
        HOLD="original nine gages occupy 0.07-2.75m, not full 31-segment coverage; frame/RP and force ownership not independently certified; no Pe/contact/local material stresses, site wind probabilities, DLC1.2 or lifetime Miner")
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print("S10_REAL_NTM_2880_GROSS_AND_30_SEED_ROWS_PASS",sha(full),sha(short))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("manifest","zip-dir","oracle","identity","gage-receipt","geometry","out","summary","receipt"):
        p.add_argument("--"+name,type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test()
    else:
        if not all((a.manifest,a.zip_dir,a.oracle,a.identity,a.gage_receipt,a.geometry,a.out,a.summary,a.receipt)):
            p.error("all source and output paths required")
        run(a)
