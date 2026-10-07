import csv,gzip,glob,os,math,itertools,json
ROOT=os.path.dirname(__file__)
geom={}
with open(os.path.join(ROOT,'T071_input_geometry_31_segments.csv'),encoding='utf-8-sig',newline='') as f:
    for r in csv.DictReader(f): geom[r['segment']]=r
rows={}
for b in 'ABCD':
    p=glob.glob(os.path.join(ROOT,'extracted',b,'*_31seg.csv.gz'))[0]
    with gzip.open(p,'rt',newline='') as f:
        for r in csv.DictReader(f): rows.setdefault(r['segment'],[]).append(r)

controls={}
for seg, rs in rows.items():
    selected={}
    for r in rs:
        for key in ('V_kN','T_abs_kNm','M_kNm','N_comp_kN'):
            if key not in selected or float(r[key]) > float(selected[key][key]):
                selected[key]=r
    controls[seg]=list({r['time_s']: r for r in selected.values()}.values())

def calc(seg,r,d,s):
    g=geom[seg]; D=float(g['D_m'])*1000; di=float(g['di_m'])*1000; t=float(g['wall_mm']); A=float(g['A_m2'])*1e6
    c=30.; h0=max(t-c-d/2-25/2,1.); b=t
    ft=2.14 if seg in ('CSEG_01','CSEG_02') else 2.09; fc=31.8 if seg in ('CSEG_01','CSEG_02') else 29.7
    V=float(r['V_kN'])*1000; M=abs(float(r['M_kNm']))*1e6; T=float(r['T_abs_kNm'])*1e6; N=float(r['N_comp_kN'])*1000
    lam=M/(V*h0) if V else 1e9; abar=math.pi*d*d/4; Asv=4*abar; Ast1=2*abar
    A_sl=2*float(g['bars_each_row'])*float(g['Abar_mm2'])
    ro=D/2-(c+d/2); ri=di/2+(c+d/2); Acor=math.pi*(ro*ro-ri*ri); ucor=2*math.pi*(ro+ri)
    Wt=2*math.pi/3*((D/2)**3-(di/2)**3)
    beta=max(.5,min(1.,1.5/(1+.2*(lam+1)*V*Wt/(T*b*h0)))) if T else 1.
    vc=1.75/(lam+1)*ft*b*h0; vn=.07*min(N,.3*fc*A); vs=360*Asv/s*h0
    vrd631=vc+vn+vs
    vrd632=(1.5-beta)*vc+vs
    xi=360*A_sl*s/(360*Ast1*ucor)
    trd=beta*.35*ft*Wt+1.2*math.sqrt(max(xi,1e-12))*360*Ast1*Acor/s
    return {'vr631':V/vrd631,'vr632':V/vrd632,'tr':T/trd,'xi':xi,'beta':beta,'V':V/1000,'T':T/1e6,'N':N/1000,'A_sl':A_sl,'Acor':Acor,'ucor':ucor,'Wt':Wt}

dias=[12,14,16,18,20,22,25,28,32,36,40,45,50]
sp=[20,25,30,35,40,50,60,70,80,100,120,150,160,180,200]
cands=[]
for d,s in itertools.product(dias,sp):
    mv=mt=mu=0; ctl=None
    for seg,rs in controls.items():
        for r in rs:
            x=calc(seg,r,d,s); u=max(x['vr631'],x['vr632'],x['tr'])
            if u>mu: mu=u;ctl=(seg,r['time_s'],x)
            mv=max(mv,x['vr632']); mt=max(mt,x['tr'])
    area=4*(math.pi*d*d/4)/s
    cands.append((mu,area,d,s,mv,mt,ctl))
passed=[x for x in cands if x[0]<=1]
chosen=min(passed,key=lambda x:(x[1],x[2],x[3])) if passed else min(cands,key=lambda x:x[0])
print('chosen',chosen[:6],chosen[6][0:2])
_,area,d,s,mv,mt,ctl=chosen
out=[]
for seg,rs in sorted(rows.items()):
    mu=0; cc=None
    for r in controls[seg]:
        x=calc(seg,r,d,s); u=max(x['vr631'],x['vr632'],x['tr'])
        if u>mu: mu=u;cc=(r['time_s'],x)
    g=geom[seg]
    out.append({'segment':seg,'z_m':g['z_center_m'],'wall_mm':g['wall_mm'],'long_bars_each_row':g['bars_each_row'],'long_bars_total':2*int(float(g['bars_each_row'])),'long_As_mm2':2*float(g['bars_each_row'])*float(g['Abar_mm2']),'hoop':'HRB400 phi%d@%d inner+outer'%(d,s),'hoop_d_mm':d,'hoop_spacing_mm':s,'tie':'phi6@480 vertical x <=500 circumferential','control_time_s':cc[0],'V_over_Vrd631':calc(seg, next(r for r in rs if r['time_s']==cc[0]),d,s)['vr631'],'V_over_Vrd632':calc(seg, next(r for r in rs if r['time_s']==cc[0]),d,s)['vr632'],'T_over_Trd':calc(seg, next(r for r in rs if r['time_s']==cc[0]),d,s)['tr'],'max_utilization':mu,'status':'S06 candidate; verify with remaining cases'})
with open(os.path.join(ROOT,'T072_31SEG_REBAR_DESIGN_S06_CORRECTED.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
meta={'selected_diameter_mm':d,'selected_spacing_mm':s,'layers':2,'max_utilization':chosen[0],'max_shear_ratio':mv,'max_torsion_ratio':mt,'xi_definition':'fy*A_sl*s/(fyv*A_st1*u_cor), NB/T 10907 Eq. 6.3.2-4','basis':'S06 exact same-time histories; b=t; c_nom=30mm; Np0=0','status':'S06 candidate, not 36-case final'}
json.dump(meta,open(os.path.join(ROOT,'T072_S06_CORRECTED_REBAR_META.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
