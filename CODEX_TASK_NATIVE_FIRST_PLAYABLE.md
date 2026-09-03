# Codex Task — Native First Playable Smooth Spherical Planet

## Goal

在 Windows + VS Code 上把 Voxel Frontier 的原生 C++23/Vulkan 主线完整跑通，并继续开发到“真正能在有限球形星球表面行走、看到光滑自然地形、抬头能看到真实天体、可无缝向太空上升”的第一版原生可玩检查点，然后自动启动游戏窗口给用户现场试玩。

**先阅读并严格遵守 `docs/TERRAIN_ARCHITECTURE.md`。**

不得继续按无限平面 Chunk 世界或方块体素世界开发。正式目标是：有限球形星球 + 顶点/三角面光滑地形 + 稀疏局部 SDF/密度场变形 + 无缝地表/大气层/太空 + 确定性可扩展宇宙。

不得用 Unreal / Unity / Godot / Three.js / WebGPU / 浏览器作为正式实现。正式游戏保持：C++23 + Vulkan + SDL3（SDL3 仅平台层）。

## Non-negotiable rules

1. 先审计真实本机环境、仓库、编译器、GPU/Vulkan，再修改；不要猜。
2. 不删除用户未提交改动。若工作区不干净，先 `git status`，安全保存到独立分支或 stash，并在报告中说明。
3. 先同步 GitHub `main`：`git switch main` + `git pull --ff-only origin main`。若不能 fast-forward，不准强制覆盖。
4. 不把“成功打开清屏窗口”当作游戏可玩。
5. 不得实现无限平面世界作为正式路线；本任务必须直接验证球形行星架构。
6. **禁止自然地形使用可见立方体/方块渲染；禁止把 Greedy Meshing 当自然地形主方案。**
7. 可使用“voxel/SDF/density sample”作为局部隐式地形数据，但最终显示必须是连续三角曲面。
8. 每个阶段必须真实编译、运行、测试。失败就修，不得把未执行测试写成 PASS。
9. 保持 CMake 可复现；不要把用户机器绝对路径硬编码进项目。
10. Debug 和 Release 都必须实际配置、构建和测试。
11. 不引入大型现成游戏引擎。第三方库仅允许底层开发依赖，且必须说明用途。
12. 最终游戏必须由 `voxel_frontier.exe` 原生运行，不是网页。

## Phase A — VS Code / Windows environment closure

记录 Windows、CPU、GPU/driver、Git、CMake、VS Code、MSVC、VULKAN_SDK、当前 branch/HEAD/status 到 `RETURN/native_spherical_first_playable/environment.txt`。

执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-windows.ps1 -InstallMissing
```

确保 `ms-vscode.cpptools`、`ms-vscode.cmake-tools` 以及仓库 `.vscode` 配置可工作。

依次真实执行 Debug/Release configure/build/test，并保存完整日志。若 baseline 失败，先修 baseline。

## Phase B — Hierarchical planetary coordinates

实现：

```text
Universe
  -> StarSystem
      -> PlanetFrame
          -> SurfacePatch
              -> LocalTerrainField
