#!/usr/bin/env python3
"""Read-only DOCX image relationship audit; no figure insertion or model run.
Usage: python recover_word_image_map.py R2Z74.docx R5_R2Z34.docx > image_map.csv
"""
import csv, hashlib, re, sys, zipfile, xml.etree.ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
CH=re.compile(r'^第([一二三四五六七八九十])章')
NUM={x:i for i,x in enumerate('一二三四五六七八九十',1)}

def audit(path):
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('word/document.xml'))
        rel=ET.fromstring(z.read('word/_rels/document.xml.rels'))
        image={e.get('Id'):'word/'+e.get('Target').lstrip('/') for e in rel if e.get('Type','').endswith('/image')}
        used={v for el in root.iter() for k,v in el.attrib.items() if k.startswith(R)}
        chapters={};chapter='FRONT'
        for p in root.find(W+'body'):
            if p.tag!=W+'p':continue
            s=p.find(W+'pPr');s=s.find(W+'pStyle') if s is not None else None
            style=s.get(W+'val','') if s is not None else ''
            t=''.join(e.text or '' for e in p.iter(W+'t')).strip()
            m=CH.match(t)
            if m and style in ('论文章标题','164'):chapter='CH%02d'%NUM[m.group(1)]
            for e in p.iter(A+'blip'):
                rid=e.get(R+'embed')
                if rid:chapters.setdefault(rid,set()).add(chapter)
        out=[]
        for rid,member in image.items():
            b=z.read(member)
            out.append({'media':member,'rid':rid,'sha256':hashlib.sha256(b).hexdigest(),
                        'used':rid in used,'chapters':','.join(sorted(chapters.get(rid,[])))})
        return out

def main():
    if len(sys.argv)!=3:raise SystemExit('two original .docx paths required')
    r2,r5=map(audit,sys.argv[1:]);ref={x['sha256']:x for x in r5}
    def number(x):return int(re.search(r'image(\d+)',x['media']).group(1))
    w=csv.writer(sys.stdout,lineterminator='\n');w.writerow(['r2_img','r5_img','r5_chapters','live'])
    for x in sorted(r2,key=number):
        y=ref.get(x['sha256'])
        w.writerow([number(x),number(y) if y else '-',y['chapters'] if y else '-',int(x['used'])])
    assert (len(r2),sum(x['used'] for x in r2),len(r5),sum(x['used'] for x in r5))==(120,3,73,73)
    assert sum(x['sha256'] in ref and not x['used'] for x in r2)==73
if __name__=='__main__':main()
