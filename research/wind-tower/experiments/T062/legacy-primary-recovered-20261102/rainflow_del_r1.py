import csv, struct, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent; CASE_ROOT=ROOT/'CASES'
LOAD_CHANNELS=['TwrBsMxt','TwrBsMyt']; CONTROL_CHANNELS=['RotSpeed','BldPitch1','BldPitch2','BldPitch3','RotThrust','GenPwr','GenTq','LSShftTq','HSShftTq']
M=4; NEQ=100000.0

def read_outb(p):
    with p.open('rb') as f:
        fid,nl,nc,nt=struct.unpack('<hhii',f.read(12)); t0,dt=struct.unpack('<2d',f.read(16)); sl=np.frombuffer(f.read(4*nc),dtype='<f4').astype(float); off=np.frombuffer(f.read(4*nc),dtype='<f4').astype(float); dl=struct.unpack('<i',f.read(4))[0]; f.read(dl); names=[f.read(nl).decode('ascii','ignore').strip() for _ in range(nc+1)]; units=[f.read(nl).decode('ascii','ignore').strip() for _ in range(nc+1)]; packed=np.frombuffer(f.read(nt*nc*2),dtype='<i2')
    if names[0]!='Time' or packed.size != nt*nc: raise ValueError(f'bad outb {p}')
    return names,units,t0+dt*np.arange(nt),((packed.reshape(nt,nc).astype(float)-off)/sl),dt

def reversals(x):
    x=np.asarray(x,float); keep=[x[0]]
    for v in x[1:]:
        if v==keep[-1]: continue
        keep.append(v)
    if len(keep)<3:return keep
    out=[keep[0]]
    for i in range(1,len(keep)-1):
        a,b,c=keep[i-1],keep[i],keep[i+1]
        if (b-a)*(c-b)<=0: out.append(b)
    out.append(keep[-1]); return out

def rainflow(x):
    pts=reversals(x); stack=[]; cycles=[]
    for v in pts:
        stack.append(float(v))
        while len(stack)>=3:
            X=abs(stack[-2]-stack[-3]); Y=abs(stack[-1]-stack[-2])
            if X<Y: break
            if len(stack)==3:
                cycles.append((X,(stack[0]+stack[1])/2.0,0.5)); del stack[0]
            else:
                cycles.append((X,(stack[-3]+stack[-2])/2.0,1.0)); del stack[-3:-1]
    for i in range(len(stack)-1):
        cycles.append((abs(stack[i+1]-stack[i]),(stack[i+1]+stack[i])/2.0,0.5))
    return cycles

