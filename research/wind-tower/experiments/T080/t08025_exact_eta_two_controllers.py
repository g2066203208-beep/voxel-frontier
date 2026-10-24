#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T080.25: exact-eta SINGLE-STATE replay for CSEG19/21, read-only.
Requires numpy, pandas and T073/T077 source tree. Does NOT verify full time histories,
HRB335 physical branch, Abaqus, standards, or seismic/wind-fatigue responses.
"""
from pathlib import Path
import sys, math, json
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EX = HERE.parent
sys.path.insert(0, str(EX / "T077"))
import t077_formal_rebar as t077

def select_controller_row(controls, d, seg):
    """Select one T075 row with the same factor/case/time identity as T077."""
    gg, gp = float(d.control_gamma_G), float(d.control_gamma_P)
    if gg not in (1.0, 1.35) or gp not in (1.0, 1.2):
        raise ValueError(f"unsupported T077 load factors: gamma_G={gg}, gamma_P={gp}")
    combo = f"G{gg:.2f}_Q1p40".replace(".", "p")
    ctrl = controls[(controls.segment == seg) &
                    (controls.case == d.control_case) &
                    (controls.control_metric == "M_max") &
                    (controls.combo == combo) &
                    (np.abs(controls.time_s - float(d.control_time_s)) < 1e-7) &
                    (np.isclose(controls.gamma_G, gg, rtol=0, atol=1e-12)) &
                    (np.isclose(controls.gamma_Q, 1.4, rtol=0, atol=1e-12))]
    if len(ctrl) != 1:
        raise RuntimeError(f"T075 controller identity is not unique: {seg}, {combo}, rows={len(ctrl)}")
    return ctrl.iloc[0], gg, gp, combo

def main():
    controls = pd.read_csv(EX/"T075"/"T075_S06_31SEG_GQ_CONTROL_ROWS.csv")
    design = pd.read_csv(EX/"T077"/"T077_FORMAL_31SEG_REBAR_BF8.csv")
    with open(EX/"T078"/"T078_PRESTRESS_DESIGN_META.json", encoding="utf-8") as f:
        eta_exact = float(json.load(f)["adopted_BF8"]["eta"])
    geom = t077.read_geom()
    rings = t077.read_rings(geom)
    output = []
    for seg in ("CSEG_19", "CSEG_21"):
        d = design.loc[design.segment == seg].iloc[0]
        assert int(d.BF) == 8 and int(d.bar_d_mm) == 40
        assert d.control_case == "U09p343881_ETM_S06" and abs(d.control_time_s-652.15)<1e-7
        c, gg, gp, combo = select_controller_row(controls, d, seg)
        m_x = gg*float(c.G_Mx_kNm) + 1.4*float(c.Q_Mx_kNm)
        m_y = gg*float(c.G_My_kNm) + 1.4*float(c.Q_My_kNm)
        m_res = math.hypot(m_x, m_y)
        ea_mm = max(20., float(geom[seg]["D_m"])*1000./30.)
        Abar = math.pi*float(d.bar_d_mm)**2/4.
        for eta in (1.0, eta_exact, 0.8, 0.7):
            Nc, Mc, NsA, MsA, Np1, Mp1 = t077.capacity_components(seg, geom[seg], rings[seg], eta)
            Nb, Mb = t077.upper_capacity(Nc+Abar*NsA+8*Np1, Mc+Abar*MsA+8*Mp1)
            p_kN = t077.e01.SIGP_INIT*eta*t077.e01.PT_A1*t077.e01.NPT*8/1000.
            N_kN = -gg*(float(c.G_Fz_kN)+float(c.Q_Fz_kN))+(gp-1)*p_kN
            M_kNm = m_res + N_kN*ea_mm/1000.
            assert Nb[0] <= N_kN*1000 <= Nb[-1]
            cap_kNm = float(np.interp(N_kN*1000, Nb, Mb)/1e6)
            u = M_kNm/cap_kNm
            if eta == 1.0:
                assert abs(N_kN-float(d.N_design_kN))<1e-6
                assert abs(M_kNm-float(d.M_design_kNm))<1e-6
                assert abs(cap_kNm-float(d.Mcap_kNm))<1e-6
                assert abs(u-float(d.max_utilization))<1e-10
            output.append(dict(segment=seg, eta=eta, N_design_kN=N_kN,
                               M_design_kNm=M_kNm, Mcap_kNm=cap_kNm,
                               utilization=u, bins=len(Nb)))
    print(json.dumps(dict(status="TWO_CONTROL_STATES_STATIC_ONLY",
                          results=output, not_verified=["full 4-case histories",
                          "HRB335", "PT native equilibrium", "code compliance",
                          "Abaqus native", "seismic", "fatigue"]), indent=2))
if __name__ == "__main__":
    main()
