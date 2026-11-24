"""Read native TurbSim BTS, generate publication-quality validation figures."""
import argparse, hashlib, json, struct, pathlib
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.linewidth':0.8,'figure.dpi':160,'savefig.dpi':300,'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,'svg.fonttype':'none','pdf.fonttype':42})
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read_bts(path):
    with open(path,'rb') as f:
        ident,nz,ny,ntwr,nt=struct.unpack('<h4i',f.read(18))
        dz,dy,dt,uhub,zhub,zbottom=struct.unpack('<6f',f.read(24))
        coeff=np.array(struct.unpack('<6f',f.read(24))).reshape(3,2)
        nc,=struct.unpack('<i',f.read(4))
        assert ident in (7,8) and min(nz,ny,nt)>0 and ntwr>=0 and 0<=nc<1000000
        info=f.read(nc).decode('utf8',errors='replace')
        offset=f.tell()
    expected=offset+2*nt*3*(nz*ny+ntwr)
    assert path.stat().st_size==expected,(path.stat().st_size,expected)
    assert np.all(np.isfinite(coeff)) and np.all(coeff[:,0]!=0)
    raw=np.memmap(path,mode='r',dtype='<i2',offset=offset,shape=(nt,nz*ny+ntwr,3))
    grid=raw[:,:nz*ny].reshape(nt,nz,ny,3)
    tower=raw[:,nz*ny:]
    scale=coeff[:,0]; offs=coeff[:,1]
    def decode(x):return (x.astype('float32')-offs.astype('float32'))/scale.astype('float32')
    dt=round(dt,6)
    return dict(ID=ident,nz=nz,ny=ny,ntwr=ntwr,nt=nt,dz=dz,dy=dy,dt=dt,uhub=uhub,zhub=zhub,zbottom=zbottom,info=info,grid=grid,tower=tower,decode=decode,y=(np.arange(ny)-(ny-1)/2)*dy,z=zbottom+np.arange(nz)*dz,t=np.arange(nt)*dt,ztwr=zbottom-np.arange(ntwr)*dz)
def save(fig,out,name):
    fig.savefig(out/(name+'.png'),bbox_inches='tight',pad_inches=.07)
    fig.savefig(out/(name+'.svg'),bbox_inches='tight',pad_inches=.07)
    plt.close(fig)
