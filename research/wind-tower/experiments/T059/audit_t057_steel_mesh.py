from pathlib import Path
import re, math, json, csv, statistics, hashlib

INP = Path("research/wind-tower/experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp")
OUTDIR = Path("research/wind-tower/experiments/T059")
JSON_OUT = OUTDIR / "T059_STEEL_MESH_AUDIT.json"
CSV_OUT = OUTDIR / "T059_STEEL_ELEMENT_METRICS.csv"
MD_OUT = OUTDIR / "README.md"

EXPECTED_T055 = {"SSEG_01":216, "SSEG_02":432, "SSEG_03":432, "SSEG_04":432}
EDGES = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]

text = INP.read_text(encoding="utf-8", errors="strict")
sha = hashlib.sha256(text.encode()).hexdigest()
OUTDIR.mkdir(parents=True, exist_ok=True)

def parse_part(name):
    m = re.search(rf"(?is)^\*Part,\s*name={re.escape(name)}\s*$([\s\S]*?)^\*End Part\s*$", text, re.M)
    if not m:
        raise RuntimeError(f"Part {name} not found")
    body = m.group(1).splitlines()
    nodes, elems = {}, []
    mode = None
    for line in body:
        s=line.strip()
        if re.match(r"^\*Node\b", s, re.I):
            mode="node"; continue
        if re.match(r"^\*Element,\s*type=C3D8R\b", s, re.I):
            mode="elem"; continue
        if s.startswith("*"):
            mode=None; continue
        if not s or s.startswith("**"):
            continue
        a=[x.strip() for x in line.split(",") if x.strip()]
        if mode=="node" and len(a)>=4 and a[0].isdigit():
            nodes[int(a[0])] = tuple(float(x) for x in a[1:4])
        elif mode=="elem" and len(a)>=9 and a[0].isdigit():
            elems.append((int(a[0]), tuple(int(x) for x in a[1:9])))
    return nodes, elems

def wrap(d):
    while d > math.pi: d -= 2*math.pi
    while d < -math.pi: d += 2*math.pi
    return d

def edge_metrics(p,q):
    x1,y1,z1=p; x2,y2,z2=q
    r1=math.hypot(x1,z1); r2=math.hypot(x2,z2)
    th1=math.atan2(z1,x1); th2=math.atan2(z2,x2)
    dy=abs(y2-y1)
    dr=abs(r2-r1)
    arc=0.5*(r1+r2)*abs(wrap(th2-th1))
    L=math.dist(p,q)
    comps={"axial":dy,"radial":dr,"circumferential":arc}
    kind=max(comps,key=comps.get)
    return L,kind,dy,dr,arc

rows=[]
summary={}
for i in range(1,5):
    name=f"SSEG_{i:02d}"
    nodes, elems=parse_part(name)
    ratios=[]; axial=[]; radial=[]; circum=[]
    for eid,conn in elems:
        ps=[nodes[n] for n in conn]
        em=[]
        for a,b in EDGES:
            L,kind,dy,dr,arc=edge_metrics(ps[a],ps[b])
            em.append((L,kind,dy,dr,arc))
            if kind=="axial" and L>1e-12: axial.append(L)
            elif kind=="radial" and L>1e-12: radial.append(L)
            elif kind=="circumferential" and L>1e-12: circum.append(L)
        lens=[x[0] for x in em if x[0]>1e-12]
        mn=min(lens); mx=max(lens); ratio=mx/mn
        ratios.append(ratio)
        dims={k:[x[0] for x in em if x[1]==k] for k in ("axial","radial","circumferential")}
        av=lambda xs: sum(xs)/len(xs) if xs else float("nan")
        rows.append({
            "part":name,"element":eid,"edge_ratio":ratio,"min_edge_m":mn,"max_edge_m":mx,
            "axial_edge_mean_m":av(dims["axial"]),"radial_edge_mean_m":av(dims["radial"]),
            "circ_edge_mean_m":av(dims["circumferential"])
        })
    ratios_sorted=sorted(ratios)
    def med(v): return statistics.median(v) if v else None
    summary[name]={
        "nodes":len(nodes),"elements":len(elems),
        "edge_ratio_gt100":sum(r>100 for r in ratios),
        "edge_ratio_gt50":sum(r>50 for r in ratios),
        "edge_ratio_min":min(ratios),"edge_ratio_median":statistics.median(ratios),"edge_ratio_max":max(ratios),
        "axial_edge_median_m":med(axial),"radial_edge_median_m":med(radial),"circ_edge_median_m":med(circum),
        "t055_warn_count":EXPECTED_T055[name],
        "matches_t055_warning_count":sum(r>100 for r in ratios)==EXPECTED_T055[name]
    }

