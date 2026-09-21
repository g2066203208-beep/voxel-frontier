#include <android_native_app_glue.h>
#include <android/log.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "math3d.hpp"
#include "renderer3d.hpp"
#include "voxel_world.hpp"
#include "gameplay.hpp"

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"Faithbound",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"Faithbound",__VA_ARGS__)

namespace fb {

constexpr float PI = 3.14159265358979323846f;

enum class Screen {
    Splash, Main, Saves, FaithSelect, CharacterCreate, Settings, About,
    Game, Inventory, Status, Dialogue, Trade, Pause, Death
};

struct InputState {
    int joyId=-1;
    int camId=-1;
    float joyBaseX=0,joyBaseY=0,joyX=0,joyY=0;
    float camLastX=0,camLastY=0;
    float camMoved=0;
    bool tap=false;
    float tapX=0,tapY=0;
    bool back=false;
};

struct Drop {
    ItemId id=ItemId::None;
    int count=1;
    Vec3 pos{};
    float bob=0;
    bool alive=true;
};

struct Slime {
    Vec3 pos{};
    float hp=25;
    float hitCooldown=0;
    float phase=0;
    bool alive=true;
};

static Color skinColor(int i){
    static const Color v[]={
        {0.98f,0.82f,0.66f,1},{0.90f,0.70f,0.52f,1},{0.75f,0.54f,0.37f,1},
        {0.57f,0.38f,0.25f,1},{0.39f,0.25f,0.17f,1},{0.95f,0.75f,0.62f,1}};
    return v[i%6];
}
static Color hairColor(int i){
    static const Color v[]={
        {0.11f,0.08f,0.05f,1},{0.30f,0.16f,0.08f,1},{0.73f,0.51f,0.18f,1},
        {0.08f,0.09f,0.11f,1},{0.55f,0.21f,0.12f,1},{0.78f,0.77f,0.72f,1}};
    return v[i%6];
}
static Color outfitColor(int i){
    static const Color v[]={
        {0.18f,0.43f,0.72f,1},{0.40f,0.62f,0.25f,1},{0.67f,0.25f,0.19f,1},
        {0.47f,0.29f,0.63f,1},{0.70f,0.49f,0.18f,1},{0.18f,0.53f,0.50f,1}};
    return v[i%6];
}
static Color itemColor(ItemId id){
    switch(id){
        case ItemId::Wood:return {0.52f,0.31f,0.13f,1};
        case ItemId::Stone:return {0.56f,0.58f,0.60f,1};
        case ItemId::Berry:return {0.85f,0.17f,0.23f,1};
        case ItemId::Fiber:return {0.35f,0.70f,0.25f,1};
        case ItemId::DirtBlock:return {0.43f,0.29f,0.16f,1};
        case ItemId::StoneBlock:return {0.46f,0.48f,0.50f,1};
        case ItemId::SandBlock:return {0.75f,0.65f,0.37f,1};
        case ItemId::Ore:return {0.38f,0.68f,0.88f,1};
        case ItemId::WoodAxe:return {0.62f,0.38f,0.16f,1};
        case ItemId::StonePick:return {0.60f,0.64f,0.68f,1};
        case ItemId::WoodSword:return {0.68f,0.47f,0.22f,1};
        case ItemId::Torch:return {0.95f,0.58f,0.12f,1};
        case ItemId::Workbench:return {0.46f,0.27f,0.11f,1};
        case ItemId::Campfire:return {0.88f,0.31f,0.09f,1};
        case ItemId::ClothHat:return {0.50f,0.36f,0.70f,1};
        case ItemId::ClothTunic:return {0.24f,0.52f,0.69f,1};
        default:return {0.22f,0.24f,0.26f,1};
    }
}

class Game {
public:
    android_app* app=nullptr;
    Renderer3D r;
    VoxelWorld world;
    SaveDataV3 save{};
    std::array<bool,3> hasSlot{false,false,false};
    std::array<SaveDataV3,3> slots{};
    int slot=0;

    Screen screen=Screen::Splash;
    Screen settingsReturn=Screen::Main;
    InputState in{};

    int selectedFaith=0;
    int body=0,skin=1,hair=0,outfit=0;
    int quality=1;
    int selectedNpc=-1;
    int craftPage=0;
    float weatherFx=0;

    float splashTime=0;
    float accumulator=0;
    float autosave=0;
    float toastTime=0;
    std::string toast;

    float facingX=0.f,facingZ=-1.f;
    float yOffset=0.f,yVel=0.f;
    bool grounded=true;
    float attackFlash=0;

    std::vector<Drop> drops;
    std::vector<Slime> slimes;

    explicit Game(android_app* a):app(a){ refreshSlots(); }

    float scale() const { return std::min(float(r.w)/1280.f,float(r.h)/720.f); }
    float ox() const { return (float(r.w)-1280.f*scale())*0.5f; }
    float oy() const { return (float(r.h)-720.f*scale())*0.5f; }
    Rect R(float x,float y,float w,float h) const { float s=scale();return {ox()+x*s,oy()+y*s,w*s,h*s}; }
    float X(float x) const { return ox()+x*scale(); }
    float Y(float y) const { return oy()+y*scale(); }

    std::string path(int i) const {
        std::string p=app->activity->internalDataPath?app->activity->internalDataPath:"";
        return p+"/faithbound_v3_slot"+std::to_string(i)+".sav";
    }

    bool readSave(int i,SaveDataV3& out){
        FILE* f=std::fopen(path(i).c_str(),"rb"); if(!f)return false;
        SaveDataV3 t{};size_t n=std::fread(&t,1,sizeof(t),f);std::fclose(f);
        if(n!=sizeof(t)||t.magic!=SAVE_MAGIC_V3||t.version!=3)return false;
        uint32_t cs=t.checksum;t.checksum=0;
        if(checksumSave(t)!=cs)return false;
        t.checksum=cs;out=t;return true;
    }
    void refreshSlots(){ for(int i=0;i<3;i++)hasSlot[i]=readSave(i,slots[i]); }
    void deleteSlot(int i){std::remove(path(i).c_str());hasSlot[i]=false;}
    void writeSave(){
        world.exportEdits(save.edits.data(),MAX_SAVE_EDITS,save.editCount);
        world.exportHarvest(save.harvest.data(),MAX_SAVE_HARVEST,save.harvestCount);
        save.quality=quality;
        save.checksum=0;save.checksum=checksumSave(save);
        FILE* f=std::fopen(path(slot).c_str(),"wb");
        if(f){std::fwrite(&save,1,sizeof(save),f);std::fclose(f);slots[slot]=save;hasSlot[slot]=true;}
    }

    const char* faithName(int f) const {
        if(f==int(Faith::Mature))return "成熟神";
        if(f==int(Faith::Newborn))return "初生神";
        return "无神者";
    }

    void spawnMobs(){
        slimes.clear();
        uint32_t h=hash32(save.seed^0x5A5A5A5Au);
        for(int i=0;i<8;i++){
            float a=float((h>>(i%16))&255)/255.f*2.f*PI + i*0.7f;
            float d=7.f+float((h>>(i%12))&7);
            int x=int(save.px+std::cos(a)*d),z=int(save.pz+std::sin(a)*d);
            x=std::clamp(x,2,WORLD_SIZE-3);z=std::clamp(z,2,WORLD_SIZE-3);
            float y=float(world.walkHeight(x,z));
            slimes.push_back({{x+0.5f,y,z+0.5f},25.f,0.f,float(i),true});
        }
    }

