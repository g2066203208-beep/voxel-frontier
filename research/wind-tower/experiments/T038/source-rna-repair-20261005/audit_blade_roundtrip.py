"""Read-only semantic audit of this specific flat DTU input and its one-instance export.

No solver/CAE invocation. Fail on unsupported instance/system transformations or
unknown connectivity formats rather than silently flattening them incorrectly.
"""
from pathlib import Path
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import json
import math
import struct

BASE = Path(__file__).resolve().parent
SOURCE = Path('D:/Codex-research-native/t026-rna-official-properties-20261004/structural_models/ABAQUS/refblade_master.inp')
EXPORTED = Path('D:/Codex-research-native/source-rna-repair-20261005/20261005_180633/RNA_REPAIR_S1_DTU_BLADE_STANDARD.inp')


def tokens(s):
    return [x.strip() for x in s.split(',')]


def values(data):
    return [float(v) for _, line in data for v in tokens(line) if v]


def blocks(path):
    rows = path.read_text(encoding='utf-8-sig').splitlines()
    result, current = [], None
    for line_no, row in enumerate(rows, 1):
        row = row.strip()
        if not row or row.startswith('**'):
            continue
        if row.startswith('*'):
            bits = tokens(row.upper())
            params, flags = {}, []
            for bit in bits[1:]:
                if '=' in bit:
                    k, v = bit.split('=', 1)
                    params[k.strip()] = v.strip()
                elif bit:
                    flags.append(bit)
            current = {'keyword': bits[0], 'params': params, 'flags': flags,
                       'data': [], 'file': str(path), 'line': line_no}
            result.append(current)
        else:
            assert current, (path, line_no)
            current['data'].append((line_no, row))
    expanded = []
    for block in result:
        if block['keyword'] == '*INCLUDE':
            # Input parameter path case comes from original text on Windows.
            expanded.extend(blocks(path.parent / block['params']['INPUT']))
        else:
            expanded.append(block)
    return expanded


