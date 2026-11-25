"""R49: independent tower-only wind/earthquake diagnostic decks.
No rotor loads. No native Abaqus verification. All wind data from verified R46/R47.
"""
import csv,hashlib,io,json,re,zipfile
from pathlib import Path
import numpy as np
ROOT=Path("public/thesis-studio")
BASE=ROOT/"inp-archive"
OUT=BASE/"R49_WIND_EQ_DIAGNOSTIC"
R44=BASE/"R44_REBAR_RESEARCH_PRECHECK/HE_R44_REBAR_RESEARCH_PRECHECK.inp"
R45=BASE/"R45_EQ_RESEARCH_CANDIDATE"
R46=BASE/"R46_WIND_MAPPING"
R47=BASE/"R47_RNA_WIND_GATE"
RAMP=10.; OFFSET=30.; PILOT=20.
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(ok,msg):
    if not ok:raise ValueError(msg)
def steps(s):return re.findall(r"(?mi)^\*Step,\s*name=([^,\r\n]+)",s)
def amps(s):
    out={};key=None;rows=[]
    for line in s.splitlines():
        if line.startswith("**"):continue
        if line.startswith("*"):
            if key:out[key]=np.fromstring(",".join(rows),sep=",").reshape(-1,2)
            key=re.search(r"name=([^,]+)",line,re.I).group(1);rows=[]
        elif line.strip():rows.append(line)
    if key:out[key]=np.fromstring(",".join(rows),sep=",").reshape(-1,2)
    return out
