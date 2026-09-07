#!/usr/bin/env python3
from pathlib import Path
import json, math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("build/generated-materials")
CX=500.0; CY=465.0; R=325.0

def mask_path(d,name,key): return d/f"{name}_mask-{key}.png"
def load_mask(d,name,key):
    p=mask_path(d,name,key)
    if not p.is_file(): return None
    return np.asarray(Image.open(p).convert("L"),dtype=np.float32)/255.0

def uv_from_normal(x,y,z):
    u=(0.5+math.atan2(z,x)/(2*math.pi))*2.10
    v=(0.5-math.asin(max(-1,min(1,y)))/math.pi)*2.10
    return u%1.0,v%1.0

def sample(tex,u,v):
    if tex is None:return 0.0
    h,w=tex.shape; xi=int((u%1.0)*(w-1)); yi=int((1-(v%1.0))*(h-1)); return float(tex[max(0,min(h-1,yi)),max(0,min(w-1,xi))])

def points(seed,count):
    rng=random.Random(seed)
    out=[]
    for _ in range(count):
        z=rng.uniform(.06,1.0)
        a=rng.random()*math.tau
        r=math.sqrt(max(0,1-z*z)); x=r*math.cos(a); y=r*math.sin(a)
        out.append((z,x,y,rng.random(),rng.random(),rng.random()))
    out.sort(key=lambda p:p[0])
    return out

def n2(x,y,bx=0.0,by=-.25):
    dx=x+bx;dy=-y+by;l=math.hypot(dx,dy)
    if l<1e-5:return 0.0,-1.0
    return dx/l,dy/l

def render_grass(d,name,base):
    den=load_mask(d,name,"bladeDensity"); lng=load_mask(d,name,"bladeLength"); bend=load_mask(d,name,"bladeBend")
    im=base.convert("RGBA"); ov=Image.new("RGBA",im.size,(0,0,0,0)); dr=ImageDraw.Draw(ov,"RGBA")
    for z,x,y,r0,r1,r2 in points(73117,5200):
        u,v=uv_from_normal(x,y,z); q=sample(den,u,v)
        if r0>q*.52:continue
        L=(10+38*sample(lng,u,v))*(.58+.42*(1-z*.35)); b=sample(bend,u,v)
        dx,dy=n2(x,y,.18*b,-.36-.18*b); bx=CX+R*x;by=CY-R*y
        tipx=bx+dx*L+(r1-.5)*7;tipy=by+dy*L
        dark=(42,78,14,int(160+70*z)); mid=(104,154,28,int(195+55*z)); light=(184,205,67,int(210+40*z))
        col=dark if r2<.25 else (mid if r2<.78 else light)
        w=2 if z<.55 else 3
        dr.line((bx,by,tipx,tipy),fill=col,width=w)
        dr.line((tipx,tipy,tipx+dx*3,tipy+dy*3),fill=(210,218,90,col[3]),width=1)
    return Image.alpha_composite(im,ov).convert("RGB")

def render_moss(d,name,base):
    den=load_mask(d,name,"mossDensity"); lng=load_mask(d,name,"mossHeight"); var=load_mask(d,name,"tuftVariation")
    im=base.convert("RGBA"); ov=Image.new("RGBA",im.size,(0,0,0,0)); dr=ImageDraw.Draw(ov,"RGBA")
    for z,x,y,r0,r1,r2 in points(55109,8200):
        u,v=uv_from_normal(x,y,z);q=sample(den,u,v)
        if r0>q*.48:continue
        L=2.5+10*sample(lng,u,v);dx,dy=n2(x,y,(r1-.5)*.22,-.10);bx=CX+R*x;by=CY-R*y;tx=bx+dx*L;ty=by+dy*L
        vv=sample(var,u,v);col=(91+int(85*vv),126+int(55*vv),20+int(35*vv),150+int(80*z))
        dr.line((bx,by,tx,ty),fill=col,width=2 if z>.45 else 1)
        if r2>.72:dr.ellipse((tx-1.7,ty-1.7,tx+1.7,ty+1.7),fill=(176,194,54,col[3]))
    return Image.alpha_composite(im,ov).convert("RGB")

