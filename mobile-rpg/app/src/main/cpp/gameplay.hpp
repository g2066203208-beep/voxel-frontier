#pragma once
#include "world_sim.hpp"
#include <array>
#include <cstdint>
#include <algorithm>

namespace fb {

enum class Faith : int32_t { Mature=0, Newborn=1, Godless=2 };

enum class ItemId : uint16_t {
    None=0,
    Wood, Stone, Berry, Fiber, DirtBlock, StoneBlock, SandBlock, Ore,
    WoodAxe, StonePick, WoodSword, Torch,
    Workbench, Campfire,
    ClothHat, ClothTunic,
    Coin, WaterFlask, RawMeat, CookedMeat, Seed, Wheat,
    IronBar, IronAxe, IronPick, IronSword,
    Furnace, Chest, Hoe, Bread
};

enum class EquipSlot : uint8_t { Head=0, Body=1, Main=2, Off=3 };

struct ItemStack {
    uint16_t id=uint16_t(ItemId::None);
    uint16_t count=0;
    uint16_t durability=0;
    uint16_t flags=0;
};

inline bool isStackable(ItemId id){
    switch(id){
        case ItemId::WoodAxe: case ItemId::StonePick: case ItemId::WoodSword:
        case ItemId::IronAxe: case ItemId::IronPick: case ItemId::IronSword:
        case ItemId::Torch: case ItemId::ClothHat: case ItemId::ClothTunic:
        case ItemId::WaterFlask: case ItemId::Hoe:
            return false;
        default:return id!=ItemId::None;
    }
}
inline uint16_t maxStack(ItemId id){
    if(id==ItemId::Coin)return 999;
    return isStackable(id)?99:1;
}
inline uint16_t maxDurability(ItemId id){
    switch(id){
        case ItemId::WoodAxe:return 80;
        case ItemId::StonePick:return 110;
        case ItemId::WoodSword:return 90;
        case ItemId::IronAxe:return 240;
        case ItemId::IronPick:return 280;
        case ItemId::IronSword:return 260;
        case ItemId::Torch:return 65;
        case ItemId::Hoe:return 160;
        case ItemId::WaterFlask:return 100;
        default:return 0;
    }
}
inline bool isTool(ItemId id){
    return id==ItemId::WoodAxe||id==ItemId::StonePick||id==ItemId::WoodSword||
           id==ItemId::IronAxe||id==ItemId::IronPick||id==ItemId::IronSword||
           id==ItemId::Torch||id==ItemId::Hoe;
}
inline bool isWearable(ItemId id){ return id==ItemId::ClothHat||id==ItemId::ClothTunic; }
inline bool isPlaceable(ItemId id){
    return id==ItemId::DirtBlock||id==ItemId::StoneBlock||id==ItemId::SandBlock||
           id==ItemId::Workbench||id==ItemId::Campfire||id==ItemId::Furnace||id==ItemId::Chest;
}
inline bool isFood(ItemId id){
    return id==ItemId::Berry||id==ItemId::CookedMeat||id==ItemId::Bread;
}
inline bool isDrink(ItemId id){ return id==ItemId::WaterFlask; }

inline Block blockForItem(ItemId id){
    switch(id){
        case ItemId::DirtBlock:return Block::Dirt;
        case ItemId::StoneBlock:return Block::Stone;
        case ItemId::SandBlock:return Block::Sand;
        case ItemId::Workbench:return Block::Workbench;
        case ItemId::Campfire:return Block::Campfire;
        default:return Block::Air;
    }
}
inline ItemId itemForBlock(Block b){
    switch(b){
        case Block::Dirt:return ItemId::DirtBlock;
        case Block::Stone:return ItemId::StoneBlock;
        case Block::Sand:return ItemId::SandBlock;
        case Block::Ore:return ItemId::Ore;
        case Block::Workbench:return ItemId::Workbench;
        case Block::Campfire:return ItemId::Campfire;
        default:return ItemId::None;
    }
}
inline const char* itemName(ItemId id){
    switch(id){
        case ItemId::Wood:return "木材";
        case ItemId::Stone:return "石料";
        case ItemId::Berry:return "浆果";
        case ItemId::Fiber:return "草纤维";
        case ItemId::DirtBlock:return "泥土";
        case ItemId::StoneBlock:return "石块";
        case ItemId::SandBlock:return "沙子";
        case ItemId::Ore:return "矿石";
        case ItemId::WoodAxe:return "木斧";
        case ItemId::StonePick:return "石镐";
        case ItemId::WoodSword:return "木剑";
        case ItemId::Torch:return "火把";
        case ItemId::Workbench:return "工作台";
        case ItemId::Campfire:return "营火";
        case ItemId::ClothHat:return "布帽";
        case ItemId::ClothTunic:return "布衣";
        case ItemId::Coin:return "铜币";
        case ItemId::WaterFlask:return "水壶";
        case ItemId::RawMeat:return "生肉";
        case ItemId::CookedMeat:return "烤肉";
        case ItemId::Seed:return "种子";
        case ItemId::Wheat:return "小麦";
        case ItemId::IronBar:return "铁锭";
        case ItemId::IronAxe:return "铁斧";
        case ItemId::IronPick:return "铁镐";
        case ItemId::IronSword:return "铁剑";
        case ItemId::Furnace:return "熔炉";
        case ItemId::Chest:return "木箱";
        case ItemId::Hoe:return "锄头";
        case ItemId::Bread:return "面包";
        default:return "空";
    }
}

struct Inventory {
    static constexpr int SLOT_COUNT=30;
    static constexpr int HOTBAR_COUNT=8;
    std::array<ItemStack,SLOT_COUNT> slots{};
    std::array<ItemStack,4> equipment{};
    int selectedHotbar=0;
    int selectedInventory=-1;

