import sys, csv
from pathlib import Path
import numpy as np
sys.path.insert(0, r'D:/Codex-research-native')
import fast_output_file as fo

root=Path(r'D:/Codex-research-native/openfast-36-r2-data-20261006/CASES')
out=Path(r'D:/Codex-research-native/openfast-36-r2-data-20261006/openfast_36_tower_base_loads.csv')
channels=['TwrBsFxt','TwrBsFyt','TwrBsFzt','TwrBsMxt','TwrBsMyt','TwrBsMzt']
rows=[]
for case in sorted(root.iterdir()):
    f=case/'DTU_10MW_RWT.outb'
    if not f.exists(): continue
    data,info=fo.load_binary_output(str(f))
    names=info['attribute_names']; idx=[names.index(c) for c in channels]
    units=[info['attribute_units'][i] for i in idx]
    a=data[:,idx]
    row={'case':case.name,'samples':len(a),'units':'/'.join(units)}
    for j,c in enumerate(channels):
        x=a[:,j]
        row[c+'_min']=float(np.min(x)); row[c+'_max']=float(np.max(x)); row[c+'_rms']=float(np.sqrt(np.mean(x*x)))
    rows.append(row)
fields=list(rows[0])
with out.open('w',newline='',encoding='utf-8-sig') as g:
    w=csv.DictWriter(g,fieldnames=fields); w.writeheader(); w.writerows(rows)
print(f'{len(rows)} cases -> {out}')
print('channels:', ', '.join(f'{c} ({u})' for c,u in zip(channels,units)))
