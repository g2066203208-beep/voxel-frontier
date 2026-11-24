from pathlib import Path
import hashlib,json,re,math
D=Path('/mnt/data'); src=D/'HE_REV13_EQ_2H_CHECK.inp'; raw=src.read_bytes(); sha=lambda x:hashlib.sha256(x).hexdigest(); assert sha(raw)=='7a56d8f7bfc059434f57dc4ddb99961e2ea1f41176b6aff27e587ad4fcd1f8d2'; s=raw.decode('ascii')
f1,f2,z=.13525,.79428,.01
alpha=4*math.pi*z*f1*f2/(f1+f2); beta=z/(math.pi*(f1+f2)); edits=[]
def edit(a,b,new): edits.append(dict(offset=a,old=s[a:b],new=new))
a=s.index('** Job name:');b=s.index('\n',a)+1;edit(a,b,'** Job name: HE_REV14_EQ_RAYLEIGH_1PCT Model name: CONTACT_REV14_EQ_RELATIVE\n** Provisional 1% Rayleigh from historical BF1 modes 1/5; relative-coordinate inertia loading; native solver NOT_RUN.\n')
materials=[]
for m in re.finditer(r'^\*Material, name=([^\n]+)\n\*Density\n[^\n]+\n\*Elastic\n[^\n]+\n',s,re.M):
 name=m[1]; B=0. if name.startswith('MAT_RNA_') else beta
 edit(m.end(),m.end(),f'*Damping, alpha={alpha:.12g}, beta={B:.12g}\n');materials.append(dict(name=name,alpha=alpha,beta=B))
assert len(materials)==14 and sum(m['beta']==0 for m in materials)==7
start=s.rindex('*Step,'); old=s[start:s.index('*Restart,',start)]
new='''*Step, name=EQ_2H_RAYLEIGH_REL, nlgeom=YES, inc=2000000, unsymm=YES
Unscaled ESM horizontal record, fixed-base relative coordinates; provisional Rayleigh 1%.
*Dynamic, application=TRANSIENT FIDELITY
0.005, 160.195, 1.e-7, 0.005
*Contact Controls, reset
** Uniform support translation: -M r a_g; no simultaneous prescribed support motion.
*Boundary, op=NEW, type=DISPLACEMENT
CSEG_01-1.FACE_BOTTOM, 1, 3, 0.
PT_36x15p2-1.SET_PT_BOTTOM_GEOM, 1, 3, 0.
** Reassert self-weight when replacing distributed loads. All directions use the same whole-model mass selection.
*Dload, op=NEW
, GRAV, 9.81, 0., -1., 0.
*Dload, op=NEW, amplitude=EQ_X_EAST_SI
, GRAV, 1., -1., 0., 0.
*Dload, op=NEW, amplitude=EQ_Z_MINUS_NORTH_SI
, GRAV, 1., 0., 0., -1.
'''
assert 'type=ACCELERATION' in old and 'EQ_X_EAST_SI' in old and 'EQ_Z_MINUS_NORTH_SI' in old
edit(start,start+len(old),new)
edits.sort(key=lambda x:x['offset']);out=[];p=0
for e in edits:
 i=e['offset'];assert i>=p and s[i:i+len(e['old'])]==e['old'];out.extend((s[p:i],e['new']));p=i+len(e['old'])
out.append(s[p:]);t=''.join(out);data=t.encode('ascii')
assert len(re.findall(r'^\*Damping,',t,re.M))==14
assert t[t.index('*Step,'):t.rindex('*Step,')]==s[s.index('*Step,'):s.rindex('*Step,')]
assert 'type=ACCELERATION' not in t[t.rindex('*Step,'):]
assert len(re.findall(r'^\*Part,',t,re.M))==len(re.findall(r'^\*End Part\b',t,re.M))==103
assert re.findall(r'^\*(?:Contact Pair|Tie,|Embedded Element|Equation|Rigid Body|Display Body|Nonstructural Mass|Solid Section|Beam Section).*$',t,re.M|re.I)==re.findall(r'^\*(?:Contact Pair|Tie,|Embedded Element|Equation|Rigid Body|Display Body|Nonstructural Mass|Solid Section|Beam Section).*$',s,re.M|re.I)
def amp(x,name):
 m=re.search(r'^\*Amplitude, name='+name+r'[^\n]*\n([^*]+)',x,re.M|re.I);assert m; vals=[float(v) for v in re.split(r'[,\s]+',m[1].strip()) if v]; assert len(vals)==64080; return vals
amps={}
for name in ('EQ_X_EAST_SI','EQ_Z_MINUS_NORTH_SI'):
 a=amp(s,name);assert a==amp(t,name);amps[name]=dict(samples=len(a)//2,first=a[:2],last=a[-2:],pga=max(abs(v) for v in a[1::2]));assert a[-2]==160.195
# reverse reconstruction (insertions included)
p=0;rev=[];delta=0
for e in edits:
 i=e['offset']+delta;assert t[i:i+len(e['new'])]==e['new'];rev.extend((t[p:i],e['old']));p=i+len(e['new']);delta+=len(e['new'])-len(e['old'])
rev.append(t[p:]);assert ''.join(rev).encode()==raw
patch=dict(base='REV13_EQ_2H_CHECK',sourceSha256=sha(raw),targetSha256=sha(data),targetSize=len(data),edits=edits)
audit=dict(sourceSha256=sha(raw),targetSha256=sha(data),targetSize=len(data),editCount=len(edits),f1=f1,f2=f2,targetDamping=z,alpha=alpha,beta=beta,frequencySource='historical BF1 2026-11-15; NOT REV13/14',materials=materials,amplitudes=amps,checks=['103/103 parts','first four steps byte identical','contact, sections, equations, rigid bodies, NSM keywords unchanged','two amplitude arrays exactly preserved','fixed supports and negative horizontal inertia directions','gravity reasserted','exact inverse reconstruction'],scope='uniform translating base, relative coordinates; rigid RNA alpha only; material damping not full tangent K; solver participation and effective mass unverified; U,V,A relative, add ground motion for absolute outputs',native_solver='NOT_RUN')
(D/'HE_REV14_EQ_RAYLEIGH_1PCT.inp').write_bytes(data);(D/'REV14_patch.json').write_text(json.dumps(patch,indent=2)+'\n');(D/'REV14_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
