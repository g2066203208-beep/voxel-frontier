#include <android_native_app_glue.h>
#include <android/log.h>
#include <android/native_activity.h>
#include <EGL/egl.h>
#include <GLES3/gl3.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <unordered_set>
#include <vector>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "Faithbound", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "Faithbound", __VA_ARGS__)

namespace fb {

constexpr float PI = 3.14159265358979323846f;
constexpr int WORLD_SIZE = 128;
constexpr int CHUNK_SIZE = 16;
constexpr int CHUNK_CACHE = 64;
constexpr uint32_t SAVE_MAGIC = 0x46423031u; // FB01

struct Color { float r,g,b,a; };
static constexpr Color C_WHITE{0.96f,0.97f,0.93f,1.f};
static constexpr Color C_INK{0.055f,0.065f,0.08f,1.f};
static constexpr Color C_PANEL{0.075f,0.095f,0.12f,0.94f};
static constexpr Color C_GOLD{0.96f,0.72f,0.22f,1.f};
static constexpr Color C_GREEN{0.33f,0.72f,0.38f,1.f};
static constexpr Color C_BLUE{0.27f,0.59f,0.93f,1.f};
static constexpr Color C_RED{0.86f,0.25f,0.25f,1.f};
static constexpr Color C_MUTED{0.48f,0.53f,0.58f,1.f};

struct Rect { float x,y,w,h; };
static bool contains(const Rect& r,float x,float y){ return x>=r.x&&x<=r.x+r.w&&y>=r.y&&y<=r.y+r.h; }
static Color mul(Color c,float f){ return {c.r*f,c.g*f,c.b*f,c.a}; }
static Color mix(Color a,Color b,float t){ return {a.r+(b.r-a.r)*t,a.g+(b.g-a.g)*t,a.b+(b.b-a.b)*t,a.a+(b.a-a.a)*t}; }

struct Vertex { float x,y,r,g,b,a; };

class Renderer {
public:
    EGLDisplay display=EGL_NO_DISPLAY;
    EGLSurface surface=EGL_NO_SURFACE;
    EGLContext context=EGL_NO_CONTEXT;
    int w=1280,h=720;
    bool ready=false;
    GLuint program=0,vbo=0,vao=0;
    std::vector<Vertex> verts;

    bool init(android_app* app){
        if(!app->window) return false;
        const EGLint cfgAttr[]={
            EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT,
            EGL_SURFACE_TYPE,EGL_WINDOW_BIT,
            EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,
            EGL_NONE
        };
        const EGLint ctxAttr[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
        display=eglGetDisplay(EGL_DEFAULT_DISPLAY);
        if(display==EGL_NO_DISPLAY || !eglInitialize(display,nullptr,nullptr)) return false;
        EGLConfig cfg=nullptr; EGLint count=0;
        if(!eglChooseConfig(display,cfgAttr,&cfg,1,&count)||count<1) return false;
        EGLint format=0; eglGetConfigAttrib(display,cfg,EGL_NATIVE_VISUAL_ID,&format);
        ANativeWindow_setBuffersGeometry(app->window,0,0,format);
        surface=eglCreateWindowSurface(display,cfg,app->window,nullptr);
        context=eglCreateContext(display,cfg,EGL_NO_CONTEXT,ctxAttr);
        if(surface==EGL_NO_SURFACE||context==EGL_NO_CONTEXT) return false;
        if(!eglMakeCurrent(display,surface,surface,context)) return false;
        eglQuerySurface(display,surface,EGL_WIDTH,&w);
        eglQuerySurface(display,surface,EGL_HEIGHT,&h);
        eglSwapInterval(display,1);

        const char* vs=R"(#version 300 es
            layout(location=0) in vec2 aPos;
            layout(location=1) in vec4 aColor;
            out vec4 vColor;
            void main(){ gl_Position=vec4(aPos,0.0,1.0); vColor=aColor; }
        )";
        const char* fs=R"(#version 300 es
            precision mediump float;
            in vec4 vColor;
            out vec4 oColor;
            void main(){ oColor=vColor; }
        )";
        auto makeShader=[](GLenum type,const char* src)->GLuint{
            GLuint s=glCreateShader(type); glShaderSource(s,1,&src,nullptr); glCompileShader(s);
            GLint ok=0; glGetShaderiv(s,GL_COMPILE_STATUS,&ok);
            if(!ok){ char log[1024]{}; glGetShaderInfoLog(s,1024,nullptr,log); LOGE("shader: %s",log); }
            return s;
        };
        GLuint sv=makeShader(GL_VERTEX_SHADER,vs), sf=makeShader(GL_FRAGMENT_SHADER,fs);
        program=glCreateProgram(); glAttachShader(program,sv); glAttachShader(program,sf); glLinkProgram(program);
        glDeleteShader(sv); glDeleteShader(sf);
        GLint linked=0; glGetProgramiv(program,GL_LINK_STATUS,&linked);
        if(!linked){ LOGE("program link failed"); return false; }

