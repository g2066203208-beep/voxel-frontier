package com.xiaoqi.companion;

import android.content.SharedPreferences;
import android.graphics.*;
import android.os.SystemClock;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;

import java.util.Calendar;
import java.util.Locale;
import java.util.Random;

public class CompanionView extends View {
    private static final float VW=1080f, VH=1920f;
    private final MainActivity host;
    private final SharedPreferences prefs;
    private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint stroke=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Random rng=new Random();

    enum Pose { IDLE, WAVE, LEAN, SQUAT, TURN, STRETCH, PHONE, SHY, SIT }

    static class Rig {
        float rootY, torsoDeg, headDeg, turn;
        float lShoulder,lElbow,lWrist,rShoulder,rElbow,rWrist;
        float lHip,lKnee,rHip,rKnee;
        float headY, armLift, skirtCompress;
        float phone, shy, sit;

        Rig copy(){
            Rig q=new Rig();
            q.rootY=rootY;q.torsoDeg=torsoDeg;q.headDeg=headDeg;q.turn=turn;
            q.lShoulder=lShoulder;q.lElbow=lElbow;q.lWrist=lWrist;
            q.rShoulder=rShoulder;q.rElbow=rElbow;q.rWrist=rWrist;
            q.lHip=lHip;q.lKnee=lKnee;q.rHip=rHip;q.rKnee=rKnee;
            q.headY=headY;q.armLift=armLift;q.skirtCompress=skirtCompress;
            q.phone=phone;q.shy=shy;q.sit=sit;
            return q;
        }
    }

    static class V { float x,y; V(float x,float y){this.x=x;this.y=y;} }

    private Pose pose=Pose.IDLE, fromPose=Pose.IDLE;
    private Rig current=new Rig(), startRig=new Rig(), targetRig=new Rig();
    private long poseStart=0;
    private float poseDuration=0.55f;
    private float sc=1f, ox=0, oy=0;
    private float lookX=0,lookY=0,targetLookX=0,targetLookY=0;
    private float hairLag=0, sleeveLag=0, skirtLag=0;
    private float downX,downY; private long downAt=0;
    private boolean downOnHead=false;
    private String bubble=""; private long bubbleUntil=0;
    private String mood="平静"; private String recent="";
    private int affection=2, visits=0;
    private long lastTap=0;
    private int pressed=-1;

    private final String[] labels={"待机","挥手","俯身","蹲下","转身","伸懒腰","拿手机","害羞","坐下"};
    private final Pose[] poses={Pose.IDLE,Pose.WAVE,Pose.LEAN,Pose.SQUAT,Pose.TURN,Pose.STRETCH,Pose.PHONE,Pose.SHY,Pose.SIT};

    public CompanionView(MainActivity host, SharedPreferences prefs){
        super(host);
        this.host=host; this.prefs=prefs;
        setLayerType(View.LAYER_TYPE_SOFTWARE,null);
        stroke.setStyle(Paint.Style.STROKE); stroke.setStrokeCap(Paint.Cap.ROUND); stroke.setStrokeJoin(Paint.Join.ROUND);
        affection=prefs.getInt("affection",2);
        visits=prefs.getInt("visits",0);
        recent=prefs.getString("recent","");
        current=rigFor(Pose.IDLE);
        targetRig=current.copy();
    }

    public void beginSession(){
        visits++;
        int h=Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        if(h<6) showBubble("这么晚还没睡呀？我陪你一会儿。",5200);
        else if(h<11) showBubble("早呀。今天也见到你了。",4200);
        else if(h<18) showBubble("你来了。今天过得怎么样？",4200);
        else showBubble("晚上好。忙完了吗？",4200);
        persist();
    }

    public void persist(){
        prefs.edit().putInt("affection",affection).putInt("visits",visits).putString("recent",recent)
                .putLong("last_visit",System.currentTimeMillis()).apply();
    }