def render_fur(d,name,base):
    den=load_mask(d,name,"strandDensity");lng=load_mask(d,name,"strandLength");bend=load_mask(d,name,"strandBend");var=load_mask(d,name,"strandVariation")
    im=base.convert("RGBA"); under=Image.new("RGBA",im.size,(0,0,0,0)); dr=ImageDraw.Draw(under,"RGBA")
    for z,x,y,r0,r1,r2 in points(91007,12000):
        u,v=uv_from_normal(x,y,z);q=sample(den,u,v)
        if r0>q*.40:continue
        L=(5+26*sample(lng,u,v))*(.72+.28*(1-z));b=sample(bend,u,v);dx,dy=n2(x,y,.20*b,-.10-.12*b);bx=CX+R*x;by=CY-R*y
        tx=bx+dx*L+(r1-.5)*3;ty=by+dy*L
        vv=sample(var,u,v);c0=np.array([72,38,18]);c1=np.array([226,170,89]);c=(c0*(1-vv)+c1*vv).astype(int);alpha=int(115+125*z)
        dr.line((bx,by,tx,ty),fill=(int(c[0]),int(c[1]),int(c[2]),alpha),width=1 if z<.7 else 2)
    soft=under.filter(ImageFilter.GaussianBlur(.45));return Image.alpha_composite(Image.alpha_composite(im,soft),under).convert("RGB")

def render_fire(d,name,base):
    den=load_mask(d,name,"flameDensity");lng=load_mask(d,name,"flameHeight");heat=load_mask(d,name,"heatDistortion");smoke=load_mask(d,name,"smoke");sparks=load_mask(d,name,"sparks")
    im=base.convert("RGBA")
    glow=Image.new("RGBA",im.size,(0,0,0,0)); core=Image.new("RGBA",im.size,(0,0,0,0)); dg=ImageDraw.Draw(glow,"RGBA");dc=ImageDraw.Draw(core,"RGBA")
    for z,x,y,r0,r1,r2 in points(44021,6200):
        u,v=uv_from_normal(x,y,z);f=sample(den,u,v)
        if r0>f*.42:continue
        L=10+66*sample(lng,u,v)*(0.68+0.32*r2);h=sample(heat,u,v);dx,dy=n2(x,y,.42*h,-.72);bx=CX+R*x;by=CY-R*y;tx=bx+dx*L+(r1-.5)*12;ty=by+dy*L
        a=int(110+120*z);dg.line((bx,by,tx,ty),fill=(255,72,6,a),width=10 if z>.55 else 7);dc.line((bx,by,tx,ty),fill=(255,143,14,min(255,a+25)),width=5 if z>.55 else 3);dc.line((bx+(tx-bx)*.35,by+(ty-by)*.35,tx,ty),fill=(255,236,95,min(255,a+35)),width=2)
        if sample(sparks,u,v)>.64 and r2>.55:dc.ellipse((tx-2,ty-2,tx+2,ty+2),fill=(255,223,88,230))
        if sample(smoke,u,v)>.48 and r1>.72:dg.ellipse((tx-8,ty-18,tx+8,ty-2),fill=(65,57,52,70))
    g=glow.filter(ImageFilter.GaussianBlur(11));g2=glow.filter(ImageFilter.GaussianBlur(3));return Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(im,g),g2),core).convert("RGB")

def process(d):
    manifest=json.loads((d/"manifest.json").read_text());preset=manifest.get("preset");name=manifest.get("material")
    if preset not in {"vf3DGrass","vf3DMoss","vf3DFur","vf3DFire"}:return
    p=d/"preview-sphere.png";base=Image.open(p).convert("RGB")
    if preset=="vf3DGrass":out=render_grass(d,name,base)
    elif preset=="vf3DMoss":out=render_moss(d,name,base)
    elif preset=="vf3DFur":out=render_fur(d,name,base)
    else:out=render_fire(d,name,base)
    out.save(p);out.save(d/"preview-3d-surface.png")

for d in sorted(x for x in ROOT.iterdir() if x.is_dir()):process(d)
