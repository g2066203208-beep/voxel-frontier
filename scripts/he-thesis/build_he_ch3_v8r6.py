#!/usr/bin/env python3
# Full page-by-page visual comparison of HE2024 thesis and current manuscript.
# Real PDF screenshots + full-fidelity 2-page PDF spreads; no screenshot fabrication.
import os, sys, re, json, math, collections, html, unicodedata
from pathlib import Path
import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
HE=ROOT/"public/thesis-studio/documents/He_Zeyu_2024_hybrid_tower_thesis.pdf"
OWN=ROOT/"public/thesis-studio/downloads/10MW-thesis-v8r6-evidence-20261123.pdf"
OUT=ROOT/"public/thesis-studio/he-thesis-comparison/ch3-v8r6"
IMG=OUT/"spreads"
OUT.mkdir(parents=True,exist_ok=True)
IMG.mkdir(exist_ok=True)

A=fitz.open(HE); B=fitz.open(OWN)
REVIEWS=json.loads((OUT.parent/"review_notes.json").read_text(encoding="utf8"))
assert len(A)==90 and len(B)==139 and len(REVIEWS)==90, "Unexpected original source identity"
assert "第3章" in A[26].get_text(), "He physical PDF page 27 is not Chapter 3"

def normalize(t):
    t=t.replace("\u200b","").replace("\ufeff","")
    return re.sub(r"\s+"," ",t).strip()
textsA=[normalize(p.get_text(sort=True)) for p in A]
textsB=[normalize(p.get_text(sort=True)) for p in B]
OUR_ANCHORS={"27":"3.4 Abaqus—OpenFAST结构动力一致性验证","28":"2.4 风轮—机舱组件的等效质量模型","29":"设RNA总质量为","30":"2.7 模态特性及阻尼参数","31":"2.7.3 Rayleigh阻尼参数","32":"2.1 研究对象与结构参数","33":"3.6.5 单片柔性叶片模态验证","34":"2.1 研究对象与结构参数","35":"2.2 有限元离散与混凝土本构","36":"2.7.4 小振幅自由衰减分析","37":"3.5.1 随机风场、整机气动弹性计算与控制工况统计","38":"3.10 本章小结"}
STATUS={"27":"方法不同","28":"方法不同","29":"方法不同","30":"部分对应","31":"部分对应","32":"部分对应","33":"部分对应","34":"部分对应","35":"部分对应","36":"部分对应","37":"缺乏同类验证","38":"部分对应"}
NOTES={"27":"何采用8自由度简化动力学；我们采用精细塔架、RNA空间质量及OpenFAST研究体系。不能认定两种模型等效或我们的Simpack历史探索已成为生产联算。","28":"何写出叶片方位角和Euler–Lagrange方程；我们列出RNA等效质量表示，不等于完成何的八自由度整机运动方程。","29":"何展开叶片与机舱系统动能；我们有RNA六乘六参考点质量矩阵，物理量相近但自由度与动力学推导不同。","30":"何逐项给出动能与弹性势能；我们以精细结构模态及阻尼为主，不应冒充已有同一八自由度能量函数。","31":"何给出8DOF的M/C/K；我们有Rayleigh阻尼参数方法，两者不能直接逐矩阵验收为一致。","32":"何给出动力模型参数与钢混塔对象；我们以158m组合研究对象的真实几何和参数为准，不复制何的模型取值。","33":"何这一页含叶片低阶振型及混凝土材料两个主题；此图仅对照我们的历史叶片模态，不等于已完成原生AeroDyn风载耦合。混凝土/预应力另需对照第二章。","34":"何给出具体混凝土节段和配筋表；我们的31段参数需按本项目原始来源、几何台账及模型身份逐项核查，不应照搬何的截面配筋值。","35":"何列出钢塔几何及有限元示意；我们有自己的钢混塔离散和材料模型，但拓扑、网格与振型核验应由各自证据支撑。","36":"何以频率、自由衰减及OpenFAST对照验证8DOF；我们有历史模态与自由衰减分析，但不能把频率接近说成非线性整体模型已完全验证。","37":"何进行两个动力模型在同一湍流风下的位移时程与谱比较；我们有OpenFAST历史响应统计，尚无对应的同状态跨模型时程闭合证据。","38":"何在本页展示位移时程与3.5小结；我们3.10总结风环境、BEM及历史筛选，尚未得到精细混塔与整机同风场的完整独立验证。"}
def word_key(t):
    return re.sub(r"[^\\w]+","",unicodedata.normalize("NFKC",t)).lower()
