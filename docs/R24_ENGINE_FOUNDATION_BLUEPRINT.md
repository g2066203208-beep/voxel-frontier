# R24 Engine Foundation Blueprint

## Goal

Build the engine so that later enabling terrain, thousands of voxel objects, physics, atmosphere, water and celestial systems cannot turn the main thread into a serial bottleneck. Rendering is uncapped. 120 FPS is the minimum gameplay acceptance line, not a frame cap.

## Proven architecture sources

- Taskflow 4.1.0: reusable C++ task graphs and work-stealing executor.
- EnTT 4.0.0: data-oriented ECS storage/views/groups for hot iteration paths.
- Jolt Physics architecture: active/sleeping bodies, static/dynamic broadphase layers, parallel collision jobs and island solving.
- Granite Vulkan render graph: automatic resource transitions, lifetime tracking, queue overlap and transient-resource reuse.
- Khronos modern Vulkan: Vulkan 1.4 baseline, dynamic rendering, Synchronization2, timeline semaphores and dedicated transfer streaming.
- meshoptimizer: meshlets/clusters for GPU culling and indirect/mesh-shader rendering.
- Voxel Tools: bounded main-thread upload budgets and avoidance of unlimited copied chunk work.

## Non-negotiable foundation rules

1. No heavyweight subsystem owns the main loop.
2. Fixed-step simulation and render rate are independent.
3. No queue can convert backlog size directly into same-frame work.
4. Every asynchronous result carries a revision/generation token; stale results are discarded.
5. Static, dynamic and streaming data use different update paths.
6. Render consumes extracted frame data instead of reaching into live gameplay state.
7. GPU uploads are batched and budgeted; no arbitrary per-chunk upload storm.
8. Long-lived world state is data-oriented. Per-object virtual dispatch is kept away from hot loops.
9. Visibility decides what is rendered before expensive rendering work is scheduled.
10. Performance telemetry and regression gates are part of the architecture, not post-release tools.

## Engine frame phases

The production task graph reserves these slots in order:

1. Input
2. SimulationPrepare
3. SimulationFixed
4. SimulationPost
5. WorldStreaming
6. Visibility
7. RenderExtract
8. RenderPrepare
9. Housekeeping

Tasks inside a phase may execute in parallel through work stealing. Hard phase barriers preserve ownership and deterministic dependencies. Later render submission/present runs from the render backend, not from arbitrary world systems.

## World/voxel streaming pipeline

A world cell is identified by world/body ID + integer cell coordinates + LOD. The state machine is:

Unloaded -> Requested -> Generating -> MeshingQueued -> Meshing -> UploadQueued -> Uploading -> Resident -> EvictionQueued -> Evicting -> Unloaded

Rules:

- Requests are stored in priority queues.
- Updating priority does not mutate heaps in place; a new revision is queued and stale entries are ignored.
- Generation, meshing, upload and eviction have independent per-frame budgets.
- A 100,000-cell request spike may increase queue depth, but cannot schedule 100,000 same-frame jobs.
- Camera distance, screen-space error, velocity prediction, gameplay importance and occlusion will feed the priority score later.
- GPU upload bytes and commit counts are separately capped.

## Physics scaling position

Physics is not enabled next. First the engine core and streaming path must be stable.

When physics is enabled it will follow Jolt-style separation:

- Static world colliders: infrequently rebuilt broadphase layer.
- Dynamic bodies: separate frequently updated broadphase layer.
- Kinematic gameplay bodies: explicit layer/filtering.
- Only active bodies enter expensive integration/collision work.
- Sleeping islands remain out of hot loops.
- Voxel destruction rebuilds collision by dirty region/chunk, never by rescanning the whole world.
- Many decorative blocks remain render-only until interaction promotes them into physics bodies.
- Large piles use sleeping/island batching and may demote back to aggregate/static representation when settled.

## Rendering scaling position

The current renderer will be migrated behind a Render Graph/RHI boundary before expensive visual modules are re-enabled.

Planned path:

- Vulkan 1.4 capability profile with fallback feature table.
- Dynamic Rendering + Synchronization2.
- Graphics / compute / transfer queue ownership tracked centrally.
- Timeline semaphores for streaming and queue dependencies.
- Persistent GPU buffers and suballocation (VMA planned for allocator integration).
- Bindless/descriptor-indexed material table where supported.
- GPU-driven visibility buffers and indirect draws.
- meshoptimizer meshlets for terrain, props and chunk meshes.
- Frustum + HZB occlusion + distance/SSE culling before raster work.
- Async compute only when measured overlap is beneficial; no async-compute-for-fashion.

## Activation order

Do not enable everything at once. Each stage must pass 1080p uncapped timing and hitch gates before the next stage.

### Stage F0 — Engine foundation (current)

Renderer OFF, Present OFF, world modules OFF. Validate scheduler, bounded fixed-step clock, streaming state machine and 100k-cell stress.

### Stage F1 — Platform + empty Vulkan presentation

Enable SDL/platform, Vulkan device/swapchain and a clear-only frame. No camera, no world, no sky. This isolates pure renderer/present cost and establishes Vulkan 1.4 capability/queue/timeline infrastructure.

### Stage F2 — Camera + frame extraction

Enable camera/input and immutable render-frame extraction only. No terrain. Verify input latency and that simulation/render rates are independent.

### Stage F3 — Render Graph + static synthetic geometry

Render a controlled synthetic mesh workload through the new graph. Establish resource lifetime, upload queue, GPU timestamps, indirect draw path and visibility framework before procedural terrain exists.

### Stage F4 — WorldPartition with synthetic chunks

Stream thousands of fake chunk payloads through generation -> meshing -> upload -> resident using hard budgets. No procedural terrain complexity yet. Test high-speed camera traversal and queue pressure.

### Stage F5 — Real static terrain

Connect existing procedural terrain to WorldPartition. Terrain generation/meshing stays off the main thread. Renderer consumes resident chunk/meshlet packets only.

### Stage F6 — Terrain streaming + ecology/props

Enable moving LOD/streaming and GPU visibility. Ecology is instanced/batched and must not create one draw or physics body per object.

### Stage F7 — Physics

Enable static terrain collision first, then a controlled dynamic-body ladder: 10 -> 100 -> 1,000 -> 10,000 active/sleeping bodies. Introduce Jolt-compatible backend boundary, active body lists, layers, sleeping islands and dirty-region collider rebuilds.

### Stage F8 — Sky / atmosphere

Enable cached/precomputed atmosphere through the Render Graph. Atmosphere cannot return to full-resolution per-pixel multi-scattering integration every frame.

### Stage F9 — Water

Enable water after the transparent path, visibility and async resource infrastructure are stable.

### Stage F10 — Celestial / weather / UI / complete gameplay

Enable low-frequency/global simulation clients last, then run full high-speed traversal and frame-pacing certification.

## Acceptance ladder

Every stage records:

- average FPS
- 1% low FPS
- P95/P99/max frame time
- CPU phase timings
- GPU pass timings
- queue depths and dropped/stale jobs
- streaming bytes/jobs per frame
- active/sleeping physics body counts
- resident world cells and GPU memory

Software CI is for regression and relative attribution. Final 120+ FPS certification must run on real discrete GPU hardware at 1920x1080 with real gameplay features enabled.
