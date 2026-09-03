# Physics v5 — GJK / EPA convex collision foundation

This milestone follows the same broad narrow-phase structure used by mature rigid-body engines: support-mapped convex intersection first, penetration/contact reconstruction second.

## Primary references

- Jolt Physics architecture and narrow phase: https://jrouwe.github.io/JoltPhysicsDocs/5.3.0/index.html
- Jolt GJK / EPA implementation sources: https://github.com/jrouwe/JoltPhysics/tree/master/Jolt/Geometry
- Box3D collision documentation: https://box3d.org/documentation/md_collision.html
- Erin Catto publications (GJK, contact manifolds, sequential impulses): https://box2d.org/publications/

## Implemented in this stage

- fixed-capacity support-mapped Minkowski vertices carrying witness points on A and B
- 3D GJK simplex progression: point -> line -> triangle -> tetrahedron
- EPA polytope expansion from the terminal GJK tetrahedron
- penetration normal and depth recovery
- barycentric witness-point reconstruction for the contact position
- engine normal convention preserved as A -> B
- optional convergence diagnostics
- no per-query heap allocation
- dedicated Box/Capsule regression coverage including pair reversal, separation, rotation and deep overlap

## Deliberate boundary

The current GJK/EPA layer emits one witness contact. It does not yet replace the existing high-quality Box/Box SAT + face-clipping manifold path. The next integration stage will route Box/Capsule through GJK/EPA, then add ConvexHull support and polyhedral face clipping/manifold reduction for arbitrary convex pairs.
