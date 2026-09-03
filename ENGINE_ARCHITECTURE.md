# Voxel Frontier Engine Architecture

## Target

Build a high-performance browser voxel RPG with a native-style engine core while preserving instant browser play.

## Production stack

- C++23 engine core
- WebAssembly via Emscripten
- WebAssembly SIMD (`-msimd128`) for data-oriented voxel operations
- WebGPU renderer as the primary graphics backend
- WebGL 2 fallback during the migration/compatibility period
- TypeScript only for browser integration, UI, input, loading and platform APIs
- Vite for the web shell and asset pipeline

## Engine split

```text
engine/
├─ include/vf/          public C++ engine headers
└─ src/                 C++ world/mesh/physics/runtime implementation

src/
├─ platform/            TypeScript browser/WASM bridge
├─ ui/                  DOM UI/HUD
└─ legacy/              temporary code during migration
```

## Performance rules

1. The world is chunked; no global world rebuild after one block edit.
2. Voxel data uses compact contiguous typed storage, not string-key maps in hot paths.
3. Only dirty chunks are remeshed.
4. Mesh generation uses face culling first, then greedy meshing.
5. Terrain generation and meshing are designed to run outside the browser main thread.
6. Rendering is chunk-mesh based, not one render instance per visible block.
7. Frustum/distance culling occurs per chunk.
8. Ray interaction uses voxel DDA traversal, not scene-wide mesh raycasting.
9. Hot loops are profiled before moving them into WASM or GPU compute.
10. WebGPU compute is used only where measurements show a real win.

## Migration gates

The current TypeScript build remains production until the replacement branch passes:

- C++ host compile
- Emscripten WebAssembly compile
- deterministic chunk-generation tests
- mesh correctness tests
- automated browser smoke test
- frame-time benchmark against the current build

No engine migration is merged solely because a newer API is available.
