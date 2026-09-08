import bpy,bmesh,json,math,os,struct,sys
from mathutils import Vector

OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/cartoon-tailor-mannequin')
os.makedirs(OUT,exist_ok=True)
SIDES=12
VOXEL=.0075
TARGET=760

# Neutral cartoon tailor mannequin: waist-up body, head and full arms only.
# No sex-specific chest/hip features, no face, hair or clothing.
TORSO=[
    (0.000,.165,.108), # flat waist cut
    (0.055,.172,.112),
    (0.140,.180,.118),
    (0.230,.190,.124),
    (0.320,.205,.130),
    (0.405,.220,.134),
    (0.470,.238,.135), # shoulder line
    (0.505,.210,.125),
]
HEAD_CENTER=(0,-.004,.735)
HEAD_RADII=(.176,.156,.176)
ARM_RADII=[(.074,.070),(.069,.065),(.061,.058),(.053,.050),(.047,.044),(.044,.041)]


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def mat(name,c):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*c,1)
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*c,1)
    b.inputs['Roughness'].default_value=.92
    return m

def append(V,F,v,f):
    o=len(V);V+=v;F += [[o+i for i in p] for p in f]

def cap(c,ring,rev=False):
    return [[c,ring[(i+1)%len(ring)],ring[i]] if rev else [c,ring[i],ring[(i+1)%len(ring)]] for i in range(len(ring))]

def loft(sec,cx=0,cy=0,sides=SIDES):
    V=[];F=[];R=[]
    for z,rx,ry in sec:
        q=[]
        for i in range(sides):
            a=2*math.pi*i/sides
            q.append(len(V));V.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
        R.append(q)
    for k in range(len(R)-1):
        for i in range(sides):
            j=(i+1)%sides
            F += [[R[k][i],R[k][j],R[k+1][j]],[R[k][i],R[k+1][j],R[k+1][i]]]
    c=len(V);V.append((cx,cy,sec[0][0]));F+=cap(c,R[0],True)
    c=len(V);V.append((cx,cy,sec[-1][0]));F+=cap(c,R[-1])
    return V,F

def ell(c,r,seg=18,nr=8):
    cx,cy,cz=c;rx,ry,rz=r
    V=[(cx,cy,cz+rz)];R=[]
    for k in range(1,nr+1):
        th=math.pi*k/(nr+1);st,ct=math.sin(th),math.cos(th);q=[]
        for i in range(seg):
            ph=2*math.pi*i/seg
            q.append(len(V));V.append((cx+rx*st*math.cos(ph),cy+ry*st*math.sin(ph),cz+rz*ct))
        R.append(q)
    bot=len(V);V.append((cx,cy,cz-rz));F=[]
    for i in range(seg):F.append([0,R[0][i],R[0][(i+1)%seg]])
    for k in range(len(R)-1):
        for i in range(seg):
            j=(i+1)%seg
            F += [[R[k][i],R[k+1][i],R[k+1][j]],[R[k][i],R[k+1][j],R[k][j]]]
    for i in range(seg):F.append([R[-1][i],bot,R[-1][(i+1)%seg]])
    return V,F

def tube(points,radii,sides=SIDES):
    V=[];F=[];R=[];ref=Vector((0,1,0))
    for k,p0 in enumerate(points):
        p=Vector(p0)
        if k==0:t=Vector(points[1])-p
        elif k==len(points)-1:t=p-Vector(points[k-1])
        else:t=Vector(points[k+1])-Vector(points[k-1])
        t.normalize();n1=t.cross(ref)
        if n1.length<1e-6:n1=t.cross(Vector((1,0,0)))
        n1.normalize();n2=t.cross(n1).normalized();rx,ry=radii[k];q=[]
        for i in range(sides):
            a=2*math.pi*i/sides
            x=p+n1*(rx*math.cos(a))+n2*(ry*math.sin(a))
            q.append(len(V));V.append(tuple(x))
        R.append(q)
    for k in range(len(R)-1):
        for i in range(sides):
            j=(i+1)%sides
            F += [[R[k][i],R[k][j],R[k+1][j]],[R[k][i],R[k+1][j],R[k+1][i]]]
    c=len(V);V.append(tuple(points[0]));F+=cap(c,R[0],True)
    c=len(V);V.append(tuple(points[-1]));F+=cap(c,R[-1])
    return V,F