    void newWorld(){
        save=SaveDataV3{};
        uint64_t now=uint64_t(std::chrono::high_resolution_clock::now().time_since_epoch().count());
        save.seed=now^(uint64_t(slot+1)*0x9E3779B97F4A7C15ULL);
        save.faith=selectedFaith;save.body=body;save.skin=skin;save.hair=hair;save.outfit=outfit;
        save.px=float(WORLD_SIZE/2)+0.5f;save.pz=float(WORLD_SIZE/2)+0.5f;
        save.cameraYaw=0.78f;save.dayTime=0.28f;save.day=1;
        save.faithPower=selectedFaith==int(Faith::Mature)?100.f:(selectedFaith==int(Faith::Newborn)?30.f:0.f);
        quality=1;
        world.reset(save.seed);
        if(selectedFaith!=int(Faith::Godless)){
            int cx=WORLD_SIZE/2,cz=WORLD_SIZE/2;
            world.setBlock(cx,world.walkHeight(cx,cz),cz-2,Block::Shrine);
        }
        save.inventory.add(ItemId::Berry,4);
        save.inventory.add(ItemId::Fiber,4);
        save.inventory.add(ItemId::ClothTunic,1);
        save.inventory.equipFrom(2);
        if(selectedFaith==int(Faith::Mature))save.inventory.add(ItemId::Torch,1);
        drops.clear();spawnMobs();
        screen=Screen::Game;toast="世界苏醒";toastTime=2.5f;writeSave();
    }

    void loadWorld(int i){
        SaveDataV3 d{};if(!readSave(i,d))return;
        slot=i;save=d;selectedFaith=save.faith;body=save.body;skin=save.skin;hair=save.hair;outfit=save.outfit;quality=save.quality;
        world.reset(save.seed);world.importEdits(save.edits.data(),save.editCount);world.importHarvest(save.harvest.data(),save.harvestCount);
        yOffset=save.playerYOffset;yVel=0;grounded=true;drops.clear();spawnMobs();
        screen=Screen::Game;toast="欢迎回来";toastTime=1.8f;
    }

    bool button(Rect q,const std::string& label,bool enabled=true,Color accent={0.28f,0.62f,0.91f,1}){
        Color panelColor={0.045f,0.060f,0.078f,0.92f};
        r.rect(q,enabled?mix(panelColor,accent,0.16f):mul(panelColor,0.72f));
        r.frame(q,2.f*scale(),enabled?accent:Color{0.36f,0.39f,0.42f,1});
        r.textCentered(q,label,std::max(16.f*scale(),14.f),enabled?Color{0.96f,0.97f,0.94f,1}:Color{0.47f,0.50f,0.52f,1});
        if(enabled&&in.tap&&contains(q,in.tapX,in.tapY)){in.tap=false;return true;}
        return false;
    }
    void panel(Rect q,Color c={0.035f,0.045f,0.060f,0.92f}){
        r.rect(q,c);r.frame(q,2.f*scale(),{0.20f,0.25f,0.31f,0.98f});
    }
    void title(const std::string& a,const std::string& b=""){
        r.textCentered(R(140,62,1000,74),a,std::max(36.f*scale(),30.f),{0.96f,0.72f,0.22f,1});
        if(!b.empty())r.textCentered(R(180,132,920,35),b,std::max(17.f*scale(),15.f),{0.78f,0.83f,0.86f,1});
    }

    void onBack(){
        switch(screen){
            case Screen::Game:screen=Screen::Pause;writeSave();break;
            case Screen::Inventory:screen=Screen::Game;break;
            case Screen::Pause:screen=Screen::Game;break;
            case Screen::Saves:case Screen::FaithSelect:case Screen::About:screen=Screen::Main;break;
            case Screen::CharacterCreate:screen=Screen::FaithSelect;break;
            case Screen::Settings:screen=settingsReturn;break;
            case Screen::Death:screen=Screen::Main;break;
            case Screen::Main:ANativeActivity_finish(app->activity);break;
            default:screen=Screen::Main;break;
        }
    }

    void renderSplash(){
        r.begin({0.015f,0.025f,0.045f,1});
        for(int i=0;i<24;i++){
            float x=X(float((i*131)%1280)),y=Y(float((i*71)%720));
            float p=0.45f+0.45f*std::sin(splashTime*1.5f+i);
            r.rect({x,y,3*scale(),3*scale()},{0.45f,0.72f,1.f,p});
        }
        r.textCentered(R(120,220,1040,95),"神契荒境",std::max(58.f*scale(),44.f),{0.96f,0.72f,0.22f,1});
        r.textCentered(R(220,340,840,42),"3D 体素开放世界 RPG",std::max(22.f*scale(),18.f),{0.86f,0.90f,0.92f,1});
        r.textCentered(R(220,610,840,38),"点击开始",std::max(18.f*scale(),16.f),{0.55f,0.62f,0.68f,1});
        r.flushUI();r.present();
        if(in.tap||splashTime>2.2f){in.tap=false;screen=Screen::Main;}
    }

    void renderMain(){
        r.begin({0.035f,0.065f,0.085f,1});
        for(int i=0;i<26;i++){
            float x=X(float(i*52-20)),base=Y(520-float((i%4)*7));
            Color g={0.10f+0.02f*(i%3),0.27f+0.025f*(i%4),0.15f,1};
            r.rect({x,base,52*scale(),220*scale()},g);
            r.rect({x+20*scale(),base-50*scale(),12*scale(),50*scale()},{0.24f,0.16f,0.08f,1});
            r.rect({x+4*scale(),base-86*scale(),45*scale(),42*scale()},{0.08f,0.31f,0.13f,1});
        }
        title("神契荒境","体素大世界 · 生存 · 信仰 · 建造");
        bool any=hasSlot[0]||hasSlot[1]||hasSlot[2];
        if(button(R(465,230,350,62),"继续游戏",any,{0.30f,0.74f,0.39f,1})){
            for(int i=0;i<3;i++)if(hasSlot[i]){loadWorld(i);break;}
        }
        if(button(R(465,310,350,62),"新世界",true,{0.96f,0.72f,0.22f,1}))screen=Screen::Saves;
        if(button(R(465,390,350,62),"读取存档",any))screen=Screen::Saves;
        if(button(R(465,470,350,62),"设置",true)) {settingsReturn=Screen::Main;screen=Screen::Settings;}
        if(button(R(465,550,350,62),"关于",true,{0.45f,0.49f,0.54f,1}))screen=Screen::About;
        r.text(X(24),Y(682),"V0.2  C++20 / GLES3 / VOXEL",std::max(13.f*scale(),11.f),{0.46f,0.53f,0.58f,1});
        r.flushUI();r.present();
    }

    void renderSaves(){
        r.begin({0.032f,0.043f,0.060f,1});
        title("存档管理","三个独立世界");
        refreshSlots();
        for(int i=0;i<3;i++){
            Rect q=R(250,205+i*137,780,108);panel(q);
            r.text(q.x+22*scale(),q.y+18*scale(),"存档槽 "+std::to_string(i+1),22*scale(),{0.96f,0.72f,0.22f,1});
            if(hasSlot[i]){
                std::string info="第 "+std::to_string(slots[i].day)+" 天  "+faithName(slots[i].faith);
                r.text(q.x+22*scale(),q.y+58*scale(),info,17*scale(),{0.90f,0.92f,0.93f,1});
                if(button({q.x+q.w-185*scale(),q.y+22*scale(),150*scale(),56*scale()},"载入",true,{0.31f,0.72f,0.39f,1})){loadWorld(i);return;}
                if(button({q.x+q.w-345*scale(),q.y+22*scale(),140*scale(),56*scale()},"删除",true,{0.82f,0.26f,0.25f,1})){deleteSlot(i);refreshSlots();}
            }else{
                r.text(q.x+22*scale(),q.y+60*scale(),"空存档",17*scale(),{0.48f,0.53f,0.58f,1});
                if(button({q.x+q.w-185*scale(),q.y+22*scale(),150*scale(),56*scale()},"创建",true,{0.96f,0.72f,0.22f,1})){slot=i;screen=Screen::FaithSelect;}
            }
        }
        if(button(R(35,630,185,55),"返回",true,{0.45f,0.49f,0.54f,1}))screen=Screen::Main;
        r.flushUI();r.present();
    }

