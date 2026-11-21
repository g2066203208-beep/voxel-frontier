#!/usr/bin/env python3
# Full page-by-page visual comparison of HE2024 thesis and current manuscript.
# Real PDF screenshots + full-fidelity 2-page PDF spreads; no screenshot fabrication.
import os, sys, re, json, math, collections, html
from pathlib import Path
import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
HE=ROOT/"public/thesis-studio/documents/He_Zeyu_2024_hybrid_tower_thesis.pdf"
OWN=ROOT/"public/thesis-studio/downloads/10MW-hybrid-tower-academic-revision-20261121.pdf"
OUT=ROOT/"public/thesis-studio/he-thesis-comparison"
IMG=OUT/"spreads"
OUT.mkdir(parents=True,exist_ok=True)
IMG.mkdir(exist_ok=True)

A=fitz.open(HE); B=fitz.open(OWN)
def normalize(t):
    t=t.replace("\u200b","").replace("\ufeff","")
    return re.sub(r"\s+"," ",t).strip()
textsA=[normalize(p.get_text(sort=True)) for p in A]
textsB=[normalize(p.get_text(sort=True)) for p in B]
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
PAGE_SIZE=(1170,852)  # landscape spread with full PDF vector pages
for i,txt in enumerate(textsA):
    top=top_matches(i)
    target=top[0][0]-1
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
        "comparison_status":"待逐项证据复核",
        "evidence_rule":"文本相似仅用于定位候选页，不足以证明工程已完成",
        "spread_image":"./spreads/compare-%03d.webp"%(i+1),
    }
    INDEX.append(entry)

    # Clean screenshot of each original PDF page and the highest-similarity page from the current manuscript.
    left=snapshot(A,i,scale=1.5)
    right=snapshot(B,target,scale=1.5)
    thumb_w=820
    thumb_h=round(max(left.height*thumb_w/left.width,right.height*thumb_w/right.width))
    header=76; gap=24; pad=25; footer=55
    canv=Image.new("RGB",(thumb_w*2+gap+pad*2,thumb_h+header+footer+pad),"#f4f6f9")
    draw=ImageDraw.Draw(canv)
    try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",23)
    except: font=ImageFont.load_default()
    draw.text((pad,19),"HE 2024  |  PDF page %03d"%(i+1),font=font,fill="#263850")
    draw.text((pad+thumb_w+gap,19),"OUR THESIS  |  PDF page %03d  |  match %.2f"%(target+1,top[0][1]),font=font,fill="#136f68")
    for pic,x in [(left,pad),(right,pad+thumb_w+gap)]:
        new_h=round(pic.height*thumb_w/pic.width)
        pic=pic.resize((thumb_w,new_h),Image.Resampling.LANCZOS)
        canv.paste(pic,(x,header))
        draw.rectangle((x,header,x+thumb_w,header+new_h),outline="#b9c6d0",width=2)
    draw.text((pad,thumb_h+header+16),"NOTE: Page pair is an automated content match, not a completion verdict.",font=font,fill="#566579")
    canv.save(IMG/("compare-%03d.webp"%(i+1)),quality=79,method=5)

    # True PDF spread, with selectable original vector text on both sides.
    page=ATLAS.new_page(width=PAGE_SIZE[0],height=PAGE_SIZE[1])
    page.draw_rect(page.rect,fill=(.97,.98,.99),overlay=False)
    page.insert_text((25,27),"REFERENCE: HE 2024  /  PDF PAGE %d"%(i+1),fontsize=12,color=(.13,.21,.33))
    page.insert_text((600,27),"CURRENT DRAFT  /  PDF PAGE %d  /  similarity %.3f"%(target+1,top[0][1]),fontsize=12,color=(.07,.42,.38))
    rect1=fitz.Rect(15,40,575,825);rect2=fitz.Rect(595,40,1155,825)
    page.show_pdf_page(rect1,A,i,keep_proportion=True)
    page.show_pdf_page(rect2,B,target,keep_proportion=True)
    if (i+1)%15==0:print("Processed",i+1,"of",len(A),flush=True)

with open(OUT/"page_index.json","w",encoding="utf-8") as f:
    json.dump({
      "reference":{"title":"大型混塔式风力机的建模与可靠度分析（何泽瑜，2024）",
                   "file":"../documents/He_Zeyu_2024_hybrid_tower_thesis.pdf","pages":len(A)},
      "ours":{"title":"10MW混合塔论文：第三章精修版（2026-11-21）",
                   "file":"../downloads/10MW-hybrid-tower-academic-revision-20261121.pdf","pages":len(B)},
      "matching_method":"Chinese character 3-gram TF-IDF; use candidate results only as a navigation aid, not a completed-work decision",
      "pages":INDEX
    },f,ensure_ascii=False,indent=2)
with open(OUT/"page_index.jsonl","w",encoding="utf-8") as f:
    for x in INDEX:f.write(json.dumps(x,ensure_ascii=False)+"\n")
with open(OUT/"toc.json","w",encoding="utf-8") as f:
    json.dump({"he":A.get_toc(),"ours":B.get_toc()},f,ensure_ascii=False,indent=2)
ATLAS.set_metadata({"title":"He 2024 vs Current 10 MW Thesis - Every PDF Page Visual Pair","author":"Thesis Research Studio","subject":"Non-verbatim comparative review"})
ATLAS.save(OUT/"He2024_vs_Current20261121_逐页双页拼图.pdf",garbage=4,deflate=True,compression_effort=4)
print("DONE:",len(A),"He pages;",len(B),"ours pages; atlas MB",round((OUT/"He2024_vs_Current20261121_逐页双页拼图.pdf").stat().st_size/1e6,2),flush=True)
