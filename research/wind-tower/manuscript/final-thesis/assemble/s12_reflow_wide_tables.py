#!/usr/bin/env python3
"""Reflow wide Pandoc tables in the S12 advisor-reading Word into 3-column record/metric/value tables.

Non-CAE, non-physics. Keeps each original table cell's complete OOXML (including OMML),
with deterministic source-SHA gate, lossless reverse projection, and negative fixtures.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, tempfile
from collections import Counter
from pathlib import Path
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

INPUT_SHA = '0cd5ecafcef5e1bf5e01363b0d9d7baa5c866081ceba2058d68b35cbc9ed3367'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def assert_source(p, expected):
    if not Path(p).is_file(): raise ValueError('MISSING_SOURCE')
    if sha(p)!=expected: raise ValueError('SOURCE_SHA_MISMATCH')

def cell_payload(cell):
    # Pandoc's legacy Compact paragraph style breaks Word/LO table layout.
    # Keep all content nodes (text runs, math, hyperlinks), discard only cell paragraph formatting.
    payload=[]
    for x in cell._tc:
        if x.tag==qn('w:tcPr'):continue
        y=copy.deepcopy(x)
        if y.tag==qn('w:p'):
            for z in list(y):
                if z.tag==qn('w:pPr'):y.remove(z)
        payload.append(y)
    return payload

def cell_signature(cell):
    from lxml import etree
    return b''.join(etree.tostring(x,method='c14n') for x in cell_payload(cell))

def copy_payload(source,target):
    tc=target._tc
    for child in list(tc):
        if child.tag!=qn('w:tcPr'):tc.remove(child)
    for child in cell_payload(source):tc.append(child)

def set_flag(parent, local):
    elt=parent.find(qn('w:'+local))
    if elt is None: elt=OxmlElement('w:'+local); parent.append(elt)
    elt.set(qn('w:val'),'1')

def style_table(table, widths):
    table.style='Table Grid'
    table.autofit=False
    table._tbl.tblPr.find(qn('w:tblLayout')).set(qn('w:type'),'fixed')
    # Explicit tblGrid and tcW are needed for reliable LibreOffice/Word pagination.
    for grid,cm in zip(table._tbl.tblGrid, widths):
        grid.set(qn('w:w'),str(int(Cm(cm).twips)))
    for i,row in enumerate(table.rows):
        for j,cell in enumerate(row.cells):
            # Reset legacy table-cell pPr while retaining every run and OMML node.
            for p in cell.paragraphs:
                for x in list(p._p):
                    if x.tag==qn('w:pPr'):p._p.remove(x)
            cell.width=Cm(widths[j]); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cell.paragraphs:
                p.paragraph_format.space_before=Pt(0)
                p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.line_spacing=1.05
                for run in p.runs:
                    run.font.size=Pt(8.5)
            # Leave OMML nodes untouched.
        trPr=row._tr.get_or_add_trPr()
        set_flag(trPr,'cantSplit')
        if i==0: set_flag(trPr,'tblHeader')

def reflow_table(doc, original):
    ncol=len(original.columns)
    if ncol<5: raise ValueError('REFLOW_ONLY_WIDE_TABLES')
    if len(original.rows)<2: raise ValueError('EMPTY_DATA_TABLE')
    before=[[cell_signature(c) for c in row.cells] for row in original.rows]
    # Reject merges and non-rectangular tables rather than silently misaligning data.
    for row in original.rows:
        if len(row.cells)!=ncol: raise ValueError('NON_RECTANGULAR_TABLE')
        for cell in row.cells:
            if cell._tc.grid_span>1: raise ValueError('MERGED_SOURCE_CELL')
    out=doc.add_table(rows=1+(len(original.rows)-1)*(ncol-1),cols=3)
    original._tbl.addnext(out._tbl)
    copy_payload(original.cell(0,0),out.cell(0,0))
    out.cell(0,1).text='指标（原表列名）'
    out.cell(0,2).text='数值（原表对应行）'
    for i in range(1,len(original.rows)):
        for j in range(1,ncol):
            k=1+(i-1)*(ncol-1)+(j-1)
            copy_payload(original.cell(i,0),out.cell(k,0))
            copy_payload(original.cell(0,j),out.cell(k,1))
            copy_payload(original.cell(i,j),out.cell(k,2))
    # Verify complete reverse mapping including math XML. We don't compare font/width props.
    for i in range(1,len(original.rows)):
        for j in range(1,ncol):
            k=1+(i-1)*(ncol-1)+(j-1)
            assert cell_signature(original.cell(i,0))==cell_signature(out.cell(k,0))
            assert cell_signature(original.cell(0,j))==cell_signature(out.cell(k,1))
            assert cell_signature(original.cell(i,j))==cell_signature(out.cell(k,2))
    assert cell_signature(original.cell(0,0))==cell_signature(out.cell(0,0))
    original._tbl.getparent().remove(original._tbl)
    style_table(out,[3.5,6.8,5.2])
    return {'original_rows':len(before),'original_columns':ncol,'new_rows':len(out.rows)}

def content_identity(doc):
    # Compare prose, images, and math outside tables; source table cell identities checked in reflow_table.
    from lxml import etree
    parts=[etree.tostring(p._p,method='c14n') for p in doc.paragraphs if not (p._p.xpath('.//w:pict') and not p._p.xpath('.//w:t'))]
    return hashlib.sha256(b''.join(parts)).hexdigest()

def stats(doc):
    return {'paragraphs':len(doc.paragraphs),'tables':len(doc.tables),'inline_images':len(doc.inline_shapes),
            'math_nodes':len(doc.element.body.xpath('.//m:oMath')),
            'headings':[p.text for p in doc.paragraphs if p.style.name=='Heading 1']}

def remove_decorative_hr_before_chapters(doc):
    # Pandoc's standalone horizontal-rule VML paragraphs before page-break headings
    # can create a fully blank page; remove only content-free HR, never a text/image/math paragraph.
    removed=0
    for p in list(doc.paragraphs):
        if p.style.name!='Heading 1' or not p.text.startswith('第'):continue
        q=p._p.getprevious()
        while q is not None:
            if q.tag in (qn('w:bookmarkStart'),qn('w:bookmarkEnd')):
                q=q.getprevious();continue
            if q.tag==qn('w:p') and q.xpath('.//w:pict') and not q.xpath('.//w:t') and not q.xpath('.//m:oMath') and not q.xpath('.//w:drawing'):
                bef=q.getprevious();q.getparent().remove(q);removed+=1;q=bef;continue
            break
    return removed

def process(source,target,expected_sha):
    assert_source(source,expected_sha)
    d=Document(source); b=stats(d); para_hash=content_identity(d)
    if len(b['headings'])<6 or b['inline_images']<20 or len(d.tables)<30:
        raise ValueError('INCOMPLETE_ADVISOR_MANUSCRIPT')
    selected=[]; transformations=[]
    for i,table in enumerate(list(d.tables)):
        if len(table.columns)>=5:
            transformations.append((i,reflow_table(d,table)))
        else:
            # Fix original narrow tables too: explicit 3/4-column widths and visible grid.
            style_table(table,[15.5/len(table.columns)]*len(table.columns))
    removed_hr=remove_decorative_hr_before_chapters(d)
    a=stats(d)
    if content_identity(d)!=para_hash or a['inline_images']!=b['inline_images'] or a['paragraphs']!=b['paragraphs']-removed_hr:
        raise AssertionError('PROSE_OR_FIGURE_CHANGED')
    if a['math_nodes']<b['math_nodes']:
        raise AssertionError('MATH_LOSS')
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True);d.save(target)
    check=Document(target)
    if stats(check)!=a: raise AssertionError('DOCX_RELOAD_MISMATCH')
    return {'source_sha256':sha(source),'output_sha256':sha(target),
            'source':b,'result':a,'reflowed_tables':len(transformations),
            'reflowed_indices':[i for i,_ in transformations], 'removed_decorative_hr':removed_hr,
            'original_table_cell_mapping':'PASS_COMPLETE_OOXML_INCLUDING_MATH',
            'prose_and_figure_preserved':True,
            'status':'DOCX_STRUCTURE_PASS_VISUAL_QA_REQUIRED'}

def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp); d=Document()
        for i,ch in enumerate('一二三四五六'): d.add_heading('第'+ch+'章',1)
        import base64
        img=p/'pixel.png';img.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/o7sAAAAASUVORK5CYII='))
        for j in range(24):d.add_picture(str(img))
        for j in range(36):
            t=d.add_table(rows=3,cols=6)
            for r in range(3):
                for c in range(6):t.cell(r,c).text=f'0-{j}-{r}-{c}'
        src=p/'a.docx';dst=p/'b.docx';d.save(src)
        rec=process(src,dst,sha(src));assert rec['reflowed_tables']==36
        try: process(src,p/'bad.docx','0'*64)
        except ValueError as e: assert 'SOURCE_SHA_MISMATCH' in str(e)
        else: raise AssertionError('BAD_SHA_ACCEPTED')
        d2=Document(dst)
        assert len(d2.tables)==36 and all(len(t.columns)==3 for t in d2.tables)
        assert d2.tables[0].cell(1,1).text=='0-0-0-1'
        assert d2.tables[0].cell(1,2).text=='0-0-1-1'
        print('SELFTEST_PASS 36_wide_tables 24_figures 6_chapters SHA_rejection reverse_projection')

def main():
    p=argparse.ArgumentParser();p.add_argument('source',nargs='?',type=Path);p.add_argument('target',nargs='?',type=Path)
    p.add_argument('--expected-sha256');p.add_argument('--receipt',type=Path);p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:return selftest()
    if not a.source or not a.target:p.error('source and target required')
    r=process(a.source,a.target,a.expected_sha256 or INPUT_SHA)
    if a.receipt:a.receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
