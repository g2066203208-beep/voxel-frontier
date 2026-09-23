#!/usr/bin/env python3
import json, math, re, sys, zipfile
from pathlib import Path

PREFIX="Sprite2D/Skeleton2D/"

def sectionize(text):
    starts=[m.start() for m in re.finditer(r'^\[',text,re.M)]
    out=[]
    for i,s in enumerate(starts):
        e=starts[i+1] if i+1<len(starts) else len(text)
        out.append(text[s:e])
    return out

def vec2(block,key,default=(0.0,0.0)):
    m=re.search(r'^'+re.escape(key)+r'\s*=\s*Vector2\(([^,]+),\s*([^\)]+)\)',block,re.M)
    return (float(m.group(1)),float(m.group(2))) if m else default

def scalar(block,key,default=0.0):
    m=re.search(r'^'+re.escape(key)+r'\s*=\s*([-+0-9.eE]+)',block,re.M)
    return float(m.group(1)) if m else default

def arr_floats(s):
    return [float(x) for x in re.findall(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?',s)]

def packed_vec2(block,key):
    m=re.search(r'^'+re.escape(key)+r'\s*=\s*PackedVector2Array\((.*?)\)\s*$',block,re.M)
    if not m:return []
    f=arr_floats(m.group(1))
    return [(f[i],f[i+1]) for i in range(0,len(f),2)]

def node_header(block):
    line=block.splitlines()[0]
    name=re.search(r'name="([^"]+)"',line)
    typ=re.search(r'type="([^"]+)"',line)
    parent=re.search(r'parent="([^"]+)"',line)
    return (name.group(1) if name else None,typ.group(1) if typ else None,parent.group(1) if parent else None)

def mat_mul(A,B):
    a,b,c,d,tx,ty=A; e,f,g,h,ux,uy=B
    return [
        a*e+c*f, b*e+d*f,
        a*g+c*h, b*g+d*h,
        a*ux+c*uy+tx, b*ux+d*uy+ty
    ]

def mat_inv(M):
    a,b,c,d,tx,ty=M
    det=a*d-b*c
    if abs(det)<1e-9: raise ValueError("singular transform")
    ia=d/det; ib=-b/det; ic=-c/det; id=a/det
    return [ia,ib,ic,id,-(ia*tx+ic*ty),-(ib*tx+id*ty)]

def local_matrix(x,y,rot,scale):
    co=math.cos(rot); si=math.sin(rot); sx,sy=scale
    return [co*sx,si*sx,-si*sy,co*sy,x,y]

def xform(M,p):
    a,b,c,d,tx,ty=M; x,y=p
    return (a*x+c*y+tx,b*x+d*y+ty)

def strip_bone_path(path):
    if path.startswith(PREFIX): return path[len(PREFIX):]
    return path

def resolve_bone(ref,bones):
    if ref in bones:return ref
    if "Hip/"+ref in bones:return "Hip/"+ref
    cand=[b for b in bones if b.endswith("/"+ref)]
    if len(cand)==1:return cand[0]
    leaf=ref.split("/")[-1]
    cand=[b for b in bones if b.split("/")[-1]==leaf]
    if len(cand)==1:return cand[0]
    raise ValueError(f"Cannot resolve mesh bone ref {ref!r}; candidates={cand}")

def parse_bones(sections):
    bones={}
    order=[]
    for s in sections:
        name,typ,parent=node_header(s)
        if typ!="Bone2D":continue
        if not parent or not parent.startswith("Sprite2D/Skeleton2D"):continue
        full=(parent+"/"+name)
        bid=strip_bone_path(full)
        pid=None if parent=="Sprite2D/Skeleton2D" else strip_bone_path(parent)
        pos=vec2(s,"position")
        rot=scalar(s,"rotation",0.0)
        scale=vec2(s,"scale",(1.0,1.0))
        rm=re.search(r'^rest\s*=\s*Transform2D\(([^\)]+)\)',s,re.M)
        rest=arr_floats(rm.group(1)) if rm else local_matrix(pos[0],pos[1],0.0,(1,1))
        if len(rest)!=6: raise ValueError("bad rest "+bid)
        bones[bid]={
            "id":bid,"parent":pid,
            "defaultX":pos[0],"defaultY":pos[1],
            "defaultRotation":math.degrees(rot),
            "defaultScaleX":scale[0],"defaultScaleY":scale[1],
            "rest":rest
        }
        order.append(bid)
    # global rest matrices
    for bid in order:
        b=bones[bid]
        b["restGlobal"]=mat_mul(bones[b["parent"]]["restGlobal"],b["rest"]) if b["parent"] else b["rest"]
        b["invRestGlobal"]=mat_inv(b["restGlobal"])
    return bones,order

def parse_faces(s):
    m=re.search(r'^polygons\s*=\s*\[(.*?)\]\s*$',s,re.M)
    if not m:return []
    faces=[]
    for fm in re.finditer(r'PackedInt32Array\((.*?)\)',m.group(1)):
        faces.append([int(x) for x in re.findall(r'-?\d+',fm.group(1))])
    tris=[]
    for f in faces:
        for i in range(1,len(f)-1):
            tris += [f[0],f[i],f[i+1]]
    return tris

def parse_weights(s,nverts,bones):
    m=re.search(r'^bones\s*=\s*\[(.*?)\]\s*$',s,re.M)
    inf=[[] for _ in range(nverts)]
    if not m:return inf
    body=m.group(1)
    pat=re.compile(r'"([^"]+)"\s*,\s*PackedFloat32Array\((.*?)\)')
    for ref,weights_s in pat.findall(body):
        bid=resolve_bone(ref,bones)
        ws=arr_floats(weights_s)
        if len(ws)!=nverts: raise ValueError(f"weight count {len(ws)} != {nverts} for {bid}")
        for i,w in enumerate(ws):
            if abs(w)>1e-8: inf[i].append([bid,w])
    for i,row in enumerate(inf):
        total=sum(w for _,w in row)
        if total>1e-8:
            for q in row:q[1]/=total
        else:
            raise ValueError(f"vertex {i} has zero total bone weight")
    return inf

def parse_meshes(sections,bones):
    meshes=[]
    allpts=[]
    for s in sections:
        name,typ,parent=node_header(s)
        if typ!="Polygon2D" or parent!="Sprite2D/Polygons":continue
        verts=packed_vec2(s,"polygon"); uvs=packed_vec2(s,"uv")
        if not verts or len(uvs)!=len(verts):continue
        pos=vec2(s,"position"); off=vec2(s,"offset")
        rot=scalar(s,"rotation",0.0); scale=vec2(s,"scale",(1,1))
        M=local_matrix(pos[0]+off[0],pos[1]+off[1],rot,scale)
        world=[xform(M,p) for p in verts]
        allpts.extend(world)
        tri=parse_faces(s)
        if not tri: continue
        meshes.append({
            "name":name,
            "image":"gBot.png",
            "vertices":[v for p in world for v in p],
            "uvs":[v for p in uvs for v in p],
            "triangles":tri,
            "influences":parse_weights(s,len(verts),bones)
        })
    if not meshes:raise ValueError("no Polygon2D meshes parsed")
    return meshes,allpts

def parse_anim_section(s):
    head=s.splitlines()[0]
    aid=re.search(r'id="([^"]+)"',head).group(1)
    length=scalar(s,"length",1.0)
    loop=bool(int(scalar(s,"loop_mode",0)))
    tracks={}
    for pm in re.finditer(r'^tracks/(\d+)/path\s*=\s*NodePath\("([^"]+)"\)',s,re.M):
        idx=pm.group(1); path=pm.group(2)
        if ":" not in path or not path.startswith(PREFIX):continue
        nodepath,prop=path.rsplit(":",1)
        bid=strip_bone_path(nodepath)
        km=re.search(r'^tracks/'+re.escape(idx)+r'/keys\s*=\s*\{(.*?)^\}',s,re.M|re.S)
        if not km:continue
        kb=km.group(1)
        tm=re.search(r'"times"\s*:\s*PackedFloat32Array\((.*?)\)',kb,re.S)
        if not tm:continue
        times=arr_floats(tm.group(1))
        vm=re.search(r'"values"\s*:\s*\[(.*?)\]\s*$',kb,re.M|re.S)
        if not vm:continue
        vs=vm.group(1)
        tr=tracks.setdefault(bid,{})
        if prop=="rotation_degrees":
            vals=arr_floats(vs)
            if len(vals)!=len(times):raise ValueError(f"rot keys mismatch {aid}:{bid}")
            tr["rotation"]=[{"time":t,"value":v} for t,v in zip(times,vals)]
        elif prop=="position":
            vals=[(float(a),float(b)) for a,b in re.findall(r'Vector2\(([^,]+),\s*([^\)]+)\)',vs)]
            if len(vals)!=len(times):raise ValueError(f"pos keys mismatch {aid}:{bid}")
            tr["position"]=[{"time":t,"x":v[0],"y":v[1]} for t,v in zip(times,vals)]
    return aid,{"duration":length,"loop":loop,"tracks":tracks}

def parse_animations(sections):
    byid={}
    amap={}
    for s in sections:
        first=s.splitlines()[0]
        if first.startswith('[sub_resource type="Animation" '):
            aid,a=parse_anim_section(s); byid[aid]=a
        elif first.startswith('[sub_resource type="AnimationLibrary" '):
            for name,aid in re.findall(r'&"([^"]+)"\s*:\s*SubResource\("([^"]+)"\)',s):
                amap[name]=aid
    out={}
    for name,aid in amap.items():
        if aid in byid:out[name]=byid[aid]
    if not out:raise ValueError("no named animations parsed")
    return out

def main():
    if len(sys.argv)!=4:
        raise SystemExit("usage: convert_godot_skeleton.py player.tscn gBot.png output.zip")
    tscn=Path(sys.argv[1]); tex=Path(sys.argv[2]); out=Path(sys.argv[3])
    text=tscn.read_text(encoding="utf-8")
    sections=sectionize(text)
    bones,order=parse_bones(sections)
    meshes,pts=parse_meshes(sections,bones)
    animations=parse_animations(sections)
    minx=min(x for x,y in pts);maxx=max(x for x,y in pts)
    miny=min(y for x,y in pts);maxy=max(y for x,y in pts)
    margin=80.0
    project={
      "format":"x2d-rig-2.0",
      "source":{
        "name":"Godot official Skeleton2D Demo",
        "repository":"godotengine/godot-demo-projects",
        "path":"2d/skeleton/player/player.tscn",
        "commit":"a3b5c113112f77291d5f3d1360f33a882fdc52f7",
        "license":"MIT",
        "sourceAuthenticAnimations":True
      },
      "width":maxx-minx+margin*2,
      "height":maxy-miny+margin*2,
      "modelOffsetX":-minx+margin,
      "modelOffsetY":-miny+margin,
      "bones":[bones[i] for i in order],
      "meshes":meshes,
      "animations":animations,
      "defaultAnimation":"idle" if "idle" in animations else next(iter(animations))
    }
    report={
      "bones":len(order),"meshes":len(meshes),
      "vertices":sum(len(m["vertices"])//2 for m in meshes),
      "triangles":sum(len(m["triangles"])//3 for m in meshes),
      "animations":{k:{"duration":v["duration"],"tracks":len(v["tracks"])} for k,v in animations.items()}
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json",json.dumps(project,ensure_ascii=False,indent=2))
        z.write(tex,"gBot.png")
        z.writestr("SOURCE.txt",
          "Godot official Skeleton2D Demo\n"
          "Repository: https://github.com/godotengine/godot-demo-projects\n"
          "Pinned commit: a3b5c113112f77291d5f3d1360f33a882fdc52f7\n"
          "Path: 2d/skeleton\nLicense: MIT\n"
          "Animations are parsed from the original player.tscn; no replacement keyframes are authored.\n")
        z.writestr("CONVERSION_REPORT.json",json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    print(out)

if __name__=="__main__":
    main()
