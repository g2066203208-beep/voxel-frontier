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


def section_moment_operator(z, ei):
    """Elastic EI*curvature at both ends of each 2-node Hermite beam.
    Sign convention: left curvature moment = -ke[theta_left],
    right curvature moment = +ke[theta_right]; NOT full dynamic section forces.
    """
    nd=2*len(z);B=np.zeros((2*len(ei),nd-2))
    positions=[];element_ids=[];ends=[]
    for i,rigidity in enumerate(ei):
        L=z[i+1]-z[i]
        if L<=0 or rigidity<=0:raise ValueError('nonpositive element length/EI')
        left=rigidity/L**2*np.array([-6.,-4.*L,6.,-2.*L])
        right=rigidity/L**2*np.array([6.,2.*L,-6.,4.*L])
        for j,(row,location,which) in enumerate(((left,z[i],'lower'),(right,z[i+1],'upper'))):
            for k,val in enumerate(row):
                gdof=2*i+k
                if gdof>=2:B[2*i+j,gdof-2]+=val
            positions.append(float(location));element_ids.append(i+1);ends.append(which)
    return B,positions,element_ids,ends

def envelope_svg(path, moment_rows, displacement_rows):
    """Direct SVG from numeric envelopes; display only, no interpolated physics."""
    from html import escape
    W,H=1080,650
    panels=[
      {'x':100,'title':'Elastic bending |M| envelope (kN m)','rows':moment_rows,
       'key':'peak_abs_elastic_bending_moment_kNm','factor':1.0},
      {'x':600,'title':'Relative lateral |u| envelope (mm)','rows':displacement_rows,
       'key':'peak_abs_relative_u_mm','factor':1.0},
    ]
    colors={'HNE':'#21618c','HNN':'#c05a25'}
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
      '<rect width="100%" height="100%" fill="#fff"/>',
      '<text x="52" y="39" font-family="Arial" font-size="22" font-weight="bold">158 m hybrid tower | measured ESM input, linear-beam screening</text>',
      '<text x="52" y="65" font-family="Arial" font-size="14" fill="#b02020">NOT ABAQUS E/WE · no PT, contact, RNA inertia or site-spectrum qualification</text>']
    for p in panels:
        x0=p['x'];y0=132;pw=380;ph=420
        vmax=max(float(row[p['key']]) for row in p['rows'])*1.10
        out.append(f'<text x="{x0}" y="106" font-family="Arial" font-size="16">{escape(p["title"])}</text>')
        out.append(f'<path d="M{x0} {y0}V{y0+ph}H{x0+pw}" fill="none" stroke="#333" stroke-width="1.5"/>')
        for k in range(5):
            yy=y0+ph*(1-k/4)
            xx=x0+pw*k/4
            out.append(f'<line x1="{x0}" y1="{yy:.2f}" x2="{x0+pw}" y2="{yy:.2f}" stroke="#ddd"/>')
            out.append(f'<text x="{x0-9}" y="{yy+5:.2f}" text-anchor="end" font-size="12" font-family="Arial">{158*k/4:.1f}</text>')
            out.append(f'<text x="{xx:.2f}" y="{y0+ph+20}" text-anchor="middle" font-size="12" font-family="Arial">{vmax*k/4:.1f}</text>')
        out.append(f'<text x="{x0-44}" y="{y0+ph/2}" transform="rotate(-90 {x0-44} {y0+ph/2})" text-anchor="middle" font-size="13" font-family="Arial">Elevation z (m)</text>')
        for direction in ('HNE','HNN'):
            data=[row for row in p['rows'] if row['direction']==direction]
            data.sort(key=lambda row:float(row['elevation_m']))
            points=' '.join(f'{x0+pw*float(row[p["key"]])/vmax:.2f},{y0+ph*(1-float(row["elevation_m"])/158):.2f}' for row in data)
            out.append(f'<polyline points="{points}" fill="none" stroke="{colors[direction]}" stroke-width="2"/>')
        for j,direction in enumerate(('HNE','HNN')):
            lx=x0+55+j*135
            out.append(f'<line x1="{lx}" y1="{y0+ph+49}" x2="{lx+30}" y2="{y0+ph+49}" stroke="{colors[direction]}" stroke-width="3"/>')
            out.append(f'<text x="{lx+37}" y="{y0+ph+54}" font-size="13" font-family="Arial">{direction}</text>')
    out.append('<text x="52" y="633" font-family="Arial" font-size="12" fill="#555">Each curve is a timewise maximum at each location, NOT a simultaneous load profile. Source: ESM IT-2012-0008/NVL/MP; zeta=5% assumed.</text>')
    out.append('</svg>')
    Path(path).write_text('\n'.join(out)+'\n')

