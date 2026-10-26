#!/usr/bin/env python3
"""Inverse Pe input sensitivity for a future S03 pilot. NOT native Abaqus or code PASS."""
import argparse, csv, json
from pathlib import Path
from s01_pt_axial_compatibility_oracle import solve, sha, SOURCE_SHA, META_SHA
ROOT = Path(__file__).resolve().parent
MODES = ('concrete_gross_only','embedded_no_host_subtraction','composite_with_host_subtraction')

def invert(rows, m, mode, gravity, subdivisions):
    forward = solve(rows,m,mode,gravity,subdivisions)
    kc = forward['Kc_GN_m']*1e9
    dg = forward['gravity_shortening_mm']/1000
    area = m['pt_area_m2']
    kp = m['pt_E_Pa']*area/m['pt_length_m']
    target = m['pt_initial_stress_Pa']*area
    p_in = target*(1+kp/kc)+kp*dg
    p_check = (p_in-kp*dg)/(1+kp/kc)
    return dict(mode=mode,gravity_on=gravity,Kc_GN_per_m=kc/1e9,
        Kpt_MN_per_m=kp/1e6,gravity_only_shortening_mm=dg*1000,
        target_Peq_MN=target/1e6,required_input_P_MN=p_in/1e6,
        required_input_sigma_MPa=p_in/area/1e6,
        increase_vs_existing_input_MPa=(p_in/area-m['pt_initial_stress_Pa'])/1e6,
        increase_vs_existing_input_pct=100*(p_in/target-1),
        forward_recomputed_Peq_MN=p_check/1e6,
        inverse_forward_residual_N=p_check-target,
        evidence='REDUCED_ORDER_PILOT_ONLY_NOT_NATIVE_OR_CODE_PASS')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True,help='New output CSV; existing files refused')
    args=p.parse_args()
    source=ROOT/'S01_PT_AXIAL_31SEG_SOURCE_20261026.csv'
    meta_file=ROOT/'S01_PT_AXIAL_SOURCE_META_20261026.json'
    assert sha(source)==SOURCE_SHA,'source CSV SHA mismatch'
    assert sha(meta_file)==META_SHA,'source metadata SHA mismatch'
    rows=list(csv.DictReader(source.open(newline='')))
    assert len(rows)==31
    m=json.loads(meta_file.read_text())
    assert m['source_inp_sha256']=='22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
    result=[invert(rows,m,mode,g,200) for mode in MODES for g in (False,True)]
    finer=[invert(rows,m,mode,g,400) for mode in MODES for g in (False,True)]
    err=max(abs(x['required_input_P_MN']-y['required_input_P_MN']) for x,y in zip(result,finer))
    assert err<1e-4,err
    assert max(abs(x['inverse_forward_residual_N']) for x in result)<1e-5
    with Path(args.out).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(result[0]));writer.writeheader();writer.writerows(result)
    print('S01 HOLD / STATIC INVERSE PILOT ONLY / NO ABAQUS')
    print('SOURCE_CSV_SHA',SOURCE_SHA,'META_SHA',META_SHA,'200_vs_400_max_MN',err)
    for r in result:
        print(r['mode'],r['gravity_on'],f"sigma_input_MPa={r['required_input_sigma_MPa']:.8f}")
if __name__=='__main__':main()
