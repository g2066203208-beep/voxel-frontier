#!/usr/bin/env python3
"""S01 PT initial-stress axial compatibility oracle; static reduced-order only, NOT Abaqus."""
import argparse, csv, hashlib, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SOURCE_SHA = 'd34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e'
META_SHA = '2f016db75ff62b14ffd12465646f9e8bd37421d9ba4eebda8e2bd4afb2c82aa6'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def solve(rows, m, mode, gravity, n):
    kpt = m['pt_E_Pa'] * m['pt_area_m2'] / m['pt_length_m']
    p0 = m['pt_initial_stress_Pa'] * m['pt_area_m2']
    top_mass = m['RNA_mass_kg'] + m['steel_tower_mass_kg_ideal_circle']
    slices = []
    for r in rows:
        dy = (float(r['y1_m']) - float(r['y0_m'])) / n
        for j in range(n):
            f = (j + .5) / n
            ri = float(r['ri0_m']) * (1-f) + float(r['ri1_m']) * f
            ro = float(r['ro0_m']) * (1-f) + float(r['ro1_m']) * f
            A = math.pi * (ro*ro - ri*ri)
            As, Ec, Es = float(r['As_long_m2']), float(r['Ec_Pa']), m['rebar_E_Pa']
            if mode == 'concrete_gross_only':
                ea, mu = Ec*A, m['rho_concrete_kg_m3']*A
            elif mode == 'embedded_no_host_subtraction':
                ea, mu = Ec*A + Es*As, m['rho_concrete_kg_m3']*A + m['rho_rebar_kg_m3']*As
            else:
                ea, mu = Ec*(A-As) + Es*As, m['rho_concrete_kg_m3']*(A-As) + m['rho_rebar_kg_m3']*As
            slices.append((dy, ea, mu*dy))
    kc = 1 / sum(dy/ea for dy,ea,_ in slices)
    above, dg = top_mass, 0.
    for dy,ea,dm in reversed(slices):
        dg += m['g_m_s2'] * (above + dm/2) * dy/ea
        above += dm
    if not gravity: dg = 0.
    pf = (p0 - kpt*dg) / (1 + kpt/kc)
    u = -pf/kc - dg
    assert abs(pf - (p0+kpt*u)) < 1e-5
    return dict(mode=mode, gravity_on=gravity, Kc_GN_m=kc/1e9,
                gravity_shortening_mm=dg*1000, PT_after_equilibrium_MN=pf/1e6,
                PT_input_MN=p0/1e6, PT_delta_pct=100*(pf/p0-1),
                top_displacement_mm=u*1000)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True, help='New output CSV; existing files refused')
    a = p.parse_args()
    source = ROOT/'S01_PT_AXIAL_31SEG_SOURCE_20261026.csv'
    meta = ROOT/'S01_PT_AXIAL_SOURCE_META_20261026.json'
    assert sha(source) == SOURCE_SHA, '31-segment input SHA mismatch'
    assert sha(meta) == META_SHA, 'metadata SHA mismatch'
    rows = list(csv.DictReader(source.open(newline='')))
    assert len(rows) == 31
    m = json.loads(meta.read_text())
    modes = ['concrete_gross_only','embedded_no_host_subtraction','composite_with_host_subtraction']
    result = [solve(rows,m,mode,gravity,200) for mode in modes for gravity in (False,True)]
    finer = [solve(rows,m,mode,gravity,400) for mode in modes for gravity in (False,True)]
    err = max(abs(x['PT_after_equilibrium_MN']-y['PT_after_equilibrium_MN']) for x,y in zip(result,finer))
    assert err < 0.0001, err
    out = Path(a.out)
    with out.open('x',newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    print('STATIC_ONLY; NOT_ABAQUS; S01_HOLD')
    print('200_vs_400_max_PT_difference_MN=',err)
    for r in result: print(r['mode'],r['gravity_on'],r['PT_after_equilibrium_MN'])

if __name__ == '__main__': main()
