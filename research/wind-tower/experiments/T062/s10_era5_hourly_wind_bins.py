#!/usr/bin/env python3
"""S10 full ERA5-derived XLSX hourly 1m/s bins; source-QC, NOT fatigue PASS."""
import argparse,csv,datetime as D,hashlib,json,math,pathlib,re,sys,zipfile,xml.etree.ElementTree as X
from collections import Counter
N="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PR="{http://schemas.openxmlformats.org/package/2006/relationships}"
SOURCE_SHA="bbc290075fb4d7ff6435988acf1ea83c2c31453d207bfa821609b8e9a86953d0"
HUB=161.368806
def digest(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for x in iter(lambda:f.read(1048576),b""):h.update(x)
 return h.hexdigest()
def norm(s):return re.sub("[^a-z0-9]","",str(s).lower())
def idx(ref):
 n=0
 for c in re.match("[A-Z]+",ref or "A").group():n=n*26+ord(c)-64
 return n-1
def xrows(z,path,ss):
 with z.open(path) as f:
  it=X.iterparse(f,events=("start","end"));_,root=next(it)
  for event,row in it:
   if event!="end" or row.tag!=N+"row":continue
   d={}
   for c in row.iter(N+"c"):
    v=c.find(N+"v");t=c.attrib.get("t","")
    if t=="inlineStr":a="".join(e.text or "" for e in c.iter(N+"t"))
    elif v is None or v.text is None:continue
    elif t=="s":a=ss[int(v.text)]
    elif t in ("str","e"):a=v.text
    else:
     try:a=float(v.text)
     except ValueError:a=v.text
    d[idx(c.attrib.get("r"))]=a
   yield int(row.attrib.get("r","0")),d
   root.clear()
def sheet_paths(z):
 w=X.fromstring(z.read("xl/workbook.xml"));r=X.fromstring(z.read("xl/_rels/workbook.xml.rels"))
 rel={}
 for e in r:
  if e.tag==PR+"Relationship":
   t=e.attrib["Target"].lstrip("/")
   rel[e.attrib["Id"]]=t if t.startswith("xl/") else "xl/"+t
 return [(e.attrib.get("name",""),rel[e.attrib[R+"id"]]) for e in w.iter(N+"sheet") if e.attrib.get(R+"id") in rel]
def strings(z):
 if "xl/sharedStrings.xml" not in z.namelist():return []
 a=[]
 with z.open("xl/sharedStrings.xml") as f:
  for _,e in X.iterparse(f,events=("end",)):
   if e.tag==N+"si":a.append("".join(t.text or "" for t in e.iter(N+"t")));e.clear()
 return a
def columns(h):
 a={norm(v):k for k,v in h.items()}
 def get(*names):
  for s in names:
   if norm(s) in a:return a[norm(s)]
  return None
 c={}
 c["hub"]=get("U_hub","Uhub","HubHtSpeed","hub_speed","hubwindspeed","wind_speed_hub","U161","WS161","Uhub_mps","hub_height_speed")
 c["u10"]=get("u10","u10m","u10_component")
 c["v10"]=get("v10","v10m","v10_component")
 c["u100"]=get("u100","u100m","u100_component")
 c["v100"]=get("v100","v100m","v100_component")
 c["s10"]=get("ws10","wind_speed_10m","windspeed10","speed10","U10_speed","Wind10m")
 c["s100"]=get("ws100","wind_speed_100m","windspeed100","speed100","U100_speed","Wind100m")
 c["time"]=get("time","datetime","valid_time","timestamp","date","utc_time","日期时间","时间")
 c["mode"]="vector" if all(c[k] is not None for k in ("u10","v10","u100","v100")) else "speed" if c["s10"] is not None and c["s100"] is not None else "u_labels" if c["u10"] is not None and c["u100"] is not None and c["v10"] is None and c["v100"] is None else None
 c["score"]=(100 if c["hub"] is not None else 0)+(75 if c["mode"] else 0)+(5 if c["time"] is not None else 0)
 return c
def gettime(v):
 if isinstance(v,(float,int)):return D.datetime(1899,12,30)+D.timedelta(days=v) if 20000<v<70000 else None
 try:return D.datetime.fromisoformat(str(v).replace("Z","+00:00")).replace(tzinfo=None)
 except ValueError:return None
def hubcalc(a,b):
 if not all(math.isfinite(v) and v>=0 for v in (a,b)):raise ValueError("BAD_WIND_MAGNITUDE")
 if a==0 or b==0:return b,True
 return b*(HUB/100)**(math.log(b/a)/math.log(10)),False
def tests():
 assert idx("AA1")==26 and norm("Wind Speed 10m")=="windspeed10m"
 assert gettime("2005-01-01 00:00:00")==D.datetime(2005,1,1)
 assert gettime(38353)==D.datetime(2005,1,1)
 assert abs(hubcalc(4,5)[0]-5*(HUB/100)**(math.log(1.25)/math.log(10)))<1e-12
 assert hubcalc(0,0.3)==(0.3,True)
 for v in (float("nan"),-1):
  try:hubcalc(v,1);raise AssertionError("BAD_ACCEPTED")
  except ValueError:pass
 print("S10_ERA5_SYNTHETIC_KNOWN_ANSWER_NEGATIVE_PASS")
def main():
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--source");p.add_argument("--out");p.add_argument("--receipt");a=p.parse_args()
 if a.self_test:tests();return
 if not all((a.source,a.out,a.receipt)):p.error("source/out/receipt required")
 src=pathlib.Path(a.source);out=pathlib.Path(a.out);rec=pathlib.Path(a.receipt);rec.parent.mkdir(parents=True,exist_ok=True)
 q={"stage":"S10 independent source-only","source":str(src),"source_sha256_expected":SOURCE_SHA,"script_sha256":digest(__file__),"source_reading_level":"complete original LFS-derived XLSX bytes if accessible","software":"Python3 stdlib streaming OOXML, cached numeric cells only","official":"historical ERA5-derived workbook; NOT original ERA5 GRIB or site mast","ref":"REF080/REF083/REF090 historical; no new full text","standard":"no newly read authorized IEC/GB clauses","run":"no OpenFAST/Abaqus/earthquake production","fig":"none","tab":"31 wind-bin rows on success","assumptions":"hub=161.368806m; hourly dynamic two-height power law; zero speed fallback U100 with alpha=0 flagged; [4,25) diagnostic operating range; 8760 standard annual hours","physics_status":"HOLD"}
 try:
  if not src.exists():raise ValueError("LFS_SOURCE_MISSING")
  q["source_bytes"]=src.stat().st_size;q["source_sha256_actual"]=digest(src)
  if q["source_bytes"]!=31793340 or q["source_sha256_actual"]!=SOURCE_SHA:raise ValueError("LFS_SHA_OR_SIZE_MISMATCH")
  with zipfile.ZipFile(src) as z:
   ss=strings(z);opts=[];samples={}
   for name,path in sheet_paths(z):
    top=[]
    for i,(rn,row) in enumerate(xrows(z,path,ss)):
     if i>=12:break
     top.append((rn,row))
    samples[name]=[{"row":rn,"cells":{str(k):str(v)[:65] for k,v in list(row.items())[:20]}} for rn,row in top[:4]]
    for rn,row in top:
     c=columns(row)
     if c["score"]>=75:opts.append((c["score"],name,path,rn,row,c))
   q["sheet_samples"]=samples
   if not opts:raise ValueError("NO_RECOGNIZED_WIND_COLUMN_SCHEMA")
   opts.sort(key=lambda t:t[0],reverse=True)
   _,name,path,header,headers,c=opts[0]
   q.update(sheet=name,header_row=header,headers={str(k):str(v) for k,v in headers.items()},columns=c)
   counts=[0]*31;vals=[];fallback=0;times=0;gaps=0;duplicates=0;badtime=0;prev=None;first=None;last=None;cross=[]
   for rn,row in xrows(z,path,ss):
    if rn<=header or not row:continue
    def num(k):
     if k is None or k not in row:raise ValueError("MISSING_CELL_ROW_"+str(rn))
     x=float(row[k])
     if not math.isfinite(x):raise ValueError("NONFINITE_ROW_"+str(rn))
     return x
    if c["mode"]=="vector":u10=math.hypot(num(c["u10"]),num(c["v10"]));u100=math.hypot(num(c["u100"]),num(c["v100"]))
    elif c["mode"]=="speed":u10=num(c["s10"]);u100=num(c["s100"])
    elif c["mode"]=="u_labels":u10=num(c["u10"]);u100=num(c["u100"])
    else:u10=u100=None
    if c["hub"] is not None:
     hub=num(c["hub"]);fb=False
     if u10 is not None and len(cross)<10000:cross.append(abs(hub-hubcalc(u10,u100)[0]))
    else:hub,fb=hubcalc(u10,u100)
    if fb:fallback+=1
    if not math.isfinite(hub) or not 0<=hub<=120:raise ValueError("HUB_WIND_OUT_OF_RANGE_ROW_"+str(rn))
    vals.append(hub);counts[min(30,int(hub))]+=1
    if c["time"] is not None:
     t=gettime(row.get(c["time"],""))
     if t is None:badtime+=1
     else:
      times+=1
      if first is None:first=t
      if prev is not None:
       d=(t-prev).total_seconds()/3600
       if d==0:duplicates+=1
       elif abs(d-1)>1e-7:gaps+=1
      prev=t;last=t
  q.update(n_hours=len(vals),time_parsed=times,time_unparsed=badtime,time_gaps_or_reverse=gaps,time_duplicates=duplicates,first_utc=str(first),last_utc=str(last),fallback_hours=fallback,hub_dynamic_crosscheck_max_abs_mps=max(cross) if cross else None)
  if len(vals)!=184080:raise ValueError("EXPECTED_184080_HOURS_GOT_"+str(len(vals)))
  if c["time"] is None or badtime or gaps or duplicates or first!=D.datetime(2005,1,1) or last!=D.datetime(2025,12,31,23):raise ValueError("FULL_UTC_TIME_AXIS_NOT_VERIFIED")
  if sum(counts)!=len(vals):raise ValueError("BIN_MASS_NOT_CONSERVED")
  v=sorted(vals);n=len(v)
  def pct(x):
   i=(n-1)*x;j=int(i);return v[j]+(v[min(j+1,n-1)]-v[j])*(i-j)
  op=sum(counts[4:25]);q.update(mean_mps=sum(vals)/n,min_mps=v[0],max_mps=v[-1],p50_mps=pct(.5),p90_mps=pct(.9),p95_mps=pct(.95),p99_mps=pct(.99),operating_hours_4_to_25=op,operating_probability=op/n)
  q["prior_summary_difference_mps"]={"mean":q["mean_mps"]-4.796029,"p95":q["p95_mps"]-9.343881,"max":q["max_mps"]-19.202140}
  out.parent.mkdir(parents=True,exist_ok=True)
  with out.open("w",newline="",encoding="utf-8") as f:
   w=csv.writer(f,lineterminator="\n");w.writerow(["bin_lower_mps","bin_upper_mps_exclusive","hours","p_all_hours","equivalent_annual_hours_8760","p_conditional_4_to_25","cdf_all_hours"])
   acc=0
   for j,x in enumerate(counts):
    acc+=x;w.writerow([j,j+1 if j<30 else "INF",x,f"{x/n:.12f}",f"{8760*x/n:.9f}",f"{x/op:.12f}" if op and 4<=j<25 else "0.000000000000",f"{acc/n:.12f}"])
  q.update(source_numeric_qc="PASS",output_sha256=digest(out),output_rows=31,physics_status="HOLD: ERA5-derived probability only; no verified DLC1.2 or local material Miner")
  print("ERA5_SOURCE_NUMERIC_PASS",json.dumps({k:q[k] for k in ("sheet","n_hours","mean_mps","p95_mps","max_mps","operating_probability","output_sha256")}))
 except Exception as e:
  q["source_numeric_qc"]="HOLD";q["error"]=type(e).__name__+": "+str(e)
  print("ERA5_SOURCE_HOLD",q["error"],json.dumps(q.get("sheet_samples",{}),ensure_ascii=False)[:6500],file=sys.stderr)
  raise
 finally:rec.write_text(json.dumps(q,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
