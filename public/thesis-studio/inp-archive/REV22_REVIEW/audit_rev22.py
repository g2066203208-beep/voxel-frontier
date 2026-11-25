"""Read the exact REV22 full assembly, not R2 or a CAE screenshot. No changes to physics."""
import csv,hashlib,json,math,re,zipfile
from pathlib import Path
from collections import Counter
BASE=Path('public/thesis-studio/inp-archive')
OUT=BASE/'REV22_REVIEW'
sha=lambda b:hashlib.sha256(b).hexdigest()
zpath=BASE/'REV21_MODE_PILOT/REV21_MODE_PILOT.zip'
assert sha(zpath.read_bytes())=='f389e927a4b42f0c26bf22f1f9ef24202255b8dd03a8d0e7585edfae83a6af91'
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    parent=z.read('HE_REV21_MODE_FULL_ASSEMBLY.inp')
    csvraw=z.read('MODE_EQ01_scaled_reference_SI.csv')
assert sha(parent)=='7538ccb15a0af82364f0482f4a30e65a59d157a3b33efb94c4beb295a646721c'
old=b'0.005, 199.995, 1.e-7, 0.01'; new=b'0.005, 199.995, 1.e-7, 0.005'
assert parent.count(old)==1
raw=parent.replace(old,new,1)
assert sha(raw)=='e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5'
assert sha(csvraw)=='640096c940f3c6d54cbe697fd2da9def7ab2428a3850316f228d451b791d1b67'
blocks=[]
for i,l in enumerate(raw.decode('ascii').splitlines(),1):
    s=l.strip()
    if not s or s.startswith('**'):continue
    if s.startswith('*'):
        blocks.append(dict(line=i,header=s,key=s.split(',')[0].upper(),data=[]))
    elif blocks:blocks[-1]['data'].append(s)
def param(b,k):
    m=re.search(r'(?:^|,)\s*'+re.escape(k)+r'\s*=\s*([^,]+)',b['header'],re.I)
    return m.group(1).strip().strip('"') if m else None
def mini(b,n=8):
    return dict(line=b['line'],header=b['header'],rows=len(b['data']),data=b['data'][:n])
def vals(s):return [float(v) for v in s.split(',') if v.strip()]
mats={}; mat=None; interactions={}; inter=None; pairs=[]; ties=[]; steps={}; step=None; amps={}; rna=None; rna_blocks=[]
for b in blocks:
    k=b['key']
    if k=='*PART':rna=(param(b,'name') or '').upper()=='RNA_FLEX_DPM'
    if k=='*END PART':rna=False
    if rna:rna_blocks.append(b)
    if k=='*MATERIAL':
        mat=(param(b,'name') or '').upper();mats[mat]=[b];inter=None;continue
    if k=='*SURFACE INTERACTION':
        inter=(param(b,'name') or '').upper();interactions[inter]=[b];mat=None;continue
    if k in ('*STEP','*CONTACT PAIR','*BOUNDARY','*AMPLITUDE','*INITIAL CONDITIONS','*TIE','*END ASSEMBLY','*SURFACE INTERACTION'):mat=None;inter=None
    if mat:mats[mat].append(b)
    if inter and k in ('*FRICTION','*SURFACE BEHAVIOR','*SURFACE INTERACTION'):interactions[inter].append(b)
    if k=='*CONTACT PAIR':pairs.append(mini(b))
    if k=='*TIE':ties.append(mini(b))
    if k=='*STEP':step=param(b,'name');steps[step]=[]
    if step:steps[step].append(b)
    if k=='*END STEP':step=None
    if k=='*AMPLITUDE':
        name=param(b,'name')
        if name and 'EQ_' in name.upper():amps[name.upper()]=b
