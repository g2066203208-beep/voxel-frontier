#!/usr/bin/env python3
"""GNU real32 arithmetic probe against SHA-locked original 2 s G/T/E log.

Not an OpenFAST/Abaqus solver, not wind-only load ownership or physical PASS.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import tempfile
import zipfile

ZIP_SHA = '983bce8ca81981ff5fd00e5261dbfb2c0b6e18b074aa4eb1ff425e6851fb9735'
RAW_SHA = '77f247d7e0b66997041ffbba70c859bdd38fd345eb303b18b78c6599fa2caa92'
RAW_NAME = 's07_native_dcm_raw.log.gz'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def synthetic():
    g = [0.0]*24
    t = [0.0]*20
    t[2] = 1e8
    t[5] = 1e8
    lines = ['G 0.1875 220 ' + ' '.join(map(str,g)),
             'T 0.1875 220 1120 ' + ' '.join(map(str,t))]
    for j in range(901):
        e = [0.0]*14
        e[1] = 1.0
        if j == 0:
            e[2] = 2.0
            e[11] = 2.0
        if j == 1:
            e[2] = -1e8
            e[11] = -1e8
        lines.append(f'E 0.1875 220 {220+j} ' + ' '.join(map(str,e)))
    return '\n'.join(lines)+'\n'

def validate(block):
    lines = block.splitlines()
    if len(lines) != 903:
        raise ValueError('GTE_ROW_COUNT_HOLD')
    for i, line in enumerate(lines):
        p = line.split()
        tag = 'G' if i==0 else 'T' if i==1 else 'E'
        node = 1120 if i==1 else 218+i
        expected = 27 if i==0 else 24 if i==1 else 18
        if len(p)!=expected or p[0]!=tag or p[2]!='220':
            raise ValueError('GTE_TAG_FIELD_HOLD')
        if i>0 and int(p[3])!=node:
            raise ValueError('GTE_NODE_HOLD')
        if abs(float(p[1])-.1875)>1e-12:
            raise ValueError('GTE_TIME_HOLD')
        for s in p[3 if i==0 else 4:]:
            if not math.isfinite(float(s)):
                raise ValueError('GTE_NONFINITE_HOLD')
    return [float(x) for x in lines[0].split()[3:]]

def extract(archive):
    b = Path(archive).read_bytes()
    if sha(b)!=ZIP_SHA:
        raise ValueError('ORIGINAL_ARTIFACT_SHA256_HOLD')
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        if z.testzip() is not None:
            raise ValueError('ORIGINAL_ZIP_CRC_HOLD')
        raw = gzip.decompress(z.read(RAW_NAME))
    if sha(raw)!=RAW_SHA:
        raise ValueError('ORIGINAL_GTE_SHA256_HOLD')
    lines = raw.decode().splitlines()
    if len(lines)!=145383:
        raise ValueError('FULL_NATIVE_GTE_LINE_COUNT_HOLD')
    for k in range(0,len(lines),903):
        p=lines[k].split()
        if p[0]=='G' and abs(float(p[1])-.1875)<1e-12:
            block='\n'.join(lines[k:k+903])+'\n'
            validate(block)
            return block, sha(raw)
    raise ValueError('T_0P1875_GTE_MISSING_HOLD')

def build_run(src, block, flags, directory):
    exe=directory/'micro.exe'
    cmd=['gfortran',*flags,'-o',str(exe),str(src)]
    compiled=subprocess.run(cmd,text=True,capture_output=True,check=True)
    proc=subprocess.run([str(exe)],input=block,text=True,capture_output=True)
    if proc.returncode:
        raise RuntimeError('GNU_MICRO_NATIVE_FAILED '+proc.stderr)
    rows={}
    for line in proc.stdout.splitlines():
        p=line.split()
        if p and p[0] in ('GNU_REAL32_S07','NATIVE_G_TARGET'):
            rows[p[0]]=[float(x) for x in p[1:]]
    if set(rows)!={'GNU_REAL32_S07','NATIVE_G_TARGET'}:
        raise ValueError('GNU_OUTPUT_PARSE_HOLD')
    if any(len(v)!=6 or not all(math.isfinite(x) for x in v) for v in rows.values()):
        raise ValueError('GNU_OUTPUT_NONFINITE_HOLD')
    return {'flags':flags,'binary_sha256':sha(exe.read_bytes()),
            'six_components_kN_kNm':rows['GNU_REAL32_S07'],
            'native_target_kN_kNm':rows['NATIVE_G_TARGET'],
            'residual_kN_kNm':[x-y for x,y in zip(rows['GNU_REAL32_S07'],rows['NATIVE_G_TARGET'])],
            'Mx_residual_kNm':rows['GNU_REAL32_S07'][3]-rows['NATIVE_G_TARGET'][3],
            'compiler_stdout':compiled.stdout}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive')
    ap.add_argument('--fortran',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    src=Path(a.fortran)
    if not src.is_file():
        raise ValueError('FORTRAN_SOURCE_MISSING')
    block,raw_sha=(synthetic(),'SYNTHETIC_ONLY') if a.self_test else extract(a.archive)
    g=validate(block)
    rejects=0
    lines=block.splitlines()
    bad_blocks=[]
    # Native log uses E-format decimals and variable spaces; mutate fields,
    # not a brittle literal substring that only matches synthetic fixtures.
    for row,field,value in [(0,0,'X'),(2,3,'221'),(0,3,'NaN')]:
        altered=lines[:]
        parts=altered[row].split()
        parts[field]=value
        altered[row]=' '.join(parts)
        bad_blocks.append('\n'.join(altered)+'\n')
    for bad in bad_blocks:
        try:
            validate(bad)
        except ValueError:
            rejects+=1
    if rejects!=3:
        raise AssertionError('NEGATIVE_TESTS_NOT_REJECTED')
    variants={'O0_no_contract':['-O0','-ffp-contract=off'],
              'O2_no_contract':['-O2','-ffp-contract=off'],
              'O2_contract_fast':['-O2','-ffp-contract=fast']}
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp)
        runs={}
        for key,flags in variants.items():
            runs[key]=build_run(src,block,flags,d)
            target=runs[key]['native_target_kN_kNm']
            if max(abs(x-y) for x,y in zip(target,g[12:18]))>1e-6:
                raise AssertionError('NATIVE_G_ROW_MISMATCH')
            if a.self_test:
                for i in (0,3):
                    if abs(runs[key]['six_components_kN_kNm'][i]-.001)>1e-8:
                        raise AssertionError('FLOAT32_CANCELLATION_FIXTURE_HOLD')
    receipt={'status':'GNU_REAL32_MICRO_DIAGNOSTIC_NOT_PHYSICS_PASS',
             'SOURCE':{'archive_zip_sha256':ZIP_SHA if not a.self_test else None,
                       'raw_gte_sha256':raw_sha,'selected_gte_sha256':sha(block.encode()),
                       'selected_time_s':.1875,
                       'read_level':'DIRECT_NATIVE_GTE_903_ROWS' if not a.self_test else 'SYNTHETIC_ONLY'},
             'REF':'OpenFAST v3.5.3 ElastoDyn.f90 L1175-L1202; not a new paper',
             'STANDARD':'No authorized IEC/GB original clauses read',
             'OFFICIAL':'GNU Fortran compiler actual binary32 operations; official OpenFAST source loop order',
             'RUN':{'new_openfast_or_abaqus_solver_runs':0,
                    'gfortran_version':subprocess.check_output(['gfortran','--version'],text=True).splitlines()[0],
                    'fortran_source_sha256':sha(src.read_bytes()),
                    'python_driver_sha256':sha(Path(__file__).read_bytes()),
                    'negative_rejections':rejects,'variant_count':len(variants)},
             'FIG':0,'TAB':runs,
             'assumptions':'Native G/T/E values are printed decimal approximations of runtime state; binary32 reading and expression ordering tested under compiler flags, not proof of exact OpenFAST optimization flags.',
             'error_budget':'Report absolute Mx residual in kN.m and cross-variant spread; historical atol=1e-5/rtol=5e-5 is diagnostic, not physical tolerance.',
             'HOLD':'Even exact numeric reconstruction cannot establish wind-only force/moment ownership, inertia/gravity removal, or DLC1.2 physics PASS.',
             'physical_pass':False}
    Path(a.out).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':receipt['status'],
                      'Mx_residuals_kNm':{k:v['Mx_residual_kNm'] for k,v in runs.items()},
                      'negative_rejections':rejects,'self_test':a.self_test}))

if __name__=='__main__':
    main()
