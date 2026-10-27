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


def test():
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
    args=p.parse_args()
    test()
    rows=build(args.geometry,args.gravity)
    with args.output.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(FIELDS)
        for r in rows:
            writer.writerow([f'{v:.9f}' if isinstance(v,float) else v for v in r])
    gammas=[r[-1] for r in rows]
    print('joints=30; min_gamma=%.9f; max_gamma=%.9f; mean_gamma=%.9f; max_span_m=%.9f' %
          (min(gammas),max(gammas),sum(gammas)/len(gammas),max(r[8] for r in rows)))
    for path in (args.geometry,args.gravity,args.output):
        print(path.name,hashlib.sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':
    main()
