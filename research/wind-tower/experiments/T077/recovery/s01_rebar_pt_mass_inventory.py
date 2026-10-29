#!/usr/bin/env python3
"""Static, reproducible T3D2 length/mass audit for a single S01 candidate INP.

No Abaqus, no physical PASS. Fails closed on input SHA and expected element sets.
"""
import argparse,csv,hashlib,io,json,math,re,sys,zipfile
from collections import defaultdict
from pathlib import Path

EXPECTED='22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
DENSITY=7850.0

def load_input(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.inp')]
        if len(names)!=1:raise ValueError('expected one INP in ZIP')
        raw=z.read(names[0]);sha=hashlib.sha256(raw).hexdigest()
        if sha!=EXPECTED:raise ValueError(f'INP SHA mismatch {sha}')
    return raw.decode('utf-8'),sha

def parse_part(block):
    nodes={};elements={};sections={};ranges={}
    mode=None
    for line in block.splitlines():
        s=line.strip()
        if not s or s.startswith('**'):continue
        if s.startswith('*'):
            upper=s.upper()
            if upper.startswith('*NODE'):mode='node'
            elif upper.startswith('*ELEMENT, TYPE=T3D2'):mode='element'
            elif upper.startswith('*ELSET,'):
                m=re.search(r'ELSET\s*=\s*([^,]+)',s,re.I)
                if not m:raise ValueError(s)
                mode=('elset',m.group(1).strip(), 'GENERATE' in upper)
                ranges[mode[1]]=[]
            elif upper.startswith('*SOLID SECTION,'):
                m=re.search(r'ELSET\s*=\s*([^,]+).*MATERIAL\s*=\s*([^,]+)',s,re.I)
                if not m:raise ValueError(s)
                mode=('section',m.group(1).strip(),m.group(2).strip())
            else:mode=None
            continue
        if mode=='node':
            a=s.split(',');nodes[int(a[0])]=tuple(map(float,a[1:4]))
        elif mode=='element':
            a=s.split(',');elements[int(a[0])]=(int(a[1]),int(a[2]))
        elif isinstance(mode,tuple) and mode[0]=='elset':
            a=[int(x) for x in s.split(',') if x.strip()]
            if mode[2]:
                if len(a)!=3:raise ValueError('bad elset generate')
                ranges[mode[1]].append((a[0],a[1],a[2]))
            else:
                for k in a:ranges[mode[1]].append((k,k,1))
        elif isinstance(mode,tuple) and mode[0]=='section':
            sections[mode[1]]=(float(s.split(',')[0]),mode[2]);mode=None
    return nodes,elements,sections,ranges

def instance_offsets(text):
    offsets={}
    for m in re.finditer(r'^\*Instance, name=([^\n]+), part=([^\n]+)\n(.*?)^\*End Instance',text,re.M|re.S|re.I):
        part=m.group(2).strip();data=[l.strip() for l in m.group(3).splitlines() if l.strip() and not l.strip().startswith('**')]
        if len(data)>1:raise ValueError(f'unsupported rotated/multi-line instance: {part}')
        offset=tuple(map(float,data[0].split(','))) if data else (0.,0.,0.)
        if len(offset)!=3:raise ValueError(f'bad translation for {part}')
        if part in offsets:raise ValueError(f'multiple instances for {part}')
        offsets[part]=offset
    return offsets

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('zip',type=Path);ap.add_argument('--csv',type=Path,required=True);ap.add_argument('--json',type=Path,required=True)
    args=ap.parse_args()
    text,sha=load_input(args.zip)
    offsets=instance_offsets(text)
    records=[];groups=defaultdict(lambda:{'elements':0,'length_m':0.,'mass_kg':0.,'first_moment_y_kgm':0.,'radial_second_moment_kgm2':0.})
    for pm in re.finditer(r'^\*Part, name=([^\n]+)\n(.*?)^\*End Part',text,re.M|re.S|re.I):
        name=pm.group(1).strip()
        if not(name.startswith('RBLONG_') or name.startswith('HOOP_TIE_CAGE') or name.startswith('PT_')):continue
        nodes,els,sections,ranges=parse_part(pm.group(2))
        if name not in offsets:raise ValueError(f'missing instance: {name}')
        ox,oy,oz=offsets[name]
        if not els:raise ValueError(f'{name} has no trusses')
        selected=set()
        for elset,(area,material) in sections.items():
            if material not in ('HRB400_D400_DIAGNOSTIC','STRAND_1860'):raise ValueError((name,material))
            group=('longitudinal' if name.startswith('RBLONG_') else 'pt' if name.startswith('PT_') else 'hoop' if 'HOOP' in elset else 'tie')
            length=mass=y1=jyy=0.;count=0
            for a,b,step in ranges[elset]:
                for k in range(a,b+1,step):
                    if k in selected:raise ValueError(f'duplicate element {name}:{k}')
                    selected.add(k)
                    n0,n1=els[k];x0,y0,z0=nodes[n0];x1,y1v,z1=nodes[n1]
                    x0+=ox;y0+=oy;z0+=oz;x1+=ox;y1v+=oy;z1+=oz
                    le=math.dist((x0,y0,z0),(x1,y1v,z1))
                    me=le*area*DENSITY
                    length+=le;mass+=me;y1+=me*(y0+y1v)/2
                    jyy+=me*((x0*x0+x0*x1+x1*x1)+(z0*z0+z0*z1+z1*z1))/3
                    count+=1
            rec=dict(part=name,group=group,elset=elset,material=material,area_m2=area,elements=count,length_m=length,mass_kg=mass,cg_y_m=y1/mass,jyy_origin_kgm2=jyy)
            records.append(rec)
            g=groups[group];g['elements']+=count;g['length_m']+=length;g['mass_kg']+=mass;g['first_moment_y_kgm']+=y1;g['radial_second_moment_kgm2']+=jyy
        if selected!=set(els):raise ValueError(f'unassigned T3D2 elements in {name}: {len(set(els)-selected)}')
    if len([r for r in records if r['group']=='longitudinal'])!=31:raise ValueError('expected 31 longitudinal parts')
    if len([r for r in records if r['group']=='pt'])!=1:raise ValueError('expected one PT part')
    if groups['pt']['elements']!=36:raise ValueError('expected 36 PT elements')
    if groups['hoop']['elements']!=201456 or groups['tie']['elements']!=12312:raise ValueError('unexpected cage topology')
    summary={}
    for group,g in sorted(groups.items()):
        summary[group]={"elements":g['elements'],"length_m":g['length_m'],"mass_kg":g['mass_kg'],"cg_y_m":g['first_moment_y_kgm']/g['mass_kg'],"jyy_origin_kgm2":g['radial_second_moment_kgm2']}
    summary['ordinary_rebar_mass_kg']=sum(summary[g]['mass_kg'] for g in ['longitudinal','hoop','tie'])
    summary['total_rebar_and_pt_mass_kg']=summary['ordinary_rebar_mass_kg']+summary['pt']['mass_kg']
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    with args.csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    payload={"status":"STATIC_GEOMETRIC_INVENTORY_ONLY_NOT_ABAQUS_PASS","input_sha256":sha,"density_kg_m3":DENSITY,"assumptions":["T3D2 centerline length times nominal section area; ignores end fixtures, overlaps and host displacement", "Material density 7850 kg/m3 for ordinary bars and strand", "Line-mass Jyy exact for straight T3D2 segments; no solid cross-section self-inertia", "Embedded-element host concrete mass not subtracted", "Part-instance translations applied to all line-mass centroids and Jyy; rotations unsupported/fail-closed"],"summary":summary,"rows":len(records),"csv_sha256":hashlib.sha256(args.csv.read_bytes()).hexdigest()}
    args.json.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(payload,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
