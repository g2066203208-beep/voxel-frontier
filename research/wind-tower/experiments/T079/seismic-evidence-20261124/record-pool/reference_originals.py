"""Archive original source figures/short bibliographic excerpts, not full proprietary papers."""
import pathlib,hashlib,json,datetime,io
import requests
from PIL import Image
import pymupdf as fitz
ROOT=pathlib.Path(__file__).resolve().parent/"replacement_references";ROOT.mkdir(exist_ok=True)
S=[
("GB_515_SPECTRUM","image","https://gf.cabr-fire.com/article-15665.htm","图5.1.5"),
("AKKAR_BOMMER_2006","pdf","https://web.bogazici.edu.tr/sinan.akkar/download/publications/11_Akkar_Bommer_EESD_35_9.pdf","Influence of long-period"),
("JAYARAM_LIN_BAKER_2011","pdf","https://www.jackwbaker.com/Publications/Jayaram_et_al_%282011%29_GM_selection_w_sigma%2C_EQ_Spectra.pdf","A Computationally Efficient"),
("BAKER_LEE_2018","pdf","https://www.jackwbaker.com/Publications/Baker_Lee_%282018%29_GM_Selection%2C_JEE.pdf","An Improved Algorithm"),
]
def sha(b):return hashlib.sha256(b).hexdigest()
rows=[]
for id,kind,url,phrase in S:
    q={"id":id,"url":url,"status":"HOLD","time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        r=requests.get(url,timeout=(8,35),headers={"User-Agent":"Mozilla/5.0"});r.raise_for_status();b=r.content;q.update(http=r.status_code,source_sha256=sha(b),source_bytes=len(b))
        if kind=="pdf":
            assert b.startswith(b"%PDF")
            doc=fitz.open(stream=b,filetype="pdf");page=doc[0]
            hit=page.search_for(phrase)
            if not hit:raise ValueError("bibliographic phrase not found")
            y=min(x.y0 for x in hit)
            # only title lines and author attribution, not the article body.
            lines=[]
            for block in page.get_text("dict")["blocks"]:
                for l in block.get("lines",[]):
                    rr=fitz.Rect(l["bbox"])
                    if rr.y0>=y-3 and rr.y0<y+115:
                        st="".join(s["text"] for s in l["spans"])
                        if any(k in st.lower() for k in ("summary","abstract","dynamic structural analysis","this paper")):continue
                        lines.append((rr,st))
            # take title and author heading only, cut above abstract
            end=y+55
            for rr,st in lines:
                if any(k.lower() in st.lower() for k in ("Akkar","Bommer","Jayaram","Baker","Lin","Lee")):end=max(end,rr.y1+3)
            end=min(end,y+105)
            clip=fitz.Rect(0,y-5,page.rect.width,end)
            b=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=clip,alpha=False).tobytes("png")
            q.update(page=1,clip=list(clip),scope="original bibliographic title/author excerpt, not full text")
        else:
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            soup=BeautifulSoup(r.text,"html.parser")
            text=soup.find(string=lambda s:s and "图5.1.5" in s and "地震影响系数曲线" in s)
            if not text:raise ValueError("caption absent")
            el=text.parent
            img=el.find_previous("img")
            if img is None:raise ValueError("source figure not found")
            link=urljoin(r.url,img.get("src",""))
            ri=requests.get(link,timeout=(8,30),headers={"User-Agent":"Mozilla/5.0","Referer":r.url});ri.raise_for_status();b=ri.content
            im=Image.open(io.BytesIO(b));im.verify();im=Image.open(io.BytesIO(b))
            assert min(im.size)>60
            q.update(image_url=link,scope="actual source figure adjacent to identified caption, visual review required")
        im=Image.open(io.BytesIO(b));fmt=im.format;im.verify()
        name=id+(".jpg" if fmt=="JPEG" else ".png");(ROOT/name).write_bytes(b)
        q.update(status="CAPTURED",file=name,sha256=sha(b),bytes=len(b))
    except Exception as e:q["error"]=str(e)[:300]
    rows.append(q);print(json.dumps(q,ensure_ascii=False),flush=True)
(ROOT/"receipt.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
