#!/usr/bin/env python3
"""Restore four existing, source-verified figures from the V2 DOCX media payload.

V3 is a separate publication snapshot. It does not touch canonical T057/T070,
main research results, or earlier Word snapshots. It deliberately does not invent
the uncomputed 0.9–4.0 m pushover response.
"""
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from io import BytesIO
import copy,hashlib,json
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DOWNLOAD=ROOT/"public/thesis-studio/downloads"
EDITOR=ROOT/"public/thesis-studio/editor-data"
WORK=ROOT/"_thesis_figure_restore"
PREFIX="10MW-thesis-editorial-v2-20261121.part"
PUB="10MW-thesis-illustrated-v3-20261121.part"
FIGS=[
 ("图2-1",23,"基准与收敛控制复核的塔顶位移—反力曲线"),
 ("图2-2",30,"推覆过程中ALLAE/ALLIE变化"),
 ("图2-3",31,"0.13610 Hz与0.13718 Hz一阶频率对照"),
 ("图2-4",32,"X/Z方向前30阶累计有效质量")
]
WORK.mkdir(exist_ok=True)
source=WORK/"base-v2.docx"
with source.open("wb") as w:
 for i in range(1,16):w.write((DOWNLOAD/(PREFIX+f"{i:02d}.bin")).read_bytes())
old=json.loads((EDITOR/"editorial-manuscript-v2.json").read_text(encoding="utf8"))
base_sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert old["source"]["sha256"]==base_sha, "Base Word source mismatch"
doc=Document(source)
before=list(doc.element.body.iterchildren())
with ZipFile(source) as z:
 for fig,num,description in FIGS:
  caps=[p for p in doc.paragraphs if p.text.strip().startswith(fig+" ")]
  assert len(caps)==1,(fig,len(caps))
  caption=caps[0]
  name=f"word/media/image{num}.png"
  data=z.read(name)
  w,h=Image.open(BytesIO(data)).size
  para=doc.add_paragraph()
  para.alignment=WD_ALIGN_PARAGRAPH.CENTER
  para.paragraph_format.line_spacing=1.0  # Prevent inherited fixed-line-height clipping.
  para.paragraph_format.space_before=Pt(8)
  para.paragraph_format.space_after=Pt(4)
  para.paragraph_format.keep_with_next=True
  para.add_run().add_picture(BytesIO(data),width=Cm(min(14.3,10.3*w/h)))
  caption._p.addprevious(para._p)
  caption.style="图题"
  caption.alignment=WD_ALIGN_PARAGRAPH.CENTER
  caption.paragraph_format.space_before=Pt(3)
  caption.paragraph_format.space_after=Pt(8)
  (EDITOR/"manuscript-figures").mkdir(parents=True,exist_ok=True)
  (EDITOR/"manuscript-figures"/f"FIG_2_{fig[-1]}.png").write_bytes(data)
assert len(doc.inline_shapes)==4
dest=WORK/"10MW混塔论文_第二章四张实图恢复V3_20261121.docx"
doc.save(dest)
# Stable bytes keep editor local-save identity stable across deterministic rebuilds.
stable=WORK/"stable.docx"
with ZipFile(dest,"r") as src,ZipFile(stable,"w") as dst:
 for item in src.infolist():
  meta=ZipInfo(item.filename,(1980,1,1,0,0,0))
  meta.compress_type=ZIP_DEFLATED
  meta.external_attr=item.external_attr
  meta.create_system=item.create_system
  dst.writestr(meta,src.read(item.filename),compress_type=ZIP_DEFLATED,compresslevel=6)
stable.replace(dest)
after=list(doc.element.body.iterchildren())
mapping={}
for i,el in enumerate(before):
 j=after.index(el)
 mapping[i]=j
assert len(set(mapping.values()))==len(mapping)
new=copy.deepcopy(old)
for chapter in new["chapters"]:
 for b in chapter["blocks"]:
  b["word_body_index"]=mapping[b["word_body_index"]]
  for fig,num,description in FIGS:
   if b.get("kind")!="table" and b.get("text","").strip().startswith(fig+" "):
    b["figure_asset"]=f"./editor-data/manuscript-figures/FIG_2_{fig[-1]}.png"
    b["figure_caption_match"]=description
new["source"].update({
 "name":dest.name,
 "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
 "bytes":dest.stat().st_size,
 "docx":None,
 "docx_parts_pattern":"./downloads/10MW-thesis-illustrated-v3-20261121.partNN.bin",
 "docx_parts":15,
 "pdf":"./downloads/10MW-thesis-illustrated-v3-20261121.pdf",
 "figure_recovery":"Four traceable images from archived Word media restored to the correct figure captions. 117 other archived media assets remain to be audited; no unsupported results were invented."
})
(EDITOR/"illustrated-manuscript-v3.json").write_text(json.dumps(new,ensure_ascii=False,separators=(",",":")),encoding="utf8")
b=dest.read_bytes();chunk=(len(b)+14)//15
for i in range(15):
 (DOWNLOAD/(PUB+f"{i+1:02d}.bin")).write_bytes(b[i*chunk:(i+1)*chunk])
with ZipFile(dest) as z:
 assert z.read("word/document.xml").count(b"<w:drawing")==4
assert sum(1 for c in new["chapters"] for b in c["blocks"] if b.get("figure_asset"))==4
assert len([b for c in new["chapters"] for b in c["blocks"]])==887
(WORK/"QA_manifest.json").write_text(json.dumps({"base_sha":base_sha,"sha256":new["source"]["sha256"],"restored_figures":[x[0] for x in FIGS],"image_provenance":"original Word media image23,image30,image31,image32; visually checked against Figure 2-1 through Figure 2-4 captions","scientific_scope":"archived historic BF1/R2P/R2R only; NOT T057 native scientific validation"},ensure_ascii=False,indent=2),encoding="utf8")
print("RESTORE_PASS",new["source"]["sha256"],dest.stat().st_size,"figures",len(FIGS),flush=True)
