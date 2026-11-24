from pathlib import Path
import hashlib,json,re,math,sys
import numpy as np
D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data'); sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(D/'HE_REV14_EQ_RAYLEIGH_1PCT.inp').read_bytes(); assert sha(raw)=='70c88e645da2e2195fbc089c4af3432d9a37eb38c66296fd23a8b7e1437d5faa';s=raw.decode('ascii')
parts=list(re.finditer(r'^\*Part, name=([^\n]+)\n.*?^\*End Part\n',s,re.M|re.S)); b=next(m for m in parts if m[1]=='RNA_MASS_SKELETON_OFFICIAL'); body=b[0];nodes={};elems={};sets={};sec={}
for m in re.finditer(r'^\*([^*\n]+)\n([^*]*)',body,re.M):
 k,v=m[1],m[2]; rows=[[float(i) for i in l.split(',') if i.strip()] for l in v.strip().splitlines() if l.strip()]
 if k=='Node':nodes={int(r[0]):np.array(r[1:]) for r in rows}
 elif k.startswith('Element,'):elems={int(r[0]):[int(i) for i in r[1:]] for r in rows}
 elif k.startswith('Elset,'):
  name=re.search('elset=([^,]+)',k)[1]; x=[int(i) for r in rows for i in r];sets[name]=list(range(x[0],x[1]+1,x[2])) if 'generate' in k else x
 elif k.startswith('Beam Section,'):
  name=re.search('elset=([^,]+)',k)[1];mat=re.search('material=([^,]+)',k)[1];rho=float(re.search(r'^\*Material, name='+mat+r'\n\*Density\n([^,\n]+)',s,re.M)[1]);rad=rows[0][0]
  for i in sets[name]:assert i not in sec;sec[i]=(mat,rho,rad)
assert len(elems)==len(sec)==28 and len(nodes)==32
# Analytical uniform circular-cylinder mass/inertia for each existing B31 carrier; not native solver lumped-mass output.
records=[]
for i,(n1,n2) in elems.items():
 a,c=nodes[n1],nodes[n2];v=c-a;L=np.linalg.norm(v);u=v/L;mat,rho,r=sec[i];m=rho*math.pi*r*r*L;cg=(a+c)/2;I=m*((L*L/12+r*r/4)*(np.eye(3)-np.outer(u,u))+r*r/2*np.outer(u,u));records.append((m,cg,I,mat,L))
M=sum(r[0] for r in records);G=sum(r[0]*r[1] for r in records)/M; G[np.abs(G)<1e-10]=0
shift=lambda d:np.dot(d,d)*np.eye(3)-np.outer(d,d)
J=sum(I+m*shift(c-G) for m,c,I,_,_ in records);J[np.abs(J)<1e-5]=0
P=np.array([0.,160.,0.]);T=np.array([0.,158.,0.]);JP=J+M*shift(G-P);JT=J+M*shift(G-T)
assert np.linalg.eigvalsh(J).min()>0 and np.linalg.eigvalsh(J).max()<np.trace(J)/2
# Check generalized rigid-body kinetic energy using several translations/rotations.
S=lambda d:np.array([[0,-d[2],d[1]],[d[2],0,-d[0]],[-d[1],d[0],0]])
def mass6(m,c,I,p):d=c-p;return np.block([[m*np.eye(3),-m*S(d)],[m*S(d),I+m*shift(d)]])
old6=sum(mass6(m,c,I,P) for m,c,I,_,_ in records);new6=mass6(M,G,J,P);assert np.allclose(old6,new6,rtol=1e-12,atol=1e-5)
alpha=.0145230339976
# Preserve historical RP position and coupling and all existing output set names; new CG node in part, six DOFs tied to RP.
newpart=f'''*Part, name=RNA_LUMPED_INERTIA
*Node
1, {G[0]:.15g}, {G[1]:.15g}, {G[2]:.15g}
*Nset, nset=SET_RNA_CG
1,
*Element, type=MASS, elset=SET_RNA_MASS
1, 1
*Mass, elset=SET_RNA_MASS, alpha={alpha:.13g}
{M:.15g},
*Element, type=ROTARYI, elset=SET_RNA_INERTIA
2, 1
*Rotary Inertia, elset=SET_RNA_INERTIA, alpha={alpha:.13g}
'''+', '.join(f'{J[i,j]:.15g}' for i,j in [(0,0),(1,1),(2,2),(0,1),(0,2),(1,2)])+'\n*End Part\n'
edits=[]
def edit(a,b,new):edits.append(dict(offset=a,oldLength=b-a,oldSha256=sha(raw[a:b]),new=new))
a=s.index('** Job name:');z=s.index('\n',a)+1;edit(a,z,'** Job name: HE_REV15_EQ_RNA_LUMPED Model name: CONTACT_REV15_RNA_LUMPED\n** REV15: display meshes removed; inherited rigid RNA analytical mass/inertia at CG; native verification pending.\n')
removed=[m for m in parts if m[1].startswith('DTU_')];assert len(removed)==3
for m in removed:edit(m.start(),m.end(),'')
edit(b.start(),b.end(),newpart)
insts=list(re.finditer(r'^\*Instance, name=([^\n,]+), part=([^\n]+)\n.*?^\*End Instance\n',s,re.M|re.S));di=[m for m in insts if m[2].startswith('DTU_')];assert len(di)==9
for m in di:edit(m.start(),m.end(),'')
ri=next(m for m in insts if m[2]=='RNA_MASS_SKELETON_OFFICIAL');edit(ri.start(),ri.end(),'*Instance, name=RNA_LUMPED_INERTIA-1, part=RNA_LUMPED_INERTIA\n*End Instance\n')
for m in re.finditer(r'^\*\* Constraint: DB_RNA_[^\n]+\n\*Display Body, instance=[^\n]+\n[^\n]+\n',s,re.M):edit(m.start(),m.end(),'')
rb=re.search(r'^\*\* Constraint: RB_RNA_DISTRIBUTED_OFFICIAL\n\*Rigid Body[^\n]+\n',s,re.M);edit(rb.start(),rb.end(),'** Constraint: RB_RNA_LUMPED_OFFSET\n*Rigid Body, ref node=SET_RNA_RP, tie nset=RNA_LUMPED_INERTIA-1.SET_RNA_CG\n')
for m in re.finditer(r'^\*Material, name=MAT_RNA_[^\n]+\n\*Density\n[^\n]+\n\*Elastic\n[^\n]+\n\*Damping[^\n]+\n',s,re.M):edit(m.start(),m.end(),'')
assert len(edits)==32,len(edits)
edits.sort(key=lambda x:x['offset']);out=[];p=0
for e in edits:
 i=e['offset'];assert i>=p and sha(raw[i:i+e['oldLength']])==e['oldSha256'];out.extend([raw[p:i],e['new'].encode('ascii')]);p=i+e['oldLength']