        glGenVertexArrays(1,&vao); glBindVertexArray(vao);
        glGenBuffers(1,&vbo); glBindBuffer(GL_ARRAY_BUFFER,vbo);
        glEnableVertexAttribArray(0);
        glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)0);
        glEnableVertexAttribArray(1);
        glVertexAttribPointer(1,4,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)(sizeof(float)*2));
        glBindVertexArray(0);

        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
        glDisable(GL_DEPTH_TEST);
        verts.reserve(220000);
        ready=true;
        LOGI("OpenGL ready %dx%d",w,h);
        return true;
    }

    void term(){
        if(display!=EGL_NO_DISPLAY){
            eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);
            if(context!=EGL_NO_CONTEXT) eglDestroyContext(display,context);
            if(surface!=EGL_NO_SURFACE) eglDestroySurface(display,surface);
            eglTerminate(display);
        }
        display=EGL_NO_DISPLAY; surface=EGL_NO_SURFACE; context=EGL_NO_CONTEXT;
        ready=false;
    }

    void begin(Color c){
        verts.clear();
        glViewport(0,0,w,h);
        glClearColor(c.r,c.g,c.b,c.a);
        glClear(GL_COLOR_BUFFER_BIT);
    }
    float nx(float x) const { return x/float(w)*2.f-1.f; }
    float ny(float y) const { return 1.f-y/float(h)*2.f; }
    void push(float x,float y,Color c){ verts.push_back({nx(x),ny(y),c.r,c.g,c.b,c.a}); }
    void tri(float ax,float ay,float bx,float by,float cx,float cy,Color c){
        push(ax,ay,c); push(bx,by,c); push(cx,cy,c);
    }
    void quad(float ax,float ay,float bx,float by,float cx,float cy,float dx,float dy,Color c){
        tri(ax,ay,bx,by,cx,cy,c); tri(ax,ay,cx,cy,dx,dy,c);
    }
    void rect(Rect r,Color c){ quad(r.x,r.y,r.x+r.w,r.y,r.x+r.w,r.y+r.h,r.x,r.y+r.h,c); }
    void frame(Rect r,float t,Color c){
        rect({r.x,r.y,r.w,t},c); rect({r.x,r.y+r.h-t,r.w,t},c);
        rect({r.x,r.y,t,r.h},c); rect({r.x+r.w-t,r.y,t,r.h},c);
    }
    void diamond(float cx,float cy,float hw,float hh,Color c){
        quad(cx,cy-hh,cx+hw,cy,cx,cy+hh,cx-hw,cy,c);
    }
    void line(float x1,float y1,float x2,float y2,float thick,Color c){
        float dx=x2-x1,dy=y2-y1,len=std::sqrt(dx*dx+dy*dy); if(len<0.001f) return;
        float ox=-dy/len*thick*0.5f, oy=dx/len*thick*0.5f;
        quad(x1+ox,y1+oy,x2+ox,y2+oy,x2-ox,y2-oy,x1-ox,y1-oy,c);
    }

    static std::array<uint8_t,7> glyph(char c){
        if(c>='a'&&c<='z') c=char(c-'a'+'A');
        switch(c){
            case 'A': return {14,17,17,31,17,17,17};
            case 'B': return {30,17,17,30,17,17,30};
            case 'C': return {14,17,16,16,16,17,14};
            case 'D': return {28,18,17,17,17,18,28};
            case 'E': return {31,16,16,30,16,16,31};
            case 'F': return {31,16,16,30,16,16,16};
            case 'G': return {14,17,16,23,17,17,15};
            case 'H': return {17,17,17,31,17,17,17};
            case 'I': return {31,4,4,4,4,4,31};
            case 'J': return {7,2,2,2,18,18,12};
            case 'K': return {17,18,20,24,20,18,17};
            case 'L': return {16,16,16,16,16,16,31};
            case 'M': return {17,27,21,21,17,17,17};
            case 'N': return {17,25,21,19,17,17,17};
            case 'O': return {14,17,17,17,17,17,14};
            case 'P': return {30,17,17,30,16,16,16};
            case 'Q': return {14,17,17,17,21,18,13};
            case 'R': return {30,17,17,30,20,18,17};
            case 'S': return {15,16,16,14,1,1,30};
            case 'T': return {31,4,4,4,4,4,4};
            case 'U': return {17,17,17,17,17,17,14};
            case 'V': return {17,17,17,17,17,10,4};
            case 'W': return {17,17,17,21,21,21,10};
            case 'X': return {17,17,10,4,10,17,17};
            case 'Y': return {17,17,10,4,4,4,4};
            case 'Z': return {31,1,2,4,8,16,31};
            case '0': return {14,17,19,21,25,17,14};
            case '1': return {4,12,4,4,4,4,14};
            case '2': return {14,17,1,2,4,8,31};
            case '3': return {30,1,1,14,1,1,30};
            case '4': return {2,6,10,18,31,2,2};
            case '5': return {31,16,16,30,1,1,30};
            case '6': return {14,16,16,30,17,17,14};
            case '7': return {31,1,2,4,8,8,8};
            case '8': return {14,17,17,14,17,17,14};
            case '9': return {14,17,17,15,1,1,14};
            case '-': return {0,0,0,31,0,0,0};
            case ':': return {0,4,4,0,4,4,0};
            case '.': return {0,0,0,0,0,6,6};
            case '/': return {1,2,2,4,8,8,16};
            case '+': return {0,4,4,31,4,4,0};
            default: return {0,0,0,0,0,0,0};
        }
    }

    void text(float x,float y,const std::string& s,float scale,Color c){
        float ox=x;
        for(char ch:s){
            if(ch=='\n'){ y+=8.f*scale; x=ox; continue; }
            if(ch==' '){ x+=4.f*scale; continue; }
            auto g=glyph(ch);
            for(int row=0;row<7;row++) for(int col=0;col<5;col++){
                if(g[row]&(1u<<(4-col))) rect({x+col*scale,y+row*scale,scale,scale},c);
            }
            x+=6.f*scale;
        }
    }
    float textWidth(const std::string& s,float scale) const {
        size_t n=0,maxn=0;
        for(char c:s){ if(c=='\n'){ maxn=std::max(maxn,n); n=0; } else n++; }
        maxn=std::max(maxn,n); return float(maxn)*6.f*scale;
    }
    void centeredText(Rect r,const std::string& s,float scale,Color c){
        float tw=textWidth(s,scale);
        text(r.x+(r.w-tw)*0.5f,r.y+(r.h-7.f*scale)*0.5f,s,scale,c);
    }
    void flush(){
        if(verts.empty()) return;
        glUseProgram(program); glBindVertexArray(vao); glBindBuffer(GL_ARRAY_BUFFER,vbo);
        glBufferData(GL_ARRAY_BUFFER,GLsizeiptr(verts.size()*sizeof(Vertex)),verts.data(),GL_STREAM_DRAW);
        glDrawArrays(GL_TRIANGLES,0,GLsizei(verts.size()));
        glBindVertexArray(0);
    }
    void present(){ flush(); eglSwapBuffers(display,surface); }
};

static uint32_t hash32(uint64_t x){
    x ^= x >> 33; x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return uint32_t(x ^ (x>>32));
}
static float h01(uint64_t seed,int x,int y,int salt=0){
    uint64_t v=seed ^ (uint64_t(uint32_t(x))*0x9E3779B185EBCA87ULL)
                     ^ (uint64_t(uint32_t(y))*0xC2B2AE3D27D4EB4FULL)
                     ^ (uint64_t(uint32_t(salt))*0x165667B19E3779F9ULL);
    return float(hash32(v)&0x00ffffffu)/float(0x01000000u);
}
static float smoothstep01(float t){ return t*t*(3.f-2.f*t); }
static float valueNoise(uint64_t seed,float x,float y,int salt){
    int x0=int(std::floor(x)), y0=int(std::floor(y));
    float tx=smoothstep01(x-float(x0)), ty=smoothstep01(y-float(y0));
    float a=h01(seed,x0,y0,salt), b=h01(seed,x0+1,y0,salt);
    float c=h01(seed,x0,y0+1,salt), d=h01(seed,x0+1,y0+1,salt);
    float ab=a+(b-a)*tx, cd=c+(d-c)*tx;
    return ab+(cd-ab)*ty;
}

enum class Terrain : uint8_t { Void, Grass, Forest, Water, Sand, Rock, Cave, Ore };
struct Tile { Terrain t=Terrain::Void; uint8_t elev=0; };

struct Chunk {
    bool valid=false;
    int layer=0,cx=0,cy=0;
    uint64_t stamp=0;
    std::array<uint8_t,CHUNK_SIZE*CHUNK_SIZE> type{};
    std::array<uint8_t,CHUNK_SIZE*CHUNK_SIZE> elev{};
};

class World {
public:
    uint64_t seed=1;
    uint64_t stamp=1;
    std::array<Chunk,CHUNK_CACHE> cache{};

    void reset(uint64_t s){ seed=s?s:1; stamp=1; for(auto& c:cache)c.valid=false; }

