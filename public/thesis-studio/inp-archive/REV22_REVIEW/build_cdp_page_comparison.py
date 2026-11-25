"""Render original publisher pages and corresponding R20 manuscript excerpt.
No synthesized reference images; no solver results. Requires PyMuPDF, Pillow,
and Google Chrome. All thesis text, table and figure are read from manuscript JSON.
"""
from pathlib import Path
import json, hashlib, html, re, subprocess, sys
import fitz
from PIL import Image, ImageDraw, ImageFont, ImageStat
from io import BytesIO
import csv
p=Path(__file__).resolve().parent
studio=p.parent.parent
pdf=p/'original-literature/chen-2020-original.pdf'
doc=fitz.open(pdf)
assert len(doc) in (17,18)
assert '10.3390/en13030533' in doc[0].get_text()
assert 'Figure 7' in doc[8].get_text() and 'Table 3' in doc[8].get_text()
for i in (7,8):
    dest=p/'original-literature'/f'chen-2020-page{i+1:02}.png'
    doc[i].get_pixmap(matrix=fitz.Matrix(2.1,2.1),alpha=False).save(dest)
    with Image.open(dest) as im:
        assert max(ImageStat.Stat(im.convert('RGB')).stddev)>5
    with Image.open(dest) as im:
        im.verify()
m=json.loads((studio/'editor-data/manuscript-v8-bem.json').read_text())
assert m['online_revision']['version']=='V8-R20-REV22-CDP-MATCHED'
c=next(c for c in m['chapters'] if c['id']=='02')
b={x['id']:x for x in c['blocks']}
fig=b['r16-cdp-figure']
assert fig['figure_asset'].endswith('cdp-matched-total-strain.svg')
escape=html.escape
paragraph=lambda id:'<p>'+escape(b[id]['text'])+'</p>'
table=b['r16-cdp-tab']['rows']
body=paragraph('b0191')+paragraph('r16-cdp-points')+'<figure><img src="cdp-matched-total-strain.svg"><figcaption>'+escape(fig['text'])+'</figcaption></figure>'+paragraph('r20-cdp-property')+'<div class="caption">'+escape(b['r16-cdp-tabcap']['text'])+'</div><table><thead><tr>'+''.join('<th>'+escape(x)+'</th>' for x in table[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(x)+'</td>' for x in row)+'</tr>' for row in table[1:])+'</tbody></table>'+paragraph('r16-cdp-limits')
page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>混凝土材料本构（在线正文摘录）</title><style>body{margin:0;background:white;color:#111;font:16px/1.62 "Noto Serif CJK SC",serif}main{box-sizing:border-box;width:860px;min-height:1200px;margin:auto;padding:34px 56px}h2{font-size:19px;margin:0 0 15px}p{margin:10px 0;text-indent:2em;text-align:justify}figure{margin:12px 0}img{display:block;width:100%;height:auto}figcaption,.caption{text-align:center;font-size:14px;margin:5px 0 9px}table{border-collapse:collapse;width:100%;border-top:2px solid #111;border-bottom:2px solid #111;font-size:14px}thead{border-bottom:1px solid #111}th,td{padding:2px 9px;text-align:center}td:first-child{text-align:left}footer{font-size:12px;color:#555;margin-top:15px;text-align:center}</style><main><h2>第二章　混凝土材料本构</h2>'+body+'<footer>在线正文摘录 · '+escape(m['online_revision']['version'])+' · 非最终Word/PDF页码</footer></main></html>'
(p/'cdp-manuscript-excerpt.html').write_text(page,encoding='utf-8')
our=p/'cdp-manuscript-excerpt.png'
subprocess.run(['google-chrome','--headless','--no-sandbox','--disable-gpu','--hide-scrollbars','--allow-file-access-from-files','--window-size=860,1600','--force-device-scale-factor=2','--screenshot='+str(our),(p/'cdp-manuscript-excerpt.html').as_uri()],check=True)
ref=p/'original-literature/chen-2020-page09.png'
a=Image.open(ref).convert('RGB')
bim=Image.open(our).convert('RGB')
# Preserve original page aspect ratios. Compare original PDF p.9 with the actual
# online manuscript excerpt (not falsely labeled a final thesis page).
target=1750
resize=lambda im: im.resize((round(im.width*target/im.height),target),Image.Resampling.LANCZOS)
a,bim=resize(a),resize(bim)
canvas=Image.new('RGB',(a.width+bim.width+84,target+80),'white')
d=ImageDraw.Draw(canvas)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',25)
d.text((20,15),'Chen et al. (2020) — PDF p. 9',font=font,fill='black')
d.text((a.width+64,15),'Thesis — R20 material subsection excerpt',font=font,fill='black')
canvas.paste(a,(20,60))
canvas.paste(bim,(a.width+64,60))
d.line((a.width+42,10,a.width+42,target+60),fill='#aaa',width=2)
out=p/'cdp-page-comparison.png'
canvas.save(out,dpi=(300,300))
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
receipt={'doi':'10.3390/en13030533','source_pdf_sha256':sha(pdf),'source_pdf_pages':len(doc),'reference_pages':[8,9],'source_page09_sha256':sha(ref),'manuscript_version':m['online_revision']['version'],'manuscript_json_sha256':sha(studio/'editor-data/manuscript-v8-bem.json'),'our_excerpt_sha256':sha(our),'comparison_sha256':sha(out),'comparison_size':list(canvas.size),'scope':'Actual PDF page 9 versus rendered excerpt of online manuscript; not final thesis pagination'}
(p/'cdp-page-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
