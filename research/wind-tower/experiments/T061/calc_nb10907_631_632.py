#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NB/T 10907-2021 6.3.1/6.3.2 screening calculation for the 31 concrete segments.

This script deliberately keeps source quantities, engineering geometry conversions,
and unresolved design assumptions separate. It does not claim a final design because
the available 31-section actions are mapped from the 115.63 m OpenFAST baseline to
158 m and the reinforcement/PT design state is not yet closed.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:/Codex-research-native/openfast-36-r2-data-20261006")
OUT = Path(r"D:/Codex-research-native/fatigue-literature-20261006/source-git/research/wind-tower/experiments/T061")
OUT.mkdir(parents=True, exist_ok=True)

LOADS = ROOT / "U09_158m_31段内力插值_筛选版.csv"
GEOM = ROOT / "U09_31段受力与纵筋几何复核.csv"
HOOP = ROOT / "U09_31段环筋拉筋构造候选计算.csv"

# ---- Material/design inputs -------------------------------------------------
# NB/T 10907-2021 Table 4.1.2 (PDF image page 18):
#   C70: ft = 2.14 N/mm2; fc = 31.8 N/mm2
#   C65: ft = 2.09 N/mm2; fc = 29.7 N/mm2
# NB/T 10907-2021 Table 4.2.2-1 (PDF image page 20): HRB400 fy=fyv=360 N/mm2.
# The source model has S345 material identity; S345 is not a listed ordinary bar
# grade in this table, so HRB400 is an explicit design-assumption, not a source
# model fact.
MATERIAL = {
    "C70": {"ft_MPa": 2.14, "fc_MPa": 31.8},
    "C65": {"ft_MPa": 2.09, "fc_MPa": 29.7},
}
FY_LONG_MPA = 360.0
FYV_MPA = 360.0

# Candidate geometry only; not direct values published by He (2024).
HOOP_D_MM = 14.0
HOOP_SPACING_MM = 80.0
HOOP_LAYERS = 2  # inner + outer circular hoop layers
COVER_MM = 30.0
LONG_D_EQ_MM = 25.0  # source-area equivalent diameter (sqrt(4*A/pi))

# The 36 PT positions and their effective force are not closed. Main calculation
# therefore uses Np0=0. A separate nominal one-strand-per-position sensitivity is
# reported, but must not be used as the final prestress state.
NP0_MAIN_N = 0.0
NP0_NOMINAL_ONE_STRAND_N = 36.0 * 140.0 * 1280.0  # candidate CAE nominal: 6.4512 MN

# OpenFAST mapped actions are not a closed code load combination. Keep a transparent
# unit factor; replace only after the formal combination/factors are approved.
LOAD_FACTOR = 1.0


def annulus_core(D_mm: float, di_mm: float, cover_mm: float, hoop_d_mm: float):
    """Return core annulus area/perimeter at hoop centerlines.

    For a hollow circular tower, the core is treated as the annulus between the
    centerlines of the outer and inner hoop layers. This is an engineering geometry
    conversion because NB/T 10907 page 27 does not prescribe a hollow-section
    construction formula for A_cor/u_cor.
    """
    offset = cover_mm + hoop_d_mm / 2.0
    ro = D_mm / 2.0 - offset
    ri = di_mm / 2.0 + offset
    if ro <= ri:
        raise ValueError(f"non-positive core thickness: D={D_mm}, di={di_mm}")
    acor = math.pi * (ro * ro - ri * ri)
    ucor = 2.0 * math.pi * (ro + ri)  # outer + inner boundary of the annular core
    return ro, ri, acor, ucor


