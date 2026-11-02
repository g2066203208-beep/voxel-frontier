#!/usr/bin/env python3
"""Conservative R5 -> R2Z74 DOCX image restoration.
Only reattach a byte-identical R5 image if its immediately following nonempty
caption is unique and text-identical in R2Z74. Never guess missing captions.
Requires lxml; does not modify either original DOCX.
Usage: python s12_restore_exact_caption_images.py R2.docx R5.docx OUTPUT.docx REPORT.json MAP.csv
"""
import copy,csv,hashlib,json,re,sys,zipfile
from collections import Counter
from pathlib import Path
from lxml import etree
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
XML='word/document.xml'; REL='word/_rels/document.xml.rels'
EXPECTED_R2='5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0'
EXPECTED_R5='da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9'

def sha(b):return hashlib.sha256(b).hexdigest()
def filehash(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def text(p):return ''.join(t.text or '' for t in p.iter(W+'t')).strip()
def norm(s):return re.sub(r'\s+','',s)
def images(z):
 rel=etree.fromstring(z.read(REL)); out={}
 for e in rel:
  if e.get('Type','').endswith('/image'):
   t=e.get('Target','')
   name=('word/'+t.lstrip('/')) if not t.startswith('/') else t.lstrip('/')
   if name.startswith('word/word/'):name=name[5:]
   out[e.get('Id')]={'member':name,'sha':sha(z.read(name))}
 return out

def main():
 if len(sys.argv)!=6:raise SystemExit('R2 R5 OUTPUT DOC_REPORT JSON_MAP_CSV required')
 r2,r5,out,report,table=map(Path,sys.argv[1:])
 assert filehash(r2)==EXPECTED_R2,'R2 input SHA mismatch'
 assert filehash(r5)==EXPECTED_R5,'R5 input SHA mismatch'
 with zipfile.ZipFile(r2) as a,zipfile.ZipFile(r5) as b:
  x=etree.fromstring(a.read(XML)); y=etree.fromstring(b.read(XML))
  m2=images(a);m5=images(b)
  assert len(m2)==120 and len(m5)==73
  r2_by_sha={d['sha']:(rid,d) for rid,d in m2.items()}
  r2body=x.find(W+'body');r5body=y.find(W+'body')
  r2paras=[p for p in r2body if p.tag==W+'p']
  r5paras=[p for p in r5body if p.tag==W+'p']
  captions={}
  for p in r2paras:
   if text(p):captions.setdefault(norm(text(p)),[]).append(p)
  rows=[]; selected=[]
  for idx,p in enumerate(r5paras):
   blips=list(p.iter(A+'blip'))
   if not blips:continue
   nextcap=next((text(q) for q in r5paras[idx+1:idx+6] if text(q)),'')
   caplist=captions.get(norm(nextcap),[])
   imsha=[];r2rid=[]
   for bl in blips:
    rid=bl.get(R+'embed'); assert rid in m5,'R5 image relationship absent'
    h=m5[rid]['sha'];assert h in r2_by_sha,'R2 byte-identical image absent'
    imsha.append(h);r2rid.append(r2_by_sha[h][0])
   reason='EXACT_UNIQUE_CAPTION' if len(caplist)==1 and len(blips)==1 and not text(p) else 'UNRESOLVED_CAPTION_OR_LAYOUT'
   # Check all R5 paragraph relationship attributes; no hidden external links allowed.
   other=[(etree.QName(k).localname,v) for e in p.iter() for k,v in e.attrib.items() if k.startswith(R) and v not in m5]
   if other:reason='UNRESOLVED_EXTRA_RELATIONSHIPS'
   rows.append({'r5_image':m5[blips[0].get(R+'embed')]['member'].split('/')[-1],
    'r2_image':r2_by_sha[imsha[0]][1]['member'].split('/')[-1],
    'image_sha256':imsha[0], 'r5_caption':nextcap,'caption_r2_matches':len(caplist),
    'decision':reason})
   if reason=='EXACT_UNIQUE_CAPTION':selected.append((p,caplist[0],r2rid[0],imsha[0],nextcap))
  assert len(rows)==74 and len(selected)==13,(len(rows),len(selected))
  assert len({id(c) for _,c,*_ in selected})==len(selected),'two figures target one caption'
  existing={v for p in r2body.iter() for k,v in p.attrib.items() if k==R+'embed'}
  for p,caption,rid,h,captext in selected:
   assert rid not in existing,'already attached image'
   clone=copy.deepcopy(p)
   blip=next(clone.iter(A+'blip'));blip.set(R+'embed',rid)
   # Keep each restored figure with its existing exact caption across page breaks.
   ppr=clone.find(W+'pPr')
   if ppr is None:ppr=etree.Element(W+'pPr');clone.insert(0,ppr)
   if ppr.find(W+'keepNext') is None:ppr.insert(0,etree.Element(W+'keepNext'))
   # Unique DOCPr id; R2 existing docPr IDs must not be duplicated.
   ns='{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
   docprs=list(clone.iter(ns+'docPr'))
   all_ids=[int(q.get('id')) for q in x.iter(ns+'docPr') if q.get('id','').isdigit()]
   for d in docprs:d.set('id',str(max(all_ids+[0])+1))
   r2body.insert(r2body.index(caption),clone)
   existing.add(rid)
  xml=etree.tostring(x,encoding='UTF-8',xml_declaration=True,standalone=True)
  out.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(out,'w') as dst:
   for info in a.infolist():
    dst.writestr(info,xml if info.filename==XML else a.read(info.filename))
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None
  root=etree.fromstring(z.read(XML));rel=images(z)
  used={e.get(R+'embed') for e in root.iter(A+'blip') if e.get(R+'embed')}
  assert len(used)==16 and len(rel)==120,(len(used),len(rel))
  assert len(list(root.iter(A+'blip')))==16
  for _,_,rid,h,_ in selected:assert rel[rid]['sha']==h
  # All 13 restored image paragraphs are directly followed by their original exact caption.
  body=root.find(W+'body');els=list(body)
  for _,_,rid,h,cap in selected:
   at=[i for i,p in enumerate(els) if any(q.get(R+'embed')==rid for q in p.iter(A+'blip'))]
   assert len(at)==1 and norm(text(els[at[0]+1]))==norm(cap)
 with open(table,'w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 rec={'status':'SOURCE_LEVEL_EXACT_CAPTION_REATTACH_ONLY_NOT_RENDER_OR_SCIENTIFIC_PASS',
 'inputs':{'r2_sha256':EXPECTED_R2,'r5_sha256':EXPECTED_R5},
 'output':{'sha256':filehash(out),'bytes':out.stat().st_size,'path':str(out)},
 'source_image_relations':120,'source_embedded_images':3,
 'r5_image_placements':74,'r5_unique_images':73,
 'restored_placements':13,'restored_unique_images':13,
 'output_embedded_images':16,'remaining_unreferenced_relations':104,
 'unresolved_placements':61,'unmatched_new_media':44,
 'constraints':['exact original image bytes','exact unique caption text','no insertion for missing caption','no original DOCX changed'],
 'verification':['ZIP CRC valid','120 image relationships retained','16 embedded images','13 captions immediately follow restored images'],
 'limitations':['no native Abaqus or structural verification','not an integrated thesis','full Word pagination and figure content QA pending'],
 'evidence':{'SOURCE':'original DOCX byte SHA256','REF':'R5 caption and figure placement','STANDARD':'not evaluated','OFFICIAL':'OOXML image relations','RUN':'Python lxml deterministic relink','FIG':'13 exact-caption original images','TAB':'74 source placement decisions','HOLD':'61 unmatched captions; 44 additional unmatched media; render and content QA'}}
 Path(report).write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:rec[k] for k in ['restored_placements','unresolved_placements','output_embedded_images','remaining_unreferenced_relations']},ensure_ascii=False))
if __name__=='__main__':main()