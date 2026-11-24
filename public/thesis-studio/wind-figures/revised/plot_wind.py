from pathlib import Path
import argparse, hashlib, json, struct, csv
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
p=argparse.ArgumentParser();p.add_argument('ntm',type=Path);p.add_argument('etm',type=Path);p.add_argument('output',type=Path);a=p.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.linewidth':.8,'legend.frameon':False,'figure.dpi':150,'savefig.dpi':300,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
colors=['#15587d','#b74430'];names=['NTM','ETM']; L=np.array([340.2,113.4,27.72]);comp='uvw'
def read(p):
 au=json.loads((p/'audit.json' if (p/'audit.json').exists() else p/'figures/audit.json').read_text());b=p/'case.bts';hsh=hashlib.sha256(b.read_bytes()).hexdigest();assert hsh==au['BTS_sha256']
 with b.open('rb') as f:
  h=struct.unpack('<h4i6f6fi',f.read(70));f.read(h[-1]);off=f.tell()
 nz,ny,ntr,nt=h[1:5];assert b.stat().st_size==off+nt*(nz*ny+ntr)*6
 raw=np.memmap(b,dtype='<i2',mode='r',offset=off,shape=(nt,nz*ny+ntr,3));scale=np.array(h[11:16:2]);bias=np.array(h[12:17:2]);dec=lambda v:(v.astype('float32')-bias)/scale
 return dict(g=raw[:,:nz*ny].reshape(nt,nz,ny,3),tw=raw[:,nz*ny:],dec=dec,t=np.arange(nt)*round(h[7],6),y=(np.arange(ny)-(ny-1)/2)*h[6],z=h[10]+np.arange(nz)*h[5],zt=h[10]-np.arange(ntr)*h[5],au=au,sha=hsh)
D=[read(a.ntm),read(a.etm)];d=D[0];t,y,z=d['t'],d['y'],d['z'];hub=d['au']['zhub'];U=d['au']['config']['speed'];start,end=d['au']['window_s'];dt=d['au']['dt'];mid=len(y)//2
assert all(np.array_equal(d[k],D[1][k]) for k in ['t','y','z','zt']);assert D[1]['au']['config']['speed']==U and D[1]['au']['window_s']==[start,end]
ix=np.where((t>=start)&(t<end))[0];ts=t[ix];nper=512 if len(ix)<4000 else 2048;nover=nper//2;fkw=dict(fs=1/dt,window='hann',nperseg=nper,noverlap=nover,detrend='constant');levels=np.array([np.argmin(abs(z-hub-v)) for v in [-89.15,0,89.15]]);inds=[ix[len(ix)//4],ix[len(ix)//2],ix[3*len(ix)//4]];figs=[]
def save(fig,stem):
 for ext in ['png','svg','pdf']:fig.savefig(out/(stem+'.'+ext),bbox_inches='tight',pad_inches=.06)
 plt.close(fig);figs.append(stem)
def panel(ax,i,s=''):ax.set_title('('+chr(97+i)+') '+s,loc='left',fontsize=10);ax.grid(alpha=.16,linewidth=.5)
def plegend(fig,handles,labels):fig.legend(handles,labels,loc='outside lower center',ncols=len(labels),fontsize=9)
def normal(q):return Normalize(min(v.min() for r in q for v in r),max(v.max() for r in q for v in r))
cmap=plt.get_cmap('viridis')
snaps=[[d['dec'](d['g'][j])[:,:,0] for j in inds] for d in D];norm=normal(snaps)
fig,ax=plt.subplots(2,3,figsize=(9,5.5),sharex=True,sharey=True,layout='constrained')
for i in range(2):
 for j,k in enumerate(inds):
  q=ax[i,j];q.pcolormesh(y,z,snaps[i][j],cmap=cmap,norm=norm,shading='nearest');q.add_patch(plt.Circle((0,hub),89.15,fill=False,color='white',lw=1));q.set_aspect('equal');q.set_title(f'({chr(97+3*i+j)}) {names[i]}, t = {t[k]:.0f} s',loc='left');q.set_xlabel('y (m)' if i==1 else '');q.set_ylabel('z (m)' if j==0 else '')
fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,label='u (m/s)',shrink=.9);save(fig,'01_rotor_snapshots')
sub=ix[::max(1,len(ix)//1200)];cuts=[[d['dec'](d['g'][sub,mid,:,:])[:,:,0],d['dec'](d['g'][sub,:,mid,:])[:,:,0]] for d in D];norm=normal(cuts);fig,ax=plt.subplots(2,2,figsize=(9.3,5.1),sharex=True,layout='constrained')
for i in range(2):
 for j,coord in enumerate([y,z]):
  q=ax[j,i];q.pcolormesh(t[sub],coord,cuts[i][j].T,cmap=cmap,norm=norm,shading='nearest');q.set_title(f'({chr(97+j*2+i)}) {names[i]} — '+['hub-height section','vertical centreline'][j],loc='left');q.set_ylabel(['y (m)','z (m)'][j]);q.set_xlabel('Time (s)' if j==1 else '')
fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,label='u (m/s)');save(fig,'02_spatiotemporal')
ids=[ix[int((len(ix)-1)*v)] for v in [.05,.27,.49,.71,.93]];slices=[[d['dec'](d['g'][j])[:,:,0] for j in ids] for d in D];norm=normal(slices);Y,Z=np.meshgrid(y,z);fig=plt.figure(figsize=(11.7,4.9));fig.subplots_adjust(left=.025,right=.89,bottom=.08,top=.92,wspace=.18)
for i in range(2):
 q=fig.add_subplot(1,2,i+1,projection='3d')
 for j,k in enumerate(ids):q.plot_surface(np.full_like(Y,t[k]),Y,Z,facecolors=cmap(norm(slices[i][j])),rstride=1,cstride=1,shade=False,linewidth=0)
 q.set_title(f'({chr(97+i)}) {names[i]}');q.set_xlabel('Time (s)');q.set_ylabel('y (m)');q.set_zlabel('z (m)',labelpad=7);q.set_xlim(start,end);q.set_box_aspect((1.5,1,1));q.view_init(24,-62);q.tick_params(labelsize=8)
fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([.93,.2,.014,.58]),label='u (m/s)');save(fig,'03_wind_field_3d')
V=[d['dec'](d['g'][:,levels,mid,:])[ix] for d in D];fig,ax=plt.subplots(3,3,figsize=(10.4,6.4),sharex=True,sharey='col',layout='constrained')
for j,iz in enumerate(levels):
 for k in range(3):
  q=ax[j,k];lines=[q.plot(ts,V[i][:,j,k],color=colors[i],lw=.55,alpha=.87)[0] for i in range(2)];panel(q,3*j+k,f'{comp[k]}, z = {z[iz]:.2f} m');q.set_xlabel('Time (s)' if j==2 else '');q.set_ylabel(f'{comp[k]} (m/s)')
plegend(fig,lines,names);save(fig,'04_height_component_timeseries')
fig,ax=plt.subplots(3,3,figsize=(10.4,6.8),sharex=True,sharey='col',layout='constrained');rows=[];summary=[]
for j,iz in enumerate(levels):
 for k in range(3):
  q=ax[j,k];handles=[]
  for i,d in enumerate(D):
   ff,ps=signal.welch(V[i][:,j,k],**fkw);ff,ps=ff[1:],ps[1:];sg=d['au']['target_sigma'][k];target=4*sg**2*L[k]/U/(1+6*ff*L[k]/U)**(5/3)
   handles.extend([q.loglog(ff,ps,lw=.8,color=colors[i])[0],q.loglog(ff,target,lw=1.05,ls='--',color=colors[i])[0]])
   rows.extend(zip([names[i]]*len(ff),[z[iz]]*len(ff),[comp[k]]*len(ff),ff,ps,target));summary.append([names[i],z[iz],comp[k],V[i][:,j,k].mean(),V[i][:,j,k].std(ddof=1),sg])
  panel(q,3*j+k,f'{comp[k]}, z = {z[iz]:.2f} m');q.set_xlabel('Frequency (Hz)' if j==2 else '');q.set_ylabel('PSD [(m/s)²/Hz]' if k==0 else '')
