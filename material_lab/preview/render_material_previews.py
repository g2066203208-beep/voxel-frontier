#!/usr/bin/env python3
from pathlib import Path
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/generated-materials")

def srgb_to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)

def linear_to_srgb(x):
    return np.where(x <= 0.0031308, 12.92*x, 1.055*np.power(np.clip(x,0,None),1/2.4)-0.055)

def bilinear(tex,u,v):
    h,w=tex.shape[:2]; u=np.mod(u,1.0); v=np.mod(v,1.0)
    x=u*(w-1); y=(1-v)*(h-1)
    x0=np.floor(x).astype(np.int32); y0=np.floor(y).astype(np.int32)
    x1=(x0+1)%w; y1=(y0+1)%h
    if tex.ndim==3:
        tx=(x-x0)[...,None]; ty=(y-y0)[...,None]
    else:
        tx=(x-x0); ty=(y-y0)
    return (tex[y0,x0]*(1-tx)+tex[y0,x1]*tx)*(1-ty)+(tex[y1,x0]*(1-tx)+tex[y1,x1]*tx)*ty

def norm(v):
    v=np.asarray(v,dtype=np.float32)
    return v/np.maximum(np.linalg.norm(v),1e-6)

def render_sphere(d:Path,name:str,out:Path):
    base_srgb=np.asarray(Image.open(d/f"{name}_baseColor.png").convert("RGB").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    base=srgb_to_linear(base_srgb)
    normal=np.asarray(Image.open(d/f"{name}_normal.png").convert("RGB").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    rough=np.asarray(Image.open(d/f"{name}_roughness.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    ao=np.asarray(Image.open(d/f"{name}_ao.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    S=1000; cx=S*.5; cy=S*.465; R=S*.34
    yy,xx=np.mgrid[0:S,0:S]; sx=(xx-cx)/R; sy=(cy-yy)/R; r2=sx*sx+sy*sy
    sz=np.zeros_like(sx,dtype=np.float32); m=r2<=1; sz[m]=np.sqrt(np.clip(1-r2[m],0,1))
    Ng=np.stack([sx,sy,sz],axis=-1); Ng/=np.maximum(np.linalg.norm(Ng,axis=-1,keepdims=True),1e-6)
    u=(0.5+np.arctan2(Ng[...,2],Ng[...,0])/(2*np.pi))*2.15
    v=(0.5-np.arcsin(np.clip(Ng[...,1],-1,1))/np.pi)*2.15
    bc=bilinear(base,u,v); nt=bilinear(normal,u,v)*2-1; rr=bilinear(rough,u,v); aa=bilinear(ao,u,v)
    T=np.stack([-Ng[...,2],np.zeros_like(sx),Ng[...,0]],axis=-1); T/=np.maximum(np.linalg.norm(T,axis=-1,keepdims=True),1e-6)
    B=np.cross(Ng,T); B/=np.maximum(np.linalg.norm(B,axis=-1,keepdims=True),1e-6)
    N=T*nt[...,0:1]+B*nt[...,1:2]+Ng*np.maximum(nt[...,2:3],0.08); N/=np.maximum(np.linalg.norm(N,axis=-1,keepdims=True),1e-6)
    up=np.clip(N[...,1],-1,1)
    sky=np.array([1.28,1.42,1.62],np.float32); ground=np.array([0.68,0.60,0.52],np.float32)
    env=((up+1)/2)[...,None]*sky+((1-up)/2)[...,None]*ground
    color=bc*env*(0.62+0.38*aa[...,None])
    V=np.array([0,0,1],np.float32)
    lights=[(norm([-0.62,0.62,0.48]),7.5,np.array([1.0,.94,.88],np.float32)),(norm([.58,.18,.80]),3.7,np.array([.78,.88,1.0],np.float32)),(norm([-.08,-.82,.56]),2.0,np.array([1.0,.72,.52],np.float32))]
    for L,intensity,lcol in lights:
        ndl=np.clip((N*L).sum(axis=-1),0,1)
        color += bc*ndl[...,None]*intensity*lcol/math.pi
        H=norm(L+V); ndh=np.clip((N*H).sum(axis=-1),0,1)
        shin=6+(1-rr)*60
        spec=(ndh**shin)*(0.012+0.045*(1-rr))*intensity
        color += spec[...,None]*lcol*0.04
    ndv=np.clip(N[...,2],0,1); color += ((1-ndv)**3)[...,None]*np.array([.04,.055,.075],np.float32)
    c=np.clip(color*1.12,0,None); a,b,c1,d1,e=2.51,.03,2.43,.59,.14; c=(c*(a*c+b))/(c*(c1*c+d1)+e); c=linear_to_srgb(np.clip(c,0,1))
    gy=np.linspace(0,1,S)[:,None,None]; top=np.array([.70,.74,.78],np.float32)[None,None,:]; bot=np.array([.20,.22,.24],np.float32)[None,None,:]
    bg=np.repeat(top*(1-gy)+bot*gy,S,axis=1); shadow=np.exp(-(((xx-cx)/(R*.78))**2+((yy-(cy+R))/(R*.12))**2)*2.5); bg*=1-.34*shadow[...,None]
    edge=np.clip((1-r2)*R*.9,0,1)[...,None]; img=bg*(1-edge)+c*edge
    out_im=Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8),"RGB")
    draw=ImageDraw.Draw(out_im)
    try: f1=ImageFont.truetype("DejaVuSans.ttf",27); f2=ImageFont.truetype("DejaVuSans.ttf",18)
    except: f1=ImageFont.load_default(); f2=f1
    draw.rounded_rectangle((28,26,560,104),radius=18,fill=(18,18,20)); draw.text((48,40),name,fill=(245,245,245),font=f1); draw.text((48,74),"real CI PBR · standardized studio sphere",fill=(190,195,200),font=f2)
    out_im.save(out)

def contact_sheet(d:Path,name:str,out:Path):
    names=[("Base Color","baseColor"),("Normal","normal"),("Roughness","roughness"),("Height","height"),("AO","ao"),("Metallic","metallic")]
    thumb=420; gap=20; label=38
    sheet=Image.new("RGB",(3*thumb+4*gap,2*(thumb+label)+3*gap),(24,24,24)); dr=ImageDraw.Draw(sheet)
    try: font=ImageFont.truetype("DejaVuSans.ttf",21)
    except: font=ImageFont.load_default()
    for i,(lab,suffix) in enumerate(names):
        im=Image.open(d/f"{name}_{suffix}.png").convert("RGB").resize((thumb,thumb),Image.Resampling.LANCZOS); r,c=divmod(i,3); x=gap+c*(thumb+gap); y=gap+r*(thumb+label+gap); sheet.paste(im,(x,y)); dr.text((x,y+thumb+6),lab,fill=(240,240,240),font=font)
    sheet.save(out)

def tile_check(d:Path,name:str,out:Path):
    im=Image.open(d/f"{name}_baseColor.png").convert("RGB").resize((600,600),Image.Resampling.LANCZOS); tile=Image.new("RGB",(1200,1200))
    for y in (0,600):
        for x in (0,600): tile.paste(im,(x,y))
    tile.save(out)

for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    bases=list(d.glob("*_baseColor.png"))
    if not bases: continue
    name=bases[0].name[:-len("_baseColor.png")]
    render_sphere(d,name,d/"preview-sphere.png")
    contact_sheet(d,name,d/"preview-maps.png")
    tile_check(d,name,d/"preview-tile-2x2.png")
    print(name)
