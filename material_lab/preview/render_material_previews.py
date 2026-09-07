#!/usr/bin/env python3
from pathlib import Path
import json
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/generated-materials")

DEFAULT_DISPLACEMENT={"amp":.080,"iterations":5,"hd_min":-.82,"hd_max":.82}
PRESET_DISPLACEMENT={
    "vfLayeredSandstonePainted":{"amp":.230,"iterations":7,"hd_min":-.18,"hd_max":.96},
    "vfPainterlyDirt":{"amp":.120,"iterations":6,"hd_min":-.42,"hd_max":.88},
    "vfPainterlyBark":{"amp":.145,"iterations":6,"hd_min":-.38,"hd_max":.92},
    "vfPainterlyLeaves":{"amp":.125,"iterations":6,"hd_min":-.32,"hd_max":.94},
    "vfPainterlySnow":{"amp":.105,"iterations":6,"hd_min":-.28,"hd_max":.84},
}
WATER_DISPLACEMENT={
    "calm":{"amp":.055,"iterations":6,"hd_min":-.55,"hd_max":.72},
    "windy":{"amp":.115,"iterations":7,"hd_min":-.50,"hd_max":.82},
    "foam":{"amp":.145,"iterations":7,"hd_min":-.46,"hd_max":.90},
    "shallow":{"amp":.075,"iterations":6,"hd_min":-.52,"hd_max":.76},
}

def metadata(d:Path):
    manifest=json.loads((d/"manifest.json").read_text(encoding="utf-8"))
    req=json.loads((d/"request.json").read_text(encoding="utf-8")) if (d/"request.json").is_file() else {}
    return manifest,req

def displacement_profile(d:Path):
    manifest,req=metadata(d); preset=manifest.get("preset")
    if preset=="vfPainterlyWater":
        return WATER_DISPLACEMENT.get(req.get("params",{}).get("mode","windy"),WATER_DISPLACEMENT["windy"])
    return PRESET_DISPLACEMENT.get(preset,DEFAULT_DISPLACEMENT)

def srgb_to_linear(x): return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def linear_to_srgb(x): return np.where(x<=.0031308,12.92*x,1.055*np.power(np.clip(x,0,None),1/2.4)-.055)
def norm(v):
    v=np.asarray(v,dtype=np.float32); return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True) if v.ndim>1 else np.linalg.norm(v),1e-6)
def bilinear(tex,u,v):
    h,w=tex.shape[:2]; u=np.mod(u,1.0); v=np.mod(v,1.0); x=u*(w-1); y=(1-v)*(h-1)
    x0=np.floor(x).astype(np.int32); y0=np.floor(y).astype(np.int32); x1=(x0+1)%w; y1=(y0+1)%h
    if tex.ndim==3: tx=(x-x0)[...,None]; ty=(y-y0)[...,None]
    else: tx=x-x0; ty=y-y0
    return (tex[y0,x0]*(1-tx)+tex[y0,x1]*tx)*(1-ty)+(tex[y1,x0]*(1-tx)+tex[y1,x1]*tx)*ty

def screen_sample(tex,x,y):
    h,w=tex.shape[:2]; xi=np.clip(np.rint(x).astype(np.int32),0,w-1); yi=np.clip(np.rint(y).astype(np.int32),0,h-1); return tex[yi,xi]

def ggx(N,V,L,rough,F0):
    H=norm(L+V); ndl=np.clip((N*L).sum(-1),0,1); ndv=np.clip((N*V).sum(-1),1e-4,1); ndh=np.clip((N*H).sum(-1),1e-4,1); vdh=np.clip(float(np.dot(V,H)),0,1)
    a=np.maximum(rough*rough,.035); a2=a*a; D=a2/np.maximum(np.pi*np.square(ndh*ndh*(a2-1)+1),1e-6); k=np.square(rough+1)/8
    G=(ndv/(ndv*(1-k)+k))*(ndl/(ndl*(1-k)+k)); F=F0+(1-F0)*np.power(1-vdh,5)
    return (D*G/np.maximum(4*ndv*ndl,1e-5))[...,None]*F,ndl

def sphere_uv(N):
    return (0.5+np.arctan2(N[...,2],N[...,0])/(2*np.pi))*2.10,(0.5-np.arcsin(np.clip(N[...,1],-1,1))/np.pi)*2.10

