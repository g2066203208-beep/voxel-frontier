# -*- coding: utf-8 -*-
"""Read copied native CAEs using auxiliary Mdb; never save/writeInput/submit."""
from abaqus import Mdb
from abaqusConstants import *
import part, material, section, assembly, step, interaction, load, mesh, regionToolset
import os, sys, json, hashlib, traceback, datetime, math
from collections import Counter

CONFIG = json.load(open(sys.argv[-1], 'r', encoding='utf-8'))
OUT = CONFIG['output_directory']
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def val(v):
    if v is None or isinstance(v,(str,int,bool)):return v
    if isinstance(v,float):return v if math.isfinite(v) else str(v)
    if isinstance(v,(list,tuple)):return [val(x) for x in v]
    if isinstance(v,dict):return {str(k):val(x) for k,x in v.items()}
    return str(v)
def attrs(o,names):
    d={}
    for n in names:
        try:d[n]=val(getattr(o,n))
        except Exception:pass
    return d
def rna(s):return any(k in str(s).upper() for k in ['RNA','BLADE','NAC','SPIN','HUB','ROTOR','REFBLADE'])
def lookup(owner,name):
    for k in ['sets','allSets','allInternalSets','surfaces','allSurfaces','allInternalSurfaces']:
        try:
            repo=getattr(owner,k)
            if name in repo:return repo[name],k
        except Exception:pass
    return None,None
def region(raw,model,part_obj=None):
    a=model.rootAssembly;obj=None;where=None
    if isinstance(raw,(tuple,list)):
        name=raw[0]
        if part_obj is not None:obj,where=lookup(part_obj,name)
        if obj is None and len(raw)>2 and isinstance(raw[2],str) and raw[2] in a.instances:
            obj,where=lookup(a.instances[raw[2]],name)
        if obj is None:obj,where=lookup(a,name)
        if obj is None and len(raw)>1 and str(raw[1]) in model.parts:obj,where=lookup(model.parts[str(raw[1])],name)
    else:obj=raw;where='object'
    d={'raw':val(raw),'resolved':obj is not None,'resolved_repository':where}
    if obj is None:return d
    nodes=set();elems=set();errors=[]
    try:
        for n in obj.nodes:nodes.add((str(getattr(n,'instanceName','')),int(n.label)))
    except Exception:pass
    try:
        for e in obj.elements:elems.add(int(e.label))
    except Exception:pass
    faces=[]
    try:
        for f in obj.faces:
            faces.append({'index':int(f.index),'instance':str(getattr(f,'instanceName',''))})
            try:
                for n in f.getNodes():nodes.add((str(getattr(n,'instanceName','')),int(n.label)))
            except Exception as ex:errors.append('face nodes: '+str(ex))
            if part_obj is not None:
                try:
                    for e in f.getElements():elems.add(int(e.label))
                except Exception as ex:errors.append('face elements: '+str(ex))
    except Exception:pass
    d['faces']=faces;d['element_labels']=sorted(elems);d['element_count']=len(elems)
    by={}
    for ins,label in sorted(nodes):by.setdefault(ins,[]).append(label)
    d['node_labels_by_instance']=by;d['node_count']=len(nodes)
    if errors:d['query_errors']=errors
    try:d['reference_points']=[val(a.getCoordinates(entity=rp)) for rp in obj.referencePoints]
    except Exception:pass
    return d
def part_record(p,m):
    d={'nodes':len(p.nodes),'elements':len(p.elements),'element_types':dict(Counter(str(e.type) for e in p.elements)),
       'faces':len(p.faces),'cells':len(p.cells),'sections':[],'composite_layups':{},'material_orientations':[]}
    for assignment in p.sectionAssignments:
        rec=attrs(assignment,['sectionName','suppressed','offset','offsetType','thicknessAssignment'])
        sec=m.sections[assignment.sectionName]
        rec['section_class']=type(sec).__name__
        rec['section_properties']=attrs(sec,['material','thickness','profile','integration','preIntegrate','symmetric','layup'])
        if rna(p.name):rec['region']=region(assignment.region,m,p)
        d['sections'].append(rec)
    try:
        for name in p.compositeLayups.keys():
            c=p.compositeLayups[name]
            rec=attrs(c,['name','suppressed','elementType','symmetric','offsetType','offset'])
            rec['plies']=[]
            for ply in c.plies:
                pr=attrs(ply,['plyName','material','thickness','orientationType','orientationValue','additionalRotationType','additionalRotationField','axis','angle','numIntPoints','suppressed'])
                try:pr['region']=region(ply.region,m,p)
                except Exception as ex:pr['region_error']=str(ex)
                rec['plies'].append(pr)
            d['composite_layups'][name]=rec
    except Exception as ex:d['composite_layup_query_error']=str(ex)
    if rna(p.name):
        try:
            for o in p.materialOrientations:d['material_orientations'].append(attrs(o,['orientationType','axis','angle','stackDirection','localCsys','fieldName','additionalRotationType','additionalRotationField','region']))
        except Exception as ex:d['orientation_query_error']=str(ex)
    return d
