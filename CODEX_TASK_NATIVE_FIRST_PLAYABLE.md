# Codex Task — Native First Playable

## Goal

在 Windows + VS Code 上把 Voxel Frontier 的原生 C++23/Vulkan 主线完整跑通，并继续开发到“真正能看见并移动于体素世界”的第一版原生可玩检查点，然后自动启动游戏窗口给用户现场试玩。

不得用 Unreal / Unity / Godot / Three.js / WebGPU / 浏览器作为正式实现。正式游戏保持：C++23 + Vulkan + SDL3（SDL3 仅平台层）。

## Non-negotiable rules

1. 先审计真实本机环境、仓库、编译器、GPU/Vulkan，再修改；不要猜。
2. 不删除用户未提交改动。若工作区不干净，先 `git status`，安全保存到独立分支或 stash，并在报告中说明。
3. 先同步 GitHub `main`：`git switch main` + `git pull --ff-only origin main`。若不能 fast-forward，不准强制覆盖。
4. 不把“成功打开清屏窗口”当作游戏可玩。当前 native runtime 只是 Vulkan clear/present bootstrap；本任务必须继续做到真实 voxel terrain rendering + first-person camera。
5. 每个阶段必须真实编译、运行、测试。失败就修，不得把未执行测试写成 PASS。
6. 保持 CMake 可复现；不要把用户机器绝对路径硬编码进项目。
7. 保持 Debug 和 Release 都能配置；至少 Debug 必须实际构建/运行，Release 至少完成构建测试。
8. 不引入大型现成游戏引擎。第三方库仅允许底层开发依赖，且必须说明用途。
9. 最终游戏必须由 `voxel_frontier.exe` 原生运行，不是网页。

## Phase A — VS Code / Windows environment closure

### A1. Audit

记录到 `RETURN/native_first_playable/environment.txt`：

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

使用仓库现有：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-windows.ps1 -InstallMissing
```

若脚本因工具安装后 PATH 尚未刷新而失败，刷新当前 shell PATH 后重试，不要直接改成假 PASS。

### A2. Required VS Code tooling

确保以下扩展已安装（仓库已有 `.vscode/extensions.json`）：

- `ms-vscode.cpptools`
- `ms-vscode.cmake-tools`

验证 `.vscode/settings.json`、`.vscode/tasks.json`、`.vscode/launch.json` 均指向 `native/` 和 `build/vscode-windows`。

### A3. Baseline build

依次真实执行：

```powershell
cd native
cmake --preset windows-debug
cmake --build --preset windows-debug --parallel
ctest --preset windows-debug

