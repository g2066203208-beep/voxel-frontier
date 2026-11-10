#!/usr/bin/env python3
"""Restore eight *unaltered* ERA5 figures from R5 into a separate Word evidence appendix.
No solver, structural-model or Abaqus files are read or modified.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,re
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image

R5_SHA='da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9'
BASE_SHA='73eebcd702d89ce4926153b755287d9d41c0b9510157c00658e27675d3dcca32'
POSITIONS=[275,278,281,284,286,289,291,294]
LABELS=['图3-1(a)','图3-1(b)','图3-2','图3-3(a)','图3-3(b)','图3-4(a)','图3-4(b)','图3-5']

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def raw(path:Path)->bytes:return path.read_bytes()

def run(source:Path,base:Path,output:Path,manifest:Path,figdir:Path):
    assert digest(raw(source))==R5_SHA,'R5 source SHA mismatch: refusing substitution'
    assert digest(raw(base))==BASE_SHA,'advisor DOCX SHA mismatch: refusing substitution'
    r5=Document(source); doc=Document(base)
    assert len(doc.inline_shapes)==28,'base image count drift'
    assert len(doc.tables)==37,'base table count drift'
    figdir.mkdir(parents=True,exist_ok=True)
    images=[]
    for pidx,label in zip(POSITIONS,LABELS):
        p=r5.paragraphs[pidx];bs=p._p.xpath('.//a:blip')
        assert len(bs)==1,f'{pidx}: expected one embedded image'
        rid=bs[0].get(qn('r:embed'));part=r5.part.related_parts[rid]
        data=part.blob
        caption=r5.paragraphs[pidx+1].text.strip()
        assert caption.startswith(label),f'{pidx}: caption mismatch {caption!r}'
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
        im=Image.open(io.BytesIO(data))
        assert im.format=='PNG',f'{pidx}: not original PNG'
        fname=f'R5_{label.replace("(","_").replace(")","").replace("-","_")}_{digest(data)[:12]}.png'
        (figdir/fname).write_bytes(data)
        images.append(dict(r5_paragraph=pidx,original_label=label,original_caption=caption,sha256=digest(data),bytes=len(data),width_px=im.width,height_px=im.height,filename=fname,source_sha256=R5_SHA))
    # Separate evidence appendix: do not renumber six-chapter scientific figures.
    doc.add_page_break()
    doc.add_heading('原R5第三章ERA5图源证据附录（非正式章节编号）',level=1)
    doc.add_paragraph('以下八幅图直接从2026-08-27 R5 Word的原始OOXML图片部件提取并原字节嵌入，未重新绘制、重采样或改写数据。此附录只用于图源回链和导师对照，不替代现行第三章统计方法与正式设计工况验收。')
    doc.add_paragraph('来源Word SHA256：'+R5_SHA+'。源图位于原稿正文第275、278、281、284、286、289、291、294段；原图题逐字保留。')
    for rec in images:
        h=doc.add_paragraph();h.style='Heading 2';h.add_run(rec['original_label']+'｜原稿图源')
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        with (figdir/rec['filename']).open('rb') as f:
            p.add_run().add_picture(f,width=Cm(13.7))
        cp=doc.add_paragraph(rec['original_caption']);cp.alignment=WD_ALIGN_PARAGRAPH.CENTER
        cp.add_run('\n原图字节SHA256：'+rec['sha256'])
        doc.add_paragraph('证据边界：本图为R5稿中的ERA5历史统计图，不能据此宣称已验证IEC设计参考风速、具体风电场址或结构疲劳寿命。')
    doc.save(output)
    check=Document(output)
    assert len(check.inline_shapes)==36,'expected 28 existing + 8 restored images'
    assert len(check.tables)==37,'unexpected table mutation'
    # Verify all original image bytes remain present, plus the exact eight restored bytes.
    blobs=[rel.target_part.blob for rel in check.part.rels.values() if rel.reltype.endswith('/image')]
    for rec in images:
        assert any(digest(b)==rec['sha256'] for b in blobs),f"restored bytes missing: {rec['original_label']}"
    with manifest.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=images[0].keys());w.writeheader();w.writerows(images)
    print('RESTORED',len(images),'SOURCE_SHA',R5_SHA,'BASE_SHA',BASE_SHA,'OUTPUT_SHA',digest(raw(output)),'MANIFEST_SHA',digest(raw(manifest)))
    print('DOCX',output,'IMAGES',len(check.inline_shapes),'TABLES',len(check.tables),'BYTES',output.stat().st_size)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for k in ('source','base','output','manifest','figdir'):a.add_argument('--'+k,required=True,type=Path)
    x=a.parse_args();run(x.source,x.base,x.output,x.manifest,x.figdir)
