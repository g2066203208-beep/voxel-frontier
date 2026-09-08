import bpy,bmesh,json,math,os,struct,sys,urllib.request
from mathutils import Vector

OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/human-tailor-v23')
os.makedirs(OUT,exist_ok=True)
BASE_URL='https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2/3dobjs/base.obj'
TARGET_HEIGHT=1.70
TARGET_TRIS=1200
CUT_Q=0.585
ARM_Q_MIN=0.40
ARM_Q_MAX=0.86
ARM_X_MIN=0.128

SLICES=[
 (0.58,0.95,0.97),(0.64,0.96,0.98),(0.70,0.985,0.99),(0.76,1.00,1.00),
 (0.81,0.99,0.99),(0.84,0.97,0.98),(0.87,0.985,0.99),(0.90,1.00,1.00),
 (0.94,1.01,1.01),(1.00,1.015,1.015),
]

def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def mat(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
 b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.92
 return m

def fetch_text(url):
 req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-human-tailor-v26'})
 return urllib.request.urlopen(req,timeout=60).read().decode('utf-8')

def parse_body(text):
 V=[];F=[];g=''
 for raw in text.splitlines():
  s=raw.strip()
  if not s or s.startswith('#'):continue
  if s.startswith('v '):
   p=s.split();V.append((float(p[1]),float(p[2]),float(p[3])))
  elif s.startswith('g '):g=s[2:].strip().split()[0] if s[2:].strip() else ''
  elif s.startswith('f ') and g=='body':
   ids=[int(t.split('/')[0])-1 for t in s[2:].split()]
   if len(ids)>=3:F.append(ids)
 if len(V)<1000 or len(F)<1000:raise RuntimeError((len(V),len(F)))
 return V,F

def frame(V):
 mn=[min(v[a] for v in V) for a in range(3)];mx=[max(v[a] for v in V) for a in range(3)]
 rg=[mx[a]-mn[a] for a in range(3)];order=sorted(range(3),key=lambda a:rg[a],reverse=True)
 return mn,mx,rg,order[1],order[2],order[0]

def smoothstep(a,b,x):
 if x<=a:return 0.0
 if x>=b:return 1.0
 t=(x-a)/(b-a);return t*t*(3-2*t)

def interp(q,idx):
 if q<=SLICES[0][0]:return SLICES[0][idx]
 if q>=SLICES[-1][0]:return SLICES[-1][idx]
 for a,b in zip(SLICES,SLICES[1:]):
  if a[0]<=q<=b[0]:
   t=smoothstep(a[0],b[0],q);return a[idx]*(1-t)+b[idx]*t
 return 1.0

def build_cropped_surface():
 rawV,rawF=parse_body(fetch_text(BASE_URL));mn,mx,rg,WA,DA,UA=frame(rawV);H=rg[UA];cw=(mn[WA]+mx[WA])*.5;cd=(mn[DA]+mx[DA])*.5
 used=sorted({i for f in rawF for i in f});R={old:i for i,old in enumerate(used)};V=[];Q=[]
 for old in used:
  p=rawV[old];x=(p[WA]-cw)/H;y=(p[DA]-cd)/H;q=(p[UA]-mn[UA])/H
  sx=interp(q,1);sy=interp(q,2)
  if abs(x)>ARM_X_MIN and ARM_Q_MIN<=q<=ARM_Q_MAX:sx=1.0;sy=1.0
  hs=smoothstep(.835,.90,q);x*=sx*(1.0+.065*hs);y*=sy*(1.0+.035*hs)
  V.append((x*TARGET_HEIGHT,y*TARGET_HEIGHT,q*TARGET_HEIGHT));Q.append((x,y,q))
 F=[]
 for f in rawF:
  ids=[R[i] for i in f];qc=sum(Q[i][2] for i in ids)/len(ids);xc=sum(Q[i][0] for i in ids)/len(ids)
  if qc>=CUT_Q or (ARM_Q_MIN<=qc<=ARM_Q_MAX and abs(xc)>=ARM_X_MIN):F.append(ids)
 return V,F,CUT_Q*TARGET_HEIGHT

def make_source():
 V,F,cut=build_cropped_surface();me=bpy.data.meshes.new('HumanTailorSource');me.from_pydata(V,[],F);me.update();o=bpy.data.objects.new('HumanTailorMannequin',me);bpy.context.collection.objects.link(o);o.data.materials.append(mat('NeutralMannequin',(.78,.75,.72)));return o,cut

def tris(o):o.data.calc_loop_triangles();return len(o.data.loop_triangles)

def close_and_clean(o):
 bm=bmesh.new();bm.from_mesh(o.data);boundary=[e for e in bm.edges if e.is_boundary]
 if boundary:
  try:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
  except Exception as ex:print('HOLES_FILL_WARNING',repr(ex))
 bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-7);bmesh.ops.dissolve_degenerate(bm,dist=1e-9,edges=bm.edges);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bmesh.ops.triangulate(bm,faces=bm.faces)
 bm.to_mesh(o.data);bm.free();o.data.validate(verbose=False,clean_customdata=True);o.data.update()

