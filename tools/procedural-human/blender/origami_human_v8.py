import bpy
import gzip
import json
import math
import os
import sys
import time
import urllib.request
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR, exist_ok=True)

# Origami Human v8 — body-only master.
# No hair, eye objects, clothes or props. Every visible polygon belongs to the
# same CC0 body surface. The source topology is transformed into a cute anime
# paper-sculpture silhouette before low-poly reconstruction.
RAW = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2'
BASE_URL = RAW + '/3dobjs/base.obj'
TARGET = RAW + '/targets/macrodetails'
TARGET_TRIS = 480
_FETCH_CACHE = {}


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def fetch_text(url, gz=False):
    key=(url,gz)
    if key in _FETCH_CACHE:
        return _FETCH_CACHE[key]
    last=None
    for attempt in range(5):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-origami-basemesh-v8'})
            data=urllib.request.urlopen(req,timeout=60).read()
            if gz:
                data=gzip.decompress(data)
            text=data.decode('utf-8')
            _FETCH_CACHE[key]=text
            return text
        except Exception as e:
            last=e
            print('FETCH_RETRY',attempt+1,url,type(e).__name__,str(e))
            time.sleep(1.2*(attempt+1))
    raise last


def parse_obj_body(text):
    verts=[]; faces=[]; group=''
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('v '):
            p=line.split(); verts.append([float(p[1]),float(p[2]),float(p[3])])
        elif line.startswith('g '):
            group=line[2:].strip().split()[0] if line[2:].strip() else ''
        elif line.startswith('f ') and group=='body':
            ids=[int(tok.split('/')[0])-1 for tok in line[2:].split()]
            if len(ids)>=3:
                faces.append(ids)
    if len(verts)<1000 or len(faces)<1000:
        raise RuntimeError(f'Unexpected base mesh: {len(verts)} verts, {len(faces)} body faces')
    return verts,faces


def parse_target(text):
    out={}
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        p=line.split()
        if len(p)>=4:
            out[int(p[0])]=(float(p[1]),float(p[2]),float(p[3]))
    return out


def add_target(verts,target,weight):
    for i,d in target.items():
        if 0<=i<len(verts):
            verts[i][0]+=d[0]*weight
            verts[i][1]+=d[1]*weight
            verts[i][2]+=d[2]*weight


def phenotype(kind,verts):
    for race in ('african','asian','caucasian'):
        add_target(verts,parse_target(fetch_text(f'{TARGET}/{race}-{kind}-young.target.gz',True)),1/3)
    macro='universal-male-young-averagemuscle-averageweight.target.gz' if kind=='male' else 'universal-female-young-averagemuscle-averageweight.target.gz'
    add_target(verts,parse_target(fetch_text(f'{TARGET}/{macro}',True)),.20 if kind=='male' else .17)


def axis_frame(verts):
    mins=[min(v[a] for v in verts) for a in range(3)]
    maxs=[max(v[a] for v in verts) for a in range(3)]
    ranges=[maxs[a]-mins[a] for a in range(3)]
    order=sorted(range(3),key=lambda a:ranges[a],reverse=True)
    return mins,maxs,ranges,order[1],order[2],order[0]


def gauss(x,c,s):
    return math.exp(-.5*((x-c)/s)**2)


def smoothstep(a,b,x):
    if x<=a: return 0.0
    if x>=b: return 1.0
    t=(x-a)/(b-a)
    return t*t*(3-2*t)


def anime_vertical_q(q,kind):
    # Head occupies roughly a quarter of total height. This is intentionally
    # closer to a cute anime figure than to an adult realistic mannequin.
    hip=.50; neck=.84
    if kind=='female':
        leg_s=.82; torso_s=.92; head_s=1.55
    else:
        leg_s=.85; torso_s=.95; head_s=1.45
    def raw(t):
        if t<=hip: return t*leg_s
        if t<=neck: return hip*leg_s+(t-hip)*torso_s
        return hip*leg_s+(neck-hip)*torso_s+(t-neck)*head_s
    return raw(q)/raw(1.0)