def scaffold():
    V=[];F=[]
    append(V,F,*loft(TORSO))
    # soft shoulder/neck bridge and neutral head
    append(V,F,*ell((0,0,.515),(.165,.120,.085),16,6))
    append(V,F,*ell((0,0,.575),(.092,.083,.115),14,6))
    append(V,F,*ell(HEAD_CENTER,HEAD_RADII,18,8))
    for s in (-1,1):
        # Slight A-pose. Full arm kept for sleeve construction.
        pts=[
            (s*.205,0,.475),
            (s*.260,-.002,.430),
            (s*.315,-.004,.350),
            (s*.355,-.006,.260),
            (s*.382,-.008,.170),
            (s*.395,-.010,.095),
        ]
        append(V,F,*tube(pts,ARM_RADII))
        append(V,F,*ell((s*.213,0,.468),(.090,.078,.085),14,6))
        append(V,F,*ell((s*.398,-.012,.065),(.052,.044,.070),14,6))
    return V,F

def raw():
    V,F=scaffold();me=bpy.data.meshes.new('CartoonTailorMannequinV21Scaffold');me.from_pydata(V,[],F);me.update()
    o=bpy.data.objects.new('CartoonTailorMannequinV21',me);bpy.context.collection.objects.link(o)
    o.data.materials.append(mat('NeutralMannequin',(.78,.75,.72)))
    return o

def tris(o):
    o.data.calc_loop_triangles();return len(o.data.loop_triangles)

def smooth(o,factor,iters,name):
    m=o.modifiers.new(name,'SMOOTH');m.factor=factor;m.iterations=iters;bpy.ops.object.modifier_apply(modifier=m.name)

def fuse(o):
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    o.data.remesh_voxel_size=VOXEL;o.data.remesh_voxel_adaptivity=0;bpy.ops.object.voxel_remesh()
    smooth(o,.32,3,'OrganicRelax')
    before=tris(o)
    d=o.modifiers.new('LowPoly','DECIMATE');d.decimate_type='COLLAPSE';d.ratio=max(.001,min(1,TARGET/max(before,1)));d.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=d.name)
    smooth(o,.035,1,'FinalRelax')
    for p in o.data.polygons:p.use_smooth=True
    o.data.update();return before,tris(o)

def topo(o):
    bm=bmesh.new();bm.from_mesh(o.data);u=set(bm.verts);cc=0
    while u:
        cc+=1;st=[u.pop()]
        while st:
            v=st.pop()
            for e in v.link_edges:
                q=e.other_vert(v)
                if q in u:u.remove(q);st.append(q)
    d={'connected_components':cc,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'verts':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces)}
    bm.free();return d

def sanitize(o):
    o.data.validate(verbose=False,clean_customdata=True);o.data.update();o.data.calc_loop_triangles()
    verts=[tuple(v.co) for v in o.data.vertices];faces=[];seen=set()
    for tri in o.data.loop_triangles:
        f=tuple(int(i) for i in tri.vertices)
        if len(set(f))<3:continue
        key=tuple(sorted(f))
        if key in seen:continue
        seen.add(key);faces.append(f)
    me=bpy.data.meshes.new('CartoonTailorMannequinV21ExportMesh');me.from_pydata(verts,[],faces);me.update(calc_edges=True)
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm,dist=1e-8,edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(me);bm.free();me.validate(verbose=False,clean_customdata=True);me.update(calc_edges=True)
    n=bpy.data.objects.new('CartoonTailorMannequinV21Export',me);bpy.context.collection.objects.link(n)
    n.data.materials.append(mat('NeutralMannequin',(.78,.75,.72)))
    for p in n.data.polygons:p.use_smooth=True
    bpy.data.objects.remove(o,do_unlink=True);return n

