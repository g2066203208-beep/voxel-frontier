import bpy, gzip, json, math, os, sys, urllib.request
from mathutils import Vector

OUT_DIR=os.path.abspath(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else os.path.abspath('artifacts/origami-human')
os.makedirs(OUT_DIR,exist_ok=True)
RAW='https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2'
BASE_URL=RAW+'/3dobjs/base.obj'; TARGET=RAW+'/targets/macrodetails'; BODY_TARGET=360

def clear_scene():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def fetch_text(url,gz=False):
    req=urllib.request.Request(url,headers={'User-Agent':'voxel-frontier-anime-origami-v6'})
    data=urllib.request.urlopen(req,timeout=60).read();
    if gz: data=gzip.decompress(data)
    return data.decode('utf-8')

def parse_obj_body(text):
    vs=[]; fs=[]; g=''
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        if s.startswith('v '):
            p=s.split(); vs.append([float(p[1]),float(p[2]),float(p[3])])
        elif s.startswith('g '): g=s[2:].strip().split()[0] if s[2:].strip() else ''
        elif s.startswith('f ') and g=='body':
            ids=[int(t.split('/')[0])-1 for t in s[2:].split()]
            if len(ids)>=3: fs.append(ids)
    return vs,fs

def parse_target(text):
    out={}
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        p=s.split()
        if len(p)>=4: out[int(p[0])]=(float(p[1]),float(p[2]),float(p[3]))
    return out

def add_target(vs,t,w):
    for i,d in t.items():
        if 0<=i<len(vs):
            vs[i][0]+=d[0]*w; vs[i][1]+=d[1]*w; vs[i][2]+=d[2]*w

def phenotype(kind,vs):
    for race in ('african','asian','caucasian'):
        add_target(vs,parse_target(fetch_text(f'{TARGET}/{race}-{kind}-young.target.gz',True)),1/3)
    macro='maxmuscle-averageweight' if kind=='male' else 'averagemuscle-minweight'
    add_target(vs,parse_target(fetch_text(f'{TARGET}/universal-{kind}-young-{macro}.target.gz',True)),.17 if kind=='male' else .12)

def frame(vs):
    mn=[min(v[a] for v in vs) for a in range(3)]; mx=[max(v[a] for v in vs) for a in range(3)]; rg=[mx[a]-mn[a] for a in range(3)]
    order=sorted(range(3),key=lambda a:rg[a],reverse=True)
    return mn,mx,rg,order[1],order[2],order[0]

def g(x,c,s): return math.exp(-.5*((x-c)/s)**2)

def qmap(q):
    # Cute 4.8-5.2 head silhouette: body compact, head occupies ~21% total height.
    if q<.48: return q/.48*.445
    if q<.865: return .445+(q-.48)/.385*.345
    return .790+(q-.865)/.135*.210

def stylize(kind,vs,fs):
    mn,mx,rg,wa,da,ua=frame(vs); H=rg[ua]; cw=(mn[wa]+mx[wa])/2; cd=(mn[da]+mx[da])/2
    used=sorted({i for f in fs for i in f}); rem={old:i for i,old in enumerate(used)}
    height=1.58 if kind=='male' else 1.50; out=[]
    for old in used:
        v=vs[old]; q=(v[ua]-mn[ua])/H
        x=(v[wa]-cw)/H*height; y=(v[da]-cd)/H*height; z=qmap(q)*height
        head=g(q,.935,.062); jaw=g(q,.875,.035); neck=g(q,.84,.027); shoulder=g(q,.77,.067); waist=g(q,.565,.065); hip=g(q,.475,.072)
        if kind=='female':
            sx=1+.40*head-.14*jaw-.10*neck-.075*shoulder-.12*waist+.10*hip
            sy=1+.25*head+.018*hip
        else:
            sx=1+.35*head-.10*jaw-.09*neck+.015*shoulder-.07*waist+.035*hip
            sy=1+.21*head+.018*shoulder
        x*=sx; y*=sy
        # Lower A-pose arms into a friendlier anime base pose without a rig.
        if .56<q<.82 and abs(x)>height*.13:
            sgn=1 if x>0 else -1; px=sgn*height*.145; pz=height*.735; dx=x-px; dz=z-pz; a=sgn*math.radians(24)
            x=px+math.cos(a)*dx+math.sin(a)*dz; z=pz-math.sin(a)*dx+math.cos(a)*dz
        if q<.072: x*=1.12; y*=1.10
        out.append((x,y,z))
    return out,[[rem[i] for i in f] for f in fs],height

def mat(name,rgb,rough=.9):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*rgb,1)
    b=m.node_tree.nodes.get('Principled BSDF')
    if b: b.inputs['Base Color'].default_value=(*rgb,1); b.inputs['Roughness'].default_value=rough
    return m

