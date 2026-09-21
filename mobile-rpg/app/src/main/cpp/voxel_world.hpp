#pragma once
#include "math3d.hpp"
#include <array>
#include <unordered_map>
#include <unordered_set>
#include <cstdint>
#include <cmath>
#include <algorithm>

namespace fb {

constexpr int WORLD_SIZE = 512;
constexpr int WORLD_Y = 32;
constexpr int CHUNK = 16;
constexpr int CHUNK_CACHE = 72;
constexpr int WORLD_CHUNKS = WORLD_SIZE / CHUNK;
constexpr int SEA_LEVEL = 6;

enum class Block : uint8_t {
    Air=0, Grass, Dirt, Stone, Sand, Water, Ore, Workbench, Campfire, Shrine
};

enum class WorldObject : uint8_t {
    None=0, Tree, Rock, BerryBush, GrassTuft
};

inline bool isSolid(Block b){
    return b!=Block::Air && b!=Block::Water;
}
inline bool isTransparent(Block b){
    return b==Block::Air || b==Block::Water;
}

inline uint32_t hash32(uint64_t x){
    x ^= x >> 33; x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return uint32_t(x ^ (x>>32));
}
inline float hash01(uint64_t seed,int x,int z,int salt=0){
    uint64_t v=seed ^ (uint64_t(uint32_t(x))*0x9E3779B185EBCA87ULL)
                     ^ (uint64_t(uint32_t(z))*0xC2B2AE3D27D4EB4FULL)
                     ^ (uint64_t(uint32_t(salt))*0x165667B19E3779F9ULL);
    return float(hash32(v)&0x00ffffffu)/float(0x01000000u);
}
inline float smooth01(float t){ return t*t*(3.f-2.f*t); }
inline float valueNoise(uint64_t seed,float x,float z,int salt){
    int x0=int(std::floor(x)), z0=int(std::floor(z));
    float tx=smooth01(x-float(x0)), tz=smooth01(z-float(z0));
    float a=hash01(seed,x0,z0,salt), b=hash01(seed,x0+1,z0,salt);
    float c=hash01(seed,x0,z0+1,salt), d=hash01(seed,x0+1,z0+1,salt);
    float ab=a+(b-a)*tx, cd=c+(d-c)*tx;
    return ab+(cd-ab)*tz;
}

struct ChunkData {
    bool valid=false;
    int cx=0,cz=0;
    uint64_t stamp=0;
    std::array<uint8_t,CHUNK*WORLD_Y*CHUNK> blocks{};
};

struct BlockEdit { uint32_t key=0; uint8_t value=0; };
struct HarvestEdit { uint32_t key=0; uint8_t value=0; };

class VoxelWorld {
public:
    uint64_t seed=1;
    uint64_t stamp=1;
    std::array<ChunkData,CHUNK_CACHE> cache{};
    std::array<int16_t,WORLD_CHUNKS*WORLD_CHUNKS> chunkSlots{};
    std::unordered_map<uint32_t,uint8_t> edits;
    std::unordered_set<uint32_t> harvested;

    void reset(uint64_t s){
        seed=s?s:1; stamp=1; edits.clear(); harvested.clear();
        for(auto& c:cache)c.valid=false;
        chunkSlots.fill(int16_t(-1));
    }

    static uint32_t key(int x,int y,int z){
        return (uint32_t(x)&0x1ffu) | ((uint32_t(z)&0x1ffu)<<9) | ((uint32_t(y)&0x1fu)<<18);
    }
    static uint32_t objectKey(int x,int z){
        return (uint32_t(x)&0x1ffu) | ((uint32_t(z)&0x1ffu)<<9);
    }
    static void decodeKey(uint32_t k,int& x,int& y,int& z){
        x=int(k&0x1ffu); z=int((k>>9)&0x1ffu); y=int((k>>18)&0x1fu);
    }

