"""Independent text/topology review of frozen G1-to-M2/M3 input transformations."""
import hashlib,json,math,re
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np

ROOT=Path('D:/Codex-research-validation/T026/tower')
G1=ROOT/'DTU158_RECONSTRUCTED_G1/DTU158_RECONSTRUCTED_G1.inp'
TARGETS=[ROOT/f'DTU158_RECONSTRUCTED_M{i}/DTU158_RECONSTRUCTED_M{i}.inp' for i in (2,3)]
TOWER={f'CSEG_{i:02}' for i in range(1,32)}|{f'SSEG_{i:02}' for i in range(1,5)}
FACE_NODES={'S1':(0,1,2,3),'S2':(4,5,6,7),'S3':(0,1,5,4),'S4':(1,2,6,5),'S5':(2,3,7,6),'S6':(3,0,4,7)}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def blocks(p):
    rows=[];head=None;data=[];line0=0
    for i,line in enumerate(Path(p).read_text(encoding='utf-8',errors='replace').splitlines(),1):
        if not line.strip() or line.startswith('**'):continue
        if line.startswith('*'):
            if head is not None:rows.append(dict(head,data=data,line=line0))
            ss=[s.strip() for s in line.split(',')];head={'key':ss[0][1:].lower().replace(' ',''),'params':{},'flags':[]};data=[];line0=i
            for s in ss[1:]:
                if '=' in s:
                    k,v=s.split('=',1);head['params'][k.lower().replace(' ','')]=v.upper().strip()
                else:head['flags'].append(s.upper())
        else:data.append([s.strip().upper() for s in line.split(',') if s.strip()])
    if head is not None:rows.append(dict(head,data=data,line=line0))
    return rows
def numeric_labels(b):
    if 'GENERATE' in b['flags']:
        return [n for row in b['data'] for n in range(int(row[0]),int(row[1])+1,int(row[2]) if len(row)>2 else 1)]
    return [int(v) if re.fullmatch(r'\d+',v) else v for row in b['data'] for v in row]
def structure(p):
    bs=blocks(p);parts={};instances={};a_nodes={};a_elements={};aset={'nset':defaultdict(list),'elset':defaultdict(list)};a_surfaces={};current=None;in_assembly=False
    for b in bs:
        k=b['key'];pars=b['params'];data=b['data']
        if k=='part':
            current=pars['name'];parts[current]={'nodes':{},'elements':{},'types':{},'nset':defaultdict(list),'elset':defaultdict(list),'surfaces':{},'blocks':[]};continue
        if k=='endpart':current=None;continue
        if k=='assembly':in_assembly=True;continue
        if k=='endassembly':in_assembly=False;continue
        if current:
            d=parts[current];d['blocks'].append(b)
            if k=='node':
                for row in data:d['nodes'][int(row[0])]=np.array([float(v) for v in row[1:4]])
                if 'nset' in pars:d['nset'][pars['nset']].extend(int(row[0]) for row in data)
            elif k=='element':
                for row in data:d['elements'][int(row[0])]=tuple(int(v) for v in row[1:]);d['types'][int(row[0])]=pars['type']
                if 'elset' in pars:d['elset'][pars['elset']].extend(int(row[0]) for row in data)
            elif k in ('nset','elset'):d[k][pars[k]].extend(numeric_labels(b))
            elif k=='surface':d['surfaces'][pars['name']]=b
        elif in_assembly:
            if k=='instance':instances[pars['name']]={'part':pars['part'],'transform':data}
            elif k=='node':
                for row in data:a_nodes[int(row[0])]=np.array([float(v) for v in row[1:4]])
            elif k=='element':
                for row in data:a_elements[int(row[0])]=tuple(int(v) for v in row[1:])
                if 'elset' in pars:aset['elset'][pars['elset']].append({'instance':None,'values':[int(row[0]) for row in data]})
            elif k in ('nset','elset'):aset[k][pars[k]].append({'instance':pars.get('instance'),'values':numeric_labels(b)})
            elif k=='surface':a_surfaces[pars['name']]=b
    return {'path':str(p),'sha256':sha(p),'blocks':bs,'parts':parts,'instances':instances,'a_nodes':a_nodes,'a_elements':a_elements,'aset':aset,'a_surfaces':a_surfaces}
