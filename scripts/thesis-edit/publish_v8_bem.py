"""V8 BEM editorial insertion; original V7 Word is the only accepted parent."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
import json, hashlib, re, subprocess, unicodedata
import fitz, cairosvg
from PIL import Image
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from lxml import etree

root=Path("public/thesis-studio")
downloads=root/"downloads"
editor=root/"editor-data"
compare=root/"he-thesis-comparison"
out=Path("_generated_thesis_v8");out.mkdir(exist_ok=True)
prefix="10MW-thesis-v8-bem-20261122"
old="10MW-thesis-v7-wind-theory-20261122"
sha=lambda x:hashlib.sha256(x).hexdigest()
def save_json(path,x):
    path.write_text(json.dumps(x,ensure_ascii=False,separators=(",",":")),encoding="utf8")

revision=json.loads(Path("scripts/thesis-edit/ch3_bem_v8.json").read_text(encoding="utf8"))
source=json.loads((editor/"manuscript-v7-wind-theory.json").read_text(encoding="utf8"))
raw=b"".join((downloads/f"{old}.part{i:02}.bin").read_bytes() for i in range(1,16))
assert sha(raw)==source["source"]["sha256"]==revision["parent_sha256"]
parent=out/"source-v7.docx";parent.write_bytes(raw)
doc=Document(parent);body=doc.element.body;original_children=list(body)
assert len(doc.inline_shapes)==4 and len(doc.tables)==37
math0=len(doc.element.xpath(".//m:oMath"))
old_by_id={b["id"]:(c["id"],deepcopy(b),original_children[b["word_body_index"]]) for c in source["chapters"] for b in c["blocks"]}
existing={el:(cid,b) for cid,b,el in old_by_id.values()}
anchor=old_by_id[revision["anchor"]][2]
assert Paragraph(anchor,doc).text==old_by_id[revision["anchor"]][1]["text"]
template=anchor
heading=next(el for cid,b,el in old_by_id.values() if b.get("text")=="3.2.4 随机风场离散与生成")
equation=next(el for cid,b,el in old_by_id.values() if b.get("equation_label")=="3.2-14")
figure_caption=old_by_id["b0354"][2]
table_caption=old_by_id["b0326"][2]
lastref=old_by_id["b0927"][2]
assert Paragraph(lastref,doc).text.startswith("[127]")
original_xml={el:etree.tostring(el) for el in original_children}
new={}
def clone_text(tpl,text):
    el=deepcopy(tpl)
    for child in list(el):
        if child.tag!=qn("w:pPr"): el.remove(child)
    p=Paragraph(el,doc)
    r=p.add_run(text)
    orig=Paragraph(tpl,doc)
    if orig.runs and orig.runs[0]._r.rPr is not None:
        r._r.insert(0,deepcopy(orig.runs[0]._r.rPr))
    return el
def insert(el,idx,cid="03",**fields):
    anchor.addprevious(el)
    fields.update(id=f"v8-{idx:03d}",word_body_index=-1)
    new[el]=(cid,fields)
    return el
# Pandoc converts the actual reviewed LaTeX into editable native Word OMML.
tex=[v for k,v in revision["blocks"] if k=="e"]
assert len(tex)==27
# Use display line breaks for the longest expressions, preserving their algebra.
tex_doc=list(tex)
tex_doc[4]=r"\begin{aligned}V_{n,b}&=\mathbf e_n^{\mathsf T}(\mathbf v_w-\mathbf v_s)\\ V_{t,b}&=\mathbf e_t^{\mathsf T}(\mathbf v_w-\mathbf v_s)\end{aligned}"
tex_doc[26]=r"\begin{aligned}\mathbf M_O={}&\sum_{b=1}^{B}\int [(\mathbf x_b-\mathbf x_O)\times(\mathbf\Phi_b\mathbf f_b)\\&\quad+\mathbf\Phi_b\mathbf m_b]\,\mathrm ds\end{aligned}"
(out/"math.md").write_text("\n\n".join("$$\n"+t+"\n$$" for t in tex_doc),encoding="utf8")
subprocess.run(["pandoc","-f","markdown","-t","docx","-o",str(out/"math.docx"),str(out/"math.md")],check=True)
mathdoc=Document(out/"math.docx")
omml=mathdoc.element.xpath(".//m:oMath")
assert len(omml)==27, len(omml)
# Original schematic, not a solver result.
fig=downloads/"bem-figure-v8.svg"
# Lay out the three panels in two rows for legible Word-page labels.
svg=fig.read_text(encoding="utf8")
# Keep the original landscape three-panel diagram; no tall white padded crop.
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out/"bem-figure.png"),output_width=1620,output_height=690)
# All new body nodes use the pre-existing thesis template.
n=0
for i,(kind,val) in enumerate(revision["blocks"]):
    bbase={"has_media":False,"has_math":False}
    if kind=="h":
        el=clone_text(heading,val);p=Paragraph(el,doc);p.paragraph_format.keep_with_next=True
        insert(el,i,kind="h3",style=p.style.name,text=val,**bbase)
    elif kind=="p":
        el=clone_text(template,val);p=Paragraph(el,doc)
        if re.match(r"^（[1-5]）",val):
            p.paragraph_format.keep_with_next=True
            for r in p.runs:r.bold=True
        insert(el,i,kind="text",style=p.style.name,text=val,**bbase)
    elif kind=="e":
        n+=1;label=f"3.3-{n}"
        el=deepcopy(equation)
        oldmath=el.xpath(".//m:oMath");assert len(oldmath)==1
        oldmath[0].getparent().replace(oldmath[0],deepcopy(omml[n-1]))
        labels=[t for t in el.xpath(".//w:t") if "3.2-14" in (t.text or "")]
        assert len(labels)==1
        labels[0].text=labels[0].text.replace("3.2-14",label)
        insert(el,i,kind="text",style=Paragraph(el,doc).style.name,text="\t\t（"+label+"）",has_media=False,has_math=True,equation_label=label,equation_latex=val)
    elif kind=="g":
        par=doc.add_paragraph()
        par.alignment=WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.first_line_indent=Pt(0)
        par.paragraph_format.space_before=Pt(4);par.paragraph_format.space_after=Pt(0)
        par.paragraph_format.keep_with_next=True
        par.add_run().add_picture(str(out/"bem-figure.png"),width=Inches(5.4))
        anchor.addprevious(par._p)
        el=clone_text(figure_caption,val)
        # Caption source XML must not retain images or numbering fields.
        insert(el,i,kind="figure",style=Paragraph(el,doc).style.name,text=val,has_media=False,has_math=False,figure_asset="./downloads/bem-figure-v8.svg",figure_caption_match=val)
    elif kind=="t":
        cap="表3.3-1  AeroDyn主要气动参数"
        el=clone_text(table_caption,cap);Paragraph(el,doc).paragraph_format.keep_with_next=True
        insert(el,f"{i}-cap" if False else i+100,kind="caption",style=Paragraph(el,doc).style.name,text=cap,**bbase)
        table=doc.add_table(rows=len(val),cols=len(val[0]))
        table.alignment=WD_TABLE_ALIGNMENT.CENTER
        table.autofit=False
        widths=(1.82,1.48,2.35)
        for col,w in zip(table.columns,widths): col.width=Inches(w)
        for ri,row in enumerate(val):
            for ci,x in enumerate(row):
                cell=table.cell(ri,ci);cell.width=Inches(widths[ci])
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p=cell.paragraphs[0];p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(2);p.paragraph_format.space_after=Pt(2)
                p.paragraph_format.line_spacing=1.1
                r=p.add_run(x);r.font.size=Pt(10.5);r.bold=(ri==0)
                r.font.name="Times New Roman";r._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),"宋体")
                if ri==0:
                    tcpr=cell._tc.get_or_add_tcPr()
                    border=OxmlElement("w:tcBorders");bottom=OxmlElement("w:bottom");bottom.set(qn("w:val"),"single");bottom.set(qn("w:sz"),"4");border.append(bottom);tcpr.append(border)
            if ri==0:table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
            table.rows[ri]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        borders=OxmlElement("w:tblBorders")
        for k in ("top","left","bottom","right","insideH","insideV"):
            child=OxmlElement("w:"+k);child.set(qn("w:val"),"single" if k in ("top","bottom") else "nil")
            if k in ("top","bottom"):child.set(qn("w:sz"),"12");child.set(qn("w:color"),"000000")
            borders.append(child)
        table._tbl.tblPr.append(borders)
        insert(table._tbl,i,kind="table",rows=val)
    else:raise ValueError(kind)
assert n==27
# Remove duplicate summaries only from unmodified old 3.3? Keep every old paragraph
# for traceable continuity, including its existing operating-case definitions.
ref_anchor=lastref
for i,ref in enumerate(revision["references"]):
    el=clone_text(lastref,ref);ref_anchor.addnext(el);ref_anchor=el
    new[el]=("07",{"id":f"v8-ref-{128+i}","kind":"text","style":Paragraph(el,doc).style.name,"text":ref,"has_media":False,"has_math":False,"word_body_index":-1})
assert all(etree.tostring(el)==xml for el,xml in original_xml.items()),"original nodes changed unexpectedly"
assert len(doc.tables)==38 and len(doc.inline_shapes)==5
assert len(doc.element.xpath(".//m:oMath"))==math0+27
tmp=out/"native-v8.docx";doc.save(tmp)
final=out/f"{prefix}.docx"
# Preserve every unaffected package component byte for byte.
allowed={"word/document.xml","word/_rels/document.xml.rels","[Content_Types].xml"}
with ZipFile(parent) as a,ZipFile(tmp) as b,ZipFile(final,"w",ZIP_DEFLATED,compresslevel=6) as z:
    for item in a.infolist():
        z.writestr(item,b.read(item.filename) if item.filename in allowed else a.read(item.filename))
    for name in set(b.namelist())-set(a.namelist()):
        z.writestr(name,b.read(name))
with ZipFile(parent) as a,ZipFile(final) as b:
    assert all(a.read(n)==b.read(n) for n in a.namelist() if n not in allowed)
check=Document(final);assert len(check.tables)==38 and len(check.inline_shapes)==5
assert len(check.element.xpath(".//m:oMath"))==math0+27
chapters={c["id"]:dict(c,blocks=[]) for c in source["chapters"]}
for idx,el in enumerate(body):
    item=new.get(el,existing.get(el))
    if item:
        cid,b=item;b["word_body_index"]=idx;chapters[cid]["blocks"].append(b)
source["chapters"]=list(chapters.values())
allblocks=[b for c in source["chapters"] for b in c["blocks"]]
assert len({b["id"] for b in allblocks})==len(allblocks)
assert sum(b.get("equation_label","").startswith("3.3-") for b in allblocks)==27
assert sum("manuscript-figures-v6" in b.get("figure_asset","") for b in allblocks)==4
binary=final.read_bytes()
source["source"].update(name="10MW混塔论文_V8_叶素动量理论精修版.docx",sha256=sha(binary),bytes=len(binary),pdf=f"./downloads/{prefix}.pdf",docx_parts_pattern=f"./downloads/{prefix}.partNN.bin",docx_parts=15,editorial_scope="V8 retains V7 source and adds reviewed BEM equations, original schematic, AeroDyn parameter table and three original references. No new physical simulation.")
subprocess.run(["libreoffice","-env:UserInstallation=file:///tmp/lo-thesis-v8","--headless","--convert-to","pdf","--outdir",str(out),str(final)],check=True)
pdfpath=out/f"{prefix}.pdf";pdf=fitz.open(pdfpath)
assert 131<=len(pdf)<=155
norm=lambda x:re.sub(r"\s+","",unicodedata.normalize("NFKC",x)).replace("−","-").replace("‐","-")
texts=[norm(p.get_text()) for p in pdf]
def locate(s):
    matches=[i+1 for i,t in enumerate(texts) if i>=31 and norm(s) in t]
    assert matches,("missing actual PDF anchor",s)
    return matches[0]
pages={f"3.3-{i}":locate(f"（3.3-{i}）") for i in range(1,28)}
# Font/Math import smoke gate: an equation number alone is NOT a rendered equation.
# Check raster ink on the equation baseline to reject blank LibreOffice math objects.
ink_ok=0
for i in range(1,28):
    pg=pdf[pages[f"3.3-{i}"]-1]
    hits=pg.search_for(f"3.3-{i}")
    rendered=False
    for hit in hits:
        baseline=fitz.Rect(130,max(0,hit.y0-2),pg.rect.width-160,min(pg.rect.height,hit.y1+2))
        if baseline.is_empty:continue
        pix=pg.get_pixmap(matrix=fitz.Matrix(1.3,1.3),clip=baseline,alpha=False)
        samples=pix.samples
        dark=sum(1 for t in range(0,len(samples)-2,3) if min(samples[t],samples[t+1],samples[t+2])<180)
        if dark>=35: rendered=True;break
    if rendered:ink_ok+=1
assert ink_ok>=24,("EQUATIONS_NOT_RENDERED: reject blank numbered formulas",ink_ok)
start=locate("3.3.1 叶素动量理论与叶片气动力计算")
end=locate("3.4 Abaqus—OpenFAST结构动力一致性验证")
assert start<=pages["3.3-1"]<=pages["3.3-27"]<=end
assert len(set(pages.values()))>=3
he=fitz.open(root/"documents/He_Zeyu_2024_hybrid_tower_thesis.pdf");assert len(he)==90
spread=compare/"v8-spreads";spread.mkdir(exist_ok=True)
groups={}
v7=json.loads((compare/"v7-page-map.json").read_text())
for hp,items in v7["pages"].items():
    groups[hp]=sorted({z["our_pdf_page"] for z in items})
for hp,(lo,hi) in {"20":(1,4),"21":(5,8),"22":(9,13),"23":(14,21),"24":(22,27)}.items():
    lp=start if lo==1 else pages[f"3.3-{lo}"]
    rp=end if hi==27 else pages[f"3.3-{hi}"]
    if hi==4:rp=max(rp,pages["3.3-5"]-1)
    groups[hp]=list(range(lp,rp+1))
def raster(d,p):
    x=d[p-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
    return Image.frombytes("RGB",(x.width,x.height),x.samples)
map_pages={}
for hp,items in groups.items():
    result=[]
    for op in items:
        a,b=raster(he,int(hp)),raster(pdf,op)
        im=Image.new("RGB",(a.width+b.width+18,max(a.height,b.height)),"#e5e9ed");im.paste(a,(0,0));im.paste(b,(a.width+18,0))
        name=f"he{hp}-v8-{op}.png";im.save(spread/name,optimize=True)
        result.append({"he_pdf_page":int(hp),"our_pdf_page":op,"image":"./v8-spreads/"+name})
    map_pages[hp]=result
# All actual amended pages are individually rendered, independent of historical comparisons.
read_pages=out/"bem-pages";read_pages.mkdir(exist_ok=True)
for p in range(start,end+1):raster(pdf,p).save(read_pages/f"page-{p}.png")
step=(len(binary)+14)//15
for i in range(15):(downloads/f"{prefix}.part{i+1:02}.bin").write_bytes(binary[i*step:(i+1)*step])
assert sha(b"".join((downloads/f"{prefix}.part{i:02}.bin").read_bytes() for i in range(1,16)))==source["source"]["sha256"]
(downloads/f"{prefix}.pdf").write_bytes(pdfpath.read_bytes())
save_json(editor/"manuscript-v8-bem.json",source)
save_json(compare/"v8-page-map.json",{"version":"V8","pdf":f"../downloads/{prefix}.pdf","pdf_pages":len(pdf),"pages":map_pages,"equation_pages":pages,"source_sha256":sha(binary),"scope":"V8 real Word PDF, BEM theory and archival aerodynamic configuration; no new numerical validation."})
save_json(out/"v8-audit.json",{"parent_sha256":sha(raw),"word_sha256":sha(binary),"pdf_pages":len(pdf),"inserted_omml":27,"tables":38,"figures":5,"bem_pdf_pages":list(range(start,end+1)),"equations":pages,"physics_runs":0,"review_status":"candidate; human page review pending"})
js=root/"manuscript-workbench.js"
s=js.read_text(encoding="utf8")
assert "manuscript-v7-wind-theory.json" in s
s=s.replace("manuscript-v7-wind-theory.json","manuscript-v8-bem.json").replace(old,prefix).replace("下载V7合并版PDF · 131页",f"下载V8审阅版PDF · {len(pdf)}页").replace("V7继承V6第二章四图，修订第三章风场理论及18条编号公式；其余原文、表格和图件保留。","V8继承V7，增补叶素动量理论27条原生公式、原理图和实际AeroDyn设置，保留原有研究结果。")
js.write_text(s,encoding="utf8")
html=root/"manuscript-workbench.html"
s=html.read_text(encoding="utf8").replace(old,prefix).replace("V7 / WIND THEORY","V8 / BEM THEORY").replace("保留第二章四图；第三章新增规范风场理论与公式。","保留第二章四图及风场理论；新增叶素动量理论。<br><a href='./chapter3-bem-v8.html'>查看3.3节完整精修正文</a>").replace("V7合并版131页",f"V8审阅版{len(pdf)}页")
html.write_text(s,encoding="utf8")
idx=compare/"index.html"
s=idx.read_text(encoding="utf8").replace("v7-page-map.json","v8-page-map.json").replace("V7修改后真实论文原页","V8修改后真实论文原页").replace("右：V7 PDF第","右：V8 PDF第").replace("第18–19页附V7修订后真实原页","第18–19、20–24页附V8修订后真实原页")
s=s.replace('<section id="v7-review" hidden>','<section id="v7-review" hidden><a href="../chapter3-bem-v8.html">3.3节叶素动量理论完整修订正文</a>')
idx.write_text(s,encoding="utf8")
print("V8_WORD_RENDER_PASS",sha(binary),len(pdf),"BEM",start,end)
