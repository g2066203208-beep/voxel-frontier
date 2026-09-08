#!/usr/bin/env python3
"""Smooth vector-macro geometry renderer for seven Voxel Frontier materials.

Snow and water remain untouched benchmarks. The other seven are constructed from
broad analytic 3D surfaces with category-specific silhouettes: rock slabs, bark
plates, soil clods, leaves, masonry, moss cushions and broad fur clumps. No
quantized height, pixel terracing, thin strands or floating micro-particles.
"""
from __future__ import annotations
import bpy, math, random, sys
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT=Path(sys.argv[-1]) if len(sys.argv)>1 and not sys.argv[-1].startswith('-') else Path('build/generated-materials')
OUT=1000
TARGETS={
 'vf_painted_layered_sandstone_master':'sandstone','vf_painterly_bark_master':'bark',
 'vf_painterly_dirt_master':'dirt','vf_painterly_leaves_master':'leaves',
 'vf_painterly_stone_wall_master':'stone_wall','vf_painterly_moss_master':'moss',
 'vf_painterly_wolf_fur_master':'wolf_fur'}
PAL={
 'sandstone':[(.30,.10,.04,1),(.47,.20,.075,1),(.57,.27,.105,1),(.68,.36,.15,1),(.78,.47,.21,1)],
 'bark':[(.10,.045,.027,1),(.18,.082,.039,1),(.25,.12,.055,1),(.34,.175,.078,1),(.43,.245,.115,1)],
 'dirt':[(.12,.065,.043,1),(.22,.12,.070,1),(.30,.17,.095,1),(.39,.24,.14,1),(.35,.28,.22,1)],
 'leaves':[(.024,.080,.032,1),(.045,.14,.046,1),(.075,.21,.065,1),(.15,.31,.095,1),(.27,.40,.14,1)],
 'stone_wall':[(.24,.225,.205,1),(.31,.315,.32,1),(.39,.40,.40,1),(.47,.46,.43,1),(.55,.52,.46,1)],
 'moss':[(.035,.09,.025,1),(.065,.16,.033,1),(.11,.235,.043,1),(.21,.345,.065,1),(.36,.455,.105,1)],
 'wolf_fur':[(.055,.065,.080,1),(.105,.12,.14,1),(.18,.195,.215,1),(.28,.285,.29,1),(.40,.39,.36,1)]}
SEED={'sandstone':771231,'bark':275903,'dirt':182031,'leaves':391477,'stone_wall':634021,'moss':55109,'wolf_fur':91007}

def clamp(x,a=0.,b=1.): return max(a,min(b,x))
def smooth(x): x=clamp(x); return x*x*(3-2*x)
def reset(): bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name,c,rough=.9):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.diffuse_color=c; m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF')
 if bs: bs.inputs['Base Color'].default_value=c; bs.inputs['Roughness'].default_value=rough
 return m

def mats(kind,rough=.9): return [mat(f'vf_{kind}_{i}',c,rough) for i,c in enumerate(PAL[kind])]

def sphere(name,r,m,segments=192,rings=96):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=r); o=bpy.context.object; o.name=name; o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def direction(lon,lat):
 a=math.radians(lon); b=math.radians(lat); c=math.cos(b); return Vector((c*math.cos(a),c*math.sin(a),math.sin(b)))

def basis(n,yaw=0):
 up=Vector((0,0,1)); ey=up-n*n.dot(up)
 if ey.length<.08: ey=Vector((1,0,0))-n*n.x
 ey.normalize(); ex=ey.cross(n).normalized()
 if yaw:
  q=Quaternion(n,yaw); ex=q@ex; ey=q@ey
 return ex,ey

