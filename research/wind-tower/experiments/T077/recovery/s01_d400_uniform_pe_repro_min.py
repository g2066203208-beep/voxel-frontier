#!/usr/bin/env python3
"""S01-D400 uniform rebar Pe/G1 provisional child; STATIC ONLY, not code/native PASS."""
import argparse
import hashlib
import zipfile
from pathlib import Path

NAME = 'S01_D400_Pe_G1_INSTRUMENTED_DIAGNOSTIC_ONLY.inp'
SRC = '4c84c61ea07138428d4c0a8f742a9ab6e55725c49d16a94f5d9eaa8f7d9d3d29'
DST = '22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
HEADER = (
    '** S01-D400-Pe uniform ordinary rebar material ID: PROVISIONAL / NOT FROZEN.\n'
    '** Only HOOP and TIE section material references changed HRB335 -> HRB400.\n'
    '** All geometry, longitudinal bars, PT Pe, contacts, equations, loads unchanged.\n'
    '** HRB335 material definition retained UNUSED for byte-traceability.\n'
    '** NB/T10907 4.2/6.4/8 full authorized clauses NOT READ; no native Abaqus.\n'
    '** Original G1 diagnostic SHA256: ' + SRC + '\n'
)
OLD = [f'*Solid Section, elset=SET_{x}_ALL, material=HRB335_T057' for x in ('HOOP','TIE')]
NEW = [x.replace('HRB335_T057','HRB400_D400_DIAGNOSTIC') for x in OLD]
sha = lambda b: hashlib.sha256(b).hexdigest()

def make(raw):
    assert sha(raw) == SRC, 'fail-closed source SHA'
    text = raw.decode('utf-8')
    assert all(text.count(x) == 1 for x in OLD)
    assert all(text.count(x) == 0 for x in NEW)
    assert text.count('*Solid Section, elset=SET_ALL, material=HRB400_D400_DIAGNOSTIC') == 31
    assert text.count('PT_36x15p2-1.SET_PT_ALL_ELEMS, 985951362.9616609, ') == 1
    assert text.count('*Equation\n') == 108 and text.count('*Contact Output\n') == 1
    out = HEADER + text
    for old,new in zip(OLD,NEW): out = out.replace(old,new,1)
    restored = out.removeprefix(HEADER)
    for old,new in zip(OLD,NEW): restored = restored.replace(new,old,1)
    assert restored.encode() == raw, 'unexpected byte change'
    assert sha(out.encode()) == DST, 'child SHA mismatch'
    return out.encode()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--zip',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    assert not a.out.exists(), 'refuse overwrite'
    with zipfile.ZipFile(a.zip) as z:
        names=[n for n in z.namelist() if Path(n).name == NAME]
        assert len(names)==1, 'expected one named INP'
        data=make(z.read(names[0]))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(data)
    print('STATIC-ONLY S01 HOLD; bytes=',len(data),'sha256=',sha(data))

if __name__ == '__main__': main()
