#!/usr/bin/env python3
from pathlib import Path
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("build/generated-materials")
CX,CY,R=500.0,470.0,275.0

def load_l(d,n,key):
    p=d/f"{n}_mask-{key}.png"
    return np.asarray(Image.open(p).convert("L"),dtype=np.float32)/255 if p.is_file() else None

def load_rgb(d,n):return np.asarray(Image.open(d/f"{n}_baseColor.png").convert("RGB"),dtype=np.float32)/255

def sample(tex,u,v):
    h,w=tex.shape[:2];x=int((u%1)*w)%w;y=int(((1-v)%1)*h)%h
    return tex[y,x]

def hsh(a,b,c=0):
    x=math.sin(a*127.1+b*311.7+c*74.7)*43758.5453
    return x-math.floor(x)

def basis(lat,lon):
    cl,sl=math.cos(lat),math.sin(lat);co,so=math.cos(lon),math.sin(lon)
    p=np.array([cl*co,sl,cl*so],np.float32)
    elon=np.array([-so,0,co],np.float32)
    elat=np.array([-sl*co,cl,-sl*so],np.float32)
    return p,elon,elat

def project(p):return (CX+p[0]*R,CY-p[1]*R)

def render_wolf(d,n):
    guard=load_l(d,n,"guardHair");length=load_l(d,n,"strandLength");under=load_l(d,n,"underfur");base=load_rgb(d,n)
    if guard is None or length is None:return
    im=Image.open(d/"preview-sphere.png").convert("RGB");dr=ImageDraw.Draw(im,"RGBA")
    strokes=[]
    # Dense short underfur first, then fewer longer guard hairs. Geometry is projected
    # from actual sphere points so silhouette hairs extend beyond the displaced shell.
    for iy in range(4,43):
        lat=-1.33+iy/46*2.66
        for ix in range(92):
            lon=-math.pi+ix/92*2*math.pi
            p,elon,elat=basis(lat,lon)
            if p[2]<.05:continue
            u=(lon/(2*math.pi)+.5)%1;v=.5-lat/math.pi
            g=float(sample(guard,u,v));uf=float(sample(under,u,v)) if under is not None else .8;ln=float(sample(length,u,v))
            rnd=hsh(ix,iy,3)
            if rnd<.30*uf:
                tang=elon*(hsh(ix,iy,5)-.5)*.018-elat*(.010+.010*hsh(ix,iy,6));q=p*(1.006+.008*uf)+tang
                strokes.append((float(p[2]),project(p*1.005),project(q),(.58,.56,.53,.38),1))
            if g>.055 and hsh(ix,iy,7)<min(.92,.20+g*1.55):
                flow=-elat*(.030+.035*ln)+elon*((hsh(ix,iy,8)-.5)*.030)
                q=p*(1.015+.035*g)+flow
                c=np.clip(sample(base,u,v)*1.42+.10,0,1);alpha=int(105+120*min(1,g*1.6));width=1 if g<.34 else 2
                strokes.append((float(p[2])+.01,project(p*1.004),project(q),(float(c[0]),float(c[1]),float(c[2]),alpha/255),width))
    strokes.sort(key=lambda s:s[0])
    for _,a,b,c,w in strokes:
        rgba=tuple(int(max(0,min(1,x))*255) for x in c)
        dr.line([a,b],fill=rgba,width=w)
    im.save(d/"preview-sphere.png")
    (d/"preview-fiber-metrics.json").write_text(json.dumps({"renderer":"explicit_projected_guard_hair_v1","strokes":len(strokes)},indent=2)+"\n")

def render_moss(d,n):
    dens=load_l(d,n,"mossDensity");height=load_l(d,n,"mossHeight");var=load_l(d,n,"tuftVariation");base=load_rgb(d,n)
    if dens is None or height is None:return
    im=Image.open(d/"preview-sphere.png").convert("RGB");dr=ImageDraw.Draw(im,"RGBA");strokes=[]
    for iy in range(4,39):
        lat=-1.30+iy/42*2.60
        for ix in range(80):
            lon=-math.pi+ix/80*2*math.pi;p,elon,elat=basis(lat,lon)
            if p[2]<.08:continue
            u=(lon/(2*math.pi)+.5)%1;v=.5-lat/math.pi;de=float(sample(dens,u,v));mh=float(sample(height,u,v));vv=float(sample(var,u,v)) if var is not None else .5
            if hsh(ix,iy,11)>.18+.72*de:continue
            count=1+(1 if de>.77 and hsh(ix,iy,12)>.40 else 0)
            for k in range(count):
                jitter=(hsh(ix,iy,20+k)-.5);tang=elon*jitter*.014+elat*(hsh(ix,iy,24+k)-.5)*.010;q=p*(1.010+.025*mh)+tang
                c=np.clip(sample(base,u,v)*(.92+.34*vv)+np.array([.05,.08,.005]),0,1);alpha=int(100+110*de)
                strokes.append((float(p[2]),project(p*1.004),project(q),(float(c[0]),float(c[1]),float(c[2]),alpha/255),1 if mh<.72 else 2))
    strokes.sort(key=lambda s:s[0])
    for _,a,b,c,w in strokes:dr.line([a,b],fill=tuple(int(max(0,min(1,x))*255) for x in c),width=w)
    im.save(d/"preview-sphere.png")
    (d/"preview-fiber-metrics.json").write_text(json.dumps({"renderer":"explicit_projected_moss_tuft_v1","strokes":len(strokes)},indent=2)+"\n")

def main():
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        mp=d/"manifest.json"
        if not mp.is_file():continue
        m=json.loads(mp.read_text());preset=m.get("preset");n=m.get("material") or d.name
        if preset=="vfPainterlyWolfFur":render_wolf(d,n)
        elif preset=="vfPainterlyMoss":render_moss(d,n)
if __name__=="__main__":main()
