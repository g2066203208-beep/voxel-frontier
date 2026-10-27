#!/usr/bin/env python3
"""Build 30 real interface geometry + gravity force-gradient diagnostics from S01/T074 CSV.

SOURCE-LEVEL static diagnostic, not a section-force-to-joint reconstruction or Abaqus run.
All units: m, m2, m3, kN, kN/m3. Python standard library only.
"""
import argparse
import csv
import hashlib
import math
from pathlib import Path

FIELDS = ('joint','z_joint_m','below_segment','above_segment','z_below_gage_m',
          'z_above_gage_m','distance_below_m','distance_above_m','gage_span_m',
          'radius_inner_joint_m','radius_outer_joint_m','annulus_volume_between_gages_m3',
          'Fz_below_gravity_kN','Fz_above_gravity_kN','Fz_above_minus_below_kN',
          'inferred_effective_unit_weight_kN_m3')


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def area_at(g, z):
    y0, y1 = float(g['y0_m']), float(g['y1_m'])
    if not y0 - 1e-7 <= z <= y1 + 1e-7:
        raise ValueError('point outside segment')
    t = (z-y0)/(y1-y0)
    ri = float(g['ri0_m']) + t*(float(g['ri1_m'])-float(g['ri0_m']))
    ro = float(g['ro0_m']) + t*(float(g['ro1_m'])-float(g['ro0_m']))
    if not 0 < ri < ro:
        raise ValueError('invalid annulus')
    return math.pi*(ro*ro-ri*ri)


def volume(g, a, b):
    # radii vary linearly, so A(z) is quadratic: Simpson's rule is exact
    return (b-a)*(area_at(g,a)+4*area_at(g,(a+b)/2)+area_at(g,b))/6


def build(geometry, gravity):
    g, w = read_csv(geometry), read_csv(gravity)
    if len(g)!=31 or len(w)!=31:
        raise ValueError('need exactly 31 concrete segments and 31 gages')
    result=[]
    for i in range(30):
        lo, hi, wglo, wghi = g[i], g[i+1], w[i], w[i+1]
        if any(x['segment'] != f'CSEG_{j:02d}' for x,j in
               ((lo,i+1),(hi,i+2),(wglo,i+1),(wghi,i+2))):
            raise ValueError('segment identity/order mismatch')
        zj = float(lo['y1_m'])
        if abs(zj-float(hi['y0_m']))>1e-7:
            raise ValueError('noncontiguous joint height')
        for side in ('ri','ro'):
            if abs(float(lo[f'{side}1_m'])-float(hi[f'{side}0_m']))>1e-7:
                raise ValueError('interface radius mismatch')
        zb, za = float(wglo['gage_z_m']), float(wghi['gage_z_m'])
        if not zb < zj < za:
            raise ValueError('gage does not bracket interface')
        v = volume(lo,zb,zj)+volume(hi,zj,za)
        dfz = float(wghi['Fz_kN'])-float(wglo['Fz_kN'])
        if not math.isfinite(dfz) or v<=0:
            raise ValueError('invalid gravity gradient')
        row=(f'J{i+1:02d}',zj,lo['segment'],hi['segment'],zb,za,
             zj-zb,za-zj,za-zb,float(lo['ri1_m']),float(lo['ro1_m']),
             v,float(wglo['Fz_kN']),float(wghi['Fz_kN']),dfz,dfz/v)
        if not all(math.isfinite(x) for x in row if isinstance(x,float)):
            raise ValueError('nonfinite output')
        result.append(row)
    return result



# S06 six-component *static* source-level wrench comparison.  This does not
# reconstruct forces at a joint or identify aerodynamic/inertial ownership.
# OpenFAST TwHt local axes deform with the tower; dynamic histories MUST first
# be rotated into a single frame using actual orientation time histories.
WRENCH_FIELDS = ('joint','below_segment','above_segment','z_below_gage_m',
                 'z_above_gage_m','gage_span_m','delta_Fx_kN',
                 'delta_Fy_kN','delta_Fz_kN','delta_Mx_at_below_kNm',
                 'delta_My_at_below_kNm','delta_Mz_at_below_kNm',
                 'My_below_raw_kNm','My_above_raw_kNm',
                 'frame_policy')


def wrench_difference(lower, upper, dz):
    """Upper minus lower cut wrench, upper transported to lower cut.

    Wrench transport: M_upper@lower = M_upper + (0,0,dz) x F_upper.
    This is algebra on SAME-ORIENTATION, SAME-SIGN, COMMON-FRAME data.
    The result is NOT a proven external force/inertia decomposition.
    """
    if not math.isfinite(dz) or dz <= 0:
        raise ValueError('nonpositive or nonfinite gage span')
    f = ('Fx_kN','Fy_kN','Fz_kN')
    m = ('Mx_kNm','My_kNm','Mz_kNm')
    lo = [float(lower[c]) for c in f + m]
    hi = [float(upper[c]) for c in f + m]
    if not all(math.isfinite(x) for x in lo + hi):
        raise ValueError('nonfinite wrench component')
    return (hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2],
            hi[3]-dz*hi[1]-lo[3],
            hi[4]+dz*hi[0]-lo[4],
            hi[5]-lo[5])