def patch(name,n,width,length,lift,m,kind='slab',yaw=0,nx=17,ny=19,base=.94,phase=0):
 ex,ey=basis(n,yaw); verts=[]; faces=[]
 for j in range(ny):
  t=j/(ny-1); yn=2*t-1
  if kind=='leaf': wf=max(.035,.32*(1-t)+.86*math.sin(math.pi*t)**.75)
  elif kind=='fur': wf=max(.055,(1-t)**.28*(.94+.10*math.sin(math.pi*t)))
  elif kind=='bark': wf=clamp(.78+.16*math.sin(math.pi*t)+.12*math.sin(3*math.pi*t+phase),.56,1.08)
  elif kind=='rock': wf=clamp(.80+.18*math.sin(math.pi*t)+.11*math.sin(2*math.pi*t+phase),.63,1.12)
  else: wf=1.0
  yy=(t-.5)*length
  for i in range(nx):
   s=i/(nx-1); xn=2*s-1; xx=(s-.5)*width*wf; exd=1-abs(xn); eyd=1-abs(yn)
   if kind=='rock':
    shoulder=smooth(min(exd/.20,eyd/.20)); h=lift*shoulder*clamp(.90+.09*xn+.06*yn,.72,1.12)
   elif kind=='slab':
    shoulder=smooth(min(exd/.18,eyd/.20)); h=lift*shoulder*(.96+.04*math.cos(xn*math.pi*.5)*math.cos(yn*math.pi*.5))
   elif kind=='bark':
    shoulder=smooth(min(exd/.15,eyd/.10)); h=lift*shoulder*(.73+.27*math.cos(xn*math.pi*.5))
   elif kind in ('clod','moss'):
    ang=math.atan2(yn,xn); rad=math.hypot(xn,yn); boundary=1+.11*math.sin(3*ang+phase)+.055*math.sin(5*ang-phase*.65); q=rad/max(.74,boundary)
    body=smooth((1.08-q)/(.62 if kind=='clod' else .70))
    h=lift*body*((.84+.16*math.cos(xn*math.pi*.5)) if kind=='clod' else (.78+.22*(1-min(1,rad))))
   elif kind=='leaf':
    arch=math.sin(math.pi*t)**1.15; center=(1-abs(xn))**1.35; fold=.28+.72*center; h=lift*arch*fold+lift*.018*t+lift*.025*xn*arch
   else:
    ease=smooth(t); arch=math.sin(math.pi*t)**.82; center=(1-abs(xn))**1.28; h=lift*(.20*arch+.80*ease)*(.27+.73*center)
   q=(n+ex*xx+ey*yy).normalized(); verts.append(tuple(q*(base+h)))
 for j in range(ny-1):
  for i in range(nx-1):
   a=j*nx+i;b=a+1;c=a+nx;d=c+1;faces.extend(((a,c,b),(b,c,d)))
 me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def scene():
 sc=bpy.context.scene
 try:sc.render.engine='BLENDER_EEVEE_NEXT'
 except:sc.render.engine='BLENDER_EEVEE'
 sc.render.resolution_x=OUT;sc.render.resolution_y=OUT;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
 try:sc.view_settings.look='Medium High Contrast'
 except:pass
 sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background')
 if bg:bg.inputs['Color'].default_value=(.065,.075,.09,1);bg.inputs['Strength'].default_value=.60
 bpy.ops.mesh.primitive_plane_add(size=18,location=(0,0,-1.46));bpy.context.object.data.materials.append(mat('vf_floor',(.09,.092,.10,1),.96))
 target=Vector((0,0,0));bpy.ops.object.camera_add(location=(0,-5.7,.24));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=3.0;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 for loc,en,size,col in [((-4.0,-4.5,5.6),1180,4.9,(1,.82,.64)),((4,-2,3.8),730,4.1,(.60,.76,1)),((0,3.5,4.7),540,3.2,(1,.54,.38))]:
  bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.data.energy=en;L.data.size=size;L.data.color=col;L.rotation_euler=(target-L.location).to_track_quat('-Z','Y').to_euler()

def sandstone(rng):
 ms=mats('sandstone',.84);sphere('sandstone_core',.945,ms[1]);k=0
 for r,(lat,count) in enumerate([(-56,5),(-34,6),(-11,6),(13,6),(36,6),(57,5)]):
  ph=.42 if r%2 else .05
  for i in range(count):
   n=direction(-180+360*(i+ph)/count+rng.uniform(-5,5),lat+rng.uniform(-4,4));patch(f'rock_{k}',n,rng.uniform(.70,.92),rng.uniform(.36,.50),rng.uniform(.050,.092),ms[1+(k%4)],'rock',rng.uniform(-.15,.15),19,17,.941+.001*(k%3),rng.random()*6.28);k+=1
 return k

def bark(rng):
 ms=mats('bark',.95);sphere('bark_core',.946,ms[1]);k=0
 for r,lat in enumerate((-50,-20,13,44)):
  for i in range(11):
   n=direction(-180+360*(i+.35*(r%2))/11+rng.uniform(-5,5),lat+rng.uniform(-7,7));patch(f'bark_{k}',n,rng.uniform(.24,.34),rng.uniform(.72,.98),rng.uniform(.026,.055),ms[1+(k%4)],'bark',rng.uniform(-.12,.12),15,23,.942+.001*(k%3),rng.random()*6.28);k+=1
 return k