    int baseHeight(int x,int z) const {
        const int c=WORLD_SIZE/2;
        float dx=float(x-c), dz=float(z-c);
        if(dx*dx+dz*dz<64.f) return 8;
        float n1=valueNoise(seed,float(x)*0.018f,float(z)*0.018f,1);
        float n2=valueNoise(seed,float(x)*0.052f,float(z)*0.052f,2);
        float ridge=std::abs(valueNoise(seed,float(x)*0.010f,float(z)*0.010f,3)*2.f-1.f);
        float h=5.0f+n1*6.3f+n2*2.2f+ridge*1.8f;
        return std::clamp(int(std::round(h)),3,WORLD_Y-6);
    }

    float moisture(int x,int z) const {
        return 0.68f*valueNoise(seed,float(x)*0.021f,float(z)*0.021f,11)
             + 0.32f*valueNoise(seed,float(x)*0.071f,float(z)*0.071f,12);
    }

    Block generatedBlockForHeight(int x,int y,int z,int h) const {
        if(y>h){
            if(y<=SEA_LEVEL) return Block::Water;
            return Block::Air;
        }

        // Shallow caves stay away from the first three surface blocks.
        if(y<h-3 && y>1){
            float cave=valueNoise(seed+0xBEEF,float(x)*0.105f+float(y)*0.19f,float(z)*0.105f-float(y)*0.13f,23);
            float cave2=valueNoise(seed+0xCAFE,float(x)*0.16f,float(z)*0.16f+float(y)*0.17f,24);
            if(cave>0.69f && cave2>0.47f) return Block::Air;
        }

        if(y==h){
            if(h<=SEA_LEVEL+1) return Block::Sand;
            if(h>=12) return Block::Stone;
            return Block::Grass;
        }
        if(y>=h-2){
            return (h<=SEA_LEVEL+1)?Block::Sand:Block::Dirt;
        }
        if(hash01(seed+44,x*3+y,z*5-y,31)>0.965f && y<12) return Block::Ore;
        return Block::Stone;
    }

    Block generatedBlock(int x,int y,int z) const {
        if(x<0||z<0||x>=WORLD_SIZE||z>=WORLD_SIZE||y<0||y>=WORLD_Y) return Block::Air;
        return generatedBlockForHeight(x,y,z,baseHeight(x,z));
    }

    void generateChunk(ChunkData& c,int cx,int cz){
        c.valid=true;c.cx=cx;c.cz=cz;c.stamp=stamp;
        for(int lz=0;lz<CHUNK;lz++) for(int lx=0;lx<CHUNK;lx++){
            int x=cx*CHUNK+lx,z=cz*CHUNK+lz;
            int h=baseHeight(x,z);
            for(int y=0;y<WORLD_Y;y++){
                int i=(y*CHUNK+lz)*CHUNK+lx;
                c.blocks[size_t(i)]=uint8_t(generatedBlockForHeight(x,y,z,h));
            }
        }
    }

    ChunkData& chunk(int cx,int cz){
        stamp++;
        const int mapIndex=cz*WORLD_CHUNKS+cx;
        int cached=int(chunkSlots[size_t(mapIndex)]);
        if(cached>=0&&cached<CHUNK_CACHE){
            ChunkData& hit=cache[size_t(cached)];
            if(hit.valid&&hit.cx==cx&&hit.cz==cz){hit.stamp=stamp;return hit;}
            chunkSlots[size_t(mapIndex)]=int16_t(-1);
        }

        int victimIndex=0;
        for(int i=0;i<CHUNK_CACHE;i++){
            if(!cache[size_t(i)].valid){victimIndex=i;break;}
            if(cache[size_t(i)].stamp<cache[size_t(victimIndex)].stamp)victimIndex=i;
        }
        ChunkData& victim=cache[size_t(victimIndex)];
        if(victim.valid&&victim.cx>=0&&victim.cz>=0&&victim.cx<WORLD_CHUNKS&&victim.cz<WORLD_CHUNKS){
            chunkSlots[size_t(victim.cz*WORLD_CHUNKS+victim.cx)]=int16_t(-1);
        }
        generateChunk(victim,cx,cz);
        chunkSlots[size_t(mapIndex)]=int16_t(victimIndex);
        return victim;
    }

