"""Acquire untried distinct events, correct lowercase ESM T90 fields, preserve actual records."""
import pathlib,json,concurrent.futures as cf,math
import numpy as np
import acquire_esm as ac
import expand_and_screen as v3
import audit_nine as au
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"replacement_v5";OUT.mkdir(exist_ok=True)
ac.OUT=OUT;ac.PERIODS=au.T.copy()
prev=[]
for d in ("acquired","acquired_v2","replacement_v3","replacement_v4"):
    prev+=json.loads((ROOT/d/"acquisition_receipt.json").read_text())["records"]
tried={(r["event"],r["station"]) for r in prev}
old=json.loads((ROOT/"replacement_v4/screen.json").read_text())
priority={r["event"] for r in old if r["priority_pass"]}
rows=json.loads((ROOT/"replacement_v4/eligible_metadata.json").read_text())
def val(r,k,default=0):
    x=ac.num(r.get(k),default)
    return x if math.isfinite(x) else default
def rank(r):
    d=min(val(r,"u_t90"),val(r,"v_t90"))
    sa=math.sqrt(abs(val(r,"u_t7_000")*val(r,"v_t7_000")))*.01
    return (-min(d,50),abs(math.log(max(sa,1e-8)/.0515023746765)),max(val(r,"u_hp"),val(r,"v_hp")))
groups={}
for r in rows:
    e,s=r["esm_event_id"],r["station_code"]
    if (e,s) in tried or e in priority:continue
    groups.setdefault(e,{})[s]=r
for e in groups:groups[e]=sorted(groups[e].values(),key=rank)
# First one candidate per previously non-priority event, then second/third; no duplicate station per event.
keys=sorted(groups,key=lambda e:(rank(groups[e][0]),e))
chosen=[]
for i in range(3):
    for e in keys:
        if i<len(groups[e]):chosen.append(groups[e][i])
        if len(chosen)>=48:break
    if len(chosen)>=48:break
tasks=[("V5",r["esm_event_id"],r["network_code"],r["station_code"],r.get("location_code") or None,r.get("channel_code") or None,r) for r in chosen]
(OUT/"requested_metadata.json").write_text(json.dumps(chosen,indent=2)+"\n")
with cf.ThreadPoolExecutor(max_workers=6) as ex:got=list(ex.map(ac.acquire,tasks))
(OUT/"acquisition_receipt.json").write_text(json.dumps({"records":got},indent=2,ensure_ascii=False)+"\n")
results=list(old);errors=[]
for r in got:
    if r["status"]!="SOURCE_PAIR_ACQUIRED_NOT_DESIGN":continue
    try:
        s=v3.score(r);a=np.loadtxt(ROOT/r["directory"]/"acceleration_SI.csv",delimiter=",",skiprows=1)
        durations=[]
        for x in a[:,1:3].T:
            ix=np.flatnonzero(abs(x)>=.1*np.max(abs(x)));durations.append(float(a[ix[-1],0]-a[ix[0],0]))
        s.update(duration_10pct_components_s=durations,duration_5T1_pass=min(durations)>=5*au.T1,D5_95_pair_s=r["D5_95_pair_s"])
        s["priority_pass"]=s["source_screen_pass"] and s["duration_5T1_pass"];results.append(s)
    except Exception as e:errors.append({"event":r["event"],"station":r["station"],"error":str(e)})
results.sort(key=lambda s:(not s["priority_pass"],not s["source_screen_pass"],s["short_band_shape_log_rmse"]))
(OUT/"screen.json").write_text(json.dumps(results,indent=2)+"\n")
summary={"requests":len(tasks),"new_acquired":sum(r["status"]=="SOURCE_PAIR_ACQUIRED_NOT_DESIGN" for r in got),"total_scored":len(results),"priority_distinct_events":len({s["event"] for s in results if s["priority_pass"]}),"formal_design":0,"errors":errors}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(summary,flush=True)
