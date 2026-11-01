#!/usr/bin/env python3
"""NONPRODUCTION 158 m fixed-base Euler-Bernoulli seismic screening, NOT Abaqus E/WE.
Real 70-station OpenFAST tower properties + archived processed ESM 3-component wave.
Only horizontal HNE/HNN; excludes PT, joints, RNA inertia/offset, soil and vertical response.
"""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh

RNA_MASS_KG = 676753.290723  # T057 RNA-R2 translational mass, NOT inertia
ESM_SHA256 = 'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def parse_tower(path):
    rows=[]; in_table=False
    for line in Path(path).read_text().splitlines():
        if line.strip().startswith('HtFract'):
            in_table=True; continue
        if not in_table: continue
        parts=line.split()
        if len(parts)==10:
            try: vals=[float(v) for v in parts]
            except ValueError: continue
            if 0<=vals[0]<=1: rows.append(vals)
        elif len(rows)>=70: break
    a=np.asarray(rows)
    if a.shape!=(70,10) or not np.isclose(a[0,0],0) or not np.isclose(a[-1,0],1):
        raise ValueError('expected exactly 70 OpenFAST stations spanning 0..1')
    if np.any(np.diff(a[:,0])<=0): raise ValueError('station fractions not strictly increasing')
    if np.any(a[:,1:4]<=0): raise ValueError('nonpositive mass/EI')
    if np.max(np.abs(a[::2,1:4]-a[1::2,1:4]))>1e-4:
        raise ValueError('expected 35 paired constant-property segments')
    # OpenFAST stations have small gaps between segments; close at mid-gap.
    z=np.r_[0.,158.*0.5*(a[1:-1:2,0]+a[2::2,0]),158.]
    if len(z)!=36 or np.any(np.diff(z)<=0): raise ValueError('invalid 35-element mesh')
    return z,a[::2,1],a[::2,2],a

def build(z,mu,ei,refine=1,rna_mass=RNA_MASS_KG):
    if refine not in (1,2): raise ValueError('refine must be 1 or 2')
    z2=[]; mu2=[]; ei2=[]
    z2.append(z[0])
    for i in range(len(mu)):
        for k in range(refine):
            z2.append(z[i]+(z[i+1]-z[i])*(k+1)/refine)
            mu2.append(mu[i]);ei2.append(ei[i])
    z=np.array(z2);nd=2*len(z)
    K=np.zeros((nd,nd));M=np.zeros((nd,nd))
    for i,(density,rigidity) in enumerate(zip(mu2,ei2)):
        L=z[i+1]-z[i];a=rigidity/L**3;b=density*L/420
        ke=a*np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],
                       [-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])
        me=b*np.array([[156,22*L,54,-13*L],[22*L,4*L*L,13*L,-3*L*L],
                       [54,13*L,156,-22*L],[-13*L,-3*L*L,-22*L,4*L*L]])
        sl=slice(2*i,2*i+4);K[sl,sl]+=ke;M[sl,sl]+=me
    M[-2,-2]+=rna_mass
    return z,K,M

def modes(z,K,M,nmodes=12):
    Kr=K[2:,2:];Mr=M[2:,2:]
    eig,phi=eigh(Kr,Mr,subset_by_index=(0,nmodes-1),check_finite=True)
    if np.any(eig<=0):raise ValueError('nonpositive eigenvalue')
    omega=np.sqrt(eig);freq=omega/(2*np.pi)
    influence=np.zeros(Kr.shape[0]);influence[::2]=1.
    gamma=phi.T@Mr@influence
    effmass=gamma**2/(influence@Mr@influence)
    orth=np.max(np.abs(phi.T@Mr@phi-np.eye(nmodes)))
    res=np.max([np.linalg.norm(Kr@phi[:,j]-eig[j]*Mr@phi[:,j])/
                (np.linalg.norm(Kr@phi[:,j])+1e-30) for j in range(nmodes)])
    return omega,freq,phi,gamma,effmass,orth,res

