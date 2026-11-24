"""Reproducible source-level audit of the frozen nine-record archive. Not a design approval."""
import argparse,csv,hashlib,io,json,math,pathlib,zipfile,shutil
import numpy as np
from scipy.signal import cont2discrete,ss2tf,lfilter,butter,sosfiltfilt
from scipy.linalg import expm
from scipy.integrate import cumulative_trapezoid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H='89d25e81769f22481baef110ec0a41995902d3bc76725ec5442ba042496e8ca4'
T1=7.3937; T=np.array([.1,.25,.5,1,2,4,6,T1,8,10,12,15]); ANG=np.arange(180)*np.pi/180
REF_PGA=.4905

def sha(b):return hashlib.sha256(b).hexdigest()
def load(b,skip=1):return np.loadtxt(io.BytesIO(b),delimiter=',',skiprows=skip)
def spectra(a,dt,periods,zeta):
    vals=[]
    for t in periods:
        w=2*np.pi/t;A=np.array([[0.,1.],[-w*w,-2*zeta*w]]);B=np.array([[0.],[-1.]]);C=np.array([[w*w,0.]])
        Ad,Bd,Cd,Dd,_=cont2discrete((A,B,C,np.array([[0.]])),dt,method='foh');n,d=ss2tf(Ad,Bd,Cd,Dd)
        y=lfilter(n[0],d,a,axis=0)
        # Correct FOH discrete initial state for nonzero input at the first physical zero-state sample.
        K=np.zeros((4,4));K[:2,:2]=A;K[:2,2:3]=B;K[2,3]=1
        b1=expm(K*dt)[:2,3]/dt
        c0=float((-Cd@b1).item());c1=float((-Cd@Ad@b1).item())
        impulse=np.zeros(len(a));impulse[0]=1
        y+=lfilter([c0,c1+d[1]*c0],d,impulse)[:,None]*a[0]
        pk=np.array([np.max(np.abs(y[:,0]*np.cos(q)+y[:,1]*np.sin(q))) for q in ANG])
        vals.append([np.median(pk),np.max(np.linalg.norm(y,axis=1)),*np.max(abs(y),axis=0)])
    return np.array(vals)

def parse_asc(b):
    h={};vals=[]
    for line in b.decode('utf-8-sig').splitlines():
        line=line.strip()
        if not line:continue
        if ':' in line and not vals:
            k,v=line.split(':',1);h[k.strip()]=v.strip()
        else:vals.extend(float(x) for x in line.split())
    a=np.array(vals)*.01
    assert h['UNITS']=='cm/s^2' and h['DATA_TYPE']=='ACCELERATION' and len(a)==int(h['NDATA']) and np.isfinite(a).all()
    return h,a

def integrate(a,dt):return cumulative_trapezoid(a,dx=dt,axis=0,initial=0.)
def vector_peak(a):return float(np.max(np.linalg.norm(a,axis=1)))
def win_energy(v,dt,window):
    e=integrate(np.sum(v*v,axis=1),dt);n=min(len(v)-1,round(window/dt));f=e[n:]-e[:-n];i=int(np.argmax(f));return float(f[i]/max(e[-1],1e-30)),i*dt

