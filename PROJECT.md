# Voxel Frontier — Roadmap

## Engine migration — CURRENT

The project is migrating from the original prototype renderer/world representation to a high-performance browser-native engine stack:

- C++23 core
- WebAssembly SIMD
- contiguous chunk storage
- greedy meshing
- 3D DDA voxel traversal
- raw WebGPU/WGSL rendering
- TypeScript browser/UI layer

### Completed foundation
- C++23 chunk terrain generation
- C++ greedy mesher
- C++ DDA voxel traversal
- Emscripten WebAssembly release build
- SIMD compilation gate
- TypeScript ↔ WASM bridge
- raw WebGPU chunk renderer
- streamed chunk manager
- first-person next-engine preview
- strict native/WASM/web CI gates
- automatic WASM packaging in Pages deployment

### Next engine hardening
- move chunk generation/meshing to Web Workers
- chunk-neighbor halo support and boundary-face removal
- world-space DDA across streamed chunks
- dirty owner/neighbor chunk updates for edits on chunk borders
- robust capsule/AABB player collision and step climbing
- frustum/distance culling
- GPU render-bundle/indirect-draw experiments where measurements justify them
- texture atlas, material layers and ambient occlusion
- browser frame-time benchmark gate

## Gameplay migration

After the next engine reaches stable rendering/streaming performance, migrate gameplay systems onto it in this order:

1. block targeting, destruction and placement
2. full collision and fall damage
3. inventory and item drops
4. survival stats and day/night
5. crafting, tools and equipment
6. creatures and combat
7. character progression
8. biomes, structures, villages and dungeons
9. vehicles, machines and large sandbox systems
10. multiplayer and persistent shared worlds

## Extensibility

- data-driven block/item/entity registry
- versioned extension API
- content-pack loader
- manifest validation
- compatibility and permission gates
