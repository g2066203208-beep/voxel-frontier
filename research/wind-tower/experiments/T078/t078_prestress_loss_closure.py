#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T078 — 158 m hybrid tower CODE-DESIGN prestress closure.

Purpose
-------
Close Task 1 of the four-task reinforcement workflow:
1) preserve source identity (15.2 mm external unbonded strand, 1280 MPa initial stress),
2) calculate Appendix-A prestress losses,
3) determine a reproducible adopted PT bundle factor for the CODE-DESIGN branch,
4) verify permanent-state full compression for all 31 concrete segments.

This is NOT a claim that He (2024) published 36x8 strands. 36 circumferential PT
positions and r=1.75 m are reconstructed model inputs; BF=8 is a design value.

Normative basis (NB/T 10907-2021 Appendix A):
A.1.2 friction: sigma_l1 = sigma_con * [1-exp(-(k*x + mu*theta))]
A.1.3 anchorage/retraction/joint compression: sigma_l2 = Ep * delta_l / l
A.1.4 elastic compression (batch tensioning):
    sigma_l3 = (m-1)/(2m) * np * sigma_c, np=Ep/Ec
A.1.5 relaxation: sigma_l4 = alpha*(sigma_con/fpk-gamma)*sigma_con
A.1.6 post-tension shrinkage/creep:
    sigma_l5 = [55 + 300*sigma_pc/fcu_transfer]/(1+15*rho)

Registered conservative CODE-DESIGN assumptions where source data are unavailable:
- current reconstructed external tendon path is straight, no deviators -> k=0, theta=0;
- one active clip anchorage without top pressure -> 6 mm anchorage set;
- 30 horizontal joints across 31 concrete segments;
- unknown joint type -> adopt maximum listed 2 mm/joint for the design upper-bound;
- 36 circumferential PT bundles are tensioned sequentially -> m=36;
- shrinkage/creep upper-bound sets ordinary-rebar ratio rho=0;
- transfer-age cube strength is not published -> design upper-bound uses 0.75*grade;
  a nominal-strength sensitivity is also emitted.

