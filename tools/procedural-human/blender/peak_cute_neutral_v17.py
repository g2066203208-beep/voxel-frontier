import bpy, bmesh, json, math, os, sys
from mathutils import Vector

OUT_DIR=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/peak-cute-neutral')
os.makedirs(OUT_DIR,exist_ok=True)

# V17: one continuous original PEAK-like neutral body shell.
# No external human mesh / hair / face / clothes / props.
HEIGHT=1.45
SIDES=12
VOXEL_SIZE=0.011
TARGET_TRIS=880

TORSO=[
 (0.555,.145,.108),(0.615,.150,.112),(0.700,.142,.108),(0.790,.130,.101),
 (0.855,.127,.099),(0.925,.139,.105),(0.995,.151,.110),(1.045,.156,.109),
 (1.085,.139,.098),(1.120,.108,.082),(1.145,.073,.064)
]
LEGS=[
 (0.052,.061,.060),(0.105,.053,.054),(0.205,.060,.061),(0.300,.067,.066),
 (0.385,.059,.060),(0.470,.071,.070),(0.555,.080,.075)
]
ARM_RADII=[(.060,.056),(.057,.053),(.052,.049),(.045,.043),(.038,.036)]


def clear_scene():
 bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def append_part(V,F,v,f):
 o=len(V); V.extend(v); F.extend([[o+i for i in p] for p in f])

def cap(c,r,rev=False):
 return [[c,r[(i+1)%len(r)],r[i]] if rev else [c,r[i],r[(i+1)%len(r)]] for i in range(len(r))]

def loft(sec,cx=0,cy=0,sides=SIDES):
 V=[];F=[];R=[]
 for z,rx,ry in sec:
  r=[]
  for i in range(sides):
   a=2*math.pi*i/sides; r.append(len(V)); V.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
  R.append(r)
 for k in range(len(R)-1):
  a,b=R[k],R[k+1]
  for i in range(sides):
   j=(i+1)%sides; F += [[a[i],a[j],b[j]],[a[i],b[j],b[i]]]
 c=len(V);V.append((cx,cy,sec[0][0]));F+=cap(c,R[0],True)
 c=len(V);V.append((cx,cy,sec[-1][0]));F+=cap(c,R[-1],False)
 return V,F

def ellipsoid(center,radii,segments=18,rings_n=8):
 cx,cy,cz=center;rx,ry,rz=radii; V=[(cx,cy,cz+rz)];R=[]
 for r in range(1,rings_n+1):
  th=math.pi*r/(rings_n+1); st,ct=math.sin(th),math.cos(th); ring=[]
  for i in range(segments):
   ph=2*math.pi*i/segments; ring.append(len(V));V.append((cx+rx*st*math.cos(ph),cy+ry*st*math.sin(ph),cz+rz*ct))
  R.append(ring)
 bot=len(V);V.append((cx,cy,cz-rz));F=[]
 for i in range(segments):F.append([0,R[0][i],R[0][(i+1)%segments]])
 for k in range(len(R)-1):
  a,b=R[k],R[k+1]
  for i in range(segments):
   j=(i+1)%segments;F += [[a[i],b[i],b[j]],[a[i],b[j],a[j]]]
 for i in range(segments):F.append([R[-1][i],bot,R[-1][(i+1)%segments]])
 return V,F

def tube(points,radii,sides=SIDES):
 V=[];F=[];R=[];ref=Vector((0,1,0))
 for k,p0 in enumerate(points):
  p=Vector(p0)
  t=(Vector(points[1])-p) if k==0 else (p-Vector(points[k-1]) if k==len(points)-1 else Vector(points[k+1])-Vector(points[k-1]))
  t.normalize();n1=t.cross(ref)
  if n1.length<1e-6:n1=t.cross(Vector((1,0,0)))
  n1.normalize();n2=t.cross(n1).normalized();rx,ry=radii[k];ring=[]
  for i in range(sides):
   a=2*math.pi*i/sides;q=p+n1*(rx*math.cos(a))+n2*(ry*math.sin(a));ring.append(len(V));V.append(tuple(q))
  R.append(ring)
 for k in range(len(R)-1):
  a,b=R[k],R[k+1]
  for i in range(sides):
   j=(i+1)%sides;F += [[a[i],a[j],b[j]],[a[i],b[j],b[i]]]
 c=len(V);V.append(tuple(points[0]));F+=cap(c,R[0],True)
 c=len(V);V.append(tuple(points[-1]));F+=cap(c,R[-1],False)
 return V,F

def scaffold():
 V=[];F=[]
 append_part(V,F,*loft(TORSO))
 # Blank round head, slightly flattened front/back and deeply overlapping the short neck.
 append_part(V,F,*ellipsoid((0,-.004,1.278),(.181,.168,.172),20,9))
 # Small neck blend volume prevents hourglass pinching under the head.
 append_part(V,F,*ellipsoid((0,0,1.125),(.088,.074,.073),14,5))
 for s in (-1,1):
  append_part(V,F,*loft(LEGS,cx=s*.072))
  # Hip blend: makes pelvis-to-thigh transition read as one soft body instead of attached legs.
  append_part(V,F,*ellipsoid((s*.070,0,.555),(.084,.077,.082),12,4))
  append_part(V,F,*ellipsoid((s*.072,-.036,.045),(.064,.086,.048),12,4))
  pts=[(s*.134,0,1.045),(s*.158,-.001,.995),(s*.176,-.003,.920),(s*.185,-.005,.835),(s*.183,-.007,.755)]
  append_part(V,F,*tube(pts,ARM_RADII))
  # Shoulder blend removes the hard shelf between torso and hanging arm.
  append_part(V,F,*ellipsoid((s*.142,0,1.035),(.073,.078,.084),12,4))
  append_part(V,F,*ellipsoid((s*.183,-.009,.713),(.042,.036,.052),12,4))
 return V,F

