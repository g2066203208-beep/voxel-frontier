#!/usr/bin/env python3
"""Real ESM three-axis SDOF response-history and mechanical-energy benchmark.

SOURCE: ESM v3 processed IT-2012-0008/NVL/MP, exact SHA-locked SI CSV.
This is a single-degree-of-freedom *method verification*, not the 158 m tower,
not a site-compatible design wave, and not an Abaqus/native seismic result.

m=1 kg; u''+2*zeta*omega*u'+omega^2*u=-a_g; u(0)=v(0)=0.
On each sample interval a_g is linearly interpolated. Closed-form state
transition is used; external-work and damping-dissipation integrals are
computed by Simpson quadrature with exact midpoint states.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import platform
from pathlib import Path

SOURCE_SHA = 'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
ORACLE_SHA = '31f94af34005e7ed763b494a3e440f6a4c6f2b6e5a0e9a4129c08ab2ed44b5f7'
ARTIFACT_SHA = '40dcb0d8ad6aa3ce1be4cd96e633d1aa266f3764c85be556e1a029c682c908d6'
DT = .005
N = 32040
PERIODS = (1., 4.)
ZETA = .05
COMP = ('HNE_acc_m_s2', 'HNN_acc_m_s2', 'HNZ_acc_m_s2')
FIELDS = ('time_s',) + COMP
OUTFIELDS = ('component','period_s','npts','dt_s','damping_ratio','peak_rel_u_m',
             'time_peak_u_s','peak_abs_acc_m_s2','peak_rel_v_m_s','final_energy_J_per_kg',
             'ground_work_J_per_kg','viscous_dissipation_J_per_kg',
             'max_energy_residual_J_per_kg','energy_residual_over_max_work_plus_diss',
             'oracle_peak_u_relative_error','newmark_peak_u_relative_error',
             'source_sha256','status')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_wave(raw, strict=True):
    if strict and sha(raw) != SOURCE_SHA:
        raise ValueError('SOURCE_SHA256_MISMATCH')
    rd = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if tuple(rd.fieldnames or ()) != FIELDS:
        raise ValueError('SOURCE_COLUMNS')
    axes = [[],[],[]]
    for i,row in enumerate(rd):
        if None in row or any(x is None for x in row.values()):
            raise ValueError('SOURCE_ROW_WIDTH')
        try: vals = [float(row[k]) for k in FIELDS]
        except ValueError: raise ValueError('SOURCE_NONNUMERIC') from None
        if not all(map(math.isfinite, vals)):
            raise ValueError('SOURCE_NONFINITE')
        if abs(vals[0]-i*DT) > 2e-10:
            raise ValueError('SOURCE_TIME_GRID')
        for j in range(3): axes[j].append(vals[j+1])
    if len(axes[0])<3 or (strict and len(axes[0])!=N):
        raise ValueError('SOURCE_NPTS')
    return axes


def transition(u,v,a0,a1,h,k,c,wd):
    """Exact endpoint/midpoint state under linear a_g between a0 and a1."""
    slope=(a1-a0)/h
    B=-slope/k
    A=(-a0-c*B)/k
    hu=u-A; hv=v-B
    def at(t):
        e=math.exp(-c*t/2)
        z=c/(2*wd)
        cs=math.cos(wd*t); sn=math.sin(wd*t)
        m11=e*(cs+z*sn);m12=e*sn/wd
        m21=e*(-k*sn/wd);m22=e*(cs-z*sn)
        return m11*hu+m12*hv+A+B*t, m21*hu+m22*hv+B
    return at(h/2),at(h)


def exact_history(acc,T,dt=DT,zeta=ZETA):
    if (len(acc)<3 or dt<=0 or T<=0 or not 0<=zeta<1
        or not all(math.isfinite(v) for v in acc)):
        raise ValueError('SDOF_INPUT_INVALID')
    w=2*math.pi/T;k=w*w;c=2*zeta*w;wd=w*math.sqrt(1-zeta*zeta)
    u=v=0.;D=W=0.;max_res=0.;max_denom=0.;peak_u=peak_v=peak_aa=0.;peak_t=0.
    history=[(0.,0.,0.,0.,0.,0.,0.)]
    for i,(a0,a1) in enumerate(zip(acc,acc[1:]),1):
        u0,v0=u,v
        (um,vm),(u,v)=transition(u,v,a0,a1,dt,k,c,wd)
        a_mid=(a0+a1)/2
        D+=c*dt/6*(v0*v0+4*vm*vm+v*v)
        W-=dt/6*(a0*v0+4*a_mid*vm+a1*v)
        E=.5*(v*v+k*u*u)
        res=E+D-W
        max_res=max(max_res,abs(res))
        max_denom=max(max_denom,abs(W)+D+E)
        if abs(u)>peak_u:peak_u=abs(u);peak_t=i*dt
        peak_v=max(peak_v,abs(v))
        aa=-c*v-k*u
        peak_aa=max(peak_aa,abs(aa))
        history.append((i*dt,u,v,aa,E,D,W))
    return dict(history=history,peak_u=peak_u,peak_t=peak_t,peak_v=peak_v,
                peak_abs_acc=peak_aa,energy=E,work=W,dissipation=D,
                max_residual=max_res,normalized_residual=max_res/max(max_denom,1e-30))


def newmark_peak(acc,T,dt=DT,zeta=ZETA):
    w=2*math.pi/T;k=w*w;c=2*zeta*w
    u=v=0.;q=-acc[0];den=1+.5*dt*c+.25*dt*dt*k
    peak=0.
    for a in acc[1:]:
        up=u+dt*v+.25*dt*dt*q
        vp=v+.5*dt*q
        nq=(-a-c*vp-k*up)/den
        u=up+.25*dt*dt*nq;v=vp+.5*dt*nq;q=nq
        peak=max(peak,abs(u))
    return peak


def oracle_map(raw):
    if sha(raw)!=ORACLE_SHA:raise ValueError('ORACLE_SHA256_MISMATCH')
    rd=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    data={}
    for row in rd:
        key=(row['component'],float(row['period_s']))
        if key in data:raise ValueError('ORACLE_DUPLICATE')
        data[key]=float(row['exact_peak_rel_displacement_m'])
    if len(data)!=18:raise ValueError('ORACLE_COUNT')
    return data


def selftest():
    # Exact constant forcing solution with zero relative initial state.
    for T in (1.,4.):
        w=2*math.pi/T;wd=w*math.sqrt(1-ZETA**2);a=.3
        h=.005;k=w*w;c=2*ZETA*w
        (_, _),(u,v)=transition(0.,0.,a,a,h,k,c,wd)
        e=math.exp(-ZETA*w*h)
        ref_u=-a/k*(1-e*(math.cos(wd*h)+ZETA*w/wd*math.sin(wd*h)))
        ref_v=-a/wd*e*math.sin(wd*h)
        assert abs(u-ref_u)<2e-15,(u,ref_u)
        assert abs(v-ref_v)<2e-15,(v,ref_v)
        hst=exact_history([a]*300,T)
        assert hst['normalized_residual']<3e-8,hst['normalized_residual']
        assert abs(hst['peak_u']-newmark_peak([a]*300,T))<2e-5
    # Reject corrupted waveform identities, widths, time grid and non-finite input.
    valid=b'time_s,HNE_acc_m_s2,HNN_acc_m_s2,HNZ_acc_m_s2\n0,0,0,0\n0.005,0,0,0\n0.01,0,0,0\n'
    cases=[(b'bad\n','SOURCE_COLUMNS'),
           (valid.replace(b'0.005,0,0,0',b'0.005,0,0'),'SOURCE_ROW_WIDTH'),
           (valid.replace(b'0.005,0,0,0',b'0.006,0,0,0'),'SOURCE_TIME_GRID'),
           (valid.replace(b'0.005,0,0,0',b'0.005,nan,0,0'),'SOURCE_NONFINITE')]
    for raw,code in cases:
        try:read_wave(raw,False)
        except ValueError as exc:assert str(exc)==code,(str(exc),code)
        else:raise AssertionError('INVALID_SOURCE_ACCEPTED_'+code)
    try:read_wave(valid,True)
    except ValueError as exc:assert str(exc)=='SOURCE_SHA256_MISMATCH'
    else:raise AssertionError('SHA_GATE_MISSING')
    print('S08_ENERGY_SELFTEST_PASS constant_forcing_exact energy_closure newmark 5_rejections')


def plot(results,out,zoom=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none',
                         'svg.hashsalt':'S08_ESM_20261102','axes.spines.top':False,
                         'axes.spines.right':False,'axes.linewidth':.75,
                         'savefig.facecolor':'white'})
    fig,axs=plt.subplots(3,2,figsize=(11.2,7.0),sharex=True,
                         gridspec_kw={'wspace':.18,'hspace':.22})
    colors=('#16627b','#a34c38','#527c4d')
    for j,name in enumerate(COMP):
        for i,T in enumerate(PERIODS):
            ax=axs[j][i];r=results[name,T]
            history=r['history']
            if zoom:
                data=[v for v in history if 20 <= v[0] <= 70]
            else:
                data=[]
                for start in range(0,len(history),8):
                    chunk=history[start:start+8]
                    extrema={min(chunk,key=lambda v:v[1]),max(chunk,key=lambda v:v[1])}
                    data.extend(sorted(extrema,key=lambda v:v[0]))
                if history[-1] not in data:data.append(history[-1])
            t=[v[0] for v in data];u=[v[1]*1000 for v in data]
            ax.plot(t,u,color=colors[j],linewidth=.85,rasterized=False)
            ax.axhline(0,color='#777777',linewidth=.55)
            ax.grid(True,axis='y',color='#dddddd',linewidth=.45)
            ax.set_ylabel(('East HNE','North HNN','Vertical HNZ')[j]+'  |  u (mm)')
            ax.set_title(f'T={T:g} s   |   max |u|={r["peak_u"]*1000:.2f} mm',fontsize=10,pad=6)
            ax.yaxis.set_major_locator(MaxNLocator(5))
            if zoom:ax.set_xlim(20,70)
            else:ax.set_xlim(0,160.195)
            if j==2:ax.set_xlabel('Time (s)')
    fig.suptitle('Real ESM 2012 / NVL processed record: independent linear SDOF relative displacement',
                 fontsize=12,fontweight='bold',y=.995)
    fig.text(.5,.014,'Numerical base-excitation benchmark only  |  5% illustrative damping  |  not a 158 m tower response or design-wave acceptance',
             ha='center',fontsize=8,color='#444444')
    fig.subplots_adjust(left=.09,right=.98,top=.91,bottom=.095)
    fig.savefig(out,format='svg',metadata={'Date':'2026-11-02','Creator':'S08 source-locked Python benchmark'})
    plt.close(fig)


def run(source,oracle,outdir):
    axes=read_wave(source.read_bytes())
    expected=oracle_map(oracle.read_bytes())
    outdir.mkdir(parents=True,exist_ok=True)
    results={};summary=[]
    for name,acc in zip(COMP,axes):
        for T in PERIODS:
            r=exact_history(acc,T)
            exact_ref=expected[name,T]
            ref_error=abs(r['peak_u']-exact_ref)/max(exact_ref,1e-30)
            nm=newmark_peak(acc,T)
            nm_error=abs(nm-r['peak_u'])/max(r['peak_u'],1e-30)
            if ref_error>2e-11:raise ValueError('INDEPENDENT_EXACT_ORACLE_MISMATCH')
            if nm_error>.002:raise ValueError('NEWMARK_DISCREPANCY')
            if r['normalized_residual']>1e-6:raise ValueError('ENERGY_BALANCE_RESIDUAL')
            results[name,T]=r
            summary.append(dict(component=name,period_s=T,npts=N,dt_s=DT,
                 damping_ratio=ZETA,peak_rel_u_m=r['peak_u'],time_peak_u_s=r['peak_t'],
                 peak_abs_acc_m_s2=r['peak_abs_acc'],peak_rel_v_m_s=r['peak_v'],
                 final_energy_J_per_kg=r['energy'],ground_work_J_per_kg=r['work'],
                 viscous_dissipation_J_per_kg=r['dissipation'],
                 max_energy_residual_J_per_kg=r['max_residual'],
                 energy_residual_over_max_work_plus_diss=r['normalized_residual'],
                 oracle_peak_u_relative_error=ref_error,
                 newmark_peak_u_relative_error=nm_error,
                 source_sha256=SOURCE_SHA,status='REAL_ESM_SDOF_METHOD_QC_ONLY_NOT_TOWER'))
    table=outdir/'S08_REAL_ESM_SDOF_ENERGY_6CASE_20261102.csv'
    with table.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=OUTFIELDS,lineterminator='\n')
        wr.writeheader();wr.writerows(summary)
    figures=[]
    for zoom in (False,True):
        p=outdir/('FIG_S08_05_REAL_ESM_SDOF_RESPONSE_20_70S.svg' if zoom else 'FIG_S08_05_REAL_ESM_SDOF_RESPONSE_FULL.svg')
        plot(results,p,zoom=zoom)
        figures.append({'filename':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
    receipt={'status':'REAL_ESM_3COMP_SDOF_HISTORY_ENERGY_NUMERIC_QC_NOT_TOWER',
             'SOURCE':'ESM v3 DOI 10.13127/esm.3 IT-2012-0008/NVL/MP processed waveform',
             'REF':'exact piecewise-linear ground acceleration underdamped SDOF transition and independent Newmark average acceleration',
             'STANDARD':'NO_AUTHORIZED_IEC_GB_SITE_CLAUSE_VERIFICATION',
             'OFFICIAL':'archived ESM processed record, low-frequency instrument suitability not verified',
             'RUN':'Python '+platform.python_version()+' float64 numerical SDOF only; Abaqus/OpenFAST structural seismic=0',
             'FIG':[x['filename'] for x in figures], 'TAB':table.name,
             'reading_level':'actual archived 32040x3 SI waveform + original source ZIP; not unprocessed station waveform',
             'source_artifact_zip_sha256':ARTIFACT_SHA,'source_csv_sha256':SOURCE_SHA,
             'prior_independent_exact_oracle_sha256':ORACLE_SHA,
             'input_npts':N,'dt_s':DT,'periods_s':list(PERIODS),'damping_ratio':ZETA,
             'assumptions':['m=1 kg normalized oscillator','piecewise-linear ground acceleration between 0.005s samples',
                            'zero relative initial conditions','5% damping illustrative, not measured tower modal damping',
                            'no scaling to a site spectrum; unverified low-frequency passband and site class'],
             'error_budget':{'max_oracle_peak_u_relative_error':max(float(r['oracle_peak_u_relative_error']) for r in summary),
                             'max_newmark_peak_u_relative_error':max(float(r['newmark_peak_u_relative_error']) for r in summary),
                             'max_energy_residual_normalized':max(float(r['energy_residual_over_max_work_plus_diss']) for r in summary),
                             'source_low_frequency_site_model_uncertainty':'UNBOUNDED'},
             'failed_cases':'selftest five rejection cases; any input SHA mismatch/energy/oracle mismatch fails closed',
             'output_table_sha256':sha(table.read_bytes()),'figures':figures,
             'S05_PASS':False,'S08_PASS':False,'native_E_WE_RUN':0,
             'HOLD':'real 158m model S01-S04 native validated state, authorized site spectrum, ESM low-frequency and actual Abaqus E pilot'}
    p=outdir/'S08_REAL_ESM_SDOF_ENERGY_HISTORY_RECEIPT_20261102.json'
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    print('S08_REAL_ESM_SDOF_6_HISTORY_ENERGY_QC_PASS_NOT_TOWER',json.dumps(receipt['error_budget'],sort_keys=True))
    print('FILES',*[str(x) for x in (table,p)],*[x['filename'] for x in figures])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--source',type=Path)
    ap.add_argument('--oracle',type=Path)
    ap.add_argument('--outdir',type=Path)
    args=ap.parse_args()
    if args.self_test:selftest()
    if args.source:
        if not args.oracle or not args.outdir:ap.error('--source requires --oracle --outdir')
        run(args.source,args.oracle,args.outdir)
    elif not args.self_test:ap.error('use --self-test or --source')

if __name__=='__main__':main()
