#!/usr/bin/env python3
from pathlib import Path
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('build/generated-materials')
OUT_SIZE=1000
RENDER_SIZE=1600
CFG={
    'vfLayeredSandstonePainted':{'amp':.36,'lo':-.22,'hi':1.12,'nlat':180,'nlon':360,'geo':.86,'facet':0.0,'subtitle':'broad continuous cliff slabs · smooth vector silhouette'},
    'vfPainterlyBark':{'amp':.105,'lo':-.72,'hi':1.04,'nlat':170,'nlon':340,'geo':.72,'facet':0.0,'subtitle':'continuous bark planes · smooth attached ridges'},
    'vfPainterlyDirt':{'amp':.135,'lo':-.72,'hi':1.02,'nlat':170,'nlon':340,'geo':.70,'facet':0.0,'subtitle':'broad clods and bowls · smooth macro relief'},
    'vfPainterlyStoneWall':{'amp':.200,'lo':-.55,'hi':1.06,'nlat':180,'nlon':360,'geo':.86,'facet':0.0,'subtitle':'broad fitted wall stones · clean recessed mortar'},
    'vfPainterlyMoss':{'amp':.085,'lo':-.60,'hi':1.06,'nlat':170,'nlon':340,'geo':.82,'facet':0.0,'subtitle':'continuous moss cushions · smooth lifted edge lobes'},
    'vfPainterlyWolfFur':{'amp':.080,'lo':-.72,'hi':1.06,'nlat':180,'nlon':360,'geo':.82,'facet':0.0,'subtitle':'broad coat planes · smooth silhouette fins'},
}

def srgb_to_linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def linear_to_srgb(x):return np.where(x<=.0031308,12.92*x,1.055*np.power(np.clip(x,0,None),1/2.4)-.055)
def norm(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-7)
def smoothstep01(x):
    x=np.clip(x,0.0,1.0);return x*x*(3.0-2.0*x)
def bilinear(tex,u,v):
    h,w=tex.shape[:2];u=np.mod(u,1.0);v=np.mod(v,1.0);x=u*(w-1);y=(1-v)*(h-1);x0=np.floor(x).astype(np.int32);y0=np.floor(y).astype(np.int32);x1=(x0+1)%w;y1=(y0+1)%h;tx=x-x0;ty=y-y0
    if tex.ndim==3:tx=tx[...,None];ty=ty[...,None]
    return (tex[y0,x0]*(1-tx)+tex[y0,x1]*tx)*(1-ty)+(tex[y1,x0]*(1-tx)+tex[y1,x1]*tx)*ty
def load_rgb(d,n,s):return np.asarray(Image.open(d/f'{n}_{s}.png').convert('RGB'),dtype=np.float32)/255
def load_l(d,n,s):return np.asarray(Image.open(d/f'{n}_{s}.png').convert('L'),dtype=np.float32)/255

def soft_terrace(x,amount,levels=7):
    if amount<=0:return x
    z=x*levels;b=math.floor(z);f=z-b;sf=f*f*(3-2*f);t=(b+sf)/levels
    return (1-amount)*x+amount*t

def make_radius_fn(height,h05,span,cfg):
    def radius(u,v,lift=0.0):
        hh=float(bilinear(height,np.array(u),np.array(v)));hn=np.clip((hh-h05)/span,cfg['lo'],cfg['hi']);hn=soft_terrace(float(hn),cfg['facet'])
        return 1+cfg['amp']*hn+lift
    return radius

def sphere_pos(u,v,radius_fn,lift=0.0):
    u=u%1.0;v=max(.02,min(.98,v));lat=math.pi/2-math.pi*v;lon=-math.pi+2*math.pi*u;cl=math.cos(lat);sl=math.sin(lat);r=radius_fn(u,v,lift)
    return np.array([r*cl*math.cos(lon),r*sl,r*cl*math.sin(lon)],np.float32)

def add_ribbon(verts,uvs,tris,radius_fn,u0,v0,du,dv,width,lift,kind='fur',tip_bias=0.0):
    # Broad smooth cards/fins: seven vertices across and ten along the flow.
    # The complete root edge is welded to the displaced shell; no thin strand geometry.
    L=math.hypot(du,dv) or 1.0;pu=-dv/L;pv=du/L
    ts=np.linspace(0.0,1.0,10)
    sides=np.linspace(-1.0,1.0,7)
    base=len(verts)
    for t in ts:
        ease=t*t*(3-2*t)
        if kind=='fur':
            wf=(1-ease)*.94+ease*.30+math.sin(math.pi*t)*.18
            center=lift*(.08*t+.64*ease)
            edge=center*(.28+.16*t)
        else:
            wf=.96+math.sin(math.pi*t)*.15-.11*ease
            center=lift*(.05*t+.34*ease)
            edge=center*(.30+.12*t)
        cu=u0+du*t;cv=v0+dv*t;bend=(t*(1-t))*tip_bias;cu+=bend*pu;cv+=bend*pv
        for side in sides:
            off=width*wf*side*.5;uu=cu+pu*off;vv=cv+pv*off
            crown=(1-abs(side))**1.55;extra=edge+(center-edge)*crown
            if t==0:extra=0.0
            verts.append(tuple(sphere_pos(uu,vv,radius_fn,extra)));uvs.append((uu%1.0,max(.02,min(.98,vv))))
    cols=len(sides)
    for sec in range(len(ts)-1):
        a=base+sec*cols;d=a+cols
        for k in range(cols-1):
            tris.extend(((a+k,d+k,a+k+1),(a+k+1,d+k,d+k+1)))

