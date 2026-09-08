import bpy, json, math, os, sys
from mathutils import Vector

OUT_DIR=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR,exist_ok=True)
HERE=os.path.dirname(os.path.abspath(__file__))

# Reuse the tested body-only mathematical source without executing its artifact block.
v8_path=os.path.join(HERE,'origami_human_v8.py')
with open(v8_path,'r',encoding='utf-8') as f: source=f.read()
marker="mb,ma=export_character('male')"
if marker not in source: raise RuntimeError('v8 import marker missing')
ns={'__name__':'origami_v8_library','__file__':v8_path}
exec(compile(source.split(marker)[0],v8_path,'exec'),ns)

clear_scene=ns['clear_scene']; fetch_text=ns['fetch_text']; parse_obj_body=ns['parse_obj_body']; phenotype=ns['phenotype']; canonical_body=ns['canonical_body']
mesh_from_data=ns['mesh_from_data']; mat=ns['mat']; tri_count=ns['tri_count']; BASE_URL=ns['BASE_URL']

BODY_TRIS=300

def mesh(name,vs,fs,m):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(vs,[],fs); me.update(); o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

def faceted(obj,target):
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    t=obj.modifiers.new('Tri','TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=t.name); before=tri_count(obj)
    d=obj.modifiers.new('ArtQEM','DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=max(.001,min(1,target/max(before,1))); d.use_collapse_triangulate=True; bpy.ops.object.modifier_apply(modifier=d.name)
    for p in obj.data.polygons: p.use_smooth=False
    obj.data.update(); return before,tri_count(obj)

def ico(name,loc,scale,m):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth=False
    return o

def wedge(name,center,scale,rz,m,front_sign=1):
    x,y,z=scale
    # Closed asymmetric paper crystal; front_sign flips its depth language.
    vs=[(-x,-y,0),(x,-y,0),(x,y,0),(-x,y,0),(0,-front_sign*y*.45,z),(0,front_sign*y*.30,-z*.32)]
    fs=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
    o=mesh(name,vs,fs,m); o.location=center; o.rotation_euler[2]=rz; return o

def flat_poly(name,points,y,m):
    # points are x,z. Fan triangulation keeps anime features extremely cheap.
    vs=[(x,y,z) for x,z in points]; c=(sum(x for x,z in points)/len(points),y,sum(z for x,z in points)/len(points)); vs.append(c); ci=len(vs)-1
    fs=[(ci,i,(i+1)%len(points)) for i in range(len(points))]
    return mesh(name,vs,fs,m)

def frustum(name,z0,z1,rx0,ry0,rx1,ry1,m,segments=6):
    vs=[]
    for z,rx,ry in ((z0,rx0,ry0),(z1,rx1,ry1)):
        for i in range(segments):
            a=2*math.pi*i/segments; vs.append((rx*math.cos(a),ry*math.sin(a),z))
    fs=[]
    for i in range(segments): fs.append((i,(i+1)%segments,segments+(i+1)%segments,segments+i))
    fs.append(tuple(range(segments-1,-1,-1))); fs.append(tuple(range(segments,2*segments)))
    o=mesh(name,vs,fs,m)
    for p in o.data.polygons: p.use_smooth=False
    return o

def paper_limb(name,a,b,r0,r1,m,segments=6):
    a=Vector(a); b=Vector(b); d=b-a; L=d.length; mid=(a+b)*.5
    bpy.ops.mesh.primitive_cone_add(vertices=segments,radius1=r0,radius2=r1,depth=L,end_fill_type='NGON',location=mid)
    o=bpy.context.object; o.name=name; o.data.materials.append(m); o.rotation_euler=Vector((0,0,1)).rotation_difference(d.normalized()).to_euler()
    for p in o.data.polygons: p.use_smooth=False
    return o

def detect_front_sign(vs):
    h=max(z for x,y,z in vs)-min(z for x,y,z in vs)
    # Nose/face center is the most protruding central point in lower head band.
    cand=[(abs(y),y) for x,y,z in vs if .78*h<z<.93*h and abs(x)<.055*h]
    if not cand: return 1
    return 1 if max(cand)[1]>=0 else -1

def stylized_body(kind):
    base,faces=parse_obj_body(fetch_text(BASE_URL)); phenotype(kind,base); vs,faces=canonical_body(kind,base,faces)
    h=max(z for x,y,z in vs)-min(z for x,y,z in vs)
    # For the visible style master, tuck source arms/hands into sleeves. Legs/head remain the mathematical body.
    out=[]
    for x,y,z in vs:
        q=z/h
        ax=abs(x)
        if .45<q<.80 and ax>.105*h:
            s=1 if x>=0 else -1
            x=s*(.105*h+(ax-.105*h)*.045); y*=.40
        out.append((x,y,z))
    skin=mat(kind+'Skin',(.93,.72,.66) if kind=='female' else (.84,.68,.61))
    body=mesh(kind.capitalize()+'DrivenBody',out,faces,skin); before,after=faceted(body,BODY_TRIS)
    return body,h,detect_front_sign(out),before,after

def make_face(kind,h,front):
    female=kind=='female'; objs=[]
    skin=mat(kind+'Face',(.98,.79,.73) if female else (.91,.75,.68)); white=mat(kind+'EyeWhite',(.99,.99,1)); iris=mat(kind+'Iris',(.91,.27,.59) if female else (.25,.50,.88)); pupil=mat(kind+'Pupil',(.06,.055,.09)); mouth=mat(kind+'Mouth',(.74,.16,.32) if female else (.45,.13,.20))
    zc=.875*h; fy=front*.137*h
    # Wide cheeks + tiny chin = cute anime face plate, deliberately planar.
    pts=[(-.090*h,zc+.074*h),(-.116*h,zc+.020*h),(-.105*h,zc-.045*h),(-.056*h,zc-.093*h),(0,zc-.112*h),(.056*h,zc-.093*h),(.105*h,zc-.045*h),(.116*h,zc+.020*h),(.090*h,zc+.074*h)]
    objs.append(flat_poly(kind+'FacePlate',pts,fy,skin))
    for s in (-1,1):
        cx=s*.049*h; cz=zc+.002*h; w=.046*h; eh=.025*h
        eyepts=[(cx-w,cz),(cx-.58*w,cz+eh),(cx+.58*w,cz+eh),(cx+w,cz),(cx+.58*w,cz-eh),(cx-.58*w,cz-eh)]
        objs.append(flat_poly(kind+('EyeWhiteL' if s<0 else 'EyeWhiteR'),eyepts,fy+front*.003*h,white))
        # Diamond iris/pupil, no spheres: reads like folded paper instead of plastic toy.
        objs.append(flat_poly(kind+('IrisL' if s<0 else 'IrisR'),[(cx-.014*h,cz),(cx,cz+.019*h),(cx+.014*h,cz),(cx,cz-.019*h)],fy+front*.005*h,iris))
        objs.append(flat_poly(kind+('PupilL' if s<0 else 'PupilR'),[(cx-.006*h,cz),(cx,cz+.011*h),(cx+.006*h,cz),(cx,cz-.011*h)],fy+front*.007*h,pupil))
        objs.append(flat_poly(kind+('SparkL' if s<0 else 'SparkR'),[(cx-.006*h,cz+.009*h),(cx-.002*h,cz+.014*h),(cx+.002*h,cz+.009*h),(cx-.002*h,cz+.005*h)],fy+front*.009*h,white))
    objs.append(flat_poly(kind+'Smile',[(-.013*h,zc-.065*h),(0,zc-.072*h),(.013*h,zc-.065*h),(0,zc-.078*h)],fy+front*.004*h,mouth))
    return objs

def make_hair(kind,h,front):
    female=kind=='female'; hair=mat(kind+'Hair',(.96,.57,.76) if female else (.29,.43,.69)); objs=[]
    # 20-triangle cap, enlarged behind face.
    cap=ico(kind+'HairCap',(0,-front*.010*h,.892*h),(.158*h,.146*h,.158*h),hair); objs.append(cap)
    # Five front locks and two side locks. Geometric rhythm is more important than strand count.
    cfg=[(-.075,.950,-.18),(-.040,.968,.08),(-.008,.978,-.02),(.030,.967,.05),(.066,.947,.17)]
    for i,(x,z,r) in enumerate(cfg):
        objs.append(wedge(f'{kind}Bang{i}',(x*h,front*.148*h,z*h),(.027*h,.011*h,.056*h),r,hair,front))
    sidez=.835 if female else .855; sideh=.090 if female else .065
    for s in (-1,1): objs.append(wedge(kind+('SideL' if s<0 else 'SideR'),(s*.112*h,front*.055*h,sidez*h),(.030*h,.022*h,sideh*h),s*.18,hair,front))
    if female:
        # Two low-cost side pony paper crystals for a stronger cute silhouette.
        for s in (-1,1): objs.append(wedge(kind+('PonyL' if s<0 else 'PonyR'),(s*.155*h,-front*.005*h,.825*h),(.040*h,.026*h,.115*h),s*.25,hair,front))
    return objs

def make_outfit_limbs(kind,h,front):
    female=kind=='female'; objs=[]
    if female:
        top=mat('FemaleTop',(.985,.67,.82)); lower=mat('FemaleSkirt',(.73,.57,.94)); accent=mat('FemaleAccent',(.96,.36,.62)); sleeve=top; shoe=mat('FemaleShoe',(.64,.45,.84))
        objs += [frustum('FemaleTop',.505*h,.705*h,.105*h,.075*h,.135*h,.082*h,top),frustum('FemaleSkirt',.405*h,.535*h,.185*h,.095*h,.108*h,.074*h,lower)]
        objs += [wedge('FemaleBowL',(-.032*h,front*.092*h,.650*h),(.038*h,.010*h,.027*h),-.32,accent,front),wedge('FemaleBowR',(.032*h,front*.092*h,.650*h),(.038*h,.010*h,.027*h),.32,accent,front)]
    else:
        top=mat('MaleJacket',(.35,.56,.88)); lower=mat('MaleShorts',(.22,.31,.56)); sleeve=top; shoe=mat('MaleShoe',(.18,.25,.48))
        objs += [frustum('MaleJacket',.505*h,.710*h,.120*h,.078*h,.145*h,.086*h,top),frustum('MaleShorts',.405*h,.525*h,.145*h,.085*h,.118*h,.078*h,lower)]
    hand=mat(kind+'Hand',(.98,.79,.73) if female else (.91,.75,.68))
    # Downward tapered sleeves + single-facet mitten hands.
    for s in (-1,1):
        shoulder=(s*(.125 if female else .135)*h,front*.005*h,.665*h)
        elbow=(s*(.155 if female else .165)*h,front*.012*h,.555*h)
        wrist=(s*(.145 if female else .155)*h,front*.020*h,.465*h)
        objs.append(paper_limb(kind+('UpperSleeveL' if s<0 else 'UpperSleeveR'),shoulder,elbow,.043*h,.035*h,sleeve))
        objs.append(paper_limb(kind+('LowerSleeveL' if s<0 else 'LowerSleeveR'),elbow,wrist,.036*h,.027*h,sleeve))
        objs.append(ico(kind+('HandL' if s<0 else 'HandR'),(wrist[0],wrist[1]+front*.004*h,wrist[2]-.025*h),(.030*h,.022*h,.038*h),hand))
        objs.append(ico(kind+('ShoeL' if s<0 else 'ShoeR'),(s*.058*h,front*.032*h,.038*h),(.062*h,.094*h,.048*h),shoe))
    return objs

def make_master(kind):
    body,h,front,before,body_tris=stylized_body(kind)
    extras=make_face(kind,h,front)+make_hair(kind,h,front)+make_outfit_limbs(kind,h,front)
    obs=[body]+extras
    return obs,h,front,before,body_tris,sum(tri_count(o) for o in obs)

def export_objects(kind,obs,path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True)

def export_master(kind):
    clear_scene(); obs,h,front,before,btris,total=make_master(kind); export_objects(kind,obs,os.path.join(OUT_DIR,kind+'.glb'))
    # Export driven body separately for gameplay morphology/rigging work.
    bpy.ops.object.select_all(action='DESELECT'); obs[0].select_set(True); bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'_body.glb'),export_format='GLB',use_selection=True)
    return h,front,before,btris,total

