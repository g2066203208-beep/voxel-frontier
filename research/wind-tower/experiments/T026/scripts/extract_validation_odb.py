from odbAccess import openOdb
import json,os,csv,traceback,bisect,sys
ROOT=r'C:/Users/REME/Documents/Codex/2026-10-03/lia/work/chapter2-completion'
manifest=json.load(open(os.path.join(ROOT,'run-manifest.json'),encoding='utf-8'))
report=[]
if len(sys.argv)>1:
    previous=os.path.join(ROOT,'solver-output-summary.json')
    if os.path.exists(previous):report=json.load(open(previous,encoding='utf8'))
for r in manifest['runs']:
    if len(sys.argv)>1 and r['job']!=sys.argv[1]:continue
    sta=os.path.join(r['directory'],r['job']+'.sta')
    if not os.path.exists(sta) or 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in open(sta,errors='replace').read():continue
    odb=None; entry={'run_id':r['run_id'],'job':r['job']}
    try:
        path=os.path.join(r['directory'],r['job']+'.odb')
        odb=openOdb(path=path,readOnly=True)
        rows=[]
        for stepname,step in odb.steps.items():
            energies={}
            for region in step.historyRegions.values():
                for name,h in region.historyOutputs.items():
                    if name.startswith('ALL') and h.data:
                        data=list(h.data);energies[name]=([p[0] for p in data],[p[1] for p in data])
            for f in step.frames:
                row={'step':stepname,'time':f.frameValue,'incrementNumber':f.incrementNumber}
                for field in ('S','E','EE','PE','PEEQT','PEEQ','DAMAGET','DAMAGEC','SDEG'):
                    if field in f.fieldOutputs:
                        vals=f.fieldOutputs[field].values
                        if vals:
                            first=vals[0].data
                            if not hasattr(first,'__len__'):row[field]=float(first)
                            else:
                                for i,x in enumerate(first):row[field+str(i+1)]=x
                for field in ('U','RF'):
                    if field in f.fieldOutputs:
                        for v in f.fieldOutputs[field].values:
                            for i,x in enumerate(v.data):row[field+str(i+1)+'_n'+str(v.nodeLabel)]=x
                for name,(times,values) in energies.items():
                    idx=bisect.bisect_left(times,f.frameValue)
                    idx=min(idx,len(times)-1)
                    if idx>0 and abs(times[idx-1]-f.frameValue)<abs(times[idx]-f.frameValue):idx-=1
                    row[name]=values[idx]
                rows.append(row)
        csvpath=os.path.join(r['directory'],'extracted.csv')
        fields=sorted(set(k for row in rows for k in row))
        with open(csvpath,'w',newline='',encoding='utf-8') as file:
            w=csv.DictWriter(file,fieldnames=fields);w.writeheader();w.writerows(rows)
        entry.update(frames=len(rows),csv=csvpath,last=rows[-1],steps={s.name:len(s.frames) for s in odb.steps.values()},odb_version=str(odb.jobData.version))
    except Exception:entry['error']=traceback.format_exc()
    finally:
        if odb:odb.close()
    report=[old for old in report if old['job']!=entry['job']];report.append(entry)
with open(os.path.join(ROOT,'solver-output-summary.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2,ensure_ascii=False,default=float)
print(json.dumps([{'run_id':r['run_id'],'frames':r.get('frames'),'error':r.get('error')} for r in report],ensure_ascii=False))
