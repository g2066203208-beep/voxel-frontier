package com.openai.x2dboneplayer;

import android.content.Context;
import android.graphics.*;
import android.view.View;
import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

public class RigPlayerView extends View {
    static class Bone {
        String id,parent;
        float dx,dy,drot,dsx=1,dsy=1;
        float[] rest=new float[6], restGlobal=new float[6], invRestGlobal=new float[6], curGlobal=new float[6], skin=new float[6];
    }
    static class RotKey { float t,v; RotKey(float T,float V){t=T;v=V;} }
    static class PosKey { float t,x,y; PosKey(float T,float X,float Y){t=T;x=X;y=Y;} }
    static class BoneTrack {
        ArrayList<RotKey> rot=new ArrayList<>();
        ArrayList<PosKey> pos=new ArrayList<>();
    }
    static class Clip {
        String name; float duration=1; boolean loop=true;
        HashMap<String,BoneTrack> tracks=new HashMap<>();
    }
    static class SpriteAttachment {
        String bone,image; float px,py,scale=1; Bitmap bmp;
    }
    static class Mesh {
        String name,image; Bitmap bmp;
        float[] restVerts, uvs, deformed;
        short[] indices;
        int[][] boneIndices;
        float[][] weights;
        Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
    }

    final ArrayList<Bone> bones=new ArrayList<>();
    final HashMap<String,Bone> boneMap=new HashMap<>();
    final HashMap<String,Integer> boneIndex=new HashMap<>();
    final ArrayList<SpriteAttachment> sprites=new ArrayList<>();
    final ArrayList<Mesh> meshes=new ArrayList<>();
    final LinkedHashMap<String,Clip> clips=new LinkedHashMap<>();
    final ArrayList<String> clipOrder=new ArrayList<>();

    final Paint bonePaint=new Paint(Paint.ANTI_ALIAS_FLAG);
    final Paint jointPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
    final Paint infoPaint=new Paint(Paint.ANTI_ALIAS_FLAG);

    float projectW=900,projectH=900,modelOffsetX=450,modelOffsetY=450;
    float duration=1,time=0;
    boolean playing=true,showBones=false,scrubbing=false,loaded=false;
    long lastNs=0;
    int clipIndex=0;
    String sourceName="",format="";

    public RigPlayerView(Context c){
        super(c);
        setBackgroundColor(0xff1e1c27);
        bonePaint.setColor(0xffffc440);bonePaint.setStrokeWidth(5);bonePaint.setStrokeCap(Paint.Cap.ROUND);
        jointPaint.setColor(0xffffe078);jointPaint.setStyle(Paint.Style.FILL);
        infoPaint.setColor(0xffc9c4d6);infoPaint.setTextSize(28);
    }

    public String currentClipName(){
        return clipOrder.isEmpty()?"":clipOrder.get(Math.max(0,Math.min(clipIndex,clipOrder.size()-1)));
    }

    public String describe(){
        String s=(sourceName==null||sourceName.isEmpty())?"Rig":sourceName;
        return s+" · "+bones.size()+" 骨骼 · "+meshes.size()+" Mesh · "+clipOrder.size()+" 动作 · "+currentClipName();
    }

    public void nextClip(){
        if(clipOrder.isEmpty())return;
        clipIndex=(clipIndex+1)%clipOrder.size();
        setClip(clipOrder.get(clipIndex));
    }

    public void setClip(String name){
        int idx=clipOrder.indexOf(name);
        if(idx>=0)clipIndex=idx;
        Clip c=clips.get(name);
        if(c!=null){duration=Math.max(.001f,c.duration);time=0;playing=true;lastNs=0;invalidate();}
    }

    private void clearAll(){
        bones.clear();boneMap.clear();boneIndex.clear();sprites.clear();meshes.clear();clips.clear();clipOrder.clear();
        projectW=900;projectH=900;modelOffsetX=450;modelOffsetY=450;duration=1;time=0;clipIndex=0;lastNs=0;sourceName="";format="";loaded=false;
    }

