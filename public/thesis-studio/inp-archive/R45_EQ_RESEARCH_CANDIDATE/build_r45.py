"""R44 + frozen V7 earthquake research candidate; no native Abaqus run.
Run from repository root. By default only EQ01 full deck is emitted.
All seven source archives and all rotated histories are independently audited.
Inherited damping is NOT calibrated; do not use as production input.
"""
import argparse, csv, hashlib, io, json, math, re, zipfile
from pathlib import Path

ROOT=Path("public/thesis-studio")
BASE=ROOT/"inp-archive"
V7=ROOT/"seismic-archive/v7"
OUT=BASE/"R45_EQ_RESEARCH_CANDIDATE"
R44=BASE/"R44_REBAR_RESEARCH_PRECHECK/HE_R44_REBAR_RESEARCH_PRECHECK.inp"
REV25=BASE/"REV25_HOOP_COST/HE_REV25_HOOP_COST_EQ005.inp"
R44_BLOB="a31b591c5d7abd900011a3188c67557c52d1b963"
REV25_SHA="b76fd0f8964f07e110fb1653ab75a75dc45c047ceb58cb84afeac11b52c40193"
XNAME="EQ_X_EAST_SI"
ZNAME="EQ_Z_MINUS_NORTH_SI"
EQSTEP="EQ_2H_RAYLEIGH_REL"
PRE_STEPS=["PT_BALANCE","Gravity","GRAVITY_CHECK","MODAL_30"]
sha=lambda b: hashlib.sha256(b).hexdigest()
blob=lambda b: hashlib.sha1(("blob %d\0"%len(b)).encode()+b).hexdigest()

def require(ok,message):
    if not ok: raise ValueError(message)

def azimuth(label):
    label=label.upper()
    if label in {"N","E","S","W"}: return {"N":0,"E":90,"S":180,"W":270}[label]
    m=re.fullmatch(r"([NS])(\d{1,2})([EW])",label)
    require(m is not None,"Unknown direction "+label)
    pole,angle,side=m.groups(); a=int(angle)
    require(a<=90,"Invalid azimuth "+label)
    return ((a if side=="E" else -a) if pole=="N" else (180-a if side=="E" else 180+a))%360

def direction(a):
    # Exact cardinal directions avoid floating point leakage.
    if a%90==0: return {0:(0,1),90:(1,0),180:(0,-1),270:(-1,0)}[a%360]
    t=math.radians(a);return math.sin(t),math.cos(t)

def rotate(h1,h2,a,b):
    e1,n1=direction(a);e2,n2=direction(b)
    return e1*h1+e2*h2,-(n1*h1+n2*h2)

def csv_rows(raw):
    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig")))
    header=next(reader)
    require(len(header)==3 and header[1:]==["H1_m_s2","H2_m_s2"],"Unexpected SI CSV header "+repr(header))
    rows=[tuple(map(float,row)) for row in reader if row]
    require(all(len(r)==3 and all(math.isfinite(v) for v in r) for r in rows),"Invalid CSV data")
    return rows

def amps(name,rows,j):
    result=["*Amplitude, name="+name+", time=STEP TIME"]
    pairs=["%.12g, %.16g"%(r[0],r[j]) for r in rows]
    result.extend(", ".join(pairs[i:i+4]) for i in range(0,len(pairs),4))
    return "\n".join(result)+"\n"

def read_amp(deck,name):
    pat=r"(?mi)^\*Amplitude,[^\n]*\bname\s*=\s*"+re.escape(name)+r"(?:,|\s*$)[^\n]*\n"
    m=re.search(pat,deck)
    require(m is not None,"missing amplitude "+name)
    vals=[]
    for line in deck[m.end():].splitlines():
        if line.startswith("**"):continue
        if line.startswith("*"):break
        vals.extend(float(v) for v in line.split(",") if v.strip())
    require(len(vals)%2==0,"amplitude odd number")
    return list(zip(vals[::2],vals[1::2]))

def stepnames(s):return re.findall(r"(?mi)^\*Step,\s*name=([^,\r\n]+)",s)
def keyword_count(s,k):return len(re.findall(r"(?mi)^\*"+re.escape(k)+r"(?:,|\s*$)",s))

def get_step(s):
    m=re.search(r"(?mi)^\*Step,\s*name="+EQSTEP+r"(?:,|$)",s)
    require(m is not None,"REV25 EQ step missing")
    end=re.search(r"(?mi)^\*End Step\s*$",s[m.start():])
    require(end is not None,"REV25 EQ step unclosed")
    return s[m.start():m.start()+end.end()].rstrip()+"\n"