def build_wrench(gravity, joint_rows):
    w = read_csv(gravity)
    if len(w) != 31 or len(joint_rows) != 30:
        raise ValueError('expected 31 gravity gages and 30 joints')
    out = []
    for i, j in enumerate(joint_rows):
        a,b=w[i],w[i+1]
        if (a['segment'],b['segment']) != (j[2],j[3]):
            raise ValueError('wrench segment identity mismatch')
        zb,za=float(a['gage_z_m']),float(b['gage_z_m'])
        if abs(zb-j[4]) > 1e-8 or abs(za-j[5]) > 1e-8:
            raise ValueError('wrench gage height mismatch')
        df=wrench_difference(a,b,za-zb)
        if abs(df[2]-j[14]) > 1e-7:
            raise ValueError('gravity axial difference mismatch')
        out.append((j[0],j[2],j[3],zb,za,za-zb,
                    *df,float(a['My_kNm']),float(b['My_kNm']),
                    'STATIC_COMMON_FRAME_ASSUMED'))
    return out


def test_wrench():
    a={'Fx_kN':'10','Fy_kN':'7','Fz_kN':'-100',
       'Mx_kNm':'30','My_kNm':'100','Mz_kNm':'3'}
    b=dict(a,Mx_kNm='44',My_kNm='80')
    assert all(abs(x)<1e-12 for x in wrench_difference(a,b,2.))
    # A linearly varying lateral force creates a nonzero distributed
    # resultant and a 3 kN*m couple about the lower cut (not zero).
    b['Fx_kN']='13';b['My_kNm']='77';b['Fz_kN']='-90'
    v=wrench_difference(a,b,2.)
    assert all(abs(x-y)<1e-12 for x,y in zip(v,(3,0,10,0,3,0)))
    for bad in (0.,-1.,float('nan')):
        try: wrench_difference(a,b,bad)
        except ValueError: pass
        else: raise AssertionError('must reject invalid span')
    b['Fx_kN']='nan'
    try: wrench_difference(a,b,2.)
    except ValueError: pass
    else: raise AssertionError('must reject nonfinite wrench')


def test():
    test_wrench()
    g={'y0_m':'0','y1_m':'2','ri0_m':'1','ri1_m':'1',
       'ro0_m':'2','ro1_m':'2'}
    assert abs(volume(g,0,2)-6*math.pi)<1e-12
    # Tapered annulus: A(z) quadratic; Simpson integral equals analytic polynomial integral.
    g['ri1_m']='1.2';g['ro1_m']='2.2'
    expected=math.pi*(2*(4-1)+(2*2*.2-2*1*.2)*2/2 + (.2**2-.2**2)*8/3)
    assert abs(volume(g,0,2)-expected)<1e-12
    try:
        area_at(g,3)
    except ValueError:
        pass
    else:
        raise AssertionError('must reject extrapolation')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--geometry',type=Path,required=True)
    p.add_argument('--gravity',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--wrench-output',type=Path,default=None,
                   help='optional static same-frame six-component gage difference CSV')
    args=p.parse_args()
    test()
    rows=build(args.geometry,args.gravity)
    with args.output.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(FIELDS)
        for r in rows:
            writer.writerow([f'{v:.9f}' if isinstance(v,float) else v for v in r])
    if args.wrench_output is not None:
        wrows=build_wrench(args.gravity,rows)
        with args.wrench_output.open('w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f,lineterminator='\\n')
            writer.writerow(WRENCH_FIELDS)
            for r in wrows:
                writer.writerow([f'{v:.9f}' if isinstance(v,float) else v for v in r])
        print('S06 static six-component: joints=%d; max_abs_dFx_kN=%.12g; max_abs_dFy_kN=%.12g; max_abs_dMx_kNm=%.12g; max_abs_dMy_kNm=%.12g; max_abs_dMz_kNm=%.12g' %
              (len(wrows),max(abs(r[6]) for r in wrows),max(abs(r[7]) for r in wrows),
               max(abs(r[9]) for r in wrows),max(abs(r[10]) for r in wrows),
               max(abs(r[11]) for r in wrows)))
        print(args.wrench_output.name,hashlib.sha256(args.wrench_output.read_bytes()).hexdigest())
    gammas=[r[-1] for r in rows]
    print('joints=30; min_gamma=%.9f; max_gamma=%.9f; mean_gamma=%.9f; max_span_m=%.9f' %
          (min(gammas),max(gammas),sum(gammas)/len(gammas),max(r[8] for r in rows)))
    for path in (args.geometry,args.gravity,args.output):
        print(path.name,hashlib.sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':
    main()