    Block block(int x,int y,int z){
        if(x<0||z<0||x>=WORLD_SIZE||z>=WORLD_SIZE||y<0||y>=WORLD_Y) return Block::Air;
        uint32_t k=key(x,y,z);
        auto it=edits.find(k);
        if(it!=edits.end()) return Block(it->second);
        int cx=x/CHUNK,cz=z/CHUNK,lx=x%CHUNK,lz=z%CHUNK;
        ChunkData& c=chunk(cx,cz);
        return Block(c.blocks[size_t((y*CHUNK+lz)*CHUNK+lx)]);
    }

    void setBlock(int x,int y,int z,Block b){
        if(x<0||z<0||x>=WORLD_SIZE||z>=WORLD_SIZE||y<0||y>=WORLD_Y) return;
        edits[key(x,y,z)]=uint8_t(b);
    }

    int topSolidY(int x,int z){
        for(int y=WORLD_Y-1;y>=0;y--){
            Block b=block(x,y,z);
            if(isSolid(b)) return y;
        }
        return 0;
    }

    int walkHeight(int x,int z){
        return topSolidY(x,z)+1;
    }

    bool waterAtSurface(int x,int z){
        int h=topSolidY(x,z);
        return block(x,std::min(WORLD_Y-1,h+1),z)==Block::Water || baseHeight(x,z)<SEA_LEVEL;
    }

    WorldObject objectAt(int x,int z) const {
        if(x<2||z<2||x>=WORLD_SIZE-2||z>=WORLD_SIZE-2) return WorldObject::None;
        if(harvested.count(objectKey(x,z))) return WorldObject::None;
        const int c=WORLD_SIZE/2;
        float ds=float((x-c)*(x-c)+(z-c)*(z-c));
        if(ds<49.f) return WorldObject::None;
        int h=baseHeight(x,z);
        if(h<=SEA_LEVEL || h>=13) return WorldObject::None;
        float m=moisture(x,z);
        float r=hash01(seed+900,x,z,6);
        if(m>0.57f && r<0.105f) return WorldObject::Tree;
        if(r>=0.105f&&r<0.137f) return WorldObject::Rock;
        if(m>0.46f&&r>=0.137f&&r<0.168f) return WorldObject::BerryBush;
        if(r>=0.168f&&r<0.205f) return WorldObject::GrassTuft;
        return WorldObject::None;
    }

    void harvestObject(int x,int z){ harvested.insert(objectKey(x,z)); }

    void exportEdits(BlockEdit* out,uint32_t cap,uint32_t& count) const {
        count=0;
        for(const auto& [k,v]:edits){ if(count>=cap) break; out[count++]={k,v}; }
    }
    void importEdits(const BlockEdit* in,uint32_t count){
        edits.clear();
        for(uint32_t i=0;i<count;i++) edits[in[i].key]=in[i].value;
    }
    void exportHarvest(HarvestEdit* out,uint32_t cap,uint32_t& count) const {
        count=0;
        for(uint32_t k:harvested){ if(count>=cap) break; out[count++]={k,1}; }
    }
    void importHarvest(const HarvestEdit* in,uint32_t count){
        harvested.clear();
        for(uint32_t i=0;i<count;i++) if(in[i].value) harvested.insert(in[i].key);
    }
};

inline Color blockColor(Block b){
    switch(b){
        case Block::Grass:return {0.27f,0.61f,0.25f,1};
        case Block::Dirt:return {0.43f,0.29f,0.16f,1};
        case Block::Stone:return {0.42f,0.44f,0.46f,1};
        case Block::Sand:return {0.72f,0.63f,0.36f,1};
        case Block::Water:return {0.14f,0.43f,0.71f,0.76f};
        case Block::Ore:return {0.38f,0.48f,0.62f,1};
        case Block::Workbench:return {0.48f,0.28f,0.11f,1};
        case Block::Campfire:return {0.72f,0.28f,0.08f,1};
        case Block::Shrine:return {0.68f,0.68f,0.63f,1};
        default:return {0,0,0,0};
    }
}

} // namespace fb