    public void loadZip(InputStream raw)throws Exception{
        clearAll();
        HashMap<String,byte[]> data=new HashMap<>();
        try(ZipInputStream z=new ZipInputStream(new BufferedInputStream(raw))){
            ZipEntry e; byte[] buf=new byte[32768];
            while((e=z.getNextEntry())!=null){
                if(e.isDirectory())continue;
                ByteArrayOutputStream o=new ByteArrayOutputStream();
                int n;while((n=z.read(buf))>0)o.write(buf,0,n);
                String name=e.getName().replace("\\","/");
                if(name.contains("/"))name=name.substring(name.lastIndexOf('/')+1);
                data.put(name,o.toByteArray());
            }
        }
        byte[] pj=data.get("project.json");
        if(pj==null)throw new IOException("ZIP 根目录缺少 project.json");
        JSONObject j=new JSONObject(new String(pj,"UTF-8"));
        format=j.optString("format","");
        JSONObject src=j.optJSONObject("source");
        if(src!=null)sourceName=src.optString("name","");
        if(j.has("meshes")&&j.has("animations"))loadV2(j,data); else loadV1(j,data);
        loaded=true;playing=true;lastNs=0;invalidate();
    }

    private void loadV2(JSONObject j,HashMap<String,byte[]> data)throws Exception{
        projectW=(float)j.optDouble("width",900);projectH=(float)j.optDouble("height",900);
        modelOffsetX=(float)j.optDouble("modelOffsetX",projectW/2);modelOffsetY=(float)j.optDouble("modelOffsetY",projectH/2);

        JSONArray ba=j.getJSONArray("bones");
        for(int i=0;i<ba.length();i++){
            JSONObject q=ba.getJSONObject(i);Bone b=new Bone();
            b.id=q.getString("id");b.parent=q.isNull("parent")?null:q.optString("parent",null);
            b.dx=(float)q.optDouble("defaultX",0);b.dy=(float)q.optDouble("defaultY",0);b.drot=(float)q.optDouble("defaultRotation",0);
            b.dsx=(float)q.optDouble("defaultScaleX",1);b.dsy=(float)q.optDouble("defaultScaleY",1);
            JSONArray r=q.getJSONArray("rest");for(int k=0;k<6;k++)b.rest[k]=(float)r.getDouble(k);
            addBone(b);
        }
        computeRest();

        JSONArray ma=j.getJSONArray("meshes");
        for(int i=0;i<ma.length();i++){
            JSONObject q=ma.getJSONObject(i);Mesh m=new Mesh();
            m.name=q.optString("name","mesh"+i);m.image=q.getString("image");
            byte[] im=data.get(m.image);
            if(im==null)throw new IOException("缺少纹理 "+m.image);
            m.bmp=BitmapFactory.decodeByteArray(im,0,im.length);
            if(m.bmp==null)throw new IOException("纹理解码失败 "+m.image);
            m.paint.setShader(new BitmapShader(m.bmp,Shader.TileMode.CLAMP,Shader.TileMode.CLAMP));
            m.restVerts=jsonFloatArray(q.getJSONArray("vertices"));
            m.uvs=jsonFloatArray(q.getJSONArray("uvs"));
            JSONArray ti=q.getJSONArray("triangles");m.indices=new short[ti.length()];
            for(int k=0;k<ti.length();k++)m.indices[k]=(short)ti.getInt(k);
            int nv=m.restVerts.length/2;m.deformed=new float[m.restVerts.length];
            m.boneIndices=new int[nv][];m.weights=new float[nv][];
            JSONArray ia=q.getJSONArray("influences");
            if(ia.length()!=nv)throw new IOException("Mesh "+m.name+" 权重顶点数量不匹配");
            for(int v=0;v<nv;v++){
                JSONArray row=ia.getJSONArray(v);
                m.boneIndices[v]=new int[row.length()];m.weights[v]=new float[row.length()];
                float sum=0;
                for(int w=0;w<row.length();w++){
                    JSONArray pair=row.getJSONArray(w);String bid=pair.getString(0);
                    Integer bi=boneIndex.get(bid);if(bi==null)throw new IOException("未知权重骨骼 "+bid);
                    m.boneIndices[v][w]=bi;m.weights[v][w]=(float)pair.getDouble(1);sum+=m.weights[v][w];
                }
                if(sum<=0)throw new IOException("Mesh "+m.name+" 顶点 "+v+" 权重和为0");
                for(int w=0;w<m.weights[v].length;w++)m.weights[v][w]/=sum;
            }
            meshes.add(m);
        }

        JSONObject an=j.getJSONObject("animations");
        ArrayList<String> names=new ArrayList<>();
        Iterator<String> it=an.keys();while(it.hasNext())names.add(it.next());
        String[] preferred={"idle","walk","run","fly","fall","jump","land","land_hard"};
        for(String p:preferred)if(names.remove(p))clipOrder.add(p);
        Collections.sort(names);clipOrder.addAll(names);
        for(String name:clipOrder){
            JSONObject cq=an.getJSONObject(name);Clip c=new Clip();c.name=name;
            c.duration=(float)cq.optDouble("duration",1);c.loop=cq.optBoolean("loop",true);
            JSONObject tr=cq.optJSONObject("tracks");
            if(tr!=null){
                Iterator<String> bt=tr.keys();
                while(bt.hasNext()){
                    String bid=bt.next();JSONObject tq=tr.getJSONObject(bid);BoneTrack t=new BoneTrack();
                    JSONArray rr=tq.optJSONArray("rotation");
                    if(rr!=null)for(int k=0;k<rr.length();k++){JSONObject x=rr.getJSONObject(k);t.rot.add(new RotKey((float)x.getDouble("time"),(float)x.getDouble("value")));}
                    JSONArray pp=tq.optJSONArray("position");
                    if(pp!=null)for(int k=0;k<pp.length();k++){JSONObject x=pp.getJSONObject(k);t.pos.add(new PosKey((float)x.getDouble("time"),(float)x.getDouble("x"),(float)x.getDouble("y")));}
                    c.tracks.put(bid,t);
                }
            }
            clips.put(name,c);
        }
        String def=j.optString("defaultAnimation",clipOrder.isEmpty()?"":clipOrder.get(0));
        clipIndex=Math.max(0,clipOrder.indexOf(def));
        if(clipIndex<0)clipIndex=0;
        if(!clipOrder.isEmpty())duration=Math.max(.001f,clips.get(clipOrder.get(clipIndex)).duration);
    }