    Tile generate(int x,int y,int layer) const {
        if(x<0||y<0||x>=WORLD_SIZE||y>=WORLD_SIZE) return {Terrain::Void,0};
        const int cx=WORLD_SIZE/2, cy=WORLD_SIZE/2;
        float ds=std::sqrt(float((x-cx)*(x-cx)+(y-cy)*(y-cy)));
        if(layer==0){
            if(ds<5.f) return {Terrain::Grass,1};
            float n=0.62f*valueNoise(seed,x*0.045f,y*0.045f,1)+0.38f*valueNoise(seed,x*0.095f,y*0.095f,2);
            float b=valueNoise(seed,x*0.035f,y*0.035f,3);
            if(n<0.27f) return {Terrain::Water,0};
            uint8_t e=n>0.72f?2:(n>0.47f?1:0);
            if(n<0.33f) return {Terrain::Sand,e};
            if(b>0.64f) return {Terrain::Forest,e};
            if(n>0.80f) return {Terrain::Rock,e};
            return {Terrain::Grass,e};
        }
        if(layer<0){
            float n=valueNoise(seed+uint64_t(-layer)*991u,x*0.105f,y*0.105f,7);
            if(n<0.17f) return {Terrain::Rock,0};
            float ore=h01(seed+77,x,y,layer*13);
            return {ore>0.86f?Terrain::Ore:Terrain::Cave,0};
        }
        // upper layer: sparse raised structures/plateaus near the central shrine
        if(layer==1 && ds<3.2f) return {Terrain::Grass,0};
        return {Terrain::Void,0};
    }

    Chunk& getChunk(int cx,int cy,int layer){
        stamp++;
        for(auto& c:cache) if(c.valid&&c.cx==cx&&c.cy==cy&&c.layer==layer){ c.stamp=stamp; return c; }
        Chunk* victim=&cache[0];
        for(auto& c:cache){ if(!c.valid){ victim=&c; break; } if(c.stamp<victim->stamp) victim=&c; }
        victim->valid=true; victim->cx=cx; victim->cy=cy; victim->layer=layer; victim->stamp=stamp;
        for(int ly=0;ly<CHUNK_SIZE;ly++) for(int lx=0;lx<CHUNK_SIZE;lx++){
            Tile t=generate(cx*CHUNK_SIZE+lx,cy*CHUNK_SIZE+ly,layer);
            int i=ly*CHUNK_SIZE+lx; victim->type[i]=uint8_t(t.t); victim->elev[i]=t.elev;
        }
        return *victim;
    }

    Tile tile(int x,int y,int layer){
        if(x<0||y<0||x>=WORLD_SIZE||y>=WORLD_SIZE) return {Terrain::Void,0};
        int cx=x/CHUNK_SIZE,cy=y/CHUNK_SIZE,lx=x%CHUNK_SIZE,ly=y%CHUNK_SIZE;
        Chunk& c=getChunk(cx,cy,layer); int i=ly*CHUNK_SIZE+lx;
        return {Terrain(c.type[i]),c.elev[i]};
    }

    int resourceAt(int x,int y,int layer) const {
        uint32_t r=hash32(seed ^ uint64_t(x*73856093) ^ uint64_t(y*19349663) ^ uint64_t((layer+5)*83492791));
        int p=int(r%100);
        Tile t=generate(x,y,layer);
        if(layer==0){
            if(t.t==Terrain::Forest && p<55) return 1; // tree
            if((t.t==Terrain::Rock||t.t==Terrain::Grass) && p<8) return 2; // stone
            if(t.t==Terrain::Grass && p>=8&&p<14) return 3; // berries
        }else if(layer<0){
            if(t.t==Terrain::Ore && p<70) return 4;
            if(t.t==Terrain::Cave && p<8) return 2;
        }
        return 0;
    }
};

enum class Faith : int32_t { Established=0, Newborn=1, Godless=2 };
enum class Screen { Splash, Main, SaveManager, FaithSelect, CharacterCreate, Settings, Game, Pause, Death, About };

struct SaveData {
    uint32_t magic=SAVE_MAGIC;
    uint32_t version=1;
    uint64_t seed=1;
    int32_t faith=0, body=0, skin=0, hair=0, outfit=0;
    float px=float(WORLD_SIZE/2), py=float(WORLD_SIZE/2);
    int32_t layer=0;
    float hp=100, hunger=100, stamina=100, faithPower=100, dayClock=0;
    int32_t day=1;
    uint32_t wood=0,stone=0,food=3;
    uint32_t checksum=0;
};

static uint32_t checksum(const SaveData& s){
    const uint8_t* p=reinterpret_cast<const uint8_t*>(&s);
    uint32_t h=2166136261u;
    for(size_t i=0;i<sizeof(SaveData)-sizeof(uint32_t);i++){ h^=p[i]; h*=16777619u; }
    return h;
}

struct InputState {
    int joyId=-1;
    float joyBaseX=0,joyBaseY=0,joyX=0,joyY=0;
    bool tap=false;
    float tapX=0,tapY=0;
    bool back=false;
};

class Game {
public:
    android_app* app=nullptr;
    Renderer r;
    World world;
    Screen screen=Screen::Splash;
    Screen returnFromSaves=Screen::Main;
    InputState in;
    SaveData save{};
    std::array<bool,3> hasSlot{false,false,false};
    std::array<SaveData,3> slots{};
    int slot=0;
    int selectedFaith=0;
    int body=0,skin=1,hair=0,outfit=0;
    int rotation=0;
    float splashTime=0;
    float simAccumulator=0;
    float autosaveTimer=0;
    float toastTimer=0;
    std::string toast;
    bool pixelGrid=true;
    std::unordered_set<uint32_t> harvested;

    explicit Game(android_app* a):app(a){ refreshSlots(); }

    float S() const { return std::min(float(r.w)/1280.f,float(r.h)/720.f); }
    float X(float base) const { return base*S()+(r.w-1280.f*S())*0.5f; }
    float Y(float base) const { return base*S()+(r.h-720.f*S())*0.5f; }
    Rect R(float x,float y,float w,float h) const { return {X(x),Y(y),w*S(),h*S()}; }

    std::string savePath(int i) const {
        std::string p=app->activity->internalDataPath?app->activity->internalDataPath:"";
        return p+"/faithbound_slot"+std::to_string(i)+".sav";
    }
    bool readSlot(int i,SaveData& out){
        FILE* f=std::fopen(savePath(i).c_str(),"rb"); if(!f) return false;
        SaveData t{}; size_t n=std::fread(&t,1,sizeof(t),f); std::fclose(f);
        if(n!=sizeof(t)||t.magic!=SAVE_MAGIC||t.version!=1) return false;
        uint32_t cs=t.checksum; t.checksum=0;
        if(checksum(t)!=cs) return false;
        t.checksum=cs; out=t; return true;
    }
    void refreshSlots(){ for(int i=0;i<3;i++) hasSlot[i]=readSlot(i,slots[i]); }
    void writeSave(){
        save.checksum=0; save.checksum=checksum(save);
        FILE* f=std::fopen(savePath(slot).c_str(),"wb");
        if(f){ std::fwrite(&save,1,sizeof(save),f); std::fclose(f); hasSlot[slot]=true; slots[slot]=save; }
    }
    void deleteSave(int i){ std::remove(savePath(i).c_str()); hasSlot[i]=false; }

