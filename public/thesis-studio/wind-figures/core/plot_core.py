"""He 2024 Fig 2-1--2-3: actual full-grid TurbSim CSV, no simulated data fabrication."""
import pathlib, argparse, json, hashlib, math
import numpy as np
from scipy.signal import welch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
from matplotlib.ticker import MultipleLocator
p=argparse.ArgumentParser();p.add_argument('ntm',type=pathlib.Path);p.add_argument('etm',type=pathlib.Path);p.add_argument('out',type=pathlib.Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':['DejaVu Serif','AR PL SungtiL GB'],'font.size':10,'mathtext.fontset':'dejavuserif','axes.unicode_minus':False,'axes.linewidth':.8,'pdf.fonttype':42,'svg.fonttype':'path','savefig.dpi':300,'legend.frameon':False})
colors=['#28669a','#a83d32']; labels=['NTM','ETM']; cases=[]; records=[]
for name,src in zip(labels,[a.ntm,a.etm]):
    q=next(src.rglob('audit.json')).parent
    au=json.loads((q/'audit.json').read_text()); t=np.loadtxt(q/'hub_uvw.csv',delimiter=',',skiprows=1); s=np.loadtxt(q/'psd_u.csv',delimiter=',',skiprows=1)
    assert au['nz']==au['ny']==51 and au['nt']==14000 and au['n_window']==12000 and au['window_s']==[100,700] and abs(au['config']['speed']-11.4)<1e-8 and au['config']['type']==('NTM' if name=='NTM' else '1ETM')
    assert t.shape==(12000,4) and np.allclose(t[:,0],100+np.arange(12000)*.05,atol=1e-9,rtol=0)
    assert au['config']['fields']['RandSeed1']=='20261124' and au['config']['fields']['ScaleIEC']=='0'
    f,P=welch(t[:,1],fs=20,window='hann',nperseg=2048,noverlap=1024,detrend='constant');f,P=f[1:],P[1:];sigma=.16*(.75*11.4+5.6) if name=='NTM' else 2*.16*(.072*(10/2+3)*(11.4/2-4)+10);target=4*sigma**2*340.2/11.4/(1+6*f*340.2/11.4)**(5/3)
    assert np.allclose(f,s[:,0],rtol=1e-12) and np.allclose(P,s[:,1],rtol=2e-5,atol=1e-9) and np.allclose(target,s[:,2],rtol=1e-10)
    m,sd=t[:,1].mean(),t[:,1].std(ddof=1);assert abs(m-au['hub_mean'][0])<3e-5 and abs(sd-au['hub_std'][0])<2e-5
    cases.append((au,t,f,P,target));records.append({'case':name,'BTS_sha256_from_native_audit':au['BTS_sha256'],'csv_sha256':hashlib.sha256((q/'hub_uvw.csv').read_bytes()).hexdigest(),'mean_u':float(m),'sd_u':float(sd),'target_sd_u':float(sigma),'relative_sd_error_pct':float(100*(sd/sigma-1)),'mean_error_pct':float(100*(m/11.4-1)),'max_absolute_PSD_recompute_difference':float(np.max(abs(P-s[:,1]))),'BTS_independent_decode':'not performed for full raw BTS','sample_count':len(t)})
    np.savetxt(a.out/(name+'_u_psd.csv'),np.c_[f,P,target],delimiter=',',header='frequency_Hz,Welch_PSD,target_PSD',comments='')
    np.savetxt(a.out/(name+'_hub_uvw.csv'),t,delimiter=',',header='time_s,u_m_s,v_m_s,w_m_s',comments='')
def save(fig,stem):
    for ext in ('png','svg','pdf'):fig.savefig(a.out/(stem+'.'+ext),bbox_inches='tight',pad_inches=.06)
    plt.close(fig)
au=cases[0][0];hub=au['zhub'];z0=au['zbottom'];y=np.linspace(-100,100,51);z=z0+np.arange(51)*4;Y,Z=np.meshgrid(y,z);R=89.15
fig,ax=plt.subplots(figsize=(4.9,5.15));fig.subplots_adjust(left=.19,right=.94,bottom=.12,top=.96)
ax.scatter(Y,Z,s=2.7,color='#aeb5ba',linewidths=0,zorder=1);ax.add_patch(Rectangle((-100,z0),200,200,fill=False,ec='.55',lw=.7));ax.add_patch(Circle((0,hub),R,fill=False,ec='#333',ls=(0,(6,4)),lw=1.05,zorder=3));ax.add_patch(Polygon([(-4.5,0),(-2,158),(2,158),(4.5,0)],closed=True,fc='white',ec='#333',lw=.8,zorder=4))
for ang in (90,210,330):
    th=np.deg2rad(ang);dr=np.array([np.cos(th),np.sin(th)]);perp=np.array([-dr[1],dr[0]]);rr=np.array([3,18,52,89.15,60,18,3]);ww=np.array([1.4,3.1,1.9,.15,-.75,-1.8,-1.4]);xy=np.array([0,hub])+rr[:,None]*dr+ww[:,None]*perp;ax.add_patch(Polygon(xy,closed=True,fc='white',ec='#333',lw=.8,zorder=5))
ax.add_patch(Circle((0,hub),2.6,fc='white',ec='#333',lw=.8,zorder=6));ax.plot(np.zeros(16),z0-np.arange(16)*4,'o',ms=2.7,mfc='#a83d32',mec='none',zorder=7);ax.axhline(0,color='.35',lw=.8);ax.annotate('轮毂高 161.37 m',xy=(0,hub),xytext=(22,hub+10),fontsize=9,arrowprops={'arrowstyle':'-','lw':.6});ax.text(0,z[-1]+9,'200 m × 200 m，51 × 51',ha='center',fontsize=9);ax.annotate('塔身补充节点',xy=(0,25.37),xytext=(25,25),fontsize=9,arrowprops={'arrowstyle':'-','lw':.6});ax.set(xlim=(-111,111),ylim=(-4,280),aspect='equal',xlabel='横向坐标 / m',ylabel='高程 / m');ax.set_xticks([-100,-50,0,50,100]);ax.set_yticks([0,50,100,150,200,250]);ax.tick_params(direction='in',length=3);save(fig,'01_wind_grid')
fig,axes=plt.subplots(2,1,figsize=(6.4,4.25),sharex=True,sharey=True);fig.subplots_adjust(left=.13,right=.98,bottom=.15,top=.96,hspace=.18)
lo=2*math.floor(min(c[1][:,1].min() for c in cases)/2);hi=2*math.ceil(max(c[1][:,1].max() for c in cases)/2)
for i,(ax,c) in enumerate(zip(axes,cases)):
    ax.plot(c[1][:,0]-100,c[1][:,1],lw=.44,color=colors[i]);ax.axhline(11.4,color='.35',lw=.65,ls='--');ax.text(.012,.90,f'({chr(97+i)}) {labels[i]}',transform=ax.transAxes,va='top',bbox={'fc':'white','ec':'none','alpha':.9,'pad':1.3});ax.set_ylim(lo,hi);ax.set_xlim(0,600);ax.set_ylabel('纵向风速 / (m·s⁻¹)');ax.grid(ls=':',color='.7',lw=.5);ax.tick_params(direction='in',length=3)
axes[-1].set_xlabel('有效时段时间 / s');axes[-1].xaxis.set_major_locator(MultipleLocator(100));save(fig,'02_hub_wind_history')
fig,axes=plt.subplots(1,2,figsize=(7.1,3.45),sharex=True,sharey=True);fig.subplots_adjust(left=.13,right=.985,bottom=.19,top=.92,wspace=.12)
for i,(ax,c) in enumerate(zip(axes,cases)):
    _,_,f,P,target=c;ax.loglog(f,P,color=colors[i],lw=.7,label='模拟自谱');ax.loglog(f,target,color='#202020',lw=1.1,ls='--',label='Kaimal目标谱');ax.set_title(f'({chr(97+i)}) {labels[i]}',loc='left',fontsize=10);ax.set_xlim(f[0],10);ax.set_ylim(1e-5,1e3);ax.grid(which='major',ls=':',lw=.6,color='.65');ax.tick_params(which='both',direction='in',length=3);ax.set_xlabel('频率 / Hz');ax.legend(loc='lower left',fontsize=8)
axes[0].set_ylabel('功率谱密度 / (m²·s⁻²·Hz⁻¹)');save(fig,'03_hub_autospectrum')
manifest={'scope':'new native full-grid 11.4 m/s pair; one same seed per turbulence type; no formal IEC or experimental validation','source_run':45422889134,'source_artifacts':[14934504439,14939410377],'grid':[51,51],'dt':.05,'duration_s':700,'window_s':[100,700],'welch':{'nperseg':2048,'noverlap':1024,'df_Hz':20/2048,'window':'Hann','detrend':'constant'},'reference':'He Zeyu (2024), thesis printed p9, Fig.2-1–2-3','figures':['01_wind_grid','02_hub_wind_history','03_hub_autospectrum'],'cases':records}
(a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(json.dumps(manifest,ensure_ascii=False,indent=2))