cmake --preset windows-release
cmake --build --preset windows-release --parallel
ctest --preset windows-release
```

把完整输出保存到：

- `RETURN/native_first_playable/configure_debug.log`
- `RETURN/native_first_playable/build_debug.log`
- `RETURN/native_first_playable/test_debug.log`
- `RETURN/native_first_playable/configure_release.log`
- `RETURN/native_first_playable/build_release.log`
- `RETURN/native_first_playable/test_release.log`

若 baseline 失败，先修 baseline，再进入下一阶段。

## Phase B — Native visible voxel world

当前 `native/src/app/Main.cpp` 只做 Vulkan clear/present。必须升级到真正可见的体素世界。

### B1. Shader pipeline

建立可复现的 shader build 路线。

优先采用当前 Vulkan SDK 官方教程使用的 Slang -> SPIR-V 路线；如果本机已有 `slangc`，使用它。若没有：

- 不要写死 `C:\VulkanSDK\x.x.x.x`；
- 优先检测 `VULKAN_SDK`；
- 若开发工具确实缺失，可安装最新官方 Vulkan SDK；
- 或采用可被 CMake 自动获取、版本固定的 shader compiler 方案；
- CI 必须也能构建 shader，不允许只在用户机器工作。

创建至少：

- voxel vertex shader
- voxel fragment shader

CMake 构建时自动产出 SPIR-V，并让 runtime 在稳定的相对路径加载或把字节嵌入构建产物。

### B2. Vulkan renderer

在现有 `VulkanRenderer` 上实现而不是推倒重写：

- depth image / depth view
- graphics pipeline
- vertex/index buffers
- camera uniform/push constants
- viewport/scissor resize handling
- correct swapchain recreation
- validation-friendly synchronization
- GPU resource destruction顺序正确

优先使用当前 Vulkan dynamic rendering / synchronization2 路线，避免重新引入旧式 render pass 复杂度，除非当前代码结构有充分理由。

### B3. Voxel mesh

新增独立模块，例如：

```text
native/include/vf/world/GreedyMesher.hpp
native/src/world/GreedyMesher.cpp
```

要求：

- 从当前 32×32×32 contiguous Chunk 生成可渲染 mesh；
- 空气面不生成；
- 内部相邻实体面不生成；
- 优先实现 greedy meshing；
- Chunk 边界必须读取相邻 Chunk halo，不能让相邻区块接缝处产生双层内部面；
- mesh 输出采用紧凑 vertex/index 数据结构；
- 不得一块方块一个 draw call；
- 至少按 Chunk mesh draw；后续 GPU-driven 可再升级。

为 mesher 写真实单元测试：

- 单方块面数/索引数
- 实心块内部面剔除
- 两相邻 Chunk 边界面剔除
- 空 Chunk = 0 geometry
- deterministic output

### B4. Camera / first-person input

实现：

- 鼠标 Pointer/relative mode 控制 yaw/pitch
- WASD 移动
- Shift 加速
- Esc 释放/重新捕获鼠标逻辑清晰
- 相机透视矩阵随窗口尺寸更新
- 进入游戏时出生在地表上方，不要出生在方块内部

这一轮可以先做 free-fly / no-clip 相机以优先验证渲染和 streaming；如果碰撞已经很容易接入，则做重力 + 地面碰撞，但不得为了碰撞阻塞“先看到真实世界”。

### B5. Chunk streaming

至少实现以玩家 Chunk 为中心的有限视距流式集合：

- 初始建议水平半径 6~8 chunks；
- 不在主线程一次性同步生成整个大世界；
- 先可以 budgeted generation，若已有线程池则异步；
- 离开视距 Chunk 可卸载 GPU mesh；
- 不能每帧重建所有 Chunk；
- 只有新生成或 Dirty Chunk 重建 mesh。

### B6. First visual art direction

这一轮不追求最终美术，但必须“看起来像一个真正的体素世界”，而不是调试三角形：

- sky clear color
- grass / dirt / stone 至少三种可区分材质颜色
- directional sun-like lighting or simple normal-based shading
- depth test
- 远近层次清晰

无需先做纹理包；先保证性能和空间感。

## Phase C — Runtime diagnostics

游戏运行后：

- 每 1 秒更新窗口标题：`Voxel Frontier | FPS: ... | Chunks: ... | Tris: ...`
- 控制台打印 GPU、Vulkan API、加载 Chunk 数
- Debug 构建启用 Vulkan validation layer（若本机存在），Release 不强制
- 捕获 validation error；出现 ERROR 时不得报 PASS

记录：

- 平均 FPS（至少观察 20 秒）
- 最低瞬时 FPS（可用简单 frame-time 统计）
- loaded chunks
- total triangles
- CPU frame ms 粗统计

不要把 CI CPU benchmark 当本机 FPS。

## Phase D — Run it for the user

完成以上内容后执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-game.ps1 -Configuration Debug
```

如果 Debug 成功，再构建 Release，并最终启动 Release：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-game.ps1 -Configuration Release
```

**最终请让 Release 的 `voxel_frontier.exe` 保持运行，不要自动关闭，让用户直接看窗口和用 WASD/鼠标试玩。**

如果程序启动后立即退出：

1. 直接从终端运行以捕获 stdout/stderr；
2. 修复问题；
3. 再启动；
4. 不要只汇报“可能是显卡驱动”。

只有在确认硬件/驱动本身不支持所需 Vulkan 功能时，才报告硬件阻塞，并给出检测到的 GPU/driver/API 证据。

## Phase E — Git / return package

不要直接覆盖用户其它工作。

完成后创建/使用分支：

```text
codex/native-first-playable
```

提交清晰 commit。若 GitHub 凭据可用：

```powershell
git push -u origin codex/native-first-playable
```

不要自行 merge `main`。

生成：

```text
RETURN/native_first_playable/
├─ environment.txt
├─ configure_debug.log
├─ build_debug.log
├─ test_debug.log
├─ configure_release.log
├─ build_release.log
├─ test_release.log
├─ runtime.log
├─ performance.txt
├─ git_status.txt
├─ git_diff_stat.txt
└─ summary.md
```

然后自动压缩为：

```text
RETURN/NATIVE_FIRST_PLAYABLE_RETURN.zip
```

`summary.md` 必须明确写：

- 最终是否 PASS
- 实际运行的 exe 路径
- GPU / Vulkan API
- Debug / Release build+test 状态
- 用户能看到什么
- 操作方式
- FPS / chunks / triangles
- 当前仍缺哪些系统
- branch + commit SHA
- 是否已 push

## Acceptance gate

只有同时满足以下条件才能写 `NATIVE_FIRST_PLAYABLE_PASS`：

1. VS Code 工具链闭合；
2. Debug configure/build/test PASS；
3. Release configure/build/test PASS；
4. Vulkan runtime 无致命错误；
5. 真实 voxel terrain 已渲染，不是纯 clear screen；
6. 鼠标可看向，WASD 可移动；
7. Chunk streaming 工作，镜头移动不会触发整世界每帧重建；
8. 至少 20 秒本机运行稳定；
9. Release exe 已启动并留给用户现场查看；
10. RETURN zip 已生成。

否则写 `NATIVE_FIRST_PLAYABLE_FAIL`，列出唯一/主要阻塞和已经拿到的证据，不得伪造 PASS。
