package com.xiaoqi.companion;

import android.content.SharedPreferences;
import android.graphics.*;
import android.os.SystemClock;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;
import java.io.IOException;
import java.io.InputStream;
import java.util.Calendar;
import java.util.Locale;
import java.util.Random;

public class CompanionView extends View {
    private static final float VW=1080f, VH=1920f;
    private final MainActivity host;
    private final SharedPreferences prefs;
    private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
    private final Paint stroke=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Random rng=new Random();

    private Bitmap master,hairL,hairR,hairRibbon,eyeClosedL,eyeClosedR,blush;
    private Bitmap waveHandR,phoneHandR,shyHandR,phoneFront,sleeveR;

    private float viewScale=1f, offX=0f, offY=0f;
    private float lookX=0f,lookY=0f,targetLookX=0f,targetLookY=0f;
    private float downX,downY;
    private long downAt,lastTap;
    private long bubbleUntil,waveUntil,phoneUntil,shyUntil,petUntil,nextAuto;
    private boolean downOnHead;
    private String bubble="",mood="平静",recent="";
    private int affection,visits;

    private final RectF chatBtn=new RectF(70,1660,300,1785);
    private final RectF waveBtn=new RectF(310,1660,540,1785);
    private final RectF phoneBtn=new RectF(550,1660,780,1785);
    private final RectF shyBtn=new RectF(790,1660,1020,1785);
    private final RectF headZone=new RectF(390,455,690,760);
    private final RectF bodyZone=new RectF(250,720,830,1450);

    public CompanionView(MainActivity context,SharedPreferences prefs){
        super(context); host=context; this.prefs=prefs;
        setLayerType(View.LAYER_TYPE_SOFTWARE,null);
        stroke.setStyle(Paint.Style.STROKE); stroke.setStrokeCap(Paint.Cap.ROUND);
        affection=prefs.getInt("affection",2);
        visits=prefs.getInt("visits",0);
        recent=prefs.getString("recent","");
        loadAssets();
    }

    private Bitmap asset(String name){
        try(InputStream in=getContext().getAssets().open("parts/"+name)){
            return BitmapFactory.decodeStream(in);
        }catch(IOException e){ return null; }
    }
    private void loadAssets(){
        master=asset("character_master.webp");
        hairL=asset("hair_left.webp"); hairR=asset("hair_right.webp"); hairRibbon=asset("hair_ribbon.webp");
        eyeClosedL=asset("eye_closed_l.webp"); eyeClosedR=asset("eye_closed_r.webp"); blush=asset("blush.webp");
        waveHandR=asset("wave_hand_r.webp"); phoneHandR=asset("phone_hand_r.webp"); shyHandR=asset("hand_shy_r.webp");
        phoneFront=asset("phone_front.webp"); sleeveR=asset("sleeve_r.webp");
    }

    public void beginSession(){
        long now=System.currentTimeMillis(),last=prefs.getLong("last_visit",0L);
        visits++;
        int h=Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        if(last==0){ mood="有点期待"; showBubble("你好，我是小栖。以后我就在这里陪你。",6500); }
        else if(now-last>36L*60L*60L*1000L){ mood="见到你了"; showBubble("你回来啦。今天想先聊聊，还是让我陪你发会儿呆？",6500); }
        else if(h<6){ mood="困困的"; showBubble("这么晚还没睡呀……我陪你一会儿。",6000); }
        else if(h<11){ mood="早安"; showBubble("早呀。今天也见到你了。",5200); }
        else if(h<18){ mood="陪着你"; showBubble("你来了。今天过得怎么样？",5200); }
        else { mood="放松"; showBubble("晚上好。忙完了吗？",5200); }
        if(!recent.isEmpty() && now-last<72L*60L*60L*1000L && rng.nextBoolean()){
            String r=recent.length()>15?recent.substring(0,15)+"…":recent;
            showBubble("上次你说“"+r+"”，后来怎么样了？",7000);
        }
        nextAuto=SystemClock.uptimeMillis()+10000;
        persist();
    }