def add_wolf_cards(verts,uvs,tris,radius_fn):
    body=[
        (.64,.24,.010,.205,.165,.105,-.010),(.82,.25,-.010,.205,.160,.100,.012),
        (.69,.45,-.008,.215,.172,.115,.010),(.86,.48,.012,.205,.165,.110,-.012),(.75,.66,-.010,.185,.160,.105,.010),
    ]
    rim=[
        (.505,.28,.024,.185,.112,.145,-.014),(.508,.50,.026,.195,.120,.150,.014),(.515,.70,.020,.175,.108,.135,-.010),
        (.995,.30,-.024,.185,.112,.145,.014),(.992,.52,-.026,.195,.120,.150,-.014),(.985,.71,-.020,.175,.108,.135,.010),
    ]
    for c in body+rim:add_ribbon(verts,uvs,tris,radius_fn,*c[:-1],kind='fur',tip_bias=c[-1])
    return len(body)+len(rim)

def add_moss_cards(verts,uvs,tris,radius_fn):
    cards=[
        (.58,.25,.020,.120,.235,.090,.010),(.80,.24,-.014,.125,.255,.095,-.012),
        (.54,.48,.022,.125,.250,.100,-.014),(.76,.46,-.010,.130,.270,.105,.012),
        (.94,.49,-.020,.115,.225,.095,.014),(.64,.70,.016,.115,.255,.100,.010),(.86,.69,-.014,.115,.250,.095,-.010),
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
            for ix in range(nlon+1):
                u=ix/nlon;verts.append(tuple(sphere_pos(u,v,radius_fn,0)));uvs.append((u,v))
        tris=[];row=nlon+1
        for iy in range(nlat):
            for ix in range(nlon):
                a=iy*row+ix;b=a+1;c=a+row;dd=c+1;tris.extend(((a,c,b),(b,c,dd)))
        card_count=0
        if preset=='vfPainterlyWolfFur':card_count=add_wolf_cards(verts,uvs,tris,radius_fn)
        elif preset=='vfPainterlyMoss':card_count=add_moss_cards(verts,uvs,tris,radius_fn)
        verts=np.asarray(verts,np.float32);uvs=np.asarray(uvs,np.float32);tris=np.asarray(tris,np.int32);V=verts[tris];UV=uvs[tris]
        Rcam=2.35;zbuf=np.full((S,S),-1e9,np.float32);ou=np.zeros((S,S),np.float32);ov=np.zeros((S,S),np.float32);on=np.zeros((S,S,3),np.float32)
        for tv,tuv in zip(V,UV):
            x=(tv[:,0]/Rcam*.44+.5)*(S-1);y=(.5-tv[:,1]/Rcam*.44)*(S-1);minx=max(0,int(np.floor(x.min())));maxx=min(S-1,int(np.ceil(x.max())));miny=max(0,int(np.floor(y.min())));maxy=min(S-1,int(np.ceil(y.max())))
            if minx>maxx or miny>maxy:continue
            ax,ay=x[0],y[0];bx,by=x[1],y[1];cx,cy=x[2],y[2];den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(den)<1e-8:continue
            yy,xx=np.mgrid[miny:maxy+1,minx:maxx+1];w0=((by-cy)*(xx-cx)+(cx-bx)*(yy-cy))/den;w1=((cy-ay)*(xx-cx)+(ax-cx)*(yy-cy))/den;w2=1-w0-w1;inside=(w0>=-.001)&(w1>=-.001)&(w2>=-.001)
            zz=w0*tv[0,2]+w1*tv[1,2]+w2*tv[2,2];sub=zbuf[miny:maxy+1,minx:maxx+1];upd=inside&(zz>sub)
            if not np.any(upd):continue
            sub[upd]=zz[upd];uu=w0*tuv[0,0]+w1*tuv[1,0]+w2*tuv[2,0];vv=w0*tuv[0,1]+w1*tuv[1,1]+w2*tuv[2,1];ou[miny:maxy+1,minx:maxx+1][upd]=uu[upd];ov[miny:maxy+1,minx:maxx+1][upd]=vv[upd]
            vn=norm(tv);nn=norm(w0[...,None]*vn[0]+w1[...,None]*vn[1]+w2[...,None]*vn[2]);on[miny:maxy+1,minx:maxx+1][upd]=nn[upd]
        mask=zbuf>-1e8;Ng=norm(np.where(mask[...,None],on,np.array([0,0,1],np.float32)));bc=srgb_to_linear(bilinear(base,ou,ov));nt=bilinear(normal_tex,ou,ov)*2-1;rr=np.clip(bilinear(rough,ou,ov),.04,1);aa=bilinear(ao,ou,ov);T=norm(np.stack([-Ng[...,2],np.zeros((S,S),np.float32),Ng[...,0]],-1));Bt=norm(np.cross(Ng,T));Ntex=norm(T*nt[...,0:1]+Bt*nt[...,1:2]+Ng*np.maximum(nt[...,2:3],.08));N=norm(Ng*cfg['geo']+Ntex*(1-cfg['geo']));color=bc*(.21+.28*aa[...,None]);lights=[(np.array([-.58,.72,.38],np.float32),2.55,np.array([1,.82,.62],np.float32)),(np.array([.68,.22,.70],np.float32),.95,np.array([.50,.64,1],np.float32)),(np.array([-.15,-.78,.60],np.float32),.44,np.array([.78,.38,.30],np.float32))];Vcam=np.array([0,0,1],np.float32)
        for L,intensity,lcol in lights:
            L=L/np.linalg.norm(L);ndl=np.clip(np.sum(N*L,axis=-1),0,1);color+=bc*ndl[...,None]*intensity*lcol*.55;H=(L+Vcam)/np.linalg.norm(L+Vcam);ndh=np.clip(np.sum(N*H,axis=-1),0,1);spec=np.power(ndh,4+36*(1-rr))*(1-rr)*.11;color+=spec[...,None]*intensity*lcol
        rimlight=np.power(1-np.clip(Ng[...,2],0,1),2.2);color+=rimlight[...,None]*np.array([.065,.085,.145],np.float32);c=np.clip(color*1.03,0,None);A,Bc,Cc,Dd,Ee=2.51,.03,2.43,.59,.14;c=(c*(A*c+Bc))/(c*(Cc*c+Dd)+Ee);c=linear_to_srgb(np.clip(c,0,1));gy=np.linspace(0,1,S,dtype=np.float32)[:,None,None];bg=np.repeat(np.array([.76,.80,.86],np.float32)[None,None,:]*(1-gy)+np.array([.14,.17,.20],np.float32)[None,None,:]*gy,S,axis=1);mimg=Image.fromarray((mask*255).astype(np.uint8),'L').filter(ImageFilter.GaussianBlur(max(1,int(S*.02))));shadow=np.roll(np.asarray(mimg,dtype=np.float32)/255,int(S*.11),axis=0)*.18;bg*=1-shadow[...,None];img=np.where(mask[...,None],c,bg)
        out=Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8),'RGB').resize((OUT_SIZE,OUT_SIZE),Image.Resampling.LANCZOS)
        draw=ImageDraw.Draw(out)
        try:f1=ImageFont.truetype('DejaVuSans.ttf',24);f2=ImageFont.truetype('DejaVuSans.ttf',16)
        except:f1=ImageFont.load_default();f2=f1
        draw.rounded_rectangle((28,28,OUT_SIZE-28,105),radius=18,fill=(18,18,20));title='TRUE MESH + MACRO CARDS' if card_count else 'TRUE MESH DISPLACEMENT';draw.text((50,43),f'{n} · {title}',fill='white',font=f1);sub=f"{cfg['subtitle']} · cards {card_count}" if card_count else f"{cfg['subtitle']} · amp {cfg['amp']:.3f}";draw.text((50,72),sub,fill=(205,205,210),font=f2);out.save(d/'preview-sphere.png')
        metrics={'renderer':'continuous_vector_height_smooth_vertex_normals_v4','preset':preset,'renderSize':S,'outputSize':OUT_SIZE,'repeatScale':1.0,'displacementAmp':cfg['amp'],'heightP05':float(h05),'heightP50':float(h50),'heightP95':float(h95),'heightSpanP05P95':float(span),'meshLatitudeSegments':nlat,'meshLongitudeSegments':nlon,'macroCards':card_count,'cardCrossSections':7 if card_count else 0,'cardLongitudinalSections':10 if card_count else 0,'cardRootAttachment':'full_edge_flush_to_displaced_surface' if card_count else 'none','heightTerracing':False,'normalInterpolation':'smooth_vertex'};(d/'preview-mesh-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8');count+=1
    print('rendered',count)
if __name__=='__main__':main()
