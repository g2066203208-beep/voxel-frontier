"""R56 portable single-INP generator; Python standard library only.
No Abaqus solver invocation. Retains R44 model and inherited damping.
"""
import argparse,csv,hashlib,json,math,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SHA=lambda b:hashlib.sha256(b).hexdigest()
def check(ok,msg):
    if not ok: raise ValueError(msg)
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def parse_amplitudes(raw):
    result={}
    for block in re.split(rb"(?mi)^\*Amplitude,",raw)[1:]:
        h,body=block.split(b"\n",1)
        name=re.search(rb"(?i)\bname=([^,\r\n]+)",h)[1].decode().strip()
        check(name not in result,"duplicate amplitude")
        vals=[float(v) for v in re.split(rb"[\s,]+",body.strip()) if v]
        check(len(vals)%2==0 and all(math.isfinite(v) for v in vals),name)
        result[name]=list(zip(vals[::2],vals[1::2]))
    return result
def serialize(A):
    result=[]
    for n,v in A.items():
        result.append("*Amplitude, name="+n+", time=STEP TIME")
        p=["%.8f, %.15e"%(t,x) for t,x in v]
        result.extend(", ".join(p[i:i+4]) for i in range(0,len(p),4))
    return ("\n".join(result)+"\n").encode("ascii")
def case_matrix():
    m=read(ROOT/"R45_receipt.json")
    return [(None,r["id"]) for r in m["records"]]+[(c,m) for c in ("NTM","1ETM") for m in ("PILOT","FULL")]+[(c,r["id"]) for c in ("NTM","1ETM") for r in m["records"]]