def mesh(name,vs,fs,m):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(vs,[],fs); me.update(); o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

def tris(o): o.data.calc_loop_triangles(); return len(o.data.loop_triangles)

def decimate(o,target):
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    t=o.modifiers.new('Tri','TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=t.name); before=tris(o)
    d=o.modifiers.new('PaperQEM','DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=max(.001,min(1,target/max(before,1))); d.use_collapse_triangulate=True; bpy.ops.object.modifier_apply(modifier=d.name)
    d2=o.modifiers.new('PaperPlanes','DECIMATE'); d2.decimate_type='DISSOLVE'; d2.angle_limit=math.radians(2.8); bpy.ops.object.modifier_apply(modifier=d2.name)
    for p in o.data.polygons: p.use_smooth=False
    o.data.update(); return before,tris(o)

def ico(name,loc,scale,m,sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth=False
    return o

def wedge(name,center,scale,rz,m):
    x,y,z=scale; vs=[(-x,-y,-z*.25),(x,-y,-z*.25),(x,y,-z*.2),(-x,y,-z*.2),(0,-y*.15,z),(0,y*.10,z)]
    fs=[(0,1,4),(1,2,4),(2,5,4),(2,3,5),(3,0,5),(0,4,5),(0,5,3),(1,2,5)]
    o=mesh(name,vs,fs,m); o.location=center; o.rotation_euler[2]=rz; return o

def flat_polygon(name,points,y,m):
    vs=[(x,y,z) for x,z in points]; c=(sum(x for x,z in points)/len(points),y,sum(z for x,z in points)/len(points)); vs.append(c); ci=len(vs)-1
    fs=[]
    for i in range(len(points)): fs.append((ci,i,(i+1)%len(points)))
    return mesh(name,vs,fs,m)

def face_and_hair(kind,h):
    female=kind=='female'; skin=mat(kind+'FacePaper',(.965,.79,.72) if female else (.89,.75,.68)); white=mat(kind+'EyeWhite',(.98,.98,.99)); iris=mat(kind+'Iris',(.86,.26,.55) if female else (.24,.48,.78),.45); dark=mat(kind+'Pupil',(.08,.07,.11),.55); hair=mat(kind+'Hair',(.96,.58,.76) if female else (.30,.42,.64))
    zc=h*.895; front=-h*.117
    # Skin face plate deliberately hides the realistic low-poly face and creates anime cheeks/jaw.
    facepts=[(-h*.070,zc+h*.067),(-h*.094,zc+h*.020),(-h*.088,zc-h*.038),(-h*.050,zc-h*.082),(0,zc-h*.103),(h*.050,zc-h*.082),(h*.088,zc-h*.038),(h*.094,zc+h*.020),(h*.070,zc+h*.067)]
    objs=[flat_polygon(kind+'AnimeFace',facepts,front,skin)]
    # Large horizontal anime eyes: white paper almond + colored gem + tiny highlight.
    for s in (-1,1):
        cx=s*h*.045; cz=zc-h*.002; w=h*.034; hh=h*.018; tilt=s*h*.004
        pts=[(cx-w,cz),(cx-w*.55,cz+hh+tilt),(cx+w*.55,cz+hh-tilt),(cx+w,cz),(cx+w*.55,cz-hh-tilt),(cx-w*.55,cz-hh+tilt)]
        objs.append(flat_polygon(kind+('EyeWhiteL' if s<0 else 'EyeWhiteR'),pts,front-h*.002,white))
        objs.append(ico(kind+('IrisL' if s<0 else 'IrisR'),(cx,front-h*.006,cz),(h*.015,h*.006,h*.016),iris,1))
        objs.append(ico(kind+('PupilL' if s<0 else 'PupilR'),(cx,front-h*.010,cz),(h*.006,h*.003,h*.008),dark,1))
        objs.append(ico(kind+('SparkL' if s<0 else 'SparkR'),(cx-s*h*.005,front-h*.013,cz+h*.006),(h*.003,h*.002,h*.003),white,1))
    # Hair volume behind the face plus layered front paper locks.
    objs.append(ico(kind+'HairVolume',(0,h*.015,zc+h*.025),(h*.118,h*.108,h*.122),hair,2))
    bang_cfg=[(-.067,-.128,.958,-.16),(-.038,-.132,.972,.06),(-.010,-.134,.978,-.02),(.023,-.133,.972,.03),(.054,-.128,.956,.14)]
    for j,(x,y,z,r) in enumerate(bang_cfg): objs.append(wedge(f'{kind}Bang{j}',(h*x,h*y,h*z),(h*.025,h*.009,h*.052),r,hair))
    side_len=.082 if female else .060
    for s in (-1,1): objs.append(wedge(f'{kind}SideLock{1 if s>0 else 0}',(s*h*.103,-h*.035,h*(.875 if female else .892)),(h*.025,h*.018,h*side_len),s*.16,hair))
    # tiny smiling mouth as a pink/dark paper diamond
    mouth=mat(kind+'Mouth',(.72,.19,.30) if female else (.45,.17,.22))
    objs.append(flat_polygon(kind+'Mouth',[(-h*.010,zc-h*.055),(0,zc-h*.060),(h*.010,zc-h*.055),(0,zc-h*.066)],front-h*.004,mouth))
    return objs

def frustum(name,z0,z1,rx0,ry0,rx1,ry1,m,segments=8):
    vs=[]
    for z,rx,ry in ((z0,rx0,ry0),(z1,rx1,ry1)):
        for i in range(segments):
            a=2*math.pi*i/segments; vs.append((rx*math.cos(a),ry*math.sin(a),z))
    fs=[]
    for i in range(segments): fs.append((i,(i+1)%segments,segments+(i+1)%segments,segments+i))
    fs.append(tuple(range(segments-1,-1,-1))); fs.append(tuple(range(segments,2*segments)))
    return mesh(name,vs,fs,m)

def outfit(kind,h):
    female=kind=='female'; objs=[]
    if female:
        top=mat('FemaleTop',(.985,.80,.88)); skirt=mat('FemaleSkirt',(.78,.66,.94)); accent=mat('FemaleBow',(.93,.37,.60))
        objs.append(frustum('FemalePaperTop',h*.535,h*.720,h*.100,h*.070,h*.130,h*.078,top,8))
        objs.append(frustum('FemalePaperSkirt',h*.455,h*.575,h*.175,h*.085,h*.105,h*.070,skirt,8))
        objs.append(wedge('FemaleBowL',(-h*.030,-h*.083,h*.660),(h*.035,h*.010,h*.025),-.35,accent)); objs.append(wedge('FemaleBowR',(h*.030,-h*.083,h*.660),(h*.035,h*.010,h*.025),.35,accent))
    else:
        jacket=mat('MaleJacket',(.55,.67,.86)); shirt=mat('MaleShirt',(.88,.92,.97)); shorts=mat('MaleShorts',(.32,.40,.58))
        objs.append(frustum('MalePaperJacket',h*.535,h*.730,h*.125,h*.075,h*.155,h*.082,jacket,8))
        objs.append(frustum('MalePaperShirt',h*.555,h*.705,h*.095,h*.078,h*.105,h*.080,shirt,8))
        objs.append(frustum('MalePaperShorts',h*.445,h*.555,h*.140,h*.082,h*.120,h*.076,shorts,8))
    for o in objs:
        for p in o.data.polygons: p.use_smooth=False
    return objs

def make(kind):
    base,fs=parse_obj_body(fetch_text(BASE_URL)); phenotype(kind,base); vs,fs,h=stylize(kind,base,fs)
    skin=mat(kind+'BodySkin',(.95,.76,.68) if kind=='female' else (.86,.72,.66))
    body=mesh(kind.capitalize()+'AnimeOrigamiBody',vs,fs,skin); before,after=decimate(body,BODY_TARGET)
    extras=face_and_hair(kind,h)+outfit(kind,h)
    return [body]+extras,before,after,h

def export(kind):
    clear_scene(); obs,b,a,h=make(kind); bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]; bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR,kind+'.glb'),export_format='GLB',use_selection=True)
    return b,a,sum(tris(o) for o in obs),h

