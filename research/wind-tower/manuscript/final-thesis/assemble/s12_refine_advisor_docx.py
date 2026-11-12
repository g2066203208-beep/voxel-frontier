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
from docx.shared import Cm, Pt

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

def normalize_undefined_compact_table_styles(doc):
    """Remove orphan Pandoc Compact style references from table paragraphs.

    The 2026-11-11 advisor DOCX references Compact in 928 table-cell
    paragraphs, although Compact is absent from the style definitions.
    LibreOffice then lays table cells out vertically over many pages.
    Remove only the undefined style reference; preserve text, runs and OMML.
    """
    known = {style.style_id for style in doc.styles}
    if 'Compact' in known:
        return 0
    fixed = 0
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    ppr = paragraph._p.pPr
                    if ppr is None:
                        continue
                    style = ppr.find(qn('w:pStyle'))
                    if style is not None and style.get(qn('w:val')) == 'Compact':
                        ppr.remove(style)
                        fixed += 1
    return fixed

def rebuild_etm_control_table(doc):
    """Replace the malformed Pandoc three-column ETM table without changing any cell text.

    This avoids a verified LibreOffice/Word pagination defect where the preceding
    paragraph is wrapped into the last column and the data cells are unstacked.
    """
    headers = ('ETM工况', '双点DEL4保留率/%', '双点最大正峰保留率/%')
    matches = [t for t in doc.tables if len(t.columns) == 3 and len(t.rows) == 5
               and tuple(c.text for c in t.rows[0].cells) == headers]
    if len(matches) > 1:
        raise ValueError('DUPLICATE_ETM_CONTROL_TABLE')
    if not matches:
        if any('4.7.22 四组真实ETM' in p.text for p in doc.paragraphs):
            raise ValueError('MISSING_ETM_CONTROL_TABLE')
        return 0  # synthetic layout self-test has no ETM research table
    old = matches[0]
    if old._tbl.xpath('.//m:oMath') or old._tbl.xpath('.//w:drawing'):
        raise ValueError('NON_TEXT_ETM_TABLE_UNSAFE_TO_REBUILD')
    before = [[c.text for c in row.cells] for row in old.rows]
    replacement = doc.add_table(rows=5, cols=3)
    for i, row in enumerate(before):
        for j, value in enumerate(row):
            replacement.cell(i, j).text = value
    replacement.style = 'Table Grid'
    replacement.autofit = False
    widths = (5.5, 5.0, 5.0)
    for j, col in enumerate(replacement.columns):
        col.width = Cm(widths[j])
    for i, row in enumerate(replacement.rows):
        for j, cell in enumerate(row.cells):
            cell.width = Cm(widths[j])
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.1
                for run in paragraph.runs:
                    run.font.size = Pt(9)
        if i == 0:
            trPr = row._tr.get_or_add_trPr()
            header = OxmlElement('w:tblHeader')
            header.set(qn('w:val'), '1')
            trPr.append(header)
    old._tbl.addnext(replacement._tbl)
    old._tbl.getparent().remove(old._tbl)
    after = [[c.text for c in row.cells] for row in replacement.rows]
    if before != after:
        raise AssertionError('ETM_TABLE_CELL_TEXT_CHANGED')
    return 1


def repair_s10_hyperlink_glyph_artifact(doc):
    """Word-only fix for a verified LO stray 'X' after the §4.7.23 source sentence.

    Keep the two visible source labels verbatim. The clickable source links
    remain in the canonical Markdown; only this generated DOCX uses plain runs.
    Refuse unexpected hyperlink counts instead of silently changing text.
    """
    candidates = [p for p in doc.paragraphs
                  if p.text.startswith('研究问题。 对同一四组历史ETM×31')]
    if not candidates:
        return 0
    if len(candidates) != 1:
        raise ValueError('AMBIGUOUS_S10_SOURCE_PARAGRAPH')
    p = candidates[0]
    links = list(p._p.findall(qn('w:hyperlink')))
    if not links:
        return 0
    if len(links) != 2:
        raise ValueError('UNEXPECTED_S10_HYPERLINK_COUNT')
    for link in links:
        parent = link.getparent()
        pos = parent.index(link)
        for child in list(link):
            parent.insert(pos, child)
            pos += 1
        parent.remove(link)
    return len(links)


