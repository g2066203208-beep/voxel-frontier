# Voxel Frontier

原创浏览器大型 RPG 体素沙盒游戏。

## 技术主线

- C++23：高性能体素世界与核心算法
- WebAssembly + SIMD：浏览器原生核心
- WebGPU + WGSL：新一代 GPU 渲染路径
- TypeScript：浏览器、UI、输入与应用层
- Vite：网页构建
- GitHub Actions + GitHub Pages：自动编译、测试与部署

## 新引擎架构

```text
Browser / TypeScript
        │
        ├─ UI / Input / App
        │
        ▼
C++23 Engine Core
        │
        ├─ contiguous chunks
        ├─ terrain generation
        ├─ greedy meshing
        └─ 3D DDA voxel traversal
        │
        ▼
WebAssembly + SIMD
        │
        ▼
WebGPU / WGSL
```

新引擎使用 `16 × 64 × 16` 连续内存 Chunk，并逐步替换旧版按字符串坐标存储、整世界重建的原型架构。方块修改采用局部 dirty-chunk 重建路线。

## 当前新引擎预览

部署后，在游戏地址后加：

```text
?engine=next
```

即可进入 C++/WASM + WebGPU 新引擎预览。当前预览优先验证 Chunk 流式加载、网格生成和 GPU 渲染性能；完整生存、背包、建造/破坏、战斗等玩法继续迁移。

## 自动质量门禁

新引擎改动必须同时通过：

- C++23 原生正确性与性能测试
- Emscripten C++ → WebAssembly SIMD Release 编译
- TypeScript strict + WebGPU 网页集成构建

生产部署会自动编译 C++、打包 `.wasm`，随后构建网页并发布，不需要玩家本机安装编译环境。

## 本地网页开发

```bash
npm install
npm run dev
```

正式构建：

```bash
npm run build
```

更详细的引擎说明见 `ENGINE.md`。
