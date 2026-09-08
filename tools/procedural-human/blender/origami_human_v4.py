import bpy
import gzip
import io
import json
import math
import os
import sys
import urllib.request
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR, exist_ok=True)

# Origami Human v4
# ----------------
# Continuous-body approach.  We start from the CC0 Anny/MPFB2 human topology,
# apply real sparse phenotype displacement fields, exaggerate only a few
# interpretable silhouette proportions, and then reconstruct the complete body
# as a very low triangle-count faceted sculpture in Blender.
#
# This avoids the 'torso block + limb tubes' mannequin look of v1-v3 while
# preserving the project's core principle: one understood human surface +
# mathematical parameters -> many characters.

RAW = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2'
BASE_URL = RAW + '/3dobjs/base.obj'
TARGET = RAW + '/targets/macrodetails'
TARGET_TRIS = 460


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def fetch_text(url, gz=False):
    req = urllib.request.Request(url, headers={'User-Agent':'voxel-frontier-origami-human'})
    data = urllib.request.urlopen(req, timeout=60).read()
    if gz:
        data = gzip.decompress(data)
    return data.decode('utf-8')


def parse_obj_body(text):
    verts=[]; faces=[]; group=''
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'): continue
        if line.startswith('v '):
            p=line.split(); verts.append([float(p[1]),float(p[2]),float(p[3])])
        elif line.startswith('g '):
            group=line[2:].strip().split()[0] if line[2:].strip() else ''
        elif line.startswith('f ') and group=='body':
            ids=[int(tok.split('/')[0])-1 for tok in line[2:].split()]
            if len(ids)>=3: faces.append(ids)
    if len(verts)<1000 or len(faces)<1000:
        raise RuntimeError(f'Unexpected base mesh: {len(verts)} verts, {len(faces)} body faces')
    return verts,faces


def parse_target(text):
    out={}
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'): continue
        p=line.split()
        if len(p)>=4:
            out[int(p[0])] = (float(p[1]),float(p[2]),float(p[3]))
    return out


def add_target(verts, target, weight):
    if abs(weight)<1e-8: return
    for i,d in target.items():
        if 0<=i<len(verts):
            verts[i][0]+=d[0]*weight; verts[i][1]+=d[1]*weight; verts[i][2]+=d[2]*weight


def phenotype(kind, verts):
    # Anny's phenotype model linearly combines the three normalized ancestry
    # components.  Equal weighting gives a neutral mixture while retaining the
    # male/female young-body displacement field.
    for race in ('african','asian','caucasian'):
        txt=fetch_text(f'{TARGET}/{race}-{kind}-young.target.gz',gz=True)
        add_target(verts,parse_target(txt),1.0/3.0)
    # Subtle body-composition bias, still using real sparse CC0 displacement data.
    if kind=='male':
        txt=fetch_text(f'{TARGET}/universal-male-young-maxmuscle-averageweight.target.gz',gz=True)
        add_target(verts,parse_target(txt),0.32)
    else:
        txt=fetch_text(f'{TARGET}/universal-female-young-averagemuscle-minweight.target.gz',gz=True)
        add_target(verts,parse_target(txt),0.18)


def axis_frame(verts):
    mins=[min(v[a] for v in verts) for a in range(3)]
    maxs=[max(v[a] for v in verts) for a in range(3)]
    ranges=[maxs[a]-mins[a] for a in range(3)]
    order=sorted(range(3),key=lambda a:ranges[a],reverse=True)
    up=order[0]; depth=order[2]; width=order[1]
    return mins,maxs,ranges,width,depth,up


def gauss(x,c,s):
    return math.exp(-0.5*((x-c)/s)**2)


def canonical_body(kind, verts, faces):
    mins,maxs,ranges,width,depth,up=axis_frame(verts)
    H=ranges[up]
    cw=(mins[width]+maxs[width])/2; cd=(mins[depth]+maxs[depth])/2
    # Only vertices referenced by anatomical body faces survive.
    used=sorted({i for f in faces for i in f}); remap={old:i for i,old in enumerate(used)}
    out=[]
    target_height=1.80 if kind=='male' else 1.66
    for old in used:
        v=verts[old]
        x=(v[width]-cw)/H*target_height
        y=(v[depth]-cd)/H*target_height
        z=(v[up]-mins[up])/H*target_height
        q=z/target_height
        # Art direction layer: exaggerate the *silhouette*, not anatomy details.
        if kind=='male':
            sx=1 + .085*gauss(q,.82,.075) + .045*gauss(q,.70,.10) - .025*gauss(q,.56,.08) - .015*gauss(q,.49,.07)
            sy=1 + .025*gauss(q,.70,.11)
        else:
            sx=1 - .045*gauss(q,.82,.075) - .055*gauss(q,.58,.075) + .085*gauss(q,.49,.075) + .025*gauss(q,.36,.11)
            sy=1 + .030*gauss(q,.49,.09)
        x*=sx; y*=sy
        out.append((x,y,z))
    compact_faces=[[remap[i] for i in f] for f in faces]
    return out,compact_faces


def mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True; m.diffuse_color=(*rgb,1)
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=(*rgb,1)
        bsdf.inputs['Roughness'].default_value=.94
    return m


def mesh_from_data(name,verts,faces,material):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(material)
    return ob


def tri_count(obj):
    obj.data.calc_loop_triangles(); return len(obj.data.loop_triangles)


def faceted_reconstruct(obj,target=TARGET_TRIS):
    # Triangulate first so the ratio is defined in actual game triangles.
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    tri=bpy.ops.object.modifier_add(type='TRIANGULATE')
    tri_mod=obj.modifiers[-1]
    bpy.ops.object.modifier_apply(modifier=tri_mod.name)
    before=tri_count(obj)

    dec=obj.modifiers.new('Origami_QEM','DECIMATE')
    dec.decimate_type='COLLAPSE'
    dec.ratio=max(.001,min(1.0,target/max(before,1)))
    dec.use_collapse_triangulate=True
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=dec.name)

    # A second conservative planar dissolve removes tiny coplanar-ish slivers
    # while retaining silhouette vertices.  Angle is intentionally small.
    dec2=obj.modifiers.new('Origami_Planar','DECIMATE')
    dec2.decimate_type='DISSOLVE'; dec2.angle_limit=math.radians(2.0)
    bpy.ops.object.modifier_apply(modifier=dec2.name)

    for p in obj.data.polygons: p.use_smooth=False
    obj.data.update()
    return before,tri_count(obj)


def make_character(kind):
    base,faces=parse_obj_body(fetch_text(BASE_URL))
    phenotype(kind,base)
    verts,faces=canonical_body(kind,base,faces)
    color=(.64,.69,.70) if kind=='male' else (.73,.64,.61)
    ob=mesh_from_data(kind.capitalize()+'Origami',verts,faces,mat(kind+'Paper',color))
    before,after=faceted_reconstruct(ob,TARGET_TRIS)
    return ob,before,after


def export_character(kind):
    clear_scene(); ob,before,after=make_character(kind)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    return before,after


def studio():
    sc=bpy.context.scene; sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.world.color=(.014,.017,.021); sc.render.engine='BLENDER_EEVEE'
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass
    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.005)); floor=bpy.context.object; floor.data.materials.append(mat('Floor',(.045,.050,.055)))
    for name,loc,energy,size in [('Key',(-3.8,-4.6,4.4),1250,3.2),('Fill',(3.0,-3.0,2.5),520,2.7),('Rim',(0,3.5,3.6),950,2.3)]:
        ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size
        ob=bpy.data.objects.new(name,ld); bpy.context.collection.objects.link(ob); ob.location=loc
        ob.rotation_euler=(Vector((0,0,1.0))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam)
    cam.location=(2.65,-5.7,2.10); cam.rotation_euler=(Vector((0,0,.92))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=68; sc.camera=cam


def render_pair():
    clear_scene(); male,bm,am=make_character('male'); female,bf,af=make_character('female')
    male.location.x=-.58; female.location.x=.58
    # Tiny sculptural asymmetry: turn figures a few degrees in opposite directions.
    male.rotation_euler[2]=math.radians(-3.0); female.rotation_euler[2]=math.radians(3.5)
    studio(); bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png'); bpy.ops.render.render(write_still=True)
    return bm,am,bf,af


mb,ma=export_character('male'); fb,fa=export_character('female'); rmb,rma,rfb,rfa=render_pair()
metrics={
    'style':'continuous-faceted-origami-v4',
    'source':'Anny/MPFB2 CC0 body surface + sparse phenotype targets',
    'method':'real phenotype -> silhouette art direction -> Blender QEM reconstruction -> planar dissolve -> flat facets',
    'male_tris_before':mb,'male_tris':ma,'female_tris_before':fb,'female_tris':fa,
    'render_male_tris':rma,'render_female_tris':rfa,
    'target_tris':TARGET_TRIS,'blender_version':'.'.join(map(str,bpy.app.version))
}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f: json.dump(metrics,f,indent=2)
print('ORIGAMI_HUMAN_V4_METRICS',json.dumps(metrics))