def keep_s10_regret_table_together(doc):
    """Render the existing 4-row §4.7.24 result table without a page split.

    No table value is edited. This prevents the observed 140/141-page
    header/body split in the 2026-11-12 Actions artifact.
    """
    tables = [t for t in doc.tables
              if len(t.columns) == 4
              and t.cell(0, 0).text == '代理选控方法'
              and t.cell(0, 1).text == '改变控制工况的塔段']
    if not tables:
        if any('4.7.24 同步目标选控后悔度' in p.text for p in doc.paragraphs):
            raise ValueError('MISSING_S10_REGRET_TABLE')
        return 0
    if len(tables) != 1 or len(tables[0].rows) != 4:
        raise ValueError('AMBIGUOUS_S10_REGRET_TABLE')
    table = tables[0]
    table.style = 'Table Grid'
    table.autofit = False
    widths = (4.2, 3.8, 4.5, 3.2)
    for j, column in enumerate(table.columns):
        column.width = Cm(widths[j])
    for i, row in enumerate(table.rows):
        set_onoff(row._tr.get_or_add_trPr(), 'cantSplit')
        for j, cell in enumerate(row.cells):
            cell.width = Cm(widths[j])
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.05
                if i < len(table.rows) - 1:
                    paragraph.paragraph_format.keep_with_next = True
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    return 1

def keep_s11_minimax_table_together(doc):
    """Keep the six-row real T071 minimax result table on one page.

    The 2026-11-12 rendered artifact split the six-row table across pages
    152 and 153. Only paragraph pagination properties change, not cell text.
    """
    tables = [t for t in doc.tables
              if len(t.rows) == 6 and len(t.columns) == 3
              and t.cell(0, 0).text == '指标（仅T071历史固定内力）'
              and t.cell(0, 2).text == '等体积解析构造']
    if not tables:
        if any('5.3.4 31段固定内力' in p.text for p in doc.paragraphs):
            raise ValueError('MISSING_S11_MINIMAX_TABLE')
        return 0
    if len(tables) != 1:
        raise ValueError('AMBIGUOUS_S11_MINIMAX_TABLE')
    table = tables[0]
    for i, row in enumerate(table.rows):
        set_onoff(row._tr.get_or_add_trPr(), 'cantSplit')
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.keep_with_next = i < len(table.rows) - 1
                paragraph.paragraph_format.keep_together = True
                paragraph.paragraph_format.space_after = Pt(0)
    return 1

def keep_s06_spectral_table_together(doc):
    """Keep all seven rows of the real 18-NTM six-column spectral table together.

    Visual QA of Actions #43166604078 found the final My row split onto the
    following page. This changes only pagination flags, not scientific data.
    """
    matches = [t for t in doc.tables
               if len(t.columns) == 6 and t.cell(0, 0).text == '塔底反力'
               and '实际风速' in t.cell(0, 1).text]
    if not matches:
        if any('3.7.23 真实18组NTM' in p.text for p in doc.paragraphs):
            raise ValueError('MISSING_S06_SPECTRAL_TABLE')
        return 0
    if len(matches) != 1 or len(matches[0].rows) != 7:
        raise ValueError('AMBIGUOUS_S06_SPECTRAL_TABLE')
    table = matches[0]
    for i, row in enumerate(table.rows):
        set_onoff(row._tr.get_or_add_trPr(), 'cantSplit')
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.keep_with_next = i < len(table.rows) - 1
                paragraph.paragraph_format.keep_together = True
                paragraph.paragraph_format.space_after = Pt(0)
    return 1


