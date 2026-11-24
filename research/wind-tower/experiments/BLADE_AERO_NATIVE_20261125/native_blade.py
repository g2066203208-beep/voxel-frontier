"""Recover original DTU158 OpenFAST inputs by SHA, create independent native aero-output cases."""
from pathlib import Path
import argparse, json, re, hashlib, io, zipfile, urllib.request, shutil, subprocess, os
P=argparse.ArgumentParser();P.add_argument('--stage',choices=['restore','run','post'],required=True);P.add_argument('--type',choices=['NTM','1ETM'],default='NTM');P.add_argument('--duration',type=float,default=10);P.add_argument('--exe',type=Path);P.add_argument('--dll',type=Path);a=P.parse_args()
ROOT=Path.cwd();OUT=ROOT/'native-aero';CASE=OUT/'case';OUT.mkdir(exist_ok=True)
PIN='5ce9b969cbbbf6a4e921d432eb43b596696458be';REPO='g2066203208-beep/voxel-frontier'
BASE=f'https://raw.githubusercontent.com/{REPO}/{PIN}/research/wind-tower/archive/'
PREFIX='CASES/U11p4_NTM_S01/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def download(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'thesis-native-aero'}),timeout=120) as f:return f.read()
def change(p,key,new):
    s=p.read_text(encoding='utf-8-sig');pat=r'(?m)^(\s*)(?:"[^"\r\n]*"|[^ \t\r\n]+)([ \t]+'+re.escape(key)+r'(?=[ \t]|$)[^\r\n]*)'
    s,n=re.subn(pat,lambda m:m[1]+str(new)+m[2],s);assert n==1,(str(p),key,n);p.write_text(s,encoding='utf8')
def getval(p,key):
    s=p.read_text(encoding='utf-8-sig')
    m=re.search(r'(?m)^\s*("[^"\r\n]*"|[^ \t\r\n]+)[ \t]+'+re.escape(key)+r'(?=[ \t]|$)',s)
    assert m,(str(p),key);return m[1]
def restore():
    CASE.mkdir(exist_ok=True)
    names=['local-assets-20261004','local-assets-20261004-supplement']
    entries={};receipts=[];zips={}
    for name in names:
        raw=download(BASE+name+'/file-manifest.json')
        (OUT/(name+'-manifest.json')).write_bytes(raw)
        for e in json.loads(raw):
            path=e['relative_path']
            if e['section']=='openfast-36-r2' and path.startswith(PREFIX) and e.get('canonical_archive') and e.get('sha256') and Path(path).suffix.lower() in ('.fst','.dat','.in','.txt'):
                if Path(path).name.startswith(('smoke','run_','openfast_')):continue
                entries[path[len(PREFIX):]]=e
    for name in ['DTU_10MW_RWT.fst','DTU_10MW_RWT_ElastoDyn.dat','DTU_10MW_InflowWind.dat','C02R3R2_158M_Tower.dat','Rotor/DTU_10MW_RWT_AeroDyn15.dat','Rotor/DTU_10MW_AeroDyn15_blade.dat','Rotor/DTU_10MW_ElastoDyn_Blades.dat','Control/DTU_10MW_RWT_ServoDyn.dat','Control/DTU_10MW_RWT_DISCON.IN','Control/Cp_Ct_Cq_10MW.txt']:
        assert name in entries,name
    for name,e in entries.items():
        ap=e['canonical_archive']
        if ap not in zips:
            data=download(f'https://raw.githubusercontent.com/{REPO}/{PIN}/{ap}')
            z=zipfile.ZipFile(io.BytesIO(data));assert z.testzip() is None
            zips[ap]=(z,sha(data))
        z,zsha=zips[ap];data=z.read(e['canonical_member'])
        assert sha(data)==e['sha256'].lower() and len(data)==e['bytes'],name
        p=CASE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        receipts.append(dict(name=name,sha256=sha(data),archive=ap,archive_sha256=zsha,member=e['canonical_member']))
    assert len(receipts)>=16
    (OUT/'source_receipt.json').write_text(json.dumps({'case_source':'U11p4_NTM_S01 historical OpenFAST v3.5.3','source_commit':PIN,'inputs':receipts,'controller_binary_original':'not recovered; version-pinned substitute required'},indent=2))
    # archive originals and verify all subsequently changed fields are explicit
    shutil.make_archive(str(OUT/'original-inputs'),'zip',CASE)
    print('SOURCE_RESTORE_PASS',len(receipts),flush=True)