def displaced_geometry(sx,sy,height,p):
    qx=sx.copy(); qy=sy.copy(); h05,h50,h95=[float(x) for x in np.percentile(height,[5,50,95])]; span=max(h95-h05,.08)
    for _ in range(p["iterations"]):
        q2=qx*qx+qy*qy; qz=np.sqrt(np.clip(1-q2,0,1)); N=norm(np.stack([qx,qy,qz],-1)); u,v=sphere_uv(N); hs=bilinear(height,u,v)
        hd=np.clip((hs-h50)/span,p["hd_min"],p["hd_max"]); radial=np.clip(1+p["amp"]*hd,1+p["amp"]*p["hd_min"],1+p["amp"]*p["hd_max"]); qx=sx/radial; qy=sy/radial
    q2=qx*qx+qy*qy; mask=q2<=1; qz=np.sqrt(np.clip(1-q2,0,1)); return norm(np.stack([qx,qy,qz],-1)),mask,q2

def studio_bg(S,cx,cy,R,water=False):
    yy,xx=np.mgrid[0:S,0:S]; gy=np.linspace(0,1,S)[:,None,None]
    top=np.array([.76,.80,.86],np.float32)[None,None,:]; bot=np.array([.15,.18,.21],np.float32)[None,None,:]
    bg=np.repeat(top*(1-gy)+bot*gy,S,axis=1)
    floor_y=int(S*.77); fm=np.clip((yy-floor_y)/(S*.15),0,1); bg=bg*(1-fm[...,None]*.44)+np.array([.18,.185,.19],np.float32)*fm[...,None]*.44
    if water:
        card1=np.exp(-np.power((xx-S*.31)/(S*.055),4))*np.exp(-np.power((yy-S*.39)/(S*.31),4))
        card2=np.exp(-np.power((xx-S*.69)/(S*.075),4))*np.exp(-np.power((yy-S*.34)/(S*.34),4))
        stripe=.5+.5*np.sin(xx/S*np.pi*8.0)
        bg += card1[...,None]*np.array([.25,.28,.31],np.float32)+card2[...,None]*np.array([.16,.20,.24],np.float32)
        bg += (stripe*.025)[...,None]*np.array([.45,.55,.65],np.float32)
    shadow=np.exp(-(((xx-cx)/(R*.84))**2+((yy-(cy+R*1.025))/(R*.135))**2)*2.45); bg*=1-.32*shadow[...,None]
    return np.clip(bg,0,1)

