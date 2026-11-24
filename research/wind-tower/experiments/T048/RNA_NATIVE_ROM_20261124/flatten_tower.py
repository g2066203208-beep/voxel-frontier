"""Guarded flattening of frozen REV18; no arbitrary INP support. Preserve all
physical tower elements, contact, materials, equation constraints and steps.
Abaqus runtime validation required; do not use on other models without review.
"""
import argparse,hashlib,json,re,collections
from pathlib import Path

def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def parse(s):
    b=[]
    for l in s.splitlines():
        if l.startswith('**') or not l.strip():continue
        if l.startswith('*'):b.append([l,[]])
        else:b[-1][1].append(l)
    return b
def key(h):return h.split(',')[0].upper()
def arg(h,k):
    m=re.search(r'(?:^|,)\s*'+re.escape(k)+r'\s*=\s*([^,]+)',h,re.I)
    return m[1].strip() if m else None
def fields(l):return [x.strip() for x in l.split(',') if x.strip()]
def label(s):assert re.fullmatch(r'\d+',s),s;return int(s)
def serialize(b):return b[0]+'\n'+'\n'.join(b[1])+ ('\n' if b[1] else '')
def stripopt(h,op):return re.sub(r',\s*'+op+r'(?=,|$)','',h,flags=re.I)
def list_lines(a):
    a=list(a);return [', '.join(map(str,a[i:i+16])) for i in range(0,len(a),16)]

