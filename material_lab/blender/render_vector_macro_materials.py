#!/usr/bin/env python3
"""Vector-like macro geometry material spheres for Voxel Frontier.

Snow and water deliberately stay on the existing renderer: they are the approved
visual benchmark. The other seven materials are rendered from analytic smooth
geometry, never from quantized height pixels. Broad attached forms overlap into
continuous surfaces instead of reading as isolated props pasted onto a ball.
"""
from __future__ import annotations
import bpy, math, random, sys
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(sys.argv[-1]) if len(sys.argv) > 1 and not sys.argv[-1].startswith('-') else Path('build/generated-materials')
OUT = 1000
BASE_R = 1.0

TARGETS = {
    'vf_painted_layered_sandstone_master': 'sandstone',
    'vf_painterly_bark_master': 'bark',
    'vf_painterly_dirt_master': 'dirt',
    'vf_painterly_leaves_master': 'leaves',
    'vf_painterly_stone_wall_master': 'stone_wall',
    'vf_painterly_moss_master': 'moss',
    'vf_painterly_wolf_fur_master': 'wolf_fur',
}

PAL = {
 'sandstone': [(0.28,0.095,0.040,1),(0.48,0.205,0.075,1),(0.61,0.300,0.115,1),(0.74,0.410,0.170,1),(0.84,0.535,0.245,1)],
 'bark': [(0.10,0.045,0.028,1),(0.19,0.085,0.040,1),(0.28,0.135,0.060,1),(0.39,0.205,0.095,1),(0.47,0.285,0.145,1)],
 'dirt': [(0.12,0.062,0.040,1),(0.23,0.120,0.067,1),(0.33,0.185,0.100,1),(0.43,0.275,0.155,1),(0.37,0.29,0.23,1)],
 'leaves': [(0.025,0.085,0.035,1),(0.050,0.155,0.050,1),(0.095,0.245,0.075,1),(0.20,0.365,0.115,1),(0.36,0.465,0.165,1)],
 'stone_wall': [(0.20,0.19,0.18,1),(0.30,0.31,0.32,1),(0.39,0.40,0.40,1),(0.49,0.47,0.43,1),(0.58,0.54,0.47,1)],
 'moss': [(0.035,0.095,0.025,1),(0.070,0.175,0.035,1),(0.13,0.275,0.050,1),(0.27,0.420,0.080,1),(0.45,0.535,0.125,1)],
 'wolf_fur': [(0.060,0.070,0.085,1),(0.12,0.135,0.155,1),(0.22,0.235,0.255,1),(0.34,0.34,0.34,1),(0.48,0.46,0.42,1)],
}
SEED = {'sandstone':771231,'bark':275903,'dirt':182031,'leaves':391477,'stone_wall':634021,'moss':55109,'wolf_fur':91007}

def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))
def smooth(t): t=clamp(t); return t*t*(3.0-2.0*t)

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name,color,rough=.88):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.diffuse_color=color; m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs: bs.inputs['Base Color'].default_value=color; bs.inputs['Roughness'].default_value=rough
    return m

def mats(kind,rough=.88): return [mat(f'vf_{kind}_{i}',c,rough) for i,c in enumerate(PAL[kind])]

def add_sphere(name,radius,material,segments=192,rings=96):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=(0,0,0))
    o=bpy.context.object; o.name=name; o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def direction(lon_deg,lat_deg):
    lon=math.radians(lon_deg); lat=math.radians(lat_deg); c=math.cos(lat)
    return Vector((c*math.cos(lon),c*math.sin(lon),math.sin(lat)))

def tangent_basis(n,yaw=0.0):
    up=Vector((0,0,1)); ey=up-n*n.dot(up)
    if ey.length<.08: ey=Vector((1,0,0))-n*n.x
    ey.normalize(); ex=ey.cross(n).normalized()
    if yaw:
        q=Quaternion(n,yaw); ex=q@ex; ey=q@ey
    return ex,ey