def parse(path):
    bs = blocks(path)
    model = {'blocks': bs, 'nodes': {}, 'elements': {}, 'nsets': defaultdict(list),
             'elsets': defaultdict(list), 'orientations': {}, 'shell_sections': [],
             'solid_sections': [], 'materials': {}, 'surfaces': {}, 'couplings': {},
             'boundaries': [], 'steps': [], 'frequencies': [], 'systems': []}
    translation = [0., 0., 0.]
    material = None
    instances, parts = [], []
    for i, b in enumerate(bs):
        k, p, d = b['keyword'], b['params'], b['data']
        if k == '*PART':
            parts.append(p['NAME'])
        if k == '*INSTANCE':
            instances.append(p)
            assert not d, 'Instance has transformation; do not silently flatten'
        if k == '*SYSTEM':
            v = values(d)
            if not v:
                translation = [0., 0., 0.]
            else:
                assert len(v) in (3, 6), 'Unsupported SYSTEM definition'
                translation = v[:3]
                if len(v) == 6:
                    delta = [v[j+3]-v[j] for j in range(3)]
                    assert all(abs(delta[j]-[1.,0.,0.][j]) < 1e-12 for j in range(3)), 'Non-translational SYSTEM'
            model['systems'].append({'line': b['line'], 'translation': translation[:]})
        elif k == '*NODE':
            labels = []
            for no, row in d:
                v = [float(x) for x in tokens(row) if x]
                assert len(v) == 4 and v[0].is_integer()
                label = int(v[0]); assert label not in model['nodes']
                model['nodes'][label] = [v[j+1]+translation[j] for j in range(3)]
                labels.append(label)
            if 'NSET' in p:
                model['nsets'][p['NSET']].extend(labels)
        elif k == '*ELEMENT':
            etype = p['TYPE']; nconn = {'S8R': 8, 'C3D20': 20}[etype]
            pending, labels = [], []
            for no, row in d:
                pending += [int(x) for x in tokens(row) if x]
                if len(pending) < nconn+1:
                    continue
                assert len(pending) == nconn+1, (etype, no)
                label = pending[0]; assert label not in model['elements']
                model['elements'][label] = [etype, pending[1:]]
                labels.append(label); pending = []
            assert not pending
            if 'ELSET' in p:
                model['elsets'][p['ELSET']].extend(labels)
        elif k in ('*NSET', '*ELSET'):
            repo = model['nsets' if k == '*NSET' else 'elsets']
            name = p[k[1:]]
            if 'INSTANCE' in p:
                assert p['INSTANCE'] == 'PART-1-1', 'Unexpected instance-qualified set'
            for no, row in d:
                v = [s.upper() for s in tokens(row) if s]
                if 'GENERATE' in b['flags']:
                    assert len(v) == 3
                    start, end, inc = map(int, v)
                    repo[name].extend(range(start, end+1, inc))
                else:
                    repo[name].extend(int(s) if s.isdigit() else s for s in v)
        elif k == '*ORIENTATION':
            xyz = [float(x) for x in tokens(d[0][1]) if x]
            xyz += [0.]*(9-len(xyz))
            axis_angle = [float(x) for x in tokens(d[1][1]) if x] if len(d)>1 else [1.,0.]
            assert len(xyz) == 9 and len(axis_angle) == 2
            model['orientations'][p['NAME']] = {'system':p.get('SYSTEM','RECTANGULAR'), 'definition':p.get('DEFINITION','COORDINATES'), 'axes_origin':xyz, 'axis_angle':axis_angle}
        elif k == '*SHELL SECTION':
            assert 'COMPOSITE' in b['flags']
            plies = []
            for no, row in d:
                t = tokens(row)
                plies.append({'thickness':float(t[0]), 'integration_points':int(t[1]), 'material':t[2].upper(), 'angle':float(t[3]), 'ply_name':t[4].upper() if len(t)>4 else ''})
            model['shell_sections'].append({'line':b['line'], 'file':b['file'], 'elset':p['ELSET'], 'orientation_name':p['ORIENTATION'], 'offset':float(p.get('OFFSET',0)), 'plies':plies, 'extra_params':{key:v for key,v in p.items() if key not in ('ELSET','ORIENTATION','OFFSET','LAYUP')}, 'flags':sorted(b['flags'])})
        elif k == '*SOLID SECTION':
            model['solid_sections'].append({'line':b['line'], 'elset':p['ELSET'], 'material':p['MATERIAL'], 'orientation_name':p.get('ORIENTATION'), 'data':values(d)})
        elif k == '*MATERIAL':
            material = p['NAME']; model['materials'][material] = {}
        elif k in ('*DENSITY','*ELASTIC'):
            pp = dict(p)
            if k == '*ELASTIC':
                pp['TYPE'] = pp.get('TYPE','ISOTROPIC')
                if pp['TYPE'] == 'ISO': pp['TYPE'] = 'ISOTROPIC'
            model['materials'][material][k] = {'params':pp, 'data':values(d), 'line':b['line']}
        elif k == '*SURFACE':
            assert p.get('TYPE') == 'NODE'
            model['surfaces'][p['NAME']] = [(tokens(row)[0].upper(), float(tokens(row)[1]) if len(tokens(row))>1 and tokens(row)[1] else 1.) for no,row in d]
        elif k == '*COUPLING':
            mode = bs[i+1]; assert mode['keyword'] in ('*KINEMATIC','*DISTRIBUTING')
            dofs = []
            for no,row in mode['data']:
                t=[int(x) for x in tokens(row) if x]
                dofs.extend(range(t[0],(t[1] if len(t)>1 else t[0])+1))
            model['couplings'][p['CONSTRAINT NAME']] = {'line':b['line'], 'ref':p['REF NODE'], 'surface':p['SURFACE'], 'type':mode['keyword'], 'dofs':sorted(dofs) if dofs else [1,2,3,4,5,6], 'mode_params':mode['params'], 'extra_params':{key:v for key,v in p.items() if key not in ('CONSTRAINT NAME','REF NODE','SURFACE')}}
        elif k == '*BOUNDARY':
            for no,row in d:
                t=tokens(row); start=int(t[1]); end=int(t[2]) if len(t)>2 and t[2] else start; value=float(t[3]) if len(t)>3 and t[3] else 0.
                model['boundaries'].extend((t[0].upper(),dof,value) for dof in range(start,end+1))
        elif k == '*STEP':
            model['steps'].append({'line':b['line'], 'params':p, 'flags':b['flags']})
        elif k == '*FREQUENCY':
            model['frequencies'].append({'line':b['line'], 'params':p, 'flags':b['flags'], 'data':values(d)})
    assert len(parts) <= 1 and len(instances) <= 1, 'Only a single untransformed instance is supported'
    model['parts']=parts; model['instances']=instances

    @lru_cache(None)
    def resolve(kind, name):
        if name.isdigit(): return frozenset([int(name)])
        repo=model[kind]; out=set()
        assert name in repo, ('Undefined set', kind, name)
        for item in repo[name]:
            if isinstance(item,int): out.add(item)
            else:
                assert item != name, 'Self-referencing set'
                out.update(resolve(kind,item))
        return frozenset(out)

    model['resolved_nsets']={name:sorted(resolve('nsets',name)) for name in model['nsets']}
    model['resolved_elsets']={name:sorted(resolve('elsets',name)) for name in model['elsets']}
    shell_assignments, solid_assignments=defaultdict(list),defaultdict(list)
    for section in model['shell_sections']:
        section['orientation']=model['orientations'][section['orientation_name']]
        for eid in resolve('elsets',section['elset']): shell_assignments[eid].append(section)
    for section in model['solid_sections']:
        section['orientation']=model['orientations'][section['orientation_name']] if section['orientation_name'] else None
        for eid in resolve('elsets',section['elset']): solid_assignments[eid].append(section)
    model['shell_assignments']=dict(shell_assignments); model['solid_assignments']=dict(solid_assignments)
    for coupling in model['couplings'].values():
        coupling['ref_nodes']=sorted(resolve('nsets',coupling['ref']))
        weighted=defaultdict(list)
        for name,weight in model['surfaces'][coupling['surface']]:
            for nid in resolve('nsets',name): weighted[nid].append(weight)
        assert all(len(v)==1 for v in weighted.values()), 'Duplicate surface node entries'
        coupling['surface_nodes_weights']=sorted((nid,v[0]) for nid,v in weighted.items())
    model['resolved_boundaries']=sorted((nid,dof,value) for name,dof,value in model['boundaries'] for nid in resolve('nsets',name))
    return model


