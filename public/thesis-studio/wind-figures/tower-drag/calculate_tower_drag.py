"""Independent quasi-steady tower-only drag; no structural velocity, rotor or FE response."""
import pathlib as P, re, csv, hashlib, json, struct, zipfile, sys
import numpy as np
from numpy.polynomial.legendre import leggauss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def geom(raw):
 parts={};tr={};name=None;mode=None
 for l in raw.decode('utf-8').splitlines():
  if l.startswith('*Part,'):
   name=l.split('name=')[1];mode=None
  elif l.startswith('*End Part'):name=None;mode=None
  elif l.startswith('*Instance,'):
   part=l.split('part=')[1];tr[part]=[0,0,0];mode='instance' if re.fullmatch(r'CSEG_\d+|SSEG_\d+|FLANGE_SOLID',part) else None
  elif l.startswith('*Node') and name and re.fullmatch(r'CSEG_\d+|SSEG_\d+|FLANGE_SOLID',name):parts[name]=[];mode='node'
  elif l.startswith('*'):
   mode=None
  elif mode=='node':parts[name].append([float(x) for x in l.split(',')[1:4]])
  elif mode=='instance':
   v=[float(x) for x in l.split(',')];assert len(v)==3;tr[part]=v;mode=None
 out=[]
 for k,v in parts.items():
  a=np.array(v)+tr[k];z=np.round(a[:,1],5);zs=np.unique(z);d=np.array([2*np.hypot(a[z==q,0],a[z==q,2]).max() for q in zs])
  out.append((k,zs,d))
 out.sort(key=lambda v:v[1][0])
 assert len(out)==36 and sum(k.startswith('CSEG') for k,_,_ in out)==31 and sum(k.startswith('SSEG') for k,_,_ in out)==4
 assert abs(out[0][1][0])<1e-5 and abs(out[-1][1][-1]-158)<1e-5
 assert all(abs(out[i][1][-1]-out[i+1][1][0])<1e-5 for i in range(35))
 return out