def locate_ours(anchor):
    k=word_key(anchor)
    hits=[i+1 for i,t in enumerate(textsB) if i>=11 and k in word_key(t)]
    if not hits:raise AssertionError("Missing theme anchor in REAL V8-R6 PDF: "+anchor)
    return hits[0]
def grams(s):
    s=re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+","",s.lower())
    return collections.Counter([s[i:i+3] for i in range(max(0,len(s)-2))])
rows=[grams(s[:5500]) for s in textsA+textsB]
df=collections.Counter()
for row in rows: df.update(row.keys())
N=len(rows)
idf={g:math.log((N+1)/(v+1))+1 for g,v in df.items()}
def vector(row):
    v={g:(1+math.log(c))*idf[g] for g,c in row.items() if df[g]<=max(5,N*.60)}
    norm=math.sqrt(sum(z*z for z in v.values())) or 1
    return {k:val/norm for k,val in v.items()}
vecA=[vector(r) for r in rows[:len(A)]]
vecB=[vector(r) for r in rows[len(A):]]
def sim(a,b):
    if len(a)>len(b):a,b=b,a
    return sum(x*b.get(g,0) for g,x in a.items())
def head(t):
    lines=[normalize(x) for x in t.splitlines() if normalize(x)]
    return lines[:8]
def notable(t):
    matches=[]
    for pattern in [r"第[一二三四五六七八九十\d]+章.{0,40}",r"(?:\d{1,2}\.){1,3}\d{0,2}\s*[^\n。]{1,38}",r"图\s*\d+[-－.]\d+[^\n]{0,45}",r"表\s*\d+[-－.]\d+[^\n]{0,45}"]:
        matches.extend(re.findall(pattern,t[:5000]))
    return list(dict.fromkeys(normalize(s)[:80] for s in matches))[:14]
def focus_tags(text):
    clusters={
      "结构基准": ["塔段","外径","壁厚","塔架模型","有限元","钢混","钢-混","混凝土","截面","塔底"],
      "RNA与气弹": ["叶片","机舱","叶轮","风轮","气动","气弹","转子","桨距","多体"],
      "动力学理论": ["拉格朗日","方程","振型","模态","频率","阻尼","Euler","Lagrange"],
      "风场载荷": ["风速","湍流","风场","风荷载","风剪切","OpenFAST","TurbSim"],
      "响应计算": ["位移","加速度","弯矩","剪力","动力响应","功率谱","极值","疲劳"],
      "可靠度": ["可靠度","失效概率","随机变量","极限状态","概率分布","Monte Carlo"],
      "优化设计": ["优化","灵敏度","参数分析","目标函数","敏感性"],
      "验证": ["验证","对比","误差","吻合","收敛","校核"],
    }
    return [label for label,keys in clusters.items() if sum(text.count(k) for k in keys)>=2]
def snapshot(doc,index,scale=1.4):
    p=doc[index]; r=p.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False,colorspace=fitz.csRGB)
    return Image.frombytes("RGB",[r.width,r.height],r.samples)
def top_matches(i):
    scores=[(sim(vecA[i],v),j) for j,v in enumerate(vecB)]
    scores.sort(reverse=True)
    return [(int(j+1),round(float(s),4)) for s,j in scores[:5]]

INDEX=[]
ATLAS=fitz.open()
PAGE_SIZE=(1170,1025)  # 2 original vector PDF pages, followed by Chinese completion audit
FONT_PATH="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

