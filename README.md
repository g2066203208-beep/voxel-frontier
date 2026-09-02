# Voxel Frontier

原创浏览器大型体素沙盒游戏，从零开发，不依赖 Minecraft、NeoForge 或任何原版资源。

## 技术栈

- TypeScript（strict mode）
- Three.js / WebGL
- Vite
- GitHub Actions + GitHub Pages

## 当前工程结构

```text
src/
├─ core/        # 游戏主循环、输入、玩家控制与碰撞
├─ render/      # Three.js 场景与体素渲染
├─ ui/          # HUD 与快捷栏
├─ world/       # 方块注册、世界数据、程序化地形
├─ main.ts      # 应用入口
├─ styles.css   # 游戏界面样式
└─ types.ts     # 公共类型
```

## 当前可玩功能

- 程序化体素地形与树木
- 第一人称移动、冲刺、跳跃与重力
- 方块碰撞
- 射线破坏/放置方块
- 5格快捷栏与方块切换
- 雾效、天空与基础光照
- GitHub Pages 自动构建与部署

## 本地开发

需要 Node.js 22 或兼容版本。

```bash
npm install
npm run dev
```

类型检查与生产构建：

```bash
npm run typecheck
npm run build
```

## 项目方向

这是独立游戏项目，不是 Minecraft Mod 工程。后续按模块继续扩展：区块流式加载、存档、纹理图集、背包、合成、实体、NPC、城市、车辆、天气、多人联机以及版本化自定义 Mod API。