    public void onUserMessage(String msg){
        recent=msg.length()>48?msg.substring(0,48):msg;
        String m=msg.toLowerCase(Locale.ROOT);
        if(containsAny(m,"累","烦","难受","压力","不开心","焦虑")){
            mood="担心你"; showBubble("那今天先别急着把自己整理好。你想说多少就说多少，我在听。",7000);
            affection+=2; setPose(Pose.LEAN);
        }else if(containsAny(m,"开心","成功","通过","好消息","太好了")){
            mood="开心"; showBubble("真的？那我要替你高兴一会儿。再讲给我听。",6000);
            affection+=2; setPose(Pose.WAVE);
        }else if(containsAny(m,"困","晚安","睡觉")){
            mood="温柔"; showBubble("那就早点休息。我明天还在这里。晚安。",6000);
            setPose(Pose.SIT);
        }else if(containsAny(m,"想你","喜欢你","想见你")){
            mood="害羞"; showBubble("……我也会期待你打开这里。只是我没好意思先说。",6500);
            affection+=3; setPose(Pose.SHY);
        }else{
            String[] r={"嗯，我在听。你继续说。","我记住了。以后你再提到它，我会接得上。","你说这件事的时候，语气好像变了一点。","我可能还不完全懂，但我想继续听。"};
            mood="认真听"; showBubble(r[rng.nextInt(r.length)],5500); affection+=1;
        }
        affection=Math.min(80,affection); persist();
    }

    private boolean containsAny(String s,String... ks){for(String k:ks)if(s.contains(k))return true;return false;}

    private Rig rigFor(Pose z){
        Rig r=new Rig();
        switch(z){
            case WAVE:
                r.rShoulder=-50; r.rElbow=-78; r.rWrist=18; r.torsoDeg=-2; r.headDeg=3; break;
            case LEAN:
                r.torsoDeg=18; r.rootY=28; r.headDeg=-7; r.headY=18; r.lShoulder=7; r.rShoulder=-7; break;
            case SQUAT:
                r.rootY=190; r.lHip=46; r.rHip=-46; r.lKnee=78; r.rKnee=-78; r.skirtCompress=1; r.torsoDeg=6; r.headDeg=-4; break;
            case TURN:
                r.turn=1; r.torsoDeg=-4; r.headDeg=12; r.lShoulder=12; r.rShoulder=-18; break;
            case STRETCH:
                r.rootY=-25; r.torsoDeg=-7; r.lShoulder=65; r.rShoulder=-65; r.lElbow=-14; r.rElbow=14; r.headDeg=-5; r.headY=-8; break;
            case PHONE:
                r.rShoulder=18; r.rElbow=-88; r.rWrist=-14; r.lShoulder=-8; r.lElbow=38; r.phone=1; r.headDeg=8; r.turn=.25f; break;
            case SHY:
                r.lShoulder=-22; r.lElbow=84; r.lWrist=-18; r.rShoulder=15; r.rElbow=-72; r.rWrist=10; r.shy=1; r.headDeg=-8; break;
            case SIT:
                r.rootY=130; r.sit=1; r.lHip=72; r.rHip=-72; r.lKnee=92; r.rKnee=-92; r.skirtCompress=.55f; r.torsoDeg=3; break;
            default: break;
        }
        return r;
    }

    private void setPose(Pose z){
        if(z==pose && z!=Pose.WAVE)return;
        fromPose=pose; pose=z;
        startRig=current.copy(); targetRig=rigFor(z);
        poseStart=SystemClock.uptimeMillis();
        poseDuration=(z==Pose.SQUAT||z==Pose.SIT)?0.75f:(z==Pose.LEAN||z==Pose.TURN?0.65f:0.5f);
        performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
    }

    private float ease(float t){
        t=Math.max(0,Math.min(1,t));
        return t*t*(3-2*t);
    }

    private float mix(float a,float b,float t){return a+(b-a)*t;}

