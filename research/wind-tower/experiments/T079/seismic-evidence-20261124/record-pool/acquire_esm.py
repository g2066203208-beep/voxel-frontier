"""ESM public source acquisition, never substitutes or synthesizes waveforms.
Candidate records, not Jiayu design-wave approval. Official MP ASC only.
"""
import concurrent.futures as cf, hashlib, io, json, csv, re, zipfile, datetime, pathlib, math, time
import requests, numpy as np
from scipy.signal import lfilter, cont2discrete
from scipy.integrate import cumulative_trapezoid

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"acquired_v2"; OUT.mkdir(exist_ok=True)
BASE="https://esm-db.eu/esmws/"
DAYS=[
("P01","1999-09-20","1999-09-21",7.0,"ILA004"),
("P02","2010-04-04","2010-04-05",6.8,"00022"),
("P03","2000-10-06","2000-10-07",6.5,"SMN005"),
("P04","1999-10-16","1999-10-17",6.8,"HEC"),
("P05","1983-05-02","1983-05-03",5.5,"PGS"),
("P06","1979-10-15","1979-10-16",6.0,"CPE"),
("P07","1984-04-24","1984-04-25",6.0,"G01"),
("R01","2009-04-06","2009-04-07",6.0,None),
("R02","2012-05-20","2012-05-21",5.8,None),
("R03","2016-08-24","2016-08-25",6.0,None),
("R04","2016-10-30","2016-10-31",6.2,None),
("R05","2020-10-30","2020-10-31",6.5,None),
("R06","2019-11-26","2019-11-27",6.1,None),
("R07","2020-12-29","2020-12-30",6.1,None),
("R08","2021-03-03","2021-03-04",6.0,None),
("R09","2014-01-26","2014-01-27",5.7,None),
("R10","2015-11-17","2015-11-18",6.0,None),
("R11","2023-02-06","2023-02-07",7.3,None),
("R12","2017-07-20","2017-07-22",6.3,None),
]
SPECIAL=[
("S01","TK-1999-0077","YPT"),
("S02_ALT","INT-20230206_0000008","4615"),
("S02_ALT_ID2","INT-20230206-0000008","4615"),
("S03_ALT","IT-1980-0012","STR"),
("S04_ALT","EMSC-20161030_0000029","T1201")]
PERIODS=np.unique(np.r_[np.geomspace(.1,15,100),4.,6.,7.3937,8.,10.,12.,15.])
def digest(b):return hashlib.sha256(b).hexdigest()
def request(endpoint,params):
    url=BASE+endpoint+"/1/query"
    r=requests.get(url,params=params,timeout=(10,50),headers={"User-Agent":"T079-seismic-research/1.0"})
    return r
def num(x,d=math.nan):
    try:return float(x)
    except:return d
def query(row):
    label,st,en,m,station=row
    p={"starttime":st,"endtime":en,"minmag":m,"maxdist":200,"unprocessed":"false","discarded":"false","automatic":"false","manual":"true"}
    if station:p["station"]=station
    try:
        r=request("dataset-selection",p)
        rec={"label":label,"url":r.url,"http":r.status_code,"sha256":digest(r.content)}
        if r.status_code!=200:return rec,[]
        j=r.json()
        if not isinstance(j,list):raise ValueError("unexpected JSON shape")
        rec["count"]=len(j);(OUT/(label+"_metadata.json")).write_bytes(r.content)
        return rec,j
    except Exception as e:return {"label":label,"error":str(e)},[]
def parse(b):
    h={}; vals=[]
    for l in b.decode("utf-8-sig").splitlines():
        l=l.strip()
        if not l:continue
        if ":" in l and not vals:
            k,v=l.split(":",1);h[k.strip()]=v.strip()
        else:
            vals.extend(float(x) for x in l.split())
    a=np.asarray(vals)
    if len(a)!=int(h["NDATA"]) or not np.isfinite(a).all():raise ValueError("sample count or finite values")
    if h["UNITS"]!="cm/s^2" or h["DATA_TYPE"]!="ACCELERATION":raise ValueError("units/type")
    dt=float(h["SAMPLING_INTERVAL_S"])
    if dt<=0 or dt>0.02:raise ValueError("sampling interval")
    if abs(np.max(np.abs(a))-abs(float(h["PGA_CM/S^2"])))>max(0.001,0.001*np.max(np.abs(a))):raise ValueError("PGA header mismatch")
    return h,a*.01,dt
