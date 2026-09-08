import bpy
import json
import math
import os
import sys
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/peak-cute-neutral')
os.makedirs(OUT_DIR, exist_ok=True)

# PEAK-like cute neutral basemesh v13
# -----------------------------------
# Original procedural character basemesh inspired only by the broad visual language
# of simple cute 3D game avatars: large blank head, compact torso, narrow shoulders,
# clean tapered limbs, small hands and stable feet.
#
# No extracted game mesh. No hair, facial features, clothes, props, gender split,
# adult MakeHuman/MPFB source, or QEM-decimated anatomy. Geometry is built directly
# from semantic section rings and simple primitive volumes.

HEIGHT = 1.55
RING_SIDES = 8

# Semantic body sections (z, half-width x, half-depth y), meters.
TORSO_SECTIONS = [
    (0.700, 0.145, 0.105),  # pelvis / leg merge
    (0.790, 0.150, 0.108),
    (0.900, 0.140, 0.102),  # waist
    (0.990, 0.155, 0.110),  # chest
    (1.070, 0.172, 0.108),  # shoulder shelf
    (1.125, 0.112, 0.082),
    (1.185, 0.060, 0.056),  # neck
]

LEG_SECTIONS = [
    (0.085, 0.052, 0.055),
    (0.165, 0.043, 0.046),  # ankle
    (0.330, 0.058, 0.060),  # calf
    (0.445, 0.049, 0.052),  # knee
    (0.590, 0.070, 0.070),  # thigh
    (0.715, 0.087, 0.078),  # thigh root
]

ARM_RADII = [
    (0.054, 0.050),
    (0.048, 0.044),
    (0.041, 0.038),
    (0.032, 0.030),
]


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def append_part(dst_v, dst_f, verts, faces):
    off = len(dst_v)
    dst_v.extend(verts)
    dst_f.extend([[off + i for i in f] for f in faces])


def cap_fan(center_idx, ring, reverse=False):
    faces = []
    n = len(ring)
    for i in range(n):
        a = ring[i]
        b = ring[(i + 1) % n]
        faces.append([center_idx, b, a] if reverse else [center_idx, a, b])
    return faces


def loft_vertical(sections, sides=8, center_x=0.0, center_y=0.0):
    verts = []
    faces = []
    rings = []
    for z, rx, ry in sections:
        ring = []
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            ring.append(len(verts))
            verts.append((center_x + rx * math.cos(a), center_y + ry * math.sin(a), z))
        rings.append(ring)
    for r in range(len(rings) - 1):
        a, b = rings[r], rings[r + 1]
        for i in range(sides):
            j = (i + 1) % sides
            faces.append([a[i], a[j], b[j]])
            faces.append([a[i], b[j], b[i]])
    bottom_center = len(verts)
    z, _, _ = sections[0]
    verts.append((center_x, center_y, z))
    faces += cap_fan(bottom_center, rings[0], reverse=True)
    top_center = len(verts)
    z, _, _ = sections[-1]
    verts.append((center_x, center_y, z))
    faces += cap_fan(top_center, rings[-1], reverse=False)
    return verts, faces


def ellipsoid(center, radii, segments=12, internal_rings=5):
    cx, cy, cz = center
    rx, ry, rz = radii
    verts = [(cx, cy, cz + rz)]
    rings = []
    for r in range(1, internal_rings + 1):
        theta = math.pi * r / (internal_rings + 1)
        st, ct = math.sin(theta), math.cos(theta)
        ring = []
        for i in range(segments):
            phi = 2.0 * math.pi * i / segments
            ring.append(len(verts))
            verts.append((cx + rx * st * math.cos(phi), cy + ry * st * math.sin(phi), cz + rz * ct))
        rings.append(ring)
    bottom = len(verts)
    verts.append((cx, cy, cz - rz))
    faces = []
    for i in range(segments):
        faces.append([0, rings[0][i], rings[0][(i + 1) % segments]])
    for r in range(len(rings) - 1):
        a, b = rings[r], rings[r + 1]
        for i in range(segments):
            j = (i + 1) % segments
            faces.append([a[i], b[i], b[j]])
            faces.append([a[i], b[j], a[j]])
    last = rings[-1]
    for i in range(segments):
        faces.append([last[i], bottom, last[(i + 1) % segments]])
    return verts, faces


def tube_along(points, radii, sides=8):
    verts = []
    faces = []
    rings = []
    ref = Vector((0.0, 1.0, 0.0))
    for idx, p_raw in enumerate(points):
        p = Vector(p_raw)
        if idx == 0:
            tangent = Vector(points[1]) - p
        elif idx == len(points) - 1:
            tangent = p - Vector(points[idx - 1])
        else:
            tangent = Vector(points[idx + 1]) - Vector(points[idx - 1])
        tangent.normalize()
        n1 = tangent.cross(ref)
        if n1.length < 1e-6:
            n1 = tangent.cross(Vector((1.0, 0.0, 0.0)))
        n1.normalize()
        n2 = tangent.cross(n1).normalized()
        rx, ry = radii[idx]
        ring = []
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            pos = p + n1 * (rx * math.cos(a)) + n2 * (ry * math.sin(a))
            ring.append(len(verts))
            verts.append(tuple(pos))
        rings.append(ring)
    for r in range(len(rings) - 1):
        a, b = rings[r], rings[r + 1]
        for i in range(sides):
            j = (i + 1) % sides
            faces.append([a[i], a[j], b[j]])
            faces.append([a[i], b[j], b[i]])
    c0 = len(verts); verts.append(tuple(points[0])); faces += cap_fan(c0, rings[0], reverse=True)
    c1 = len(verts); verts.append(tuple(points[-1])); faces += cap_fan(c1, rings[-1], reverse=False)
    return verts, faces


