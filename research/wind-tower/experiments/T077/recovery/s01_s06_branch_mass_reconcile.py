#!/usr/bin/env python3
"""S01/S06 immutable-source mass reconciliation; static arithmetic, NOT solver V&V.

Reproduces 2026-10-27 reported R335/D400 branch four-row *counterfactual*
from the recorded component ledger. Optional --tower-dat independently integrates
70 OpenFAST tower stations and fails closed on SHA/version/mass mismatch.
No original T057/T070 or D400 INP mutation; no Abaqus/OpenFAST production RUN.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

OPENFAST_TOWER_PATH = 'S06_C02R3R2_158M_Tower_RECOVERED_20261026.dat'
OPENFAST_SHA256_REGISTERED = 'f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983'
T057_INP_SHA256_REGISTERED = 'c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db'
T070_INP_SHA256_REGISTERED = '9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9'
D400_INP_SHA256_REGISTERED = '22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'

# kg: registered static integrations. These are INPUT FACTS, not fresh INP integration.
REGISTERED = {
    'openfast_tower_without_RNA_kg': 1923663.610690804,
    'concrete_kg': 1617978.893,
    'steel_tower_kg': 191094.168,
    'r335_longitudinal_kg': 75831.702110169,
    'd400_longitudinal_kg': 253358.224310,
    'hoops_kg': 64477.253,
    'ties_kg': 657.757,
    'PT_kg': 35449.344,
    'rho_steel_kg_m3': 7850.0,
    'rho_concrete_kg_m3': 2400.0,
}
REFERENCE = 'research/wind-tower/experiments/T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md'

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def read_openfast_tower(path: Path):
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    count = next((int(s.split()[0]) for s in lines if 'NTwInpSt' in s), None)
    if count != 70:
        raise ValueError('EXPECTED 70 NTwInpSt; got %r' % count)
    ix = next((i for i, s in enumerate(lines) if s.strip().startswith('HtFract') and 'TMassDen' in s), None)
    if ix is None: raise ValueError('Missing HtFract/TMassDen table header')
    rows = []
    for line in lines[ix+1:]:
        words = line.split()
        if len(words) != 10: continue
        try: values = [float(k) for k in words]
        except ValueError: continue
        rows.append(values)
        if len(rows) == count: break
    if len(rows) != 70: raise ValueError('Need exactly 70 tower rows')
    z = [158.0*r[0] for r in rows]
    d = [r[1] for r in rows]
    if not all(math.isfinite(v) for v in z+d): raise ValueError('non-finite input')
    if any(dv <= 0 for dv in d): raise ValueError('non-positive line mass')
    if abs(z[0]) > 1e-5 or abs(z[-1]-158.0) > 1e-5: raise ValueError('wrong tower height endpoints')
    if any(b <= a for a,b in zip(z,z[1:])): raise ValueError('heights not strictly increasing')
    total = sum((b-a)*(da+db)/2 for a,b,da,db in zip(z,z[1:],d,d[1:]))
    return {'stations':70,'tower_height_m':158.0,'mass_kg':total}

def calculate(reference_mass_kg: float):
    o = REGISTERED
    common = o['concrete_kg']+o['steel_tower_kg']+o['hoops_kg']+o['ties_kg']+o['PT_kg']
    out=[]
    for branch,L in [('R335',o['r335_longitudinal_kg']),('D400',o['d400_longitudinal_kg'])]:
        gross=common+L
        displaced=(L+o['hoops_kg']+o['ties_kg'])*o['rho_concrete_kg_m3']/o['rho_steel_kg_m3']
        for name,val in [('as_model_double_count',gross),('counterfactual_replaced_host_concrete',gross-displaced)]:
            out.append({'branch':branch,'mass_scope':name,'mass_t':val/1000,
                        'difference_to_openfast_t':(val-reference_mass_kg)/1000,
                        'difference_pct':100*(val/reference_mass_kg-1),
                        'host_displacement_applied_kg':displaced if name.startswith('counterfactual') else 0})
    return out

def self_test():
    rows=calculate(REGISTERED['openfast_tower_without_RNA_kg'])
    checks={('R335','as_model_double_count'):3.213946,
            ('R335','counterfactual_replaced_host_concrete'):0.973528,
            ('D400','as_model_double_count'):12.442510,
            ('D400','counterfactual_replaced_host_concrete'):7.380620}
    for row in rows:
        key=(row['branch'],row['mass_scope'])
        if abs(row['difference_pct']-checks[key])>=0.000003:
            raise AssertionError('reconciliation mismatch %s: %.9f'%(key,row['difference_pct']))
    assert abs(REGISTERED['d400_longitudinal_kg']-REGISTERED['r335_longitudinal_kg']-177526.522199831)<0.001
    # Synthetic data tests the 70-station parser; it is not a real source download.
    from tempfile import TemporaryDirectory
    fake=['70 NTwInpSt',
          'HtFract TMassDen TwFAStif TwSSStif TwGJStff TwEAStff TwFAIner TwSSIner TwFAcgOf TwSScgOf',
          '(-) (kg/m) (N m^2) (N m^2) (N m^2) (N) (kg m) (kg m) (m) (m)']
    fake+=['%.12f 12000 1 1 1 1 1 1 0 0'%(i/69) for i in range(70)]
    with TemporaryDirectory() as td:
        p=Path(td)/'synthetic.dat'
        p.write_text('\n'.join(fake)+'\n',encoding='utf-8')
        r=read_openfast_tower(p)
        assert abs(r['mass_kg']-12000*158)<0.01
    print('SELF_TEST_PASS: arithmetic + synthetic 70-station parsing; NOT Abaqus/OpenFAST')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tower-dat',type=Path,help='Exact recovered OpenFAST 70-station source; SHA enforced')
    ap.add_argument('--out-dir',type=Path,help='NEW output directory; must not exist')
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test:
        self_test();return
    if args.out_dir is None: ap.error('--out-dir is required')
    if args.out_dir.exists(): raise SystemExit('REFUSE: output exists')
    input_grade='REGISTERED_MASS_LEDGER_ONLY_NO_SOURCE_REHASH'
    mass=REGISTERED['openfast_tower_without_RNA_kg']
    tower_input=None
    if args.tower_dat:
        if not args.tower_dat.is_file(): raise SystemExit('REFUSE: no tower source file')
        actual=sha256(args.tower_dat)
        if actual != OPENFAST_SHA256_REGISTERED:
            raise SystemExit('REFUSE: tower source SHA256 mismatch '+actual)
        tower_input=read_openfast_tower(args.tower_dat)
        if abs(tower_input['mass_kg']-mass)>0.02:
            raise SystemExit('REFUSE: tower input mass mismatch %.9f vs %.9f'%(tower_input['mass_kg'],mass))
        mass=tower_input['mass_kg']
        input_grade='DIRECT_OPENFAST_RAW_SHA_AND_MASS_VERIFIED'
    rows=calculate(mass)
    args.out_dir.mkdir(parents=True,exist_ok=False)
    csv_path=args.out_dir/'S01_S06_R335_D400_BRANCH_MASS_RECONCILED.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    record={'source_grade':input_grade,
       'references':{'main_record':REFERENCE,'source_openfast':OPENFAST_TOWER_PATH},
       'source_sha256_registered_not_rehashed_unless_tower_dat_supplied':{
           'openfast':OPENFAST_SHA256_REGISTERED,'T057':T057_INP_SHA256_REGISTERED,
           'T070':T070_INP_SHA256_REGISTERED,'D400':D400_INP_SHA256_REGISTERED},
       'registered_component_inputs_kg':REGISTERED,
       'optional_openfast_direct_verification':tower_input,
       'assumptions':['RNA excluded','R335 shares D400 host/steel-tower/hoop/tie/PT mass: counterfactual, not exact T057 mass',
         'gross FE input double counts embedded rebar/concrete volume',
         'host-displacement case is NOT actual INP mass',
         'fixed 2400/7850 densities; tower input original generator unknown'],
       'numerical_error_budget':'float and printed component rounding only; input INP integrals not independently rerun',
       'physical_error_budget':'NEED_ESTIMATE: true T057 host/hoop/tie/PT mass, stiffness, contacts, PT equilibrium, RNA/modal dynamics',
       'status':'STATIC_ARITHMETIC_ONLY_0_OF_12_PASS','native_abaqus':'NOT_RUN','seismic_results':0,
       'fig':'NONE','tab':csv_path.name,'rows':rows}
    (args.out_dir/'S01_S06_R335_D400_BRANCH_MASS_RECONCILED.json').write_text(
        json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result_csv':str(csv_path),'evidence_level':input_grade,
                      'gross_R335_pct':rows[0]['difference_pct'],'gross_D400_pct':rows[2]['difference_pct']},ensure_ascii=False))

if __name__=='__main__':main()