out.append(raw[p:]);data=b''.join(out);t=data.decode('ascii');assert len(re.findall(r'^\*Part,',t,re.M))==len(re.findall(r'^\*End Part',t,re.M))==100
assert not re.search(r'^\*(?:Display Body|.*MAT_RNA_|.*RNA_MASS_SKELETON_OFFICIAL|.*DTU_(?:BLADE|NACELLE|SPINNER))',t,re.M|re.I)
assert t[t.index('*Step,'):]==s[s.index('*Step,'):]
for k in ['Contact Pair','Tie,','Embedded Element','Equation','Nonstructural Mass','Solid Section','Coupling,']:
 assert re.findall(r'^\*'+k+r'.*$',t,re.M|re.I)==re.findall(r'^\*'+k+r'.*$',s,re.M|re.I),k
assert len(re.findall(r'^\*Element, type=MASS,',t,re.M))==1 and len(re.findall(r'^\*Element, type=ROTARYI,',t,re.M))==1
counts=lambda x:{k:len(re.findall(r'^\*'+k+r'\b',x,re.M|re.I)) for k in ['Part','Instance','Display Body','Rigid Body','Material']}
def elementcounts(x):
 d={}
 for m in re.finditer(r'^\*Element, type=([^,\n]+)[^\n]*\n([^*]+)',x,re.M|re.I):d[m[1]]=d.get(m[1],0)+len(m[2].strip().splitlines())
 return d
by={}
for m,c,I,mat,L in records:by[mat]=by.get(mat,0)+m
patch=dict(schema=2,base='REV14_EQ_RAYLEIGH_1PCT',sourceSha256=sha(raw),targetSha256=sha(data),targetSize=len(data),edits=edits)
audit=dict(sourceSha256=sha(raw),targetSha256=sha(data),sourceBytes=len(raw),targetBytes=len(data),editCount=len(edits),RNA_mass_kg=M,CG_global_m=G.tolist(),RP_global_m=P.tolist(),tower_top_global_m=T.tolist(),J_CG_kgm2=J.tolist(),J_RP_kgm2=JP.tolist(),J_tower_top_kgm2=JT.tolist(),principal_inertia_kgm2=np.linalg.eigvalsh(J).tolist(),mass_by_old_material_kg=by,rigid_mass6_RP=new6.tolist(),mass6_max_abs_difference=float(np.max(np.abs(old6-new6))),DTU_report_mass_kg=673998.,mass_difference_kg=M-673998.,alpha=alpha,source_counts=counts(s),target_counts=counts(t),source_element_counts=elementcounts(s),target_element_counts=elementcounts(t),checks=['source hash','all 5 steps byte identical','contact/tie/embedded/equation/NSM/solid section/coupling keywords identical','positive physical inertia','analytical 6x6 rigid mass matrix equivalence','no display or RNA carrier definitions remain'],scope='Analytical cylinder inertia of inherited RNA skeleton; old native low-order rigid mass lumping may differ; not complete DTU prototype identification. Fixed rotor, no flexible blades. Other setup unchanged.',native_solver='NOT_RUN')
(D/'HE_REV15_EQ_RNA_LUMPED.inp').write_bytes(data);(D/'REV15_RNA_patch.json').write_text(json.dumps(patch,indent=2)+'\n');(D/'REV15_RNA_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
