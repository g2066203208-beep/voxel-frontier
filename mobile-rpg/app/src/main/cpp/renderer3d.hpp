#pragma once
#include "math3d.hpp"
#include "font_chars.hpp"
#include <android_native_app_glue.h>
#include <android/bitmap.h>
#include <android/log.h>
#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <jni.h>
#include <vector>
#include <unordered_map>
#include <string>
#include <algorithm>
#include <cmath>

namespace fb {

struct V3 { float x,y,z,r,g,b,a; };
struct V2 { float x,y,r,g,b,a; };
struct VT { float x,y,u,v,r,g,b,a; };
struct Rect { float x=0,y=0,w=0,h=0; };
inline bool contains(Rect r,float x,float y){ return x>=r.x&&x<=r.x+r.w&&y>=r.y&&y<=r.y+r.h; }

class Renderer3D {
public:
    EGLDisplay display=EGL_NO_DISPLAY;
    EGLSurface surface=EGL_NO_SURFACE;
    EGLContext context=EGL_NO_CONTEXT;
    int w=1280,h=720;
    bool ready=false;

    GLuint prog3=0,prog2=0,progText=0;
    GLuint vao3=0,vbo3=0,vao2=0,vbo2=0,vaoT=0,vboT=0,fontTex=0;
    GLint mvpLoc=-1,screenLoc=-1,textScreenLoc=-1;
    std::vector<V3> v3;
    std::vector<V2> v2;
    std::vector<VT> vt;
    std::unordered_map<char32_t,int> glyphIndex;

    static GLuint shader(GLenum type,const char* src){
        GLuint s=glCreateShader(type); glShaderSource(s,1,&src,nullptr); glCompileShader(s);
        GLint ok=0; glGetShaderiv(s,GL_COMPILE_STATUS,&ok);
        if(!ok){ char log[2048]{}; glGetShaderInfoLog(s,2048,nullptr,log); __android_log_print(ANDROID_LOG_ERROR,"Faithbound","shader %s",log); }
        return s;
    }
    static GLuint program(const char* vs,const char* fs){
        GLuint a=shader(GL_VERTEX_SHADER,vs),b=shader(GL_FRAGMENT_SHADER,fs),p=glCreateProgram();
        glAttachShader(p,a);glAttachShader(p,b);glLinkProgram(p);
        glDeleteShader(a);glDeleteShader(b);
        GLint ok=0;glGetProgramiv(p,GL_LINK_STATUS,&ok);
        if(!ok){ char log[2048]{};glGetProgramInfoLog(p,2048,nullptr,log);__android_log_print(ANDROID_LOG_ERROR,"Faithbound","link %s",log); }
        return p;
    }