def read_esm(path):
    if sha(path)!=ESM_SHA256:raise ValueError('processed ESM source SHA256 mismatch')
    with Path(path).open(newline='') as f:
        reader=csv.DictReader(f);rows=list(reader);fields=reader.fieldnames
    if len(rows)!=32040:raise ValueError('unexpected ESM npts')
    comps=[c for c in fields if 'HNE' in c or 'HNN' in c]
    if len(comps)!=2:raise ValueError('missing HNE/HNN columns: '+str(fields))
    time_col=next((c for c in fields if c.lower() in ('time_s','time','t_s')),None)
    if not time_col:raise ValueError('no time column: '+str(fields))
    t=np.array([float(row[time_col]) for row in rows]);dt=np.diff(t)
    if not np.allclose(dt,0.005,rtol=0,atol=1e-8):raise ValueError('time grid mismatch')
    a={c[:3]:np.array([float(row[c]) for row in rows]) for c in comps}
    if any(not np.all(np.isfinite(x)) for x in a.values()):raise ValueError('nonfinite ground acceleration')
    return t,a

def integrate_modal(acc,omega,phi,gamma,K,dt,zeta=0.05):
    # Newmark average acceleration, initial rest, -Gamma*a_g generalized forcing.
    q=np.zeros(len(omega));v=q.copy();aa=-gamma*acc[0]
    c=2*zeta*omega;k=omega**2;b=.25;g=.5
    den=1+b*dt*dt*k+g*dt*c
    peak={'top_u_m':(0.,0),'top_abs_acc_m_s2':(0.,0),
          'base_elastic_shear_N':(0.,0),'base_elastic_moment_Nm':(0.,0)}
    history=[]
    for idx,ag in enumerate(acc):
        if idx:
            qp=q+dt*v+dt*dt*(.5-b)*aa;vp=v+dt*(1-g)*aa
            an=(-gamma*ag-c*vp-k*qp)/den
            q=qp+b*dt*dt*an;v=vp+g*dt*an;aa=an
        u=phi@q;u_abs_acc=phi@aa
        top_u=u[-2];top_abs_acc=u_abs_acc[-2]+ag
        shear=K[0,2:]@u;moment=K[1,2:]@u
        for key,val in [('top_u_m',top_u),('top_abs_acc_m_s2',top_abs_acc),
                        ('base_elastic_shear_N',shear),('base_elastic_moment_Nm',moment)]:
            if abs(val)>peak[key][0]:peak[key]=(float(abs(val)),idx)
        if idx%20==0:history.append((idx*dt,top_u,top_abs_acc,shear,moment))
    return peak,history