    private void updateRig(long now,float t){
        float u=ease((now-poseStart)/1000f/Math.max(.01f,poseDuration));
        current.rootY=mix(startRig.rootY,targetRig.rootY,u);
        current.torsoDeg=mix(startRig.torsoDeg,targetRig.torsoDeg,u);
        current.headDeg=mix(startRig.headDeg,targetRig.headDeg,u);
        current.turn=mix(startRig.turn,targetRig.turn,u);
        current.lShoulder=mix(startRig.lShoulder,targetRig.lShoulder,u);
        current.lElbow=mix(startRig.lElbow,targetRig.lElbow,u);
        current.lWrist=mix(startRig.lWrist,targetRig.lWrist,u);
        current.rShoulder=mix(startRig.rShoulder,targetRig.rShoulder,u);
        current.rElbow=mix(startRig.rElbow,targetRig.rElbow,u);
        current.rWrist=mix(startRig.rWrist,targetRig.rWrist,u);
        current.lHip=mix(startRig.lHip,targetRig.lHip,u); current.lKnee=mix(startRig.lKnee,targetRig.lKnee,u);
        current.rHip=mix(startRig.rHip,targetRig.rHip,u); current.rKnee=mix(startRig.rKnee,targetRig.rKnee,u);
        current.headY=mix(startRig.headY,targetRig.headY,u);
        current.skirtCompress=mix(startRig.skirtCompress,targetRig.skirtCompress,u);
        current.phone=mix(startRig.phone,targetRig.phone,u);
        current.shy=mix(startRig.shy,targetRig.shy,u);
        current.sit=mix(startRig.sit,targetRig.sit,u);

        float idle=(pose==Pose.IDLE)?1f:.30f;
        current.torsoDeg += (float)Math.sin(t*1.365f)*2.4f*idle;
        current.headY += (float)Math.sin(t*1.848f)*7f*idle;
        float targetHair=-(current.torsoDeg+current.headDeg)*.24f-lookX*5f;
        hairLag += (targetHair-hairLag)*.065f;
        sleeveLag += ((float)Math.sin(t*2.0f)*2.2f-sleeveLag)*.05f;
        skirtLag += ((float)Math.sin(t*1.45f)*1.5f-skirtLag)*.04f;
    }

    @Override protected void onSizeChanged(int w,int h,int ow,int oh){
        sc=Math.min(w/VW,h/VH); ox=(w-VW*sc)*.5f; oy=(h-VH*sc)*.5f;
    }

    @Override protected void onDraw(Canvas c){
        long now=SystemClock.uptimeMillis(); float t=now/1000f;
        lookX+=(targetLookX-lookX)*.11f; lookY+=(targetLookY-lookY)*.11f;
        updateRig(now,t);

        c.save(); c.translate(ox,oy); c.scale(sc,sc);
        drawRoom(c,t);
        drawHeader(c);
        drawPuppet(c,t,now);
        if(bubbleUntil>now)drawBubble(c);
        drawTester(c);
        c.restore();
        postInvalidateOnAnimation();
    }

