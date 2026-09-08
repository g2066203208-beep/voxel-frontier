import bpy
import math
import json
import os
import sys
from mathutils import Vector

# Procedural origami / polyhedral humanoid generator.
# No sculpted source mesh is required: the character is built from explicit
# cross-sections, tapered prisms and a tiny faceted head. The same parameter
# schema produces male/female and future body variants.

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass


def mat(name, color, roughness=0.78):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Roughness'].default_value = roughness
    return m


def make_section_body(name, ys, widths, depths, sides=6, twists=None, material=None, offset=(0,0,0)):
    """Create a faceted body from stacked elliptical polygon rings.

    Each ring may rotate independently. That controlled twist prevents the
    result from looking like a cheap cylinder and creates intentional origami
    facets between anatomical landmarks.
    """
    if twists is None:
        twists = [0.0] * len(ys)
    verts = []
    for y, w, d, tw in zip(ys, widths, depths, twists):
        for i in range(sides):
            a = tw + 2.0 * math.pi * i / sides
            verts.append((offset[0] + math.cos(a) * w, offset[1] + y, offset[2] + math.sin(a) * d))
    faces = []
    # caps as triangle fans around implicit ring center vertices
    verts.append((offset[0], offset[1] + ys[0], offset[2]))
    bot_c = len(verts) - 1
    verts.append((offset[0], offset[1] + ys[-1], offset[2]))
    top_c = len(verts) - 1
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((bot_c, j, i))
        a0, a1 = i, j
        b0, b1 = (len(ys)-1)*sides + i, (len(ys)-1)*sides + j
        faces.append((top_c, b0, b1))
    # deliberately triangulated bands; alternating diagonal makes facet rhythm
    for r in range(len(ys)-1):
        base0 = r * sides
        base1 = (r+1) * sides
        for i in range(sides):
            j = (i+1) % sides
            a, b, c, d = base0+i, base0+j, base1+j, base1+i
            if (r + i) % 2 == 0:
                faces.extend(((a,b,c),(a,c,d)))
            else:
                faces.extend(((a,b,d),(b,c,d)))
    mesh = bpy.data.meshes.new(name + 'Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    for p in mesh.polygons:
        p.use_smooth = False
    return obj


def orthonormal_basis(p0, p1):
    axis = (Vector(p1) - Vector(p0)).normalized()
    ref = Vector((0,0,1)) if abs(axis.z) < 0.9 else Vector((1,0,0))
    u = axis.cross(ref).normalized()
    v = axis.cross(u).normalized()
    return axis, u, v


def make_limb(name, p0, p1, r0, r1, sides=5, twist=0.18, material=None):
    p0, p1 = Vector(p0), Vector(p1)
    _, u, v = orthonormal_basis(p0, p1)
    verts = []
    for end, (p, r, tw) in enumerate(((p0,r0,0.0),(p1,r1,twist))):
        for i in range(sides):
            a = tw + 2*math.pi*i/sides
            q = p + u*(math.cos(a)*r) + v*(math.sin(a)*r*0.82)
            verts.append(tuple(q))
    verts.extend((tuple(p0), tuple(p1)))
    c0, c1 = len(verts)-2, len(verts)-1
    faces=[]
    for i in range(sides):
        j=(i+1)%sides
        faces.append((c0,j,i))
        faces.append((c1,sides+i,sides+j))
        a,b,c,d=i,j,sides+j,sides+i
        if i%2: faces.extend(((a,b,d),(b,c,d)))
        else: faces.extend(((a,b,c),(a,c,d)))
    mesh=bpy.data.meshes.new(name+'Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj)
    if material: obj.data.materials.append(material)
    for p in mesh.polygons: p.use_smooth=False
    return obj


def make_ico_head(name, center, radius, scale, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius, location=center)
    obj=bpy.context.object; obj.name=name
    obj.scale=scale
    obj.data.materials.append(material)
    for p in obj.data.polygons: p.use_smooth=False
    return obj


def make_wedge(name, center, size, material):
    cx,cy,cz=center; sx,sy,sz=size
    verts=[
        (cx-sx,cy-sy,cz-sz),(cx+sx,cy-sy,cz-sz),(cx,cy+sy,cz-sz*1.25),
        (cx-sx*0.55,cy-sy*0.35,cz+sz),(cx+sx*0.55,cy-sy*0.35,cz+sz),(cx,cy+sy,cz+sz*1.15)
    ]
    faces=[(0,1,2),(3,5,4),(0,3,4),(0,4,1),(1,4,5),(1,5,2),(2,5,3),(2,3,0)]
    mesh=bpy.data.meshes.new(name+'Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj); obj.data.materials.append(material)
    return obj


def make_foot(name, center, length, width, height, material):
    cx,cy,cz=center
    # asymmetrical 6-vertex prism: heel narrow, toe broader, top slopes down
    verts=[
        (cx-width*.42,cy-height*.5,cz-length*.42),(cx+width*.42,cy-height*.5,cz-length*.42),
        (cx-width*.55,cy-height*.5,cz+length*.58),(cx+width*.55,cy-height*.5,cz+length*.58),
        (cx-width*.34,cy+height*.5,cz-length*.34),(cx+width*.34,cy+height*.5,cz-length*.34),
        (cx-width*.45,cy+height*.08,cz+length*.58),(cx+width*.45,cy+height*.08,cz+length*.58),
    ]
    faces=[(0,2,3),(0,3,1),(4,5,7),(4,7,6),(0,1,5),(0,5,4),(2,6,7),(2,7,3),(0,4,6),(0,6,2),(1,3,7),(1,7,5)]
    mesh=bpy.data.meshes.new(name+'Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj); obj.data.materials.append(material)
    return obj


def params_for(kind):
    if kind == 'female':
        return dict(height=1.66, shoulder=.205, chest=.164, waist=.112, hip=.176, depth=.102,
                    arm=.73, leg=.82, limb=.058, head=.108, neck=.047, jaw=.92)
    return dict(height=1.80, shoulder=.235, chest=.185, waist=.130, hip=.158, depth=.112,
                arm=.79, leg=.89, limb=.065, head=.112, neck=.052, jaw=1.05)


def build_character(kind='male', xoff=0.0, material=None, collection_prefix=''):
    p=params_for(kind); H=p['height']; s=H/1.80
    # landmark heights, expressed once: the whole style is driven by these few ratios
    foot=0.055*s; knee=0.49*s; hip=0.93*s; waist=1.11*s; chest=1.31*s; shoulder=1.48*s; neck=1.55*s; head_c=1.67*s
    # torso rings create an explicit shoulder -> ribcage -> waist -> pelvis rhythm
    torso=make_section_body(collection_prefix+'Torso',
        [hip,waist,chest,shoulder],
        [p['hip'],p['waist'],p['chest'],p['shoulder']],
        [p['depth']*.94,p['depth']*.78,p['depth'],p['depth']*.82],
        sides=6, twists=[0.0,.12,-.08,.14], material=material, offset=(xoff,0,0))
    pelvis=make_section_body(collection_prefix+'Pelvis',
        [hip-.13*s,hip-.03*s,hip+.03*s],
        [p['hip']*.78,p['hip'],p['hip']*.92],
        [p['depth']*.80,p['depth']*.92,p['depth']*.84],
        sides=6, twists=[-.1,.08,-.05], material=material, offset=(xoff,0,0))
    make_section_body(collection_prefix+'Neck',[shoulder,neck],[p['neck']*.9,p['neck']],[p['neck']*.78,p['neck']*.75],sides=5,twists=[0,.22],material=material,offset=(xoff,0,0))
    make_ico_head(collection_prefix+'Head',(xoff,head_c,0),p['head'],(p['jaw'],1.12,0.92),material)
    make_wedge(collection_prefix+'FacePlane',(xoff,head_c-.005,p['head']*.78),(p['head']*.22,p['head']*.18,p['head']*.13),material)

    # limbs use pentagonal sections; elbow/knee direction offsets prevent mannequin stiffness
    shoulder_x=p['shoulder']*.93; hip_x=p['hip']*.55
    for side in (-1,1):
        sx=xoff+side*shoulder_x
        elbow=(xoff+side*(shoulder_x+.055*s), 1.18*s, 0.012*side)
        wrist=(xoff+side*(shoulder_x+.045*s), .89*s, -0.01*side)
        make_limb(collection_prefix+('L' if side<0 else 'R')+'UpperArm',(sx,1.445*s,0),elbow,p['limb']*1.05,p['limb']*.83,5,.24*side,material)
        make_limb(collection_prefix+('L' if side<0 else 'R')+'ForeArm',elbow,wrist,p['limb']*.82,p['limb']*.60,5,-.18*side,material)
        make_section_body(collection_prefix+('L' if side<0 else 'R')+'Hand',[.82*s,.90*s],[p['limb']*.56,p['limb']*.64],[p['limb']*.30,p['limb']*.34],sides=4,twists=[.18,-.12],material=material,offset=(xoff+side*(shoulder_x+.045*s),0,0))

        upper=(xoff+side*hip_x,hip-.10*s,0)
        knee_p=(xoff+side*(hip_x*.90),knee,0.018)
        ankle=(xoff+side*(hip_x*.82),foot+.07*s,-.005)
        make_limb(collection_prefix+('L' if side<0 else 'R')+'Thigh',upper,knee_p,p['limb']*1.32,p['limb']*.86,6,.18*side,material)
        make_limb(collection_prefix+('L' if side<0 else 'R')+'Shin',knee_p,ankle,p['limb']*.82,p['limb']*.54,5,-.15*side,material)
        make_foot(collection_prefix+('L' if side<0 else 'R')+'Foot',(ankle[0],foot,0.055*s),.24*s,.105*s,.075*s,material)
    return p


def tri_count():
    total=0
    for o in bpy.context.scene.objects:
        if o.type=='MESH':
            total += sum(max(0,len(poly.vertices)-2) for poly in o.data.polygons)
    return total


def select_character(prefix):
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and o.name.startswith(prefix): o.select_set(True)


def export_character(kind):
    clear_scene()
    m=mat(kind+'Mat', (0.57,0.64,0.69) if kind=='male' else (0.76,0.57,0.55))
    build_character(kind,0,m,kind+'_')
    count=tri_count()
    for o in bpy.context.scene.objects: o.select_set(o.type=='MESH')
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'), export_format='GLB', use_selection=True)
    return count


def studio_scene():
    scene=bpy.context.scene
    scene.render.resolution_x=1600; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.world.color=(0.025,0.03,0.04)
    try:
        scene.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version >= (4,2,0) else 'BLENDER_EEVEE'
    except Exception:
        pass
    # floor
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0,0,0))
    floor=bpy.context.object; floor.data.materials.append(mat('Floor',(0.055,0.065,0.08),.92))
    # lights
    for name,loc,energy,size in [('Key',(3.5,4.0,4.5),1200,3.0),('Fill',(-3,2.8,2.5),700,2.5),('Rim',(0,3,-3),900,2.0)]:
        data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size
        obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj); obj.location=loc
        direction=Vector((0,1.0,0))-obj.location; obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    # camera
    camd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',camd); bpy.context.collection.objects.link(cam)
    cam.location=(3.6,1.35,4.3); target=Vector((0,0.92,0)); cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); camd.lens=58
    scene.camera=cam


def render_pair():
    clear_scene()
    male_mat=mat('Male',(0.49,0.58,0.66),.83)
    female_mat=mat('Female',(0.73,0.49,0.47),.83)
    build_character('male',-.72,male_mat,'male_')
    build_character('female',.72,female_mat,'female_')
    model_tris=tri_count()
    studio_scene()
    bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png')
    bpy.ops.render.render(write_still=True)
    return model_tris


male_tris=export_character('male')
female_tris=export_character('female')
pair_tris=render_pair()
metrics={
    'style':'origami-polyhedral',
    'generator':'Blender headless procedural geometry',
    'male_tris':male_tris,
    'female_tris':female_tris,
    'pair_tris_before_floor':pair_tris,
    'target_tris_per_character':'250-700',
    'blender_version':'.'.join(map(str,bpy.app.version)),
}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f: json.dump(metrics,f,indent=2)
print('ORIGAMI_HUMAN_METRICS',json.dumps(metrics))
