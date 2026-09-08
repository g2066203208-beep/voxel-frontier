#!/usr/bin/env python3
"""Vector-like macro geometry material spheres for Voxel Frontier.

Snow and water deliberately stay on the existing renderer: they are the approved
visual benchmark.  The other seven materials are rendered from analytic smooth
geometry, not from quantized height pixels.  Every protrusion is a broad curved
surface attached to the sphere, so the silhouette is clean and the 3D height is
real rather than a staircase in a raster height map.
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
 'sandstone': [(0.22,0.070,0.030,1),(0.42,0.140,0.050,1),(0.67,0.300,0.090,1),(0.88,0.520,0.180,1),(0.94,0.680,0.300,1)],
 'bark': [(0.095,0.040,0.025,1),(0.18,0.075,0.035,1),(0.31,0.135,0.055,1),(0.48,0.235,0.095,1),(0.25,0.17,0.10,1)],
 'dirt': [(0.11,0.055,0.035,1),(0.22,0.105,0.055,1),(0.35,0.18,0.085,1),(0.50,0.29,0.15,1),(0.30,0.22,0.18,1)],
 'leaves': [(0.025,0.095,0.035,1),(0.055,0.18,0.055,1),(0.12,0.31,0.085,1),(0.30,0.49,0.15,1),(0.50,0.55,0.18,1)],
 'stone_wall': [(0.11,0.105,0.105,1),(0.24,0.25,0.27,1),(0.38,0.39,0.39,1),(0.53,0.50,0.44,1),(0.66,0.61,0.51,1)],
 'moss': [(0.035,0.10,0.025,1),(0.075,0.20,0.035,1),(0.18,0.36,0.055,1),(0.39,0.53,0.10,1),(0.58,0.62,0.16,1)],
 'wolf_fur': [(0.065,0.075,0.090,1),(0.13,0.145,0.165,1),(0.25,0.255,0.265,1),(0.39,0.37,0.34,1),(0.60,0.56,0.49,1)],
}

SEED = {'sandstone':771231,'bark':275903,'dirt':182031,'leaves':391477,'stone_wall':634021,'moss':55109,'wolf_fur':91007}


def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))
def smooth(t):
    t=clamp(t); return t*t*(3.0-2.0*t)

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.cameras,bpy.data.lights):
        pass

def mat(name, color, rough=.88):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=color; m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs:
        bs.inputs['Base Color'].default_value=color
        bs.inputs['Roughness'].default_value=rough
    return m

def mats(kind,rough=.88): return [mat(f'vf_{kind}_{i}',c,rough) for i,c in enumerate(PAL[kind])]

def add_sphere(name, radius, material, segments=192, rings=96):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=(0,0,0))
    o=bpy.context.object; o.name=name; o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def direction(lon_deg, lat_deg):
    lon=math.radians(lon_deg); lat=math.radians(lat_deg); c=math.cos(lat)
    return Vector((c*math.cos(lon),c*math.sin(lon),math.sin(lat)))

def tangent_basis(n:Vector, yaw=0.0):
    up=Vector((0,0,1)); ey=up-n*n.dot(up)
    if ey.length < 0.08: ey=Vector((1,0,0))-n*n.x
    ey.normalize(); ex=ey.cross(n).normalized()
    if yaw:
        q=Quaternion(n,yaw); ex=q@ex; ey=q@ey
    return ex,ey

def patch(name, n, width, length, lift, material, kind='slab', yaw=0.0, nx=13, ny=17, base_r=BASE_R):
    """Build one smooth broad surface patch attached to the sphere.

    kind=slab: rounded broad plateau with all four borders flush.
    kind=leaf: lens silhouette, root flush, crown lifted, pointed tip.
    kind=fur: wide tapered pelt card, root flush, soft lifted tip.
    kind=moss: broad rounded mat with a gently lifted outer lip.
    kind=clod: flattened soil mound, borders flush.
    kind=bark: long soft plate with flush borders and shallow crown.
    """
    ex,ey=tangent_basis(n,yaw); verts=[]; faces=[]
    for j in range(ny):
        t=j/(ny-1); yy=(t-.5)*length
        if kind in ('leaf','fur'):
            wf=max(.045, math.sin(math.pi*t)**(.72 if kind=='leaf' else .58))
        elif kind=='bark': wf=.90+.10*math.sin(math.pi*t)
        else: wf=1.0
        for i in range(nx):
            s=i/(nx-1); xx=(s-.5)*width*wf
            edge_x=1.0-abs(2*s-1); edge_y=1.0-abs(2*t-1)
            if kind=='slab':
                shoulder=smooth(min(edge_x/.24,edge_y/.26)); crown=.90+.10*math.cos((2*s-1)*math.pi*.5)*math.cos((2*t-1)*math.pi*.5); h=lift*shoulder*crown
            elif kind=='clod':
                q=(2*s-1)**2+(2*t-1)**2; h=lift*smooth((1.0-q)/.55)*(0.84+.16*math.cos((2*s-1)*math.pi*.5))
            elif kind=='bark':
                shoulder=smooth(min(edge_x/.20,edge_y/.14)); h=lift*shoulder*(.72+.28*math.cos((2*s-1)*math.pi*.5))
            elif kind=='moss':
                q=(2*s-1)**2+(2*t-1)**2; body=smooth((1.08-q)/.60); lip=smooth(edge_y/.35)*math.sin(math.pi*t)**1.2; h=lift*(.72*body+.28*lip)*(.78+.22*edge_x)
            elif kind=='leaf':
                arch=math.sin(math.pi*t)**1.25; camber=(.35+.65*math.sin(math.pi*s)**1.4); h=lift*arch*camber + lift*.06*t
            else: # fur
                ease=smooth(t); arch=math.sin(math.pi*t)**.85; camber=.30+.70*math.sin(math.pi*s)**1.45; h=lift*(.20*arch+.76*ease)*camber
            q=(n + ex*xx + ey*yy).normalized(); verts.append(tuple(q*(base_r+h)))
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i; b=a+1; c=a+nx; d=c+1; faces.append((a,c,b)); faces.append((b,c,d))
    me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def scene_setup(kind):
    sc=bpy.context.scene
    try: sc.render.engine='BLENDER_EEVEE_NEXT'
    except: sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=OUT; sc.render.resolution_y=OUT; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
    try:
        sc.view_settings.look='Medium High Contrast'
    except: pass
    sc.world.use_nodes=True; bg=sc.world.node_tree.nodes.get('Background')
    if bg: bg.inputs['Color'].default_value=(.055,.065,.080,1); bg.inputs['Strength'].default_value=.42
    floor=mat('vf_floor',(0.075,0.082,0.095,1),.95)
    bpy.ops.mesh.primitive_plane_add(size=18,location=(0,0,-1.48)); bpy.context.object.data.materials.append(floor)
    target=Vector((0,0,0)); bpy.ops.object.camera_add(location=(0,-5.7,.35)); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=3.25; cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); sc.camera=cam
    for loc,en,size,col in [((-4.0,-4.5,5.6),980,4.8,(1.0,.78,.57)),((4.0,-2.0,3.8),610,4.0,(.56,.72,1.0)),((0.0,3.5,4.7),460,3.0,(1.0,.46,.30))]:
        bpy.ops.object.light_add(type='AREA',location=loc); L=bpy.context.object; L.data.energy=en; L.data.size=size; L.data.color=col; L.rotation_euler=(target-L.location).to_track_quat('-Z','Y').to_euler()

def build_sandstone(rng):
    ms=mats('sandstone',.80); add_sphere('sandstone_core',.965,ms[1])
    rows=[(-48,5),(-24,6),(0,6),(24,6),(48,5)]
    k=0
    for lat,count in rows:
        offset=(lat%17)*2.7
        for i in range(count):
            lon=-180+360*(i+.5)/count+offset
            n=direction(lon,lat+rng.uniform(-4,4)); w=rng.uniform(.42,.58); L=rng.uniform(.25,.34); h=rng.uniform(.070,.125)
            patch(f'rock_slab_{k}',n,w,L,h,ms[2+(k%3)],'slab',yaw=rng.uniform(-.12,.12),nx=15,ny=13,base_r=.955); k+=1
    return k

def build_bark(rng):
    ms=mats('bark',.92); add_sphere('bark_core',.975,ms[1])
    k=0
    for ring_lat in (-34,0,34):
        for i in range(10):
            lon=-180+36*i+rng.uniform(-6,6); n=direction(lon,ring_lat+rng.uniform(-7,7))
            patch(f'bark_plate_{k}',n,rng.uniform(.12,.19),rng.uniform(.50,.70),rng.uniform(.035,.075),ms[2+(k%3)],'bark',yaw=rng.uniform(-.10,.10),nx=11,ny=19,base_r=.968); k+=1
    return k

def build_dirt(rng):
    ms=mats('dirt',.96); add_sphere('dirt_core',.990,ms[1])
    pts=[(-120,-42),(-70,-35),(-20,-43),(35,-34),(88,-42),(145,-30),(-150,-5),(-95,2),(-42,-2),(8,8),(55,-6),(110,4),(165,0),(-125,34),(-65,31),(-8,39),(48,33),(102,38),(155,31)]
    for k,(lon,lat) in enumerate(pts):
        n=direction(lon+rng.uniform(-7,7),lat+rng.uniform(-5,5)); patch(f'soil_clod_{k}',n,rng.uniform(.22,.36),rng.uniform(.16,.27),rng.uniform(.025,.055),ms[2+(k%3)],'clod',yaw=rng.uniform(-.6,.6),nx=13,ny=13,base_r=.982)
    return len(pts)

def build_stone_wall(rng):
    ms=mats('stone_wall',.88); add_sphere('mortar',.935,ms[0])
    k=0
    for r,(lat,count) in enumerate([(-52,5),(-28,6),(-4,7),(20,6),(44,5)]):
        offset=180/count*(r%2)
        for i in range(count):
            lon=-180+360*(i+.5)/count+offset; n=direction(lon,lat+rng.uniform(-3,3))
            patch(f'wall_stone_{k}',n,rng.uniform(.36,.47),rng.uniform(.22,.30),rng.uniform(.055,.085),ms[1+(k%4)],'slab',yaw=rng.uniform(-.08,.08),nx=15,ny=13,base_r=.930); k+=1
    return k

def build_leaves(rng):
    ms=mats('leaves',.89); add_sphere('leaf_shadow_core',.935,ms[0])
    k=0
    for lat,count in [(-38,6),(-6,7),(26,7),(51,5)]:
        for i in range(count):
            lon=-180+360*(i+.35*(k%2))/count; n=direction(lon,lat+rng.uniform(-5,5))
            patch(f'leaf_{k}',n,rng.uniform(.24,.34),rng.uniform(.34,.48),rng.uniform(.055,.100),ms[1+(k%4)],'leaf',yaw=rng.uniform(-.45,.45),nx=13,ny=17,base_r=.940); k+=1
    return k

def build_moss(rng):
    ms=mats('moss',.97); add_sphere('moss_bed',.965,ms[1]); k=0
    for lat,count in [(-40,5),(-10,6),(20,6),(48,5)]:
        for i in range(count):
            lon=-180+360*(i+.5)/count+rng.uniform(-7,7); n=direction(lon,lat+rng.uniform(-5,5))
            patch(f'moss_cushion_{k}',n,rng.uniform(.28,.42),rng.uniform(.22,.34),rng.uniform(.035,.070),ms[2+(k%3)],'moss',yaw=rng.uniform(-.5,.5),nx=15,ny=15,base_r=.958); k+=1
    return k

def build_wolf(rng):
    ms=mats('wolf_fur',.94); add_sphere('wolf_undercoat',.955,ms[1]); k=0
    # Few large pelt cards; not thousands of hairs and not a regular scale pattern.
    cards=[]
    for lat,count,phase in [(-42,5,.15),(-15,6,.45),(14,6,.05),(41,5,.35)]:
        for i in range(count): cards.append((-180+360*(i+phase)/count,lat))
    for lon,lat in cards:
        n=direction(lon+rng.uniform(-6,6),lat+rng.uniform(-5,5)); patch(f'fur_clump_{k}',n,rng.uniform(.24,.34),rng.uniform(.36,.50),rng.uniform(.065,.115),ms[1+(k%4)],'fur',yaw=rng.uniform(-.30,.30),nx=13,ny=19,base_r=.948); k+=1
    return k

def render_one(d:Path,kind:str):
    reset(); scene_setup(kind); rng=random.Random(SEED[kind]);
    count={'sandstone':build_sandstone,'bark':build_bark,'dirt':build_dirt,'leaves':build_leaves,'stone_wall':build_stone_wall,'moss':build_moss,'wolf_fur':build_wolf}[kind](rng)
    sc=bpy.context.scene; sc.render.filepath=str(d/'preview-sphere.png'); bpy.ops.render.render(write_still=True)
    (d/'preview-vector-geometry.json').write_text('{\n  "renderer": "blender_analytic_macro_geometry_v1",\n  "style": "snow-water-benchmark-vector-macro",\n  "kind": "%s",\n  "macroElements": %d,\n  "thinStrands": 0,\n  "quantizedHeight": false,\n  "detachedFloatingGeometry": false\n}\n' % (kind,count),encoding='utf-8')
    print('rendered',kind,count,d/'preview-sphere.png')

for dirname,kind in TARGETS.items():
    d=ROOT/dirname
    if d.is_dir(): render_one(d,kind)