    private void drawRoom(Canvas c,float t){
        int hour=Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        boolean night=hour<6||hour>=20;
        int a=night?Color.rgb(44,43,66):Color.rgb(247,242,237);
        int b=night?Color.rgb(89,72,95):Color.rgb(229,216,210);
        p.setShader(new LinearGradient(0,0,0,VH,a,b,Shader.TileMode.CLAMP)); c.drawRect(0,0,VW,VH,p); p.setShader(null);

        fill(Color.argb(220,68,61,78)); rr(c,690,160,995,610,30);
        fill(night?Color.rgb(38,49,82):Color.rgb(170,210,225)); rr(c,712,182,973,588,22);
        fill(Color.argb(105,255,255,255)); c.drawRect(838,182,847,588,p); c.drawRect(712,385,973,394,p);
        if(night){fill(Color.rgb(255,237,178));c.drawCircle(905,250,34,p);} else {fill(Color.argb(120,255,255,255));c.drawOval(new RectF(745,245,842,282),p);}

        fill(night?Color.rgb(94,76,108):Color.rgb(193,166,184));
        Path q=new Path();q.moveTo(650,125);q.lineTo(715,150);q.lineTo(690,650);q.lineTo(620,665);q.close();c.drawPath(q,p);
        q=new Path();q.moveTo(1010,125);q.lineTo(970,150);q.lineTo(990,650);q.lineTo(1050,665);q.close();c.drawPath(q,p);

        fill(night?Color.rgb(82,67,72):Color.rgb(132,98,82)); rr(c,75,350,420,378,10);
        fill(Color.rgb(205,143,127));rr(c,110,285,155,350,5);
        fill(Color.rgb(121,151,162));rr(c,165,267,215,350,5);
        fill(Color.rgb(182,166,106));rr(c,225,298,278,350,5);

        fill(Color.rgb(126,91,75));rr(c,140,470,255,585,22);
        fill(Color.rgb(84,135,99));c.drawOval(new RectF(105,395,205,505),p);c.drawOval(new RectF(190,375,300,500),p);

        fill(night?Color.rgb(75,65,76):Color.rgb(220,204,194)); c.drawRect(0,1250,VW,VH,p);
        fill(night?Color.rgb(109,88,116):Color.rgb(205,176,187)); c.drawOval(new RectF(115,1325,965,1745),p);
        fill(Color.argb(28,60,45,70));c.drawOval(new RectF(250,1400,830,1575),p);
    }

    private void drawHeader(Canvas c){
        fill(Color.argb(215,255,252,249));rr(c,52,44,1028,180,34);
        stroke(Color.argb(38,65,53,78),2);c.drawRoundRect(new RectF(52,44,1028,180),34,34,stroke);
        text(c,"小栖 · 布偶动作原型",88,100,38,Color.rgb(64,54,77),true,Paint.Align.LEFT);
        text(c,"当前："+labels[pose.ordinal()]+"   /   "+closeness(),88,148,24,Color.rgb(132,113,137),false,Paint.Align.LEFT);
        fill(Color.rgb(143,126,225));c.drawCircle(952,110,28,p);fill(Color.WHITE);c.drawCircle(944,104,4,p);c.drawCircle(960,104,4,p);
        stroke(Color.WHITE,3);c.drawArc(new RectF(942,103,962,126),25,130,false,stroke);
    }

    private String closeness(){
        if(affection<7)return "初次见面";
        if(affection<18)return "渐渐熟悉";
        if(affection<38)return "熟悉的朋友";
        return "很亲近";
    }

    private V polar(V o,float len,float deg){
        double r=Math.toRadians(deg); return new V(o.x+(float)Math.sin(r)*len,o.y+(float)Math.cos(r)*len);
    }

