"""Verify the archived original INP/TXT directly against the plotted CSV."""
import hashlib, csv, json, math
from pathlib import Path
p=Path(__file__).resolve().parent
src=p.parent/'REV22_VALIDATION_KIT/HE_REV22_FULL_ASSEMBLY_EQ005.txt'
raw=src.read_bytes()
sha=hashlib.sha256(raw).hexdigest()
assert sha=='e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5',sha
mats={}
material=None
card=None
for line in raw.decode('utf-8-sig').splitlines():
    line=line.strip()
    if not line or line.startswith('**'):continue
    if line.startswith('*'):
        card=line.split(',')[0].upper()
        if card=='*MATERIAL':
            material=line.split('=',1)[1].strip().upper()
        if material in ('C65','C70') and card in ('*ELASTIC','*DENSITY','*CONCRETE COMPRESSION HARDENING','*CONCRETE TENSION STIFFENING','*CONCRETE COMPRESSION DAMAGE','*CONCRETE TENSION DAMAGE'):
            mats.setdefault(material,{})[card]=[]
        continue
    if material in mats and card in mats[material]:
        mats[material][card].append([float(x.strip()) for x in line.split(',') if x.strip()])
rows=list(csv.DictReader((p/'rev22-cdp-curves.csv').open()))
checks=[]
for mat,c in mats.items():
    e0,nu=c['*ELASTIC'][0]
    for branch,sc,dc in [('compression','*CONCRETE COMPRESSION HARDENING','*CONCRETE COMPRESSION DAMAGE'),('tension','*CONCRETE TENSION STIFFENING','*CONCRETE TENSION DAMAGE')]:
        data=[r for r in rows if r['material']==mat and r['branch']==branch]
        assert len(data)==len(c[sc])==len(c[dc])
        err=[0,0,0,0]
        for i,(r,(s,e),(d,de)) in enumerate(zip(data,c[sc],c[dc])):
            assert int(r['point'])==i+1 and e==de
            err=[max(a,b) for a,b in zip(err,[abs(float(r['stress_MPa'])-s/1e6),abs(float(r['inelastic_or_cracking_strain'])-e),abs(float(r['total_strain'])-(e+s/e0)),abs(float(r['damage'])-d)])]
        assert max(err)<1e-12,err
        checks.append(dict(material=mat,branch=branch,points=len(data),max_abs_error=err))
assert len(checks)==4 and sum(x['points'] for x in checks)==100
receipt=dict(source=str(src.name),source_sha256=sha,source_bytes=len(raw),csv_sha256=hashlib.sha256((p/'rev22-cdp-curves.csv').read_bytes()).hexdigest(),check=checks,order_of_errors=['stress_MPa','input_strain','total_strain','damage'],scope='Original archived file only; not current local CAE or physical validation')
(p/'cdp-direct-source-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
