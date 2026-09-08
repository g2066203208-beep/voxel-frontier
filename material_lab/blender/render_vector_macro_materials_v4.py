#!/usr/bin/env python3
"""V4 painterly vector-macro material spheres.
Snow/water are intentionally untouched. The other seven use smooth analytic 3D
geometry plus their own procedural BaseColor/Roughness bakes, so geometry and
paint read as one continuous material instead of separate solid-color props.
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
SEED={'sandstone':771231,'bark':275903,'dirt':182031,'leaves':391477,'stone_wall':634021,'moss':55109,'wolf_fur':91007}

def clamp(x,a=0.,b=1.): return max(a,min(b,x))
def smooth(x): x=clamp(x); return x*x*(3-2*x)
def wrap(a): return (a+math.pi)%(2*math.pi)-math.pi

def reset(): bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def flat_mat(name,c,rough=.94):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=c; bs.inputs['Roughness'].default_value=rough
 return m

def pbr_mat(d:Path,name:str):
 m=bpy.data.materials.new('paint_'+name); m.use_nodes=True; n=m.node_tree.nodes; l=m.node_tree.links; n.clear()
 out=n.new('ShaderNodeOutputMaterial'); bs=n.new('ShaderNodeBsdfPrincipled'); uv=n.new('ShaderNodeTexCoord')
 col=n.new('ShaderNodeTexImage'); col.image=bpy.data.images.load(str((d/f'{name}_baseColor.png').resolve()),check_existing=True); col.interpolation='Linear'
 hs=n.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value=.90; hs.inputs['Value'].default_value=1.14; hs.inputs['Fac'].default_value=1.0
 rou=n.new('ShaderNodeTexImage'); rou.image=bpy.data.images.load(str((d/f'{name}_roughness.png').resolve()),check_existing=True); rou.image.colorspace_settings.name='Non-Color'; rou.interpolation='Linear'
 l.new(uv.outputs['UV'],col.inputs['Vector']); l.new(col.outputs['Color'],hs.inputs['Color']); l.new(hs.outputs['Color'],bs.inputs['Base Color'])
 l.new(uv.outputs['UV'],rou.inputs['Vector']); l.new(rou.outputs['Color'],bs.inputs['Roughness']); l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 return m

def set_uv(o):
 me=o.data
 if not hasattr(me,'uv_layers'): return
 uv=me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  for li in p.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co.normalized(); u=(.5+math.atan2(co.y,co.x)/(2*math.pi))%1.; v=.5+math.asin(clamp(co.z,-1,1))/math.pi; uv.data[li].uv=(u,v)

def sphere(name,r,m,field=None,seg=224,rings=112):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=r); o=bpy.context.object; o.name=name; o.data.materials.append(m)
 if field:
  for v in o.data.vertices:
   q=v.co.normalized(); v.co=q*field(q)
 for p in o.data.polygons:p.use_smooth=True
 set_uv(o); return o

def direction(lon,lat):
 a=math.radians(lon);b=math.radians(lat);c=math.cos(b);return Vector((c*math.cos(a),c*math.sin(a),math.sin(b)))

def fib(count,rng):
 ga=math.pi*(3-math.sqrt(5)); out=[]
 for i in range(count):
  z=1-2*(i+.5)/count; rr=math.sqrt(max(0,1-z*z)); a=i*ga+rng.uniform(-.10,.10); q=Vector((rr*math.cos(a),rr*math.sin(a),z)); out.append(q)
 return out

def basis(n,yaw=0):
 up=Vector((0,0,1)); ey=up-n*n.dot(up)
 if ey.length<.08: ey=Vector((1,0,0))-n*n.x
 ey.normalize(); ex=ey.cross(n).normalized()
 if yaw:
  q=Quaternion(n,yaw); ex=q@ex;ey=q@ey
 return ex,ey

def mesh_obj(name,verts,faces,m):
 me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 set_uv(o);return o

def card(name,n,width,length,lift,m,kind,phase=0,yaw=0,base=.94,nx=17,ny=23):
 ex,ey=basis(n,yaw);verts=[];faces=[]
 for j in range(ny):
  t=j/(ny-1)
  if kind=='fur': yy=(.5-t)*length; wf=max(.045,(1-t)**.34*(.93+.07*math.sin(2*math.pi*t+phase)))
  else: yy=(t-.5)*length; wf=max(.035,.13*(1-t)+.92*math.sin(math.pi*t)**.72)
  for i in range(nx):
   s=i/(nx-1);xn=2*s-1;xx=(s-.5)*width*wf;center=(1-abs(xn))**1.35
   if kind=='fur': h=lift*(.13*math.sin(math.pi*t)+.87*smooth(t))*(.26+.74*center)
   else:
    arch=math.sin(math.pi*t)**1.16; h=lift*arch*(.30+.70*center)+lift*.020*xn*arch
   q=(n+ex*xx+ey*yy).normalized();verts.append(tuple(q*(base+h)))
 for j in range(ny-1):
  for i in range(nx-1):a=j*nx+i;b=a+1;c=a+nx;dd=c+1;faces.extend(((a,c,b),(b,c,dd)))
 return mesh_obj(name,verts,faces,m)

def slab(name,n,width,length,lift,m,phase=0,yaw=0,base=.935,nx=19,ny=17):
 ex,ey=basis(n,yaw);verts=[];faces=[]
 for j in range(ny):
  t=j/(ny-1);yn=2*t-1; wf=clamp(.82+.15*math.sin(math.pi*t)+.10*math.sin(2*math.pi*t+phase),.62,1.10); yy=(t-.5)*length
  for i in range(nx):
   s=i/(nx-1);xn=2*s-1;xx=(s-.5)*width*wf+.035*width*yn*math.sin(phase);exd=1-abs(xn);eyd=1-abs(yn);sh=smooth(min(exd/.18,eyd/.20));h=lift*sh*clamp(.94+.07*xn+.04*yn,.78,1.12);q=(n+ex*xx+ey*yy).normalized();verts.append(tuple(q*(base+h)))
 for j in range(ny-1):
  for i in range(nx-1):a=j*nx+i;b=a+1;c=a+nx;dd=c+1;faces.extend(((a,c,b),(b,c,dd)))
 return mesh_obj(name,verts,faces,m)

def cap(n,c,rad):
 t=(n.dot(c)-math.cos(rad))/(1-math.cos(rad));return smooth(t)

def setup():
 sc=bpy.context.scene
 try:sc.render.engine='BLENDER_EEVEE_NEXT'
 except:sc.render.engine='BLENDER_EEVEE'
 sc.render.resolution_x=OUT;sc.render.resolution_y=OUT;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
 try:sc.view_settings.look='Medium High Contrast'
 except:pass
 sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.07,.08,.095,1);bg.inputs['Strength'].default_value=.62
 bpy.ops.mesh.primitive_plane_add(size=18,location=(0,0,-1.47));bpy.context.object.data.materials.append(flat_mat('floor',(.09,.095,.105,1),.97))
 target=Vector((0,0,0));bpy.ops.object.camera_add(location=(0,-5.7,.24));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=3.00;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 for loc,en,size,col in [((-4.0,-4.5,5.7),1250,5.0,(1,.83,.67)),((4,-2,3.8),760,4.2,(.62,.78,1)),((0,3.6,4.8),560,3.2,(1,.55,.40))]:
  bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.data.energy=en;L.data.size=size;L.data.color=col;L.rotation_euler=(target-L.location).to_track_quat('-Z','Y').to_euler()

def build_sandstone(m,rng):
 bands=[(-.72,.18,.060,2,.3),(-.40,.16,.075,3,1.1),(-.10,.17,.090,2,2.0),(.20,.18,.080,3,.4),(.50,.17,.068,2,1.7),(.76,.15,.052,3,2.5)]
 def field(n):
  lat=math.asin(n.z);lon=math.atan2(n.y,n.x);r=.970
  for c,w,a,k,p in bands:
   q=math.exp(-((lat-c)/w)**4);sector=.72+.28*(.5+.5*math.sin(k*lon+p+.25*math.sin(lat*3)));r+=a*q*sector
  r+=.010*math.sin(2*lon+.6)*math.cos(lat);return r
 sphere('layered_sandstone',1,m,field);return len(bands)

def build_bark(m,rng):
 centers=[-math.pi+2*math.pi*(i+.18*rng.random())/11 for i in range(11)]; widths=[rng.uniform(.13,.20) for _ in centers];ph=[rng.random()*6.28 for _ in centers]
 def field(n):
  lon=math.atan2(n.y,n.x);z=n.z;best=0
  for c,w,p in zip(centers,widths,ph):
   cc=c+.10*math.sin(2.1*z+p)+.035*math.sin(5*z-p);d=wrap(lon-cc);best=max(best,math.exp(-(d/w)**4))
  return .970+.055*best*(.80+.20*math.cos(z*2.4))+.008*math.sin(3*z+1.3*lon)
 sphere('continuous_bark',1,m,field);return len(centers)

def build_dirt(m,rng):
 cs=[(q,rng.uniform(.30,.48),rng.uniform(.018,.040)) for q in fib(19,rng)]; pits=[(q,rng.uniform(.20,.30),rng.uniform(.006,.015)) for q in fib(7,rng)]
 def field(n):
  up=0;dn=0
  for c,rad,a in cs:up=max(up,a*cap(n,c,rad)*( .84+.16*math.sin(5*math.atan2(n.y,n.x)+c.z*3)))
  for c,rad,a in pits:dn=max(dn,a*cap(n,c,rad));return .985+up-dn
 sphere('continuous_dirt',1,m,field);return len(cs)+len(pits)

def build_moss(m,rng):
 cs=[(q,rng.uniform(.36,.56),rng.uniform(.030,.065)) for q in fib(15,rng)]
 def field(n):
  total=0
  for c,rad,a in cs: total=max(total,a*cap(n,c,rad))
  return .970+total
 sphere('continuous_moss',1,m,field)
 # Only a few broad lifted carpet edges break the silhouette.
 for i,c in enumerate(cs[:6]): card(f'moss_edge_{i}',c[0],rng.uniform(.38,.54),rng.uniform(.36,.50),rng.uniform(.020,.040),m,'leaf',rng.random()*6.28,rng.uniform(-.5,.5),.968,15,19)
 return len(cs)+6

def build_leaves(m,rng):
 sphere('leaf_shadow',.900,m); pts=fib(30,rng)
 for i,n in enumerate(pts):card(f'leaf_{i}',n,rng.uniform(.38,.53),rng.uniform(.48,.66),rng.uniform(.045,.078),m,'leaf',rng.random()*6.28,rng.uniform(-.48,.48),.910+.001*(i%4),17,21)
 return len(pts)

def build_fur(m,rng):
 sphere('wolf_undercoat',.905,m);pts=fib(21,rng)
 for i,n in enumerate(pts):card(f'fur_{i}',n,rng.uniform(.46,.62),rng.uniform(.68,.88),rng.uniform(.050,.085),m,'fur',rng.random()*6.28,rng.uniform(-.28,.28),.915+.001*(i%4),17,23)
 return len(pts)

def build_wall(m,rng):
 sphere('mortar',.930,flat_mat('mortar',(.22,.21,.20,1),.97));k=0
 for r,(lat,count) in enumerate([(-54,5),(-32,6),(-10,7),(13,7),(35,6),(56,5)]):
  ph=.47 if r%2 else .02
  for i in range(count):n=direction(-180+360*(i+ph)/count,lat+rng.uniform(-2,2));slab(f'stone_{k}',n,rng.uniform(.56,.72),rng.uniform(.30,.41),rng.uniform(.035,.057),m,rng.random()*6.28,rng.uniform(-.06,.06),.928+.0005*(k%2));k+=1
 return k

def render_one(d,kind):
 reset();setup();rng=random.Random(SEED[kind]);m=pbr_mat(d,d.name)
 count={'sandstone':build_sandstone,'bark':build_bark,'dirt':build_dirt,'leaves':build_leaves,'moss':build_moss,'wolf_fur':build_fur,'stone_wall':build_wall}[kind](m,rng)
 bpy.context.scene.render.filepath=str(d/'preview-sphere.png');bpy.ops.render.render(write_still=True)
 (d/'preview-vector-geometry.json').write_text('{\n "renderer":"blender_vector_macro_v4_pbr_continuous",\n "kind":"%s",\n "macroElements":%d,\n "usesProceduralBakedPaint":true,\n "quantizedHeight":false,\n "thinStrands":0,\n "detachedFloatingGeometry":false\n}\n'%(kind,count),encoding='utf-8')
 print('rendered',kind,count)

for dirname,kind in TARGETS.items():
 d=ROOT/dirname
 if d.is_dir():render_one(d,kind)