    private void drawPuppet(Canvas c,float t,long now){
        float cx=540, rootY=985+current.rootY;
        float torsoRad=current.torsoDeg;
        float turn=current.turn;
        float bodyW=300-48*Math.abs(turn);
        float bodyScaleX=1f-.18f*Math.abs(turn);

        V hip=new V(cx,rootY+280);
        V chest=new V(cx+(float)Math.sin(Math.toRadians(torsoRad))*65,rootY);
        V neck=new V(chest.x+(float)Math.sin(Math.toRadians(torsoRad))*60,chest.y-145);
        V head=new V(neck.x+(float)Math.sin(Math.toRadians(current.headDeg))*22,neck.y-165+current.headY);

        // shadow
        fill(Color.argb(45,50,38,61)); c.drawOval(new RectF(cx-250,hip.y+300,cx+250,hip.y+390),p);

        // back hair chunks
        drawHairBack(c,head,current.headDeg+current.torsoDeg,hairLag);

        // rear skirt panel
        c.save(); c.rotate(current.torsoDeg*.45f+skirtLag,hip.x,hip.y);
        fill(Color.rgb(150,138,179)); Path back=new Path();
        back.moveTo(hip.x-bodyW*.52f,hip.y-110);back.lineTo(hip.x+bodyW*.52f,hip.y-110);
        back.lineTo(hip.x+230,hip.y+245-70*current.skirtCompress);back.lineTo(hip.x-230,hip.y+245-70*current.skirtCompress);back.close();c.drawPath(back,p);
        c.restore();

        // legs
        drawLeg(c,hip,-1,current.lHip,current.lKnee,current.sit);
        drawLeg(c,hip, 1,current.rHip,current.rKnee,current.sit);

        // torso core
        c.save(); c.rotate(current.torsoDeg,chest.x,chest.y+100); c.scale(bodyScaleX,1f,chest.x,chest.y+100);
        fill(Color.rgb(243,233,229)); rr(c,chest.x-110,chest.y-55,chest.x+110,chest.y+265,55);
        fill(Color.rgb(145,134,187)); Path coat=new Path();
        coat.moveTo(chest.x-168,chest.y);coat.quadTo(chest.x,chest.y-65,chest.x+168,chest.y);
        coat.lineTo(chest.x+155,chest.y+300);coat.lineTo(chest.x+58,chest.y+315);
        coat.lineTo(chest.x+32,chest.y+90);coat.lineTo(chest.x-32,chest.y+90);
        coat.lineTo(chest.x-58,chest.y+315);coat.lineTo(chest.x-155,chest.y+300);coat.close();c.drawPath(coat,p);
        // collar
        fill(Color.rgb(255,248,244)); Path l=new Path();l.moveTo(chest.x-85,chest.y+15);l.lineTo(chest.x-10,chest.y+95);l.lineTo(chest.x-118,chest.y+115);l.close();c.drawPath(l,p);
        Path r=new Path();r.moveTo(chest.x+85,chest.y+15);r.lineTo(chest.x+10,chest.y+95);r.lineTo(chest.x+118,chest.y+115);r.close();c.drawPath(r,p);
        fill(Color.rgb(213,142,163)); c.drawCircle(chest.x,chest.y+100,18,p);
        c.restore();

        // arms
        V lShould=new V(chest.x-155*bodyScaleX,chest.y+45);
        V rShould=new V(chest.x+155*bodyScaleX,chest.y+45);
        drawArm(c,lShould,-1,current.lShoulder,current.lElbow,current.lWrist,current.shy>0.5f,false);
        drawArm(c,rShould, 1,current.rShoulder,current.rElbow,current.rWrist,false,current.phone>0.5f);

        // neck
        fill(Color.rgb(247,216,204)); drawCapsule(c,new V(neck.x,neck.y+45),new V(neck.x,neck.y+115),42,Color.rgb(247,216,204));

        // head / face
        drawHead(c,head,current.headDeg+current.torsoDeg*.35f,turn,t,now);

        // phone (separate prop)
        if(current.phone>.05f){
            float px=rShould.x+120,py=rShould.y-78;
            c.save();c.rotate(-12,px,py);fill(Color.rgb(63,56,76));rr(c,px-34,py-70,px+34,py+70,12);
            fill(Color.rgb(173,198,208));rr(c,px-28,py-59,px+28,py+48,8);fill(Color.rgb(213,142,163));c.drawCircle(px,py-5,8,p);c.restore();
        }

        // tiny accessory / charm
        if(pose==Pose.PHONE){
            fill(Color.rgb(250,242,232));c.drawCircle(cx+215,rootY+410,24,p);stroke(Color.rgb(83,70,92),3);c.drawCircle(cx+208,rootY+404,2,p);c.drawCircle(cx+222,rootY+404,2,p);
        }
    }

    private void drawHairBack(Canvas c,V h,float baseDeg,float lag){
        c.save();c.rotate(baseDeg*.45f+lag,h.x,h.y);
        fill(Color.rgb(66,56,79));c.drawOval(new RectF(h.x-205,h.y-235,h.x+205,h.y+260),p);
        // independent bundles
        drawHairLock(c,h.x-160,h.y-40,145,34,-8+lag*1.4f,Color.rgb(69,58,82));
        drawHairLock(c,h.x-95,h.y+15,185,38,-4+lag,Color.rgb(76,63,89));
        drawHairLock(c,h.x+95,h.y+15,185,38,4+lag,Color.rgb(76,63,89));
        drawHairLock(c,h.x+160,h.y-40,145,34,8+lag*1.4f,Color.rgb(69,58,82));
        c.restore();
    }