    void newWorld(){
        save=SaveData{};
        auto now=uint64_t(std::chrono::high_resolution_clock::now().time_since_epoch().count());
        save.seed=now ^ (uint64_t(slot+1)*0x9E3779B97F4A7C15ULL);
        save.faith=selectedFaith; save.body=body; save.skin=skin; save.hair=hair; save.outfit=outfit;
        save.px=float(WORLD_SIZE/2); save.py=float(WORLD_SIZE/2);
        save.faithPower=selectedFaith==0?100.f:(selectedFaith==1?30.f:0.f);
        save.food=3;
        rotation=0; harvested.clear(); world.reset(save.seed); screen=Screen::Game;
        toast="WORLD AWAKENS"; toastTimer=2.5f; writeSave();
    }
    void loadWorld(int i){
        SaveData d{}; if(!readSlot(i,d)) return;
        slot=i; save=d; selectedFaith=save.faith; body=save.body; skin=save.skin; hair=save.hair; outfit=save.outfit;
        world.reset(save.seed); harvested.clear(); screen=Screen::Game; toast="WELCOME BACK"; toastTimer=1.8f;
    }

    void onBack(){
        switch(screen){
            case Screen::Game: screen=Screen::Pause; writeSave(); break;
            case Screen::Pause: screen=Screen::Game; break;
            case Screen::SaveManager: case Screen::FaithSelect: case Screen::Settings:
            case Screen::About: screen=Screen::Main; break;
            case Screen::CharacterCreate: screen=Screen::FaithSelect; break;
            case Screen::Death: screen=Screen::Main; break;
            case Screen::Main: ANativeActivity_finish(app->activity); break;
            default: screen=Screen::Main; break;
        }
    }

    bool button(Rect rc,const std::string& label,bool enabled=true,Color accent=C_BLUE){
        r.rect(rc,enabled?mix(C_PANEL,accent,0.16f):mul(C_PANEL,0.75f));
        r.frame(rc,2.f*S(),enabled?accent:C_MUTED);
        float sc=std::max(1.4f,2.5f*S());
        r.centeredText(rc,label,sc,enabled?C_WHITE:C_MUTED);
        if(enabled&&in.tap&&contains(rc,in.tapX,in.tapY)){ in.tap=false; return true; }
        return false;
    }
    void title(const std::string& t,const std::string& sub=""){
        float sc=std::max(2.f,5.f*S());
        Rect rr=R(170,70,940,70);
        r.centeredText(rr,t,sc,C_GOLD);
        if(!sub.empty()) r.centeredText(R(170,132,940,30),sub,std::max(1.2f,2.f*S()),C_WHITE);
    }
    void panel(Rect rc){ r.rect(rc,C_PANEL); r.frame(rc,2.f*S(),{0.22f,0.27f,0.32f,1}); }

    void renderSplash(){
        r.begin({0.025f,0.035f,0.055f,1});
        for(int i=0;i<18;i++){
            float x=float((i*137)%1280), y=float((i*79)%720);
            float pulse=0.5f+0.5f*std::sin(splashTime*1.6f+i);
            r.rect(R(x,y,3,3),{0.4f,0.7f,1.f,0.35f+0.45f*pulse});
        }
        r.centeredText(R(90,230,1100,100),"FAITHBOUND",std::max(3.f,8.f*S()),C_GOLD);
        r.centeredText(R(180,340,920,40),"A LAYERED WORLD",std::max(1.5f,3.f*S()),C_WHITE);
        r.centeredText(R(180,610,920,30),"TAP TO BEGIN",std::max(1.2f,2.f*S()),C_MUTED);
        if(in.tap||splashTime>2.6f){ in.tap=false; screen=Screen::Main; }
    }

    void renderMain(){
        r.begin({0.045f,0.075f,0.075f,1});
        // simple pixel landscape
        r.rect(R(0,490,1280,230),{0.13f,0.23f,0.14f,1});
        for(int i=0;i<25;i++){
            float x=R(float(i*55-20),0,0,0).x;
            float b=Y(505)-float((i%3)*10)*S();
            r.rect({x,b,9*S(),50*S()},{0.24f,0.15f,0.08f,1});
            r.tri(x-25*S(),b+6*S(),x+5*S(),b-65*S(),x+35*S(),b+6*S(),{0.08f,0.26f,0.12f,1});
        }
        title("FAITHBOUND","MOBILE RPG SYSTEMS PROTOTYPE");
        bool any=hasSlot[0]||hasSlot[1]||hasSlot[2];
        if(button(R(470,235,340,62),"CONTINUE",any,C_GREEN)){
            for(int i=0;i<3;i++) if(hasSlot[i]){ loadWorld(i); break; }
        }
        if(button(R(470,315,340,62),"NEW WORLD",true,C_GOLD)){ returnFromSaves=Screen::Main; screen=Screen::SaveManager; }
        if(button(R(470,395,340,62),"LOAD GAME",any,C_BLUE)){ returnFromSaves=Screen::Main; screen=Screen::SaveManager; }
        if(button(R(470,475,340,62),"SETTINGS",true,C_BLUE)) screen=Screen::Settings;
        if(button(R(470,555,340,62),"ABOUT",true,C_MUTED)) screen=Screen::About;
        r.text(X(26),Y(680),"ALPHA 0.1  C++20 / GLES3",std::max(1.f,1.7f*S()),C_MUTED);
    }

    std::string faithName(int f) const { return f==0?"ESTABLISHED GOD":(f==1?"NEWBORN GOD":"GODLESS"); }

    void renderSaveManager(){
        r.begin({0.045f,0.055f,0.07f,1});
        title("SAVE SLOTS","CHOOSE A WORLD SLOT");
        refreshSlots();
        for(int i=0;i<3;i++){
            Rect rc=R(260,205+i*135,760,105);
            panel(rc);
            r.text(rc.x+24*S(),rc.y+18*S(),"SLOT "+std::to_string(i+1),std::max(1.3f,2.2f*S()),C_GOLD);
            if(hasSlot[i]){
                r.text(rc.x+24*S(),rc.y+50*S(),"DAY "+std::to_string(slots[i].day)+"  "+faithName(slots[i].faith),
                       std::max(1.f,1.7f*S()),C_WHITE);
                Rect play{rc.x+rc.w-190*S(),rc.y+22*S(),155*S(),55*S()};
                if(button(play,"LOAD",true,C_GREEN)){ loadWorld(i); return; }
                Rect del{rc.x+rc.w-355*S(),rc.y+22*S(),145*S(),55*S()};
                if(button(del,"DELETE",true,C_RED)){ deleteSave(i); refreshSlots(); }
            }else{
                r.text(rc.x+24*S(),rc.y+54*S(),"EMPTY",std::max(1.f,1.8f*S()),C_MUTED);
                Rect create{rc.x+rc.w-190*S(),rc.y+22*S(),155*S(),55*S()};
                if(button(create,"CREATE",true,C_GOLD)){ slot=i; screen=Screen::FaithSelect; }
            }
        }
        if(button(R(35,625,190,55),"BACK",true,C_MUTED)) screen=Screen::Main;
    }