for i in range(26,38):
    txt=textsA[i]
    top=top_matches(i)
    note=REVIEWS[str(i+1)].copy()
    note["our_page"]=locate_ours(OUR_ANCHORS[str(i+1)])
    note["status"]=STATUS[str(i+1)]
    note["next"]=NOTES[str(i+1)]
    target=int(note["our_page"])-1
    assert 0<=target<len(B)
    entry={
        "reference_pdf_page":i+1,
        "reference_printed_page":None,
        "reference_excerpt":txt[:1150],
        "reference_end":txt[-300:],
        "reference_notable":notable(A[i].get_text(sort=True)),
        "reference_focus":focus_tags(txt),
        "candidate_pages":[{"page":j,"similarity":score} for j,score in top],
        "our_match_page":target+1,
        "our_excerpt":textsB[target][:950],
        "our_notable":notable(B[target].get_text(sort=True)),
        "comparison_status":note["status"],
        "expert_review":note,
        "matching_method":"按V8-R6原生PDF的章节/术语锚点定位；主题相近不作为物理验证通过",
        "match_anchor":OUR_ANCHORS[str(i+1)],
        "physics_verified":False,
        "evidence_rule":"文本相似仅用于定位候选页，不足以证明工程已完成",
        "spread_image":"./spreads/compare-%03d.webp"%(i+1),
    }
    INDEX.append(entry)

    # Clean screenshot of each original PDF page and the highest-similarity page from the current manuscript.
    left=snapshot(A,i,scale=1.5)
    right=snapshot(B,target,scale=1.5)
    thumb_w=1080
    thumb_h=round(max(left.height*thumb_w/left.width,right.height*thumb_w/right.width))
    header=76; gap=24; pad=25; footer=170
    canv=Image.new("RGB",(thumb_w*2+gap+pad*2,thumb_h+header+footer+pad),"#f4f6f9")
    draw=ImageDraw.Draw(canv)
    try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",23)
    except: font=ImageFont.load_default()
    try: cfont=ImageFont.truetype(FONT_PATH,23,index=2)
    except: cfont=font
    draw.text((pad,19),"HE 2024  |  PDF page %03d"%(i+1),font=font,fill="#263850")
    draw.text((pad+thumb_w+gap,19),"OUR V8-R6  |  PDF page %03d  |  TOPIC ONLY"%(target+1),font=font,fill="#136f68")
    for pic,x in [(left,pad),(right,pad+thumb_w+gap)]:
        new_h=round(pic.height*thumb_w/pic.width)
        pic=pic.resize((thumb_w,new_h),Image.Resampling.LANCZOS)
        canv.paste(pic,(x,header))
        draw.rectangle((x,header,x+thumb_w,header+new_h),outline="#b9c6d0",width=2)
    def lines(t,width):
        pieces=[];buf=""
        for char in t:
            if buf and draw.textbbox((0,0),buf+char,font=cfont)[2]>width:
                pieces.append(buf);buf=char
            else:buf+=char
        if buf:pieces.append(buf)
        return pieces
    yy=thumb_h+header+13
    for line in lines("判定："+note["status"]+"｜何的本页："+note["summary"],thumb_w*2+gap)[:2]:
        draw.text((pad,yy),line,font=cfont,fill="#264352");yy+=31
    for line in lines("我们的工作："+note["next"],thumb_w*2+gap)[:3]:
        draw.text((pad,yy),line,font=cfont,fill="#365867");yy+=30
    canv.save(IMG/("compare-%03d.webp"%(i+1)),quality=79,method=5)

    # True PDF spread, with selectable original vector text on both sides.
    page=ATLAS.new_page(width=PAGE_SIZE[0],height=PAGE_SIZE[1])
    page.draw_rect(page.rect,fill=(.97,.98,.99),overlay=False)
    page.insert_text((25,27),"REFERENCE: HE 2024  /  PDF PAGE %d"%(i+1),fontsize=12,color=(.13,.21,.33))
    page.insert_text((600,27),"OUR V8-R6  /  PDF PAGE %d  /  TOPIC-PAIRED"%(target+1),fontsize=12,color=(.07,.42,.38))
    rect1=fitz.Rect(15,40,575,825);rect2=fitz.Rect(595,40,1155,825)
    page.show_pdf_page(rect1,A,i,keep_proportion=True)
    page.show_pdf_page(rect2,B,target,keep_proportion=True)
    page.insert_textbox(fitz.Rect(20,852,1150,904),"判定："+note["status"]+"。何的本页："+note["summary"],fontname="china-s",fontsize=13,lineheight=1.3,color=(.15,.29,.36))
    page.insert_textbox(fitz.Rect(20,915,1150,1020),"我们的工作："+note["next"],fontname="china-s",fontsize=13,lineheight=1.3,color=(.13,.35,.33))
    if (i+1)%15==0:print("Processed",i+1,"of",len(A),flush=True)

with open(OUT/"page_index.json","w",encoding="utf-8") as f:
    json.dump({
      "reference":{"title":"大型混塔式风力机的建模与可靠度分析（何泽瑜，2024）",
                   "file":"../../documents/He_Zeyu_2024_hybrid_tower_thesis.pdf","pages":len(A)},
      "ours":{"title":"10MW混塔论文V8-R6（2026-11-23）",
                   "file":"../../downloads/10MW-thesis-v8r6-evidence-20261123.pdf","pages":len(B)},
      "matching_method":"每页由人工按研究内容与实际证据匹配，自动文本相似度只作为初始定位，不用于完成度判断",
      "pages":INDEX
    },f,ensure_ascii=False,indent=2)