    private void loadV1(JSONObject j,HashMap<String,byte[]> data)throws Exception{
        sourceName="Legacy X2D v0.1";
        projectW=(float)j.optDouble("width",1080);projectH=(float)j.optDouble("height",1920);
        modelOffsetX=0;modelOffsetY=0;
        JSONArray ba=j.getJSONArray("bones");
        for(int i=0;i<ba.length();i++){
            JSONObject q=ba.getJSONObject(i);Bone b=new Bone();
            b.id=q.getString("id");b.parent=q.isNull("parent")?null:q.optString("parent",null);
            b.dx=(float)q.optDouble("x",0);b.dy=(float)q.optDouble("y",0);b.drot=(float)q.optDouble("rotation",0);
            b.rest=local(b.dx,b.dy,b.drot,1,1);addBone(b);
        }
        computeRest();
        JSONArray sa=j.optJSONArray("sprites");
        if(sa!=null)for(int i=0;i<sa.length();i++){
            JSONObject q=sa.getJSONObject(i);SpriteAttachment a=new SpriteAttachment();
            a.bone=q.getString("bone");a.image=q.getString("image");a.px=(float)q.optDouble("pivotX",0);a.py=(float)q.optDouble("pivotY",0);a.scale=(float)q.optDouble("scale",1);
            byte[] im=data.get(a.image);if(im!=null)a.bmp=BitmapFactory.decodeByteArray(im,0,im.length);sprites.add(a);
        }
        Clip c=new Clip();c.name="default";c.duration=(float)j.optDouble("duration",2);c.loop=true;
        JSONObject kf=j.optJSONObject("keyframes");
        if(kf!=null){
            Iterator<String> it=kf.keys();
            while(it.hasNext()){
                String bid=it.next();JSONArray ar=kf.getJSONArray(bid);BoneTrack t=new BoneTrack();
                for(int k=0;k<ar.length();k++){
                    JSONObject q=ar.getJSONObject(k);float tt=(float)q.optDouble("time",0);
                    t.pos.add(new PosKey(tt,(float)q.optDouble("x",0),(float)q.optDouble("y",0)));
                    t.rot.add(new RotKey(tt,(float)q.optDouble("rotation",0)));
                }
                c.tracks.put(bid,t);
            }
        }
        clips.put(c.name,c);clipOrder.add(c.name);duration=c.duration;clipIndex=0;
    }