    int count(ItemId id) const {
        int n=0; for(const auto& s:slots) if(ItemId(s.id)==id)n+=s.count;
        return n;
    }
    bool add(ItemId id,int amount,uint16_t durability=0){
        if(id==ItemId::None||amount<=0)return false;
        if(durability==0)durability=maxDurability(id);
        if(isStackable(id)){
            for(auto& s:slots) if(ItemId(s.id)==id&&s.count<maxStack(id)){
                int take=std::min<int>(amount,maxStack(id)-s.count);
                s.count=uint16_t(s.count+take);amount-=take;if(amount<=0)return true;
            }
        }
        for(auto& s:slots) if(s.count==0||ItemId(s.id)==ItemId::None){
            int take=std::min<int>(amount,maxStack(id));
            s.id=uint16_t(id);s.count=uint16_t(take);s.durability=durability;amount-=take;
            if(amount<=0)return true;
        }
        return amount<=0;
    }
    bool remove(ItemId id,int amount){
        if(amount<=0)return true;
        for(auto& s:slots) if(ItemId(s.id)==id&&s.count){
            int take=std::min<int>(amount,s.count);s.count=uint16_t(s.count-take);amount-=take;
            if(s.count==0)s={};if(amount<=0)return true;
        }
        return false;
    }
    bool consumeFromSlot(int idx,int amount=1){
        if(idx<0||idx>=SLOT_COUNT||slots[idx].count<amount)return false;
        slots[idx].count=uint16_t(slots[idx].count-amount);if(slots[idx].count==0)slots[idx]={};return true;
    }
    ItemStack* hotbar(){return &slots[selectedHotbar];}
    const ItemStack* hotbar()const{return &slots[selectedHotbar];}

