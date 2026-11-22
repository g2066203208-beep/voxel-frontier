"""Merge reviewed Chapter 3 Word XML into the published V6 graphics parent.
Preserve every other Word part, including all four V6 figure PNGs.
The input patch is exact reviewed paragraph XML; reject any changed anchor.
No numerical simulation is performed.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml import parse_xml
from lxml import etree
from copy import deepcopy
import base64, zlib, json, hashlib, re, unicodedata, subprocess
import fitz
from PIL import Image

ROOT=Path("public/thesis-studio")
DLD=ROOT/"downloads"
EDITOR=ROOT/"editor-data"
COMPARE=ROOT/"he-thesis-comparison"
PATCH=Path("scripts/thesis-edit/ch3_wind_theory_reviewed_20261122.b64")
PREFIX="10MW-thesis-v7-wind-theory-20261122"
OLD="10MW-thesis-ch2-graphics-v6-20261122"
OUT=Path("_generated_thesis_v7")
OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
write_json=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,separators=(",",":")),encoding="utf8")
source=json.loads((EDITOR/"ch2-graphics-manuscript-v6.json").read_text(encoding="utf8"))
raw=b"".join((DLD/f"{OLD}.part{i:02}.bin").read_bytes() for i in range(1,16))
assert sha(raw)==source["source"]["sha256"]=="e6520c3d6ca09d388a641826810e9629396599f6d8c254c79d1c38b1cc61592d"
parent=OUT/"source-v6.docx"
parent.write_bytes(raw)
patch=PATCH.read_text().strip()
assert sha(patch.encode())=="0945dc3c5f5e7311a8a0846ee03b62e5ab1ba00e363fb72566f5f144eedeb83e"
patch=json.loads(zlib.decompress(base64.b64decode(patch)))
d=Document(parent)
assert (len(d.paragraphs),len(d.tables),len(d.inline_shapes),len(d.element.xpath(".//m:oMath")))==(901,37,4,51)
body=d.element.body
parents=list(body)
ps=list(d.paragraphs)
# Preserve stable IDs, existing images, and all unmodified blocks.
existing={parents[b["word_body_index"]]:(c["id"],deepcopy(b)) for c in source["chapters"] for b in c["blocks"]}
new={}
latex=[
r"U_{10}(t)=\sqrt{u_{10}^{2}(t)+v_{10}^{2}(t)}",
r"U_{100}(t)=\sqrt{u_{100}^{2}(t)+v_{100}^{2}(t)}",
r"\alpha(t)=\frac{\ln[U_{100}(t)/U_{10}(t)]}{\ln(100/10)}",
r"U_{\mathrm{hub}}(t)=U_{100}(t)\left(\frac{z_{\mathrm{hub}}}{100\,\mathrm{m}}\right)^{\alpha(t)}",
r"\mathbf V(y,z,t)=[\overline U(z)+u',\,v',\,w']^{\mathsf T}",
r"\overline U(z)=U_{\mathrm{ref}}\left(\frac{z}{z_{\mathrm{hub}}}\right)^{\alpha_p}",
r"\sigma_{u,\mathrm{NTM}}=I_{\mathrm{ref}}(0.75U_{\mathrm{ref}}+5.6\,\mathrm{m/s})",
r"\sigma_{u,\mathrm{ETM}}=cI_{\mathrm{ref}}\left[0.072\left(\frac{V_{\mathrm{ave}}}{c}+3\right)\left(\frac{U_{\mathrm{ref}}}{c}-4\right)+10\right]",
r"S_k(f)=\frac{4\sigma_k^2L_k/U_{\mathrm{ref}}}{(1+6fL_k/U_{\mathrm{ref}})^{5/3}},\quad k=u,v,w",
r"\sigma_k^2=\int_0^\infty S_k(f)\,\mathrm df",
r"\Lambda_u=0.7\min(z_{\mathrm{hub}},60\,\mathrm m)",
r"(L_u,L_v,L_w)=(8.1,2.7,0.66)\Lambda_u",
r"(\sigma_v,\sigma_w)=(0.8,0.5)\sigma_u",
r"r_{ij}=\sqrt{(y_i-y_j)^2+(z_i-z_j)^2}",
r"\gamma_{ij}(f)=\exp\left[-12\sqrt{(fr_{ij}/U_{\mathrm{ref}})^2+(0.12r_{ij}/L_u)^2}\right]",
r"S_{ij}(f)=\gamma_{ij}(f)\sqrt{S_{ii}(f)S_{jj}(f)}",
r"\mathbf S(f_n)=\mathbf H(f_n)\mathbf H^{\mathsf H}(f_n)",
r"\Delta y=\frac{W}{N_y-1},\quad\Delta z=\frac{H}{N_z-1}"
]
formula_map={**{f"3.1-{i+1}":v for i,v in enumerate(latex[:4])},**{f"3.2-{i+1}":v for i,v in enumerate(latex[4:])}}
for i,j,expected,xmls in patch:
    assert [q.text for q in ps[i:j]]==expected,("source anchor differs",i,j)
    assert 314<=i<=482, i
    anchor=ps[i]._p
    idx=body.index(anchor)
    for k,x in enumerate(xmls):
        el=parse_xml(x)
        p=Paragraph(el,d)
        # Terminology correction: grid directions are horizontal transverse and vertical.
        if p.text.startswith("计算得纵、横网格间距"):
            for run in p.runs:
                if "纵、横" in run.text: run.text=run.text.replace("纵、横","横向、竖向")
        body.insert(idx+k,el)
        math=bool(el.xpath(".//m:oMath"))
        style=p.style.name
        kind="h2" if style=="论文一级标题" else "h3" if style=="论文二级标题" else "caption" if style=="表题" else "text"
        b={"id":f"v7-{i:04}-{k:02}","kind":kind,"style":style,"text":p.text,"has_media":False,"has_math":math}
        if math:
            match=re.search(r"3\.[12]-\d+",p.text)
            if match:
                b["equation_label"]=match.group(0)
                b["equation_latex"]=formula_map[match.group(0)]
        new[el]=("03",b)
    for q in ps[i:j]:
        body.remove(q._p)
assert len(d.paragraphs)==932 and len(d.tables)==37 and len(d.inline_shapes)==4
assert len(d.element.xpath(".//m:oMath"))==64
# All chapter-two text and XML remain exactly unchanged.
assert all(q._p.getparent() is body for q in ps[:314])
document_xml=etree.tostring(d.element,encoding="UTF-8",xml_declaration=True,standalone=True)
dest=OUT/f"{PREFIX}.docx"
with ZipFile(parent) as zi,ZipFile(dest,"w",compression=ZIP_DEFLATED,compresslevel=6) as zo:
    for entry in zi.infolist():
        zo.writestr(entry,document_xml if entry.filename=="word/document.xml" else zi.read(entry.filename))
with ZipFile(parent) as zi,ZipFile(dest) as zo:
    assert set(zi.namelist())==set(zo.namelist())
    assert all(zi.read(n)==zo.read(n) for n in zi.namelist() if n!="word/document.xml")
check=Document(dest)
assert (len(check.paragraphs),len(check.tables),len(check.inline_shapes),len(check.element.xpath(".//m:oMath")))==(932,37,4,64)
assert [q.text for q in check.paragraphs[:314]]==[q.text for q in Document(parent).paragraphs[:314]]
# Rebuild structured view using actual body order; never retarget old word_body_index values.
chapters={c["id"]:dict(c,blocks=[]) for c in source["chapters"]}
for idx,el in enumerate(body):
    entry=new.get(el,existing.get(el))
    if entry:
        c,b=entry
        b["word_body_index"]=idx
        chapters[c]["blocks"].append(b)
source["chapters"]=list(chapters.values())
assert len(source["chapters"])==8
assert sum("equation_latex" in b for c in source["chapters"] for b in c["blocks"])==18
assert sum("manuscript-figures-v6" in b.get("figure_asset","") for c in source["chapters"] for b in c["blocks"])==4
assert len([b["id"] for c in source["chapters"] for b in c["blocks"]])==len({b["id"] for c in source["chapters"] for b in c["blocks"]})
binary=dest.read_bytes()
source["source"].update({"name":"10MW混塔论文_V7_第二章图件与第三章风场理论合并版.docx","sha256":sha(binary),"bytes":len(binary),"pdf":f"./downloads/{PREFIX}.pdf","docx":None,"docx_parts_pattern":f"./downloads/{PREFIX}.partNN.bin","docx_parts":15,"editorial_scope":"V7 preserves V6 four figures, adds reviewed Chapter 3 wind theory; no new physical runs."})
# Render the actual merged Word, not pre-V6 page raster.
subprocess.run(["libreoffice","-env:UserInstallation=file:///tmp/lo-thesis-v7","--headless","--convert-to","pdf","--outdir",str(OUT),str(dest)],check=True)
pdfpath=OUT/f"{PREFIX}.pdf"
assert pdfpath.exists() and pdfpath.stat().st_size>100000
pdf=fitz.open(pdfpath)
assert 125<=len(pdf)<=155
def normalize(s):
    return re.sub(r"\s+","",unicodedata.normalize("NFKC",s)).replace("‐","-").replace("−","-")
def find_anchor(term):
    hits=[i+1 for i,p in enumerate(pdf) if normalize(term) in normalize(p.get_text()) and 32<=i+1<=65]
    assert hits,("missing rendered equation",term)
    return hits[0]
equation_pages={k:find_anchor(k) for k in formula_map}
assert len(equation_pages)==18
# Reference exact PDF physical pages 18,19; use anchor-matched right-hand pages.
he=fitz.open(ROOT/"documents/He_Zeyu_2024_hybrid_tower_thesis.pdf")
assert len(he)==90
spreads=COMPARE/"v7-spreads"
spreads.mkdir(exist_ok=True)
groups={"18":sorted({equation_pages[k] for k in ["3.1-1","3.1-4","3.2-1","3.2-2"]}),"19":sorted({equation_pages[k] for k in ["3.2-3","3.2-5","3.2-11","3.2-14"]})}
def raster(doc,page):
    pix=doc[page-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
    return Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
pages={}
for hp,our_pages in groups.items():
    pairs=[]
    for op in our_pages:
        left,right=raster(he,int(hp)),raster(pdf,op)
        canvas=Image.new("RGB",(left.width+right.width+18,max(left.height,right.height)),"#e5e9ed")
        canvas.paste(left,(0,0));canvas.paste(right,(left.width+18,0))
        name=f"he{hp}-v7-{op}.png"
        canvas.save(spreads/name,optimize=True)
        pairs.append({"he_pdf_page":int(hp),"our_pdf_page":op,"image":"./v7-spreads/"+name})
    pages[hp]=pairs
# Publish exact Word chunks and PDF only after passing the checks.
step=(len(binary)+14)//15
for idx in range(15):
    (DLD/f"{PREFIX}.part{idx+1:02}.bin").write_bytes(binary[idx*step:(idx+1)*step])
assert sha(b"".join((DLD/f"{PREFIX}.part{i:02}.bin").read_bytes() for i in range(1,16)))==source["source"]["sha256"]
(DLD/f"{PREFIX}.pdf").write_bytes(pdfpath.read_bytes())
write_json(EDITOR/"manuscript-v7-wind-theory.json",source)
write_json(COMPARE/"v7-page-map.json",{"version":"V7","pdf":f"../downloads/{PREFIX}.pdf","pdf_pages":len(pdf),"pages":pages,"equation_pages":equation_pages,"source_sha256":sha(binary),"scope":"真实PDF原页；风场目标谱、实算风场时程、自谱与相干性验证仍待原始风场数据核验。"})
# Wire existing workbench, only after all outputs exist.
js=ROOT/"manuscript-workbench.js"
s=js.read_text(encoding="utf8")
assert "ch2-graphics-manuscript-v6.json" in s
s=s.replace("ch2-graphics-manuscript-v6.json","manuscript-v7-wind-theory.json").replace(OLD,PREFIX)
s=s.replace("下载第二章四图重绘版PDF · 132页",f"下载V7合并版PDF · {len(pdf)}页")
s=s.replace("V6在V5正文基础上重绘并替换图2-1至图2-4；原有完整Word正文、公式和表格保留。","V7继承V6第二章四图，修订第三章风场理论及18条编号公式；其余原文、表格和图件保留。")
# Real equation view in browser, Word equations remain native OMML.
anchor=" const wrap=E('div','paper-block kind-'+b.kind+(changed?' edited':''));wrap.dataset.block=b.id;"
assert anchor in s
s=s.replace(anchor,anchor+'''
 if(b.equation_latex){
  const line=E('div','v7-equation');
  const formula=E('span','v7-formula');
  if(window.katex)window.katex.render(b.equation_latex,formula,{throwOnError:false,displayMode:true});
  else formula.textContent=b.equation_latex;
  line.append(formula,E('span','v7-equation-number','（'+b.equation_label+'）'));
  wrap.append(line);return wrap;
 }
''')
js.write_text(s,encoding="utf8")
html=ROOT/"manuscript-workbench.html"
s=html.read_text(encoding="utf8").replace(OLD,PREFIX).replace("CHAPTER TWO V6","V7 / WIND THEORY").replace("第二章四张计算图已规范重绘，保留原有Word正文、公式及计算记录。","保留第二章四图；第三章新增规范风场理论与公式。").replace("第二章四图重绘版132页 · 公式与图件",f"V7合并版{len(pdf)}页 · 公式与图件")
s=s.replace('<script defer src="./manuscript-workbench.js"></script>','<link rel="stylesheet" href="./vendor/katex/katex.min.css"><script defer src="./vendor/katex/katex.min.js"></script><script defer src="./manuscript-workbench.js"></script><style>.v7-equation{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:8px;overflow:auto}.v7-formula{min-width:0}.v7-equation-number{white-space:nowrap;font-family:serif}</style>')
html.write_text(s,encoding="utf8")
# Keep 90-page historical atlas; add latest side-by-side Word renders at reviewed pages only.
idx=COMPARE/"index.html"
s=idx.read_text(encoding="utf8")
assert 'id="spread-link"' in s
s=s.replace('<div class="audit">','<section id="v7-review" hidden><h2>V7修改后真实论文原页</h2><div id="v7-pairs"></div></section><div class="audit">')
s=s.replace("何论文的地震、软件开发和可靠度章节不是我们抗风优化论文必须照搬的研究目标。","本文保留风与地震研究要求；软件开发及可靠度分析不机械照搬。")
s=s.replace('function go(n){','let v7Map=null;fetch("./v7-page-map.json").then(r=>r.json()).then(v=>{v7Map=v;if(index&&notes)go(current)}).catch(()=>{});\\nfunction go(n){'.replace("\\n","\n"))
old='$("#his").textContent=v.summary;$("#mine").textContent=v.next;'
assert old in s
s=s.replace(old,old+'''
const review=$("#v7-review"), pairs=$("#v7-pairs");pairs.replaceChildren();const latest=v7Map?.pages[String(current)];review.hidden=!latest;
if(latest){for(const pair of latest){const cap=document.createElement("p");cap.textContent="左：何 PDF第"+pair.he_pdf_page+"页｜右：V7 PDF第"+pair.our_pdf_page+"页";const a=document.createElement("a");a.href=pair.image;a.target="_blank";a.rel="noopener";const img=document.createElement("img");img.src=pair.image;img.alt=cap.textContent;img.style.cssText="width:100%;height:auto;display:block";a.append(img);pairs.append(cap,a)}}
''')
s=s.replace("本人论文2026-11-21精修基准136页","历史对照：2026-11-21基准136页；第18–19页附V7修订后真实原页")
idx.write_text(s,encoding="utf8")
write_json(OUT/"v7-audit.json",{"parent_sha256":sha(raw),"word_sha256":sha(binary),"paragraphs":932,"tables":37,"inline_shapes":4,"math_objects":64,"numbered_wind_equations":18,"pdf_pages":len(pdf),"equation_pages":equation_pages,"preserved_non_document_xml_parts":True,"new_physical_runs":0})
print("V7_REAL_WORD_RENDERED",sha(binary),len(pdf),equation_pages)
