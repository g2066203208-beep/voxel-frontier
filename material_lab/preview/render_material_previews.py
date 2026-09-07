#!/usr/bin/env python3
from pathlib import Path
import json
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/generated-materials")

DEFAULT_DISPLACEMENT = {
    "amp": .080,
    "iterations": 5,
    "hd_min": -.82,
    "hd_max": .82,
}
PRESET_DISPLACEMENT = {
    "vfLayeredSandstonePainted": {
        "amp": .230,
        "iterations": 7,
        "hd_min": -.18,
        "hd_max": .96,
    },
}

def preview_displacement_profile(material_dir: Path):
    manifest_path = material_dir / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    preset = manifest.get("preset")
    return PRESET_DISPLACEMENT.get(preset, DEFAULT_DISPLACEMENT)

def srgb_to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)

def linear_to_srgb(x):
    return np.where(x <= 0.0031308, 12.92*x, 1.055*np.power(np.clip(x,0,None),1/2.4)-0.055)

def bilinear(tex,u,v):
    h,w=tex.shape[:2]; u=np.mod(u,1.0); v=np.mod(v,1.0)
    x=u*(w-1); y=(1-v)*(h-1)
    x0=np.floor(x).astype(np.int32); y0=np.floor(y).astype(np.int32)
    x1=(x0+1)%w; y1=(y0+1)%h
    if tex.ndim==3:
        tx=(x-x0)[...,None]; ty=(y-y0)[...,None]
    else:
        tx=(x-x0); ty=(y-y0)
    return (tex[y0,x0]*(1-tx)+tex[y0,x1]*tx)*(1-ty)+(tex[y1,x0]*(1-tx)+tex[y1,x1]*tx)*ty

def norm(v):
    v=np.asarray(v,dtype=np.float32)
    return v/np.maximum(np.linalg.norm(v),1e-6)

def ggx_specular(N,V,L,rough,F0):
    H=norm(L+V)
    ndl=np.clip((N*L).sum(axis=-1),0.0,1.0)
    ndv=np.clip((N*V).sum(axis=-1),1e-4,1.0)
    ndh=np.clip((N*H).sum(axis=-1),1e-4,1.0)
    vdh=np.clip(V[0]*H[0]+V[1]*H[1]+V[2]*H[2],0.0,1.0)
    alpha=np.maximum(rough*rough,0.035)
    a2=alpha*alpha
    denom=np.pi*np.square(ndh*ndh*(a2-1.0)+1.0)
    D=a2/np.maximum(denom,1e-6)
    k=np.square(rough+1.0)/8.0
    Gv=ndv/(ndv*(1.0-k)+k); Gl=ndl/(ndl*(1.0-k)+k); G=Gv*Gl
    F=F0+(1.0-F0)*np.power(1.0-vdh,5.0)
    return (D*G/np.maximum(4.0*ndv*ndl,1e-5))[...,None]*F, ndl

def sphere_uv(Ng):
    u=(0.5+np.arctan2(Ng[...,2],Ng[...,0])/(2*np.pi))*2.10
    v=(0.5-np.arcsin(np.clip(Ng[...,1],-1,1))/np.pi)*2.10
    return u,v

def displaced_geometry(sx,sy,height,amp=0.080,iterations=5,hd_min=-0.82,hd_max=0.82):
    qx=sx.copy(); qy=sy.copy()
    h05=float(np.percentile(height,5)); h50=float(np.percentile(height,50)); h95=float(np.percentile(height,95))
    hspan=max(h95-h05,0.08)
    sampled=np.full_like(sx,h50,dtype=np.float32)
    for _ in range(iterations):
        q2=qx*qx+qy*qy
        qz=np.sqrt(np.clip(1-q2,0,1))
        Ng=np.stack([qx,qy,qz],axis=-1)
        Ng/=np.maximum(np.linalg.norm(Ng,axis=-1,keepdims=True),1e-6)
        u,v=sphere_uv(Ng)
        sampled=bilinear(height,u,v)
        hd=np.clip((sampled-h50)/hspan,hd_min,hd_max)
        radial=np.clip(1.0+amp*hd,1.0+amp*hd_min,1.0+amp*hd_max)
        qx=sx/radial; qy=sy/radial
    q2=qx*qx+qy*qy
    mask=q2<=1.0
    qz=np.sqrt(np.clip(1-q2,0,1))
    Ng=np.stack([qx,qy,qz],axis=-1)
    Ng/=np.maximum(np.linalg.norm(Ng,axis=-1,keepdims=True),1e-6)
    return Ng,mask,q2,sampled