    void renderFaith(){
        r.begin({0.035f,0.046f,0.065f,1});
        title("选择信仰","死亡规则与文明起点由此改变");
        const char* names[]={"成熟神","初生神","无神者"};
        const char* desc[]={"已有神殿与信徒，死亡可复活","从零发展信仰，神力不足时无法复活","不信神，仅有一条命"};
        Color cols[]={{0.27f,0.58f,0.93f,1},{0.96f,0.72f,0.22f,1},{0.86f,0.25f,0.25f,1}};
        for(int i=0;i<3;i++){
            Rect q=R(100+i*365,225,340,270);
            r.rect(q,i==selectedFaith?mix(Color{0.04f,0.05f,0.07f,1},cols[i],0.28f):Color{0.04f,0.05f,0.07f,1});
            r.frame(q,(i==selectedFaith?4.f:2.f)*scale(),cols[i]);
            r.textCentered({q.x,q.y+30*scale(),q.w,44*scale()},names[i],26*scale(),cols[i]);
            r.textCentered({q.x+18*scale(),q.y+115*scale(),q.w-36*scale(),80*scale()},desc[i],16*scale(),{0.90f,0.92f,0.94f,1});
            if(in.tap&&contains(q,in.tapX,in.tapY)){selectedFaith=i;in.tap=false;}
        }
        if(button(R(775,565,290,60),"继续",true,{0.31f,0.72f,0.39f,1}))screen=Screen::CharacterCreate;
        if(button(R(215,565,210,60),"返回",true,{0.45f,0.49f,0.54f,1}))screen=Screen::Saves;
        r.flushUI();r.present();
    }

    void previewCharacter(Rect q){
        panel(q);
        float cx=q.x+q.w*0.5f,cy=q.y+q.h*0.50f,s=4.5f*scale();
        Color sc=skinColor(skin),hc=hairColor(hair),oc=outfitColor(outfit),outline={0.025f,0.028f,0.032f,1};
        r.rect({cx-10*s,cy-48*s,20*s,23*s},outline);r.rect({cx-8*s,cy-46*s,16*s,19*s},sc);
        r.rect({cx-10*s,cy-51*s,20*s,7*s},hc);
        if(hair%3==1)r.rect({cx+6*s,cy-45*s,5*s,15*s},hc);
        if(hair%3==2)r.rect({cx-11*s,cy-44*s,5*s,16*s},hc);
        r.rect({cx-13*s,cy-25*s,26*s,33*s},outline);r.rect({cx-11*s,cy-23*s,22*s,29*s},oc);
        r.rect({cx-17*s,cy-18*s,6*s,26*s},outline);r.rect({cx-15*s,cy-16*s,4*s,22*s},sc);
        r.rect({cx+11*s,cy-18*s,6*s,26*s},outline);r.rect({cx+11*s,cy-16*s,4*s,22*s},sc);
        r.rect({cx-10*s,cy+7*s,8*s,26*s},outline);r.rect({cx-8*s,cy+7*s,5*s,23*s},mul(oc,0.68f));
        r.rect({cx+2*s,cy+7*s,8*s,26*s},outline);r.rect({cx+3*s,cy+7*s,5*s,23*s},mul(oc,0.68f));
    }

    void renderCharacterCreate(){
        r.begin({0.038f,0.050f,0.064f,1});
        title("创建角色","2D 像素精灵将存在于 3D 体素世界");
        Rect p=R(125,195,380,400);previewCharacter(p);
        r.textCentered({p.x,p.y+p.h-48*scale(),p.w,32*scale()},faithName(selectedFaith),18*scale(),{0.96f,0.72f,0.22f,1});

        float bx=610,by=220;
        r.text(X(bx),Y(by),"体型",20*scale(),{0.92f,0.94f,0.95f,1});
        if(button(R(bx+180,by-13,235,52),body==0?"体型 A":"体型 B"))body=(body+1)%2;
        r.text(X(bx),Y(by+82),"肤色",20*scale(),{0.92f,0.94f,0.95f,1});
        if(button(R(bx+180,by+69,235,52),"肤色 "+std::to_string(skin+1)))skin=(skin+1)%6;
        r.text(X(bx),Y(by+164),"发型",20*scale(),{0.92f,0.94f,0.95f,1});
        if(button(R(bx+180,by+151,235,52),"发型 "+std::to_string(hair+1)))hair=(hair+1)%6;
        r.text(X(bx),Y(by+246),"服装",20*scale(),{0.92f,0.94f,0.95f,1});
        if(button(R(bx+180,by+233,235,52),"服装 "+std::to_string(outfit+1)))outfit=(outfit+1)%6;
        if(button(R(625,570,225,58),"随机",true,{0.96f,0.72f,0.22f,1})){
            uint32_t h=hash32(uint64_t(std::chrono::high_resolution_clock::now().time_since_epoch().count()));
            body=h%2;skin=(h>>3)%6;hair=(h>>7)%6;outfit=(h>>11)%6;
        }
        if(button(R(875,570,245,58),"进入世界",true,{0.31f,0.72f,0.39f,1}))newWorld();
        if(button(R(35,630,185,55),"返回",true,{0.45f,0.49f,0.54f,1}))screen=Screen::FaithSelect;
        r.flushUI();r.present();
    }

    void renderSettings(){
        r.begin({0.035f,0.046f,0.060f,1});
        title("设置","移动端性能选项");
        panel(R(320,195,640,360));
        r.text(X(385),Y(255),"画质",22*scale(),{0.92f,0.94f,0.95f,1});
        const char* qn[]={"低","中","高"};
        if(button(R(710,232,190,54),qn[quality],true,{0.27f,0.60f,0.91f,1}))quality=(quality+1)%3;
        r.text(X(385),Y(335),"固定模拟",22*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(710),Y(335),"60 赫兹",18*scale(),{0.31f,0.72f,0.39f,1});
        r.text(X(385),Y(405),"分块生成",22*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(710),Y(405),"16 x 16",18*scale(),{0.31f,0.72f,0.39f,1});
        r.text(X(385),Y(475),"体素大世界",22*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(710),Y(475),"512 x 512 x 32",18*scale(),{0.31f,0.72f,0.39f,1});
        if(button(R(35,630,185,55),"返回",true,{0.45f,0.49f,0.54f,1}))screen=settingsReturn;
        r.flushUI();r.present();
    }

    void renderAbout(){
        r.begin({0.035f,0.046f,0.060f,1});
        title("关于","V0.2 体素重构");
        panel(R(225,190,830,370));
        r.text(X(285),Y(240),"原生安卓 / C++20 / OpenGL ES 3",19*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(285),Y(290),"3D 体素大世界 + 2D 像素精灵",19*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(285),Y(340),"分块生成 / 可见面剔除 / LRU 缓存",19*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(285),Y(390),"背包 / 装备 / 工具 / 制作 / 世界交互",19*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(285),Y(440),"昼夜循环 / 生存 / 信仰复活 / 永久死亡",19*scale(),{0.92f,0.94f,0.95f,1});
        r.text(X(285),Y(495),"开发版：系统与美术将持续扩展",19*scale(),{0.96f,0.72f,0.22f,1});
        if(button(R(35,630,185,55),"返回",true,{0.45f,0.49f,0.54f,1}))screen=Screen::Main;
        r.flushUI();r.present();
    }