def smooth_faceless_depth(o):
 # Final game mesh is already low-poly here. Erase facial relief only in depth (Y),
 # while preserving the human X/Z silhouette, jaw, cranium and ears.
 verts=o.data.vertices;adj=[set() for _ in verts]
 for e in o.data.edges:
  a,b=e.vertices;adj[a].add(b);adj[b].add(a)
 # Wide mid-face mask: eyes, nose, philtrum and mouth. Chin and skull boundary stay untouched.
 sel={v.index for v in verts if 1.415<v.co.z<1.665 and v.co.y>0.015 and abs(v.co.x)<0.112}
 # Strong Laplacian depth relaxation with ALL neighbors as anchors. This removes crease memory
 # much more reliably than smoothing only inside the selected patch.
 for _ in range(55):
  upd={}
  for i in sel:
   ns=list(adj[i])
   if len(ns)>=2:
    avg=sum(verts[j].co.y for j in ns)/len(ns)
    # taper near face-mask boundary so cheeks/jaw join continuously
    wx=max(0.0,min(1.0,(0.112-abs(verts[i].co.x))/0.035))
    wz=min(smoothstep(1.415,1.455,verts[i].co.z),1.0-smoothstep(1.625,1.665,verts[i].co.z))
    w=.82*max(0.0,wx*wz)
    upd[i]=verts[i].co.y*(1.0-w)+avg*w
  for i,y in upd.items():verts[i].co.y=y
 # One final band-wise fairing pass: central face should be a clean, gently convex mannequin plane.
 bands={}
 for i in sel:
  k=round(verts[i].co.z/0.018)
  bands.setdefault(k,[]).append(i)
 for ids in bands.values():
  if len(ids)<3:continue
  cheek=[verts[i].co.y for i in ids if 0.065<abs(verts[i].co.x)<0.112]
  if not cheek:continue
  base=sum(cheek)/len(cheek)
  for i in ids:
   x=abs(verts[i].co.x);bulge=.006*max(0.0,1.0-(x/0.112)**2)
   verts[i].co.y=verts[i].co.y*.15+(base+bulge)*.85
 o.data.update();print('FACELESS_SMOOTH_VERTS',len(sel))

def decimate_real_surface(o,target):
 bpy.context.view_layer.objects.active=o;o.select_set(True);before=tris(o)
 d=o.modifiers.new('Human_QEM','DECIMATE');d.decimate_type='COLLAPSE';d.ratio=max(.001,min(1.0,target/max(before,1)));d.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=d.name)
 p=o.modifiers.new('Human_PlanarCleanup','DECIMATE');p.decimate_type='DISSOLVE';p.angle_limit=math.radians(1.5);bpy.ops.object.modifier_apply(modifier=p.name)
 smooth_faceless_depth(o)
 for poly in o.data.polygons:poly.use_smooth=False
 o.data.update();return before,tris(o)

def sanitize(o):
 o.data.calc_loop_triangles();all_verts=[tuple(v.co) for v in o.data.vertices];faces=[];seen=set()
 for t in o.data.loop_triangles:
  f=tuple(int(i) for i in t.vertices);key=tuple(sorted(f))
  if len(set(f))<3 or key in seen:continue
  seen.add(key);faces.append(f)
 used=sorted({i for f in faces for i in f});remap={old:new for new,old in enumerate(used)};verts=[all_verts[i] for i in used];faces=[[remap[i] for i in f] for f in faces]
 print('SANITIZE_COMPACT',json.dumps({'source_vertices':len(all_verts),'used_vertices':len(verts),'triangles':len(faces)}))
 me=bpy.data.meshes.new('HumanTailorExportMesh');me.from_pydata(verts,[],faces);me.update(calc_edges=True)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6);bmesh.ops.dissolve_degenerate(bm,dist=1e-8,edges=bm.edges);bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
 bd=[e for e in bm.edges if e.is_boundary]
 if bd:
  try:bmesh.ops.holes_fill(bm,edges=bd,sides=0)
  except Exception as ex:print('FINAL_HOLES_FILL_WARNING',repr(ex))
 bmesh.ops.triangulate(bm,faces=bm.faces);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();me.update(calc_edges=True)
 n=bpy.data.objects.new('HumanTailorExport',me);bpy.context.collection.objects.link(n);n.data.materials.append(mat('NeutralMannequin',(.78,.75,.72)));[setattr(p,'use_smooth',False) for p in n.data.polygons];bpy.data.objects.remove(o,do_unlink=True);return n

