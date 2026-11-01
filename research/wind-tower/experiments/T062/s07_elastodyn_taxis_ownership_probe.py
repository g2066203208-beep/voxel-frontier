#!/usr/bin/env python3
"""Source-locked, opt-in OpenFAST v3.5.3 tower-gage diagnostic and independent ledger.

Never patches the frozen turbine model or a production executable. A patched copy
of official ElastoDyn.f90 must be compiled separately; this script does NOT run
OpenFAST/Abaqus and cannot approve external wind loads or material fatigue.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

OFFICIAL_SHA256 = 'a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3'
ANCHOR = '      m%AllOuts( TwHtMLzt(I) ) =     DOT_PRODUCT( MomFGagT, m%CoordSys%t2(p%TwrGagNd(I),:) )'
# All vectors below are in the ElastoDyn internal inertial frame (z1,z2,z3).
# Native t1/-t3/t2 are the LOCAL column axes, not RP-derived Euler angles.
PROBE = '''
      ! S07_DIAGNOSTIC_ONLY: opt-in, short native pilot; no dynamics changed.
      BLOCK
         CHARACTER(LEN=512) :: s07_path
         INTEGER :: s07_len, s07_stat, s07_unit, s07_io, s07_j, s07_g
         CALL GET_ENVIRONMENT_VARIABLE('OPENFAST_S07_DCM_PROBE', s07_path, &
              LENGTH=s07_len, STATUS=s07_stat)
         s07_g = p%TwrGagNd(I)
         IF (s07_stat == 0 .AND. s07_len > 0 .AND. s07_g == 220) THEN
            OPEN(NEWUNIT=s07_unit, FILE=TRIM(s07_path), STATUS='UNKNOWN', &
                 POSITION='APPEND', ACTION='WRITE', IOSTAT=s07_io)
            IF (s07_io /= 0) ERROR STOP 'S07_PROBE_OPEN_FAILED'
            WRITE(s07_unit,'(A,1X,ES24.16E3,1X,I0,1X,*(ES24.16E3,1X))',IOSTAT=s07_io) &
                 'G', t, s07_g, m%RtHS%rZT(:,s07_g), &
                 m%CoordSys%t1(s07_g,:), -m%CoordSys%t3(s07_g,:), &
                 m%CoordSys%t2(s07_g,:), FrcFGagT, MomFGagT, &
                 m%AllOuts(TwHtFLxt(I)), m%AllOuts(TwHtFLyt(I)), &
                 m%AllOuts(TwHtFLzt(I)), m%AllOuts(TwHtMLxt(I)), &
                 m%AllOuts(TwHtMLyt(I)), m%AllOuts(TwHtMLzt(I))
            IF (s07_io /= 0) ERROR STOP 'S07_PROBE_G_WRITE_FAILED'
            WRITE(s07_unit,'(A,1X,ES24.16E3,1X,I0,1X,I0,1X,*(ES24.16E3,1X))',IOSTAT=s07_io) &
                 'T', t, s07_g, p%TwrNodes, p%YawBrMass, p%Gravity, &
                 FrcONcRt, MomBNcRt, LinAccEO, m%RtHS%rZO, &
                 m%CoordSys%z2, m%CoordSys%a2
            IF (s07_io /= 0) ERROR STOP 'S07_PROBE_T_WRITE_FAILED'
            DO s07_j = s07_g, p%TwrNodes
               WRITE(s07_unit,'(A,1X,ES24.16E3,1X,I0,1X,I0,1X,*(ES24.16E3,1X))',IOSTAT=s07_io) &
                    'E', t, s07_g, s07_j, p%MassT(s07_j), p%DHNodes(s07_j), &
                    FTTower(:,s07_j), LinAccET(:,s07_j), &
                    m%RtHS%rZT(:,s07_j), MFHydro(:,s07_j)
               IF (s07_io /= 0) ERROR STOP 'S07_PROBE_E_WRITE_FAILED'
            ENDDO
            CLOSE(s07_unit, IOSTAT=s07_io)
            IF (s07_io /= 0) ERROR STOP 'S07_PROBE_CLOSE_FAILED'
         ENDIF
      END BLOCK
'''


def sha(b):
    return hashlib.sha256(b).hexdigest()


def patch(source, target_node=220):
    if target_node != 220:
        raise ValueError('ONLY_VALIDATED_GAGE_220')
    if sha(source) != OFFICIAL_SHA256:
        raise ValueError('OFFICIAL_SOURCE_SHA256_MISMATCH')
    s = source.decode('utf-8')
    if s.count(ANCHOR) != 1 or 'S07_DIAGNOSTIC_ONLY' in s:
        raise ValueError('ANCHOR_OR_ALREADY_PATCHED')
    return s.replace(ANCHOR, ANCHOR + '\n' + PROBE, 1).encode('utf-8')


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def add(a, b):
    return [x+y for x,y in zip(a,b)]


def sub(a, b):
    return [x-y for x,y in zip(a,b)]


def scale(a, s):
    return [x*s for x in a]


def dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def close(a, b, rtol=5e-5, atol=1e-5):
    return all(abs(x-y) <= atol + rtol*max(abs(x),abs(y)) for x,y in zip(a,b))


def parse_records(text):
    groups = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        p = line.split()
        tag = p[0]
        if tag not in ('G','T','E'):
            raise ValueError(f'BAD_TAG line={lineno}')
        time = float(p[1]); node = int(p[2])
        if not math.isfinite(time) or node != 220:
            raise ValueError(f'BAD_TIME_OR_GAGE line={lineno}')
        vals = list(map(float, p[4 if tag in ('T','E') else 3:]))
        if not all(map(math.isfinite, vals)):
            raise ValueError(f'NONFINITE line={lineno}')
        expected = {'G':24, 'T':20, 'E':14}[tag]
        if len(vals) != expected:
            raise ValueError(f'FIELD_COUNT {tag} {len(vals)} != {expected}')
        group = groups.setdefault((time,node), {'E':{}})
        if tag == 'E':
            j = int(p[3]);
            if j in group['E']:
                raise ValueError('DUPLICATE_ELEMENT')
            group['E'][j] = vals
        else:
            if tag in group:
                raise ValueError('DUPLICATE_RECORD')
            group[tag] = (int(p[3]), vals) if tag == 'T' else vals
    return groups


def audit_group(group):
    if 'G' not in group or 'T' not in group:
        raise ValueError('MISSING_G_OR_T')
    g = group['G']; topnode, T = group['T']; E = group['E']
    if sorted(E) != list(range(220, topnode+1)):
        raise ValueError('MISSING_OR_EXTRA_ELEMENT')
    rG = g[0:3]
    basis = [g[3:6],g[6:9],g[9:12]]
    Q = [[basis[c][r] for c in range(3)] for r in range(3)]
    for i in range(3):
        for j in range(3):
            if abs(dot(basis[i],basis[j])-(1 if i==j else 0)) > 2e-5:
                raise ValueError('DCM_ORTHOGONAL_HOLD')
    if abs(dot(basis[0],cross(basis[1],basis[2]))-1) > 2e-5:
        raise ValueError('DCM_HANDEDNESS_HOLD')
    # T = mass, g, Ftop(3), Mtop(3), accTop(3), rTop(3), z2(3), a2(3)
    mass, grav = T[:2]; Ftop=T[2:5]; Mtop=T[5:8]; accTop=T[8:11]
    rTop=T[11:14]; z2=T[14:17]; a2=T[17:20]
    F = sub(Ftop,scale(add(scale(z2,grav),accTop),mass))
    M = add(cross(sub(rTop,rG),F),Mtop)
    for j in range(220,topnode+1):
        row = E[j]; mj,dh = row[:2]; ft=row[2:5]; acc=row[5:8]
        rj=row[8:11]; mh=row[11:14]
        density = sub(ft,scale(add(scale(z2,grav),acc),mj))
        if j==220:
            w=0.5*abs(dh)
            arm=scale(a2,0.25*dh)
        else:
            w=abs(dh)
            arm=sub(rj,rG)
        F=add(F,scale(density,w))
        M=add(M,scale(add(cross(arm,density),mh),w))
    F=scale(F,0.001); M=scale(M,0.001)
    if not close(F,g[12:15]) or not close(M,g[15:18]):
        raise ValueError('INERTIA_GRAVITY_OWNERSHIP_RECONSTRUCTION_HOLD')
    localF=[dot(F,b) for b in basis]
    localM=[dot(M,b) for b in basis]
    if not close(localF,g[18:21]) or not close(localM,g[21:24]):
        raise ValueError('LOCAL_GLOBAL_WRENCH_MISMATCH')
    # OpenFAST internal -> IEC (xi, yi, zi): (x, -z, y).
    to_iec=lambda v:[v[0],-v[2],v[1]]
    Qiec=[[to_iec(basis[c])[r] for c in range(3)] for r in range(3)]
    return {'Q_IEC_local_to_global':Qiec, 'F_IEC_kN':to_iec(F),
            'M_IEC_kNm_at_gage':to_iec(M), 'element_rows':len(E),
            'source_ownership':'INCLUDES_TOP_AND_TOWER_GRAVITY_INERTIA_NOT_WIND_ONLY'}


def selftest():
    # Independent analytic ledger with nonzero gravity, top/nodal inertia, and hydro moment.
    # 2 elements: gauge 220, top node 221. Force N and moment N m in internal frame.
    # F = (1236, -204.58, -30) N; M = (838.32, 6334, -21.5) N m.
    g=[0,0,4, 1,0,0, 0,0,-1, 0,1,0,
       1.236,-0.20458,-0.03, 0.83832,6.334,-0.0215,
       1.236,0.03,-0.20458, 0.83832,0.0215,6.334]
    t=[10,9.81, 1000,0,0, 0,0,0, 1,2,3, 0,0,10, 0,1,0, 0,1,0]
    e1=[2,2, 50,0,0, 0.5,1,0, 0,0,4, 0,0,1]
    e2=[3,2, 100,0,0, 0.5,1,0, 0,0,6, 0,0,1]
    s='\n'.join(['G 0 220 '+' '.join(map(str,g)),
                 'T 0 220 221 '+' '.join(map(str,t)),
                 'E 0 220 220 '+' '.join(map(str,e1)),
                 'E 0 220 221 '+' '.join(map(str,e2))])
    r=audit_group(next(iter(parse_records(s).values())))
    assert r['element_rows']==2
    assert close(r['F_IEC_kN'],[1.236,0.03,-0.20458],rtol=1e-12,atol=1e-12)
    assert close(r['M_IEC_kNm_at_gage'],[0.83832,0.0215,6.334],rtol=1e-12,atol=1e-12)
    for bad in [s.replace('E 0 220 221','E 0 220 220'),
                s.replace('G 0 220 0 0 4','G 0 220 nan 0 4'),
                s.replace('1.236 -0.20458 -0.03','9.236 -0.20458 -0.03'),
                s.replace('T 0 220 221','T 0 220 222'),
                s.replace('10 9.81 1000','100 9.81 1000'),
                s.replace('0 0 -1 0 1 0','0 0 1 0 1 0')]:
        try: audit_group(next(iter(parse_records(bad).values())))
        except ValueError: pass
        else: raise AssertionError('NEGATIVE_TEST_NOT_REJECTED')
    try: patch(b'bad')
    except ValueError: pass
    else: raise AssertionError('BAD_SHA_ACCEPTED')
    return {'synthetic_ledger':'PASS_NONZERO_GRAVITY_INERTIA_HYDRO',
            'negative_rejections':7, 'native_solver_run':False,'physical_pass':False,
            'Q_IEC':r['Q_IEC_local_to_global']}


def fortran_smoke():
    compiler=shutil.which('gfortran')
    if not compiler:
        raise RuntimeError('GFORTRAN_UNAVAILABLE')
    # Minimal typed stubs compile the EXACT inserted BLOCK with strict F2008.
    stub='''program smoke
implicit none
type coord
 real(8)::t1(221,3),t2(221,3),t3(221,3),z2(3),a2(3)
end type
type rhs
 real(8)::rZT(3,0:221),rZO(3)
end type
type model
 type(coord)::CoordSys
 type(rhs)::RtHS
 real(8)::AllOuts(6)
end type
type params
 integer::TwrGagNd(1),TwrNodes
 real(8)::YawBrMass,Gravity,MassT(221),DHNodes(221)
end type
type(model)::m
type(params)::p
real(8)::t,FrcFGagT(3),MomFGagT(3),FrcONcRt(3),MomBNcRt(3),LinAccEO(3)
real(8)::FTTower(3,221),LinAccET(3,221),MFHydro(3,221)
integer::I,TwHtFLxt(1),TwHtFLyt(1),TwHtFLzt(1),TwHtMLxt(1),TwHtMLyt(1),TwHtMLzt(1)
p%TwrGagNd=220;p%TwrNodes=221
p%YawBrMass=0;p%Gravity=9.81d0;p%MassT=0;p%DHNodes=2
m%CoordSys%t1=0;m%CoordSys%t2=0;m%CoordSys%t3=0
m%CoordSys%t1(:,1)=1;m%CoordSys%t2(:,2)=1;m%CoordSys%t3(:,3)=1
m%CoordSys%z2=(/0d0,1d0,0d0/);m%CoordSys%a2=m%CoordSys%z2
m%RtHS%rZT=0;m%RtHS%rZO=(/0d0,0d0,10d0/)
m%RtHS%rZT(3,220)=4;m%RtHS%rZT(3,221)=6
FTTower=0;FTTower(1,220)=50;FTTower(1,221)=100
LinAccET=0;MFHydro=0;LinAccEO=0
FrcONcRt=(/1000d0,0d0,0d0/);MomBNcRt=0
FrcFGagT=(/1.25d0,0d0,0d0/);MomFGagT=(/0d0,6.4d0,-.025d0/)
TwHtFLxt=1;TwHtFLyt=2;TwHtFLzt=3;TwHtMLxt=4;TwHtMLyt=5;TwHtMLzt=6
m%AllOuts=(/1.25d0,0d0,0d0,0d0,.025d0,6.4d0/)
I=1;t=0
'''
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); src=root/'probe.f90'; exe=root/'probe'; out=root/'probe.txt'
        src.write_text(stub+PROBE+'\nend program smoke\n')
        subprocess.run([compiler,'-std=f2008','-Wall','-Wextra','-fcheck=all',str(src),'-o',str(exe)],check=True,capture_output=True,text=True)
        subprocess.run([str(exe)],check=True,capture_output=True,text=True,
                       env={**os.environ,'OPENFAST_S07_DCM_PROBE':str(out)})
        rows=parse_records(out.read_text())
        result=audit_group(next(iter(rows.values())))
        assert len(rows)==1 and result['element_rows']==2
    return {'fortran_syntax_and_runtime':'PASS','independent_ledger':'PASS',
            'scope':'SYNTHETIC_STUB_NOT_OPENFAST_NATIVE','physical_pass':False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--selftest',action='store_true')
    ap.add_argument('--fortran-smoke',action='store_true')
    ap.add_argument('--source',type=Path)
    ap.add_argument('--out',type=Path)
    ap.add_argument('--audit',type=Path)
    args=ap.parse_args()
    if args.selftest: print(json.dumps(selftest(),indent=2));return
    if args.fortran_smoke: print(json.dumps(fortran_smoke(),indent=2));return
    if args.source:
        if not args.out or args.out.exists() or args.out.resolve()==args.source.resolve():
            raise ValueError('OUTPUT_MUST_BE_NEW_SEPARATE_FILE')
        result=patch(args.source.read_bytes())
        args.out.write_bytes(result)
        print(json.dumps({'source_sha256':OFFICIAL_SHA256,'patched_sha256':sha(result),
                          'status':'SOURCE_PATCH_ONLY_NOT_COMPILED'}))
    elif args.audit:
        groups=parse_records(args.audit.read_text())
        result=[{'time_s':k[0],**audit_group(v)} for k,v in sorted(groups.items())]
        print(json.dumps({'status':'SOURCE_LEDGER_QC_ONLY','probe_sha256':sha(args.audit.read_bytes()),'source_sha256':OFFICIAL_SHA256,'rows':result,'physical_pass':False},indent=2))
    else: ap.error('Use --selftest, --fortran-smoke, --source/--out, or --audit')

if __name__=='__main__': main()
