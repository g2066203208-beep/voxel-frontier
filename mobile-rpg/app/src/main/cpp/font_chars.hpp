#pragma once
#include <cstdint>

// Runtime rasterized with Android system font; no font file is bundled.
static constexpr char32_t kFontGlyphs[] =
    U" ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    U".,:;!?+-*/%()[]<>_=#@"
    U"神契荒境继续游戏新世界读取存档设置关于槽空载入删除创建选择信仰成熟初生无者殿复活从零发展一条命返回"
    U"角色体型肤色发服装随机进入暂停保存主菜单生命饥饿力第天清晨白黄昏夜晚背包装备工具木镐石斧剑火把徒手"
    U"交互采集挖掘放置攻击使用旋转跳跃材料食物浆果矿石草泥土沙子工作台篝已获得没有目标苏醒欢迎来恩故事终结"
    U"开发版原安卓素大分块生成固定赫兹像精灵昼循环触摸摇杆性能画质高中低品数量头部身副栏快捷制需要功资源不足"
    U"关闭选当前位置时间木材石料泥块沙块草纤维营火箱空位拾取丢弃耐久武器衣帽鞋铜铁自动靠近树岩丛龛水地山森海岸"
    U"晴朗微风速度伤害防御升级技能任务地图探索建造村庄农田房屋睡觉配方长按拖动堆叠世界范围前方方块模式安全退出确定取消";

static constexpr uint32_t kFontGlyphCount = sizeof(kFontGlyphs) / sizeof(kFontGlyphs[0]) - 1;
