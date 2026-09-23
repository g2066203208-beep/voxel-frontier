package com.openai.x2dboneplayer;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

public class MainActivity extends Activity {
    private static final int REQ_ZIP=1001;
    private BonePlayerView player;
    private TextView status,timeText;
    private SeekBar seek;
    private Button playBtn,bonesBtn;
    private final Handler ui=new Handler(Looper.getMainLooper());

    @Override public void onCreate(Bundle b){
        super.onCreate(b);
        buildUi();
        player.loadDemo();
        status.setText("内置示例：真实父子骨骼层级正在播放");
        ui.post(uiTick);
    }

    private void buildUi(){
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(21,19,29));
        root.setOnApplyWindowInsetsListener((v,i)->{
            v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),
                    i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());
            return i;
        });

        status=new TextView(this);
        status.setTextColor(Color.WHITE);
        status.setTextSize(14);
        status.setPadding(dp(12),dp(8),dp(12),dp(6));
        root.addView(status,new LinearLayout.LayoutParams(-1,-2));

        player=new BonePlayerView(this);
        root.addView(player,new LinearLayout.LayoutParams(-1,0,1));

        LinearLayout row1=new LinearLayout(this);
        row1.setGravity(Gravity.CENTER);
        row1.setPadding(dp(6),dp(5),dp(6),dp(2));
        Button importBtn=button("导入骨骼ZIP");
        playBtn=button("暂停");
        bonesBtn=button("隐藏骨骼");
        Button resetBtn=button("重置");
        row1.addView(importBtn,weight());
        row1.addView(playBtn,weight());
        row1.addView(bonesBtn,weight());
        row1.addView(resetBtn,weight());
        root.addView(row1,new LinearLayout.LayoutParams(-1,-2));

        LinearLayout row2=new LinearLayout(this);
        row2.setGravity(Gravity.CENTER_VERTICAL);
        row2.setPadding(dp(10),dp(0),dp(10),dp(8));
        timeText=new TextView(this);
        timeText.setTextColor(Color.LTGRAY);
        timeText.setText("0.00 / 2.00 s");
        seek=new SeekBar(this);
        seek.setMax(1000);
        row2.addView(timeText,new LinearLayout.LayoutParams(dp(110),-2));
        row2.addView(seek,new LinearLayout.LayoutParams(0,-2,1));
        root.addView(row2,new LinearLayout.LayoutParams(-1,-2));

        importBtn.setOnClickListener(v->pickZip());
        playBtn.setOnClickListener(v->{
            player.playing=!player.playing;
            playBtn.setText(player.playing?"暂停":"播放");
        });
        bonesBtn.setOnClickListener(v->{
            player.showBones=!player.showBones;
            bonesBtn.setText(player.showBones?"隐藏骨骼":"显示骨骼");
            player.invalidate();
        });
        resetBtn.setOnClickListener(v->{player.time=0;player.playing=true;playBtn.setText("暂停");player.invalidate();});
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar s,int p,boolean fromUser){
                if(fromUser){player.time=player.duration*p/1000f;player.invalidate();}
            }
            public void onStartTrackingTouch(SeekBar s){player.scrubbing=true;}
            public void onStopTrackingTouch(SeekBar s){player.scrubbing=false;}
        });

        setContentView(root);
    }

    private LinearLayout.LayoutParams weight(){return new LinearLayout.LayoutParams(0,dp(48),1);}
    private Button button(String s){
        Button b=new Button(this); b.setText(s); b.setTextSize(13); b.setAllCaps(false);
        return b;
    }
    private int dp(int v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}

    private void pickZip(){
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/zip");
        i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/zip","application/octet-stream"});
        startActivityForResult(i,REQ_ZIP);
    }

    @Override protected void onActivityResult(int req,int result,Intent data){
        super.onActivityResult(req,result,data);
        if(req!=REQ_ZIP||result!=RESULT_OK||data==null) return;
        Uri uri=data.getData();
        try(InputStream in=getContentResolver().openInputStream(uri)){
            player.loadZip(in);
            status.setText("已导入："+displayName(uri)+" · "+player.bones.size()+" 骨骼 · "+player.attachments.size()+" 图片");
            playBtn.setText("暂停");
        }catch(Exception e){
            new AlertDialog.Builder(this).setTitle("导入失败").setMessage(e.toString()).setPositiveButton("确定",null).show();
        }
    }

    private String displayName(Uri uri){
        String n="project.zip";
        try(android.database.Cursor c=getContentResolver().query(uri,null,null,null,null)){
            if(c!=null&&c.moveToFirst()){
                int idx=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if(idx>=0)n=c.getString(idx);
            }
        }catch(Exception ignored){}
        return n;
    }

    private final Runnable uiTick=new Runnable(){
        @Override public void run(){
            if(player!=null){
                float d=Math.max(.001f,player.duration);
                seek.setProgress((int)(1000f*player.time/d));
                timeText.setText(String.format(Locale.US,"%.2f / %.2f s",player.time,d));
            }
            ui.postDelayed(this,50);
        }
    };

    @Override protected void onDestroy(){ui.removeCallbacksAndMessages(null);super.onDestroy();}

    public static class BonePlayerView extends View {
        static class Bone{
            String id,parent; float x,y,rot,len,wx,wy,wrot;
            Bone(String i,String p,float X,float Y,float R,float L){id=i;parent=p;x=X;y=Y;rot=R;len=L;}
        }
        static class Key{
            float t,x,y,r; Key(float T,float X,float Y,float R){t=T;x=X;y=Y;r=R;}
        }
        static class Attachment{
            String bone,image; float px,py,scale=1; Bitmap bmp;
        }

        final ArrayList<Bone> bones=new ArrayList<>();
        final HashMap<String,Bone> boneMap=new HashMap<>();
        final HashMap<String,ArrayList<Key>> tracks=new HashMap<>();
        final ArrayList<Attachment> attachments=new ArrayList<>();
        final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
        final Paint bonePaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        float projectW=1080,projectH=1920,duration=2f,time=0;
        boolean playing=true,showBones=true,scrubbing=false,demo=true;
        long lastNs=0;

        BonePlayerView(Context c){
            super(c);
            setBackgroundColor(Color.rgb(30,28,39));
            bonePaint.setStrokeCap(Paint.Cap.ROUND);
        }

        void clearModel(){
            bones.clear();boneMap.clear();tracks.clear();attachments.clear();
            time=0;lastNs=0;
        }

        void addBone(Bone b){bones.add(b);boneMap.put(b.id,b);}
        void addKeys(String id,Key... ks){
            ArrayList<Key> l=new ArrayList<>();Collections.addAll(l,ks);tracks.put(id,l);
        }

        public void loadDemo(){
            clearModel(); demo=true; projectW=720;projectH=1080;duration=2.4f;
            addBone(new Bone("root",null,360,650,0,0));
            addBone(new Bone("torso","root",0,0,-90,220));
            addBone(new Bone("head","torso",220,0,0,0));
            addBone(new Bone("upperArmL","torso",165,0,-120,150));
            addBone(new Bone("foreArmL","upperArmL",150,0,-20,145));
            addBone(new Bone("upperArmR","torso",165,0,120,150));
            addBone(new Bone("foreArmR","upperArmR",150,0,20,145));
            addBone(new Bone("thighL","root",-50,0,82,190));
            addBone(new Bone("calfL","thighL",190,0,8,190));
            addBone(new Bone("thighR","root",50,0,98,190));
            addBone(new Bone("calfR","thighR",190,0,-8,190));
            addKeys("root",
                new Key(0,360,650,0),new Key(.6f,360,642,0),new Key(1.2f,360,650,0),
                new Key(1.8f,360,642,0),new Key(2.4f,360,650,0));
            addKeys("torso",new Key(0,0,0,-92),new Key(1.2f,0,0,-88),new Key(2.4f,0,0,-92));
            addKeys("upperArmL",new Key(0,165,0,-135),new Key(.6f,165,0,-65),new Key(1.2f,165,0,-125),new Key(1.8f,165,0,-55),new Key(2.4f,165,0,-135));
            addKeys("foreArmL",new Key(0,150,0,-35),new Key(.6f,150,0,-75),new Key(1.2f,150,0,-25),new Key(1.8f,150,0,-70),new Key(2.4f,150,0,-35));
            addKeys("upperArmR",new Key(0,165,0,125),new Key(1.2f,165,0,145),new Key(2.4f,165,0,125));
            addKeys("foreArmR",new Key(0,150,0,30),new Key(1.2f,150,0,5),new Key(2.4f,150,0,30));
            addKeys("thighL",new Key(0,-50,0,80),new Key(1.2f,-50,0,88),new Key(2.4f,-50,0,80));
            addKeys("thighR",new Key(0,50,0,100),new Key(1.2f,50,0,92),new Key(2.4f,50,0,100));
            playing=true;invalidate();
        }

        public void loadZip(InputStream raw)throws Exception{
            clearModel(); demo=false;
            HashMap<String,byte[]> data=new HashMap<>();
            ZipInputStream z=new ZipInputStream(new BufferedInputStream(raw));
            ZipEntry e; byte[] buf=new byte[16384];
            while((e=z.getNextEntry())!=null){
                if(e.isDirectory())continue;
                ByteArrayOutputStream o=new ByteArrayOutputStream();
                int n;while((n=z.read(buf))>0)o.write(buf,0,n);
                String name=e.getName().replace("\\","/");
                if(name.contains("/"))name=name.substring(name.lastIndexOf('/')+1);
                data.put(name,o.toByteArray());
            }
            if(!data.containsKey("project.json"))throw new IOException("ZIP 根目录需要 project.json");
            JSONObject j=new JSONObject(new String(data.get("project.json"),"UTF-8"));
            projectW=(float)j.optDouble("width",1080);projectH=(float)j.optDouble("height",1920);
            duration=Math.max(.1f,(float)j.optDouble("duration",2));
            JSONArray ba=j.getJSONArray("bones");
            for(int i=0;i<ba.length();i++){
                JSONObject b=ba.getJSONObject(i);
                String parent=b.isNull("parent")?null:b.optString("parent",null);
                addBone(new Bone(b.getString("id"),parent,(float)b.optDouble("x",0),(float)b.optDouble("y",0),
                    (float)b.optDouble("rotation",0),(float)b.optDouble("length",0)));
            }
            JSONArray sa=j.optJSONArray("sprites");
            if(sa!=null)for(int i=0;i<sa.length();i++){
                JSONObject s=sa.getJSONObject(i); Attachment a=new Attachment();
                a.bone=s.getString("bone");a.image=s.getString("image");
                a.px=(float)s.optDouble("pivotX",0);a.py=(float)s.optDouble("pivotY",0);a.scale=(float)s.optDouble("scale",1);
                byte[] png=data.get(a.image);
                if(png!=null)a.bmp=BitmapFactory.decodeByteArray(png,0,png.length);
                attachments.add(a);
            }
            JSONObject kf=j.optJSONObject("keyframes");
            if(kf!=null){
                Iterator<String> it=kf.keys();
                while(it.hasNext()){
                    String id=it.next();JSONArray arr=kf.getJSONArray(id);ArrayList<Key> list=new ArrayList<>();
                    for(int n=0;n<arr.length();n++){
                        JSONObject q=arr.getJSONObject(n);
                        list.add(new Key((float)q.optDouble("time",0),(float)q.optDouble("x",0),
                            (float)q.optDouble("y",0),(float)q.optDouble("rotation",0)));
                    }
                    Collections.sort(list,(a,b)->Float.compare(a.t,b.t));tracks.put(id,list);
                }
            }
            playing=true;time=0;lastNs=0;invalidate();
        }

        @Override protected void onDraw(Canvas c){
            super.onDraw(c);
            long now=System.nanoTime();
            if(lastNs==0)lastNs=now;
            float dt=(now-lastNs)/1_000_000_000f; lastNs=now;
            if(playing&&!scrubbing){
                time+=Math.min(dt,.05f);
                if(time>duration)time%=duration;
            }
            solve();
            float s=Math.min(getWidth()/projectW,getHeight()/projectH)*.92f;
            float ox=(getWidth()-projectW*s)/2f, oy=(getHeight()-projectH*s)/2f;
            c.save();c.translate(ox,oy);c.scale(s,s);
            if(demo)drawDemo(c); else drawSprites(c);
            if(showBones)drawBones(c);
            c.restore();
            if(playing)postInvalidateOnAnimation();
        }

        private float[] pose(Bone b){
            ArrayList<Key> l=tracks.get(b.id);
            if(l==null||l.size()==0)return new float[]{b.x,b.y,b.rot};
            if(l.size()==1){Key k=l.get(0);return new float[]{k.x,k.y,k.r};}
            Key a=l.get(0),z=l.get(l.size()-1);
            if(time<=a.t)return new float[]{a.x,a.y,a.r};
            if(time>=z.t)return new float[]{z.x,z.y,z.r};
            for(int i=0;i<l.size()-1;i++){
                Key k0=l.get(i),k1=l.get(i+1);
                if(time>=k0.t&&time<=k1.t){
                    float f=(time-k0.t)/Math.max(.0001f,k1.t-k0.t);
                    float rr=k0.r+shortAngle(k1.r-k0.r)*f;
                    return new float[]{lerp(k0.x,k1.x,f),lerp(k0.y,k1.y,f),rr};
                }
            }
            return new float[]{b.x,b.y,b.rot};
        }

        private float shortAngle(float d){while(d>180)d-=360;while(d<-180)d+=360;return d;}
        private float lerp(float a,float b,float t){return a+(b-a)*t;}

        private void solve(){
            for(Bone b:bones){
                float[] q=pose(b);float lx=q[0],ly=q[1],lr=q[2];
                Bone parent=b.parent==null?null:boneMap.get(b.parent);
                if(parent==null){b.wx=lx;b.wy=ly;b.wrot=lr;}
                else{
                    double r=Math.toRadians(parent.wrot);
                    b.wx=parent.wx+(float)(Math.cos(r)*lx-Math.sin(r)*ly);
                    b.wy=parent.wy+(float)(Math.sin(r)*lx+Math.cos(r)*ly);
                    b.wrot=parent.wrot+lr;
                }
            }
        }

        private void drawSprites(Canvas c){
            for(Attachment a:attachments){
                if(a.bmp==null)continue; Bone b=boneMap.get(a.bone);if(b==null)continue;
                c.save();c.translate(b.wx,b.wy);c.rotate(b.wrot);c.scale(a.scale,a.scale);
                c.drawBitmap(a.bmp,-a.px,-a.py,p);c.restore();
            }
        }

        private void limb(Canvas c,String id,int color,float width){
            Bone b=boneMap.get(id);if(b==null)return;
            double r=Math.toRadians(b.wrot);
            float ex=b.wx+(float)Math.cos(r)*b.len,ey=b.wy+(float)Math.sin(r)*b.len;
            p.setColor(color);p.setStrokeWidth(width);p.setStrokeCap(Paint.Cap.ROUND);p.setStyle(Paint.Style.STROKE);
            c.drawLine(b.wx,b.wy,ex,ey,p);
            p.setStyle(Paint.Style.FILL);c.drawCircle(ex,ey,width*.52f,p);
        }

        private void drawDemo(Canvas c){
            p.setStyle(Paint.Style.FILL);
            Bone root=boneMap.get("root"), torso=boneMap.get("torso"), head=boneMap.get("head");
            p.setColor(Color.rgb(118,101,203));c.drawOval(root.wx-75,root.wy-90,root.wx+75,root.wy+55,p);
            limb(c,"thighL",Color.rgb(228,201,190),46);limb(c,"calfL",Color.rgb(66,57,78),40);
            limb(c,"thighR",Color.rgb(228,201,190),46);limb(c,"calfR",Color.rgb(66,57,78),40);
            limb(c,"upperArmL",Color.rgb(139,125,181),48);limb(c,"foreArmL",Color.rgb(228,201,190),36);
            limb(c,"upperArmR",Color.rgb(139,125,181),48);limb(c,"foreArmR",Color.rgb(228,201,190),36);
            double tr=Math.toRadians(torso.wrot);
            float tx=torso.wx+(float)Math.cos(tr)*105,ty=torso.wy+(float)Math.sin(tr)*105;
            c.save();c.translate(tx,ty);c.rotate(torso.wrot+90);
            p.setColor(Color.rgb(236,230,242));c.drawRoundRect(-70,-120,70,120,35,35,p);c.restore();
            p.setColor(Color.rgb(244,216,205));c.drawCircle(head.wx,head.wy,72,p);
            p.setColor(Color.rgb(77,66,88));c.drawArc(head.wx-82,head.wy-82,head.wx+82,head.wy+82,190,160,true,p);
            p.setColor(Color.rgb(72,59,84));c.drawCircle(head.wx-25,head.wy+5,6,p);c.drawCircle(head.wx+25,head.wy+5,6,p);
        }

        private void drawBones(Canvas c){
            bonePaint.setStyle(Paint.Style.STROKE);bonePaint.setStrokeWidth(8);bonePaint.setColor(Color.argb(230,255,196,64));
            Paint joint=new Paint(Paint.ANTI_ALIAS_FLAG);joint.setStyle(Paint.Style.FILL);joint.setColor(Color.argb(240,255,225,120));
            for(Bone b:bones){
                if(b.len>0){
                    double r=Math.toRadians(b.wrot);
                    float ex=b.wx+(float)Math.cos(r)*b.len,ey=b.wy+(float)Math.sin(r)*b.len;
                    c.drawLine(b.wx,b.wy,ex,ey,bonePaint);c.drawCircle(ex,ey,10,joint);
                }
                c.drawCircle(b.wx,b.wy,12,joint);
            }
        }
    }
}
