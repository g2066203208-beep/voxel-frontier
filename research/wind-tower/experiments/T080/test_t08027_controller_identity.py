#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T080.27 isolated metadata regression tests; no Abaqus, no T077 import.

AST-extract the production selector from T080.25 to test its actual code.
Synthetic rows use the case/time and G_Fz identities recorded in T075.
This tests metadata matching only, NOT the fibre-capacity replay.
"""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

SOURCE = Path(__file__).with_name("t08025_exact_eta_two_controllers.py")
root = ast.parse(SOURCE.read_text(encoding="utf-8"))
func = next(n for n in root.body
            if isinstance(n, ast.FunctionDef) and n.name == "select_controller_row")
scope = {"pd": pd, "np": np}
exec(compile(ast.Module(body=[func], type_ignores=[]), str(SOURCE), "exec"), scope)
select_controller_row = scope["select_controller_row"]

CASE = "U09p343881_ETM_S06"

def design(gg, gp=1.2):
    return SimpleNamespace(control_case=CASE, control_time_s=652.15,
                           control_gamma_G=gg, control_gamma_P=gp)

def fixture():
    return pd.DataFrame([
        dict(segment="CSEG_19", case=CASE, time_s=652.15,
             combo="G1p00_Q1p40", gamma_G=1., gamma_Q=1.4,
             control_metric="M_max", G_Fz_kN=-14564.880633749928),
        dict(segment="CSEG_19", case=CASE, time_s=652.15,
             combo="G1p35_Q1p40", gamma_G=1.35, gamma_Q=1.4,
             control_metric="M_max", G_Fz_kN=-14564.880633749928),
        dict(segment="CSEG_21", case=CASE, time_s=652.15,
             combo="G1p35_Q1p40", gamma_G=1.35, gamma_Q=1.4,
             control_metric="M_max", G_Fz_kN=-13508.053356027796),
    ])

class ControllerIdentityTests(unittest.TestCase):
    def test_cseg19_correct_combo(self):
        row, gg, gp, combo = select_controller_row(fixture(), design(1.), "CSEG_19")
        self.assertEqual((combo, gg, gp), ("G1p00_Q1p40", 1., 1.2))
        self.assertEqual(row.gamma_G, 1.)

    def test_cseg21_correct_combo(self):
        row, gg, gp, combo = select_controller_row(fixture(), design(1.35), "CSEG_21")
        self.assertEqual(combo, "G1p35_Q1p40")
        self.assertEqual(row.gamma_G, 1.35)

    def test_missing_rejected(self):
        with self.assertRaises(RuntimeError):
            select_controller_row(fixture().iloc[0:0], design(1.), "CSEG_19")

    def test_duplicate_rejected(self):
        rows = fixture()
        rows = pd.concat([rows, rows.iloc[[0]]], ignore_index=True)
        with self.assertRaises(RuntimeError):
            select_controller_row(rows, design(1.), "CSEG_19")

    def test_wrong_g_factor_rejected(self):
        rows = fixture()
        rows.loc[0, "gamma_G"] = 1.35
        with self.assertRaises(RuntimeError):
            select_controller_row(rows, design(1.), "CSEG_19")

    def test_wrong_q_factor_rejected(self):
        rows = fixture()
        rows.loc[0, "gamma_Q"] = 1.3
        with self.assertRaises(RuntimeError):
            select_controller_row(rows, design(1.), "CSEG_19")

    def test_wrong_metric_rejected(self):
        rows = fixture()
        rows.loc[0, "control_metric"] = "N_max"
        with self.assertRaises(RuntimeError):
            select_controller_row(rows, design(1.), "CSEG_19")

    def test_unsupported_g_factor_rejected(self):
        with self.assertRaises(ValueError):
            select_controller_row(fixture(), design(1.1), "CSEG_19")

if __name__ == "__main__":
    unittest.main(verbosity=2)