def row_calc(load, geom, hoop):
    seg = load["segment"]
    D_mm = float(geom["D_m"]) * 1000.0
    di_mm = float(geom["di_m"]) * 1000.0
    A_mm2 = float(geom["A_m2"]) * 1.0e6
    t_mm = float(hoop["wall_thickness_mm"])
    # Cross-check the imported geometry before using the source A.
    A_geom_mm2 = math.pi / 4.0 * (D_mm * D_mm - di_mm * di_mm)
    I_m4 = float(geom["I_m4"])

    # Concrete identity from the formal model: C70 for CSEG_01-02, C65 thereafter.
    concrete = "C70" if seg in {"CSEG_01", "CSEG_02"} else "C65"
    ft = MATERIAL[concrete]["ft_MPa"]
    fc = MATERIAL[concrete]["fc_MPa"]

    # Actions: use magnitudes for code demand. Fzt already contains OpenFAST gravity;
    # no additional tower/RNA weight is added here.
    V_kN = math.hypot(float(load["Fxt_kN"]), float(load["Fyt_kN"])) * LOAD_FACTOR
    M_kNm = float(load["M_bend_kNm"]) * LOAD_FACTOR
    T_kNm = abs(float(load["Mzt_kNm"])) * LOAD_FACTOR
    N_kN = max(0.0, -float(load["Fzt_kN"])) * LOAD_FACTOR
    V_N = V_kN * 1000.0
    M_Nmm = M_kNm * 1.0e6
    T_Nmm = T_kNm * 1.0e6
    N_N = N_kN * 1000.0

    # Effective depth: center-to-center distance between the two longitudinal bar
    # rows, using c_nom + hoop diameter + half longitudinal-bar diameter at each face.
    # This is explicit geometry, not a hidden standard value.
    h0_mm = D_mm - 2.0 * (COVER_MM + HOOP_D_MM + LONG_D_EQ_MM / 2.0)
    h0_mm = max(h0_mm, 1.0)

    # For a circular hollow section, NB/T gives b as a calculation width but no direct
    # hollow-tube prescription. Main result uses the physical wall width b=t; a second
    # equivalent-width result b=2A/h0 is reported for sensitivity.
    b_wall_mm = t_mm
    b_equiv_mm = 2.0 * A_mm2 / h0_mm

    lam = M_Nmm / (V_N * h0_mm) if V_N > 0 else float("inf")

    # Candidate transverse reinforcement. A closed circular hoop contributes two legs
    # to the shear plane; two radial layers therefore give Asv=2*n_layer*Abar. For
    # torsion Ast1 is the total single-leg area of the two layers. Both are explicit
    # conversions, pending a project-specific hollow-section clause/detail drawing.
    Ahoop_mm2 = math.pi * HOOP_D_MM**2 / 4.0
    Asv_mm2 = 2.0 * HOOP_LAYERS * Ahoop_mm2
    Ast1_mm2 = HOOP_LAYERS * Ahoop_mm2
    s_mm = HOOP_SPACING_MM

    # Concrete axial force term in 6.3.1: cap N at 0.3 fc A when N is larger.
    N_cap_N = 0.3 * fc * A_mm2
    N_used_N = min(N_N, N_cap_N)
    Np0_main = NP0_MAIN_N

    # 6.3.1 (shear only): V <= 1.75/(lambda+1)*ft*b*h0 + fyv*Asv/s*h0 + 0.07N
    vc631_wall = 1.75 / (lam + 1.0) * ft * b_wall_mm * h0_mm
    vs631 = FYV_MPA * Asv_mm2 / s_mm * h0_mm
    vn631 = 0.07 * N_used_N
    vrd631_wall = vc631_wall + vs631 + vn631
    vc631_eq = 1.75 / (lam + 1.0) * ft * b_equiv_mm * h0_mm
    vrd631_eq = vc631_eq + vs631 + vn631

    # 6.3.2: beta_t is bounded to [0.5,1.0] by the standard.
    ro_cor, ri_cor, Acor_mm2, ucor_mm = annulus_core(D_mm, di_mm, COVER_MM, HOOP_D_MM)
    # Exact circular-annulus plastic torsional resistance modulus:
    # Wt = (2*pi/3)(Ro^3-Ri^3), which tends to 2*A_m*t for a thin ring.
    Ro_mm = D_mm / 2.0
    Ri_mm = di_mm / 2.0
    Wt_mm3 = 2.0 * math.pi / 3.0 * (Ro_mm**3 - Ri_mm**3)
    beta_raw = 1.5 / (1.0 + 0.2 * (lam + 1.0) * V_N * Wt_mm3 / (T_Nmm * b_wall_mm * h0_mm)) if T_Nmm > 0 else 1.0
    beta = min(1.0, max(0.5, beta_raw))
    vc632_wall = (1.0 - beta) * 1.75 / (lam + 1.0) * ft * b_wall_mm * h0_mm
    vnp632 = 0.05 * Np0_main
    vrd632_wall = vc632_wall + vs631 + vnp632
    vc632_eq = (1.0 - beta) * 1.75 / (lam + 1.0) * ft * b_equiv_mm * h0_mm
    vrd632_eq = vc632_eq + vs631 + vnp632

    # 6.3.2-3 and -4. Here longitudinal and hoop steel are both HRB400 by design
    # assumption, so xi = fy*Ast1*s/(fyv*Ast1*u_cor) = s/u_cor numerically.
    xi = FY_LONG_MPA * Ast1_mm2 * s_mm / (FYV_MPA * Ast1_mm2 * ucor_mm)
    tc = beta * (0.35 * ft + 0.05 * Np0_main / A_mm2) * Wt_mm3
    ts = beta * 1.2 * math.sqrt(xi) * FYV_MPA * Ast1_mm2 * Acor_mm2 / s_mm
    trd_Nmm = tc + ts

    # Optional one-strand-per-PT-position sensitivity only; it does not change the
    # main check and is labelled candidate, because the real strand grouping/losses are open.
    np0_nominal = NP0_NOMINAL_ONE_STRAND_N
    vn632_nominal = 0.05 * np0_nominal
    tc_nominal = beta * (0.35 * ft + 0.05 * np0_nominal / A_mm2) * Wt_mm3
    vrd632_nominal = vc632_wall + vs631 + vn632_nominal
    trd_nominal = tc_nominal + ts

    return {
        "segment": seg,
        "z_center_m": float(load["z_center_m"]),
        "concrete": concrete,
        "source_D_m": float(geom["D_m"]),
        "source_di_m": float(geom["di_m"]),
        "wall_thickness_mm": t_mm,
        "A0_mm2": A_mm2,
        "A0_geom_mm2": A_geom_mm2,
        "A_geom_source_rel_error_pct": 100.0 * (A_geom_mm2 - A_mm2) / A_mm2,
        "h0_mm_assumed": h0_mm,
        "b_wall_mm_assumed": b_wall_mm,
        "b_equiv_2A_over_h0_mm_sensitivity": b_equiv_mm,
        "V_d_kN": V_kN,
        "M_d_kNm": M_kNm,
        "T_d_kNm": T_kNm,
        "N_comp_d_kN": N_kN,
        "N_used_6_3_1_kN": N_used_N / 1000.0,
        "N_cap_0p3fcA_kN": N_cap_N / 1000.0,
        "lambda_M_over_Vh0": lam,
        "ft_MPa": ft,
        "fc_MPa": fc,
        "fy_long_MPa_assumed": FY_LONG_MPA,
        "fyv_MPa_assumed": FYV_MPA,
        "hoop_d_mm_candidate": HOOP_D_MM,
        "hoop_spacing_mm_candidate": s_mm,
        "hoop_layers_candidate": HOOP_LAYERS,
        "Ahoop_mm2": Ahoop_mm2,
        "Asv_mm2_all_legs_assumed": Asv_mm2,
        "Ast1_mm2_torsion_assumed": Ast1_mm2,
        "core_outer_radius_mm": ro_cor,
        "core_inner_radius_mm": ri_cor,
        "Acor_mm2_assumed": Acor_mm2,
        "ucor_mm_assumed": ucor_mm,
        "Wt_mm3_assumed": Wt_mm3,
        "beta_raw": beta_raw,
        "beta_t_clipped": beta,
        "Np0_main_N": Np0_main,
        "xi": xi,
        "Vrd_631_wall_kN": vrd631_wall / 1000.0,
        "Vrd_631_equiv_kN_sensitivity": vrd631_eq / 1000.0,
        "Vrd_632_wall_kN": vrd632_wall / 1000.0,
        "Vrd_632_equiv_kN_sensitivity": vrd632_eq / 1000.0,
        "Vrd_631_concrete_kN": vc631_wall / 1000.0,
        "Vrd_631_steel_kN": vs631 / 1000.0,
        "Vrd_631_N_term_kN": vn631 / 1000.0,
        "Vrd_632_concrete_kN": vc632_wall / 1000.0,
        "Vrd_632_steel_kN": vs631 / 1000.0,
        "Vrd_632_Np0_term_kN": vnp632 / 1000.0,
        "V_ratio_631_wall": V_N / vrd631_wall if vrd631_wall > 0 else float("inf"),
        "V_ratio_632_wall": V_N / vrd632_wall if vrd632_wall > 0 else float("inf"),
        "Trd_632_kNm": trd_Nmm / 1.0e6,
        "Trd_concrete_kNm": tc / 1.0e6,
        "Trd_steel_kNm": ts / 1.0e6,
        "T_ratio_632": T_Nmm / trd_Nmm if trd_Nmm > 0 else float("inf"),
        "Vrd_632_one_strand_nominal_kN_candidate": vrd632_nominal / 1000.0,
        "Trd_one_strand_nominal_kNm_candidate": trd_nominal / 1.0e6,
        "screening_status": "PASS under mapped-action + candidate HRB400/hoop assumptions; HOLD for final design",
    }