    public void persist(){
        prefs.edit().putInt("affection",affection).putInt("visits",visits)
                .putString("recent",recent).putLong("last_visit",System.currentTimeMillis()).apply();
    }

    public void onUserMessage(String msg){
        recent=msg.length()>48?msg.substring(0,48):msg;
        String m=msg.toLowerCase(Locale.ROOT),reply;
        if(has(m,"累","烦","压力","难受","不开心","焦虑")){
            mood="认真陪你"; reply="那就先别急着把所有事情解决。你慢慢说，我听着。";
        }else if(has(m,"开心","成功","通过","好消息","太好了")){
            mood="替你开心"; reply="真的？那我要认真替你高兴一下。再讲点细节给我听。"; waveUntil=SystemClock.uptimeMillis()+2300;
        }else if(has(m,"困","睡觉","晚安")){
            mood="温柔"; reply="那早点休息。手机放下也没关系，我明天还在。";
        }else if(has(m,"想你","喜欢你","想见你")){
            mood="害羞"; reply="……我也会期待你打开这里。"; shyUntil=SystemClock.uptimeMillis()+3200;
        }else{
            String[] a={"嗯，我在听。你继续说。","我记住了。以后你再提到，我会接得上。","这件事对你应该挺重要的。你现在是什么感觉？","我可能还没完全懂，但我想继续听。"};
            reply=a[rng.nextInt(a.length)]; mood="认真听";
        }
        affection=Math.min(80,affection+1); showBubble(reply,7500); persist();
    }
    private boolean has(String s,String...ks){ for(String k:ks) if(s.contains(k))return true; return false; }
    private void showBubble(String s,long ms){ bubble=s; bubbleUntil=SystemClock.uptimeMillis()+ms; invalidate(); }

    @Override protected void onSizeChanged(int w,int h,int ow,int oh){
        viewScale=Math.min(w/VW,h/VH); offX=(w-VW*viewScale)/2f; offY=(h-VH*viewScale)/2f;
    }

    @Override protected void onDraw(Canvas raw){
        super.onDraw(raw);
        long now=SystemClock.uptimeMillis(); float t=now/1000f;
        lookX+=(targetLookX-lookX)*0.08f; lookY+=(targetLookY-lookY)*0.08f;
        if(now>nextAuto){
            int a=rng.nextInt(4);
            if(a==0){ waveUntil=now+1900; mood="注意到你"; }
            else if(a==1){ phoneUntil=now+3000; mood="看看手机"; }
            else if(a==2){ targetLookX=rng.nextBoolean()?-.45f:.45f; targetLookY=-.12f; mood="发呆"; }
            else mood="陪着你";
            nextAuto=now+11000+rng.nextInt(8000);
        }
        raw.save(); raw.translate(offX,offY); raw.scale(viewScale,viewScale);
        drawRoom(raw,t); drawHeader(raw); drawCharacter(raw,t,now);
        if(bubbleUntil>now) drawBubble(raw);
        drawActions(raw);
        raw.restore(); postInvalidateOnAnimation();
    }

