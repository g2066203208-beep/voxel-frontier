#!/usr/bin/env python3
from pathlib import Path
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("build/generated-materials")
CFG={
    "vfLayeredSandstonePainted":{"amp":.42,"lo":-.18,"hi":1.16,"nlat":84,"nlon":168,"geo":.72,"facet":.42,"subtitle":"terraced cliff slabs · extreme hero relief"},
    "vfPainterlyBark":{"amp":.050,"lo":-.72,"hi":1.04,"nlat":96,"nlon":192,"geo":.43,"facet":.025,"subtitle":"continuous rugged bark skin · no open seams"},
    "vfPainterlyDirt":{"amp":.095,"lo":-.72,"hi":1.02,"nlat":96,"nlon":192,"geo":.44,"facet":.030,"subtitle":"clods crumbs pits · tactile granular ground"},
    "vfPainterlyStoneWall":{"amp":.175,"lo":-.55,"hi":1.06,"nlat":84,"nlon":168,"geo":.70,"facet":.34,"subtitle":"proud irregular stones · recessed mortar"},
    "vfPainterlyMoss":{"amp":.100,"lo":-.60,"hi":1.06,"nlat":96,"nlon":192,"geo":.45,"facet":.020,"subtitle":"dense cushion colonies · raised soft tufts"},
    "vfPainterlyWolfFur":{"amp":.055,"lo":-.72,"hi":1.06,"nlat":110,"nlon":220,"geo":.36,"facet":.0,"subtitle":"dense underfur · narrow directional guard tufts"},
}

def srgb_to_linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def linear_to_srgb(x):return np.where(x<=.0031308,12.92*x,1.055*np.power(np.clip(x,0,None),1/2.4)-.055)
def norm(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-7)
def bilinear(tex,u,v):
    h,w=tex.shape[:2];u=np.mod(u,1.0);v=np.mod(v,1.0);x=u*(w-1);y=(1-v)*(h-1);x0=np.floor(x).astype(np.int32);y0=np.floor(y).astype(np.int32);x1=(x0+1)%w;y1=(y0+1)%h;tx=x-x0;ty=y-y0
    if tex.ndim==3:tx=tx[...,None];ty=ty[...,None]
    return (tex[y0,x0]*(1-tx)+tex[y0,x1]*tx)*(1-ty)+(tex[y1,x0]*(1-tx)+tex[y1,x1]*tx)*ty
def load_rgb(d,n,s):return np.asarray(Image.open(d/f"{n}_{s}.png").convert("RGB"),dtype=np.float32)/255
def load_l(d,n,s):return np.asarray(Image.open(d/f"{n}_{s}.png").convert("L"),dtype=np.float32)/255

