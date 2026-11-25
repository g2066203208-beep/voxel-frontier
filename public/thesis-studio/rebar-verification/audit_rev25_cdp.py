"""Source-locked preflight: no model edit, no Abaqus run. Run from repository root."""
from pathlib import Path
import csv, hashlib, json, re, sys
ROOT=Path("public/thesis-studio/inp-archive")
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
curve=ROOT/"REV22_REVIEW/rev22-cdp-curves.csv"
rev=ROOT/"REV25_HOOP_COST/HE_REV25_HOOP_COST_EQ005.inp"
assert SHA(curve)=="313f64f2662faebb355605538330f036274da1a404f9611e51451018d6d66e9c"
assert SHA(rev)=="b76fd0f8964f07e110fb1653ab75a75dc45c047ceb58cb84afeac11b52c40193"
# An optional local exported deck can be compared without claiming it is REV25.
target=Path(sys.argv[1]) if len(sys.argv)>1 else rev
data=list(csv.DictReader(curve.open()))
mats={}; mat=None; card=None
wanted={"*ELASTIC","*CONCRETE COMPRESSION HARDENING","*CONCRETE COMPRESSION DAMAGE","*CONCRETE TENSION STIFFENING","*CONCRETE TENSION DAMAGE"}
for ln in target.read_text(encoding="utf-8-sig").splitlines():
    s=ln.strip()
    if not s or s.startswith("**"): continue
    if s.startswith("*"):
        card=s.split(",")[0].upper()
        if card=="*MATERIAL":
            m=re.search(r"(?:^|,)\s*name\s*=\s*([^,]+)",s,re.I)
            mat=m.group(1).strip().upper() if m else None
        if mat in ("C65","C70") and card in wanted:
            assert card not in mats.setdefault(mat,{}), (mat,card,"duplicate")
            mats[mat][card]=[]
    elif mat in mats and card in mats[mat]:
        mats[mat][card].append([float(x) for x in s.split(",") if x.strip()])
results=[]; failures=[]
for m,E in (("C65",36500.),("C70",37000.)):
    for b,sc,dc in (("compression","*CONCRETE COMPRESSION HARDENING","*CONCRETE COMPRESSION DAMAGE"),("tension","*CONCRETE TENSION STIFFENING","*CONCRETE TENSION DAMAGE")):
        a=[r for r in data if r["material"]==m and r["branch"]==b]
        stress=[float(r["stress_MPa"]) for r in a]; e=[float(r["inelastic_or_cracking_strain"]) for r in a]; d=[float(r["damage"]) for r in a]
        pl=[x-y/(1-y)*z/E for x,y,z in zip(e,d,stress)]
        assert len(a)==(26 if b=="compression" else 24)
        assert min(pl)>=0 and all(v>u for u,v in zip(pl,pl[1:]))
        assert all(0<=x<1 for x in d) and all(v>=u for u,v in zip(d,d[1:]))
        c=mats.get(m,{}); errs=[]
        if not c.get("*ELASTIC") or abs(c["*ELASTIC"][0][0]/1e6-E)>1e-7: errs.append("elastic_mismatch")
        for k,exp in ((sc,[(s*1e6,x) for s,x in zip(stress,e)]),(dc,list(zip(d,e)))):
            got=c.get(k,[])
            if len(got)!=len(exp): errs.append(k+":point_count="+str(len(got)))
            elif any(len(g)!=2 or any(abs(v-w)>max(1e-12,abs(w)*1e-10) for v,w in zip(g,p)) for g,p in zip(got,exp)): errs.append(k+":values_mismatch")
        failures.extend([m+"/"+b+"/"+x for x in errs])
        results.append(dict(material=m,branch=b,points=len(a),min_pl=min(pl),min_increment=min(v-u for u,v in zip(pl,pl[1:])),last_pl=pl[-1],deck_match=not errs,errors=errs))
report=dict(scope="static CDP comparison only",target=str(target),target_sha256=SHA(target),results=results,failures=failures,native="NOT_RUN")
print(json.dumps(report,indent=2))
sys.exit(bool(failures))
