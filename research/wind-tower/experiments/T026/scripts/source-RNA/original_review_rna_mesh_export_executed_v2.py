# -*- coding: ascii -*-
"""Abaqus 2025: read existing source COPY; export actual RNA surface meshes.
No Job, submit, writeInput, save, geometry edit or mesh mutation is performed.
"""
from abaqus import Mdb
from abaqusConstants import *
import part, material, section, assembly, step, interaction, load, mesh, regionToolset
import os, csv, json, hashlib, datetime, traceback, math
from collections import Counter

SOURCE_COPY = r'D:/Codex-research-native/t026-cae-probe/cae_audit_20261004_193900_105064/DTU158_SOURCE_COPY.cae'
OUT = r'D:/Codex-research-native/t026-rna-source-readonly-20261004'
EXPECTED_SHA = '9e1544e236a1454b209c3688603e0562a384c09607baebd80dd1707b9fb8a1f4'
MODELS = ['DTU158_SITE_S04_INTERFACE_DYNAMIC', 'RNA_REAL_EXPLICIT']
OUTER = ['DTU_BLADE_SMOOTH_%d-1' % i for i in (1,2,3)] + [n for i in (1,2,3) for n in ('DTU_NACELLE_SEG_%d-1' % i, 'DTU_SPINNER_SEG_%d-1' % i)]

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def value(v):
    if v is None or isinstance(v,(str,int,bool)):return v
    if isinstance(v,float):return v if math.isfinite(v) else str(v)
    if isinstance(v,(tuple,list)):return [value(x) for x in v]
    if isinstance(v,dict):return {str(k):value(x) for k,x in v.items()}
    return str(v)

def attrs(obj,names):
    result={}
    for n in names:
        try:result[n]=value(getattr(obj,n))
        except Exception:pass
    return result

def lookup(repo,name):
    for attr in ('sets','allSets','allInternalSets','surfaces','allSurfaces','allInternalSurfaces'):
        try:
            bucket=getattr(repo,attr)
            if name in bucket:return bucket[name],attr
        except Exception:pass
    return None,None

def resolve(raw,a,model):
    try:
        if not isinstance(raw,(tuple,list)):return raw,'object'
        name=raw[0]
        if len(raw)>2 and isinstance(raw[2],str) and raw[2] in a.instances:
            obj,which=lookup(a.instances[raw[2]],name)
            if obj is not None:return obj,'instance:'+raw[2]+'.'+which
        obj,which=lookup(a,name)
        if obj is not None:return obj,'assembly.'+which
        if len(raw)>1 and raw[1] in model.parts:
            obj,which=lookup(model.parts[raw[1]],name)
            if obj is not None:return obj,'part:'+raw[1]+'.'+which
    except Exception:pass
    return None,'unresolved'

def region_details(raw,a,model):
    obj,resolution=resolve(raw,a,model)
    out={'raw':value(raw),'resolution':resolution,'resolved':obj is not None}
    if obj is None:return out,[]
    node_pairs=set();face_rows=[];errors=[]
    try:
        for n in obj.nodes:node_pairs.add((str(n.instanceName),int(n.label)))
    except Exception:pass
    try:
        faces=list(obj.faces)
        out['geometric_face_count']=len(faces)
        for f in faces:
            row={'index':int(f.index),'instanceName':str(getattr(f,'instanceName',''))}
            try:
                fn=list(f.getNodes());row['mesh_node_count']=len(fn)
                for n in fn:node_pairs.add((str(n.instanceName),int(n.label)))
            except Exception as exc:row['getNodes_error']=str(exc);errors.append(str(exc))
            face_rows.append(row)
    except Exception as exc:out['faces_access_error']=str(exc)
    # For geometric face regions use Face.getNodes only; adjacent full elements
    # include off-face nodes and must not expand the coupling surface.
    if not face_rows and not node_pairs:
        try:
            for e in obj.elements:
                for n in e.getNodes():node_pairs.add((str(n.instanceName),int(n.label)))
            out['node_membership_method']='element_getNodes_for_element_only_region'
        except Exception:pass
    else:out['node_membership_method']='direct_nodes_and_geometric_face_getNodes'
    out['faces']=face_rows
    by_instance={}
    for ins,label in sorted(node_pairs):by_instance.setdefault(ins,[]).append(label)
    out['mesh_node_count']=len(node_pairs)
    out['node_ranges']={ins:{'count':len(labels),'min':min(labels),'max':max(labels),'label_sha256':hashlib.sha256(','.join(str(x) for x in labels).encode('ascii')).hexdigest()} for ins,labels in by_instance.items()}
    try:
        out['reference_points']=[]
        for index,r in enumerate(obj.referencePoints):
            rec={'index_in_region':index,'coordinates':value(a.getCoordinates(entity=r))}
            # ReferencePoint.id is absent in this installation; coordinates are
            # obtained through the documented assembly query without guessing.
            if hasattr(r,'id'):rec['repository_id']=int(r.id)
            out['reference_points'].append(rec)
    except AttributeError:
        if type(obj).__name__!='Surface':out['reference_points_access_error']='Reference point API unavailable for this region.'
    except Exception as exc:out['reference_points_access_error']=str(exc)
    return out,sorted(node_pairs)