def load_mask(d:Path,name:str,key:str):
    p=d/f"{name}_mask-{key}.png"
    if not p.is_file(): return None
    return np.asarray(Image.open(p).convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255

def render_water(d,name,Ng,N,nt,rr,u,v,mask,r2,xx,yy,cx,cy,R,params):
    S=xx.shape[1]; bg=studio_bg(S,cx,cy,R,True)
    foam_tex=load_mask(d,name,"foam"); trans_tex=load_mask(d,name,"transmission"); refr_tex=load_mask(d,name,"refraction"); glint_tex=load_mask(d,name,"glint")
    foam=bilinear(foam_tex,u,v) if foam_tex is not None else np.zeros_like(r2)
    trans=bilinear(trans_tex,u,v) if trans_tex is not None else np.ones_like(r2)*.8
    refr=bilinear(refr_tex,u,v) if refr_tex is not None else np.ones_like(r2)*.5
    glint=bilinear(glint_tex,u,v) if glint_tex is not None else np.zeros_like(r2)
    ref_strength=float(params.get("refraction",.75)); transparency=float(params.get("transparency",.82))
    dx=(N[...,0]*.72+nt[...,0]*.46)*refr*ref_strength*54.0
    dy=(-N[...,1]*.48+nt[...,1]*.32)*refr*ref_strength*34.0
    refracted=screen_sample(bg,xx+dx,yy+dy)
    thickness=np.clip(Ng[...,2]*1.85,.05,1.85)
    absorb=np.array([1.55,.42,.18],np.float32)
    transmission_color=np.exp(-absorb[None,None,:]*thickness[...,None]*(.56+.70*(1-trans[...,None])))
    refracted*=transmission_color
    V=np.array([0,0,1],np.float32); ndv=np.clip(N[...,2],0,1); fres=.020+.980*np.power(1-ndv,5)
    up=np.clip(N[...,1],-1,1); sky=np.array([.78,.95,1.22],np.float32); ground=np.array([.12,.20,.24],np.float32); env=((up+1)/2)[...,None]*sky+((1-up)/2)[...,None]*ground
    tint=np.array([.015,.22,.29],np.float32)[None,None,:]
    color=refracted*(transparency*trans*(1-fres))[...,None] + tint*(.12+.32*(1-trans))[...,None]
    color += env*(.18+.82*fres)[...,None]*(.42+.58*(1-rr))[...,None]
    F0=np.ones(N.shape,dtype=np.float32)*.020
    for L,intensity,lcol in [
        (norm(np.array([-.58,.70,.41],np.float32)),9.5,np.array([1.0,.96,.90],np.float32)),
        (norm(np.array([ .61,.21,.76],np.float32)),5.1,np.array([.68,.84,1.00],np.float32)),
        (norm(np.array([-.12,-.82,.56],np.float32)),2.0,np.array([.82,.93,1.00],np.float32)),
    ]:
        spec,ndl=ggx(N,V,L,rr,F0); color += spec*intensity*lcol*(.65+1.10*(1-rr))[...,None]
    color += glint[...,None]*np.array([.78,.97,1.00],np.float32)*2.15
    foam_light=.54+.46*np.clip((N*norm(np.array([-.58,.70,.41],np.float32))).sum(-1),0,1)
    foam_col=np.stack([.79+.17*foam_light,.88+.10*foam_light,.88+.10*foam_light],-1)
    color=color*(1-foam[...,None])+foam_col*foam[...,None]
    c=np.clip(color*1.04,0,None); a,b,c1,d1,e=2.51,.03,2.43,.59,.14; c=(c*(a*c+b))/(c*(c1*c+d1)+e); c=linear_to_srgb(np.clip(c,0,1))
    edge=np.clip((1-r2)*R*.90,0,1)[...,None]*mask[...,None].astype(np.float32)
    return bg*(1-edge)+c*edge

def render_sphere(d:Path,name:str,out:Path):
    manifest,req=metadata(d); preset=manifest.get("preset"); params=req.get("params",{})
    base_srgb=np.asarray(Image.open(d/f"{name}_baseColor.png").convert("RGB").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255; base=srgb_to_linear(base_srgb)
    normal=np.asarray(Image.open(d/f"{name}_normal.png").convert("RGB").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    rough=np.asarray(Image.open(d/f"{name}_roughness.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    ao=np.asarray(Image.open(d/f"{name}_ao.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    metal=np.asarray(Image.open(d/f"{name}_metallic.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    height=np.asarray(Image.open(d/f"{name}_height.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    S=1000; cx=S*.5; cy=S*.465; R=S*.325; yy,xx=np.mgrid[0:S,0:S]; sx=(xx-cx)/R; sy=(cy-yy)/R
    Ng,mask,r2=displaced_geometry(sx,sy,height,displacement_profile(d)); u,v=sphere_uv(Ng)
    bc=bilinear(base,u,v); nt=bilinear(normal,u,v)*2-1; rr=np.clip(bilinear(rough,u,v),.035,1); aa=bilinear(ao,u,v); mm=np.clip(bilinear(metal,u,v),0,1)
    T=norm(np.stack([-Ng[...,2],np.zeros_like(sx),Ng[...,0]],-1)); B=norm(np.cross(Ng,T)); N=norm(T*nt[...,0:1]+B*nt[...,1:2]+Ng*np.maximum(nt[...,2:3],.06))
    eps=1/1024; gx=(bilinear(height,u+eps,v)-bilinear(height,u-eps,v))*3.2; gy=(bilinear(height,u,v+eps)-bilinear(height,u,v-eps))*3.2; HN=norm(T*(-gx[...,None])+B*(-gy[...,None])+Ng); N=norm(N*.78+HN*.22)
    if preset=="vfPainterlyWater":
        img=render_water(d,name,Ng,N,nt,rr,u,v,mask,r2,xx,yy,cx,cy,R,params)
        subtitle="transmission · refraction · Fresnel · crest foam · true wave displacement"
    else:
        V=np.array([0,0,1],np.float32); up=np.clip(N[...,1],-1,1); sky=np.array([.72,.88,1.12],np.float32); ground=np.array([.36,.29,.23],np.float32); env=((up+1)/2)[...,None]*sky+((1-up)/2)[...,None]*ground
        F0=.04*(1-mm)[...,None]+bc*mm[...,None]; diffuse=bc*(1-mm[...,None]); color=diffuse*env*(.42+.58*aa[...,None])*.62
        for L,intensity,lcol in [(norm(np.array([-.64,.66,.40],np.float32)),8.0,np.array([1,.93,.84],np.float32)),(norm(np.array([.58,.20,.79],np.float32)),3.7,np.array([.72,.84,1],np.float32)),(norm(np.array([-.10,-.84,.53],np.float32)),1.9,np.array([1,.67,.47],np.float32))]:
            spec,ndl=ggx(N,V,L,rr,F0); color+=diffuse*ndl[...,None]*intensity*lcol/math.pi; color+=spec*(.22+.78*np.power(1-rr,1.7))[...,None]*intensity*lcol*.34
        ndv=np.clip(N[...,2],0,1); fres=F0+(1-F0)*np.power(1-ndv[...,None],5); color+=fres*(.012+.025*(1-rr)[...,None])*np.array([.58,.70,.88],np.float32); color*=.91+.09*aa[...,None]
        c=np.clip(color*1.08,0,None); a,b,c1,d1,e=2.51,.03,2.43,.59,.14; c=(c*(a*c+b))/(c*(c1*c+d1)+e); c=linear_to_srgb(np.clip(c,0,1)); bg=studio_bg(S,cx,cy,R,False); edge=np.clip((1-r2)*R*.90,0,1)[...,None]*mask[...,None].astype(np.float32); img=bg*(1-edge)+c*edge
        subtitle="true Height displacement · painterly GGX studio sphere"
    out_im=Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8),"RGB"); draw=ImageDraw.Draw(out_im)
    try: f1=ImageFont.truetype("DejaVuSans.ttf",27); f2=ImageFont.truetype("DejaVuSans.ttf",18)
    except: f1=ImageFont.load_default(); f2=f1
    draw.rounded_rectangle((28,26,820,104),radius=18,fill=(18,18,20)); draw.text((48,40),name,fill=(245,245,245),font=f1); draw.text((48,74),subtitle,fill=(190,195,200),font=f2); out_im.save(out)

def contact_sheet(d:Path,name:str,out:Path):
    items=[("Base Color","baseColor"),("Normal","normal"),("Roughness","roughness"),("Height","height"),("AO","ao"),("Metallic","metallic")]; thumb=420; gap=20; label=38; sheet=Image.new("RGB",(3*thumb+4*gap,2*(thumb+label)+3*gap),(24,24,24)); dr=ImageDraw.Draw(sheet)
    try: font=ImageFont.truetype("DejaVuSans.ttf",21)
    except: font=ImageFont.load_default()
    for i,(lab,suffix) in enumerate(items):
        im=Image.open(d/f"{name}_{suffix}.png").convert("RGB").resize((thumb,thumb),Image.Resampling.LANCZOS); r,c=divmod(i,3); x=gap+c*(thumb+gap); y=gap+r*(thumb+label+gap); sheet.paste(im,(x,y)); dr.text((x,y+thumb+6),lab,fill=(240,240,240),font=font)
    sheet.save(out)
    masks=[("Foam","foam"),("Transmission","transmission"),("Refraction","refraction"),("Glint","glint")]
    if all((d/f"{name}_mask-{k}.png").is_file() for _,k in masks):
        s2=Image.new("RGB",(2*thumb+3*gap,2*(thumb+label)+3*gap),(24,24,24)); d2=ImageDraw.Draw(s2)
        for i,(lab,k) in enumerate(masks):
            im=Image.open(d/f"{name}_mask-{k}.png").convert("RGB").resize((thumb,thumb),Image.Resampling.LANCZOS); r,c=divmod(i,2); x=gap+c*(thumb+gap); y=gap+r*(thumb+label+gap); s2.paste(im,(x,y)); d2.text((x,y+thumb+6),lab,fill=(240,240,240),font=font)
        s2.save(d/"preview-water-fields.png")

def tile_check(d:Path,name:str,out:Path):
    im=Image.open(d/f"{name}_baseColor.png").convert("RGB").resize((600,600),Image.Resampling.LANCZOS); tile=Image.new("RGB",(1200,1200))
    for y in (0,600):
        for x in (0,600): tile.paste(im,(x,y))
    tile.save(out)

for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    bases=list(d.glob("*_baseColor.png"))
    if not bases: continue
    name=bases[0].name[:-len("_baseColor.png")]; render_sphere(d,name,d/"preview-sphere.png"); contact_sheet(d,name,d/"preview-maps.png"); tile_check(d,name,d/"preview-tile-2x2.png"); print(name)