with open(OUT/"page_index.jsonl","w",encoding="utf-8") as f:
    for x in INDEX:f.write(json.dumps(x,ensure_ascii=False)+"\n")
with open(OUT/"toc.json","w",encoding="utf-8") as f:
    json.dump({"he":A.get_toc(),"ours":B.get_toc()},f,ensure_ascii=False,indent=2)
ATLAS.set_metadata({"title":"He 2024 vs Current 10 MW Thesis - Reviewed Page-by-Page Visual Atlas","author":"Thesis Research Studio","subject":"Non-verbatim comparative review"})
ATLAS.save(OUT/"He_chapter3_p27-38_vs_10MW_V8R6.pdf",garbage=4,deflate=True,compression_effort=4)

html_cards=[]
for row in INDEX:
    he_page=row["reference_pdf_page"]; our_page=row["our_match_page"]
    note=row["expert_review"]; pic=row["spread_image"]
    header=f"何论文PDF第{he_page}页 ｜ 我们V8-R6 PDF第{our_page}页"
    html_cards.append(
        f'<article><div class="entry-title"><h2>{html.escape(header)}</h2><span>{html.escape(note["status"])}</span></div>'
        f'<p class="desc">何本页：{html.escape(note["summary"])}</p>'
        f'<a href="{html.escape(pic)}" target="_blank" rel="noopener"><img loading="lazy" src="{html.escape(pic)}" alt="{html.escape(header)}的原页拼图"></a>'
        f'<p class="detail"><b>真实配对页锚点：</b>{html.escape(row["match_anchor"])}</p>'
        f'<p class="detail"><b>差异与验收边界：</b>{html.escape(note["next"])}</p></article>'
    )
markup='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>何泽瑜第三章PDF27—38页与我们的V8-R6原图对照</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f1f4f6;color:#172f3c;font:15px/1.7 "Noto Sans CJK SC","Microsoft YaHei",sans-serif}
header.hero{background:#153441;color:white;padding:24px max(20px,calc((100vw - 1120px)/2))}
h1{font-size:24px;margin:0 0 6px}header p{margin:2px 0 14px;color:#cee0e8}.hero a{color:#d4f6ee}
main{max-width:1130px;margin:0 auto;padding:20px 16px 45px;display:grid;gap:18px}
article,.intro{border:1px solid #d6e1e8;border-radius:9px;background:white;padding:20px}
.entry-title{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}
h2{font-size:18px;margin:0}.entry-title span{color:#725e32;font-weight:600}
.desc{color:#526a7a;font-size:14px;margin:8px 0 12px}
img{width:100%;height:auto;display:block;border:1px solid #d1dfe7}.detail{font-size:14px;margin:10px 0 0}
.links{display:flex;gap:18px;flex-wrap:wrap}.intro p{margin:3px 0}</style></head>
<body><header class="hero"><h1>何泽瑜第三章 × 我们10 MW混塔论文 V8-R6</h1>
<p>何论文原PDF第27—38页，共12页。每页与我们的139页版本按真实研究主题对应，非机械同页对照。</p>
<div class="links"><a href="./He_chapter3_p27-38_vs_10MW_V8R6.pdf">下载12页高清原页对照PDF</a><a href="./page_index.json">逐页依据与原文摘录</a><a href="../">返回原论文工作室</a></div>
</header><main><div class="intro"><p><b>验收范围：</b>这里只核验原页来源、页码及主题差异，不等于8自由度简化模型、精细塔架模型或联算物理结果全部通过。</p>
<p>何文第三章是8-DOF动力学建模；我们已有的历史Simpack结构探索不可冒充已完成的气动—精细结构实时联算。正式同态风载、完整接口平衡及局部材料疲劳仍需原始计算证据。</p></div>''' + ''.join(html_cards) + '</main></body></html>'
(OUT/"index.html").write_text(markup,encoding="utf8")
assert len(INDEX)==12 and [x["reference_pdf_page"] for x in INDEX]==list(range(27,39))
print("HE_CH3_V8R6_REAL_PAGE_PASS",len(INDEX),len(A),len(B),[(q["reference_pdf_page"],q["our_match_page"]) for q in INDEX],flush=True)

