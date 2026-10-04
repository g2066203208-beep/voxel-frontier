from odbAccess import openOdb
import json,os,csv,sys,collections
ROOT=r'C:/Users/REME/Documents/Codex/2026-10-03/lia/work/chapter2-completion'
manifest=json.load(open(os.path.join(ROOT,'run-manifest.json'),encoding='utf8'))
records=[r for r in manifest['runs'] if r['run_id'] in sys.argv[1:]]
reports=[]
for r in records:
    odb=openOdb(path=os.path.join(r['directory'],r['job']+'.odb'),readOnly=True)
    report={'run_id':r['run_id'],'job':r['job'],'steps':{},'instances':{n:{'nodes':len(i.nodes),'elements':len(i.elements)} for n,i in odb.rootAssembly.instances.items()},'nodeSets':list(odb.rootAssembly.nodeSets.keys())}
    coords={(n,x.label):x.coordinates for n,i in odb.rootAssembly.instances.items() for x in i.nodes}
    for x in getattr(odb.rootAssembly,'nodes',[]):coords[('ASSEMBLY',x.label)]=x.coordinates
    rp=odb.rootAssembly.nodeSets['SET_RNA_RP']
    for sname,step in odb.steps.items():
        history={rn:{hn:list(h.data or []) for hn,h in reg.historyOutputs.items()} for rn,reg in step.historyRegions.items()}
        frames=[]
        for i,f in enumerate(step.frames):
            info={'frame':i,'time':f.frameValue,'frequency':getattr(f,'frequency',None),'mode':getattr(f,'mode',None)}
            if 'U' in f.fieldOutputs:
                info['RNA_U']=[list(v.data) for v in f.fieldOutputs['U'].getSubset(region=rp).values]
            if 'RF' in f.fieldOutputs:
                values=[]
                for v in f.fieldOutputs['RF'].values:
                    data=tuple(float(x) for x in v.data)
                    iname=v.instance.name if v.instance is not None else 'ASSEMBLY'
                    if any(abs(x)>1e-6 for x in data):values.append({'instance':iname,'node':v.nodeLabel,'RF':data,'coord':coords.get((iname,v.nodeLabel))})
                info['nonzero_reactions']=values
            if sname=='Gravity' and i==len(step.frames)-1:
                pt=odb.rootAssembly.instances['PT_36X15P2-1']
                if 'S' in f.fieldOutputs:info['PT_S']=[float(v.data[0]) for v in f.fieldOutputs['S'].getSubset(region=pt).values]
                for name in ('DAMAGET','DAMAGEC'):
                    if name in f.fieldOutputs:info['max_'+name]=max(float(v.data) for v in f.fieldOutputs[name].values)
            if sname=='Modal_From_Gravity' and f.mode in (1,2,3,4):
                displacement={(v.instance.name if v.instance is not None else 'ASSEMBLY',v.nodeLabel):v.data for v in f.fieldOutputs['U'].values}
                layers=collections.defaultdict(list)
                for key,coord in coords.items():
                    if key[0].startswith(('CSEG','SSEG')) and key in displacement:
                        layers[round(coord[1],4)].append(displacement[key])
                info['tower_section_average_U']=[{'height':h,'U':[sum(float(x[k]) for x in vals)/len(vals) for k in range(3)],'nodes':len(vals)} for h,vals in sorted(layers.items())]
            frames.append(info)
        report['steps'][sname]={'frames':frames,'history':history}
    odb.close();reports.append(report)
path=os.path.join(ROOT,'tower-results-'+records[0]['run_id']+'.json')
with open(path,'w',encoding='utf8') as f:json.dump(reports,f,indent=2,default=lambda v:v.tolist() if hasattr(v,'tolist') else float(v))
print(path)
print(json.dumps([{'job':r['job'],'frequencies':[f['frequency'] for f in r['steps']['Modal_From_Gravity']['frames'] if f['mode'] in (1,2,3,4)],'gravity_U':r['steps']['Gravity']['frames'][-1].get('RNA_U')} for r in reports],default=float))
