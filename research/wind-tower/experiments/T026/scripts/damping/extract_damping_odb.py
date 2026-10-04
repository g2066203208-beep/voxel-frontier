from odbAccess import openOdb
import csv
import hashlib
import json
import traceback
from pathlib import Path

ROOT=Path('D:/Codex-research-validation/T026/damping')
manifest=json.loads((ROOT/'damping-run-manifest.json').read_text(encoding='utf-8'))
records=[]
for run in manifest['runs']:
    if run['status'] not in ('solver-completed-awaiting-verification','verification-passed','verification-failed'):
        continue
    odb=None
    record={'run_id':run['run_id'],'job':run['job'],'readOnly':True}
    try:
        odbpath=Path(run['directory'])/(run['job']+'.odb')
        odb=openOdb(path=str(odbpath),readOnly=True)
        record['odb_path']=str(odbpath)
        record['odb_sha256']=hashlib.sha256(odbpath.read_bytes()).hexdigest()
        record['odb_version']=str(odb.jobData.version)
        record['steps']={sname:{'procedure':str(step.procedure),'frames':len(step.frames),'history_regions':list(step.historyRegions.keys())} for sname,step in odb.steps.items()}
        record['histories']={}
        for sname,step in odb.steps.items():
            histories={}
            owners={}
            for region_key,region in step.historyRegions.items():
                for output_name,output in region.historyOutputs.items():
                    if output_name in ('U1','V1','A1','ALLSE','ALLKE','ALLVD','ALLWK','ETOTAL'):
                        if output_name in histories:
                            raise RuntimeError('Ambiguous history '+output_name+' in '+sname)
                        histories[output_name]=[[float(t),float(v)] for t,v in output.data]
                        owners[output_name]=region_key
            record['histories'][sname]={'data':histories,'owners':owners}
        free=record['histories']['Free']['data']
        times=[p[0] for p in free['U1']]
        fields=['time','U1','V1','A1','ALLSE','ALLKE','ALLVD','ALLWK','ETOTAL']
        rows=[]
        for index,time in enumerate(times):
            row={'time':time}
            for name in fields[1:]:
                points=free.get(name,[])
                if len(points)==len(times) and abs(points[index][0]-time)<1e-10:
                    row[name]=points[index][1]
                else:
                    row[name]=''
            rows.append(row)
        destination=Path(run['directory'])/'free-history.csv'
        with destination.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        record['history_csv']=str(destination)
        record['history_csv_sha256']=hashlib.sha256(destination.read_bytes()).hexdigest()
        record['tip_owner']=record['histories']['Free']['owners'].get('U1')
    except Exception:
        record['error']=traceback.format_exc()
    finally:
        if odb:
            odb.close()
    records.append(record)
(ROOT/'damping-extracted.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps([{'run_id':r['run_id'],'steps':r.get('steps'),'error':r.get('error')} for r in records],indent=2))