    Color skyColor(float t) const {
        float sun=std::sin((t-0.25f)*2.f*PI);
        float d=clamp01((sun+0.18f)/0.78f);
        Color night={0.018f,0.028f,0.075f,1};
        Color dawn={0.35f,0.19f,0.20f,1};
        Color day={0.32f,0.62f,0.84f,1};
        if(d<0.28f)return mix(night,dawn,d/0.28f);
        return mix(dawn,day,(d-0.28f)/0.72f);
    }
    float daylight() const {
        float sun=std::sin((save.dayTime-0.25f)*2.f*PI);
        return 0.18f+0.82f*clamp01((sun+0.10f)/0.85f);
    }
    std::string timeName() const {
        float h=save.dayTime*24.f;
        if(h<5||h>=21)return "夜晚";
        if(h<8)return "清晨";
        if(h<17)return "白天";
        return "黄昏";
    }

    Mat4 cameraMvp(Vec3& camRight,Vec3& camForward){
        float yaw=save.cameraYaw;
        Vec3 target{save.px,float(world.walkHeight(int(save.px),int(save.pz)))+1.2f+yOffset*0.25f,save.pz};
        float dist=quality==0?15.5f:(quality==1?18.0f:20.5f);
        float pitch=0.72f;
        Vec3 offset{std::sin(yaw)*std::cos(pitch)*dist,std::sin(pitch)*dist,std::cos(yaw)*std::cos(pitch)*dist};
        Vec3 eye=target+offset;
        camForward=normalize(target-eye);
        camRight=normalize(cross(camForward,{0,1,0}));
        Mat4 view=lookAt(eye,target,{0,1,0});
        Mat4 proj=perspective(50.f*PI/180.f,float(r.w)/float(std::max(1,r.h)),0.1f,90.f);
        return mul(proj,view);
    }

    uint8_t exposedFaces(int x,int y,int z,Block b){
        uint8_t m=0;
        auto vis=[&](Block n){
            if(b==Block::Water)return n==Block::Air;
            return n==Block::Air||n==Block::Water;
        };
        if(vis(world.block(x,y+1,z)))m|=Renderer3D::Top;
        if(vis(world.block(x,y-1,z)))m|=Renderer3D::Bottom;
        if(vis(world.block(x,y,z-1)))m|=Renderer3D::North;
        if(vis(world.block(x,y,z+1)))m|=Renderer3D::South;
        if(vis(world.block(x+1,y,z)))m|=Renderer3D::East;
        if(vis(world.block(x-1,y,z)))m|=Renderer3D::West;
        return m;
    }

    void drawTree(int x,int z,Vec3 right,float light){
        float y=float(world.walkHeight(x,z));
        Vec3 c{x+0.5f,y,z+0.5f};
        Color outline={0.025f,0.035f,0.025f,1};
        r.billboardRect(c,0.42f,1.55f,0.f,right,outline,0.012f);
        r.billboardRect(c,0.31f,1.43f,0.03f,right,mul({0.42f,0.24f,0.10f,1},light));
        r.billboardRect(c,1.65f,1.20f,1.05f,right,outline,0.010f);
        r.billboardRect(c,1.48f,1.05f,1.12f,right,mul({0.10f,0.40f,0.15f,1},light));
        r.billboardRect(c,1.20f,0.80f,1.78f,right,mul({0.14f,0.50f,0.19f,1},light));
    }
    void drawRock(int x,int z,Vec3 right,float light){
        float y=float(world.walkHeight(x,z));Vec3 c{x+0.5f,y,z+0.5f};
        r.billboardRect(c,0.95f,0.63f,0.f,right,mul({0.48f,0.50f,0.52f,1},light));
        r.billboardRect(c,0.55f,0.30f,0.45f,right,mul({0.64f,0.66f,0.67f,1},light),0.01f);
    }
    void drawBerry(int x,int z,Vec3 right,float light){
        float y=float(world.walkHeight(x,z));Vec3 c{x+0.5f,y,z+0.5f};
        r.billboardRect(c,1.0f,0.68f,0.f,right,mul({0.12f,0.43f,0.14f,1},light));
        for(int i=-1;i<=1;i++)r.billboardRect(c+right*(0.22f*i),0.12f,0.12f,0.34f+0.12f*(i&1),right,mul({0.85f,0.15f,0.21f,1},light),0.015f);
    }
    void drawGrass(int x,int z,Vec3 right,float light){
        float y=float(world.walkHeight(x,z));Vec3 c{x+0.5f,y,z+0.5f};
        r.billboardRect(c,0.65f,0.55f,0.f,right,mul({0.30f,0.66f,0.23f,1},light));
    }

    void drawPlayer(Vec3 right,Vec3 forward,float light){
        int gx=int(std::floor(save.px)),gz=int(std::floor(save.pz));
        float gy=float(world.walkHeight(gx,gz))+yOffset;
        Vec3 c{save.px,gy,save.pz};
        r.quad3({c.x-0.34f,c.y+0.012f,c.z-0.20f},{c.x+0.34f,c.y+0.012f,c.z-0.20f},
                {c.x+0.34f,c.y+0.012f,c.z+0.20f},{c.x-0.34f,c.y+0.012f,c.z+0.20f},{0.01f,0.015f,0.02f,0.35f});
        Color sc=mul(skinColor(save.skin),light),hc=mul(hairColor(save.hair),light),oc=mul(outfitColor(save.outfit),light);
        Color outline={0.025f,0.028f,0.032f,1};
        float bob=grounded?0.f:0.04f;
        r.billboardRect(c-right*0.14f,0.20f,0.58f,0.03f+bob,right,outline,0.014f);
        r.billboardRect(c-right*0.14f,0.13f,0.52f,0.06f+bob,right,mul(oc,0.62f));
        r.billboardRect(c+right*0.14f,0.20f,0.58f,0.03f+bob,right,outline,0.014f);
        r.billboardRect(c+right*0.14f,0.13f,0.52f,0.06f+bob,right,mul(oc,0.62f));
        r.billboardRect(c,0.76f,0.76f,0.52f+bob,right,outline,0.014f);
        r.billboardRect(c,0.68f,0.68f,0.56f+bob,right,oc);
        r.billboardRect(c-right*0.43f,0.18f,0.62f,0.60f+bob,right,outline,0.012f);
        r.billboardRect(c-right*0.43f,0.12f,0.55f,0.64f+bob,right,sc);
        r.billboardRect(c+right*0.43f,0.18f,0.62f,0.60f+bob,right,outline,0.012f);
        r.billboardRect(c+right*0.43f,0.12f,0.55f,0.64f+bob,right,sc);
        r.billboardRect(c,0.67f,0.66f,1.25f+bob,right,outline,0.016f);
        r.billboardRect(c,0.59f,0.58f,1.29f+bob,right,sc);
        r.billboardRect(c,0.62f,0.20f,1.69f+bob,right,hc,0.018f);
        if(save.hair%3==1)r.billboardRect(c+right*0.25f,0.16f,0.45f,1.38f+bob,right,hc,0.018f);
        if(save.hair%3==2)r.billboardRect(c-right*0.25f,0.16f,0.45f,1.38f+bob,right,hc,0.018f);
        r.billboardRect(c-right*0.14f,0.06f,0.06f,1.51f+bob,right,{0.04f,0.04f,0.05f,1},0.022f);
        r.billboardRect(c+right*0.14f,0.06f,0.06f,1.51f+bob,right,{0.04f,0.04f,0.05f,1},0.022f);

        ItemId held=save.inventory.mainHand();
        if(held!=ItemId::None){
            Color ic=mul(itemColor(held),light);
            Vec3 hcPos=c+right*0.56f;
            r.billboardRect(hcPos,0.10f,0.78f,0.55f+bob,right,mul({0.43f,0.25f,0.10f,1},light),0.026f);
            r.billboardRect(hcPos+right*0.06f,0.34f,0.18f,1.14f+bob,right,ic,0.028f);
        }
        if(attackFlash>0){
            Vec3 p=c+Vec3{facingX,0,facingZ}*0.75f;
            r.billboardRect(p,0.15f,1.15f,0.55f,right,{1.f,0.88f,0.45f,0.55f},0.04f);
        }
        (void)forward;
    }