def mat(name,rgb):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
 b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*rgb,1);b.inputs['Roughness'].default_value=.94
 return m

def raw():
 V,F=scaffold();me=bpy.data.meshes.new('PeakCuteNeutralV17ScaffoldMesh');me.from_pydata(V,[],F);me.update();o=bpy.data.objects.new('PeakCuteNeutralV17',me);bpy.context.collection.objects.link(o);o.data.materials.append(mat('NeutralBody',(.79,.75,.73)));return o

def tris(o):o.data.calc_loop_triangles();return len(o.data.loop_triangles)

def smooth(o,factor,it,name):
 m=o.modifiers.new(name,'SMOOTH');m.factor=factor;m.iterations=it;bpy.ops.object.modifier_apply(modifier=m.name)

def fuse(o):
 bpy.context.view_layer.objects.active=o;o.select_set(True);o.data.remesh_voxel_size=VOXEL_SIZE;o.data.remesh_voxel_adaptivity=0;bpy.ops.object.voxel_remesh();smooth(o,.40,3,'SurfaceRelax')
 before=tris(o);d=o.modifiers.new('LowPoly','DECIMATE');d.decimate_type='COLLAPSE';d.ratio=max(.001,min(1,TARGET_TRIS/max(before,1)));d.use_collapse_triangulate=True
 try:d.use_symmetry=True;d.symmetry_axis='X'
 except Exception:pass
 bpy.ops.object.modifier_apply(modifier=d.name);smooth(o,.08,1,'FinalRelax')
 for p in o.data.polygons:p.use_smooth=True
 o.data.update();return before,tris(o)

def topo(o):
 bm=bmesh.new();bm.from_mesh(o.data);unseen=set(bm.verts);comp=0
 while unseen:
  comp+=1;stack=[unseen.pop()]
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    q=e.other_vert(v)
    if q in unseen:unseen.remove(q);stack.append(q)
 out={'connected_components':comp,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'verts':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces)};bm.free();return out

def make():
 o=raw();before,after=fuse(o);return o,before,after,topo(o)

def studio(mode):
 sc=bpy.context.scene;sc.render.resolution_x=1050;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.engine='BLENDER_EEVEE';sc.world.color=(.026,.029,.035)
 bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,-.002));bpy.context.object.data.materials.append(mat('Floor',(.075,.08,.09)))
 for name,loc,en,size in [('Key',(-3.2,-4.1,4),950,2.7),('Fill',(3,-3,2.5),400,2.4),('Rim',(0,3.2,3.2),650,2.0)]:
  ld=bpy.data.lights.new(name,'AREA');ld.energy=en;ld.shape='DISK';ld.size=size;o=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.72))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);cam.location=(0,-4.8,1.23) if mode=='front' else (1.12,-4.65,1.24);cam.rotation_euler=(Vector((0,0,.72))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cd.lens=78;sc.camera=cam

def render(filename,mode):
 clear_scene();o,_,_,_=make();studio(mode);bpy.context.scene.render.filepath=os.path.join(OUT_DIR,filename);bpy.ops.render.render(write_still=True)

def export():
 clear_scene();o,b,a,t=make();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,'neutral.glb'),export_format='GLB',use_selection=True);return b,a,t

before,after,T=export();render('neutral-preview.png','threequarter');render('neutral-front.png','front')
M={'style':'peak-like-cute-neutral-single-shell-v17','original_geometry':True,'external_character_mesh':False,'neutral_only':True,'male_female_split':False,'hair':False,'face_addons':False,'clothing':False,'props':False,'height_m':HEIGHT,'head_height_m':.344,'visual_head_ratio':round(HEIGHT/.344,3),'tris_before_decimate':before,'tris':after,'single_continuous_shell':T['connected_components']==1 and T['boundary_edges']==0 and T['nonmanifold_edges']==0,**T,'voxel_size_m':VOXEL_SIZE,'target_tris':TARGET_TRIS,'topology_method':'semantic soft volumes -> voxel union -> surface relax -> symmetric low-poly reduction -> one manifold exterior shell','blender_version':'.'.join(map(str,bpy.app.version))}
json.dump(M,open(os.path.join(OUT_DIR,'metrics.json'),'w'),indent=2)
json.dump({'torso':TORSO,'legs':LEGS,'arm_radii':ARM_RADII,'head':{'center':[0,-.004,1.278],'radii':[.181,.168,.172]}},open(os.path.join(OUT_DIR,'section_spec.json'),'w'),indent=2)
print('PEAK_CUTE_NEUTRAL_V17_METRICS',json.dumps(M))
