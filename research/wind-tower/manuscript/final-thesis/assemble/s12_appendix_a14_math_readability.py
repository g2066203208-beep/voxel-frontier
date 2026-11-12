#!/usr/bin/env python3
"""Add four readable A.14 scalar spectral-matching equations to the existing advisor DOCX.
Non-CAE, no structural calculation. Input SHA lock avoids silently patching a new edition.
Usage: python s12_appendix_a14_math_readability.py input.docx output.docx --expected-sha SHA256
"""
import argparse, hashlib
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

EQUATIONS = (
    "qᵢ = PSA_ESM(Tᵢ) / PSA_target(Tᵢ) > 0;    E(a) = maxᵢ |a qᵢ − 1|",
    "a* = 2 / (q_min + q_max);    E_min = (q_max − q_min) / (q_max + q_min)",
    "a_log = 1 / √(q_min q_max);    L_min = ½ ln(q_max / q_min)",
    "E_min ≤ ε  ⇔  q_max / q_min ≤ (1 + ε) / (1 − ε),    0 ≤ ε < 1",
)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--expected-sha", required=True)
    a = ap.parse_args()
    if a.source.resolve() == a.output.resolve():
        raise ValueError("refuse in-place overwrite")
    actual = hashlib.sha256(a.source.read_bytes()).hexdigest()
    if actual != a.expected_sha:
        raise ValueError("SOURCE_SHA_MISMATCH " + actual)
    d = Document(a.source)
    hits = [i for i,p in enumerate(d.paragraphs) if p.text.startswith("A.14 实测ESM")]
    if len(hits) != 1:
        raise ValueError("A14_ANCHOR_NOT_UNIQUE")
    anchor = d.paragraphs[hits[0]+2]
    if "数学定义与严格证明" not in anchor.text:
        raise ValueError("A14_PROOF_ANCHOR_CHANGED")
    if any(EQUATIONS[0] in p.text for p in d.paragraphs):
        raise ValueError("DUPLICATE_FORMULAE")
    before_tables = len(d.tables)
    for eq in EQUATIONS:
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        rr = p.add_run(eq)
        rr.font.name = "Cambria Math"
        rr.font.size = Pt(10)
        anchor._p.addprevious(p._p)
    assert len(d.tables) == before_tables
    d.save(a.output)
    print("S12_A14_READABILITY_PASS", hashlib.sha256(a.output.read_bytes()).hexdigest())
if __name__ == "__main__":
    main()
