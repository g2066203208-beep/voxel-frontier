# Voxel Frontier — Native Engine Roadmap

## Engine foundation — CURRENT

Production target: native PC game built on a custom C++23 engine.

### Foundation completed
- 32×32×32 contiguous voxel chunks
- deterministic seeded terrain generation
- correct negative world/chunk coordinate conversion
- dirty owner chunk updates
- dirty neighbor propagation for border edits
- SDL3 desktop platform/window/event layer
- Vulkan 1.3+ instance/device/surface/swapchain bootstrap, Vulkan 1.4 preferred
- explicit synchronization2 frame submission
- direct swapchain clear/present loop
- C++ Release correctness tests
- Linux engine-core CI
- Windows native runtime CI producing `voxel_frontier.exe`

### Engine milestone 1 — playable native voxel world
- custom work-stealing job system
- camera-driven chunk streaming
- greedy meshing with neighbor halo
- mesh upload allocator
- Vulkan depth buffer and shader pipeline
- bindless material/texture table
- frustum and distance culling
- first-person input/controller
- AABB/capsule collision and step climbing
- voxel DDA targeting
- destruction/placement with dirty-chunk remesh
- CPU/GPU frame profiler

### Engine milestone 2 — large-world performance
- palette + bit-packed voxel storage
- region files and asynchronous save/load
- background generation/meshing workers
- meshlets and GPU-driven indirect draw path where profiling proves useful
- occlusion/Hi-Z culling experiments
- asynchronous asset streaming
- memory arenas and transient frame allocators
- DirectStorage integration on Windows where it produces measurable benefit
- crash reporting and deterministic replay support

## Gameplay systems

After the native world foundation is stable:

1. inventory and item stacks
2. crafting and tools
3. survival stats and environment
4. melee/ranged combat
5. entity/component runtime
6. creatures and AI
7. skills and character progression
8. biome/resource simulation
9. structures, villages, dungeons and cities
10. vehicles and machines
11. multiplayer authoritative server
12. persistent shared worlds

## Tooling

- custom debug/profiler overlay
- content compiler
- shader compiler/cache
- asset database
- world inspection tools
- automated correctness/performance regression tests

The old browser build is retained only as a historical prototype while the native engine reaches feature parity; it is no longer the production architecture.