    private void drawHairLock(Canvas c,float x,float y,float len,float w,float deg,int color){
        c.save();c.rotate(deg,x,y);fill(color);Path q=new Path();
        q.moveTo(x-w,y);q.quadTo(x-w*.6f,y+len*.55f,x,y+len);q.quadTo(x+w*.6f,y+len*.55f,x+w,y);q.close();c.drawPath(q,p);c.restore();
    }

    private void drawHead(Canvas c,V h,float deg,float turn,float t,long now){
        c.save();c.rotate(deg,h.x,h.y);c.scale(1f-.10f*Math.abs(turn),1f,h.x,h.y);

        // ears
        fill(Color.rgb(245,211,199));c.drawOval(new RectF(h.x-177,h.y-20,h.x-125,h.y+70),p);c.drawOval(new RectF(h.x+125,h.y-20,h.x+177,h.y+70),p);
        // face
        fill(Color.rgb(252,227,214));c.drawRoundRect(new RectF(h.x-150,h.y-168,h.x+150,h.y+172),118,118,p);

        // blush
        if(current.shy>.25f){
            fill(Color.argb((int)(55+90*current.shy),236,138,154));c.drawOval(new RectF(h.x-125,h.y+45,h.x-55,h.y+78),p);c.drawOval(new RectF(h.x+55,h.y+45,h.x+125,h.y+78),p);
        }

        float blink=(t%4.8f)>4.62f?Math.max(.08f,Math.abs((t%4.8f)-4.71f)/.09f):1f;
        float ex=lookX*12+turn*9, ey=lookY*8;
        drawEye(c,h.x-74+ex,h.y-12+ey,blink);drawEye(c,h.x+74+ex,h.y-12+ey,blink);

        stroke(Color.rgb(91,74,99),6);
        c.drawLine(h.x-104,h.y-64-current.shy*6,h.x-48,h.y-70-current.shy*8,stroke);
        c.drawLine(h.x+48,h.y-70-current.shy*8,h.x+104,h.y-64-current.shy*6,stroke);

        fill(Color.rgb(225,165,158));c.drawCircle(h.x,h.y+36,4,p);
        stroke(Color.rgb(149,88,103),5);
        if(current.shy>.5f)c.drawArc(new RectF(h.x-28,h.y+58,h.x+28,h.y+95),20,140,false,stroke);
        else c.drawLine(h.x-18,h.y+78,h.x+18,h.y+78,stroke);

        // front hair in separate locks
        fill(Color.rgb(72,61,84));Path cap=new Path();cap.moveTo(h.x-155,h.y-82);cap.cubicTo(h.x-140,h.y-212,h.x-60,h.y-245,h.x,h.y-225);cap.cubicTo(h.x+95,h.y-252,h.x+158,h.y-174,h.x+158,h.y-72);cap.lineTo(h.x+115,h.y-112);cap.lineTo(h.x+70,h.y-45);cap.lineTo(h.x+23,h.y-123);cap.lineTo(h.x-28,h.y-42);cap.lineTo(h.x-82,h.y-123);cap.lineTo(h.x-128,h.y-48);cap.close();c.drawPath(cap,p);
        drawHairLock(c,h.x-120,h.y-45,120,25,-12+hairLag*.5f,Color.rgb(76,63,89));
        drawHairLock(c,h.x+120,h.y-45,120,25,12+hairLag*.5f,Color.rgb(76,63,89));
        c.restore();
    }

    private void drawEye(Canvas c,float x,float y,float open){
        fill(Color.rgb(255,251,249));c.drawOval(new RectF(x-33,y,x+33,y+52*open),p);
        fill(Color.rgb(104,82,112));c.drawOval(new RectF(x-21,y+7,x+21,y+49*open),p);
        fill(Color.rgb(48,40,54));c.drawOval(new RectF(x-9,y+16,x+9,y+48*open),p);
        if(open>.55f){fill(Color.WHITE);c.drawCircle(x+5,y+13,4,p);}
    }