def build(wind,mode):
    r45=read(ROOT/"R45_receipt.json")
    r55=read(ROOT/"R55_receipt.json")
    base=(ROOT/"R44.inp").read_bytes()
    check(SHA(base)==r45["r44_sha256"],"R44 SHA")
    r=next((x for x in r45["records"] if x["id"]==mode),None)
    check((wind is None and r is not None) or (wind in ("NTM","1ETM") and (r is not None or mode in ("PILOT","FULL"))),"unsupported case")
    dur=(30.+r["duration"] if wind else r["duration"]) if r else (20. if mode=="PILOT" else 599.95)
    dt=.005 if r else .025
    name=(wind+"_" if wind else "")+mode
    files={}
    if r:
        p=ROOT/(r["id"]+"_"+r["station"]+"_amplitudes.inc")
        raw=p.read_bytes()
        check(SHA(raw)==r["amplitude_sha256"],"EQ SHA")
        eq=parse_amplitudes(raw)
        check(set(eq)=={"EQ_X_EAST_SI","EQ_Z_MINUS_NORTH_SI"},"EQ names")
        for k,v in eq.items():
            check(len(v)==r["npts"] and max(abs(t-i*r["dt"]) for i,(t,x) in enumerate(v))<1e-8,"EQ grid")
        if wind:
            shifted={k:[(0.,0.),(29.995,0.)]+[(round(t+30.,8),x) for t,x in v] for k,v in eq.items()}
            eqa=serialize(shifted)
            rt=parse_amplitudes(eqa)
            check(all(max(abs(a[1]-b[1]) for a,b in zip(rt[k][2:],v))<=1e-12 for k,v in eq.items()),"EQ value roundtrip")
        else:eqa=raw
    if wind:
        rec=next(x for x in r55["cases"] if x["case"]==wind)
        zp=ROOT/rec["archive"]
        check(SHA(zp.read_bytes())==rec["sha256"],"R55 SHA")
        with zipfile.ZipFile(zp) as z:
            check(z.testzip() is None,"R55 CRC")
            files={k:z.read(k) for k in rec["files"]}
        check(all(SHA(v)==rec["files"][k] for k,v in files.items()),"R55 members")
        key="WIND_RNA_EQ01.inp" if r else "WIND_RNA_"+mode+".inp"
        deck=files[key]
        # Preserve original piecewise linear interpolation, including the next bracketing sample.
        if mode!="FULL":
            source=parse_amplitudes(files["wind_amplitudes.inc"])
            check(len(source)==150,"wind count")
            n=min(12000,math.ceil(dur/.05-1e-9)+1)
            cropped={k:v[:n] for k,v in source.items()}
            check(all(len(v)==n and v[-1][0]+1e-8>=dur for v in cropped.values()),"wind coverage")
            files["wind_amplitudes.inc"]=serialize(cropped)
            got=parse_amplitudes(files["wind_amplitudes.inc"])
            check(all(len(got[k])==n and max(abs(a[0]-b[0]) for a,b in zip(got[k],v))<1e-8 and max(abs(a[1]-b[1]) for a,b in zip(got[k],v))<1e-7 for k,v in cropped.items()),"wind crop roundtrip")
        else:n=12000
        if r:files["eq01_offset_amplitudes.inc"]=eqa
        deck=re.sub(rb"(?mi)^\*Include,\s*input=([^\r\n]+)\r?\n",lambda m:files[m[1].decode().strip()].rstrip()+b"\n",deck)
    else:
        src=(ROOT/"R45_EQ01.inp").read_bytes()
        check(SHA(src)==r45["deck_sha256"],"R45 template")
        step=src[src.index(b"*Step, name=EQ_2H_RAYLEIGH_REL"):]
        deck=base.replace(b"*Material, name=C65",eqa.rstrip()+b"\n*Material, name=C65",1).rstrip()+b"\n"+step
        n=0
    # Modify ONLY the final general dynamic step. Prior topology, material and gravity/modal steps are untouched.
    idx=list(re.finditer(rb"(?mi)^\*Step,",deck))[-1].start()
    head,step=deck[:idx],deck[idx:]
    check(len(re.findall(rb"(?mi)^\*Step,",step))==1 and len(re.findall(rb"(?mi)^\*End Step\s*$",step))==1,"final step")
    step=re.sub(rb"(?mi)^(\*Step,\s*name=)[^,\r\n]+",lambda m:m[1]+name.encode(),step,count=1)
    step=re.sub(rb"(?mi)^(\*Dynamic[^\r\n]*\r?\n)[^\r\n]+",lambda m:m[1]+("%.6g, %.3f, 1.e-7, %.6g"%(dt,dur,dt)).encode(),step,count=1)
    step=re.sub(rb"(?mi)^MODE EQ01 research-scaled horizontal record;[^\r\n]*",("R56 "+name+" diagnostic; inherited provisional damping.").encode(),step)
    step=re.sub(rb"(?mi)^(\*Step,[^\r\n]*\binc=)\d+",lambda m:m[1]+str(2*math.ceil(dur/dt+1e-8)+1000).encode(),step,count=1)
    if mode=="PILOT":
        # Preserve all output variables and history frequency; change only field snapshot counts in final step.
        step=step.replace(b"number interval=80,",b"number interval=10,").replace(b"number interval=10, time marks=NO\n*Element Output, elset=REV04_ALL_REBAR",b"number interval=2, time marks=NO\n*Element Output, elset=REV04_ALL_REBAR")
        check(b"number interval=2, time marks=NO" in step,"pilot rebar output")
    deck=head+step
    check(not re.search(rb"(?mi)^\*Include,",deck),"unresolved include")
    check(len(re.findall(rb"(?mi)^\*Part,",deck))==100 and len(re.findall(rb"(?mi)^\*Instance,",deck))==100 and len(re.findall(rb"(?mi)^\*Contact Pair,",deck))==30,"topology")
    check(len(re.findall(rb"(?mi)^\*Step,",deck))==5,"step count")
    check(len(re.findall(rb"(?mi)^\*Cload,",step))==(150 if wind else 0),"wind loads")
    check(len(re.findall(rb"(?mi)^\*Dload(?:,|$)",step))==(3 if r else 1),"gravity/inertia blocks")
    check(len(re.findall(rb"(?mi)^\*Amplitude,",deck))==((150 if wind else 0)+(2 if r else 0)),"amplitude count")
    check((b"amplitude=EQ_" in step)==bool(r),"EQ load reference")
    check(b"frequency=1" in step and b"*Contact Output" in step,"history preserved")
    return deck,dict(case=name,duration_s=dur,max_increment_s=dt,minimum_increment_count=math.ceil(dur/dt-1e-8),wind_samples=n,eq_samples=r["npts"] if r else 0,bytes=len(deck),sha256=SHA(deck),parts=100,instances=100,contacts=30,wind_cloads=150 if wind else 0,eq_loads=2 if r else 0,output_policy="pilot 10 full-field intervals and 2 rebar intervals; history unchanged" if mode=="PILOT" else "R55/R45 inherited field and history")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--wind",choices=["NTM","1ETM","NONE"],default="NTM")
    p.add_argument("--mode",choices=["PILOT","FULL"]+["EQ%02d"%i for i in range(1,8)],default="PILOT")
    p.add_argument("--out",default=".")
    a=p.parse_args();deck,rec=build(None if a.wind=="NONE" else a.wind,a.mode)
    out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
    dst=out/("HE_R56_"+rec["case"]+".inp")
    dst.write_bytes(deck)
    print(json.dumps(rec,indent=2));print(dst)
if __name__=="__main__":main()
