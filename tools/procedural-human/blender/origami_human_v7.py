# Cute anime origami master-model layer over the tested V6 generator.
# The CC0 human remains the anatomical source of truth, but the visible art
# direction is intentionally non-realistic: ~3.6-4 head proportions, large
# paper eyes/hair, hidden source arms, designed faceted sleeves/hands/shoes.
import os

HERE=os.path.dirname(os.path.abspath(__file__))
path=os.path.join(HERE,'origami_human_v6.py')
with open(path,'r',encoding='utf-8') as f:
    src=f.read()

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
            req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-anime-origami-master'})
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
if old_fetch not in src: raise RuntimeError('fetch patch anchor missing')
src=src.replace(old_fetch,new_fetch)

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
if old_wedge not in src: raise RuntimeError('wedge patch anchor missing')
src=src.replace(old_wedge,new_wedge)

repls={
    "BODY_TARGET=360":"BODY_TARGET=300",
    "if q<.48: return q/.48*.445":"if q<.44: return q/.44*.365",
    "if q<.865: return .445+(q-.48)/.385*.345":"if q<.835: return .365+(q-.44)/.395*.355",
    "return .790+(q-.865)/.135*.210":"return .720+(q-.835)/.165*.280",
    "height=1.58 if kind=='male' else 1.50":"height=1.42 if kind=='male' else 1.34",
    "sx=1+.40*head-.14*jaw-.10*neck-.075*shoulder-.12*waist+.10*hip":"sx=1+.72*head-.18*jaw-.12*neck-.09*shoulder-.14*waist+.12*hip",
    "sy=1+.25*head+.018*hip":"sy=1+.43*head+.022*hip",
    "sx=1+.35*head-.10*jaw-.09*neck+.015*shoulder-.07*waist+.035*hip":"sx=1+.64*head-.15*jaw-.11*neck+.005*shoulder-.085*waist+.04*hip",
    "sy=1+.21*head+.018*shoulder":"sy=1+.39*head+.020*shoulder",
    "if q<.072: x*=1.12; y*=1.10":"if q<.090: x*=1.24; y*=1.20",
    "w=h*.034; hh=h*.018":"w=h*.052; hh=h*.028",
    "(-h*.070,zc+h*.067),(-h*.094,zc+h*.020),(-h*.088,zc-h*.038),(-h*.050,zc-h*.082)":"(-h*.088,zc+h*.082),(-h*.118,zc+h*.025),(-h*.110,zc-h*.047),(-h*.062,zc-h*.098)",
    "(h*.050,zc-h*.082),(h*.088,zc-h*.038),(h*.094,zc+h*.020),(h*.070,zc+h*.067)":"(h*.062,zc-h*.098),(h*.110,zc-h*.047),(h*.118,zc+h*.025),(h*.088,zc+h*.082)",
    "(h*.118,h*.108,h*.122)":"(h*.155,h*.140,h*.165)",
    "(.985,.80,.88)":"(.98,.57,.76)",
    "(.78,.66,.94)":"(.68,.48,.92)",
    "(.55,.67,.86)":"(.32,.53,.86)",
    "(.32,.40,.58)":"(.20,.29,.52)",
    "'style':'cute-anime-paper-sculpture-v6'":"'style':'cute-anime-origami-master-v8'",
    "'4.8-5.2 head proportions'":"'3.6-4.1 head proportions'",
}
for a,b in repls.items():
    if a not in src: raise RuntimeError('art patch anchor missing: '+a)
    src=src.replace(a,b)

# Suppress the source arms/hands into the torso silhouette. Visible arms are
# rebuilt below as intentional paper sleeves, preventing QEM finger spikes.
old_arm="""        # Lower A-pose arms into a friendlier anime base pose without a rig.
        if .56<q<.82 and abs(x)>height*.13:
            sgn=1 if x>0 else -1; px=sgn*height*.145; pz=height*.735; dx=x-px; dz=z-pz; a=sgn*math.radians(24)
            x=px+math.cos(a)*dx+math.sin(a)*dz; z=pz-math.sin(a)*dx+math.cos(a)*dz
"""
new_arm="""        # Fold source arms/hands inward; designed paper sleeves become the visible limbs.
        if .50<q<.83 and abs(x)>height*.105:
            sgn=1 if x>0 else -1
            x=sgn*(height*.108 + max(0.0,abs(x)-height*.105)*.025)
            y*=.42
"""
if old_arm not in src: raise RuntimeError('arm patch anchor missing')
src=src.replace(old_arm,new_arm)

# Add an oriented 6-sided truncated prism helper before outfit().
outfit_anchor="def outfit(kind,h):"
limb_helper="""def paper_limb(name,a,b,r0,r1,m,segments=6):
    a=Vector(a); b=Vector(b); d=b-a; L=d.length
    mid=(a+b)*.5
    bpy.ops.mesh.primitive_cone_add(vertices=segments,radius1=r0,radius2=r1,depth=L,end_fill_type='NGON',location=mid)
    o=bpy.context.object; o.name=name; o.data.materials.append(m)
    o.rotation_euler=Vector((0,0,1)).rotation_difference(d.normalized()).to_euler()
    for p in o.data.polygons: p.use_smooth=False
    return o

def outfit(kind,h):"""
if outfit_anchor not in src: raise RuntimeError('outfit helper anchor missing')
src=src.replace(outfit_anchor,limb_helper,1)

# Add oversized anime paper sleeves, mitten-hands and shoes before flat-shading.
shade_anchor="""    for o in objs:
        for p in o.data.polygons: p.use_smooth=False
    return objs
"""
shade_insert="""    sleeve=mat(kind+'Sleeve',(.98,.58,.77) if female else (.30,.52,.86))
    hand=mat(kind+'HandPaper',(.965,.79,.72) if female else (.89,.75,.68))
    shoe=mat(kind+'ShoePaper',(.73,.43,.88) if female else (.22,.31,.55))
    # Sleeves overlap the torso shell so the character reads as one paper sculpture.
    for s in (-1,1):
        shoulder=(s*h*(.128 if female else .138),-h*.005,h*.665)
        elbow=(s*h*(.158 if female else .170),-h*.018,h*.545)
        wrist=(s*h*(.145 if female else .155),-h*.030,h*.455)
        objs.append(paper_limb(kind+('SleeveL1' if s<0 else 'SleeveR1'),shoulder,elbow,h*.044,h*.036,sleeve,6))
        objs.append(paper_limb(kind+('SleeveL2' if s<0 else 'SleeveR2'),elbow,wrist,h*.038,h*.028,sleeve,6))
        objs.append(ico(kind+('HandL' if s<0 else 'HandR'),(wrist[0],wrist[1]-h*.006,wrist[2]-h*.022),(h*.030,h*.022,h*.036),hand,1))
        footx=s*h*.060
        objs.append(ico(kind+('ShoeL' if s<0 else 'ShoeR'),(footx,-h*.025,h*.035),(h*.062,h*.092,h*.045),shoe,1))
    for o in objs:
        for p in o.data.polygons: p.use_smooth=False
    return objs
"""
if shade_anchor not in src: raise RuntimeError('outfit extension anchor missing')
src=src.replace(shade_anchor,shade_insert,1)

exec(compile(src,path,'exec'),{'__name__':'__main__','__file__':path})
