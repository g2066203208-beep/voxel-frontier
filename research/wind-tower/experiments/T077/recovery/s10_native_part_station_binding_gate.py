#!/usr/bin/env python3
"""Source-locked 68-part/31-wind-gage S10 preflight; NOT an ODB or fatigue PASS."""
import argparse
import csv
import hashlib
import io
import math
from collections import Counter, defaultdict
from pathlib import Path
from s10_load_del_control_stability import compute as load_controls

LOAD_SHA = "9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b"
CTRL_BLOB = "27f931b09b1ff9105597946ff00ecbf7d0db985a"
MASS_BLOB = "1ae32a02a565c2d578485c29c819f30de0242933"
CASES = ("U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06")
CHANNELS = ("Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm")
COUNTS = {"concrete":31,"longitudinal_rebar":31,"PT":1,"steel_tower":4,"hoops_and_ties":1}
GROUPS = {
 "concrete":("concrete","HOLD_NATIVE_POINT_AND_PRINCIPAL_STRESS_CRITERION"),
 "longitudinal_rebar":("ordinary_rebar","HOLD_NATIVE_POINT_AND_HRB335_VS_HRB500"),
 "PT":("prestressing_strand","HOLD_CONTINUOUS_PT_36_LONG_ELEMENTS_NO_GAGE_IP"),
 "steel_tower":("structural_steel","HOLD_STEEL_46M_NO_31GAGE_WIND_STATION"),
 "hoops_and_ties":("ordinary_rebar","HOLD_HOOP_TIE_CAGE_NO_31GAGE_POINT")}
HEADER = ("source_part,source_group,material_class,element_type,element_count,"
 "part_centroid_y_m,load_segment,gage_z_min_m,gage_z_max_m,gage_z_span_mm,"
 "gage_minus_centroid_min_m,gage_minus_centroid_max_m,My_m4_case,My_m10_case,"
 "Mx_m4_case,Mx_m10_case,Fz_m4_case,Fz_m10_case,native_instance,native_element_set,"
 "native_element_label,native_integration_point,native_material_id,native_stress_basis,"
 "binding_status").split(",")

def check(ok,msg):
 if not ok: raise ValueError(msg)

def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def parse(raw):
 return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))

