from odbAccess import openOdb
import json,sys

path=sys.argv[-2];output=sys.argv[-1]
odb=openOdb(path=path,readOnly=True)
result={'odb':path,'job_data':{'version':str(odb.jobData.version),'precision':str(odb.jobData.precision)},'steps':{}}
for name,step in odb.steps.items():
    entry={'frames':[],'history':{}}
    for frame in step.frames:
        row={'time':frame.frameValue,'nodes':{}}
        for quantity in ['U','UR','V','VR','A','AR','RF','RM']:
            if quantity not in frame.fieldOutputs:continue
            for value in frame.fieldOutputs[quantity].values:
                if value.nodeLabel not in (1,2):continue
                try:data=value.data
                except Exception:data=value.dataDouble
                row['nodes'].setdefault(str(value.nodeLabel),{})[quantity]=list(data)
        entry['frames'].append(row)
    for region_name,region in step.historyRegions.items():
        entry['history'][region_name]={key:list(value.data) for key,value in region.historyOutputs.items()}
    result['steps'][name]=entry
odb.close()
with open(output,'w') as stream:json.dump(result,stream,indent=2)
print('ODB extraction complete: '+output)
