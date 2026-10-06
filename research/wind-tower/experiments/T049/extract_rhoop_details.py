# -*- coding: utf-8 -*-
"""
Read-only RHOOP audit for the original Abaqus CAE.

Run with Abaqus Python/noGUI, for example:
  abaqus cae noGUI=extract_rhoop_details.py -- config.json

The script opens an auxiliary Mdb, copies models into memory and NEVER saves,
writes input, creates/submits jobs, or mutates the source CAE.
"""
from abaqus import Mdb
from abaqusConstants import *
import part, material, section, assembly, step, interaction, load, mesh, regionToolset
import os, sys, json, math, hashlib, traceback
from collections import defaultdict, Counter, deque

def arg_config():
    for x in reversed(sys.argv):
        if x.lower().endswith('.json') and os.path.isfile(x):
            return x
    raise RuntimeError('config json not found in argv')

CFG=json.load(open(arg_config(),'r',encoding='utf-8'))
OUT=CFG['output']
SRC=CFG['source_cae']
MODEL_FILTER=CFG.get('models',None)

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def val(v):
    if v is None or isinstance(v,(str,int,bool)): return v
    if isinstance(v,float): return v if math.isfinite(v) else str(v)
    if isinstance(v,(list,tuple)): return [val(x) for x in v]
    if isinstance(v,dict): return {str(k):val(x) for k,x in v.items()}
    return str(v)

def attrs(o,names):
    d={}
    for n in names:
        try: d[n]=val(getattr(o,n))
        except Exception: pass
    return d

def section_info(m,name):
    s=m.sections[name]
    d={'name':name,'class':type(s).__name__}
    d.update(attrs(s,['material','area','thickness','profile','integration','preIntegrate']))
    mat=d.get('material')
    if mat and mat in m.materials:
        ma=m.materials[mat]
        md={}
        for p in ['density','elastic','plastic']:
            try: md[p]=attrs(getattr(ma,p),['table','type','temperatureDependency','dependencies'])
            except Exception: pass
        d['material_properties']=md
    if isinstance(d.get('area'),(int,float)) and d['area']>0:
        d['equivalent_diameter_mm']=1000.0*math.sqrt(4.0*d['area']/math.pi)
    return d

def components(p):
    # Graph connected components of the orphan/mesh line elements.
    node_by_label={int(n.label):n for n in p.nodes}
    adj=defaultdict(set)
    elem_nodes={}
    for e in p.elements:
        labs=[int(x) for x in e.connectivity]
        elem_nodes[int(e.label)]=labs
        for a,b in zip(labs[:-1],labs[1:]):
            adj[a].add(b); adj[b].add(a)
    seen=set(); comps=[]
    for lab in node_by_label:
        if lab in seen: continue
        q=[lab]; seen.add(lab); ns=[]
        while q:
            u=q.pop(); ns.append(u)
            for v in adj.get(u,()):
                if v not in seen: seen.add(v); q.append(v)
        nset=set(ns)
        es=[eid for eid,labs in elem_nodes.items() if any(x in nset for x in labs)]
        xyz=[node_by_label[x].coordinates for x in ns]
        ys=[float(x[1]) for x in xyz]
        rs=[math.sqrt(float(x[0])**2+float(x[2])**2) for x in xyz]
        comps.append({
          'nodes':len(ns),'elements':len(es),
          'y_mean':sum(ys)/len(ys),'y_min':min(ys),'y_max':max(ys),
          'r_mean':sum(rs)/len(rs),'r_min':min(rs),'r_max':max(rs)
        })
    return sorted(comps,key=lambda x:(x['y_mean'],x['r_mean']))

def part_record(m,p):
    rec={
      'part':p.name,'nodes':len(p.nodes),'elements':len(p.elements),
      'element_types':dict(Counter(str(e.type) for e in p.elements)),
      'sections':[]
    }
    xyz=[n.coordinates for n in p.nodes]
    if xyz:
        rec['bounds']={'min':[min(float(x[k]) for x in xyz) for k in range(3)],
                       'max':[max(float(x[k]) for x in xyz) for k in range(3)]}
    for a in p.sectionAssignments:
        sname=a.sectionName
        d=section_info(m,sname)
        d['assignment']=attrs(a,['suppressed','offset','offsetType','thicknessAssignment'])
        rec['sections'].append(d)
    comps=components(p)
    rec['connected_components']=comps
    rec['component_count']=len(comps)
    if len(comps)>1:
        ys=sorted(x['y_mean'] for x in comps)
        rec['vertical_spacing_m']=[ys[i+1]-ys[i] for i in range(len(ys)-1)]
        sp=rec['vertical_spacing_m']
        rec['vertical_spacing_summary_m']={'min':min(sp),'max':max(sp),'mean':sum(sp)/len(sp)}
    return rec

def model_record(m):
    a=m.rootAssembly
    names=[n for n in m.parts.keys() if n.upper().startswith('RHOOP')]
    out={'model':m.name,'rhoop_part_count':len(names),'parts':{},'instances':{},'embedded_constraints':[]}
    for n in sorted(names):
        out['parts'][n]=part_record(m,m.parts[n])
    for n,inst in a.instances.items():
        if inst.partName in names or n.upper().startswith('RHOOP'):
            sr=None
            try: sr=bool(a.features[n].isSuppressed())
            except Exception: pass
            out['instances'][n]={'part':inst.partName,'suppressed':sr,'nodes':len(inst.nodes),'elements':len(inst.elements)}
    # Preserve raw EmbeddedRegion definitions that mention RHOOP so we can prove
    # whether restored hoops are actually embedded and into which host.
    for n,c in m.constraints.items():
        if type(c).__name__!='EmbeddedRegion': continue
        raw={'name':n,'class':type(c).__name__}
        for key in ['embeddedRegion','hostRegion']:
            try: raw[key]=val(getattr(c,key))
            except Exception as ex: raw[key+'_error']=str(ex)
        txt=json.dumps(raw,ensure_ascii=False).upper()
        if 'RHOOP' in txt:
            out['embedded_constraints'].append(raw)
    return out

before=sha256(SRC)
db=Mdb()
report={'source':SRC,'source_sha256_before':before,'read_only_intent':True,'models':{}}
try:
    db.openAuxMdb(pathName=SRC)
    names=list(db.getAuxMdbModelNames())
    if MODEL_FILTER: names=[x for x in names if x in MODEL_FILTER]
    for i,name in enumerate(names):
        alias='rhoop_audit_'+str(i)
        try:
            db.copyAuxMdbModel(fromName=name,toName=alias)
            report['models'][name]=model_record(db.models[alias])
        except Exception:
            report['models'][name]={'error':traceback.format_exc()}
        finally:
            if alias in db.models: del db.models[alias]
    db.closeAuxMdb()
finally:
    try: db.close()
    except Exception: pass

after=sha256(SRC)
report['source_sha256_after']=after
report['source_unchanged']=(before==after)
os.makedirs(os.path.dirname(OUT) or '.',exist_ok=True)
with open(OUT,'w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({'output':OUT,'source_unchanged':report['source_unchanged'],'models':list(report['models'])},ensure_ascii=False))
