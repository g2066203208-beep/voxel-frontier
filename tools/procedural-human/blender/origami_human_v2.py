import bpy
import math
import json
import os
import sys
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Origami Human v2
# Native Blender Z-up. No source character mesh, no decimation, no sculpting.
# Every plane is generated from a small set of anatomical / silhouette ratios.
# The goal is not anatomical realism: it is a readable human silhouette built
# as a deliberate geometric sculpture.
# -----------------------------------------------------------------------------

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def make_mat(name, rgb, roughness=.86):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*rgb, 1)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = 0.0
    return m


def mesh_object(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + 'Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = False
    return obj


def faceted_loft(name, rings, sides, material, phase=0.0):
    """Triangulated loft through polygon rings.

    rings: [(z, half_width, half_depth, twist), ...]
    A deliberate alternating diagonal creates large readable folded planes.
    """
    verts = []
    for z, wx, dy, twist in rings:
        for i in range(sides):
            a = phase + twist + 2 * math.pi * i / sides
            verts.append((math.cos(a) * wx, math.sin(a) * dy, z))
    faces = []
    for r in range(len(rings) - 1):
        a0, b0 = r * sides, (r + 1) * sides
        for i in range(sides):
            j = (i + 1) % sides
            a, b, c, d = a0+i, a0+j, b0+j, b0+i
            if (i + r) & 1:
                faces.extend(((a,b,d), (b,c,d)))
            else:
                faces.extend(((a,b,c), (a,c,d)))
    verts.append((0,0,rings[0][0])); bot = len(verts)-1
    verts.append((0,0,rings[-1][0])); top = len(verts)-1
    for i in range(sides):
        j=(i+1)%sides
        faces.append((bot,j,i))
        faces.append((top,(len(rings)-1)*sides+i,(len(rings)-1)*sides+j))
    return mesh_object(name, verts, faces, material)


def limb_prism(name, p0, p1, r0, r1, sides, material, squash=.72, twist=.0):
    p0, p1 = Vector(p0), Vector(p1)
    axis = (p1-p0).normalized()
    ref = Vector((0,0,1)) if abs(axis.z) < .90 else Vector((0,1,0))
    u = axis.cross(ref).normalized()
    v = axis.cross(u).normalized()
    verts=[]
    for p,r,tw in ((p0,r0,0),(p1,r1,twist)):
        for i in range(sides):
            a=tw+2*math.pi*i/sides
            q=p + u*(math.cos(a)*r) + v*(math.sin(a)*r*squash)
            verts.append(tuple(q))
    verts.extend((tuple(p0),tuple(p1))); c0,c1=len(verts)-2,len(verts)-1
    faces=[]
    for i in range(sides):
        j=(i+1)%sides
        faces.extend(((c0,j,i),(c1,sides+i,sides+j)))
        a,b,c,d=i,j,sides+j,sides+i
        if i&1: faces.extend(((a,b,d),(b,c,d)))
        else: faces.extend(((a,b,c),(a,c,d)))
    return mesh_object(name,verts,faces,material)


def crystal_head(name, center, hw, depth, height, jaw, material):
    cx,cy,cz=center
    ring_specs=[
        (-.46, hw*.42*jaw, depth*.62),
        (-.30, hw*.72*jaw, depth*.82),
        (-.04, hw,          depth),
        (.18,  hw*.92,      depth*.93),
        (.40,  hw*.72,      depth*.80),
    ]
    verts=[]; sides=6; phase=-math.pi/2
    for zf,w,d in ring_specs:
        for i in range(sides):
            a=phase + 2*math.pi*i/sides + (0.08 if int((zf+.5)*10)%2 else -0.04)
            verts.append((cx+math.cos(a)*w, cy+math.sin(a)*d, cz+zf*height))
    faces=[]
    for r in range(len(ring_specs)-1):
        for i in range(sides):
            j=(i+1)%sides
            a,b,c,d=r*sides+i,r*sides+j,(r+1)*sides+j,(r+1)*sides+i
            if (r+i)&1: faces.extend(((a,b,d),(b,c,d)))
            else: faces.extend(((a,b,c),(a,c,d)))
    verts.extend(((cx,cy,cz-.50*height),(cx,cy,cz+.48*height)))
    bot,top=len(verts)-2,len(verts)-1
    for i in range(sides):
        j=(i+1)%sides
        faces.append((bot,j,i))
        k=(len(ring_specs)-1)*sides
        faces.append((top,k+i,k+j))
    head=mesh_object(name,verts,faces,material)
    nose_z=cz+.02*height
    nverts=[
        (cx-hw*.18,cy-depth*.91,nose_z+height*.12),
        (cx+hw*.18,cy-depth*.91,nose_z+height*.12),
        (cx,cy-depth*1.30,nose_z),
        (cx,cy-depth*.88,nose_z-height*.18),
    ]
    mesh_object(name+'FaceFold',nverts,[(0,1,2),(0,2,3),(1,3,2),(0,3,1)],material)
    return head


def hand_wedge(name, c, sx, sy, sz, material, side=1):
    x,y,z=c
    verts=[(x-sx,y,z),(x,y-sy,z+sz*.15),(x+sx,y,z),(x,y+sy,z),
           (x,y,z+sz),(x+side*sx*.18,y,z-sz*.72)]
    faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,5,1),(1,5,2),(2,5,3),(3,5,0)]
    return mesh_object(name,verts,faces,material)


