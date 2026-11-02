import csv, struct
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
CASE_ROOT=ROOT/'CASES'
CHANNELS=['YawBrTDxp','YawBrTDyp','YawBrTAxp','YawBrTAyp','TwrBsMxt','TwrBsMyt','RotSpeed','BldPitch1','BldPitch2','BldPitch3','RotThrust','GenTq','GenPwr','LSShftTq','HSShftTq']

def read_outb(p):
    with p.open('rb') as f:
        fid,nlen,nchan,nt=struct.unpack('<hhii',f.read(12)); t0,dt=struct.unpack('<2d',f.read(16))
        slope=np.frombuffer(f.read(4*nchan),dtype='<f4').astype(float); off=np.frombuffer(f.read(4*nchan),dtype='<f4').astype(float)
        dlen=struct.unpack('<i',f.read(4))[0]; f.read(dlen)
        names=[f.read(nlen).decode('ascii','ignore').strip() for _ in range(nchan+1)]
        units=[f.read(nlen).decode('ascii','ignore').strip() for _ in range(nchan+1)]
        packed=np.frombuffer(f.read(nt*nchan*2),dtype='<i2')
    if names[0] != 'Time' or len(names) != nchan+1: raise ValueError(f'Unexpected channel header in {p}')
    if packed.size != nt*nchan: raise ValueError(f'Truncated {p}')
    data=(packed.reshape(nt,nchan).astype(float)-off)/slope
    return names,units,t0+dt*np.arange(nt),data,dt

def stats(x):
    return {'mean':float(np.mean(x)),'std':float(np.std(x,ddof=1)),'min':float(np.min(x)),'max':float(np.max(x)),'rms':float(np.sqrt(np.mean(x*x))),'p95':float(np.percentile(x,95)),'p99':float(np.percentile(x,99))}

def write(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    rows=[]; cases=[]
    for d in sorted(CASE_ROOT.iterdir()):
        if not d.is_dir() or not d.name.startswith('U'): continue
        p=d/'DTU_10MW_RWT.outb'
        if not p.exists(): continue
        names,units,t,data,dt=read_outb(p); ix={n:i-1 for i,n in enumerate(names) if n!='Time'}; mask=(t>=100)&(t<=700)
        for ch in CHANNELS:
            if ch not in ix: continue
            rows.append({'case_id':d.name,'channel':ch,'unit':units[ix[ch]+1],'dt_s':dt,'n_samples':int(mask.sum()),'mapping':'names_index_minus_1',**stats(data[mask,ix[ch]])})
        top=np.hypot(data[mask,ix['YawBrTDxp']],data[mask,ix['YawBrTDyp']]); base=np.hypot(data[mask,ix['TwrBsMxt']],data[mask,ix['TwrBsMyt']])
        cases.append({'case_id':d.name,'URef_mps':{'U09p343881':'9.343881','U11p4':'11.400000','U19p202140':'19.202140'}[d.name.split('_')[0]],'wind_type':'ETM' if '_ETM_' in d.name else 'NTM','seed':d.name.rsplit('_',1)[1],'top_disp_max_m':float(top.max()),'top_disp_rms_m':float(np.sqrt(np.mean(top*top))),'tower_base_bending_max_kNm':float(base.max()),'tower_base_bending_rms_kNm':float(np.sqrt(np.mean(base*base)))})
    write(ROOT/'FORMAL_36CASE_CHANNEL_METRICS_CORRECTED.csv',rows); write(ROOT/'FORMAL_36CASE_CONTROL_RANKING_CORRECTED.csv',sorted(cases,key=lambda x:x['tower_base_bending_max_kNm'],reverse=True))
    groups=[]
    for u in ['9.343881','11.400000','19.202140']:
        for w in ['NTM','ETM']:
            rr=[x for x in cases if x['URef_mps']==u and x['wind_type']==w]
            if rr: groups.append({'URef_mps':u,'wind_type':w,'n_seeds':len(rr),'top_disp_max_mean_m':np.mean([x['top_disp_max_m'] for x in rr]),'top_disp_max_seed_std_m':np.std([x['top_disp_max_m'] for x in rr],ddof=1),'tower_base_bending_max_mean_kNm':np.mean([x['tower_base_bending_max_kNm'] for x in rr]),'tower_base_bending_max_seed_std_kNm':np.std([x['tower_base_bending_max_kNm'] for x in rr],ddof=1)})
    write(ROOT/'FORMAL_36CASE_GROUP_SUMMARY_CORRECTED.csv',groups); print(f'correctly analyzed {len(cases)} cases and {len(rows)} channel rows')
if __name__=='__main__': main()