plegend(fig,handles,['NTM native','NTM target','ETM native','ETM target']);save(fig,'05_nine_component_spectra')
fig,ax=plt.subplots(2,3,figsize=(10.1,6.1),sharey=True,layout='constrained');profile=[]
for i,d in enumerate(D):
 v=d['dec'](d['g'][:,:,mid,:])[ix];tw=d['dec'](d['tw'])[ix]
 zz=np.r_[d['zt'][1:],z];v=np.concatenate([tw[:,1:,:],v],axis=1);o=np.argsort(zz);zz=zz[o];v=v[:,o,:];m=v.mean(0);sd=v.std(0,ddof=1);ti=100*sd/m[:,0,None];angles=np.degrees(np.arctan2(m[:,1],m[:,0]));values=[m[:,0],angles,*ti.T,m[:,2]]
 for k,q in enumerate(ax.flat):q.plot(values[k],zz,'o-',ms=2.5,lw=.85,color=colors[i],label=names[i]);q.axhline(z[0],color='.5',ls=':',lw=.8)
 for j in range(len(zz)):profile.append([names[i],zz[j],*m[j],*sd[j],*ti[j],angles[j]])
ax[0,0].plot(U*(zz/hub)**.2,zz,'--',lw=1,color='.2',label='Power law, α=0.2');ax[0,1].axvline(0,ls='--',color='.3',lw=.8);ax[1,2].axvline(0,ls='--',color='.3',lw=.8)
for k,(q,label) in enumerate(zip(ax.flat,['Mean u (m/s)','Mean-flow direction (°)','TIᵤ (%)','TIᵥ (%)','TIw (%)','Mean w (m/s)'])):panel(q,k);q.set_xlabel(label);q.set_ylabel('Height (m)' if k%3==0 else '')
ax[0,0].legend(fontsize=8);save(fig,'06_full_height_profiles')
fig,ax=plt.subplots(1,3,figsize=(10.1,3.4),sharey=True,layout='constrained');co=[];steps=[1,2,4] if len(y)==11 else [1,5,20]
for j,step in enumerate(steps):
 r=step*(y[1]-y[0]);q=ax[j];hs=[]
 for i,d in enumerate(D):
  X=d['dec'](d['g'][:,mid,:,0:3])[ix,:,0].T;A=X[:-step];B=X[step:];ff,pa=signal.welch(A,axis=-1,**fkw);_,pb=signal.welch(B,axis=-1,**fkw);_,px=signal.csd(A,B,axis=-1,**fkw);cc=(px.real/np.sqrt(np.maximum(pa*pb,1e-30))).mean(0);hs.append(q.semilogx(ff[1:],cc[1:],lw=.8,color=colors[i])[0]);co.extend(zip([names[i]]*(len(ff)-1),[r]*(len(ff)-1),ff[1:],cc[1:]))
 target=np.exp(-12*np.sqrt((ff*r/U)**2+(.12*r/340.2)**2));hs.append(q.semilogx(ff[1:],target[1:],'--',lw=1,color='.15')[0]);panel(q,j,f'r = {r:.0f} m');q.set_xlabel('Frequency (Hz)');q.set_ylim(-.5,1.02)
ax[0].set_ylabel('Longitudinal co-coherence');plegend(fig,hs,['NTM','ETM','IEC target']);save(fig,'07_spatial_cocoherence')
for name,header,data in [('spectra.csv',['case','height_m','component','frequency_Hz','PSD','hub_reference_target'],rows),('height_stats.csv',['case','height_m','component','mean','std','target_sigma'],summary),('profiles.csv',['case','z_m','u_mean','v_mean','w_mean','u_sd','v_sd','w_sd','TIu_pct','TIv_pct','TIw_pct','mean_direction_deg'],profile),('coherence.csv',['case','spacing_m','f_Hz','pair_mean_cocoherence'],co)]:
 with (out/name).open('w') as f:w=csv.writer(f);w.writerow(header);w.writerows(data)
manifest=dict(scope='native new cases; pilot if grid 11; no measurement or structural validation',source_BTS=[d['sha'] for d in D],grid=len(y),speed=U,window=[start,end],heights=z[levels].tolist(),nperseg=nper,overlap=nover,df_Hz=1/dt/nper,coherence='pair-averaged signed real cross spectrum normalized by autospectra; pairs not independent',target='IEC hub-reference spectra at all heights for comparison, not height-specific measured spectra',files=figs)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