    private void drawArm(Canvas c,V s,int side,float shoulder,float elbow,float wrist,boolean coverFace,boolean phoneHand){
        float base=side<0?-8:8;
        V e=polar(s,190,base+shoulder);
        V w=polar(e,180,base+shoulder+elbow);
        if(coverFace){ w=new V(480,700); e=new V(405,850); }
        drawCapsule(c,s,e,60,Color.rgb(145,134,187));
        drawCapsule(c,e,w,55,Color.rgb(139,126,179));
        V hand=polar(w,55,base+shoulder+elbow+wrist);
        drawCapsule(c,w,hand,38,Color.rgb(250,224,212));
        // sleeve cuff
        drawCapsule(c,new V(e.x,e.y),new V(e.x+(w.x-e.x)*.28f,e.y+(w.y-e.y)*.28f),64,Color.rgb(117,105,155));
        if(phoneHand) fill(Color.rgb(250,224,212));
    }

    private void drawLeg(Canvas c,V hip,int side,float hipDeg,float kneeDeg,float sit){
        float sx=hip.x+side*90, sy=hip.y+20;
        V h=new V(sx,sy);
        float base=side<0?-4:4;
        float thighLen=225;
        float calfLen=220;
        V k=polar(h,thighLen,base+hipDeg);
        V a=polar(k,calfLen,base+hipDeg+kneeDeg);
        if(sit>.5f){
            k=new V(hip.x+side*165,hip.y+150);
            a=new V(hip.x+side*245,hip.y+245);
        }
        drawCapsule(c,h,k,62,Color.rgb(110,101,143));
        drawCapsule(c,k,a,55,Color.rgb(239,229,224));
        V foot=new V(a.x+side*55,a.y+25);
        drawCapsule(c,a,foot,48,Color.rgb(77,67,90));
    }

    private void drawCapsule(Canvas c,V a,V b,float radius,int color){
        float dx=b.x-a.x,dy=b.y-a.y;float len=(float)Math.sqrt(dx*dx+dy*dy);
        float ang=(float)Math.toDegrees(Math.atan2(dy,dx));
        c.save();c.translate(a.x,a.y);c.rotate(ang);fill(color);c.drawRoundRect(new RectF(0,-radius,len,radius),radius,radius,p);c.restore();
    }

    private void drawBubble(Canvas c){
        fill(Color.argb(238,255,253,250));rr(c,90,220,990,395,32);stroke(Color.argb(35,70,58,82),2);c.drawRoundRect(new RectF(90,220,990,395),32,32,stroke);
        drawWrapped(c,bubble,130,278,820,31,44,Color.rgb(68,58,79));
    }

    private void drawTester(Canvas c){
        fill(Color.argb(220,255,252,249));rr(c,48,1540,1032,1880,38);stroke(Color.argb(35,70,58,82),2);c.drawRoundRect(new RectF(48,1540,1032,1880),38,38,stroke);
        text(c,"动作测试台（全部都是独立姿态参数，可直接换成最终素材）",78,1590,22,Color.rgb(129,112,134),false,Paint.Align.LEFT);
        for(int i=0;i<9;i++){
            int row=i/3,col=i%3;
            float x=76+col*316,y=1618+row*82;
            RectF q=new RectF(x,y,x+286,y+64);
            int bg=(pose==poses[i])?Color.rgb(143,126,225):Color.rgb(247,242,243);
            fill(bg);c.drawRoundRect(q,24,24,p);
            stroke(Color.argb(42,68,56,80),2);c.drawRoundRect(q,24,24,stroke);
            text(c,labels[i],q.centerX(),q.centerY()+9,24,(pose==poses[i])?Color.WHITE:Color.rgb(69,58,79),true,Paint.Align.CENTER);
        }
        text(c,"长按头部=摸头 · 拖动屏幕=视线跟随 · 双击头部=害羞",540,1862,18,Color.rgb(146,129,149),false,Paint.Align.CENTER);
    }

