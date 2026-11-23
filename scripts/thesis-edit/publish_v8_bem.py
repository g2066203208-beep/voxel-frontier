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
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from lxml import etree

root=Path("public/thesis-studio")
downloads=root/"downloads"
editor=root/"editor-data"
compare=root/"he-thesis-comparison"
out=Path("_generated_thesis_v8");out.mkdir(exist_ok=True)
prefix="10MW-thesis-v8r9-he28-20261123"
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
expected_eq=revision.get("expected_native_equations",32)
assert len(tex)==expected_eq
he28=revision["he28_model_mechanics"]
assert he28["insert_before_id"]=="b0371" and [k for k,v in he28["blocks"]]==["p","e","p","p","e","p"]
he28_eq=[v for k,v in he28["blocks"] if k=="e"]
assert len(he28_eq)==2 and he28["equation_labels"]==["3.4-1","3.4-2"]
# Use display line breaks for the longest expressions, preserving their algebra.
tex_doc=list(tex)
tex_doc[4]=r"\begin{aligned}V_{n,b}&=\mathbf e_n^{\mathsf T}(\mathbf v_w-\mathbf v_s)\\ V_{t,b}&=\mathbf e_t^{\mathsf T}(\mathbf v_w-\mathbf v_s)\end{aligned}"
tex_doc[26]=r"\begin{aligned}\mathbf M_O={}&\sum_{b=1}^{B}\int [(\mathbf x_b-\mathbf x_O)\times(\mathbf\Phi_b\mathbf f_b)\\&\quad+\mathbf\Phi_b\mathbf m_b]\,\mathrm ds\end{aligned}"
tex_doc.extend(he28_eq)
(out/"math.md").write_text("\n\n".join("$$\n"+t+"\n$$" for t in tex_doc),encoding="utf8")
subprocess.run(["pandoc","-f","markdown","-t","docx","-o",str(out/"math.docx"),str(out/"math.md")],check=True)
mathdoc=Document(out/"math.docx")
omml=mathdoc.element.xpath(".//m:oMath")
assert len(omml)==expected_eq+len(he28_eq), len(omml)
# Two independent monochrome publication-grade source SVG diagrams.
figsources={
    "图3.3-1":("bem-streamtube-rotor-v9.svg","bem-streamtube-rotor-v9.png",540),
    "图3.3-2":("bem-airfoil-velocity-force-v9.svg","bem-airfoil-velocity-force-v9.png",560)
}
for caption,(src,png,h) in figsources.items():
    svg=(downloads/src).read_text(encoding="utf8")
    assert "viewBox" in svg and "Noto Serif CJK" in svg
    cairosvg.svg2png(bytestring=svg.encode("utf8"),write_to=str(out/png),output_width=1620,output_height=round(1620*h/1120))
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
        label=val.split()[0]
        assert label in figsources,("unknown figure label",val)
        src,png,_=figsources[label]
        par=doc.add_paragraph()
        par.alignment=WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.first_line_indent=Pt(0)
        par.paragraph_format.space_before=Pt(8);par.paragraph_format.space_after=Pt(8)
        par.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
        par.paragraph_format.keep_with_next=True
        par.add_run().add_picture(str(out/png),width=Inches(5.4))
        anchor.addprevious(par._p)
        el=clone_text(figure_caption,val)
        insert(el,i,kind="figure",style=Paragraph(el,doc).style.name,text=val,has_media=False,has_math=False,figure_asset="./downloads/"+src,figure_caption_match=val)
    elif kind=="t":
        cap="表3.3-1  AeroDyn主要气动参数"
        el=clone_text(table_caption,cap)
        cappar=Paragraph(el,doc)
        cappar.paragraph_format.keep_with_next=True
        # The 9-row BEM setup table is short; start it on a fresh page rather
        # than splitting two rows off without a "continued table" caption.
        cappar.paragraph_format.page_break_before=True
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
assert n==expected_eq
he28_anchor=old_by_id[he28["insert_before_id"]][2]
assert he28_anchor.getparent() is body
added28=[]
n28=0
for i,(kind,val) in enumerate(he28["blocks"]):
    if kind=="p":
        el=clone_text(template,val)
        para=Paragraph(el,doc)
        for run in para.runs:
            run.font.color.rgb=RGBColor(0,0,0)
            run.underline=False
        if i+1<len(he28["blocks"]) and he28["blocks"][i+1][0]=="e":
            para.paragraph_format.keep_with_next=True
        info=dict(id=f"v8r9-he28-{i:02d}",kind="text",style=para.style.name,
                  text=val,has_media=False,has_math=False,word_body_index=-1)
    else:
        label=he28["equation_labels"][n28]
        el=deepcopy(equation)
        origmath=el.xpath(".//m:oMath");assert len(origmath)==1
        origmath[0].getparent().replace(origmath[0],deepcopy(omml[expected_eq+n28]))
        labels=[t for t in el.xpath(".//w:t") if "3.2-14" in (t.text or "")]
        assert len(labels)==1
        labels[0].text=labels[0].text.replace("3.2-14",label)
        info=dict(id=f"v8r9-he28-{i:02d}",kind="text",style=Paragraph(el,doc).style.name,
                  text="\\t\\t（"+label+"）",has_media=False,has_math=True,
                  equation_label=label,equation_latex=val,word_body_index=-1)
        n28+=1
    he28_anchor.addprevious(el)
    new[el]=("03",info)
    added28.append(el)
