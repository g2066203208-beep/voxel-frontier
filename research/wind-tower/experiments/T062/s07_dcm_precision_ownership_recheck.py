#!/usr/bin/env python3
"""Reconstruct S07 native OpenFAST ElastoDyn gage-220 free-body ledger.

Reads only the SHA-locked original GitHub Actions #41632768388 SINGLE-precision
2-second artifact. Compare IEEE binary32 stepwise arithmetic against binary64
replay of printed native G/T/E values. This is a numerical diagnostics test,
not wind-only ownership closure or a physical acceptance test.

Official OpenFAST v3.5.3 ElastoDyn.f90 L1165-L1206 is the source formula.
Python 3.11+ standard library only; no native solver invoked.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
import struct
import zipfile

EXPECTED_ZIP_SHA = '983bce8ca81981ff5fd00e5261dbfb2c0b6e18b074aa4eb1ff425e6851fb9735'
EXPECTED_RAW_SHA = '77f247d7e0b66997041ffbba70c859bdd38fd345eb303b18b78c6599fa2caa92'
EXPECTED_OFFICIAL_SOURCE_SHA = 'a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3'
RAW_NAME = 's07_native_dcm_raw.log.gz'

def q(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]

def vec_add(a,b,rounder):
    return [rounder(x+y) for x,y in zip(a,b)]

def vec_sub(a,b,rounder):
    return [rounder(x-y) for x,y in zip(a,b)]

def vec_mul(a,c,rounder):
    return [rounder(x*c) for x in a]

def cross(a,b,rounder):
    return [rounder(rounder(a[1]*b[2])-rounder(a[2]*b[1])),
            rounder(rounder(a[2]*b[0])-rounder(a[0]*b[2])),
            rounder(rounder(a[0]*b[1])-rounder(a[1]*b[0]))]

def parse(line,tag):
    p=line.split()
    if p[0]!=tag or int(p[2])!=220:
        raise ValueError('BAD_TAG_OR_GAGE')
    t=float(p[1])
    if not math.isfinite(t):
        raise ValueError('NONFINITE_TIME')
    v=[float(x) for x in p[4 if tag in ('T','E') else 3:]]
    if len(v)!={'G':24,'T':20,'E':14}[tag] or not all(math.isfinite(x) for x in v):
        raise ValueError('FIELD_COUNT_OR_NONFINITE')
    return t, (int(p[3]) if tag!='G' else None), v

def reconstruct(g,t,elems,rounder):
    R=rounder
    rG=g[:3]
    mass,grav=t[:2]
    Ftop=t[2:5];Mtop=t[5:8];accTop=t[8:11];rTop=t[11:14];z2=t[14:17];a2=t[17:20]
    top_acc=vec_add(vec_mul(z2,grav,R),accTop,R)
    F=vec_sub(Ftop,vec_mul(top_acc,mass,R),R)
    M=vec_add(cross(vec_sub(rTop,rG,R),F,R),Mtop,R)
    for i,e in enumerate(elems):
        mj,dh=e[:2];ft=e[2:5];acc=e[5:8];rj=e[8:11];mh=e[11:14]
        a=vec_add(vec_mul(z2,grav,R),acc,R)
        density=vec_sub(ft,vec_mul(a,mj,R),R)
        if i==0:
            w=R(R(.5)*abs(dh))
            arm=vec_mul(a2,R(R(.25)*dh),R)
        else:
            w=abs(dh)
            arm=vec_sub(rj,rG,R)
        F=vec_add(F,vec_mul(density,w,R),R)
        dM=vec_add(cross(arm,density,R),mh,R)
        M=vec_add(M,vec_mul(dM,w,R),R)
    return [R(x*R(.001)) for x in F+M]

def mx_cancellation_at_first_failure(lines):
    """Absolute-term cancellation diagnostic in N m (not a missing-force claim)."""
    for k in range(0,len(lines),903):
        time,_,g=parse(lines[k],'G')
        if abs(time-0.1875)>1e-12:
            continue
        _,_,t=parse(lines[k+1],'T')
        rG=g[:3]; mass,grav=t[:2]
        Ftop=t[2:5]; Mtop=t[5:8]; accTop=t[8:11]
        rTop=t[11:14]; z2=t[14:17]; a2=t[17:20]
        F=vec_sub(Ftop,vec_mul(vec_add(vec_mul(z2,grav,float),accTop,float),mass,float),float)
        topM=vec_add(cross(vec_sub(rTop,rG,float),F,float),Mtop,float)
        terms=[topM[0]]
        for j,line in enumerate(lines[k+2:k+903]):
            _,_,e=parse(line,'E')
            mj,dh=e[:2]
            den=vec_sub(e[2:5],vec_mul(vec_add(vec_mul(z2,grav,float),e[5:8],float),mj,float),float)
            arm=vec_mul(a2,.25*dh,float) if j==0 else vec_sub(e[8:11],rG,float)
            w=abs(dh)*(.5 if j==0 else 1)
            terms.append((cross(arm,den,float)[0]+e[11])*w)
        return {'time_s':time,'native_Mx_Nm':g[15]*1000,
                'absolute_term_sum_Nm':sum(map(abs,terms)),
                'cancellation_factor':sum(map(abs,terms))/abs(g[15]*1000)}
    raise ValueError('FIRST_FAIL_TIME_MISSING')

def evaluate(lines):
    if len(lines)!=145383 or len(lines)%903:
        raise ValueError('RAW_LINE_COUNT_HOLD')
    stats={'float64_fail':[],'float32_fail':[],'float64_max_abs':[0.]*6,
           'float32_max_abs':[0.]*6,'float64_max_tol_ratio':[0.]*6,
           'float32_max_tol_ratio':[0.]*6,'first_fail_float64':None,'first_fail_float32':None}
    for k in range(0,len(lines),903):
        b=lines[k:k+903];gtime,_,g=parse(b[0],'G')
        ttime,topnode,t=parse(b[1],'T')
        if ttime!=gtime or topnode!=1120:
            raise ValueError('TOPNODE_OR_TIME_HOLD')
        elems=[]
        for j,line in enumerate(b[2:]):
            etime,node,e=parse(line,'E')
            if etime!=gtime or node!=220+j:
                raise ValueError('ELEMENT_INDEX_OR_TIME_HOLD')
            elems.append(e)
        for key,rounder in [('float64',float),('float32',q)]:
            v=reconstruct(g,t,elems,rounder)
            tar=g[12:18]
            diffs=[v[i]-tar[i] for i in range(6)]
            ratios=[abs(diffs[i])/(1e-5+5e-5*max(abs(v[i]),abs(tar[i]))) for i in range(6)]
            bad=[i for i,x in enumerate(ratios) if x>1]
            stats[key+'_max_abs']=[max(a,abs(b)) for a,b in zip(stats[key+'_max_abs'],diffs)]
            stats[key+'_max_tol_ratio']=[max(a,b) for a,b in zip(stats[key+'_max_tol_ratio'],ratios)]
            if bad:
                event={'time_s':gtime,'failed_component_indices':bad,
                       'max_tol_ratio':max(ratios[i] for i in bad),
                       'residual_kN_or_kNm':[diffs[i] for i in bad],
                       'native_target':[tar[i] for i in bad]}
                stats[key+'_fail'].append(event)
                if stats['first_fail_'+key] is None:
                    stats['first_fail_'+key]=event
    stats['native_sample_count']=len(lines)//903
    stats['elements_per_sample']=901
    stats['float64_pass_samples']=stats['native_sample_count']-len(stats['float64_fail'])
    stats['float32_pass_samples']=stats['native_sample_count']-len(stats['float32_fail'])
    return stats

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    b=open(args.archive,'rb').read()
    if hashlib.sha256(b).hexdigest()!=EXPECTED_ZIP_SHA:
        raise ValueError('SOURCE_ZIP_SHA256_HOLD')
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP_CRC_HOLD')
        raw=gzip.decompress(z.read(RAW_NAME))
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_RAW_SHA:
        raise ValueError('SOURCE_RAW_SHA256_HOLD')
    lines=raw.decode('utf-8').splitlines()
    # Native corruption rejection: use the same real row; do not fabricate a successful solver.
    negative=0
    for bad in [lines[:2]+lines[3:], [lines[0].replace('G ', 'X ',1)]+lines[1:903],
                [lines[0],lines[1]]+[lines[2].replace('1.6682062500000000E+004','NaN',1)]+lines[3:903]]:
        try: evaluate(bad)
        except ValueError: negative+=1
    if negative!=3:
        raise AssertionError('NEGATIVE_TEST_REJECTION_HOLD')
    s=evaluate(lines)
    s['first_failure_Mx_cancellation']=mx_cancellation_at_first_failure(lines)
    s.update({'status':'PRECISION_ARITHMETIC_DIAGNOSTIC_NOT_PHYSICS_PASS',
              'SOURCE':{'zip_sha256':EXPECTED_ZIP_SHA,'raw_probe_sha256':EXPECTED_RAW_SHA,
                        'read_level':'DIRECT_NATIVE_2S_PROBE_G_T_E_ALL_161_TIMESTEPS',
                        'official_elastodyn_f90_sha256':EXPECTED_OFFICIAL_SOURCE_SHA},
              'REF':'OpenFAST v3.5.3 official ElastoDyn.f90 L1165-L1206',
              'STANDARD':'No IEC/GB authorized text read',
              'OFFICIAL':'OpenFAST v3.5.3 tagged source; single precision native 2s artifact',
              'RUN':'Python standard-library float64 and float32 source-formula replay only; 0 solver',
              'FIG':0,'TAB':'161 native G/T/E ledgers, 901 elements each; 6 components',
              'negative_rejections':negative,
              'assumptions':'float32 emulates per-operation rounding, not exact GNU compiler instruction ordering',
              'error_budget':'Original parser atol=1e-5 and rtol=5e-5 per component; cancellation-sensitive near-zero components; no physical tolerance defined',
              'HOLD':'Float32 replay is not exact native floating point ordering; residual at t=0.1875 Mx remains; source load ownership includes gravity/inertia; no formal six-component mapping/DLC1.2 physical PASS',
              'physical_pass':False})
    with open(args.out,'w') as f:json.dump(s,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({k:s[k] for k in ['native_sample_count','float64_pass_samples','float32_pass_samples','first_fail_float64','first_fail_float32','negative_rejections','physical_pass']},indent=2))

if __name__=='__main__':main()
