#!/usr/bin/env python3
from pathlib import Path
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('build/generated-materials')
OUT_SIZE=1000
RENDER_SIZE=1600
# Snow/water are the visual benchmark. Height-only opaque materials now stay on the
# same smooth studio-sphere renderer. This pass is reserved for categories that
# genuinely need broad attached geometry to break the silhouette.
CFG={
    'vfPainterlyLeaves':{'amp':.018,'lo':-.55,'hi':.78,'nlat':170,'nlon':340,'geo':.82,'subtitle':'broad attached leaf cards · smooth vector silhouette'},
    'vfPainterlyMoss':{'amp':.025,'lo':-.60,'hi':.82,'nlat':170,'nlon':340,'geo':.82,'subtitle':'continuous moss carpet · six broad lifted mat edges'},
    'vfPainterlyWolfFur':{'amp':.020,'lo':-.66,'hi':.82,'nlat':180,'nlon':360,'geo':.82,'subtitle':'broad coat shell · eight attached silhouette fur cards'},
}

def srgb_to_linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def linear_to_srgb(x):return np.where(x<=.0031308,12.92*x,1.055*np.power(np.clip(x,0,None),1/2.4)-.055)
def norm(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-7)
def bilinear(tex,u,v):
    h,w=tex.shape[:2];u=np.mod(u,1.0);v=np.mod(v,1.0);x=u*(w-1);y=(1-v)*(h-1);x0=np.floor(x).astype(np.int32);y0=np.floor(y).astype(np.int32);x1=(x0+1)%w;y1=(y0+1)%h;tx=x-x0;ty=y-y0
    if tex.ndim==3:tx=tx[...,None];ty=ty[...,None]
    return (tex[y0,x0]*(1-tx)+tex[y0,x1]*tx)*(1-ty)+(tex[y1,x0]*(1-tx)+tex[y1,x1]*tx)*ty
def load_rgb(d,n,s):return np.asarray(Image.open(d/f'{n}_{s}.png').convert('RGB'),dtype=np.float32)/255
def load_l(d,n,s):return np.asarray(Image.open(d/f'{n}_{s}.png').convert('L'),dtype=np.float32)/255

def make_radius_fn(height,h05,span,cfg):
    def radius(u,v,lift=0.0):
        hh=float(bilinear(height,np.array(u),np.array(v)));hn=np.clip((hh-h05)/span,cfg['lo'],cfg['hi'])
        return 1+cfg['amp']*hn+lift
    return radius

def sphere_pos(u,v,radius_fn,lift=0.0):
    u=u%1.0;v=max(.02,min(.98,v));lat=math.pi/2-math.pi*v;lon=-math.pi+2*math.pi*u;cl=math.cos(lat);sl=math.sin(lat);r=radius_fn(u,v,lift)
    return np.array([r*cl*math.cos(lon),r*sl,r*cl*math.sin(lon)],np.float32)

def add_ribbon(verts,uvs,tris,radius_fn,u0,v0,du,dv,width,lift,kind='fur',tip_bias=0.0):
    L=math.hypot(du,dv) or 1.0;pu=-dv/L;pv=du/L;ts=np.linspace(0.0,1.0,11);sides=np.linspace(-1.0,1.0,9);base=len(verts)
    for t in ts:
        ease=t*t*(3-2*t)
        if kind=='fur':
            wf=(1-ease)*.98+ease*.24+math.sin(math.pi*t)*.16;center=lift*(.06*t+.72*ease);edge=center*(.24+.15*t)
        else:
            wf=.98+math.sin(math.pi*t)*.14-.12*ease;center=lift*(.04*t+.36*ease);edge=center*(.28+.12*t)
        cu=u0+du*t;cv=v0+dv*t;bend=t*(1-t)*tip_bias;cu+=bend*pu;cv+=bend*pv
        for side in sides:
            off=width*wf*side*.5;uu=cu+pu*off;vv=cv+pv*off;crown=(1-abs(side))**1.6;extra=edge+(center-edge)*crown
            if t==0:extra=0.0
            verts.append(tuple(sphere_pos(uu,vv,radius_fn,extra)));uvs.append((uu%1.0,max(.02,min(.98,vv))))
    cols=len(sides)
    for sec in range(len(ts)-1):
        a=base+sec*cols;d=a+cols
        for k in range(cols-1):tris.extend(((a+k,d+k,a+k+1),(a+k+1,d+k,d+k+1)))

