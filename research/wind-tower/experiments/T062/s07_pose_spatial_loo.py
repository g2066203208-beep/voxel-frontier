"""S07 near-base 9-gage spatial rank and leave-one-gage-out robustness.
Input: historical S07 ZIP containing gzip CSV, SHA-locked; NO physical solver.
Usage: python s07_pose_spatial_loo.py <source.zip> <output.csv>
"""
import sys,zipfile,gzip,io,csv,hashlib
import numpy as np
from pathlib import Path
EXPECTED_GZIP_SHA256="2e113c83990d81b064636dca05308fc72676cb329033b9d603c8807d5cf0ecea"
def evaluate(src,dest):
    with zipfile.ZipFile(src) as z:
        compressed=z.read("S07_18NTM_W_POSE9_FULLRATE_216018ROW.csv.gz")
    if hashlib.sha256(compressed).hexdigest()!=EXPECTED_GZIP_SHA256:
        raise ValueError("source SHA256 mismatch")
    a=np.genfromtxt(io.BytesIO(gzip.decompress(compressed)),delimiter=",",names=True,dtype=None,encoding="utf-8")
    rows=[]
    for case in np.unique(a["case"]):
        s=a[a["case"]==case]
        if len(s)!=12001 or np.max(np.abs(np.diff(s["time_s"])-0.05))>1e-7:
            raise ValueError("time grid mismatch")
        for channel in ("RPxi","RPyi","TPxi","TPyi"):
            X=np.column_stack([s[f"TwHt{k}{channel}"] for k in range(1,10)])
            def metrics(B):
                C=np.corrcoef(B,rowvar=False)
                if not np.isfinite(C).all(): raise ValueError("invalid covariance")
                eig=np.linalg.eigvalsh(C)
                return eig[-1]/eig.sum(),eig.sum()**2/(eig@eig)
            pc,rank=metrics(X)
            loo=np.array([metrics(np.delete(X,k,axis=1)) for k in range(9)])
            rows.append([case,channel,pc,rank,loo[:,0].min(),loo[:,0].max(),loo[:,1].min(),loo[:,1].max()])
    if len(rows)!=72: raise ValueError("expected 18 cases x 4 channels")
    with open(dest,"w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["case","channel","pc1_full9","rank_full9","pc1_loo_min","pc1_loo_max","rank_loo_min","rank_loo_max"])
        w.writerows(rows)
    return rows
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: python s07_pose_spatial_loo.py source.zip output.csv")
    evaluate(Path(sys.argv[1]),Path(sys.argv[2]))
