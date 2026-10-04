"""Read real ODB summaries/DAT and independently balance nodal gravity mass.
No solver, input changes, Word edits, or root-manifest mutation.
"""
import collections
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
FIG=Path('D:/Codex-research-validation/T026/figures')
FIG.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'run-manifest.json').read_text(encoding='utf-8'))
runs=[r for r in manifest['runs'] if r['run_id'] in ('RUN-T026-032','RUN-T026-034','RUN-T026-035')]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
nsign=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)
gauss=np.array(list(itertools.product([-1/math.sqrt(3),1/math.sqrt(3)],repeat=3)))
shape=[];gradient=[]
for xi in gauss:
    f=1+nsign*xi
    shape.append(np.prod(f,axis=1)/8)
    gradient.append(np.column_stack([nsign[:,j]*np.prod(np.delete(f,j,axis=1),axis=1)/8 for j in range(3)]))
shape=np.array(shape);gradient=np.array(gradient)

def parse_input(path):
    lines=Path(path).read_text(encoding='ascii').splitlines();blocks=[]
    for line in lines:
        line=line.strip()
        if not line or line.startswith('**'):continue
        if line.startswith('*'):
            fields=line[1:].split(',');opt={};flags=[]
            for item in fields[1:]:
                if '=' in item:
                    k,v=item.split('=',1);opt[k.strip().upper()]=v.strip().upper()
                else:flags.append(item.strip().upper())
            blocks.append([fields[0].strip().upper(),opt,flags,[]])
        else:blocks[-1][3].append(line)
    parts={};instances={};density={};asmsets=collections.defaultdict(list);nsm=[];part=None;mat=None
    for key,opt,flags,data in blocks:
        if key=='PART':part=opt['NAME'];parts[part]={'nodes':{},'elements':{},'sets':collections.defaultdict(list),'sections':[]}
        elif key=='END PART':part=None
        elif key=='INSTANCE':
            placements=[[float(v) for v in line.split(',') if v.strip()] for line in data]
            if any(len(p)!=3 for p in placements):raise RuntimeError('Unexpected nontranslation transform')
            instances[opt['NAME']]={'part':opt['PART'],'translation':sum((np.array(p) for p in placements),np.zeros(3))}
        elif key=='MATERIAL':mat=opt['NAME']
        elif key=='DENSITY':density[mat]=float(data[0].split(',')[0])
        elif key=='NODE' and part:
            for line in data:
                v=[x.strip() for x in line.split(',') if x.strip()];parts[part]['nodes'][int(v[0])]=np.array(list(map(float,v[1:4])))
        elif key=='ELEMENT' and part:
            for line in data:
                v=[int(x) for x in line.split(',') if x.strip()];parts[part]['elements'][v[0]]=(opt['TYPE'],v[1:])
                if 'ELSET' in opt:parts[part]['sets'][opt['ELSET']].append(v[0])
        elif key=='ELSET':
            v=[x.strip().upper() for line in data for x in line.split(',') if x.strip()]
            if 'GENERATE' in flags:
                lab=[]
                for i in range(0,len(v),3):a,b,c=map(int,v[i:i+3]);lab.extend(range(a,b+1,c))
            else:lab=[int(x) if x.isdigit() else x for x in v]
            if part:parts[part]['sets'][opt['ELSET']].extend(lab)
            elif 'INSTANCE' in opt:asmsets[opt['ELSET']].extend((opt['INSTANCE'],e) for e in lab)
        elif key in ('SOLID SECTION','BEAM SECTION'):
            area=None;radius=None
            if key=='BEAM SECTION':
                if opt['SECTION']!='CIRC':raise RuntimeError('Beam not CIRC')
                radius=float(data[0].split(',')[0]);area=math.pi*radius**2
            elif any(t=='T3D2' for t,n in parts[part]['elements'].values()):area=float(data[0].split(',')[0])
            parts[part]['sections'].append((opt['ELSET'],opt['MATERIAL'],area))
        elif key=='NONSTRUCTURAL MASS':
            if opt['UNITS']!='TOTAL MASS' or opt.get('DISTRIBUTION','MASS PROPORTIONAL')!='MASS PROPORTIONAL':raise RuntimeError('NSM assumption mismatch')
            nsm.append((opt['ELSET'],float(data[0].split(',')[0])))
    def resolve(p,setname,visited=None):
        visited=set() if visited is None else visited
        if setname in visited:raise RuntimeError('Recursive set')
        answer=[]
        for v in p['sets'][setname]:
            if isinstance(v,int):answer.append(v)
            else:answer.extend(resolve(p,v,visited|{setname}))
        return set(answer)
    node_mass=collections.defaultdict(float);coords={};elements={};min_j=float('inf');counts=collections.Counter()
    for iname,info in instances.items():
        p=parts[info['part']]
        for node,xyz in p['nodes'].items():coords[(iname,node)]=xyz+info['translation']
        assignments={}
        for elset,material,area in p['sections']:
            for lab in resolve(p,elset):
                if lab in assignments:raise RuntimeError('Overlapping section')
                assignments[lab]=(density[material],area)
        if set(assignments)!=set(p['elements']):raise RuntimeError('Incomplete section')
        solid_labels=[lab for lab,(typ,conn) in p['elements'].items() if typ.startswith('C3D8')]
        if solid_labels:
            xyz=np.array([[coords[(iname,node)] for node in p['elements'][lab][1]] for lab in solid_labels])
            jac=np.einsum('eia,gib->egab',xyz,gradient)
            determinants=np.linalg.det(jac);min_j=min(min_j,float(np.min(determinants)))
            rho=np.array([assignments[lab][0] for lab in solid_labels])
            weights=np.einsum('eg,gi,e->ei',determinants,shape,rho)
            for lab,weight in zip(solid_labels,weights):
                typ,conn=p['elements'][lab];counts[typ]+=1
                record=[((iname,node),float(w)) for node,w in zip(conn,weight)]
                elements[(iname,lab)]=record
                for node,w in record:node_mass[node]+=w
        for lab,(typ,conn) in p['elements'].items():
            if typ.startswith('C3D8'):continue
            if typ not in ('T3D2','B31'):raise RuntimeError('Unexpected mass element')
            rho,area=assignments[lab];L=float(np.linalg.norm(coords[(iname,conn[1])]-coords[(iname,conn[0])]))
            record=[((iname,node),rho*area*L/2) for node in conn];elements[(iname,lab)]=record;counts[typ]+=1
            for node,w in record:node_mass[node]+=w
    nsm_record=[]
    for setname,total in nsm:
        members=set(asmsets[setname]);underlying=sum(w for member in members for node,w in elements[member]);scale=total/underlying
        for member in members:
            for node,w in elements[member]:node_mass[node]+=w*scale
        nsm_record.append({'set':setname,'mass_kg':total,'elements':len(members),'underlying_mass_kg':underlying})
    return node_mass,coords,counts,min_j,nsm_record

