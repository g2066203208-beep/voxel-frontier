import bpy
import bmesh
import json
import math
import os
import sys
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/peak-cute-neutral')
os.makedirs(OUT_DIR, exist_ok=True)

# PEAK-like cute neutral basemesh v15
# The semantic volumes are only a construction scaffold. Before export they are
# fused through voxel remeshing into ONE continuous manifold shell, then reduced
# to a clean low-poly surface. No hair, facial geometry, clothing or props.

HEIGHT = 1.50
SIDES = 10
VOXEL_SIZE = 0.018
TARGET_TRIS = 720

TORSO = [
    (0.650, 0.138, 0.103),
    (0.720, 0.146, 0.108),
    (0.800, 0.149, 0.110),
    (0.885, 0.150, 0.111),
    (0.965, 0.154, 0.111),
    (1.030, 0.157, 0.108),
    (1.085, 0.141, 0.096),
    (1.135, 0.105, 0.078),
    (1.170, 0.073, 0.062),
]

LEGS = [
    (0.070, 0.055, 0.056),
    (0.135, 0.048, 0.050),
    (0.250, 0.059, 0.061),
    (0.350, 0.055, 0.056),
    (0.470, 0.067, 0.068),
    (0.570, 0.076, 0.073),
    (0.650, 0.084, 0.076),
]

ARM_RADII = [(0.061,0.056),(0.056,0.051),(0.050,0.046),(0.043,0.040),(0.038,0.035)]


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def append_part(V,F,verts,faces):
    off=len(V); V.extend(verts); F.extend([[off+i for i in f] for f in faces])


def cap(center,ring,reverse=False):
    out=[]
    for i in range(len(ring)):
        j=(i+1)%len(ring)
        out.append([center,ring[j],ring[i]] if reverse else [center,ring[i],ring[j]])
    return out


def loft(sections,cx=0.0,cy=0.0,sides=SIDES):
    V=[];F=[];rings=[]
    for z,rx,ry in sections:
        ring=[]
        for i in range(sides):
            a=2*math.pi*i/sides
            ring.append(len(V)); V.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
        rings.append(ring)
    for r in range(len(rings)-1):
        a,b=rings[r],rings[r+1]
        for i in range(sides):
            j=(i+1)%sides
            F.append([a[i],a[j],b[j]]);F.append([a[i],b[j],b[i]])
    c=len(V);V.append((cx,cy,sections[0][0]));F+=cap(c,rings[0],True)
    c=len(V);V.append((cx,cy,sections[-1][0]));F+=cap(c,rings[-1],False)
    return V,F


def ellipsoid(center,radii,segments=14,internal_rings=6):
    cx,cy,cz=center;rx,ry,rz=radii
    V=[(cx,cy,cz+rz)];rings=[]
    for r in range(1,internal_rings+1):
        th=math.pi*r/(internal_rings+1);st,ct=math.sin(th),math.cos(th);ring=[]
        for i in range(segments):
            ph=2*math.pi*i/segments
            ring.append(len(V));V.append((cx+rx*st*math.cos(ph),cy+ry*st*math.sin(ph),cz+rz*ct))
        rings.append(ring)
    bottom=len(V);V.append((cx,cy,cz-rz));F=[]
    for i in range(segments):F.append([0,rings[0][i],rings[0][(i+1)%segments]])
    for r in range(len(rings)-1):
        a,b=rings[r],rings[r+1]
        for i in range(segments):
            j=(i+1)%segments;F.append([a[i],b[i],b[j]]);F.append([a[i],b[j],a[j]])
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
        t.normalize();n1=t.cross(ref)
        if n1.length<1e-6:n1=t.cross(Vector((1,0,0)))
        n1.normalize();n2=t.cross(n1).normalized();rx,ry=radii[k];ring=[]
        for i in range(sides):
            a=2*math.pi*i/sides;q=p+n1*(rx*math.cos(a))+n2*(ry*math.sin(a))
            ring.append(len(V));V.append(tuple(q))
        rings.append(ring)
    for r in range(len(rings)-1):
        a,b=rings[r],rings[r+1]
        for i in range(sides):
            j=(i+1)%sides;F.append([a[i],a[j],b[j]]);F.append([a[i],b[j],b[i]])
    c=len(V);V.append(tuple(points[0]));F+=cap(c,rings[0],True)
    c=len(V);V.append(tuple(points[-1]));F+=cap(c,rings[-1],False)
    return V,F


def scaffold_geometry():
    V=[];F=[]
    append_part(V,F,*loft(TORSO))
    # Head deliberately overlaps neck/upper torso so the union creates one continuous silhouette.
    append_part(V,F,*ellipsoid((0,-0.004,1.315),(0.178,0.166,0.190),14,6))
    for s in (-1,1):
        append_part(V,F,*loft(LEGS,cx=s*0.071))
        # Feet overlap ankle volume.
        append_part(V,F,*ellipsoid((s*0.071,-0.045,0.051),(0.066,0.105,0.052),10,3))
        # Shoulder root starts deep inside torso; arm remains soft and nearly vertical.
        pts=[(s*0.135,0,1.045),(s*0.165,0,0.985),(s*0.185,-0.002,0.900),(s*0.193,-0.004,0.805),(s*0.188,-0.006,0.710)]
        append_part(V,F,*tube(pts,ARM_RADII))
        append_part(V,F,*ellipsoid((s*0.188,-0.009,0.665),(0.046,0.039,0.060),10,3))
    return V,F


