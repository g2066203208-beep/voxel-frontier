#!/usr/bin/env python3
"""Read-only exact-image provenance for R5 figures 3-7/3-8; not physics V&V."""
import argparse,csv,hashlib,zipfile,xml.etree.ElementTree as E
from pathlib import Path
R5='da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9'
R2='6d7edc3a286500776c2300495eb970f7c655ddf29da6514532d58bc9ca26b4e9'
w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
a='{http://schemas.openxmlformats.org/drawingml/2006/main}'
r='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
def digest(b):return hashlib.sha256(b).hexdigest()
def load(path,expected):
    b=Path(path).read_bytes()
    assert digest(b)==expected,'SOURCE_SHA256_MISMATCH'
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None,'ZIP_CRC_FAIL'
        root=E.fromstring(z.read('word/document.xml'))
        rel=E.fromstring(z.read('word/_rels/document.xml.rels'))
        mapping={e.attrib['Id']:e.attrib['Target'] for e in rel}
        imgs={rid:(target,digest(z.read('word/'+target))) for rid,target in mapping.items() if target.lower().endswith('.png')}
        paras=root.find(w+'body').findall(w+'p')
        live=[x.attrib[r+'embed'] for x in root.iter(a+'blip') if r+'embed' in x.attrib]
    return paras,imgs,live
def text(p):return ''.join(x.text or '' for x in p.iter(w+'t'))
def ids(p):return [x.attrib[r+'embed'] for x in p.iter(a+'blip') if r+'embed' in x.attrib]
def run(r5,r2,out):
    p5,i5,l5=load(r5,R5);p2,i2,l2=load(r2,R2)
    rows=[]
    for num in ('3-7','3-8'):
        hits=[k for k,p in enumerate(p5) if text(p).startswith('图'+num+'  ')]
        assert len(hits)==1,'CAPTION_NOT_UNIQUE'
        k=hits[0];rids=ids(p5[k-1]);assert len(rids)==1,'IMAGE_NOT_UNIQUE'
        name,h=i5[rids[0]]
        other=[(rid,n) for rid,(n,d) in i2.items() if d==h]
        assert len(other)==1,'CROSS_WORD_SHA_NOT_UNIQUE'
        rid2,n2=other[0]
        assert l5.count(rids[0])==1 and l2.count(rid2)==0,'LINK_STATUS_MISMATCH'
        rows.append([num,k,name,h,n2,1,0,'SOURCE_ONLY_NOT_PHYSICS_PASS'])
    dest=Path(out);assert not dest.exists(),'REFUSE_OVERWRITE'
    with dest.open('w',encoding='utf-8',newline='') as f:
        wr=csv.writer(f);wr.writerow(['r5_figure','r5_caption_paragraph_zero_based','r5_media','image_sha256','r2_media','r5_live_refs','r2_live_refs','status']);wr.writerows(rows)
    print('SOURCE_IMAGE_IDENTITY_PASS',len(rows),'CSV_SHA256',digest(dest.read_bytes()))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--r5',required=True);p.add_argument('--r2',required=True);p.add_argument('--out',required=True);x=p.parse_args();run(x.r5,x.r2,x.out)