    void renderFaith(){
        r.begin({0.04f,0.055f,0.075f,1});
        title("CHOOSE YOUR FAITH","THIS CHANGES DEATH AND REBIRTH");
        const std::array<std::string,3> names={"ESTABLISHED GOD","NEWBORN GOD","GODLESS"};
        const std::array<std::string,3> desc={"TEMPLE / SAFE REBIRTH","START FROM NOTHING / REBIRTH","ONE LIFE / NO REBIRTH"};
        const std::array<Color,3> cols={C_BLUE,C_GOLD,C_RED};
        for(int i=0;i<3;i++){
            Rect rc=R(105+i*365,230,335,250);
            r.rect(rc,i==selectedFaith?mix(C_PANEL,cols[i],0.25f):C_PANEL);
            r.frame(rc,(i==selectedFaith?4.f:2.f)*S(),cols[i]);
            r.centeredText({rc.x+10*S(),rc.y+28*S(),rc.w-20*S(),50*S()},names[i],std::max(1.2f,2.1f*S()),cols[i]);
            r.centeredText({rc.x+15*S(),rc.y+105*S(),rc.w-30*S(),50*S()},desc[i],std::max(1.f,1.45f*S()),C_WHITE);
            if(in.tap&&contains(rc,in.tapX,in.tapY)){ selectedFaith=i; in.tap=false; }
        }
        if(button(R(760,560,300,62),"CONTINUE",true,C_GREEN)) screen=Screen::CharacterCreate;
        if(button(R(220,560,220,62),"BACK",true,C_MUTED)) screen=Screen::SaveManager;
    }

    Color skinColor(int i) const {
        static const Color v[6]={{0.98f,0.82f,0.65f,1},{0.89f,0.69f,0.50f,1},{0.72f,0.50f,0.34f,1},
                                 {0.53f,0.34f,0.23f,1},{0.36f,0.22f,0.16f,1},{0.95f,0.73f,0.60f,1}};
        return v[i%6];
    }
    Color outfitColor(int i) const {
        static const Color v[6]={{0.18f,0.45f,0.72f,1},{0.42f,0.65f,0.26f,1},{0.68f,0.25f,0.20f,1},
                                 {0.48f,0.30f,0.64f,1},{0.72f,0.52f,0.20f,1},{0.20f,0.55f,0.52f,1}};
        return v[i%6];
    }
    Color hairColor(int i) const {
        static const Color v[6]={{0.12f,0.08f,0.05f,1},{0.32f,0.17f,0.08f,1},{0.75f,0.53f,0.20f,1},
                                 {0.12f,0.12f,0.13f,1},{0.58f,0.22f,0.12f,1},{0.80f,0.78f,0.70f,1}};
        return v[i%6];
    }
    void drawPerson(float cx,float cy,float scale,int sk,int hr,int out){
        Color sc=skinColor(sk),hc=hairColor(hr),oc=outfitColor(out);
        r.rect({cx-6*scale,cy-13*scale,12*scale,12*scale},sc);
        r.rect({cx-7*scale,cy-15*scale,14*scale,4*scale},hc);
        if(hr%3==1) r.rect({cx+5*scale,cy-11*scale,4*scale,8*scale},hc);
        if(hr%3==2) r.rect({cx-9*scale,cy-12*scale,4*scale,9*scale},hc);
        r.rect({cx-8*scale,cy-1*scale,16*scale,17*scale},oc);
        r.rect({cx-10*scale,cy+2*scale,3*scale,12*scale},sc);
        r.rect({cx+7*scale,cy+2*scale,3*scale,12*scale},sc);
        r.rect({cx-7*scale,cy+16*scale,5*scale,12*scale},mul(oc,0.7f));
        r.rect({cx+2*scale,cy+16*scale,5*scale,12*scale},mul(oc,0.7f));
    }
    void renderCharacter(){
        r.begin({0.05f,0.065f,0.075f,1});
        title("CREATE YOUR WANDERER","APPEARANCE CAN CHANGE LATER");
        Rect preview=R(135,205,360,385); panel(preview);
        drawPerson(preview.x+preview.w*0.5f,preview.y+preview.h*0.48f,5.0f*S(),skin,hair,outfit);
        r.centeredText({preview.x,preview.y+preview.h-55*S(),preview.w,35*S()},faithName(selectedFaith),std::max(1.f,1.5f*S()),C_GOLD);

        float bx=600,by=225;
        r.text(X(bx),Y(by),"BODY",std::max(1.2f,2.f*S()),C_WHITE);
        if(button(R(bx+180,by-15,220,50),body==0?"TYPE A":"TYPE B",true,C_BLUE)) body=(body+1)%2;
        r.text(X(bx),Y(by+80),"SKIN",std::max(1.2f,2.f*S()),C_WHITE);
        if(button(R(bx+180,by+65,220,50),"SHADE "+std::to_string(skin+1),true,C_BLUE)) skin=(skin+1)%6;
        r.text(X(bx),Y(by+160),"HAIR",std::max(1.2f,2.f*S()),C_WHITE);
        if(button(R(bx+180,by+145,220,50),"STYLE "+std::to_string(hair+1),true,C_BLUE)) hair=(hair+1)%6;
        r.text(X(bx),Y(by+240),"OUTFIT",std::max(1.2f,2.f*S()),C_WHITE);
        if(button(R(bx+180,by+225,220,50),"SET "+std::to_string(outfit+1),true,C_BLUE)) outfit=(outfit+1)%6;
        if(button(R(630,575,230,58),"RANDOMIZE",true,C_GOLD)){
            uint32_t h=hash32(uint64_t(std::chrono::high_resolution_clock::now().time_since_epoch().count()));
            body=h%2; skin=(h>>3)%6; hair=(h>>7)%6; outfit=(h>>11)%6;
        }
        if(button(R(890,575,230,58),"ENTER WORLD",true,C_GREEN)) newWorld();
        if(button(R(35,625,180,55),"BACK",true,C_MUTED)) screen=Screen::FaithSelect;
    }

    void renderSettings(){
        r.begin({0.045f,0.055f,0.07f,1}); title("SETTINGS","PROTOTYPE OPTIONS");
        panel(R(330,210,620,330));
        r.text(X(390),Y(270),"PIXEL TILE OUTLINES",std::max(1.2f,2.f*S()),C_WHITE);
        if(button(R(720,245,170,50),pixelGrid?"ON":"OFF",true,pixelGrid?C_GREEN:C_MUTED)) pixelGrid=!pixelGrid;
        r.text(X(390),Y(350),"SIMULATION",std::max(1.2f,2.f*S()),C_WHITE);
        r.text(X(720),Y(350),"FIXED 60 HZ",std::max(1.1f,1.8f*S()),C_GREEN);
        r.text(X(390),Y(430),"WORLD STREAMING",std::max(1.2f,2.f*S()),C_WHITE);
        r.text(X(720),Y(430),"CHUNK CACHE",std::max(1.1f,1.8f*S()),C_GREEN);
        if(button(R(35,625,180,55),"BACK",true,C_MUTED)) screen=Screen::Main;
    }

