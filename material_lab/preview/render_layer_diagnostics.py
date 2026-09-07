#!/usr/bin/env python3
from pathlib import Path
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("build/generated-materials")

def font(size):
    try: return ImageFont.truetype("DejaVuSans.ttf",size)
    except: return ImageFont.load_default()

def checker(w,h,cell=36):
    yy,xx=np.mgrid[0:h,0:w]
    q=((xx//cell+yy//cell)&1).astype(np.float32)
    a=np.array([.76,.76,.76],np.float32); b=np.array([.42,.42,.42],np.float32)
    return a[None,None,:]*(1-q[...,None])+b[None,None,:]*q[...,None]

def alpha_preview(d:Path,name:str):
    op=d/f"{name}_mask-opacity.png"
    if not op.is_file(): return
    base=np.asarray(Image.open(d/f"{name}_baseColor.png").convert("RGB"),dtype=np.float32)/255
    alpha=np.asarray(Image.open(op).convert("L"),dtype=np.float32)/255
    bg=checker(base.shape[1],base.shape[0])
    out=bg*(1-alpha[...,None])+base*alpha[...,None]
    Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8),"RGB").save(d/"preview-alpha-cutout.png")

def masks_preview(d:Path,name:str):
    files=sorted(d.glob(f"{name}_mask-*.png"))
    if not files:return
    thumb=320; gap=18; label=34; cols=min(3,len(files)); rows=math.ceil(len(files)/cols)
    sheet=Image.new("RGB",(cols*thumb+(cols+1)*gap,rows*(thumb+label)+(rows+1)*gap),(24,24,24)); draw=ImageDraw.Draw(sheet); f=font(18)
    for i,p in enumerate(files):
        im=Image.open(p).convert("RGB").resize((thumb,thumb),Image.Resampling.LANCZOS)
        r,c=divmod(i,cols); x=gap+c*(thumb+gap); y=gap+r*(thumb+label+gap)
        sheet.paste(im,(x,y)); draw.text((x,y+thumb+6),p.stem.split("_mask-",1)[-1],fill=(242,242,242),font=f)
    sheet.save(d/"preview-layer-masks.png")

for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    bases=list(d.glob("*_baseColor.png"))
    if not bases: continue
    name=bases[0].name[:-len("_baseColor.png")]
    alpha_preview(d,name); masks_preview(d,name)
    print(name)
