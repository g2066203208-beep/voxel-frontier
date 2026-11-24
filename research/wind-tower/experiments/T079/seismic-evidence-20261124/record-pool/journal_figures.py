"""Journal-style figures from frozen actual samples; V7 backup and DSLC literature example are separate."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.signal import welch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator,AutoMinorLocator,LogLocator
from audit_nine import spectra
P=Path(__file__).resolve().parent
V=P/'research_seven_v7'
O=P/'journal_figures_20261124';O.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'serif','font.serif':['STIXGeneral','DejaVu Serif'],'mathtext.fontset':'stix','font.size':9,'axes.labelsize':9,'axes.linewidth':.65,'xtick.direction':'in','ytick.direction':'in','xtick.top':True,'ytick.right':True,'xtick.major.size':3,'ytick.major.size':3,'xtick.minor.size':1.6,'ytick.minor.size':1.6,'legend.fontsize':8,'legend.frameon':False,'savefig.facecolor':'white','svg.fonttype':'none','pdf.fonttype':42})
T1=7.3937
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(fig,name):
    for ext in ['png','pdf','svg']:fig.savefig(O/(name+'.'+ext),dpi=600,bbox_inches='tight',pad_inches=.045)
    plt.close(fig)
def pair(ax,t,a,dirs):
    ax.plot(t,a[:,1],color='.60',lw=.4,label=dirs[1],rasterized=False)
    ax.plot(t,a[:,0],color='black',lw=.45,label=dirs[0])
    m=np.max(abs(a));ax.set_ylim(-1.13*m,1.13*m);ax.set_xlim(t[0],t[-1])
    ax.yaxis.set_major_locator(MaxNLocator(4,symmetric=True));ax.xaxis.set_major_locator(MaxNLocator(5))
def psd(ax,a,dt,dirs):
    n=min(len(a),round(40/dt))
    f,s=welch(a,fs=1/dt,window='hann',nperseg=n,noverlap=n//2,detrend='constant',scaling='density',axis=0)
    k=(f>0)&(f<=2)
    for i,c in [(1,'.60'),(0,'black')]:ax.semilogy(f[k],np.maximum(s[k,i],1e-25),color=c,lw=.7,label=dirs[i])
    ax.axvline(1/T1,color='.25',ls='--',lw=.65)
    ax.set_xlim(0,2);ax.xaxis.set_major_locator(MaxNLocator(5))
    return f,s
def tag(ax,label):ax.text(.015,.94,label,transform=ax.transAxes,ha='left',va='top',fontsize=8,bbox={'facecolor':'white','edgecolor':'none','pad':.7})
rows=[];qc=[]
for d in sorted(V.glob('EQ[0-9][0-9]')):
    m=json.loads((d/'selection.json').read_text());f=d/'scaled_reference_SI.csv'
    assert sha(f)==m['files'][f.name]
    x=np.loadtxt(f,delimiter=',',skiprows=1);t=x[:,0];a=x[:,1:];dt=m['dt']
    assert len(x)==m['npts'] and np.isfinite(x).all() and np.allclose(np.diff(t),dt,atol=1e-7)
    sp=np.loadtxt(d/'spectra.csv',delimiter=',',skiprows=1);rows.append((m,t,a,sp))
    qc.append({'station':m['station'],'sha256':sha(f),'npts':len(t),'PGA_m_s2':float(np.max(abs(a)))})
assert len(rows)==7
for kind in ['time','psd']:
    fig,axs=plt.subplots(4,2,figsize=(6.7,7.0),layout='constrained')
    for j,(ax,(m,t,a,sp)) in enumerate(zip(axs.flat,rows)):
        if kind=='time':
            pair(ax,t,a,m['dirs']);ax.set_xlabel('Time (s)');ax.set_ylabel(r'Acceleration (m/s$^2$)')
        else:
            f,s=psd(ax,a,m['dt'],m['dirs']);ax.set_xlabel('Frequency (Hz)');ax.set_ylabel(r'PSD (m$^2$/s$^4$/Hz)')
            np.savetxt(O/(m['id']+'_PSD.csv'),np.c_[f,s],delimiter=',',header='f_Hz,H1_PSD_SI,H2_PSD_SI',comments='')
        tag(ax,f'({chr(97+j)}) {m["station"]}');ax.legend(loc='upper right',handlelength=1.5,borderaxespad=.3,ncol=2)
    axs.flat[7].axis('off')
    if kind=='psd':axs.flat[7].text(.08,.7,r'Dashed line: $f_1=0.1353$ Hz',transform=axs.flat[7].transAxes)
    save(fig,'V7_backup_01_acceleration' if kind=='time' else 'V7_backup_02_PSD')
fig,ax=plt.subplots(figsize=(6.7,3.8),layout='constrained')
T=rows[0][3][:,0];target=rows[0][3][:,3]
S=np.array([r[3][:,2] for r in rows]);assert all(np.allclose(r[3][:,0],T) for r in rows)
for j,s in enumerate(S):ax.loglog(T,s,color='.65',lw=.65,label='Individual records' if j==0 else None)
ax.loglog(T,S.mean(axis=0),color='black',lw=1.5,label='Mean spectrum')
ax.loglog(T,target,color='black',ls='--',lw=1.2,label='Research target')
ax.axvline(T1,ls=':',color='.25',lw=.8);ax.text(T1,.96,r'$T_1=7.394$ s',transform=ax.get_xaxis_transform(),ha='right',va='top')
ax.set(xlim=(.1,10),xlabel='Period (s)',ylabel=r'5% damped RotD50 PSA (m/s$^2$)');ax.legend(loc='lower left')
save(fig,'V7_backup_03_response_spectra')
# Exact literature precedent: GeoNet DSLC N63E and orthogonal N27W, original, not tuned.
f=next((P/'geonet-dslc').glob('*_DSLC_V2A.csv'));x=np.loadtxt(f,delimiter=',',skiprows=5);t=x[:,0];a=x[:,1:3]*.001
assert len(t)==7386 and np.allclose(np.diff(t),.02) and np.isclose(np.max(abs(a[:,0])),2.3528)
dirs=['N63E','N27W']
fig,ax=plt.subplots(figsize=(6.7,2.5),layout='constrained');pair(ax,t,a,dirs);ax.set(xlabel='Time (s)',ylabel=r'Acceleration (m/s$^2$)');ax.legend(loc='upper right',ncol=2);save(fig,'DSLC_01_acceleration')
fig,ax=plt.subplots(figsize=(6.7,3.1),layout='constrained');fq,s=psd(ax,a,.02,dirs);ax.set(xlabel='Frequency (Hz)',ylabel=r'PSD (m$^2$/s$^4$/Hz)');ax.legend();save(fig,'DSLC_02_PSD');np.savetxt(O/'DSLC_PSD.csv',np.c_[fq,s],delimiter=',',header='f_Hz,N63E,N27W',comments='')
T=np.unique(np.r_[np.geomspace(.1,10,161),T1]);ss=spectra(a,.02,T,.05)
fig,ax=plt.subplots(figsize=(6.7,3.5),layout='constrained')
ax.loglog(T,ss[:,2],color='black',lw=.9,label=dirs[0]);ax.loglog(T,ss[:,3],color='.55',lw=.9,label=dirs[1]);ax.loglog(T,ss[:,0],color='black',ls='--',lw=1.2,label='RotD50');ax.axvline(T1,color='.25',ls=':',lw=.7);ax.set(xlabel='Period (s)',ylabel=r'5% damped PSA (m/s$^2$)',xlim=(.1,10));ax.legend();save(fig,'DSLC_03_response_spectra');np.savetxt(O/'DSLC_response_spectra.csv',np.c_[T,ss],delimiter=',',header='T_s,RotD50,RotD100,N63E,N27W',comments='')
# Provider-corrected acceleration, velocity and displacement; no reintegration.
fig,axs=plt.subplots(3,1,figsize=(6.7,5.6),sharex=True,layout='constrained')
for i,(ax,y,lab) in enumerate(zip(axs,[x[:,1]*.001,x[:,4]*.001,x[:,7]*.001],[r'Acceleration (m/s$^2$)','Velocity (m/s)','Displacement (m)'])):
    ax.plot(t,y,color='black',lw=.5);ax.set_ylabel(lab);tag(ax,f'({chr(97+i)}) DSLC N63E')
axs[-1].set_xlabel('Time (s)');save(fig,'DSLC_04_three_motion_histories')
report={'V7_status':'backup suite; not the seven literature-exact records','DSLC_status':'one verified literature-exact station/component; original amplitudes','T1_s':T1,'PSD':'Welch Hann 40 s, 50% overlap, constant detrend, one-sided density; df 0.025 Hz','response':'5% PSA, V7 original stored scaled RotD50 spectra, DSLC FOH computed','source_V7':qc,'source_DSLC_sha256':sha(f),'source_DSLC_npts':len(t),'figures':{q.name:sha(q) for q in O.iterdir() if q.suffix in ['.png','.svg','.pdf']}}
(O/'manifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