    private void showBubble(String s,long ms){bubble=s;bubbleUntil=SystemClock.uptimeMillis()+ms;invalidate();}

    private void drawWrapped(Canvas c,String s,float x,float y,float maxW,float size,float lineH,int color){
        p.setTextSize(size);p.setColor(color);p.setTypeface(Typeface.create("sans",Typeface.NORMAL));p.setTextAlign(Paint.Align.LEFT);
        StringBuilder line=new StringBuilder();float yy=y;
        for(int i=0;i<s.length();i++){char ch=s.charAt(i);String test=line.toString()+ch;if(p.measureText(test)>maxW&&line.length()>0){c.drawText(line.toString(),x,yy,p);yy+=lineH;line.setLength(0);}line.append(ch);}
        if(line.length()>0)c.drawText(line.toString(),x,yy,p);
    }

    private void text(Canvas c,String s,float x,float y,float size,int color,boolean bold,Paint.Align align){
        p.setShader(null);p.setStyle(Paint.Style.FILL);p.setColor(color);p.setTextSize(size);p.setTextAlign(align);p.setTypeface(Typeface.create("sans",bold?Typeface.BOLD:Typeface.NORMAL));c.drawText(s,x,y,p);
    }
    private void fill(int color){p.setShader(null);p.setStyle(Paint.Style.FILL);p.setColor(color);}
    private void stroke(int color,float width){stroke.setColor(color);stroke.setStrokeWidth(width);stroke.setStyle(Paint.Style.STROKE);}
    private void rr(Canvas c,float l,float t,float r,float b,float radius){c.drawRoundRect(new RectF(l,t,r,b),radius,radius,p);}
    private float clamp(float v,float a,float b){return Math.max(a,Math.min(b,v));}
    private float vx(float x){return (x-ox)/sc;} private float vy(float y){return (y-oy)/sc;}

    @Override public boolean onTouchEvent(MotionEvent e){
        float x=vx(e.getX()),y=vy(e.getY());long now=SystemClock.uptimeMillis();
        if(e.getActionMasked()==MotionEvent.ACTION_DOWN){
            downX=x;downY=y;downAt=now;downOnHead=(x>330&&x<750&&y>440&&y<890);
            targetLookX=clamp((x-540)/320,-1,1);targetLookY=clamp((y-720)/400,-.8f,.8f);
            pressed=buttonAt(x,y); return true;
        }
        if(e.getActionMasked()==MotionEvent.ACTION_MOVE){
            targetLookX=clamp((x-540)/320,-1,1);targetLookY=clamp((y-720)/400,-.8f,.8f);return true;
        }
        if(e.getActionMasked()==MotionEvent.ACTION_UP){
            float dx=x-downX,dy=y-downY;float d=(float)Math.sqrt(dx*dx+dy*dy);long held=now-downAt;
            int hit=buttonAt(x,y);
            if(d<35&&pressed>=0&&hit==pressed){ setPose(poses[hit]); showBubble("动作："+labels[hit],1800); }
            else if(d<35&&downOnHead&&held>480){ mood="被摸头"; affection=Math.min(80,affection+1); setPose(Pose.SHY); showBubble("嗯……可以再摸一下。",3600); }
            else if(d<35&&downOnHead){
                if(now-lastTap<320){mood="害羞";setPose(Pose.SHY);showBubble("你是故意连续戳我的吧？",3800);}else showBubble("怎么啦？我在。",2600);
                lastTap=now;
            }
            targetLookX=0;targetLookY=0;pressed=-1;persist();return true;
        }
        if(e.getActionMasked()==MotionEvent.ACTION_CANCEL){targetLookX=targetLookY=0;pressed=-1;return true;}
        return true;
    }

    private int buttonAt(float x,float y){
        for(int i=0;i<9;i++){int row=i/3,col=i%3;float bx=76+col*316,by=1618+row*82;if(x>=bx&&x<=bx+286&&y>=by&&y<=by+64)return i;}
        return -1;
    }
}
