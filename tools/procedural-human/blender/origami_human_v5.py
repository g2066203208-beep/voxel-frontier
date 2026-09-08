import bpy, gzip, json, math, os, sys, urllib.request
from mathutils import Vector

OUT_DIR=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR,exist_ok=True)
RAW='https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2'
BASE_URL=RAW+'/3dobjs/base.obj'; TARGET=RAW+'/targets/macrodetails'; BODY_TARGET=430

# V5: cute anime + faceted paper sculpture. Geometry, not texture, carries the style.
# One understood CC0 human topology -> real male/female phenotype -> anime proportion warp
# -> Blender low-poly reconstruction -> paper hair/eyes as separate semantic meshes.

def clear_scene():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def fetch_text(url,gz=False):
    req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-origami-human-v5'})
    data=urllib.request.urlopen(req,timeout=60).read()
    if gz: data=gzip.decompress(data)
    return data.decode('utf-8')

def parse_obj_body(text):
    verts=[]; faces=[]; group=''
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        if s.startswith('v '):
            p=s.split(); verts.append([float(p[1]),float(p[2]),float(p[3])])
        elif s.startswith('g '): group=s[2:].strip().split()[0] if s[2:].strip() else ''
        elif s.startswith('f ') and group=='body':
            ids=[int(tok.split('/')[0])-1 for tok in s[2:].split()]
            if len(ids)>=3: faces.append(ids)
    return verts,faces

def parse_target(text):
    out={}
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        p=s.split()
        if len(p)>=4: out[int(p[0])]=(float(p[1]),float(p[2]),float(p[3]))
    return out

def add_target(verts,target,w):
    for i,d in target.items():
        if 0<=i<len(verts):
            verts[i][0]+=d[0]*w; verts[i][1]+=d[1]*w; verts[i][2]+=d[2]*w

def phenotype(kind,verts):
    for race in ('african','asian','caucasian'):
        add_target(verts,parse_target(fetch_text(f'{TARGET}/{race}-{kind}-young.target.gz',True)),1/3)
    macro=('maxmuscle-averageweight' if kind=='male' else 'averagemuscle-minweight')
    add_target(verts,parse_target(fetch_text(f'{TARGET}/universal-{kind}-young-{macro}.target.gz',True)),.20 if kind=='male' else .14)

def axis_frame(verts):
    mins=[min(v[a] for v in verts) for a in range(3)]; maxs=[max(v[a] for v in verts) for a in range(3)]
    ranges=[maxs[a]-mins[a] for a in range(3)]; order=sorted(range(3),key=lambda a:ranges[a],reverse=True)
    return mins,maxs,ranges,order[1],order[2],order[0]

def gauss(x,c,s): return math.exp(-.5*((x-c)/s)**2)

def remap_q(q):
    # 5-ish heads tall: legs remain elegant, torso compact, head gets a full 20% of stature.
    if q<.50: return q/.50*.47
    if q<.87: return .47+(q-.50)/.37*.33
    return .80+(q-.87)/.13*.20

def anime_body(kind,verts,faces):
    mins,maxs,ranges,width,depth,up=axis_frame(verts); H=ranges[up]
    cw=(mins[width]+maxs[width])/2; cd=(mins[depth]+maxs[depth])/2
    used=sorted({i for f in faces for i in f}); r={old:i for i,old in enumerate(used)}
    height=1.62 if kind=='male' else 1.54; out=[]
    for old in used:
        v=verts[old]; q=(v[up]-mins[up])/H
        x=(v[width]-cw)/H*height; y=(v[depth]-cd)/H*height; z=remap_q(q)*height
        # Deliberate anime/origami silhouette grammar.
        head=gauss(q,.935,.060); neck=gauss(q,.855,.030); shoulder=gauss(q,.79,.065)
        waist=gauss(q,.57,.070); hip=gauss(q,.48,.075); thigh=gauss(q,.37,.10); calf=gauss(q,.18,.09)
        if kind=='female':
            sx=1 + .34*head - .10*neck - .05*shoulder - .10*waist + .10*hip + .025*thigh
            sy=1 + .22*head + .025*hip
        else:
            sx=1 + .29*head - .08*neck + .055*shoulder - .055*waist + .025*hip + .020*calf
            sy=1 + .18*head + .020*shoulder
        # Slightly larger feet read as cute toy/paper sculpture at tiny triangle counts.
        if q<.075: sx*=1.10; sy*=1.08
        x*=sx; y*=sy
        out.append((x,y,z))
    return out,[[r[i] for i in f] for f in faces],height

def mat(name,rgb,rough=.92):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*rgb,1)
    b=m.node_tree.nodes.get('Principled BSDF')
    if b: b.inputs['Base Color'].default_value=(*rgb,1); b.inputs['Roughness'].default_value=rough
    return m

def mesh_obj(name,verts,faces,material):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.update(); ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(material); return ob

def tri_count(ob): ob.data.calc_loop_triangles(); return len(ob.data.loop_triangles)

