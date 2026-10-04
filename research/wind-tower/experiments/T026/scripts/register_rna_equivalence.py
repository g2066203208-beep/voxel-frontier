from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parent
mp=ROOT/'run-manifest.json';m=json.loads(mp.read_text(encoding='utf8'))
base=next(r for r in m['runs'] if r['run_id']=='RUN-T026-032')
props=json.loads((ROOT/'rna-discrete-inertia-comparison.json').read_text(encoding='utf8'))
source=Path(base['input']).read_text()
partname='RNA_MASS_SKELETON_OFFICIAL'
s=re.sub(r'^\*Part, name='+partname+r'\n.*?^\*End Part\s*\n','',source,flags=re.M|re.S)
s=re.sub(r'^\*Instance, name='+partname+r'-1,.*?^\*End Instance\s*\n','',s,flags=re.M|re.S)
s=re.sub(r'^\*Rigid Body, ref node=SET_RNA_RP, elset='+partname+r'-1.SET_ALL_WIRES\s*\n','',s,flags=re.M)
assert partname not in s
cg=props['CG_m']; mass=props['mass_kg']
for runid,label,key in [('RUN-T026-036','EQUIV','ROTARYI_input_discrete_about_CG'),('RUN-T026-037','CONTINUOUS','ROTARYI_input_continuous_about_CG')]:
    assert not any(r['run_id']==runid for r in m['runs'])
    inertia=props[key]
    block='''*Part, name=RNA_SPATIAL_POINT
*Node
1, %s
*Element, type=MASS, elset=RNA_TRANSLATIONAL_MASS
1,1
*Element, type=ROTARYI, elset=RNA_ROTATIONAL_INERTIA
2,1
*Nset, nset=CG
1,
*Mass,elset=RNA_TRANSLATIONAL_MASS
%.16g
*Rotary Inertia,elset=RNA_ROTATIONAL_INERTIA
%s
*End Part
''' % (','.join('%.16g'%x for x in cg),mass,','.join('%.16g'%x for x in inertia))
    text=s.replace('*Assembly, name=Assembly',block+'*Assembly, name=Assembly',1)
    text=text.replace('*Assembly, name=Assembly\n','*Assembly, name=Assembly\n*Instance,name=RNA_SPATIAL_POINT-1,part=RNA_SPATIAL_POINT\n*End Instance\n',1)
    coupling='''*Surface,type=NODE,name=RNA_CG_POINT
RNA_SPATIAL_POINT-1.CG,1.
*Coupling,constraint name=RNA_CG_RIGID,ref node=SET_RNA_RP,surface=RNA_CG_POINT
*Kinematic
1,6
'''
    text=text.replace('*End Assembly',coupling+'*End Assembly',1)
    text=re.sub(r'^\*Heading\n[^*]*','*Heading\nT026 RNA '+label+' spatial mass test, same reconstructed G1 tower\n',text,flags=re.M)
    job='DTU158_RNA_'+label+'_G1';d=Path('D:/Codex-research-validation/T026/tower')/job;d.mkdir(exist_ok=True);inp=d/(job+'.inp');inp.write_text(text,encoding='ascii')
    rec={k:v for k,v in base.items() if k not in ['started','finished','output_files','process_returncode','completion_evidence']}
    rec.update(run_id=runid,baseline_id='DTU158-T026-RNA-'+label+'-G1',job=job,directory=str(d),input=str(inp),input_hash=hashlib.sha256(inp.read_bytes()).hexdigest(),status='registered-not-started',output_hash='',notes='Same mass/CG; discrete actual inertia equivalence' if label=='EQUIV' else 'Same mass/CG; continuous mathematical inertia sensitivity, not calibrated physical RNA',changed_variables={'RNA_representation':label,'mass_kg':mass,'CG_m':cg,'ROTARYI_tensor_order':props['ROTARYI_keyword_order'],'ROTARYI_values':inertia},acceptance={'equivalence_frequency_relative':1e-4,'equivalence_static_displacements_relative':1e-4,'equivalence_mass_relative':1e-6,'inertia_sensitivity':'report measured differences, no pass threshold or physical calibration claim','reason':'solver printed frequency resolution and alternative constraint assembly; physically identical discrete mass before sensitivity'},time_window=base['time_window'])
    m['runs'].append(rec);(d/'ResearchCard.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf8')
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
print('Registered RNA 036 discrete equivalence and 037 continuous sensitivity')