def csv_output(path,header,rows):
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(rows)
    return {'path':path,'sha256':sha(path),'rows':len(rows),'bytes':os.path.getsize(path)}

def model_export(model,alias):
    a=model.rootAssembly
    out={'model':model.name,'outer_instances':{},'parts':{},'couplings':{},'rotation_BC':{},'RP_sets':{},'coordinate_convention':'Actual assembly instance node coordinates; source CAE uses SI geometry, Y vertical. No scale or projection applied.'}
    node_rows=[];elem_rows=[];section_rows=[]
    for name in sorted(OUTER):
        ins=a.instances[name];p=model.parts[ins.partName]
        nodes=sorted(ins.nodes,key=lambda x:x.label);elements=sorted(ins.elements,key=lambda x:x.label)
        for n in nodes:node_rows.append([name,int(n.label)]+[format(float(x),'.17g') for x in n.coordinates])
        for e in elements:
            labels=[int(n.label) for n in e.getNodes()]
            assert len(labels)<=8
            elem_rows.append([name,int(e.label),str(e.type),len(labels)]+labels+['']*(8-len(labels)))
        coords=[n.coordinates for n in nodes]
        out['outer_instances'][name]={'part':ins.partName,'nodes':len(nodes),'elements':len(elements),'element_types':dict(Counter(str(e.type) for e in elements)),'bounds_actual_assembly_m':{'min':[min(c[i] for c in coords) for i in range(3)],'max':[max(c[i] for c in coords) for i in range(3)]},'excludedFromSimulation':value(ins.excludedFromSimulation),'feature_suppressed':bool(a.features[name].isSuppressed())}
        if ins.partName not in out['parts']:
            assignments=[]
            for assignment in p.sectionAssignments:
                sec=model.sections[assignment.sectionName]
                mat=model.materials[sec.material]
                rec={'sectionName':assignment.sectionName,'section_class':type(sec).__name__,'material':sec.material,'density':value(mat.density.table),'elastic':value(mat.elastic.table),'region':value(assignment.region),'suppressed':bool(assignment.suppressed)}
                profile=getattr(sec,'profile',None)
                if profile is not None:rec['profile']={'name':str(profile),'class':type(model.profiles[profile]).__name__,'values':attrs(model.profiles[profile],['r','a','b'])}
                assignments.append(rec);section_rows.append([ins.partName,assignment.sectionName,type(sec).__name__,sec.material,json.dumps(value(mat.density.table)),json.dumps(value(assignment.region)),str(assignment.suppressed)])
            out['parts'][ins.partName]={'geometry_faces':len(p.faces),'geometry_cells':len(p.cells),'mesh_elements':dict(Counter(str(e.type) for e in p.elements)),'assignments':assignments,'beam_orientation_count':len(p.beamSectionOrientations)}
    out['nodes_csv']=csv_output(os.path.join(OUT,alias+'_nodes.csv'),['instance','node_label','X_m','Y_m','Z_m'],node_rows)
    out['elements_csv']=csv_output(os.path.join(OUT,alias+'_elements.csv'),['instance','element_label','type','node_count']+['n%d'%i for i in range(1,9)],elem_rows)
    out['sections_csv']=csv_output(os.path.join(OUT,alias+'_section_assignments.csv'),['part','section','section_class','material','density_table','assigned_region','suppressed'],section_rows)
    region_rows=[]
    for name in sorted(model.constraints.keys()):
        c=model.constraints[name]
        if name.startswith('CPL_RNA') or name.startswith('CPL_NAC') or name=='COUPLING_RNA_TOP':
            row={'class':type(c).__name__,'settings':attrs(c,['suppressed','couplingType','influenceRadius','u1','u2','u3','ur1','ur2','ur3','adjust'])}
            row['surface'],pairs=region_details(c.surface,a,model)
            row['controlPoint'],dummy=region_details(c.controlPoint,a,model)
            for ins,label in pairs:region_rows.append([name,ins,label])
            out['couplings'][name]=row
    out['coupling_region_nodes_csv']=csv_output(os.path.join(OUT,alias+'_coupling_region_nodes.csv'),['coupling','instance','node_label'],region_rows)
    if 'BC_RNA_ROTATION' in model.boundaryConditions:
        bc=model.boundaryConditions['BC_RNA_ROTATION'];out['rotation_BC']={'class':type(bc).__name__,'settings':attrs(bc,['createStepName','suppressed','v1','v2','v3','vr1','vr2','vr3','distributionType','amplitude','localCsys','fieldName'])}
        out['rotation_BC']['region'],dummy=region_details(bc.region,a,model)
        states={}
        for sn in model.steps.keys():
            try:
                state=model.steps[sn].boundaryConditionStates['BC_RNA_ROTATION']
                states[sn]=attrs(state,['status','v1','v2','v3','vr1','vr2','vr3','v1State','v2State','v3State','vr1State','vr2State','vr3State'])
            except Exception:pass
        out['rotation_BC']['step_states']=states
    for name in ('SET_RNA_RP','SET_TOWER_TOP','_PickedSet230'):
        obj,which=lookup(a,name)
        if obj is not None:out['RP_sets'][name]=region_details(obj,a,model)[0]
    out['steps']={n:{'class':type(s).__name__,'settings':attrs(s,['previous','timePeriod','nlgeom','perturbation'])} for n,s in model.steps.items()}
    return out

