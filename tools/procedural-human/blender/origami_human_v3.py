import bpy
import math
import json
import os
import sys
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR, exist_ok=True)

# Origami Human v3
# ----------------
# A deliberately abstract humanoid sculpture, not a decimated anatomical mesh.
# Geometry is defined by silhouette landmarks and crease planes.  Blender uses
# native Z-up.  Front is -Y.  Every surface is flat-shaded by design.


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def material(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*rgb, 1)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*rgb, 1)
        bsdf.inputs['Roughness'].default_value = .90
        bsdf.inputs['Metallic'].default_value = 0.0
    return m


def make_mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name+'Mesh')
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = False
    return ob


def artistic_ring(z, width, front, back, skew=0.0, ridge=1.0):
    """Eight vertices with an explicit front ridge and oblique side planes.

    This is intentionally *not* an ellipse.  The ring itself carries the
    origami language: center-front ridge, bevelled flanks, broad side point,
    and a shallow faceted back.
    """
    return [
        (-width*.58 + skew, -front*.88, z),
        (0.0 + skew*.30,    -front*ridge, z),
        ( width*.58 + skew, -front*.88, z),
        ( width + skew,      -front*.08, z),
        ( width*.55 + skew,   back*.82, z),
        (0.0 + skew*.30,      back, z),
        (-width*.55 + skew,   back*.82, z),
        (-width + skew,      -front*.08, z),
    ]


def torso_sculpture(name, rings, mat):
    # rings = (z,width,front,back,skew,ridge)
    verts=[]
    for r in rings:
        verts.extend(artistic_ring(*r))
    sides=8
    faces=[]
    for k in range(len(rings)-1):
        lo=k*sides; hi=(k+1)*sides
        for i in range(sides):
            j=(i+1)%sides
            a,b,c,d=lo+i,lo+j,hi+j,hi+i
            # Alternate diagonals but force a strong V-fold on the front three sectors.
            if i in (0,1,2) and (k+i)%2==0:
                faces.extend(((a,b,c),(a,c,d)))
            elif (k+i)%2:
                faces.extend(((a,b,d),(b,c,d)))
            else:
                faces.extend(((a,b,c),(a,c,d)))
    # caps
    z0=rings[0][0]; z1=rings[-1][0]
    verts.extend(((0,0,z0),(0,0,z1))); c0,c1=len(verts)-2,len(verts)-1
    for i in range(sides):
        j=(i+1)%sides
        faces.append((c0,j,i))
        base=(len(rings)-1)*sides
        faces.append((c1,base+i,base+j))
    return make_mesh(name,verts,faces,mat)


def prism_between(name, p0, p1, r0, r1, mat, sides=4, twist=0.0, squash=.62):
    p0,p1=Vector(p0),Vector(p1)
    axis=(p1-p0).normalized()
    ref=Vector((0,0,1)) if abs(axis.z)<.92 else Vector((0,1,0))
    u=axis.cross(ref).normalized(); v=axis.cross(u).normalized()
    verts=[]
    for p,r,tw in ((p0,r0,0.0),(p1,r1,twist)):
        for i in range(sides):
            a=tw+math.pi/4 + 2*math.pi*i/sides
            q=p + u*(math.cos(a)*r) + v*(math.sin(a)*r*squash)
            verts.append(tuple(q))
    verts.extend((tuple(p0),tuple(p1))); c0,c1=len(verts)-2,len(verts)-1
    faces=[]
    for i in range(sides):
        j=(i+1)%sides
        faces.extend(((c0,j,i),(c1,sides+i,sides+j)))
        a,b,c,d=i,j,sides+j,sides+i
        # one diagonal gives each limb a graphic sequence of facets
        if i%2: faces.extend(((a,b,d),(b,c,d)))
        else: faces.extend(((a,b,c),(a,c,d)))
    return make_mesh(name,verts,faces,mat)


