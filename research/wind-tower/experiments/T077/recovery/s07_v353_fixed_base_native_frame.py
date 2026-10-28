#!/usr/bin/env python3
"""S07: source-derived ElastoDyn v3.5.3 tower DCM on VERIFIED FIXED BASE only.

The OpenFAST TwHt*RP* channels are NOT generic Euler angles. When the original
ElastoDyn input disables all six platform DOFs, its AngPosEF and SmllRotTrans
equations permit reconstruction of the tower local basis. The FL/ML outputs
remain INTERNAL SECTION RESULTANTS; NEVER export them as Abaqus external loads.
Python 3.11+ standard library only; no production solver.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import struct
import sys
import zipfile

CASE = "U09p343881_ETM_S01"
ED_SHA = "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65"
FST_SHA = "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605"
OUTB_SHA = "0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c"
STATIC_ZIP_SHA = "ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267"
DYNAMIC_ZIP_SHA = "c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0"
ED_BLOB = "2bcfb11fc40712febb5a8b5c2947c87e2aabb7b1"
NWTC_BLOB = "2daf088cca20a91e559490749b99cb35f25f208b"
FLAGS = ("PtfmSgDOF", "PtfmSwDOF", "PtfmHvDOF", "PtfmRDOF", "PtfmPDOF", "PtfmYDOF")
SUFFIX = ("FLxt", "FLyt", "FLzt", "MLxt", "MLyt", "MLzt",
          "TPxi", "TPyi", "TPzi", "RPxi", "RPyi", "RPzi")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def checked(path, expected):
    raw = Path(path).read_bytes()
    if sha(raw) != expected:
        raise ValueError("SHA256 mismatch: " + str(path))
    return raw


def member(raw_zip, path, expected):
    with zipfile.ZipFile(__import__("io").BytesIO(raw_zip)) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP CRC failed")
        raw = z.read(path)
    if sha(raw) != expected:
        raise ValueError("archived member SHA256 mismatch: " + path)
    return raw


def fixed_platform(ed):
    """Fail closed: a moving platform invalidates inversion of RP to theta."""
    text = ed.decode("utf-8-sig", errors="strict")
    flags = {}
    for name in FLAGS:
        matches = re.findall(r"(?im)^\s*(true|false|\.true\.|\.false\.)\s+" +
                             re.escape(name) + r"\b", text)
        if len(matches) != 1:
            raise ValueError("missing or duplicate platform DOF: " + name)
        flags[name] = matches[0].strip(".").lower() == "true"
    if any(flags.values()):
        raise ValueError("platform DOF active: RP does not uniquely determine tower DCM")
    return flags


def official_contract(ed_source, nwtc_source):
    e = Path(ed_source).read_bytes()
    n = Path(nwtc_source).read_bytes()
    if blob(e) != ED_BLOB or blob(n) != NWTC_BLOB:
        raise ValueError("OpenFAST v3.5.3 official Git blob mismatch")
    for token in ("SmllRotTrans( 'tower deflection (ElastoDyn SetCoordSy)'",
                  "RtHSdat%AngPosEF (:,J)            =  RtHSdat%AngPosEX",
                  "m%AllOuts( TwHtRPxi(I) ) =  m%RtHS%AngPosEF(1",
                  "m%AllOuts( TwHtRPyi(I) ) = -m%RtHS%AngPosEF(3",
                  "CoordSys%t1(J,:) = TransMat(1,1)*CoordSys%a1",
                  "m%AllOuts( TwHtFLxt(I) ) =     DOT_PRODUCT( FrcFGagT"):
        if token not in e.decode("utf-8"):
            raise ValueError("ElastoDyn source signature missing: " + token)
    for token in ("SUBROUTINE SmllRotTransD(", "TransMat(1,2) = (  Theta3*SqrdSum",
                  "TransMat(2,3) = (  Theta1*SqrdSum"):
        if token not in n.decode("utf-8"):
            raise ValueError("NWTC source signature missing: " + token)
    return {"elastodyn_blob": blob(e), "nwtc_num_blob": blob(n),
            "elastodyn_sha256": sha(e), "nwtc_num_sha256": sha(n)}


def dcm_fixed(rpx_deg, rpy_deg, rpz_deg):
    """IEC local->IEC global; exact source SmllRotTrans polar matrix.

    For fixed base: thetaSS=RPxi, thetaFA=RPyi, theta2=0; RPzi=0.
    ElastoDyn internal (x,y,z) maps to IEC (x,-z,y).
    Local IEC axes are (t1,-t3,t2). No Euler approximation is used.
    """
    a, b, z = (math.radians(float(v)) for v in (rpx_deg, rpy_deg, rpz_deg))
    if not all(map(math.isfinite, (a, b, z))):
        raise ValueError("nonfinite RP")
    if abs(z) > 1e-10:
        raise ValueError("nonzero RPzi: unsupported fixed-platform inversion")
    if max(abs(a), abs(b)) >= 0.4:
        raise ValueError("SmllRotTrans small-angle validity exceeded")
    s = a*a + b*b
    d = math.sqrt(1+s)
    c = 1/d
    k = 1/(d*(d+1))  # stable (1-c)/s, including s=0
    t11, t12, t13 = c+k*a*a, b*c, k*a*b
    t21, t22, t23 = -b*c, c, a*c
    t31, t32, t33 = k*a*b, -a*c, c+k*b*b
    R = ((t11, -t31, t21),
         (-t13, t33, -t23),
         (t12, -t32, t22))
    return R


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def mul(R,v):
    return tuple(dot(row,v) for row in R)


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def verify(R):
    return max(abs(dot(R[i],R[j])-(i==j)) for i in range(3) for j in range(3))


def selftest():
    I = dcm_fixed(0,0,0)
    assert I == ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
    for a,b in ((0.1,0), (0,0.1), (0.1,-0.2), (0.00001,0.00002)):
        R = dcm_fixed(a,b,0)
        assert verify(R)<1e-14
        assert abs(dot(R[0],cross(R[1],R[2]))-1)<1e-14
        F=(12.,-7.,25.); M=(40.,50.,-10.)
        fg=mul(R,F); mg=mul(R,M)
        back=tuple(dot(tuple(R[j][i] for j in range(3)),fg) for i in range(3))
        assert max(abs(x-y) for x,y in zip(F,back))<1e-12
        assert math.isclose(sum(x*x for x in M),sum(x*x for x in mg),rel_tol=1e-13)
    for bad in ((0,0,0.01),(30,0,0),(float("nan"),0,0)):
        try: dcm_fixed(*bad)
        except ValueError: pass
        else: raise AssertionError("bad RP accepted")
    try: fixed_platform(b"True PtfmRDOF\n")
    except ValueError: pass
    else: raise AssertionError("unproven platform accepted")
    fake="\n".join("False "+x for x in FLAGS).encode()
    assert not any(fixed_platform(fake).values())
    try: fixed_platform(fake.replace(b"False PtfmRDOF",b"True PtfmRDOF"))
    except ValueError: pass
    else: raise AssertionError("moving platform accepted")
    print("PASS: stable source polar DCM, signs, orthogonality, inverse, tamper gates")


def audit(args):
    sys.path.insert(0,str(Path(args.parser).resolve().parent))
    import s06_historical_outb_source_gate as parser
    ed_zip = checked(args.static_zip, STATIC_ZIP_SHA)
    out_zip = checked(args.dynamic_zip, DYNAMIC_ZIP_SHA)
    prefix=f"CASES/{CASE}/DTU_10MW_RWT"
    ed = member(ed_zip,prefix+"_ElastoDyn.dat",ED_SHA)
    fst = member(ed_zip,prefix+".fst",FST_SHA)
    flags = fixed_platform(ed)
    source = official_contract(args.elastodyn_source,args.nwtc_source)
    raw = member(out_zip,prefix+".outb",OUTB_SHA)
    h = parser.outb_header(raw)
    if h["file_id"] != 4 or h["num_samples"] != 12001 or abs(h["time_increment_s"]-.05)>1e-12:
        raise ValueError("unexpected original OUTB time identity")
    names=h["channel_names"]
    if names[0]!="Time":
        raise ValueError("Time channel missing")
    channels={f"TwHt{g}{suffix}":None for g in range(1,10) for suffix in SUFFIX}
    for name in channels:
        if name not in names:
            raise ValueError("missing native channel "+name)
        idx=names.index(name)-1
        unit=h["channel_units"][idx+1]
        expected=("(kN)" if name.endswith(("FLxt","FLyt","FLzt")) else
                  "(kN-m)" if "ML" in name else "(m)" if "TP" in name else "(deg)")
        if unit!=expected:
            raise ValueError("native unit mismatch "+name+" "+unit)
        scale=h["column_scales"][idx]
        if not scale or not math.isfinite(scale):
            raise ValueError("invalid native packing scale")
        channels[name]=(idx,scale,h["column_offsets"][idx])
    n=h["num_output_channels"]
    max_ortho=max_inverse=max_rot=max_force_shift=max_moment_shift=0.0
    count=0; first=[]
    for ti in range(h["num_samples"]):
        offset=h["data_offset_bytes"]+2*n*ti
        def read(name):
            j,s,o=channels[name]
            return (struct.unpack_from("<h",raw,offset+2*j)[0]-o)/s
        for g in range(1,10):
            p=f"TwHt{g}"
            rp=tuple(read(p+x) for x in ("RPxi","RPyi","RPzi"))
            R=dcm_fixed(*rp)
            F=tuple(read(p+x) for x in ("FLxt","FLyt","FLzt"))
            M=tuple(read(p+x) for x in ("MLxt","MLyt","MLzt"))
            A=tuple(read(p+x) for x in ("TPxi","TPyi","TPzi"))
            fg=mul(R,F); mg=mul(R,M)
            at_base=tuple(x+y for x,y in zip(mg,cross(A,fg)))
            back=tuple(dot(tuple(R[j][i] for j in range(3)),fg) for i in range(3))
            err=max(abs(x-y) for x,y in zip(back,F))
            max_inverse=max(max_inverse,err)
            max_ortho=max(max_ortho,verify(R))
            max_rot=max(max_rot,math.hypot(rp[0],rp[1]))
            max_force_shift=max(max_force_shift,max(abs(x-y) for x,y in zip(fg,F)))
            max_moment_shift=max(max_moment_shift,max(abs(x-y) for x,y in zip(at_base,M)))
            if ti==0:
                first.append({"gage":g,"RP_deg":rp,"local_force_kN":F,
                              "global_force_kN":fg,"local_moment_kNm":M,
                              "global_moment_at_base_kNm":at_base})
            count+=1
    if count!=108009 or max_ortho>1e-12 or max_inverse>1e-8:
        raise AssertionError("dynamic DCM/inverse numerical acceptance failed")
    return {
        "stage":"S07_CONDITIONAL_FIXED_BASE_DCM_ALGORITHM_TESTED_NOT_PHYSICS_PASS",
        "SOURCE":{"static_zip_sha256":sha(ed_zip),"dynamic_zip_sha256":sha(out_zip),
                  "fst_sha256":sha(fst),"elastodyn_input_sha256":sha(ed),
                  "outb_sha256":sha(raw),"reading_level":"original 12001x9 packed OUTB, original FST/ElastoDyn, original v3.5.3 Fortran"},
        "OFFICIAL":source,"RUN":{"python":platform.python_version(),"native_solver":"NOT_RUN",
                "synchronous_time_steps":12001,"gages":9,"transforms":count,
                "platform_dof_flags":flags},
        "TAB":{"first_sample":first,"max_R_orthogonality_abs":max_ortho,
               "max_inverse_force_error_kN":max_inverse,
               "max_RP_xy_norm_deg":max_rot,
               "max_force_component_change_from_identity_kN":max_force_shift,
               "max_base_moment_change_from_untransported_local_kNm":max_moment_shift},
        "REF":"OpenFAST v3.5.3 ElastoDyn.f90 lines 922-943, 1190-1206, 6005-6034, 6856-6860; NWTC_Num.f90 lines 5378-5470",
        "STANDARD":"NONE; no authorized IEC/GB clauses read",
        "FIG":"NONE; no native Abaqus physical response",
        "assumptions":["all six platform DOFs false in original input (programmatically verified)",
                       "ElastoDyn small-angle tower formulation valid for this source",
                       "RP source angular components inverted only under fixed-base condition"],
        "error_budget":{"numerical_inverse_force_kN":max_inverse,
                        "orthogonality_abs":max_ortho,
                        "packed_OUTB_quantization":"channel scale/offset finite, precision limited by int16 packing; physical uncertainty NEED_ESTIMATE",
                        "dynamic_load_ownership":"UNVERIFIED"},
        "HOLD":"9 near-base gages only; 31-gage rerun different source; internal section resultants include inertia/gravity/RNA; no Abaqus external load or free-body physics PASS"
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    for key in ("static-zip","dynamic-zip","elastodyn-source","nwtc-source","parser","output"):
        p.add_argument("--"+key)
    args=p.parse_args()
    if args.self_test:
        selftest()
        if not args.output:
            return
    if not all(getattr(args,k.replace("-","_")) for k in
               ("static-zip","dynamic-zip","elastodyn-source","nwtc-source","parser","output")):
        p.error("original static/dynamic ZIP, official source, parser, and output required")
    result=audit(args)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("PASS S07 source-derived fixed-base DCM numerical gate; NOT free-body/ABAQUS PHYSICS PASS")
    print(json.dumps({k:result["TAB"][k] for k in result["TAB"] if k!="first_sample"},sort_keys=True))


if __name__=="__main__":
    main()