def audit_step(step):
    require(keyword_count(step,"Step")==keyword_count(step,"End Step")==1,"step closure")
    require(keyword_count(step,"Dynamic")==1 and keyword_count(step,"Dload")==3,"unexpected load template")
    require(", GRAV, 9.81, 0., -1., 0." in step,"gravity missing")
    require(", GRAV, 1., -1., 0., 0." in step and ", GRAV, 1., 0., 0., -1." in step,"inertial direction missing")
    require("CSEG_01-1.FACE_BOTTOM" in step and "PT_36x15p2-1.SET_PT_BOTTOM_GEOM" in step,"boundary missing")
    require(step.count("amplitude="+XNAME)==1 and step.count("amplitude="+ZNAME)==1,"amplitude references")
    require(not re.search(r"(?mi)^\*(?:Cload|Dsload|Include)\b",step),"unexpected load type")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case",default="EQ01",choices=["EQ%02d"%i for i in range(1,8)])
    args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    pre=R44.read_bytes(); parent=REV25.read_bytes()
    require(len(pre)==8256811 and blob(pre)==R44_BLOB,"R44 original blob mismatch")
    require(len(parent)==16192219 and sha(parent)==REV25_SHA,"REV25 original SHA256 mismatch")
    deck=pre.decode("ascii"); old=parent.decode("ascii")
    require(stepnames(deck)==PRE_STEPS and keyword_count(deck,"Amplitude")==0,"R44 not frozen precheck")
    require(keyword_count(deck,"Part")==keyword_count(deck,"End Part")==100,"part closure")
    require(keyword_count(deck,"Instance")==keyword_count(deck,"End Instance")==100,"instance closure")
    require(keyword_count(deck,"Contact Pair")==30,"contact pair count")
    require(keyword_count(deck,"End Step")==4 and [l.strip().lower() for l in deck.splitlines() if l.strip() and not l.lstrip().startswith("**")][-1]=="*end step","precheck not closed")
    template=get_step(old);audit_step(template)
    # An existing load template is copied without changing OP=NEW or gravity.
    dtline="0.005, 199.995, 1.e-7, 0.005"
    require(template.count(dtline)==1,"source dynamic increment line mismatch")
    for setref in ["FACE_BOTTOM","SET_PT_BOTTOM_GEOM"]:
        require(re.search(r"(?mi)^\*(?:Nset|Elset|Surface),[^\n]*\b(?:nset|elset|name)\s*=\s*"+setref+r"(?:,|\s*$)",deck) is not None,"boundary set not found "+setref)
    # Only insert amplitude declarations before first material and append one dynamic step.
    marker="*Material, name=C65"
    require(deck.count(marker)==1,"material insert marker")
    man=json.loads((V7/"manifest.json").read_text())
    summ=json.loads((V7/"summary.json").read_text())
    require(sha((V7/"summary.json").read_bytes())==man["summary.json"]["sha256"],"summary hash")
    rowsout={};receipts=[]
    require(len(summ["selected"])==7,"frozen wave count")
    for spec in summ["selected"]:
        ident=spec["id"]; filename=ident+"_"+spec["station"]+".zip"
        raw=(V7/filename).read_bytes()
        require(len(raw)==man[filename]["bytes"] and sha(raw)==man[filename]["sha256"],"archive hash "+filename)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            require(z.testzip() is None,"ZIP CRC "+filename)
            members={}
            for name in z.namelist():
                if name.endswith("/"):continue
                key=Path(name).name
                require(key not in members,"duplicate basename "+filename)
                members[key]=z.read(name)
        for k,h in spec["files"].items():
            require(k in members and sha(members[k])==h,"member SHA "+filename+"/"+k)
        source=csv_rows(members["original_horizontal_SI.csv"])
        scaled=csv_rows(members["scaled_reference_SI.csv"])
        n=spec["npts"];dt=spec["dt"];scale=spec["scale"]
        require(len(source)==len(scaled)==n and dt==.005,"point count "+ident)
        terr=max(max(abs(s[0]-i*dt),abs(o[0]-i*dt)) for i,(o,s) in enumerate(zip(source,scaled)))
        scaleerr=max(abs(s[j]-o[j]*scale) for o,s in zip(source,scaled) for j in (1,2))
        require(terr<=1e-8 and abs(scaled[-1][0]-spec["record_duration"])<=1e-8,"time axis "+ident)
        require(scaleerr<=1e-7,"source scale mismatch "+ident)
        pga=max(abs(r[j]) for r in scaled for j in (1,2))
        require(abs(pga-spec["scaled_pga"])<=1e-7,"PGA mismatch "+ident)
        a,b=map(azimuth,spec["dirs"])
        require((a-b)%180==90,"nonorthogonal components "+ident)
        rotated=[(t,*rotate(h1,h2,a,b)) for t,h1,h2 in scaled]
        normerr=max(abs(math.hypot(x,z)-math.hypot(h1,h2)) for (_,x,z),(_,h1,h2) in zip(rotated,scaled))
        require(normerr<=1e-12,"rotation invariant "+ident)
        xamp,zamp=amps(XNAME,rotated,1),amps(ZNAME,rotated,2)
        rounderr=0
        for j,name,part in [(1,XNAME,xamp),(2,ZNAME,zamp)]:
            recovered=read_amp(part,name)
            require(len(recovered)==n,"amplitude count "+ident)
            rounderr=max(rounderr,max(max(abs(t-row[0]),abs(v-row[j])) for (t,v),row in zip(recovered,rotated)))
        require(rounderr<=1e-10,"amplitude roundtrip "+ident)
        if ident=="EQ01":
            for j,name in [(1,XNAME),(2,ZNAME)]:
                previous=read_amp(old,name)
                require(len(previous)==n and max(max(abs(t-r[0]),abs(v-r[j])) for (t,v),r in zip(previous,rotated))<=1e-10,"EQ01 mismatch REV25 "+name)
        # Store verified amplitudes, no extra scaling, one file per independent case.
        ampfile=OUT/(ident+"_"+spec["station"]+"_amplitudes.inc")
        ampfile.write_text(xamp+zamp,encoding="ascii")
        rowsout[ident]=(spec,xamp+zamp)
        receipts.append(dict(id=ident,station=spec["station"],directions=spec["dirs"],azimuth_deg=[a,b],npts=n,dt=dt,duration=scaled[-1][0],zip_sha256=sha(raw),member_hash_count=len(spec["files"]),scale_from_source=scale,applied_multiplier=1,pga_components_source=pga,pga_X=max(abs(r[1]) for r in rotated),pga_Z=max(abs(r[2]) for r in rotated),time_max_error=terr,scale_max_error=scaleerr,rotation_norm_max_error=normerr,amplitude_roundtrip_max_error=rounderr,amplitude_sha256=sha(ampfile.read_bytes())))
    require(sum(r["npts"] for r in receipts)==217264,"total frozen samples")
    spec,amptext=rowsout[args.case]
    dyn=template.replace(dtline,"0.005, %.3f, 1.e-7, 0.005"%spec["record_duration"],1)
    audit_step(dyn)
    note="** R45 RESEARCH DIAGNOSTIC ONLY: inherited damping NOT calibrated; native NOT_RUN.\n"
    candidate=deck.replace(marker,amptext+marker,1).rstrip()+"\n"+note+dyn
    require(stepnames(candidate)==PRE_STEPS+[EQSTEP],"five step order")
    require(keyword_count(candidate,"Amplitude")==2,"amplitude count")
    require(candidate.replace(amptext,"",1).split(note,1)[0].rstrip()==deck.rstrip(),"precheck was modified")
    target=OUT/("HE_R45_"+args.case+"_INHERITED_DAMPING_DIAGNOSTIC.inp")
    target.write_text(candidate,encoding="ascii")
    receipt=dict(status="RESEARCH_DIAGNOSTIC_STATIC_ONLY",native="NOT_RUN",production_release="HOLD",r44_blob=blob(pre),r44_sha256=sha(pre),rev25_sha256=sha(parent),case=args.case,deck=target.name,deck_sha256=sha(target.read_bytes()),deck_bytes=target.stat().st_size,steps=stepnames(candidate),parts=100,instances=100,contacts=30,records=receipts,limits=["X east Y up Z minus north: assumed fixed geographic tower orientation as REV22; site orientation not independently surveyed.","Inherited damping not calibrated; use only after native precheck and user approval for diagnostic. No production release.","Existing OP=NEW DLOAD template preserved; native whole-mass inertia/reaction coverage not demonstrated.","No wind step. No native verification, no design acceptance."])
    (OUT/"receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in receipt.items() if k!="records"},indent=2))
if __name__=="__main__":main()
