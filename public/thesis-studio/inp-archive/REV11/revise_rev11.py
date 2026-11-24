from pathlib import Path
import re,hashlib,json,math,collections
D=Path('/mnt/data'); src=D/'HE_REV10_HE_CHECK.inp'; raw=src.read_bytes(); sha=lambda x:hashlib.sha256(x).hexdigest(); assert sha(raw)=='5ec5518edbe6f0fb038f24fafe402b72c0dbc2e0a51c72af44fe069c104d1507'
s=raw.decode('ascii'); edits=[]
def edit(a,b,new): edits.append(dict(offset=a,old=s[a:b],new=new))
a=s.index('** Job name:'); b=s.index('\n',a)+1; edit(a,b,'** Job name: HE_REV11_HE_CHECK Model name: CONTACT_REV11\n** REV11: HRB400 standard-strength envelope with literature strain landmarks; HPB300 ties; Q355 hot-rolled tower; Q355 100mm plate flange candidate. Cyclic calibration pending.\n')
# exact part-scoped assignments
counts=collections.Counter()
for p in re.finditer(r'^\*Part, name=([^\n]+)\n.*?^\*End Part\b',s,re.M|re.S):
 name=p[1]; block=p[0]
 for m in re.finditer(r'^\*Solid Section,.*material=S345$',block,re.M):
  if name.startswith('RHOOP_') and 'elset=SET_TIE,' in m[0]: dest='HPB300_TIE'
  elif name.startswith('SSEG_'): dest='Q355_TOWER_T16_40'
  elif name=='FLANGE_SOLID': dest='Q355_FLANGE_PLATE_T100'
  else: raise ValueError((name,m[0]))
  edit(p.start()+m.start(),p.start()+m.end(),m[0].replace('material=S345','material='+dest));counts[dest]+=1
assert counts=={'HPB300_TIE':31,'Q355_TOWER_T16_40':4,'Q355_FLANGE_PLATE_T100':1}
# HRB400 engineering characteristic strength envelope, C.1.2 shape; strain landmarks Zhang 2016 Table 1 mean. True stress/log strain before necking.
E=200e9; fy=400e6; fu=540e6; ey=fy/E; esh=.0164; eu=.1339
# Sample the plateau and linear strengthening with converted true stress and log plastic strain. First row plastic strain zero by Abaqus definition.
eng=[(ey,fy),(.01,fy),(esh,fy)]+[(esh+(eu-esh)*i/12,fy+(fu-fy)*i/12) for i in range(1,13)]
rows=[]
for i,(e,sig) in enumerate(eng):
 t=sig*(1+e); ep=0 if i==0 else math.log1p(e)-t/E; rows.append((t,ep))
assert all(y[0]>x[0] and y[1]>x[1] for x,y in zip(rows,rows[1:]))
def fmt(rows): return ''.join(f'{x:.12g}, {y:.12g}\n' for x,y in rows)
def mat(name,E,plastic,rows):return f'*Material, name={name}\n*Density\n7850.,\n*Elastic\n{E:.12g}, 0.3\n*Plastic{plastic}\n'+fmt(rows)
# Steel tower retains original 1% hardening as a documented sensitivity, now kinematic (not calibrated). No invented flange/tie hardening; EPP placeholder only.
H=206e9*.01/.99
materials=mat('HPB300_TIE',210e9,'',[(300e6,0)])+mat('Q355_TOWER_T16_40',206e9,', hardening=KINEMATIC',[(345e6,0),(345e6+H*.01,.01)])+mat('Q355_FLANGE_PLATE_T100',206e9,'',[(315e6,0)])+mat('HRB400',E,'',rows)
a=s.index('*Material, name=S345\n');b=s.index('*Material, name=STRAND_1860\n',a);edit(a,b,materials)
# Correct only current screening comment, preserve previous historical header.
a=s.index('** GB50135-2019 6.5 reference; assumed design fy=300 MPa for screening only.');b=s.index('\n',a);edit(a,b,'** GB50135-2019 6.5 reference; HRB400 design fy=360 MPa for hoop screening; not full code compliance.')
edits.sort(key=lambda x:x['offset']);out=[];p=0
for e in edits:
 i=e['offset'];assert i>=p and s[i:i+len(e['old'])]==e['old'];out.extend((s[p:i],e['new']));p=i+len(e['old'])
out.append(s[p:]); target=''.join(out);data=target.encode('ascii');
assert len(re.findall(r'^\*Part,',target,re.M))==len(re.findall(r'^\*End Part\b',target,re.M))==103
assert not re.search(r'^\*.*(?:material=S345|name=S345)$',target,re.M|re.I)
assert target[target.index('*Step,'):]==s[s.index('*Step,'):]
# independent reverse check and other non-edit content checks
p=0;rev=[];delta=0
for e in edits:
 i=e['offset']+delta;assert target[i:i+len(e['new'])]==e['new'];rev.extend((target[p:i],e['old']));p=i+len(e['new']);delta+=len(e['new'])-len(e['old'])
rev.append(target[p:]);assert ''.join(rev).encode()==raw
# exact nominal mass change inherited component-volume ledger; no geometry change
masses={'ties':783.332082087,'steel_tower':188206.134473043,'flange':8791.970361212};dm={k:v*(7850/7800-1) for k,v in masses.items()};oldmass=2585467.773573;newmass=oldmass+sum(dm.values())
patch={'base':'REV10','sourceSha256':sha(raw),'targetSha256':sha(data),'targetSize':len(data),'edits':edits}
audit={'source_sha256':sha(raw),'target_sha256':sha(data),'bytes':len(data),'edit_count':len(edits),'section_changes':dict(counts),'HRB400_nominal_engineering':eng,'HRB400_true_stress_plastic_strain':rows,'mass_delta_kg':dm,'mass_total_delta_kg':sum(dm.values()),'estimated_total_kg':newmass,'native_solver':'NOT_RUN','checks':['103/103 Part','no active S345','steps unchanged','exact reverse reconstruction','strictly increasing HRB400 stress/plastic strain']}
(D/'HE_REV11_HE_CHECK.inp').write_bytes(data);(D/'REV11_patch.json').write_text(json.dumps(patch,indent=2)+'\n');(D/'REV11_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
