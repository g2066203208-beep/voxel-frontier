#!/usr/bin/env python3
"""S10 exact continuous-azimuth instantaneous GROSS elastic stress envelope.

Source-only postprocessing of 4 ETM x 31 independently archived gage histories.
The maximizing azimuth may CHANGE at each time; the resulting envelope is NOT
a material-point stress history and MUST NOT be rainflow-counted as such.
No PT, local material stress, fatigue life, native Abaqus, or DLC1.2 PASS.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import s06_31gage_batch_coherence_qc as source

CASES=source.CASES
EXPECTED_SHA={
    "manifest":"dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8",
    "gross":"8ae262435e13c0f10326acef7270b9962c943bb5f212171d830fe834f3a364ed",
    "control":"36c0a8a97db36885159fff79cc61daced9c939ab688f98ce1c6b860a89ac91d3",
}
FIELDS=("case","segment","gage_z_m","continuous_max_sigma_MPa",
        "continuous_max_azimuth_deg","continuous_max_time_s",
        "grid16_max_sigma_MPa","grid16_max_azimuth_deg","grid16_tension_gap_MPa",
        "continuous_min_sigma_MPa","continuous_min_azimuth_deg",
        "continuous_min_time_s","grid16_min_sigma_MPa",
        "grid16_min_azimuth_deg","grid16_compression_gap_MPa",
        "max_instantaneous_bending_amplitude_MPa",
        "rigorous_16angle_peak_gap_upper_bound_MPa","n_samples","status")
STATUS="CONDITIONAL_GROSS_ELASTIC_SOURCE_ENVELOPE_NOT_MATERIAL_POINT"
N=12001
TOL=1e-8

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def locked(path, key):
    data=Path(path).read_bytes()
    require(digest(data)==EXPECTED_SHA[key], "INPUT_SHA256_MISMATCH:"+key)
    return data

def annulus(area, inertia):
    require(math.isfinite(area) and math.isfinite(inertia) and area>0 and inertia>0,"BAD_GEOMETRY")
    ro2=(4*inertia/area+area/math.pi)/2
    ri2=(4*inertia/area-area/math.pi)/2
    require(ri2>0 and ro2>ri2,"NON_ANNULAR_SECTION")
    ro=math.sqrt(ro2);ri=math.sqrt(ri2)
    require(abs(math.pi*(ro*ro-ri*ri)-area)/area<1e-10,"AREA_IDENTITY")
    require(abs(math.pi*(ro**4-ri**4)/4-inertia)/inertia<1e-10,"INERTIA_IDENTITY")
    return ro

def envelope_at(force_z,moment_x,moment_y,area,inertia,outer_radius):
    vals=(force_z,moment_x,moment_y,area,inertia,outer_radius)
    require(all(math.isfinite(x) for x in vals) and area>0 and inertia>0 and outer_radius>0,"NONFINITE_OR_INVALID")
    axial=.001*force_z/area
    amp=.001*outer_radius*math.hypot(moment_x,moment_y)/inertia
    theta=math.degrees(math.atan2(moment_x,-moment_y))%360 if amp else 0.0
    return axial+amp,axial-amp,theta,(theta+180)%360,amp

def selftest():
    ro=annulus(math.pi*(25-16),math.pi*(625-256)/4)
    require(abs(ro-5)<1e-10,"ANNULUS_KNOWN_ANSWER")
    hi,lo,th,opp,amp=envelope_at(0,1,0,2,1,1)
    require(abs(hi-.001)<1e-14 and abs(lo+.001)<1e-14 and abs(th-90)<1e-10 and abs(opp-270)<1e-10,"CARDINAL_KNOWN_ANSWER")
    a=math.pi/16
    hi,lo,th,opp,amp=envelope_at(0,math.sin(a),-math.cos(a),2,1,1)
    grid=max(.001*(math.sin(a)*math.sin(math.radians(k*22.5))+math.cos(a)*math.cos(math.radians(k*22.5))) for k in range(16))
    require(abs((hi-grid)-amp*(1-math.cos(a)))<1e-14 and abs(th-11.25)<1e-10,"HALF_STEP_SHARP_BOUND")
    for bad in (float("nan"),float("inf")):
        try: envelope_at(bad,0,0,1,1,1)
        except ValueError: pass
        else: raise AssertionError("NONFINITE_ACCEPTED")
    print("S10_CONTINUOUS_AZIMUTH_SYNTHETIC_SELFTEST_PASS")

def read_gross(path):
    rows=list(csv.DictReader(Path(path).open(encoding="utf-8",newline="")))
    require(len(rows)==31,"GROSS_31")
    out={}
    for r in rows:
        idx=int(r["segment"])
        require(idx not in out and 1<=idx<=31,"GROSS_SEGMENT")
        a=float(r["gross_area_m2"]);i=float(r["gross_I_m4"])
        out[idx]=(a,i,annulus(a,i))
    require(len(out)==31,"GROSS_UNIQUE_31")
    return out

def read_control(path):
    rows=list(csv.DictReader(Path(path).open(encoding="utf-8",newline="")))
    require(len(rows)==124,"CONTROL_124")
    out={}
    for r in rows:
        k=(r["case"],r["segment"])
        require(r["case"] in CASES and k not in out,"CONTROL_IDENTITY")
        out[k]=r
    return out

def fmt(x,places=9):
    return f"{x:.{places}f}"

def run(args):
    for key in EXPECTED_SHA:
        locked(getattr(args,key),key)
    geometry=read_gross(args.gross)
    controls=read_control(args.control)
    records=[];archives=[];max_gap_t=0.;max_gap_c=0.;max_ratio=0.;max_bound_slack=0.
    for case in CASES:
        source.CASE=case
        source.EXPECTED=source.load_case_manifest(args.manifest,case)
        for batch in "ABCD":
            data,heights,meta=source.parse_archive(args.source_dir/f"S06_{case}_{batch}_original.zip",batch)
            archives.append(dict(case=case,**meta))
            for idx,history in sorted(data.items()):
                seg=f"CSEG_{idx:02d}";key=(case,seg)
                require(key in controls,"MISSING_CONTROL")
                control=controls[key]
                require(abs(float(control["gage_z_m"])-heights[idx])<1e-7,"GAGE_Z_IDENTITY")
                a,i,ro=geometry[idx]
                highest=(-math.inf,None);lowest=(math.inf,None);maxamp=0.
                for t,v in enumerate(history):
                    hi,lo,th,opp,amp=envelope_at(v[2],v[3],v[4],a,i,ro)
                    if hi>highest[0]:highest=(hi,(th,t))
                    if lo<lowest[0]:lowest=(lo,(opp,t))
                    if amp>maxamp:maxamp=amp
                gridhi=float(control["max_sigma_tension_MPa"])
                gridlo=float(control["min_sigma_compression_MPa"])
                dt=highest[0]-gridhi;dc=gridlo-lowest[0]
                bound=maxamp*(1-math.cos(math.pi/16))
                require(dt>=-TOL and dc>=-TOL,"GRID16_EXCEEDS_CONTINUOUS")
                require(dt<=bound+TOL and dc<=bound+TOL,"ANGLE_BOUND_VIOLATION")
                max_gap_t=max(max_gap_t,dt);max_gap_c=max(max_gap_c,dc)
                max_ratio=max(max_ratio,dt/bound if bound else 0,dc/bound if bound else 0)
                max_bound_slack=max(max_bound_slack,dt-bound,dc-bound)
                records.append(dict(case=case,segment=seg,gage_z_m=fmt(heights[idx]),
                    continuous_max_sigma_MPa=fmt(highest[0]),
                    continuous_max_azimuth_deg=fmt(highest[1][0],6),
                    continuous_max_time_s=fmt(100+.05*highest[1][1],2),
                    grid16_max_sigma_MPa=fmt(gridhi),
                    grid16_max_azimuth_deg=fmt(float(control["azimuth_at_max_tension_deg"]),6),
                    grid16_tension_gap_MPa=fmt(max(0.,dt)),
                    continuous_min_sigma_MPa=fmt(lowest[0]),
                    continuous_min_azimuth_deg=fmt(lowest[1][0],6),
                    continuous_min_time_s=fmt(100+.05*lowest[1][1],2),
                    grid16_min_sigma_MPa=fmt(gridlo),
                    grid16_min_azimuth_deg=fmt(float(control["azimuth_at_min_compression_deg"]),6),
                    grid16_compression_gap_MPa=fmt(max(0.,dc)),
                    max_instantaneous_bending_amplitude_MPa=fmt(maxamp),
                    rigorous_16angle_peak_gap_upper_bound_MPa=fmt(bound),
                    n_samples=N,status=STATUS))
    require(len(records)==124 and len(archives)==16,"INCOMPLETE_124_16")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n")
        writer.writeheader();writer.writerows(records)
    receipt={
        "status":"SOURCE_NUMERIC_QC_ONLY_NOT_NATIVE_OR_MATERIAL_FATIGUE",
        "source_level":"16 historical Actions ZIP/GZIP derived gage histories, not raw OUTB",
        "SOURCE":{"manifest_sha256":EXPECTED_SHA["manifest"],"gross_sha256":EXPECTED_SHA["gross"],
                  "existing_16angle_control_sha256":EXPECTED_SHA["control"],"archives":archives},
        "REF":"Inherited OpenFAST/T077 nominal section mapping and ASTM rainflow context; no new full-text reading",
        "STANDARD":"No new authorized IEC/GB/NB original clauses read",
        "OFFICIAL":"Historical GitHub Actions archives; no new solver execution",
        "RUN":"Python 3 source-only continuous azimuth extrema, no Abaqus/OpenFAST production",
        "FIG":"NONE","TAB":args.out.name,
        "rows":len(records),"time_points_per_gage":N,
        "max_tension_gap_MPa":max_gap_t,"max_compression_gap_MPa":max_gap_c,
        "max_gap_over_theoretical_bound":max_ratio,
        "max_numerical_bound_slack_MPa":max_bound_slack,
        "csv_sha256":digest(args.out.read_bytes()),
        "assumptions":["Common fixed section frame within each individual batch, not physically verified",
                       "Gross circular annulus; sigma=0.001*(Fz/A+(Ro/I)*(Mx*sin(theta)-My*cos(theta)))",
                       "At each time, optimizing theta is a spatial envelope, NOT a fixed material point"],
        "error_budget":{"archive_sha256":"exact","time_grid_s":"2e-8",
                        "grid16_source_rounding_MPa":"~5e-11",
                        "numeric_tolerance_MPa":TOL,
                        "csv_rounding_MPa":"<=5e-10",
                        "rigorous_bound":"gap<=max_t(Ro/I*hypot(Mx,My)*0.001)*(1-cos(pi/16))"},
        "HOLD":["Dynamic local coordinate transforms and PT/gravity ownership unverified",
                "Continuous-angle extrema cannot be rainflow-counted as one material point",
                "No local material stress, DLC1.2 life, seismic E/WE or native Abaqus PASS"],
        "physical_pass":False,"native_Abaqus_runs":0
    }
    args.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("S10_CONTINUOUS_AZIMUTH_REAL_SOURCE_QC",json.dumps({
        "rows":len(records),"archives":len(archives),"max_tension_gap_MPa":max_gap_t,
        "max_compression_gap_MPa":max_gap_c,"max_gap_over_bound":max_ratio,
        "csv_sha256":receipt["csv_sha256"]},sort_keys=True))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ("source-dir","manifest","gross","control","out","receipt"):
        parser.add_argument("--"+k,type=Path)
    parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args()
    if args.selftest:selftest()
    if args.source_dir:
        require(all(getattr(args,k) for k in ("manifest","gross","control","out","receipt")),"MISSING_INPUT")
        run(args)
    elif not args.selftest:
        parser.error("use --selftest or --source-dir")