def write(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        if not rows: return
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    qa=[]; ledger=[]; delrows=[]; controls=[]; all_cycles=[]
    ids=[]
    for d in sorted(CASE_ROOT.iterdir()):
        if not d.is_dir() or not d.name.startswith('U'): continue
        p=d/'DTU_10MW_RWT.outb'
        if not p.exists(): continue
        ids.append(d.name); names,units,t,data,dt=read_outb(p); ix={n:i-1 for i,n in enumerate(names) if n!='Time'}; unit_map={n:units[i] for i,n in enumerate(names) if n!='Time'}; mask=(t>=100)&(t<=700)
        if d.name in ['U09p343881_NTM_S01','U11p4_NTM_S01','U19p202140_NTM_S01']:
            for ch in LOAD_CHANNELS+CONTROL_CHANNELS:
                data_col=ix[ch]; header_index=data_col+1; vals=data[mask,data_col][:5]
                qa.append({'case_id':d.name,'channel':ch,'header_index':header_index,'data_column':data_col,'unit':unit_map[ch],'first_value_1':float(vals[0]),'first_value_2':float(vals[1]),'first_value_3':float(vals[2]),'first_value_4':float(vals[3]),'first_value_5':float(vals[4]),'status':'PASS' if data_col>=0 else 'FAIL'})
        for ch in LOAD_CHANNELS:
            cyc=rainflow(data[mask,ix[ch]]); all_cycles.extend((d.name,ch,*c) for c in cyc)
            total=sum(c[2] for c in cyc); ranges=np.array([c[0] for c in cyc]); weights=np.array([c[2] for c in cyc]);
            for k,(r,mean,count) in enumerate(cyc,1): ledger.append({'case_id':d.name,'channel':ch,'cycle_id':k,'range':r,'amplitude':r/2.0,'mean':mean,'count':count,'unit':unit_map[ch]})
            delv=float((np.sum(weights*ranges**M)/NEQ)**(1.0/M)); delrows.append({'case_id':d.name,'URef_mps':{'U09p343881':'9.343881','U11p4':'11.400000','U19p202140':'19.202140'}[d.name.split('_')[0]],'wind_type':'ETM' if '_ETM_' in d.name else 'NTM','seed':d.name.rsplit('_',1)[1],'channel':ch,'m':M,'Neq':NEQ,'total_cycles_weighted':total,'n_cycle_records':len(cyc),'max_range':float(ranges.max()),'p95_range':float(np.percentile(ranges,95)),'p99_range':float(np.percentile(ranges,99)),'DEL_load_comparison':delv,'unit':unit_map[ch],'goodman_correction':'NOT_APPLIED'})
        for ch in CONTROL_CHANNELS:
            x=data[mask,ix[ch]]; s={'mean':x.mean(),'std':x.std(ddof=1),'min':x.min(),'max':x.max(),'rms':math.sqrt(np.mean(x*x)),'p95':np.percentile(x,95),'p99':np.percentile(x,99)}
            controls.append({'case_id':d.name,'channel':ch,'unit':unit_map[ch],'dt_s':dt,'n_samples':int(mask.sum()),**{k:float(v) for k,v in s.items()}})
    write(ROOT/'02_CHANNEL_MAPPING_QA_RAINFLOW.csv',qa); write(ROOT/'03_RAINFLOW_CYCLE_LEDGER.csv',ledger)
    # Per-case/channel range histogram with 30 common bins per channel.
    hist=[]
    for ch in LOAD_CHANNELS:
        vals=np.array([c[2] for c in all_cycles if c[1]==ch]); edges=np.linspace(0,float(vals.max()),31)
        for cid in ids:
            rr=np.array([c[2] for c in all_cycles if c[0]==cid and c[1]==ch]); counts,_=np.histogram(rr,bins=edges,weights=[c[4] for c in all_cycles if c[0]==cid and c[1]==ch])
            for i,n in enumerate(counts): hist.append({'case_id':cid,'channel':ch,'bin_id':i+1,'range_lo':edges[i],'range_hi':edges[i+1],'weighted_count':float(n)})
    write(ROOT/'04_RAINFLOW_RANGE_HISTOGRAM.csv',hist); write(ROOT/'05_LOAD_DEL_M4_ALL36.csv',delrows); write(ROOT/'08_CONTROLLER_RESPONSE_CORRECTED.csv',controls)
    groups=[]
    for u in ['9.343881','11.400000','19.202140']:
        for w in ['NTM','ETM']:
            for ch in LOAD_CHANNELS:
                rr=[r for r in delrows if r['URef_mps']==u and r['wind_type']==w and r['channel']==ch]; vals=np.array([r['DEL_load_comparison'] for r in rr]);
                if len(vals): groups.append({'URef_mps':u,'wind_type':w,'channel':ch,'n_seeds':len(vals),'DEL_mean':float(vals.mean()),'DEL_seed_std':float(vals.std(ddof=1)),'DEL_min':float(vals.min()),'DEL_max':float(vals.max())})
    write(ROOT/'06_LOAD_DEL_M4_GROUP_SUMMARY.csv',groups)
    rank=sorted(delrows,key=lambda r:r['DEL_load_comparison'],reverse=True)
    write(ROOT/'07_DEL_CONTROL_RANKING.csv',[{'rank':i+1,**r} for i,r in enumerate(rank)])
    comp=[]
    for u in ['9.343881','11.400000','19.202140']:
        for ch in LOAD_CHANNELS:
            n=[r['DEL_mean'] for r in groups if r['URef_mps']==u and r['wind_type']=='NTM' and r['channel']==ch]; e=[r['DEL_mean'] for r in groups if r['URef_mps']==u and r['wind_type']=='ETM' and r['channel']==ch]
            if n and e: comp.append({'URef_mps':u,'channel':ch,'NTM_DEL_mean':n[0],'ETM_DEL_mean':e[0],'ETM_minus_NTM_pct':100*(e[0]-n[0])/n[0]})
    write(ROOT/'09_NTM_ETM_DEL_COMPARISON.csv',comp)
    (ROOT/'RAINflow_DEL_STATUS.txt').write_text(f'PASS\n36 cases; {len(ledger)} cycle records; m={M}; Neq={NEQ}; Goodman=NOT_APPLIED\n',encoding='ascii')
    print(f'processed {len(ids)} cases; cycles={len(ledger)}')
if __name__=='__main__': main()
