package com.xiaoqi.companion;

import android.content.Context;
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
    private static final float VW = 1080f;
    private static final float VH = 1920f;

    private final MainActivity host;
    private final SharedPreferences prefs;
    private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Random random = new Random();

    private float scale = 1f, offX = 0f, offY = 0f;
    private float lookX = 0f, lookY = 0f, targetLookX = 0f, targetLookY = 0f;
    private float downX, downY;
    private long downTime = 0, lastTapTime = 0;
    private boolean downOnHead = false;
    private long bubbleUntil = 0, waveUntil = 0, petUntil = 0, shyUntil = 0;
    private long nextAuto = 0;
    private String bubble = "";
    private String mood = "平静";
    private String recent = "";
    private int affection = 2;
    private int visits = 0;
    private int poseMode = 0;

    private final RectF chatButton = new RectF(95, 1690, 385, 1800);
    private final RectF quietButton = new RectF(395, 1690, 685, 1800);
    private final RectF poseButton = new RectF(695, 1690, 985, 1800);
    private final RectF headZone = new RectF(330, 485, 750, 910);
    private final RectF bodyZone = new RectF(345, 900, 735, 1480);

    public CompanionView(MainActivity context, SharedPreferences prefs) {
        super(context);
        this.host = context;
        this.prefs = prefs;
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        p.setTypeface(Typeface.create("sans", Typeface.NORMAL));
        stroke.setStyle(Paint.Style.STROKE);
        stroke.setStrokeCap(Paint.Cap.ROUND);
        stroke.setStrokeJoin(Paint.Join.ROUND);
        setFocusable(true);
        affection = prefs.getInt("affection", 2);
        visits = prefs.getInt("visits", 0);
        recent = prefs.getString("recent", "");
    }

    public void beginSession() {
        long now = System.currentTimeMillis();
        long last = prefs.getLong("last_visit", 0L);
        visits++;
        Calendar cal = Calendar.getInstance();
        int hour = cal.get(Calendar.HOUR_OF_DAY);

        String greeting;
        if (last == 0L) {
            greeting = "你好。我叫小栖……以后，我可以住在这里吗？";
            mood = "有点期待";
        } else if (now - last > 36L * 60L * 60L * 1000L) {
            greeting = "你回来啦。我还以为今天也见不到你了。";
            mood = "安心";
        } else if (hour < 6) {
            greeting = "这么晚还醒着呀？我陪你一会儿。";
            mood = "困困的";
        } else if (hour < 11) {
            greeting = "早呀。今天也见到你了。";
            mood = "清醒";
        } else if (hour < 18) {
            greeting = "你来了。今天过得怎么样？";
            mood = "好奇";
        } else {
            greeting = "晚上好。忙完了吗？来这里坐一会儿吧。";
            mood = "放松";
        }

        if (!recent.isEmpty() && now - last < 72L * 60L * 60L * 1000L && random.nextBoolean()) {
            String r = recent.length() > 16 ? recent.substring(0, 16) + "…" : recent;
            greeting = "你回来啦。上次你跟我说“" + r + "”，后来怎么样了？";
        }
        showBubble(greeting, 7500);
        nextAuto = SystemClock.uptimeMillis() + 9000;
        persist();
    }

    public void persist() {
        prefs.edit()
                .putInt("affection", affection)
                .putInt("visits", visits)
                .putString("recent", recent)
                .putLong("last_visit", System.currentTimeMillis())
                .apply();
    }

    public void onUserMessage(String message) {
        recent = message.length() > 48 ? message.substring(0, 48) : message;
        String m = message.toLowerCase(Locale.ROOT);
        String reply;

        if (containsAny(m, "累", "烦", "难受", "压力", "不开心", "焦虑")) {
            reply = "那今天先别急着把自己整理好。你想说多少就说多少，我在听。";
            mood = "担心你";
            affection += 2;
        } else if (containsAny(m, "开心", "好消息", "成功", "通过", "拿到了", "太好了")) {
            reply = "真的？那我要替你高兴一会儿。再讲给我听，我想知道细节。";
            mood = "很开心";
            affection += 2;
            waveUntil = SystemClock.uptimeMillis() + 1800;
        } else if (containsAny(m, "困", "睡觉", "晚安")) {
            reply = "那就早点休息。手机放远一点也没关系，我明天还在这里。晚安。";
            mood = "温柔";
            affection += 1;
        } else if (containsAny(m, "早安", "早上好")) {
            reply = "早安。先喝点水再开始今天，好不好？";
            mood = "精神";
            affection += 1;
        } else if (containsAny(m, "想你", "喜欢你", "想见你")) {
            reply = "……我也会期待你打开这里。只是我刚刚没好意思先说。";
            mood = "害羞";
            shyUntil = SystemClock.uptimeMillis() + 3000;
            affection += 3;
        } else if (containsAny(m, "谢谢", "感谢")) {
            reply = "不用谢我呀。朋友之间，本来就可以这样。";
            mood = "开心";
            affection += 1;
        } else {
            String[] replies = {
                    "嗯，我在听。你继续说。",
                    "我记住了。下次你再提到这件事，我应该能接得上。",
                    "听起来这件事对你挺重要的。你自己现在是什么感觉？",
                    "我可能还不完全懂，但我想继续听你讲。",
                    "今天的你和昨天好像有一点不一样。是发生什么了吗？"
            };
            reply = replies[random.nextInt(replies.length)];
            mood = "认真听";
            affection += 1;
        }
        affection = Math.min(80, affection);
        showBubble(reply, 8000);
        performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
        persist();
    }

    private boolean containsAny(String s, String... keys) {
        for (String k : keys) if (s.contains(k)) return true;
        return false;
    }

    private void showBubble(String text, long ms) {
        bubble = text;
        bubbleUntil = SystemClock.uptimeMillis() + ms;
        invalidate();
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        scale = Math.min(w / VW, h / VH);
        offX = (w - VW * scale) * 0.5f;
        offY = (h - VH * scale) * 0.5f;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        long now = SystemClock.uptimeMillis();
        float t = now / 1000f;

        lookX += (targetLookX - lookX) * 0.10f;
        lookY += (targetLookY - lookY) * 0.10f;

        if (now > nextAuto) {
            int a = random.nextInt(5);
            if (a == 0) {
                mood = "发呆";
                showBubble("……刚刚发了一会儿呆。你在做什么？", 5000);
            } else if (a == 1) {
                waveUntil = now + 1500;
                mood = "注意到你";
            } else if (a == 2) {
                targetLookX = random.nextBoolean() ? -0.55f : 0.55f;
                targetLookY = -0.15f;
            } else if (a == 3 && visits > 2) {
                showBubble("我发现，等你打开这里已经变成一种习惯了。", 5500);
                mood = "安心";
            } else {
                mood = "平静";
            }
            nextAuto = now + 9000 + random.nextInt(9000);
        }

        canvas.save();
        canvas.translate(offX, offY);
        canvas.scale(scale, scale);

        drawRoom(canvas, t);
        drawTopStatus(canvas);
        drawCompanion(canvas, t, now);
        if (bubbleUntil > now) drawBubble(canvas);
        drawBottomActions(canvas);

        canvas.restore();
        postInvalidateOnAnimation();
    }

    private void drawRoom(Canvas c, float t) {
        Calendar cal = Calendar.getInstance();
        int hour = cal.get(Calendar.HOUR_OF_DAY);
        boolean night = hour < 6 || hour >= 20;

        int top = night ? Color.rgb(42, 43, 67) : Color.rgb(246, 241, 234);
        int bottom = night ? Color.rgb(79, 67, 91) : Color.rgb(232, 220, 211);
        LinearGradient g = new LinearGradient(0, 0, 0, VH, top, bottom, Shader.TileMode.CLAMP);
        p.setShader(g);
        c.drawRect(0, 0, VW, VH, p);
        p.setShader(null);

        // Window.
        fill(Color.argb(220, 72, 62, 83));
        rr(c, 650, 150, 960, 520, 34);
        fill(night ? Color.rgb(38, 49, 83) : Color.rgb(170, 210, 224));
        rr(c, 672, 172, 938, 498, 24);
        fill(Color.argb(110, 255, 255, 255));
        c.drawRect(800, 172, 810, 498, p);
        c.drawRect(672, 330, 938, 340, p);
        if (night) {
            fill(Color.rgb(255, 236, 176));
            c.drawCircle(865, 242, 28, p);
            fill(Color.argb(210, 245, 240, 220));
            for (int i = 0; i < 8; i++) {
                float sx = 700 + (i * 37) % 210;
                float sy = 210 + (i * 61) % 210;
                c.drawCircle(sx, sy, 3 + (i % 2), p);
            }
        } else {
            fill(Color.argb(120, 255, 255, 255));
            c.drawOval(new RectF(705, 235, 790, 270), p);
            c.drawOval(new RectF(835, 395, 915, 425), p);
        }

        // Curtain.
        fill(night ? Color.rgb(91, 72, 102) : Color.rgb(193, 166, 184));
        Path curtain = new Path();
        curtain.moveTo(620, 120); curtain.lineTo(675, 145); curtain.lineTo(660, 565);
        curtain.lineTo(600, 585); curtain.close(); c.drawPath(curtain, p);
        curtain = new Path();
        curtain.moveTo(970, 120); curtain.lineTo(930, 145); curtain.lineTo(950, 565);
        curtain.lineTo(1012, 585); curtain.close(); c.drawPath(curtain, p);

        // Shelf and books.
        fill(night ? Color.rgb(89, 69, 67) : Color.rgb(136, 101, 83));
        rr(c, 92, 250, 460, 275, 10);
        fill(Color.rgb(210, 143, 124)); rr(c, 130, 198, 180, 252, 8);
        fill(Color.rgb(123, 151, 162)); rr(c, 190, 186, 240, 252, 8);
        fill(Color.rgb(181, 167, 105)); rr(c, 250, 207, 300, 252, 8);
        fill(Color.rgb(121, 111, 150)); rr(c, 310, 175, 365, 252, 8);

        // Plant.
        fill(Color.rgb(126, 90, 73)); rr(c, 135, 355, 260, 470, 20);
        fill(Color.rgb(85, 135, 98));
        c.drawOval(new RectF(115, 300, 200, 390), p);
        c.drawOval(new RectF(185, 280, 280, 380), p);
        c.drawOval(new RectF(145, 250, 235, 355), p);

        // Floor and rug.
        fill(night ? Color.rgb(75, 64, 75) : Color.rgb(220, 203, 190));
        c.drawRect(0, 1180, VW, VH, p);
        fill(night ? Color.rgb(106, 83, 113) : Color.rgb(207, 174, 184));
        c.drawOval(new RectF(165, 1280, 915, 1720), p);

        // Small lamp.
        fill(Color.rgb(113, 83, 72)); rr(c, 825, 915, 930, 1120, 18);
        fill(night ? Color.rgb(255, 220, 157) : Color.rgb(229, 188, 149));
        Path shade = new Path();
        shade.moveTo(780, 900); shade.lineTo(970, 900); shade.lineTo(925, 1020); shade.lineTo(820, 1020); shade.close();
        c.drawPath(shade, p);
        if (night) {
            p.setShader(new RadialGradient(875, 970, 260, Color.argb(75,255,213,140), Color.TRANSPARENT, Shader.TileMode.CLAMP));
            c.drawCircle(875, 970, 260, p);
            p.setShader(null);
        }

        // Floating dust gives the room life.
        fill(Color.argb(night ? 70 : 55, 255, 244, 225));
        for (int i = 0; i < 16; i++) {
            float x = 80 + ((i * 149) % 920);
            float y = 580 + ((i * 83) % 540) + (float)Math.sin(t * 0.45f + i) * 12f;
            c.drawCircle(x, y, 2.5f, p);
        }
    }

    private void drawTopStatus(Canvas c) {
        fill(Color.argb(190, 255, 252, 249));
        rr(c, 54, 52, 1026, 185, 34);
        stroke(Color.argb(45, 70, 55, 82), 2);
        c.drawRoundRect(new RectF(54, 52, 1026, 185), 34, 34, stroke);

        text(c, "小栖", 92, 108, 39, Color.rgb(62, 53, 76), true);
        text(c, "·  " + mood, 185, 106, 27, Color.rgb(126, 109, 135), false);
        text(c, closenessLabel(), 92, 153, 24, Color.rgb(139, 120, 145), false);

        fill(Color.rgb(142, 123, 239));
        c.drawCircle(946, 114, 28, p);
        fill(Color.WHITE);
        c.drawCircle(938, 108, 4, p);
        c.drawCircle(954, 108, 4, p);
        stroke(Color.WHITE, 3);
        c.drawArc(new RectF(936, 107, 956, 128), 25, 130, false, stroke);
    }

    private String closenessLabel() {
        String relation;
        if (affection < 7) relation = "初次见面";
        else if (affection < 18) relation = "渐渐熟悉";
        else if (affection < 38) relation = "熟悉的朋友";
        else relation = "很亲近";
        return relation + "  ·  第 " + visits + " 次见面";
    }

    private void drawCompanion(Canvas c, float t, long now) {
        float sway = (float)Math.sin(t * 0.82f) * 5f;
        float breath = (float)Math.sin(t * 2.0f) * 4f;
        float headTurn = lookX * 4.5f;
        float baseX = 540 + sway;
        float baseY = poseMode == 2 ? 1110 : 1035;

        // Shadow/cushion.
        fill(Color.argb(50, 58, 46, 66));
        c.drawOval(new RectF(baseX - 230, 1390, baseX + 230, 1480), p);
        fill(Color.rgb(183, 155, 182));
        c.drawOval(new RectF(baseX - 185, 1340, baseX + 185, 1445), p);

        // Back hair.
        c.save();
        c.rotate(headTurn * 0.75f, baseX, 700);
        fill(Color.rgb(67, 57, 79));
        Path hairBack = new Path();
        hairBack.moveTo(baseX - 182, 650);
        hairBack.cubicTo(baseX - 170, 485, baseX - 82, 430, baseX, 430);
        hairBack.cubicTo(baseX + 110, 430, baseX + 182, 510, baseX + 180, 680);
        hairBack.lineTo(baseX + 135, 890);
        hairBack.cubicTo(baseX + 55, 935, baseX - 60, 935, baseX - 140, 885);
        hairBack.close();
        c.drawPath(hairBack, p);
        c.restore();

        // Legs behind body.
        fill(Color.rgb(95, 91, 124));
        rr(c, baseX - 125, baseY + 210, baseX - 18, baseY + 455, 48);
        rr(c, baseX + 18, baseY + 210, baseX + 125, baseY + 455, 48);
        fill(Color.rgb(75, 67, 91));
        rr(c, baseX - 142, baseY + 390, baseX - 10, baseY + 475, 38);
        rr(c, baseX + 10, baseY + 390, baseX + 142, baseY + 475, 38);

        // Torso.
        fill(Color.rgb(149, 135, 190));
        Path torso = new Path();
        torso.moveTo(baseX - 152, baseY - 120);
        torso.quadTo(baseX, baseY - 178 - breath, baseX + 152, baseY - 120);
        torso.lineTo(baseX + 178, baseY + 275);
        torso.quadTo(baseX, baseY + 335, baseX - 178, baseY + 275);
        torso.close();
        c.drawPath(torso, p);

        // Collar and shirt.
        fill(Color.rgb(246, 235, 230));
        Path collarL = new Path();
        collarL.moveTo(baseX - 80, baseY - 110); collarL.lineTo(baseX - 8, baseY - 26); collarL.lineTo(baseX - 112, baseY + 10); collarL.close();
        c.drawPath(collarL, p);
        Path collarR = new Path();
        collarR.moveTo(baseX + 80, baseY - 110); collarR.lineTo(baseX + 8, baseY - 26); collarR.lineTo(baseX + 112, baseY + 10); collarR.close();
        c.drawPath(collarR, p);
        fill(Color.rgb(89, 75, 111));
        rr(c, baseX - 14, baseY - 22, baseX + 14, baseY + 175, 12);

        // Arms: right arm can wave.
        float wave = now < waveUntil ? (float)Math.sin((waveUntil - now) / 110.0f) * 32f : 0f;
        drawArm(c, baseX - 162, baseY - 55, -12f, false);
        drawArm(c, baseX + 162, baseY - 55, 14f - wave, true);

        // Neck.
        fill(Color.rgb(250, 218, 203));
        rr(c, baseX - 48, baseY - 205, baseX + 48, baseY - 85, 24);

        // Head group.
        float headY = baseY - 430 + breath * 0.35f;
        c.save();
        c.rotate(headTurn, baseX, headY);

        // Ears.
        fill(Color.rgb(247, 212, 198));
        c.drawOval(new RectF(baseX - 177, headY - 30, baseX - 125, headY + 55), p);
        c.drawOval(new RectF(baseX + 125, headY - 30, baseX + 177, headY + 55), p);

        // Face.
        fill(Color.rgb(252, 226, 212));
        c.drawRoundRect(new RectF(baseX - 150, headY - 170, baseX + 150, headY + 175), 118, 118, p);

        // Blush.
        if (now < shyUntil || now < petUntil) {
            fill(Color.argb(105, 238, 137, 147));
            c.drawOval(new RectF(baseX - 122, headY + 38, baseX - 55, headY + 70), p);
            c.drawOval(new RectF(baseX + 55, headY + 38, baseX + 122, headY + 70), p);
        }

        // Eyes track finger.
        float blinkPhase = (t + 0.7f) % 4.9f;
        float open = blinkPhase > 4.66f ? Math.max(0.08f, Math.abs(blinkPhase - 4.77f) / 0.11f) : 1f;
        float ex = lookX * 10f, ey = lookY * 7f;
        fill(Color.rgb(67, 57, 78));
        c.drawOval(new RectF(baseX - 91 + ex, headY - 22 + ey, baseX - 55 + ex, headY - 22 + ey + 40 * open), p);
        c.drawOval(new RectF(baseX + 55 + ex, headY - 22 + ey, baseX + 91 + ex, headY - 22 + ey + 40 * open), p);
        if (open > 0.55f) {
            fill(Color.rgb(252, 250, 249));
            c.drawCircle(baseX - 67 + ex, headY - 12 + ey, 5, p);
            c.drawCircle(baseX + 79 + ex, headY - 12 + ey, 5, p);
        }

        // Brows.
        stroke(Color.rgb(91, 75, 98), 6);
        c.drawLine(baseX - 100, headY - 63, baseX - 48, headY - 69, stroke);
        c.drawLine(baseX + 48, headY - 69, baseX + 100, headY - 63, stroke);

        // Nose/mouth.
        fill(Color.rgb(227, 168, 160));
        c.drawCircle(baseX, headY + 35, 5, p);
        stroke(Color.rgb(150, 90, 104), 6);
        if (now < petUntil) {
            c.drawArc(new RectF(baseX - 28, headY + 61, baseX + 28, headY + 100), 20, 140, false, stroke);
        } else {
            c.drawLine(baseX - 18, headY + 79, baseX + 18, headY + 79, stroke);
        }

        // Front hair.
        fill(Color.rgb(72, 61, 84));
        Path bangs = new Path();
        bangs.moveTo(baseX - 155, headY - 80);
        bangs.cubicTo(baseX - 148, headY - 210, baseX - 60, headY - 245, baseX + 10, headY - 225);
        bangs.cubicTo(baseX + 100, headY - 250, baseX + 160, headY - 175, baseX + 158, headY - 65);
        bangs.lineTo(baseX + 110, headY - 118);
        bangs.lineTo(baseX + 72, headY - 42);
        bangs.lineTo(baseX + 20, headY - 125);
        bangs.lineTo(baseX - 30, headY - 38);
        bangs.lineTo(baseX - 82, headY - 122);
        bangs.lineTo(baseX - 125, headY - 48);
        bangs.close();
        c.drawPath(bangs, p);

        c.restore();

        // Pet hearts.
        if (now < petUntil) {
            float k = 1f - (petUntil - now) / 1500f;
            drawHeart(c, baseX + 185, headY - 120 - k * 80, 18, Color.rgb(235, 126, 151));
            drawHeart(c, baseX - 205, headY - 50 - k * 105, 13, Color.rgb(237, 157, 174));
        }
    }

    private void drawArm(Canvas c, float x, float y, float angle, boolean right) {
        c.save();
        c.rotate(angle, x, y);
        fill(Color.rgb(149, 135, 190));
        float l = right ? x : x - 92;
        float r = right ? x + 92 : x;
        rr(c, l, y, r, y + 300, 44);
        fill(Color.rgb(252, 226, 212));
        float hx = right ? x + 45 : x - 45;
        c.drawCircle(hx, y + 294, 42, p);
        c.restore();
    }

    private void drawBubble(Canvas c) {
        fill(Color.argb(235, 255, 253, 250));
        rr(c, 90, 245, 990, 430, 34);
        Path tail = new Path();
        tail.moveTo(505, 430); tail.lineTo(555, 474); tail.lineTo(590, 430); tail.close();
        c.drawPath(tail, p);
        stroke(Color.argb(38, 75, 61, 89), 2);
        c.drawRoundRect(new RectF(90,245,990,430),34,34,stroke);
        drawWrappedText(c, bubble, 130, 304, 820, 32, 48, Color.rgb(67, 57, 78));
    }

    private void drawBottomActions(Canvas c) {
        fill(Color.argb(205, 255, 252, 249));
        rr(c, 54, 1625, 1026, 1848, 42);
        stroke(Color.argb(35, 72, 58, 86), 2);
        c.drawRoundRect(new RectF(54,1625,1026,1848),42,42,stroke);

        pill(c, chatButton, "聊聊天", "○", Color.rgb(142,123,239));
        pill(c, quietButton, "一起发呆", "…", Color.rgb(182,145,166));
        pill(c, poseButton, "换个动作", "↻", Color.rgb(111,151,159));

        text(c, "直接摸摸她、戳戳她，或者让她看着你的手指。", 540, 1830, 20, Color.rgb(150,133,151), false, Paint.Align.CENTER);
    }

    private void pill(Canvas c, RectF r, String label, String icon, int accent) {
        fill(Color.argb(230, 250, 247, 246));
        c.drawRoundRect(r, 34, 34, p);
        stroke(Color.argb(45, 65, 53, 79), 2);
        c.drawRoundRect(r, 34, 34, stroke);
        fill(accent);
        c.drawCircle(r.left + 47, r.centerY(), 25, p);
        text(c, icon, r.left + 47, r.centerY() + 8, 24, Color.WHITE, true, Paint.Align.CENTER);
        text(c, label, r.left + 85, r.centerY() + 9, 26, Color.rgb(70, 59, 80), true);
    }

    private void drawHeart(Canvas c, float x, float y, float s, int color) {
        fill(color);
        Path h = new Path();
        h.moveTo(x, y + s);
        h.cubicTo(x - s * 1.4f, y, x - s, y - s, x, y - s * 0.25f);
        h.cubicTo(x + s, y - s, x + s * 1.4f, y, x, y + s);
        c.drawPath(h, p);
    }

    private void drawWrappedText(Canvas c, String s, float x, float y, float maxWidth, float size, float lineHeight, int color) {
        p.setTypeface(Typeface.create("sans", Typeface.NORMAL));
        p.setTextSize(size);
        p.setColor(color);
        p.setTextAlign(Paint.Align.LEFT);
        StringBuilder line = new StringBuilder();
        float yy = y;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            String test = line.toString() + ch;
            if (p.measureText(test) > maxWidth && line.length() > 0) {
                c.drawText(line.toString(), x, yy, p);
                yy += lineHeight;
                line.setLength(0);
            }
            line.append(ch);
        }
        if (line.length() > 0) c.drawText(line.toString(), x, yy, p);
    }

    private void text(Canvas c, String s, float x, float y, float size, int color, boolean bold) {
        text(c, s, x, y, size, color, bold, Paint.Align.LEFT);
    }

    private void text(Canvas c, String s, float x, float y, float size, int color, boolean bold, Paint.Align align) {
        p.setShader(null);
        p.setStyle(Paint.Style.FILL);
        p.setColor(color);
        p.setTextSize(size);
        p.setTextAlign(align);
        p.setTypeface(Typeface.create("sans", bold ? Typeface.BOLD : Typeface.NORMAL));
        c.drawText(s, x, y, p);
    }

    private void fill(int color) {
        p.setShader(null);
        p.setStyle(Paint.Style.FILL);
        p.setColor(color);
    }

    private void stroke(int color, float width) {
        stroke.setColor(color);
        stroke.setStrokeWidth(width);
        stroke.setStyle(Paint.Style.STROKE);
    }

    private void rr(Canvas c, float l, float t, float r, float b, float radius) {
        c.drawRoundRect(new RectF(l, t, r, b), radius, radius, p);
    }

    private float clamp(float v, float a, float b) {
        return Math.max(a, Math.min(b, v));
    }

    private float vx(float screenX) {
        return (screenX - offX) / scale;
    }

    private float vy(float screenY) {
        return (screenY - offY) / scale;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float x = vx(event.getX());
        float y = vy(event.getY());
        long now = SystemClock.uptimeMillis();

        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                downX = x; downY = y; downTime = now;
                downOnHead = headZone.contains(x, y);
                targetLookX = clamp((x - 540f) / 310f, -1f, 1f);
                targetLookY = clamp((y - 760f) / 360f, -0.75f, 0.75f);
                return true;

            case MotionEvent.ACTION_MOVE:
                targetLookX = clamp((x - 540f) / 310f, -1f, 1f);
                targetLookY = clamp((y - 760f) / 360f, -0.75f, 0.75f);
                return true;

            case MotionEvent.ACTION_UP:
                float dx = x - downX, dy = y - downY;
                float dist = (float)Math.sqrt(dx * dx + dy * dy);
                long held = now - downTime;

                if (dist < 36f) {
                    if (chatButton.contains(x, y)) {
                        host.openChat();
                    } else if (quietButton.contains(x, y)) {
                        mood = "陪着你";
                        showBubble("好。那我们什么都不做，就一起待一会儿。", 6000);
                        affection = Math.min(80, affection + 1);
                        performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
                    } else if (poseButton.contains(x, y)) {
                        poseMode = (poseMode + 1) % 3;
                        waveUntil = now + 1200;
                        showBubble(poseMode == 2 ? "这样坐着会不会更像在陪你？" : "换好了。你觉得这样怎么样？", 4500);
                    } else if (downOnHead && held > 480) {
                        petUntil = now + 1500;
                        shyUntil = now + 2300;
                        mood = "被摸头";
                        affection = Math.min(80, affection + 2);
                        showBubble("嗯……可以再摸一下。", 4200);
                        performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
                    } else if (headZone.contains(x, y)) {
                        if (now - lastTapTime < 310) {
                            shyUntil = now + 2500;
                            petUntil = now + 1200;
                            mood = "有点害羞";
                            showBubble("连续戳我两下……你是故意的吧？", 4500);
                        } else {
                            mood = "看着你";
                            showBubble(random.nextBoolean() ? "怎么啦？我在。" : "你刚刚是在叫我吗？", 4000);
                        }
                        affection = Math.min(80, affection + 1);
                        lastTapTime = now;
                    } else if (bodyZone.contains(x, y)) {
                        waveUntil = now + 1600;
                        mood = "回应你";
                        showBubble("收到。这个算是我们的打招呼方式吗？", 4200);
                    } else {
                        mood = "跟着看";
                        showBubble("我会看着你点的地方。", 3200);
                    }
                }

                targetLookX = 0f;
                targetLookY = 0f;
                persist();
                return true;

            case MotionEvent.ACTION_CANCEL:
                targetLookX = 0f;
                targetLookY = 0f;
                return true;
        }
        return true;
    }
}
