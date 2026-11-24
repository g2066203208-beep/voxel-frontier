import argparse, json, pathlib, re
p=argparse.ArgumentParser()
p.add_argument('--speed',type=float,required=True)
p.add_argument('--type',choices=['NTM','1ETM'],required=True)
p.add_argument('--grid',type=int,choices=[11,51],required=True)
p.add_argument('--duration',type=int,choices=[120,700],required=True)
p.add_argument('--out',type=pathlib.Path,required=True)
a=p.parse_args()
root=pathlib.Path(__file__).resolve().parent
src=(root/'TurbSim_reference.inp').read_text()
fields={'RandSeed1':'20261124','RandSeed2':'"RanLux"','WrADFF':'True','WrADHH':'True','WrADTWR':'True','ScaleIEC':'0','NumGrid_Z':str(a.grid),'NumGrid_Y':str(a.grid),'TimeStep':'0.05','AnalysisTime':str(a.duration),'UsableTime':'"ALL"','HubHt':'161.368806','GridHeight':'200','GridWidth':'200','VFlowAng':'0','HFlowAng':'0','TurbModel':'"IECKAI"','IECstandard':'"1-Ed3"','IECturbc':'"A"','IEC_WindType':'"'+a.type+'"','ETMc':'"default"','WindProfileType':'"default"','RefHt':'161.368806','URef':str(a.speed),'PLExp':'"default"','SCMod1':'"IEC"','InCDec1':'"12.0 0.000352733686067"'}
for key,value in fields.items():
    pat=r'^\s*[^\n]*?\s+'+re.escape(key)+r'\s+-.*$'
    # Match exactly one field line. Preserve the original field comment.
    matches=[i for i,l in enumerate(src.splitlines()) if re.search(r'\s'+re.escape(key)+r'\s+-',l)]
    if len(matches)!=1: raise ValueError((key,matches))
    lines=src.splitlines()
    tail=lines[matches[0]][re.search(r'\s'+re.escape(key)+r'\s+-',lines[matches[0]]).start():]
    lines[matches[0]]=value.ljust(15)+tail
    src='\n'.join(lines)+'\n'
a.out.mkdir(parents=True,exist_ok=True)
(a.out/'case.inp').write_text(src)
(a.out/'case_config.json').write_text(json.dumps({'speed':a.speed,'type':a.type,'grid':a.grid,'duration':a.duration,'fields':fields,'scope':'new native research case'},indent=2))
print('Generated',a.out,fields)
