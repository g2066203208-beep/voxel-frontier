# -*- coding: utf-8 -*-
"""REV22 assembly import verification. Run in Abaqus/CAE Python, not stock Python.
This imports mesh parts, not native CAD geometry. Never changes the source INP.
Usage: abaqus cae noGUI=import_rev22_assembly.py -- /absolute/path/to/input.inp /absolute/path/to/new.cae
No solver submission. The saved CAE is a review copy, not a verified solver equivalent.
"""
from __future__ import print_function
import os, sys, hashlib, re, json
from abaqus import mdb

EXPECTED_SHA = 'e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5'
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args) != 2:
    raise RuntimeError('Require source INP and new destination CAE')
src, dst = map(os.path.abspath,args)
if not dst.lower().endswith('.cae') or os.path.exists(dst):
    raise RuntimeError('Require a NEW .cae path; never overwrite')
if not os.path.isdir(os.path.dirname(dst)):
    raise RuntimeError('Destination directory must exist')
raw = open(src,'rb').read()
if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
    raise RuntimeError('Source SHA mismatch: do not import wrong revision')
deck = raw.decode('ascii')
parts = re.findall(r'^\*Part,\s*name=([^,\r\n]+)',deck,re.M|re.I)
instances = re.findall(r'^\*Instance,\s*name=([^,\r\n]+),\s*part=([^,\r\n]+)',deck,re.M|re.I)
expected = dict((i.strip().upper(),p.strip().upper()) for i,p in instances)
if len(parts)!=100 or len(expected)!=100:
    raise RuntimeError('Unexpected source assembly topology')
name='HE_REV22_ASSEMBLY_REVIEW'
if name in mdb.models:
    raise RuntimeError('Review model name already exists; run in a fresh CAE session')
model=mdb.ModelFromInputFile(name=name,inputFileName=src)
assembly=model.rootAssembly
assembly.regenerate()
actual_parts=sorted(str(x).upper() for x in model.parts.keys())
actual_instances=dict((str(k).upper(),str(v.partName).upper()) for k,v in assembly.instances.items())
expected_parts=sorted(x.strip().upper() for x in parts)
report={'source_sha256':EXPECTED_SHA,'source_part_count':100,'source_instance_count':100,
        'imported_part_count':len(actual_parts),'imported_instance_count':len(actual_instances),
        'missing_parts':sorted(set(expected_parts)-set(actual_parts)),
        'extra_parts':sorted(set(actual_parts)-set(expected_parts)),
        'missing_instances':sorted(set(expected)-set(actual_instances)),
        'extra_instances':sorted(set(actual_instances)-set(expected)),
        'instance_part_mismatches':sorted(k for k in expected if k in actual_instances and expected[k]!=actual_instances[k]),
        'parts':[{'name':str(k),'nodes':len(v.nodes),'elements':len(v.elements),'geometry_cells':len(v.cells),'geometry_edges':len(v.edges)} for k,v in model.parts.items()],
        'scope':'mesh assembly inspection only; unsupported keywords, loads, interactions and solver equivalence not certified'}
ok=actual_parts==expected_parts and actual_instances==expected
report['assembly_identity']='PASS' if ok else 'FAIL'
receipt=dst+'.assembly-audit.json'
if os.path.exists(receipt):
    raise RuntimeError('Receipt already exists; choose new destination')
with open(receipt,'w') as f:
    json.dump(report,f,indent=2)
if not ok:
    raise RuntimeError('Assembly identity changed during import; CAE NOT saved; see receipt')
mdb.saveAs(pathName=dst)
print('ASSEMBLY_IDENTITY_PASS',len(actual_parts),len(actual_instances),dst)
print('Mesh parts only. Original INP remains authoritative for solver; no analysis submitted.')