def _compact_science_table(table, widths, font_pt):
    """Correct two observed page-level table defects; never edit cell text/OMML."""
    if len(widths) != len(table.columns) or abs(sum(widths) - 15.5) > 0.01:
        raise ValueError('SCIENCE_TABLE_WIDTH_INVALID')
    table.style = 'Table Grid'
    table.autofit = False
    layout = table._tbl.tblPr.find(qn('w:tblLayout'))
    if layout is None:
        layout = OxmlElement('w:tblLayout')
        table._tbl.tblPr.append(layout)
    layout.set(qn('w:type'), 'fixed')
    for col, width in zip(table.columns, widths):
        col.width = Cm(width)
    for row_number, row in enumerate(table.rows):
        trpr = row._tr.get_or_add_trPr()
        if trpr.find(qn('w:cantSplit')) is None:
            trpr.append(OxmlElement('w:cantSplit'))
        if row_number == 0 and trpr.find(qn('w:tblHeader')) is None:
            trpr.append(OxmlElement('w:tblHeader'))
        for cell, width in zip(row.cells, widths):
            cell.width = Cm(width)
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                paragraph.paragraph_format.keep_together = True
                if row_number:
                    ppr = paragraph._p.get_or_add_pPr()
                    if ppr.find(qn('w:noWrap')) is None:
                        ppr.append(OxmlElement('w:noWrap'))
                for run in paragraph.runs:
                    run.font.size = Pt(font_pt + (0.2 if row_number == 0 else 0))


def restore_s05_figure_and_compact_tables(target: Path, figure: Path):
    """Restore missing source-locked Fig A-14 and fix verified 7x6/3x7 tables.

    The previous 194-page DOCX passed structural QA yet lacked Fig A-14;
    its 7x6 table split long case IDs across lines and its 3x7 numeric
    table split decimal values. Preserve every existing scientific cell,
    paragraph and OMML node. Only add the original SVG and its caption.
    """
    import io
    import cairosvg
    figure_sha = '11d47d347463987ad9e77933b69d4d13963b0f8231f66807cf72770f997d8964'
    if not figure.is_file() or sha256(figure) != figure_sha:
        raise ValueError('S05_FIGURE_SHA_MISMATCH')
    doc = Document(target)
    before_tables = [[[c.text for c in row.cells] for row in t.rows] for t in doc.tables]
    before_paragraphs = [p.text for p in doc.paragraphs]
    before_figures = len(doc.inline_shapes)
    before_math = stats(doc)['math_nodes']
    s10 = [t for t in doc.tables if len(t.rows) == 7 and len(t.columns) == 6
           and t.cell(0, 0).text == '通道' and t.cell(0, 2).text == '控制工况']
    s05 = [t for t in doc.tables if len(t.rows) == 3 and len(t.columns) == 7
           and t.cell(0, 0).text == '33点源谱']
    if len(s10) != 1 or len(s05) != 1:
        raise ValueError('SCIENCE_TABLE_NOT_UNIQUE')
    if any(p.text.startswith('图A-14：') for p in doc.paragraphs):
        raise ValueError('DUPLICATE_S05_FIGURE')
    _compact_science_table(s10[0], [0.8, 0.85, 3.15, 2.5, 2.15, 6.05], 7.8)
    _compact_science_table(s05[0], [1.4, 2.15, 2.15, 2.0, 2.2, 2.1, 3.5], 7.4)
    image = doc.add_paragraph()
    image.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image.paragraph_format.keep_with_next = True
    image.paragraph_format.keep_together = True
    png = cairosvg.svg2png(bytestring=figure.read_bytes(), output_width=1800)
    image.add_run().add_picture(io.BytesIO(png), width=Cm(14.7))
    caption = doc.add_paragraph('图A-14：ESM处理谱与示意目标谱的33周期单尺度极小极大比较（非设计谱验收）')
    caption.style = doc.styles['Caption']
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.keep_together = True
    s05[0]._tbl.addnext(image._p)
    image._p.addnext(caption._p)
    temp = target.with_name(target.stem + '_qa_temp.docx')
    doc.save(temp)
    verified = Document(temp)
    after_tables = [[[c.text for c in row.cells] for row in t.rows] for t in verified.tables]
    after_paragraphs = [p.text for p in verified.paragraphs]
    cap_idx = [i for i, value in enumerate(after_paragraphs) if value.startswith('图A-14：')]
    if before_tables != after_tables:
        raise AssertionError('SCIENCE_TABLE_DATA_CHANGED')
    if len(cap_idx) != 1 or cap_idx[0] < 1:
        raise AssertionError('S05_CAPTION_NOT_UNIQUE')
    index = cap_idx[0]
    if after_paragraphs[index - 1] != '' or before_paragraphs != (after_paragraphs[:index - 1] + after_paragraphs[index + 1:]):
        raise AssertionError('SCIENCE_PROSE_CHANGED')
    if len(verified.inline_shapes) != before_figures + 1 or stats(verified)['math_nodes'] != before_math:
        raise AssertionError('FIGURE_OR_OMML_IDENTITY_CHANGED')
    temp.replace(target)
    return {'source_figure_sha256': figure_sha, 'embedded_figures_before': before_figures,
            'embedded_figures_after': len(verified.inline_shapes),
            'table_cell_text_unchanged': True, 'old_prose_unchanged': True,
            'math_nodes_unchanged': before_math,
            'fixed_tables': ['S10_7x6', 'S05_3x7'],
            'figure_restored': 'FIG_S05_33PERIOD_SCALAR_MINIMAX_20261113.svg',
            'output_sha256': sha256(target)}

