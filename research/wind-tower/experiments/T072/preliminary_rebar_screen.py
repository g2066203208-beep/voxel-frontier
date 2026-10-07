"""Fast S06 screening for the next design step.

This intentionally reports a preliminary screening result.  It uses the
NB/T 10907 6.3.1/6.3.2 form already archived in T061, with explicit geometry
assumptions for a hollow circular wall.  It is not the final code design.
"""
import csv, gzip, glob, math, os

ROOT = os.path.dirname(__file__)
geom = {}
with open(os.path.join(ROOT, "T071_input_geometry_31_segments.csv"), encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        geom[r["segment"]] = r

phi = 14.0
s = 80.0
c = 30.0
abar = math.pi * phi * phi / 4.0
fyv = 360.0
fy = 360.0
out = {}
for batch in "ABCD":
    path = glob.glob(os.path.join(ROOT, "extracted", batch, "*_31seg.csv.gz"))[0]
    with gzip.open(path, "rt", newline="") as f:
        for r in csv.DictReader(f):
            g = geom[r["segment"]]
            D = float(g["D_m"]) * 1000
            di = float(g["di_m"]) * 1000
            t = float(g["wall_mm"])
            A = float(g["A_m2"]) * 1e6
            h0 = max(t - c - phi/2 - 25.0/2, 1.0)
            b = t
            ft = 2.14 if r["segment"] in {"CSEG_01", "CSEG_02"} else 2.09
            fc = 31.8 if r["segment"] in {"CSEG_01", "CSEG_02"} else 29.7
            V = float(r["V_kN"])*1000
            M = abs(float(r["M_kNm"]))*1e6
            T = float(r["T_abs_kNm"])*1e6
            N = float(r["N_comp_kN"])*1000
            lam = M/(V*h0) if V else 1e9
            asv = 4*abar
            ast = 2*abar
            vc = 1.75/(lam+1)*ft*b*h0
            vn = 0.07*min(N, 0.3*fc*A)
            vs = fyv*asv/s*h0
            vrd = vc+vn+vs
            ro=D/2-(c+phi/2); ri=di/2+(c+phi/2)
            acor=math.pi*(ro*ro-ri*ri)
            ucor=2*math.pi*(ro+ri)
            wt=2*math.pi/3*((D/2)**3-(di/2)**3)
            beta=max(.5,min(1.0,1.5/(1+0.2*(lam+1)*V*wt/(T*b*h0)))) if T else 1.0
            vrd_t=(1.5-beta)*vc+vs
            xi=s/ucor
            trd=beta*.35*ft*wt+1.2*math.sqrt(max(xi,1e-12))*fy*ast*acor/s
            rec=out.setdefault(r["segment"], {"z":float(r["gage_z_m"]),"max_v":(-1,None),"max_vt":(-1,None),"max_t":(-1,None),"max_v_ratio":(-1,None),"max_t_ratio":(-1,None),"max_comb":(-1,None)})
            vals=[V/vrd, T/trd, V/vrd_t, V/vrd_t+T/trd]
            if vals[0]>rec["max_v_ratio"][0]: rec["max_v_ratio"]=(vals[0],r["time_s"])
            if vals[1]>rec["max_t_ratio"][0]: rec["max_t_ratio"]=(vals[1],r["time_s"])
            if vals[2]>rec["max_v"][0]: rec["max_v"]=(vals[2],r["time_s"])
            if vals[3]>rec["max_comb"][0]: rec["max_comb"]=(vals[3],r["time_s"])
            if T/trd>rec["max_t"][0]: rec["max_t"]=(T/trd,r["time_s"])

path=os.path.join(ROOT,"T072_U09p343881_ETM_S06_PRELIMINARY_REBAR_SCREEN.csv")
with open(path,"w",newline="",encoding="utf-8") as f:
    fields=["segment","gage_z_m","V_over_Vrd_631","V_over_Vrd_632","T_over_Trd","VplusT_screen","time_V_s","time_VT_s","time_T_s"]
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for seg in sorted(out):
        r=out[seg]; w.writerow({"segment":seg,"gage_z_m":r["z"],"V_over_Vrd_631":r["max_v_ratio"][0],"V_over_Vrd_632":r["max_v"][0],"T_over_Trd":r["max_t_ratio"][0],"VplusT_screen":r["max_comb"][0],"time_V_s":r["max_v"][1],"time_VT_s":r["max_comb"][1],"time_T_s":r["max_t"][1]})
print(path)
worst=max(out,key=lambda s:out[s]["max_comb"][0]); print("worst_comb",worst,out[worst])
