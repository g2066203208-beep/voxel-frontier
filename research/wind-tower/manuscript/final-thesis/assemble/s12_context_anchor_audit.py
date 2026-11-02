#!/usr/bin/env python3
"""Read-only R5/R2 DOCX paragraph-context locator for still-unplaced images.
Usage: python s12_context_anchor_audit.py R5.docx R2_working.docx OUT.csv OUT.json
Never edits DOCX or infers that a reference screenshot is a thesis result.
"""
import csv,hashlib,json,re,sys,zipfile
from collections import Counter
from pathlib import Path
from lxml import etree
from rapidfuzz import fuzz,process
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
EXPECTED_R5='da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9'
EXPECTED_R2='6d7edc3a286500776c2300495eb970f7c655ddf29da6514532d58bc9ca26b4e9'
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def txt(p):return ''.join(e.text or '' for e in p.iter(W+'t')).strip()
def norm(s):return re.sub(r'\s+','',s)
def good(s):
 return len(s)>=45 and not s.startswith(('【证据链】','【3.','证据图','图','表','注：'))
def get(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  root=etree.fromstring(z.read('word/document.xml'))
  return [p for p in root.find(W+'body') if p.tag==W+'p']
def main():
 r5,r2,oc,oj=map(Path,sys.argv[1:]);assert len(sys.argv)==5
 assert digest(r5)==EXPECTED_R5,'R5 source SHA mismatch'
 assert digest(r2)==EXPECTED_R2,'R2 working copy SHA mismatch'
 a,b=get(r5),get(r2); ta=[norm(txt(p)) for p in a];tb=[norm(txt(p)) for p in b]
 r2pool=[(i,t) for i,t in enumerate(tb) if good(t)]
 choices=[t for _,t in r2pool];inds=[i for i,_ in r2pool]
 assert len(a)>700 and len(b)>800
 def match(t):
  if not good(t):return None
  matches=process.extract(t,choices,scorer=fuzz.ratio,limit=3)
  if not matches:return None
  best,sc,_=matches[0];i=inds[choices.index(best)]
  second=matches[1][1] if len(matches)>1 else 0
  return {'r2_p':i,'score':round(sc,2),'runner_up':round(second,2),'unique':sc>=95 and second<90,'preview':txt(b[i])[:95]}
 def anchor(k,direction):
  for distance in range(1,55):
   j=k+distance*direction
   if j<0 or j>=len(a):break
   t=ta[j]
   if not good(t):continue
   m=match(t)
   if m and m['score']>=95 and m['unique']:
    return {'r5_p':j,'distance':distance,'text':txt(a[j])[:120],**m}
  return None
 rows=[]; exact_count=0
 for i,p in enumerate(a):
  if not list(p.iter(A+'blip')):continue
  caption=next((txt(q) for q in a[i+1:i+6] if txt(q)),'')
  exact=sum(norm(caption)==x for x in tb)
  if exact==1:exact_count+=1;continue
  before=anchor(i,-1);after=anchor(i,1)
  gap=(after['r2_p']-before['r2_p']) if before and after else None
  d_before=(i-before['r5_p']) if before else None
  d_after=(after['r5_p']-i) if after else None
  if before and after and gap<0:
   grade='REORDERED_CONTEXT_HOLD'
  elif before and after and gap>70:
   grade='WIDE_R2_CONTEXT_HOLD'
  elif before and after and max(d_before,d_after)>15:
   grade='DISTANT_R5_CONTEXT_HOLD'
  elif before and after and gap<=30:
   grade='TWO_SIDED_NEAR_MATCH_REVIEW_ONLY'
  elif before and after:
   grade='R2_GAP_REVIEW'
  elif before or after:
   grade='ONE_SIDED_CONTEXT_HOLD'
  else:grade='NO_CONTEXT_MANUAL'
  # Reference screenshots are not original research figures.
  role='REFERENCE_SCREENSHOT' if caption.startswith('证据图') else 'ORIGINAL_FIGURE_CANDIDATE'
  rows.append({'r5_image_para':i,'r5_caption':caption,'figure_role':role,
   'r2_caption_matches':exact,'anchor_grade':grade,
   'r5_before_distance':d_before if d_before is not None else '',
   'r5_after_distance':d_after if d_after is not None else '',
   'r2_anchor_gap':gap if gap is not None else '',
   'r5_before_para':before['r5_p'] if before else '',
   'r2_before_para':before['r2_p'] if before else '',
   'before_score':before['score'] if before else '',
   'before_context':before['text'] if before else '',
   'r5_after_para':after['r5_p'] if after else '',
   'r2_after_para':after['r2_p'] if after else '',
   'after_score':after['score'] if after else '',
   'after_context':after['text'] if after else '',
   'action':'MANUAL_CAPTION_AND_SECTION_REVIEW_NO_INSERT'})
 assert len(rows)==61 and exact_count==13,(len(rows),exact_count)
 counts=dict(Counter(r['anchor_grade'] for r in rows)); roles=dict(Counter(r['figure_role'] for r in rows))
 oc.parent.mkdir(parents=True,exist_ok=True)
 with open(oc,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 receipt={'status':'READ_ONLY_PARAGRAPH_CONTEXT_AUDIT_NOT_PLACEMENT_PASS',
  'sources':{'r5_sha256':EXPECTED_R5,'r2_working_sha256':EXPECTED_R2},
  'algorithm':{'paragraph':'top-level w:p only','normalize':'remove whitespace',
   'match':'rapidfuzz.fuzz.ratio; 95% similar is NOT exact','min_text_characters':45,
   'anchor_threshold':95,'runner_up_below':90,'scan_radius_r5_paragraphs':54,
   'max_r2_bounded_gap':30,'max_r5_near_distance':15,'scope':'13 existing exact caption excluded; 61 unresolved only'},
  'counts':{'original_r5_image_placements':74,'already_restored_exact_caption':13,'remaining':len(rows),'grades':counts,'roles':roles},
  'output_csv_sha256':digest(oc),'software':{'python':sys.version.split()[0],
   'lxml':etree.LXML_VERSION,'rapidfuzz':__import__('rapidfuzz').__version__},
  'evidence':{'SOURCE':'R5 original and R2 13-image working copy locked SHA',
   'REF':'R5 narrative paragraphs, not external article full text',
   'STANDARD':'none read; no clause compliance','OFFICIAL':'OOXML document.xml',
   'RUN':'read-only SHA-checked Python context audit','FIG':'no figures inserted',
   'TAB':'61-row candidate context ledger','HOLD':'manual placement and caption/scientific-role verification'},
  'limitations':['paragraph match does not prove correct figure location',
   'references evidence screenshots must not be labelled own experimental results',
   'chapter reorganization may make same-text paragraphs misleading',
   '44 additional R2-only image media not assigned',
   'no new Abaqus/earthquake/fatigue physical RUN']}
 oj.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'rows':len(rows),'exact_restored':exact_count,'grades':counts,'roles':roles,'csv_sha256':digest(oc)},ensure_ascii=False))
if __name__=='__main__':main()