    void drawDrop(const Drop& d,Vec3 right,float light){
        if(!d.alive)return;
        Vec3 p=d.pos+Vec3{0,0.10f+0.12f*std::sin(d.bob),0};
        Color c=mul(itemColor(d.id),light);
        r.billboardRect(p,0.34f,0.34f,0.f,right,{0.02f,0.02f,0.025f,0.9f},0.012f);
        r.billboardRect(p,0.28f,0.28f,0.03f,right,c,0.016f);
    }

    void drawSlime(const Slime& s,Vec3 right,float light){
        if(!s.alive)return;
        Vec3 p=s.pos;
        float bob=0.05f*std::sin(s.phase);
        r.billboardRect(p,0.92f,0.63f,bob,right,{0.025f,0.03f,0.035f,1},0.012f);
        r.billboardRect(p,0.82f,0.55f,0.04f+bob,right,mul({0.29f,0.72f,0.52f,1},light));
        r.billboardRect(p-right*0.19f,0.08f,0.08f,0.39f+bob,right,{0.03f,0.04f,0.045f,1},0.02f);
        r.billboardRect(p+right*0.19f,0.08f,0.08f,0.39f+bob,right,{0.03f,0.04f,0.045f,1},0.02f);
    }

    void buildScene(Vec3& right,Vec3& forward,Mat4& mvp){
        mvp=cameraMvp(right,forward);
        float light=daylight();
        int radius=quality==0?9:(quality==1?12:15);
        int cx=int(save.px),cz=int(save.pz);
        for(int z=cz-radius;z<=cz+radius;z++){
            for(int x=cx-radius;x<=cx+radius;x++){
                if(x<0||z<0||x>=WORLD_SIZE||z>=WORLD_SIZE)continue;
                float dx=float(x-cx),dz=float(z-cz);
                if(dx*dx+dz*dz>float(radius*radius*1.22f))continue;
                for(int y=0;y<WORLD_Y;y++){
                    Block b=world.block(x,y,z);
                    if(b==Block::Air)continue;
                    uint8_t faces=exposedFaces(x,y,z,b);
                    if(!faces)continue;
                    Color col=blockColor(b);
                    float dist=std::sqrt(dx*dx+dz*dz);
                    float fog=clamp01((dist-float(radius)*0.65f)/(float(radius)*0.45f));
                    col=mix(col,skyColor(save.dayTime),fog*0.35f);
                    r.cube(float(x),float(y),float(z),faces,col,light);
                }
                WorldObject o=world.objectAt(x,z);
                if(o==WorldObject::Tree)drawTree(x,z,right,light);
                else if(o==WorldObject::Rock)drawRock(x,z,right,light);
                else if(o==WorldObject::BerryBush)drawBerry(x,z,right,light);
                else if(o==WorldObject::GrassTuft)drawGrass(x,z,right,light);
            }
        }
        for(const auto& d:drops)drawDrop(d,right,light);
        for(const auto& s:slimes)drawSlime(s,right,light);
        drawPlayer(right,forward,light);
    }

    void drawBar(float x,float y,const char* label,float v,Color c){
        r.text(X(x),Y(y-1),label,16*scale(),{0.95f,0.96f,0.94f,1});
        r.rect(R(x+64,y,218,17),{0.06f,0.07f,0.085f,0.92f});
        r.rect(R(x+66,y+2,214*clamp01(v/100.f),13),c);
        r.frame(R(x+64,y,218,17),1.3f*scale(),{0.28f,0.31f,0.34f,1});
    }

    void drawHotbar(){
        float s=scale();
        float total=8*58.f;
        float x=640.f-total*0.5f;
        for(int i=0;i<8;i++){
            Rect q=R(x+i*58.f,646,52,52);
            Color border=i==save.inventory.selectedHotbar?Color{0.96f,0.72f,0.22f,1}:Color{0.30f,0.35f,0.40f,1};
            r.rect(q,{0.035f,0.045f,0.060f,0.92f});r.frame(q,(i==save.inventory.selectedHotbar?3.f:1.5f)*s,border);
            auto st=save.inventory.slots[i];
            if(st.count){
                Color ic=itemColor(ItemId(st.id));
                r.rect({q.x+11*s,q.y+10*s,30*s,28*s},ic);
                if(st.count>1)r.text(q.x+30*s,q.y+31*s,std::to_string(st.count),12*s,{1,1,1,1});
                if(st.durability){
                    float maxd=float(std::max<uint16_t>(1,maxDurability(ItemId(st.id))));
                    r.rect({q.x+5*s,q.y+44*s,42*s,4*s},{0.10f,0.11f,0.12f,1});
                    r.rect({q.x+5*s,q.y+44*s,42*s*(st.durability/maxd),4*s},{0.32f,0.78f,0.36f,1});
                }
            }
            if(in.tap&&contains(q,in.tapX,in.tapY)){save.inventory.selectedHotbar=i;in.tap=false;}
        }
    }

    void renderWorldUI(){
        panel(R(16,14,320,113));
        drawBar(30,31,"生命",save.hp,{0.86f,0.24f,0.24f,1});
        drawBar(30,63,"饥饿",save.hunger,{0.94f,0.67f,0.19f,1});
        drawBar(30,95,"体力",save.stamina,{0.31f,0.72f,0.39f,1});

        panel(R(970,14,294,114));
        int hour=int(save.dayTime*24.f)%24;
        std::string t="第 "+std::to_string(save.day)+" 天  "+timeName();
        r.text(X(988),Y(31),t,17*scale(),{0.95f,0.96f,0.94f,1});
        std::string clock=(hour<10?"0":"")+std::to_string(hour)+":00";
        r.text(X(988),Y(61),"时间 "+clock,16*scale(),{0.74f,0.84f,0.93f,1});
        r.text(X(988),Y(91),faithName(save.faith),16*scale(),{0.96f,0.72f,0.22f,1});

        float jx=in.joyId>=0?in.joyBaseX:X(105),jy=in.joyId>=0?in.joyBaseY:Y(610);
        float s=scale();
        r.rect({jx-58*s,jy-58*s,116*s,116*s},{0.02f,0.03f,0.04f,0.42f});
        r.frame({jx-58*s,jy-58*s,116*s,116*s},2*s,{0.68f,0.74f,0.78f,0.48f});
        r.rect({jx+in.joyX*38*s-22*s,jy+in.joyY*38*s-22*s,44*s,44*s},{0.62f,0.70f,0.75f,0.65f});

        if(button(R(1095,455,150,54),"攻击",true,{0.84f,0.28f,0.25f,1}))attack();
        if(button(R(1095,517,150,54),"交互",true,{0.96f,0.72f,0.22f,1}))interact();
        ItemId hi=ItemId(save.inventory.hotbar()->id);
        std::string digLabel=isPlaceable(hi)?"放置":"挖掘";
        if(button(R(930,517,150,54),digLabel,true,{0.27f,0.60f,0.91f,1})){
            if(isPlaceable(hi))placeSelected();else dig();
        }
        if(button(R(930,455,150,54),"跳跃",true,{0.31f,0.72f,0.39f,1}))jump();
        if(button(R(1095,579,150,54),"背包",true,{0.50f,0.38f,0.72f,1}))screen=Screen::Inventory;
        if(button(R(930,579,150,54),"旋转",true,{0.27f,0.60f,0.91f,1}))save.cameraYaw+=PI*0.5f;
        if(button(R(1170,145,78,46),"暂停",true,{0.45f,0.49f,0.54f,1})){screen=Screen::Pause;writeSave();}

        drawHotbar();
        if(toastTime>0){
            Rect q=R(410,148,460,48);r.rect(q,{0.025f,0.03f,0.04f,0.86f});r.frame(q,2*s,{0.96f,0.72f,0.22f,1});
            r.textCentered(q,toast,18*s,{0.97f,0.97f,0.94f,1});
        }
    }