    private void drawRoom(Canvas c,float t){
        int h=Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        boolean night=h<6||h>=20;
        int top=night?Color.rgb(39,39,58):Color.rgb(246,241,236);
        int bot=night?Color.rgb(76,62,84):Color.rgb(226,211,207);
        p.setShader(new LinearGradient(0,0,0,VH,top,bot,Shader.TileMode.CLAMP)); c.drawRect(0,0,VW,VH,p); p.setShader(null);
        fill(night?0xFF35384F:0xFFE6DBD5); rr(c,650,190,995,610,34);
        fill(night?0xFF27334E:0xFFA9CFDC); rr(c,675,215,970,585,23);
        fill(0x66FFFFFF); c.drawRect(818,215,828,585,p); c.drawRect(675,390,970,400,p);
        if(night){ fill(0xFFFFE4A8); c.drawCircle(890,285,31,p); }
        fill(night?0xFF66556B:0xFFC5AAB6);
        Path l=new Path(); l.moveTo(620,160);l.lineTo(690,200);l.lineTo(660,650);l.lineTo(595,675);l.close();c.drawPath(l,p);
        Path r=new Path(); r.moveTo(1010,160);r.lineTo(950,195);r.lineTo(968,650);r.lineTo(1030,675);r.close();c.drawPath(r,p);
        fill(night?0xFF504650:0xFFDACBC3); c.drawRect(0,1270,VW,VH,p);
        fill(night?0xFF715C77:0xFFD0ADB9); c.drawOval(new RectF(115,1320,965,1690),p);
        fill(night?0xFF60484D:0xFF8D6858); rr(c,78,335,415,360,10);
        fill(0xFF79916D); c.drawOval(new RectF(115,265,205,355),p); c.drawOval(new RectF(175,245,270,350),p);
        fill(0xFF8B695B); rr(c,135,340,245,445,18);
        if(night){
            p.setShader(new RadialGradient(865,970,300,0x44FFD997,0x00FFD997,Shader.TileMode.CLAMP));c.drawCircle(865,970,300,p);p.setShader(null);
        }
        fill(night?0xFF725B58:0xFF9A7460); rr(c,820,970,925,1180,18);
        fill(night?0xFFFFDFA5:0xFFE6BE98);
        Path shade=new Path(); shade.moveTo(770,950);shade.lineTo(970,950);shade.lineTo(925,1065);shade.lineTo(815,1065);shade.close();c.drawPath(shade,p);
        fill(night?0x55FFF1D4:0x33FFFFFF);
        for(int i=0;i<13;i++){float x=70+(i*167)%920,y=650+(i*91)%520+(float)Math.sin(t*.45+i)*9;c.drawCircle(x,y,2.5f,p);}
    }

    private void drawHeader(Canvas c){
        fill(0xDDFEF9F7); rr(c,55,50,1025,178,34);
        text(c,"小栖",92,108,40,0xFF443B50,true,Paint.Align.LEFT);
        text(c,"· "+mood,190,106,26,0xFF807085,false,Paint.Align.LEFT);
        String rel=affection<8?"刚刚认识":affection<20?"渐渐熟悉":affection<40?"熟悉的朋友":"很亲近";
        text(c,rel+"  ·  第 "+visits+" 次见面",92,151,23,0xFF8B798E,false,Paint.Align.LEFT);
        fill(0xFF8E7BEF); c.drawCircle(950,112,27,p);
        fill(Color.WHITE); c.drawCircle(942,106,4,p);c.drawCircle(958,106,4,p);
        stroke.setColor(Color.WHITE);stroke.setStrokeWidth(3);c.drawArc(new RectF(940,107,960,128),20,140,false,stroke);
    }