    void renderAbout(){
        r.begin({0.045f,0.055f,0.07f,1}); title("ABOUT","FAITHBOUND ALPHA 0.1");
        panel(R(235,200,810,350));
        r.text(X(300),Y(250),"NATIVE ANDROID / C++20 / OPENGL ES 3",std::max(1.f,1.75f*S()),C_WHITE);
        r.text(X(300),Y(305),"SEEDED FINITE WORLD / LAYERED TILES",std::max(1.f,1.75f*S()),C_WHITE);
        r.text(X(300),Y(360),"CHUNK CACHE / VISIBLE TILE CULLING",std::max(1.f,1.75f*S()),C_WHITE);
        r.text(X(300),Y(415),"FAITH / REBIRTH / SURVIVAL / SAVES",std::max(1.f,1.75f*S()),C_WHITE);
        r.text(X(300),Y(470),"VERTICAL SLICE - CONTENT WILL EXPAND",std::max(1.f,1.75f*S()),C_GOLD);
        if(button(R(35,625,180,55),"BACK",true,C_MUTED)) screen=Screen::Main;
    }

    Color terrainColor(Terrain t) const {
        switch(t){
            case Terrain::Grass:return {0.27f,0.57f,0.24f,1};
            case Terrain::Forest:return {0.18f,0.43f,0.18f,1};
            case Terrain::Water:return {0.13f,0.42f,0.68f,1};
            case Terrain::Sand:return {0.67f,0.57f,0.32f,1};
            case Terrain::Rock:return {0.34f,0.37f,0.37f,1};
            case Terrain::Cave:return {0.22f,0.20f,0.22f,1};
            case Terrain::Ore:return {0.30f,0.26f,0.35f,1};
            default:return {0.02f,0.025f,0.03f,1};
        }
    }

    void worldToScreen(float wx,float wy,int elev,float& sx,float& sy) const {
        float dx=wx-save.px,dy=wy-save.py;
        float rx=dx,ry=dy;
        switch(rotation&3){
            case 1: rx=dy; ry=-dx; break;
            case 2: rx=-dx; ry=-dy; break;
            case 3: rx=-dy; ry=dx; break;
            default: break;
        }
        float tw=54.f*S(), th=27.f*S();
        sx=r.w*0.5f+(rx-ry)*tw*0.5f;
        sy=r.h*0.46f+(rx+ry)*th*0.5f-float(elev)*13.f*S();
    }

    uint32_t keyAt(int x,int y,int layer) const {
        return uint32_t((layer+8)&15)<<28 | uint32_t(y&0x3fff)<<14 | uint32_t(x&0x3fff);
    }

    void drawTile(int x,int y,Tile t){
        if(t.t==Terrain::Void) return;
        float sx,sy; worldToScreen(float(x)+0.5f,float(y)+0.5f,t.elev,sx,sy);
        float hw=27.f*S(),hh=13.5f*S(),side=12.f*S();
        Color top=terrainColor(t.t);
        if(save.layer<0) top=mix(top,{0.12f,0.13f,0.18f,1},0.34f);
        if(t.elev>0 && save.layer==0){
            float d=float(t.elev)*side;
            r.quad(sx-hw,sy,sx,sy+hh,sx,sy+hh+d,sx-hw,sy+d,mul(top,0.55f));
            r.quad(sx+hw,sy,sx,sy+hh,sx,sy+hh+d,sx+hw,sy+d,mul(top,0.68f));
        }
        r.diamond(sx,sy,hw,hh,top);
        if(pixelGrid) {
            r.line(sx-hw,sy,sx,sy-hh,1.f*S(),mul(top,0.6f));
            r.line(sx,sy-hh,sx+hw,sy,1.f*S(),mul(top,0.6f));
        }

        int res=world.resourceAt(x,y,save.layer);
        if(harvested.count(keyAt(x,y,save.layer))) res=0;
        float by=sy-hh-2*S();
        if(res==1){ // tree
            r.rect({sx-3*S(),by-22*S(),6*S(),24*S()},{0.34f,0.20f,0.09f,1});
            r.rect({sx-12*S(),by-39*S(),24*S(),18*S()},{0.09f,0.34f,0.13f,1});
            r.rect({sx-8*S(),by-48*S(),16*S(),14*S()},{0.12f,0.43f,0.16f,1});
        } else if(res==2){
            r.rect({sx-8*S(),by-10*S(),16*S(),10*S()},{0.50f,0.52f,0.52f,1});
            r.rect({sx-3*S(),by-15*S(),10*S(),7*S()},{0.62f,0.63f,0.63f,1});
        } else if(res==3){
            r.rect({sx-10*S(),by-8*S(),20*S(),9*S()},{0.10f,0.38f,0.13f,1});
            r.rect({sx-4*S(),by-12*S(),4*S(),4*S()},{0.78f,0.18f,0.24f,1});
            r.rect({sx+4*S(),by-9*S(),4*S(),4*S()},{0.78f,0.18f,0.24f,1});
        } else if(res==4){
            r.tri(sx-9*S(),by,sx,by-23*S(),sx+3*S(),by,{0.30f,0.78f,0.95f,1});
            r.tri(sx-2*S(),by,sx+8*S(),by-16*S(),sx+11*S(),by,{0.60f,0.30f,0.92f,1});
        }
    }

    void drawShrine(){
        if(save.faith==int(Faith::Godless)||save.layer!=0) return;
        float sx,sy; worldToScreen(float(WORLD_SIZE/2)+0.5f,float(WORLD_SIZE/2)-1.5f,1,sx,sy);
        r.rect({sx-20*S(),sy-42*S(),40*S(),30*S()},{0.56f,0.56f,0.50f,1});
        r.rect({sx-7*S(),sy-70*S(),14*S(),30*S()},{0.70f,0.68f,0.60f,1});
        float pulse=0.65f+0.35f*std::sin(save.dayClock*2.f);
        r.frame({sx-21*S(),sy-84*S(),42*S(),42*S()},3*S(),{1.f,0.72f,0.16f,pulse});
    }

