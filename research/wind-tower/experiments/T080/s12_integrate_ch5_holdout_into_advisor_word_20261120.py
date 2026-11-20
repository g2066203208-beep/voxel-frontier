#!/usr/bin/env python3
"""Reproducibly add verified T077 historical Ch5 evidence to the archived 2026-11-13 advisor DOCX.
Usage: python s12_integrate_ch5_holdout_into_advisor_word_20261120.py INPUT.docx OUTPUT.docx
Requires python-docx. Does not run any structural solver or regenerate physical data.
"""
import argparse, hashlib
from docx import Document
from docx.shared import Pt

def integrate(source, destination):
    d = Document(source)
    if any(p.text.startswith("5.4.99 整风速类别") for p in d.paragraphs):
        raise ValueError("Refusing duplicate insertion")
    anchor = next((p for p in d.paragraphs if p.text.strip() == "5.5 疲劳驱动多目标优化"), None)
    if anchor is None:
        raise ValueError("Missing canonical Ch5 insertion anchor")
    def paragraph(s, style="Normal", new_page=False):
        p = d.add_paragraph(style=style); p.add_run(s)
        if new_page: p.paragraph_format.page_break_before = True
        anchor._p.addprevious(p._p)
    def tab(headers, rows):
        t = d.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
        for j, h in enumerate(headers): t.rows[0].cells[j].text = h
        for values in rows:
            cells = t.add_row().cells
            for j, value in enumerate(values): cells[j].text = str(value)
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs: r.font.size = Pt(8)
        anchor._p.addprevious(t._tbl)
    paragraph("5.4.99 整风速类别盲留出的峰值位置捕获与代理准入拒绝", "Heading 3", True)
    paragraph("在历史四组ETM、31段×16方位名义弹性应力DEL4上，按整风速类别盲留出检验逐位置线性代理的极值位置捕获率。训练时不接触留出风速；域外推必须预测前拒绝。峰值捕获率为留出组代理选定位置的真实响应除以留出组全域真实最大响应。")
    tab(["留出风速 / m/s", "留出行数", "峰值捕获率", "准入"], [
        ["9.343881",496,"99.905518%","外推，拒绝"],
        ["11.400000",496,"100.000000%","插值，仅候选"],
        ["19.202140",992,"95.920144%","外推，拒绝"]])
    paragraph("高风速组漏峰4.079856%，否证所有留出组均至少捕获99%峰值的假说。496/992行不是独立风场数；平均误差和插值表现不能证明跨风速、跨设计可靠性。")
    paragraph("SOURCE=T077 1984行CSV Git blob b5effa2a493cec0a9af8a10a3b93df0ff997d2d0；RUN=T080 s11_group_holdout_peak_risk_20261120.cjs；历史V8源级计算，独立原生CLI及本次CSV字节SHA256未重新验证。该值是名义应力DEL4，非局部材料Miner寿命。")
    paragraph("5.4.100 相同风速不同湍流种子下的控制截面迁移", "Heading 3")
    paragraph("固定19.202140 m/s ETM，以S04或S06各自真实峰值位置作为选择器，在另一seed相同位置读取真实响应，并除以留出seed全域真实峰值。训练seed选择器不是跨风速代理；两方向互换不构成独立泛化试验。")
    tab(["训练→测试","训练控制段","测试控制段","峰值捕获率","漏峰 / MPa"],[
        ["S04→S06","CSEG03","CSEG04","99.876763%","0.007709"],
        ["S06→S04","CSEG04","CSEG03","99.879547%","0.007738"]])
    paragraph("两方向控制段均迁移，但漏峰小于0.008 MPa；位置标签一致性不等于幅值保守性。这不能撤销§5.4.99跨风速95.920144%的失败，也不能推断seed总体可靠度、跨设计可靠性或材料寿命。")
    paragraph("SOURCE=T077同一1984行历史CSV；RUN=T080 s11_etm_same_wind_seed_transfer_20261120.cjs。历史计算源级记录已存档，本次仅进行导师Word章节装配。")
    d.save(destination)
    print("source_sha256",hashlib.sha256(open(source,"rb").read()).hexdigest())
    print("output_sha256",hashlib.sha256(open(destination,"rb").read()).hexdigest())
    print("paragraphs",len(Document(destination).paragraphs),"tables",len(Document(destination).tables))
if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("source"); parser.add_argument("destination")
    args=parser.parse_args(); integrate(args.source,args.destination)
