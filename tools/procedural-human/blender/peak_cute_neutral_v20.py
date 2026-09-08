import bpy,bmesh,json,math,os,struct,sys
from mathutils import Vector
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/peak-cute-neutral');os.makedirs(OUT,exist_ok=True)
HEIGHT=1.32;SIDES=14;VOXEL=.0095;TARGET=920
TORSO=[(.480,.150,.110),(.530,.155,.115),(.600,.150,.112),(.680,.142,.108),(.750,.137,.105),(.820,.145,.110),(.870,.155,.114),(.910,.160,.112),(.940,.140,.100)]
LEGS=[(.045,.067,.065),(.095,.060,.060),(.180,.068,.067),(.270,.074,.072),(.350,.066,.066),(.420,.078,.075),(.490,.086,.080)]
ARMS=[(.075,.070),(.070,.065),(.063,.059),(.055,.052),(.048,.045)]
HEAD_CENTER=(0,-.004,1.115);HEAD_RADII=(.205,.190,.205)

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
def ell(c,r,seg=22,nr=10):
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
 V=[];F=[];ap(V,F,*loft(TORSO));ap(V,F,*ell(HEAD_CENTER,HEAD_RADII));ap(V,F,*ell((0,0,.925),(.115,.095,.083),16,6));ap(V,F,*ell((0,0,.500),(.150,.105,.100),18,7))
 for s in (-1,1):
  ap(V,F,*loft(LEGS,cx=s*.076));ap(V,F,*ell((s*.074,0,.485),(.091,.083,.090),16,6));ap(V,F,*ell((s*.076,-.032,.045),(.070,.090,.050),16,6))
  pts=[(s*.128,0,.895),(s*.155,-.001,.835),(s*.175,-.003,.755),(s*.188,-.005,.670),(s*.190,-.007,.585)]
  ap(V,F,*tube(pts,ARMS));ap(V,F,*ell((s*.135,0,.890),(.110,.095,.110),18,7));ap(V,F,*ell((s*.190,-.010,.540),(.052,.046,.065),16,6))
 return V,F