    void renderGame(){
        Color sky=skyColor(save.dayTime);r.begin(sky);
        Vec3 right{},forward{};Mat4 mvp{};
        buildScene(right,forward,mvp);
        r.flush3D(mvp);
        renderWorldUI();
        r.flushUI();r.present();
    }

    bool nearWorkbench(){
        int px=int(save.px),pz=int(save.pz);
        for(int z=pz-2;z<=pz+2;z++)for(int x=px-2;x<=px+2;x++){
            int y=world.topSolidY(x,z);
            if(world.block(x,y,z)==Block::Workbench)return true;
        }
        return false;
    }

    void renderInventory(){
        Color sky=skyColor(save.dayTime);r.begin(sky);
        Vec3 right{},forward{};Mat4 mvp{};buildScene(right,forward,mvp);r.flush3D(mvp);
        r.rect({0,0,float(r.w),float(r.h)},{0.01f,0.015f,0.02f,0.72f});

        panel(R(110,65,1060,590));
        r.text(X(145),Y(88),"背包",30*scale(),{0.96f,0.72f,0.22f,1});
        r.text(X(145),Y(132),"装备栏",19*scale(),{0.86f,0.89f,0.91f,1});

        const char* eqName[]={"头部","身体","主手","副手"};
        for(int e=0;e<4;e++){
            Rect q=R(145,170+e*76,210,62);
            r.rect(q,{0.05f,0.065f,0.08f,1});r.frame(q,1.5f*scale(),{0.28f,0.33f,0.38f,1});
            r.text(q.x+10*scale(),q.y+10*scale(),eqName[e],15*scale(),{0.65f,0.70f,0.74f,1});
            auto st=save.inventory.equipment[e];
            r.text(q.x+72*scale(),q.y+21*scale(),st.count?itemName(ItemId(st.id)):"无",17*scale(),{0.94f,0.95f,0.93f,1});
            if(in.tap&&contains(q,in.tapX,in.tapY)&&st.count){save.inventory.unequip(e);in.tap=false;}
        }

        r.text(X(405),Y(132),"物品",19*scale(),{0.86f,0.89f,0.91f,1});
        for(int i=0;i<Inventory::SLOT_COUNT;i++){
            int row=i/6,col=i%6;
            Rect q=R(405+col*86,170+row*82,72,68);
            bool sel=i==save.inventory.selectedInventory;
            r.rect(q,{0.048f,0.060f,0.075f,1});r.frame(q,(sel?3.f:1.5f)*scale(),sel?Color{0.96f,0.72f,0.22f,1}:Color{0.28f,0.33f,0.38f,1});
            auto st=save.inventory.slots[i];
            if(st.count){
                Color ic=itemColor(ItemId(st.id));r.rect({q.x+18*scale(),q.y+13*scale(),36*scale(),31*scale()},ic);
                r.text(q.x+7*scale(),q.y+48*scale(),std::to_string(st.count),12*scale(),{0.92f,0.94f,0.95f,1});
            }
            if(in.tap&&contains(q,in.tapX,in.tapY)){save.inventory.selectedInventory=i;in.tap=false;}
        }

        int si=save.inventory.selectedInventory;
        if(si>=0&&si<Inventory::SLOT_COUNT&&save.inventory.slots[si].count){
            ItemId id=ItemId(save.inventory.slots[si].id);
            r.text(X(145),Y(500),"选中："+std::string(itemName(id)),18*scale(),{0.96f,0.72f,0.22f,1});
            if(button(R(145,535,100,48),"装备",isTool(id)||isWearable(id),{0.31f,0.72f,0.39f,1}))save.inventory.equipFrom(si);
            if(button(R(255,535,100,48),"丢弃",true,{0.82f,0.26f,0.25f,1}))dropInventory(si);
        }

        r.text(X(930),Y(132),"制作",19*scale(),{0.86f,0.89f,0.91f,1});
        bool bench=nearWorkbench();
        for(int i=0;i<RECIPE_COUNT;i++){
            const Recipe& rec=RECIPES[i];
            Rect q=R(905,170+i*52,225,44);
            bool ok=canCraft(save.inventory,rec,bench);
            std::string name=itemName(rec.out);
            if(button(q,name,ok,ok?Color{0.31f,0.72f,0.39f,1}:Color{0.45f,0.49f,0.54f,1})){
                if(craft(save.inventory,rec,bench)){toast="制作成功";toastTime=1.3f;}
            }
        }
        if(!bench)r.text(X(905),Y(600),"高级配方需要工作台",14*scale(),{0.62f,0.66f,0.69f,1});
        if(button(R(1000,600,130,44),"关闭",true,{0.45f,0.49f,0.54f,1}))screen=Screen::Game;
        r.flushUI();r.present();
    }

    void renderPause(){
        Color sky=skyColor(save.dayTime);r.begin(sky);
        Vec3 right{},forward{};Mat4 mvp{};buildScene(right,forward,mvp);r.flush3D(mvp);
        r.rect({0,0,float(r.w),float(r.h)},{0.005f,0.008f,0.012f,0.66f});
        panel(R(390,125,500,465));
        r.textCentered(R(415,155,450,55),"暂停",34*scale(),{0.96f,0.72f,0.22f,1});
        if(button(R(500,240,280,56),"继续游戏",true,{0.31f,0.72f,0.39f,1}))screen=Screen::Game;
        if(button(R(500,312,280,56),"保存游戏",true)){writeSave();toast="已保存";toastTime=1.5f;}
        if(button(R(500,384,280,56),"设置",true)){settingsReturn=Screen::Pause;screen=Screen::Settings;}
        if(button(R(500,456,280,56),"主菜单",true,{0.82f,0.26f,0.25f,1})){writeSave();screen=Screen::Main;}
        r.flushUI();r.present();
    }

    void renderDeath(){
        r.begin({0.055f,0.018f,0.024f,1});
        std::string a=save.faith==int(Faith::Godless)?"故事终结":"神恩消散";
        std::string b=save.faith==int(Faith::Godless)?"无神者只有一条命":"神力不足，无法复活";
        title(a,b);
        panel(R(355,245,570,240));
        r.textCentered(R(375,295,530,52),"第 "+std::to_string(save.day)+" 天",27*scale(),{0.94f,0.95f,0.93f,1});
        if(button(R(495,402,290,58),"主菜单",true,{0.82f,0.26f,0.25f,1}))screen=Screen::Main;
        r.flushUI();r.present();
    }

    void render(){
        if(!r.ready)return;
        if(in.back){in.back=false;onBack();}
        switch(screen){
            case Screen::Splash:renderSplash();break;
            case Screen::Main:renderMain();break;
            case Screen::Saves:renderSaves();break;
            case Screen::FaithSelect:renderFaith();break;
            case Screen::CharacterCreate:renderCharacterCreate();break;
            case Screen::Settings:renderSettings();break;
            case Screen::About:renderAbout();break;
            case Screen::Game:renderGame();break;
            case Screen::Inventory:renderInventory();break;
            case Screen::Pause:renderPause();break;
            case Screen::Death:renderDeath();break;
        }
        in.tap=false;
    }

    void spawnDrop(ItemId id,int count,Vec3 p){
        if(id==ItemId::None||count<=0)return;
        drops.push_back({id,count,p,0,true});
    }