def main():
    p=argparse.ArgumentParser();p.add_argument('zip');p.add_argument('out');o=p.parse_args();out=pathlib.Path(o.out);out.mkdir(parents=True,exist_ok=True)
    src=pathlib.Path(o.zip).read_bytes();assert sha(src)==H
    results=[];period_rows=[];plots=[];downloads=[]
    with zipfile.ZipFile(io.BytesIO(src)) as z:
        assert z.testzip() is None;names=z.namelist();assert len(names)==len(set(names)) and all(not x.startswith('/') and '..' not in pathlib.PurePosixPath(x).parts for x in names)
        manifest=json.loads(z.read('MANIFEST.json'));assert set(names)==set(manifest)|{'MANIFEST.json'}
        for n,m in manifest.items():b=z.read(n);assert len(b)==m['bytes'] and sha(b)==m['sha256'],n
        info=json.loads(z.read('NINE_SOURCE_CANDIDATES.json'))
        for r in info['rows']:
            rid,st=r['id'],r['station'];d=f'records/{rid}_{st}/';dt=r['dt'];a=load(z.read(d+'acceleration_SI.csv'));t=a[:,0];x=a[:,1:];assert len(t)==r['npts'] and np.isfinite(a).all() and np.max(abs(np.diff(t)-dt))<1e-6
            assert np.allclose(np.max(abs(x[:,:2]),axis=0),r['pga'][:2],rtol=1e-8,atol=1e-8)
            if rid!='SP02':
                b=z.read(d+'original_MP_ACC.zip');assert sha(b)==r['original_sha256'];rc=json.loads(z.read(d+'receipt.json'))
                with zipfile.ZipFile(io.BytesIO(b)) as zz:
                    assert zz.testzip() is None;orig={}
                    for item in rc['headers']:
                        bb=zz.read(item['member']);assert sha(bb)==item['sha256'];h,s=parse_asc(bb);assert h['EVENT_ID']==r['event'] and h['STATION_CODE']==st and float(h['SAMPLING_INTERVAL_S'])==dt
                        orig[h['STREAM'][-1]]=(h,s)
                    cols=['E','N']+(['Z'] if x.shape[1]==3 else []);xx=np.column_stack([orig[k][1] for k in cols]);assert len(xx)==len(t);assert len(set(orig[k][0]['DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS'] for k in cols))==1
                maxfc=max(r['fc']);screen_Tmax=1/(2*maxfc);fc_desc='/'.join(map(str,r['fc']));v=integrate(x[:,:2],dt);u=integrate(v,dt);provider=None
            else:
                n=next(n for n in names if n.startswith(d) and n.endswith('_V2A.csv'));b=z.read(n);assert sha(b)==r['original_sha256'];raw=load(b,5);assert np.max(abs(raw[:,0]-t))<1e-8;xx=raw[:,1:4]*.001;assert x.shape==xx.shape
                maxfc=.1;screen_Tmax=10.;fc_desc='0.01–0.10 transition';v=raw[:,4:6]*.001;u=raw[:,7:9]*.001;iv=integrate(x[:,:2],dt)+v[0];iu=integrate(iv,dt)+u[0]
                provider={'max_integrated_velocity_difference_m_s':vector_peak(iv-v),'max_integrated_displacement_difference_m':vector_peak(iu-u),'note':'trapezoid integration from provider initial conditions; difference is a diagnostic, not a correction'}
            diff=float(np.max(abs(xx-x)));assert np.allclose(xx,x,rtol=1e-9,atol=1e-9), (rid,diff)
            h=x[:,:2];pga=float(np.max(abs(h)));pgv=vector_peak(v);pgd=vector_peak(u);tail_n=max(1,int(5/dt));vel_end=float(np.linalg.norm(v[-1]));end_ratio=vel_end/max(pgv,1e-30);tail_mean=float(np.linalg.norm(np.mean(h[-tail_n:],axis=0)));tail_ratio=tail_mean/pga
            e=integrate(np.sum(h*h,axis=1),dt);dur=float(np.interp(.95*e[-1],e,t)-np.interp(.05*e[-1],e,t));f4,p4=win_energy(v,dt,4);f7,p7=win_energy(v,dt,T1)
            specs={zz:spectra(h,dt,T,zz) for zz in (.01,.02,.05)};base=specs[.05];i1=int(np.flatnonzero(T==T1)[0]);srcspec=load(z.read(d+'spectra_5pct.csv'));ref=float(srcspec[np.argmin(abs(srcspec[:,0]-T1)),1]);assert abs(base[i1,0]-ref)/ref<1e-6,(rid,base[i1,0],ref)
            # Extra filters are diagnostic only, never applied to archived/source motions.
            extras={};changes={}
            for fc in (.06,.08):
                y=sosfiltfilt(butter(4,fc,fs=1/dt,btype='highpass',output='sos'),h,axis=0,padtype='odd',padlen=min(len(h)-1,math.ceil(3/fc/dt)))
                sp=spectra(y,dt,T,.05);extras[fc]=sp;changes[fc]=(sp[:,0]/base[:,0]-1)*100
            mask=(T>=4)&(T<=12);maxsens=float(np.max(abs(changes[.08][mask])));sens1=float(changes[.08][i1]);scale=REF_PGA/pga;flags=[]
            if end_ratio>.05:flags.append('END_VELOCITY_GT5PCT')
            if tail_ratio>.01:flags.append('TAIL_MEAN_GT1PCT_PGA')
            if maxsens>20:flags.append('HP008_4_12S_MAX_CHANGE_GT20PCT')
            if screen_Tmax<15:flags.append('15S_BAND_NOT_PASSED')
            if dt>.01:flags.append('DT_GT0P01')
            if rid.startswith('EQ') and not .5<=scale<=2:flags.append('REFERENCE_PGA_SCALE_OUTSIDE_0P5_2')
            if rid.startswith('SP'):decision='SPECIAL_SENSITIVITY_ONLY'
            elif scale>2 or scale<.5:decision='REPLACE_PRIORITY'
            elif screen_Tmax>=15 and maxsens<=20 and end_ratio<=.05 and tail_ratio<=.01:decision='PRIORITY_FOR_TARGET_MATCH'
            else:decision='HOLD_FOR_BAND_BASELINE_REVIEW'
            result=dict(id=rid,station=st,event=r['event'],dt_s=dt,npts=len(t),duration_s=float(t[-1]-t[0]),pga_hmax_m_s2=pga,pgv_vector_m_s=pgv,pgd_vector_m=pgd,terminal_v_vector_m_s=vel_end,terminal_v_over_pgv=end_ratio,tail_mean_over_pga=tail_ratio,source_numeric_max_abs_error_m_s2=diff,D5_95_s=dur,filter=fc_desc,diagnostic_Tmax_s=screen_Tmax,RotD50_T1_1pct=float(specs[.01][i1,0]),RotD50_T1_2pct=float(specs[.02][i1,0]),RotD50_T1_5pct=float(base[i1,0]),RotD100_T1_5pct=float(base[i1,1]),hp006_T1_change_pct=float(changes[.06][i1]),hp008_T1_change_pct=sens1,hp008_max_abs_4_12s_change_pct=maxsens,scale_to_reference_pga=scale,scaled_T1_PSA_m_s2=float(base[i1,0]*scale),velocity_energy_4s_fraction=f4,velocity_energy_T1_fraction=f7,velocity_energy_4s_start_s=float(t[0]+p4),velocity_source='GeoNet official velocity' if rid=='SP02' else 'trapezoid acceleration integration v0=0',provider_integration=provider,flags=flags,decision=decision,design_eligible=False)
            results.append(result);plots.append((rid,st,t,h,v,u,T,base,changes[.08]))
            for i,tt in enumerate(T):period_rows.append([rid,st,tt,*[specs[zz][i,0] for zz in (.01,.02,.05)],base[i,1],changes[.06][i],changes[.08][i]])
            # Exact provider files and per-record analysis plus common manifest.
            folder=out/'records';folder.mkdir(exist_ok=True);zp=folder/f'{rid}_{st}.zip'
            with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zz:
                for n in names:
                    if n.startswith(d):zz.writestr(n[len(d):],z.read(n))
                zz.writestr('QC.json',json.dumps(result,ensure_ascii=False,indent=2)+'\n');zz.writestr('README.md',z.read('README.md'))
            downloads.append(dict(id=rid,station=st,file=str(zp.relative_to(out)),bytes=zp.stat().st_size,sha256=sha(zp.read_bytes())))
        for n in ('nine_actual_waveforms.png','nine_actual_spectra.png','NINE_SOURCE_CANDIDATES.json','README.md'):(out/n).write_bytes(z.read(n))
    (out/'T079_NINE_REAL_SOURCE_CANDIDATES.zip').write_bytes(src)
    with (out/'period_diagnostics.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['id','station','period_s','RotD50_1pct_m_s2','RotD50_2pct_m_s2','RotD50_5pct_m_s2','RotD100_5pct_m_s2','extra_hp006_change_pct','extra_hp008_change_pct']);w.writerows(period_rows)
    with (out/'quality_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    fig,ax=plt.subplots(3,3,figsize=(13,8),layout='constrained')
    for a,(rid,st,t,h,v,u,tt,base,ch) in zip(ax.flat,plots):
        a.plot(t,v[:,0],lw=.65,label='H1');a.plot(t,v[:,1],lw=.65,label='H2');a.set_title(rid+' '+st);a.set_xlabel('Original time (s)');a.set_ylabel('Velocity (m/s)');a.grid(alpha=.2);a.legend(fontsize=7)
    fig.suptitle('Velocity diagnostics — source integration (ESM) / official velocity (GeoNet)');fig.savefig(out/'nine_velocity_diagnostics.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    for rid,st,t,h,v,u,tt,base,ch in plots:ax.semilogx(tt,ch,marker='.',label=rid+' '+st)
    ax.axhline(20,ls=':',color='0.4');ax.axhline(-20,ls=':',color='0.4');ax.axvline(T1,ls='--',color='0.4');ax.set_xlim(4,15);ax.set_xlabel('Period (s)');ax.set_ylabel('Additional 0.08 Hz high-pass change (%)');ax.grid(alpha=.2);ax.legend(ncol=2,fontsize=8);fig.savefig(out/'nine_long_period_sensitivity.png',dpi=150);plt.close(fig)
    qc={'scope':'Processed-record source QA and diagnostic screens, not raw-instrument reliability or Jiayu design-spectrum approval','source_sha256':H,'T1_s':T1,'PGA_reference_m_s2':REF_PGA,'method':{'band':'ESM 2*reported corner margin; GeoNet end of low-frequency transition 0.10 Hz. Screening only, not usable period certification.','velocity':'ESM trapezoid v0=0, GeoNet supplied velocity and displacement. Permanent displacement not by itself invalid.','sensitivity':'4th-order Butterworth zero-phase extra high pass .06/.08 Hz, odd padding min(N-1,ceil(3/fc/dt)); not original processing error bound.','pulse':'4s and T1 sliding vector velocity energy concentration is a diagnostic, not Baker/Shahi classification.','thresholds':'Research-only: terminal velocity/peak 5%, 5s tail acceleration mean vector/PGA 1%, 4–12s sensitivity 20%, common reference-PGA factor .5–2; no normative claims.','target':'No approved long-period target or exact site hazard. Final admission zero. Scaling is reference PGA-only diagnostic; no scale applied to files.','references':['https://escweb.wr.usgs.gov/nsmp-data/processing.html','https://doi.org/10.1007/s10518-024-01970-5','https://www.geonet.org.nz/data/types/strong_motion','https://www.jackwbaker.com/pulse-classification.html']},'records':results,'downloads':downloads,'formal_design_eligible':0}
    (out/'quality_audit.json').write_text(json.dumps(qc,ensure_ascii=False,indent=2)+'\n');shutil.copy2(__file__,out/'audit_source.py')
    files={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='download-manifest.json'}
    (out/'download-manifest.json').write_text(json.dumps({'source_sha256':H,'files':files},ensure_ascii=False,indent=2)+'\n')
    for r in results:print(r['id'],r['station'],r['decision'],f"k={r['scale_to_reference_pga']:.3f} T1={r['RotD50_T1_5pct']:.6f} V_end={r['terminal_v_over_pgv']:.2%} HP08_T1={r['hp008_T1_change_pct']:.2f}% HP08_MAX={r['hp008_max_abs_4_12s_change_pct']:.2f}% Tmax={r['diagnostic_Tmax_s']:.2f}",r['flags'])
if __name__=='__main__':main()