def faceted(ob,target=BODY_TARGET):
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    t=ob.modifiers.new('Tri','TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=t.name); before=tri_count(ob)
    d=ob.modifiers.new('PaperQEM','DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=max(.001,min(1,target/max(before,1))); d.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=d.name)
    d2=ob.modifiers.new('PaperPlanes','DECIMATE'); d2.decimate_type='DISSOLVE'; d2.angle_limit=math.radians(2.5); bpy.ops.object.modifier_apply(modifier=d2.name)
    for p in ob.data.polygons: p.use_smooth=False
    ob.data.update(); return before,tri_count(ob)

def ico(name,loc,scale,material,sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc); ob=bpy.context.object; ob.name=name; ob.scale=scale; ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth=False
    return ob

def wedge(name,center,scale,rot_z,material):
    # 8-face paper crystal used for bangs and side locks.
    x,y,z=scale; verts=[(-x,-y,-z*.3),(x,-y,-z*.3),(x,y,-z*.2),(-x,y,-z*.2),(0,-y*.2,z),(0,y*.15,z)]
    faces=[(0,1,4),(1,2,4),(2,5,4),(2,3,5),(3,0,5),(0,4,5),(0,5,3),(1,2,5)]
    ob=mesh_obj(name,[(a,b,c) for a,b,c in verts],faces,material); ob.location=center; ob.rotation_euler[2]=rot_z; return ob

def semantic_face_hair(kind,height):
    # Front is -Y in this pipeline/camera.
    female=kind=='female'; zc=height*.895
    skin=mat(kind+'SkinPaper',(.93,.76,.69) if female else (.84,.71,.64))
    eye=mat(kind+'EyeGem',(.72,.20,.42) if female else (.22,.43,.67),.55)
    hair=mat(kind+'HairPaper',(.95,.63,.76) if female else (.35,.45,.62))
    # Hair cap: a low-poly faceted helmet, slightly back so face stays open.
    cap=ico(kind+'HairCap',(0,.018,zc+.025),(height*.115,height*.105,height*.118),hair,2)
    # Large anime eye gems, flattened along depth.
    eye_z=height*.902; ex=height*.043; ey=-height*.103
    eyes=[]
    for s in (-1,1):
        e=ico(kind+('EyeL' if s<0 else 'EyeR'),(s*height*.043,ey,eye_z),(height*.025,height*.010,height*.020),eye,1); eyes.append(e)
    # Tiny nose/mouth planes are implied by facets; bangs do most of the character work.
    bangs=[]
    configs=[(-.060,-.118,.944,-.12),(-.025,-.122,.958,.06),(.018,-.123,.954,-.05),(.055,-.117,.940,.12)]
    for j,(fx,fy,fz,rz) in enumerate(configs):
        bangs.append(wedge(f'{kind}Bang{j}',(height*fx,height*fy,height*fz),(height*.028,height*.010,height*.055),rz,hair))
    # Side locks: female a touch longer, male sharper/shorter.
    sidez=.875 if female else .892; sideh=.080 if female else .060
    for s in (-1,1):
        bangs.append(wedge(f'{kind}SideHair{1 if s>0 else 0}',(s*height*.102,-height*.032,height*sidez),(height*.025,height*.018,height*sideh),s*.18,hair))
    return [cap]+eyes+bangs

def make_character(kind):
    base,faces=parse_obj_body(fetch_text(BASE_URL)); phenotype(kind,base); verts,faces,height=anime_body(kind,base,faces)
    body=mesh_obj(kind.capitalize()+'AnimeOrigamiBody',verts,faces,mat(kind+'BodyPaper',(.88,.72,.66) if kind=='female' else (.76,.68,.63)))
    before,after=faceted(body); extras=semantic_face_hair(kind,height)
    return [body]+extras,before,after,height

def export_character(kind):
    clear_scene(); obs,before,after,height=make_character(kind)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    total=sum(tri_count(o) for o in obs)
    return before,after,total,height

def studio():
    sc=bpy.context.scene; sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.engine='BLENDER_EEVEE'; sc.world.color=(.035,.040,.055)
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except: pass
    bpy.ops.mesh.primitive_plane_add(size=7,location=(0,0,-.004)); bpy.context.object.data.materials.append(mat('Floor',(.105,.115,.145)))
    for name,loc,en,size in [('Key',(-3.2,-4.0,4.5),1150,3.0),('Fill',(3.0,-3.0,2.4),520,2.5),('Rim',(0,3.5,3.8),900,2.1)]:
        ld=bpy.data.lights.new(name,'AREA'); ld.energy=en; ld.shape='DISK'; ld.size=size; o=bpy.data.objects.new(name,ld); bpy.context.collection.objects.link(o); o.location=loc; o.rotation_euler=(Vector((0,0,.95))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam); cam.location=(2.45,-5.6,1.92); cam.rotation_euler=(Vector((0,0,.82))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=70; sc.camera=cam

def render_pair():
    clear_scene(); m,mb,ma,mh=make_character('male'); f,fb,fa,fh=make_character('female')
    for o in m: o.location.x-=.56; o.rotation_euler[2]=math.radians(-3)
    for o in f: o.location.x+=.56; o.rotation_euler[2]=math.radians(4)
    studio(); bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png'); bpy.ops.render.render(write_still=True)
    return sum(tri_count(o) for o in m),sum(tri_count(o) for o in f)

mb,ma,mt,mh=export_character('male'); fb,fa,ft,fh=export_character('female'); rmt,rft=render_pair()
metrics={'style':'cute-anime-origami-v5','source':'Anny/MPFB2 CC0 body + sparse phenotype targets','body_target_tris':BODY_TARGET,'male_body_tris':ma,'female_body_tris':fa,'male_total_tris':mt,'female_total_tris':ft,'render_male_total_tris':rmt,'render_female_total_tris':rft,'male_height_m':mh,'female_height_m':fh,'geometry_style':['~5-head anime proportions','enlarged faceted head','large eye gems','paper-crystal hair','flat facets','continuous body surface'],'blender_version':'.'.join(map(str,bpy.app.version))}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f: json.dump(metrics,f,indent=2)
print('ORIGAMI_HUMAN_V5_METRICS',json.dumps(metrics))