def main():
    p=argparse.ArgumentParser();p.add_argument('bts',type=pathlib.Path);p.add_argument('config',type=pathlib.Path);p.add_argument('out',type=pathlib.Path);a=p.parse_args()
    cfg=json.loads(a.config.read_text()); d=read_bts(a.bts);a.out.mkdir(parents=True,exist_ok=True)
    nt,nz,ny=d['nt'],d['nz'],d['ny'];dt=d['dt'];y,z,t=d['y'],d['z'],d['t'];dec=d['decode'];g=d['grid'];U=cfg['speed'];is_etm=cfg['type']=='1ETM'
    assert nz==ny==cfg['grid'] and abs(dt-.05)<1e-7 and abs(d['zhub']-161.368806)<.001 and abs(y[-1]-y[0]-200)<.001 and abs(z[-1]-z[0]-200)<.001
    assert d['ntwr']>0,'Requested tower points absent'
    # Only complete requested statistical window, not extra padded times.
    start=100 if cfg['duration']==700 else 20
    end=cfg['duration']; take=(t>=start)&(t<end); assert take.sum()==round((end-start)/dt)
    ts=t[take]; midy=ny//2;midz=nz//2
    q=dec(g[:,midz,midy]);valid=q[take]
    # three components and three rotor elevations (nearest grid points)
    levels=[int(np.argmin(abs(z-(d['zhub']+v)))) for v in [-89.15,0,89.15]]
    sig=.16*(.75*U+5.6) if not is_etm else 2*.16*(.072*(10/2+3)*(U/2-4)+10)
    sigmas=sig*np.array([1,.8,.5]);L=np.array([340.2,113.4,27.72])
    cols=['#13557c','#ba532e','#38754e']
    fig,ax=plt.subplots(3,1,figsize=(7.3,5.6),sharex=True,layout='constrained')
    for k in range(3):
        ax[k].plot(ts,valid[:,k],lw=.45,color=cols[k]);ax[k].set_ylabel('uvw'[k]+' (m/s)');ax[k].grid(alpha=.15)
    ax[-1].set_xlabel('Time (s)');save(fig,a.out,'01_hub_uvw')
    fig,ax=plt.subplots(3,1,figsize=(7.3,5.6),sharex=True,layout='constrained')
    for k,iz in enumerate(levels):
        ax[k].plot(ts,dec(g[:,iz,midy])[take,0],lw=.45,color=cols[k]);ax[k].set_ylabel(f'u at {z[iz]:.1f} m\n(m/s)');ax[k].grid(alpha=.15)
    ax[-1].set_xlabel('Time (s)');save(fig,a.out,'02_height_timeseries')
    # Actual temporal and spatial sections; common color normalization.
    sl=np.flatnonzero(take); stride=max(1,len(sl)//1200); ix=sl[::stride]; v=dec(g[ix,midz,:,:])[:,:,0];w=dec(g[ix,:,midy,:])[:,:,0]
    frame_ids=[sl[len(sl)//4],sl[len(sl)//2],sl[3*len(sl)//4]]
    snaps=[dec(g[i])[:,:,0] for i in frame_ids]
    vv=np.concatenate([v.ravel(),w.ravel()]+[x.ravel() for x in snaps]); lo,hi=np.min(vv),np.max(vv)
    fig,ax=plt.subplots(2,1,figsize=(7.3,5.4),layout='constrained')
    im=ax[0].pcolormesh(t[ix],y,v.T,shading='auto',cmap='viridis',vmin=lo,vmax=hi);ax[0].set_ylabel('Lateral y (m)');ax[0].set_title('(a) Hub-height plane',loc='left')
    ax[1].pcolormesh(t[ix],z,w.T,shading='auto',cmap='viridis',vmin=lo,vmax=hi);ax[1].set_ylabel('Height z (m)');ax[1].set_xlabel('Time (s)');ax[1].set_title('(b) Tower-centre vertical plane',loc='left');fig.colorbar(im,ax=ax,label='u (m/s)');save(fig,a.out,'03_spatiotemporal')
    fig,ax=plt.subplots(1,3,figsize=(9,3.2),sharey=True,layout='constrained')
    for k,(i,snap) in enumerate(zip(frame_ids,snaps)):
        im=ax[k].pcolormesh(y,z,snap,shading='auto',cmap='viridis',vmin=lo,vmax=hi);ax[k].add_patch(plt.Circle((0,d['zhub']),89.15,fill=False,color='white',lw=.9));ax[k].set_aspect('equal');ax[k].set_title(f't = {t[i]:.1f} s');ax[k].set_xlabel('y (m)')
    ax[0].set_ylabel('z (m)');fig.colorbar(im,ax=ax,label='u (m/s)');save(fig,a.out,'04_rotor_snapshots')
    # Spectra: mean-removed actual Welch estimate vs theoretical IEC curves.
    nper=2048 if cfg['duration']==700 else 512;nover=nper//2
    fig,ax=plt.subplots(1,3,figsize=(9.3,3.1),layout='constrained')
    spec=[]
    for k in range(3):
        f,P=signal.welch(valid[:,k],fs=1/dt,window='hann',nperseg=nper,noverlap=nover,detrend='constant')
        mask=f>0; ff=f[mask]; target=4*sigmas[k]**2*L[k]/U/(1+6*ff*L[k]/U)**(5/3)
        ax[k].loglog(ff,P[mask],color=cols[k],lw=.9,label='Native BTS')
        ax[k].loglog(ff,target,color='#222',lw=1.15,ls='--',label='IEC target')
        ax[k].set_title('uvw'[k]);ax[k].set_xlabel('f (Hz)');ax[k].grid(which='major',alpha=.15)
        spec.append(np.c_[ff,P[mask],target])
    ax[0].set_ylabel('PSD ((m/s)²/Hz)');ax[0].legend(fontsize=8);save(fig,a.out,'05_psd_validation')
    for k in range(3):np.savetxt(a.out/f'psd_{"uvw"[k]}.csv',spec[k],delimiter=',',header='f_Hz,welch_psd,target_psd',comments='')
    # Mean wind profile and actual turbulence intensities on the centerline, incl. tower data.
    ctr=dec(g[:, :,midy,:])[take]
    zz=z.copy();m=ctr[:,:,0].mean(0);sd=ctr[:,:,0].std(0,ddof=1)
    if d['ntwr']:
        tw=dec(d['tower'])[take,:,0];zz=np.r_[d['ztwr'],zz];m=np.r_[tw.mean(0),m];sd=np.r_[tw.std(0,ddof=1),sd]
    order=np.argsort(zz);zz,m,sd=zz[order],m[order],sd[order]
    fig,ax=plt.subplots(1,2,figsize=(6.6,4),sharey=True,layout='constrained')
    ax[0].plot(m,zz,'o-',ms=2,lw=.8,label='Native BTS');ax[0].plot(U*(zz/d['zhub'])**.2,zz,'--',color='#222',lw=.9,label='0.2 power-law reference');ax[0].set_xlabel('Mean u (m/s)');ax[0].set_ylabel('Height (m)');ax[0].legend(fontsize=8)
    ti=np.divide(sd,m,out=np.full_like(sd,np.nan),where=m>0)
    ax[1].plot(ti*100,zz,'o-',ms=2,lw=.8,color=cols[1]);ax[1].set_xlabel('Turbulence intensity (%)')
    for x in ax:x.axhline(d['zbottom'],ls=':',color='#555',lw=.9);x.grid(alpha=.15)
    save(fig,a.out,'06_profiles')
    np.savetxt(a.out/'profiles.csv',np.c_[zz,m,sd,ti],delimiter=',',header='height_m,mean_u_m_s,std_u_m_s,TI',comments='')
    # Coherence comparison: sqrt magnitude-squared coherence (finite sample bias).
    rs=[d['dy'],5*d['dy'],min(20,ny//2)*d['dy']];rs=list(dict.fromkeys(rs))
    fig,ax=plt.subplots(len(rs),1,figsize=(7.1,5.5),sharex=True,layout='constrained');ax=np.atleast_1d(ax)
    for k,r in enumerate(rs):
        iy=midy+round(r/d['dy']);b=dec(g[:,midz,iy])[take,0];f,C=signal.coherence(valid[:,0],b,fs=1/dt,window='hann',nperseg=nper,noverlap=nover,detrend='constant')
        f=f[1:];est=np.sqrt(np.clip(C[1:],0,1));target=np.exp(-12*np.sqrt((f*r/U)**2+(.12*r/340.2)**2));ax[k].semilogx(f,est,color=cols[k],lw=.65,label='sqrt(MSC)');ax[k].semilogx(f,target,'--',color='#222',lw=1,label='IEC target');ax[k].set_ylim(0,1.05);ax[k].set_ylabel(f'r={r:.0f} m');ax[k].grid(alpha=.15)
        np.savetxt(a.out/f'coherence_{r:.0f}m.csv',np.c_[f,est,target],delimiter=',',header='f_Hz,sqrt_MSC,IEC_target',comments='')
    ax[0].legend(fontsize=8);ax[-1].set_xlabel('Frequency (Hz)');save(fig,a.out,'07_coherence_validation')
    np.savetxt(a.out/'hub_uvw.csv',np.c_[ts,valid],delimiter=',',header='time_s,u_m_s,v_m_s,w_m_s',comments='')
    out={k:d[k] for k in ['ID','nz','ny','nt','ntwr','dy','dz','dt','uhub','zhub','zbottom','info']}
    out.update({'scope':'NATIVE TURBSIM NEW RESEARCH CASE, NOT HISTORICAL 36 CASES','config':cfg,'BTS_sha256':sha(a.bts),'BTS_bytes':a.bts.stat().st_size,'window_s':[start,end],'n_window':int(take.sum()),'hub_mean':valid.mean(0).tolist(),'hub_std':valid.std(0,ddof=1).tolist(),'target_sigma':sigmas.tolist(),'tower_lowest_z_m':float(np.min(d['ztwr'])),'welch_nperseg':nper,'welch_overlap':nover,'warnings':['Finite-sample PSD/coherence estimates; no automatic physical pass.', 'ETM target uses IEC class I Vave=10 m/s and default c=2 m/s; compare native summary.', '0.2 power-law is reference, not proof of actual profile.', 'Tower centre nodes do not independently establish distributed external aerodynamic loads.']})
    (a.out/'audit.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
