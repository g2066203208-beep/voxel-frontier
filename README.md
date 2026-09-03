# Voxel Frontier

原创大型 PC 体素 RPG 沙盒游戏。

## 正式技术主线

- C++23：游戏与引擎主体
- Vulkan 1.4：自研图形与 GPU 计算后端
- SDL3：仅负责窗口、输入、手柄、音频等平台接入
- CMake：原生工程构建
- GitHub Actions：Windows/Linux 自动编译与测试

正式版不再以浏览器为运行目标。游戏世界、渲染、资源系统、任务调度、物理、AI、存档、网络和玩法系统均沿自研原生引擎路线开发。

## 当前原生工程

```text
native/
├─ include/vf/
│  ├─ core/       # 引擎主循环
│  ├─ platform/   # SDL3 平台层
│  ├─ render/     # Vulkan 原生渲染器
│  └─ world/      # Chunk / World
├─ src/
│  ├─ app/
│  ├─ core/
│  ├─ platform/
│  ├─ render/
│  └─ world/
└─ tests/
```

当前底座已经采用 `32 × 32 × 32` 连续内存 Chunk，支持确定性世界生成、正确负坐标映射、局部 Dirty Chunk 与边界邻居失效传播。Windows 运行时直接生成 `voxel_frontier.exe`。

## 第一阶段目标

1. 原生 Vulkan 窗口与稳定帧循环
2. 多线程 Chunk 流式生成
3. Greedy Meshing / Meshlet 数据
4. GPU 顶点与索引缓冲管理
5. 深度、相机、Shader 与视锥裁剪
6. 第一人称移动与碰撞
7. 方块破坏、放置与局部重网格
8. 性能 Profiler 与自动帧时间门禁

基础性能稳定后，再向生存、背包、合成、战斗、NPC、城市、车辆和多人世界扩展。

## Windows 构建

```powershell
cmake -S native -B build/native -A x64 -DVF_BUILD_RUNTIME=ON -DVF_BUILD_TESTS=ON
cmake --build build/native --config Release --parallel
ctest --test-dir build/native -C Release --output-on-failure
```

VS Code 已配置 `native` 为 CMake 工程源目录。详细说明见 `native/README.md`。
