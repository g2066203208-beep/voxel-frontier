#!/usr/bin/env python3
"""Non-destructive Word pagination/figure/table repair for the S12 advisor manuscript.

No scientific text, image, mathematical formula, data table, or source content is changed.
Requires python-docx. Run with --self-test for a synthetic positive/negative fixture.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

CHAPTERS = tuple(f'第{x}章' for x in '一二三四五六')

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def set_onoff(parent, tag: str, value=True):
    elt = parent.find(qn('w:' + tag))
    if elt is None:
        elt = OxmlElement('w:' + tag)
        parent.append(elt)
    elt.set(qn('w:val'), '1' if value else '0')

def stats(doc):
    paragraphs = doc.paragraphs
    return {
        'paragraphs': len(paragraphs),
        'tables': len(doc.tables),
        'rows': sum(len(t.rows) for t in doc.tables),
        'inline_images': len(doc.inline_shapes),
        'math_nodes': sum(len(p._p.xpath('.//m:oMath')) for p in paragraphs) +
            sum(len(t._tbl.xpath('.//m:oMath')) for t in doc.tables),
        'text_sha256': hashlib.sha256(('\u241e'.join(p.text for p in paragraphs) + '\u241f' +
            '\u241e'.join('\u241d'.join(c.text for row in t.rows for c in row.cells)
                for t in doc.tables)).encode('utf-8')).hexdigest(),
        'chapter_titles': [p.text for p in paragraphs if p.style.name == 'Heading 1' and
            any(p.text.startswith(ch) for ch in CHAPTERS)],
    }

def refine(source: Path, target: Path, expected_sha: str | None = None):
    if not source.is_file():
        raise ValueError('MISSING_SOURCE')
    actual = sha256(source)
    if expected_sha and actual != expected_sha:
        raise ValueError(f'SOURCE_SHA_MISMATCH expected={expected_sha} actual={actual}')
    d = Document(source)
    before = stats(d)
    if len(before['chapter_titles']) != 6 or before['inline_images'] < 20:
        raise ValueError('INCOMPLETE_SIX_CHAPTER_MANUSCRIPT')
    changes = Counter()
    caption_style = d.styles['Caption']
    caption_style.font.size = Pt(10)
    caption_style.paragraph_format.space_after = Pt(5)
    caption_style.paragraph_format.keep_together = True
    for p in d.paragraphs:
        if p.style.name.startswith('Heading '):
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.keep_together = True
            changes['protected_headings'] += 1
        if p.style.name == 'Heading 1' and any(p.text.startswith(c) for c in CHAPTERS[1:]):
            p.paragraph_format.page_break_before = True
            changes['chapter_page_breaks'] += 1
        if p._p.xpath('.//w:drawing'):
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.keep_together = True
            changes['protected_figures'] += 1
        if not p.text.strip() and p._p.xpath('.//m:oMath'):
            p.paragraph_format.keep_together = True
            changes['protected_display_math'] += 1
        if p.style.name in ('Normal', 'Body Text'):
            pPr = p._p.get_or_add_pPr()
            set_onoff(pPr, 'widowControl')
            changes['widow_control_paragraphs'] += 1
    for i, p in enumerate(d.paragraphs):
        if i and d.paragraphs[i-1]._p.xpath('.//w:drawing') and p.text.strip().startswith('图'):
            p.style = caption_style
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_together = True
            changes['normalized_figure_captions'] += 1
    for table in d.tables:
        if not table.rows:
            continue
        for j, row in enumerate(table.rows):
            trPr = row._tr.get_or_add_trPr()
            set_onoff(trPr, 'cantSplit')
            if j == 0:
                set_onoff(trPr, 'tblHeader')
                changes['repeating_table_headers'] += 1
            changes['unsplittable_table_rows'] += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    d.save(target)
    after = stats(Document(target))
    if before != after:
        raise AssertionError(f'CONTENT_MUTATION {before} {after}')
    return {'source_sha256': actual, 'output_sha256': sha256(target),
            'source_stats': before, 'output_stats': after, 'layout_fixes': dict(changes),
            'scientific_content_unchanged': True,
            'status': 'OOXML_STRUCTURE_PASS_VISUAL_QA_REQUIRED'}

def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        d = Document()
        for ch in CHAPTERS:
            d.add_heading(ch + ' 测试', level=1)
            d.add_paragraph('来源内容必须保持不变')
        for _ in range(20):
            # Create 20 actual inline images without external libraries.
            import base64
            png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/o7sAAAAASUVORK5CYII=')
            img = root / 'pixel.png'
            img.write_bytes(png)
            d.add_paragraph().add_run().add_picture(str(img))
            d.add_paragraph('图：测试图')
        t=d.add_table(rows=2,cols=2)
        t.cell(0,0).text='变量';t.cell(0,1).text='数值'
        t.cell(1,0).text='A';t.cell(1,1).text='1'
        src=root/'source.docx';out=root/'out.docx';d.save(src)
        receipt=refine(src,out,sha256(src))
        assert receipt['layout_fixes']['chapter_page_breaks']==5
        assert receipt['layout_fixes']['repeating_table_headers']==1
        assert receipt['layout_fixes']['normalized_figure_captions']==20
        assert receipt['scientific_content_unchanged']
        try:
            refine(src,root/'bad.docx','0'*64)
        except ValueError as e:
            assert 'SOURCE_SHA_MISMATCH' in str(e)
        else:
            raise AssertionError('NEGATIVE_SHA_TEST_FAILED')
        again=refine(out,root/'again.docx',sha256(out))
        assert again['source_stats']==receipt['source_stats']
        print('SELF_TEST_PASS 6chapters 20figures 1table 1SHA_rejection idempotent_structure')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',nargs='?',type=Path)
    p.add_argument('output',nargs='?',type=Path)
    p.add_argument('--expected-sha256')
    p.add_argument('--receipt',type=Path)
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not a.source or not a.output:
        p.error('source and output required')
    r=refine(a.source,a.output,a.expected_sha256)
    if a.receipt:
        a.receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False))

if __name__=='__main__':
    main()