    void interact(){
        int px=int(save.px),pz=int(save.pz);
        float best=999;int bx=0,bz=0;WorldObject bo=WorldObject::None;
        for(int z=pz-2;z<=pz+2;z++)for(int x=px-2;x<=px+2;x++){
            WorldObject o=world.objectAt(x,z);if(o==WorldObject::None)continue;
            float dx=x+0.5f-save.px,dz=z+0.5f-save.pz,d=dx*dx+dz*dz;
            if(d<best&&d<5.f){best=d;bx=x;bz=z;bo=o;}
        }
        if(bo==WorldObject::None){toast="没有可交互目标";toastTime=1.1f;return;}
        ItemId tool=save.inventory.mainHand();
        Vec3 p{bx+0.5f,float(world.walkHeight(bx,bz))+0.25f,bz+0.5f};
        if(bo==WorldObject::Tree){
            int n=tool==ItemId::WoodAxe?5:2;spawnDrop(ItemId::Wood,n,p);spawnDrop(ItemId::Fiber,1,p+Vec3{0.18f,0,0});
            if(tool==ItemId::WoodAxe)save.inventory.wearMainDurability();
            toast="获得木材";
        }else if(bo==WorldObject::Rock){
            int n=tool==ItemId::StonePick?5:1;spawnDrop(ItemId::Stone,n,p);
            if(tool==ItemId::StonePick)save.inventory.wearMainDurability();
            toast="获得石料";
        }else if(bo==WorldObject::BerryBush){
            spawnDrop(ItemId::Berry,3,p);toast="获得浆果";
        }else{
            spawnDrop(ItemId::Fiber,3,p);toast="获得草纤维";
        }
        world.harvestObject(bx,bz);toastTime=1.3f;save.stamina=std::max(0.f,save.stamina-5.f);
    }

    void targetCell(int& tx,int& tz){
        tx=int(std::floor(save.px+facingX*1.6f));tz=int(std::floor(save.pz+facingZ*1.6f));
        tx=std::clamp(tx,1,WORLD_SIZE-2);tz=std::clamp(tz,1,WORLD_SIZE-2);
    }

    void dig(){
        int tx,tz;targetCell(tx,tz);int y=world.topSolidY(tx,tz);Block b=world.block(tx,y,tz);
        if(b==Block::Shrine||b==Block::Workbench||b==Block::Campfire){
            ItemId it=itemForBlock(b);if(it!=ItemId::None)spawnDrop(it,1,{tx+0.5f,float(y)+0.7f,tz+0.5f});
            world.setBlock(tx,y,tz,Block::Air);toast="已拆除";toastTime=1.f;return;
        }
        ItemId tool=save.inventory.mainHand();
        if((b==Block::Stone||b==Block::Ore)&&tool!=ItemId::StonePick){
            toast="石块需要石镐";toastTime=1.2f;return;
        }
        if(b==Block::Water||b==Block::Air){toast="没有可挖掘方块";toastTime=1.f;return;}
        ItemId it=itemForBlock(b);
        if(it==ItemId::None){
            if(b==Block::Grass||b==Block::Dirt)it=ItemId::DirtBlock;
            else if(b==Block::Sand)it=ItemId::SandBlock;
            else if(b==Block::Stone)it=ItemId::StoneBlock;
            else if(b==Block::Ore)it=ItemId::Ore;
        }
        world.setBlock(tx,y,tz,Block::Air);
        spawnDrop(it,1,{tx+0.5f,float(y)+0.8f,tz+0.5f});
        if(tool==ItemId::StonePick)save.inventory.wearMainDurability();
        save.stamina=std::max(0.f,save.stamina-6.f);toast="挖掘成功";toastTime=1.f;
    }

    void placeSelected(){
        ItemStack* st=save.inventory.hotbar();if(!st||!st->count)return;
        ItemId id=ItemId(st->id);Block b=blockForItem(id);if(b==Block::Air)return;
        int tx,tz;targetCell(tx,tz);int y=world.topSolidY(tx,tz)+1;
        if(y>=WORLD_Y-1){toast="无法放置";toastTime=1.f;return;}
        if(std::abs(float(tx)+0.5f-save.px)<0.7f&&std::abs(float(tz)+0.5f-save.pz)<0.7f){toast="不能放在角色位置";toastTime=1.f;return;}
        if(world.block(tx,y,tz)!=Block::Air){toast="无法放置";toastTime=1.f;return;}
        world.setBlock(tx,y,tz,b);save.inventory.consumeFromSlot(save.inventory.selectedHotbar,1);
        toast="放置成功";toastTime=1.f;
    }

    void attack(){
        ItemId weapon=save.inventory.mainHand();
        float dmg=weapon==ItemId::WoodSword?18.f:7.f;
        Slime* best=nullptr;float bd=999;
        for(auto& s:slimes)if(s.alive){
            float dx=s.pos.x-save.px,dz=s.pos.z-save.pz,d=std::sqrt(dx*dx+dz*dz);
            float front=(dx*facingX+dz*facingZ)/(d+1e-4f);
            if(d<2.3f&&front>0.15f&&d<bd){bd=d;best=&s;}
        }
        if(best){
            best->hp-=dmg;
            if(weapon==ItemId::WoodSword)save.inventory.wearMainDurability();
            if(best->hp<=0){best->alive=false;spawnDrop(ItemId::Berry,1,best->pos+Vec3{0,0.25f,0});toast="击败怪物";toastTime=1.2f;}
        }
        attackFlash=0.16f;save.stamina=std::max(0.f,save.stamina-4.f);
    }

    void jump(){
        if(grounded&&save.stamina>5.f){grounded=false;yVel=4.8f;save.stamina-=5.f;}
    }

    void dropInventory(int idx){
        if(idx<0||idx>=Inventory::SLOT_COUNT)return;
        ItemStack& st=save.inventory.slots[idx];if(!st.count)return;
        ItemId id=ItemId(st.id);
        spawnDrop(id,1,{save.px+facingX*0.8f,float(world.walkHeight(int(save.px),int(save.pz)))+0.35f,save.pz+facingZ*0.8f});
        save.inventory.consumeFromSlot(idx,1);
    }

    void pickupDrops(float dt){
        for(auto& d:drops)if(d.alive){
            d.bob+=dt*4.f;
            float dx=d.pos.x-save.px,dz=d.pos.z-save.pz,d2=dx*dx+dz*dz;
            if(d2<1.45f*1.45f){
                if(save.inventory.add(d.id,d.count)){d.alive=false;toast="拾取 "+std::string(itemName(d.id));toastTime=0.8f;}
            }
        }
        drops.erase(std::remove_if(drops.begin(),drops.end(),[](const Drop& d){return !d.alive;}),drops.end());
    }

    void updateSlimes(float dt){
        for(auto& s:slimes)if(s.alive){
            s.phase+=dt*4.f;s.hitCooldown=std::max(0.f,s.hitCooldown-dt);
            float dx=save.px-s.pos.x,dz=save.pz-s.pos.z,d=std::sqrt(dx*dx+dz*dz);
            if(d<7.f&&d>0.9f){
                float sp=0.62f*dt;s.pos.x+=dx/d*sp;s.pos.z+=dz/d*sp;
                int sx=int(s.pos.x),sz=int(s.pos.z);s.pos.y=float(world.walkHeight(sx,sz));
            }else if(d<=0.95f&&s.hitCooldown<=0){
                save.hp=std::max(0.f,save.hp-7.f);s.hitCooldown=1.15f;toast="受到攻击";toastTime=0.7f;
            }
        }
    }

