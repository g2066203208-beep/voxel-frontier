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

# Retro Low-Poly Human v10
# BODY BASEMESH ONLY: no hair, facial add-ons, clothing, props or extra shells.
# The original full CC0 body remains the only source mesh. All styling is done by
# moving its existing vertices, then performing symmetric low-poly reconstruction.

RAW='https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2'
BASE_URL=RAW+'/3dobjs/base.obj'
TARGET=RAW+'/targets/macrodetails'
TARGET_TRIS=800


def clear_scene():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)


def fetch_text(url,gz=False):
    req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-retro-lowpoly-v10'})
    data=urllib.request.urlopen(req,timeout=60).read()
    if gz: data=gzip.decompress(data)
    return data.decode('utf-8')


def parse_obj_body(text):
    verts=[]; faces=[]; group=''
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'): continue
        if line.startswith('v '):
            p=line.split(); verts.append([float(p[1]),float(p[2]),float(p[3])])
        elif line.startswith('g '): group=line[2:].strip().split()[0] if line[2:].strip() else ''
        elif line.startswith('f ') and group=='body':
            ids=[int(t.split('/')[0])-1 for t in line[2:].split()]
            if len(ids)>=3: faces.append(ids)
    if len(verts)<1000 or len(faces)<1000: raise RuntimeError('Unexpected body mesh')
    return verts,faces


def parse_target(text):
    out={}
    for raw in text.splitlines():
        p=raw.strip().split()
        if len(p)>=4 and not raw.lstrip().startswith('#'):
            out[int(p[0])]=(float(p[1]),float(p[2]),float(p[3]))
    return out


def add_target(verts,target,w):
    for i,d in target.items():
        if 0<=i<len(verts):
            verts[i][0]+=d[0]*w; verts[i][1]+=d[1]*w; verts[i][2]+=d[2]*w


def phenotype(kind,verts):
    for race in ('african','asian','caucasian'):
        add_target(verts,parse_target(fetch_text(f'{TARGET}/{race}-{kind}-young.target.gz',True)),1/3)
    add_target(verts,parse_target(fetch_text(f'{TARGET}/universal-{kind}-young-averagemuscle-averageweight.target.gz',True)),0.14 if kind=='female' else 0.18)


def axis_frame(verts):
    mins=[min(v[a] for v in verts) for a in range(3)]
    maxs=[max(v[a] for v in verts) for a in range(3)]
    ranges=[maxs[a]-mins[a] for a in range(3)]
    order=sorted(range(3),key=lambda a:ranges[a],reverse=True)
    return mins,maxs,ranges,order[1],order[2],order[0]


def gauss(x,c,s): return math.exp(-0.5*((x-c)/s)**2)

def smoothstep(a,b,x):
    if x<=a:return 0.0
    if x>=b:return 1.0
    t=(x-a)/(b-a); return t*t*(3-2*t)


def vertical_remap(q,kind):
    # Shorter torso / cleaner leg length than v9; still natural retro proportions.
    hip=.525; neck=.855
    leg_s=1.055 if kind=='female' else 1.045
    torso_s=.945 if kind=='female' else .955
    head_s=1.045 if kind=='female' else 1.035
    def raw(t):
        if t<=hip:return t*leg_s
        if t<=neck:return hip*leg_s+(t-hip)*torso_s
        return hip*leg_s+(neck-hip)*torso_s+(t-neck)*head_s
    return raw(q)/raw(1.0)


def canonical_body(kind,verts,faces):
    mins,maxs,ranges,width,depth,up=axis_frame(verts)
    H=ranges[up]; cw=(mins[width]+maxs[width])/2; cd=(mins[depth]+maxs[depth])/2
    used=sorted({i for f in faces for i in f}); remap={old:i for i,old in enumerate(used)}
    height=1.64 if kind=='female' else 1.74
    out=[]

    for old in used:
        v=verts[old]; x=(v[width]-cw)/H; y=(v[depth]-cd)/H; q=(v[up]-mins[up])/H
        q2=vertical_remap(q,kind); z=q2*height

        # Slightly larger cranium, less long-necked than v9.
        head=smoothstep(.862,.900,q)
        x*=1+(0.105 if kind=='female' else 0.080)*head
        y*=1+(0.080 if kind=='female' else 0.060)*head
        jaw=gauss(q,.873,.025); x*=1-(.030 if kind=='female' else .018)*jaw
        neck=gauss(q,.832,.030); x*=1-(.105 if kind=='female' else .075)*neck; y*=1-.050*neck

        if kind=='female':
            sx=(1
                -.020*gauss(q,.790,.055)
                -.010*gauss(q,.690,.080)
                -.045*gauss(q,.580,.055)
                +.035*gauss(q,.500,.060)
                +.012*gauss(q,.390,.085))
            sy=1-.005*gauss(q,.690,.08)+.022*gauss(q,.500,.07)
        else:
            sx=(1
                +.042*gauss(q,.790,.060)
                +.018*gauss(q,.700,.085)
                -.030*gauss(q,.580,.065)
                -.008*gauss(q,.500,.070))
            sy=1+.012*gauss(q,.700,.09)
        x*=sx; y*=sy

        # Arms: visibly shorter than v9 and slightly less spindly.
        arm_gate=gauss(q,.680,.170); ax=abs(x); torso_edge=.110 if kind=='female' else .120
        if ax>torso_edge:
            collapsed=torso_edge+(ax-torso_edge)*(.885 if kind=='female' else .900)
            ax=ax*(1-arm_gate)+collapsed*arm_gate; x=math.copysign(ax,x)
            y*=1+.045*arm_gate

        # Hands: aggressively reduce finger spread in all three dimensions.
        hand_gate=gauss(q,.565,.100); hand_start=.245 if kind=='female' else .265
        if abs(x)>hand_start and hand_gate>.06:
            ax=abs(x); ax=hand_start+(ax-hand_start)*.36; x=math.copysign(ax,x)
            y*=1-.40*hand_gate
            zc=.565*height
            z=zc+(z-zc)*(1-.55*hand_gate)

        # Legs: softer thigh-to-knee-to-calf rhythm, less diamond-shaped.
        thigh=gauss(q,.365,.110); calf=gauss(q,.175,.075); knee=gauss(q,.255,.040); ankle=gauss(q,.070,.035)
        if kind=='female':
            x*=1+.020*thigh-.012*knee+.022*calf-.018*ankle
            y*=1+.015*thigh+.012*calf
        else:
            x*=1+.030*thigh-.010*knee+.028*calf-.014*ankle
            y*=1+.020*thigh+.015*calf

        # Feet: short/thick simple wedge rather than long pointed toes.
        foot=1-smoothstep(.035,.090,q)
        if foot>0:
            x*=1+.045*foot
            y*=1-.080*foot
            if q<.018: z=0.0

        out.append((x*height,y*height,z))

    return out,[[remap[i] for i in f] for f in faces]


def mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*rgb,1)
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf: bsdf.inputs['Base Color'].default_value=(*rgb,1); bsdf.inputs['Roughness'].default_value=.90
    return m


def mesh_from_data(name,verts,faces,material):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(material); return ob


def tri_count(obj): obj.data.calc_loop_triangles(); return len(obj.data.loop_triangles)


def lowpoly(obj):
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    tri=obj.modifiers.new('Triangulate','TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=tri.name); before=tri_count(obj)
    dec=obj.modifiers.new('Retro_QEM','DECIMATE'); dec.decimate_type='COLLAPSE'; dec.ratio=max(.001,min(1,TARGET_TRIS/max(before,1))); dec.use_collapse_triangulate=True
    try:
        dec.use_symmetry=True; dec.symmetry_axis='X'
    except Exception: pass
    bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in obj.data.polygons:p.use_smooth=False
    obj.data.update(); return before,tri_count(obj)


def make_character(kind):
    base,faces=parse_obj_body(fetch_text(BASE_URL)); phenotype(kind,base); verts,faces=canonical_body(kind,base,faces)
    color=(.60,.67,.74) if kind=='male' else (.76,.68,.70)
    ob=mesh_from_data(kind.capitalize()+'RetroBaseV10',verts,faces,mat(kind+'Base',color)); before,after=lowpoly(ob); return ob,before,after


def export_character(kind):
    clear_scene(); ob,before,after=make_character(kind); bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True); return before,after


def studio():
    sc=bpy.context.scene; sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.engine='BLENDER_EEVEE'; sc.world.color=(.025,.028,.034)
    try:sc.view_settings.look='AgX - Medium High Contrast'
    except Exception:pass
    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.006)); bpy.context.object.data.materials.append(mat('Floor',(.075,.080,.088)))
    for name,loc,energy,size in [('Key',(-3.2,-4.4,4.2),1050,3.0),('Fill',(3.1,-3.6,2.7),440,2.7),('Rim',(0,3.4,3.5),700,2.1)]:
        ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size; lob=bpy.data.objects.new(name,ld); bpy.context.collection.objects.link(lob); lob.location=loc; lob.rotation_euler=(Vector((0,0,.86))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam); cam.location=(1.75,-6.6,1.58); cam.rotation_euler=(Vector((0,0,.84))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=74; sc.camera=cam


def render_pair():
    clear_scene(); male,bm,am=make_character('male'); female,bf,af=make_character('female'); male.location.x=-.56; female.location.x=.56; male.rotation_euler[2]=math.radians(-1); female.rotation_euler[2]=math.radians(1); studio(); bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-retro-lowpoly.png'); bpy.ops.render.render(write_still=True); return bm,am,bf,af

mb,ma=export_character('male'); fb,fa=export_character('female'); render_pair()
metrics={'style':'retro-lowpoly-basemesh-v10-body-only','source':'Anny/MPFB2 CC0 full body + phenotype targets','extra_character_geometry':False,'hair':False,'face_addons':False,'clothing':False,'target_tris':TARGET_TRIS,'male_tris_before':mb,'male_tris':ma,'female_tris_before':fb,'female_tris':fa,'method':'full basemesh -> restrained retro proportions -> hand/foot cleanup -> symmetric QEM -> flat shading','blender_version':'.'.join(map(str,bpy.app.version))}
with open(os.path.join(OUT_DIR,'metrics.json'),'w') as f:json.dump(metrics,f,indent=2)
print('RETRO_LOWPOLY_V10_METRICS',json.dumps(metrics))