def add_leaf(verts,uvs,tris,radius_fn,u0,v0,du,dv,width,lift,bias=0.0):
    # Smooth lens-shaped leaf card. Narrow root is welded to the shell, broad middle
    # floats above it, and the tip gently returns toward the surface.
    L=math.hypot(du,dv) or 1.0;pu=-dv/L;pv=du/L;ts=np.linspace(0.0,1.0,12);sides=np.linspace(-1.0,1.0,11);base=len(verts)
    for t in ts:
        leafw=max(.045,math.sin(math.pi*t)**.72);arch=math.sin(math.pi*t)**1.28;cu=u0+du*t;cv=v0+dv*t;cu+=t*(1-t)*bias*pu;cv+=t*(1-t)*bias*pv
        for side in sides:
            off=width*leafw*side*.5;uu=cu+pu*off;vv=cv+pv*off;crown=(1-abs(side))**1.5;extra=lift*arch*(.38+.62*crown)+lift*.08*t
            if t==0:extra=0.0
            verts.append(tuple(sphere_pos(uu,vv,radius_fn,extra)));uvs.append((uu%1.0,max(.02,min(.98,vv))))
    cols=len(sides)
    for sec in range(len(ts)-1):
        a=base+sec*cols;d=a+cols
        for k in range(cols-1):tris.extend(((a+k,d+k,a+k+1),(a+k+1,d+k,d+k+1)))

def add_leaf_cards(verts,uvs,tris,radius_fn):
    cards=[
        (.60,.19,.020,.205,.205,.085,-.010),(.80,.20,-.012,.195,.190,.078,.012),
        (.67,.38,.010,.215,.220,.092,.012),(.87,.40,-.018,.205,.205,.086,-.010),
        (.58,.57,.018,.205,.205,.086,-.012),(.79,.59,-.010,.215,.215,.092,.010),
        (.68,.76,.012,.185,.190,.078,.010),(.92,.73,-.018,.170,.175,.072,-.010),
        (.515,.34,.030,.185,.155,.080,-.014),(.990,.33,-.030,.180,.155,.080,.014),
        (.520,.64,.026,.170,.150,.074,.012),(.985,.64,-.026,.170,.150,.074,-.012),
    ]
    for c in cards:add_leaf(verts,uvs,tris,radius_fn,*c)
    return len(cards)

def add_wolf_cards(verts,uvs,tris,radius_fn):
    cards=[
        (.64,.23,.012,.220,.175,.095,-.010),(.83,.26,-.010,.215,.165,.090,.012),
        (.70,.47,-.008,.230,.182,.102,.010),(.87,.50,.010,.215,.170,.094,-.012),
        (.510,.34,.026,.190,.112,.110,-.014),(.990,.36,-.026,.190,.112,.110,.014),
        (.515,.66,.024,.178,.108,.102,.012),(.985,.68,-.024,.178,.108,.102,-.012),
    ]
    for c in cards:add_ribbon(verts,uvs,tris,radius_fn,*c[:-1],kind='fur',tip_bias=c[-1])
    return len(cards)

def add_moss_cards(verts,uvs,tris,radius_fn):
    cards=[
        (.59,.25,.018,.135,.250,.070,.010),(.82,.28,-.014,.130,.235,.068,-.012),
        (.56,.51,.020,.138,.255,.075,-.012),(.80,.52,-.012,.140,.260,.078,.012),
        (.65,.73,.014,.125,.235,.068,.010),(.91,.69,-.016,.118,.215,.064,-.010),
    ]
    for c in cards:add_ribbon(verts,uvs,tris,radius_fn,*c[:-1],kind='moss',tip_bias=c[-1])
    return len(cards)