def run():
    assert a.exe and a.exe.is_file() and a.dll and a.dll.is_file()
    wind=next((ROOT/'incoming').rglob('case.bts'))
    expected={'NTM':'548695c6f8f4241643291624eef4ced091b1b4186d43faad4ea9cb98df3121e1','1ETM':'235d1224cc3f0d0b282e9fb94647ca5b507c8c37b6256bf056f02dbabfb3b04e'}[a.type]
    assert sha(wind.read_bytes())==expected
    assert sha(a.exe.read_bytes())=='0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a'
    assert sha(a.dll.read_bytes())=='7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa'
    dst=CASE/'new_wind.bts';shutil.copyfile(wind,dst)
    fst=CASE/'DTU_10MW_RWT.fst';ifw=CASE/'DTU_10MW_InflowWind.dat';ad=CASE/'Rotor/DTU_10MW_RWT_AeroDyn15.dat';srv=CASE/'Control/DTU_10MW_RWT_ServoDyn.dat'
    # Preserve physical model and original control parameters; only input wind and output configuration change.
    assert getval(ad,'TwrAero').lower()=='false'
    ed=CASE/'DTU_10MW_RWT_ElastoDyn.dat'
    edits=[(fst,'AeroFile','"Rotor/DTU_10MW_RWT_AeroDyn15.dat"'),(fst,'TMax',a.duration),(fst,'TStart',0 if a.duration<100 else 100),(fst,'DT_Out',0.05),(fst,'OutFileFmt',2),(ifw,'WindType',3),(ifw,'FileName_BTS','"new_wind.bts"'),(srv,'DLL_FileName','"libdiscon.dll"')]
    # ED references historically point to shared ../Rotor; relocate only those active paths.
    for key in ['BldFile(1)','BldFile(2)','BldFile(3)']:
        old=getval(ed,key).strip('"').replace('\\','/')
        if old.startswith('../Rotor/'):
            edits.append((ed,key,'"'+old[3:]+'"'))
        else:
            assert (CASE/old).is_file(),(key,old)
    audit=[]
    for path,k,v in edits:
        old=getval(path,k);change(path,k,v);audit.append({'file':str(path.relative_to(CASE)),'field':k,'old':old,'new':str(v)})
    shutil.copy2(a.dll,CASE/'Control/libdiscon.dll')
    # Explicitly request all six true aerodynamic rotor loads in hub coordinates.
    s=ad.read_text(encoding='utf-8-sig');pat=r'(?m)^END[^\r\n]*';m=re.search(pat,s);assert m
    assert 'BldNd_BladesOut' not in s
    s=s[:m.start()]+''.join(f'"RtAero{k}h"\n' for k in ['Fx','Fy','Fz','Mx','My','Mz'])+s[m.start():m.end()]+'\n---------------------- NODE OUTPUTS --------------------------------------------\n3 BldNd_BladesOut\n99 BldNd_BlOutNd\nOutList\n"Fx"\n"Fy"\n"Mm"\n"Fn"\n"Ft"\n"Fl"\n"Fd"\n"VRel"\n"Alpha"\nEND\n'
    ad.write_text(s,encoding='utf8')
    (OUT/'run_config.json').write_text(json.dumps({'type':a.type,'duration_s':a.duration,'wind_sha256':expected,'exe_sha256':sha(a.exe.read_bytes()),'controller_sha256':sha(a.dll.read_bytes()),'controller':'ROSCO 2.6.0 version replacement, byte identity to historical DLL unverified','edits':audit,'AeroDyn_outputs':'RtAero six-component hub wrench; all blade nodes legacy local Fx Fy Mm Fn Ft Fl Fd VRel Alpha','TwrAero':False,'scope':'new inflow, historical reduced structure, not REV22 or mapped FE load'},indent=2))
    with (OUT/'native.log').open('w',encoding='utf8') as f:
        proc=subprocess.run([str(a.exe.resolve()),fst.name],cwd=CASE,stdout=f,stderr=subprocess.STDOUT,timeout=5400)
    log=(OUT/'native.log').read_text(errors='replace');print(log[-7000:])
    assert proc.returncode==0 and 'OpenFAST terminated normally' in log,proc.returncode
