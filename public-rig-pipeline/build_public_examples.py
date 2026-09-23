#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, math, os, sys, zipfile, shutil

ROOT=Path(__file__).resolve().parent
WORK=ROOT/"work"
OUT=ROOT/"out"
WORK.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

def components(img, min_area=120):
    rgba=img.convert("RGBA")
    a=rgba.getchannel("A")
    w,h=rgba.size
    pix=a.load()
    seen=bytearray(w*h)
    comps=[]
    from collections import deque
    for y in range(h):
        for x in range(w):
            idx=y*w+x
            if seen[idx] or pix[x,y] < 16:
                continue
            q=deque([(x,y)]);seen[idx]=1
            xs=[];ys=[]
            while q:
                xx,yy=q.popleft();xs.append(xx);ys.append(yy)
                for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                    if 0<=nx<w and 0<=ny<h:
                        ii=ny*w+nx
                        if not seen[ii] and pix[nx,ny]>=16:
                            seen[ii]=1;q.append((nx,ny))
            if len(xs)>=min_area:
                comps.append({"bbox":(min(xs),min(ys),max(xs)+1,max(ys)+1),"area":len(xs)})
    return comps

def nearest_unique(comps, size, targets):
    w,h=size
    used=set(); out={}
    for name,(tx,ty) in targets.items():
        best=None
        for i,c in enumerate(comps):
            if i in used: continue
            x0,y0,x1,y1=c["bbox"]
            cx=(x0+x1)/2/w; cy=(y0+y1)/2/h
            bw=(x1-x0)/w; bh=(y1-y0)/h
            # center distance + a small penalty for tiny decorative fragments
            score=(cx-tx)**2+(cy-ty)**2 + (0.01 if bw*bh<0.0015 else 0)
            if best is None or score<best[0]:best=(score,i)
        if best:
            used.add(best[1]);out[name]=comps[best[1]]
    return out

def crop_part(img,bbox,pad=5):
    x0,y0,x1,y1=bbox
    x0=max(0,x0-pad);y0=max(0,y0-pad);x1=min(img.width,x1+pad);y1=min(img.height,y1+pad)
    return img.crop((x0,y0,x1,y1))

def contact_sheet(img, comps, outpath):
    preview=img.convert("RGBA").copy()
    d=ImageDraw.Draw(preview)
    for i,c in enumerate(comps):
        x0,y0,x1,y1=c["bbox"]
        d.rectangle((x0,y0,x1,y1),outline=(255,40,40,255),width=2)
        d.text((x0+2,y0+2),str(i),fill=(255,255,0,255))
    preview.save(outpath)

def make_local_axis(part, kind):
    # Bone local +X points from parent joint to child joint.
    # Vertical source parts are rotated so the attachment follows that axis.
    if kind=="torso":
        return part.transpose(Image.Transpose.ROTATE_270)  # hip -> head
    return part.transpose(Image.Transpose.ROTATE_90)      # top joint -> distal joint

def save_part(img, name, dst, kind="limb"):
    q=make_local_axis(img,kind)
    q.save(dst/name)
    return q.size