def render_one(d:Path,preset:str):
    cfg=CFG[preset];name=d.name;base=load_rgb(d,name,"baseColor");normal_tex=load_rgb(d,name,"normal");rough=load_l(d,name,"roughness");ao=load_l(d,name,"ao");height=load_l(d,name,"height");nlat,nlon=cfg["nlat"],cfg["nlon"]
    vg=np.linspace(0,1,nlat+1,dtype=np.float32);ug=np.linspace(0,1,nlon+1,dtype=np.float32);U,V=np.meshgrid(ug,vg);lon=2*np.pi*(U-.5);lat=np.pi*(.5-V);N0=np.stack([np.cos(lat)*np.cos(lon),np.sin(lat),np.cos(lat)*np.sin(lon)],-1);tu,tv=U,V;hs=bilinear(height,tu,tv)
    cap=max(3,int(nlat*.055))
    for r in range(cap):
        a=r/max(1,cap-1);m=float(hs[r].mean());hs[r]=m*(1-a)+hs[r]*a;m=float(hs[-1-r].mean());hs[-1-r]=m*(1-a)+hs[-1-r]*a
    h05,h50,h95=[float(x) for x in np.percentile(height,[5,50,95])];span=max(h95-h05,.055);hd=np.clip((hs-h50)/span,cfg["lo"],cfg["hi"]);P=N0*(1+cfg["amp"]*hd)[...,None]
    ay=np.deg2rad(-5);ax=np.deg2rad(4);Ry=np.array([[np.cos(ay),0,np.sin(ay)],[0,1,0],[-np.sin(ay),0,np.cos(ay)]],np.float32);Rx=np.array([[1,0,0],[0,np.cos(ax),-np.sin(ax)],[0,np.sin(ax),np.cos(ax)]],np.float32);P=P@(Rx@Ry).T
    idx=np.arange((nlat+1)*(nlon+1),dtype=np.int32).reshape(nlat+1,nlon+1);a=idx[:-1,:-1].ravel();b=idx[:-1,1:].ravel();c=idx[1:,1:].ravel();e=idx[1:,:-1].ravel();tris=np.concatenate([np.stack([a,b,c],1),np.stack([a,c,e],1)],0);Pf=P.reshape(-1,3);tuf=tu.ravel();tvf=tv.ravel();fn=np.cross(Pf[tris[:,1]]-Pf[tris[:,0]],Pf[tris[:,2]]-Pf[tris[:,0]]);vn=np.zeros_like(Pf)
    for k in range(3):np.add.at(vn,tris[:,k],fn)
    vn=norm(vn)
    if cfg["facet"]>0:
        q=norm(np.round(vn*7.0)/7.0);vn=norm(vn*(1-cfg["facet"])+q*cfg["facet"])
    S=1050;cx,cy,R=S*.5,S*.47,S*.275;sx=cx+Pf[:,0]*R;sy=cy-Pf[:,1]*R;sz=Pf[:,2];zbuf=np.full((S,S),-1e9,np.float32);ou=np.zeros((S,S),np.float32);ov=np.zeros((S,S),np.float32);on=np.zeros((S,S,3),np.float32)
    for ti,t in enumerate(tris):
        x0,x1,x2=sx[t];y0,y1,y2=sy[t];minx=max(0,int(math.floor(min(x0,x1,x2))));maxx=min(S-1,int(math.ceil(max(x0,x1,x2))));miny=max(0,int(math.floor(min(y0,y1,y2))));maxy=min(S-1,int(math.ceil(max(y0,y1,y2))))
        if maxx<minx or maxy<miny:continue
        den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(den)<1e-7:continue
        xs=np.arange(minx,maxx+1,dtype=np.float32)+.5;ys=np.arange(miny,maxy+1,dtype=np.float32)+.5;X,Y=np.meshgrid(xs,ys);w0=((y1-y2)*(X-x2)+(x2-x1)*(Y-y2))/den;w1=((y2-y0)*(X-x2)+(x0-x2)*(Y-y2))/den;w2=1-w0-w1;inside=(w0>=-1e-5)&(w1>=-1e-5)&(w2>=-1e-5)
        if not inside.any():continue
        depth=w0*sz[t[0]]+w1*sz[t[1]]+w2*sz[t[2]];zb=zbuf[miny:maxy+1,minx:maxx+1];upd=inside&(depth>zb)
        if not upd.any():continue
        zb[upd]=depth[upd];ru=ou[miny:maxy+1,minx:maxx+1];rv=ov[miny:maxy+1,minx:maxx+1];rn=on[miny:maxy+1,minx:maxx+1];iu=w0*tuf[t[0]]+w1*tuf[t[1]]+w2*tuf[t[2]];iv=w0*tvf[t[0]]+w1*tvf[t[1]]+w2*tvf[t[2]];smooth=w0[...,None]*vn[t[0]]+w1[...,None]*vn[t[1]]+w2[...,None]*vn[t[2]];face=norm(fn[ti][None,None,:])[0,0];nn=norm(smooth*.82+face*.18);ru[upd]=iu[upd];rv[upd]=iv[upd];rn[upd]=nn[upd]
    mask=zbuf>-1e8;Ng=norm(np.where(mask[...,None],on,np.array([0,0,1],np.float32)));bc=srgb_to_linear(bilinear(base,ou,ov));nt=bilinear(normal_tex,ou,ov)*2-1;rr=np.clip(bilinear(rough,ou,ov),.04,1);aa=bilinear(ao,ou,ov);T=norm(np.stack([-Ng[...,2],np.zeros((S,S),np.float32),Ng[...,0]],-1));Bt=norm(np.cross(Ng,T));Ntex=norm(T*nt[...,0:1]+Bt*nt[...,1:2]+Ng*np.maximum(nt[...,2:3],.08));N=norm(Ng*cfg["geo"]+Ntex*(1-cfg["geo"]));color=bc*(.21+.28*aa[...,None]);lights=[(np.array([-.58,.72,.38],np.float32),2.55,np.array([1,.82,.62],np.float32)),(np.array([.68,.22,.70],np.float32),.95,np.array([.50,.64,1],np.float32)),(np.array([-.15,-.78,.60],np.float32),.44,np.array([.78,.38,.30],np.float32))];Vcam=np.array([0,0,1],np.float32)
    for L,intensity,lcol in lights:
        L=L/np.linalg.norm(L);ndl=np.clip(np.sum(N*L,axis=-1),0,1);color+=bc*ndl[...,None]*intensity*lcol*.55;H=(L+Vcam)/np.linalg.norm(L+Vcam);ndh=np.clip(np.sum(N*H,axis=-1),0,1);spec=np.power(ndh,4+36*(1-rr))*(1-rr)*.11;color+=spec[...,None]*intensity*lcol
    rim=np.power(1-np.clip(Ng[...,2],0,1),2.2);color+=rim[...,None]*np.array([.065,.085,.145],np.float32);c=np.clip(color*1.03,0,None);A,Bc,Cc,Dd,Ee=2.51,.03,2.43,.59,.14;c=(c*(A*c+Bc))/(c*(Cc*c+Dd)+Ee);c=linear_to_srgb(np.clip(c,0,1));gy=np.linspace(0,1,S,dtype=np.float32)[:,None,None];bg=np.repeat(np.array([.76,.80,.86],np.float32)[None,None,:]*(1-gy)+np.array([.14,.17,.20],np.float32)[None,None,:]*gy,S,axis=1);mimg=Image.fromarray((mask*255).astype(np.uint8),"L").filter(ImageFilter.GaussianBlur(20));shadow=np.roll(np.asarray(mimg,dtype=np.float32)/255,int(S*.11),axis=0)*.18;bg*=1-shadow[...,None];img=np.where(mask[...,None],c,bg);out=Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8),"RGB");draw=ImageDraw.Draw(out);draw.rounded_rectangle((28,28,S-28,105),radius=18,fill=(18,18,20));draw.text((50,43),f"{name} · TRUE MESH DISPLACEMENT",fill="white");draw.text((50,70),f"{cfg['subtitle']} · amp {cfg['amp']:.3f}",fill=(205,205,210));out=out.resize((1000,1000),Image.Resampling.LANCZOS);out.save(d/"preview-sphere.png");metrics={"renderer":"seam_safe_true_uv_mesh_zbuffer_v5","preset":preset,"repeatScale":1.0,"displacementAmp":cfg["amp"],"heightP05":h05,"heightP50":h50,"heightP95":h95,"heightSpanP05P95":span,"meshLatitudeSegments":nlat,"meshLongitudeSegments":nlon};(d/"preview-mesh-metrics.json").write_text(json.dumps(metrics,indent=2)+"\n",encoding="utf-8");print(json.dumps({"material":name,**metrics}))
def main():
    count=0
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        mp=d/"manifest.json"
        if not mp.is_file():continue
        preset=json.loads(mp.read_text(encoding="utf-8")).get("preset")
        if preset in CFG:render_one(d,preset);count+=1
    print(f"true mesh previews: {count}")
if __name__=="__main__":main()