def spectra(a,b,dt):
    # Exact discrete state-space with piecewise-linear acceleration input.
    # scipy FOH yields equivalent transfer function with input feedthrough.
    ang=np.deg2rad(np.arange(180)); cs=np.cos(ang);ss=np.sin(ang)
    result=[]
    for T in PERIODS:
        w=2*np.pi/T
        A=np.array([[0,1],[-w*w,-.1*w]])
        B=np.array([[0],[-1.]])
        C=np.array([[w*w,0.]])
        Ad,Bd,Cd,Dd,_=cont2discrete((A,B,C,np.array([[0.]])),dt,method="foh")
        # state at first step corrected for FOH initial input; initial physical state zero.
        # Use ZOH state transfer and FOH b; x_d0=-B1*u0, where B1 obtained via augmented exp.
        from scipy.linalg import expm
        H=np.zeros((4,4)); H[:2,:2]=A;H[:2,2:3]=B;H[2,3]=1.
        E=expm(H*dt);b1=E[:2,3]/dt
        # scipy dlsim with explicit initial state is slower; transfer lfilter
        # homogeneous correction for nonzero first sample calculated separately.
        from scipy.signal import ss2tf
        n,d=ss2tf(Ad,Bd,Cd,Dd)
        u=lfilter(n[0],d,a);v=lfilter(n[0],d,b)
        if a[0]!=0 or b[0]!=0:
            # correction from zero discrete state to correct physical initial state
            c0=float((-Cd@b1).item())
            c1=float((-Cd@Ad@b1).item())
            corr=lfilter([c0,c1+d[1]*c0],d,np.r_[1.,np.zeros(len(a)-1)])
            u+=corr*a[0];v+=corr*b[0]
        peaks=np.array([np.max(np.abs(u*c+v*s)) for c,s in zip(cs,ss)])
        result.append([T,np.median(peaks),np.max(np.hypot(u,v)),np.max(abs(u)),np.max(abs(v))])
    return result
def acquire(task):
    label,event,net,station,loc,ins,meta=task
    params={"eventid":event,"station":station,"format":"ascii","processing-type":"MP","data-type":"ACC","quality-class":"BEST,GOOD"}
    if net:params["network"]=net
    if loc:params["location"]=loc
    if ins:params["channel"]=ins+"*"
    rct={"label":label,"event":event,"station":station,"network_requested":net,"metadata":meta,"status":"HOLD"}
    try:
        r=request("eventdata",params)
        if r.status_code==400:
            params.pop("location",None);params.pop("channel",None);r=request("eventdata",params)
        rct.update(url=r.url,http=r.status_code,source_sha256=digest(r.content),bytes=len(r.content))
        if not r.ok:rct["response_excerpt"]=r.text[:300]
        if not r.ok or not zipfile.is_zipfile(io.BytesIO(r.content)):raise ValueError("not a public processed ZIP")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            if z.testzip():raise ValueError("CRC error")
            chans={}
            for name in z.namelist():
                if not name.upper().endswith(".ASC"):continue
                h,a,dt=parse(z.read(name))
                if h["EVENT_ID"]!=event or h["STATION_CODE"]!=station:raise ValueError("event/station mismatch")
                k=(h["NETWORK"],h["LOCATION"],h["STREAM"][:2]);chans.setdefault(k,{})[h["STREAM"][-1]]=(h,a,dt,name,digest(z.read(name)))
            eligible=[(k,v) for k,v in chans.items() if ("E" in v and "N" in v)]
            if len(eligible)!=1:raise ValueError("ambiguous or missing synchronized E/N pair")
            k,v=eligible[0];h,a,dt,*_=v["E"];g,b,dt2,*_=v["N"]
            if len(a)!=len(b) or dt!=dt2 or h["DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS"]!=g["DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS"]:raise ValueError("pair grid mismatch")
            rct["licenses"]=[x[0].get("DATA_LICENSE","") for x in v.values()]
            if not all(re.search(r"CC[-_ ]?BY(?:[-_ ]|[0-9])",x,re.I) and not re.search(r"\b(?:NC|ND)\b|NONCOMMERCIAL|NODERIVATIVES",x,re.I) for x in rct["licenses"]):raise ValueError("redistribution license not verified")
            fc=[num(x[0].get("LOW_CUT_FREQUENCY_HZ")) for x in [v["E"],v["N"]]]
            d=OUT/(event+"__"+k[0]+"_"+station+"_"+(k[1] or "blank")+"_"+k[2]);d.mkdir(exist_ok=True)
            (d/"original_MP_ACC.zip").write_bytes(r.content)
            t=np.arange(len(a))*dt
            data=[t,a,b]; cols="time_s,E_m_s2,N_m_s2"
            if "Z" in v and len(v["Z"][1])==len(a) and v["Z"][2]==dt and v["Z"][0]["DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS"]==h["DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS"]:
                data.append(v["Z"][1]);cols+=",Z_m_s2"
            np.savetxt(d/"acceleration_SI.csv",np.column_stack(data),delimiter=",",header=cols,comments="",fmt="%.10g")
            rs=spectra(a,b,dt)
            np.savetxt(d/"spectra_5pct.csv",rs,delimiter=",",header="T_s,RotD50_m_s2,RotD100_m_s2,E_PSA_m_s2,N_PSA_m_s2",comments="",fmt="%.10g")
            ari=cumulative_trapezoid(a*a+b*b,dx=dt,initial=0)
            dur=float(np.interp(.95*ari[-1],ari,t)-np.interp(.05*ari[-1],ari,t))
            rct.update(status="SOURCE_PAIR_ACQUIRED_NOT_DESIGN",directory=str(d.relative_to(ROOT)),dt_s=dt,npts=len(a),duration_s=float(t[-1]),PGA_m_s2=[float(max(abs(a))),float(max(abs(b)))],D5_95_pair_s=dur,low_cut_hz=fc,reported_fc_le_005=bool(all(np.isfinite(fc)) and max(fc)<=.05),Sa7_3937_RotD50=float(np.array(rs)[np.where(PERIODS==7.3937)[0][0],1]),headers=[dict(stream=x[0]["STREAM"],member=x[3],sha256=x[4],header=x[0]) for x in v.values()],files={p.name:{"sha256":digest(p.read_bytes()),"bytes":p.stat().st_size} for p in d.iterdir() if p.is_file()},scope="official processed samples, cutoff screen only, no site target or instrument reliability certification")
            (d/"receipt.json").write_text(json.dumps(rct,indent=2,ensure_ascii=False,allow_nan=True)+"\n")
    except Exception as e:rct["error"]=str(e)
    print("PAIR",json.dumps({k:v for k,v in rct.items() if k not in ("headers","metadata","files")},ensure_ascii=False),flush=True)
    return rct