def main():
    loads = pd.read_csv(LOADS)
    geom = pd.read_csv(GEOM)
    hoop = pd.read_csv(HOOP)
    merged = loads.merge(geom, on="segment", suffixes=("", "_geom")).merge(hoop, on="segment", suffixes=("", "_hoop"))
    rows = [row_calc(l, g, h) for (_, l), (_, g), (_, h) in zip(loads.iterrows(), geom.set_index("segment").loc[loads["segment"]].reset_index().iterrows(), hoop.set_index("segment").loc[loads["segment"]].reset_index().iterrows())]
    out = pd.DataFrame(rows)
    csv_path = OUT / "U09_31段NB10907_631_632剪扭承载力逐段计算_筛选版.csv"
    out.to_csv(csv_path, index=False, encoding="utf-8-sig", float_format="%.9g")

    # A compact summary supports audit without replacing the full table.
    i_v = out["V_ratio_632_wall"].idxmax()
    i_t = out["T_ratio_632"].idxmax()
    i_v31 = out["V_ratio_631_wall"].idxmax()
    md = OUT / "NB10907_631_632剪扭承载力计算说明_筛选版_20261007.md"
    md_text = f"""# NB/T 10907—2021 第6.3.1、6.3.2条逐段剪扭计算（筛选版）

本文件只完成可重算的规范公式代入，不把结果写成最终塔架设计。动作输入来自 `U09_158m_31段内力插值_筛选版.csv`，该文件把115.63 m DTU OpenFAST基准塔架的无量纲站点结果映射到158 m混塔，因此仍是筛选载荷。

## 1. 规范来源

公式与变量来自 NB/T 10907—2021 第6.3.1、6.3.2条，证据图为 `evidence/NBT10907_pdf_36.jpg`、`evidence/NBT10907_pdf_37.jpg`。材料取值来自同标准表4.1.2、表4.2.2-1：C70 的 `f_t=2.14 MPa`、`f_c=31.8 MPa`，C65 的 `f_t=2.09 MPa`、`f_c=29.7 MPa`，HRB400 的 `f_y=f_yv=360 MPa`。

## 2. 逐段输入与公式

对第 i 段，`V=sqrt(Fxt²+Fyt²)`，`M=sqrt(Mxt²+Myt²)`，`T=abs(Mzt)`，`N=max(0,-Fzt)`；OpenFAST 的 `Fzt` 已含重力，本计算未再次叠加重量。单位换成 N、N·mm、mm。

有效高度采用显式几何假设 `h0=D−2(c_nom+d_h+d_l/2)`，其中 `c_nom=30 mm`、环筋 `d_h=14 mm`、等面积纵筋 `d_l=25 mm`。第6.3.1主算取 `b=t`（实体壁厚）；另给出 `b=2A0/h0` 的等效宽度敏感性。NB/T 10907页36没有给本项目圆环薄壁截面的专用 b 换算，因此两者都不能冒称标准直接给定。

环筋候选为内外两层 φ14@80。每个闭合圆环按剪力方向计两肢，故 `Asv=2×2×Aφ14`；扭转项取两层单肢合计 `Ast1=2×Aφ14`。这是构造几何转换，何泽瑜论文未公开这组环筋数值。

圆环核心几何取环筋中心线间的环形区域：`Acor=π(Ro,cor²−Ri,cor²)`，`ucor=2π(Ro,cor+Ri,cor)`。圆环塑性抗扭抵抗矩取 `Wt=(2π/3)(Ro³−Ri³)`，为圆环塑性积分结果。

轴压项按第6.3.1条执行 `N_used=min(N,0.3 f_c A0)`。主算 `Np0=0`，因为预应力有效力、摩阻/锚具/收缩徐变/松弛损失尚未闭合；表中另列一股/位置的名义候选 `Np0=6.4512 MN` 敏感性，不能作为最终预应力。

第6.3.1：`V ≤ 1.75/(λ+1) f_t b h0 + f_yv Asv/s h0 + 0.07N`，`λ=M/(Vh0)`。

第6.3.2：`βt=1.5/[1+0.2(λ+1) V Wt/(T b h0)]`，按标准限制 `0.5≤βt≤1.0`；`V ≤ (1−βt)1.75/(λ+1) f_t b h0 + f_yv Asv/s h0 + 0.05Np0`；`T ≤ βt(0.35f_t+0.05Np0/A0)Wt + 1.2√ξ f_yv Ast1 Acor/s`，`ξ=f_y Ast1 s/(f_yv Ast1 ucor)`。

## 3. 结果摘要（主算 b=t，Np0=0）

- 第6.3.1剪力需求比最大段：`{out.loc[i_v31,'segment']}`，`V/Vrd={out.loc[i_v31,'V_ratio_631_wall']:.4f}`。
- 第6.3.2剪力需求比最大段：`{out.loc[i_v,'segment']}`，`V/Vrd={out.loc[i_v,'V_ratio_632_wall']:.4f}`。
- 第6.3.2扭矩需求比最大段：`{out.loc[i_t,'segment']}`，`T/Trd={out.loc[i_t,'T_ratio_632']:.4f}`。
- 控制段 `{out.loc[i_v,'segment']}`：`V={out.loc[i_v,'V_d_kN']:.3f} kN`，`T={out.loc[i_v,'T_d_kNm']:.3f} kN·m`，`N={out.loc[i_v,'N_comp_d_kN']:.3f} kN`，`βt={out.loc[i_v,'beta_t_clipped']:.4f}`，`Vrd,6.3.2={out.loc[i_v,'Vrd_632_wall_kN']:.3f} kN`，`Trd={out.loc[i_v,'Trd_632_kNm']:.3f} kN·m`。

逐段完整数值见同目录 CSV。

## 4. 结论边界

在本筛选输入、HRB400候选、φ14@80内外双层环筋、`b=t`、`Np0=0` 的假设下，31段剪扭需求比均小于1；这只能证明候选构造在当前映射动作下通过了一个透明的筛选计算。它不等于最终规范设计，因为158 m专用OpenFAST载荷、正式组合分项系数、环筋/拉筋构造条款、保护层环境类别、开孔/接缝局部效应、预应力有效力和损失仍未闭合。

## 5. 可追溯文件

- 输入：`U09_158m_31段内力插值_筛选版.csv`、`U09_31段受力与纵筋几何复核.csv`、`U09_31段环筋拉筋构造候选计算.csv`。
- 规范证据：`evidence/NBT10907_pdf_36.jpg`、`evidence/NBT10907_pdf_37.jpg`。
- 输出：`U09_31段NB10907_631_632剪扭承载力逐段计算_筛选版.csv`。
"""
    md.write_text(md_text, encoding="utf-8")
    print(csv_path)
    print(md)
    print(out[["segment", "V_ratio_631_wall", "V_ratio_632_wall", "T_ratio_632"]].to_string(index=False))


if __name__ == "__main__":
    main()
