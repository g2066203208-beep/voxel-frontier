#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T073 fixed-He-count E.0.1 feasibility map.

He Table 3-2 longitudinal-bar COUNTS remain immutable.
The ordinary-bar diameter/area is scanned because He (2024) does not publish it.
Primary material identity remains S345 to preserve the He source-model identity.
PT bundle factor remains a sensitivity because He does not publish strands/bundle.
"""
from __future__ import annotations
import csv,gzip,glob,json,math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
GEOM=ROOT.parent/"T071"/"T071_input_geometry_31_segments.csv"
RADII=ROOT/"T073_T053_RBLONG_RADII.csv"
OUT_MAP=ROOT/"T073_E01_HE_LOCKED_COUNT_DIAMETER_PT_MAP.csv"
OUT_MIN=ROOT/"T073_E01_MIN_DIAMETER_BY_PT_BF.csv"
OUT_META=ROOT/"T073_E01_FEASIBILITY_META.json"

ES=200000.; FY=345.; FYC=345.
EP=195000.; FPY=1320.; FPYC=390.
SIGP_INIT=1280.; PT_A1=140.; PT_R=1750.; NPT=36
ETAS=(0.70,0.80,0.85,0.90,1.00)
BFS=tuple(range(1,17))
DIAMS=(14,16,18,20,22,25,28,32,36,40,50)
NR=16; NTH=360; NZ=1500

def read_geom():
    with GEOM.open(encoding="utf-8-sig",newline="") as f:return {r["segment"]:r for r in csv.DictReader(f)}

def rings(geom):
    rr={}
    with RADII.open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):rr.setdefault(f"CSEG_{int(r['segment']):02d}",[]).append(r)
    out={}
    for seg,rows in rr.items():
        n=int(float(geom[seg]["bars_each_row"])); ex=[]
        for r in sorted(rows,key=lambda x:float(x["radius_m"])):
            ex += [float(r["radius_m"])*1000.]*max(1,int(round(int(r["node_count_at_radius"])/n)))
        if len(ex)!=4: raise RuntimeError((seg,ex))
        out[seg]=(0.5*(ex[0]+ex[1]),0.5*(ex[2]+ex[3]),n)
    return out

def cpars(seg):
    fcu,fc=(70.,31.8) if seg in ("CSEG_01","CSEG_02") else (65.,29.7)
    n=2-(fcu-50)/60; e0=.002+.5*(fcu-50)*1e-5; ecu=.0033-(fcu-50)*1e-5
    return fc,n,e0,ecu

def sc(e,fc,n,e0):
    e=np.asarray(e); s=np.zeros_like(e)
    m=(e>0)&(e<=e0); q=np.clip(1-e[m]/e0,0,None); s[m]=fc*(1-q**n); s[e>e0]=fc
    return s

def concfib(D,di):
    ro=D/2;ri=di/2;dr=(ro-ri)/NR;dt=2*math.pi/NTH
    rs=ri+(np.arange(NR)+.5)*dr; th=(np.arange(NTH)+.5)*dt
    R,T=np.meshgrid(rs,th,indexing="ij")
    return (R*np.sin(T)).ravel(),(R*dr*dt).ravel()

def components(seg,g,ring,eta):
    D=float(g["D_m"])*1000;di=float(g["di_m"])*1000;ro=D/2
    fc,nn,e0,ecu=cpars(seg)
    zc,ac=concfib(D,di)
    rin,rout,nbar=ring
    th=2*math.pi*np.arange(nbar)/nbar
    zs=np.concatenate([rin*np.sin(th),rout*np.sin(th)])
    zmin=float(zs.min())
    thp=2*math.pi*np.arange(NPT)/NPT;zp=PT_R*np.sin(thp)
    sig0=SIGP_INIT*eta

    zn=np.concatenate([np.linspace(-3*ro,-ro,150,endpoint=False),np.linspace(-ro,.999*ro,NZ-150)])
    kc=ecu/(ro-zn); ks=np.where(zn>zmin,.01/(zn-zmin),np.inf); kap=np.minimum(kc,ks)
    Nc=np.empty_like(zn);Mc=np.empty_like(zn)
    NsA=np.empty_like(zn);MsA=np.empty_like(zn)
    Np1=np.empty_like(zn);Mp1=np.empty_like(zn)
    for i in range(0,len(zn),50):
        sl=slice(i,min(i+50,len(zn))); zz=zn[sl,None];kk=kap[sl,None]
        ec=kk*(zc[None,:]-zz); sigc=sc(ec,fc,nn,e0)
        Nc[sl]=(sigc*ac).sum(1);Mc[sl]=(sigc*ac*zc).sum(1)
        es=kk*(zs[None,:]-zz); ss=np.clip(ES*es,-FY,FYC); cs=sc(es,fc,nn,e0)
        d=ss-cs
        NsA[sl]=d.sum(1);MsA[sl]=(d*zs[None,:]).sum(1) # per 1 mm2/bar
        ep=kk*(zp[None,:]-zz); sp=np.clip(sig0-EP*ep,sig0-FPYC,FPY)
        F=-sp*PT_A1
        Np1[sl]=F.sum(1);Mp1[sl]=(F*zp[None,:]).sum(1)
    return Nc,Mc,NsA,MsA,Np1,Mp1

def envelope(N,M):
    N=np.asarray(N);M=np.abs(np.asarray(M));o=np.argsort(N);N=N[o];M=M[o]
    span=max(float(N[-1]-N[0]),1.);bw=max(span/2500,5e4)
    b=np.floor((N-N[0])/bw).astype(int);u=np.unique(b)
    Nb=np.array([N[b==x].mean() for x in u]);Mb=np.array([M[b==x].max() for x in u])
    o=np.argsort(Nb);return Nb[o],Mb[o]

def histories():
    fs=sorted(glob.glob(str(ROOT/"artifacts"/"*"/"*31seg.csv.gz")))
    if len(fs)!=4:raise RuntimeError(fs)
    d={}
    for p in fs:
        with gzip.open(p,"rt",newline="") as f:
            for r in csv.DictReader(f):d.setdefault(r["segment"],[]).append(r)
    return {s:{
        "t":np.array([float(r["time_s"]) for r in rr]),
        "N":np.array([-float(r["Fz_kN"]) for r in rr]),
        "M":np.array([float(r["M_kNm"]) for r in rr])} for s,rr in d.items()}

def util(hist,ea,Nb,Mb,gN,gM):
    Nd=hist["N"]*gN*1000
    Md=(hist["M"]*gM+hist["N"]*gN*ea/1000)*1e6
    cap=np.full_like(Nd,np.nan);m=(Nd>=Nb.min())&(Nd<=Nb.max());cap[m]=np.interp(Nd[m],Nb,Mb)
    u=np.where(np.isfinite(cap)&(cap>0),Md/cap,np.inf)
    k=int(np.nanargmax(u))
    return float(u[k]),float(hist["t"][k]),float(Nd[k]/1000),float(Md[k]/1e6),float(cap[k]/1e6) if np.isfinite(cap[k]) else None

def constructability(g,ring,d):
    D=float(g["D_m"])*1000;di=float(g["di_m"])*1000
    rin,rout,n=ring
    cover_outer=D/2-rout-d/2
    cover_inner=rin-di/2-d/2
    clear_outer=2*rout*math.sin(math.pi/n)-d
    clear_inner=2*rin*math.sin(math.pi/n)-d
    return min(cover_outer,cover_inner),min(clear_outer,clear_inner)

def main():
    G=read_geom();R=rings(G);H=histories()
    combos={"uniform_1p40_screen":(1.4,1.4),"provisional_N1p35_M1p40":(1.35,1.4)}
    # cache strain-state components
    C={(seg,eta):components(seg,G[seg],R[seg],eta) for seg in sorted(G) for eta in ETAS}
    rows=[]
    for cname,(gN,gM) in combos.items():
      for d in DIAMS:
        A=math.pi*d*d/4
        for bf in BFS:
          worst=None
          mincov=1e9;minclear=1e9
          for seg in sorted(G):
            ea=max(20.,float(G[seg]["D_m"])*1000/30)
            cov,clr=constructability(G[seg],R[seg],d);mincov=min(mincov,cov);minclear=min(minclear,clr)
            for eta in ETAS:
              Nc,Mc,NsA,MsA,Np1,Mp1=C[(seg,eta)]
              Nb,Mb=envelope(Nc+A*NsA+bf*Np1,Mc+A*MsA+bf*Mp1)
              uu,tt,NN,MM,CC=util(H[seg],ea,Nb,Mb,gN,gM)
              rec=(uu,seg,eta,tt,NN,MM,CC)
              if worst is None or uu>worst[0]:worst=rec
          rows.append({
            "combo":cname,"bar_d_mm":d,"Abar_mm2":A,"BF":bf,
            "max_utilization":worst[0],"control_segment":worst[1],"control_eta":worst[2],
            "control_time_s":worst[3],"N_design_kN":worst[4],"M_design_kNm":worst[5],"Mcap_kNm":worst[6],
            "min_net_cover_mm_if_T053_centrelines_fixed":mincov,
            "min_clear_bar_spacing_mm":minclear,
            "PASS":"PASS" if worst[0]<=1 else "FAIL"
          })
    with OUT_MAP.open("w",newline="",encoding="utf-8") as f:
      w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    mins=[]
    for cname in combos:
      for bf in BFS:
        q=[r for r in rows if r["combo"]==cname and r["BF"]==bf and r["PASS"]=="PASS"]
        if q:
          r=min(q,key=lambda x:x["bar_d_mm"])
          mins.append({"combo":cname,"BF":bf,"minimum_passing_d_mm":r["bar_d_mm"],"max_utilization":r["max_utilization"],"control_segment":r["control_segment"],"control_eta":r["control_eta"],"min_net_cover_mm":r["min_net_cover_mm_if_T053_centrelines_fixed"],"min_clear_spacing_mm":r["min_clear_bar_spacing_mm"]})
        else:
          mins.append({"combo":cname,"BF":bf,"minimum_passing_d_mm":"NONE<=50","max_utilization":"","control_segment":"","control_eta":"","min_net_cover_mm":"","min_clear_spacing_mm":""})
    with OUT_MIN.open("w",newline="",encoding="utf-8") as f:
      w=csv.DictWriter(f,fieldnames=list(mins[0]));w.writeheader();w.writerows(mins)
    best={}
    for cname in combos:
      q=[r for r in rows if r["combo"]==cname and r["PASS"]=="PASS"]
      best[cname]=min(q,key=lambda x:(x["bar_d_mm"],x["BF"])) if q else None
    OUT_META.write_text(json.dumps({"method":"GB/T50010 E.0.1 fixed He counts feasibility map","material":"S345 source-model symmetric 345 MPa screen","diameters_mm":DIAMS,"BFs":BFS,"etas":ETAS,"best_min_diameter_then_BF":best},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(best,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