assert len(added28)==6 and n28==2
# These five V5-era wind-case paragraphs were left after the newly inserted 3.3.3
# in previous builds, breaking the academic section order and repeating 3.1/3.2/3.5.
# Remove only these exact, auditable source IDs; preserve them in the frozen V7 parent.
redundant_ids=["b0359","v7-0354-00","b0361","v7-0356-00","b0363"]
for rid in redundant_ids:
    cid,block,element=old_by_id[rid]
    assert cid=="03" and block["kind"]=="text" and element.getparent() is body
    body.remove(element)
assert all(old_by_id[rid][2].getparent() is None for rid in redundant_ids)
# Replace the archived four-paragraph 3.10 summary in the real original Word.
summary_anchor=old_by_id["b0642"][2]
assert Paragraph(summary_anchor,doc).text=="3.10 本章小结"
summary_par=Paragraph(summary_anchor,doc)
summary_par.paragraph_format.page_break_before=True
summary_par.paragraph_format.keep_with_next=True
for sid in ("b0643","b0644","b0645","b0646"):
    element=old_by_id[sid][2]
    assert element.getparent() is body
    body.remove(element)
assert len(revision["chapter3_summary"])==6
# Academic style gate for all 31 revised source paragraphs, 3.3.4 prose and chapter summary.
assert revision.get("version")=="V8-R9"
assert len(revision["claim_corrections"])==48
assert len(revision["blocks"])==98 and sum(k=="e" for k,v in revision["blocks"])==37
for text_part in list(revision["claim_corrections"].values())+[v for k,v in revision["blocks"] if k=="p"]+list(revision["chapter3_summary"]):
    for bad in ("不能冒称","不在此宣称","不能据此宣称","本版不将","待验证状态","RUN=0","HOLD","AI写作"):
        assert bad not in text_part,("EDITORIAL_LANGUAGE_GATE",bad,text_part[:90])
cursor=summary_anchor
for j,paragraph in enumerate(revision["chapter3_summary"],1):
    el=clone_text(template,paragraph)
    cursor.addnext(el);cursor=el
    new[el]=("03",{"id":f"v8r5-summary-{j}","kind":"text","style":Paragraph(el,doc).style.name,"text":paragraph,"has_media":False,"has_math":False,"word_body_index":-1})
