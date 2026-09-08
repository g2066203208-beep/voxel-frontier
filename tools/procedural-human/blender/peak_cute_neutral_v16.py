import bpy
import bmesh
import json
import math
import os
import sys
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/peak-cute-neutral')
os.makedirs(OUT_DIR, exist_ok=True)

# PEAK-like cute neutral basemesh v16
# -----------------------------------
# One original, continuous, faceless neutral human shell.
# Construction volumes are only a temporary implicit design scaffold. They are
# voxel-unioned, surface-smoothed, then reduced to a compact game mesh.
# No external human mesh, no hair, no facial geometry, no clothing, no props.

HEIGHT = 1.50
SIDES = 12
VOXEL_SIZE = 0.0125
TARGET_TRIS = 820

# z, half-width, half-depth.  These sections deliberately describe a compact,
# cute, almost bean-like torso rather than adult anatomy.
TORSO = [
    (0.575, 0.142, 0.105),   # pelvis / leg union
    (0.625, 0.150, 0.110),
    (0.700, 0.151, 0.111),
    (0.785, 0.146, 0.108),
    (0.870, 0.143, 0.106),   # soft waist
    (0.955, 0.148, 0.109),
    (1.025, 0.157, 0.112),   # chest
    (1.080, 0.162, 0.110),   # shoulder mass
    (1.125, 0.132, 0.094),
    (1.165, 0.082, 0.069),   # short neck union
]

LEGS = [
    (0.060, 0.058, 0.058),
    (0.120, 0.050, 0.052),   # ankle
    (0.220, 0.057, 0.059),
    (0.320, 0.064, 0.065),   # calf
    (0.405, 0.057, 0.059),   # knee
    (0.495, 0.069, 0.069),
    (0.575, 0.080, 0.076),   # thigh root overlaps pelvis
]

ARM_RADII = [
    (0.062, 0.057),
    (0.059, 0.054),
    (0.053, 0.049),
    (0.046, 0.043),
    (0.039, 0.037),
]


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def append_part(V, F, verts, faces):
    off = len(V)
    V.extend(verts)
    F.extend([[off + i for i in f] for f in faces])


def cap(center, ring, reverse=False):
    out = []
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        out.append([center, ring[j], ring[i]] if reverse else [center, ring[i], ring[j]])
    return out


def loft(sections, cx=0.0, cy=0.0, sides=SIDES):
    V, F, rings = [], [], []
    for z, rx, ry in sections:
        ring = []
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            ring.append(len(V))
            V.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
        rings.append(ring)
    for r in range(len(rings) - 1):
        a, b = rings[r], rings[r + 1]
        for i in range(sides):
            j = (i + 1) % sides
            F.append([a[i], a[j], b[j]])
            F.append([a[i], b[j], b[i]])
    c = len(V); V.append((cx, cy, sections[0][0])); F += cap(c, rings[0], True)
    c = len(V); V.append((cx, cy, sections[-1][0])); F += cap(c, rings[-1], False)
    return V, F


def ellipsoid(center, radii, segments=18, internal_rings=8):
    cx, cy, cz = center
    rx, ry, rz = radii
    V = [(cx, cy, cz + rz)]
    rings = []
    for r in range(1, internal_rings + 1):
        th = math.pi * r / (internal_rings + 1)
        st, ct = math.sin(th), math.cos(th)
        ring = []
        for i in range(segments):
            ph = 2.0 * math.pi * i / segments
            ring.append(len(V))
            V.append((cx + rx * st * math.cos(ph), cy + ry * st * math.sin(ph), cz + rz * ct))
        rings.append(ring)
    bottom = len(V)
    V.append((cx, cy, cz - rz))
    F = []
    for i in range(segments):
        F.append([0, rings[0][i], rings[0][(i + 1) % segments]])
    for r in range(len(rings) - 1):
        a, b = rings[r], rings[r + 1]
        for i in range(segments):
            j = (i + 1) % segments
            F.append([a[i], b[i], b[j]])
            F.append([a[i], b[j], a[j]])
    last = rings[-1]
    for i in range(segments):
        F.append([last[i], bottom, last[(i + 1) % segments]])
    return V, F