def canonical_body(kind,verts,faces):
    mins,maxs,ranges,width,depth,up=axis_frame(verts)
    H=ranges[up]; cw=(mins[width]+maxs[width])/2; cd=(mins[depth]+maxs[depth])/2
    used=sorted({i for f in faces for i in f}); remap={old:i for i,old in enumerate(used)}
    target_height=1.48 if kind=='male' else 1.40
    out=[]
    for old in used:
        v=verts[old]
        x=(v[width]-cw)/H
        y=(v[depth]-cd)/H
        q=(v[up]-mins[up])/H
        q2=anime_vertical_q(q,kind)

        # Large cranium + short tapered lower face, on the original body vertices.
        head_t=smoothstep(.795,.865,q)
        x*=1+( .45 if kind=='female' else .39)*head_t
        y*=1+( .34 if kind=='female' else .29)*head_t
        jaw=gauss(q,.862,.032)
        x*=1-(.145 if kind=='female' else .115)*jaw
        y*=1-(.070 if kind=='female' else .052)*jaw

        # Compact shoulders/ribcage, readable waist/hip rhythm.
        if kind=='female':
            sx=(1-.13*gauss(q,.79,.060)-.06*gauss(q,.69,.080)-.12*gauss(q,.57,.060)+.12*gauss(q,.49,.065)+.035*gauss(q,.36,.095))
            sy=1-.035*gauss(q,.70,.09)+.045*gauss(q,.49,.08)
        else:
            sx=(1-.025*gauss(q,.79,.060)+.015*gauss(q,.69,.085)-.06*gauss(q,.57,.070)+.025*gauss(q,.49,.075))
            sy=1+.010*gauss(q,.70,.10)
        x*=sx; y*=sy

        # Collapse detailed fingers into a compact hand envelope before QEM.
        ax=abs(x)
        if .52<q<.76 and ax>(.245 if kind=='female' else .260):
            sign=1 if x>=0 else -1
            edge=.245 if kind=='female' else .260
            x=sign*(edge+(ax-edge)*.14)
            y*=.55

        X=x*target_height; Y=y*target_height; Z=q2*target_height

        # Rotate arms down ~43 degrees around each shoulder so the master reads
        # like a friendly character, not a T/A-pose technical mannequin.
        if .50<q<.82 and abs(X)>target_height*(.105 if kind=='female' else .115):
            sgn=1 if X>0 else -1
            cx=sgn*target_height*(.110 if kind=='female' else .120)
            cz=anime_vertical_q(.77,kind)*target_height
            dx=X-cx; dz=Z-cz
            a=-sgn*math.radians(43)
            X=cx+math.cos(a)*dx-math.sin(a)*dz
            Z=cz+math.sin(a)*dx+math.cos(a)*dz

        # Slightly oversized feet make the tiny body feel stable/cute.
        if q<.075:
            X*=1.18; Y*=1.16

        out.append((X,Y,Z))
    return out,[[remap[i] for i in f] for f in faces]


def mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True; m.diffuse_color=(*rgb,1)
    b=m.node_tree.nodes.get('Principled BSDF')
    if b:
        b.inputs['Base Color'].default_value=(*rgb,1); b.inputs['Roughness'].default_value=.96
    return m


def mesh_from_data(name,verts,faces,material):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(material)
    return ob


def tri_count(obj):
    obj.data.calc_loop_triangles(); return len(obj.data.loop_triangles)


def faceted_reconstruct(obj,target=TARGET_TRIS):
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    t=obj.modifiers.new('Triangulate','TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=t.name)
    before=tri_count(obj)
    d=obj.modifiers.new('Origami_QEM','DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=max(.001,min(1,target/max(before,1))); d.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=d.name)
    d2=obj.modifiers.new('Origami_Planar','DECIMATE'); d2.decimate_type='DISSOLVE'; d2.angle_limit=math.radians(1.2)
    bpy.ops.object.modifier_apply(modifier=d2.name)
    for p in obj.data.polygons: p.use_smooth=False
    obj.data.update(); return before,tri_count(obj)


def make_character(kind):
    base,faces=parse_obj_body(fetch_text(BASE_URL)); phenotype(kind,base)
    verts,faces=canonical_body(kind,base,faces)
    color=(.63,.70,.82) if kind=='male' else (.88,.68,.77)
    ob=mesh_from_data(kind.capitalize()+'CuteAnimeOrigamiBase',verts,faces,mat(kind+'Paper',color))
    before,after=faceted_reconstruct(ob,TARGET_TRIS)
    return ob,before,after


def export_character(kind):
    clear_scene(); ob,before,after=make_character(kind)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    return before,after


def studio():
    sc=bpy.context.scene; sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.engine='BLENDER_EEVEE'; sc.world.color=(.020,.023,.030)
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass
    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.005)); bpy.context.object.data.materials.append(mat('Floor',(.060,.064,.074)))
    for name,loc,energy,size in [('Key',(-3.6,-4.5,4.4),1250,3.1),('Fill',(3.0,-3.2,2.8),520,2.7),('Rim',(0,3.2,3.6),850,2.2)]:
        ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size
        lob=bpy.data.objects.new(name,ld); bpy.context.collection.objects.link(lob); lob.location=loc
        lob.rotation_euler=(Vector((0,0,.72))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam)
    cam.location=(2.35,-5.25,1.65); cam.rotation_euler=(Vector((0,0,.67))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=70; sc.camera=cam


def render_pair():
    clear_scene(); male,mb,ma=make_character('male'); female,fb,fa=make_character('female')
    male.location.x=-.50; female.location.x=.50; male.rotation_euler[2]=math.radians(-3); female.rotation_euler[2]=math.radians(3)
    studio(); bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png'); bpy.ops.render.render(write_still=True)
    return mb,ma,fb,fa


mb,ma=export_character('male'); fb,fa=export_character('female'); rmb,rma,rfb,rfa=render_pair()
metrics={
    'style':'cute-anime-origami-basemesh-v8-body-only',
    'source':'Anny/MPFB2 CC0 full body surface + sparse phenotype targets',
    'extra_character_geometry':False,'hair':False,'face_addons':False,'clothing':False,
    'female_head_ratio_target':4.0,'male_head_ratio_target':4.2,
    'male_tris_before':mb,'male_tris':ma,'female_tris_before':fb,'female_tris':fa,'target_tris':TARGET_TRIS,
    'method':'full basemesh -> phenotype -> anime remap -> hand abstraction -> lowered arms -> QEM -> flat facets',
    'blender_version':'.'.join(map(str,bpy.app.version))
}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f: json.dump(metrics,f,indent=2)
print('ORIGAMI_HUMAN_V8_METRICS',json.dumps(metrics))
