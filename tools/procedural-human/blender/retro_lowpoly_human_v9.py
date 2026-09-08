import bpy
import gzip
import json
import math
import os
import sys
import urllib.request
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/retro-lowpoly-human')
os.makedirs(OUT_DIR, exist_ok=True)

# Retro Low-Poly Human v9
# -----------------------
# BODY BASEMESH ONLY. No hair, face add-ons, clothing, props or extra shells.
# Start from the original full CC0 Anny/MPFB2 body, apply real male/female
# phenotype displacement fields, then reshape ONLY the existing body vertices.
# Art direction: clean late-90s/early-2000s low-poly game basemesh with attractive
# proportions and readable silhouette, NOT origami and NOT super-deformed chibi.

RAW = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2'
BASE_URL = RAW + '/3dobjs/base.obj'
TARGET = RAW + '/targets/macrodetails'
TARGET_TRIS = 760


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def fetch_text(url, gz=False):
    req = urllib.request.Request(url, headers={'User-Agent':'voxel-frontier-retro-lowpoly-human'})
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
    return verts,faces


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


def add_target(verts,target,weight):
    if abs(weight)<1e-8:
        return
    for i,d in target.items():
        if 0<=i<len(verts):
            verts[i][0]+=d[0]*weight
            verts[i][1]+=d[1]*weight
            verts[i][2]+=d[2]*weight


def phenotype(kind,verts):
    for race in ('african','asian','caucasian'):
        add_target(verts,parse_target(fetch_text(f'{TARGET}/{race}-{kind}-young.target.gz',True)),1.0/3.0)
    src=f'{TARGET}/universal-{kind}-young-averagemuscle-averageweight.target.gz'
    add_target(verts,parse_target(fetch_text(src,True)),0.16 if kind=='female' else 0.20)


def axis_frame(verts):
    mins=[min(v[a] for v in verts) for a in range(3)]
    maxs=[max(v[a] for v in verts) for a in range(3)]
    ranges=[maxs[a]-mins[a] for a in range(3)]
    order=sorted(range(3),key=lambda a:ranges[a],reverse=True)
    up=order[0]; depth=order[2]; width=order[1]
    return mins,maxs,ranges,width,depth,up


def gauss(x,c,s):
    return math.exp(-0.5*((x-c)/s)**2)


def smoothstep(a,b,x):
    if x<=a: return 0.0
    if x>=b: return 1.0
    t=(x-a)/(b-a)
    return t*t*(3.0-2.0*t)


def vertical_remap(q,kind):
    # Balanced stylized proportions: roughly 6.5 heads female / 6.8 heads male.
    # Slightly longer legs than v8, shorter neck, compact but not chibi torso.
    hip=0.515
    neck=0.855
    leg_s=1.035 if kind=='female' else 1.025
    torso_s=0.980 if kind=='female' else 0.990
    head_s=1.055 if kind=='female' else 1.040

    def raw(t):
        if t<=hip:
            return t*leg_s
        if t<=neck:
            return hip*leg_s+(t-hip)*torso_s
        return hip*leg_s+(neck-hip)*torso_s+(t-neck)*head_s
    return raw(q)/raw(1.0)


def canonical_body(kind,verts,faces):
    mins,maxs,ranges,width,depth,up=axis_frame(verts)
    H=ranges[up]
    cw=(mins[width]+maxs[width])*0.5
    cd=(mins[depth]+maxs[depth])*0.5
    used=sorted({i for f in faces for i in f})
    remap={old:i for i,old in enumerate(used)}
    target_height=1.66 if kind=='female' else 1.76

    out=[]
    for old in used:
        v=verts[old]
        x=(v[width]-cw)/H
        y=(v[depth]-cd)/H
        q=(v[up]-mins[up])/H
        z=vertical_remap(q,kind)*target_height

        # Head: modest stylization, cleaner cranium and less stretched neck.
        head=smoothstep(0.865,0.905,q)
        x*=1.0+(0.075 if kind=='female' else 0.055)*head
        y*=1.0+(0.060 if kind=='female' else 0.045)*head
        jaw=gauss(q,0.875,0.025)
        x*=1.0-(0.035 if kind=='female' else 0.022)*jaw

        # Neck: slightly slimmer, visually shorter and cleaner.
        neck_gate=gauss(q,0.835,0.032)
        x*=1.0-(0.095 if kind=='female' else 0.070)*neck_gate
        y*=1.0-0.045*neck_gate

        if kind=='female':
            # Readable S-curve without exaggeration.
            sx=(1.0
                -0.030*gauss(q,0.790,0.055)   # shoulders
                -0.015*gauss(q,0.690,0.080)   # ribcage
                -0.060*gauss(q,0.575,0.055)   # waist
                +0.060*gauss(q,0.500,0.060)   # pelvis
                +0.020*gauss(q,0.390,0.090))  # upper thigh
            sy=(1.0
                -0.010*gauss(q,0.690,0.080)
                +0.035*gauss(q,0.500,0.070))
        else:
            # Youthful V-shape: shoulders readable but not superhero-wide.
            sx=(1.0
                +0.060*gauss(q,0.790,0.060)
                +0.030*gauss(q,0.700,0.085)
                -0.035*gauss(q,0.575,0.065)
                -0.015*gauss(q,0.500,0.070))
            sy=1.0+0.018*gauss(q,0.700,0.090)
        x*=sx; y*=sy

        # Arms: shorten and slightly thicken forearm silhouette.
        arm_gate=gauss(q,0.685,0.170)
        ax=abs(x)
        torso_edge=0.112 if kind=='female' else 0.122
        if ax>torso_edge:
            new_ax=torso_edge+(ax-torso_edge)*(0.925 if kind=='female' else 0.935)
            ax=ax*(1.0-arm_gate)+new_ax*arm_gate
            x=math.copysign(ax,x)
            # Keep limbs from becoming needle-thin after decimation.
            y*=1.0+0.030*arm_gate

        # Hands: fold finger spread back into a simple palm/wedge silhouette.
        # No new geometry: only compress extreme existing hand vertices.
        hand_gate=gauss(q,0.575,0.090)
        hand_start=0.275 if kind=='female' else 0.295
        if abs(x)>hand_start and hand_gate>0.08:
            ax=abs(x)
            ax=hand_start+(ax-hand_start)*0.48
            x=math.copysign(ax,x)
            y*=0.78+0.22*(1.0-hand_gate)

        # Legs: readable thigh/calf rhythm; avoid stick-like shins.
        thigh=gauss(q,0.360,0.105)
        calf=gauss(q,0.175,0.070)
        ankle=gauss(q,0.070,0.035)
        if kind=='female':
            x*=1.0+0.035*thigh+0.025*calf-0.020*ankle
            y*=1.0+0.020*thigh+0.015*calf
        else:
            x*=1.0+0.045*thigh+0.035*calf-0.015*ankle
            y*=1.0+0.025*thigh+0.020*calf

        # Feet: slightly larger, simpler, more stable retro-game silhouette.
        foot_gate=1.0-smoothstep(0.035,0.090,q)
        if foot_gate>0:
            x*=1.0+0.055*foot_gate
            y*=1.0+0.090*foot_gate

        out.append((x*target_height,y*target_height,z))

    compact_faces=[[remap[i] for i in f] for f in faces]
    return out,compact_faces


def mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*rgb,1)
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=(*rgb,1)
        bsdf.inputs['Roughness'].default_value=.92
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


def lowpoly_reconstruct(obj,target=TARGET_TRIS):
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    tri=obj.modifiers.new('Triangulate','TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri.name)
    before=tri_count(obj)

    dec=obj.modifiers.new('Retro_QEM','DECIMATE')
    dec.decimate_type='COLLAPSE'
    dec.ratio=max(.001,min(1.0,target/max(before,1)))
    dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)

    # No origami planar dissolve. Keep the clean QEM silhouette and flat-shade it.
    for p in obj.data.polygons:
        p.use_smooth=False
    obj.data.update()
    return before,tri_count(obj)


def make_character(kind):
    base,faces=parse_obj_body(fetch_text(BASE_URL))
    phenotype(kind,base)
    verts,faces=canonical_body(kind,base,faces)
    color=(0.62,0.69,0.76) if kind=='male' else (0.78,0.68,0.71)
    ob=mesh_from_data(kind.capitalize()+'RetroLowpolyBase',verts,faces,mat(kind+'Base',color))
    before,after=lowpoly_reconstruct(ob)
    return ob,before,after


def export_character(kind):
    clear_scene()
    ob,before,after=make_character(kind)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    return before,after


def studio():
    sc=bpy.context.scene
    sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.engine='BLENDER_EEVEE'
    sc.world.color=(.025,.028,.034)
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass

    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.006))
    floor=bpy.context.object; floor.data.materials.append(mat('Floor',(.075,.080,.088)))

    for name,loc,energy,size in [
        ('Key',(-3.2,-4.4,4.2),1050,3.0),
        ('Fill',(3.1,-3.6,2.7),440,2.7),
        ('Rim',(0,3.4,3.5),700,2.1)]:
        ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size
        lob=bpy.data.objects.new(name,ld); bpy.context.collection.objects.link(lob); lob.location=loc
        lob.rotation_euler=(Vector((0,0,.88))-Vector(loc)).to_track_quat('-Z','Y').to_euler()

    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam)
    cam.location=(1.95,-6.4,1.62)
    cam.rotation_euler=(Vector((0,0,.86))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler()
    cd.lens=72; sc.camera=cam


def render_pair():
    clear_scene()
    male,bm,am=make_character('male'); female,bf,af=make_character('female')
    male.location.x=-.58; female.location.x=.58
    male.rotation_euler[2]=math.radians(-1.5); female.rotation_euler[2]=math.radians(1.5)
    studio()
    bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-retro-lowpoly.png')
    bpy.ops.render.render(write_still=True)
    return bm,am,bf,af


mb,ma=export_character('male')
fb,fa=export_character('female')
rmb,rma,rfb,rfa=render_pair()
metrics={
    'style':'retro-lowpoly-basemesh-v9-body-only',
    'source':'Anny/MPFB2 CC0 full body surface + sparse phenotype targets',
    'extra_character_geometry':False,
    'hair':False,
    'face_addons':False,
    'clothing':False,
    'target_tris':TARGET_TRIS,
    'male_tris_before':mb,'male_tris':ma,
    'female_tris_before':fb,'female_tris':fa,
    'female_head_ratio_target':6.5,
    'male_head_ratio_target':6.8,
    'method':'full basemesh -> phenotype -> attractive retro proportions -> hand/foot silhouette cleanup -> QEM -> flat shading',
    'blender_version':'.'.join(map(str,bpy.app.version))
}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f:
    json.dump(metrics,f,indent=2)
print('RETRO_LOWPOLY_HUMAN_V9_METRICS',json.dumps(metrics))