def tube(points, radii, sides=SIDES):
    V, F, rings = [], [], []
    ref = Vector((0, 1, 0))
    for k, p0 in enumerate(points):
        p = Vector(p0)
        if k == 0:
            t = Vector(points[1]) - p
        elif k == len(points) - 1:
            t = p - Vector(points[k - 1])
        else:
            t = Vector(points[k + 1]) - Vector(points[k - 1])
        t.normalize()
        n1 = t.cross(ref)
        if n1.length < 1e-6:
            n1 = t.cross(Vector((1, 0, 0)))
        n1.normalize()
        n2 = t.cross(n1).normalized()
        rx, ry = radii[k]
        ring = []
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            q = p + n1 * (rx * math.cos(a)) + n2 * (ry * math.sin(a))
            ring.append(len(V))
            V.append(tuple(q))
        rings.append(ring)
    for r in range(len(rings) - 1):
        a, b = rings[r], rings[r + 1]
        for i in range(sides):
            j = (i + 1) % sides
            F.append([a[i], a[j], b[j]])
            F.append([a[i], b[j], b[i]])
    c = len(V); V.append(tuple(points[0])); F += cap(c, rings[0], True)
    c = len(V); V.append(tuple(points[-1])); F += cap(c, rings[-1], False)
    return V, F


def scaffold_geometry():
    V, F = [], []
    append_part(V, F, *loft(TORSO))

    # Large blank head with no face construction at all.  It overlaps the neck
    # deeply enough that the voxel union produces a continuous soft transition.
    append_part(V, F, *ellipsoid((0.0, -0.004, 1.320), (0.184, 0.171, 0.182), 18, 8))

    for s in (-1, 1):
        append_part(V, F, *loft(LEGS, cx=s * 0.069))

        # Small rounded foot.  Slightly forward, but deliberately not shoe-like.
        append_part(V, F, *ellipsoid((s * 0.069, -0.041, 0.047), (0.063, 0.092, 0.049), 12, 4))

        # Arm root starts deep inside the shoulder mass.  The centerline bows out
        # gently and then hangs nearly vertically, producing a natural silhouette.
        pts = [
            (s * 0.137,  0.000, 1.068),
            (s * 0.165, -0.001, 1.005),
            (s * 0.181, -0.003, 0.925),
            (s * 0.190, -0.005, 0.835),
            (s * 0.187, -0.007, 0.748),
        ]
        append_part(V, F, *tube(pts, ARM_RADII))

        # Tiny mitten-like hand; still part of the final single exterior shell.
        append_part(V, F, *ellipsoid((s * 0.187, -0.010, 0.704), (0.043, 0.037, 0.054), 12, 4))

    return V, F


def material(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*rgb, 1.0)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*rgb, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.94
    return m


def raw_object():
    V, F = scaffold_geometry()
    me = bpy.data.meshes.new('PeakCuteNeutralV16ScaffoldMesh')
    me.from_pydata(V, [], F)
    me.update()
    ob = bpy.data.objects.new('PeakCuteNeutralV16', me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material('NeutralBody', (0.79, 0.75, 0.73)))
    return ob


