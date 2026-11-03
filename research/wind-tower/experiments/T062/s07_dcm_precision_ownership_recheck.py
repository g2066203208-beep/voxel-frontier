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

def reconstruct_legacy_order(g,t,elems,rounder):
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

def reconstruct(g,t,elems,rounder):
    """Replay the *actual source order*: all upper J nodes, THEN gage half-node.

    OpenFAST v3.5.3 ElastoDyn.f90 lines 1175-1202:
    DO J=(gage+1),TwrNodes ... ENDDO; afterward add half gage element.
    The old Python diagnostic reversed that order, and collapsed the two
    left-associative half-element multiplications into one precomputed weight.
    Those transformations are not floating-point equivalent near cancellation.
    """
    R=rounder
    rG=g[:3]
    mass,grav=t[:2]
    Ftop=t[2:5]; Mtop=t[5:8]; accTop=t[8:11]
    rTop=t[11:14]; z2=t[14:17]; a2=t[17:20]
    top_acc=vec_add(vec_mul(z2,grav,R),accTop,R)
    F=vec_sub(Ftop,vec_mul(top_acc,mass,R),R)
    M=vec_add(cross(vec_sub(rTop,rG,R),F,R),Mtop,R)
    if len(elems)!=901:
        raise ValueError('EXPECTED_901_ELEMENT_ROWS')
    # Fortran DO J=(gage+1),TwrNodes: 900 complete elements above gage.
    for e in elems[1:]:
        mj,dh=e[:2]; ft=e[2:5]; acc=e[5:8]; rj=e[8:11]; mh=e[11:14]
        acc_g=vec_add(vec_mul(z2,grav,R),acc,R)
        den=vec_sub(ft,vec_mul(acc_g,mj,R),R)
        w=abs(dh)
        F=vec_add(F,vec_mul(den,w,R),R)
        dm=vec_add(cross(vec_sub(rj,rG,R),den,R),mh,R)
        M=vec_add(M,vec_mul(dm,w,R),R)
    # Fortran adds the 1/2 strain-gage element AFTER all upper elements.
    e=elems[0]
    mj,dh=e[:2]; ft=e[2:5]; acc=e[5:8]; mh=e[11:14]
    den=vec_sub(ft,vec_mul(vec_add(vec_mul(z2,grav,R),acc,R),mj,R),R)
    # Source expression: TmpVec2 * 0.5 * abs(DHNodes), left associative.
    F=vec_add(F,vec_mul(vec_mul(den,R(.5),R),abs(dh),R),R)
    F=vec_mul(F,R(.001),R)
    arm=vec_mul(a2,R(R(.25)*dh),R)
    dm=vec_add(cross(arm,den,R),mh,R)
    M=vec_add(M,vec_mul(vec_mul(dm,R(.5),R),abs(dh),R),R)
    M=vec_mul(M,R(.001),R)
    return F+M

def source_order_negative_fixture():
    """Deterministic float32 cancellation test: order must not be swapped."""
    g=[0.0]*24
    t=[0.0]*20
    t[2]=1e8   # tower-top force in N
    e0=[0.0]*14; e0[1]=1.0; e0[2]=2.0    # half element contributes +1 N
    e1=[0.0]*14; e1[1]=1.0; e1[2]=-1e8  # upper element contributes -1e8 N
    ez=[0.0]*14; ez[1]=1.0
    elems=[e0,e1]+[ez[:] for _ in range(899)]
    actual=reconstruct(g,t,elems,q)[0]
    reversed_value=reconstruct_legacy_order(g,t,elems,q)[0]
    if abs(actual-q(.001))>1e-9 or reversed_value!=0.0:
        raise AssertionError(('SOURCE_LOOP_ORDER_FIXTURE_FAILED',actual,reversed_value))
    return {'source_order_Fx_kN':actual,'legacy_half_first_Fx_kN':reversed_value}


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
           'float32_max_abs':[0.]*6,'legacy_float32_max_abs':[0.]*6,'float64_max_tol_ratio':[0.]*6,
           'float32_max_tol_ratio':[0.]*6,'legacy_float32_max_tol_ratio':[0.]*6,'first_fail_float64':None,'first_fail_float32':None,'legacy_float32_fail':[],'first_fail_legacy_float32':None}
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
        for key,rounder,func in [('float64',float,reconstruct),('float32',q,reconstruct),('legacy_float32',q,reconstruct_legacy_order)]:
            v=func(g,t,elems,rounder)
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
    fixture=source_order_negative_fixture()
    s=evaluate(lines)
    s['source_order_fixture']=fixture
    s['legacy_float32_pass_samples']=s['native_sample_count']-len(s['legacy_float32_fail'])
    s['source_order_float32_pass_delta']=s['float32_pass_samples']-s['legacy_float32_pass_samples']
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
              'official_source_order':'Full upper tower elements J=gage+1..TwrNodes FIRST; half gage element LAST; half weight left associative',
              'legacy_replay_warning':'Earlier diagnostic incorrectly processed half gage element first, changing float32 summation order; old 11-to-1 claim is not source-faithful until rechecked',
              'assumptions':'float32 emulates per-operation rounding and source loop order, not exact GNU compiler instruction ordering or FMA behavior',
              'error_budget':'Original parser atol=1e-5 and rtol=5e-5 per component; cancellation-sensitive near-zero components; no physical tolerance defined',
              'HOLD':'Native source-order replay must be checked against original archive CI; compiler FMA/rounding remains unverified; source load ownership includes gravity/inertia; no formal six-component mapping/DLC1.2 physical PASS',
              'physical_pass':False})
    with open(args.out,'w') as f:json.dump(s,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({k:s[k] for k in ['native_sample_count','float64_pass_samples','float32_pass_samples','legacy_float32_pass_samples','source_order_float32_pass_delta','first_fail_float64','first_fail_float32','negative_rejections','physical_pass']},indent=2))

if __name__=='__main__':main()