def numeric_row_after(lines,title,count):
    start=next(i for i,line in enumerate(lines) if title in line)
    for line in lines[start+1:]:
        toks=line.split()
        if len(toks)==count:
            try:return list(map(float,toks))
            except ValueError:pass
    raise RuntimeError(title)

def modal_table(lines,title):
    normalized=title.replace(' ','')
    start=next(i for i,line in enumerate(lines) if re.sub(r'\s','',line)==normalized)
    records=[]
    for line in lines[start+1:]:
        tokens=line.split()
        if len(tokens)==7 and tokens[0].isdigit():
            records.append({'mode':int(tokens[0]),'components':list(map(float,tokens[1:]))})
            if len(records)==30:break
    if len(records)!=30 or [r['mode'] for r in records]!=list(range(1,31)):raise RuntimeError('Incomplete30 '+title)
    return records

report={'report_id':'T026-three-tower-mesh-verification','scope':'Actual root-run ODB histories/fields + DAT; independent Python mass integration, no solver or root-manifest/Word mutation',
        'last_two_budget_relative':.005,'budget_status':'Frozen before results; denominator fine mesh M3; no hindsight tolerance changes',
        'cases':[],'modal_direction_order':['X','Y','Z','RX','RY','RZ'],
        'modal_fraction_definition':'Sum30 translational effective masses / total model mass from DAT (includes constrained nodal mass). Also report / independently integrated free-node mass only as a separately labelled diagnostic; do not merge definitions.',
        'external_support_definition':['CSEG_01-1.FACE_BOTTOM','PT_36X15P2-1.SET_PT_BOTTOM_GEOM'],
        'gravity_balance_reference':'All body/NSM/RNA gravity masses integrated from same input; actual NLGEOM end-state node coordinates initial+ODB U. Internal ties/couplings/springs/RNA RP reactions excluded.',
        'mesh_family':'Frozen source geometry/materials/connectors/PT/rebar/RNA; different native tower discretizations; anisotropic family, no uniform-h Richardson/GCI inference.',
        'not_claimed':['Physical calibration of RNA/material/damping','Damage/postpeak mesh objectivity','30 modes sufficient for all local stress responses','Finite element cloud image from averaged-mode line plots']}