def studio():
    sc=bpy.context.scene; sc.render.resolution_x=1500; sc.render.resolution_y=1000; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.engine='BLENDER_EEVEE'; sc.world.color=(.055,.058,.075)
    try: sc.view_settings.look='AgX - Medium High Contrast'
    except: pass
    bpy.ops.mesh.primitive_plane_add(size=7,location=(0,0,-.004)); bpy.context.object.data.materials.append(mat('Floor',(.16,.17,.21)))
    for n,loc,en,size in [('Key',(-3.2,-4.2,4.4),1300,3.0),('Fill',(3.1,-3.0,2.6),560,2.5),('Rim',(0,3.7,3.6),920,2.2)]:
        ld=bpy.data.lights.new(n,'AREA'); ld.energy=en; ld.shape='DISK'; ld.size=size; o=bpy.data.objects.new(n,ld); bpy.context.collection.objects.link(o); o.location=loc; o.rotation_euler=(Vector((0,0,.82))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); bpy.context.collection.objects.link(cam); cam.location=(2.25,-5.5,1.74); cam.rotation_euler=(Vector((0,0,.78))-Vector(cam.location)).to_track_quat('-Z','Y').to_euler(); cd.lens=72; sc.camera=cam

def render_pair():
    clear_scene(); m,mb,ma,mh=make('male'); f,fb,fa,fh=make('female')
    for o in m: o.location.x-=.54; o.rotation_euler[2]=math.radians(-3)
    for o in f: o.location.x+=.54; o.rotation_euler[2]=math.radians(4)
    studio(); bpy.context.scene.render.filepath=os.path.join(OUT_DIR,'male-female-origami.png'); bpy.ops.render.render(write_still=True)
    return sum(tris(o) for o in m),sum(tris(o) for o in f)

mb,ma,mt,mh=export('male'); fb,fa,ft,fh=export('female'); rmt,rft=render_pair()
metrics={'style':'cute-anime-paper-sculpture-v6','source':'Anny/MPFB2 CC0 body + sparse phenotype targets','body_target_tris':BODY_TARGET,'male_body_tris':ma,'female_body_tris':fa,'male_total_tris':mt,'female_total_tris':ft,'render_male_total_tris':rmt,'render_female_total_tris':rft,'male_height_m':mh,'female_height_m':fh,'geometry_style':['4.8-5.2 head proportions','tapered anime jaw','large almond anime eyes','layered faceted paper hair','lowered friendly base pose','semantic default paper outfit','flat origami facets'],'blender_version':'.'.join(map(str,bpy.app.version))}
with open(os.path.join(OUT_DIR,'metrics.json'),'w',encoding='utf-8') as f: json.dump(metrics,f,indent=2)
print('ORIGAMI_HUMAN_V6_METRICS',json.dumps(metrics))