def post():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from outb_reader import outb_header
    import csv
    raw=(CASE/'DTU_10MW_RWT.outb').read_bytes();h=outb_header(raw);n=h['num_output_channels'];nt=h['num_samples'];names=h['channel_names'];units=dict(zip(names,h['channel_units']))
    assert h['file_id'] in (2,4) and h['time_increment_s']>0
    t=h['first_time_s']+np.arange(nt)*h['time_increment_s'];expected_end=a.duration
    assert abs(t[-1]-expected_end)<.051 and abs(h['time_increment_s']-.05)<1e-8
    assert np.isfinite(h['column_scales']).all() and np.all(np.asarray(h['column_scales'])!=0)
    v=(np.frombuffer(raw,dtype='<i2',offset=h['data_offset_bytes']).reshape(nt,n).astype(np.float64)-np.asarray(h['column_offsets']))/np.asarray(h['column_scales'])
    assert np.isfinite(v).all()
    groups=['Fx','Fy','Mm','Fn','Ft','Fl','Fd','VRel','Alpha']
    pat=re.compile(r'^AB([123])N(\d{3})('+ '|'.join(groups)+r')$')
    nd={(int(m[1]),int(m[2]),m[3]):k for k in names if (m:=pat.fullmatch(k))}
    nodeids=sorted({k[1] for k in nd});assert nodeids==list(range(1,41))
    assert set(nd)=={(b,j,g) for b in range(1,4) for j in range(1,41) for g in groups}
    unit_gate={'Fx':'(N/m)','Fy':'(N/m)','Mm':'(N-m/m)','Fn':'(N/m)','Ft':'(N/m)','Fl':'(N/m)','Fd':'(N/m)','VRel':'(m/s)','Alpha':'(deg)'}
    assert all(units[k]==unit_gate[g] for (b,j,g),k in nd.items())
    assert nt==(201 if a.duration==10 else 12001)
    assert abs(t[0]-(0 if a.duration==10 else 100))<1e-9
    blade=CASE/'Rotor/DTU_10MW_AeroDyn15_blade.dat';lines=blade.read_text().splitlines()
    ix=next(i for i,l in enumerate(lines) if 'BlSpn' in l)
    radii=[]
    for l in lines[ix+2:]:
        try:
            vals=[float(q) for q in l.split()[:7]]
            if len(vals)!=7:break
            radii.append(vals[0])
        except ValueError:break
    assert len(radii)==len(nodeids)==40,(len(radii),nodeids)
    C=lambda k:v[:,names.index(k)-1]
    rotor=['RtAero'+k+'h' for k in ['Fx','Fy','Fz','Mx','My','Mz']]
    assert all(k in names for k in rotor),rotor
    assert all(units[k]==('(N)' if i<3 else '(N-m)') for i,k in enumerate(rotor))
    np.savez_compressed(OUT/'blade_node_aero.npz',time_s=t,span_m=radii,blade=np.arange(1,4),node=nodeids,**{g:np.stack([np.stack([C(nd[b,j,g]) for j in nodeids],1) for b in range(1,4)],1) for g in groups})
    np.savetxt(OUT/'rotor_aero_wrench.csv',np.column_stack([t]+[C(k) for k in rotor]),delimiter=',',header='time_s,'+','.join(rotor),comments='')
    stats=[]
    for b in range(1,4):
        for j,r in zip(nodeids,radii):
            for g in groups:
                k=nd[b,j,g];x=C(k);stats.append([b,j,r,g,units[k],x.mean(),x.std(ddof=1),x.min(),x.max()])
    with (OUT/'blade_span_statistics.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['blade','node','span_m','quantity','unit','mean','std','min','max']);w.writerows(stats)
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.linewidth':.8,'legend.frameon':False,'savefig.dpi':300})
    fig,ax=plt.subplots(1,3,figsize=(10,3.6),layout='constrained')
    for q,g in zip(ax,['Fx','Fy','Mm']):
        for b in range(1,4):
            xs=np.stack([C(nd[b,j,g]) for j in nodeids],1);q.plot(radii,xs.mean(0),label=f'Blade {b}',lw=1.0)
        q.set_xlabel('Span (m)');q.set_ylabel(f'{g} {units[nd[1,1,g]]}');q.grid(alpha=.2)
    ax[0].legend()
    for ext in ['png','svg','pdf']:fig.savefig(OUT/('01_blade_span_loads.'+ext))
    plt.close(fig)
    fig,ax=plt.subplots(3,2,figsize=(9,6),sharex=True,layout='constrained')
    for q,k in zip(ax.flat,rotor):
        q.plot(t,C(k),lw=.6);q.set_ylabel(k+' '+units[k]);q.grid(alpha=.2)
    for q in ax[-1]:q.set_xlabel('Time (s)')
    for ext in ['png','svg','pdf']:fig.savefig(OUT/('02_rotor_aero_wrench.'+ext))
    plt.close(fig)
    (OUT/'result_receipt.json').write_text(json.dumps({'status':'NATIVE_OUTPUT_PASS','duration_s':a.duration,'classification':'pilot only' if a.duration<100 else 'new native coupled OpenFAST historical reduced structural model, not REV22','samples':nt,'first_time_s':float(t[0]),'last_time_s':float(t[-1]),'blade_nodes':len(nodeids),'blades':3,'node_channels':len(nd),'outb_sha256':sha(raw),'rotor_units':{k:units[k] for k in rotor},'node_units':{g:units[nd[1,1,g]] for g in groups},'force_mapping':'HOLD: legacy local nodal coordinates, no global distributed-load balance or FE transfer'},indent=2))
    print('NATIVE_OUTPUT_PASS',nt,len(nodeids),len(nd),flush=True)
if a.stage=='restore':restore()
elif a.stage=='run':run()
else:post()