def foot_wedge(name, c, w, length, h, material):
    x,y,z=c
    verts=[
        (x-w*.34,y+length*.35,z),(x+w*.34,y+length*.35,z),
        (x-w*.54,y-length*.65,z),(x+w*.54,y-length*.65,z),
        (x-w*.28,y+length*.24,z+h),(x+w*.28,y+length*.24,z+h),
        (x-w*.42,y-length*.48,z+h*.38),(x+w*.42,y-length*.48,z+h*.38),
    ]
    faces=[(0,2,3),(0,3,1),(4,5,7),(4,7,6),(0,1,5),(0,5,4),
           (2,6,7),(2,7,3),(0,4,6),(0,6,2),(1,3,7),(1,7,5)]
    return mesh_object(name,verts,faces,material)


def params(kind):
    if kind=='female':
        return dict(H=1.66, shoulder=.205, chest=.167, waist=.108, hip=.178,
                    depth=.103, limb=.057, neck=.044, head_w=.102, head_h=.225,
                    head_d=.088, jaw=.88, stance=.068)
    return dict(H=1.80, shoulder=.238, chest=.188, waist=.129, hip=.160,
                depth=.112, limb=.064, neck=.050, head_w=.108, head_h=.235,
                head_d=.094, jaw=1.08, stance=.072)


def build(kind, xoff, material, prefix):
    p=params(kind); s=p['H']/1.80
    ankle=.075*s; knee=.50*s; crotch=.865*s; hip=.94*s; waist=1.08*s
    ribs=1.25*s; clav=1.40*s; shoulder_z=1.45*s; neck0=1.47*s; neck1=1.54*s
    head_c=1.66*s

    torso=faceted_loft(prefix+'Torso',[
        (crotch,p['hip']*.62,p['depth']*.72,-.02),
        (hip,   p['hip'],    p['depth']*.95,.07),
        (waist, p['waist'],  p['depth']*.72,-.10),
        (ribs,  p['chest'],  p['depth'],.06),
        (clav,  p['shoulder']*.90,p['depth']*.83,-.07),
        (shoulder_z,p['shoulder'],p['depth']*.70,.04),
    ],8,material,phase=-math.pi/2)
    torso.location.x=xoff

    neck_obj=faceted_loft(prefix+'Neck',[(neck0,p['neck']*.92,p['neck']*.75,0),(neck1,p['neck'],p['neck']*.70,.18)],5,material,phase=-math.pi/2)
    neck_obj.location.x=xoff
    crystal_head(prefix+'Head',(xoff,0,head_c),p['head_w'],p['head_d'],p['head_h'],p['jaw'],material)

    shoulder_x=p['shoulder']*.90
    hip_x=p['hip']*.47
    for side in (-1,1):
        tag='L' if side<0 else 'R'
        sh=(xoff+side*shoulder_x, 0, shoulder_z-.015*s)
        elbow=(xoff+side*(shoulder_x+.035*s), .010*side, 1.17*s)
        wrist=(xoff+side*(shoulder_x+.015*s), -.012, .91*s)
        limb_prism(prefix+tag+'UpperArm',sh,elbow,p['limb']*1.08,p['limb']*.86,5,material,.67,.22*side)
        limb_prism(prefix+tag+'Forearm',elbow,wrist,p['limb']*.88,p['limb']*.58,5,material,.66,-.18*side)
        hand_wedge(prefix+tag+'Hand',(wrist[0],wrist[1]-.006,wrist[2]-.055*s),p['limb']*.60,p['limb']*.48,.105*s,material,side)

        thigh0=(xoff+side*hip_x,0,crotch+.025*s)
        kp=(xoff+side*(hip_x*.92),-.010,knee)
        ap=(xoff+side*(hip_x*.84),.012,ankle)
        limb_prism(prefix+tag+'Thigh',thigh0,kp,p['limb']*1.37,p['limb']*.88,6,material,.78,.16*side)
        limb_prism(prefix+tag+'Shin',kp,ap,p['limb']*.90,p['limb']*.55,5,material,.70,-.16*side)
        foot_wedge(prefix+tag+'Foot',(ap[0],-.018,0),p['limb']*1.25,.235*s,.065*s,material)
    return p