def flatten(src,kind,precheck=False):
    blocks=parse(src);parts={};inst={};head=[];assembly=[];post=[];mode='head';active=None
    for h,r in blocks:
        k=key(h)
        if k=='*PART':assert mode in ('head','partdone');active=arg(h,'name');assert active not in parts;parts[active]=[];mode='part'
        elif k=='*END PART':assert mode=='part';active=None;mode='partdone'
        elif k=='*ASSEMBLY':assert mode=='partdone';mode='assembly'
        elif k=='*INSTANCE':
            assert mode=='assembly';name=arg(h,'name');p=arg(h,'part');assert name not in inst and p in parts and len(r)<=1
            t=tuple(map(float,fields(r[0]))) if r else (0.,0.,0.);assert len(t)==3;inst[name]=(p,t);mode='instance'
        elif k=='*END INSTANCE':assert mode=='instance' and not r;mode='assembly'
        elif k=='*END ASSEMBLY':assert mode=='assembly';mode='post'
        elif mode=='part':parts[active].append((h,r))
        elif mode=='head':head.append((h,r))
        elif mode=='assembly':assembly.append((h,r))
        elif mode=='post':post.append((h,r))
        else:raise ValueError((mode,h))
    assert len(inst)==len(parts)==100 and len({p for p,t in inst.values()})==100
    rna='RNA_FLEX_DPM-1';assert inst[rna][0]=='RNA_FLEX_DPM';retain=kind=='reference'
    use={i:v for i,v in inst.items() if i!=rna or retain}
    noff=1;eoff=0;maps={};sets={'NSET':{},'ELSET':{},'SURFACE':{}};mapped=[];nodes={1:(0.,160.,0.)};elems={};tower_el=[];part_stats={};
    for i,(p,t) in use.items():
        b=parts[p];nn={};ee={}
        for h,r in b:
            if key(h)=='*NODE':
                for line in r:
                    a=fields(line);n=label(a[0]);assert n not in nn and len(a)==4;nn[n]=tuple(float(x) for x in a[1:]);
            if key(h)=='*ELEMENT':
                for line in r:
                    a=list(map(label,fields(line)));assert a[0] not in ee;ee[a[0]]=(arg(h,'type'),a[1:]);
        assert nn and ee and all(n in nn for _,ns in ee.values() for n in ns)
        maps[i]=(noff,eoff,set(nn),set(ee));local={};
        for h,r in b:
            k=key(h);tag={'*NSET':'NSET','*ELSET':'ELSET','*SURFACE':'NAME'}.get(k)
            if tag:
                a=arg(h,tag);local[a.upper()]=i+'__'+a
            if k=='*ELEMENT' and arg(h,'elset'):
                a=arg(h,'elset');local[a.upper()]=i+'__'+a
        def lname(x):assert x.upper() in local,(i,x);return local[x.upper()]
        def local_header(h):
            for tag in ('nset','elset','name'):
                a=arg(h,tag)
                if a is not None and a.upper() in local:h=re.sub(r'(?i)(,\s*'+tag+r'\s*=\s*)'+re.escape(a)+r'(?=,|$)',lambda m:m[1]+lname(a),h)
            return stripopt(h,'internal')
        def record_set(typ,name,ids):
            sets[typ].setdefault(name.upper(),set()).update(ids)
        start=len(mapped);counts=collections.Counter()
        for h,r in b:
            k=key(h);nh=local_header(h);out=[]
            if k=='*NODE':
                for l in r:
                    a=fields(l);n=label(a[0])+noff; xyz=tuple(float(v)+dt for v,dt in zip(a[1:],t));assert n not in nodes;nodes[n]=xyz
                    out.append(f'{n}, '+', '.join(format(v,'.17g') for v in xyz))
            elif k=='*ELEMENT':
                ns=[]
                for l in r:
                    a=list(map(label,fields(l)));e=a[0]+eoff;conn=[x+noff for x in a[1:]];assert e not in elems;elems[e]=(arg(h,'type'),conn);counts[arg(h,'type')]+=1;out.append(', '.join(map(str,[e]+conn)));ns.append(e)
                    if i!=rna:tower_el.append(e)
                if arg(h,'elset'):record_set('ELSET',lname(arg(h,'elset')),ns)
            elif k in ('*NSET','*ELSET'):
                typ=k[1:];offset,ids=(noff,nn) if typ=='NSET' else (eoff,ee);gen='generate' in h.lower();ns=[]
                for l in r:
                    a=list(map(label,fields(l)))
                    if gen:assert len(a)==3 and a[2]>0 and (a[1]-a[0])%a[2]==0;v=list(range(a[0],a[1]+1,a[2]));out.append(', '.join(map(str,[a[0]+offset,a[1]+offset,a[2]])))
                    else:v=a;out.append(', '.join(str(x+offset) for x in a))
                    assert set(v)<=ids.keys();ns.extend(x+offset for x in v)
                record_set(typ,lname(arg(h,typ)),ns)
            elif k=='*SURFACE':
                assert arg(h,'type').upper()=='ELEMENT';name=lname(arg(h,'name'));ss=[]
                for l in r:
                    a=fields(l);assert len(a)==2;es=lname(a[0]);assert es.upper() in sets['ELSET'];ss.append((es.upper(),a[1]));out.append(es+', '+a[1])
                sets['SURFACE'][name.upper()]=ss
            elif k in ('*SOLID SECTION','*BEAM GENERAL SECTION','*MASS','*ROTARY INERTIA'):
                assert arg(nh,'elset').upper() in sets['ELSET'];out=r
            elif k in ('*TRANSVERSE SHEAR STIFFNESS','*SHEAR CENTER'):out=r
            elif k=='*MPC':
                for l in r:
                    a=fields(l);assert a[0]=='BEAM' and len(a)==3 and all(label(x) in nn for x in a[1:]);out.append('BEAM, '+', '.join(str(label(x)+noff) for x in a[1:]))
            else:raise ValueError('Unknown part keyword '+h)
            mapped.append((nh,out))
        part_stats[i]={'nodes':len(nn),'elements':len(ee),'node_offset':noff,'element_offset':eoff,'translation':t,'types':dict(counts)}
        # Inverse map checks for every element, coordinate, and label.
        for n,xyz in nn.items():assert max(abs(nodes[n+noff][j]-xyz[j]-t[j]) for j in range(3))<1e-12
        for e,(typ,conn) in ee.items():assert elems[e+eoff]==(typ,[n+noff for n in conn])
        noff+=max(nn);eoff+=max(ee)
    # All qualified original instance references must resolve to a previously mapped set.
    pat=re.compile(r'\b([A-Za-z0-9_-]+-\d+)\.([A-Za-z0-9_-]+)\b')
    refs=collections.Counter()
    def qualify(l):
        def sub(m):
            i,a=m.groups();assert i in use,(i,a);v=i+'__'+a;assert any(v.upper() in sets[k] for k in sets),(i,a);refs[m[0]]+=1;return v
        return pat.sub(sub,l)
    ass=[];rp_seen=0;removed=0;ass_set_counts={}
    for h,r in assembly:
        k=key(h)
        if k=='*NODE':
            assert len(r)==1;v=fields(r[0]);assert label(v[0])==1 and tuple(map(float,v[1:]))==nodes[1];ass.append((h,r));rp_seen+=1;continue
        if k=='*RIGID BODY' and rna in h and not retain:assert not r;removed+=1;continue
        if k in ('*NSET','*ELSET'):
            typ=k[1:];i=arg(h,'instance');name=arg(h,typ);nh=stripopt(h,'internal');ns=[];out=[];gen='generate' in h.lower()
            if i:
                assert i in maps;no,eo,nn,ee=maps[i];o,ids=(no,nn) if typ=='NSET' else (eo,ee);nh=re.sub(r',\s*instance\s*=\s*[^,]+','',nh,flags=re.I)
                for l in r:
                    a=list(map(label,fields(l)))
                    if gen:assert len(a)==3 and a[2]>0 and (a[1]-a[0])%a[2]==0;v=list(range(a[0],a[1]+1,a[2]));out.append(', '.join(map(str,[a[0]+o,a[1]+o,a[2]])))
                    else:v=a;out.append(', '.join(str(x+o) for x in a))
                    assert set(v)<=ids;ns.extend(x+o for x in v)
            else:
                assert not gen
                for l in r:
                    a=fields(qualify(l));out.append(', '.join(a))
                    for v in a:
                        if v.isdigit():assert int(v) in (nodes if typ=='NSET' else elems);ns.append(int(v))
                        else:assert v.upper() in sets[typ];ns.extend(sets[typ][v.upper()])
            sets[typ].setdefault(name.upper(),set()).update(ns);ass.append((nh,out));ass_set_counts[name.upper()]=len(sets[typ][name.upper()]);continue
        assert k in ('*COUPLING','*KINEMATIC','*EQUATION','*RIGID BODY','*TIE','*EMBEDDED ELEMENT','*NONSTRUCTURAL MASS'),h
        ass.append((qualify(h),[qualify(l) for l in r]))
    assert rp_seen==1 and removed==(0 if retain else 1)
    # Ensure no output/use of deleted RNA definitions. Explicitly include native substructure in fixed-global GRAV.
    post0=[(qualify(h),[qualify(l) for l in r]) for h,r in post];pout=[];skipping=False;nl=0
    for h,r in post0:
        k=key(h)
        if precheck and k=='*STEP' and 'EQ_2H_RAYLEIGH_REL' in h:skipping=True
        if skipping:continue
        if k=='*DLOAD' and not retain:
            assert len(r)==1 and re.match(r'^\s*,\s*GRAV,',r[0],re.I);out=['REV20_TOWER_ALL'+r[0], 'REV20_RNA'+r[0]];nl+=1;pout.append((h,out))
        else:pout.append((h,r))
    new=[];new.extend(head);new.extend(mapped);new.extend(ass)
    if not retain:
        el=eoff+1;assert el not in elems
        new.extend([('*Elset, elset=REV20_TOWER_ALL',list_lines(tower_el)),('*Element, type=SUBSTR, file=RNA_ROM10, elset=REV20_RNA',[f'{el}, 1']),('*Substructure Property, elset=REV20_RNA, large rotations=YES',['0., 0., 0.']),('*Substructure Damping Controls, viscous=ELEMENT',[])])
    new.extend(pout)
    counts=collections.Counter(key(h) for h,r in new)
    assert counts['*CONTACT PAIR']==30 and counts['*EMBEDDED ELEMENT']==62 and counts['*TIE']==5 and counts['*EQUATION']==108 and counts['*NONSTRUCTURAL MASS']==31 and counts['*COUPLING']==1
    assert counts['*STEP']==(4 if precheck else 5) and counts['*END STEP']==counts['*STEP']
    assert len(nodes)==(96605 if retain else 96297) and len(elems)==(96464 if retain else 96004),(len(nodes),len(elems))
    assert sets['NSET']['SET_RNA_RP']=={1} and sets['NSET']['_PICKEDSET230']=={1}
    assert all(n in nodes for typ,conn in elems.values() for n in conn)
    assert all(len(v)>0 and v<=nodes.keys() for v in sets['NSET'].values()) and all(len(v)>0 and v<=elems.keys() for v in sets['ELSET'].values())
    result=''.join(serialize(x) for x in new)
    assert not pat.search(result) and '*Part,' not in result and '*Assembly,' not in result
    report={'parent_sha256':sha(src),'target_sha256':sha(result),'bytes':len(result.encode()),'kind':kind,'precheck':precheck,'source_instances':100,'mapped_instances':len(use),'physical_nodes':len(nodes),'physical_elements':len(elems),'native_substructure_elements':0 if retain else 1,'explicit_tower_plus_RNA_gravity_blocks':nl,'counts':dict(counts),'part_stats':part_stats,'qualified_reference_count':sum(refs.values()),'sets':{k:len(v) for k,v in sets.items()},'native':'NOT_RUN'}
    return result,report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();s=a.parent.read_text();assert sha(s)=='91c4d7499ffc7cdd30144fe39f74da3d7fd4b6ce49bbfd6c716d4f5e0ae0b041';a.out.mkdir(parents=True,exist_ok=True)
    reports=[]
    for kind,pre,name in [('reference',True,'HE_REV20_FLAT_REFERENCE_PRECHECK.inp'),('rom',True,'HE_REV20_ROM10_PRECHECK.inp'),('rom',False,'HE_REV20_ROM10_EQ_LEAN010.inp')]:
        out,rep=flatten(s,kind,pre);(a.out/name).write_text(out);rep['file']=name;reports.append(rep);print(name,rep['bytes'],rep['target_sha256'])
    (a.out/'REV20_TOWER_FLAT_AUDIT.json').write_text(json.dumps(reports,indent=2)+'\n')