    void renderWorld(){
        Color sky=save.layer<0?Color{0.025f,0.03f,0.045f,1}:Color{0.10f,0.18f,0.20f,1};
        r.begin(sky);
        struct Item{int x,y;float order;Tile t;};
        std::vector<Item> items; items.reserve(900);
        int pcx=int(save.px),pcy=int(save.py);
        const int rad=15;
        for(int y=pcy-rad;y<=pcy+rad;y++) for(int x=pcx-rad;x<=pcx+rad;x++){
            Tile t=world.tile(x,y,save.layer); if(t.t==Terrain::Void) continue;
            float sx,sy; worldToScreen(float(x)+0.5f,float(y)+0.5f,t.elev,sx,sy);
            if(sx<-90*S()||sx>r.w+90*S()||sy<-120*S()||sy>r.h+120*S()) continue;
            items.push_back({x,y,sy,t});
        }
        std::sort(items.begin(),items.end(),[](const Item&a,const Item&b){return a.order<b.order;});
        for(const auto& it:items) drawTile(it.x,it.y,it.t);
        drawShrine();

        Tile pt=world.tile(int(save.px),int(save.py),save.layer);
        float psx,psy; worldToScreen(save.px,save.py,pt.elev,psx,psy);
        drawPerson(psx,psy-18*S(),1.6f*S(),save.skin,save.hair,save.outfit);

        // HUD
        panel(R(18,16,330,105));
        auto bar=[&](float x,float y,float value,Color c,const std::string& label){
            r.text(X(x),Y(y-2),label,std::max(0.9f,1.35f*S()),C_WHITE);
            r.rect(R(x+72,y,220,17),{0.12f,0.13f,0.14f,1});
            r.rect(R(x+74,y+2,216*std::clamp(value,0.f,100.f)/100.f,13),c);
        };
        bar(34,35,save.hp,C_RED,"HP");
        bar(34,64,save.hunger,C_GOLD,"FOOD");
        bar(34,93,save.stamina,C_GREEN,"STA");

        panel(R(955,16,305,110));
        r.text(X(975),Y(34),"DAY "+std::to_string(save.day),std::max(1.1f,1.8f*S()),C_WHITE);
        r.text(X(975),Y(66),"Z "+std::to_string(save.layer)+"  ROT "+std::to_string(rotation*90),
               std::max(1.f,1.55f*S()),C_BLUE);
        r.text(X(975),Y(96),faithName(save.faith),std::max(0.85f,1.25f*S()),C_GOLD);

        panel(R(442,644,396,62));
        r.text(X(458),Y(660),"WOOD "+std::to_string(save.wood)+"   STONE "+std::to_string(save.stone)+"   FOOD "+std::to_string(save.food),
               std::max(0.9f,1.35f*S()),C_WHITE);

        // joystick base
        float jx=in.joyId>=0?in.joyBaseX:X(105), jy=in.joyId>=0?in.joyBaseY:Y(605);
        r.rect({jx-58*S(),jy-58*S(),116*S(),116*S()},{0.05f,0.06f,0.07f,0.45f});
        r.frame({jx-58*S(),jy-58*S(),116*S(),116*S()},2*S(),{0.7f,0.75f,0.78f,0.45f});
        r.rect({jx+in.joyX*38*S()-22*S(),jy+in.joyY*38*S()-22*S(),44*S(),44*S()},{0.65f,0.72f,0.76f,0.65f});

        if(button(R(1080,540,165,58),"ACTION",true,C_GOLD)) gather();
        if(button(R(1080,610,165,58),"EAT",save.food>0,C_GREEN)) eat();
        if(button(R(895,610,150,58),save.layer<0?"UP":"DIG",true,C_BLUE)) changeLayer();
        if(button(R(895,540,150,58),"ROTATE",true,C_BLUE)){ rotation=(rotation+1)&3; toast="VIEW ROTATED"; toastTimer=1.f; }
        if(button(R(1170,145,78,48),"PAUSE",true,C_MUTED)){ screen=Screen::Pause; writeSave(); }

        if(toastTimer>0){
            Rect tr=R(420,150,440,48); r.rect(tr,{0.03f,0.04f,0.05f,0.83f}); r.frame(tr,2*S(),C_GOLD);
            r.centeredText(tr,toast,std::max(1.f,1.7f*S()),C_WHITE);
        }
    }

    void gather(){
        int bx=int(std::floor(save.px)), by=int(std::floor(save.py));
        int best=0,bx2=bx,by2=by; float bd=99;
        for(int y=by-1;y<=by+1;y++) for(int x=bx-1;x<=bx+1;x++){
            int res=world.resourceAt(x,y,save.layer);
            if(!res||harvested.count(keyAt(x,y,save.layer))) continue;
            float dx=(x+0.5f)-save.px,dy=(y+0.5f)-save.py,d=dx*dx+dy*dy;
            if(d<bd){bd=d;best=res;bx2=x;by2=y;}
        }
        if(!best){ toast="NOTHING TO GATHER"; toastTimer=1.2f; return; }
        harvested.insert(keyAt(bx2,by2,save.layer));
        if(best==1){ save.wood+=3; toast="+3 WOOD"; }
        else if(best==2){ save.stone+=2; toast="+2 STONE"; }
        else if(best==3){ save.food+=2; toast="+2 FOOD"; }
        else if(best==4){ save.stone+=4; toast="+4 ORE"; }
        if(save.faith==int(Faith::Newborn)) save.faithPower=std::min(100.f,save.faithPower+0.8f);
        save.stamina=std::max(0.f,save.stamina-7.f); toastTimer=1.2f;
    }
    void eat(){
        if(save.food==0)return; save.food--; save.hunger=std::min(100.f,save.hunger+28.f);
        save.hp=std::min(100.f,save.hp+5.f); toast="ATE FOOD"; toastTimer=1.f;
    }
    void changeLayer(){
        if(save.layer<0){ save.layer++; toast="CLIMBED UP"; }
        else { save.layer=-1; toast="DUG TO Z -1"; }
        toastTimer=1.4f; world.cache={};
    }

    void renderPause(){
        renderWorld();
        r.rect({0,0,float(r.w),float(r.h)},{0,0,0,0.58f});
        panel(R(390,135,500,450)); title("PAUSED");
        if(button(R(500,245,280,58),"RESUME",true,C_GREEN)) screen=Screen::Game;
        if(button(R(500,325,280,58),"SAVE GAME",true,C_BLUE)){ writeSave(); toast="SAVED"; }
        if(button(R(500,405,280,58),"SETTINGS",true,C_BLUE)) screen=Screen::Settings;
        if(button(R(500,485,280,58),"MAIN MENU",true,C_RED)){ writeSave(); screen=Screen::Main; }
    }

    void renderDeath(){
        r.begin({0.045f,0.02f,0.025f,1});
        title(save.faith==int(Faith::Godless)?"YOUR STORY ENDS":"THE LIGHT FADES",
              save.faith==int(Faith::Godless)?"GODLESS - ONE LIFE":"FAITH WAS TOO WEAK");
        panel(R(350,250,580,230));
        r.centeredText(R(370,300,540,50),"DAY "+std::to_string(save.day),std::max(1.4f,2.5f*S()),C_WHITE);
        if(button(R(500,405,280,58),"MAIN MENU",true,C_RED)) screen=Screen::Main;
    }