# Replace source paragraphs whose wording incorrectly upgraded an unverified historical
# Simpack route to the current validated production chain. All retained results,
# formulas, tables, figures, and frozen physical sources remain unchanged.
for sid,revised in revision.get("claim_corrections",{}).items():
    assert sid in old_by_id,("unknown claim",sid)
    cid,block,original=old_by_id[sid]
    assert block["kind"] in ("text","figure","h2","h3"),("unsafe claim type",sid,block["kind"])
    assert original.getparent() is body
    native_text=Paragraph(original,doc).text
    expected_text=block["text"]
    if native_text!=expected_text:
        # Legacy editor strings can differ from Word paragraph text only in Unicode
        # normalization or field/soft-break spacing. Reject substantive changes.
        from difflib import SequenceMatcher
        normalize_source=lambda v:re.sub(r"\s+","",unicodedata.normalize("NFKC",v)).replace(chr(173),"")
        actual_norm,expected_norm=normalize_source(native_text),normalize_source(expected_text)
        similarity=SequenceMatcher(None,actual_norm,expected_norm,autojunk=False).ratio()
        assert similarity>=0.995 and actual_norm[:60]==expected_norm[:60],(
            "PARENT_SOURCE_TEXT_DRIFT",sid,len(actual_norm),len(expected_norm),
            round(similarity,6),actual_norm[-120:],expected_norm[-120:])
    el=clone_text(original,revised)
    # All revised body paragraphs use academic black text; preserve heading/caption styles.
    if block["kind"]=="text":
        para=Paragraph(el,doc)
        for run in para.runs:
            run.font.color.rgb=RGBColor(0,0,0)
            run.underline=False
            run.bold=False
    original.addprevious(el);body.remove(original)
    new[el]=(cid,dict(block,text=revised,word_body_index=-1))
assert len(revision.get("claim_corrections",{}))>=25
ref_anchor=lastref
for i,ref in enumerate(revision["references"]):
    el=clone_text(lastref,ref);ref_anchor.addnext(el);ref_anchor=el
    new[el]=("07",{"id":f"v8-ref-{128+i}","kind":"text","style":Paragraph(el,doc).style.name,"text":ref,"has_media":False,"has_math":False,"word_body_index":-1})
assert all(etree.tostring(el)==xml for el,xml in original_xml.items() if el.getparent() is body and el is not summary_anchor),"retained original nodes changed unexpectedly"
assert all(Paragraph(old_by_id[rid][2],doc).text==old_by_id[rid][1]["text"] for rid in redundant_ids),"removed paragraph text differs from frozen original"
assert len(doc.tables)==38 and len(doc.inline_shapes)==6
assert Paragraph(old_by_id["b0364"][2],doc).text.startswith("3.4 ") and old_by_id["b0364"][2].getprevious() is not old_by_id["b0363"][2]
assert len(doc.element.xpath(".//m:oMath"))==math0+expected_eq+len(he28_eq)
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
check=Document(final);assert len(check.tables)==38 and len(check.inline_shapes)==6
assert len(check.element.xpath(".//m:oMath"))==math0+expected_eq+len(he28_eq)
doc_text=[p.text for p in check.paragraphs]
for k,v in he28["blocks"]:
    if k=="p":assert v in doc_text,("HE28_FORMAL_PARAGRAPH_MISSING",v[:70])
for label in he28["equation_labels"]:
    assert any(label in p for p in doc_text),("HE28_FORMULA_MISSING",label)
# Actual Word-body source claim texts must match all revised academic paragraphs.
word_content=[q.text for q in check.paragraphs]
for sid,t in revision["claim_corrections"].items():
    assert t in word_content,("ACADEMIC_REVISION_NOT_IN_WORD",sid)
for t in revision["chapter3_summary"]:
    assert t in word_content,("ACADEMIC_SUMMARY_NOT_IN_WORD",t[:80])
# Check the five model-definition paragraphs against current exact source wording.
p27_ids=("b0367","b0368","b0369","b0370","b0371")
p27_paras=[p.text for p in check.paragraphs]
p27_indices=[p27_paras.index(revision["claim_corrections"][sid]) for sid in p27_ids]
assert p27_indices==sorted(p27_indices),("HE27_SOURCE_PARAGRAPHS_OUT_OF_ORDER",p27_indices)
chapters={c["id"]:dict(c,blocks=[]) for c in source["chapters"]}
for idx,el in enumerate(body):
    item=new.get(el,existing.get(el))
    if item:
        cid,b=item;b["word_body_index"]=idx;chapters[cid]["blocks"].append(b)
