# Engine Architecture

Voxel Frontier uses a layered browser-native architecture.

## Native core

C++23 owns hot-path voxel algorithms. Chunks use contiguous byte storage and are compiled to WebAssembly with SIMD enabled. Current native modules cover terrain fill, greedy mesh generation and DDA voxel traversal.

## Browser layer

TypeScript owns application startup, UI/input integration and capability selection. The next engine is loaded on demand, so the compatibility renderer is not part of the next-engine startup bundle.

## GPU layer

The next renderer uses raw WebGPU and WGSL. C++ mesh vertices are packed to a fixed 16-byte format and uploaded directly to GPU vertex/index buffers.

## Streaming

Chunk streaming is distance-driven and budgeted per frame. Editing a voxel remeshes the owning chunk rather than rebuilding the full world. Cross-chunk halo meshing and worker-based generation are the next performance tasks.

## Compatibility

The existing renderer remains as a fallback until the next engine reaches gameplay feature parity. WebGPU capability is checked at runtime.