def faceted_head(name, cx, zc, hw, h, d, jaw, mat):
    """Mask-like head with hand-authored planes: crown/brow/cheek/jaw/chin."""
    # Front is negative Y.  Paired vertices create a central front ridge.
    verts=[
        # crown / upper skull
        (cx, -d*.10, zc+h*.52),
        (cx-hw*.62, -d*.32, zc+h*.39), (cx+hw*.62, -d*.32, zc+h*.39),
        (cx-hw*.90,  d*.18, zc+h*.30), (cx+hw*.90,  d*.18, zc+h*.30),
        # brow / temple
        (cx-hw, -d*.64, zc+h*.13), (cx, -d*.86, zc+h*.16), (cx+hw, -d*.64, zc+h*.13),
        (cx-hw*.92, d*.58, zc+h*.10), (cx+hw*.92, d*.58, zc+h*.10),
        # cheek / face ridge
        (cx-hw*.82, -d*.78, zc-h*.08), (cx, -d, zc-h*.03), (cx+hw*.82, -d*.78, zc-h*.08),
        (cx-hw*.72, d*.70, zc-h*.08), (cx+hw*.72, d*.70, zc-h*.08),
        # jaw
        (cx-hw*.56*jaw, -d*.55, zc-h*.31), (cx, -d*.72, zc-h*.34), (cx+hw*.56*jaw, -d*.55, zc-h*.31),
        (cx-hw*.45*jaw, d*.48, zc-h*.29), (cx+hw*.45*jaw, d*.48, zc-h*.29),
        # chin and back skull lower point
        (cx, -d*.40, zc-h*.48), (cx, d*.42, zc-h*.40),
    ]
    # deliberately irregular triangulation, symmetric only where silhouette needs it
    faces=[
        (0,1,2),(0,3,1),(0,2,4),(0,4,3),
        (1,5,6),(1,6,2),(2,6,7),(2,7,4),(1,3,8),(1,8,5),(4,7,9),(4,9,3),(3,9,8),
        (5,10,11),(5,11,6),(6,11,12),(6,12,7),(5,8,13),(5,13,10),(7,12,14),(7,14,9),(8,9,14),(8,14,13),
        (10,15,16),(10,16,11),(11,16,17),(11,17,12),(10,13,18),(10,18,15),(12,17,19),(12,19,14),(13,14,19),(13,19,18),
        (15,20,16),(16,20,17),(15,18,21),(15,21,20),(17,20,21),(17,21,19),(18,19,21),
    ]
    return make_mesh(name,verts,faces,mat)


def diamond_hand(name,c,size,mat,side):
    x,y,z=c; sx=size*.52; sy=size*.34; sz=size
    verts=[(x-sx,y,z),(x,y-sy,z),(x+sx,y,z),(x,y+sy,z),(x,y,z+sz*.38),(x+side*sx*.12,y,z-sz*.62)]
    faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,5,1),(1,5,2),(2,5,3),(3,5,0)]
    return make_mesh(name,verts,faces,mat)


def foot_fold(name,c,w,L,h,mat,side,angle=0.0):
    x,y,z=c
    # 8 verts: heel narrow, toe asymmetric, top is one folded ramp.
    toe_shift=side*w*.08
    verts=[
        (x-w*.28,y+L*.28,z),(x+w*.28,y+L*.28,z),
        (x-w*.52+toe_shift,y-L*.72,z),(x+w*.46+toe_shift,y-L*.72,z),
        (x-w*.24,y+L*.18,z+h),(x+w*.24,y+L*.18,z+h),
        (x-w*.39+toe_shift,y-L*.58,z+h*.28),(x+w*.35+toe_shift,y-L*.58,z+h*.28),
    ]
    faces=[(0,2,3),(0,3,1),(4,5,7),(4,7,6),(0,1,5),(0,5,4),(2,6,7),(2,7,3),(0,4,6),(0,6,2),(1,3,7),(1,7,5)]
    ob=make_mesh(name,verts,faces,mat)
    if angle:
        ob.rotation_euler[2]=angle
    return ob


def P(kind):
    if kind=='female':
        return dict(H=1.66, shoulder=.204, chest=.162, waist=.102, hip=.181, depth=.095, limb=.054,
                    headw=.100, headh=.220, headd=.082, jaw=.86, arm_drop=.0)
    return dict(H=1.80, shoulder=.240, chest=.184, waist=.124, hip=.158, depth=.105, limb=.061,
                headw=.106, headh=.230, headd=.088, jaw=1.08, arm_drop=.0)


