"""Extract actual REV22 material cards and section assignments without solver.
Do not infer material grades from old revisions. No input modification.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, re
p=Path(__file__).resolve().parent
src=p.parent/'REV22_VALIDATION_KIT/HE_REV22_FULL_ASSEMBLY_EQ005.txt'
raw=src.read_bytes()
sha=hashlib.sha256(raw).hexdigest()
assert sha=='e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5'
materials={}
assignments=[]
part=None
material=None
card=None
for no,line in enumerate(raw.decode('utf-8-sig').splitlines(),1):
    s=line.strip()
    if not s or s.startswith('**'):continue
    if s.startswith('*'):
        fields=[x.strip() for x in s.split(',')]
        keyword=fields[0].upper()
        opts={x.split('=',1)[0].strip().upper():x.split('=',1)[1].strip().strip('"') for x in fields[1:] if '=' in x}
        if keyword=='*PART':part=opts.get('NAME')
        elif keyword=='*END PART':part=None
        if keyword=='*MATERIAL':
            material=opts['NAME'];assert material not in materials
            materials[material]={'line':no,'cards':[]}
        if keyword.endswith('SECTION') and 'MATERIAL' in opts:
            assignments.append({'line':no,'part':part,'keyword':keyword,'elset':opts.get('ELSET'),'material':opts['MATERIAL'],'header':s,'data':[]})
            material=None;card=None
        elif material is not None and keyword in ('*DENSITY','*ELASTIC','*PLASTIC','*DAMPING','*CONCRETE DAMAGED PLASTICITY','*CONCRETE COMPRESSION HARDENING','*CONCRETE COMPRESSION DAMAGE','*CONCRETE TENSION STIFFENING','*CONCRETE TENSION DAMAGE','*EXPANSION','*DEPVAR','*USER MATERIAL','*RATE DEPENDENT','*CYCLIC HARDENING'):
            card={'line':no,'header':s,'data':[]};materials[material]['cards'].append(card)
        elif keyword!='*MATERIAL':
            material=None;card=None
        else:card=None
        active_section=assignments[-1] if assignments and assignments[-1]['line']==no else None
    else:
        if card is not None:card['data'].append(s)
        if active_section is not None:active_section['data'].append(s)
counts=Counter(x['material'] for x in assignments)
assert set(counts).issubset(materials),set(counts)-set(materials)
assert {'C65','C70'}.issubset(materials)
report={'source':src.name,'source_sha256':sha,'source_bytes':len(raw),'materials':materials,'section_counts':dict(counts),'sections':assignments,'native_solver':'NOT_RUN','scope':'Exact archived material cards and assignments; no grade certification, no physical validation, no local CAE check'}
(p/'rev22-material-inventory.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'materials':list(materials),'section_counts':dict(counts)},ensure_ascii=False))
