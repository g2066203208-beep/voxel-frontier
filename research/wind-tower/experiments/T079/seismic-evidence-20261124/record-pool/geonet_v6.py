"""GeoNet official structural-analyses archive acquisition; record-specific usable-frequency screening.
Do not infer a sample format or declare a record approved without numerical source checks."""
import requests, pathlib, hashlib, zipfile, json, csv, io, re, math
import pandas as pd
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"geonet_v6";OUT.mkdir(exist_ok=True)
URL="https://static.geonet.org.nz/info/resources/applications_data/earthquake/strong_motion/"
def fetch(name):
    p=pathlib.Path("/tmp")/name;h=hashlib.sha256()
    with requests.get(URL+name,stream=True,timeout=(15,120)) as r:
        r.raise_for_status()
        with p.open("wb") as f:
            for c in r.iter_content(1024*1024):
                if c:f.write(c);h.update(c)
    print(name,p.stat().st_size,h.hexdigest(),flush=True)
    return p,{"url":URL+name,"bytes":p.stat().st_size,"sha256":h.hexdigest()}
def norm(s):return re.sub(r"[^a-z0-9]","",str(s).lower())
def read_table(z,n):
    raw=z.read(n)
    if n.lower().endswith((".xlsx",".xls")):return pd.read_excel(io.BytesIO(raw))
    for skip in range(4):
        for enc in ("utf-8-sig","latin-1"):
            try:
                df=pd.read_csv(io.BytesIO(raw),sep=None,engine="python",encoding=enc,skiprows=skip,low_memory=False) 
            except Exception:
                try:df=pd.read_csv(io.BytesIO(raw),sep=None,engine="python",encoding=enc,skiprows=skip)
                except Exception:continue
            if any(norm(c)=="record" for c in df.columns):return df
    return None
def num(v):
    try:return float(v)
    except:return float("nan")
flat,fr=fetch("Flatfiles.zip")
tables=[];cand=[]
with zipfile.ZipFile(flat) as z:
    inventory=z.namelist()
    for n in inventory:
        if not n.lower().endswith((".csv",".txt",".xlsx",".xls")):continue
        try:
            df=read_table(z,n)
            if df is None:continue
            cols={norm(c):c for c in df.columns}
            tables.append({"name":n,"rows":len(df),"columns":list(map(str,df.columns))})
            if not all(k in cols for k in ("record","fmin","mw","tectclass","cuspid")):continue
            if "sa" not in n.lower() and "response" not in n.lower() and not any("sarotd50" in k for k in cols):continue
            for _,r in df.iterrows():
                f=num(r[cols["fmin"]]);mw=num(r[cols["mw"]]);tect=str(r[cols["tectclass"]]).lower()
                if not (0<f<=1/15 and 5.5<=mw<=8 and "crust" in tect):continue
                if "striggerflag" in cols and num(r[cols["striggerflag"]])==1:continue
                if "directivity" in cols and num(r[cols["directivity"]])==1:continue
                record=str(r[cols["record"]]);event=str(r[cols["cuspid"]]);dist=num(r[cols["rrupkm"]]) if "rrupkm" in cols else float("nan")
                if math.isfinite(dist) and not 15<=dist<=300:continue
                if record.startswith("20100903"):continue
                vals={str(k):None if pd.isna(v) else str(v) for k,v in r.items()}
                cand.append({"record":record,"event":event,"fmin":f,"mw":mw,"rrup":dist if math.isfinite(dist) else None,"table":n,"row":vals})
        except Exception as e:tables.append({"name":n,"error":str(e)})
(OUT/"flatfile_inventory.json").write_text(json.dumps({"source":fr,"members":inventory,"tables":tables,"candidate_rows":len(cand)},indent=2))
(OUT/"eligible_metadata.json").write_text(json.dumps(cand,indent=2))
# Actual published candidate archive; use only records that have exact official metadata identity.
archive,ar=fetch("ForStructuralAnalyses.zip")
with zipfile.ZipFile(archive) as z:
    names=z.namelist();(OUT/"archive_inventory.json").write_text(json.dumps({"source":ar,"members":names},indent=2))
    groups={}
    for r in cand:
        matches=[n for n in names if r["record"].lower() in pathlib.PurePosixPath(n).name.lower() and not n.endswith("/")]
        if matches:groups.setdefault(r["event"],{})[r["record"]]=(r,matches)
    chosen=[]
    for event,rs in sorted(groups.items(),key=lambda x:-max(v[0]["mw"] for v in x[1].values()))[:12]:
        for r,matches in sorted(rs.values(),key=lambda x:(x[0]["fmin"],abs((x[0]["rrup"] or 100)-80)))[:3]:
            d=OUT/re.sub(r"[^a-zA-Z0-9_-]","_",r["record"]);d.mkdir(exist_ok=True)
            entries=[]
            for n in matches:
                bb=z.read(n)
                if len(bb)>20*1024*1024:continue
                fn=pathlib.PurePosixPath(n).name;(d/fn).write_bytes(bb)
                entries.append({"member":n,"file":fn,"sha256":hashlib.sha256(bb).hexdigest(),"bytes":len(bb),"header_preview":bb[:1500].decode("utf-8",errors="replace")})
            if entries:
                (d/"receipt.json").write_text(json.dumps({"metadata":r,"source":ar,"files":entries,"license":"GeoNet CC BY 3.0 NZ","status":"SOURCE_ACQUIRED_FORMAT_AND_QC_PENDING"},indent=2))
                chosen.append({"record":r["record"],"event":r["event"],"fmin":r["fmin"],"files":len(entries)})
    (OUT/"summary.json").write_text(json.dumps({"archive":ar,"metadata":fr,"eligible":len(cand),"matched_events":len(groups),"actual_downloaded_records":chosen,"formal_design":0},indent=2))
    print("SUMMARY",json.dumps(chosen),flush=True)