def clean_model():
    o=raw();before,_=fuse(o);o=sanitize(o);t=topo(o)
    assert t['connected_components']==1 and t['boundary_edges']==0 and t['nonmanifold_edges']==0,t
    return o,before,tris(o),t

def glb_check(path):
    data=open(path,'rb').read();assert len(data)>1000 and data[:4]==b'glTF';off=12;doc=None
    while off+8<=len(data):
        ln,typ=struct.unpack_from('<II',data,off);off+=8;chunk=data[off:off+ln];off+=ln
        if typ==0x4E4F534A:doc=json.loads(chunk.decode('utf-8').rstrip(' \x00'))
    assert doc and doc.get('meshes');pr=sum(len(m.get('primitives',[])) for m in doc['meshes']);assert pr>0
    return len(data),len(doc['meshes']),pr

def studio(view):
    sc=bpy.context.scene;sc.render.resolution_x=900;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.engine='BLENDER_EEVEE';sc.world.color=(.025,.028,.033)
    bpy.ops.mesh.primitive_plane_add(size=5,location=(0,0,-.005));bpy.context.object.data.materials.append(mat('Floor',(.070,.074,.082)))
    for name,loc,energy,size in [('Key',(-3,-4,3),850,2.4),('Fill',(3,-3,2),350,2.0),('Rim',(0,3,2.7),550,1.8)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=energy;ld.shape='DISK';ld.size=size;x=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(x);x.location=loc;x.rotation_euler=(Vector((0,0,.45))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam)
    if view=='front':cam.location=(0,-3.2,.47)
    elif view=='side':cam.location=(3.2,0,.47)
    else:cam.location=(0,3.2,.47)
    cam.rotation_euler=(Vector((0,0,.46))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cd.lens=72;sc.camera=cam

def render(name,view):
    clear();o,_,_,_=clean_model();studio(view);bpy.context.scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)

def export():
    clear();o,b,a,t=clean_model();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    path=os.path.join(OUT,'neutral-waist-up-mannequin.glb');bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_normals=True)
    gb,gm,gp=glb_check(path);return b,a,t,gb,gm,gp

b,a,T,gb,gm,gp=export()
render('front.png','front');render('side.png','side');render('back.png','back')
M={
 'style':'cartoon-lowpoly-neutral-tailor-mannequin-v21',
 'purpose':'player clothing design / tailoring mannequin',
 'original_geometry':True,'external_character_mesh':False,'neutral_only':True,'male_female_split':False,
 'waist_up_only':True,'head':True,'full_arms':True,'legs':False,
 'hair':False,'face_addons':False,'clothing':False,'props':False,
 'tris_before_decimate':b,'tris':a,
 'single_continuous_shell':T['connected_components']==1 and T['boundary_edges']==0 and T['nonmanifold_edges']==0,
 **T,'target_tris':TARGET,'voxel_size_m':VOXEL,
 'glb_bytes':gb,'glb_meshes':gm,'glb_primitives':gp,'glb_valid_mesh':gp>0,
 'pose':'slight A-pose for sleeve construction','blender_version':'.'.join(map(str,bpy.app.version))
}
json.dump(M,open(os.path.join(OUT,'metrics.json'),'w'),indent=2)
json.dump({'torso':TORSO,'arm_radii':ARM_RADII,'head':{'center':HEAD_CENTER,'radii':HEAD_RADII}},open(os.path.join(OUT,'section_spec.json'),'w'),indent=2)
print('TAILOR_MANNEQUIN_V21_METRICS',json.dumps(M))