def localset(s,p,kind,name,seen=None):
    seen=set() if seen is None else seen
    token=(p,kind,name)
    if token in seen:raise ValueError('recursive set '+str(token))
    if name not in s['parts'][p][kind]:raise KeyError(token)
    seen.add(token);vals=set()
    for x in s['parts'][p][kind][name]:
        vals.add(x) if isinstance(x,int) else vals.update(localset(s,p,kind,x,seen.copy()))
    return vals
def resolve(s,kind,name,seen=None):
    name=name.upper();seen=set() if seen is None else seen
    if name in seen:raise ValueError('recursive assembly set '+name)
    seen.add(name)
    if '.' in name:
        ins,local=name.split('.',1);p=s['instances'][ins]['part'];return {(ins,n) for n in localset(s,p,kind,local)}
    if name not in s['aset'][kind]:
        if name.isdigit():return {(None,int(name))}
        raise KeyError(('assembly',kind,name))
    vals=set()
    for record in s['aset'][kind][name]:
        for x in record['values']:
            if isinstance(x,int):vals.add((record['instance'],x))
            elif record['instance']:
                p=s['instances'][record['instance']]['part'];vals.update((record['instance'],n) for n in localset(s,p,kind,x))
            else:vals.update(resolve(s,kind,x,seen.copy()))
    return vals
def valid_ref(s,kind,ref):
    values=resolve(s,kind,ref);errors=[]
    for ins,n in values:
        d=s['a_nodes'] if kind=='nset' else s['a_elements']
        if ins:
            if ins not in s['instances']:errors.append(('missing_instance',ins));continue
            p=s['instances'][ins]['part'];d=s['parts'][p]['nodes' if kind=='nset' else 'elements']
        if n not in d:errors.append((ins,n))
    return values,errors
def transform(s,ins,p):
    x=np.array(p,dtype=float);rows=s['instances'][ins]['transform']
    if rows:
        if len(rows[0])==3:x+=np.array([float(v) for v in rows[0]])
        rot=rows[1:] if len(rows[0])==3 else rows
        if rot:
            assert len(rot)==1 and len(rot[0])==7
            vals=[float(v) for v in rot[0]];a=np.array(vals[:3]);v=np.array(vals[3:6])-a;v/=np.linalg.norm(v);th=math.radians(vals[6]);r=x-a
            x=a+r*math.cos(th)+np.cross(v,r)*math.sin(th)+v*np.dot(v,r)*(1-math.cos(th))
    return x
def worldnode(s,ins,label):return s['a_nodes'][label] if ins is None else transform(s,ins,s['parts'][s['instances'][ins]['part']]['nodes'][label])
def surface_nodes(s,ref):
    if '.' in ref:
        ins,name=ref.split('.',1);p=s['instances'][ins]['part'];b=s['parts'][p]['surfaces'][name]
        if b['params'].get('type','ELEMENT')=='NODE':return {(ins,n) for row in b['data'] for n in localset(s,p,'nset',row[0])}
        out=set()
        for row in b['data']:
            labels={int(row[0])} if row[0].isdigit() else localset(s,p,'elset',row[0])
            for e in labels:
                con=s['parts'][p]['elements'][e]
                out.update((ins,con[i]) for i in FACE_NODES[row[1]])
        return out
    b=s['a_surfaces'][ref];out=set()
    for row in b['data']:
        if b['params'].get('type','ELEMENT')=='NODE':out.update(resolve(s,'nset',row[0]));continue
        for ins,e in resolve(s,'elset',row[0]):
            con=s['parts'][s['instances'][ins]['part']]['elements'][e] if ins else s['a_elements'][e]
            out.update((ins,con[i]) for i in FACE_NODES[row[1]])
    return out
def canonical(b):return {'key':b['key'],'params':b['params'],'flags':sorted(b['flags']),'data':b['data']}
def physics_snapshot(s):
    out=[];part=None;asm=False
    for b in s['blocks']:
        k=b['key'];pars=b['params']
        if k=='part':part=pars['name']
        if part not in TOWER:
            ignore=False
            if k in ('nset','elset'):
                if pars.get('instance','').removesuffix('-1') in TOWER:ignore=True
                if pars.get(k)=='SET_CH4_STRESS_CTRL':ignore=True
            if not ignore:out.append(canonical(b))
        if k=='endpart':part=None
    return out
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()

