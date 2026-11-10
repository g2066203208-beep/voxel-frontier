#!/usr/bin/env python3
"""Render SHA-locked six-chapter research Markdown into advisor-reading DOCX.
No Abaqus/CAE, solver, or scientific simulation is involved.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import cairosvg

IMG = re.compile(r'!\[([^\]]*)\]\(([^)]+?\.svg)\)')
CHAPTERS = tuple(f'# 第{i}章' for i in ('一','二','三','四','五','六'))
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def reject(cond: bool, message: str):
    if cond:
        raise ValueError(message)

def reference_docx(target: Path):
    d = Document()
    sec = d.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    sec.top_margin = sec.bottom_margin = Cm(2.5)
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.5)
    for name, size, bold in [('Normal', 11, False), ('Title', 20, True),
                             ('Heading 1', 16, True), ('Heading 2', 14, True),
                             ('Heading 3', 12, True), ('Caption', 9, False)]:
        s = d.styles[name]
        s.font.name = 'Times New Roman'
        s.font.size = Pt(size)
        s.font.bold = bold
        s._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), '宋体' if not bold else '黑体')
        s.paragraph_format.space_after = Pt(5 if name == 'Normal' else 9)
        if name == 'Normal':
            s.paragraph_format.line_spacing = 1.4
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run('研究母稿 · 导师内部阅读  |  ')
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), 'PAGE')
    footer._p.append(fld)
    d.save(target)

def build(source: Path, output: Path, expected_sha: str | None):
    source = source.resolve()
    reject(not source.is_file(), f'MISSING_SOURCE {source}')
    src_sha = sha256(source)
    reject(bool(expected_sha and src_sha != expected_sha),
           f'SOURCE_SHA_MISMATCH expected={expected_sha} actual={src_sha}')
    original = source.read_text(encoding='utf-8')
    reject(len(original) < 100_000, 'TRUNCATED_SIX_CHAPTER_SOURCE')
    reject(any(original.count(c) != 1 for c in CHAPTERS), 'CHAPTER_COUNT_OR_IDENTITY')
    reject('12阶段0/12' not in original and '12阶段**0/12' not in original,
           'MISSING_RESEARCH_LIMITATION')
    reject(original.count('DOI:') < 25, 'REFERENCE_LIST_INCOMPLETE')
    text = original[original.index(CHAPTERS[0]):]
    imgs = list(IMG.finditer(text))
    reject(len(imgs) < 20, f'FIGURE_COVERAGE_TOO_LOW {len(imgs)}')
    seen = set()
    image_receipts = []
    with tempfile.TemporaryDirectory(prefix='s12_advisor_docx_') as t:
        temp = Path(t)
        figures = temp / 'figures'
        figures.mkdir()
        def convert(m):
            caption, rel = m.group(1), m.group(2)
            svg = (source.parent / rel).resolve()
            reject(not svg.is_file(), f'MISSING_FIGURE {rel}')
            reject(not svg.is_relative_to(source.parents[3]), f'FIGURE_OUTSIDE_RESEARCH {rel}')
            data = svg.read_bytes()
            reject(b'<svg' not in data[:2000], f'INVALID_SVG {rel}')
            digest = hashlib.sha256(data).hexdigest()
            dst = figures / f'{digest[:20]}.png'
            if digest not in seen:
                cairosvg.svg2png(bytestring=data, write_to=str(dst), output_width=1700)
                seen.add(digest)
            image_receipts.append({'caption':caption,'source':rel,'sha256':digest,'png':dst.name})
            return f'![{caption}]({dst.as_posix()})'
        body = IMG.sub(convert, text)
        reject(body.count('![') > len(image_receipts), 'UNHANDLED_IMAGE_SYNTAX')
        front = ('# 10 MW级陆上风机预应力混凝土—钢混合塔架\n\n'
                 '## 六章研究母稿（导师内部阅读版）\n\n'
                 '**研究对象：** DTU 10 MW，158 m混合塔架（混凝土112 m、钢塔46 m）。\n\n'
                 '**证据状态：** 12阶段整阶段验收0/12；正式DLC1.2为0/126；'
                 '局部材料Miner寿命、真实结构优化及同态风震响应尚未闭合。'
                 '**本文件不是学位论文送审版，不得将筛查结果作为结构安全证明。**\n\n'
                 f'**源文件SHA256：** {src_sha}。图表按现有研究母稿嵌入，原Word媒体尚未完整恢复。\n\n'
                 '---\n\n')
        md = temp / 'advisor.md'
        # Pandoc's math parser rejects the legacy plain-TeX \rm control word.
        # Convert only this typographic command in the transient DOCX input;
        # do not alter the evidence-locked research manuscript.
        body = re.sub(r'\\rm\s*([A-Za-z]+)', r'\\mathrm{\1}', body)
        md.write_text(front + body, encoding='utf-8')
        ref = temp / 'reference.docx'
        reference_docx(ref)
        output.parent.mkdir(parents=True, exist_ok=True)
        pandoc = shutil.which('pandoc')
        if not pandoc:
            import pypandoc
            pandoc = pypandoc.get_pandoc_path()
        command = [pandoc, str(md), '--from=markdown+tex_math_single_backslash+tex_math_dollars+pipe_tables',
                   '--to=docx', '--standalone', f'--reference-doc={ref}',
                   '--wrap=none', f'--output={output}']
        p = subprocess.run(command, text=True, capture_output=True)
        reject(p.returncode != 0, f'PANDOC_FAILED {p.stderr[-4000:]}')
        reject('Could not convert TeX math' in p.stderr, f'MATH_CONVERSION_WARNING {p.stderr[-1000:]}')
        with zipfile.ZipFile(output) as z:
            reject(z.testzip() is not None, 'DOCX_ZIP_CRC')
            media = [n for n in z.namelist() if n.startswith('word/media/')]
            reject(len(media) != len(seen), f'EMBEDDED_MEDIA_COUNT {len(media)} vs {len(seen)}')
            doc = ET.fromstring(z.read('word/document.xml'))
            maths = len(doc.findall('.//m:oMath', NS))
            tables = len(doc.findall('.//w:tbl', NS))
            reject(maths < 10, f'MATH_OBJECT_COUNT_TOO_LOW {maths}')
            reject(tables < 8, f'TABLE_COUNT_TOO_LOW {tables}')
        return {'status':'DOCX_SOURCE_ASSEMBLY_PASS_NOT_PHYSICS',
                'source':str(source),'source_sha256':src_sha,
                'output_sha256':sha256(output), 'output_bytes':output.stat().st_size,
                'figure_occurrences':len(image_receipts), 'unique_embedded_figures':len(media),
                'math_objects':maths,'tables':tables,'figures':image_receipts,
                'pandoc_stderr':p.stderr[-2000:],
                'limitations':['No original Word media reconstruction',
                               'No native physical verification',
                               'No claim of thesis submission readiness']}

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--source',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    a.add_argument('--expected-sha256')
    a.add_argument('--receipt',type=Path)
    args=a.parse_args()
    r=build(args.source,args.output,args.expected_sha256)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        args.receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k!='figures'},ensure_ascii=False))

if __name__=='__main__':
    main()
