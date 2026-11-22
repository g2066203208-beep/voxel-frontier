#!/usr/bin/env python3
"""Fail-closed DOCX assembly of the already reviewed Ch6 §6.1.8 source; no solver."""
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
import argparse, hashlib, re
START='### 6.1.8 高风风向条件分布与全年分布的区别'
END='## 6.2 已有贡献与创新边界'
TITLE=START[4:]
def extract(md):
    assert md.count(START)==1 and md.count(END)==1
    body=md.split(START,1)[1].split(END,1)[0]
    blocks=[x.strip() for x in re.split(r'\n\s*\n',body) if x.strip()]
    assert len(blocks)==2
    out=[]
    for b in blocks:
        assert not b.startswith('#') and '$$' not in b
        b=b.replace('**','').replace('\\(','').replace('\\)','').replace('\\mid','|')
        assert '\\' not in b, 'LaTeX not converted: stop rather than print fake formula'
        out.append(b)
    return out
def integrate(src,md,dst):
    blocks=extract(Path(md).read_text(encoding='utf8'))
    doc=Document(src)
    paragraphs=list(doc.paragraphs)
    assert not any(p.text.strip()==TITLE for p in paragraphs), 'duplicate heading'
    anchors=[p for p in paragraphs if re.match(r'^6\.2(?:\s|$)',p.text.strip())]
    assert len(anchors)==1, 'missing or ambiguous 6.2 anchor'
    anchor=anchors[0]
    el=OxmlElement('w:p');anchor._p.addprevious(el)
    p=Paragraph(el,anchor._parent)
    p.style='Heading 3'
    p.add_run(TITLE)
    for b in blocks:
        el=OxmlElement('w:p');p._p.addnext(el)
        p=Paragraph(el,p._parent);p.add_run(b)
    dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    doc.save(dst)
    text=[p.text.strip() for p in Document(dst).paragraphs]
    i=text.index(TITLE)
    assert text[i+1:i+3]==blocks and text[i+3].startswith('6.2')
    return {'input_sha256':hashlib.sha256(Path(src).read_bytes()).hexdigest(),'source_md_sha256':hashlib.sha256(Path(md).read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'paragraphs':2}
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--docx',required=True);ap.add_argument('--chapter-md',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args()
    print(integrate(a.docx,a.chapter_md,a.out))