    void simulate(float dt){
        if(screen==Screen::Splash){splashTime+=dt;return;}
        if(screen!=Screen::Game)return;
        toastTime=std::max(0.f,toastTime-dt);attackFlash=std::max(0.f,attackFlash-dt);

        float mag=std::sqrt(in.joyX*in.joyX+in.joyY*in.joyY);
        if(mag>0.08f){
            float sx=in.joyX/mag*std::min(1.f,mag),sy=in.joyY/mag*std::min(1.f,mag);
            float yaw=save.cameraYaw;
            Vec2 right{std::cos(yaw),-std::sin(yaw)};
            Vec2 forward{-std::sin(yaw),-std::cos(yaw)};
            float dx=right.x*sx+forward.x*(-sy);
            float dz=right.y*sx+forward.y*(-sy);
            float len=std::sqrt(dx*dx+dz*dz);if(len>1e-4f){dx/=len;dz/=len;facingX=dx;facingZ=dz;}
            float speed=2.75f*(0.60f+0.40f*save.stamina/100.f);
            float nx=save.px+dx*speed*dt,nz=save.pz+dz*speed*dt;
            int curH=world.walkHeight(int(save.px),int(save.pz)),newH=world.walkHeight(int(nx),int(nz));
            Block above=world.block(int(nx),newH,int(nz));
            bool water=world.baseHeight(int(nx),int(nz))<SEA_LEVEL;
            if(!water&&above==Block::Air&&newH-curH<=1){
                save.px=std::clamp(nx,1.5f,float(WORLD_SIZE)-2.f);
                save.pz=std::clamp(nz,1.5f,float(WORLD_SIZE)-2.f);
            }
            save.stamina=std::max(0.f,save.stamina-dt*2.7f);
        }else save.stamina=std::min(100.f,save.stamina+dt*5.2f);

        if(!grounded){
            yVel-=9.8f*dt;yOffset+=yVel*dt;
            if(yOffset<=0){yOffset=0;yVel=0;grounded=true;}
        }
        save.playerYOffset=yOffset;

        save.hunger=std::max(0.f,save.hunger-dt*0.055f);
        if(save.hunger<=0.01f)save.hp=std::max(0.f,save.hp-dt*2.0f);

        save.dayTime+=dt/360.f;
        if(save.dayTime>=1.f){save.dayTime-=1.f;save.day++;if(save.faith!=int(Faith::Godless))save.faithPower=std::min(100.f,save.faithPower+2.f);}

        pickupDrops(dt);updateSlimes(dt);
        autosave+=dt;if(autosave>30.f){autosave=0;writeSave();}

        if(save.hp<=0){
            if(save.faith==int(Faith::Mature)||(save.faith==int(Faith::Newborn)&&save.faithPower>=10.f)){
                if(save.faith==int(Faith::Newborn))save.faithPower-=10.f;
                save.hp=100;save.hunger=65;save.stamina=100;save.px=float(WORLD_SIZE/2)+0.5f;save.pz=float(WORLD_SIZE/2)+0.5f;
                yOffset=0;yVel=0;grounded=true;toast="神恩复生";toastTime=2.4f;writeSave();
            }else{
                if(save.faith==int(Faith::Godless))deleteSlot(slot);
                screen=Screen::Death;
            }
        }
    }

    int onInput(AInputEvent* event){
        int type=AInputEvent_getType(event);
        if(type==AINPUT_EVENT_TYPE_KEY){
            if(AKeyEvent_getKeyCode(event)==AKEYCODE_BACK&&AKeyEvent_getAction(event)==AKEY_EVENT_ACTION_UP){in.back=true;return 1;}
            return 0;
        }
        if(type!=AINPUT_EVENT_TYPE_MOTION)return 0;
        int action=AMotionEvent_getAction(event);
        int masked=action&AMOTION_EVENT_ACTION_MASK;
        int index=(action&AMOTION_EVENT_ACTION_POINTER_INDEX_MASK)>>AMOTION_EVENT_ACTION_POINTER_INDEX_SHIFT;
        int id=AMotionEvent_getPointerId(event,index);
        float x=AMotionEvent_getX(event,index),y=AMotionEvent_getY(event,index);

        if(masked==AMOTION_EVENT_ACTION_DOWN||masked==AMOTION_EVENT_ACTION_POINTER_DOWN){
            if(screen==Screen::Game&&x<r.w*0.38f&&y>r.h*0.47f&&in.joyId<0){
                in.joyId=id;in.joyBaseX=x;in.joyBaseY=y;in.joyX=in.joyY=0;return 1;
            }
            if(screen==Screen::Game&&x>r.w*0.38f&&y>r.h*0.20f&&in.camId<0){
                in.camId=id;in.camLastX=x;in.camLastY=y;in.camMoved=0;return 1;
            }
        }
        if(masked==AMOTION_EVENT_ACTION_MOVE){
            size_t n=AMotionEvent_getPointerCount(event);
            for(size_t i=0;i<n;i++){
                int pid=AMotionEvent_getPointerId(event,i);
                float px=AMotionEvent_getX(event,i),py=AMotionEvent_getY(event,i);
                if(pid==in.joyId){
                    float dx=px-in.joyBaseX,dy=py-in.joyBaseY,rad=70.f*scale();
                    float m=std::sqrt(dx*dx+dy*dy);if(m>rad){dx*=rad/m;dy*=rad/m;}
                    in.joyX=dx/rad;in.joyY=dy/rad;
                }else if(pid==in.camId){
                    float dx=px-in.camLastX,dy=py-in.camLastY;in.camLastX=px;in.camLastY=py;
                    in.camMoved+=std::abs(dx)+std::abs(dy);
                    save.cameraYaw-=dx*0.0065f;
                }
            }
            return 1;
        }
        if(masked==AMOTION_EVENT_ACTION_UP||masked==AMOTION_EVENT_ACTION_POINTER_UP){
            if(id==in.joyId){in.joyId=-1;in.joyX=in.joyY=0;return 1;}
            if(id==in.camId){
                bool wasTap=in.camMoved<18.f*scale();in.camId=-1;if(wasTap){in.tap=true;in.tapX=x;in.tapY=y;}return 1;
            }
            in.tap=true;in.tapX=x;in.tapY=y;return 1;
        }
        if(masked==AMOTION_EVENT_ACTION_CANCEL){in.joyId=in.camId=-1;in.joyX=in.joyY=0;return 1;}
        return 1;
    }

    void onCmd(int32_t cmd){
        switch(cmd){
            case APP_CMD_INIT_WINDOW:if(app->window&&!r.ready)r.init(app);break;
            case APP_CMD_TERM_WINDOW:if(r.ready)r.term();break;
            case APP_CMD_PAUSE:case APP_CMD_SAVE_STATE:if(screen==Screen::Game||screen==Screen::Inventory||screen==Screen::Pause)writeSave();break;
            default:break;
        }
    }
};

static void handleCmd(android_app* app,int32_t cmd){
    auto* g=reinterpret_cast<Game*>(app->userData);if(g)g->onCmd(cmd);
}
static int32_t handleInput(android_app* app,AInputEvent* e){
    auto* g=reinterpret_cast<Game*>(app->userData);return g?g->onInput(e):0;
}

} // namespace fb

void android_main(android_app* app){
    fb::Game game(app);
    app->userData=&game;app->onAppCmd=fb::handleCmd;app->onInputEvent=fb::handleInput;

    using Clock=std::chrono::steady_clock;
    auto last=Clock::now();double acc=0;constexpr double step=1.0/60.0;

    while(!app->destroyRequested){
        int events=0;android_poll_source* source=nullptr;
        int timeout=game.r.ready?0:-1;
        while(ALooper_pollOnce(timeout,nullptr,&events,reinterpret_cast<void**>(&source))>=0){
            if(source)source->process(app,source);
            if(app->destroyRequested)break;
            timeout=0;
        }
        if(app->destroyRequested)break;
        if(!game.r.ready)continue;

        auto now=Clock::now();double dt=std::chrono::duration<double>(now-last).count();last=now;
        dt=std::min(dt,0.10);acc+=dt;int guard=0;
        while(acc>=step&&guard++<8){game.simulate(float(step));acc-=step;}
        game.render();
    }
    if(game.r.ready)game.r.term();
}
