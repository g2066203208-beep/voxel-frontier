"""Targeted metadata prefilter and acquisition from ESM official flatfile.
All thresholds are research diagnostics; no fabricated target beyond 6 s."""
import concurrent.futures as cf,csv,io,json,math,pathlib,hashlib
import numpy as np
import requests
import acquire_esm as ac
import expand_and_screen as v3
import audit_nine as au
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"replacement_v4";OUT.mkdir(exist_ok=True)
ac.OUT=OUT;ac.PERIODS=au.T.copy()
FIELDS="esm_event_id,event_time,ev_nation_code,mw,fm_type_code,network_code,station_code,location_code,channel_code,sensor_depth_m,proximity,preferred_vs30_m_s,preferred_ec8_code,epi_dist,jb_dist,rup_dist,instrument_type_code,quality_class,processing_type,u_hp,v_hp,u_pga,v_pga,rotD50_pga,rotD50_pgv,u_T90,v_T90,rotD50_T90,u_t4_000,v_t4_000,u_t7_000,v_t7_000,u_t10_000,v_t10_000"
def query(a):
    label,begin,end=a
    params={"starttime":begin,"endtime":end,"min-magnitude":5.5,"min-pga":12,"max-pga":180,"max-epicentral-distance":250,"channel":"HN,HG,HL","instrument-type":"D","processing-type":"MP","quality-class":"BEST,GOOD","late-triggered":"N","include-fields":FIELDS,"spectra":"SA"}
    url="https://esm-db.eu/esmws/flatfile/1/query"
    try:
        r=requests.get(url,params=params,timeout=(10,100));receipt={"label":label,"url":r.url,"http":r.status_code,"sha256":hashlib.sha256(r.content).hexdigest(),"bytes":len(r.content)}
        if not r.ok or not r.content:return receipt,[]
        s=r.content.decode("utf-8-sig");d=csv.Sniffer().sniff(s[:8192],delimiters=";,\t");rows=list(csv.DictReader(io.StringIO(s),dialect=d))
        assert rows and "u_hp" in rows[0] and "esm_event_id" in rows[0],(str(rows[:1])[:500])
        (OUT/(label+"_flatfile.csv")).write_bytes(r.content);receipt["count"]=len(rows);return receipt,rows
    except Exception as e:return {"label":label,"error":str(e)},[]
def fl(x,k):return ac.num(x.get(k),float("nan"))
def main():
    windows=[("1990_2007","1990-01-01","2007-12-31"),("2008_2015","2008-01-01","2015-12-31"),("2016_2020","2016-01-01","2020-12-31"),("2021_2026","2021-01-01","2026-11-24")]
    with cf.ThreadPoolExecutor(max_workers=4) as ex:queries=list(ex.map(query,windows))
    prev=[]
    for d in ("acquired","acquired_v2","replacement_v3"):
        prev+=json.loads((ROOT/d/"acquisition_receipt.json").read_text())["records"]
    tried={(r["event"],r["station"]) for r in prev}
    prevscreen=json.loads((ROOT/"replacement_v3/screen.json").read_text())
    passed={r["event"] for r in prevscreen if r["source_screen_pass"]}
    pool=[]
    for receipt,rows in queries:
        print("FLATFILE",receipt,flush=True)
        for r in rows:
            e,st=r["esm_event_id"],r["station_code"]
            fc=max(fl(r,"u_hp"),fl(r,"v_hp"))
            if (e,st) in tried or not np.isfinite(fc) or fc<=0 or fc>1/30:continue
            if r.get("proximity","").lower().startswith(("inside","close")):continue
            if not 0<=fl(r,"sensor_depth_m")<=1:continue
            pga=max(abs(fl(r,"u_pga")),abs(fl(r,"v_pga")))
            if not np.isfinite(pga) or not 12<=pga<=250:continue
            # prioritize long-duration and strong long-period response, not merely PGA proximity.
            dur=fl(r,"rotD50_T90")
            sa=math.sqrt(abs(fl(r,"u_t7_000")*fl(r,"v_t7_000")))
            if not np.isfinite(sa):sa=0
            r["_score"]=[e in passed,r.get("network_code") not in ("IT","IV","8P"),-min(dur if np.isfinite(dur) else 0,60),-sa/max(pga,1e-6),fc]
            pool.append(r)
    pool.sort(key=lambda r:r["_score"])
    chosen=[];seen=set();counts={}
    # event-balanced selection, preserve all candidate metadata.
    for r in pool:
        e,st=r["esm_event_id"],r["station_code"]
        if (e,st) in seen or counts.get(e,0)>=3:continue
        seen.add((e,st));counts[e]=counts.get(e,0)+1;chosen.append(r)
        if len(chosen)>=30:break
    (OUT/"eligible_metadata.json").write_text(json.dumps(pool,indent=2,ensure_ascii=False)+"\n")
    tasks=[("FLATFILE",r["esm_event_id"],r["network_code"],r["station_code"],r.get("location_code") or None,r.get("channel_code") or None,r) for r in chosen]
    print("PREFILTER",len(pool),"REQUESTS",len(tasks),flush=True)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:got=list(ex.map(ac.acquire,tasks))
    (OUT/"acquisition_receipt.json").write_text(json.dumps({"queries":[q for q,_ in queries],"records":got},indent=2,ensure_ascii=False)+"\n")
    unique={}
    for r in prev+got:
        if r["status"]=="SOURCE_PAIR_ACQUIRED_NOT_DESIGN":unique[(r["event"],r["station"])]=r
    results=[]
    for r in unique.values():
        try:
            s=v3.score(r);a=np.loadtxt(ROOT/r["directory"]/"acceleration_SI.csv",delimiter=",",skiprows=1);t=a[:,0];h=a[:,1:3]
            durations=[]
            for x in h.T:
                ix=np.flatnonzero(abs(x)>=.1*np.max(abs(x)));durations.append(float(t[ix[-1]]-t[ix[0]]))
            s["duration_10pct_components_s"]=durations;s["duration_5T1_pass"]=min(durations)>=5*au.T1
            s["D5_95_pair_s"]=r["D5_95_pair_s"]
            s["priority_pass"]=s["source_screen_pass"] and s["duration_5T1_pass"]
            results.append(s)
        except Exception as e:print("SCORE_ERROR",r["event"],r["station"],str(e),flush=True)
    results.sort(key=lambda x:(not x["priority_pass"],not x["source_screen_pass"],x["short_band_shape_log_rmse"],-x["T1_over_PGA"]))
    (OUT/"screen.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
    print("SUMMARY",len(pool),len(got),sum(r["status"]=="SOURCE_PAIR_ACQUIRED_NOT_DESIGN" for r in got),len(results),sum(r["source_screen_pass"] for r in results),sum(r["priority_pass"] for r in results),flush=True)
if __name__=="__main__":main()
