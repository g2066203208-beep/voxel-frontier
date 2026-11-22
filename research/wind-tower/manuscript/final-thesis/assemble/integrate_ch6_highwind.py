#!/usr/bin/env python3
"""Fail-closed insertion of the existing ERA5 directional conclusion into V8-R4's Chapter 7.
The research Markdown uses a six-chapter outline; V8-R4 is a seven-chapter DOCX.
No Abaqus/CAE operation is performed.
"""
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from docx.shared import Pt
import argparse, hashlib

PARAS = [
'（5）依据原R5学位论文恢复的嘉鱼ERA5十六方位风向频率表，N、NNE、SSW及SW四个方位的全年频率合计为39.78%，在原表定义的高风组中合计为87.39%；四个方向的条件富集系数P(d|H)/P(d)依次为2.0458、2.4036、2.6410和1.2323。由此可见，全年风向频率不能直接替代高风条件下的风向抽样权重。该结论仅对恢复表的条件分组成立，不代表风载或材料疲劳放大。',
'方向富集系数并非P(H|d)。计算某风向下高风事件的绝对发生概率仍须知道高风总体概率P(H)，并采用P(H|d)=P(d|H)P(H)/P(d)；缺少原始逐小时风速—风向联合计数时，不能确定高风小时数及方向条件疲劳损伤。印刷百分比舍入、ERA5代表性及实际风场误差须分别评估。本项结论可用于提出联合风速—风向分层抽样要求，不能替代正式DLC1.2覆盖、同步风载时程或材料寿命验证。'
]
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def integrate(src, dst, expected_sha=None):
    src, dst = Path(src), Path(dst)
    assert src.resolve() != dst.resolve(), 'refuse in-place edit'
    if expected_sha:
        assert sha(src) == expected_sha, 'source SHA256 mismatch'
    doc = Document(src)
    ps = list(doc.paragraphs)
    # TOC repeats the text: use the unique non-Normal body chapter heading.
    chapters = [(i,p) for i,p in enumerate(ps)
                if p.text.strip() == '第七章 结论与展望' and p.style.name != 'Normal']
    assert len(chapters) == 1, 'unique body chapter 7 required'
    start = chapters[0][0]
    anchors = [(i,p.text.strip()) for i,p in enumerate(ps[start:],start)
               if p.text.strip() in ('7.1 主要结论', '7.2 主要创新点')]
    assert len(anchors) == 2 and [x[1] for x in anchors] == ['7.1 主要结论','7.2 主要创新点'], 'chapter anchors missing/ambiguous'
    a,b = anchors[0][0],anchors[1][0]
    old = [p.text.strip() for p in ps[a+1:b] if p.text.strip()]
    # V8-R4 keeps conclusions (1)-(4) in one original paragraph.
    assert len(old) == 1 and all(old[0].count(f'（{i}）') == 1 for i in range(1,5)) and '（5）' not in old[0], 'original conclusions changed or already inserted'
    assert '39.78%' not in old[0] and '87.39%' not in old[0], 'duplicate conclusion'
    anchor = ps[b]
    for s in PARAS:
        el = OxmlElement('w:p')
        anchor._p.addprevious(el)
        p = Paragraph(el, anchor._parent)
        p.style = 'Normal'
        r = p.add_run(s)
        r.font.name = 'Noto Serif CJK SC'
        r.font.size = Pt(12)
        r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Noto Serif CJK SC')
    dst.parent.mkdir(parents=True,exist_ok=True)
    doc.save(dst)
    t = [p.text.strip() for p in Document(dst).paragraphs]
    idx = len(t)-1-t[::-1].index('7.2 主要创新点')
    assert t[idx-2:idx] == PARAS
    assert sum('39.78%' in x and '87.39%' in x for x in t) == 1
    return {'input_sha256':sha(src),'output_sha256':sha(dst),
            'added_paragraphs':2,'preserved_conclusions':4}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--docx',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--expected-sha256')
    a = p.parse_args()
    print(integrate(a.docx,a.out,a.expected_sha256))