def studio(camera_front=1):
    sc=bpy.context.scene; sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.engine='BLENDER_EEVEE'; sc.world.color=(.035,.039,.052)
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except: pass
    bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.005)); bpy.context.object.data.materials.append(mat('Floor',(.11,.12,.15)))
    for n,loc,en,size in [('Key',(-3.5,-camera_front*4.0,4.2),1250,3.1),('Fill',(3.0,-camera_front*3.0,2.6),520,2.5),('Rim',(0,camera_front*3.7,3.5),900,2.2)]:
        ld=bpy.data.lights.new(n,'AREA'); ld.energy=en; ld.shape='DISK'; ld.size=size; o=bpy.data.objects.new(n,ld); bpy.context.collection.objects.link(o); o.location=loc; o.rotation_euler=(Vector((0,0,.68))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam); cam.location=(2.05,camera_front*5.25,1.55); cam.rotation_euler=(Vector((0,0,.66))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=72; sc.camera=cam

def render_pair():
    clear_scene(); m,mh,mfront,mb0,mb,mt=make_master('male'); f,fh,ffront,fb0,fb,ft=make_master('female')
    for o in m: o.location.x-=.48
    for o in f: o.location.x+=.48
    # Use detected front direction; both source phenotypes share the same convention.
    studio(mfront)
    bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png'); bpy.ops.render.render(write_still=True)
    return mb,mt,fb,ft,mfront

mh,mfront,mb0,mb,mt=export_master('male'); fh,ffront,fb0,fb,ft=export_master('female'); rmb,rmt,rfb,rft,front=render_pair()
metrics={'style':'anime-origami-master-v9','source':'Anny/MPFB2 CC0 driven body + procedural paper-art style shell','male_body_tris':mb,'female_body_tris':fb,'male_master_tris':mt,'female_master_tris':ft,'male_height_m':mh,'female_height_m':fh,'detected_front_sign':front,'modules':['driven body','anime face plate','paper eyes','faceted hair','neutral paper outfit','paper sleeves','mitten hands','chunky shoes'],'blender_version':'.'.join(map(str,bpy.app.version))}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f: json.dump(metrics,f,indent=2)
print('ANIME_ORIGAMI_MASTER_V9',json.dumps(metrics))