def foot_wedge(sign):
    # Short, slightly oversized and stable foot. Front is -Y in the preview camera.
    cx = sign * 0.076
    x0, x1 = cx - 0.060, cx + 0.060
    y_back, y_front = 0.040, -0.125
    z0, z1, ztoe = 0.000, 0.075, 0.050
    verts = [
        (x0, y_back, z0), (x1, y_back, z0), (x1, y_front, z0), (x0, y_front, z0),
        (x0, y_back, z1), (x1, y_back, z1), (x1, y_front, ztoe), (x0, y_front, ztoe),
    ]
    faces = [
        [0, 2, 1], [0, 3, 2],
        [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4],
        [1, 2, 6], [1, 6, 5],
        [2, 3, 7], [2, 7, 6],
        [3, 0, 4], [3, 4, 7],
    ]
    return verts, faces


def build_geometry():
    V, F = [], []

    # Torso / pelvis
    append_part(V, F, *loft_vertical(TORSO_SECTIONS, RING_SIDES))

    # Head: blank oversized rounded head, no facial geometry.
    append_part(V, F, *ellipsoid((0.0, -0.006, 1.375), (0.158, 0.148, 0.175), segments=12, internal_rings=5))

    # Legs: slightly inward under the pelvis; intersections are intentional to keep
    # the silhouette continuous without an expensive boolean/remesh operation.
    for sign in (-1, 1):
        append_part(V, F, *loft_vertical(LEG_SECTIONS, RING_SIDES, center_x=sign * 0.076))
        append_part(V, F, *foot_wedge(sign))

    # Arms hang nearly straight with a tiny outward curve, PEAK-like simple rhythm.
    for sign in (-1, 1):
        pts = [
            (sign * 0.165, 0.000, 1.070),
            (sign * 0.190, 0.002, 0.955),
            (sign * 0.205, 0.000, 0.825),
            (sign * 0.195, -0.003, 0.705),
        ]
        append_part(V, F, *tube_along(pts, ARM_RADII, RING_SIDES))
        append_part(V, F, *ellipsoid((sign * 0.195, -0.008, 0.655), (0.043, 0.035, 0.055), segments=8, internal_rings=1))

    return V, F


def material(name='NeutralBody'):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (0.78, 0.74, 0.72, 1.0)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.78, 0.74, 0.72, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.92
    return m


def make_neutral():
    verts, faces = build_geometry()
    me = bpy.data.meshes.new('PeakCuteNeutralV13Mesh')
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new('PeakCuteNeutralV13', me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material())
    # Smooth low-poly surface: simple geometry but not faceted/origami-like.
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def export_glb():
    clear_scene()
    ob = make_neutral()
    tris = tri_count(ob)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, 'neutral.glb'), export_format='GLB', use_selection=True)
    return tris


def studio():
    sc = bpy.context.scene
    sc.render.resolution_x = 1050
    sc.render.resolution_y = 1200
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.engine = 'BLENDER_EEVEE'
    sc.world.color = (0.026, 0.029, 0.035)
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass

    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.002))
    floor = bpy.context.object
    fm = bpy.data.materials.new('Floor')
    fm.diffuse_color = (0.075, 0.080, 0.090, 1.0)
    floor.data.materials.append(fm)

    for name, loc, energy, size in [
        ('Key', (-3.2, -4.1, 4.0), 950, 2.7),
        ('Fill', (3.0, -3.0, 2.5), 400, 2.4),
        ('Rim', (0.0, 3.2, 3.2), 650, 2.0),
    ]:
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.shape = 'DISK'
        ld.size = size
        lob = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(lob)
        lob.location = loc
        lob.rotation_euler = (Vector((0, 0, 0.80)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cd)
    bpy.context.collection.objects.link(cam)
    cam.location = (1.35, -5.2, 1.45)
    cam.rotation_euler = (Vector((0, 0, 0.79)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = 76
    sc.camera = cam


def render_preview():
    clear_scene()
    ob = make_neutral()
    ob.rotation_euler[2] = math.radians(3.0)
    studio()
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR, 'neutral-preview.png')
    bpy.ops.render.render(write_still=True)


tris = export_glb()
render_preview()

metrics = {
    'style': 'peak-like-cute-neutral-basemesh-v13',
    'original_geometry': True,
    'external_character_mesh': False,
    'neutral_only': True,
    'male_female_split': False,
    'hair': False,
    'face_addons': False,
    'clothing': False,
    'props': False,
    'extra_character_geometry': False,
    'height_m': HEIGHT,
    'head_height_m': 0.350,
    'visual_head_ratio': round(HEIGHT / 0.350, 3),
    'tris': tris,
    'torso_section_count': len(TORSO_SECTIONS),
    'leg_section_count': len(LEG_SECTIONS),
    'arm_section_count': len(ARM_RADII),
    'ring_sides': RING_SIDES,
    'topology_method': 'semantic section lofts + low-poly ellipsoids/wedges; no QEM decimation',
    'shading': 'smooth normals',
    'blender_version': '.'.join(map(str, bpy.app.version)),
}

with open(os.path.join(OUT_DIR, 'metrics.json'), 'w', encoding='utf-8') as f:
    json.dump(metrics, f, indent=2)

with open(os.path.join(OUT_DIR, 'section_spec.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'torso_sections': TORSO_SECTIONS,
        'leg_sections': LEG_SECTIONS,
        'arm_radii': ARM_RADII,
        'head': {'center': [0.0, -0.006, 1.375], 'radii': [0.158, 0.148, 0.175]},
    }, f, indent=2)

print('PEAK_CUTE_NEUTRAL_V13_METRICS', json.dumps(metrics))
