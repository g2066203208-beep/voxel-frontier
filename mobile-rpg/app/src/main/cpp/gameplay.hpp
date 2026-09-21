#pragma once
#include "voxel_world.hpp"
#include <array>
#include <cstdint>
#include <string_view>
#include <algorithm>

namespace fb {

enum class Faith : int32_t { Mature=0, Newborn=1, Godless=2 };

enum class ItemId : uint16_t {
    None=0,
    Wood, Stone, Berry, Fiber, DirtBlock, StoneBlock, SandBlock, Ore,
    WoodAxe, StonePick, WoodSword, Torch,
    Workbench, Campfire,
    ClothHat, ClothTunic
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
        case ItemId::Torch: case ItemId::ClothHat: case ItemId::ClothTunic:
            return false;
        default:return id!=ItemId::None;
    }
}
inline uint16_t maxStack(ItemId id){ return isStackable(id)?99:1; }
inline uint16_t maxDurability(ItemId id){
    switch(id){
        case ItemId::WoodAxe:return 80;
        case ItemId::StonePick:return 110;
        case ItemId::WoodSword:return 90;
        case ItemId::Torch:return 65;
        default:return 0;
    }
}
inline bool isTool(ItemId id){
    return id==ItemId::WoodAxe||id==ItemId::StonePick||id==ItemId::WoodSword||id==ItemId::Torch;
}
inline bool isWearable(ItemId id){ return id==ItemId::ClothHat||id==ItemId::ClothTunic; }
inline bool isPlaceable(ItemId id){
    return id==ItemId::DirtBlock||id==ItemId::StoneBlock||id==ItemId::SandBlock||id==ItemId::Workbench||id==ItemId::Campfire;
}
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
        default:return "空";
    }
}

struct Inventory {
    static constexpr int SLOT_COUNT=24;
    static constexpr int HOTBAR_COUNT=8;
    std::array<ItemStack,SLOT_COUNT> slots{};
    std::array<ItemStack,4> equipment{};
    int selectedHotbar=0;
    int selectedInventory=-1;

    int count(ItemId id) const {
        int n=0;
        for(const auto& s:slots) if(ItemId(s.id)==id) n+=s.count;
        return n;
    }
    bool add(ItemId id,int amount,uint16_t durability=0){
        if(id==ItemId::None||amount<=0) return false;
        if(durability==0) durability=maxDurability(id);
        if(isStackable(id)){
            for(auto& s:slots) if(ItemId(s.id)==id && s.count<maxStack(id)){
                int take=std::min<int>(amount,maxStack(id)-s.count);
                s.count=uint16_t(s.count+take); amount-=take; if(amount<=0)return true;
            }
        }
        for(auto& s:slots) if(s.count==0||ItemId(s.id)==ItemId::None){
            int take=std::min<int>(amount,maxStack(id));
            s.id=uint16_t(id); s.count=uint16_t(take); s.durability=durability; amount-=take;
            if(amount<=0)return true;
        }
        return amount<=0;
    }
    bool remove(ItemId id,int amount){
        if(amount<=0)return true;
        for(auto& s:slots) if(ItemId(s.id)==id && s.count){
            int take=std::min<int>(amount,s.count);
            s.count=uint16_t(s.count-take); amount-=take;
            if(s.count==0)s={};
            if(amount<=0)return true;
        }
        return false;
    }
    bool consumeFromSlot(int idx,int amount=1){
        if(idx<0||idx>=SLOT_COUNT||slots[idx].count<amount)return false;
        slots[idx].count=uint16_t(slots[idx].count-amount);
        if(slots[idx].count==0)slots[idx]={};
        return true;
    }
    ItemStack* hotbar(){ return &slots[selectedHotbar]; }
    const ItemStack* hotbar() const { return &slots[selectedHotbar]; }

