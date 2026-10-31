#!/usr/bin/env python3
"""S07: real original OpenFAST v3.5.3 ETM OUTB, 12001x9 synchronized FL/ML/TP/RP.
Only a *candidate* small-rotation/point-transport algebraic QC. The TwHt FL/ML
are INTERNAL section resultants (gravity/inertia included), NOT Abaqus wind loads.
RP -> local frame sign/order is not independently validated. No solver is run.
Python 3.11 stdlib; preserve source bytes, emit only a small JSON receipt.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

from s06_historical_outb_source_gate import outb_header

CASE = "U09p343881_ETM_S01"
ARCHIVE_SHA = "c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0"
OUTB_SHA = "0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c"
MEMBER = "CASES/" + CASE + "/DTU_10MW_RWT.outb"
SUFFIX = ("FLxt","FLyt","FLzt","MLxt","MLyt","MLzt",
          "TPxi","TPyi","TPzi","RPxi","RPyi","RPzi")
UNITS = ("(kN)",)*3 + ("(kN-m)",)*3 + ("(m)",)*3 + ("(deg)",)*3
TIMES = (0,6000,12000)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def must(cond, msg):
    if not cond:
        raise ValueError(msg)

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def mv(R,v):
    return tuple(sum(R[i][j]*v[j] for j in range(3)) for i in range(3))

def trans(R):
    return tuple(tuple(R[j][i] for j in range(3)) for i in range(3))

def norm(v):
    return math.sqrt(sum(x*x for x in v))

def smallrot(theta):
    """Literal candidate SmllRotTrans353 algebra; NOT validated RP->TowerLn2Mesh."""
    must(len(theta)==3 and all(math.isfinite(x) and abs(x)<=.4 for x in theta),
         "RP_SMALL_ANGLE_SOURCE_HOLD")
    a,b,c=theta
    s=a*a+b*b+c*c
    if s==0:
        return ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
    root=math.sqrt(1+s)
    den=s*root
    ab=a*b*(root-1);ac=a*c*(root-1);bc=b*c*(root-1)
    R=(
      ((a*a*root+b*b+c*c)/den,(c*s+ab)/den,(-b*s+ac)/den),
      ((-c*s+ab)/den,(a*a+b*b*root+c*c)/den,(a*s+bc)/den),
      ((b*s+ac)/den,(-a*s+bc)/den,(a*a+b*b+c*c*root)/den))
    must(max(abs(sum(R[i][k]*R[j][k] for k in range(3))-(1 if i==j else 0))
             for i in range(3) for j in range(3))<2e-10,"ROTATION_NOT_ORTHOGONAL")
    return R

def decode(raw,h,channel,k):
    j=h["channel_names"].index(channel)-1
    s=h["column_scales"][j];o=h["column_offsets"][j]
    must(math.isfinite(s) and s!=0 and math.isfinite(o),"BAD_PACKED_SCALE")
    q=struct.unpack_from("<h",raw,h["data_offset_bytes"]+
                         2*(k*h["num_output_channels"]+j))[0]
    v=(q-o)/s
    must(math.isfinite(v),"NONFINITE_NATIVE_SAMPLE")
    return v,.5/abs(s)


def kinematic_chord(stations):
    """Compare measured TP chord with integral of RP-implied tangent; NOT an independent frame oracle.
    stations: ordered (TP[m], RP[deg], TP_halfLSB[m], RP_halfLSB[deg]).
    Both R^T e_z and R e_z are compared, with dz measured from native TPzi.
    """
    must(len(stations)>=2, "KINEMATIC_NEEDS_TWO_STATIONS")
    obs=tuple(stations[-1][0][j]-stations[0][0][j] for j in (0,1))
    pred={"transpose":[0.,0.],"direct":[0.,0.]}
    bound=[stations[0][2][j]+stations[-1][2][j] for j in (0,1)]
    for left,right in zip(stations[:-1],stations[1:]):
        p0,r0,pe0,re0=left
        p1,r1,pe1,re1=right
        dz=p1[2]-p0[2]
        must(math.isfinite(dz) and 0<dz<158., "KINEMATIC_NONMONOTONIC_Z")
        R0=smallrot(tuple(math.radians(x) for x in r0))
        R1=smallrot(tuple(math.radians(x) for x in r1))
        maxslope=[0.,0.]
        for name in pred:
            A0=trans(R0) if name=="transpose" else R0
            A1=trans(R1) if name=="transpose" else R1
            t0=mv(A0,(0.,0.,1.))
            t1=mv(A1,(0.,0.,1.))
            must(t0[2]>.9 and t1[2]>.9,"KINEMATIC_INVALID_TANGENT")
            for j in (0,1):
                s0=t0[j]/t0[2];s1=t1[j]/t1[2]
                pred[name][j]+=dz*.5*(s0+s1)
                maxslope[j]=max(maxslope[j],abs(s0),abs(s1))
        # Conservative packed-data propagation only; excludes beam shear,
        # finite station spacing, RP-to-frame definition and model-form errors.
        rp_rad=max(*(abs(x) for x in re0+re1))*math.pi/180.
        dz_lsb=pe0[2]+pe1[2]
        for j in (0,1):
            bound[j]+=dz*4*rp_rad+dz_lsb*maxslope[j]
    residual={name:tuple(obs[j]-pred[name][j] for j in (0,1)) for name in pred}
    return {"observed_m":obs,"predicted_m":pred,"residual_m":residual,
            "packed_error_bound_m":tuple(bound)}

def kinematic_history(raw,h):
    """Use every native synchronous 9-station TP/RP sample; no new solver."""
    n=h["num_samples"]
    squared={"transpose":0.,"direct":0.}
    maxima={"transpose":0.,"direct":0.}
    max_packed=0.
    preference={"transpose":0,"direct":0,"tie_within_packed":0}
    examples=[]
    for k in range(n):
        stations=[]
        for g in range(1,10):
            tp=[decode(raw,h,f"TwHt{g}TP{a}",k) for a in ("xi","yi","zi")]
            rp=[decode(raw,h,f"TwHt{g}RP{a}",k) for a in ("xi","yi","zi")]
            stations.append((tuple(v for v,_ in tp),tuple(v for v,_ in rp),
                             tuple(e for _,e in tp),tuple(e for _,e in rp)))
        c=kinematic_chord(stations)
        distances={name:norm(c["residual_m"][name]) for name in squared}
        for name in squared:
            squared[name]+=distances[name]**2
            maxima[name]=max(maxima[name],distances[name])
        eps=norm(c["packed_error_bound_m"])
        max_packed=max(max_packed,eps)
        if abs(distances["transpose"]-distances["direct"])<=eps:
            preference["tie_within_packed"]+=1
        else:
            preference[min(distances,key=distances.get)]+=1
        if k in TIMES:
            examples.append({"time_s":100.+.05*k,"gage_1_to_9":c,
                             "residual_norm_m":distances})
    must(sum(preference.values())==n and len(examples)==3,
         "KINEMATIC_SAMPLE_COUNT_MISMATCH")
    return {"status":"NATIVE_TP_RP_SPATIAL_KINEMATIC_CANDIDATE_ONLY",
            "source":"same original 9-station 12001-step ETM OUTB SHA locked above",
            "method":"TP chord (gage9-gage1) versus trapezoidal integration of local-z tangent from SmllRotTrans(RP), for R^T and R; native TPzi sets dz",
            "time_samples":n,"spatial_stations":9,
            "rms_chord_residual_m":{key:math.sqrt(val/n) for key,val in squared.items()},
            "max_chord_residual_m":maxima,
            "max_conservative_packed_bound_m":max_packed,
            "preferred_sign_sample_counts":preference,
            "samples":examples,
            "limitations":"Kinematic consistency is not independent TowerLn2Mesh%Orientation validation; beam shear, finite station spacing and RP semantic/model errors are unbudgeted; ETM near-base only; no external-load mapping PASS"}

def selftest():
    I=smallrot((0.,0.,0.))
    must(mv(I,(1,2,3))==(1.,2.,3.),"IDENTITY_FAIL")
    R=smallrot((0.,0.,.1))
    must(abs(R[0][1]-.1/math.sqrt(1.01))<1e-12,"V353_SOURCE_FORMULA_FAIL")
    f=(100.,0.,0.); fg=mv(trans(R),f)
    must(abs(fg[1]-9.950371902099892)<1e-10,"ROTATION_KNOWN_SOLUTION")
    pos=(0.,2.,0.);mg=cross(pos,fg)
    must(abs(mg[2]+200/math.sqrt(1.01))<1e-10,"ARM_KNOWN_SOLUTION")
    must(norm(tuple(x-y for x,y in zip(mv(R,fg),f)))<1e-10,"ROUNDTRIP_FAIL")
    refused=0
    for bad in ((.401,0,0),(float("nan"),0,0),(0,0,float("inf"))):
        try:smallrot(bad)
        except ValueError:refused+=1
    must(refused==3,"BAD_RP_ACCEPTED")

    zero=(0.,0.,0.)
    known=[((0.,0.,0.),zero,zero,zero),
           ((.05,0.,1.),(0.,math.degrees(.1),0.),zero,zero),
           ((.2,0.,2.),(0.,math.degrees(.2),0.),zero,zero)]
    kc=kinematic_chord(known)
    must(norm(kc["residual_m"]["transpose"])<1e-12 and
         abs(norm(kc["residual_m"]["direct"])-.4)<1e-12,
         "KINEMATIC_KNOWN_CHORD_FAIL")
    bad=[known[0],((.1,0.,0.),zero,zero,zero)]
    try:kinematic_chord(bad)
    except ValueError as e:must("NONMONOTONIC_Z" in str(e),"BAD_KINEMATIC_REJECTION")
    else:raise AssertionError("NONMONOTONIC_Z_ACCEPTED")
    print("S07_KINEMATIC_SELFTEST_PASS known_chord transpose_vs_direct bad_z_rejected")
    print("S07_SELFTEST_PASS identity v353_formula known_rotation known_arm inverse 3_bad_RP")

def run(archive,receipt,out):
    source=Path(archive).read_bytes()
    must(sha(source)==ARCHIVE_SHA,"ARCHIVE_SHA256_MISMATCH")
    old_bytes=Path(receipt).read_bytes()
    old=json.loads(old_bytes)
    must(old["case"]==CASE and old["outb_sha256"]==OUTB_SHA,
         "PRIOR_NATIVE_RECEIPT_IDENTITY_MISMATCH")
    with zipfile.ZipFile(archive) as z:
        must(z.testzip() is None,"ZIP_CRC_FAILURE")
        raw=z.read(MEMBER)
    must(sha(raw)==OUTB_SHA,"OUTB_SHA256_MISMATCH")
    h=outb_header(raw)
    must(h["file_id"]==4 and h["num_samples"]==12001 and
         abs(h["first_time_s"]-100)<1e-12 and
         abs(h["time_increment_s"]-.05)<1e-12,"NATIVE_TIME_GRID_MISMATCH")
    names=h["channel_names"]
    must(names[0]=="Time" and len(names)==len(set(names)),"BAD_CHANNEL_HEADER")
    for g in range(1,10):
        for suffix,unit in zip(SUFFIX,UNITS):
            name=f"TwHt{g}{suffix}"
            must(name in names and h["channel_units"][names.index(name)]==unit,
                 "MISSING_OR_WRONG_UNIT_"+name)
    must(len(old["selected_original_synchronous_samples"])==3,"BAD_PRIOR_SAMPLES")
    for k,previous in zip(TIMES,old["selected_original_synchronous_samples"]):
        must(previous["sample_index"]==k and abs(previous["time_s"]-(100+.05*k))<1e-10,
             "PRIOR_TIME_GRID_MISMATCH")
        for name,item in previous["channels"].items():
            v,lsb=decode(raw,h,name,k)
            must(abs(v-item["value"])<=lsb+5e-9,"PRIOR_SAMPLE_PARITY_FAIL_"+name)
    summary=[];selected=[]
    for g in range(1,10):
        prefix=f"TwHt{g}"
        sums={"max_RP_abs_deg":0.,"max_candidate_force_rotation_delta_N":0.,
              "max_candidate_frame_choice_delta_N":0.,
              "max_candidate_base_moment_arm_Nm":0.,
              "max_force_norm_roundtrip_N":0.,"max_moment_roundtrip_Nm":0.,
              "max_rotation_orthogonality_error":0.,
              "max_native_force_halfLSB_N":0.,"max_native_RP_halfLSB_deg":0.}
        for k in range(12001):
            values=[decode(raw,h,prefix+s,k) for s in SUFFIX]
            v=[x[0] for x in values]
            F=tuple(x*1000 for x in v[:3])
            M=tuple(x*1000 for x in v[3:6])
            pos=tuple(v[6:9])
            rp=tuple(v[9:12])
            R=smallrot(tuple(math.radians(x) for x in rp))
            Rt=trans(R)
            Fg=mv(Rt,F);Mg=mv(Rt,M)
            arm=cross(pos,Fg)
            M0=tuple(Mg[i]+arm[i] for i in range(3))
            fback=mv(R,Fg)
            mback=mv(R,tuple(M0[i]-arm[i] for i in range(3)))
            ortho=max(abs(sum(R[i][j]*R[t][j] for j in range(3))-
                          (1 if i==t else 0)) for i in range(3) for t in range(3))
            sums["max_RP_abs_deg"]=max(sums["max_RP_abs_deg"],max(abs(x) for x in rp))
            sums["max_candidate_force_rotation_delta_N"]=max(sums["max_candidate_force_rotation_delta_N"],
                                                           norm(tuple(Fg[i]-F[i] for i in range(3))))
            sums["max_candidate_frame_choice_delta_N"]=max(sums["max_candidate_frame_choice_delta_N"],
                                                          norm(tuple(Fg[i]-mv(R,F)[i] for i in range(3))))
            sums["max_candidate_base_moment_arm_Nm"]=max(sums["max_candidate_base_moment_arm_Nm"],norm(arm))
            sums["max_force_norm_roundtrip_N"]=max(sums["max_force_norm_roundtrip_N"],
                                                  norm(tuple(fback[i]-F[i] for i in range(3))),
                                                  abs(norm(Fg)-norm(F)))
            sums["max_moment_roundtrip_Nm"]=max(sums["max_moment_roundtrip_Nm"],
                                               norm(tuple(mback[i]-M[i] for i in range(3))))
            sums["max_rotation_orthogonality_error"]=max(sums["max_rotation_orthogonality_error"],ortho)
            sums["max_native_force_halfLSB_N"]=max(sums["max_native_force_halfLSB_N"],
                                                  *(1000*x[1] for x in values[:3]))
            sums["max_native_RP_halfLSB_deg"]=max(sums["max_native_RP_halfLSB_deg"],
                                                 *(x[1] for x in values[9:12]))
            if k in TIMES and g in (1,9):
                selected.append({"gage":g,"time_s":round(100+.05*k,9),
                                 "native_F_N":[round(x,6) for x in F],
                                 "native_M_Nm":[round(x,6) for x in M],
                                 "native_TP_m":[round(x,9) for x in pos],
                                 "native_RP_deg":[round(x,9) for x in rp],
                                 "candidate_F_global_N":[round(x,6) for x in Fg],
                                 "candidate_M_at_origin_Nm":[round(x,6) for x in M0],
                                 "frame_status":"RP_TO_FRAME_UNVERIFIED"})
        summary.append({"gage":g,"samples":12001,**sums})
    result={
      "stage":"S07_REAL_ORIGINAL_ETM_9GAGE_SYNCHRONOUS_SOURCE_FRAME_CANDIDATE_QC",
      "status":"REAL_OUTB_MATH_QC_PASS_FRAME_AND_LOAD_OWNERSHIP_HOLD",
      "case":CASE,"source_archive_sha256":ARCHIVE_SHA,"source_outb_sha256":OUTB_SHA,
      "source_receipt_sha256":sha(old_bytes),
      "script_sha256":sha(Path(__file__).read_bytes()),
      "time_grid":{"start_s":100.,"end_s":700.,"dt_s":.05,"n":12001},
      "gage_count":9,"station_sample_count":9*12001,
      "source_level":"Original ZIP+OUTB full packed bytes, SHA and CRC; 3-sample parity to previous verified receipt",
      "orientation_candidate":"SmllRotTrans353(RP*deg2rad) transpose used as one candidate; opposite R also quantified; neither independently validated against TowerLn2Mesh%Orientation",
      "moment_candidate":"M_origin=R_candidate*M_section+TP_global x (R_candidate*F_section); algebraic transport only, not an external load or tower-base equilibrium assertion",
      "SOURCE":"Original SHA-pinned 2026-10-04 supplementary ETM OUTB and T062 previous source receipt",
      "REF":"OpenFAST v3.5.3 ElastoDyn.f90 L937-943,1169-1206,6023-6034; NWTC_Num.f90 L5378-5470",
      "STANDARD":"No authorized 2025 IEC/GB/NB clause read; not a code check",
      "OFFICIAL":"Original native OpenFAST OUTB; this script only reads and transforms, no new solver RUN",
      "RUN":"Python 3.11 source-byte read, 108009 synchronized station-samples and numeric tests",
      "FIG":"none","TAB":"9-station summary and six actual three-time-point samples",
      "assumptions":"TP is global position and origin Q=(0,0,0) m; RP orientation sign/order candidate, not independently verified; FL/ML are INTERNAL section resultants",
      "error_budget":"Per-channel packed half-LSB in summary; floating point orthogonality/roundtrip in summary; RP-to-frame, section force ownership, reference-point physical errors UNKNOWN",
      "failure_log":"No source mismatch when status PASS; script aborts on source SHA, CRC, header, units, time, parity, or RP angle >0.4rad",
      "HOLD":"ETM not DLC1.2 NTM; nine near-base stations not 31 full-height; TP/RP kinematic chord is not an independent TowerLn2Mesh orientation test; internal FL/ML cannot be applied as independent Abaqus external loads; no material fatigue, earthquake or native Abaqus PASS",
      "physical_pass":False,"summary":summary,"selected_native_samples":selected,
      "kinematic_qc":kinematic_history(raw,h)
    }
    must(len(summary)==9 and len(selected)==6,"OUTPUT_COVERAGE_FAIL")
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("S07_ORIGINAL_ETM_NATIVE_HISTORY_SOURCE_QC_PASS "+json.dumps({
      "source_outb_sha256":OUTB_SHA,"station_samples":9*12001,
      "max_frame_candidate_force_delta_N":max(x["max_candidate_force_rotation_delta_N"] for x in summary),
      "max_algebraic_force_roundtrip_N":max(x["max_force_norm_roundtrip_N"] for x in summary),
      "physical_pass":False,"kinematic_qc":result["kinematic_qc"]["rms_chord_residual_m"]}))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive")
    p.add_argument("--receipt")
    p.add_argument("--out")
    a=p.parse_args()
    if a.self_test:selftest()
    else:
        must(a.archive and a.receipt and a.out,"REQUIRED_ARCHIVE_RECEIPT_OUTPUT")
        run(a.archive,a.receipt,a.out)

if __name__=="__main__":
    main()