def mat(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.94;return m
def raw():
 V,F=scaffold();me=bpy.data.meshes.new('CuteNeutralV20Scaffold');me.from_pydata(V,[],F);me.update();o=bpy.data.objects.new('CuteNeutralV20',me);bpy.context.collection.objects.link(o);o.data.materials.append(mat('NeutralBody',(.79,.75,.73)));return o
def tr(o):o.data.calc_loop_triangles();return len(o.data.loop_triangles)
def sm(o,f,it,n):m=o.modifiers.new(n,'SMOOTH');m.factor=f;m.iterations=it;bpy.ops.object.modifier_apply(modifier=m.name)
def fuse(o):
 bpy.context.view_layer.objects.active=o;o.select_set(True);o.data.remesh_voxel_size=VOXEL;o.data.remesh_voxel_adaptivity=0;bpy.ops.object.voxel_remesh();sm(o,.42,4,'OrganicRelax');before=tr(o);d=o.modifiers.new('LowPoly','DECIMATE');d.decimate_type='COLLAPSE';d.ratio=max(.001,min(1,TARGET/max(before,1)));d.use_collapse_triangulate=True
 # Symmetry-aware collapse can duplicate seam triangles in Blender 4.0.2.
 # The scaffold and voxel field are already symmetric, so use ordinary QEM collapse.
 try:d.use_symmetry=False
 except:pass
 bpy.ops.object.modifier_apply(modifier=d.name);sm(o,.06,1,'FinalRelax');[setattr(p,'use_smooth',True) for p in o.data.polygons];o.data.update();return before,tr(o)
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
def sanitize(o):
 # Work from topology, not loop/custom-normal data. Weld coincident vertices first,
 # triangulate once, remove duplicate geometric faces, then recalculate normals.
 bm=bmesh.new();bm.from_mesh(o.data)
 input_faces=len(bm.faces);input_verts=len(bm.verts)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
 if bm.edges:bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
 if bm.faces:bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
 bm.verts.ensure_lookup_table();bm.verts.index_update();bm.faces.ensure_lookup_table()
 seen=set();dups=[];deg=[]
 for f in list(bm.faces):
  ids=tuple(v.index for v in f.verts)
  if len(set(ids))<3:
   deg.append(f);continue
  key=tuple(sorted(ids))
  if key in seen:dups.append(f)
  else:seen.add(key)
 if deg:bmesh.ops.delete(bm,geom=deg,context='FACES')
 if dups:bmesh.ops.delete(bm,geom=dups,context='FACES')
 if bm.faces:bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bm.normal_update()
 me=bpy.data.meshes.new('CuteNeutralV20ExportMesh');bm.to_mesh(me);bm.free();me.validate(verbose=True,clean_customdata=True);me.update(calc_edges=True)
 n=bpy.data.objects.new('CuteNeutralV20Export',me);bpy.context.collection.objects.link(n);n.data.materials.append(mat('NeutralBody',(.79,.75,.73)));[setattr(p,'use_smooth',True) for p in n.data.polygons]
 print('SANITIZE_TOPOLOGY',json.dumps({'input_faces':input_faces,'input_verts':input_verts,'output_faces':len(me.polygons),'output_verts':len(me.vertices),'duplicates_removed':len(dups),'degenerate_removed':len(deg)}))
 bpy.data.objects.remove(o,do_unlink=True);return n
def glb_check(path):
 data=open(path,'rb').read();assert len(data)>1000 and data[:4]==b'glTF';off=12;doc=None
 while off+8<=len(data):
  ln,typ=struct.unpack_from('<II',data,off);off+=8;chunk=data[off:off+ln];off+=ln
  if typ==0x4E4F534A:doc=json.loads(chunk.decode('utf-8').rstrip(' \x00'))
 assert doc and doc.get('meshes');pr=sum(len(m.get('primitives',[])) for m in doc['meshes']);assert pr>0;return len(data),len(doc['meshes']),pr
def clean_model():
 o,b,_,_=make();o=sanitize(o);t=topo(o);assert t['connected_components']==1 and t['boundary_edges']==0 and t['nonmanifold_edges']==0,t;return o,b,tr(o),t
def studio(front=False):
 sc=bpy.context.scene;sc.render.resolution_x=1050;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.engine='BLENDER_EEVEE';sc.world.color=(.026,.029,.035);bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,-.002));bpy.context.object.data.materials.append(mat('Floor',(.075,.08,.09)))
 for n,l,e,z in [('Key',(-3.2,-4.1,4),950,2.7),('Fill',(3,-3,2.5),400,2.4),('Rim',(0,3.2,3.2),650,2.0)]:ld=bpy.data.lights.new(n,'AREA');ld.energy=e;ld.shape='DISK';ld.size=z;x=bpy.data.objects.new(n,ld);bpy.context.collection.objects.link(x);x.location=l;x.rotation_euler=(Vector((0,0,.65))-Vector(l)).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);cam.location=(0,-4.4,1.08) if front else (1.03,-4.3,1.10);cam.rotation_euler=(Vector((0,0,.65))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cd.lens=78;sc.camera=cam
def render(name,front=False):clear();o,_,_,_=clean_model();studio(front);bpy.context.scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)
def export():
 clear();o,b,a,t=clean_model();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;path=os.path.join(OUT,'neutral.glb');bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_normals=True);gb,gm,gp=glb_check(path);return b,a,t,gb,gm,gp
b,a,T,gb,gm,gp=export();render('neutral-preview.png');render('neutral-front.png',True)
M={'style':'compact-cute-neutral-single-shell-v20','inspiration':'simple round scout-like proportions; original geometry','original_geometry':True,'external_character_mesh':False,'neutral_only':True,'male_female_split':False,'hair':False,'face_addons':False,'clothing':False,'props':False,'height_m':HEIGHT,'head_height_m':.410,'visual_head_ratio':round(HEIGHT/.410,3),'tris_before_decimate':b,'tris':a,'single_continuous_shell':T['connected_components']==1 and T['boundary_edges']==0 and T['nonmanifold_edges']==0,**T,'voxel_size_m':VOXEL,'target_tris':TARGET,'glb_bytes':gb,'glb_meshes':gm,'glb_primitives':gp,'glb_valid_mesh':gp>0,'topology_method':'semantic soft volumes -> one voxel-unioned shell -> relax -> ordinary QEM low-poly -> welded/triangulated clean mesh -> validated GLB','blender_version':'.'.join(map(str,bpy.app.version))};json.dump(M,open(os.path.join(OUT,'metrics.json'),'w'),indent=2);json.dump({'torso':TORSO,'legs':LEGS,'arm_radii':ARMS,'head':{'center':HEAD_CENTER,'radii':HEAD_RADII}},open(os.path.join(OUT,'section_spec.json'),'w'),indent=2);print('CUTE_NEUTRAL_V20_METRICS',json.dumps(M))