def artifact(path):
    return {'path':str(path), 'bytes':path.stat().st_size, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def section_signature(section):
    return {'offset':section['offset'], 'plies':[{k:v for k,v in p.items() if k!='ply_name'} for p in section['plies']], 'orientation':section['orientation'], 'extra_params':section['extra_params'], 'flags':section['flags']}


def compare():
    source, exported = parse(SOURCE), parse(EXPORTED)
    report={'scope':'Read-only source/export semantic audit. No CAE invocation, solve, source edit or upload.', 'source':artifact(SOURCE), 'exported':artifact(EXPORTED), 'parser_constraints':['Exact S8R/C3D20 connectivity length','Single untransformed instance only','SYSTEM translations checked to have identity rotation','NODE surfaces with no duplicate entries','Explicit per-element ordered layer comparison independent of CAE group names']}
    report['keyword_counts']={name:dict(Counter(b['keyword'] for b in m['blocks'])) for name,m in [('source',source),('exported',exported)]}
    sn,en=source['nodes'],exported['nodes']; common=sorted(sn.keys()&en.keys())
    coord_diffs=[]
    for nid in common:
        v=[en[nid][j]-sn[nid][j] for j in range(3)]
        if any(v): coord_diffs.append({'node':nid,'source':sn[nid],'exported':en[nid],'max_abs_m':max(map(abs,v))})
    coord_diffs.sort(key=lambda x:x['max_abs_m'],reverse=True)
    report['nodes']={'source_count':len(sn),'exported_count':len(en),'missing_labels':sorted(sn.keys()-en.keys()),'added_labels':sorted(en.keys()-sn.keys()),'coordinates_not_exact_count':len(coord_diffs),'max_abs_coordinate_delta_m':coord_diffs[0]['max_abs_m'] if coord_diffs else 0,'coordinate_delta_examples':coord_diffs[:15]}
    coord_groups=Counter(); float32_errors=[]
    for diff in coord_diffs:
        nid=diff['node']; coord_groups['shell' if nid<=101394 else 'reference' if nid<=101496 else 'glue_added']+=1
        cast=[float(format(struct.unpack('f',struct.pack('f',x))[0],'.9g')) for x in sn[nid]]
        if cast!=en[nid]: float32_errors.append({'node':nid,'source':sn[nid],'exported':en[nid],'float32_9g':cast})
    report['nodes']['coordinate_changed_groups']=dict(coord_groups)
    report['nodes']['all_changed_coordinates_equal_source_cast_to_float32_and_formatted_9_significant_digits']=not float32_errors
    report['nodes']['float32_9g_mismatch_examples']=float32_errors[:8]
    report['elements']={'source_types':dict(Counter(x[0] for x in source['elements'].values())),'exported_types':dict(Counter(x[0] for x in exported['elements'].values())),'missing_labels':sorted(source['elements'].keys()-exported['elements'].keys()),'added_labels':sorted(exported['elements'].keys()-source['elements'].keys()),'type_or_ordered_connectivity_mismatches':[eid for eid in source['elements'].keys()&exported['elements'].keys() if source['elements'][eid]!=exported['elements'][eid]]}
    for kind,typ in [('shell','S8R'),('solid','C3D20')]:
        a,b=source[kind+'_assignments'],exported[kind+'_assignments']; expected={eid for eid,e in source['elements'].items() if e[0]==typ}
        info={'source_sections':len(source[kind+'_sections']),'exported_sections':len(exported[kind+'_sections']),'source_covered_elements':len(a),'exported_covered_elements':len(b),'source_missing':sorted(expected-a.keys()),'exported_missing':sorted(expected-b.keys()),'source_overlaps':[eid for eid,v in a.items() if len(v)!=1],'exported_overlaps':[eid for eid,v in b.items() if len(v)!=1],'source_unexpected':sorted(a.keys()-expected),'exported_unexpected':sorted(b.keys()-expected)}
        mismatch=[]; names_differ=0
        for eid in sorted(a.keys()&b.keys()):
            assert len(a[eid])==len(b[eid])==1
            aa,bb=a[eid][0],b[eid][0]
            if kind=='shell':
                va,vb=section_signature(aa),section_signature(bb)
                if aa['elset']!=bb['elset'] or aa['orientation_name']!=bb['orientation_name']: names_differ+=1
            else:
                va={k:aa[k] for k in ['material','orientation','data']}; vb={k:bb[k] for k in ['material','orientation','data']}
            if va!=vb: mismatch.append({'element':eid,'source_line':aa['line'],'exported_line':bb['line'],'source':va,'exported':vb})
        info['semantic_mismatch_count']=len(mismatch); info['semantic_mismatch_examples']=mismatch[:8]; info['element_assignment_or_orientation_name_changed_count']=names_differ
        report[kind+'_sections']=info
    material_diffs=[]; structure_diffs=[]
    for name in sorted(source['materials'].keys()|exported['materials'].keys()):
        a,b=source['materials'].get(name,{}),exported['materials'].get(name,{})
        if a.keys()!=b.keys(): structure_diffs.append(name)
        for keyword in a.keys()&b.keys():
            if a[keyword]['params']!=b[keyword]['params'] or len(a[keyword]['data'])!=len(b[keyword]['data']): structure_diffs.append(name+keyword)
            for j,(x,y) in enumerate(zip(a[keyword]['data'],b[keyword]['data'])):
                if x!=y: material_diffs.append({'material':name,'keyword':keyword,'component_index_1_based':j+1,'source':x,'exported':y,'absolute_delta':y-x,'relative_delta':(y-x)/x if x else None,'source_line':a[keyword]['line'],'exported_line':b[keyword]['line']})
    report['materials']={'source_names':sorted(source['materials']),'exported_names':sorted(exported['materials']),'structure_mismatches':structure_diffs,'numeric_differences':material_diffs,'source':source['materials'],'exported':exported['materials']}
    native_path=BASE/'native-blade-candidate.json'
    native=json.loads(native_path.read_text(encoding='utf-8'))
    native_numeric_diffs=[]
    for name,mat in source['materials'].items():
        for keyword,native_key in [('*DENSITY','density'),('*ELASTIC','elastic')]:
            native_values=[float(x) for row in native['materials'][name][native_key]['table'] for x in row]
            if native_values!=mat[keyword]['data']: native_numeric_diffs.append({'material':name,'property':native_key,'source':mat[keyword]['data'],'native':native_values})
    report['materials']['native_readback_evidence']=artifact(native_path)
    report['materials']['native_readback_numeric_mismatches']=native_numeric_diffs
    report['materials']['native_evidence_limit']='Read-only inspection of the creator-provided native JSON, not a second CAE invocation by this reviewer.'
    cc=[]
    for name in sorted(source['couplings'].keys()&exported['couplings'].keys()):
        a,b=source['couplings'][name],exported['couplings'][name]
        keys=['ref_nodes','surface_nodes_weights','type','dofs','mode_params','extra_params']
        diffs=[k for k in keys if a[k]!=b[k]]
        if diffs: cc.append({'name':name,'differing_fields':diffs})
    report['couplings']={'source_count':len(source['couplings']),'exported_count':len(exported['couplings']),'missing_names':sorted(source['couplings'].keys()-exported['couplings'].keys()),'added_names':sorted(exported['couplings'].keys()-source['couplings'].keys()),'semantic_mismatches':cc,'source_types':dict(Counter(c['type'] for c in source['couplings'].values())),'exported_types':dict(Counter(c['type'] for c in exported['couplings'].values())),'root_source':source['couplings']['COUPCON-001'],'root_exported':exported['couplings']['COUPCON-001']}
    report['boundary_conditions']={'identical_resolved_nodes_dofs_values':source['resolved_boundaries']==exported['resolved_boundaries'],'source':source['resolved_boundaries'],'exported':exported['resolved_boundaries']}
    report['analysis']={'source_steps':source['steps'],'exported_steps':exported['steps'],'source_frequency':source['frequencies'],'exported_frequency':exported['frequencies'],'requested_mode_count_preserved':source['frequencies'][0]['data'][0]==exported['frequencies'][0]['data'][0]==8}
    report['analysis']['official_frequency_reference']={'url':'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-frequency.htm','read_date':'2026-10-05','observed_defaults':['EIGENSOLVER=LANCZOS default','SIM=YES default','Mass normalization used with default SIM','ACOUSTIC COUPLING=ON default for Lanczos'],'interpretation':'Export spells out documented Abaqus 2025 defaults. This does not prove historical Abaqus versions used the same defaults or provide solved frequencies.'}
    report['organization']={'source_parts':source['parts'],'exported_parts':exported['parts'],'source_instances':source['instances'],'exported_instances':exported['instances'],'source_orientation_definition_count':len(source['orientations']),'exported_orientation_definition_count':len(exported['orientations'])}
    report['source_files']=[artifact(SOURCE.parent/x) for x in ['README.txt','refblade_master.inp','refblade_mesh.inp','refblade_materials.inp','refblade_layup.inp','refblade_te_glue.inp']]
    report['limitations']=['Text-level semantic comparison does not validate element Jacobians, stiffness, mass or eigenmodes.','Floating point coordinate/material serializer differences are reported explicitly, not silently accepted as exact equality.','Frequency options newly made explicit by CAE must be distinguished from proof of identical solver execution.','The source-model assumptions (no prebend, imperfect tip and glue density=1) remain inherited.','Original RNA integration/Explicit compatibility is outside this audit.']
    (BASE/'roundtrip-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['materials','couplings','source_files','keyword_counts']},ensure_ascii=False,indent=2))
    print('MATERIAL_DIFFERENCES',json.dumps(material_diffs,ensure_ascii=False))
    print('COUPLING_DIFFERENCES',json.dumps(cc,ensure_ascii=False))
    return report


if __name__=='__main__':
    compare()