def patch(name,n,width,length,lift,material,kind='slab',yaw=0.0,nx=15,ny=19,base_r=BASE_R):
    ex,ey=tangent_basis(n,yaw); verts=[]; faces=[]
    for j in range(ny):
        t=j/(ny-1); yy=(t-.5)*length
        if kind=='leaf': wf=max(.11,math.sin(math.pi*t)**.72)
        elif kind=='fur': wf=max(.14,(1-t)**.22*(.88+.14*math.sin(math.pi*t)))
        elif kind=='bark': wf=.91+.09*math.sin(math.pi*t)
        else: wf=1.0
        for i in range(nx):
            s=i/(nx-1); xx=(s-.5)*width*wf; edge_x=1-abs(2*s-1); edge_y=1-abs(2*t-1)
            if kind=='slab':
                shoulder=smooth(min(edge_x/.22,edge_y/.24)); crown=.92+.08*math.cos((2*s-1)*math.pi*.5)*math.cos((2*t-1)*math.pi*.5); h=lift*shoulder*crown
            elif kind=='clod':
                q=(2*s-1)**2+(2*t-1)**2; h=lift*smooth((1.10-q)/.68)*(.88+.12*math.cos((2*s-1)*math.pi*.5))
            elif kind=='bark':
                shoulder=smooth(min(edge_x/.16,edge_y/.11)); h=lift*shoulder*(.76+.24*math.cos((2*s-1)*math.pi*.5))
            elif kind=='moss':
                q=(2*s-1)**2+(2*t-1)**2; body=smooth((1.18-q)/.72); h=lift*body*(.82+.18*edge_x)+lift*.08*math.sin(math.pi*t)*edge_x
            elif kind=='leaf':
                arch=math.sin(math.pi*t)**1.18; camber=.30+.70*math.sin(math.pi*s)**1.35; h=lift*arch*camber+lift*.035*t
            else:
                ease=smooth(t); arch=math.sin(math.pi*t)**.82; camber=.28+.72*math.sin(math.pi*s)**1.3; h=lift*(.22*arch+.78*ease)*camber
            q=(n+ex*xx+ey*yy).normalized(); verts.append(tuple(q*(base_r+h)))
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i; b=a+1; c=a+nx; d=c+1; faces.extend(((a,c,b),(b,c,d)))
    me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def scene_setup(kind):
    sc=bpy.context.scene
    try: sc.render.engine='BLENDER_EEVEE_NEXT'
    except: sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=OUT; sc.render.resolution_y=OUT; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
    try: sc.view_settings.look='Medium High Contrast'
    except: pass
    sc.world.use_nodes=True; bg=sc.world.node_tree.nodes.get('Background')
    if bg: bg.inputs['Color'].default_value=(.060,.070,.085,1); bg.inputs['Strength'].default_value=.52
    bpy.ops.mesh.primitive_plane_add(size=18,location=(0,0,-1.46)); bpy.context.object.data.materials.append(mat('vf_floor',(0.085,0.088,0.098,1),.96))
    target=Vector((0,0,0)); bpy.ops.object.camera_add(location=(0,-5.7,.28)); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=3.05; cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); sc.camera=cam
    for loc,en,size,col in [((-4.0,-4.5,5.6),1120,4.8,(1.0,.80,.60)),((4.0,-2.0,3.8),700,4.0,(.58,.74,1.0)),((0.0,3.5,4.7),520,3.0,(1.0,.50,.34))]:
        bpy.ops.object.light_add(type='AREA',location=loc); L=bpy.context.object; L.data.energy=en; L.data.size=size; L.data.color=col; L.rotation_euler=(target-L.location).to_track_quat('-Z','Y').to_euler()

def build_sandstone(rng):
    ms=mats('sandstone',.82); add_sphere('sandstone_core',.952,ms[1]); k=0
    for r,(lat,count) in enumerate([(-55,5),(-34,6),(-13,7),(9,7),(31,6),(52,5)]):
        phase=.30 if r%2 else .02
        for i in range(count):
            lon=-180+360*(i+phase)/count+rng.uniform(-4,4); n=direction(lon,lat+rng.uniform(-3,3))
            patch(f'rock_slab_{k}',n,rng.uniform(.62,.82),rng.uniform(.30,.40),rng.uniform(.055,.100),ms[1+(k%4)],'slab',rng.uniform(-.10,.10),17,15,.946+.001*(k%3)); k+=1
    return k

def build_bark(rng):
    ms=mats('bark',.94); add_sphere('bark_core',.958,ms[1]); k=0
    for r,lat in enumerate((-48,-18,15,46)):
        for i in range(12):
            lon=-180+30*(i+.25*(r%2))+rng.uniform(-4,4); n=direction(lon,lat+rng.uniform(-6,6))
            patch(f'bark_plate_{k}',n,rng.uniform(.19,.27),rng.uniform(.65,.86),rng.uniform(.028,.060),ms[1+(k%4)],'bark',rng.uniform(-.09,.09),13,21,.952+.001*(k%3)); k+=1
    return k