def compute(load,control,mass):
 check(hashlib.sha256(load).hexdigest()==LOAD_SHA,"LOAD_SHA256_MISMATCH")
 check(blob(control)==CTRL_BLOB,"CONTROL_GIT_BLOB_MISMATCH")
 check(blob(mass)==MASS_BLOB,"MASS_GIT_BLOB_MISMATCH")
 expected,_=load_controls(load)
 check(expected==control,"CONTROLLER_NOT_REPRODUCIBLE")
 L,C,P=parse(load),parse(control),parse(mass)
 check((len(L),len(C),len(P))==(744,186,68),"SOURCE_COUNT_MISMATCH")
 check(Counter(p["group"] for p in P)==COUNTS,"PART_GROUP_MISMATCH")
 check(len({p["part"] for p in P})==68,"DUPLICATE_PART")
 ctl={(r["segment"],r["channel"]):r for r in C}
 check(len(ctl)==186,"DUPLICATE_CONTROLLER")
 z=defaultdict(dict)
 for r in L:
  key=(r["segment"],r["case"]); ch=r["channel"]
  check(r["case"] in CASES and ch in CHANNELS and ch not in z[key],"BAD_LOAD_KEY")
  z[key][ch]=float(r["gage_z_m"])
 check(len(z)==124,"MISSING_GAGE_CASE")
 for vals in z.values():
  check(set(vals)==set(CHANNELS),"MISSING_GAGE_CHANNEL")
  vv=list(vals.values())
  check(all(math.isfinite(v) for v in vv) and max(vv)-min(vv)<=1e-9,"MIXED_GAGE_Z_WITHIN_CASE")
 out=[]; spans=[]; offsets=[]
 for p in P:
  group=p["group"]
  check(int(p["element_count"])>0 and math.isfinite(float(p["centroid_y_m"])),"BAD_PART")
  seg=p["part"] if group=="concrete" else ("CSEG_"+p["part"].split("_")[1] if group=="longitudinal_rebar" else "")
  extra=[""]*11
  if seg:
   check(seg in {f"CSEG_{i:02d}" for i in range(1,32)},"BAD_PART_SEGMENT")
   zz=[next(iter(z[(seg,case)].values())) for case in CASES]
   lo,hi=min(zz),max(zz); mid=float(p["centroid_y_m"])
   check(0<lo<=hi<112,"GAGE_HEIGHT_OUT_OF_RANGE")
   spans.append((hi-lo)*1000);offsets.extend((lo-mid,hi-mid))
   def pick(ch):
    r=ctl.get((seg,ch))
    check(r is not None and r["m4_case"] in CASES and r["m10_case"] in CASES,"MISSING_CONTROLLER")
    return r["m4_case"],r["m10_case"]
   extra=[f"{lo:.9f}",f"{hi:.9f}",f"{(hi-lo)*1000:.6f}",
          f"{lo-mid:.9f}",f"{hi-mid:.9f}",*pick("My_kNm"),*pick("Mx_kNm"),*pick("Fz_kN")]
  out.append([p["part"],group,GROUPS[group][0],p["element_type"],p["element_count"],
              p["centroid_y_m"],seg,*extra,"","","","","","",GROUPS[group][1]])
 check(len(out)==68 and len(spans)==62,"OUTPUT_COVERAGE_MISMATCH")
 f=io.StringIO(newline="");w=csv.writer(f,lineterminator="\n")
 w.writerow(HEADER);w.writerows(out)
 return f.getvalue().encode(),{"rows":68,"mapped_to_wind_gage_parts":62,
  "unique_wind_gages":31,"max_gage_case_z_span_mm":max(spans),
  "max_abs_gage_minus_part_centroid_m":max(map(abs,offsets)),
  "native_element_IP_bindings":0,"native_abaqus_runs":0}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 d=Path(__file__).resolve().parent
 ap.add_argument("--load",type=Path,default=d/"S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv")
 ap.add_argument("--control",type=Path,default=d/"S10_ETM_LOAD_DEL_CONTROL_186_20261028.csv")
 ap.add_argument("--mass",type=Path,default=d/"S01_T057_ORIGINAL_68PART_STATIC_MASS_20261027.csv")
 ap.add_argument("--out",type=Path,default=d/"S10_68PART_NATIVE_STRESS_BINDING_PREFLIGHT_20261028.csv")
 ap.add_argument("--self-test",action="store_true")
 args=ap.parse_args()
 source=[p.read_bytes() for p in (args.load,args.control,args.mass)]
 result,stats=compute(*source)
 committed=args.out.read_bytes()
 check(committed==result,"COMMITTED_OUTPUT_NOT_REPRODUCIBLE")
 if args.self_test:
  for i in range(3):
   bad=bytearray(source[i]);bad[-3]^=1
   modified=source[:];modified[i]=bytes(bad)
   try:compute(*modified)
   except ValueError:pass
   else:raise AssertionError(f"NEGATIVE_MUTATION_ACCEPTED_{i}")
  check(all(not r["native_instance"] and not r["native_element_label"] and
            not r["native_integration_point"] for r in parse(result)),
        "FABRICATED_NATIVE_ID")
 for key,val in stats.items():print(f"{key}={val}")
 for key,raw in zip(("load","control","mass","output"),source+[result]):
  print(f"{key}_sha256={hashlib.sha256(raw).hexdigest()}")
 print("S10 REAL SOURCE QC ONLY; NO ODB; NO MATERIAL FATIGUE LIFE; PHYSICS HOLD")

if __name__=="__main__":main()