os.makedirs(OUT,exist_ok=True)
report_path=os.path.join(OUT,'original_review_export_report.json')
before=sha(SOURCE_COPY)
report={'created_local':datetime.datetime.now().isoformat(),'source_copy':SOURCE_COPY,'copy_sha256_before':before,'expected_copy_sha256':EXPECTED_SHA,'models':{},'scope':'Read only actual source COPY with openAuxMdb/copyAuxMdbModel. Complete outer RNA coordinates, element getNodes labels, regions and BCs.','no_solver_submit':True,'no_writeInput':True,'no_CAE_save':True,'no_source_modification':True,'official_API_sources':[
    {'title':'Mdb auxiliary model interface','url':'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKERRefMap/simaker-c-mdbpyc.htm'},
    {'title':'MeshElement.getNodes and internal indices versus labels','url':'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKERRefMap/simaker-c-meshelementpyc.htm'},
    {'title':'Face.getNodes associated mesh nodes','url':'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKERRefMap/simaker-c-facepyc.htm'}]}
db=None
try:
    assert before==EXPECTED_SHA,'Source copy differs; audit must not silently switch identities.'
    db=Mdb();db.openAuxMdb(pathName=SOURCE_COPY)
    report['aux_model_names']=list(db.getAuxMdbModelNames())
    for name in MODELS:
        assert name in report['aux_model_names'],name
        db.copyAuxMdbModel(fromName=name,toName=name)
    db.closeAuxMdb()
    for i,name in enumerate(MODELS):
        try:report['models'][name]=model_export(db.models[name],['primary','explicit'][i])
        except Exception:report['models'][name]={'error':traceback.format_exc()}
    if all('error' not in m for m in report['models'].values()):
        a,b=[report['models'][n] for n in MODELS]
        report['models_mesh_equal']={k:a[k]['sha256']==b[k]['sha256'] for k in ('nodes_csv','elements_csv','sections_csv','coupling_region_nodes_csv')}
    report['status']='SUCCESS' if all('error' not in m for m in report['models'].values()) else 'PARTIAL_FAILURE'
except Exception:report['fatal_error']=traceback.format_exc();report['status']='FAILURE'
finally:
    if db is not None:
        try:db.close()
        except Exception:report['close_error']=traceback.format_exc()
    report['copy_sha256_after']=sha(SOURCE_COPY)
    report['copy_unchanged']=report['copy_sha256_after']==before
    report['interpretation_boundary']='Complete source outer geometry is present. Export does not validate its assigned structural section, density, physical flexibility, rotation response, aeroelasticity or dynamic conclusions. Existing BeamSection assignment to S3/S4R surfaces is reported as source evidence without repairing it.'
    with open(report_path,'w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({'report':report_path,'status':report.get('status'),'copy_unchanged':report['copy_unchanged']}))