source["chapters"]=list(chapters.values())
allblocks=[b for c in source["chapters"] for b in c["blocks"]]
assert len({b["id"] for b in allblocks})==len(allblocks)
assert sum(b.get("equation_label","").startswith("3.3-") for b in allblocks)==expected_eq
assert {b.get("equation_label") for b in allblocks if b.get("equation_label","").startswith("3.4-")}==set(he28["equation_labels"])
assert sum("manuscript-figures-v6" in b.get("figure_asset","") for b in allblocks)==4
assert {b["text"].split()[0] for b in allblocks if b.get("figure_asset","").endswith("-v9.svg")}=={"图3.3-1","图3.3-2"}
binary=final.read_bytes()
source["source"].update(name="10MW混塔论文_V8R9_整机运动学与动力学正式修订版.docx",sha256=sha(binary),bytes=len(binary),pdf=f"./downloads/{prefix}.pdf",docx_parts_pattern=f"./downloads/{prefix}.partNN.bin",docx_parts=15,editorial_scope="V8-R9: 37 native BEM/aero formulas preserved, 31 original V7 evidence-boundary corrections retained; five §3.4.1 paragraphs corrected against He PDF27 on verified geometry, frame, six-component tower interface, and prestress/connection assumptions. Physical wind mapping, W/E/WE, Miner and optimization remain unverified.")
subprocess.run(["libreoffice","-env:UserInstallation=file:///tmp/lo-thesis-v8","--headless","--convert-to","pdf","--outdir",str(out),str(final)],check=True)
pdfpath=out/f"{prefix}.pdf";pdf=fitz.open(pdfpath)
assert 131<=len(pdf)<=158
norm=lambda x:re.sub(r"\s+","",unicodedata.normalize("NFKC",x)).replace("−","-").replace("‐","-")
texts=[norm(p.get_text()) for p in pdf]
def locate(s):
    matches=[i+1 for i,t in enumerate(texts) if i>=31 and norm(s) in t]
    assert matches,("missing actual PDF anchor",s)
    return matches[0]
pages={f"3.3-{i}":locate(f"（3.3-{i}）") for i in range(1,expected_eq+1)}
# Font/Math import smoke gate: an equation number alone is NOT a rendered equation.
# Check raster ink on the equation baseline to reject blank LibreOffice math objects.
ink_ok=0
for i in range(1,expected_eq+1):
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
assert start<=pages["3.3-1"]<=pages["3.3-27"]<=pages[f"3.3-{expected_eq}"]<=end
assert len(set(pages.values()))>=3
# The original figure must occupy a readable area, not a clipped line.
figures=[]
for pi in range(start-1,end):
    for info in pdf[pi].get_image_info():
        rect=fitz.Rect(info["bbox"])
        if rect.width>250 and rect.height>95 and info["width"]>=1000:
            figures.append((pi+1,rect.width,rect.height))
assert len(figures)>=2,("TWO_BEM_FIGURES_NOT_RENDERED",figures)
# Require all aerodynamic setup rows on one physical PDF page.
table_pages=[i+1 for i,t in enumerate(texts) if "WakeMod" in t and "AeroDyn" in t]
assert any(all(z in texts[p-1] for z in ("WakeMod","SkewMod","AirDens","MaxIter","TwrAero")) for p in table_pages),("BEM_TABLE_SPLIT_OR_TRUNCATED",table_pages)
print("BEM_FORMULAS_FIGURE_AND_TABLE_VISIBLE",ink_ok,figures,table_pages)
he=fitz.open(root/"documents/He_Zeyu_2024_hybrid_tower_thesis.pdf");assert len(he)==90
spread=compare/"v8r9-spreads";spread.mkdir(exist_ok=True)
groups={}
v7=json.loads((compare/"v7-page-map.json").read_text())
for hp,items in v7["pages"].items():
    groups[hp]=sorted({z["our_pdf_page"] for z in items})
