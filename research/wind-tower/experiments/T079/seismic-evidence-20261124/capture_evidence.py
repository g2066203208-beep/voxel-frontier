import asyncio, hashlib, io, json, pathlib, re, time
from datetime import datetime, timezone
import httpx, pymupdf
from PIL import Image
from playwright.async_api import async_playwright

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"original"
OUT.mkdir(exist_ok=True)
S=json.loads((ROOT/"sources.json").read_text())
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
def sha(b): return hashlib.sha256(b).hexdigest()
def timestamp(): return datetime.now(timezone.utc).isoformat()
def valid_image(b):
    im=Image.open(io.BytesIO(b)); im.verify()
    im=Image.open(io.BytesIO(b))
    if min(im.size)<60: raise ValueError("image too small")
    return list(im.size),im.format
async def capture(browser,client,sem,s):
    async with sem:
        r=dict(s,checked_utc=timestamp(),status="HOLD")
        try:
            if s["kind"] in ("image","pdf"):
                resp=await client.get(s["url"],headers={"User-Agent":UA,"Referer":"https://gf.cabr-fire.com/" if s["kind"]=="image" else "https://pubs.cstam.org.cn/"})
                resp.raise_for_status(); b=resp.content
                r.update(http_status=resp.status_code,final_url=str(resp.url),source_bytes=len(b),source_sha256=sha(b),content_type=resp.headers.get("content-type",""))
                if s["kind"]=="image":
                    dim,fmt=valid_image(b)
                    if fmt not in ("JPEG","PNG"):raise ValueError("unexpected source image encoding")
                    fn=s["id"]+(".jpg" if fmt=="JPEG" else ".png")
                    r["scope"]="unmodified original source table image; visual content requires review"
                    r["pixel_size"]=dim
                else:
                    if not b.startswith(b"%PDF"):raise ValueError("not a PDF")
                    with pymupdf.open(stream=b,filetype="pdf") as doc:
                        candidates=[]
                        for p in doc:
                            for phrase in ("Information of the selected ground motions","地震动信息"):
                                for rect in p.search_for(phrase):
                                    candidates.append((p.number,rect))
                        if not candidates:raise ValueError("table caption absent")
                        # Locate the actual numerical table with a distinctive identifier.
                        good=[(i,rect) for i,rect in candidates if "YPT" in doc[i].get_text() and "ILA" in doc[i].get_text()]
                        if not good:raise ValueError("caption without candidate records")
                        i,rect=min(good,key=lambda x:x[1].y0)
                        p=doc[i]; words=p.get_text("words")
                        # Crop factual table only, using table row text coordinates.
                        hits=[w for w in words if any(t in w[4].upper() for t in ("BLC360","FRN135","YPT-150","ILA004","G01230"))]
                        if len(hits)<2:raise ValueError("table row identifiers missing")
                        y0=max(0,rect.y0-8);y1=min(p.rect.height,max(w[3] for w in hits)+13)
                        if y1-y0<100:raise ValueError("table crop too short")
                        clip=pymupdf.Rect(0,y0,p.rect.width,y1)
                        b=p.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=clip,alpha=False).tobytes("png")
                        r.update(pdf_page_1based=i+1,clip_points=list(clip),pixel_size=valid_image(b)[0])
                        fn=s["id"]+".png"
            else:
                page=await browser.new_page(viewport={"width":1440,"height":1050},device_scale_factor=1.5,locale="zh-CN")
                try:
                    resp=await page.goto(s["url"],wait_until="domcontentloaded",timeout=32000)
                    r.update(http_status=resp.status if resp else None,final_url=page.url)
                    if not resp or resp.status>=400:raise ValueError("source HTTP unavailable")
                    # Capture only the short factual heading/registration or targeted clause,
                    # never the entire proprietary article or paywalled standard.
                    loc=page.get_by_text(s["needle"],exact=False)
                    await loc.first.wait_for(state="visible",timeout=10000)
                    choices=[]
                    for k in range(min(await loc.count(),30)):
                        x=loc.nth(k)
                        if not await x.is_visible():continue
                        box=await x.bounding_box()
                        if box and box["width"]>70 and 10<=box["height"]<=550:
                            choices.append((box["height"],x))
                    if not choices:raise ValueError("no verified visible bounded source element")
                    _,x=min(choices,key=lambda a:a[0])
                    text=await x.inner_text()
                    if s["needle"].casefold() not in text.casefold():raise ValueError("identity text missing")
                    # Limit screenshot to a brief source excerpt/heading, not a full work.
                    if len(text)>900:raise ValueError("excerpt too broad")
                    await x.scroll_into_view_if_needed()
                    box=await x.bounding_box()
                    if not box:raise ValueError("source element bounds missing")
                    b=await x.screenshot(timeout=10000,animations="disabled")
                    # Small headings are allowed.
                    im=Image.open(io.BytesIO(b)); im.verify()
                    im=Image.open(io.BytesIO(b))
                    r.update(pixel_size=list(im.size),matched_needle=s["needle"],page_title=await page.title(),rendered_excerpt_text_sha256=sha(text.encode()))
                    fn=s["id"]+".png"
                finally:
                    await page.close()
            (OUT/fn).write_bytes(b)
            r.update(status="CAPTURED",file="original/"+fn,bytes=len(b),sha256=sha(b))
        except Exception as e:
            r["error"]=str(e)[:450]
        print(json.dumps(r,ensure_ascii=False),flush=True)
        return r
async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path="/usr/bin/google-chrome",headless=True,args=["--no-sandbox"])
        async with httpx.AsyncClient(follow_redirects=True,timeout=35) as c:
            rows=await asyncio.gather(*(capture(browser,c,asyncio.Semaphore(5),s) for s in [])) if False else await asyncio.gather(*(capture(browser,c,sem,s) for s in S))
        await browser.close()
    (ROOT/"capture-receipt.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n")
    md=["# 地震选波原始证据图册（2026-11-24）","","仅显示实际获取并通过格式及来源身份检查的原图；失败保留原始错误。登记页不是规范全文，截图不是地震波原件。完整版权文件不重新分发。","","|证据|状态|范围|","|---|---|---|"]
    for r in rows:
        md.append(f"|{r['id']}|{r['status']}|{r['scope']}|")
    for r in rows:
        md += ["",f"## {r['id']}","","来源："+r["url"],"范围："+r["scope"]]
        if r["status"]=="CAPTURED":
            md += ["","!["+r["id"]+"]("+r["file"]+")","","SHA-256: "+r["sha256"]]
        else: md += ["","**HOLD：** "+r["error"]]
    (ROOT/"EVIDENCE_ATLAS.md").write_text("\n".join(md)+"\n")
    print("CAPTURE_TOTAL",sum(r["status"]=="CAPTURED" for r in rows),len(rows))
if __name__=="__main__":
    sem=asyncio.Semaphore(5)
    asyncio.run(main())