def serialize(data):
    out=[]
    for k,v in data.items():
        out.append("*Amplitude, name="+k+", time=STEP TIME")
        pairs=["%.8f, %.15e"%(t,x) for t,x in v]
        out.extend(", ".join(pairs[i:i+4]) for i in range(0,len(pairs),4))
    text="\n".join(out)+"\n";d=amps(text)
    check(set(d)==set(data),"amplitude identity")
    err=max(float(np.max(np.abs(d[k]-v))) for k,v in data.items())
    check(err<=1e-7,"serialization")
    return text,err
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    base=R44.read_bytes()
    check(sha(base)=="97438ac785f5d6ccb9a6b0737cd7115d6b7de6ae47c111d62bb7912b4908fa58","R44 SHA")
    s=base.decode("ascii");pre=steps(s)
    check(pre==["PT_BALANCE","Gravity","GRAVITY_CHECK","MODAL_30"],"prestep order")
    check(len(re.findall(r"(?mi)^\*End Assembly\s*$",s))==1,"assembly marker")
    check(s.count("*Material, name=C65")==1,"material marker")
    r45=json.loads((R45/"receipt.json").read_text());eqraw=(R45/r45["deck"]).read_bytes()
    check(sha(eqraw)==r45["deck_sha256"],"R45 SHA")
    eqtext=eqraw.decode("ascii")
    match=re.search(r"(?mi)^\*Step,\s*name=EQ_2H_RAYLEIGH_REL(?:,|$)",eqtext)
    check(match is not None,"R45 step")
    step=eqtext[match.start():].strip()+"\n"
    check(len(steps(step))==1 and len(re.findall(r"(?mi)^\*End Step\s*$",step))==1,"R45 closure")
    dtline="0.005, 199.995, 1.e-7, 0.005"
    check(step.count(dtline)==1,"dynamic line")
    # Preserve all boundary, gravity and output settings in existing diagnostic step.
    lines=step.splitlines(keepends=True)
    gravity=[];eqblocks=[];i=0
    while i<len(lines):
        if re.match(r"(?i)^\*Dload(?:,|$)",lines[i]):
            j=i+1
            while j<len(lines) and not lines[j].startswith("*"):j+=1
            block="".join(lines[i:j])
            if "amplitude=EQ_" in block: eqblocks.append(block)
            else:gravity.append(block)
            i=j
        else:i+=1
    check(len(gravity)==1 and len(eqblocks)==2 and "GRAV, 9.81, 0., -1., 0." in gravity[0],"gravity and inertia ownership")
    check(not re.search(r"(?mi)^\*(?:Cload|Dsload)\b",step),"unexpected source external load")
    # All DLOAD records use identical OP=NEW when reset is requested; preserve source definition otherwise.
    ops=[re.search(r"(?i)\bop\s*=\s*(\w+)",b.splitlines()[0]) for b in gravity+eqblocks]
    check(not any(o and o[1].upper()=="NEW" for o in ops) or all(o and o[1].upper()=="NEW" for o in ops),"DLOAD inconsistent OP")
    eq01=r45["records"][0];check(eq01["id"]=="EQ01" and eq01["duration"]==199.995,"EQ01 identity")
    raw=(R45/("EQ01_"+eq01["station"]+"_amplitudes.inc")).read_bytes()
    check(sha(raw)==eq01["amplitude_sha256"],"EQ01 amp SHA")
    eq=amps(raw.decode("ascii"));check(set(eq)=={"EQ_X_EAST_SI","EQ_Z_MINUS_NORTH_SI"},"EQ identity")
    # Offset exact waveform; zero before event. No resampling or multiplier.
    shifted={}
    for k,v in eq.items():
        check(v.shape==(40000,2) and np.max(np.abs(v[:,0]-np.arange(40000)*.005))<=1e-8,"EQ time")
        shifted[k]=np.vstack(([0.,0.],[OFFSET-.005,0.],v+np.array([OFFSET,0.])))
        check(np.array_equal(shifted[k][2:,1],v[:,1]),"EQ waveform preservation")
    eqamp,eqerr=serialize(shifted)
    r46=json.loads((R46/"receipt.json").read_text());r47=json.loads((R47/"tower_alignment_receipt.json").read_text())
    check(r47["status"]=="SHAFT_ALIGNED_TOWER_CLOAD_STATIC_PASS","axis gate")
    cload=(R47/r47["file"]).read_bytes();check(sha(cload)==r47["sha256"],"CLOAD sha")
    cs=cload.decode("ascii")
    check(len(re.findall(r"(?mi)^\*Cload,",cs))==144,"wind load count")
    # Use explicit consistent reset of CLOAD, independent from DLOAD gravity.
    cs=re.sub(r"(?mi)^\*Cload,", "*Cload, op=NEW,",cs)
    results=[]
    for rec in r46["cases"]:
        b=(R46/rec["archive"]).read_bytes();check(sha(b)==rec["sha256"],"R46 ZIP sha")
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            check(z.testzip() is None,"ZIP CRC")
            files={k:z.read(k) for k in rec["members"]}
        check(all(sha(v)==rec["members"][k] for k,v in files.items()),"R46 members")
        wind=amps(files["amplitudes.inc"].decode())
        check(len(wind)==144,"wind amp count")
        ramped={};unchanged=0;first=0.
        for k,v in wind.items():
            t=v[:,0];check(v.shape==(12000,2) and np.max(np.abs(t-np.arange(12000)*.05))<1e-8,"wind time")
            a=np.clip(t/RAMP,0,1);r=a*a*(3-2*a)
            vv=np.column_stack((t,v[:,1]*r))
            unchanged=max(unchanged,float(np.max(np.abs(vv[t>=RAMP,1]-v[t>=RAMP,1]))))
            first=max(first,abs(vv[0,1]));ramped[k]=vv
        check(unchanged==0 and first==0,"wind ramp unchanged after 10s")
        wt,werr=serialize(ramped)
        # Verify load references and wind force conservation after ramp on actual nodes.
        maprows=list(csv.DictReader(io.StringIO(files["node_map.csv"].decode())))
        sets={}
        for row in maprows:sets.setdefault(row["assembly_set"],[]).append(row)
        check(len(sets)==72,"sets")
        F=np.zeros((12000,3));M=np.zeros_like(F);c=cs.splitlines()
        for header,row in zip(c[::2],c[1::2]):
            an=re.search(r"amplitude=([^,]+)",header,re.I).group(1)
            ns,do,mag=row.split(",");ns=ns.strip();do=int(do);mag=float(mag)
            xyz=np.array([[float(r[k]) for k in ["X_m","Y_m","Z_m"]] for r in sets[ns]])
            f=np.zeros_like(F);f[:,do-1]=ramped[an][:,1]*mag*len(xyz)
            F+=f;M+=np.cross(xyz.mean(axis=0),f)
        rawcsv=(ROOT/"wind-figures/tower-drag/timeseries"/("native-full-11.4-"+rec["case"]+"_resultant.csv")).read_bytes()
        alignment=next(x for x in r47["cases"] if x["case"]==rec["case"])
        check(sha(rawcsv)==alignment["source_resultant_sha256"],"source resultant")
        arr=np.loadtxt(io.BytesIO(rawcsv),delimiter=",",skiprows=1)
        rr=np.clip((arr[:,0]-100)/RAMP,0,1);rr=rr*rr*(3-2*rr)
        tf=np.column_stack((arr[:,2],np.zeros(len(arr)),arr[:,1]))*rr[:,None]
        tm=np.column_stack((arr[:,3],np.zeros(len(arr)),-arr[:,4]))*rr[:,None]
        fe=float(np.max(np.abs(F-tf)));me=float(np.max(np.abs(M-tm)))
        check(fe<1e-5 and me<.1,"ramped force and moment conservation")
        # Three separate entry INPs. No sequential loading of independent cases.
        def build(mode,duration,dt,with_eq):
            model=s.replace("*End Assembly","*Include, input=assembly_sets.inc\n*End Assembly",1)
            marker="*Material, name=C65"
            model=model.replace(marker,"*Include, input=wind_amplitudes.inc\n"+("*Include, input=eq01_offset_amplitudes.inc\n" if with_eq else "")+marker,1)
            dyn=step.replace("name=EQ_2H_RAYLEIGH_REL","name="+mode,1).replace(dtline,"%.6g, %.3f, 1.e-7, %.6g"%(dt,duration,dt),1)
            if not with_eq:
                for block in eqblocks:dyn=dyn.replace(block,"",1)
            # Insert concentrated external loads after all DLOADs, before subsequent output cards.
            anchor=gravity[0] if not with_eq else eqblocks[-1]
            check(dyn.count(anchor)==1,"wind insertion anchor")
            dyn=dyn.replace(anchor,anchor+"*Include, input=cload_aligned.inc\n",1)
            # Raise increment cap only if necessary, no other solver controls altered.
            m=re.search(r"(?mi)^(\*Step,[^\n]*\binc\s*=\s*)(\d+)",dyn)
            if m and int(m[2])<int(np.ceil(duration/dt))*2:dyn=dyn[:m.start(2)]+str(int(np.ceil(duration/dt))*2)+dyn[m.end(2):]
            output=model.rstrip()+"\n** R49 DIAGNOSTIC: TOWER ONLY; rotor absent; inherited damping not calibrated.\n"+dyn
            check(steps(output)==pre+[mode],"step identity")
            check(len(re.findall(r"(?mi)^\*Part,",output))==100 and len(re.findall(r"(?mi)^\*Contact Pair,",output))==30,"topology")
            check(len(re.findall(r"(?mi)^\*Dload,",dyn))+(len(re.findall(r"(?mi)^\*Dload\s*$",dyn)))==(3 if with_eq else 1),"DLOAD count")
            check(("amplitude=EQ_" in dyn)==with_eq,"EQ load presence")
            check(output.count("*Include, input=cload_aligned.inc")==1,"cload include")
            return output
        members={"assembly_sets.inc":files["assembly_sets.inc"],"wind_amplitudes.inc":wt.encode("ascii"),"cload_aligned.inc":cs.encode("ascii"),"eq01_offset_amplitudes.inc":eqamp.encode("ascii"),"node_map.csv":files["node_map.csv"]}
        modes=[("WIND_TOWER_PILOT",PILOT,.025,False),("WIND_TOWER_FULL",599.95,.025,False),("WIND_TOWER_EQ01",OFFSET+199.995,.005,True)]
        for mode,duration,dt,e in modes:members[mode+".inp"]=build(mode,duration,dt,e).encode("ascii")
        members["README.txt"]=("R49 TOWER-ONLY DIAGNOSTICS. Extract all files in one working directory. Submit only ONE entry INP per job. WIND_TOWER_PILOT: 20 s. WIND_TOWER_FULL: 599.95 s. WIND_TOWER_EQ01: earthquake begins at wind elapsed 30 s (research sensitivity assumption), duration 229.995 s. Wind source starts at 100 s, smooth cubic ramp 0-10 s, unchanged thereafter. EQ01 exact 40000 points shifted 30 s, zero before event; original initial value reached over 0.005 s. Rotor loads absent, inherited damping uncalibrated, no native check. All are diagnostics not production load combinations. Wind axis +Z is a chosen aligned research direction, EQ geographical axes unchanged. Do not interpret as code design or full wind-earthquake load. No Abaqus run.").encode("ascii")
        zp=OUT/("R49_"+rec["case"]+"_TOWER_ONLY_DIAGNOSTICS.zip")
        with zipfile.ZipFile(zp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for k,v in members.items():z.writestr(k,v)
        with zipfile.ZipFile(zp) as z:
            check(z.testzip() is None and all(z.read(k)==v for k,v in members.items()),"archive readback")
            for k in [x[0]+".inp" for x in modes]:
                refs=re.findall(rb"(?mi)^\*Include,\s*input=([^\r\n]+)",z.read(k))
                check(all(x.decode() in members for x in refs),"include reference")
        results.append(dict(case=rec["case"],archive=zp.name,bytes=zp.stat().st_size,sha256=sha(zp.read_bytes()),files={k:sha(v) for k,v in members.items()},max_wind_force_error_N=fe,max_wind_moment_error_Nm=me,post_ramp_source_difference_N=unchanged,amplitude_serialization_error=werr,eq_serialization_error=eqerr,entry_decks=[dict(name=m+".inp",duration_s=t,max_increment_s=d,minimum_increment_count=int(np.ceil(t/d)),EQ=e) for m,t,d,e in modes]))
        print(json.dumps(results[-1]),flush=True)
    receipt=dict(status="TOWER_ONLY_WIND_EQ_DIAGNOSTIC_STATIC_PASS",native="NOT_RUN",production="HOLD",R44_sha256=sha(base),R45_sha256=sha(eqraw),wind_ramp_s=RAMP,eq_offset_s=OFFSET,eq_source_points=40000,eq_initial_values={k:float(v[0,1]) for k,v in eq.items()},cases=results,limitations=["No rotor wind load or final physical wind-earthquake input.","Ramp and 30 s onset are explicitly chosen diagnostic assumptions, not code combination or probability model.","Inherited material damping uncalibrated; source output controls preserved; estimated increments are lower bounds, not measured runtime.","Abaqus Data Check and native reaction coverage not run."])
    (OUT/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
if __name__=="__main__":main()