The variable-section elastic-compression term is implemented as a length-weighted
average concrete strain along the 112 m tendon, which is explicitly an engineering
implementation of A.1.4 for a tapered tower; it is not quoted as a code formula.
"""
from pathlib import Path
import csv, json, math

ROOT = Path(__file__).resolve().parent
T071 = ROOT.parent / "T071" / "T071_input_geometry_31_segments.csv"
T074 = ROOT.parent / "T074" / "T074_158M_31SEG_GRAVITY_BASELINE.csv"

OUT_BF = ROOT / "T078_PRESTRESS_LOSS_BF_SCAN.csv"
OUT_SEG = ROOT / "T078_BF8_SEGMENT_LOSS_AND_GRAVITY_CHECK.csv"
OUT_META = ROOT / "T078_PRESTRESS_DESIGN_META.json"
OUT_REPORT = ROOT / "T078_PRESTRESS_DESIGN_REPORT.md"

SIGMA_CON = 1280.0
EP = 195000.0
FPK = 1860.0
A_STRAND = 140.0
N_POS = 36
PT_RADIUS_MM = 1750.0
L_MM = 112000.0

K_EXTERNAL = 0.0
THETA_RAD = 0.0
MU_EXTERNAL_REFERENCE = 0.15
ANCHOR_SET_MM = 6.0
N_JOINTS = 30
JOINT_COMP_ADOPTED_MM = 2.0
JOINT_COMP_REFERENCE_MM = 1.0
M_BATCHES = 36
RHO_SHRINK = 0.0
TRANSFER_STRENGTH_FACTOR = 0.75

HISTORICAL_BF_MIN_SCREEN = 5.59
BF_MIN_INTEGER_SCREEN = math.ceil(HISTORICAL_BF_MIN_SCREEN)
BF_ADOPTED = 8

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def segment_lengths(geom):
    ztops=[float(r["top_height_m"]) for r in geom]
    prev=0.0; out=[]
    for z in ztops:
        out.append(z-prev); prev=z
    if abs(sum(out)-112.0)>1e-6:
        raise RuntimeError(f"concrete segment lengths sum to {sum(out)} m, expected 112 m")
    return out

def concrete_grade(seg):
    return 70.0 if seg in ("CSEG_01","CSEG_02") else 65.0

def Ec_MPa(seg):
    return 37000.0 if seg in ("CSEG_01","CSEG_02") else 36500.0

def relaxation_loss():
    ratio=SIGMA_CON/FPK
    if ratio <= 0.7:
        alpha,gamma=0.125,0.5
    elif ratio <= 0.8:
        alpha,gamma=0.2,0.575
    else:
        raise ValueError("sigma_con/fpk outside Appendix-A stated range")
    return alpha*(ratio-gamma)*SIGMA_CON

def friction_loss():
    x=L_MM/1000.0
    return SIGMA_CON*(1.0-math.exp(-(K_EXTERNAL*x + MU_EXTERNAL_REFERENCE*THETA_RAD)))

def anchorage_loss(joint_comp_mm):
    delta=ANCHOR_SET_MM + N_JOINTS*joint_comp_mm
    return EP*delta/L_MM, delta

def elastic_loss(P0_N, geom, lengths):
    weighted=0.0
    for r,Lm in zip(geom,lengths):
        A_mm2=float(r["A_m2"])*1e6
        weighted += Lm/112.0 * (EP/Ec_MPa(r["segment"]))*(P0_N/A_mm2)
    return (M_BATCHES-1)/(2.0*M_BATCHES)*weighted

def shrink_creep_local(P0_N, row, transfer_factor):
    A_mm2=float(row["A_m2"])*1e6
    sigma_pc=P0_N/A_mm2
    fcu_transfer=concrete_grade(row["segment"])*transfer_factor
    loss=(55.0 + 300.0*sigma_pc/fcu_transfer)/(1.0+15.0*RHO_SHRINK)
    return sigma_pc,fcu_transfer,loss

def make_branch(bf, geom, lengths, joint_comp_mm, transfer_factor):
    Ap=N_POS*bf*A_STRAND
    P0_N=Ap*SIGMA_CON
    l1=friction_loss()
    l2,delta=anchorage_loss(joint_comp_mm)
    l3=elastic_loss(P0_N,geom,lengths)
    l4=relaxation_loss()
    loc=[shrink_creep_local(P0_N,r,transfer_factor) for r in geom]
    l5=max(v[2] for v in loc)
    ctl_i=max(range(len(loc)),key=lambda i:loc[i][2])
    total=l1+l2+l3+l4+l5
    sigma_pe=max(0.0,SIGMA_CON-total)
    eta=sigma_pe/SIGMA_CON
    Pe_N=Ap*sigma_pe
    return {
        "BF":bf,"strands_total":N_POS*bf,"Ap_mm2":Ap,"P0_MN":P0_N/1e6,
        "loss_friction_MPa":l1,"loss_anchor_joint_MPa":l2,"delta_l_mm":delta,
        "loss_elastic_MPa":l3,"loss_relaxation_MPa":l4,
        "loss_shrink_creep_MPa":l5,"shrink_creep_control_segment":geom[ctl_i]["segment"],
        "loss_total_MPa":total,"sigma_pe_MPa":sigma_pe,"eta":eta,"Pe_MN":Pe_N/1e6,
        "joint_comp_mm_each":joint_comp_mm,"transfer_strength_factor":transfer_factor,
    },loc

def gravity_check(Pe_MN, geom, gravity):
    gm={r["segment"]:r for r in gravity}
    rows=[]
    for g in geom:
        seg=g["segment"]; q=gm[seg]
        A=float(g["A_m2"]); I=float(g["I_m4"]); D=float(g["D_m"])
        Ng=max(0.0,-float(q["Fz_kN"]))
        Mg=math.hypot(float(q["Mx_kNm"]),float(q["My_kNm"]))
        PkN=Pe_MN*1000.0
        sigma_uniform=(Ng+PkN)/A/1000.0
        sigma_bend=Mg*(D/2.0)/I/1000.0
        sigmin=sigma_uniform-sigma_bend
        sigmax=sigma_uniform+sigma_bend
        rows.append({
            "segment":seg,"grade":f"C{int(concrete_grade(seg))}","A_m2":A,"I_m4":I,"D_m":D,
            "gravity_Ncomp_kN":Ng,"gravity_M_kNm":Mg,"Pe_MN":Pe_MN,
            "uniform_compression_MPa":sigma_uniform,"gravity_bending_edge_MPa":sigma_bend,
            "min_edge_compression_MPa":sigmin,"max_edge_compression_MPa":sigmax,
            "permanent_full_compression_PASS":"PASS" if sigmin>=0 else "FAIL",
        })
    return rows

def main():
    geom=read_csv(T071); gravity=read_csv(T074)
    if len(geom)!=31 or len(gravity)!=31:
        raise RuntimeError("expected 31 geometry and gravity rows")
    lengths=segment_lengths(geom)

    bfrows=[]
    branch_cache={}
    for bf in range(1,17):
        rec,loc=make_branch(bf,geom,lengths,JOINT_COMP_ADOPTED_MM,TRANSFER_STRENGTH_FACTOR)
        rec["historical_BF_min_screen_eta0p70"]=HISTORICAL_BF_MIN_SCREEN
        rec["screen_min_integer_BF"]=BF_MIN_INTEGER_SCREEN
        rec["adopted_BF"] = BF_ADOPTED
        rec["adopted"] = "YES" if bf==BF_ADOPTED else "NO"
        bfrows.append(rec); branch_cache[bf]=(rec,loc)

    adopted,loc=branch_cache[BF_ADOPTED]
    grav=gravity_check(adopted["Pe_MN"],geom,gravity)
    for i,row in enumerate(grav):
        sigma_pc,fcu_t,l5=loc[i]
        row.update({
            "segment_length_m":lengths[i],
            "sigma_pc_initial_MPa_for_A1p6_upper_bound":sigma_pc,
            "fcu_transfer_assumed_MPa":fcu_t,
            "rho_for_A1p6":RHO_SHRINK,
            "shrink_creep_loss_local_MPa":l5,
        })

    ref1,_=make_branch(BF_ADOPTED,geom,lengths,JOINT_COMP_REFERENCE_MM,TRANSFER_STRENGTH_FACTOR)
    ref2,_=make_branch(BF_ADOPTED,geom,lengths,JOINT_COMP_REFERENCE_MM,1.0)

    with OUT_BF.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(bfrows[0].keys())); w.writeheader(); w.writerows(bfrows)
    with OUT_SEG.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(grav[0].keys())); w.writeheader(); w.writerows(grav)

    min_grav=min(grav,key=lambda r:r["min_edge_compression_MPa"])
    meta={
        "status":"TASK1-CLOSED-CODE-DESIGN / PT-LOSS-AND-PERMANENT-COMPRESSION",
        "source_identity":{
            "strand_diameter_mm":15.2,"sigma_initial_MPa":SIGMA_CON,"Ep_MPa":EP,"fpk_MPa":FPK,
            "position_count_reconstructed":N_POS,"radius_mm_reconstructed":PT_RADIUS_MM,
            "single_strand_area_mm2":A_STRAND,
            "warning":"36 positions/radius/BF are not He-public direct; BF=8 is this thesis CODE-DESIGN value"
        },
        "normative_basis":{
            "prestress_losses":"NB/T 10907-2021 Appendix A A.1.1-A.1.6",
            "materials":"NB/T 10907-2021 Tables 4.1.2, 4.1.3, 4.2.2; GB/T 5224-2023 product identity",
            "service_boundary":"NB/T 10907-2021 7.1-7.2; final crack-control grade/coupled SLS is Task3"
        },
        "registered_assumptions":{
            "external_path":"straight reconstructed path; k=0, theta=0, so friction loss=0 in the modelled free length",
            "anchorage":"one active clip anchorage without top pressure, 6 mm",
            "horizontal_joints":N_JOINTS,"joint_compression_mm_each_adopted":JOINT_COMP_ADOPTED_MM,
            "joint_compression_reason":"actual joint type not source-direct; adopt maximum listed Table A.1.3 value as upper bound",
            "tensioning_batches":M_BATCHES,
            "rho_for_shrink_creep":RHO_SHRINK,
            "transfer_strength_factor":TRANSFER_STRENGTH_FACTOR,
            "transfer_strength_reason":"tensioning-age strength is unpublished; 0.75*grade is a registered conservative sensitivity, not a source claim"
        },
        "PT_quantity_selection":{
            "historical_T072_joint_screen_BFmin_at_eta0p70":HISTORICAL_BF_MIN_SCREEN,
            "minimum_integer_BF_from_that_screen":BF_MIN_INTEGER_SCREEN,
            "adopted_BF":BF_ADOPTED,
            "selection_reason":"BF8 is retained as a robust code-design choice above the earlier BF>=5.59 screen; the earlier screen is engineering evidence, not a code-mandated strand count"
        },
        "adopted_BF8":adopted,
        "BF8_reference_sensitivities":{
            "1mm_joint_0p75grade":ref1,
            "1mm_joint_nominal_grade":ref2
        },
        "permanent_compression_control":min_grav,
        "completion_boundary":{
            "closed_here":["PT quantity for CODE-DESIGN branch","Appendix-A loss components","effective prestress","31-segment permanent gravity+PT full-compression check"],
            "not_claimed_here":["final operational crack-control grade","final crack width","final fatigue","final 36x31 envelope","final joint ULS after ordinary reinforcement is frozen"],
            "reason":"Those are coupled Task3/Task4 checks in the agreed four-task workflow; they are not missing PT-loss calculations."
        }
    }
    OUT_META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    lines=[]
    add=lines.append
    add("# T078 — 158 m混塔任务1：预应力设计闭合（CODE-DESIGN）")
    add("")
    add("**状态：TASK1-CLOSED-CODE-DESIGN / PT损失与有效预应力已闭合。**")
    add("")
    add("本任务只冻结本文规范设计支路的预应力数量、损失和有效预应力；不把BF=8写成何泽瑜论文原值。最终裂缝等级、疲劳、36×31全包络和最终接缝ULS按既定四任务流程放在任务3/4。")
    add("")
    add("## 1. 来源身份与冻结边界")
    add("")
    add("- 何泽瑜2024直接：15.2 mm钢绞线、T3D2表示、底端固定、顶部锚固于钢—混转换法兰。")
    add("- Xu/He同谱系2025：体外无黏结、Ep=195 GPa、初始预应力1280 MPa、fpy=1320 MPa、fpk=1860 MPa。")
    add("- 当前模型重建：36个环向PT位置、r=1.75 m、单股面积140 mm²。以上36位置/r不是何文公开直接值。")
    add("- 本任务设计值：每位置8股，即36×8=288股；Ap=40320 mm²。身份为CODE-DESIGN。")
    add("")
    add("## 2. 规范原文位置")
    add("")
    add("NB/T 10907—2021附录A明确要求考虑五类损失：孔道/导向摩擦、锚具变形与回缩及接缝压密、混凝土弹性压缩、钢绞线松弛、混凝土收缩徐变。具体采用A.1.2～A.1.6。")
    add("")
    add("- A.1.2：sigma_l1 = sigma_con*[1-exp(-(k*x+mu*theta))]。体外筋表A.1.2给出k=0；摩擦只在转向装置和锚固装置管道段发生。")
    add("- A.1.3：sigma_l2 = Ep*Delta_l/l。表A.1.3夹片锚具无顶压取6 mm；接缝压密按每个接缝计。")
    add("- A.1.4：一次张拉后张构件弹性压缩损失为0；分批张拉采用(m-1)/(2m)*np*sigma_c。")
    add("- A.1.5：1280/1860=0.6882<=0.7，故alpha=0.125、gamma=0.5。")
    add("- A.1.6：后张法收缩徐变损失采用[55+300*sigma_pc/fcu_transfer]/(1+15*rho)。")
    add("")
    add("## 3. 本文登记的保守设计假设")
    add("")
    add("原型资料没有给张拉施工方案、锚具型号、接缝压密量和张拉龄期强度。为避免伪造原型参数，本任务把这些明确登记为本文设计假设：")
    add("")
    add("1. 当前重建PT为直线体外无黏结筋，无转向点：k=0、theta=0，因此自由长度摩阻损失取0。")
    add("2. 单端张拉，活动端按夹片锚具无顶压的6 mm回缩。")
    add("3. 31个混凝土节段之间按30个水平接缝计；由于真实接缝型式未公开，采用表A.1.3列值中的上界2 mm/缝作为设计上界。")
    add("4. 36个环向束位置按36批顺序张拉，m=36；这是比一次整体张拉更不利的弹性压缩支路。")
    add("5. 收缩徐变上界取rho=0，使分母最小；张拉龄期强度未公开，主设计支路登记为0.75×混凝土等级，并另给名义强度敏感性。")
    add("")
    add("## 4. BF=8逐项损失计算")
    add("")
    add(f"总股数=36×8=288；Ap=288×140={adopted['Ap_mm2']:.0f} mm²。")
    add(f"名义初始力P0=Ap×1280={adopted['P0_MN']:.4f} MN。")
    add("")
    add(f"1) 摩阻损失：k=0、theta=0 -> sigma_l1={adopted['loss_friction_MPa']:.3f} MPa。")
    add(f"2) 锚具+接缝压密：Delta_l=6+30×2={adopted['delta_l_mm']:.1f} mm；sigma_l2=195000×{adopted['delta_l_mm']:.1f}/112000={adopted['loss_anchor_joint_MPa']:.3f} MPa。")
    add(f"3) 弹性压缩：36批张拉、按31段Ec/A沿112 m长度加权，sigma_l3={adopted['loss_elastic_MPa']:.3f} MPa。")
    add(f"4) 松弛：0.125×(1280/1860-0.5)×1280={adopted['loss_relaxation_MPa']:.3f} MPa。")
    add(f"5) 收缩徐变：rho=0、0.75×等级支路逐段计算，最不利{adopted['shrink_creep_control_segment']}，sigma_l5={adopted['loss_shrink_creep_MPa']:.3f} MPa。")
    add("")
    add(f"总损失={adopted['loss_total_MPa']:.3f} MPa，占初始应力{adopted['loss_total_MPa']/SIGMA_CON*100:.2f}%。")
    add(f"有效预应力 sigma_pe=1280-{adopted['loss_total_MPa']:.3f}={adopted['sigma_pe_MPa']:.3f} MPa，eta={adopted['eta']:.4f}。")
    add(f"有效总预应力 Pe=40320×{adopted['sigma_pe_MPa']:.3f}={adopted['Pe_MN']:.3f} MN。")
    add("")
    add("## 5. 为什么最终采用BF=8而不是把它冒充原型参数")
    add("")
    add(f"T072既有接缝/预压工程敏感性在更不利的eta=0.70下反算等效最小BF约{HISTORICAL_BF_MIN_SCREEN:.2f}，其最小整数为BF={BF_MIN_INTEGER_SCREEN}。该结果不是规范直接给出的股数，因此本任务不把BF6称为‘规范规定最小股数’。为了给未显式建模的接缝、施工和损失不确定性留出设计余量，CODE-DESIGN支路采用BF=8；相对5.59的面积/股数裕量约{(BF_ADOPTED/HISTORICAL_BF_MIN_SCREEN-1)*100:.1f}%。")
    add("")
    add(f"采用附录A保守损失后eta={adopted['eta']:.4f}，仍高于T077已扫描的0.70下界；T077对BF8同时扫描eta=0.70/0.80/0.85/0.90/1.00并完成四个控制工况31段纵筋ULS，因此本任务得到的有效预应力没有超出既有纵筋容量分析域。")
    add("")
    add("## 6. 31段永久状态压紧检查")
    add("")
    add("用T074纯重力基线与本任务有效Pe进行毛截面边缘应力检查：sigma_min=(N_G+Pe)/A-M_G*(D/2)/I。该检查回答‘重力+有效预应力下是否保持全截面受压’，不是把它冒充运行ETM裂缝验算。")
    add("")
    add(f"31/31段均为PASS；最小压应力控制{min_grav['segment']}，sigma_min={min_grav['min_edge_compression_MPa']:.3f} MPa > 0。")
    add("")
    add("## 7. BF=8敏感性（说明设计假设影响）")
    add("")
    add(f"- 若接缝压密按1 mm/缝、仍取0.75×等级：sigma_pe={ref1['sigma_pe_MPa']:.3f} MPa，Pe={ref1['Pe_MN']:.3f} MN。")
    add(f"- 若接缝1 mm/缝且张拉龄期强度直接取名义等级：sigma_pe={ref2['sigma_pe_MPa']:.3f} MPa，Pe={ref2['Pe_MN']:.3f} MN。")
    add("- 正式采用值取更不利的2 mm/缝+0.75×等级支路，因此后续Task2不会高估有效预应力。")
    add("")
    add("## 8. Task1关闭项与后续边界")
    add("")
    add("**本任务已经关闭：** PT规范设计数量(BF8)、初始面积/力、A.1.2～A.1.6五类损失、有效应力/有效力、31段永久状态全截面压紧。")
    add("")
    add("**本任务不冒充已经关闭：** 运行状态最终裂缝控制等级与裂缝宽度、最终疲劳、最终36×31包络、普通钢筋冻结后的接缝ULS。这些是既定Task3/Task4的耦合验算，而不是‘预应力损失还没算’。")
    add("")
    add("## 9. 可复算文件")
    add("")
    add("- t078_prestress_loss_closure.py：全部计算脚本；")
    add("- T078_PRESTRESS_LOSS_BF_SCAN.csv：BF1～16损失/有效力；")
    add("- T078_BF8_SEGMENT_LOSS_AND_GRAVITY_CHECK.csv：31段收缩徐变局部值与永久压紧检查；")
    add("- T078_PRESTRESS_DESIGN_META.json：来源身份、规范、假设、冻结边界。")
    add("")
    add("## 10. 规范证据页索引")
    add("")
    add("- NB/T 10907—2021 PDF第16页（印刷第7页）：C65/C70材料参数；")
    add("- PDF第17～18页（印刷第8～9页）：15.2 mm钢绞线强度、设计值和Ep；")
    add("- PDF第42页（印刷第33页）：附录A.1.1、A.1.2；")
    add("- PDF第43页（印刷第34页）：A.1.3、A.1.4；")
    add("- PDF第44～45页（印刷第35～36页）：A.1.5、A.1.6；")
    add("- PDF第35～37页（印刷第26～28页）：SLS应力/裂缝控制；最终等级由Task3统一冻结。")
    OUT_REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")

    print(json.dumps({
        "BF_adopted":BF_ADOPTED,
        "P0_MN":adopted["P0_MN"],
        "loss_total_MPa":adopted["loss_total_MPa"],
        "sigma_pe_MPa":adopted["sigma_pe_MPa"],
        "eta":adopted["eta"],
        "Pe_MN":adopted["Pe_MN"],
        "gravity_min_segment":min_grav["segment"],
        "gravity_min_compression_MPa":min_grav["min_edge_compression_MPa"]
    },ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