    bool equipFrom(int idx){
        if(idx<0||idx>=SLOT_COUNT||slots[idx].count==0)return false;
        ItemId id=ItemId(slots[idx].id);int e=-1;
        if(id==ItemId::ClothHat)e=int(EquipSlot::Head);
        else if(id==ItemId::ClothTunic)e=int(EquipSlot::Body);
        else if(isTool(id))e=int(EquipSlot::Main);
        else return false;
        ItemStack incoming=slots[idx];incoming.count=1;consumeFromSlot(idx,1);
        if(equipment[e].count)add(ItemId(equipment[e].id),1,equipment[e].durability);
        equipment[e]=incoming;return true;
    }
    bool unequip(int e){
        if(e<0||e>=4||equipment[e].count==0)return false;
        if(!add(ItemId(equipment[e].id),1,equipment[e].durability))return false;
        equipment[e]={};return true;
    }
    ItemId mainHand()const{
        if(equipment[int(EquipSlot::Main)].count)return ItemId(equipment[int(EquipSlot::Main)].id);
        if(hotbar()->count)return ItemId(hotbar()->id);
        return ItemId::None;
    }
    void wearMainDurability(int amount=1){
        auto& e=equipment[int(EquipSlot::Main)];ItemStack* s=e.count?&e:hotbar();
        if(!s||!s->count||s->durability==0)return;
        s->durability=uint16_t(s->durability>amount?s->durability-amount:0);if(s->durability==0)*s={};
    }
};

enum class CraftTier : uint8_t { Hand=0, Bench=1, Furnace=2, Campfire=3 };

struct Recipe {
    ItemId out; uint16_t outCount;
    ItemId a; uint16_t aCount;
    ItemId b; uint16_t bCount;
    CraftTier tier=CraftTier::Hand;
};
static constexpr Recipe RECIPES[] = {
    {ItemId::WoodAxe,1,ItemId::Wood,5,ItemId::Fiber,2,CraftTier::Hand},
    {ItemId::StonePick,1,ItemId::Wood,4,ItemId::Stone,6,CraftTier::Hand},
    {ItemId::WoodSword,1,ItemId::Wood,6,ItemId::Stone,2,CraftTier::Hand},
    {ItemId::Torch,1,ItemId::Wood,2,ItemId::Fiber,2,CraftTier::Hand},
    {ItemId::Workbench,1,ItemId::Wood,10,ItemId::Stone,4,CraftTier::Hand},
    {ItemId::Campfire,1,ItemId::Wood,5,ItemId::Stone,6,CraftTier::Hand},
    {ItemId::WaterFlask,1,ItemId::Fiber,4,ItemId::Wood,2,CraftTier::Bench},
    {ItemId::Hoe,1,ItemId::Wood,4,ItemId::Stone,3,CraftTier::Bench},
    {ItemId::Chest,1,ItemId::Wood,14,ItemId::Fiber,3,CraftTier::Bench},
    {ItemId::Furnace,1,ItemId::Stone,18,ItemId::Ore,4,CraftTier::Bench},
    {ItemId::ClothHat,1,ItemId::Fiber,8,ItemId::Wood,1,CraftTier::Bench},
    {ItemId::ClothTunic,1,ItemId::Fiber,14,ItemId::Wood,2,CraftTier::Bench},
    {ItemId::IronBar,1,ItemId::Ore,3,ItemId::Wood,2,CraftTier::Furnace},
    {ItemId::IronAxe,1,ItemId::IronBar,4,ItemId::Wood,3,CraftTier::Bench},
    {ItemId::IronPick,1,ItemId::IronBar,5,ItemId::Wood,3,CraftTier::Bench},
    {ItemId::IronSword,1,ItemId::IronBar,5,ItemId::Wood,2,CraftTier::Bench},
    {ItemId::CookedMeat,1,ItemId::RawMeat,1,ItemId::Wood,1,CraftTier::Campfire},
    {ItemId::Bread,1,ItemId::Wheat,3,ItemId::Wood,1,CraftTier::Campfire}
};
static constexpr int RECIPE_COUNT=int(sizeof(RECIPES)/sizeof(RECIPES[0]));

struct CraftContext { bool bench=false; bool furnace=false; bool campfire=false; };

inline bool tierAvailable(CraftTier t,const CraftContext& c){
    if(t==CraftTier::Hand)return true;
    if(t==CraftTier::Bench)return c.bench;
    if(t==CraftTier::Furnace)return c.furnace;
    if(t==CraftTier::Campfire)return c.campfire;
    return false;
}
inline bool canCraft(const Inventory& inv,const Recipe& r,const CraftContext& c){
    return tierAvailable(r.tier,c)&&inv.count(r.a)>=r.aCount&&inv.count(r.b)>=r.bCount;
}
inline bool craft(Inventory& inv,const Recipe& r,const CraftContext& c){
    if(!canCraft(inv,r,c))return false;
    inv.remove(r.a,r.aCount);inv.remove(r.b,r.bCount);return inv.add(r.out,r.outCount);
}

constexpr uint32_t SAVE_MAGIC_V3=0x46425633u;
constexpr uint32_t MAX_SAVE_EDITS=512;
constexpr uint32_t MAX_SAVE_HARVEST=512;
constexpr uint32_t MAX_SAVE_NPCS=12;

struct SaveDataV3 {
    uint32_t magic=SAVE_MAGIC_V3;
    uint32_t version=3;
    uint64_t seed=1;
    int32_t faith=0;
    int32_t body=0,skin=1,hair=0,outfit=0;
    float px=float(WORLD_SIZE/2)+0.5f;
    float pz=float(WORLD_SIZE/2)+0.5f;
    float playerYOffset=0;
    float hp=100,hunger=100,stamina=100,faithPower=100;
    float dayTime=0.28f;
    int32_t day=1;
    float cameraYaw=0.78f;
    int32_t quality=1;
    Attributes attributes{};
    Personality personality{};
    Skills skills{};
    Needs needs{};
    WeatherState weather{};
    Inventory inventory{};
    uint32_t npcCount=0;
    std::array<NpcState,MAX_SAVE_NPCS> npcs{};
    uint32_t editCount=0;
    std::array<BlockEdit,MAX_SAVE_EDITS> edits{};
    uint32_t harvestCount=0;
    std::array<HarvestEdit,MAX_SAVE_HARVEST> harvest{};
    uint32_t checksum=0;
};

inline uint32_t checksumSave(const SaveDataV3& s){
    const uint8_t* p=reinterpret_cast<const uint8_t*>(&s);uint32_t h=2166136261u;
    for(size_t i=0;i<sizeof(SaveDataV3)-sizeof(uint32_t);i++){h^=p[i];h*=16777619u;}return h;
}

} // namespace fb
