package com.openai.x2dboneplayer;

import android.app.*;
import android.os.*;
import android.content.*;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;

public class MainActivity extends Activity {
    private static final int REQ_ZIP=1001;
    RigPlayerView player;
    TextView status,timeText;
    SeekBar seek;
    Button playBtn,bonesBtn,clipBtn;
    final Handler ui=new Handler(Looper.getMainLooper());

    @Override public void onCreate(Bundle b){
        super.onCreate(b);
        buildUi();
        try{
            InputStream in=getAssets().open("GodotOfficialSkeleton2D.x2d.zip");
            player.loadZip(in);
            status.setText("已载入内置官方案例 · "+player.describe());
        }catch(Exception e){
            status.setText("请选择「导入Rig ZIP」；当前未加载角色");
        }
        ui.post(uiTick);
    }

    private void buildUi(){
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xff15131d);
        root.setOnApplyWindowInsetsListener((v,i)->{
            v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),
                    i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());
            return i;
        });

        status=new TextView(this);
        status.setTextColor(0xffeeeeee);
        status.setTextSize(13);
        status.setPadding(dp(12),dp(8),dp(12),dp(6));
        root.addView(status,new LinearLayout.LayoutParams(-1,-2));

        player=new RigPlayerView(this);
        root.addView(player,new LinearLayout.LayoutParams(-1,0,1));

        LinearLayout row=new LinearLayout(this);
        row.setGravity(Gravity.CENTER);
        row.setPadding(dp(5),dp(4),dp(5),dp(2));
        Button importBtn=button("导入Rig ZIP");
        playBtn=button("暂停");
        bonesBtn=button("显示骨骼");
        clipBtn=button("动作");
        row.addView(importBtn,weight());
        row.addView(playBtn,weight());
        row.addView(bonesBtn,weight());
        row.addView(clipBtn,weight());
        root.addView(row,new LinearLayout.LayoutParams(-1,-2));

        LinearLayout timeline=new LinearLayout(this);
        timeline.setGravity(Gravity.CENTER_VERTICAL);
        timeline.setPadding(dp(10),0,dp(10),dp(8));
        timeText=new TextView(this);
        timeText.setTextColor(0xffcccccc);
        timeText.setTextSize(12);
        seek=new SeekBar(this); seek.setMax(1000);
        timeline.addView(timeText,new LinearLayout.LayoutParams(dp(118),-2));
        timeline.addView(seek,new LinearLayout.LayoutParams(0,-2,1));
        root.addView(timeline,new LinearLayout.LayoutParams(-1,-2));

        importBtn.setOnClickListener(v->pickZip());
        playBtn.setOnClickListener(v->{
            player.playing=!player.playing;
            playBtn.setText(player.playing?"暂停":"播放");
            player.invalidate();
        });
        bonesBtn.setOnClickListener(v->{
            player.showBones=!player.showBones;
            bonesBtn.setText(player.showBones?"隐藏骨骼":"显示骨骼");
            player.invalidate();
        });
        clipBtn.setOnClickListener(v->{
            player.nextClip();
            clipBtn.setText(player.currentClipName());
            status.setText(player.describe());
        });
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar s,int p,boolean fromUser){
                if(fromUser){
                    player.time=player.duration*Math.max(0,Math.min(1000,p))/1000f;
                    player.invalidate();
                }
            }
            public void onStartTrackingTouch(SeekBar s){player.scrubbing=true;}
            public void onStopTrackingTouch(SeekBar s){player.scrubbing=false;}
        });
        setContentView(root);
    }

    private Button button(String s){
        Button b=new Button(this);b.setText(s);b.setTextSize(12);b.setAllCaps(false);return b;
    }
    private LinearLayout.LayoutParams weight(){return new LinearLayout.LayoutParams(0,dp(48),1);}
    private int dp(int v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}

    private void pickZip(){
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/zip");
        i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/zip","application/octet-stream","application/x-zip-compressed"});
        startActivityForResult(i,REQ_ZIP);
    }

    @Override protected void onActivityResult(int req,int result,Intent data){
        super.onActivityResult(req,result,data);
        if(req!=REQ_ZIP||result!=RESULT_OK||data==null)return;
        Uri uri=data.getData();
        try(InputStream in=getContentResolver().openInputStream(uri)){
            player.loadZip(in);
            status.setText("已导入 "+displayName(uri)+" · "+player.describe());
            clipBtn.setText(player.currentClipName());
            playBtn.setText("暂停");
        }catch(Exception e){
            new AlertDialog.Builder(this).setTitle("导入失败").setMessage(e.toString()).setPositiveButton("确定",null).show();
        }
    }

    private String displayName(Uri uri){
        String n="rig.zip";
        try(android.database.Cursor c=getContentResolver().query(uri,null,null,null,null)){
            if(c!=null&&c.moveToFirst()){
                int idx=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if(idx>=0)n=c.getString(idx);
            }
        }catch(Exception ignored){}
        return n;
    }

    final Runnable uiTick=new Runnable(){
        @Override public void run(){
            float d=Math.max(.001f,player.duration);
            if(!player.scrubbing)seek.setProgress((int)(1000f*player.time/d));
            timeText.setText(String.format(Locale.US,"%.2f / %.2f s",player.time,d));
            String clip=player.currentClipName();
            clipBtn.setText(clip.length()==0?"动作":clip);
            ui.postDelayed(this,50);
        }
    };

    @Override protected void onDestroy(){ui.removeCallbacksAndMessages(null);super.onDestroy();}
}
