import bpy
import json
import math
import os
import sys
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/peak-cute-neutral')
os.makedirs(OUT_DIR, exist_ok=True)

# PEAK-like cute neutral basemesh v14
# Original procedural geometry. No external character mesh, no hair/face/clothes.
# Goal: soft simple cute silhouette rather than realistic anatomy or origami facets.

HEIGHT = 1.52
SIDES = 8

TORSO = [
    (0.665, 0.132, 0.098),
    (0.750, 0.145, 0.105),
    (0.845, 0.143, 0.104),
    (0.930, 0.145, 0.105),
    (1.010, 0.153, 0.108),
    (1.070, 0.158, 0.105),
    (1.125, 0.130, 0.088),
    (1.175, 0.068, 0.060),
]

LEGS = [
    (0.075, 0.052, 0.054),
    (0.150, 0.045, 0.047),
    (0.300, 0.058, 0.060),
    (0.405, 0.050, 0.052),
    (0.535, 0.066, 0.066),
    (0.665, 0.080, 0.073),
]

ARM_RADII = [(0.055, 0.051), (0.050, 0.046), (0.043, 0.040), (0.035, 0.032)]


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def append_part(V, F, verts, faces):
    off = len(V)
    V.extend(verts)
    F.extend([[off + i for i in f] for f in faces])


def cap(center, ring, reverse=False):
    out=[]
    for i in range(len(ring)):
        j=(i+1)%len(ring)
        out.append([center, ring[j], ring[i]] if reverse else [center, ring[i], ring[j]])
    return out


def loft(sections, cx=0.0, cy=0.0, sides=SIDES):
    V=[]; F=[]; rings=[]
    for z,rx,ry in sections:
        ring=[]
        for i in range(sides):
            a=2*math.pi*i/sides
            ring.append(len(V)); V.append((cx+rx*math.cos(a), cy+ry*math.sin(a), z))
        rings.append(ring)
    for r in range(len(rings)-1):
        a,b=rings[r],rings[r+1]
        for i in range(sides):
            j=(i+1)%sides
            F.append([a[i],a[j],b[j]]); F.append([a[i],b[j],b[i]])
    c=len(V); V.append((cx,cy,sections[0][0])); F+=cap(c,rings[0],True)
    c=len(V); V.append((cx,cy,sections[-1][0])); F+=cap(c,rings[-1],False)
    return V,F


def ellipsoid(center,radii,segments=12,internal_rings=5):
    cx,cy,cz=center; rx,ry,rz=radii
    V=[(cx,cy,cz+rz)]; rings=[]
    for r in range(1,internal_rings+1):
        th=math.pi*r/(internal_rings+1); st,ct=math.sin(th),math.cos(th)
        ring=[]
        for i in range(segments):
            ph=2*math.pi*i/segments
            ring.append(len(V)); V.append((cx+rx*st*math.cos(ph),cy+ry*st*math.sin(ph),cz+rz*ct))
        rings.append(ring)
    bottom=len(V); V.append((cx,cy,cz-rz)); F=[]
    for i in range(segments):F.append([0,rings[0][i],rings[0][(i+1)%segments]])
    for r in range(len(rings)-1):
        a,b=rings[r],rings[r+1]
        for i in range(segments):
            j=(i+1)%segments
            F.append([a[i],b[i],b[j]]); F.append([a[i],b[j],a[j]])
    last=rings[-1]
    for i in range(segments):F.append([last[i],bottom,last[(i+1)%segments]])
    return V,F


def tube(points,radii,sides=SIDES):
    V=[];F=[];rings=[];ref=Vector((0,1,0))
    for k,p0 in enumerate(points):
        p=Vector(p0)
        if k==0:t=Vector(points[1])-p
        elif k==len(points)-1:t=p-Vector(points[k-1])
        else:t=Vector(points[k+1])-Vector(points[k-1])
        t.normalize(); n1=t.cross(ref)
        if n1.length<1e-6:n1=t.cross(Vector((1,0,0)))
        n1.normalize(); n2=t.cross(n1).normalized(); rx,ry=radii[k]; ring=[]
        for i in range(sides):
            a=2*math.pi*i/sides; q=p+n1*(rx*math.cos(a))+n2*(ry*math.sin(a))
            ring.append(len(V)); V.append(tuple(q))
        rings.append(ring)
    for r in range(len(rings)-1):
        a,b=rings[r],rings[r+1]
        for i in range(sides):
            j=(i+1)%sides
            F.append([a[i],a[j],b[j]]);F.append([a[i],b[j],b[i]])
    c=len(V);V.append(tuple(points[0]));F+=cap(c,rings[0],True)
    c=len(V);V.append(tuple(points[-1]));F+=cap(c,rings[-1],False)
    return V,F