def refine(source: Path, target: Path, expected_sha: str | None = None):
    if not source.is_file():
        raise ValueError('MISSING_SOURCE')
    actual = sha256(source)
    if expected_sha and actual != expected_sha:
        raise ValueError(f'SOURCE_SHA_MISMATCH expected={expected_sha} actual={actual}')
    d = Document(source)
    before = stats(d)
    compact_fixes = normalize_undefined_compact_table_styles(d)
    rebuilt_etm_table = rebuild_etm_control_table(d)
    s10_links = repair_s10_hyperlink_glyph_artifact(d)
    s10_regret_table = keep_s10_regret_table_together(d)
    s11_minimax_table = keep_s11_minimax_table_together(d)
    s06_spectral_table = keep_s06_spectral_table_together(d)
    if len(before['chapter_titles']) != 6 or before['inline_images'] < 20:
        raise ValueError('INCOMPLETE_SIX_CHAPTER_MANUSCRIPT')
    changes = Counter()
    changes['rebuilt_etm_control_table'] = rebuilt_etm_table
    changes['s10_hyperlinks_unwrapped_for_lo_glyph'] = s10_links
    changes['s10_regret_table_kept_together'] = s10_regret_table
    changes['s11_minimax_table_kept_together'] = s11_minimax_table
    changes['s06_spectral_table_kept_together'] = s06_spectral_table
    changes['normalized_undefined_compact_table_paragraphs'] = compact_fixes
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
        orphan = OxmlElement('w:pStyle')
        orphan.set(qn('w:val'), 'Compact')
        t.cell(0,0).paragraphs[0]._p.get_or_add_pPr().insert(0, orphan)
        t.cell(1,0).text='A';t.cell(1,1).text='1'
        src=root/'source.docx';out=root/'out.docx';d.save(src)
        receipt=refine(src,out,sha256(src))
        assert receipt['layout_fixes']['chapter_page_breaks']==5
        assert receipt['layout_fixes']['repeating_table_headers']==1
        assert receipt['layout_fixes']['normalized_undefined_compact_table_paragraphs']==1
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
        assert again['layout_fixes']['normalized_undefined_compact_table_paragraphs']==0
        # Positive and idempotent regression fixtures for the real S10 layout defect.
        mini = Document()
        p = mini.add_paragraph('研究问题。 对同一四组历史ETM×31个混凝土塔段')
        for label in ('124行分量源', '1984行同步16方位源'):
            h = OxmlElement('w:hyperlink')
            rr = OxmlElement('w:r')
            tt = OxmlElement('w:t')
            tt.text = label
            rr.append(tt)
            h.append(rr)
            p._p.append(h)
        tbl = mini.add_table(rows=4, cols=4)
        for j, value in enumerate(('代理选控方法', '改变控制工况的塔段',
                                   '同步目标后悔度范围', '31段平均后悔度')):
            tbl.cell(0, j).text = value
        for i in range(1, 4):
            for j in range(4):
                tbl.cell(i, j).text = str(i * 4 + j)
        mini_before = stats(mini)
        assert repair_s10_hyperlink_glyph_artifact(mini) == 2
        assert keep_s10_regret_table_together(mini) == 1
        assert stats(mini) == mini_before
        assert repair_s10_hyperlink_glyph_artifact(mini) == 0
        assert keep_s10_regret_table_together(mini) == 1
        assert stats(mini) == mini_before
        # Real S11 six-row table: preserve all values, keep every row together.
        s11 = mini.add_table(rows=6, cols=3)
        for j, value in enumerate(('指标（仅T071历史固定内力）', '基准截面', '等体积解析构造')):
            s11.cell(0, j).text = value
        for i in range(1, 6):
            for j in range(3):
                s11.cell(i, j).text = str(i * 3 + j)
        before_s11 = stats(mini)
        assert keep_s11_minimax_table_together(mini) == 1
        assert keep_s11_minimax_table_together(mini) == 1
        assert stats(mini) == before_s11
        s11_copy = mini.add_table(rows=6, cols=3)
        s11_copy.cell(0, 0).text = '指标（仅T071历史固定内力）'
        s11_copy.cell(0, 2).text = '等体积解析构造'
        try:
            keep_s11_minimax_table_together(mini)
        except ValueError as e:
            assert 'AMBIGUOUS_S11_MINIMAX_TABLE' in str(e)
        else:
            raise AssertionError('S11_DUPLICATE_TABLE_ACCEPTED')
        # Real S06 seven-row six-column spectral table: page-unified, byte-stable.
        s06 = mini.add_table(rows=7, cols=6)
        s06.cell(0, 0).text = '塔底反力'
        s06.cell(0, 1).text = '实际风速/m·s⁻¹'
        for i in range(1, 7):
            for j in range(6):
                s06.cell(i, j).text = str(i * 6 + j)
        before_s06 = stats(mini)
        assert keep_s06_spectral_table_together(mini) == 1
        assert keep_s06_spectral_table_together(mini) == 1
        assert stats(mini) == before_s06
        s06_copy = mini.add_table(rows=7, cols=6)
        s06_copy.cell(0, 0).text = '塔底反力'
        s06_copy.cell(0, 1).text = '实际风速/m·s⁻¹'
        try:
            keep_s06_spectral_table_together(mini)
        except ValueError as e:
            assert 'AMBIGUOUS_S06_SPECTRAL_TABLE' in str(e)
        else:
            raise AssertionError('S06_DUPLICATE_TABLE_ACCEPTED')
        # Refuse an ambiguous matching source paragraph.
        mini.add_paragraph('研究问题。 对同一四组历史ETM×31重复')
        try:
            repair_s10_hyperlink_glyph_artifact(mini)
        except ValueError as e:
            assert 'AMBIGUOUS_S10_SOURCE_PARAGRAPH' in str(e)
        else:
            raise AssertionError('S10_DUPLICATE_PARAGRAPH_ACCEPTED')
        print('SELF_TEST_PASS 6chapters 20figures 1table S10_regret_layout S11_minimax_layout S06_spectral_layout S10_hyperlink_regression SHA_rejection idempotent_structure')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',nargs='?',type=Path)
    p.add_argument('output',nargs='?',type=Path)
    p.add_argument('--expected-sha256')
    p.add_argument('--receipt',type=Path)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--s05-figure',type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not a.source or not a.output:
        p.error('source and output required')
    r=refine(a.source,a.output,a.expected_sha256)
    if a.s05_figure:
        r['visual_science_qa']=restore_s05_figure_and_compact_tables(a.output,a.s05_figure)
        r['output_sha256']=sha256(a.output)
        r['status']='SCIENCE_TABLE_AND_FIGURE_SOURCE_PASS_VISUAL_QA_REQUIRED'
    if a.receipt:
        a.receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False))

if __name__=='__main__':
    main()
