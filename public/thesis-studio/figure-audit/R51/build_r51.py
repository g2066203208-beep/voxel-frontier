"""R51 source-locked original figure comparisons; no data alteration."""
import hashlib,io,json,urllib.request
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import fitz
ROOT=Path("public/thesis-studio")
OUT=ROOT/"figure-audit/R51"
sha=lambda b:hashlib.sha256(b).hexdigest()
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=45) as f:return f.read()
def read_image(raw):
    im=Image.open(io.BytesIO(raw));im.verify()
    return Image.open(io.BytesIO(raw)).convert("RGB")
def save_png(im,path):
    im.save(path,dpi=(300,300))
def fit(im,w,h):
    # Preserve source aspect ratio. No rescaling of axes or alteration to traces.
    scale=min(w/im.width,h/im.height)
    return im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
def font(size):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",size)
def pair(ours,ref,stem,left,right,note):
    w=1400
    ours=fit(ours.copy(),w-90,1700);ref=fit(ref.copy(),w-90,1700)
    h=max(ours.height,ref.height)+155
    canvas=Image.new("RGB",(2*w,h+80),"white");d=ImageDraw.Draw(canvas)
    d.line((w,35,w,h),fill=(195,195,195),width=2)
    d.text((45,30),left,font=font(27),fill="black")
    d.text((w+45,30),right,font=font(27),fill="black")
    canvas.paste(ours,((w-ours.width)//2,100+(h-155-ours.height)//2))
    canvas.paste(ref,(w+(w-ref.width)//2,100+(h-155-ref.height)//2))
    d.text((45,h+5),note,font=font(23),fill="black")
    p=OUT/(stem+"-pair.png");save_png(canvas,p);return p
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fig8url="https://mdpi-res.com/energies/energies-13-03833/article_deploy/html/images/energies-13-03833-g008.png"
    shahiurl="https://www.jackwbaker.com/Publications/Shahi_Baker_%282014%29_Pulse_Classification%2C_BSSA.pdf"
    # Each reference download verified and saved as original bytes before generating composites.
    records=[]
    jobs=[
      ("eq-r10-010","seismic-archive/journal-figures/V7_backup_01_acceleration.png","acceleration","Energies (2020), Fig. 8(a,b)","Acceleration time histories; different ground motions and scales.","SAME_QUANTITY"),
      ("eq-r10-012","seismic-archive/journal-figures/V7_backup_02_PSD.png","power-spectrum","Energies (2020), Fig. 8(d)","Frequency PSD vs period power spectrum; methods and normalization differ.","METHOD_ONLY"),
      ("eq-r10-016","seismic-archive/journal-figures/V7_backup_03_response_spectra.png","response-spectrum","Energies (2020), Fig. 8(c)","Acceleration response spectra; different components, target and units.","SAME_QUANTITY"),
      ("eq-r10-024","seismic-archive/second-suite/qualification/05_pulse_candidate_velocity_screening.png","pulse-velocity","Shahi & Baker (2014), Fig. 1","Velocity time histories; candidate traces do not establish pulse classification.","SAME_QUANTITY")
    ]
    refs={}
    for fid,asset,stem,label,note,kind in jobs:
        row=dict(id=fid,asset=asset,reference=label,scope=note,kind=kind,status="HOLD")
        try:
            if stem=="pulse-velocity":
                if "shahi" not in refs:
                    raw=fetch(shahiurl);(OUT/"shahi-baker-2014-original.pdf").write_bytes(raw)
                    doc=fitz.open(stream=raw,filetype="pdf")
                    page=doc[1];assert "Different types of ground motions" in page.get_text()
                    pix=page.get_pixmap(matrix=fitz.Matrix(2.7,2.7),alpha=False)
                    im=Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                    save_png(im,OUT/"shahi-baker-page-2.png")
                    refs["shahi"]=(raw,im)
                raw,im=refs["shahi"]
                # Reference figure and original caption on printed p2457. Preserve full page separately.
                w,h=im.size;reference=im.crop((int(w*.08),int(h*.067),int(w*.93),int(h*.50)))
                row.update(source_url=shahiurl,doi="10.1785/0120130191",pdf_page=2,original_file="shahi-baker-2014-original.pdf")
            else:
                if "fig8" not in refs:
                    raw=fetch(fig8url);im=read_image(raw);assert im.width>=1000 and im.height>=700
                    (OUT/"energies-13-03833-fig8-original.png").write_bytes(raw)
                    refs["fig8"]=(raw,im)
                raw,im=refs["fig8"];w,h=im.size
                # Fig. 8 four panels: upper acceleration, lower left response, lower right power.
                boxes={"acceleration":(0,0,w,int(h*.50)),"response-spectrum":(0,int(h*.50),int(w*.50),h),"power-spectrum":(int(w*.50),int(h*.50),w,h)}
                reference=im.crop(boxes[stem]);
                if stem=="acceleration":
                    # Stack source panels (a,b) without changing their axes.
                    top=reference;mid=top.width//2
                    a=top.crop((0,0,mid,top.height));b=top.crop((mid,0,top.width,top.height))
                    reference=Image.new("RGB",(max(a.width,b.width),a.height+b.height+14),"white");reference.paste(a,(0,0));reference.paste(b,(0,a.height+14))
                row.update(source_url=fig8url,doi="10.3390/en13153833",original_file="energies-13-03833-fig8-original.png")
            op=ROOT/asset;oursraw=op.read_bytes();ours=read_image(oursraw)
            assert ours.width>=500 and ours.height>=200
            crop=OUT/(stem+"-reference.png");save_png(reference,crop)
            p=pair(ours,reference,stem,"This study | archived data",label,note)
            row.update(status="ARCHIVED",our_sha256=sha(oursraw),original_sha256=sha(raw),crop_sha256=sha(crop.read_bytes()),pair_sha256=sha(p.read_bytes()),pair=str(p.relative_to(ROOT)),pair_pixels=list(read_image(p.read_bytes()).size))
        except Exception as e:row["error"]=str(e)
        records.append(row)
        print(json.dumps(row),flush=True)
    (OUT/"receipt.json").write_text(json.dumps(records,indent=2)+"\n")
    if not any(x["status"]=="ARCHIVED" for x in records):raise RuntimeError("no pair succeeded")
if __name__=="__main__":main()