def integrate_modal(acc,omega,phi,gamma,K,dt,zeta=0.05,moment_phi=None,node_phi=None,history_stride=20):
    # Newmark average acceleration, initial rest, -Gamma*a_g generalized forcing.
    if type(history_stride) is not int or history_stride<1:
        raise ValueError('history_stride must be a positive integer')
    q=np.zeros(len(omega));v=q.copy();aa=-gamma*acc[0]
    c=2*zeta*omega;k=omega**2;b=.25;g=.5
    den=1+b*dt*dt*k+g*dt*c
    peak={'top_u_m':(0.,0),'top_abs_acc_m_s2':(0.,0),
          'base_elastic_shear_N':(0.,0),'base_elastic_moment_Nm':(0.,0)}
    history=[]
    if moment_phi is not None:
        nm=moment_phi.shape[0];nn=node_phi.shape[0]
        mom_min=np.full(nm,np.inf);mom_max=np.full(nm,-np.inf)
        mom_abs=np.zeros(nm);mom_signed=np.zeros(nm);mom_idx=np.zeros(nm,dtype=int)
        nod_abs=np.zeros(nn);nod_signed=np.zeros(nn);nod_idx=np.zeros(nn,dtype=int)
    for idx,ag in enumerate(acc):
        if idx:
            qp=q+dt*v+dt*dt*(.5-b)*aa;vp=v+dt*(1-g)*aa
            an=(-gamma*ag-c*vp-k*qp)/den
            q=qp+b*dt*dt*an;v=vp+g*dt*an;aa=an
        if moment_phi is not None:
            m=moment_phi@q;nu=node_phi@q
            mom_min=np.minimum(mom_min,m);mom_max=np.maximum(mom_max,m)
            update_m=np.abs(m)>mom_abs
            mom_abs[update_m]=np.abs(m[update_m])
            mom_signed[update_m]=m[update_m];mom_idx[update_m]=idx
            update_n=np.abs(nu)>nod_abs
            nod_abs[update_n]=np.abs(nu[update_n])
            nod_signed[update_n]=nu[update_n];nod_idx[update_n]=idx
        u=phi@q;u_abs_acc=phi@aa
        top_u=u[-2];top_abs_acc=u_abs_acc[-2]+ag
        shear=K[0,2:]@u;moment=K[1,2:]@u
        for key,val in [('top_u_m',top_u),('top_abs_acc_m_s2',top_abs_acc),
                        ('base_elastic_shear_N',shear),('base_elastic_moment_Nm',moment)]:
            if abs(val)>peak[key][0]:peak[key]=(float(abs(val)),idx)
        if idx%history_stride==0:history.append((idx*dt,top_u,top_abs_acc,shear,moment))
    envelope=None
    if moment_phi is not None:
        envelope={'mom_min':mom_min,'mom_max':mom_max,'mom_abs':mom_abs,
                  'mom_signed':mom_signed,'mom_idx':mom_idx,
                  'nod_abs':nod_abs,'nod_signed':nod_signed,'nod_idx':nod_idx}
    return peak,history,envelope

