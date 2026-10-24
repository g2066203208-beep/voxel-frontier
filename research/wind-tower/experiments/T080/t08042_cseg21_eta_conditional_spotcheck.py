#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T080.42 CSEG21 deterministic, single-state source-formula replay.

SOURCE: T071 geometry CSEG_21; T073 radii and E.0.1 code;
T077 BF8 CSEG_21 historical controlling row; T078 PT design metadata.
This self-contained replay avoids the missing four full-history gzip files.
It does NOT establish a new governing case, code compliance, or Abaqus V&V.
Requires numpy. All length/stress/force units: mm, MPa, N, N*mm.
"""
import math
import numpy as np

D = 5.699999603247647 * 1000
DI = 5.039999869290876 * 1000
R_IN, R_OUT, N_BAR = 2582.5, 2787.5, 76
ES, FY, FYC = 200000., 435., 410.
EP, FPY, FPYC = 195000., 1320., 390.
SIGP_INIT, PT_A1, PT_R, NPT = 1280., 140., 1750., 36
BF, A_BAR = 8, math.pi * 40**2 / 4
N_HIST = 28777.721107233167 * 1000
M_HIST = 259879.70551790795 * 1e6
MCAP_HIST = 260380.49847828923 * 1e6
ETA_DESIGN = 0.7702745023137976
GAMMA_P = 1.2


def concrete_stress(e, fc, n, e0):
    s = np.zeros_like(e)
    mask = (e > 0) & (e <= e0)
    q = np.clip(1 - e[mask] / e0, 0, None)
    s[mask] = fc * (1 - q**n)
    s[e > e0] = fc
    return s


def evaluate(eta, nr, nth, nz, n_target, m_target):
    ro, ri = D / 2, DI / 2
    dr, dtheta = (ro - ri) / nr, 2 * math.pi / nth
    rs = ri + (np.arange(nr) + .5) * dr
    th = (np.arange(nth) + .5) * dtheta
    rr, tt = np.meshgrid(rs, th, indexing="ij")
    zc = (rr * np.sin(tt)).ravel()
    ac = (rr * dr * dtheta).ravel()
    bar_theta = 2 * math.pi * np.arange(N_BAR) / N_BAR
    zs = np.concatenate([R_IN * np.sin(bar_theta), R_OUT * np.sin(bar_theta)])
    zp = PT_R * np.sin(2 * math.pi * np.arange(NPT) / NPT)
    fcu, fc = 65., 29.7
    n = 2 - (fcu - 50) / 60
    e0 = .002 + .5 * (fcu - 50) * 1e-5
    ecu = .0033 - (fcu - 50) * 1e-5
    zn = np.concatenate([
        np.linspace(-3 * ro, -ro, int(nz / 10), endpoint=False),
        np.linspace(-ro, .999 * ro, nz - int(nz / 10))
    ])
    kappa = np.minimum(ecu / (ro - zn),
                       np.where(zn > zs.min(), .01 / (zn - zs.min()), np.inf))
    normal = np.empty_like(zn)
    moment = np.empty_like(zn)
    for i in range(0, len(zn), 50):
        sl = slice(i, min(i + 50, len(zn)))
        zz, kk = zn[sl, None], kappa[sl, None]
        ec = kk * (zc[None, :] - zz)
        sigc = concrete_stress(ec, fc, n, e0)
        nc = (sigc * ac).sum(1)
        mc = (sigc * ac * zc).sum(1)
        es = kk * (zs[None, :] - zz)
        sigs = np.clip(ES * es, -FY, FYC)
        sigc_at_bar = concrete_stress(es, fc, n, e0)
        ns = (sigs - sigc_at_bar).sum(1)
        ms = ((sigs - sigc_at_bar) * zs[None, :]).sum(1)
        ep = kk * (zp[None, :] - zz)
        sigp = np.clip(SIGP_INIT * eta - EP * ep,
                       SIGP_INIT * eta - FPYC, FPY)
        fp = -sigp * PT_A1
        np1, mp1 = fp.sum(1), (fp * zp[None, :]).sum(1)
        normal[sl] = nc + A_BAR * ns + BF * np1
        moment[sl] = np.abs(mc + A_BAR * ms + BF * mp1)

    order = np.argsort(normal)
    normal, moment = normal[order], moment[order]
    span = max(float(normal[-1] - normal[0]), 1.)
    width = max(span / 2500, 5e4)
    bins = np.floor((normal - normal[0]) / width).astype(int)
    unique = np.unique(bins)
    nb = np.array([normal[bins == k].mean() for k in unique])
    mb = np.array([moment[bins == k].max() for k in unique])
    order = np.argsort(nb)
    nb, mb = nb[order], mb[order]
    assert nb.min() <= n_target <= nb.max(), "target N outside binned capacity"
    cbin = np.interp(n_target, nb, mb)
    craw = np.interp(n_target, normal, moment)
    return {
        "eta": eta, "nr": nr, "nth": nth, "nz": nz,
        "n_kN": n_target / 1000, "m_kNm": m_target / 1e6,
        "mcap_binned_kNm": cbin / 1e6,
        "mcap_raw_sorted_kNm": craw / 1e6,
        "util_binned": m_target / cbin,
        "util_raw_sorted": m_target / craw,
        "bin_minus_raw_percent": 100 * (cbin / craw - 1)
    }


def main():
    # T077 gamma_P incremental demand: N = -gamma_G*Fz + (gamma_P-1)*P(eta).
    # Historical same-time, same-gamma, same-wind state only; NOT a new envelope.
    for eta in (1., ETA_DESIGN):
        delta_n = (GAMMA_P - 1) * (eta - 1) * 51.6096e6
        nt = N_HIST + delta_n
        mt = M_HIST + delta_n * max(20., D / 30)
        for nr, nth, nz in ((16, 360, 1500), (16, 360, 3000),
                            (24, 540, 3000)):
            r = evaluate(eta, nr, nth, nz, nt, mt)
            if eta == 1. and (nr, nth, nz) == (16, 360, 1500):
                assert abs(r["mcap_binned_kNm"] - MCAP_HIST / 1e6) < 1e-6
                assert abs(r["util_binned"] - 0.9980766879113144) < 1e-10
            print(r)


if __name__ == "__main__":
    main()
