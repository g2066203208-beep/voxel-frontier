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

def rgba(rgb,a):return tuple(int(max(0,min(1,float(x)))*255) for x in (*rgb,a))

def render_wolf(d,n):
    guard=load_l(d,n,"guardHair");length=load_l(d,n,"strandLength");under=load_l(d,n,"underfur");base=load_rgb(d,n)
    if guard is None or length is None:return
    im=Image.open(d/"preview-sphere.png").convert("RGB");dr=ImageDraw.Draw(im,"RGBA")
    candidates=[]
    for iy in range(8):
        lat=-1.10+iy/7*2.20
        for ix in range(14):
            lon=-math.pi+ix/14*2*math.pi;p,elon,elat=basis(lat,lon)
            if p[2]<.10:continue
            u=(lon/(2*math.pi)+.5)%1;v=.5-lat/math.pi
            g=float(sample(guard,u,v));uf=float(sample(under,u,v)) if under is not None else .8;ln=float(sample(length,u,v))
            score=g*.72+uf*.20+p[2]*.08
            candidates.append((score,ix,iy,p,elon,elat,u,v,g,uf,ln))
    candidates.sort(key=lambda q:q[0],reverse=True)
    plates=[]
    for _,ix,iy,p,elon,elat,u,v,g,uf,ln in candidates[:12]:
        # One broad tapered coat sheet replaces dozens of individual hairs.
        width=.070+.030*hsh(ix,iy,3)
        length3=.085+.050*ln
        side=(hsh(ix,iy,4)-.5)*.025
        root=p*1.006+elon*side
        flow=-elat*length3+elon*(hsh(ix,iy,5)-.5)*.035
        tip=(p+flow)*1.025
        left0=root-elon*width*.52;right0=root+elon*width*.52
        left1=(root+flow*.58)-elon*width*.62;right1=(root+flow*.58)+elon*width*.62
        tipL=tip-elon*width*.22;tipR=tip+elon*width*.22
        pts=[project(left0),project(right0),project(right1),project(tipR),project(tipL),project(left1)]
        c=np.clip(sample(base,u,v)*1.18+.055,0,1);alpha=.42+.28*g
        plates.append((float(p[2]),pts,c,alpha))
    plates.sort(key=lambda q:q[0])
    for _,pts,c,a in plates:
        dr.polygon(pts,fill=rgba(c,a))
    im.save(d/"preview-sphere.png")
    (d/"preview-fiber-metrics.json").write_text(json.dumps({"renderer":"broad_painterly_wolf_coat_sheets_v2","broadPlates":len(plates),"thinStrands":0},indent=2)+"\n")

def render_moss(d,n):
    dens=load_l(d,n,"mossDensity");height=load_l(d,n,"mossHeight");var=load_l(d,n,"tuftVariation");base=load_rgb(d,n)
    if dens is None or height is None:return
    im=Image.open(d/"preview-sphere.png").convert("RGB");dr=ImageDraw.Draw(im,"RGBA")
    candidates=[]
    for iy in range(7):
        lat=-1.08+iy/6*2.16
        for ix in range(12):
            lon=-math.pi+ix/12*2*math.pi;p,elon,elat=basis(lat,lon)
            if p[2]<.10:continue
            u=(lon/(2*math.pi)+.5)%1;v=.5-lat/math.pi;de=float(sample(dens,u,v));mh=float(sample(height,u,v));vv=float(sample(var,u,v)) if var is not None else .5
            candidates.append((de*.76+mh*.16+p[2]*.08,ix,iy,p,elon,elat,u,v,de,mh,vv))
    candidates.sort(key=lambda q:q[0],reverse=True)
    patches=[]
    for _,ix,iy,p,elon,elat,u,v,de,mh,vv in candidates[:10]:
        # Large low cushions overlap into a continuous mat; no grass-like strokes.
        rx=.075+.035*hsh(ix,iy,10);ry=.060+.030*hsh(ix,iy,11);radial=.010+.025*mh
        center=p*(1+radial);pts=[]
        for k in range(12):
            a=2*math.pi*k/12
            q=center+elon*math.cos(a)*rx+elat*math.sin(a)*ry
            pts.append(project(q))
        c=np.clip(sample(base,u,v)*(.98+.20*vv)+np.array([.035,.055,.0]),0,1);alpha=.34+.34*de
        patches.append((float(p[2]),pts,c,alpha))
    patches.sort(key=lambda q:q[0])
    for _,pts,c,a in patches:
        dr.polygon(pts,fill=rgba(c,a))
    im.save(d/"preview-sphere.png")
    (d/"preview-fiber-metrics.json").write_text(json.dumps({"renderer":"broad_painterly_moss_cushions_v2","broadPatches":len(patches),"thinStrokes":0},indent=2)+"\n")

def main():
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        mp=d/"manifest.json"
        if not mp.is_file():continue
        m=json.loads(mp.read_text());preset=m.get("preset");n=m.get("material") or d.name
        if preset=="vfPainterlyWolfFur":render_wolf(d,n)
        elif preset=="vfPainterlyMoss":render_moss(d,n)
if __name__=="__main__":main()