def self_test():
    z=np.linspace(0,100,36);mu=np.ones(35)*1200;ei=np.ones(35)*1e10
    z,K,M=build(z,mu,ei,rna_mass=0)
    om,f,phi,g,em,orth,res=modes(z,K,M)
    exact=(1.875104068711961**2)/(2*np.pi*100**2)*np.sqrt(1e10/1200)
    assert abs(f[0]/exact-1)<2e-5,(f[0],exact)
    assert orth<1e-8 and res<1e-7,(orth,res)
    p,h=integrate_modal(np.zeros(101),om[:4],phi[:,:4],g[:4],K,0.01)
    assert all(v[0]==0 for v in p.values())
    p,_=integrate_modal(np.sin(np.arange(1001)*0.01),om[:4],phi[:,:4],g[:4],K,0.01)
    assert p['top_u_m'][0]>0
    print('PASS uniform cantilever analytic frequency, orthogonality, modal residual, zero/nonzero forcing',f[0],exact)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tower');ap.add_argument('--esm')
    ap.add_argument('--outdir');ap.add_argument('--self-test',action='store_true');args=ap.parse_args()
    if args.self_test:self_test();return
    if not args.tower or not args.esm or not args.outdir:ap.error('--tower --esm --outdir required')
    out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
    z,mu,ei,stations=parse_tower(args.tower)
    z1,K,M=build(z,mu,ei);om,f,phi,g,eff,orth,res=modes(z1,K,M)
    z2,K2,M2=build(z,mu,ei,refine=2);om2,f2,_,_,_,_,_=modes(z2,K2,M2)
    mesherr=np.abs(f2[:6]-f[:6])/f2[:6]
    if mesherr.max()>0.02:raise ValueError('mesh convergence 2% screen failed')
    if orth>1e-8 or res>1e-7:raise ValueError('modal numerical QC failed')
    mass_est=float(np.sum(mu*np.diff(z)));rna=float(RNA_MASS_KG)
    t,acc=read_esm(args.esm);dt=float(t[1]-t[0]);summary=[];histories={}
    for name,series in acc.items():
        peaks,history=integrate_modal(series,om,phi,g,K,dt)
        summary.append({'direction':name,'peak_top_relative_displacement_m':peaks['top_u_m'][0],
                        'time_peak_top_displacement_s':peaks['top_u_m'][1]*dt,
                        'peak_top_absolute_acceleration_m_s2':peaks['top_abs_acc_m_s2'][0],
                        'peak_base_elastic_shear_kN':peaks['base_elastic_shear_N'][0]/1000,
                        'peak_base_elastic_moment_kNm':peaks['base_elastic_moment_Nm'][0]/1000})
        histories[name]=history
    with (out/'S08_158M_BEAM_PROXY_MODAL_20261102.csv').open('w',newline='') as h:
        w=csv.writer(h);w.writerow(['mode','frequency_Hz','period_s','effective_mass_fraction',
          'cumulative_mass_fraction','refined_frequency_Hz','relative_mesh_difference'])
        for i in range(12):w.writerow([i+1,f[i],1/f[i],eff[i],sum(eff[:i+1]),f2[i],abs(f2[i]-f[i])/f2[i]])
    with (out/'S08_158M_BEAM_PROXY_PEAKS_20261102.csv').open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=summary[0].keys());w.writeheader();w.writerows(summary)
    with (out/'S08_158M_BEAM_PROXY_HISTORY_20261102.csv').open('w',newline='') as h:
        w=csv.writer(h);w.writerow(['direction','time_s','top_relative_u_m','top_absolute_acc_m_s2',
          'base_elastic_shear_N','base_elastic_moment_Nm'])
        for key,history in histories.items():
            for row in history:w.writerow([key,*row])
    receipt={'classification':'NONPRODUCTION_CONDITIONAL_LINEAR_158M_BEAM_PROXY_NOT_ABAQUS_E',
      'source_reading_level':'GitHub OpenFAST 70-station tower file + archived processed ESM acceleration',
      'source_tower_sha256':sha(args.tower),'source_esm_sha256':sha(args.esm),
      'code_sha256':sha(__file__),'software':'Python NumPy SciPy Euler-Bernoulli consistent mass Newmark',
      'tower_height_m':158,'elements_coarse':35,'elements_refined':70,
      'rna_tip_translational_mass_kg':rna,'tower_mass_estimate_kg':mass_est,
      'n_modes':len(f),'damping_ratio_assumed':0.05,
      'max_first_six_mesh_frequency_relative_difference':float(mesherr.max()),
      'modal_mass_orthogonality_max':float(orth),'modal_residual_relative_max':float(res),
      'first_six_frequency_Hz':list(map(float,f[:6])),
      'first_twelve_effective_mass_fraction_sum':float(sum(eff)),
      'ground_motion_npts':len(t),'ground_motion_dt_s':dt,
      'SOURCE':'T077/recovery/S06_C02R3R2_158M_Tower_RECOVERED_20261026.dat and historical ESM artifact 12884814391',
      'REF':'Existing T079 seismic method notes; no new paper full-text read',
      'STANDARD':'No authorized GB/IEC clauses read; NOT STANDARD PASS',
      'OFFICIAL':'Recovered OpenFAST tower file is a project source, not official DTU tower design',
      'RUN':'Python reduced-order beam model only; native Abaqus E/WE=0',
      'FIG':'None; numerical tables only',
      'TAB':['S08_158M_BEAM_PROXY_MODAL_20261102.csv','S08_158M_BEAM_PROXY_PEAKS_20261102.csv',
             'S08_158M_BEAM_PROXY_HISTORY_20261102.csv'],
      'assumptions':['perfectly continuous linear Euler-Bernoulli beam, fixed base',
          'no prestress/contact/cracking/soil/foundation','RNA mass at 158m; CG offset, inertia, blades ignored',
          'horizontal HNE/HNN only; HNZ vertical not represented','5% equal modal damping assumed',
          'base shear/moment are elastic restoring components, not total dynamic support reactions',
          '35 segments from 70 OpenFAST paired stations, tiny interstation gaps closed'],
      'error_budget':'Uniform cantilever frequency <2e-5; modal residual <1e-7; orthogonality <1e-8; first 6 coarse/refined frequencies <2%; physical model error UNQUANTIFIED',
      'failure_records':[],'stage':'S08 independent structural proxy only; BLOCKED for Abaqus native E',
      'HOLD':'no native Abaqus E, no PT/contact initial state, no RNA inertia, no site-matched design spectrum',
      'peak_summary':summary}
    (out/'S08_158M_BEAM_PROXY_RECEIPT_20261102.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'f1_Hz':f[0],'f2_Hz':f[1],'mass_kg':mass_est,
      'mesherr6':mesherr.max(),'modal_mass12':sum(eff),'peaks':summary},indent=2))
if __name__=='__main__':main()
