#!/usr/bin/env python3
"""S10: exact wind-bin cluster sign-flip inference, NOT independent-seed inference."""
import csv, itertools, math, sys
from pathlib import Path
DEFAULT = Path(__file__).with_name("S10_TURBULENCE_CHANNEL_INTERACTION_18ROW_20261111.csv")

def evaluate(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    groups={}
    if len(rows)!=18: raise ValueError("expected 18 observations")
    for r in rows:
        label=r["wind_seed"]
        wind,seed=label.rsplit("_",1)
        if seed not in {f"S{i:02d}" for i in range(1,7)}: raise ValueError("bad seed")
        x=float(r["interaction_pp"])
        if not math.isfinite(x): raise ValueError("nonfinite")
        if abs((float(r["ETM_Mx_minus_My_pp"])-float(r["NTM_Mx_minus_My_pp"]))-x)>2e-9:
            raise ValueError("interaction identity failed")
        if seed in groups.setdefault(wind,{}): raise ValueError("duplicate")
        groups[wind][seed]=x
    if len(groups)!=3 or any(len(v)!=6 for v in groups.values()): raise ValueError("incomplete wind-bin cluster")
    means=[sum(v.values())/6 for _,v in sorted(groups.items())]
    observed=sum(means)/3
    null=[sum(s*x for s,x in zip(signs,means))/3 for signs in itertools.product((-1,1),repeat=3)]
    p=sum(x>=observed-1e-12 for x in null)/len(null)
    loo=[(sum(means)-x)/2 for x in means]
    return means,observed,p,min(loo),max(loo)

def selftest():
    import tempfile
    means,obs,p,lo,hi=evaluate(DEFAULT)
    assert abs(obs-3.755735280888889)<1e-9
    assert p==0.125
    assert abs(lo-3.59060949875)<1e-9
    assert abs(hi-3.90065489975)<1e-9
    with tempfile.TemporaryDirectory() as d:
        pth=Path(d)/"bad.csv"
        text=DEFAULT.read_text(encoding="utf-8")
        for broken in (text.replace("4.455018293","NaN",1),text.replace("4.455018293","99",1),text.replace("U09p343881_S01","U09p343881_S02",1),text.splitlines()[0]+"\n"+"\n".join(text.splitlines()[1:-1])+"\n"):
            pth.write_text(broken,encoding="utf-8")
            try: evaluate(pth)
            except ValueError: pass
            else: raise AssertionError("invalid input accepted")
    print("PASS: 18 source rows, 3 clusters, exact 8 sign flips, 4 rejects")

if __name__=="__main__":
    if "--self-test" in sys.argv: selftest()
    else:
        means,obs,p,lo,hi=evaluate(Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT)
        print(f"bin_means_pp={means}; overall_pp={obs:.9f}; exact_one_sided_p={p:.6f}; LOO_pp=[{lo:.9f},{hi:.9f}]")
