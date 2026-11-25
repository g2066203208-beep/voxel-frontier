"""R53 regenerate 8 missing ERA5 thesis figures from 84 source-locked quarterly archives."""
import csv,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import genextreme,gumbel_r
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
R=Path("research/wind-tower")
ROOT=Path("public/thesis-studio");OUT=ROOT/"figure-audit/R53"
INV=R/"experiments/T046/inner-inventory"
sha=lambda b:hashlib.sha256(b).hexdigest()
def req(ok,msg):
    if not ok:raise ValueError(msg)
def table(name):return list(csv.DictReader((INV/name).open(),delimiter="\t"))
def extract():
    q=table("QUARTERLY_ARCHIVES.tsv");inner=table("INNER_MEMBERS.tsv")
    req(len(q)==84 and len(inner)==168,"source inventory size")
    checks={(x["quarter_id"],x["inner_member"]):x for x in inner}
    frames=[];sources=[]
    for row in sorted(q,key=lambda x:x["quarter_id"]):
        with zipfile.ZipFile(R/row["outer_archive"]) as z:raw=z.read(row["quarter_member"])
        req(len(raw)==int(row["quarter_bytes"]) and sha(raw)==row["quarter_sha256"],"quarter SHA "+row["quarter_id"])
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            req(z.testzip() is None,"quarter CRC")
            members=[n for n in z.namelist() if not n.endswith("/")]
            req(len(members)==2,"quarter count")
            for n in members:
                data=z.read(n);ref=checks[(row["quarter_id"],n)]
                req(len(data)==int(ref["bytes"]) and sha(data)==ref["sha256"],"inner SHA")
                if "instant" not in n:continue
                with xr.open_dataset(io.BytesIO(data),engine="h5netcdf") as ds:
                    req(all(k in ds for k in ["u10","v10","u100","v100"]),"variables "+str(list(ds.data_vars)))
                    selected=ds[["u10","v10","u100","v100"]].interp(latitude=30.2,longitude=113.925)
                    # Only singleton ancillary axes permitted.
                    for dim in list(selected.dims):
                        if dim not in ("valid_time","time"):
                            req(selected.sizes[dim]==1,"unexpected dimension "+dim)
                            selected=selected.isel({dim:0},drop=True)
                    t="valid_time" if "valid_time" in selected.coords else "time"
                    df=pd.DataFrame({k:np.asarray(selected[k].values,dtype=float) for k in ["u10","v10","u100","v100"]},index=pd.DatetimeIndex(selected[t].values))
                    req(np.isfinite(df.to_numpy()).all(),"nonfinite "+row["quarter_id"])
                    frames.append(df);sources.append({"quarter":row["quarter_id"],"quarter_sha256":sha(raw),"instant_sha256":sha(data),"rows":len(df)})
    df=pd.concat(frames).sort_index()
    expected=pd.date_range("2005-01-01","2025-12-31 23:00:00",freq="h")
    req(df.index.equals(expected) and len(df)==184080,"hour completeness")
    return df,sources
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,sources=extract()
    u10=np.hypot(df.u10,df.v10).to_numpy();u100=np.hypot(df.u100,df.v100).to_numpy()
    req(np.all(u10>0) and np.all(u100>0),"zero speed; do not silently repair")
    alpha=np.log(u100/u10)/np.log(10.);u160=u100*1.6**alpha;uh=u100*(161.368806/100)**alpha
    valid=(u10>=.5)&(u100>=.5)
    direction=np.mod(np.degrees(np.arctan2(-df.u100,-df.v100)),360).to_numpy()
    sectors=np.floor((direction+11.25)/22.5).astype(int)%16
    q95=np.quantile(u100,.95);high=u100>=q95
    # Independent historical numerical identity before publishing any graph.
    targets={"mean10":(u10.mean(),2.617,.0006),"mean100":(u100.mean(),4.298716,6e-6),"p50":(np.quantile(u100,.5),4.061353,6e-6),"p95":(q95,8.385445,6e-6),"p99":(np.quantile(u100,.99),10.429040,6e-6),"max100":(u100.max(),17.626156,6e-6),"mean160":(u160.mean(),4.786600,6e-6),"meanHub":(uh.mean(),4.796029,6e-6),"p95Hub":(np.quantile(uh,.95),9.343881,6e-6),"maxHub":(uh.max(),19.202140,6e-6),"validAlpha":(int(valid.sum()),180768,0)}
    for k,(x,old,tol) in targets.items():req(abs(x-old)<=tol,"historical mismatch "+k+" "+str(x))
    for i,(allv,highv) in {0:(11.73,24.00),1:(15.45,37.14),2:(9.72,3.66),9:(None,20.10)}.items():
        if allv is not None:req(abs(100*np.mean(sectors==i)-allv)<=.015,"direction mismatch "+str(i))
        req(abs(100*np.mean(sectors[high]==i)-highv)<=.015,"high direction mismatch "+str(i))
    data=pd.DataFrame(dict(u10=u10,u100=u100,u160=u160,uhub=uh,alpha=alpha,direction_deg=direction),index=df.index)
    annual=data[["u10","u100","u160","uhub"]].groupby(data.index.year).mean()
    monthly=data[["u10","u100","u160","uhub"]].groupby(data.index.month).mean()
    annualmax=data.u100.groupby(data.index.year).max()
    order=np.sort(u100);exceed=100*(len(order)-np.arange(len(order)))/len(order)
    counts=np.zeros((16,6));edges=np.array([0,2,4,6,8,10,np.inf])
    for i in range(16):counts[i]=np.histogram(u100[sectors==i],bins=edges)[0]/len(data)*100
    highpct=np.bincount(sectors[high],minlength=16)/high.sum()*100
    req(abs(counts.sum()-100)<1e-10 and abs(highpct.sum()-100)<1e-10,"direction normalization")
    shape,loc,scale=genextreme.fit(annualmax.to_numpy());gloc,gscale=gumbel_r.fit(annualmax.to_numpy())
    T=np.geomspace(1.05,100,200);gev=genextreme.ppf(1-1/T,shape,loc=loc,scale=scale);gum=gumbel_r.ppf(1-1/T,loc=gloc,scale=gscale)
    req(np.isfinite(gev).all() and np.isfinite(gum).all(),"GEV")
    returns={str(t):float(genextreme.ppf(1-1/t,shape,loc=loc,scale=scale)) for t in [20,50,100]}
    # The old text rounded GEV values; reject if materially different.
    req(max(abs(returns[str(t)]-v) for t,v in [(20,16.91),(50,17.49),(100,17.86)])<.12,"GEV old fit discrepancy")
    plt.rcParams.update({"font.family":"DejaVu Serif","font.size":10,"axes.linewidth":.8,"xtick.direction":"in","ytick.direction":"in","legend.frameon":False,"svg.fonttype":"none"})
    figures=[]
    def save(fig,id,description):
        for ext in ["png","svg","pdf"]:fig.savefig(OUT/(id+"."+ext),dpi=300,bbox_inches="tight")
        plt.close(fig);figures.append({"id":id,"asset":"./figure-audit/R53/"+id+".svg","description":description,"png_sha256":sha((OUT/(id+".png")).read_bytes()),"svg_sha256":sha((OUT/(id+".svg")).read_bytes())})
    fig,ax=plt.subplots(figsize=(6.7,3.5),layout="constrained")
    for k,label,ls in [("u100","100 m","-"),("u160","160 m","--")]:ax.plot(annual.index,annual[k],ls,label=label,marker="o",ms=3,lw=1.1)
    ax.set(xlabel="Year",ylabel="Annual mean wind speed (m/s)",xticks=np.arange(2005,2026,4));ax.legend();save(fig,"b0332","21 annual means, 100 m and extrapolated 160 m")
    fig,ax=plt.subplots(figsize=(6.1,3.5),layout="constrained");ax.semilogy(order,exceed,c="black",lw=1.0)
    for q in [.5,.95,.99]:
        v=np.quantile(u100,q);ax.plot(v,100*(1-q),"o",ms=3,c="black");ax.annotate("P%d"%round(100*q),(v,100*(1-q)),xytext=(5,6),textcoords="offset points",fontsize=9)
    ax.set(xlabel="Wind speed at 100 m (m/s)",ylabel="Empirical exceedance (%)",xlim=(0,18));save(fig,"b0335","184080-hour empirical exceedance")
    fig,ax=plt.subplots(figsize=(6.1,3.5),layout="constrained")
    for k,label,ls in [("u100","100 m","-"),("u160","160 m","--")]:ax.plot(monthly.index,monthly[k],ls,label=label,marker="o",ms=3,lw=1.1)
    ax.set(xlabel="Month",ylabel="Monthly mean wind speed (m/s)",xticks=np.arange(1,13));ax.legend();save(fig,"b0341","12 monthly climatological means")
    dirs=np.arange(16)*np.pi/8;labels=["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    fig,ax=plt.subplots(figsize=(5.6,5.6),subplot_kw={"projection":"polar"},layout="constrained")
    bottom=np.zeros(16)
    for i,label in enumerate(["0–2","2–4","4–6","6–8","8–10","≥10"]):
        ax.bar(dirs,counts[:,i],width=np.pi/8*.9,bottom=bottom,label=label,color=plt.cm.Blues(.20+i*.13),edgecolor=".35",linewidth=.3);bottom+=counts[:,i]
    ax.set_theta_zero_location("N");ax.set_theta_direction(-1);ax.set_xticks(dirs,labels,fontsize=8);ax.set_rlabel_position(78.75);ax.set_rticks([4,8,12,16]);ax.yaxis.set_major_formatter(PercentFormatter(xmax=100,decimals=0));ax.legend(title="Speed (m/s)",loc="lower center",bbox_to_anchor=(.5,-.22),ncol=3,fontsize=8);save(fig,"b0344","joint wind direction/speed frequency, all hours")
    fig,ax=plt.subplots(figsize=(5.1,5.1),subplot_kw={"projection":"polar"},layout="constrained")
    ax.bar(dirs,highpct,width=np.pi/8*.9,color="#547da2",edgecolor=".2",linewidth=.5);ax.set_theta_zero_location("N");ax.set_theta_direction(-1);ax.set_xticks(dirs,labels,fontsize=8);ax.set_rlabel_position(78.75);ax.set_rticks([10,20,30,40]);ax.yaxis.set_major_formatter(PercentFormatter(xmax=100,decimals=0));ax.set_title("V100 ≥ P95 = %.3f m/s"%q95,fontsize=10,pad=15);save(fig,"b0346","conditional direction frequency among upper 5% wind speed")
    fig,ax=plt.subplots(figsize=(6.1,3.5),layout="constrained");a=alpha[valid];lo=np.floor(a.min()/.02)*.02;hi=np.ceil(a.max()/.02)*.02;bins=np.arange(lo,hi+.021,.02);req(bins[0]<=a.min() and bins[-1]>=a.max(),"histogram coverage");ax.hist(a,bins=bins,density=True,color=".72",edgecolor=".45",linewidth=.3)
    for q,ls in [(.25,"--"),(.5,"-"),(.75,"--")]:ax.axvline(np.quantile(alpha[valid],q),c="black",ls=ls,lw=.9,label="P%d"%round(100*q))
    ax.set(xlabel="Hourly power-law shear exponent",ylabel="Probability density");ax.legend(ncol=3);save(fig,"b0349","180768 valid hourly exponents; bins cover full observed range")
    fig,ax=plt.subplots(figsize=(5.6,3.3),layout="constrained")
    ax.plot([u10.mean(),u100.mean(),u160.mean(),uh.mean()],[10,100,160,161.368806],"o-",label="Hourly ERA5 extrapolation",lw=1.1,ms=4)
    ax.plot([4.79],[160],marker="s",mfc="white",mec="black",ls="none",label="Project EIA");ax.set(xlabel="Long-term mean wind speed (m/s)",ylabel="Height (m)");ax.legend(loc="lower right",fontsize=8);save(fig,"b0351","observed reanalysis levels, hourly extrapolation, public EIA crosscheck")
    fig,ax=plt.subplots(figsize=(6.1,3.5),layout="constrained");v=np.sort(annualmax.to_numpy());n=len(v);plotT=1/(1-(np.arange(1,n+1)-.44)/(n+.12))
    ax.semilogx(plotT,v,"o",mfc="white",mec="black",ms=4,label="Annual maxima (Gringorten)");ax.semilogx(T,gev,"-",lw=1.2,label="GEV (MLE)");ax.semilogx(T,gum,"--",lw=1.0,label="Gumbel (MLE)");ax.set(xlabel="Return period (years)",ylabel="100 m hourly wind speed (m/s)",xlim=(1,100));ax.legend(fontsize=8);save(fig,"b0354","21 annual maxima, GEV and Gumbel sensitivity, not IEC design wind")
    annual.to_csv(OUT/"annual_means.csv",index_label="year");monthly.to_csv(OUT/"monthly_means.csv",index_label="month");annualmax.to_csv(OUT/"annual_maxima.csv",index_label="year")
    pd.DataFrame(counts,index=labels,columns=["0_2","2_4","4_6","6_8","8_10","10_inf"]).assign(high_percent=highpct).to_csv(OUT/"direction_frequency.csv",index_label="direction")
    pd.DataFrame(dict(T_year=T,GEV_m_s=gev,Gumbel_m_s=gum)).to_csv(OUT/"return_levels.csv",index=False)
    np.savez_compressed(OUT/"hourly_site_series.npz",time_utc=df.index.to_numpy().astype("datetime64[s]"),u10=u10,u100=u100,u160=u160,uhub=uh,alpha=alpha,direction_deg=direction,alpha_valid=valid)
    receipt={"status":"RAW_ERA5_RECOMPUTED_PASS","quarter_count":len(sources),"inner_hash_count":168,"samples":len(data),"point":{"longitude":113.925,"latitude":30.2},"interpolation":"bilinear u/v before magnitude","source_inventory_sha256":{k:sha((INV/k).read_bytes()) for k in ["INNER_MEMBERS.tsv","QUARTERLY_ARCHIVES.tsv"]},"historical_checks":{k:{"actual":float(x),"old":float(y),"abs_error":float(abs(x-y)),"tolerance":z} for k,(x,y,z) in targets.items()},"annual_100m_min_max":[float(annual.u100.min()),float(annual.u100.max())],"monthly_100m_min_max":[float(monthly.u100.min()),float(monthly.u100.max())],"high_samples":int(high.sum()),"alpha_quantiles":np.quantile(alpha[valid],[.05,.25,.5,.75,.95]).tolist(),"GEV":{"shape_scipy":float(shape),"loc":float(loc),"scale":float(scale),"return_levels":returns},"figures":figures,"sources":sources,"hourly_npz_sha256":sha((OUT/"hourly_site_series.npz").read_bytes()),"limitations":"ERA5 reanalysis, extrapolated heights, not site measurements; no new IEC design-wind claim. Source archive verified all 168 members, but only instant wind variables scientifically used."}
    (OUT/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n");print(json.dumps({k:v for k,v in receipt.items() if k not in ("sources","figures")},indent=2))
if __name__=="__main__":main()
