import bpy,bmesh,json,math,os,sys
from mathutils import Vector
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/peak-cute-neutral');os.makedirs(OUT,exist_ok=True)
HEIGHT=1.43;SIDES=14;VOXEL=.010;TARGET=960
TORSO=[(.575,.148,.108),(.640,.150,.111),(.720,.145,.108),(.805,.136,.103),(.865,.132,.101),(.930,.141,.106),(.995,.151,.110),(1.045,.156,.110),(1.080,.145,.103),(1.108,.112,.086)]
LEGS=[(.050,.062,.060),(.105,.055,.055),(.205,.061,.061),(.300,.067,.066),(.385,.060,.060),(.480,.071,.069),(.575,.079,.074)]
ARMS=[(.063,.058),(.059,.055),(.054,.050),(.048,.045),(.042,.040)]

def clear():bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def ap(V,F,v,f):o=len(V);V+=v;F += [[o+i for i in p] for p in f]
def cap(c,r,rev=False):return [[c,r[(i+1)%len(r)],r[i]] if rev else [c,r[i],r[(i+1)%len(r)]] for i in range(len(r))]
def loft(sec,cx=0,cy=0,sides=SIDES):
 V=[];F=[];R=[]
 for z,rx,ry in sec:
  q=[]
  for i in range(sides):a=2*math.pi*i/sides;q.append(len(V));V.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
  R.append(q)
 for k in range(len(R)-1):
  for i in range(sides):j=(i+1)%sides;F += [[R[k][i],R[k][j],R[k+1][j]],[R[k][i],R[k+1][j],R[k+1][i]]]
 c=len(V);V.append((cx,cy,sec[0][0]));F+=cap(c,R[0],True);c=len(V);V.append((cx,cy,sec[-1][0]));F+=cap(c,R[-1]);return V,F
def ell(c,r,seg=20,nr=9):
 cx,cy,cz=c;rx,ry,rz=r;V=[(cx,cy,cz+rz)];R=[]
 for k in range(1,nr+1):
  th=math.pi*k/(nr+1);st,ct=math.sin(th),math.cos(th);q=[]
  for i in range(seg):ph=2*math.pi*i/seg;q.append(len(V));V.append((cx+rx*st*math.cos(ph),cy+ry*st*math.sin(ph),cz+rz*ct))
  R.append(q)
 bot=len(V);V.append((cx,cy,cz-rz));F=[]
 for i in range(seg):F.append([0,R[0][i],R[0][(i+1)%seg]])
 for k in range(len(R)-1):
  for i in range(seg):j=(i+1)%seg;F += [[R[k][i],R[k+1][i],R[k+1][j]],[R[k][i],R[k+1][j],R[k][j]]]
 for i in range(seg):F.append([R[-1][i],bot,R[-1][(i+1)%seg]])
 return V,F
def tube(points,radii,sides=SIDES):
 V=[];F=[];R=[];ref=Vector((0,1,0))
 for k,p0 in enumerate(points):
  p=Vector(p0);t=(Vector(points[1])-p) if k==0 else (p-Vector(points[k-1]) if k==len(points)-1 else Vector(points[k+1])-Vector(points[k-1]));t.normalize();n1=t.cross(ref)
  if n1.length<1e-6:n1=t.cross(Vector((1,0,0)))
  n1.normalize();n2=t.cross(n1).normalized();rx,ry=radii[k];q=[]
  for i in range(sides):a=2*math.pi*i/sides;x=p+n1*(rx*math.cos(a))+n2*(ry*math.sin(a));q.append(len(V));V.append(tuple(x))
  R.append(q)
 for k in range(len(R)-1):
  for i in range(sides):j=(i+1)%sides;F += [[R[k][i],R[k][j],R[k+1][j]],[R[k][i],R[k+1][j],R[k+1][i]]]
 c=len(V);V.append(tuple(points[0]));F+=cap(c,R[0],True);c=len(V);V.append(tuple(points[-1]));F+=cap(c,R[-1]);return V,F
def scaffold():
 V=[];F=[];ap(V,F,*loft(TORSO));ap(V,F,*ell((0,-.004,1.255),(.184,.171,.178),22,10));ap(V,F,*ell((0,0,1.102),(.105,.086,.085),16,6))
 for s in (-1,1):
  ap(V,F,*loft(LEGS,cx=s*.073));ap(V,F,*ell((s*.071,0,.575),(.085,.078,.086),14,5));ap(V,F,*ell((s*.073,-.034,.044),(.064,.084,.048),14,5))
  pts=[(s*.128,0,1.030),(s*.151,-.001,.985),(s*.170,-.003,.915),(s*.181,-.005,.832),(s*.181,-.007,.752)]
  ap(V,F,*tube(pts,ARMS));ap(V,F,*ell((s*.130,0,1.026),(.097,.086,.101),16,6));ap(V,F,*ell((s*.181,-.009,.708),(.045,.039,.057),14,5))
 return V,F