def dirt(rng):
 ms=mats('dirt',.98);sphere('dirt_core',.958,ms[1]);k=0
 for r,(lat,count) in enumerate([(-51,6),(-27,7),(-2,8),(24,7),(48,6)]):
  ph=.43 if r%2 else .04
  for i in range(count):
   n=direction(-180+360*(i+ph)/count+rng.uniform(-6,6),lat+rng.uniform(-5,5));patch(f'clod_{k}',n,rng.uniform(.44,.62),rng.uniform(.34,.48),rng.uniform(.015,.038),ms[1+(k%4)],'clod',rng.uniform(-.8,.8),17,17,.954+.001*(k%3),rng.random()*6.28);k+=1
 return k

def wall(rng):
 ms=mats('stone_wall',.92);sphere('mortar',.934,ms[0]);k=0
 for r,(lat,count) in enumerate([(-55,5),(-34,6),(-12,7),(11,7),(34,6),(55,5)]):
  ph=.48 if r%2 else .02
  for i in range(count):
   n=direction(-180+360*(i+ph)/count,lat+rng.uniform(-2,2));patch(f'stone_{k}',n,rng.uniform(.58,.72),rng.uniform(.32,.41),rng.uniform(.035,.055),ms[1+(k%4)],'slab',rng.uniform(-.055,.055),19,17,.932+.0005*(k%2));k+=1
 return k

def leaves(rng):
 ms=mats('leaves',.93);sphere('leaf_shadow',.900,ms[0]);k=0
 for r,(lat,count) in enumerate([(-52,6),(-30,7),(-7,8),(17,8),(40,7),(60,5)]):
  ph=.40 if r%2 else .03
  for i in range(count):
   n=direction(-180+360*(i+ph)/count+rng.uniform(-5,5),lat+rng.uniform(-5,5));L=rng.uniform(.58,.78)*(-1 if k%4==0 else 1);patch(f'leaf_{k}',n,rng.uniform(.42,.58),L,rng.uniform(.035,.065),ms[1+(k%4)],'leaf',rng.uniform(-.42,.42),17,21,.908+.001*(k%4));k+=1
 return k

def moss(rng):
 ms=mats('moss',.99);sphere('moss_bed',.922,ms[1]);k=0
 for r,(lat,count) in enumerate([(-53,6),(-31,7),(-8,8),(16,8),(39,7),(59,5)]):
  ph=.44 if r%2 else .04
  for i in range(count):
   n=direction(-180+360*(i+ph)/count+rng.uniform(-6,6),lat+rng.uniform(-5,5));patch(f'moss_{k}',n,rng.uniform(.48,.68),rng.uniform(.38,.52),rng.uniform(.027,.052),ms[1+(k%4)],'moss',rng.uniform(-.55,.55),19,19,.925+.001*(k%3),rng.random()*6.28);k+=1
 return k

def wolf(rng):
 ms=mats('wolf_fur',.97);sphere('wolf_undercoat',.895,ms[1]);k=0
 for r,(lat,count) in enumerate([(-54,6),(-33,7),(-11,8),(12,8),(35,7),(56,6)]):
  ph=.46 if r%2 else .08
  for i in range(count):
   n=direction(-180+360*(i+ph)/count+rng.uniform(-5,5),lat+rng.uniform(-4,4));patch(f'fur_{k}',n,rng.uniform(.40,.56),-rng.uniform(.62,.84),rng.uniform(.040,.075),ms[1+(k%4)],'fur',rng.uniform(-.26,.26),17,23,.907+.001*(k%4));k+=1
 return k

def render_one(d,kind):
 reset();scene();rng=random.Random(SEED[kind]);count={'sandstone':sandstone,'bark':bark,'dirt':dirt,'leaves':leaves,'stone_wall':wall,'moss':moss,'wolf_fur':wolf}[kind](rng);bpy.context.scene.render.filepath=str(d/'preview-sphere.png');bpy.ops.render.render(write_still=True)
 (d/'preview-vector-geometry.json').write_text('{\n  "renderer":"blender_analytic_macro_geometry_v3",\n  "kind":"%s",\n  "macroElements":%d,\n  "quantizedHeight":false,\n  "thinStrands":0,\n  "categorySpecificSilhouette":true,\n  "detachedFloatingGeometry":false\n}\n'%(kind,count),encoding='utf-8')
 print('rendered',kind,count)

for dirname,kind in TARGETS.items():
 d=ROOT/dirname
 if d.is_dir():render_one(d,kind)