def count_tris(prefix=None):
    total=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or (prefix and not o.name.startswith(prefix)):
            continue
        total += sum(max(0,len(poly.vertices)-2) for poly in o.data.polygons)
    return total


def export_one(kind):
    clear_scene()
    material=make_mat(kind+'Mat',(0.28,0.42,0.51) if kind=='male' else (0.62,0.34,0.31))
    build(kind,0,material,kind+'_')
    tris=count_tris(kind+'_')
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and o.name.startswith(kind+'_'):
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    return tris


def add_studio():
    scene=bpy.context.scene
    scene.render.resolution_x=1400; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.world.color=(.018,.022,.030)
    scene.render.engine='BLENDER_EEVEE'
    try:
        scene.view_settings.look='AgX - Medium High Contrast'
    except Exception:
        pass

    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.003))
    floor=bpy.context.object; floor.name='StudioFloor'; floor.data.materials.append(make_mat('Floor',(.045,.052,.065),.96))

    for name,loc,energy,size in [
        ('Key',(-3.2,-4.0,4.2),1050,3.0),
        ('Fill',(3.4,-2.5,2.8),600,2.5),
        ('Rim',(0,3.2,3.4),850,2.1),
    ]:
        ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size
        lo=bpy.data.objects.new(name,ld); bpy.context.collection.objects.link(lo); lo.location=loc
        target=Vector((0,0,1.0)); lo.rotation_euler=(target-Vector(loc)).to_track_quat('-Z','Y').to_euler()

    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam)
    cam.location=(3.15,-5.6,2.25); target=Vector((0,0,0.92)); cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=64
    scene.camera=cam


def render_pair():
    clear_scene()
    mm=make_mat('Male',(0.25,0.43,0.53),.86); fm=make_mat('Female',(0.64,0.34,0.30),.86)
    build('male',-.58,mm,'male_'); build('female',.58,fm,'female_')
    male=count_tris('male_'); female=count_tris('female_')
    add_studio()
    bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png')
    bpy.ops.render.render(write_still=True)
    return male,female


male_tris=export_one('male')
female_tris=export_one('female')
rm,rf=render_pair()
metrics={
    'style':'origami-polyhedral-v2',
    'generator':'pure procedural Blender geometry (no source character mesh)',
    'male_tris':male_tris,
    'female_tris':female_tris,
    'render_male_tris':rm,
    'render_female_tris':rf,
    'target_tris_per_character':'250-700',
    'blender_version':'.'.join(map(str,bpy.app.version)),
    'coordinate_system':'Blender native Z-up',
}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f:
    json.dump(metrics,f,ensure_ascii=False,indent=2)
print('ORIGAMI_HUMAN_V2_METRICS',json.dumps(metrics))