with CSV_OUT.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

audit={
    "schema":1,
    "input":str(INP),
    "input_sha256":sha,
    "purpose":"Quantify inherited T055 steel-tower aspect-ratio warning on current T057 geometry.",
    "method":"For each C3D8R, compute 12 physical edge lengths and max/min edge ratio; classify edges in cylindrical axial/radial/circumferential directions.",
    "abaqus_warning_reference":"T055 native Abaqus 2025 DAT reported 1512 elements aspect ratio >100:1: SSEG_01=216, SSEG_02=432, SSEG_03=432, SSEG_04=432.",
    "summary":summary,
    "total_edge_ratio_gt100":sum(v["edge_ratio_gt100"] for v in summary.values()),
    "total_t055_warn_count":sum(EXPECTED_T055.values()),
    "all_counts_match_t055":all(v["matches_t055_warning_count"] for v in summary.values()),
    "note":"Edge-ratio reconstruction is an independent geometry diagnostic; Abaqus internal shape metric remains authoritative. Matching counts strongly identifies the geometric cause."
}
JSON_OUT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

md=["# T059 — T057钢塔实体网格高长宽比定量审计","",
    f"输入：`{INP}`  ","SHA-256："+sha,"",
    "T055原生Abaqus 2025 Data Check已报告1512个 `aspect ratio > 100:1` 单元。本任务不改模型，先对当前T057四段钢塔C3D8R实际节点坐标与单元连接做独立几何诊断。","",
    "## 分段结果","",
    "|钢塔段|单元数|edge ratio>100|T055 Abaqus警告数|中位edge ratio|最大edge ratio|轴向边中位(m)|厚度/径向边中位(m)|周向边中位(m)|",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for n,v in summary.items():
    md.append(f"|{n}|{v['elements']}|{v['edge_ratio_gt100']}|{v['t055_warn_count']}|{v['edge_ratio_median']:.3f}|{v['edge_ratio_max']:.3f}|{(v['axial_edge_median_m'] or 0):.6f}|{(v['radial_edge_median_m'] or 0):.6f}|{(v['circ_edge_median_m'] or 0):.6f}|")
md += ["",
    "## 判定规则","",
    "- 若独立edge-ratio >100计数与T055 Abaqus警告逐段一致，则可把问题定性为**系统性几何网格比例问题**，不是零散畸形单元。",
    "- 若SSEG_02–04全部单元超限，则禁止通过“只修几个坏单元”处理。",
    "- 后继网格必须围绕控制最短边（通常为薄壁厚度方向）设计轴向/周向尺寸，并重新做Abaqus native Data Check。",
    "- 局部钢塔疲劳应力在网格收敛前不得进入最终寿命结论。","",
    "详细逐单元数据：`T059_STEEL_ELEMENT_METRICS.csv`  ",
    "机器审计：`T059_STEEL_MESH_AUDIT.json`","",
    "## 下一步","",
    "根据本审计得到的实际三向边长，建立T060钢塔网格整改候选；至少两级网格，并以关键应力、塔顶位移和低阶频率进行收敛判定。"]
MD_OUT.write_text("\n".join(md)+"\n",encoding="utf-8")
print(json.dumps(audit,ensure_ascii=False))