    bool equipFrom(int idx){
        if(idx<0||idx>=SLOT_COUNT||slots[idx].count==0)return false;
        ItemId id=ItemId(slots[idx].id);
        int e=-1;
        if(id==ItemId::ClothHat)e=int(EquipSlot::Head);
        else if(id==ItemId::ClothTunic)e=int(EquipSlot::Body);
        else if(isTool(id))e=int(EquipSlot::Main);
        else return false;

        ItemStack incoming=slots[idx];
        incoming.count=1;
        consumeFromSlot(idx,1);
        if(equipment[e].count) add(ItemId(equipment[e].id),1,equipment[e].durability);
        equipment[e]=incoming;
        return true;
    }
    bool unequip(int e){
        if(e<0||e>=4||equipment[e].count==0)return false;
        if(!add(ItemId(equipment[e].id),1,equipment[e].durability))return false;
        equipment[e]={}; return true;
    }

    ItemId mainHand() const {
        if(equipment[int(EquipSlot::Main)].count) return ItemId(equipment[int(EquipSlot::Main)].id);
        if(hotbar()->count) return ItemId(hotbar()->id);
        return ItemId::None;
    }

    void wearMainDurability(int amount=1){
        auto& e=equipment[int(EquipSlot::Main)];
        ItemStack* s=e.count?&e:hotbar();
        if(!s||!s->count||s->durability==0)return;
        s->durability=uint16_t(s->durability>amount?s->durability-amount:0);
        if(s->durability==0)*s={};
    }
};

struct Recipe {
    ItemId out; uint16_t outCount;
    ItemId a; uint16_t aCount;
    ItemId b; uint16_t bCount;
    bool needsBench=false;
};
static constexpr Recipe RECIPES[] = {
    {ItemId::WoodAxe,1, ItemId::Wood,5, ItemId::Fiber,2,false},
    {ItemId::StonePick,1, ItemId::Wood,4, ItemId::Stone,6,false},
    {ItemId::WoodSword,1, ItemId::Wood,6, ItemId::Stone,2,false},
    {ItemId::Torch,1, ItemId::Wood,2, ItemId::Fiber,2,false},
    {ItemId::Workbench,1, ItemId::Wood,10, ItemId::Stone,4,false},
    {ItemId::Campfire,1, ItemId::Wood,5, ItemId::Stone,6,false},
    {ItemId::ClothHat,1, ItemId::Fiber,8, ItemId::Wood,1,true},
    {ItemId::ClothTunic,1, ItemId::Fiber,14, ItemId::Wood,2,true}
};
static constexpr int RECIPE_COUNT=int(sizeof(RECIPES)/sizeof(RECIPES[0]));

inline bool canCraft(const Inventory& inv,const Recipe& r,bool nearBench){
    if(r.needsBench&&!nearBench)return false;
    return inv.count(r.a)>=r.aCount && inv.count(r.b)>=r.bCount;
}
inline bool craft(Inventory& inv,const Recipe& r,bool nearBench){
    if(!canCraft(inv,r,nearBench))return false;
    inv.remove(r.a,r.aCount); inv.remove(r.b,r.bCount);
    return inv.add(r.out,r.outCount);
}

constexpr uint32_t SAVE_MAGIC_V2=0x46425632u;
constexpr uint32_t MAX_SAVE_EDITS=384;
constexpr uint32_t MAX_SAVE_HARVEST=384;

struct SaveDataV2 {
    uint32_t magic=SAVE_MAGIC_V2;
    uint32_t version=2;
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
    Inventory inventory{};
    uint32_t editCount=0;
    std::array<BlockEdit,MAX_SAVE_EDITS> edits{};
    uint32_t harvestCount=0;
    std::array<HarvestEdit,MAX_SAVE_HARVEST> harvest{};
    uint32_t checksum=0;
};

inline uint32_t checksumSave(const SaveDataV2& s){
    const uint8_t* p=reinterpret_cast<const uint8_t*>(&s);
    uint32_t h=2166136261u;
    for(size_t i=0;i<sizeof(SaveDataV2)-sizeof(uint32_t);i++){ h^=p[i]; h*=16777619u; }
    return h;
}

} // namespace fb