def tri_count(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


def apply_smooth(ob, factor, iterations, name):
    mod = ob.modifiers.new(name, 'SMOOTH')
    mod.factor = factor
    mod.iterations = iterations
    mod.use_x = True
    mod.use_y = True
    mod.use_z = True
    bpy.ops.object.modifier_apply(modifier=mod.name)


def fuse_to_single_shell(ob):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # Higher-resolution union than v15 to eliminate head dents and preserve the
    # intended silhouette before polygon reduction.
    ob.data.remesh_voxel_size = VOXEL_SIZE
    ob.data.remesh_voxel_adaptivity = 0.0
    bpy.ops.object.voxel_remesh()

    # Relax voxel stair-stepping before decimation; this is surface smoothing,
    # not subdivision, so polygon budget remains governed by the final decimator.
    apply_smooth(ob, 0.38, 3, 'PreDecimateSurfaceRelax')

    before = tri_count(ob)
    dec = ob.modifiers.new('LowPoly', 'DECIMATE')
    dec.decimate_type = 'COLLAPSE'
    dec.ratio = max(0.001, min(1.0, TARGET_TRIS / max(before, 1)))
    dec.use_collapse_triangulate = True
    try:
        dec.use_symmetry = True
        dec.symmetry_axis = 'X'
    except Exception:
        pass
    bpy.ops.object.modifier_apply(modifier=dec.name)

    # Very small post relaxation removes isolated QEM spikes without washing out
    # the low-poly silhouette.
    apply_smooth(ob, 0.10, 1, 'PostDecimateRelax')

    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.update()
    return before, tri_count(ob)


def topology_metrics(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            v = stack.pop()
            for e in v.link_edges:
                ov = e.other_vert(v)
                if ov in unseen:
                    unseen.remove(ov)
                    stack.append(ov)
    out = {
        'connected_components': components,
        'boundary_edges': boundary,
        'nonmanifold_edges': nonmanifold,
        'verts': len(bm.verts),
        'edges': len(bm.edges),
        'faces': len(bm.faces),
    }
    bm.free()
    return out


def make():
    ob = raw_object()
    before, after = fuse_to_single_shell(ob)
    topo = topology_metrics(ob)
    return ob, before, after, topo


def studio(camera_mode='threequarter'):
    sc = bpy.context.scene
    sc.render.resolution_x = 1050
    sc.render.resolution_y = 1200
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.engine = 'BLENDER_EEVEE'
    sc.world.color = (0.026, 0.029, 0.035)

    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.002))
    bpy.context.object.data.materials.append(material('Floor', (0.075, 0.080, 0.090)))

    for name, loc, energy, size in [
        ('Key', (-3.2, -4.1, 4.0), 950, 2.7),
        ('Fill', (3.0, -3.0, 2.5), 400, 2.4),
        ('Rim', (0.0, 3.2, 3.2), 650, 2.0),
    ]:
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy; ld.shape = 'DISK'; ld.size = size
        o = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.76)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cd)
    bpy.context.collection.objects.link(cam)
    if camera_mode == 'front':
        cam.location = (0.0, -5.0, 1.28)
    else:
        cam.location = (1.18, -4.8, 1.30)
    cam.rotation_euler = (Vector((0, 0, 0.75)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = 78
    sc.camera = cam


def export_model():
    clear_scene()
    ob, before, after, topo = make()
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, 'neutral.glb'), export_format='GLB', use_selection=True)
    return before, after, topo


def render_view(filename, mode):
    clear_scene()
    ob, _, _, _ = make()
    studio(mode)
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR, filename)
    bpy.ops.render.render(write_still=True)


before, after, topo = export_model()
render_view('neutral-preview.png', 'threequarter')
render_view('neutral-front.png', 'front')

metrics = {
    'style': 'peak-like-cute-neutral-single-shell-v16',
    'original_geometry': True,
    'external_character_mesh': False,
    'neutral_only': True,
    'male_female_split': False,
    'hair': False,
    'face_addons': False,
    'clothing': False,
    'props': False,
    'height_m': HEIGHT,
    'head_height_m': 0.364,
    'visual_head_ratio': round(HEIGHT / 0.364, 3),
    'tris_before_decimate': before,
    'tris': after,
    'single_continuous_shell': topo['connected_components'] == 1 and topo['boundary_edges'] == 0 and topo['nonmanifold_edges'] == 0,
    **topo,
    'voxel_size_m': VOXEL_SIZE,
    'target_tris': TARGET_TRIS,
    'topology_method': 'semantic volumes -> high-res voxel union -> surface relax -> symmetric low-poly reduction -> one exterior manifold shell',
    'shading': 'smooth normals',
    'blender_version': '.'.join(map(str, bpy.app.version)),
}
with open(os.path.join(OUT_DIR, 'metrics.json'), 'w', encoding='utf-8') as f:
    json.dump(metrics, f, indent=2)
with open(os.path.join(OUT_DIR, 'section_spec.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'torso': TORSO,
        'legs': LEGS,
        'arm_radii': ARM_RADII,
        'head': {'center': [0.0, -0.004, 1.320], 'radii': [0.184, 0.171, 0.182]},
        'feet': {'center_y': -0.041, 'radii': [0.063, 0.092, 0.049]},
    }, f, indent=2)
print('PEAK_CUTE_NEUTRAL_V16_METRICS', json.dumps(metrics))
