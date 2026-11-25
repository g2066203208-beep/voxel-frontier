from pathlib import Path
import fitz, cairosvg, io, json, hashlib, csv
from PIL import Image, ImageDraw, ImageFont, ImageStat
ROOT=Path('public/thesis-studio/rebar-verification')
WU=Path('research/wind-tower/references/open-access/Wu_2022_SCS_44_407_160m_Hybrid_Tower.pdf')
HE=Path('public/thesis-studio/documents/He_Zeyu_2024_hybrid_tower_thesis.pdf')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def blob(p):
 b=p.read_bytes()
 return hashlib.sha1(('blob '+str(len(b))+'\0').encode()+b).hexdigest()
assert blob(WU)=='353d2d17cc4ea12c43e3aae0a36c7da79e0bc43e'
assert blob(HE)=='311e5f62936368f77f2901516739a879596dfdf8'
fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def font(s):return ImageFont.truetype(fontpath,s)
def crop(doc,p,box):
 with fitz.open(doc) as pdf:
  page=pdf[p]
  a,b,c,d=box
  clip=fitz.Rect(a*page.rect.width,b*page.rect.height,c*page.rect.width,d*page.rect.height)
  pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=clip,alpha=False)
  return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
def ownsvg(name):
 return Image.open(io.BytesIO(cairosvg.svg2png(url=str(ROOT/name),scale=2))).convert('RGB')
def fit(im,w,h):
 s=min(w/im.width,h/im.height)
 return im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
def table():
 rows=list(csv.reader((ROOT/'r43-thesis-table.csv').open()))
 assert len(rows)==32
 # Abbreviate segment ids in this figure only; complete values remain in CSV.
 rows[0]=['塔节','壁厚/mm','纵筋/层','直径/mm','实体环筋','间距/mm','拉筋']
 im=Image.new('RGB',(1400,1600),'white');d=ImageDraw.Draw(im);f=font(29)
 for i,row in enumerate(rows):
  y=40+i*46
  if i==0:d.line((20,y-8,1380,y-8),fill='black',width=3)
  for j,v in enumerate(row):
   d.text((20+j*195,y),v.replace('CSEG_',''),font=f,fill='black')
  if i==0 or i==31:d.line((20,y+38,1380,y+38),fill='black',width=2)
 return im
receipts=[]
def pair(name,ref,idx,box,right,left_title,right_title,note):
 a=crop(ref,idx,box)
 b=right if isinstance(right,Image.Image) else ownsvg(right)
 assert max(ImageStat.Stat(a).stddev)>3 and max(ImageStat.Stat(b).stddev)>3
 source=ROOT/(name+'-reference.png');a.save(source,dpi=(300,300))
 W,H=3400,2000
 canvas=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(canvas)
 d.text((60,35),left_title,font=font(45),fill='black')
 d.text((W//2+50,35),right_title,font=font(45),fill='black')
 d.line((W//2,25,W//2,1820),fill='#aaa',width=2)
 for i,im in enumerate((a,b)):
  q=fit(im,W//2-110,1580)
  canvas.paste(q,(i*(W//2)+(W//2-q.width)//2,145+(1580-q.height)//2))
 d.text((60,1850),note,font=font(32),fill='black')
 out=ROOT/(name+'.png');canvas.save(out,dpi=(300,300))
 with Image.open(out) as f:f.verify()
 receipts.append(dict(file=out.name,sha256=sha(out),reference_file=str(ref),reference_sha256=sha(ref),reference_pdf_page=idx+1,crop_fraction=box,reference_image_sha256=sha(source),our_source=right if isinstance(right,str) else 'r43-thesis-table.csv',our_sha256=sha(ROOT/(right if isinstance(right,str) else 'r43-thesis-table.csv')),note=note))
pair('r43-wu-fig4-cage-pair',WU,2,(.07,.215,.94,.515),'r43-fig-cage.svg','Wu 等（2022）图4 · 原图','本文图2.3-1 · 构造候选','同类钢筋布置图；不同塔型与材料，不作验证或直接移植。')
pair('r43-wu-table2-rebar-pair',WU,3,(.07,.085,.49,.64),table(),'Wu 等（2022）表2 · 原表','本文表2.3-1 · 31段配筋','同类分段配筋表；文献28段，本研究31段。')
pair('r43-he-fig33-cage-pair',HE,30,(0,0,1,1),'r43-fig-cage.svg','何泽瑜（2024）PDF第31页','本文图2.3-1 · 构造候选','原页图3-3为复合截面；本文补充普通钢筋构造。')
pair('r43-he-table32-rebar-pair',HE,33,(0,0,1,1),table(),'何泽瑜（2024）PDF第34页','本文表2.3-1 · 31段配筋','原页表3-2提供几何和根数；新表直径和环筋为独立候选。')
pair('r43-he-fig46-section-method',HE,43,(0,0,1,1),'r43-fig-section.svg','何泽瑜（2024）PDF第44页','本文图2.3-3 · 条件需求比','仅纤维计算方法参照，图中物理量不同，不能作一对一验证。')
pair('r43-wu-fig13-strut-method',WU,6,(.07,.395,.94,.64),'r43-fig-strut.svg','Wu 等（2022）图13 · 原图','本文图2.3-2 · 斜压敏感性','截面力学分析参照；不同物理量，不计为正式同类图匹配。')
pair('r43-wu-table3-pt-method',WU,3,(.51,.085,.94,.66),'r43-fig-pt.svg','Wu 等（2022）表3 · 原表','本文图2.3-4 · 预应力敏感性','预应力输入的组织方式参照；非相同输出指标，不计为正式同类图匹配。')
(ROOT/'r43-reference-pairs-receipt.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipts,ensure_ascii=False,indent=2))
