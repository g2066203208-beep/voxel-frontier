"""Source-locked REV25 preflight only; never changes physical model or certifies design."""
from pathlib import Path
import hashlib, json, re, math
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'REV25_HOOP_COST/HE_REV25_HOOP_COST_EQ005.inp'
OUT=ROOT/'REV26_PREFLIGHT'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=SRC.read_bytes()
assert sha(raw)=='b76fd0f8964f07e110fb1653ab75a75dc45c047ceb58cb84afeac11b52c40193'
s=raw.decode('ascii')
parts=dict(re.findall(r'^\*Part,\s*name=([^,\r\n]+)[ \t]*\r?\n(.*?)^\*End Part[ \t]*\r?\n',s,re.M|re.S|re.I))
assert len(parts)==100
def section(name):
    z=parts[name]; cards=re.findall(r'^\*Solid Section,([^\r\n]+)\r?\n([^\r\n]+)',z,re.M|re.I)
    assert len(cards)==1,(name,cards)
    k,v=cards[0]
    return {'material':re.search(r'material=([^,]+)',k,re.I).group(1).strip(),'area_m2':float(v.split(',')[0])}
long=[]
for i in range(1,32):
    a=section('RBLONG_%02d'%i)
    a['segment']=i;a['equivalent_d_mm']=math.sqrt(4*a['area_m2']/math.pi)*1000
    a['design_d_mm']=50 if i<=25 else 40 if i<=28 else 36
    a['design_material']='HRB500'
    long.append(a)
pt=section('PT_36x15p2')
steps=list(re.finditer(r'^\*Step\b[^\r\n]*',s,re.M|re.I))
names=[re.search(r'\bname=([^,]+)',m.group(),re.I).group(1).strip() for m in steps]
assert names==['PT_BALANCE','Gravity','GRAVITY_CHECK','MODAL_30','EQ_2H_RAYLEIGH_REL'],names
pilot=s[:steps[-1].start()].encode('ascii')
assert re.search(rb'\*End Step\s*(?:\*\*[^\r\n]*\s*)*$',pilot,re.I)
assert len(re.findall(rb'^\*Step\b',pilot,re.M|re.I))==4
assert len(re.findall(rb'^\*End Step\b',pilot,re.M|re.I))==4
assert not re.search(rb'^\*Dynamic\b',pilot,re.M|re.I)
assert raw.startswith(pilot)
dest=OUT/'HE_REV26_PREFLIGHT_PT_GRAVITY_MODAL.inp'
dest.write_bytes(pilot)
audit={'scope':'REV25 exact-prefix pilot; no material or design changes; not native checked','source_sha256':sha(raw),'output_sha256':sha(pilot),'bytes':len(pilot),'parts':len(parts),'instances':len(re.findall(r'^\*Instance,',s,re.M|re.I)),'steps':names[:-1],'removed_step':names[-1],'longitudinal':long,'pt':pt,'native':'NOT_RUN','design_gate':'HOLD: original HRB400 phi25 is not R37 design HRB500 schedule; full load combinations, strut and construction checks outstanding'}
(OUT/'receipt.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
