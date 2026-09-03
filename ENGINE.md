# Voxel Frontier Engine

## Current next-generation stack

- C++23 native simulation/voxel core
- Emscripten WebAssembly release build
- WebAssembly SIMD (`-msimd128`)
- contiguous `uint8_t` chunk storage
- greedy voxel meshing
- 3D DDA voxel traversal
- raw WebGPU renderer with WGSL shaders
- TypeScript browser/UI integration
- dynamic compatibility-engine fallback

## Chunk model

Current chunk dimensions are `16 × 64 × 16` blocks. A chunk is stored as one contiguous byte array rather than string-keyed per-block objects.

World editing is moving to dirty-chunk updates: editing a block remeshes the owning chunk rather than rebuilding every visible block in the world.

## Rendering path

The next renderer consumes the native mesher's packed 16-byte vertex format directly:

- `float32 x, y, z`
- `uint32 packed block/normal data`

The primary path is WebGPU/WGSL. The existing renderer remains available as a compatibility fallback while feature parity is completed.

## Preview

After the next engine is packaged by the deployment workflow, use:

`?engine=next`

The next-engine preview currently focuses on rendering and streaming performance. Survival, inventory, full building/destruction parity and advanced collision are migrated after the engine foundation is validated.

## CI gates

Every next-engine change must pass:

1. native C++23 correctness/performance tests;
2. Emscripten C++ → WebAssembly SIMD release compilation;
3. strict TypeScript + WebGPU integration build.

The production Pages workflow builds the native engine first, copies `vf_engine.js` and `vf_engine.wasm` into the web bundle, then builds and deploys the browser client.