    private static float[] jsonFloatArray(JSONArray a)throws Exception{
        float[] r=new float[a.length()];for(int i=0;i<r.length;i++)r[i]=(float)a.getDouble(i);return r;
    }
    private void addBone(Bone b){boneIndex.put(b.id,bones.size());bones.add(b);boneMap.put(b.id,b);}
    private void computeRest(){
        for(Bone b:bones){
            if(b.parent==null)b.restGlobal=copy(b.rest);
            else b.restGlobal=mul(boneMap.get(b.parent).restGlobal,b.rest);
            b.invRestGlobal=inv(b.restGlobal);
        }
    }

    @Override protected void onDraw(Canvas c){
        super.onDraw(c);
        long now=System.nanoTime();if(lastNs==0)lastNs=now;
        float dt=Math.min(.05f,(now-lastNs)/1_000_000_000f);lastNs=now;
        Clip clip=clips.get(currentClipName());
        if(playing&&!scrubbing&&loaded&&clip!=null){
            time+=dt;
            if(time>duration){time=clip.loop?(time%duration):duration;}
        }
        if(!loaded){
            c.drawText("导入一个 X2D Rig ZIP",40,70,infoPaint);
            c.drawText("v0.2 支持：Mesh / UV / 多骨权重 / 原始动画Clip",40,115,infoPaint);
            return;
        }
        solve(clip);
        deform();
        float s=Math.min(getWidth()/Math.max(1,projectW),getHeight()/Math.max(1,projectH))*.94f;
        float ox=(getWidth()-projectW*s)/2f,oy=(getHeight()-projectH*s)/2f;
        c.save();c.translate(ox,oy);c.scale(s,s);c.translate(modelOffsetX,modelOffsetY);
        drawMeshes(c);drawSprites(c);if(showBones)drawBones(c);c.restore();
        if(playing)postInvalidateOnAnimation();
    }

    private void solve(Clip clip){
        for(Bone b:bones){
            float x=b.dx,y=b.dy,r=b.drot;
            BoneTrack t=clip==null?null:clip.tracks.get(b.id);
            if(t!=null){
                if(!t.pos.isEmpty()){float[] p=samplePos(t.pos,time);x=p[0];y=p[1];}
                if(!t.rot.isEmpty())r=sampleRot(t.rot,time);
            }
            float[] lm=local(x,y,r,b.dsx,b.dsy);
            if(b.parent==null)b.curGlobal=lm; else b.curGlobal=mul(boneMap.get(b.parent).curGlobal,lm);
        }
        for(Bone b:bones)b.skin=mul(b.curGlobal,b.invRestGlobal);
    }

    private void deform(){
        for(Mesh m:meshes){
            int nv=m.restVerts.length/2;
            for(int v=0;v<nv;v++){
                float x=m.restVerts[v*2],y=m.restVerts[v*2+1],ox=0,oy=0;
                for(int j=0;j<m.boneIndices[v].length;j++){
                    Bone b=bones.get(m.boneIndices[v][j]);float[] q=apply(b.skin,x,y);float w=m.weights[v][j];
                    ox+=q[0]*w;oy+=q[1]*w;
                }
                m.deformed[v*2]=ox;m.deformed[v*2+1]=oy;
            }
        }
    }