    void simulate(float dt){
        if(screen==Screen::Splash){ splashTime+=dt; return; }
        if(screen!=Screen::Game) return;
        toastTimer=std::max(0.f,toastTimer-dt);
        float mag=std::sqrt(in.joyX*in.joyX+in.joyY*in.joyY);
        if(mag>0.08f){
            float jx=in.joyX/mag*std::min(1.f,mag),jy=in.joyY/mag*std::min(1.f,mag);
            float dx=jx,dy=jy;
            switch(rotation&3){
                case 1: dx=jy; dy=-jx; break;
                case 2: dx=-jx; dy=-jy; break;
                case 3: dx=-jy; dy=jx; break;
                default: break;
            }
            float speed=2.6f*(0.55f+0.45f*save.stamina/100.f);
            float nx=save.px+dx*speed*dt, ny=save.py+dy*speed*dt;
            Tile t=world.tile(int(nx),int(ny),save.layer);
            bool walk=t.t!=Terrain::Void&&t.t!=Terrain::Water&&t.t!=Terrain::Rock;
            if(save.layer<0) walk=t.t==Terrain::Cave||t.t==Terrain::Ore;
            if(walk){ save.px=std::clamp(nx,1.f,float(WORLD_SIZE-2)); save.py=std::clamp(ny,1.f,float(WORLD_SIZE-2)); }
            save.stamina=std::max(0.f,save.stamina-dt*3.5f);
        }else save.stamina=std::min(100.f,save.stamina+dt*5.0f);

        save.hunger=std::max(0.f,save.hunger-dt*0.075f);
        if(save.hunger<=0.01f) save.hp=std::max(0.f,save.hp-dt*2.4f);
        save.dayClock+=dt;
        if(save.dayClock>=180.f){ save.dayClock-=180.f; save.day++; if(save.faith!=int(Faith::Godless)) save.faithPower=std::min(100.f,save.faithPower+2.f); }
        autosaveTimer+=dt;
        if(autosaveTimer>25.f){ autosaveTimer=0; writeSave(); }

        if(save.hp<=0.f){
            if(save.faith==int(Faith::Established) || (save.faith==int(Faith::Newborn)&&save.faithPower>=10.f)){
                if(save.faith==int(Faith::Newborn)) save.faithPower-=10.f;
                save.hp=100; save.hunger=55; save.stamina=100; save.px=float(WORLD_SIZE/2); save.py=float(WORLD_SIZE/2); save.layer=0;
                toast="REBORN BY FAITH"; toastTimer=2.5f; writeSave();
            }else{
                if(save.faith==int(Faith::Godless)) deleteSave(slot);
                screen=Screen::Death;
            }
        }
    }

    void handleTapNavigation(){
        if(in.back){ in.back=false; onBack(); }
    }

    void render(){
        if(!r.ready) return;
        handleTapNavigation();
        switch(screen){
            case Screen::Splash: renderSplash(); break;
            case Screen::Main: renderMain(); break;
            case Screen::SaveManager: renderSaveManager(); break;
            case Screen::FaithSelect: renderFaith(); break;
            case Screen::CharacterCreate: renderCharacter(); break;
            case Screen::Settings: renderSettings(); break;
            case Screen::About: renderAbout(); break;
            case Screen::Game: renderWorld(); break;
            case Screen::Pause: renderPause(); break;
            case Screen::Death: renderDeath(); break;
        }
        in.tap=false;
        r.present();
    }

    int onInput(AInputEvent* event){
        int type=AInputEvent_getType(event);
        if(type==AINPUT_EVENT_TYPE_KEY){
            int action=AKeyEvent_getAction(event), code=AKeyEvent_getKeyCode(event);
            if(code==AKEYCODE_BACK && action==AKEY_EVENT_ACTION_UP){ in.back=true; return 1; }
            return 0;
        }
        if(type!=AINPUT_EVENT_TYPE_MOTION) return 0;
        int action=AMotionEvent_getAction(event);
        int masked=action&AMOTION_EVENT_ACTION_MASK;
        int index=(action&AMOTION_EVENT_ACTION_POINTER_INDEX_MASK)>>AMOTION_EVENT_ACTION_POINTER_INDEX_SHIFT;
        int id=AMotionEvent_getPointerId(event,index);
        float x=AMotionEvent_getX(event,index),y=AMotionEvent_getY(event,index);

        if(masked==AMOTION_EVENT_ACTION_DOWN||masked==AMOTION_EVENT_ACTION_POINTER_DOWN){
            if(screen==Screen::Game && x<r.w*0.43f && y>r.h*0.50f && in.joyId<0){
                in.joyId=id; in.joyBaseX=x; in.joyBaseY=y; in.joyX=0; in.joyY=0; return 1;
            }
        }
        if(masked==AMOTION_EVENT_ACTION_MOVE && in.joyId>=0){
            size_t count=AMotionEvent_getPointerCount(event);
            for(size_t i=0;i<count;i++) if(AMotionEvent_getPointerId(event,i)==in.joyId){
                float px=AMotionEvent_getX(event,i),py=AMotionEvent_getY(event,i);
                float dx=px-in.joyBaseX,dy=py-in.joyBaseY,rad=70.f*S();
                float m=std::sqrt(dx*dx+dy*dy);
                if(m>rad){dx*=rad/m;dy*=rad/m;}
                in.joyX=dx/rad; in.joyY=dy/rad; return 1;
            }
        }
        if(masked==AMOTION_EVENT_ACTION_UP||masked==AMOTION_EVENT_ACTION_POINTER_UP){
            if(id==in.joyId){ in.joyId=-1; in.joyX=in.joyY=0; return 1; }
            in.tap=true; in.tapX=x; in.tapY=y; return 1;
        }
        if(masked==AMOTION_EVENT_ACTION_CANCEL){ in.joyId=-1; in.joyX=in.joyY=0; return 1; }
        return 1;
    }

    void onCmd(int32_t cmd){
        switch(cmd){
            case APP_CMD_INIT_WINDOW: if(app->window&&!r.ready) r.init(app); break;
            case APP_CMD_TERM_WINDOW: r.term(); break;
            case APP_CMD_PAUSE: if(screen==Screen::Game) writeSave(); break;
            case APP_CMD_SAVE_STATE: if(screen==Screen::Game) writeSave(); break;
            default: break;
        }
    }
};

static void handle_cmd(android_app* app,int32_t cmd){
    auto* g=reinterpret_cast<Game*>(app->userData); if(g) g->onCmd(cmd);
}
static int32_t handle_input(android_app* app,AInputEvent* event){
    auto* g=reinterpret_cast<Game*>(app->userData); return g?g->onInput(event):0;
}

} // namespace fb

void android_main(struct android_app* app){
    fb::Game game(app);
    app->userData=&game;
    app->onAppCmd=fb::handle_cmd;
    app->onInputEvent=fb::handle_input;

    using clock=std::chrono::steady_clock;
    auto last=clock::now();
    double acc=0.0;
    constexpr double step=1.0/60.0;

    while(!app->destroyRequested){
        int events=0; android_poll_source* source=nullptr;
        int timeout=game.r.ready?0:-1;
        while(ALooper_pollOnce(timeout,nullptr,&events,reinterpret_cast<void**>(&source))>=0){
            if(source) source->process(app,source);
            if(app->destroyRequested) break;
            timeout=0;
        }
        if(app->destroyRequested) break;
        if(!game.r.ready) continue;

        auto now=clock::now();
        double dt=std::chrono::duration<double>(now-last).count(); last=now;
        dt=std::min(dt,0.10); acc+=dt;
        int guard=0;
        while(acc>=step && guard++<8){ game.simulate(float(step)); acc-=step; }
        game.render();
    }
    if(game.r.ready) game.r.term();
}