for hp,(lo,hi) in {"20":(1,4),"21":(5,8),"22":(9,13),"23":(14,21),"24":(22,27)}.items():
    lp=start if lo==1 else pages[f"3.3-{lo}"]
    rp=end if hi==27 else pages[f"3.3-{hi}"]
    if hi==4:rp=max(rp,pages["3.3-5"]-1)
    groups[hp]=list(range(lp,rp+1))
groups["25"]=list(range(pages["3.3-28"],pages["3.3-32"]+1))
# He PDF26 is a chapter summary; pair with our actual section 3.10 summary.
groups["26"]=[locate("3.10 本章小结")]
# 何2024 PDF27: compare his 8-DOF model hypotheses with OUR revised subsection, not an old thematic lookalike.
he27_start=locate("3.4.1")
he27_end=locate("塔身独立分布气动力应分别处理")
assert he27_start<=he27_end and he27_end-he27_start<=2
# Pair He p27 with every native page actually containing the revised subsection.
groups["27"]=list(range(he27_start,he27_end+1))
he28_start=locate("为描述三叶片风轮的瞬时空间方位")
he28_end=locate("（3.4-2）")
assert he28_start<=he28_end and he28_end-he28_start<=2
groups["28"]=list(range(he28_start,he28_end+1))
def raster(d,p):
    x=d[p-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
    return Image.frombytes("RGB",(x.width,x.height),x.samples)
map_pages={}
for hp,items in groups.items():
    result=[]
    for op in items:
        a,b=raster(he,int(hp)),raster(pdf,op)
        im=Image.new("RGB",(a.width+b.width+18,max(a.height,b.height)),"#e5e9ed");im.paste(a,(0,0));im.paste(b,(a.width+18,0))
        name=f"he{hp}-v8r9-{op}.png";im.save(spread/name,optimize=True)
        result.append({"he_pdf_page":int(hp),"our_pdf_page":op,"image":"./v8r9-spreads/"+name})
    map_pages[hp]=result
# All actual amended pages are individually rendered, independent of historical comparisons.
read_pages=out/"bem-pages";read_pages.mkdir(exist_ok=True)
for p in range(start,end+1):raster(pdf,p).save(read_pages/f"page-{p}.png")
step=(len(binary)+14)//15
for i in range(15):(downloads/f"{prefix}.part{i+1:02}.bin").write_bytes(binary[i*step:(i+1)*step])
assert sha(b"".join((downloads/f"{prefix}.part{i:02}.bin").read_bytes() for i in range(1,16)))==source["source"]["sha256"]
(downloads/f"{prefix}.pdf").write_bytes(pdfpath.read_bytes())
save_json(editor/"manuscript-v8-bem.json",source)
assert len(map_pages["28"])>=1 and all(x["he_pdf_page"]==28 for x in map_pages["28"])
save_json(compare/"v8r9-page-map.json",{"version":"V8-R9","pdf":f"../downloads/{prefix}.pdf","pdf_pages":len(pdf),"pages":map_pages,"equation_pages":pages,"source_sha256":sha(binary),"scope":"V8-R9 original Word/PDF with 37 native aero formulas, and source-bounded §3.4.1 model/coordinate/DOF correction based on He PDF27; no new physical validation."})
save_json(out/"v8-audit.json",{"parent_sha256":sha(raw),"word_sha256":sha(binary),"pdf_pages":len(pdf),"inserted_omml":expected_eq+len(he28_eq),"he28_equations":he28["equation_labels"],"tables":38,"figures":6,"bem_pdf_pages":list(range(start,end+1)),"equations":pages,"physics_runs":0,"review_status":"two source-SVG figures; actual Word/PDF page inspection required"})
js=root/"manuscript-workbench.js"
s=js.read_text(encoding="utf8")
assert ("manuscript-v7-wind-theory.json" in s or "manuscript-v8-bem.json" in s), "unknown editor mother version"
s=s.replace("manuscript-v7-wind-theory.json","manuscript-v8-bem.json").replace("10MW-thesis-v8r8-academic-20261123",prefix).replace("10MW-thesis-v8r7-he27-20261123",prefix).replace("10MW-thesis-v8r6-evidence-20261123",prefix).replace("10MW-thesis-v8r5-theory-20261123",prefix).replace("10MW-thesis-v8r4-bem-20261122",prefix).replace("10MW-thesis-v8r3-bem-20261122",prefix).replace("10MW-thesis-v8r2-bem-20261122",prefix).replace("10MW-thesis-v8-bem-20261122",prefix).replace(old,prefix).replace("下载V7合并版PDF · 131页",f"下载V8审阅版PDF · {len(pdf)}页").replace("V7继承V6第二章四图，修订第三章风场理论及18条编号公式；其余原文、表格和图件保留。","V8继承V7，增补叶素动量理论27条原生公式、原理图和实际AeroDyn设置，保留原有研究结果。")
js.write_text(s,encoding="utf8")
html=root/"manuscript-workbench.html"
s=html.read_text(encoding="utf8").replace("10MW-thesis-v8r8-academic-20261123",prefix).replace("10MW-thesis-v8r5-theory-20261123",prefix).replace("10MW-thesis-v8r4-bem-20261122",prefix).replace("10MW-thesis-v8r3-bem-20261122",prefix).replace("10MW-thesis-v8r2-bem-20261122",prefix).replace("10MW-thesis-v8-bem-20261122",prefix).replace(old,prefix).replace("V7 / WIND THEORY","V8 / BEM THEORY").replace("保留第二章四图；第三章新增规范风场理论与公式。","保留第二章四图及风场理论；新增叶素动量理论。<br><a href='./chapter3-bem-v8.html'>查看3.3节完整精修正文</a>").replace("V7合并版131页",f"V8审阅版{len(pdf)}页")
html.write_text(s,encoding="utf8")
idx=compare/"index.html"
s=idx.read_text(encoding="utf8").replace("v8r8-page-map.json","v8r9-page-map.json").replace("v8r7-page-map.json","v8r9-page-map.json").replace("v8r6-page-map.json","v8r9-page-map.json").replace("v8r5-page-map.json","v8r9-page-map.json").replace("v8r4-page-map.json","v8r9-page-map.json").replace("v7-page-map.json","v8r5-page-map.json").replace("v8-page-map.json","v8r5-page-map.json").replace("V7修改后真实论文原页","V8-R4修改后真实论文原页").replace("右：V7 PDF第","右：V8 PDF第").replace("第18–19页附V7修订后真实原页","第18–19、20–24页附V8修订后真实原页")
if '<a href="../chapter3-bem-v8.html">3.3节叶素动量理论完整修订正文</a>' not in s:
    s=s.replace('<section id="v7-review" hidden>','<section id="v7-review" hidden><a href="../chapter3-bem-v8.html">3.3节叶素动量理论完整修订正文</a>')
idx.write_text(s,encoding="utf8")

# Side-by-side original page illustrations and source-based prose outside the thesis body.
from html import escape as html_escape
he28_pngs=[]
for entry in map_pages["28"]:
    pp=int(entry["our_pdf_page"])
    uri="../"+entry["image"].removeprefix("./")
    he28_pngs.append(
        '<figure><a href="'+html_escape(uri)+'" target="_blank" rel="noopener">'
        '<img loading="lazy" alt="何泽瑜PDF第28页与我们论文PDF第'+str(pp)+'页的原始对照图" src="'+html_escape(uri)+'"></a>'
        '<figcaption>左：何泽瑜论文原PDF第28页　右：我们V8-R9论文原PDF第'+str(pp)+'页</figcaption></figure>'
    )
he28_pair_info=[
 ("图3-1：混塔整机正视与侧视、塔顶自由度","我方已有158 m混塔、RNA及OpenFAST不同模型层级；研究对象与八自由度简化模型不同。"),
 ("图3-2：叶片局部模型、法向与侧向弯曲","我方3.3节已有叶片气动坐标与气动力的虚功表示；各模型的柔性自由度由实际结构输入决定。"),
 ("式（3.1）：三个叶片的旋转方位角","补写式（3.4-1），采用变转速积分与120°相位差，恒定转速为其特例。"),
 ("式（3.2）：8自由度Euler–Lagrange方程","补写一般动力平衡式（3.4-2）；实际整机采用Kane方法的ElastoDyn，而非参考论文的八自由度运动方程。")
]
he28_audit="<table><tbody>"+ "".join(
    "<tr><th>"+html_escape(label)+"</th><td>"+html_escape(note)+"</td></tr>"
    for label,note in he28_pair_info)+"</tbody></table>"
he28_formal="".join(
    ("<p>"+html_escape(content)+"</p>") if kind=="p"
    else ("<div class='eq' data-tex='"+html_escape(content,quote=True)+"'>"+html_escape(content)+"</div>")
    for kind,content in he28["blocks"]
)
he28_html=(
'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
'<title>何论文PDF28：逐项核对及学术正文原图</title><link rel="stylesheet" href="../../vendor/katex/katex.min.css">'
'<script defer src="../../vendor/katex/katex.min.js"></script>'
'<style>*{box-sizing:border-box}body{margin:0;background:#f0f4f6;color:#1b3440;font:15px/1.85 "Noto Serif CJK SC","SimSun",serif}'
'header{padding:24px max(15px,calc((100vw - 1140px)/2));background:#173644;color:white;font:14px/1.7 "Microsoft YaHei",sans-serif}'
'header h1{font-size:23px;margin:0 0 5px}header a{color:#d5eeee}'
'main{max-width:1160px;margin:auto;padding:18px 12px 40px}.paper{background:white;border:1px solid #d2dfe6;border-radius:8px;padding:20px;margin:16px 0}'
'h2{font-size:19px;margin:0 0 14px}h3{font-size:17px}figure{margin:16px 0 30px}figure img{display:block;width:100%;height:auto;border:1px solid #cbdae1}'
'figcaption{font-size:13px;color:#5c6c77;margin:7px 0}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #dbe5ea;padding:9px;text-align:left;vertical-align:top}'
'th{width:36%}.eq{margin:17px 0;text-align:center;overflow:auto}p{text-indent:2em;text-align:justify}'
'@media(max-width:700px){.paper{padding:12px}header h1{font-size:19px}}</style></head>'
'<body><header><h1>何泽瑜第三章第28页 · 原始论文逐项比对与我方正式修订</h1>'
'<a href="./">返回第三章原页对照</a>　·　<a href="../../downloads/10MW-thesis-v8r9-he28-20261123.pdf">最新版完整论文PDF</a></header>'
'<main><section class="paper"><h2>原文与修订后的真实PDF页面</h2>'+ "".join(he28_pngs)+'</section>'
'<section class="paper"><h2>本页逐项对比</h2>'+he28_audit+'</section>'
'<section class="paper"><h2>正式论文3.4.1节新增学术正文</h2>'+he28_formal+
'<p>理论来源：[132] OpenFAST ElastoDyn官方手册；[133] OpenFAST AeroDyn坐标系文档。</p></section></main>'
'<script>window.addEventListener("DOMContentLoaded",()=>{if(window.katex)for(const el of document.querySelectorAll(".eq"))katex.render(el.dataset.tex,el,{displayMode:true,throwOnError:false});});</script>'
'</body></html>'
)
he28_page=compare/"ch3-v8r6/he28-academic-revision.html"
he28_page.write_text(he28_html,encoding="utf8")
gallery_page=compare/"ch3-v8r6/index.html"
gallery=gallery_page.read_text(encoding="utf8")
if 'href="./he28-academic-revision.html"' not in gallery:
    gallery_anchor='<a href="./he27-academic-revision.html">'
    assert gallery_anchor in gallery
    gallery=gallery.replace(gallery_anchor,
       '<a href="./he28-academic-revision.html">第28页方位角与动力学公式原页修订</a>'+gallery_anchor)
    gallery_page.write_text(gallery,encoding="utf8")

print("V8_WORD_RENDER_PASS",sha(binary),len(pdf),"BEM",start,end)