def topo(o):
 bm=bmesh.new();bm.from_mesh(o.data);un=set(bm.verts);cc=0
 while un:
  cc+=1;st=[un.pop()]
  while st:
   v=st.pop()
   for e in v.link_edges:
    w=e.other_vert(v)
    if w in un:un.remove(w);st.append(w)
 d={'connected_components':cc,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'verts':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces)};bm.free();return d

def clean_model():
 o,cut=make_source();close_and_clean(o);before,_=decimate_real_surface(o,TARGET_TRIS);o=sanitize(o);t=topo(o);assert t['connected_components']==1 and t['boundary_edges']==0 and t['nonmanifold_edges']==0,t;return o,before,tris(o),t,cut

def glb_check(path):
 data=open(path,'rb').read();assert len(data)>1000 and data[:4]==b'glTF';off=12;doc=None
 while off+8<=len(data):
  ln,typ=struct.unpack_from('<II',data,off);off+=8;chunk=data[off:off+ln];off+=ln
  if typ==0x4E4F534A:doc=json.loads(chunk.decode('utf-8').rstrip(' \x00'))
 assert doc and doc.get('meshes');pr=sum(len(m.get('primitives',[])) for m in doc['meshes']);assert pr>0;return len(data),len(doc['meshes']),pr

def studio(view,cut):
 sc=bpy.context.scene;sc.render.resolution_x=900;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.engine='BLENDER_EEVEE';sc.world.color=(.025,.028,.033)
 target=Vector((0,0,(cut+TARGET_HEIGHT)*.5))
 for name,loc,e,size in [('Key',(-3,-4,3.8),950,2.6),('Fill',(3,-3,2.7),350,2.2),('Rim',(0,3,3.3),600,2.0)]:
  ld=bpy.data.lights.new(name,'AREA');ld.energy=e;ld.shape='DISK';ld.size=size;x=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(x);x.location=loc;x.rotation_euler=(target-Vector(loc)).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);dist=3.8
 cam.location=(0,dist,target.z) if view=='front' else ((dist,0,target.z) if view=='side' else (0,-dist,target.z))
 cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=1.30;sc.camera=cam

def render(name,view):
 clear();o,_,_,_,cut=clean_model();studio(view,cut);bpy.context.scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)

def export():
 clear();o,b,a,t,cut=clean_model();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;path=os.path.join(OUT,'neutral-human-waist-up.glb');bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_normals=True);gb,gm,gp=glb_check(path);return b,a,t,gb,gm,gp,cut

b,a,T,gb,gm,gp,cut=export();render('front.png','front');render('side.png','side');render('back.png','back')
M={'style':'reference-matched-faceless-neutral-lowpoly-tailor-v26','purpose':'player clothing creation mannequin','source':'CC0 MPFB2 body surface via Anny repository','original_human_surface':True,'reference_mannequin_style':True,'faceless':True,'neutral_only':True,'waist_up_only':True,'head':True,'full_arms':True,'legs':False,'hair':False,'face_addons':False,'clothing':False,'props':False,'tris_before_decimate':b,'tris':a,'single_continuous_shell':T['connected_components']==1 and T['boundary_edges']==0 and T['nonmanifold_edges']==0,**T,'target_tris':TARGET_TRIS,'waist_cut_z_m':cut,'glb_bytes':gb,'glb_meshes':gm,'glb_primitives':gp,'glb_valid_mesh':gp>0,'topology_method':'real human surface -> neutral/head proportion -> crop/cap -> direct QEM -> strong depth-only faceless fairing -> compact low-poly','blender_version':'.'.join(map(str,bpy.app.version))};json.dump(M,open(os.path.join(OUT,'metrics.json'),'w'),indent=2);print('HUMAN_TAILOR_V26_METRICS',json.dumps(M))