def main():
    count=0
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        mp=d/'manifest.json'
        if not mp.is_file():continue
        m=json.loads(mp.read_text());preset=m.get('preset');cfg=CFG.get(preset)
        if not cfg:continue
        n=m.get('material') or d.name;base=load_rgb(d,n,'baseColor');normal_tex=load_rgb(d,n,'normal');rough=load_l(d,n,'roughness');ao=load_l(d,n,'ao');height=load_l(d,n,'height')
        h05,h50,h95=np.percentile(height,[5,50,95]);span=max(h95-h05,1e-5);S=RENDER_SIZE;nlat=cfg['nlat'];nlon=cfg['nlon'];radius_fn=make_radius_fn(height,h05,span,cfg)
        verts=[];uvs=[]
        for iy in range(nlat+1):
            v=1-iy/nlat
            for ix in range(nlon+1):u=ix/nlon;verts.append(tuple(sphere_pos(u,v,radius_fn,0)));uvs.append((u,v))
        tris=[];row=nlon+1
        for iy in range(nlat):
            for ix in range(nlon):
                a=iy*row+ix;b=a+1;c=a+row;dd=c+1;tris.extend(((a,c,b),(b,c,dd)))
        if preset=='vfPainterlyLeaves':card_count=add_leaf_cards(verts,uvs,tris,radius_fn)
        elif preset=='vfPainterlyWolfFur':card_count=add_wolf_cards(verts,uvs,tris,radius_fn)
        else:card_count=add_moss_cards(verts,uvs,tris,radius_fn)
        verts=np.asarray(verts,np.float32);uvs=np.asarray(uvs,np.float32);tris=np.asarray(tris,np.int32);V=verts[tris];UV=uvs[tris]
        Rcam=2.18;zbuf=np.full((S,S),-1e9,np.float32);ou=np.zeros((S,S),np.float32);ov=np.zeros((S,S),np.float32);on=np.zeros((S,S,3),np.float32)
        for tv,tuv in zip(V,UV):
            x=(tv[:,0]/Rcam*.44+.5)*(S-1);y=(.5-tv[:,1]/Rcam*.44)*(S-1);minx=max(0,int(np.floor(x.min())));maxx=min(S-1,int(np.ceil(x.max())));miny=max(0,int(np.floor(y.min())));maxy=min(S-1,int(np.ceil(y.max())))
            if minx>maxx or miny>maxy:continue
            ax,ay=x[0],y[0];bx,by=x[1],y[1];cx,cy=x[2],y[2];den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(den)<1e-8:continue
            yy,xx=np.mgrid[miny:maxy+1,minx:maxx+1];w0=((by-cy)*(xx-cx)+(cx-bx)*(yy-cy))/den;w1=((cy-ay)*(xx-cx)+(ax-cx)*(yy-cy))/den;w2=1-w0-w1;inside=(w0>=-.001)&(w1>=-.001)&(w2>=-.001);zz=w0*tv[0,2]+w1*tv[1,2]+w2*tv[2,2];sub=zbuf[miny:maxy+1,minx:maxx+1];upd=inside&(zz>sub)
            if not np.any(upd):continue
            sub[upd]=zz[upd];uu=w0*tuv[0,0]+w1*tuv[1,0]+w2*tuv[2,0];vv=w0*tuv[0,1]+w1*tuv[1,1]+w2*tuv[2,1];ou[miny:maxy+1,minx:maxx+1][upd]=uu[upd];ov[miny:maxy+1,minx:maxx+1][upd]=vv[upd];vn=norm(tv);nn=norm(w0[...,None]*vn[0]+w1[...,None]*vn[1]+w2[...,None]*vn[2]);on[miny:maxy+1,minx:maxx+1][upd]=nn[upd]
        mask=zbuf>-1e8;Ng=norm(np.where(mask[...,None],on,np.array([0,0,1],np.float32)));bc=srgb_to_linear(bilinear(base,ou,ov));nt=bilinear(normal_tex,ou,ov)*2-1;rr=np.clip(bilinear(rough,ou,ov),.04,1);aa=bilinear(ao,ou,ov);T=norm(np.stack([-Ng[...,2],np.zeros((S,S),np.float32),Ng[...,0]],-1));Bt=norm(np.cross(Ng,T));Ntex=norm(T*nt[...,0:1]+Bt*nt[...,1:2]+Ng*np.maximum(nt[...,2:3],.08));N=norm(Ng*cfg['geo']+Ntex*(1-cfg['geo']));color=bc*(.25+.31*aa[...,None]);lights=[(np.array([-.58,.72,.38],np.float32),2.75,np.array([1,.84,.66],np.float32)),(np.array([.68,.22,.70],np.float32),1.05,np.array([.54,.68,1],np.float32)),(np.array([-.15,-.78,.60],np.float32),.48,np.array([.80,.44,.34],np.float32))];Vcam=np.array([0,0,1],np.float32)
        for L,intensity,lcol in lights:
            L=L/np.linalg.norm(L);ndl=np.clip(np.sum(N*L,axis=-1),0,1);color+=bc*ndl[...,None]*intensity*lcol*.55;H=(L+Vcam)/np.linalg.norm(L+Vcam);ndh=np.clip(np.sum(N*H,axis=-1),0,1);spec=np.power(ndh,4+36*(1-rr))*(1-rr)*.10;color+=spec[...,None]*intensity*lcol
        rimlight=np.power(1-np.clip(Ng[...,2],0,1),2.2);color+=rimlight[...,None]*np.array([.06,.08,.13],np.float32);c=np.clip(color*1.04,0,None);A,Bc,Cc,Dd,Ee=2.51,.03,2.43,.59,.14;c=(c*(A*c+Bc))/(c*(Cc*c+Dd)+Ee);c=linear_to_srgb(np.clip(c,0,1));gy=np.linspace(0,1,S,dtype=np.float32)[:,None,None];bg=np.repeat(np.array([.76,.80,.86],np.float32)[None,None,:]*(1-gy)+np.array([.14,.17,.20],np.float32)[None,None,:]*gy,S,axis=1);mimg=Image.fromarray((mask*255).astype(np.uint8),'L').filter(ImageFilter.GaussianBlur(max(1,int(S*.02))));shadow=np.roll(np.asarray(mimg,dtype=np.float32)/255,int(S*.11),axis=0)*.18;bg*=1-shadow[...,None];img=np.where(mask[...,None],c,bg)
        out=Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8),'RGB').resize((OUT_SIZE,OUT_SIZE),Image.Resampling.LANCZOS);draw=ImageDraw.Draw(out)
        try:f1=ImageFont.truetype('DejaVuSans.ttf',24);f2=ImageFont.truetype('DejaVuSans.ttf',16)
        except:f1=ImageFont.load_default();f2=f1
        draw.rounded_rectangle((28,28,OUT_SIZE-28,105),radius=18,fill=(18,18,20));draw.text((50,43),f'{n} · TRUE MESH + MACRO CARDS',fill='white',font=f1);draw.text((50,72),f"{cfg['subtitle']} · cards {card_count}",fill=(205,205,210),font=f2);out.save(d/'preview-sphere.png')
        metrics={'renderer':'benchmark_style_macro_cards_v5','preset':preset,'renderSize':S,'outputSize':OUT_SIZE,'displacementAmp':cfg['amp'],'heightP05':float(h05),'heightP95':float(h95),'macroCards':card_count,'cardRootAttachment':'full-edge flush to displaced surface','heightTerracing':False,'normalInterpolation':'smooth_vertex'};(d/'preview-mesh-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8');count+=1
    print('rendered',count)
if __name__=='__main__':main()