def main():
    # Reuse already archived official metadata; no duplicate first-round requests.
    queries=[]
    for row in DAYS:
        label=row[0]; p=ROOT/"acquired"/(label+"_metadata.json")
        if p.exists():
            b=p.read_bytes();j=json.loads(b);queries.append(({"label":label,"metadata_source":str(p.relative_to(ROOT)),"sha256":digest(b),"count":len(j)},j))
    # Additional independent historical Italian records, selected from official event dates.
    extra=[("R13","2009-04-07","2009-04-08",5.3,None),("R14","2012-05-29","2012-05-30",5.6,None),("R15","2016-10-26","2016-10-27",5.8,None),("R16","2017-01-18","2017-01-19",5.4,None),("R17","2011-10-23","2011-10-24",7.0,None)]
    with cf.ThreadPoolExecutor(max_workers=5) as ex: queries+=list(ex.map(query,extra))
    tasks=[]; seen=set()
    for rec,rows in queries:
        print("QUERY",json.dumps(rec),flush=True)
        # exact requested station, otherwise choose three records per distinct event
        rows=[r for r in rows if r.get("event_id") and r.get("station_code") and "MP" in r.get("processing_avail",[])]
        rows.sort(key=lambda r:(0 if r.get("net_name") in ("IT","IV","8P") else 1,0 if r.get("class")=="BEST" else 1,abs(num(r.get("corr_hz_PGA"),100)-40),num(r.get("epi_dist"),100)))
        per={}
        for r in rows:
            e=r["event_id"];st=r["station_code"];nt=r.get("net_name");loc=r.get("location_code","");ins=r.get("instr_code","").replace("*","")
            key=(e,nt,st,loc,ins)
            if key in seen or per.get(e,0)>=2:continue
            seen.add(key);per[e]=per.get(e,0)+1
            tasks.append((rec["label"],e,nt,st,loc,ins,r))
            if sum(per.values())>=4:break
    for label,event,station in SPECIAL:
        tasks.append((label,event,None,station,None,None,{"special_reference":"Yang et al 2025 DOI 10.1111/mice.13408"}))
    # explicit Chi-Chi record ID from Yang et al; source station availability may differ.
    tasks.append(("P01_EXACT","INT-UT19990920_174715",None,"ILA004",None,None,{}))
    print("TASKS",len(tasks),flush=True)
    with cf.ThreadPoolExecutor(max_workers=4) as ex: results=list(ex.map(acquire,tasks))
    (OUT/"acquisition_receipt.json").write_text(json.dumps({"queries":[x[0] for x in queries],"records":results},indent=2,ensure_ascii=False)+"\n")
    rows=[r for r in results if r["status"]=="SOURCE_PAIR_ACQUIRED_NOT_DESIGN"]
    cols=["label","event","station","directory","dt_s","npts","duration_s","PGA_m_s2","D5_95_pair_s","low_cut_hz","reported_fc_le_005","Sa7_3937_RotD50","source_sha256"]
    with (OUT/"candidate_inventory.csv").open("w") as f:
        wr=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore");wr.writeheader();wr.writerows(rows)
    print("SUMMARY",len(rows),len(set(r["event"] for r in rows)),sum(r["reported_fc_le_005"] for r in rows),flush=True)
if __name__=="__main__":main()