    private void drawCharacter(Canvas c,float t,long now){
        if(master==null){ text(c,"素材加载失败",540,900,34,Color.RED,true,Paint.Align.CENTER);return; }
        float sway=(float)Math.sin(t*1.18f)*3.2f;
        float rot=(float)Math.sin(t*.72f)*.75f + lookX*.55f;
        float breath=1f+(float)Math.sin(t*1.85f)*.0048f;
        float lean=now<waveUntil?-1.2f:now<shyUntil?1.0f:0f;

        final float L=130,T=365,W=820,H=1025;
        c.save();
        c.rotate(rot+lean,540,930);
        c.translate(sway+lookX*3f,lookY*2f);
        c.scale(1f,breath,540,930);
        p.setAlpha(255); c.drawBitmap(master,null,new RectF(L,T,L+W,T+H),p);

        // Extra separated hair strands: subtle secondary motion, not enough to change her silhouette.
        float hairSwing=(float)Math.sin(t*1.1f+.7f)*2.8f-rot*.55f;
        if(hairL!=null){
            c.save();c.rotate(hairSwing,350,545);p.setAlpha(205);
            c.drawBitmap(hairL,null,new RectF(235,535,375,770),p);c.restore();
        }
        if(hairR!=null){
            c.save();c.rotate(-hairSwing*.8f,720,540);p.setAlpha(195);
            c.drawBitmap(hairR,null,new RectF(700,530,828,765),p);c.restore();
        }
        if(hairRibbon!=null){
            c.save();c.rotate(-hairSwing*.65f,690,520);p.setAlpha(215);
            c.drawBitmap(hairRibbon,null,new RectF(675,505,805,695),p);c.restore();
        }
        p.setAlpha(255);

        // Blink: briefly cover the painted eyes, then draw separated closed-eye lashes.
        float bp=t%4.6f;
        if(bp>4.43f){
            fill(0xFFF2D4C9);
            c.drawOval(new RectF(474,526,532,556),p);c.drawOval(new RectF(546,526,604,556),p);
            if(eyeClosedL!=null)c.drawBitmap(eyeClosedL,null,new RectF(478,533,528,551),p);
            if(eyeClosedR!=null)c.drawBitmap(eyeClosedR,null,new RectF(550,533,600,551),p);
        }

        if((now<shyUntil||now<petUntil)&&blush!=null){
            p.setAlpha(155); c.drawBitmap(blush,null,new RectF(462,550,618,618),p); p.setAlpha(255);
        }

        // Wave: use separated sleeve + hand and pivot them around the shoulder.
        if(now<waveUntil && sleeveR!=null && waveHandR!=null){
            float u=1f-(waveUntil-now)/2300f;
            float wave=(float)Math.sin(u*Math.PI*5.5f)*10f;
            c.save(); c.rotate(-42+wave,690,710);
            c.drawBitmap(sleeveR,null,new RectF(650,690,790,1040),p);
            c.save(); c.rotate(-8+wave*.5f,760,700);
            c.drawBitmap(waveHandR,null,new RectF(716,602,804,750),p); c.restore();
            c.restore();
        }

        if(now<phoneUntil && phoneHandR!=null){
            c.save();c.rotate(-7,650,820);
            c.drawBitmap(phoneHandR,null,new RectF(595,725,695,905),p);
            if(phoneFront!=null){p.setAlpha(245);c.drawBitmap(phoneFront,null,new RectF(615,704,682,827),p);p.setAlpha(255);}
            c.restore();
        }

        if(now<shyUntil && shyHandR!=null){
            c.save();c.rotate(-18,650,720);c.drawBitmap(shyHandR,null,new RectF(575,615,700,785),p);c.restore();
        }
        c.restore();

        if(now<petUntil){
            float k=1f-(petUntil-now)/1700f;drawHeart(c,700,505-k*75,18,0xFFE4839C);drawHeart(c,372,555-k*90,13,0xFFEDA5B5);
        }
    }

    private void drawBubble(Canvas c){
        fill(0xF2FFFCF9);rr(c,85,220,995,400,34);
        Path tail=new Path();tail.moveTo(500,400);tail.lineTo(548,446);tail.lineTo(590,400);tail.close();c.drawPath(tail,p);
        stroke.setColor(0x30463854);stroke.setStrokeWidth(2);c.drawRoundRect(new RectF(85,220,995,400),34,34,stroke);
        wrap(c,bubble,125,278,830,31,45,0xFF463B50);
    }

    private void drawActions(Canvas c){
        fill(0xEAFEF9F7);rr(c,45,1608,1035,1835,42);
        pill(c,chatBtn,"聊聊天","●",0xFF8E7BEF);
        pill(c,waveBtn,"挥挥手","⌁",0xFFB58FA6);
        pill(c,phoneBtn,"拿手机","▣",0xFF6E969F);
        pill(c,shyBtn,"害羞","♡",0xFFD58EA2);
        text(c,"可以直接摸头、点她，视线和发丝会跟着你的手动。",540,1817,19,0xFF958397,false,Paint.Align.CENTER);
    }
    private void pill(Canvas c,RectF r,String label,String icon,int accent){
        fill(0xF4FFFFFF);c.drawRoundRect(r,31,31,p);stroke.setColor(0x26463A50);stroke.setStrokeWidth(2);c.drawRoundRect(r,31,31,stroke);
        fill(accent);c.drawCircle(r.left+38,r.centerY(),22,p);
        text(c,icon,r.left+38,r.centerY()+7,20,Color.WHITE,true,Paint.Align.CENTER);
        text(c,label,r.left+70,r.centerY()+9,24,0xFF463B50,true,Paint.Align.LEFT);
    }

