#pragma once
#include "math3d.hpp"
#include "voxel_world.hpp"
#include <array>
#include <cstdint>
#include <cmath>
#include <algorithm>

namespace fb {

enum class WeatherType : uint8_t { Clear=0, Cloudy, Rain, Storm, Fog };
enum class Biome : uint8_t { Plains=0, Forest, Coast, Highland, Dryland };
enum class NpcRole : uint8_t { Villager=0, Merchant, Guard, Lumberjack, Farmer };

struct Attributes {
    uint8_t strength=5;
    uint8_t agility=5;
    uint8_t vitality=5;
    uint8_t intelligence=5;
    uint8_t willpower=5;
    uint8_t charisma=5;
    uint8_t luck=5;
};

struct Personality {
    // 0..100
    uint8_t bravery=50;
    uint8_t sociability=50;
    uint8_t discipline=50;
    uint8_t curiosity=50;
    uint8_t empathy=50;
};

struct Skills {
    float gathering=0;
    float mining=0;
    float combat=0;
    float crafting=0;
    float survival=0;
    float social=0;
};

struct Needs {
    float thirst=100;
    float sanity=100;
    float mood=70;
    float bodyTemp=37.0f;
};

struct WeatherState {
    WeatherType type=WeatherType::Clear;
    float intensity=0;
    float temperatureC=22;
    float humidity=0.45f;
    float wind=0.18f;
    float timer=0;
};

struct SettlementAnchor {
    int x=0,z=0;
    uint8_t size=0; // 0 camp 1 hamlet 2 village
};

struct NpcState {
    uint32_t id=0;
    float x=0,z=0;
    NpcRole role=NpcRole::Villager;
    Personality personality{};
    int16_t relation=0;
    int coins=30;
    float mood=65;
    float wanderPhase=0;
};

inline const char* weatherName(WeatherType t){
    switch(t){
        case WeatherType::Clear:return "晴朗";
        case WeatherType::Cloudy:return "多云";
        case WeatherType::Rain:return "小雨";
        case WeatherType::Storm:return "暴雨";
        case WeatherType::Fog:return "雾";
        default:return "晴朗";
    }
}
inline const char* roleName(NpcRole r){
    switch(r){
        case NpcRole::Merchant:return "商人";
        case NpcRole::Guard:return "守卫";
        case NpcRole::Lumberjack:return "伐木工";
        case NpcRole::Farmer:return "农夫";
        default:return "居民";
    }
}
inline const char* biomeName(Biome b){
    switch(b){
        case Biome::Forest:return "森林";
        case Biome::Coast:return "海岸";
        case Biome::Highland:return "高地";
        case Biome::Dryland:return "旱地";
        default:return "平原";
    }
}

inline Biome biomeAt(uint64_t seed,int x,int z,int height,float moisture){
    if(height<=SEA_LEVEL+1)return Biome::Coast;
    float temp=valueNoise(seed+0x7342,float(x)*0.014f,float(z)*0.014f,77);
    if(height>=12)return Biome::Highland;
    if(moisture>0.62f)return Biome::Forest;
    if(moisture<0.30f || temp>0.76f)return Biome::Dryland;
    return Biome::Plains;
}

inline float ambientTemperature(Biome b,float dayTime,WeatherType w,int height){
    float dayWave=std::sin((dayTime-0.25f)*6.2831853f);
    float base=22.f+dayWave*5.f-float(std::max(0,height-8))*0.65f;
    if(b==Biome::Highland)base-=4.f;
    if(b==Biome::Coast)base-=1.f;
    if(b==Biome::Dryland)base+=4.f;
    if(w==WeatherType::Rain)base-=3.f;
    if(w==WeatherType::Storm)base-=5.f;
    if(w==WeatherType::Fog)base-=2.f;
    return base;
}

inline WeatherState makeWeather(uint64_t seed,int day,float dayTime){
    uint32_t h=hash32(seed ^ uint64_t(day)*0x9e3779b9u ^ uint64_t(int(dayTime*8))*0x85ebca6bu);
    int roll=int(h%100);
    WeatherState s{};
    if(roll<48)s.type=WeatherType::Clear;
    else if(roll<68)s.type=WeatherType::Cloudy;
    else if(roll<86)s.type=WeatherType::Rain;
    else if(roll<94)s.type=WeatherType::Fog;
    else s.type=WeatherType::Storm;
    s.intensity=(s.type==WeatherType::Storm)?0.95f:(s.type==WeatherType::Rain?0.60f:(s.type==WeatherType::Fog?0.45f:0.15f));
    s.humidity=(s.type==WeatherType::Rain||s.type==WeatherType::Storm)?0.92f:(s.type==WeatherType::Fog?0.86f:0.45f);
    s.wind=(s.type==WeatherType::Storm)?0.88f:(s.type==WeatherType::Rain?0.46f:0.20f);
    s.timer=45.f+float((h>>8)%90);
    return s;
}

inline std::array<SettlementAnchor,3> settlementAnchors(uint64_t seed){
    const int c=WORLD_SIZE/2;
    uint32_t h=hash32(seed^0xA17E991u);
    std::array<SettlementAnchor,3> a{};
    a[0]={c+18,c-7,2};
    a[1]={c-30,c+22,1};
    a[2]={c+42,c+35,1};
    a[1].x+=int((h&7))-3;a[1].z+=int((h>>3)&7)-3;
    a[2].x+=int((h>>6)&7)-3;a[2].z+=int((h>>9)&7)-3;
    return a;
}

inline float pointSegmentDistance(float px,float pz,float ax,float az,float bx,float bz){
    float vx=bx-ax,vz=bz-az,wx=px-ax,wz=pz-az;
    float vv=vx*vx+vz*vz;
    float t=vv>0?std::clamp((wx*vx+wz*vz)/vv,0.f,1.f):0.f;
    float dx=px-(ax+vx*t),dz=pz-(az+vz*t);
    return std::sqrt(dx*dx+dz*dz);
}

inline bool proceduralRoad(uint64_t seed,int x,int z){
    auto a=settlementAnchors(seed);
    const int c=WORLD_SIZE/2;
    float d0=pointSegmentDistance(float(x),float(z),float(c),float(c),float(a[0].x),float(a[0].z));
    float d1=pointSegmentDistance(float(x),float(z),float(a[0].x),float(a[0].z),float(a[1].x),float(a[1].z));
    float d2=pointSegmentDistance(float(x),float(z),float(a[0].x),float(a[0].z),float(a[2].x),float(a[2].z));
    return std::min({d0,d1,d2})<0.72f;
}

inline Personality randomPersonality(uint64_t seed,uint32_t id){
    auto v=[&](int salt){ return uint8_t(25+(hash32(seed^uint64_t(id*41+salt*137))%66)); };
    return {v(1),v(2),v(3),v(4),v(5)};
}

inline Attributes randomAttributes(uint64_t seed){
    Attributes a{};
    auto v=[&](int salt){ return uint8_t(4+(hash32(seed^uint64_t(salt*199))%5)); };
    a.strength=v(1);a.agility=v(2);a.vitality=v(3);a.intelligence=v(4);
    a.willpower=v(5);a.charisma=v(6);a.luck=v(7);
    return a;
}

inline float tradeModifier(uint8_t charisma,int relation,uint8_t sociability){
    float c=(float(charisma)-5.f)*0.025f;
    float r=float(relation)*0.0025f;
    float s=(float(sociability)-50.f)*0.0015f;
    return std::clamp(1.f-c-r-s,0.72f,1.28f);
}

} // namespace fb