required=['*CONCRETE DAMAGED PLASTICITY','*CONCRETE COMPRESSION HARDENING','*CONCRETE TENSION STIFFENING','*CONCRETE COMPRESSION DAMAGE','*CONCRETE TENSION DAMAGE']
material={}
for name in ('C65','C70'):
    bs=mats.get(name,[]);by={b['key']:b for b in bs};missing=[k for k in required if k not in by]; checks={}
    if not missing:
        E=vals(by['*ELASTIC']['data'][0])[0]
        for hard,dam in [(required[1],required[3]),(required[2],required[4])]:
            h=[vals(x)[:2] for x in by[hard]['data']];d=[vals(x)[:2] for x in by[dam]['data']]
            def interp(x):
                if x<=d[0][1]:return d[0][0]
                for (d0,x0),(d1,x1) in zip(d,d[1:]):
                    if x<=x1:return d0+(d1-d0)*(x-x0)/(x1-x0)
                return d[-1][0]
            legal=(all(0<=q<1 for q,x in d) and all(y[1]>x[1] for x,y in zip(h,h[1:])) and all(y[1]>x[1] for x,y in zip(d,d[1:])) and all(y[0]>=x[0] for x,y in zip(d,d[1:])) and abs(h[0][1])<1e-12 and abs(d[0][1])<1e-12)
            p=[x-interp(x)/(1-interp(x))*stress/E for stress,x in h] if legal else []
            checks[hard]=dict(rows=len(h),damage_rows=len(d),zero_first=bool(h and abs(h[0][1])<1e-12),plastic_strain_nonnegative_monotonic=bool(p and min(p)>=-1e-10 and all(y>=x-1e-10 for x,y in zip(p,p[1:]))),min_plastic=min(p) if p else None)
    material[name]=dict(missing=missing,checks=checks,cards=[mini(b,2000) for b in bs if b['key'] in required+['*MATERIAL','*DENSITY','*ELASTIC','*DAMPING']])
eq=steps.get('EQ_2H_RAYLEIGH_REL',[])
loads=[mini(b,100) for b in eq if b['key'] in ('*DLOAD','*CLOAD','*BOUNDARY','*DYNAMIC')]
amp_info={}
for name,b in amps.items():
    a=[v for row in b['data'] for v in vals(row)]; t=a[::2];y=a[1::2]
    amp_info[name]=dict(line=b['line'],samples=len(t),start=t[0],end=t[-1],pga=max(map(abs,y)),dt_min=min(j-i for i,j in zip(t,t[1:])),dt_max=max(j-i for i,j in zip(t,t[1:])),references=[x['line'] for x in loads if name in x['header'].upper()])
reader=list(csv.reader(csvraw.decode('utf-8-sig').splitlines()))
source=[[float(v) for v in row] for row in reader[1:] if row]
for name,b in amps.items():
    a=[v for row in b['data'] for v in vals(row)]
    if len(a)//2==len(source):
        amp_info[name]['source_matches']=[dict(column=reader[0][i],sign=sgn,max_absolute_error=max(abs(a[2*j+1]-sgn*r[i]) for j,r in enumerate(source))) for i in (1,2) for sgn in (1,-1)]
        amp_info[name]['source_time_max_error']=max(abs(a[2*j]-r[0]) for j,r in enumerate(source))
rna_counts=Counter()
for b in rna_blocks:
    if b['key']=='*ELEMENT':rna_counts[param(b,'type') or 'UNKNOWN']+=len(b['data'])
masses=[vals(b['data'][0])[0] for b in rna_blocks if b['key']=='*MASS' and b['data']]
friction={name:[mini(b) for b in bs] for name,bs in interactions.items()}
report=dict(version='REV22-REVIEW-V1',status='SOURCE_STATIC_READBACK_COMPLETE',native='NOT_RUN',sha256=sha(raw),bytes=len(raw),concrete=material,contact_pairs=pairs,interactions=friction,ties=ties,step_names=list(steps),eq_loads=loads,eq_amplitudes=amp_info,rna=dict(element_counts=dict(rna_counts),mass_cards=len(masses),sum_explicit_mass_kg=sum(masses),beam_general_sections=sum(b['key']=='*BEAM GENERAL SECTION' for b in rna_blocks)),limits=['Original archived INP only; CAE in-memory/export must be compared separately','Static input checks do not establish physical validity or Abaqus execution','Tie does not establish bolt or local flange behaviour','Whole-model GRAV coverage/force balance requires native verification','No physics changed'])
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(sha256=report['sha256'],concrete={n:{'missing':v['missing'],'checks':v['checks']} for n,v in material.items()},contact_pairs=len(pairs),ties=len(ties),loads=loads,amplitudes=amp_info,rna=report['rna']),ensure_ascii=False,indent=2))