def self_test():
    z=np.linspace(0,100,36);mu=np.ones(35)*1200;ei=np.ones(35)*1e10
    z,K,M=build(z,mu,ei,rna_mass=0)
    om,f,phi,g,em,orth,res=modes(z,K,M)
    exact=(1.875104068711961**2)/(2*np.pi*100**2)*np.sqrt(1e10/1200)
    assert abs(f[0]/exact-1)<2e-5,(f[0],exact)
    assert orth<1e-8 and res<1e-7,(orth,res)
    p,h,_=integrate_modal(np.zeros(101),om[:4],phi[:,:4],g[:4],K,0.01)
    assert all(v[0]==0 for v in p.values())
    p,_,_=integrate_modal(np.sin(np.arange(1001)*0.01),om[:4],phi[:,:4],g[:4],K,0.01)
    assert p['top_u_m'][0]>0
    # Full-rate history retains all internally tracked maxima, and exact
    # 20x decimation reproduces the original 0.1s archive on a 0.005s grid.
    synthetic=np.sin(np.arange(1001)*0.005*5)
    pf,hf,_=integrate_modal(synthetic,om[:4],phi[:,:4],g[:4],K,0.005,history_stride=1)
    pc,hc,_=integrate_modal(synthetic,om[:4],phi[:,:4],g[:4],K,0.005,history_stride=20)
    assert len(hf)==1001 and len(hc)==51
    assert all(np.array_equal(hf[20*i],row) for i,row in enumerate(hc))
    for key,col in (('top_u_m',1),('top_abs_acc_m_s2',2),
                    ('base_elastic_shear_N',3),('base_elastic_moment_Nm',4)):
        full_peak=max(abs(row[col]) for row in hf)
        assert np.isclose(full_peak,pf[key][0],rtol=1e-12,atol=1e-9),(key,full_peak,pf[key])
        assert np.isclose(pf[key][0],pc[key][0],rtol=1e-12,atol=1e-9)
        assert full_peak+1e-9>=max(abs(row[col]) for row in hc)
    for bad in (0,-1,1.5,True):
        try:integrate_modal(synthetic[:3],om[:4],phi[:,:4],g[:4],K,0.005,history_stride=bad)
        except ValueError:pass
        else:raise AssertionError('accepted invalid history stride')
    print('PASS full-rate 0.005s 4-QoI peak identity and exact 20x legacy decimation, 4 invalid strides rejected')
    B,_,_,_=section_moment_operator(z,ei)
    u=np.linspace(-0.002,0.003,K.shape[0]);u[:2]=0.
    for i in (0,3,34):
        L=z[i+1]-z[i];k=ei[i]/L**3*np.array(
            [[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],
             [-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])
        endforces=k@u[2*i:2*i+4]
        m0=B[2*i]@u[2:];m1=B[2*i+1]@u[2:]
        assert np.isclose(m0,-endforces[1],rtol=1e-10,atol=1e-6)
        assert np.isclose(m1,endforces[3],rtol=1e-10,atol=1e-6)
    print('PASS 35-element EI-curvature endpoint operators vs element end-force moments')
    print('PASS uniform cantilever analytic frequency, orthogonality, modal residual, zero/nonzero forcing',f[0],exact)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tower');ap.add_argument('--esm')
    ap.add_argument('--outdir');ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--full-rate-history',action='store_true',help='save E-only 0.005s proxy history, not S09 W/E/WE')
    args=ap.parse_args()
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
    B,section_z,section_element,section_end=section_moment_operator(z,ei)
    moment_phi=B@phi
    node_phi=np.vstack((np.zeros((1,len(om))),phi[::2]))
    t,acc=read_esm(args.esm);dt=float(t[1]-t[0]);summary=[];histories={};envelopes={};full_histories={}

    for name,series in acc.items():
        peaks,history,envelope=integrate_modal(series,om,phi,g,K,dt,moment_phi=moment_phi,node_phi=node_phi,history_stride=1 if args.full_rate_history else 20)
        summary.append({'direction':name,'peak_top_relative_displacement_m':peaks['top_u_m'][0],
                        'time_peak_top_displacement_s':peaks['top_u_m'][1]*dt,
                        'peak_top_absolute_acceleration_m_s2':peaks['top_abs_acc_m_s2'][0],
                        'peak_base_elastic_shear_kN':peaks['base_elastic_shear_N'][0]/1000,
                        'peak_base_elastic_moment_kNm':peaks['base_elastic_moment_Nm'][0]/1000})
        if args.full_rate_history:
            full_histories[name]=history
            history=history[::20]
        histories[name]=history;envelopes[name]=envelope
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
    full_rate_meta=None
    if args.full_rate_history:
        full_name='S08_158M_BEAM_PROXY_HISTORY_0P005S_20261106.csv'
        with (out/full_name).open('w',newline='') as h:
            w=csv.writer(h);w.writerow(['direction','time_s','top_relative_u_m',
                'top_absolute_acc_m_s2','base_elastic_shear_N','base_elastic_moment_Nm'])
            for key in ('HNE','HNN'):
                for row in full_histories[key]:w.writerow([key,*row])
        comparisons=[]
        for direction in ('HNE','HNN'):
            rows=full_histories[direction]
            if len(rows)!=len(t) or len(histories[direction])!=len(t[::20]):
                raise ValueError('FULL_RATE_ROW_COUNT_MISMATCH')
            if not np.allclose([r[0] for r in rows],t,rtol=0,atol=1e-8):
                raise ValueError('FULL_RATE_ESM_TIME_GRID_MISMATCH')
            if not all(rows[i*20]==r for i,r in enumerate(histories[direction])):
                raise ValueError('LEGACY_20X_DECIMATION_MISMATCH')
            original=next(x for x in summary if x['direction']==direction)
            for key,col,scale in (
                ('peak_top_relative_displacement_m',1,1.),
                ('peak_top_absolute_acceleration_m_s2',2,1.),
                ('peak_base_elastic_shear_kN',3,1000.),
                ('peak_base_elastic_moment_kNm',4,1000.)):
                measured=max(abs(row[col]) for row in rows)/scale
                expected=original[key]
                if not np.isclose(measured,expected,rtol=1e-11,atol=1e-10):
                    raise ValueError('FULL_RATE_PEAK_MISMATCH_'+direction+'_'+key)
                comparisons.append({'direction':direction,'qoi':key,
                    'full_rate_peak_abs':float(measured),
                    'original_integrator_peak_abs':float(expected),
                    'absolute_residual':float(abs(measured-expected))})
        full_rate_meta={
            'file':full_name,'file_sha256':sha(out/full_name),
            'legacy_file':'S08_158M_BEAM_PROXY_HISTORY_20261102.csv',
            'legacy_file_sha256':sha(out/'S08_158M_BEAM_PROXY_HISTORY_20261102.csv'),
            'n_rows':sum(len(v) for v in full_histories.values()),
            'rows_per_direction':len(t),'dt_s':dt,'n_directions':len(full_histories),
            'exact_20x_decimation_reproduces_legacy':True,
            'eight_peak_integrator_checks':comparisons,
            'admissible_for_S09_four_scenario_comparison':False,
            'initial_state_sha256':None,'W_WE_histories_present':False}
    moment_rows=[];displacement_rows=[]
    for direction,envelope in envelopes.items():
        for i in range(len(section_z)):
            moment_rows.append({
                'direction':direction,'element':section_element[i],
                'end':section_end[i],'elevation_m':section_z[i],
                'peak_abs_elastic_bending_moment_kNm':float(envelope['mom_abs'][i])/1000,
                'signed_moment_at_peak_kNm':float(envelope['mom_signed'][i])/1000,
                'time_peak_s':float(envelope['mom_idx'][i])*dt,
                'max_positive_kNm':max(0.,float(envelope['mom_max'][i])/1000),
                'min_negative_kNm':min(0.,float(envelope['mom_min'][i])/1000)})
        for i,elevation in enumerate(z):
            displacement_rows.append({
                'direction':direction,'node':i,'elevation_m':float(elevation),
                'peak_abs_relative_u_mm':float(envelope['nod_abs'][i])*1000,
                'signed_u_at_peak_mm':float(envelope['nod_signed'][i])*1000,
                'time_peak_s':float(envelope['nod_idx'][i])*dt})
    assert len(moment_rows)==140 and len(displacement_rows)==72
    moment_file='S08_158M_BEAM_PROXY_35SEG_MOMENT_ENVELOPE_20261102.csv'
    displacement_file='S08_158M_BEAM_PROXY_36NODE_DISPLACEMENT_ENVELOPE_20261102.csv'
    figure_file='FIG_S08_07_158M_BEAM_PROXY_ALONG_HEIGHT_ENVELOPES_NOT_ABAQUS.svg'
    for filename,rows in ((moment_file,moment_rows),(displacement_file,displacement_rows)):
        with (out/filename).open('w',newline='') as h:
            w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    envelope_svg(out/figure_file,moment_rows,displacement_rows)
    # The last node is exactly the original tower-top displacement DOF.
    for direction in acc:
        row=next(row for row in displacement_rows if row['direction']==direction and row['node']==35)
        original=next(row for row in summary if row['direction']==direction)
        assert np.isclose(row['peak_abs_relative_u_mm']/1000,
                          original['peak_top_relative_displacement_m'],rtol=1e-12,atol=1e-12)
    assert all(np.isfinite(float(row['peak_abs_elastic_bending_moment_kNm'])) for row in moment_rows)
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
      'FIG':figure_file+' (linear-beam screening only, not Abaqus)',
      'TAB':['S08_158M_BEAM_PROXY_MODAL_20261102.csv','S08_158M_BEAM_PROXY_PEAKS_20261102.csv',
             'S08_158M_BEAM_PROXY_HISTORY_20261102.csv',moment_file,displacement_file],
      'assumptions':['perfectly continuous linear Euler-Bernoulli beam, fixed base',
          'no prestress/contact/cracking/soil/foundation','RNA mass at 158m; CG offset, inertia, blades ignored',
          'horizontal HNE/HNN only; HNZ vertical not represented','5% equal modal damping assumed',
          'base shear/moment are elastic restoring components, not total dynamic support reactions',
          '35 segments from 70 OpenFAST paired stations, tiny interstation gaps closed'],
      'error_budget':'Uniform cantilever frequency <2e-5; modal residual <1e-7; orthogonality <1e-8; first 6 coarse/refined frequencies <2%; physical model error UNQUANTIFIED',
      'along_height_envelopes':{'beam_elements':35,'section_ends_per_element':2,'moment_rows':140,'node_rows':72,'each_location_timewise_peak_not_simultaneous':True,'elastic_moment_only_not_total_support_reaction':True},
      'failure_records':[],'stage':'S08 independent structural proxy only; BLOCKED for Abaqus native E',
      'HOLD':'no native Abaqus E, no PT/contact initial state, no RNA inertia, no site-matched design spectrum',
      'peak_summary':summary}
    if full_rate_meta is not None:
        receipt['full_rate_history']=full_rate_meta
        sidecar={
            'classification':'REAL_ESM_E_ONLY_NONPRODUCTION_BEAM_PROXY_0P005S_NOT_S09_PAIRED',
            'SOURCE':receipt['SOURCE'],'REF':receipt['REF'],
            'STANDARD':receipt['STANDARD'],'OFFICIAL':receipt['OFFICIAL'],
            'RUN':'Full-rate Newmark beam-proxy history; no native structural solver',
            'FIG':0,'TAB':full_rate_meta['file'],
            'source_reading_level':receipt['source_reading_level'],
            'source_tower_sha256':receipt['source_tower_sha256'],
            'source_esm_sha256':receipt['source_esm_sha256'],
            'code_sha256':receipt['code_sha256'],
            'software':receipt['software'],
            'assumptions':receipt['assumptions'],
            'error_budget':receipt['error_budget']+
                '; full-rate 8-QoI peaks vs integrator rtol=1e-11, atol=1e-10; physical model error unquantified',
            'failure_records':[],
            'full_rate_history':full_rate_meta,
            'HOLD':'E-only linear beam proxy; no matching B/W/WE, no verified initial-state SHA, no native physics PASS',
            'S08_PASS':False,'S09_PASS':False,'native_E_WE_RUN':0}
        (out/'S08_158M_BEAM_PROXY_FULL_RATE_RECEIPT_20261106.json').write_text(
            json.dumps(sidecar,ensure_ascii=False,indent=2)+'\n')
    (out/'S08_158M_BEAM_PROXY_RECEIPT_20261102.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'f1_Hz':f[0],'f2_Hz':f[1],'mass_kg':mass_est,
      'mesherr6':mesherr.max(),'modal_mass12':sum(eff),'peaks':summary},indent=2))
if __name__=='__main__':main()