def build_sheet(src_path, sex, title, animation_name):
    src=Image.open(src_path).convert("RGBA")
    comps=components(src)
    contact_sheet(src,comps,OUT/f"{sex}_component_inventory.png")

    # Deterministic map against the published sheet layout.
    # It is versioned here so future source changes are visible in Git diff.
    if sex=="female":
        targets={
          "head":(0.63,0.13),"neck":(0.63,0.23),"chest":(0.63,0.30),
          "waist":(0.63,0.38),"pelvis":(0.63,0.45),
          "upper_arm_l":(0.55,0.62),"forearm_l":(0.55,0.70),
          "upper_arm_r":(0.69,0.62),"forearm_r":(0.69,0.70),
          "thigh_l":(0.55,0.81),"calf_l":(0.55,0.91),
          "thigh_r":(0.69,0.81),"calf_r":(0.69,0.91)
        }
    else:
        targets={
          "head":(0.63,0.13),"neck":(0.63,0.23),"chest":(0.63,0.30),
          "waist":(0.63,0.38),"pelvis":(0.63,0.45),
          "upper_arm_l":(0.55,0.62),"forearm_l":(0.55,0.70),
          "upper_arm_r":(0.71,0.62),"forearm_r":(0.71,0.70),
          "thigh_l":(0.55,0.81),"calf_l":(0.55,0.91),
          "thigh_r":(0.71,0.81),"calf_r":(0.71,0.91)
        }
    mapped=nearest_unique(comps,src.size,targets)

    pkg=WORK/f"{sex}_pkg"
    if pkg.exists():shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    (pkg/"SOURCE_LICENSE.txt").write_text(
      f"{title}\nSource: https://opengameart.org/content/femalemale-bones-sheet\n"
      "Author: Spring Spring\nLicense: CC0 1.0\n"
      f"Animation: {animation_name} is a deterministic demo authored by this GitHub pipeline; it is not claimed as source animation.\n",
      encoding="utf-8")

    # Build a single torso bitmap preserving published chest/waist/pelvis vertical order.
    body_names=["chest","waist","pelvis"]
    body_boxes=[mapped[n]["bbox"] for n in body_names]
    x0=min(b[0] for b in body_boxes); y0=min(b[1] for b in body_boxes)
    x1=max(b[2] for b in body_boxes); y1=max(b[3] for b in body_boxes)
    torso=crop_part(src,(x0,y0,x1,y1),8)
    torso_size=save_part(torso,"torso.png",pkg,"torso")

    sizes={}
    for n in ["head","upper_arm_l","forearm_l","upper_arm_r","forearm_r","thigh_l","calf_l","thigh_r","calf_r"]:
        part=crop_part(src,mapped[n]["bbox"],5)
        sizes[n]=save_part(part,f"{n}.png",pkg,"limb")

    def attach(bone,img,size,px=8):
        # local bone starts near left-center in pre-rotated image
        return {"bone":bone,"image":img,"pivotX":px,"pivotY":size[1]/2,"scale":1.0}

    duration=3.0
    project={
      "format":"x2d-bone-player-0.1",
      "provenance":{
        "source_id":"oga_female_male_bones_sheet",
        "source_license":"CC0-1.0",
        "source_animation":False,
        "animation_origin":"demo_authored"
      },
      "width":720,"height":1080,"duration":duration,
      "bones":[
        {"id":"root","parent":None,"x":360,"y":660,"rotation":0,"length":0},
        {"id":"torso","parent":"root","x":0,"y":0,"rotation":-90,"length":220},
        {"id":"head","parent":"torso","x":220,"y":0,"rotation":0,"length":0},
        {"id":"upper_arm_l","parent":"torso","x":165,"y":-70,"rotation":-125,"length":145},
        {"id":"forearm_l","parent":"upper_arm_l","x":145,"y":0,"rotation":-20,"length":140},
        {"id":"upper_arm_r","parent":"torso","x":165,"y":70,"rotation":125,"length":145},
        {"id":"forearm_r","parent":"upper_arm_r","x":145,"y":0,"rotation":20,"length":140},
        {"id":"thigh_l","parent":"root","x":-45,"y":0,"rotation":82,"length":190},
        {"id":"calf_l","parent":"thigh_l","x":190,"y":0,"rotation":8,"length":185},
        {"id":"thigh_r","parent":"root","x":45,"y":0,"rotation":98,"length":190},
        {"id":"calf_r","parent":"thigh_r","x":190,"y":0,"rotation":-8,"length":185}
      ],
      "sprites":[
        attach("torso","torso.png",torso_size,10),
        attach("head","head.png",sizes["head"],sizes["head"][0]/2),
        attach("upper_arm_l","upper_arm_l.png",sizes["upper_arm_l"]),
        attach("forearm_l","forearm_l.png",sizes["forearm_l"]),
        attach("upper_arm_r","upper_arm_r.png",sizes["upper_arm_r"]),
        attach("forearm_r","forearm_r.png",sizes["forearm_r"]),
        attach("thigh_l","thigh_l.png",sizes["thigh_l"]),
        attach("calf_l","calf_l.png",sizes["calf_l"]),
        attach("thigh_r","thigh_r.png",sizes["thigh_r"]),
        attach("calf_r","calf_r.png",sizes["calf_r"])
      ],
      "keyframes":{
        "root":[
          {"time":0,"x":360,"y":660,"rotation":0},
          {"time":1.5,"x":360,"y":652,"rotation":0},
          {"time":3.0,"x":360,"y":660,"rotation":0}
        ],
        "torso":[
          {"time":0,"x":0,"y":0,"rotation":-92},
          {"time":1.5,"x":0,"y":0,"rotation":-88},
          {"time":3.0,"x":0,"y":0,"rotation":-92}
        ],
        "upper_arm_l":[
          {"time":0,"x":165,"y":-70,"rotation":-125},
          {"time":0.75,"x":165,"y":-70,"rotation":-65 if sex=="female" else -105},
          {"time":1.5,"x":165,"y":-70,"rotation":-125},
          {"time":2.25,"x":165,"y":-70,"rotation":-55 if sex=="female" else -115},
          {"time":3.0,"x":165,"y":-70,"rotation":-125}
        ],
        "forearm_l":[
          {"time":0,"x":145,"y":0,"rotation":-20},
          {"time":0.75,"x":145,"y":0,"rotation":-70 if sex=="female" else -25},
          {"time":1.5,"x":145,"y":0,"rotation":-20},
          {"time":2.25,"x":145,"y":0,"rotation":-65 if sex=="female" else -15},
          {"time":3.0,"x":145,"y":0,"rotation":-20}
        ],
        "upper_arm_r":[
          {"time":0,"x":165,"y":70,"rotation":125},
          {"time":1.5,"x":165,"y":70,"rotation":140},
          {"time":3.0,"x":165,"y":70,"rotation":125}
        ],
        "thigh_l":[
          {"time":0,"x":-45,"y":0,"rotation":82},
          {"time":1.5,"x":-45,"y":0,"rotation":88},
          {"time":3.0,"x":-45,"y":0,"rotation":82}
        ],
        "thigh_r":[
          {"time":0,"x":45,"y":0,"rotation":98},
          {"time":1.5,"x":45,"y":0,"rotation":92},
          {"time":3.0,"x":45,"y":0,"rotation":98}
        ]
      }
    }
    (pkg/"project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding="utf-8")
    outzip=OUT/(f"CC0_{sex.capitalize()}_BoneSheet_{'Wave' if sex=='female' else 'Idle'}.x2d.zip")
    with zipfile.ZipFile(outzip,"w",zipfile.ZIP_DEFLATED) as z:
        for p in pkg.iterdir():z.write(p,p.name)
    return outzip

def inventory_tree(path:Path):
    lines=[]
    if path.exists():
      for p in sorted(path.rglob("*")):
        if p.is_file():lines.append(str(p.relative_to(path)))
    return "\n".join(lines)

if __name__=="__main__":
    female=WORK/"f.png"; male=WORK/"m.png"
    if not female.exists() or not male.exists():
        raise SystemExit("Expected work/f.png and work/m.png downloaded by workflow")
    print(build_sheet(female,"female","Female+Male Bones Sheet","wave"))
    print(build_sheet(male,"male","Female+Male Bones Sheet","idle"))
    inv=OUT/"source_inventory.txt"
    inv.write_text(
      "=== sprites.7z ===\n"+inventory_tree(WORK/"sprites7z")+"\n\n"+
      "=== archer.zip ===\n"+inventory_tree(WORK/"archer")+"\n\n"+
      "=== godot 2d/skeleton ===\n"+inventory_tree(WORK/"godot_skeleton")+"\n",
      encoding="utf-8")
    with zipfile.ZipFile(OUT/"public_source_inventory.zip","w",zipfile.ZIP_DEFLATED) as z:
        z.write(inv,inv.name)
        for p in [OUT/"female_component_inventory.png",OUT/"male_component_inventory.png"]:
            z.write(p,p.name)
    print("DONE")