def read(path,expect):
 assert sha(path)==expect
 with path.open('rb') as f:
  h=struct.unpack('<h4i6f6fi',f.read(70));f.read(h[-1]);off=f.tell()
 ident,nz,ny,ntr,nt=h[:5];dz,dy,dt,uh,hub,z0=h[5:11]
 assert (ident,nz,ny,ntr,nt)==(8,51,51,16,14000) and abs(dt-.05)<1e-7
 assert path.stat().st_size==off+nt*3*(nz*ny+ntr)*2
 sc=np.array(h[11:16:2]);ofs=np.array(h[12:17:2]);assert np.all(sc!=0)
 a=np.memmap(path,dtype='<i2',mode='r',offset=off,shape=(nt,nz*ny+ntr,3))
 # Only 600 s effective window; retain grid centerline and lower supplemental tower nodes.
 a=a[2000:14000];g=a[:,:nz*ny].reshape(12000,nz,ny,3)[:,:,ny//2,:2];tw=a[:,nz*ny:,:2]
 z=np.r_[z0-np.arange(ntr)*dz,z0+np.arange(nz)*dz]
 v=(np.concatenate([tw,g],axis=1).astype(np.float64)-ofs[:2])/sc[:2]
 # Duplicate z0 is represented by grid centerline, not averaged. Tower node 0 may differ; record it.
 dup=float(np.max(np.abs(v[:,0]-v[:,ntr])))
 keep=np.r_[np.arange(1,ntr),np.arange(ntr,ntr+nz)];z=z[keep];v=v[:,keep];order=np.argsort(z);z=z[order];v=v[:,order]
 assert np.all(np.diff(z)>0) and 0<z[0]<2 and z[-1]>158
 return z,v,dup
def weights(z,x):
 j=np.clip(np.searchsorted(z,x,side='right')-1,0,len(z)-2);w=(x-z[j])/(z[j+1]-z[j])
 return j,w
def integrate(geometry,z,v,order,ground='zero'):
 # below lowest BTS point: explicit sensitivity; no measurement at ground
 low=np.zeros((len(v),1,2)) if ground=='zero' else v[:,:1,:]
 z=np.r_[0,z];v=np.concatenate([low,v],axis=1)
 nodes,ww=leggauss(order);F=[];M=[];area=[]
 for name,Z,D in geometry:
  cuts=np.unique(np.r_[Z,z[(z>Z[0])&(z<Z[-1])]])
  a,b=cuts[:-1],cuts[1:]
  x=((a+b)[:,None]/2+(b-a)[:,None]/2*nodes).ravel()
  w=((b-a)[:,None]/2*ww).ravel()
  i,s=weights(z,x)
  u=v[:,i,:]*(1-s[None,:,None])+v[:,i+1,:]*s[None,:,None]
  diameter=np.interp(x,Z,D)
  # Cd=0.5, rho=1.225; horizontal wind velocity relative to stationary vertical tower.
  q=.5*1.225*.5*diameter[None,:,None]*np.linalg.norm(u,axis=2)[:,:,None]*u
  f=np.einsum('tqc,q->tc',q,w);m=np.einsum('tqc,q->tc',q,w*x)
  F.append(f);M.append(m);area.append(float(w@diameter))
 return np.stack(F,axis=1),np.stack(M,axis=1),np.array(area)
def selftest():
 z=np.array([1.,10.]);v=np.tile([10.,-3.],(3,2,1));g=[('test',np.array([0.,10.]),np.array([2.,2.]))]
 F,M,A=integrate(g,z,v,3,'hold');q=.5*1.225*.5*2*np.hypot(10,3)*np.array([10,-3])
 assert np.allclose(F[:,0],10*q) and np.allclose(M[:,0],50*q) and np.allclose(A,20)
def main():
 selftest()
 root=P.Path('public/thesis-studio/wind-figures');out=root/'tower-drag';out.mkdir(exist_ok=True)
 manifest=json.loads((root/'native/manifest.json').read_text())
 inp=P.Path('incoming/REV21.zip');assert inp.is_file()
 with zipfile.ZipFile(inp) as zz:
  assert zz.testzip() is None
  n=next(n for n in zz.namelist() if n.endswith('HE_REV21_MODE_FULL_ASSEMBLY.inp'));raw=zz.read(n)
 assert hashlib.sha256(raw).hexdigest()=='7538ccb15a0af82364f0482f4a30e65a59d157a3b33efb94c4beb295a646721c'
 g=geom(raw)
 with (out/'geometry.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['part','z_m','outer_diameter_m']);w.writerows((n,z,d) for n,zz,dd in g for z,d in zip(zz,dd))
 rec=[];series={};profiles={};maps=out/'timeseries';maps.mkdir(exist_ok=True)
 heights=np.array([(z[0]+z[-1])/2 for _,z,_ in g]);hlo=np.array([z[0] for _,z,_ in g]);hhi=np.array([z[-1] for _,z,_ in g])
 for case in manifest['cases']:
  if case['grid']!=51:continue
  key=case['key'];p=next((P.Path('incoming/bts')/(key+'-bts')).rglob('case.bts'))
  z,v,dup=read(p,case['BTS_sha256'])
  F,M,area=integrate(g,z,v,3);F5,M5,_=integrate(g,z,v,5);Fg,Mg,_=integrate(g,z,v,3,'hold')
  errF=np.max(np.abs(F-F5));errM=np.max(np.abs(M-M5));relF=errF/max(1,np.max(np.abs(F5)));relM=errM/max(1,np.max(np.abs(M5)))
  assert relF<.002 and relM<.002,(relF,relM)
  # equivalent endpoint forces, exact resultant and first moment of every segment
  upper=(M-hlo[None,:,None]*F)/(hhi-hlo)[None,:,None];lower=F-upper
  ef=float(np.max(np.abs(lower+upper-F)));em=float(np.max(np.abs(lower*hlo[None,:,None]+upper*hhi[None,:,None]-M)))
  assert ef<1e-8 and em<1e-6
  fs=F.sum(axis=1);ms=M.sum(axis=1)
  # Abaqus global Y vertical; wind u=+X, v=-Z for right-handed mapping; r x F -> Mx=-z*v, Mz=-z*u.
  t=np.arange(12000)*.05+100
  arr=np.c_[t,fs[:,0],fs[:,1],ms[:,0],ms[:,1]]
  np.savetxt(maps/(key+'_resultant.csv'),arr,delimiter=',',header='time_s,Fu_N,Fv_N,first_moment_u_Nm,first_moment_v_Nm',comments='')
  np.savez_compressed(maps/(key+'_endpoint_loads.npz'),time_s=t,part=np.array([n for n,_,_ in g]),z_lower_m=hlo,z_upper_m=hhi,lower_uv_N=lower,upper_uv_N=upper)
  profiles[key]=(F[:,:,0]/(hhi-hlo)).mean(0),(F[:,:,0]/(hhi-hlo)).std(0,ddof=1),np.max(np.abs(F[:,:,0]/(hhi-hlo)),axis=0)
  series[key]=arr
  re=1.0/1.4775510204081632e-5*np.linalg.norm(v[:,(z<=158),:],axis=2)*np.interp(z[z<=158],np.unique(np.concatenate([a[1] for a in g])),np.array([max(np.interp(h,zz,dd) for _,zz,dd in g if zz[0]-1e-8<=h<=zz[-1]+1e-8) for h in np.unique(np.concatenate([a[1] for a in g]))]))[None,:]
  rec.append(dict(key=key,speed=case['speed'],type=case['type'],BTS_sha256=case['BTS_sha256'],cd=.5,area_m2=float(sum(area)),mean_Fu_N=float(fs[:,0].mean()),peak_abs_Fu_N=float(abs(fs[:,0]).max()),mean_Mu_Nm=float(ms[:,0].mean()),peak_abs_Mu_Nm=float(abs(ms[:,0]).max()),peak_abs_Fv_N=float(abs(fs[:,1]).max()),peak_abs_Mv_Nm=float(abs(ms[:,1]).max()),ground_hold_max_delta_Fu_N=float(abs(Fg.sum(1)[:,0]-fs[:,0]).max()),ground_hold_max_delta_Mu_Nm=float(abs(Mg.sum(1)[:,0]-ms[:,0]).max()),quadrature_rel_F=relF,quadrature_rel_M=relM,mapping_residual_N=ef,mapping_residual_Nm=em,duplicate_z0_velocity_diff=dup,Re_5_50_95=np.percentile(re,[5,50,95]).tolist()))
  print('VERIFIED',key,rec[-1],flush=True)
 assert len(rec)==6
 plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.linewidth':.8,'legend.frameon':False,'savefig.dpi':300,'svg.fonttype':'path','pdf.fonttype':42})
 def save(fig,n):
  for ext in ['png','svg','pdf']:fig.savefig(out/(n+'.'+ext),bbox_inches='tight',pad_inches=.06)
  plt.close(fig)
 cols={'NTM':'#215d8c','1ETM':'#a63c35'}
 fig,ax=plt.subplots(1,3,figsize=(9,4.5),sharey=True,layout='constrained')
 for key,(m,s,p) in profiles.items():
  if '11.4-' not in key:continue
  kind=key.split('-')[-1]
  for q,d in zip(ax,[m,s,p]):q.plot(d/1000,heights,'o-',ms=2.2,lw=.9,color=cols[kind],label=kind)
 for i,(q,l) in enumerate(zip(ax,['Mean q_u (kN/m)','Std q_u (kN/m)','Absolute peak q_u (kN/m)'])):q.set_xlabel(l);q.axhline(112,color='.5',ls=':',lw=.8);q.grid(alpha=.15);q.set_title(f'({chr(97+i)})',loc='left')
 ax[0].set_ylabel('Height (m)');ax[0].legend();save(fig,'01_heightwise_drag')
 fig,ax=plt.subplots(2,2,figsize=(9,5),sharex=True,sharey='row',layout='constrained')
 for j,k in enumerate(['NTM','1ETM']):
  a=series['native-full-11.4-'+k]
  for i,(y,label,factor) in enumerate([(1,'Tower drag (kN)',1e-3),(3,'Base first moment (MN m)',1e-6)]):
   q=ax[i,j];q.plot(a[:,0]-100,a[:,y]*factor,color=cols[k],lw=.55);q.set_title(f'({chr(97+i*2+j)}) {k}',loc='left');q.set_ylabel(label if j==0 else '');q.grid(alpha=.15);q.set_xlim(0,600)
   if i==1:q.set_xlabel('Time (s)')
 save(fig,'02_resultant_histories')
 fig,ax=plt.subplots(1,2,figsize=(7.8,3.6),layout='constrained')
 for k in ['NTM','1ETM']:
  rr=sorted([r for r in rec if r['type']==k],key=lambda r:r['speed']);x=[r['speed'] for r in rr]
  for q,key,factor in [(ax[0],'peak_abs_Fu_N',1e-3),(ax[1],'peak_abs_Mu_Nm',1e-6)]:
   y=np.array([r[key]*factor for r in rr]);q.plot(x,y,'o-',color=cols[k],label=k+' Cd=0.5');q.plot(x,y*1.4,'s--',color=cols[k],label=k+' Cd=0.7',ms=4)
 ax[0].set_ylabel('Peak tower drag (kN)');ax[1].set_ylabel('Peak first moment (MN m)')
 for q in ax:q.set_xlabel('Reference wind speed (m/s)');q.grid(alpha=.15)
 ax[0].legend(fontsize=8);save(fig,'03_cd_sensitivity')
 with (out/'statistics.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rec[0]));w.writeheader();w.writerows(rec)
 (out/'receipt.json').write_text(json.dumps({'scope':'six new stationary tower quasi-steady drag cases; Cd=0.5 baseline, 0.7 sensitivity; no motion feedback/rotor/load admission/FE','source_zip_sha256':sha(inp),'source_inp_sha256':hashlib.sha256(raw).hexdigest(),'source':'REV21 parent; REV22 only increment change','nodes':'16 supplemental incl duplicate bottom, 51 grid centerline; zero at ground compared to hold','cases':rec,'mapping':'mathematical 2-end equivalent forces; not Abaqus node or CLOAD mapping','coefficient_reference':'Archived AeroDyn Cd=0.5 (disabled); WES 2026 DOI 10.5194/wes-11-4059-2026; sensitivity 0.7 per DOI 10.1080/14786451.2021.1953495; not normative design acceptance'},indent=2))
if __name__=='__main__':main()