def mat(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.94;return m
def raw():
 V,F=scaffold();me=bpy.data.meshes.new('PeakCuteNeutralV18Scaffold');me.from_pydata(V,[],F);me.update();o=bpy.data.objects.new('PeakCuteNeutralV18',me);bpy.context.collection.objects.link(o);o.data.materials.append(mat('NeutralBody',(.79,.75,.73)));return o
def tr(o):o.data.calc_loop_triangles();return len(o.data.loop_triangles)
def sm(o,f,it,n):m=o.modifiers.new(n,'SMOOTH');m.factor=f;m.iterations=it;bpy.ops.object.modifier_apply(modifier=m.name)
def fuse(o):
 bpy.context.view_layer.objects.active=o;o.select_set(True);o.data.remesh_voxel_size=VOXEL;o.data.remesh_voxel_adaptivity=0;bpy.ops.object.voxel_remesh();sm(o,.43,4,'OrganicRelax');before=tr(o);d=o.modifiers.new('LowPoly','DECIMATE');d.decimate_type='COLLAPSE';d.ratio=max(.001,min(1,TARGET/max(before,1)));d.use_collapse_triangulate=True
 try:d.use_symmetry=True;d.symmetry_axis='X'
 except:pass
 bpy.ops.object.modifier_apply(modifier=d.name);sm(o,.07,1,'FinalRelax');[setattr(p,'use_smooth',True) for p in o.data.polygons];o.data.update();return before,tr(o)
def topo(o):
 bm=bmesh.new();bm.from_mesh(o.data);u=set(bm.verts);cc=0
 while u:
  cc+=1;st=[u.pop()]
  while st:
   v=st.pop()
   for e in v.link_edges:
    q=e.other_vert(v)
    if q in u:u.remove(q);st.append(q)
 d={'connected_components':cc,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'verts':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces)};bm.free();return d
def make():o=raw();b,a=fuse(o);return o,b,a,topo(o)
def studio(front=False):
 sc=bpy.context.scene;sc.render.resolution_x=1050;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.engine='BLENDER_EEVEE';sc.world.color=(.026,.029,.035);bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,-.002));bpy.context.object.data.materials.append(mat('Floor',(.075,.08,.09)))
 for n,l,e,z in [('Key',(-3.2,-4.1,4),950,2.7),('Fill',(3,-3,2.5),400,2.4),('Rim',(0,3.2,3.2),650,2.0)]:ld=bpy.data.lights.new(n,'AREA');ld.energy=e;ld.shape='DISK';ld.size=z;x=bpy.data.objects.new(n,ld);bpy.context.collection.objects.link(x);x.location=l;x.rotation_euler=(Vector((0,0,.71))-Vector(l)).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);cam.location=(0,-4.7,1.18) if front else (1.08,-4.55,1.20);cam.rotation_euler=(Vector((0,0,.71))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cd.lens=78;sc.camera=cam
def render(name,front=False):clear();o,_,_,_=make();studio(front);bpy.context.scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)
def export():clear();o,b,a,t=make();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'neutral.glb'),export_format='GLB',use_selection=True);return b,a,t
b,a,T=export();render('neutral-preview.png');render('neutral-front.png',True)
M={'style':'peak-like-cute-neutral-single-shell-v18','original_geometry':True,'external_character_mesh':False,'neutral_only':True,'male_female_split':False,'hair':False,'face_addons':False,'clothing':False,'props':False,'height_m':HEIGHT,'head_height_m':.356,'visual_head_ratio':round(HEIGHT/.356,3),'tris_before_decimate':b,'tris':a,'single_continuous_shell':T['connected_components']==1 and T['boundary_edges']==0 and T['nonmanifold_edges']==0,**T,'voxel_size_m':VOXEL,'target_tris':TARGET,'topology_method':'soft semantic scaffold -> high-res voxel union -> organic surface relax -> symmetric low-poly reduction -> one manifold exterior shell','blender_version':'.'.join(map(str,bpy.app.version))};json.dump(M,open(os.path.join(OUT,'metrics.json'),'w'),indent=2);json.dump({'torso':TORSO,'legs':LEGS,'arm_radii':ARMS,'head':{'center':[0,-.004,1.255],'radii':[.184,.171,.178]}},open(os.path.join(OUT,'section_spec.json'),'w'),indent=2);print('PEAK_CUTE_NEUTRAL_V18_METRICS',json.dumps(M))