def render_sphere(d:Path,name:str,out:Path):
    base_srgb=np.asarray(Image.open(d/f"{name}_baseColor.png").convert("RGB").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    base=srgb_to_linear(base_srgb)
    normal=np.asarray(Image.open(d/f"{name}_normal.png").convert("RGB").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    rough=np.asarray(Image.open(d/f"{name}_roughness.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    ao=np.asarray(Image.open(d/f"{name}_ao.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    metal=np.asarray(Image.open(d/f"{name}_metallic.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    height=np.asarray(Image.open(d/f"{name}_height.png").convert("L").resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255

    S=1000; cx=S*.5; cy=S*.465; R=S*.325
    yy,xx=np.mgrid[0:S,0:S]; sx=(xx-cx)/R; sy=(cy-yy)/R
    displacement=preview_displacement_profile(d)
    Ng,mask,r2,hh=displaced_geometry(
        sx,sy,height,
        amp=displacement["amp"],
        iterations=displacement["iterations"],
        hd_min=displacement["hd_min"],
        hd_max=displacement["hd_max"],
    )
    u,v=sphere_uv(Ng)
    bc=bilinear(base,u,v); nt=bilinear(normal,u,v)*2-1; rr=np.clip(bilinear(rough,u,v),.035,1); aa=bilinear(ao,u,v); mm=np.clip(bilinear(metal,u,v),0,1)

    T=np.stack([-Ng[...,2],np.zeros_like(sx),Ng[...,0]],axis=-1); T/=np.maximum(np.linalg.norm(T,axis=-1,keepdims=True),1e-6)
    B=np.cross(Ng,T); B/=np.maximum(np.linalg.norm(B,axis=-1,keepdims=True),1e-6)
    N=T*nt[...,0:1]+B*nt[...,1:2]+Ng*np.maximum(nt[...,2:3],0.06); N/=np.maximum(np.linalg.norm(N,axis=-1,keepdims=True),1e-6)

    eps=1.0/1024.0
    hL=bilinear(height,u-eps,v); hR=bilinear(height,u+eps,v); hD=bilinear(height,u,v-eps); hU=bilinear(height,u,v+eps)
    gx=(hR-hL)*3.2; gy=(hU-hD)*3.2
    HN=T*(-gx[...,None])+B*(-gy[...,None])+Ng
    HN/=np.maximum(np.linalg.norm(HN,axis=-1,keepdims=True),1e-6)
    N=N*.80+HN*.20; N/=np.maximum(np.linalg.norm(N,axis=-1,keepdims=True),1e-6)

    V=np.array([0,0,1],np.float32)
    up=np.clip(N[...,1],-1,1)
    sky=np.array([.72,.88,1.12],np.float32); ground=np.array([.36,.29,.23],np.float32)
    env=((up+1)/2)[...,None]*sky+((1-up)/2)[...,None]*ground
    F0=.04*(1-mm)[...,None]+bc*mm[...,None]
    diffuse_color=bc*(1-mm[...,None])
    color=diffuse_color*env*(.42+.58*aa[...,None])*.62
    lights=[
        (norm([-.64,.66,.40]),8.0,np.array([1.00,.93,.84],np.float32)),
        (norm([ .58,.20,.79]),3.7,np.array([.72,.84,1.00],np.float32)),
        (norm([-.10,-.84,.53]),1.9,np.array([1.00,.67,.47],np.float32)),
    ]
    for L,intensity,lcol in lights:
        spec,ndl=ggx_specular(N,V,L,rr,F0)
        color += diffuse_color*ndl[...,None]*intensity*lcol/math.pi
        rough_energy=(.22+.78*np.power(1-rr,1.7))[...,None]
        color += spec*rough_energy*intensity*lcol*.34
    refl_dir=norm([-.36,.36,.86])
    ndrefl=np.clip((N*refl_dir).sum(axis=-1),0,1)
    broad=np.exp(-np.square(1-ndrefl)/(0.014+rr*rr*.22))*np.square(1-rr)*.15
    color += broad[...,None]*(F0+.018)*np.array([1.0,.98,.94],np.float32)*3.2
    ndv=np.clip(N[...,2],0,1)
    fres=F0+(1-F0)*np.power(1-ndv[...,None],5)
    color += fres*(.012+.025*(1-rr)[...,None])*np.array([.58,.70,.88],np.float32)
    color*=.91+.09*aa[...,None]
    c=np.clip(color*1.08,0,None); a,b,c1,d1,e=2.51,.03,2.43,.59,.14; c=(c*(a*c+b))/(c*(c1*c+d1)+e); c=linear_to_srgb(np.clip(c,0,1))

    gy=np.linspace(0,1,S)[:,None,None]; top=np.array([.73,.76,.80],np.float32)[None,None,:]; bot=np.array([.17,.19,.21],np.float32)[None,None,:]
    bg=np.repeat(top*(1-gy)+bot*gy,S,axis=1); floor_y=int(S*.78); fm=np.clip((yy-floor_y)/(S*.14),0,1)
    bg=bg*(1-fm[...,None]*.40)+np.array([.20,.195,.19],np.float32)*fm[...,None]*.40
    shadow=np.exp(-(((xx-cx)/(R*.84))**2+((yy-(cy+R*1.025))/(R*.135))**2)*2.45); bg*=1-.35*shadow[...,None]
    edge=np.clip((1-r2)*R*.90,0,1)[...,None]; edge*=mask[...,None].astype(np.float32)
    img=bg*(1-edge)+c*edge
    out_im=Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8),"RGB")
    draw=ImageDraw.Draw(out_im)
    try: f1=ImageFont.truetype("DejaVuSans.ttf",27); f2=ImageFont.truetype("DejaVuSans.ttf",18)
    except: f1=ImageFont.load_default(); f2=f1
    draw.rounded_rectangle((28,26,650,104),radius=18,fill=(18,18,20)); draw.text((48,40),name,fill=(245,245,245),font=f1); draw.text((48,74),"true Height displacement · faceted GGX studio sphere",fill=(190,195,200),font=f2)
    out_im.save(out)

def contact_sheet(d:Path,name:str,out:Path):
    names=[("Base Color","baseColor"),("Normal","normal"),("Roughness","roughness"),("Height","height"),("AO","ao"),("Metallic","metallic")]
    thumb=420; gap=20; label=38; sheet=Image.new("RGB",(3*thumb+4*gap,2*(thumb+label)+3*gap),(24,24,24)); dr=ImageDraw.Draw(sheet)
    try: font=ImageFont.truetype("DejaVuSans.ttf",21)
    except: font=ImageFont.load_default()
    for i,(lab,suffix) in enumerate(names):
        im=Image.open(d/f"{name}_{suffix}.png").convert("RGB").resize((thumb,thumb),Image.Resampling.LANCZOS); r,c=divmod(i,3); x=gap+c*(thumb+gap); y=gap+r*(thumb+label+gap); sheet.paste(im,(x,y)); dr.text((x,y+thumb+6),lab,fill=(240,240,240),font=font)
    sheet.save(out)

def tile_check(d:Path,name:str,out:Path):
    im=Image.open(d/f"{name}_baseColor.png").convert("RGB").resize((600,600),Image.Resampling.LANCZOS); tile=Image.new("RGB",(1200,1200))
    for y in (0,600):
        for x in (0,600): tile.paste(im,(x,y))
    tile.save(out)

for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    bases=list(d.glob("*_baseColor.png"))
    if not bases: continue
    name=bases[0].name[:-len("_baseColor.png")]
    render_sphere(d,name,d/"preview-sphere.png"); contact_sheet(d,name,d/"preview-maps.png"); tile_check(d,name,d/"preview-tile-2x2.png"); print(name)