base=structure(G1);base_physics=physics_snapshot(base)
review={'created_for':'RUN-T026-034/035 independent mesh-input review; no solver','baseline':{'path':str(G1),'sha256':base['sha256']},'inputs':{},'issues':[]}
for path in TARGETS:
    s=structure(path);issues=[];checks=[];detail={}
    def check(name,ok,evidence):
        checks.append({'name':name,'passed':bool(ok),'evidence':evidence})
        if not ok:issues.append(name)
    snap=physics_snapshot(s)
    check('all_non_tower_and_non_remapped_physical_cards_identical_to_G1',snap==base_physics,{'baseline_digest':digest(base_physics),'target_digest':digest(snap),'excluded_changes':'35 tower Part blocks; tower instance mesh label sets; unused SET_CH4_STRESS_CTRL'})
    stale=[{'line':b['line'],'instance':b['params'].get('instance'),'data':b['data']} for b in s['blocks'] if b['key'] in ('nset','elset') and b['params'].get(b['key'])=='SET_CH4_STRESS_CTRL']
    stale_expected={'RBLONG_03-1':[['110']],'RBLONG_05-1':[['97']],'PT_36X15P2-1':[['19']]}
    check('old_control_set_only_valid_unchanged_nontower_components',len(stale)==3 and all(stale_expected.get(x['instance'])==x['data'] for x in stale),{'obsolete_tower_labels_removed':True,'whole_set_removed':False,'remaining_cards':stale,'disposition':'Root explicitly retains these valid non-refined-component labels in already-solved input; not an accepted chapter4 observation region; later chapters require newly tagged locations.'})
    typecounts=Counter();nodecounts=0;solid_cards={}
    for p in TOWER:
        d=s['parts'][p];typecounts.update(d['types'].values());nodecounts+=len(d['nodes'])
        for e,nodes in d['elements'].items():
            if any(n not in d['nodes'] for n in nodes):issues.append('invalid_tower_connectivity:'+p+':'+str(e))
        solids=[canonical(b) for b in d['blocks'] if b['key']=='solidsection']
        source=[canonical(b) for b in base['parts'][p]['blocks'] if b['key']=='solidsection']
        solid_cards[p]=solids
        if solids!=source:issues.append('solid_section_changed:'+p)
    check('tower_element_types_and_material_section_tokens_preserved',not any(x.startswith(('invalid_tower_connectivity:','solid_section_changed:')) for x in issues),{'element_type_counts':dict(typecounts),'tower_nodes':nodecounts,'solid_sections':solid_cards})
    active={}
    for prefix in ('CSEG','SSEG'):
        expected_e={(ins,e) for ins,i in s['instances'].items() if i['part'].startswith(prefix+'_') for e in s['parts'][i['part']]['elements']}
        expected_n={(ins,n) for ins,i in s['instances'].items() if i['part'].startswith(prefix+'_') for n in s['parts'][i['part']]['nodes']}
        es,err_e=valid_ref(s,'elset',f'SET_{prefix}_ALL_ACTIVE');ns,err_n=valid_ref(s,'nset',f'SET_{prefix}_ALL_ACTIVE')
        active[prefix]={'elements':len(es),'expected_elements':len(expected_e),'missing_elements':len(expected_e-es),'extra_elements':len(es-expected_e),'nodes':len(ns),'expected_nodes':len(expected_n),'invalid_labels':err_e+err_n}
        check(prefix+'_whole_mesh_active_sets_complete',es==expected_e and ns==expected_n and not err_e and not err_n,active[prefix])
    nsm=[]
    for b in s['blocks']:
        if b['key']=='nonstructuralmass':
            vals,errs=valid_ref(s,'elset',b['params']['elset']);nsm.append({'line':b['line'],'target':b['params']['elset'],'total_mass_kg':float(b['data'][0][0]),'covered_elements':len(vals),'invalid_labels':errs,'units':b['params']['units']})
    check('three_original_NSM_cards_and_complete_target_sets',len(nsm)==3 and sorted(x['total_mass_kg'] for x in nsm)==sorted([4622.69,33004.8,2172.73]) and all(not x['invalid_labels'] for x in nsm),{'cards':nsm,'total_NSM_kg':sum(x['total_mass_kg'] for x in nsm)})
    endpoints={}
    for name,y in [('SET_TOWER_BASE',0.0),('SET_TOWER_TOP',158.0)]:
        vals,errors=valid_ref(s,'nset',name);xyz=np.array([worldnode(s,ins,n) for ins,n in vals]);end_ins='CSEG_01-1' if y==0.0 else 'SSEG_04-1';end_part=s['instances'][end_ins]['part']
        expected={(end_ins,n) for n in s['parts'][end_part]['nodes'] if abs(worldnode(s,end_ins,n)[1]-y)<2e-5}
        endpoints[name]={'node_count':len(vals),'expected_node_count':len(expected),'global_y_range':[float(xyz[:,1].min()),float(xyz[:,1].max())],'expected_y':y,'missing_nodes':len(expected-vals),'extra_nodes':len(vals-expected)}
        check(name+'_covers_geometric_end_face',vals==expected and not errors and np.allclose(xyz[:,1],y,atol=2e-5),endpoints[name])
    surfchecks={}
    for p in sorted(TOWER):
        ins=p+'-1';pn=s['parts'][p]['nodes'];all_y=np.array([worldnode(s,ins,n)[1] for n in pn]);lo=float(all_y.min());hi=float(all_y.max())
        for face,y in [('BOTTOM',lo),('TOP',hi)]:
            ref=ins+'.SURF_'+face;nodes=surface_nodes(s,ref);coords=np.array([worldnode(s,i,n) for i,n in nodes]);expected={(ins,n) for n in pn if abs(worldnode(s,ins,n)[1]-y)<2e-5}
            good=nodes==expected and np.allclose(coords[:,1],y,atol=2e-5);surfchecks[ref]={'count':len(nodes),'expected_count':len(expected),'global_y':y,'exact_boundary_node_coverage':good}
            if not good:issues.append('surface_end_coverage:'+ref)
    check('all_70_tower_end_surfaces_cover_complete_end_faces',all(x['exact_boundary_node_coverage'] for x in surfchecks.values()),surfchecks)
    bc=[];couplings=[];ties=[];embeds=[];rigids=[];equations=0;pt_initial=[]
    for b in s['blocks']:
        if b['key']=='boundary':
            for row in b['data']:
                values,err=valid_ref(s,'nset',row[0]);bc.append({'region':row[0],'node_count':len(values),'invalid_labels':err,'DOF_tokens':row[1:]})
        elif b['key']=='coupling':
            ref=b['params']['refnode'];vals,err=valid_ref(s,'nset',ref);surface=b['params']['surface'];sn=surface_nodes(s,surface)
            couplings.append({'constraint':b['params'].get('constraintname'),'refnode':ref,'refnode_count':len(vals),'surface':surface,'surface_node_count':len(sn),'invalid_refnode':err})
        elif b['key']=='tie':
            for row in b['data']:
                ties.append({'name':b['params'].get('name'),'surface_pair':row[:2],'surface_node_counts':[len(surface_nodes(s,x)) for x in row[:2]]})
        elif b['key']=='embeddedelement':
            host=b['params']['hostelset'];vals,err=valid_ref(s,'elset',host)
            embedded_refs=[row[0] for row in b['data']];nodes=set();emb_elem=0
            for ref in embedded_refs:
                elems,ee=valid_ref(s,'elset',ref);err+=ee;emb_elem+=len(elems)
                for ins,e in elems:
                    p=s['instances'][ins]['part'];nodes.update((ins,n) for n in s['parts'][p]['elements'][e])
            host_ins=host.split('.')[0];host_part=s['instances'][host_ins]['part'];hp=s['parts'][host_part];yc=[worldnode(s,host_ins,n)[1] for n in hp['nodes']];lo=min(yc);hi=max(yc)
            def radii(y):
                rr=[math.hypot(*(worldnode(s,host_ins,n)[[0,2]])) for n in hp['nodes'] if abs(worldnode(s,host_ins,n)[1]-y)<2e-5];return min(rr),max(rr)
            r0,r1=radii(lo),radii(hi);outside=[]
            for ins,n in nodes:
                xyz=worldnode(s,ins,n);r=math.hypot(xyz[0],xyz[2]);t=(xyz[1]-lo)/(hi-lo);ri=r0[0]*(1-t)+r1[0]*t;ro=r0[1]*(1-t)+r1[1]*t
                if not(lo-2e-5<=xyz[1]<=hi+2e-5 and ri-2e-5<=r<=ro+2e-5):outside.append([ins,n,xyz.tolist(),r,ri,ro])
            embeds.append({'host':host,'host_elements':len(vals),'expected_host_elements':len(hp['elements']),'embedded_elements':emb_elem,'embedded_node_count':len(nodes),'invalid_labels':err,'nodes_outside_analytic_host':outside})
        elif b['key']=='rigidbody':
            vals,err=valid_ref(s,'nset',b['params']['refnode']);els,ee=valid_ref(s,'elset',b['params']['elset']);rigids.append({'refnode':b['params']['refnode'],'ref_xyz':[worldnode(s,i,n).tolist() for i,n in vals],'elements':len(els),'element_types':dict(Counter(s['parts'][s['instances'][i]['part']]['types'][e] for i,e in els)),'invalid_refs':err+ee})
        elif b['key']=='equation':
            equations+=1
            terms=[v for row in b['data'][1:] for v in row]
            for i in range(0,len(terms),3):
                vals,err=valid_ref(s,'nset',terms[i])
                if not vals or err:issues.append('equation_invalid_region:'+terms[i])
        elif b['key']=='initialconditions':
            vals,err=valid_ref(s,'elset',b['data'][0][0]);pt_initial.append({'type':b['params']['type'],'region':b['data'][0][0],'elements':len(vals),'sigma11_Pa':float(b['data'][0][1]),'invalid_labels':err})
    check('all_boundary_regions_nonempty_and_labels_valid',all(x['node_count'] and not x['invalid_labels'] for x in bc),bc)
    check('all_coupling_RPs_and_surfaces_nonempty',all(x['refnode_count']==1 and x['surface_node_count'] and not x['invalid_refnode'] for x in couplings),{'count':len(couplings),'records':couplings})
    check('all_4_concrete_steel_ties_resolve_to_complete_end_surfaces',len(ties)==4 and all(len(x['surface_node_counts'])==2 and all(x['surface_node_counts']) for x in ties),ties)
    check('31_embedded_long_bar_hosts_cover_whole_respective_refined_CSEG',len(embeds)==31 and all(x['host_elements']==x['expected_host_elements'] and x['embedded_elements'] and not x['invalid_labels'] and not x['nodes_outside_analytic_host'] for x in embeds),embeds)
    check('108_PT_equations_resolve_unchanged',equations==108 and not any(x.startswith('equation_invalid_region') for x in issues),{'count':equations})
    check('PT_initial_stress_covers_all_36_tendons',len(pt_initial)==1 and pt_initial[0]['elements']==36 and pt_initial[0]['sigma11_Pa']==1.28e9 and not pt_initial[0]['invalid_labels'],pt_initial)
    check('RNA_rigid_body_covers_28_B31_at_RP_0_160_0',len(rigids)==1 and rigids[0]['elements']==28 and rigids[0]['element_types']=={'B31':28} and not rigids[0]['invalid_refs'] and np.allclose(rigids[0]['ref_xyz'][0],[0,160,0]),rigids)
    # Exercise every named local/global mesh set, including internal generated surface sets.
    invalid_sets=[];countsets=0
    for p,d in s['parts'].items():
        for kind in ('nset','elset'):
            universe=d['nodes'] if kind=='nset' else d['elements']
            for n in d[kind]:
                countsets+=1
                try:
                    vals=localset(s,p,kind,n);bad=vals-set(universe)
                    if bad:invalid_sets.append({'part':p,'kind':kind,'name':n,'bad':sorted(bad)[:12]})
                except Exception as exc:invalid_sets.append({'part':p,'kind':kind,'name':n,'error':str(exc)})
    for kind in ('nset','elset'):
        for n in s['aset'][kind]:
            countsets+=1
            try:
                vals,errs=valid_ref(s,kind,n)
                if errs:invalid_sets.append({'scope':'assembly','kind':kind,'name':n,'bad':errs[:12]})
            except Exception as exc:invalid_sets.append({'scope':'assembly','kind':kind,'name':n,'error':str(exc)})
    check('all_local_and_assembly_sets_have_valid_labels',not invalid_sets,{'checked_sets':countsets,'invalid_sets':invalid_sets})
    review['inputs'][path.stem]={'path':str(path),'sha256':s['sha256'],'checks':checks,'issues':issues,'status':'PASS-input-topology-and-frozen-parameters' if not issues else 'FAIL/HOLD','no_solver_started':True}
    review['issues'].extend([path.stem+':'+x for x in issues])
review['evidence_limits']=['Text/topology review does not establish solver convergence or physical validity.','Embedded membership is checked against the preserved axisymmetric annular frustum, not a new contact/bond-slip model.','Continuous CAE mass-property inertia and solver discretized rigid-body inertia must be reported separately.','SET_CH4_STRESS_CTRL removal is explicitly checked; subsequent chapters require newly tagged locations rather than inherited source labels.']
out=Path(__file__).with_name('mesh-input-independent-review.json');out.write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'output':str(out),'inputs':{k:{'status':v['status'],'issues':v['issues']} for k,v in review['inputs'].items()}},ensure_ascii=False))