for r in runs:
    summary_path=ROOT/('tower-results-'+r['run_id']+'.json');summary=json.loads(summary_path.read_text(encoding='utf-8'))[0]
    gravity_path=ROOT/('gravity-nodes-'+r['run_id']+'.json');gravity=json.loads(gravity_path.read_text(encoding='utf-8'))
    nm,coords,counts,min_j,nsm=parse_input(r['input'])
    u={(row[0].upper(),int(row[1])):np.array(row[2:5]) for row in gravity['gravity_U']}
    missing=[str(node) for node in nm if node not in u]
    if missing:raise RuntimeError('Missing gravity mass node U '+repr(missing[:5]))
    mass=sum(nm.values());initial_cg=sum((w*coords[node] for node,w in nm.items()),np.zeros(3))/mass
    current_cg=sum((w*(coords[node]+u[node]) for node,w in nm.items()),np.zeros(3))/mass
    external_F=np.zeros(3);external_M=np.zeros(3);external_nodes=set();support_sums={}
    for rf in gravity['external_reactions']:
        node=(rf['instance'].upper(),rf['node']);external_nodes.add(node)
        force=np.array(rf['RF'][:3]);position=np.array(rf['coord'])+u[node]
        external_F+=force;external_M+=np.cross(position,force)
        support_sums.setdefault(rf['instance'],np.zeros(3));support_sums[rf['instance']]+=force
    body_F=np.array([0.,-mass*9.81,0.]);body_M=np.cross(current_cg,body_F)
    force_residual=external_F+body_F;moment_residual=external_M+body_M
    weight=mass*9.81;base_radius=max(np.linalg.norm(np.array(v['coord'])[[0,2]]) for v in gravity['external_reactions'])
    force_rel=float(np.linalg.norm(force_residual)/weight)
    moment_scale=weight*base_radius;moment_rel=float(np.linalg.norm(moment_residual)/moment_scale)
    free_mass=mass-sum(nm.get(node,0.) for node in external_nodes)
    datpath=Path(r['directory'])/(r['job']+'.dat');lines=datpath.read_text(errors='replace').splitlines()
    dat_mass=numeric_row_after(lines,'TOTAL MASS OF MODEL',1)[0]
    dat_cg=numeric_row_after(lines,'LOCATION OF THE CENTER OF MASS OF THE MODEL',3)
    effective=modal_table(lines,'EFFECTIVE MASS');participation=modal_table(lines,'PARTICIPATION FACTORS')
    cumulative=np.cumsum([row['components'] for row in effective],axis=0)
    modal_frames=summary['steps']['Modal_From_Gravity']['frames'];modes=[f for f in modal_frames if f.get('mode') in (1,2,3,4)]
    g=summary['steps']['Gravity']['frames'][-1]
    case={'run_id':r['run_id'],'baseline_id':r['baseline_id'],'job':r['job'],
          'sources':{'input':{'path':r['input'],'sha256':sha(r['input'])},'ODB':{'path':gravity['ODB'],'sha256':gravity['ODB_sha256']},
                     'DAT':{'path':str(datpath),'sha256':sha(datpath)},'ODB_summary':{'path':str(summary_path),'sha256':sha(summary_path)},
                     'gravity_read':{'path':str(gravity_path),'sha256':sha(gravity_path)}},
          'counts':dict(counts),'tower_solid_elements':counts['C3D8R']+counts['C3D8I'],'minimum_gauss_detJ':min_j,
          'mass_kg':mass,'DAT_mass_kg':dat_mass,'mass_integral_DAT_relative_difference':abs(dat_mass-mass)/mass,
          'initial_CG_m':initial_cg.tolist(),'DAT_initial_CG_m':dat_cg,'current_gravity_CG_m':current_cg.tolist(),
          'source_NSM_assignments':nsm,'free_node_mass_diagnostic_kg':free_mass,
          'gravity':{'RP_U_m':g['RNA_U'][0],'external_set_node_counts':{k:len(v) for k,v in gravity['external_set_membership'].items()},
                     'external_support_force_N':external_F.tolist(),'support_subtotal_force_N':{k:v.tolist() for k,v in support_sums.items()},
                     'external_support_moment_about_origin_Nm':external_M.tolist(),'gravity_force_N':body_F.tolist(),'gravity_moment_about_origin_Nm':body_M.tolist(),
                     'force_residual_N':force_residual.tolist(),'moment_residual_Nm':moment_residual.tolist(),
                     'force_residual_relative_to_weight':force_rel,'moment_residual_scaled_by_weight_base_radius':moment_rel,
                     'moment_scale_Nm':moment_scale,'base_radius_m':base_radius,
                     'force_budget_relative':1e-5,'moment_budget_scaled':1e-5,'force_pass':force_rel<=1e-5,'moment_pass':moment_rel<=1e-5,
                     'initial_CG_moment_residual_for_comparison_Nm':(external_M+np.cross(initial_cg,body_F)).tolist(),
                     'definition':'Only external fixed-node RF; moments at actual fixed node coordinates; body moment at deformed mass center. No internal RP/coupling reactions.'},
          'PT':{'S11_range_MPa':[min(g['PT_S'])/1e6,max(g['PT_S'])/1e6],'initial_input_MPa':1280.,
                'max_DAMAGET':g['max_DAMAGET'],'max_DAMAGEC':g['max_DAMAGEC'],
                'zero_damage_gravity_state':g['max_DAMAGET']==0 and g['max_DAMAGEC']==0,
                'meaning':'True final gravity state stress range; input1280MPa is not final effective stress. Zero damage only in this base state.'},
          'first_four_frequency_Hz':[f['frequency'] for f in modes],
          'Flex_X_RP_U_m':summary['steps']['Flex_X']['frames'][-1]['RNA_U'][0],
          'Flex_Z_RP_U_m':summary['steps']['Flex_Z']['frames'][-1]['RNA_U'][0],
          'load_N':1000.,'Flex_definition':'1kN small linear perturbation about the same balanced Gravity state; U per same RP at(0,160,0). Not nonlinear capacity or dynamic time history.',
          '30mode_effective_mass':effective,'30mode_participation_factors':participation,
          'effective_mass_vs_PF_square_relative_by_direction':(np.max(abs(np.array([r['components'] for r in effective])-np.array([r['components'] for r in participation])**2),axis=0)/np.maximum(cumulative[-1],1e-30)).tolist(),
          '30mode_effective_mass_total_components':cumulative[-1].tolist(),
          'translational_30mode_fraction_of_total_mass':(cumulative[-1,:3]/dat_mass).tolist(),
          'translational_30mode_fraction_of_free_node_mass_diagnostic':(cumulative[-1,:3]/free_mass).tolist(),
          'cumulative_effective_mass_components':cumulative.tolist(),
          'first_four_real_section_mean_modes':modes}
    report['cases'].append(case)
