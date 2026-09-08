import bpy
import gzip
import json
import math
import os
import sys
import urllib.request
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR, exist_ok=True)

# Origami Human v8
# ----------------
# FULL BODY BASEMESH ONLY.
# No hair, eyes, facial add-ons, clothing, props or body shells are created.
# Pipeline:
#   CC0 Anny/MPFB2 full body surface
#   -> real male/female sparse phenotype targets
#   -> anime proportion remap on the SAME body vertices
#   -> silhouette shaping on the SAME body vertices
#   -> Blender QEM low-poly reconstruction
#   -> flat-shaded faceted/origami basemesh
#
# Art direction reference target:
#   cute anime basemesh, not super-deformed chibi
#   female ~5.1 heads tall, male ~5.3 heads tall
#   larger head, shorter limbs, compact torso, clean shoulder/waist/hip rhythm

RAW = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2'
BASE_URL = RAW + '/3dobjs/base.obj'
TARGET = RAW + '/targets/macrodetails'
TARGET_TRIS = 520


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def fetch_text(url, gz=False):
    req = urllib.request.Request(url, headers={'User-Agent':'voxel-frontier-anime-origami-basemesh'})
    data = urllib.request.urlopen(req, timeout=60).read()
    if gz:
        data = gzip.decompress(data)
    return data.decode('utf-8')


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
    return verts, faces


def parse_target(text):
    out={}
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        p=line.split()
        if len(p)>=4:
            out[int(p[0])] = (float(p[1]),float(p[2]),float(p[3]))
    return out


def add_target(verts, target, weight):
    if abs(weight)<1e-8:
        return
    for i,d in target.items():
        if 0<=i<len(verts):
            verts[i][0]+=d[0]*weight
            verts[i][1]+=d[1]*weight
            verts[i][2]+=d[2]*weight


def phenotype(kind, verts):
    # Real CC0 phenotype displacement fields. These modify the SAME master mesh.
    for race in ('african','asian','caucasian'):
        txt=fetch_text(f'{TARGET}/{race}-{kind}-young.target.gz', gz=True)
        add_target(verts, parse_target(txt), 1.0/3.0)
    if kind=='male':
        txt=fetch_text(f'{TARGET}/universal-male-young-averagemuscle-averageweight.target.gz', gz=True)
        add_target(verts, parse_target(txt), 0.24)
    else:
        txt=fetch_text(f'{TARGET}/universal-female-young-averagemuscle-averageweight.target.gz', gz=True)
        add_target(verts, parse_target(txt), 0.20)


def axis_frame(verts):
    mins=[min(v[a] for v in verts) for a in range(3)]
    maxs=[max(v[a] for v in verts) for a in range(3)]
    ranges=[maxs[a]-mins[a] for a in range(3)]
    order=sorted(range(3), key=lambda a:ranges[a], reverse=True)
    up=order[0]; depth=order[2]; width=order[1]
    return mins,maxs,ranges,width,depth,up


def gauss(x,c,s):
    return math.exp(-0.5*((x-c)/s)**2)


def smoothstep(a,b,x):
    if x<=a: return 0.0
    if x>=b: return 1.0
    t=(x-a)/(b-a)
    return t*t*(3-2*t)


def anime_vertical_q(q, kind):
    # Piecewise vertical remap. Shorter legs + slightly compact torso + taller head.
    # Final normalization keeps the feet at 0 and crown at 1.
    hip=0.50
    neck=0.84
    if kind=='female':
        leg_s=0.90; torso_s=0.96; head_s=1.18
    else:
        leg_s=0.92; torso_s=0.97; head_s=1.14

    def raw(t):
        if t<=hip:
            return t*leg_s
        if t<=neck:
            return hip*leg_s + (t-hip)*torso_s
        return hip*leg_s + (neck-hip)*torso_s + (t-neck)*head_s

    return raw(q)/raw(1.0)


def canonical_body(kind, verts, faces):
    mins,maxs,ranges,width,depth,up=axis_frame(verts)
    H=ranges[up]
    cw=(mins[width]+maxs[width])/2
    cd=(mins[depth]+maxs[depth])/2
    used=sorted({i for f in faces for i in f})
    remap={old:i for i,old in enumerate(used)}

    target_height=1.60 if kind=='female' else 1.70
    out=[]

    for old in used:
        v=verts[old]
        x=(v[width]-cw)/H
        y=(v[depth]-cd)/H
        q=(v[up]-mins[up])/H

        # --- Anime head/body proportion on the SAME master vertices ---
        q2=anime_vertical_q(q, kind)
        z=q2*target_height

        # Head enlargement begins smoothly at the upper neck.
        head_t=smoothstep(0.82,0.875,q)
        if kind=='female':
            head_xy=1.0 + 0.24*head_t
            head_depth=1.0 + 0.18*head_t
        else:
            head_xy=1.0 + 0.20*head_t
            head_depth=1.0 + 0.15*head_t
        x*=head_xy
        y*=head_depth

        # Subtle jaw/face taper: only reshape existing head vertices.
        jaw=gauss(q,0.865,0.030)
        x*=1.0 - (0.060 if kind=='female' else 0.045)*jaw
        y*=1.0 - (0.025 if kind=='female' else 0.018)*jaw

        # --- Silhouette art direction, still only moving master vertices ---
        if kind=='female':
            # Narrower shoulders, compact ribcage, clear waist, softly wider pelvis.
            sx=(1.0
                -0.080*gauss(q,0.80,0.060)
                -0.045*gauss(q,0.69,0.085)
                -0.090*gauss(q,0.57,0.060)
                +0.085*gauss(q,0.49,0.060)
                +0.025*gauss(q,0.37,0.090))
            sy=(1.0
                -0.030*gauss(q,0.70,0.090)
                +0.030*gauss(q,0.49,0.080))
        else:
            # Youthful male: modest shoulder width, straighter waist, not heroic/bodybuilder.
            sx=(1.0
                +0.035*gauss(q,0.80,0.065)
                +0.020*gauss(q,0.69,0.090)
                -0.035*gauss(q,0.57,0.070)
                -0.010*gauss(q,0.49,0.070))
            sy=1.0 +0.012*gauss(q,0.70,0.100)
        x*=sx
        y*=sy

        # Shorten arms without adding/removing geometry: compress only vertices far
        # outside the torso in the arm-height band around the shoulder center.
        ax=abs(x)
        arm_gate=gauss(q,0.69,0.16)
        torso_edge=0.105 if kind=='female' else 0.115
        if ax>torso_edge:
            factor=(0.90 if kind=='female' else 0.92)
            compressed=torso_edge + (ax-torso_edge)*factor
            ax = ax*(1-arm_gate) + compressed*arm_gate
            x=math.copysign(ax,x)

        out.append((x*target_height, y*target_height, z))

    compact_faces=[[remap[i] for i in f] for f in faces]
    return out, compact_faces


def mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*rgb,1)
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=(*rgb,1)
        bsdf.inputs['Roughness'].default_value=.96
    return m


def mesh_from_data(name,verts,faces,material):
    me=bpy.data.meshes.new(name+'Mesh')
    me.from_pydata(verts,[],faces)
    me.update()
    ob=bpy.data.objects.new(name,me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def faceted_reconstruct(obj,target=TARGET_TRIS):
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)

    tri_mod=obj.modifiers.new('Triangulate','TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri_mod.name)
    before=tri_count(obj)

    dec=obj.modifiers.new('Origami_QEM','DECIMATE')
    dec.decimate_type='COLLAPSE'
    dec.ratio=max(.001,min(1.0,target/max(before,1)))
    dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)

    # Very small planar dissolve: preserve silhouette; expose intentional planes.
    dec2=obj.modifiers.new('Origami_Planar','DECIMATE')
    dec2.decimate_type='DISSOLVE'
    dec2.angle_limit=math.radians(1.4)
    bpy.ops.object.modifier_apply(modifier=dec2.name)

    for p in obj.data.polygons:
        p.use_smooth=False
    obj.data.update()
    return before,tri_count(obj)


def make_character(kind):
    base,faces=parse_obj_body(fetch_text(BASE_URL))
    phenotype(kind,base)
    verts,faces=canonical_body(kind,base,faces)
    color=(0.72,0.76,0.81) if kind=='male' else (0.84,0.75,0.78)
    ob=mesh_from_data(kind.capitalize()+'AnimeOrigamiBase',verts,faces,mat(kind+'Paper',color))
    before,after=faceted_reconstruct(ob,TARGET_TRIS)
    return ob,before,after


def export_character(kind):
    clear_scene()
    ob,before,after=make_character(kind)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    return before,after


def studio():
    sc=bpy.context.scene
    sc.render.resolution_x=1500
    sc.render.resolution_y=1000
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    sc.world.color=(.018,.021,.027)
    sc.render.engine='BLENDER_EEVEE'
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass

    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.005))
    floor=bpy.context.object
    floor.data.materials.append(mat('Floor',(.055,.060,.068)))

    for name,loc,energy,size in [
        ('Key',(-3.6,-4.5,4.4),1200,3.1),
        ('Fill',(3.0,-3.2,2.8),500,2.7),
        ('Rim',(0,3.2,3.6),820,2.2)
    ]:
        ld=bpy.data.lights.new(name,'AREA')
        ld.energy=energy; ld.shape='DISK'; ld.size=size
        lob=bpy.data.objects.new(name,ld)
        bpy.context.collection.objects.link(lob)
        lob.location=loc
        lob.rotation_euler=(Vector((0,0,0.88))-Vector(loc)).to_track_quat('-Z','Y').to_euler()

    cd=bpy.data.cameras.new('Camera')
    cam=bpy.data.objects.new('Camera',cd)
    bpy.context.collection.objects.link(cam)
    cam.location=(2.55,-5.55,1.92)
    cam.rotation_euler=(Vector((0,0,.82))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler()
    cd.lens=68
    sc.camera=cam


def render_pair():
    clear_scene()
    male,bm,am=make_character('male')
    female,bf,af=make_character('female')
    male.location.x=-.58
    female.location.x=.58
    male.rotation_euler[2]=math.radians(-2.5)
    female.rotation_euler[2]=math.radians(2.5)
    studio()
    bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png')
    bpy.ops.render.render(write_still=True)
    return bm,am,bf,af


mb,ma=export_character('male')
fb,fa=export_character('female')
rmb,rma,rfb,rfa=render_pair()
metrics={
    'style':'anime-origami-basemesh-v8-body-only',
    'source':'Anny/MPFB2 CC0 full body surface + sparse phenotype targets',
    'extra_character_geometry':False,
    'hair':False,
    'face_addons':False,
    'clothing':False,
    'female_head_ratio_target':5.1,
    'male_head_ratio_target':5.3,
    'male_tris_before':mb,
    'male_tris':ma,
    'female_tris_before':fb,
    'female_tris':fa,
    'target_tris':TARGET_TRIS,
    'method':'full basemesh -> phenotype -> proportion remap -> silhouette shaping -> QEM -> flat facets',
    'blender_version':'.'.join(map(str,bpy.app.version))
}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f:
    json.dump(metrics,f,indent=2)
print('ORIGAMI_HUMAN_V8_METRICS',json.dumps(metrics))