def build_dirt(rng):
    ms=mats('dirt',.97); add_sphere('dirt_core',.972,ms[1]); k=0
    for r,(lat,count) in enumerate([(-48,6),(-22,7),(5,7),(31,7),(52,5)]):
        phase=.40 if r%2 else .05
        for i in range(count):
            lon=-180+360*(i+phase)/count+rng.uniform(-6,6); n=direction(lon,lat+rng.uniform(-5,5))
            patch(f'soil_clod_{k}',n,rng.uniform(.38,.54),rng.uniform(.27,.40),rng.uniform(.018,.044),ms[1+(k%4)],'clod',rng.uniform(-.7,.7),15,15,.966+.001*(k%3)); k+=1
    return k

def build_stone_wall(rng):
    ms=mats('stone_wall',.90); add_sphere('mortar',.920,ms[0]); k=0
    for r,(lat,count) in enumerate([(-55,5),(-34,6),(-12,7),(11,7),(34,6),(55,5)]):
        phase=.48 if r%2 else .02
        for i in range(count):
            lon=-180+360*(i+phase)/count; n=direction(lon,lat+rng.uniform(-2.5,2.5))
            patch(f'wall_stone_{k}',n,rng.uniform(.52,.66),rng.uniform(.28,.37),rng.uniform(.045,.070),ms[1+(k%4)],'slab',rng.uniform(-.06,.06),17,15,.918+.0007*(k%2)); k+=1
    return k

def build_leaves(rng):
    ms=mats('leaves',.91); add_sphere('leaf_shadow_core',.918,ms[0]); k=0
    for r,(lat,count) in enumerate([(-50,6),(-28,7),(-5,8),(20,8),(44,7),(62,5)]):
        phase=.38 if r%2 else .02
        for i in range(count):
            lon=-180+360*(i+phase)/count+rng.uniform(-5,5); n=direction(lon,lat+rng.uniform(-5,5)); sign=-1 if (k%3==0) else 1
            patch(f'leaf_{k}',n,rng.uniform(.36,.50),sign*rng.uniform(.50,.64),rng.uniform(.042,.075),ms[1+(k%4)],'leaf',rng.uniform(-.40,.40),15,19,.925+.001*(k%4)); k+=1
    return k

def build_moss(rng):
    ms=mats('moss',.98); add_sphere('moss_bed',.938,ms[1]); k=0
    for r,(lat,count) in enumerate([(-50,5),(-29,6),(-7,7),(17,7),(40,6),(59,5)]):
        phase=.42 if r%2 else .05
        for i in range(count):
            lon=-180+360*(i+phase)/count+rng.uniform(-6,6); n=direction(lon,lat+rng.uniform(-5,5))
            patch(f'moss_cushion_{k}',n,rng.uniform(.43,.60),rng.uniform(.33,.46),rng.uniform(.030,.058),ms[1+(k%4)],'moss',rng.uniform(-.5,.5),17,17,.936+.001*(k%3)); k+=1
    return k

def build_wolf(rng):
    ms=mats('wolf_fur',.96); add_sphere('wolf_undercoat',.925,ms[1]); k=0
    for r,(lat,count) in enumerate([(-48,6),(-27,7),(-5,7),(18,7),(42,6),(60,5)]):
        phase=.46 if r%2 else .08
        for i in range(count):
            lon=-180+360*(i+phase)/count+rng.uniform(-5,5); n=direction(lon,lat+rng.uniform(-4,4))
            patch(f'fur_clump_{k}',n,rng.uniform(.34,.46),-rng.uniform(.52,.70),rng.uniform(.050,.092),ms[1+(k%4)],'fur',rng.uniform(-.24,.24),15,21,.930+.001*(k%4)); k+=1
    return k

def render_one(d,kind):
    reset(); scene_setup(kind); rng=random.Random(SEED[kind]); count={'sandstone':build_sandstone,'bark':build_bark,'dirt':build_dirt,'leaves':build_leaves,'stone_wall':build_stone_wall,'moss':build_moss,'wolf_fur':build_wolf}[kind](rng)
    sc=bpy.context.scene; sc.render.filepath=str(d/'preview-sphere.png'); bpy.ops.render.render(write_still=True)
    (d/'preview-vector-geometry.json').write_text('{\n  "renderer": "blender_analytic_macro_geometry_v2",\n  "style": "snow-water-benchmark-overlapping-vector-macro",\n  "kind": "%s",\n  "macroElements": %d,\n  "thinStrands": 0,\n  "quantizedHeight": false,\n  "overlappingCoverage": true,\n  "detachedFloatingGeometry": false\n}\n' % (kind,count),encoding='utf-8')
    print('rendered',kind,count,d/'preview-sphere.png')

for dirname,kind in TARGETS.items():
    d=ROOT/dirname
    if d.is_dir(): render_one(d,kind)