    private void drawMeshes(Canvas c){
        for(Mesh m:meshes){
            c.drawVertices(Canvas.VertexMode.TRIANGLES,m.deformed.length,m.deformed,0,m.uvs,0,null,0,m.indices,0,m.indices.length,m.paint);
        }
    }
    private void drawSprites(Canvas c){
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
        for(SpriteAttachment a:sprites){
            if(a.bmp==null)continue;Bone b=boneMap.get(a.bone);if(b==null)continue;
            c.save();
            float[] M=b.curGlobal;
            Matrix mm=new Matrix();mm.setValues(new float[]{M[0],M[2],M[4],M[1],M[3],M[5],0,0,1});
            c.concat(mm);c.scale(a.scale,a.scale);c.drawBitmap(a.bmp,-a.px,-a.py,p);c.restore();
        }
    }
    private void drawBones(Canvas c){
        for(Bone b:bones){
            float bx=b.curGlobal[4],by=b.curGlobal[5];
            if(b.parent!=null){
                Bone p=boneMap.get(b.parent);c.drawLine(p.curGlobal[4],p.curGlobal[5],bx,by,bonePaint);
            }
            c.drawCircle(bx,by,7,jointPaint);
        }
    }

    private static float sampleRot(ArrayList<RotKey> a,float t){
        if(a.size()==1)return a.get(0).v;if(t<=a.get(0).t)return a.get(0).v;if(t>=a.get(a.size()-1).t)return a.get(a.size()-1).v;
        for(int i=0;i<a.size()-1;i++){RotKey x=a.get(i),y=a.get(i+1);if(t>=x.t&&t<=y.t){float f=(t-x.t)/Math.max(.000001f,y.t-x.t);return x.v+(y.v-x.v)*f;}}
        return a.get(a.size()-1).v;
    }
    private static float[] samplePos(ArrayList<PosKey> a,float t){
        if(a.size()==1)return new float[]{a.get(0).x,a.get(0).y};if(t<=a.get(0).t)return new float[]{a.get(0).x,a.get(0).y};
        if(t>=a.get(a.size()-1).t){PosKey z=a.get(a.size()-1);return new float[]{z.x,z.y};}
        for(int i=0;i<a.size()-1;i++){PosKey x=a.get(i),y=a.get(i+1);if(t>=x.t&&t<=y.t){float f=(t-x.t)/Math.max(.000001f,y.t-x.t);return new float[]{x.x+(y.x-x.x)*f,x.y+(y.y-x.y)*f};}}
        PosKey z=a.get(a.size()-1);return new float[]{z.x,z.y};
    }

    static float[] local(float x,float y,float deg,float sx,float sy){
        double r=Math.toRadians(deg);float co=(float)Math.cos(r),si=(float)Math.sin(r);
        return new float[]{co*sx,si*sx,-si*sy,co*sy,x,y};
    }
    static float[] mul(float[] A,float[] B){
        return new float[]{
            A[0]*B[0]+A[2]*B[1], A[1]*B[0]+A[3]*B[1],
            A[0]*B[2]+A[2]*B[3], A[1]*B[2]+A[3]*B[3],
            A[0]*B[4]+A[2]*B[5]+A[4], A[1]*B[4]+A[3]*B[5]+A[5]
        };
    }
    static float[] inv(float[] M){
        float det=M[0]*M[3]-M[1]*M[2];if(Math.abs(det)<1e-8f)return new float[]{1,0,0,1,0,0};
        float a=M[3]/det,b=-M[1]/det,c=-M[2]/det,d=M[0]/det;
        return new float[]{a,b,c,d,-(a*M[4]+c*M[5]),-(b*M[4]+d*M[5])};
    }
    static float[] apply(float[] M,float x,float y){return new float[]{M[0]*x+M[2]*y+M[4],M[1]*x+M[3]*y+M[5]};}
    static float[] copy(float[] a){return Arrays.copyOf(a,a.length);}
}
