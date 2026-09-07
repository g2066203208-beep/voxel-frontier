#!/usr/bin/env python3
from pathlib import Path
import json, math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("build/generated-materials")
CX=500.0; CY=465.0; R=325.0

def load_mask(d,name,key):
    p=d/f"{name}_mask-{key}.png"
    if not p.is_file(): return None
    return np.asarray(Image.open(p).convert("L"),dtype=np.float32)/255.0

def uv_from_normal(x,y,z):
    return ((0.5+math.atan2(z,x)/(2*math.pi))*2.10)%1.0,((0.5-math.asin(max(-1,min(1,y)))/math.pi)*2.10)%1.0

def sample(tex,u,v):
    if tex is None:return 0.0
    h,w=tex.shape;xi=int((u%1.0)*(w-1));yi=int((1-(v%1.0))*(h-1));return float(tex[max(0,min(h-1,yi)),max(0,min(w-1,xi))])

def points(seed,count):
    rng=random.Random(seed);out=[]
    for _ in range(count):
        z=rng.uniform(.04,1.0);a=rng.random()*math.tau;r=math.sqrt(max(0,1-z*z));x=r*math.cos(a);y=r*math.sin(a)
        out.append((z,x,y,rng.random(),rng.random(),rng.random()))
    out.sort(key=lambda p:p[0]);return out

def unit(dx,dy):
    l=math.hypot(dx,dy)
    return (0,-1) if l<1e-6 else (dx/l,dy/l)

def relabel(im,name,subtitle):
    out=im.convert("RGB");dr=ImageDraw.Draw(out)
    try:f1=ImageFont.truetype("DejaVuSans.ttf",27);f2=ImageFont.truetype("DejaVuSans.ttf",18)
    except:f1=ImageFont.load_default();f2=f1
    dr.rounded_rectangle((28,26,900,104),radius=18,fill=(18,18,20));dr.text((48,40),name,fill=(245,245,245),font=f1);dr.text((48,74),subtitle,fill=(190,195,200),font=f2)
    return out

def render_grass(d,name,base):
    den,lng,bend=(load_mask(d,name,k) for k in ("bladeDensity","bladeLength","bladeBend"))
    im=base.convert("RGBA");ov=Image.new("RGBA",im.size,(0,0,0,0));dr=ImageDraw.Draw(ov,"RGBA")
    for z,x,y,r0,r1,r2 in points(73117,3600):
        u,v=uv_from_normal(x,y,z);q=sample(den,u,v)
        if r0>q*.34:continue
        L=(16+48*sample(lng,u,v))*(.78+.22*(1-z));b=sample(bend,u,v);bx=CX+R*x;by=CY-R*y
        dx,dy=unit(x*.35+.28*b+(r1-.5)*.12,-.92-y*.14-.12*b)
        tipx=bx+dx*L;tipy=by+dy*L;side=unit(-dy,dx);w=2.4+3.2*(.35+.65*q)*(1-.28*z)
        midx=bx+dx*L*.56+side[0]*(r2-.5)*5;midy=by+dy*L*.56+side[1]*(r2-.5)*5
        poly=[(bx-side[0]*w,by-side[1]*w),(midx-side[0]*w*.62,midy-side[1]*w*.62),(tipx,tipy),(midx+side[0]*w*.62,midy+side[1]*w*.62),(bx+side[0]*w,by+side[1]*w)]
        if r2<.24:col=(45,86,21,190)
        elif r2<.78:col=(92,143,31,215)
        else:col=(154,181,54,225)
        dr.polygon(poly,fill=col);dr.line((bx,by,midx,midy,tipx,tipy),fill=(184,198,72,145),width=1)
    return relabel(Image.alpha_composite(im,ov),name,"procedural 3D grass blades · clump density · wind bend")

def render_moss(d,name,base):
    den,lng,var=(load_mask(d,name,k) for k in ("mossDensity","mossHeight","tuftVariation"))
    im=base.convert("RGBA");ov=Image.new("RGBA",im.size,(0,0,0,0));dr=ImageDraw.Draw(ov,"RGBA")
    for z,x,y,r0,r1,r2 in points(55109,9000):
        u,v=uv_from_normal(x,y,z);q=sample(den,u,v)
        if r0>q*.36:continue
        h=sample(lng,u,v);vv=sample(var,u,v);bx=CX+R*x;by=CY-R*y
        dx,dy=unit(x*.22+(r1-.5)*.22,-.28-y*.10);L=1.5+6.5*h
        tx=bx+dx*L;ty=by+dy*L;rad=1.0+2.0*vv
        col=(76+int(70*vv),112+int(55*vv),20+int(24*vv),140+int(85*z))
        dr.line((bx,by,tx,ty),fill=col,width=1 if z<.55 else 2)
        if r2>.50:dr.ellipse((tx-rad,ty-rad,tx+rad,ty+rad),fill=(132+int(45*vv),156+int(38*vv),35+int(25*vv),col[3]))
    return relabel(Image.alpha_composite(im,ov),name,"procedural 3D moss fuzz · tuft clusters · seamless coverage")