def build(kind,xoff,mat,prefix):
    p=P(kind); s=p['H']/1.80
    ankle=.074*s; knee=.495*s; crotch=.855*s; hip=.925*s; waist=1.075*s; ribs=1.255*s; clav=1.405*s; shoulder_z=1.455*s
    neck0=1.468*s; neck1=1.535*s; headc=1.655*s

    # Small lateral/y offsets make the body feel like a posed sculpture, not a T-pose mannequin.
    lean = -.012*s if kind=='male' else .010*s
    torso=torso_sculpture(prefix+'Body',[
        (crotch,p['hip']*.57,p['depth']*.68,p['depth']*.54,0.0,1.03),
        (hip,p['hip'],p['depth']*.88,p['depth']*.76,-lean*.4,1.04),
        (waist,p['waist'],p['depth']*.70,p['depth']*.60,lean,1.10),
        (ribs,p['chest'],p['depth'],p['depth']*.76,lean*.5,1.12),
        (clav,p['shoulder']*.88,p['depth']*.78,p['depth']*.64,-lean*.4,1.18),
        (shoulder_z,p['shoulder'],p['depth']*.60,p['depth']*.54,0.0,1.20),
    ],mat)
    torso.location.x=xoff

    # Neck as a small pentagonal crystal.
    neck=prism_between(prefix+'Neck',(xoff,0,neck0),(xoff,0,neck1),.049*s,.045*s,mat,sides=5,twist=.22,squash=.72)
    faceted_head(prefix+'Head',xoff,headc,p['headw'],p['headh'],p['headd'],p['jaw'],mat)

    shoulder_x=p['shoulder']*.91; hip_x=p['hip']*.46
    # Contrapposto: female right hip carries weight, male subtler asymmetric stance.
    pose_amp=.025*s if kind=='female' else .015*s
    for side in (-1,1):
        tag='L' if side<0 else 'R'
        arm_side_shift = pose_amp * side
        sh=(xoff+side*shoulder_x,0,shoulder_z-.012*s)
        elbow=(xoff+side*(shoulder_x+.030*s), -0.006+arm_side_shift*.25,1.175*s + (pose_amp*.15 if side>0 else -pose_amp*.12))
        wrist=(xoff+side*(shoulder_x+.008*s), -0.016-arm_side_shift*.18,.915*s + (pose_amp*.10 if side>0 else -pose_amp*.08))
        prism_between(prefix+tag+'UpperArm',sh,elbow,p['limb']*1.08,p['limb']*.82,mat,4,.19*side,.60)
        prism_between(prefix+tag+'Forearm',elbow,wrist,p['limb']*.83,p['limb']*.54,mat,4,-.16*side,.58)
        diamond_hand(prefix+tag+'Hand',(wrist[0],wrist[1],wrist[2]-.054*s),.095*s,mat,side)

        # one leg bears weight, the other relaxes a few cm and angles out
        support = 1 if (kind=='female' and side>0) else (-1 if kind=='male' and side<0 else 0)
        hipz=crotch+.028*s + (pose_amp*.55 if support else -pose_amp*.22)
        thigh0=(xoff+side*hip_x,0,hipz)
        knee_x=xoff+side*(hip_x*.92 + (0.010*s if support==0 else 0))
        knee_y=-.006 if support else .010
        kp=(knee_x,knee_y,knee + (pose_amp*.20 if support else -pose_amp*.10))
        ankle_x=xoff+side*(hip_x*.82 + (0.018*s if support==0 else -0.004*s))
        ap=(ankle_x,.012 if support else -.006,ankle)
        prism_between(prefix+tag+'Thigh',thigh0,kp,p['limb']*1.30,p['limb']*.82,mat,5,.14*side,.69)
        prism_between(prefix+tag+'Shin',kp,ap,p['limb']*.80,p['limb']*.50,mat,4,-.13*side,.60)
        foot_fold(prefix+tag+'Foot',(ap[0],-.016,0),p['limb']*1.22,.225*s,.058*s,mat,side,angle=(.035*side if not support else -.015*side))
    return p


def tris(prefix=None):
    n=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or (prefix and not o.name.startswith(prefix)): continue
        n += sum(max(0,len(poly.vertices)-2) for poly in o.data.polygons)
    return n


def export_one(kind):
    clear_scene(); m=material(kind+'Paper',(0.78,0.80,0.77) if kind=='male' else (0.82,0.76,0.72))
    build(kind,0,m,kind+'_'); n=tris(kind+'_')
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and o.name.startswith(kind+'_'): o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    return n


def studio():
    sc=bpy.context.scene
    sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.world.color=(.018,.020,.025); sc.render.engine='BLENDER_EEVEE'
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except Exception: pass
    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.003)); floor=bpy.context.object; floor.data.materials.append(material('Floor',(.055,.058,.060)))
    for name,loc,energy,size in [('Key',(-3.4,-4.2,4.2),1100,3.2),('Fill',(3.0,-2.8,2.5),520,2.5),('Rim',(0,3.0,3.5),900,2.2)]:
        ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size
        ob=bpy.data.objects.new(name,ld); bpy.context.collection.objects.link(ob); ob.location=loc
        ob.rotation_euler=(Vector((0,0,1.0))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam)
    cam.location=(2.9,-5.5,2.15); cam.rotation_euler=(Vector((0,0,0.93))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=68; sc.camera=cam


def render_pair():
    clear_scene(); mm=material('MaleStone',(.54,.61,.63)); fm=material('FemaleStone',(.68,.55,.52))
    build('male',-.56,mm,'male_'); build('female',.56,fm,'female_')
    a,b=tris('male_'),tris('female_'); studio(); bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png'); bpy.ops.render.render(write_still=True)
    return a,b


male=export_one('male'); female=export_one('female'); rm,rf=render_pair()
metrics={'style':'origami-polyhedral-v3','generator':'procedural crease-plane sculpture; no source human mesh','male_tris':male,'female_tris':female,'render_male_tris':rm,'render_female_tris':rf,'blender_version':'.'.join(map(str,bpy.app.version)),'coordinate_system':'Blender native Z-up'}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f: json.dump(metrics,f,indent=2)
print('ORIGAMI_HUMAN_V3_METRICS',json.dumps(metrics))
