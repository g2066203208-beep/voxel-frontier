#!/usr/bin/env python3
"""S10 ODB-local-stress provenance preflight; never grants material-life PASS.

Consumes the existing s10_native_odb_local_stress_gate.py provisional manifest.
All source/log/review/material evidence is byte-checked, but review authorship,
native equilibrium, and physical error budgets are NOT authenticated here.
Never relabel UNVERIFIED_NATIVE_LOCAL_STRESS or produce N_allow.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import tempfile
from pathlib import Path

T057='c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db'
D400='22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
MAP={T057:'502fe65c94a8d060611e6b4293790ed3a5f48174a41b7732a3b221a5195e66fd',
     D400:'9850c1983a1bc69cc829f338260a31ff29b4e6ab86660749d453f9cc5791ff83'}
GROUP={'concrete':'concrete','longitudinal_rebar':'ordinary_rebar',
       'hoops_and_ties':'ordinary_rebar','PT':'prestressing_strand',
       'steel_tower':'structural_steel'}
GATES=('S01_MODEL_IDENTITY','S03_GRAVITY_PE_CONTACT','S04_LOCAL_STRESS_VV',
       'S07_DLC12_LOAD_IDENTITY','INTEGRATION_POINT_AND_BASIS',
       'INITIAL_MEAN_STRESS','MATERIAL_CURVE_DOMAIN')
SHA_FIELDS=('inp_sha256','odb_sha256','run_card_sha256',
            'source_map_sha256','source_sha256')

def insist(ok,code):
    if not ok: raise ValueError(code)

def digest(raw): return hashlib.sha256(raw).hexdigest()

def is_sha(x):
    return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)

def verify_file(root,item,label):
    insist(isinstance(item,dict) and is_sha(item.get('sha256')),'MISSING_EVIDENCE_SHA_'+label)
    insist(isinstance(item.get('path'),str) and item['path'] and
           not Path(item['path']).is_absolute(),'INVALID_EVIDENCE_PATH_'+label)
    base=Path(root).resolve()
    p=(base/item['path']).resolve()
    insist(base in p.parents and p.is_file(),'MISSING_OR_OUTSIDE_EVIDENCE_'+label)
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    insist(h.hexdigest()==item['sha256'],'EVIDENCE_BYTES_MISMATCH_'+label)
    return item['sha256']

def audit(raw,native,review,curve,map_raw,root,synthetic_map_sha=None):
    insist(all(isinstance(x,dict) for x in (native,review,curve)),'INVALID_MANIFEST')
    insist(native.get('status')=='NATIVE_EXTRACTION_QC_ONLY_PHYSICS_HOLD' and
           native.get('stress_owner')=='UNVERIFIED_NATIVE_LOCAL_STRESS' and
           native.get('initial_state')=='NEED_INDEPENDENT_NATIVE_REVIEW',
           'NATIVE_STRESS_MUST_REMAIN_UNVERIFIED')
    insist(native.get('inp_sha256') in MAP,'UNREGISTERED_INP_BRANCH')
    for k in SHA_FIELDS:
        insist(is_sha(native.get(k)),'INVALID_SHA_'+k)
        insist(review.get(k)==native[k],'REVIEW_IDENTITY_MISMATCH_'+k)
    insist(digest(raw)==native['source_sha256'],'STRESS_SOURCE_SHA_MISMATCH')
    expected=MAP[native['inp_sha256']] if synthetic_map_sha is None else synthetic_map_sha
    insist(digest(map_raw)==native['source_map_sha256']==expected,'SOURCE_MAP_SHA_MISMATCH')
    insist(native.get('stress_component')=='S11' and native.get('odb_stress_unit')=='Pa'
           and native.get('odb_time_unit')=='s','STRESS_COMPONENT_OR_UNITS')
    insist(native.get('stress_basis') in
           ('ODB_GLOBAL_S11','ODB_ELEMENT_LOCAL_S11','TRUSS_AXIAL_S11'),
           'STRESS_BASIS_NOT_LOCKED')
    insist(native.get('material_class') in GROUP.values(),'UNKNOWN_MATERIAL_CLASS')
    insist(native.get('stress_basis')!='TRUSS_AXIAL_S11' or
           native['material_class'] in ('ordinary_rebar','prestressing_strand'),
           'TRUSS_BASIS_WRONG_MATERIAL')
    samples=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    insist(len(samples)>=3 and set(samples[0])=={'time_s','stress_MPa'} and
           len(samples)==native.get('n_samples'),'STRESS_CSV_SCHEMA_OR_FRAME_COUNT')
    times=[]
    for row in samples:
        insist(None not in row and row.get('time_s') is not None and
               row.get('stress_MPa') is not None,'MALFORMED_CSV')
        t,s=float(row['time_s']),float(row['stress_MPa'])
        insist(math.isfinite(t) and math.isfinite(s),'NONFINITE_STRESS')
        times.append(t)
    dt=float(native.get('dt_s',float('nan')))
    insist(math.isfinite(dt) and dt>0 and all(
        abs(b-a-dt)<=max(1e-9,1e-7*dt) for a,b in zip(times,times[1:])),
        'TIME_GRID_MISMATCH')
    insist(abs(times[0]-float(native.get('time_start_s',float('nan'))))<1e-9 and
           abs(times[-1]-float(native.get('time_end_s',float('nan'))))<1e-9,
           'TIME_SPAN_MISMATCH')
    bindings=list(csv.DictReader(io.StringIO(map_raw.decode('utf-8-sig'))))
    matches=[r for r in bindings if r.get('native_instance_from_INP','').upper()==
             str(native.get('instance','')).upper()]
    insist(len(matches)==1,'SOURCE_INSTANCE_NOT_UNIQUE')
    b=matches[0]
    insist(GROUP.get(b.get('source_group'))==native['material_class'] and
           b.get('section_material_from_INP')==native.get('material_id') and
           b.get('native_elset_from_INP','').upper()==
           str(native.get('element_set','')).upper(),'MATERIAL_BINDING_MISMATCH')
    insist(b.get('height_candidate_element_label')==str(native.get('element_label')),
           'SOURCE_ELEMENT_CANDIDATE_MISMATCH')
    insist(not b.get('native_integration_point') and not b.get('native_stress_basis'),
           'SOURCE_MAP_CANNOT_CERTIFY_IP')
    insist(type(native.get('integration_point')) is int and
           native['integration_point']>0,'INVALID_INTEGRATION_POINT')
    logs=native.get('native_log_sha256')
    insist(isinstance(logs,dict) and set(logs)=={'dat','msg','sta','log'} and
           all(is_sha(x) for x in logs.values()),'INCOMPLETE_NATIVE_LOG_SHA')
    for ext in ('dat','msg','sta','log'):
        insist(review.get('native_log_sha256',{}).get(ext)==logs[ext],
               'REVIEW_LOG_MISMATCH_'+ext)
        insist(verify_file(root,review.get('native_logs',{}).get(ext),'LOG_'+ext)==logs[ext],
               'NATIVE_LOG_BYTES_MISMATCH_'+ext)
    for k in ('run_id','material_id','material_class','stress_location',
              'stress_basis','integration_point'):
        insist(review.get(k)==native.get(k),'REVIEW_LOCATION_MISMATCH_'+k)
    insist(review.get('reviewer') and review.get('review_date') and
           review.get('review_level')=='EXTERNAL_NATIVE_EVIDENCE_REVIEW_DECLARED',
           'REVIEW_DECLARATION_MISSING')
    gates=review.get('gate_evidence')
    insist(isinstance(gates,dict) and set(gates)==set(GATES),
           'INCOMPLETE_PHYSICAL_REVIEW_EVIDENCE')
    for g in GATES: verify_file(root,gates[g],g)
    insist(curve.get('material_class')==native['material_class'] and
           curve.get('material_id')==native['material_id'] and
           curve.get('model_ref')==review.get('material_model_ref'),
           'MATERIAL_CURVE_IDENTITY_MISMATCH')
    insist(curve.get('source_level') in
           ('PRIMARY_FULLTEXT_PAGE_REVIEWED','AUTHORIZED_STANDARD_PAGE_REVIEWED') and
           curve.get('page_locator') and curve.get('source_url') and
           curve.get('stress_unit')=='MPa' and curve.get('mean_stress_rule') in
           ('NONE_KEEP_MEAN','GOODMAN_TENSION_ONLY','QU2026_PT_GOODMAN'),
           'MATERIAL_CURVE_SOURCE_OR_UNITS_MISSING')
    insist(curve['mean_stress_rule']!='GOODMAN_TENSION_ONLY' or
           native['material_class'] in ('ordinary_rebar','structural_steel'),
           'GOODMAN_MATERIAL_MISMATCH')
    insist(curve['mean_stress_rule']!='QU2026_PT_GOODMAN' or
           native['material_class']=='prestressing_strand',
           'PT_GOODMAN_MATERIAL_MISMATCH')
    curve_sha=verify_file(root,curve.get('source_file'),'CURVE_SOURCE')
    insist(curve_sha==review.get('material_source_sha256'),
           'REVIEW_CURVE_SHA_MISMATCH')
    return {'status':'SOURCE_BYTES_CONSISTENT_REVIEW_AUTHENTICITY_UNVERIFIED',
            'physical_pass':False,'miner_admitted':False,
            'stress_owner':'UNVERIFIED_NATIVE_LOCAL_STRESS',
            'initial_state':'NEED_INDEPENDENT_NATIVE_REVIEW',
            'source_sha256':native['source_sha256'],
            'inp_sha256':native['inp_sha256'],'odb_sha256':native['odb_sha256'],
            'source_map_sha256':native['source_map_sha256'],
            'material_id':native['material_id'],'material_class':native['material_class'],
            'material_model_ref':curve['model_ref'],
            'material_source_sha256':curve_sha,
            'time_points':len(samples),'dt_s':dt,
            'verified_log_bytes':4,'declared_review_evidence_files':len(GATES),
            'hold':'Declared reviews cannot authenticate Abaqus equilibrium, PT mean state, mesh stress or S-N validity. No automatic rainflow/Miner production promotion.'}

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        def put(name,data):
            (root/name).write_bytes(data)
            return {'path':name,'sha256':digest(data)}
        raw=b'time_s,stress_MPa\n0,1\n0.1,3\n0.2,1\n'
        sm=('source_part,source_group,native_instance_from_INP,native_elset_from_INP,'
            'section_material_from_INP,height_candidate_element_label,native_integration_point,native_stress_basis\n'
            'SSEG_01,steel_tower,STEEL-1,SET_A,Q345,17,,\n').encode()
        logs={k:put('pilot.'+k,('SYNTH_'+k).encode()) for k in ('dat','msg','sta','log')}
        native=dict(status='NATIVE_EXTRACTION_QC_ONLY_PHYSICS_HOLD',
            stress_owner='UNVERIFIED_NATIVE_LOCAL_STRESS',
            initial_state='NEED_INDEPENDENT_NATIVE_REVIEW',inp_sha256=T057,
            odb_sha256='b'*64,run_card_sha256='c'*64,source_map_sha256=digest(sm),
            source_sha256=digest(raw),run_id='SYNTHETIC_ONLY',material_class='structural_steel',
            material_id='Q345',stress_component='S11',stress_basis='ODB_GLOBAL_S11',
            stress_location='SYNTHETIC_IP',instance='STEEL-1',element_set='SET_A',
            element_label=17,integration_point=1,n_samples=3,dt_s=.1,
            time_start_s=0,time_end_s=.2,odb_stress_unit='Pa',odb_time_unit='s',
            native_log_sha256={k:v['sha256'] for k,v in logs.items()})
        review={k:native[k] for k in SHA_FIELDS}
        review.update({k:native[k] for k in
                       ('run_id','material_id','material_class','stress_location',
                        'stress_basis','integration_point')})
        review.update(reviewer='SYNTHETIC_NOT_PERSON',review_date='2026-11-01',
            review_level='EXTERNAL_NATIVE_EVIDENCE_REVIEW_DECLARED',
            native_log_sha256=native['native_log_sha256'],native_logs=logs,
            material_model_ref='SYNTHETIC_CURVE',
            gate_evidence={k:put(k+'.txt',('SYNTH_'+k).encode()) for k in GATES})
        curve=dict(material_class='structural_steel',material_id='Q345',
            model_ref='SYNTHETIC_CURVE',source_level='PRIMARY_FULLTEXT_PAGE_REVIEWED',
            page_locator='SYNTHETIC',source_url='SYNTHETIC_TEST_ONLY',
            stress_unit='MPa',mean_stress_rule='NONE_KEEP_MEAN',
            source_file=put('curve.txt',b'SYNTHETIC_CURVE_NOT_REAL'))
        review['material_source_sha256']=curve['source_file']['sha256']
        def good(n=native,r=review,c=curve,src=raw):
            return audit(src,n,r,c,sm,root,synthetic_map_sha=digest(sm))
        ok=good()
        assert not ok['physical_pass'] and not ok['miner_admitted']
        negatives=[
            lambda:good(n=dict(native,stress_owner='VERIFIED_LOCAL_MATERIAL_STRESS')),
            lambda:good(src=raw+b'\n'),
            lambda:good(n=dict(native,inp_sha256='d'*64)),
            lambda:good(n=dict(native,material_id='HRB500')),
            lambda:good(n=dict(native,stress_basis='TRUSS_AXIAL_S11')),
            lambda:good(n=dict(native,dt_s=.2)),
            lambda:good(n=dict(native,odb_stress_unit='MPa')),
            lambda:good(r=dict(review,odb_sha256='0'*64)),
            lambda:good(r=dict(review,native_log_sha256={})),
            lambda:good(r=dict(review,gate_evidence={})),
            lambda:good(r=dict(review,material_source_sha256='0'*64)),
            lambda:good(c=dict(curve,material_class='concrete')),
            lambda:good(c=dict(curve,source_level='ABSTRACT_ONLY')),
            lambda:good(src=raw.replace(b'0.1,3',b'0.15,3'))]
        for i,fn in enumerate(negatives):
            try: fn()
            except (ValueError,TypeError): pass
            else: raise AssertionError('BAD_INPUT_ACCEPTED_'+str(i))
        (root/'pilot.dat').write_bytes(b'TAMPERED_LOG')
        try: good()
        except ValueError as e: assert 'EVIDENCE_BYTES_MISMATCH' in str(e)
        else: raise AssertionError('TAMPERED_LOG_ACCEPTED')
        return {'status':'PASS_SYNTHETIC_ONLY','negative_tests':len(negatives)+1,
                'physical_pass':False,'miner_admitted':False,
                'source_csv_sha256':digest(raw),'source_map_sha256':digest(sm)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    for k in ('stress-csv','native-manifest','review-receipt','material-curve',
              'source-map','evidence-root','output'):
        p.add_argument('--'+k,type=Path)
    a=p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),sort_keys=True))
        return
    keys=('stress_csv','native_manifest','review_receipt','material_curve',
          'source_map','evidence_root','output')
    if any(getattr(a,k) is None for k in keys):
        p.error('seven input/output paths required (or --self-test)')
    out=audit(a.stress_csv.read_bytes(),json.loads(a.native_manifest.read_text()),
              json.loads(a.review_receipt.read_text()),
              json.loads(a.material_curve.read_text()),a.source_map.read_bytes(),
              a.evidence_root)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('S10_SOURCE_PREFLIGHT_ONLY_NOT_PHYSICS_OR_MINER_PASS')

if __name__=='__main__': main()
