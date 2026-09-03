# Codex Task — Native First Playable Spherical Planet

## Goal

在 Windows + VS Code 上把 Voxel Frontier 的原生 C++23/Vulkan 主线完整跑通，并继续开发到“真正能在有限球形星球表面行走、抬头能看到真实天体、可无缝向太空上升”的第一版原生可玩检查点，然后自动启动游戏窗口给用户现场试玩。

不得继续按无限平面 Chunk 世界开发。正式目标是：有限球形星球 + 无缝地表/大气层/太空 + 确定性可扩展宇宙。

不得用 Unreal / Unity / Godot / Three.js / WebGPU / 浏览器作为正式实现。正式游戏保持：C++23 + Vulkan + SDL3（SDL3 仅平台层）。

## Non-negotiable rules

1. 先审计真实本机环境、仓库、编译器、GPU/Vulkan，再修改；不要猜。
2. 不删除用户未提交改动。若工作区不干净，先 `git status`，安全保存到独立分支或 stash，并在报告中说明。
3. 先同步 GitHub `main`：`git switch main` + `git pull --ff-only origin main`。若不能 fast-forward，不准强制覆盖。
4. 不把“成功打开清屏窗口”当作游戏可玩。
5. 不得实现无限平面世界作为正式路线；本任务必须直接验证球形行星架构。
6. 每个阶段必须真实编译、运行、测试。失败就修，不得把未执行测试写成 PASS。
7. 保持 CMake 可复现；不要把用户机器绝对路径硬编码进项目。
8. Debug 和 Release 都必须实际配置、构建和测试。
9. 不引入大型现成游戏引擎。第三方库仅允许底层开发依赖，且必须说明用途。
10. 最终游戏必须由 `voxel_frontier.exe` 原生运行，不是网页。

## Phase A — VS Code / Windows environment closure

### A1. Audit

记录到 `RETURN/native_spherical_first_playable/environment.txt`：

- Windows version
- CPU
- GPU name + driver version
- `git --version`
- `cmake --version`
- `code --version`（若命令存在）
- Visual Studio / Build Tools 安装路径
- MSVC toolset version
- `VULKAN_SDK`（若存在）
- 当前 git branch / HEAD SHA / `git status --short`

执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-windows.ps1 -InstallMissing
```

### A2. Required VS Code tooling

确保以下扩展已安装：

- `ms-vscode.cpptools`
- `ms-vscode.cmake-tools`

验证 `.vscode/settings.json`、`.vscode/tasks.json`、`.vscode/launch.json` 均能指向 `native/` 和本机构建目录。

### A3. Baseline build

依次真实执行 Debug/Release configure/build/test，并保存完整日志。若 baseline 失败，先修 baseline，再进入下一阶段。

## Phase B — Spherical planet spatial architecture

实现明确的层级参考系，而不是一个巨大 float 世界：

```text
Universe
  -> StarSystem
      -> PlanetFrame
          -> SurfacePatch
              -> LocalTerrain