    bool init(android_app* app){
        const EGLint cfgAttr[]={
            EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT,EGL_SURFACE_TYPE,EGL_WINDOW_BIT,
            EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_DEPTH_SIZE,24,EGL_NONE};
        const EGLint ctxAttr[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
        display=eglGetDisplay(EGL_DEFAULT_DISPLAY);
        if(display==EGL_NO_DISPLAY||!eglInitialize(display,nullptr,nullptr))return false;
        EGLConfig cfg=nullptr;EGLint count=0;
        if(!eglChooseConfig(display,cfgAttr,&cfg,1,&count)||count<1)return false;
        EGLint format=0;eglGetConfigAttrib(display,cfg,EGL_NATIVE_VISUAL_ID,&format);
        ANativeWindow_setBuffersGeometry(app->window,0,0,format);
        surface=eglCreateWindowSurface(display,cfg,app->window,nullptr);
        context=eglCreateContext(display,cfg,EGL_NO_CONTEXT,ctxAttr);
        if(surface==EGL_NO_SURFACE||context==EGL_NO_CONTEXT||!eglMakeCurrent(display,surface,surface,context))return false;
        eglQuerySurface(display,surface,EGL_WIDTH,&w);eglQuerySurface(display,surface,EGL_HEIGHT,&h);
        eglSwapInterval(display,1);

        const char* vs3=R"(#version 300 es
        layout(location=0) in vec3 aPos;
        layout(location=1) in vec4 aColor;
        uniform mat4 uMVP;
        out vec4 vColor;
        void main(){ gl_Position=uMVP*vec4(aPos,1.0); vColor=aColor; })";
        const char* fs3=R"(#version 300 es
        precision mediump float;
        in vec4 vColor; out vec4 oColor;
        void main(){ oColor=vColor; })";
        const char* vs2=R"(#version 300 es
        layout(location=0) in vec2 aPos;
        layout(location=1) in vec4 aColor;
        uniform vec2 uScreen;
        out vec4 vColor;
        void main(){
          vec2 p=vec2(aPos.x/uScreen.x*2.0-1.0,1.0-aPos.y/uScreen.y*2.0);
          gl_Position=vec4(p,0.0,1.0); vColor=aColor;
        })";
        const char* fs2=R"(#version 300 es
        precision mediump float;
        in vec4 vColor; out vec4 oColor;
        void main(){ oColor=vColor; })";
        const char* vst=R"(#version 300 es
        layout(location=0) in vec2 aPos;
        layout(location=1) in vec2 aUV;
        layout(location=2) in vec4 aColor;
        uniform vec2 uScreen;
        out vec2 vUV; out vec4 vColor;
        void main(){
          vec2 p=vec2(aPos.x/uScreen.x*2.0-1.0,1.0-aPos.y/uScreen.y*2.0);
          gl_Position=vec4(p,0.0,1.0); vUV=aUV; vColor=aColor;
        })";
        const char* fst=R"(#version 300 es
        precision mediump float;
        uniform sampler2D uTex;
        in vec2 vUV; in vec4 vColor; out vec4 oColor;
        void main(){ float a=texture(uTex,vUV).a; if(a<0.05)discard; oColor=vec4(vColor.rgb,vColor.a*a); })";

        prog3=program(vs3,fs3);prog2=program(vs2,fs2);progText=program(vst,fst);
        mvpLoc=glGetUniformLocation(prog3,"uMVP");
        screenLoc=glGetUniformLocation(prog2,"uScreen");
        textScreenLoc=glGetUniformLocation(progText,"uScreen");

        glGenVertexArrays(1,&vao3);glBindVertexArray(vao3);
        glGenBuffers(1,&vbo3);glBindBuffer(GL_ARRAY_BUFFER,vbo3);
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,sizeof(V3),(void*)0);
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,4,GL_FLOAT,GL_FALSE,sizeof(V3),(void*)(3*sizeof(float)));

        glGenVertexArrays(1,&vao2);glBindVertexArray(vao2);
        glGenBuffers(1,&vbo2);glBindBuffer(GL_ARRAY_BUFFER,vbo2);
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,sizeof(V2),(void*)0);
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,4,GL_FLOAT,GL_FALSE,sizeof(V2),(void*)(2*sizeof(float)));

        glGenVertexArrays(1,&vaoT);glBindVertexArray(vaoT);
        glGenBuffers(1,&vboT);glBindBuffer(GL_ARRAY_BUFFER,vboT);
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,sizeof(VT),(void*)0);
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,2,GL_FLOAT,GL_FALSE,sizeof(VT),(void*)(2*sizeof(float)));
        glEnableVertexAttribArray(2);glVertexAttribPointer(2,4,GL_FLOAT,GL_FALSE,sizeof(VT),(void*)(4*sizeof(float)));
        glBindVertexArray(0);

        v3.reserve(400000);v2.reserve(30000);vt.reserve(30000);
        if(!buildFontAtlas(app)) __android_log_print(ANDROID_LOG_WARN,"Faithbound","Chinese font atlas unavailable");
        glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
        ready=true;return true;
    }

    bool buildFontAtlas(android_app* app){
        JavaVM* vm=app->activity->vm; if(!vm)return false;
        JNIEnv* env=nullptr; bool detach=false;
        jint state=vm->GetEnv(reinterpret_cast<void**>(&env),JNI_VERSION_1_6);
        if(state!=JNI_OK){ if(vm->AttachCurrentThread(&env,nullptr)!=JNI_OK)return false; detach=true; }

        constexpr int atlas=1024, cell=32, cols=32;
        jclass cfgCls=env->FindClass("android/graphics/Bitmap$Config");
        jclass bmpCls=env->FindClass("android/graphics/Bitmap");
        jclass canvasCls=env->FindClass("android/graphics/Canvas");
        jclass paintCls=env->FindClass("android/graphics/Paint");
        if(!cfgCls||!bmpCls||!canvasCls||!paintCls){ if(detach)vm->DetachCurrentThread();return false; }

        jfieldID argb=env->GetStaticFieldID(cfgCls,"ARGB_8888","Landroid/graphics/Bitmap$Config;");
        jobject config=env->GetStaticObjectField(cfgCls,argb);
        jmethodID create=env->GetStaticMethodID(bmpCls,"createBitmap","(IILandroid/graphics/Bitmap$Config;)Landroid/graphics/Bitmap;");
        jobject bitmap=env->CallStaticObjectMethod(bmpCls,create,atlas,atlas,config);
        jmethodID cctor=env->GetMethodID(canvasCls,"<init>","(Landroid/graphics/Bitmap;)V");
        jobject canvas=env->NewObject(canvasCls,cctor,bitmap);
        jmethodID pctor=env->GetMethodID(paintCls,"<init>","()V");
        jobject paint=env->NewObject(paintCls,pctor);
        jmethodID setColor=env->GetMethodID(paintCls,"setColor","(I)V");
        jmethodID setTextSize=env->GetMethodID(paintCls,"setTextSize","(F)V");
        jmethodID setAA=env->GetMethodID(paintCls,"setAntiAlias","(Z)V");
        jmethodID setFakeBold=env->GetMethodID(paintCls,"setFakeBoldText","(Z)V");
        jmethodID drawText=env->GetMethodID(canvasCls,"drawText","(Ljava/lang/String;FFLandroid/graphics/Paint;)V");
        env->CallVoidMethod(paint,setColor,jint(0xffffffff));
        env->CallVoidMethod(paint,setTextSize,jfloat(25.f));
        env->CallVoidMethod(paint,setAA,JNI_TRUE);
        env->CallVoidMethod(paint,setFakeBold,JNI_TRUE);

        glyphIndex.clear();
        for(uint32_t i=0;i<kFontGlyphCount && i<1024;i++){
            char32_t cp=kFontGlyphs[i]; glyphIndex[cp]=int(i);
            jchar ch=jchar(cp);
            jstring js=env->NewString(&ch,1);
            float x=float((i%cols)*cell+2), y=float((i/cols)*cell+26);
            env->CallVoidMethod(canvas,drawText,js,jfloat(x),jfloat(y),paint);
            env->DeleteLocalRef(js);
        }

        AndroidBitmapInfo info{};
        void* pixels=nullptr;
        bool ok=AndroidBitmap_getInfo(env,bitmap,&info)==ANDROID_BITMAP_RESULT_SUCCESS &&
                AndroidBitmap_lockPixels(env,bitmap,&pixels)==ANDROID_BITMAP_RESULT_SUCCESS;
        if(ok){
            glGenTextures(1,&fontTex);glBindTexture(GL_TEXTURE_2D,fontTex);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
            glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,info.width,info.height,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
            AndroidBitmap_unlockPixels(env,bitmap);
        }
        env->DeleteLocalRef(paint);env->DeleteLocalRef(canvas);env->DeleteLocalRef(bitmap);
        env->DeleteLocalRef(config);env->DeleteLocalRef(paintCls);env->DeleteLocalRef(canvasCls);env->DeleteLocalRef(bmpCls);env->DeleteLocalRef(cfgCls);
        if(detach)vm->DetachCurrentThread();
        return ok;
    }

    void term(){
        if(display!=EGL_NO_DISPLAY){
            eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);
            if(context!=EGL_NO_CONTEXT)eglDestroyContext(display,context);
            if(surface!=EGL_NO_SURFACE)eglDestroySurface(display,surface);
            eglTerminate(display);
        }
        display=EGL_NO_DISPLAY;surface=EGL_NO_SURFACE;context=EGL_NO_CONTEXT;ready=false;
    }

    void begin(Color sky){
        v3.clear();v2.clear();vt.clear();
        glViewport(0,0,w,h);glClearColor(sky.r,sky.g,sky.b,sky.a);
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    }

    void p3(Vec3 p,Color c){ v3.push_back({p.x,p.y,p.z,c.r,c.g,c.b,c.a}); }
    void tri3(Vec3 a,Vec3 b,Vec3 c,Color col){ p3(a,col);p3(b,col);p3(c,col); }
    void quad3(Vec3 a,Vec3 b,Vec3 c,Vec3 d,Color col){ tri3(a,b,c,col);tri3(a,c,d,col); }

    enum FaceMask : uint8_t { Top=1,Bottom=2,North=4,South=8,East=16,West=32 };
    void cube(float x,float y,float z,uint8_t faces,Color base,float light=1.f){
        Color top=mul(base,light), north=mul(base,light*0.74f), south=mul(base,light*0.88f);
        Color east=mul(base,light*0.80f),west=mul(base,light*0.67f),bottom=mul(base,light*0.52f);
        float x1=x+1,y1=y+1,z1=z+1;
        if(faces&Top) quad3({x,y1,z},{x,z1?y1:y1,z1},{x1,y1,z1},{x1,y1,z},top);
        if(faces&Bottom) quad3({x,y,z1},{x,y,z},{x1,y,z},{x1,y,z1},bottom);
        if(faces&North) quad3({x1,y,z},{x,y,z},{x,y1,z},{x1,y1,z},north);
        if(faces&South) quad3({x,y,z1},{x1,y,z1},{x1,y1,z1},{x,y1,z1},south);
        if(faces&East) quad3({x1,y,z1},{x1,y,z},{x1,y1,z},{x1,y1,z1},east);
        if(faces&West) quad3({x,y,z},{x,y,z1},{x,y1,z1},{x,y1,z},west);
    }

    void billboardRect(Vec3 center,float width,float height,float y0,Vec3 camRight,Color c,float depth=0.f){
        Vec3 r=normalize(Vec3{camRight.x,0,camRight.z})*(width*0.5f);
        Vec3 f=normalize(cross({0,1,0},r));
        Vec3 off=f*depth;
        Vec3 a=center-r+Vec3{0,y0,0}+off;
        Vec3 b=center+r+Vec3{0,y0,0}+off;
        Vec3 cc=center+r+Vec3{0,y0+height,0}+off;
        Vec3 d=center-r+Vec3{0,y0+height,0}+off;
        quad3(a,b,cc,d,c);
    }

    void rect(Rect q,Color c){
        V2 a{q.x,q.y,c.r,c.g,c.b,c.a},b{q.x+q.w,q.y,c.r,c.g,c.b,c.a},cc{q.x+q.w,q.y+q.h,c.r,c.g,c.b,c.a},d{q.x,q.y+q.h,c.r,c.g,c.b,c.a};
        v2.insert(v2.end(),{a,b,cc,a,cc,d});
    }
    void frame(Rect q,float t,Color c){
        rect({q.x,q.y,q.w,t},c);rect({q.x,q.y+q.h-t,q.w,t},c);rect({q.x,q.y,t,q.h},c);rect({q.x+q.w-t,q.y,t,q.h},c);
    }

    static bool nextUtf8(const std::string& s,size_t& i,char32_t& cp){
        if(i>=s.size())return false;
        unsigned char c=(unsigned char)s[i++];
        if(c<0x80){cp=c;return true;}
        if((c>>5)==0x6 && i<s.size()){cp=((c&0x1f)<<6)|((unsigned char)s[i++]&0x3f);return true;}
        if((c>>4)==0xe && i+1<s.size()){cp=((c&0x0f)<<12)|(((unsigned char)s[i++]&0x3f)<<6)|((unsigned char)s[i++]&0x3f);return true;}
        if((c>>3)==0x1e && i+2<s.size()){cp=((c&7)<<18)|(((unsigned char)s[i++]&0x3f)<<12)|(((unsigned char)s[i++]&0x3f)<<6)|((unsigned char)s[i++]&0x3f);return true;}
        cp='?';return true;
    }

    float textWidth(const std::string& s,float size) const {
        size_t i=0;char32_t cp=0;float x=0,maxx=0;
        while(nextUtf8(s,i,cp)){
            if(cp=='\n'){maxx=std::max(maxx,x);x=0;continue;}
            x += (cp<128?size*0.62f:size*1.02f);
        }
        return std::max(maxx,x);
    }

    void text(float x,float y,const std::string& s,float size,Color color){
        if(fontTex==0)return;
        constexpr float atlas=1024.f,cell=32.f; constexpr int cols=32;
        size_t i=0;char32_t cp=0;float ox=x;
        while(nextUtf8(s,i,cp)){
            if(cp=='\n'){x=ox;y+=size*1.24f;continue;}
            auto it=glyphIndex.find(cp);
            if(it==glyphIndex.end()){ it=glyphIndex.find(U'?'); if(it==glyphIndex.end()){x+=size*0.7f;continue;} }
            int idx=it->second,cx=idx%cols,cy=idx/cols;
            float u0=(cx*cell)/atlas,v0=(cy*cell)/atlas,u1=((cx+1)*cell)/atlas,v1=((cy+1)*cell)/atlas;
            float cw=(cp<128?size*0.72f:size),ch=size;
            float advance=(cp<128?size*0.62f:size*1.02f);
            VT a{x,y,u0,v0,color.r,color.g,color.b,color.a},b{x+cw,y,u1,v0,color.r,color.g,color.b,color.a};
            VT c{x+cw,y+ch,u1,v1,color.r,color.g,color.b,color.a},d{x,y+ch,u0,v1,color.r,color.g,color.b,color.a};
            vt.insert(vt.end(),{a,b,c,a,c,d});x+=advance;
        }
    }
    void textCentered(Rect q,const std::string& s,float size,Color c){
        text(q.x+(q.w-textWidth(s,size))*0.5f,q.y+(q.h-size)*0.5f,s,size,c);
    }

    void flush3D(const Mat4& mvp){
        if(v3.empty())return;
        glEnable(GL_DEPTH_TEST);glDepthMask(GL_TRUE);glDisable(GL_CULL_FACE);
        glUseProgram(prog3);glUniformMatrix4fv(mvpLoc,1,GL_FALSE,mvp.m);
        glBindVertexArray(vao3);glBindBuffer(GL_ARRAY_BUFFER,vbo3);
        glBufferData(GL_ARRAY_BUFFER,GLsizeiptr(v3.size()*sizeof(V3)),nullptr,GL_STREAM_DRAW);
        glBufferSubData(GL_ARRAY_BUFFER,0,GLsizeiptr(v3.size()*sizeof(V3)),v3.data());
        glDrawArrays(GL_TRIANGLES,0,GLsizei(v3.size()));
    }
    void flushUI(){
        glDisable(GL_DEPTH_TEST);glDepthMask(GL_FALSE);
        if(!v2.empty()){
            glUseProgram(prog2);glUniform2f(screenLoc,float(w),float(h));
            glBindVertexArray(vao2);glBindBuffer(GL_ARRAY_BUFFER,vbo2);
            glBufferData(GL_ARRAY_BUFFER,GLsizeiptr(v2.size()*sizeof(V2)),nullptr,GL_STREAM_DRAW);
            glBufferSubData(GL_ARRAY_BUFFER,0,GLsizeiptr(v2.size()*sizeof(V2)),v2.data());
            glDrawArrays(GL_TRIANGLES,0,GLsizei(v2.size()));
        }
        if(!vt.empty()&&fontTex){
            glUseProgram(progText);glUniform2f(textScreenLoc,float(w),float(h));
            glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,fontTex);
            glUniform1i(glGetUniformLocation(progText,"uTex"),0);
            glBindVertexArray(vaoT);glBindBuffer(GL_ARRAY_BUFFER,vboT);
            glBufferData(GL_ARRAY_BUFFER,GLsizeiptr(vt.size()*sizeof(VT)),nullptr,GL_STREAM_DRAW);
            glBufferSubData(GL_ARRAY_BUFFER,0,GLsizeiptr(vt.size()*sizeof(VT)),vt.data());
            glDrawArrays(GL_TRIANGLES,0,GLsizei(vt.size()));
        }
        glDepthMask(GL_TRUE);
    }
    void present(){ eglSwapBuffers(display,surface); }
};

} // namespace fb