fine=report['cases'][-1];middle=report['cases'][-2]
comparisons=[]
for i,(a,b) in enumerate(zip(middle['first_four_frequency_Hz'],fine['first_four_frequency_Hz']),1):
    delta=abs(a-b)/abs(b);comparisons.append({'quantity':'frequency_mode_'+str(i),'middle':a,'fine':b,'units':'Hz','relative_change':delta,'pass':delta<=.005})
for field,component in [('Flex_X_RP_U_m',0),('Flex_Z_RP_U_m',2)]:
    a=middle[field][component];b=fine[field][component];delta=abs(a-b)/abs(b)
    comparisons.append({'quantity':field,'middle':a,'fine':b,'units':'m per1000N','relative_change':delta,'pass':delta<=.005})
for name,a,b in [('mass',middle['mass_kg'],fine['mass_kg']),('gravity_RP_UY',middle['gravity']['RP_U_m'][1],fine['gravity']['RP_U_m'][1]),('gravity_RP_UZ',middle['gravity']['RP_U_m'][2],fine['gravity']['RP_U_m'][2])]:
    comparisons.append({'quantity':name,'middle':a,'fine':b,'relative_change':abs(a-b)/abs(b),'units':'kg' if name=='mass' else 'm','diagnostic_only':True})
report['last_two_mesh_comparisons']=comparisons
report['frequency_and_flexibility_budget_pass']=all(c['pass'] for c in comparisons if 'pass' in c)
report['all_three_force_moment_balance_pass']=all(c['gravity']['force_pass'] and c['gravity']['moment_pass'] for c in report['cases'])
report['all_three_gravity_damage_zero']=all(c['PT']['zero_damage_gravity_state'] for c in report['cases'])
report['coverage_conclusion']='30mode effective-mass fractions reported for X/Y/Z using all30 EM/PF and DAT total mass. All-mode sum excludes mass at kinematically restrained DOFs, so complements of total-mass ratios cannot be assigned wholly to missing high modes. No assertion of complete modal coverage or convergence of local stress without response comparison.'
report['legacy_control_Elsets']='Three inherited control-Elset entries are legal and not used by the chapter2 verification steps; preserve the source input/card identity rather than silently deleting legacy sets.'
path=ROOT/'tower-verification-results.json';path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'mass':[c['mass_kg'] for c in report['cases']], 'balance':[(c['run_id'],c['gravity']['force_residual_relative_to_weight'],c['gravity']['moment_residual_scaled_by_weight_base_radius']) for c in report['cases']],
                  'first_four_f':[c['first_four_frequency_Hz'] for c in report['cases']],
                  'EM30fractions':[c['translational_30mode_fraction_of_total_mass'] for c in report['cases']],
                  'mesh_comparisons':comparisons,'mesh_pass':report['frequency_and_flexibility_budget_pass'],
                  'balance_pass':report['all_three_force_moment_balance_pass']},indent=2))