def build():
    V=[];F=[]
    append_part(V,F,*loft(TORSO))

    # Larger round blank head, deliberately overlapping the short neck so there is
    # no floating gap. Slightly wider than deep, still neutral and faceless.
    append_part(V,F,*ellipsoid((0,-0.005,1.345),(0.174,0.162,0.185),12,5))

    for s in (-1,1):
        append_part(V,F,*loft(LEGS,cx=s*0.070))
        # Rounded simple foot rather than a box/wedge.
        append_part(V,F,*ellipsoid((s*0.070,-0.040,0.050),(0.064,0.105,0.050),8,2))

        # Arms begin inside the shoulder volume, then hang almost vertically.
        pts=[(s*0.145,0,1.055),(s*0.178,0,0.945),(s*0.190,-0.002,0.820),(s*0.183,-0.004,0.705)]
        append_part(V,F,*tube(pts,ARM_RADII))
        # Small rounded mitten-like hand; no fingers/facial/detail geometry.
        append_part(V,F,*ellipsoid((s*0.183,-0.008,0.655),(0.043,0.036,0.055),8,2))
    return V,F


def body_mat():
    m=bpy.data.materials.get('NeutralBody') or bpy.data.materials.new('NeutralBody');m.use_nodes=True
    m.diffuse_color=(0.79,0.75,0.73,1)
    b=m.node_tree.nodes.get('Principled BSDF')
    if b:b.inputs['Base Color'].default_value=(0.79,0.75,0.73,1);b.inputs['Roughness'].default_value=.92
    return m


def make():
    V,F=build();me=bpy.data.meshes.new('PeakCuteNeutralV14Mesh');me.from_pydata(V,[],F);me.update()
    ob=bpy.data.objects.new('PeakCuteNeutralV14',me);bpy.context.collection.objects.link(ob);ob.data.materials.append(body_mat())
    for p in ob.data.polygons:p.use_smooth=True
    return ob


def tris(ob):ob.data.calc_loop_triangles();return len(ob.data.loop_triangles)


def studio():
    sc=bpy.context.scene;sc.render.resolution_x=1050;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.engine='BLENDER_EEVEE';sc.world.color=(.026,.029,.035)
    bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,-.002));fm=bpy.data.materials.new('Floor');fm.diffuse_color=(.075,.08,.09,1);bpy.context.object.data.materials.append(fm)
    for name,loc,en,size in [('Key',(-3.2,-4.1,4),950,2.7),('Fill',(3,-3,2.5),400,2.4),('Rim',(0,3.2,3.2),650,2.0)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=en;ld.shape='DISK';ld.size=size;o=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.78))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);cam.location=(1.30,-5.0,1.38);cam.rotation_euler=(Vector((0,0,.77))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cd.lens=78;sc.camera=cam


def export_and_render():
    clear_scene();ob=make();n=tris(ob);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,'neutral.glb'),export_format='GLB',use_selection=True)
    clear_scene();ob=make();ob.rotation_euler[2]=math.radians(3);studio();bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'neutral-preview.png');bpy.ops.render.render(write_still=True);return n

n=export_and_render()
metrics={'style':'peak-like-cute-neutral-basemesh-v14','original_geometry':True,'external_character_mesh':False,'neutral_only':True,'male_female_split':False,'hair':False,'face_addons':False,'clothing':False,'props':False,'height_m':HEIGHT,'head_height_m':0.370,'visual_head_ratio':round(HEIGHT/.370,3),'tris':n,'torso_section_count':len(TORSO),'leg_section_count':len(LEGS),'arm_section_count':len(ARM_RADII),'ring_sides':SIDES,'topology_method':'direct semantic lofts + rounded low-poly primitive volumes; no adult source mesh, no decimation','shading':'smooth normals','blender_version':'.'.join(map(str,bpy.app.version))}
with open(os.path.join(OUT_DIR,'metrics.json'),'w') as f:json.dump(metrics,f,indent=2)
with open(os.path.join(OUT_DIR,'section_spec.json'),'w') as f:json.dump({'torso':TORSO,'legs':LEGS,'arm_radii':ARM_RADII,'head':{'center':[0,-.005,1.345],'radii':[.174,.162,.185]}},f,indent=2)
print('PEAK_CUTE_NEUTRAL_V14_METRICS',json.dumps(metrics))