def render_fur(d,name,base):
    den,lng,bend,var=(load_mask(d,name,k) for k in ("strandDensity","strandLength","strandBend","strandVariation"))
    im=base.convert("RGBA");strands=Image.new("RGBA",im.size,(0,0,0,0));dr=ImageDraw.Draw(strands,"RGBA")
    for z,x,y,r0,r1,r2 in points(91007,13500):
        u,v=uv_from_normal(x,y,z);q=sample(den,u,v)
        if r0>q*.38:continue
        L=(6+27*sample(lng,u,v))*(.80+.20*(1-z));b=sample(bend,u,v);vv=sample(var,u,v);bx=CX+R*x;by=CY-R*y
        dx,dy=unit(x*.48+.18*b+(r1-.5)*.10,-.58-y*.34+.08*b);tx=bx+dx*L;ty=by+dy*L
        c0=np.array([63,34,17]);c1=np.array([216,164,91]);c=(c0*(1-vv)+c1*vv).astype(int);alpha=int(95+145*z)
        dr.line((bx,by,tx,ty),fill=(int(c[0]),int(c[1]),int(c[2]),alpha),width=1 if z<.65 else 2)
    soft=strands.filter(ImageFilter.GaussianBlur(.55));out=Image.alpha_composite(Image.alpha_composite(im,soft),strands)
    return relabel(out,name,"procedural strand/shell fur · flow field · length variation")

def flame_poly(bx,by,tx,ty,w,curve):
    dx,dy=unit(tx-bx,ty-by);sx,sy=-dy,dx;mx=bx+(tx-bx)*.55+sx*curve;my=by+(ty-by)*.55+sy*curve
    return [(bx-sx*w,by-sy*w),(mx-sx*w*.58,my-sy*w*.58),(tx,ty),(mx+sx*w*.58,my+sy*w*.58),(bx+sx*w,by+sy*w)]

def render_fire(d,name,base):
    den,lng,heat,smoke,sparks=(load_mask(d,name,k) for k in ("flameDensity","flameHeight","heatDistortion","smoke","sparks"))
    im=base.convert("RGBA");glow=Image.new("RGBA",im.size,(0,0,0,0));outer=Image.new("RGBA",im.size,(0,0,0,0));inner=Image.new("RGBA",im.size,(0,0,0,0));dg=ImageDraw.Draw(glow,"RGBA");do=ImageDraw.Draw(outer,"RGBA");di=ImageDraw.Draw(inner,"RGBA")
    for z,x,y,r0,r1,r2 in points(44021,1500):
        u,v=uv_from_normal(x,y,z);f=sample(den,u,v)
        if r0>f*.23:continue
        h=sample(heat,u,v);L=28+90*sample(lng,u,v)*(0.72+0.28*r2);bx=CX+R*x;by=CY-R*y
        dx,dy=unit(x*.20+.44*h+(r1-.5)*.18,-1.0-y*.08);tx=bx+dx*L;ty=by+dy*L;w=5+10*f*(.55+.45*z);curve=(r2-.5)*18
        poly=flame_poly(bx,by,tx,ty,w,curve);dg.polygon(poly,fill=(255,72,0,90));do.polygon(poly,fill=(242,63,0,135+int(80*z)))
        inner_poly=flame_poly(bx+(tx-bx)*.18,by+(ty-by)*.18,tx,ty,w*.46,curve*.45);di.polygon(inner_poly,fill=(255,151,18,185+int(60*z)))
        core_poly=flame_poly(bx+(tx-bx)*.45,by+(ty-by)*.45,tx,ty,w*.18,curve*.15);di.polygon(core_poly,fill=(255,237,107,225))
        if sample(sparks,u,v)>.68 and r2>.68:di.ellipse((tx-2.0,ty-2.0,tx+2.0,ty+2.0),fill=(255,219,90,230))
        if sample(smoke,u,v)>.58 and r1>.82:dg.ellipse((tx-10,ty-26,tx+10,ty-4),fill=(50,45,42,42))
    g1=glow.filter(ImageFilter.GaussianBlur(18));g2=glow.filter(ImageFilter.GaussianBlur(6));out=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(im,g1),g2),outer),inner)
    return relabel(out,name,"procedural emissive flame volume · tongues · glow · smoke · sparks")

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