    private void drawHeart(Canvas c,float x,float y,float s,int color){
        fill(color);Path h=new Path();h.moveTo(x,y+s);h.cubicTo(x-s*1.4f,y,x-s,y-s,x,y-s*.25f);h.cubicTo(x+s,y-s,x+s*1.4f,y,x,y+s);c.drawPath(h,p);
    }
    private void wrap(Canvas c,String s,float x,float y,float max,float size,float line,int color){
        p.setTextSize(size);p.setTypeface(Typeface.create("sans",Typeface.NORMAL));p.setTextAlign(Paint.Align.LEFT);p.setColor(color);
        StringBuilder b=new StringBuilder();float yy=y;
        for(int i=0;i<s.length();i++){char ch=s.charAt(i);String test=b.toString()+ch;if(p.measureText(test)>max&&b.length()>0){c.drawText(b.toString(),x,yy,p);yy+=line;b.setLength(0);}b.append(ch);}
        if(b.length()>0)c.drawText(b.toString(),x,yy,p);
    }
    private void text(Canvas c,String s,float x,float y,float size,int color,boolean bold,Paint.Align align){
        p.setShader(null);p.setStyle(Paint.Style.FILL);p.setColor(color);p.setTextSize(size);p.setTextAlign(align);p.setTypeface(Typeface.create("sans",bold?Typeface.BOLD:Typeface.NORMAL));c.drawText(s,x,y,p);
    }
    private void fill(int color){p.setShader(null);p.setStyle(Paint.Style.FILL);p.setColor(color);p.setAlpha(Color.alpha(color));}
    private void rr(Canvas c,float l,float t,float r,float b,float rad){c.drawRoundRect(new RectF(l,t,r,b),rad,rad,p);}
    private float clamp(float v,float a,float b){return Math.max(a,Math.min(b,v));}
    private float vx(float x){return(x-offX)/viewScale;}private float vy(float y){return(y-offY)/viewScale;}

    @Override public boolean onTouchEvent(MotionEvent e){
        float x=vx(e.getX()),y=vy(e.getY());long now=SystemClock.uptimeMillis();
        switch(e.getActionMasked()){
            case MotionEvent.ACTION_DOWN:
                downX=x;downY=y;downAt=now;downOnHead=headZone.contains(x,y);
                targetLookX=clamp((x-540)/320f,-1,1);targetLookY=clamp((y-650)/380f,-.7f,.7f);return true;
            case MotionEvent.ACTION_MOVE:
                targetLookX=clamp((x-540)/320f,-1,1);targetLookY=clamp((y-650)/380f,-.7f,.7f);return true;
            case MotionEvent.ACTION_UP:
                float dx=x-downX,dy=y-downY;float dist=(float)Math.hypot(dx,dy);long held=now-downAt;
                if(dist<45){
                    if(chatBtn.contains(x,y))host.openChat();
                    else if(waveBtn.contains(x,y)){waveUntil=now+2300;mood="跟你挥手";showBubble("看到你啦。",3200);}
                    else if(phoneBtn.contains(x,y)){phoneUntil=now+3200;mood="拿起手机";showBubble("嗯？要一起看看吗？",3600);}
                    else if(shyBtn.contains(x,y)){shyUntil=now+3200;mood="有点害羞";showBubble("……别一直盯着我看呀。",3800);}
                    else if(downOnHead&&held>430){petUntil=now+1700;shyUntil=now+2200;mood="被摸头";showBubble("嗯……这个可以。",3500);affection=Math.min(80,affection+2);performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);}
                    else if(headZone.contains(x,y)){if(now-lastTap<320){shyUntil=now+2500;mood="被你戳到了";showBubble("你是故意连续戳我的吧？",3800);}else{mood="看着你";showBubble("怎么啦？我在。",3000);}lastTap=now;}
                    else if(bodyZone.contains(x,y)){waveUntil=now+1800;mood="回应你";showBubble("收到。",2400);}
                }
                targetLookX=0;targetLookY=0;persist();return true;
            case MotionEvent.ACTION_CANCEL:targetLookX=0;targetLookY=0;return true;
        }return true;
    }
}
