# Physics Contact Solver References

Voxel Frontier's contact solver is custom C++ code. The projects below are used as engineering references and validation targets, not as runtime dependencies.

## Jolt Physics

Reference: https://jrouwe.github.io/JoltPhysics/

Relevant architecture followed:

- broad phase works on conservative bounds before expensive shape tests;
- narrow phase operates on transformed collision shapes;
- support-mapped convex collision is organized around GJK/EPA;
- contact manifolds are generated separately from constraint solving;
- contact constraints use Jacobians/effective mass and persistent state.

Voxel Frontier v4 follows this separation: `Broadphase` -> `CollisionGeometry` -> persistent contact cache -> sequential impulse solve.

## Box2D / Erin Catto

References:

- https://box2d.org/publications/
- https://box2d.org/posts/2024/02/solver2d/

Relevant techniques followed:

- contact manifolds rather than one ad-hoc center impulse;
- accumulated impulses with clamping;
- warm starting from the previous fixed step;
- iterative sequential impulses at real contact points;
- friction bounded by the accumulated normal impulse.

## Box3D / Erin Catto

Reference: https://github.com/erincatto/box3d

Useful 3D scale/default references used by the current solver:

- linear slop: 0.005 m;
- contact recycle distance: 10 x linear slop = 0.05 m;
- restitution velocity threshold: 1.0 m/s;
- bounded contact push speed: 3.0 m/s;
- convex contact manifolds support up to four points.

Voxel Frontier does not claim bit-for-bit Box3D behavior. The current solver still uses a classic Baumgarte velocity bias for penetration recovery; Box3D's modern soft-contact formulation is a future comparison/validation target.

## Bullet Physics

Reference: https://github.com/bulletphysics/bullet3

Bullet is retained as a cross-check for persistent manifold concepts, shape-pair organization and mature rigid-body behavior.

## Scope of v4

Implemented in this milestone:

1. authoritative Sphere / oriented Box / Capsule collision shapes;
2. exact shape AABB sweep-and-prune broadphase;
3. specialized sphere/box/capsule narrow phase;
4. full 15-axis OBB SAT;
5. reference/incident face clipping for up to four OBB contacts;
6. persistent contact cache using feature IDs and local-anchor fallback matching;
7. normal and friction warm starting;
8. point-contact sequential impulses with angular effective mass;
9. restitution threshold and bounded penetration recovery;
10. shape-aware planet support contact.

Deliberately not approximated in v4:

- Box/Capsule and arbitrary convex pairs: these wait for the shared GJK/EPA path;
- compound collision shapes: the gear demonstration's second visual cross-bar is not yet authoritative collision geometry;
- non-spherical distributed buoyancy: boats and large hulls will use multiple displaced-volume samples rather than a fake bounding-sphere volume.