```

要求：

- 恒星系/行星中心等大尺度位置使用 double 和/或 64-bit 整数坐标；
- Vulkan 渲染使用 camera-relative/local-origin float 坐标；
- 玩家在地表和太空移动时可以切换/重定位局部参考原点，不产生明显跳变；
- 总宇宙规模不能直接决定每帧成本；未加载天体只保留 seed/元数据。

新增自动测试：

- planet local <-> system 坐标往返；
- 大距离下 camera-relative 转换精度；
- 局部原点重定位前后视觉坐标连续性。

## Phase C — First finite real planet

创建一个真实有限球形行星，测试半径可先做小型化以便很快验证曲率，例如数百米到数公里级，但必须是有限球面而不是平面包装。

PlanetDefinition 至少包含：

- deterministic seed
- center
- radius
- atmosphere radius
- gravity strength / falloff parameters
- terrain height function parameters
- material/biome basic parameters

### C1. Cube-sphere topology

行星地表采用：

- 6 个 cube faces；
- cube -> sphere 投影；
- 每个 face 使用 quadtree/hierarchical patch；
- 相邻 face 边界连续；
- LOD 由相机距离或 screen-space error 驱动；
- 只生成/保留当前需要的 patch；
- 禁止整颗星球最高精度一次性网格化。

为以下内容写 Release 下真实生效的测试：

- 六个 face 的方向映射；
- sphere projection 归一化/半径正确；
- 相邻 face 共享边连续；
- parent/child patch 覆盖一致性；
- deterministic terrain height。

### C2. Terrain

本轮可以先用确定性的 radial height/displacement 做真实地形，不要求立刻实现完整洞穴/挖掘 SDF。

但代码结构必须预留：

```text
Base procedural planet
+ local high-detail deformation/voxel layer
+ persistent player edits
```

可见结果必须有起伏地形，不是完美光滑调试球。

## Phase D — Vulkan planetary renderer

在现有 `VulkanRenderer` 上实现：

- depth image / depth view
- real graphics pipeline
- SPIR-V shader build
- camera data
- indexed surface-patch rendering
- resize/swapchain recreation
- correct winding / culling
- frustum culling
- basic directional sunlight
- simple terrain material bands/colors

优先 dynamic rendering + synchronization2。

### D1. LOD / extreme-distance representation ladder

同一颗行星必须按距离采用越来越便宜的表示，而不是永远保留近地面网格：

1. 地面近景：高细节 patch / local terrain
2. 区域远景：较粗 surface patch
3. 轨道距离：低多边形 cube-sphere / sphere proxy
4. 行星际距离：极低成本 proxy / impostor-like representation

这些表示必须属于同一个 Planet ID/seed/position，接近时连续换级，不得用另一张假的 skybox 图替换。

## Phase E — Radial gravity and first-person movement

实现：

- mouse look
- WASD
- Shift sprint
- Esc 释放/重新捕获鼠标
- local up = normalize(playerPosition - planetCenter)
- gravity 指向 planet center
- 前后左右移动投影到局部切平面
- 玩家朝向随曲面逐渐旋转
- 地表高度查询/碰撞使玩家站在球面真实地形上

必须能沿球面移动足够距离，看出局部 `up` 在变化，而不是平面世界。

## Phase F — Seamless surface -> atmosphere -> space

不允许切换到另一个 map，不允许加载屏幕，不允许 teleport 到“太空关卡”。

本轮至少提供一种明确的调试飞行/上升控制，例如 Space/Ctrl 或自由飞行切换。

要求：

- 玩家从地面连续上升；
- 随高度增加，地形 LOD 自动降低；
- 上升到足以看见明显星球曲率/完整大部分球体；
- 近地参考系和太空参考系切换不出现明显精度跳动；
- 从高空重新下降能够回到同一颗星球同一地表；
- 不能因为离开地面就把整颗星球高精度 mesh 留在内存/GPU。

## Phase G — Real second celestial body

在当前恒星系加入至少一个第二真实天体：

- deterministic ID/seed
- system-space position
- radius
- cheap distant proxy
- 真实参与天体目录/参考系

它必须真的由位置、半径、轨道/静态参数定义，不是 skybox 绘制。

本轮不要求实际登陆第二颗星，但架构必须让后续“飞过去 -> proxy LOD -> sphere LOD -> surface LOD -> 落地”成为同一路径。

## Phase H — Ultra-far rendering / bounded cost

核心目标是：宇宙可以理论无限，但每帧成本有严格上界。

实现/预留：

- hierarchical sector / star-system metadata
- CPU coarse culling
- local scene Vulkan frustum culling
- distant celestial bodies batched in very small GPU buffers
- multi-draw indirect / GPU-generated draw list architecture hooks
- mesh/task shader path仅在硬件支持且测量有收益时启用；必须有 indexed fallback
- patch generation/mesh/upload 使用 per-frame budget
- 未进入活动范围的星球绝不生成真实地形 mesh

不要声称“无限星球全部同时渲染”。正确目标是：无限可生成、可抵达；当前视锥中所有需要可见的远天体用极廉价层级表达。

## Phase I — Runtime diagnostics

窗口标题或 overlay 每秒显示：

```text
Voxel Frontier | FPS | frame ms | visible patches | resident patches | tris | altitude | active frame
```

还要打印：

- GPU
- Vulkan API
- active planet
- planet radius
- player altitude
- resident planet patch count
- distant celestial proxy count

至少记录 20 秒真实本机运行性能。

## Phase J — Run it for the user

完成后运行 Debug，再运行最终 Release。

最终保持 Release `voxel_frontier.exe` 窗口打开，让用户亲自：

- WASD/鼠标在球面走；
- 感受重力/up 方向跟随星球；
- 上升到高空/太空；
- 看地表 LOD 自动降级；
- 看另一颗真实天体在天空/太空中存在。

若启动失败，直接抓 stdout/stderr 和 Vulkan 错误修复，不要猜驱动问题。

## Phase K — Git / return package

使用分支：

```text
codex/native-spherical-first-playable
```

不要自行 merge `main`。

生成：

```text
RETURN/native_spherical_first_playable/
├─ environment.txt
├─ configure_debug.log
├─ build_debug.log
├─ test_debug.log
├─ configure_release.log
├─ build_release.log
├─ test_release.log
├─ runtime.log
├─ performance.txt
├─ planet_metrics.txt
├─ git_status.txt
├─ git_diff_stat.txt
└─ summary.md
```

压缩：

```text
RETURN/NATIVE_SPHERICAL_FIRST_PLAYABLE_RETURN.zip
```

## Acceptance gate

只有同时满足以下条件才能写 `NATIVE_SPHERICAL_FIRST_PLAYABLE_PASS`：

1. VS Code/MSVC/CMake 工具链闭合；
2. Debug configure/build/test PASS；
3. Release configure/build/test PASS；
4. Vulkan runtime 无致命错误；
5. 实际渲染有限球形地形，不是平面也不是完美调试球；
6. cube-sphere / hierarchical patch LOD 工作；
7. 鼠标 + WASD 能沿球面移动；
8. radial gravity/up 工作；
9. 能连续上升到高空/太空，无独立地图加载；
10. 高度增加时 LOD 显著降低，内存/三角形不会维持地面峰值；
11. 至少一个第二真实天体以廉价 proxy 可见；
12. 20 秒本机稳定运行并有真实性能指标；
13. Release exe 保持打开供用户试玩；
14. RETURN zip 已生成；
15. 分支已 push。

否则必须写 `NATIVE_SPHERICAL_FIRST_PLAYABLE_FAIL` 或 `PARTIAL`，列出真实阻塞，不得伪造 PASS。
