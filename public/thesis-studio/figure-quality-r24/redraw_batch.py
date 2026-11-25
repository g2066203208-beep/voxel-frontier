"""Batch scientific replot from archived numeric sources only.
A missing source or failed numeric check blocks that figure individually.
Existing thesis is not changed automatically."""
from pathlib import Path
import csv, hashlib,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator,MaxNLocator
from matplotlib import font_manager
from PIL import Image
root=Path(__file__).resolve().parents[1];out=Path(__file__).resolve().parent
zh=next((x for x in ['Noto Serif CJK SC','AR PL SungtiL GB'] if any(f.name==x for f in font_manager.fontManager.ttflist)),None)
assert zh, 'Chinese serif font required'
plt.rcParams.update({'font.family':['Liberation Serif',zh],'font.size':9,'mathtext.fontset':'stix','axes.unicode_minus':False,'axes.linewidth':.7,'xtick.direction':'in','ytick.direction':'in','xtick.major.size':3,'ytick.major.size':3,'legend.frameon':False,'svg.fonttype':'path','pdf.fonttype':42,'savefig.dpi':300,'lines.linewidth':.85})
C={'NTM':'#185783','ETM':'#a63c32'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvnum(path):
    return np.genfromtxt(root/path,delimiter=',',names=True,dtype=float,encoding='utf-8-sig')
def labels(ax,x,y,panel=None):
    ax.set(xlabel=x,ylabel=y)
    if panel:ax.set_title(panel,loc='left',fontsize=9,pad=4)
    ax.tick_params(top=True,right=True)
def fig2(rows=1,cols=2,h=3):
    return plt.subplots(rows,cols,figsize=(170/25.4,h),layout='constrained',squeeze=False)
def save(id,fig,src):
    for ext in ['svg','png','pdf']:fig.savefig(out/(id+'.'+ext),bbox_inches='tight',pad_inches=.045)
    plt.close(fig)
    with Image.open(out/(id+'.png')) as im:
        im.verify()
    return {'id':id,'status':'RENDERED','sources':[{'path':str(p),'sha256':sha(root/p)} for p in src],'svg_sha256':sha(out/(id+'.svg')),'png_sha256':sha(out/(id+'.png'))}
results=[]
def run(id,fn):
    try:results.append(fn())
    except Exception as e:results.append({'id':id,'status':'BLOCKED','reason':str(e)});plt.close('all')
def cdp():
    src='inp-archive/REV22_REVIEW/rev22-cdp-curves.csv'
    a=list(csv.DictReader((root/src).open()))
    assert len(a)==100
    fig,ax=fig2(h=3.35)
    for i,branch in enumerate(['compression','tension']):
        q=ax[0,i];v=q.twinx()
        for j,m in enumerate(['C65','C70']):
            r=[x for x in a if x['material']==m and x['branch']==branch];assert len(r)==(26 if i==0 else 24)
            t=np.array([float(x['total_strain']) for x in r]);s=np.array([float(x['stress_MPa']) for x in r]);d=np.array([float(x['damage']) for x in r]);assert np.all(np.diff(t)>0) and np.all((d>=0)&(d<1))
            q.plot(t*1000,s,color=list(C.values())[j],label=m);v.plot(t*1000,d,color=list(C.values())[j],ls='--')
        labels(q,'总应变 / ‰','应力 / MPa','(a) 受压' if i==0 else '(b) 受拉');v.set_ylabel('损伤因子');v.set_ylim(0,1);v.tick_params(direction='in');q.set_ylim(bottom=0);q.legend(loc='upper right',fontsize=8)
    return save('r16-cdp-figure',fig,[src])
run('r16-cdp-figure',cdp)
def hub():
    ss=[f'wind-figures/native/native-full-11.4-{k}/hub_uvw.csv' for k in ['NTM','1ETM']]
    fig,axs=fig2(2,1,3.6);series=[]
    for k,s in zip(C,ss):
        a=np.loadtxt(root/s,delimiter=',',skiprows=1);assert a.shape==(12000,4) and np.allclose(a[:,0],100+np.arange(12000)*.05)
        series.append(a)
    lo=5*np.floor(min(a[:,1].min() for a in series)/5);hi=5*np.ceil(max(a[:,1].max() for a in series)/5)
    for i,(k,a) in enumerate(zip(C,series)):
        q=axs[i,0];q.plot(a[:,0]-100,a[:,1],color=C[k],lw=.48);q.axhline(11.4,color='.25',ls='--',lw=.7);q.set(xlim=(0,600),ylim=(lo,hi));labels(q,'时间 / s' if i else '','纵向风速 / (m/s)',f'({chr(97+i)}) {k}')
        if not i:q.tick_params(labelbottom=False)
    return save('wind-r11-002',fig,ss)
run('wind-r11-002',hub)
def tower_profile():
    ss=[f'wind-figures/tower-drag/timeseries/native-full-11.4-{k}_endpoint_loads.npz' for k in ['NTM','1ETM']]
    fig,axs=fig2(1,3,3.7)
    for k,s in zip(C,ss):
        a=np.load(root/s,allow_pickle=False);lo=a['z_lower_m'];hi=a['z_upper_m'];assert len(lo)==36 and np.all(hi>lo)
        f=(a['lower_uv_N'][:,:,0]+a['upper_uv_N'][:,:,0])/(hi-lo)/1000;assert f.shape==(12000,36)
        for i,v in enumerate([f.mean(0),f.std(0,ddof=1),abs(f).max(0)]):
            q=axs[0,i];q.plot(v,(lo+hi)/2,color=C[k],ls='-' if k=='NTM' else '--',label=k);q.axhline(112,color='.4',ls=':',lw=.65);q.set_ylim(0,158)
    for i,q in enumerate(axs[0]):labels(q,['均值 / (kN/m)','标准差 / (kN/m)','绝对峰值 / (kN/m)'][i],'高程 / m' if i==0 else '',f'({chr(97+i)})');q.tick_params(labelleft=i==0)
    axs[0,0].legend(fontsize=8)
    return save('wind-r14-005',fig,ss)
run('wind-r14-005',tower_profile)
def tower_time():
    ss=[f'wind-figures/tower-drag/timeseries/native-full-11.4-{k}_resultant.csv' for k in ['NTM','1ETM']]
    fig,axs=fig2(2,2,3.6);series=[]
    for s in ss:
        a=np.loadtxt(root/s,delimiter=',',skiprows=1);assert a.shape==(12000,5);series.append(a)
    for i,(col,scale,lab) in enumerate([(1,.001,'风阻合力 / kN'),(3,1e-6,'基底一阶矩 / (MN·m)')]):
        ymax=max(a[:,col].max()*scale for a in series);ymin=min(a[:,col].min()*scale for a in series)
        for j,(k,a) in enumerate(zip(C,series)):
            q=axs[i,j];q.plot(a[:,0]-100,a[:,col]*scale,color=C[k],lw=.5);q.set(xlim=(0,600),ylim=(min(0,ymin),ymax*1.05));labels(q,'时间 / s' if i else '',lab if j==0 else '',f'({chr(97+2*i+j)}) {k}');q.tick_params(labelbottom=bool(i),labelleft=j==0)
    return save('wind-r14-007',fig,ss)
run('wind-r14-007',tower_time)
def historical(id,channels,ylabs,scales):
    ss=[f'wind-figures/historical-control/U11p4_{k}_S01.csv' for k in C]
    aa=[csvnum(s) for s in ss]
    assert all(len(a)==12001 for a in aa)
    fig,axs=fig2(len(channels),2,2.1*len(channels))
    for i,(ch,lab,scale) in enumerate(zip(channels,ylabs,scales)):
        v=[a[ch]*scale for a in aa];lo=min(z.min() for z in v);hi=max(z.max() for z in v);pad=max((hi-lo)*.04,1e-8)
        for j,(k,a,y) in enumerate(zip(C,aa,v)):
            q=axs[i,j];t=a[a.dtype.names[0]];assert abs(t[0]-100)<1e-6 and abs(t[-1]-700)<1e-6
            q.plot(t-100,y,color=C[k],lw=.5);q.set(xlim=(0,600),ylim=(lo-pad,hi+pad));labels(q,'时间 / s' if i==len(channels)-1 else '',lab if j==0 else '',f'({chr(97+2*i+j)}) {k}');q.tick_params(labelbottom=i==len(channels)-1,labelleft=j==0)
    return save(id,fig,ss)
run('wind-r13-002',lambda:historical('wind-r13-002',['Wind1VelX','RotSpeed','BldPitch1','GenPwr','TwrBsMyt'],['风速 / (m/s)','转速 / (r/min)','桨距角 / °','功率 / MW','塔底弯矩 / (MN·m)'],[1,1,1,.001,.001]))
run('wind-r13-004',lambda:historical('wind-r13-004',['GenPwr','RotThrust'],['发电功率 / MW','转子推力 / MN'],[.001,.001]))
def peaks():
    src='wind-figures/historical-control/statistics.csv';a=list(csv.DictReader((root/src).open()));fig,axs=fig2(2,2,5.1);speeds=[9.343881,11.4,19.20214];keys=['U09p343881','U11p4','U19p202140']
    for i,(ch,label) in enumerate(zip(['TwrBsMxt','TwrBsMyt','RootMxb1','RootMyb1'],['塔底 Mx','塔底 My','叶根 Mx','叶根 My'])):
        q=axs.flat[i]
        for k in C:
            for s,key in zip(speeds,keys):
                v=[float(r['abs_peak'])/1000 for r in a if r['channel']==ch and r['case'].startswith(key+'_'+k+'_') and r['unit']=='(kN-m)'];assert len(v)==6
                q.plot([s]*6,v,marker='o' if k=='NTM' else 's',mfc='none',mec=C[k],ms=3,ls='none');q.plot(s,np.mean(v),marker='o' if k=='NTM' else 's',color=C[k],ms=4,label=k if key==keys[0] else None)
        q.set_xticks(speeds,['9.344','11.400','19.202']);labels(q,'参考风速 / (m/s)',label+' / (MN·m)',f'({chr(97+i)})');q.set_ylim(bottom=0)
    axs[0,0].legend()
    return save('wind-r13-008',fig,[src])
run('wind-r13-008',peaks)
def direction():
    src='primary-data/era5-direction.csv';a=list(csv.DictReader((root/src).open()));assert len(a)==16
    theta=np.arange(16)*2*np.pi/16;v=[float(x['high_v100_ge_p95_pct']) for x in a]
    assert abs(sum(v)-100)<.2
    f=plt.figure(figsize=(85/25.4,3.45),layout='constrained');q=f.add_subplot(111,projection='polar');q.set_theta_zero_location('N');q.set_theta_direction(-1);q.bar(theta,v,width=2*np.pi/16*.85,color='#185783',edgecolor='black',linewidth=.4);q.set_xticks(theta[::2],[x['sector'] for x in a[::2]]);q.set_rlabel_position(270);q.set_yticks([10,20,30,40],['10%','20%','30%','40%']);q.set_ylim(0,40)
    return save('b0346',f,[src])
run('b0346',direction)
(out/'receipt.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(results,indent=2,ensure_ascii=False))