def material(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
    b=m.node_tree.nodes.get('Principled BSDF')
    if b:b.inputs['Base Color'].default_value=(*rgb,1);b.inputs['Roughness'].default_value=.92
    return m


def raw_object():
    V,F=scaffold_geometry();me=bpy.data.meshes.new('PeakCuteNeutralV15ScaffoldMesh');me.from_pydata(V,[],F);me.update()
    ob=bpy.data.objects.new('PeakCuteNeutralV15',me);bpy.context.collection.objects.link(ob);ob.data.materials.append(material('NeutralBody',(0.79,0.75,0.73)))
    return ob


def tri_count(ob):ob.data.calc_loop_triangles();return len(ob.data.loop_triangles)


def fuse_to_single_shell(ob):
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    # Blender voxel remesh turns all intersecting construction volumes into one exterior shell.
    ob.data.remesh_voxel_size=VOXEL_SIZE
    ob.data.remesh_voxel_adaptivity=0.0
    bpy.ops.object.voxel_remesh()
    # Reduce to game-low-poly density while retaining the fused silhouette.
    before=tri_count(ob)
    dec=ob.modifiers.new('LowPoly','DECIMATE');dec.decimate_type='COLLAPSE';dec.ratio=max(.001,min(1.0,TARGET_TRIS/max(before,1)));dec.use_collapse_triangulate=True
    try:
        dec.use_symmetry=True;dec.symmetry_axis='X'
    except Exception:pass
    bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in ob.data.polygons:p.use_smooth=True
    ob.data.update()
    return before,tri_count(ob)


def topology_metrics(ob):
    bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
    boundary=sum(1 for e in bm.edges if e.is_boundary)
    nonmanifold=sum(1 for e in bm.edges if not e.is_manifold)
    # Connected components over vertices.
    unseen=set(bm.verts);components=0
    while unseen:
        components+=1;stack=[unseen.pop()]
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                ov=e.other_vert(v)
                if ov in unseen:
                    unseen.remove(ov);stack.append(ov)
    vcount=len(bm.verts);ecount=len(bm.edges);fcount=len(bm.faces);bm.free()
    return {'connected_components':components,'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'verts':vcount,'edges':ecount,'faces':fcount}


def make():
    ob=raw_object();before,after=fuse_to_single_shell(ob);topo=topology_metrics(ob);return ob,before,after,topo


def studio():
    sc=bpy.context.scene;sc.render.resolution_x=1050;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.engine='BLENDER_EEVEE';sc.world.color=(.026,.029,.035)
    bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,-.002));bpy.context.object.data.materials.append(material('Floor',(.075,.08,.09)))
    for name,loc,en,size in [('Key',(-3.2,-4.1,4),950,2.7),('Fill',(3,-3,2.5),400,2.4),('Rim',(0,3.2,3.2),650,2.0)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=en;ld.shape='DISK';ld.size=size;o=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.76))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);cam.location=(1.28,-4.9,1.34);cam.rotation_euler=(Vector((0,0,.76))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cd.lens=78;sc.camera=cam


def export_and_render():
    clear_scene();ob,before,after,topo=make();bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,'neutral.glb'),export_format='GLB',use_selection=True)
    clear_scene();ob,_,_,_=make();ob.rotation_euler[2]=math.radians(3);studio();bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'neutral-preview.png');bpy.ops.render.render(write_still=True)
    return before,after,topo

before,after,topo=export_and_render()
metrics={
    'style':'peak-like-cute-neutral-single-shell-v15','original_geometry':True,'external_character_mesh':False,
    'neutral_only':True,'male_female_split':False,'hair':False,'face_addons':False,'clothing':False,'props':False,
    'height_m':HEIGHT,'head_height_m':0.380,'visual_head_ratio':round(HEIGHT/.380,3),'tris_before_decimate':before,'tris':after,
    'single_continuous_shell':topo['connected_components']==1 and topo['boundary_edges']==0 and topo['nonmanifold_edges']==0,
    **topo,'voxel_size_m':VOXEL_SIZE,'target_tris':TARGET_TRIS,
    'topology_method':'semantic construction volumes -> voxel union/remesh -> one exterior manifold shell -> symmetric low-poly reduction',
    'shading':'smooth normals','blender_version':'.'.join(map(str,bpy.app.version))
}
with open(os.path.join(OUT_DIR,'metrics.json'),'w') as f:json.dump(metrics,f,indent=2)
with open(os.path.join(OUT_DIR,'section_spec.json'),'w') as f:json.dump({'torso':TORSO,'legs':LEGS,'arm_radii':ARM_RADII,'head':{'center':[0,-.004,1.315],'radii':[.178,.166,.190]}},f,indent=2)
print('PEAK_CUTE_NEUTRAL_V15_METRICS',json.dumps(metrics))