def inspect(m,original_name):
    a=m.rootAssembly
    out={'source_model_name':original_name,'part_count':len(m.parts),'parts':{},'instances':{},'materials':{},'constraints':{},'steps':{},'boundary_conditions':{}}
    for n,p in m.parts.items():out['parts'][n]=part_record(p,m)
    for n,i in a.instances.items():
        rec={'part':i.partName,'nodes':len(i.nodes),'elements':len(i.elements),'excluded':val(i.excludedFromSimulation)}
        try:rec['feature_suppressed']=bool(a.features[n].isSuppressed())
        except Exception as ex:rec['suppression_query_error']=str(ex)
        if rna(n) or rna(i.partName):
            rec['element_types']=dict(Counter(str(e.type) for e in i.elements))
            rec['node_labels']=[int(x.label) for x in i.nodes]
            if len(i.nodes):rec['bounds']={'min':[min(float(x.coordinates[k]) for x in i.nodes) for k in range(3)],'max':[max(float(x.coordinates[k]) for x in i.nodes) for k in range(3)]}
        out['instances'][n]=rec
    for n,ma in m.materials.items():
        rec={}
        for prop in ['density','elastic','plastic','lamina','maxStress','failStress','failStrain','hashinDamageInitiation']:
            try:rec[prop]=attrs(getattr(ma,prop),['table','type','temperatureDependency','dependencies'])
            except Exception:pass
        out['materials'][n]=rec
    out['constraint_classes']=dict(Counter(type(c).__name__ for c in m.constraints.values()))
    for n,c in m.constraints.items():
        if not rna(n):continue
        rec={'class':type(c).__name__,'settings':attrs(c,['suppressed','couplingType','influenceRadius','u1','u2','u3','ur1','ur2','ur3','tieRotations'])}
        for key in ['surface','controlPoint','refPointRegion','bodyRegion','pinRegion','tieRegion','main','secondary']:
            try:rec[key]=region(getattr(c,key),m)
            except Exception as ex:rec[key+'_query_error']=str(ex)
        out['constraints'][n]=rec
    for n,s in m.steps.items():out['steps'][n]={'class':type(s).__name__,'properties':attrs(s,['previous','timePeriod','nlgeom','perturbation','suppressed','numEigen'])}
    for n,bc in m.boundaryConditions.items():
        rec={'class':type(bc).__name__,'properties':attrs(bc,['createStepName','suppressed','u1','u2','u3','ur1','ur2','ur3','v1','v2','v3','vr1','vr2','vr3','amplitude','localCsys'])}
        if rna(n):
            try:rec['region']=region(bc.region,m)
            except Exception as ex:rec['region_error']=str(ex)
            rec['step_states']={}
            for sn,s in m.steps.items():
                try:rec['step_states'][sn]=attrs(s.boundaryConditionStates[n],['status','u1','u2','u3','ur1','ur2','ur3','v1','v2','v3','vr1','vr2','vr3'])
                except Exception:pass
        out['boundary_conditions'][n]=rec
    return out

os.makedirs(OUT,exist_ok=True)
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'no_job_or_writeInput_or_save':True,'sources':[]}
def flush():
    with open(os.path.join(OUT,'native-inventory.json'),'w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
for source in CONFIG['sources']:
    rec={'source':source['source'],'copy':source['copy'],'expected_sha256':source['sha256'],'models':{}}
    report['sources'].append(rec);db=None
    try:
        rec['copy_before']=sha(source['copy']);assert rec['copy_before']==source['sha256']
        db=Mdb();db.openAuxMdb(pathName=source['copy']);rec['model_names']=list(db.getAuxMdbModelNames());flush()
        for index,name in enumerate(rec['model_names']):
            alias='audit_model_'+str(index)
            try:
                db.copyAuxMdbModel(fromName=name,toName=alias)
                rec['models'][name]=inspect(db.models[alias],name)
            except Exception:rec['models'][name]={'error':traceback.format_exc()}
            finally:
                if alias in db.models:del db.models[alias]
            flush()
        db.closeAuxMdb();rec['status']='complete' if all('error' not in x for x in rec['models'].values()) else 'partial'
    except Exception:rec['fatal_error']=traceback.format_exc();rec['status']='failed'
    finally:
        if db is not None:
            try:db.close()
            except Exception:pass
        rec['copy_after']=sha(source['copy']);rec['original_after']=sha(source['source'])
        rec['source_and_copy_unchanged']=rec['copy_before']==rec['copy_after']==rec['original_after']==source['sha256'];flush()
report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['status']='complete' if all(r['status']=='complete' and r['source_and_copy_unchanged'] for r in report['sources']) else 'partial-or-failed'
flush();print(json.dumps({'report':os.path.join(OUT,'native-inventory.json'),'status':report['status'],'sources':len(report['sources'])}))
