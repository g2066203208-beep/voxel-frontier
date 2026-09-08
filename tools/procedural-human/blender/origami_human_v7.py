# V7 is a compact art-direction layer over the tested V6 generator.
# It keeps the same deterministic Blender/CC0 pipeline while pushing the base
# silhouettes closer to cute anime paper sculpture: larger heads/eyes, shorter
# bodies, friendlier arm angle, compact hands and chunkier feet.
#
# Reliability additions in this wrapper:
# - source asset cache + retry/backoff so one transient raw.githubusercontent reset
#   cannot kill the render after GLB export;
# - manifold paper wedges so bangs/bows export without invalid-mesh warnings.
import os

HERE=os.path.dirname(os.path.abspath(__file__))
path=os.path.join(HERE,'origami_human_v6.py')
with open(path,'r',encoding='utf-8') as f:
    src=f.read()

# Add retry support to the imported V6 source.
src=src.replace(
    "import bpy, gzip, json, math, os, sys, urllib.request",
    "import bpy, gzip, json, math, os, sys, urllib.request, time"
)

old_fetch="""def fetch_text(url,gz=False):
    req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-anime-origami-v6'})
    data=urllib.request.urlopen(req,timeout=60).read();
    if gz: data=gzip.decompress(data)
    return data.decode('utf-8')
"""
new_fetch="""_FETCH_CACHE={}
def fetch_text(url,gz=False):
    key=(url,gz)
    if key in _FETCH_CACHE:
        return _FETCH_CACHE[key]
    last=None
    for attempt in range(5):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-anime-origami-v7'})
            data=urllib.request.urlopen(req,timeout=60).read()
            if gz: data=gzip.decompress(data)
            text=data.decode('utf-8')
            _FETCH_CACHE[key]=text
            return text
        except Exception as e:
            last=e
            print('FETCH_RETRY',attempt+1,url,type(e).__name__,str(e))
            time.sleep(1.2*(attempt+1))
    raise last
"""
if old_fetch not in src:
    raise RuntimeError('V7 fetch patch anchor missing')
src=src.replace(old_fetch,new_fetch)

# Replace the earlier non-manifold hair/bow wedge by a simple closed bipyramid.
old_wedge="""def wedge(name,center,scale,rz,m):
    x,y,z=scale; vs=[(-x,-y,-z*.25),(x,-y,-z*.25),(x,y,-z*.2),(-x,y,-z*.2),(0,-y*.15,z),(0,y*.10,z)]
    fs=[(0,1,4),(1,2,4),(2,5,4),(2,3,5),(3,0,5),(0,4,5),(0,5,3),(1,2,5)]
    o=mesh(name,vs,fs,m); o.location=center; o.rotation_euler[2]=rz; return o
"""
new_wedge="""def wedge(name,center,scale,rz,m):
    x,y,z=scale
    vs=[(-x,-y,0),(x,-y,0),(x,y,0),(-x,y,0),(0,-y*.35,z),(0,y*.35,-z*.38)]
    fs=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
    o=mesh(name,vs,fs,m); o.location=center; o.rotation_euler[2]=rz; return o
"""
if old_wedge not in src:
    raise RuntimeError('V7 wedge patch anchor missing')
src=src.replace(old_wedge,new_wedge)

repls={
    "BODY_TARGET=360":"BODY_TARGET=320",
    "if q<.48: return q/.48*.445":"if q<.46: return q/.46*.405",
    "if q<.865: return .445+(q-.48)/.385*.345":"if q<.855: return .405+(q-.46)/.395*.355",
    "return .790+(q-.865)/.135*.210":"return .760+(q-.855)/.145*.240",
    "height=1.58 if kind=='male' else 1.50":"height=1.50 if kind=='male' else 1.42",
    "sx=1+.40*head-.14*jaw-.10*neck-.075*shoulder-.12*waist+.10*hip":"sx=1+.52*head-.16*jaw-.11*neck-.080*shoulder-.13*waist+.11*hip",
    "sy=1+.25*head+.018*hip":"sy=1+.30*head+.020*hip",
    "sx=1+.35*head-.10*jaw-.09*neck+.015*shoulder-.07*waist+.035*hip":"sx=1+.46*head-.12*jaw-.10*neck+.010*shoulder-.075*waist+.035*hip",
    "sy=1+.21*head+.018*shoulder":"sy=1+.27*head+.018*shoulder",
    "a=sgn*math.radians(24)":"a=sgn*math.radians(30)",
    "if q<.072: x*=1.12; y*=1.10":"if q<.080: x*=1.20; y*=1.16",
    "w=h*.034; hh=h*.018":"w=h*.043; hh=h*.023",
    "(-h*.070,zc+h*.067),(-h*.094,zc+h*.020),(-h*.088,zc-h*.038),(-h*.050,zc-h*.082)":"(-h*.078,zc+h*.074),(-h*.105,zc+h*.022),(-h*.098,zc-h*.042),(-h*.055,zc-h*.090)",
    "(h*.050,zc-h*.082),(h*.088,zc-h*.038),(h*.094,zc+h*.020),(h*.070,zc+h*.067)":"(h*.055,zc-h*.090),(h*.098,zc-h*.042),(h*.105,zc+h*.022),(h*.078,zc+h*.074)",
    "(h*.118,h*.108,h*.122)":"(h*.132,h*.118,h*.140)",
    "'style':'cute-anime-paper-sculpture-v6'":"'style':'cute-chibi-anime-paper-sculpture-v7'",
    "'4.8-5.2 head proportions'":"'4.2-4.7 head proportions'",
}
for a,b in repls.items():
    if a not in src:
        raise RuntimeError('V7 patch anchor missing: '+a)
    src=src.replace(a,b)

anchor="        x*=sx; y*=sy\n        # Lower A-pose arms"
insert="        x*=sx; y*=sy\n        # Collapse fragile realistic fingers into a compact paper-hand envelope before decimation.\n        if .54<q<.77 and abs(x)>height*.245:\n            sgn=1 if x>0 else -1\n            x=sgn*(height*.245+(abs(x)-height*.245)*.22)\n            y*=.82\n        # Lower A-pose arms"
if anchor not in src:
    raise RuntimeError('V7 hand patch anchor missing')
src=src.replace(anchor,insert)

exec(compile(src,path,'exec'),{'__name__':'__main__','__file__':path})
