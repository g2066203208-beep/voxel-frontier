"""Build REV22 precheck and time-step comparison decks from exact archived ZIPs.
Run: python build_rev22.py REV21_MODE_PILOT.zip REV20_RNA_FULL_PACKAGE.zip OUTPUT_DIR
Only static verification; native Abaqus NOT_RUN.
"""
import argparse, hashlib, json, re, zipfile
from pathlib import Path
S21='f389e927a4b42f0c26bf22f1f9ef24202255b8dd03a8d0e7585edfae83a6af91'
S20='58f8afead62781ea80f3d01fc81055e97fb6ab5e85b04ce53d3ae9c65951e83f'
CASES={'FULL_ASSEMBLY':'7538ccb15a0af82364f0482f4a30e65a59d157a3b33efb94c4beb295a646721c','ROM10_NATIVE':'94b6d047f038aa501269e970050f83e32919e6b3ba4b6cd8ae8e99c93187b9c4'}
STEPS=[b'PT_BALANCE',b'Gravity',b'GRAVITY_CHECK',b'MODAL_30',b'EQ_2H_RAYLEIGH_REL']
STEP=re.compile(rb'^\*Step, name=([^,\r\n]+).*$',re.M|re.I)
END=re.compile(rb'^\*End Step[ \t]*\r?$',re.M|re.I)
OLD=b'0.005, 199.995, 1.e-7, 0.01'
NEW=b'0.005, 199.995, 1.e-7, 0.005'
def sha(b): return hashlib.sha256(b).hexdigest()
def check(ok,msg):
    if not ok: raise ValueError(msg)
def build(p21,p20,out):
    check(sha(p21.read_bytes())==S21,'REV21 ZIP mismatch')
    check(sha(p20.read_bytes())==S20,'REV20 ZIP mismatch')
    out.mkdir(parents=True,exist_ok=True)
    result={'native':'NOT_RUN','source_sha256':[S21,S20],'files':{}}
    def save(n,b):
        (out/n).write_bytes(b)
        result['files'][n]={'bytes':len(b),'sha256':sha(b)}
    with zipfile.ZipFile(p21) as z:
        check(z.testzip() is None,'REV21 CRC')
        for case,h in CASES.items():
            name='HE_REV21_MODE_'+case+'.inp'
            src=z.read(name)
            check(sha(src)==h,'Parent SHA')
            steps=list(STEP.finditer(src))
            check([m.group(1) for m in steps]==STEPS and len(END.findall(src))==5,'Step mismatch')
            i=steps[-1].start()
            pre=src[:i]
            check(len(END.findall(pre))==4,'Precheck mismatch')
            check(src[i:].count(OLD)==1 and src.count(OLD)==1,'Ambiguous increment')
            fine=src.replace(OLD,NEW,1)
            check(fine.replace(NEW,OLD,1)==src,'Byte mismatch')
            save('HE_REV22_'+case+'_PRECHECK.inp',pre)
            save('HE_REV22_'+case+'_EQ005.inp',fine)
            save(name,src)
        for n in ['RNA_REV20_10HZ_GENERATE.inp','MODE_EQ01_scaled_reference_SI.csv','REV21_MODE_AUDIT.json']:
            save(n,z.read(n))
    with zipfile.ZipFile(p20) as z:
        check(z.testzip() is None,'REV20 CRC')
        for n,info in json.loads(z.read('REV20_MANIFEST.json')).items():
            b=z.read(n)
            check(len(b)==info['bytes'] and sha(b)==info['sha256'],'REV20 member mismatch: '+n)
        check(z.read('RNA_REV20_10HZ_GENERATE.inp')==(out/'RNA_REV20_10HZ_GENERATE.inp').read_bytes(),'Generator mismatch')
        for n in ['HE_REV20_FLAT_REFERENCE_PRECHECK.inp','RNA_REV20_10HZ_GRAVITY_TEST.inp','RNA_REV20_FULL_GRAVITY_TEST.inp','RNA_REV20_FULL_PRELOAD_MODAL.inp','RNA_REV20_10HZ_EXPECTED.npz','RNA_REV20_10HZ_AUDIT.json']:
            save(n,z.read(n))
    (out/'REV22_STATIC_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['rev21','rev20','out']: p.add_argument(n,type=Path)
    a=p.parse_args()
    build(a.rev21,a.rev20,a.out)