```

要求：
- 大尺度位置用 double 和/或 64-bit 整数坐标；
- Vulkan 使用 camera-relative/local-origin float；
- reference-frame rebasing 不产生明显视觉跳动；
- 未加载天体仅为 seed/元数据，每帧成本不能随宇宙总规模增长。

测试：坐标往返、大距离 camera-relative 精度、rebase 连续性。

## Phase C — First finite smooth planet

创建真实有限球形行星。PlanetDefinition 至少包含 seed、center、radius、atmosphere radius、gravity、terrain parameters、material/biome parameters。

### C1. Surface topology and explicit geometry

行星地表主渲染采用**顶点 + 索引三角面**：
- 六个 cube faces -> sphere/ellipsoid，或等效的 clipmap-friendly 参数化；
- 每个 face 使用 quadtree / hierarchical surface patch；
- 相邻 face 边界连续；
- LOD 由 screen-space error / projected size 优先驱动，而不是只看固定距离；
- 只保留当前需要的 patch；
- 禁止整颗星球最高精度一次性网格化；
- 共享/复用规则网格 index topology，顶点位置由 patch 参数 + procedural displacement 产生；
- 允许 CPU 生成顶点作为第一版，但接口必须允许后续迁往 GPU procedural generation / mesh shader。

测试：六面映射、sphere projection、共享边连续、parent/child 覆盖、deterministic terrain、无 NaN/裂缝。

### C2. Procedural smooth terrain

第一版地形真值优先使用：

```text
base radius + deterministic procedural displacement
```

可组合低频大陆/丘陵 + 中频地貌 + 高频近景细节，但要设置幅值/频率预算避免噪声堆砌。

自然地形必须是连续曲面，禁止立方体台阶感。

### C3. Reserve the sculptable layer correctly

本轮不强制完成完整挖掘，但架构必须直接预留：

```text
Procedural planet surface
+ sparse local SDF / density bricks
+ persistent CSG/deformation deltas
-> smooth surface extraction
-> triangle mesh
```

要求：
- 未修改区域不得分配整颗星球的稠密 3D voxel grid；
- 只有洞穴、悬挑、挖掘、填土等真正需要 3D 拓扑的区域才创建 sparse local field；
- 长期优先评估 Dual Contouring；Marching Cubes 可作为较简单参考/回退；
- 多分辨率局部场以后必须使用 Transvoxel-style transition 或其他经验证的 crack-free seam 方法；
- **不允许把 local field 直接显示为方块。**

## Phase D — Vulkan planetary renderer

在现有 `VulkanRenderer` 上实现：
- depth image/view
- graphics pipeline
- SPIR-V shader build
- camera data
- indexed surface-patch rendering
- resize/swapchain recreation
- winding/culling
- frustum culling
- **planet horizon culling**（球体背面的 patch 不进入昂贵绘制）
- sunlight / normal-based shading
- terrain material bands/colors

优先 dynamic rendering + synchronization2。

### D1. Representation ladder

同一 Planet ID 必须连续使用：
1. 地面：高细节 smooth surface patches
2. 区域远景：粗 surface mesh patches
3. 轨道：低成本 sphere/cube-sphere proxy
4. 行星际：极廉价 analytical/proxy representation

禁止假的 skybox planet 代替真实 Planet。

## Phase E — Radial gravity and movement

实现 mouse look、WASD、Shift、Esc、radial up/gravity、切平面移动、地表高度/碰撞。玩家沿球面移动时局部 up 必须连续变化。

## Phase F — Seamless surface -> atmosphere -> space

不允许 scene/map 切换、loading screen 或 teleport。

提供调试上升/自由飞行控制，使玩家从地面连续上升到足以看见明显曲率/大部分星球；随高度增加 terrain surface LOD 必须显著降低，并可重新下降到同一位置附近。

## Phase G — Real second celestial body

加入至少一个具有真实 ID/seed/system-space position/radius 的第二天体，用 cheap distant proxy 显示。它不是 skybox 图，并且架构必须支持后续真正飞过去并连续展开成 surface LOD。

## Phase H — Ultra-far bounded-cost rendering

实现/预留：
- hierarchical sector / star-system metadata
- CPU coarse culling
- frustum + planet horizon culling
- distant celestial batching
- multi-draw indirect / GPU-generated draw-list hooks
- mesh/task shader 只在支持且测量有收益时启用，保留 indexed fallback
- patch generation/upload strict per-frame budget
- 未进入活动范围的星球绝不生成近地 surface mesh 或 local SDF

目标是“无限可生成、无限可抵达”，不是“把无限天体同时逐个画出来”。

## Phase I — Runtime diagnostics

每秒显示/记录：

```text
Voxel Frontier | FPS | frame ms | visible patches | resident patches | tris | altitude | active frame
```

另记录 GPU、Vulkan API、active planet、planet radius、altitude、surface patch counts、distant proxies、CPU frame ms、GPU frame ms（能实现则做 timestamp queries）。

至少 20 秒真实性能运行。

## Phase J — Run for user

最终保持 Release `voxel_frontier.exe` 打开，让用户亲自：
- 看光滑球形自然地形；
- WASD/鼠标沿球面移动；
- 感受 radial gravity/up；
- 上升到太空；
- 看 LOD 从高细节三角面逐渐降到行星 proxy；
- 看第二真实天体。

## Phase K — Git / return package

使用：

```text
codex/native-spherical-first-playable
```

不要自行 merge main。

生成 `RETURN/native_spherical_first_playable/` 下的环境、Debug/Release configure/build/test、runtime、performance、planet_metrics、git status/diff、summary，并压缩：

```text
RETURN/NATIVE_SPHERICAL_FIRST_PLAYABLE_RETURN.zip
```

## Acceptance gate

只有同时满足以下条件才能写 `NATIVE_SPHERICAL_FIRST_PLAYABLE_PASS`：
1. VS Code/MSVC/CMake 闭合；
2. Debug configure/build/test PASS；
3. Release configure/build/test PASS；
4. Vulkan runtime 无致命错误；
5. 实际渲染**光滑顶点/三角面球形地形**，不是平面、不是方块地形、不是纯调试球；
6. hierarchical patch LOD 工作且 seam 可接受；
7. 鼠标 + WASD 沿球面移动；
8. radial gravity/up 工作；
9. 连续上升到高空/太空，无独立地图加载；
10. 高度增加时 LOD/三角形/内存显著降低；
11. 第二真实天体 proxy 可见；
12. 20 秒本机稳定运行并记录真实性能；
13. Release exe 保持打开供用户试玩；
14. RETURN zip 已生成；
15. 分支已 push。

否则必须写 FAIL/PARTIAL，列出真实阻塞，不得伪造 PASS。
