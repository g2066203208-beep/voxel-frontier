import bpy
import json
import math
import os
import sys
import urllib.request
from collections import defaultdict
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/slice-neutral-human')
os.makedirs(OUT_DIR, exist_ok=True)

# Slice-Driven Cute Neutral Basemesh v12
# --------------------------------------
# One neutral body only. No male/female split, no hair, facial add-ons,
# clothing, props, or extra character geometry.
#
# The body is controlled by an explicit vertical slice lattice. Each control
# slice defines target vertical position, width scale and depth scale. The
# original CC0 body vertices are deformed by interpolation between slices,
# then reconstructed as a compact low-poly mesh. After generation, the final
# mesh is cut again by real horizontal planes to measure contour loops,
# section width/depth/area and integrated volume.

BASE_URL = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2/3dobjs/base.obj'
TARGET_HEIGHT = 1.62
TARGET_TRIS = 1050
SLICE_COUNT = 49

# q_source, z_target_normalized, width_scale, depth_scale, semantic label
# Art direction: cute Japanese 3D-game neutral basemesh. Roughly 6.3 heads,
# compact torso, narrow shoulder line, small waist/pelvis rhythm, slim healthy
# limbs, small hands and feet. Values remain close enough to the real CC0 body
# to preserve anatomy while giving a cleaner stylized silhouette.
CONTROL_SLICES = [
    (0.000, 0.000, 0.94, 0.91, 'sole'),
    (0.055, 0.055, 0.88, 0.90, 'ankle'),
    (0.150, 0.158, 0.93, 0.95, 'calf'),
    (0.250, 0.267, 0.90, 0.93, 'knee'),
    (0.365, 0.402, 0.95, 0.98, 'thigh'),
    (0.470, 0.520, 0.98, 1.00, 'crotch'),
    (0.525, 0.575, 0.99, 1.00, 'pelvis'),
    (0.590, 0.635, 0.94, 0.96, 'waist'),
    (0.675, 0.708, 0.96, 0.97, 'lower_rib'),
    (0.740, 0.766, 0.97, 0.98, 'chest'),
    (0.795, 0.815, 0.94, 0.96, 'shoulder'),
    (0.835, 0.842, 0.82, 0.88, 'neck'),
    (0.865, 0.868, 1.02, 1.02, 'jaw'),
    (0.915, 0.920, 1.11, 1.09, 'face'),
    (0.965, 0.970, 1.13, 1.11, 'cranium'),
    (1.000, 1.000, 1.08, 1.08, 'crown'),
]


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'voxel-frontier-slice-neutral-v12'})
    return urllib.request.urlopen(req, timeout=60).read().decode('utf-8')


def parse_obj_body(text):
    verts, faces = [], []
    group = ''
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('v '):
            p = line.split()
            verts.append([float(p[1]), float(p[2]), float(p[3])])
        elif line.startswith('g '):
            group = line[2:].strip().split()[0] if line[2:].strip() else ''
        elif line.startswith('f ') and group == 'body':
            ids = [int(t.split('/')[0]) - 1 for t in line[2:].split()]
            if len(ids) >= 3:
                faces.append(ids)
    if len(verts) < 1000 or len(faces) < 1000:
        raise RuntimeError(f'Unexpected body mesh: {len(verts)} verts, {len(faces)} faces')
    return verts, faces


def axis_frame(verts):
    mins = [min(v[a] for v in verts) for a in range(3)]
    maxs = [max(v[a] for v in verts) for a in range(3)]
    ranges = [maxs[a] - mins[a] for a in range(3)]
    order = sorted(range(3), key=lambda a: ranges[a], reverse=True)
    return mins, maxs, ranges, order[1], order[2], order[0]


def interp_slice(q, field_index):
    if q <= CONTROL_SLICES[0][0]:
        return CONTROL_SLICES[0][field_index]
    if q >= CONTROL_SLICES[-1][0]:
        return CONTROL_SLICES[-1][field_index]
    for i in range(len(CONTROL_SLICES) - 1):
        a, b = CONTROL_SLICES[i], CONTROL_SLICES[i + 1]
        if a[0] <= q <= b[0]:
            t = (q - a[0]) / max(1e-9, b[0] - a[0])
            # smooth cubic interpolation avoids visible bands between slices
            t = t * t * (3.0 - 2.0 * t)
            return a[field_index] * (1.0 - t) + b[field_index] * t
    return CONTROL_SLICES[-1][field_index]


def smoothstep(a, b, x):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    t = (x - a) / (b - a)
    return t * t * (3.0 - 2.0 * t)


def gauss(x, c, s):
    return math.exp(-0.5 * ((x - c) / s) ** 2)


def slice_deform(verts, faces):
    mins, maxs, ranges, width, depth, up = axis_frame(verts)
    H = ranges[up]
    cw = (mins[width] + maxs[width]) * 0.5
    cd = (mins[depth] + maxs[depth]) * 0.5
    used = sorted({i for f in faces for i in f})
    remap = {old: i for i, old in enumerate(used)}

    # Estimate original maximum lateral extent for arm-local coordinates.
    raw_data = []
    max_abs_x = 0.0
    for old in used:
        v = verts[old]
        x = (v[width] - cw) / H
        y = (v[depth] - cd) / H
        q = (v[up] - mins[up]) / H
        raw_data.append((old, x, y, q))
        if 0.50 <= q <= 0.84:
            max_abs_x = max(max_abs_x, abs(x))

    out = []
    for old, x0, y0, q in raw_data:
        z_n = interp_slice(q, 1)
        sx = interp_slice(q, 2)
        sy = interp_slice(q, 3)
        x = x0 * sx
        y = y0 * sy
        z = z_n * TARGET_HEIGHT

        # Head keeps the slice-defined large cranium but softens the lower jaw.
        jaw_gate = gauss(q, 0.872, 0.026)
        x *= 1.0 - 0.025 * jaw_gate
        y *= 1.0 - 0.010 * jaw_gate

        # Arm branch: treat the arm as its own sequence of lateral sections.
        # This keeps a clean upper-arm -> forearm -> hand taper while retaining
        # the original connected body topology.
        torso_edge = 0.108
        ax = abs(x)
        arm_band = smoothstep(0.50, 0.58, q) * (1.0 - smoothstep(0.81, 0.845, q))
        if ax > torso_edge and arm_band > 0.02 and max_abs_x > torso_edge:
            u = min(1.0, max(0.0, (abs(x0) - torso_edge) / max(1e-6, max_abs_x - torso_edge)))
            # slightly shorter arms, with elegant taper
            x_sign = 1.0 if x >= 0 else -1.0
            arm_len = torso_edge + (ax - torso_edge) * 0.90
            x = x_sign * arm_len
            radius = (1.00 - 0.20 * u - 0.10 * smoothstep(0.72, 1.0, u))
            y *= radius
            # compress vertical arm thickness around a simple downward A-pose centerline
            center_z = TARGET_HEIGHT * (0.785 - 0.205 * u)
            z = center_z + (z - center_z) * radius

            # Hand is intentionally a small mitten/wedge volume, not finger spikes.
            if u > 0.80:
                h = smoothstep(0.80, 1.0, u)
                hand_center = TARGET_HEIGHT * 0.585
                y *= 1.0 - 0.42 * h
                z = hand_center + (z - hand_center) * (1.0 - 0.50 * h)
                x = x_sign * (torso_edge + (abs(x) - torso_edge) * (1.0 - 0.16 * h))

        # Leg slice refinement: preserve source anatomy but soften extreme gaps
        # and keep thigh/calf readable after low-poly reconstruction.
        thigh = gauss(q, 0.355, 0.105)
        knee = gauss(q, 0.255, 0.040)
        calf = gauss(q, 0.165, 0.075)
        ankle = gauss(q, 0.060, 0.032)
        x *= 1.0 + 0.018 * thigh - 0.012 * knee + 0.018 * calf - 0.018 * ankle
        y *= 1.0 + 0.010 * thigh + 0.012 * calf

        # Feet remain small and short, with a stable sole plane.
        foot = 1.0 - smoothstep(0.030, 0.085, q)
        if foot > 0.0:
            y *= 1.0 - 0.10 * foot
            if q < 0.016:
                z = 0.0

        out.append((x * TARGET_HEIGHT, y * TARGET_HEIGHT, z))

    compact_faces = [[remap[i] for i in f] for f in faces]
    return out, compact_faces


def material(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*rgb, 1.0)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*rgb, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.90
    return m


def mesh_from_data(name, verts, faces, mat):
    me = bpy.data.meshes.new(name + 'Mesh')
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def reconstruct_lowpoly(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    tri = obj.modifiers.new('Triangulate', 'TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri.name)
    before = tri_count(obj)

    dec = obj.modifiers.new('SliceDriven_QEM', 'DECIMATE')
    dec.decimate_type = 'COLLAPSE'
    dec.ratio = max(0.001, min(1.0, TARGET_TRIS / max(before, 1)))
    dec.use_collapse_triangulate = True
    try:
        dec.use_symmetry = True
        dec.symmetry_axis = 'X'
    except Exception:
        pass
    bpy.ops.object.modifier_apply(modifier=dec.name)

    for p in obj.data.polygons:
        p.use_smooth = True
    obj.data.update()
    return before, tri_count(obj)


def make_neutral():
    verts, faces = parse_obj_body(fetch_text(BASE_URL))
    verts, faces = slice_deform(verts, faces)
    ob = mesh_from_data('CuteNeutralSliceV12', verts, faces, material('NeutralSkin', (0.76, 0.73, 0.71)))
    before, after = reconstruct_lowpoly(ob)
    return ob, before, after


def quant_key(x, y, tol=1e-5):
    return (int(round(x / tol)), int(round(y / tol)))


def triangle_plane_segment(a, b, c, z, eps=1e-8):
    pts = []
    for p, q in ((a, b), (b, c), (c, a)):
        dp, dq = p.z - z, q.z - z
        if abs(dp) < eps and abs(dq) < eps:
            continue
        if abs(dp) < eps:
            pts.append((p.x, p.y))
        elif abs(dq) < eps:
            pts.append((q.x, q.y))
        elif dp * dq < 0.0:
            t = dp / (dp - dq)
            r = p + (q - p) * t
            pts.append((r.x, r.y))
    unique = []
    for p in pts:
        if not any((p[0]-q[0])**2 + (p[1]-q[1])**2 < 1e-14 for q in unique):
            unique.append(p)
    if len(unique) == 2:
        return unique[0], unique[1]
    return None


def trace_loops(segments, tol=1e-5):
    if not segments:
        return []
    coords = {}
    adj = defaultdict(list)
    edges = set()
    for a, b in segments:
        ka, kb = quant_key(*a, tol), quant_key(*b, tol)
        if ka == kb:
            continue
        coords.setdefault(ka, a)
        coords.setdefault(kb, b)
        adj[ka].append(kb)
        adj[kb].append(ka)
        edges.add(tuple(sorted((ka, kb))))

    loops = []
    unused = set(edges)
    while unused:
        e = next(iter(unused))
        start, cur = e[0], e[1]
        loop_keys = [start, cur]
        unused.discard(tuple(sorted((start, cur))))
        prev = start
        guard = 0
        while cur != start and guard < 10000:
            guard += 1
            candidates = [n for n in adj[cur] if n != prev and tuple(sorted((cur, n))) in unused]
            if not candidates:
                # allow closure on the already-used start edge
                candidates = [n for n in adj[cur] if n == start]
            if not candidates:
                break
            nxt = candidates[0]
            edge = tuple(sorted((cur, nxt)))
            unused.discard(edge)
            prev, cur = cur, nxt
            if cur != start:
                loop_keys.append(cur)
        if cur == start and len(loop_keys) >= 3:
            loops.append([coords[k] for k in loop_keys])
    return loops


def polygon_area(loop):
    if len(loop) < 3:
        return 0.0
    s = 0.0
    for i in range(len(loop)):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % len(loop)]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def measure_slices(obj, count=SLICE_COUNT):
    obj.data.calc_loop_triangles()
    verts = [v.co.copy() for v in obj.data.vertices]
    zmin = min(v.z for v in verts)
    zmax = max(v.z for v in verts)
    records = []

    for si in range(count):
        t = (si + 0.5) / count
        z = zmin + (zmax - zmin) * t
        segments = []
        for tri in obj.data.loop_triangles:
            a, b, c = [verts[i] for i in tri.vertices]
            if z < min(a.z, b.z, c.z) or z > max(a.z, b.z, c.z):
                continue
            seg = triangle_plane_segment(a, b, c, z)
            if seg:
                segments.append(seg)
        loops = trace_loops(segments)
        all_pts = [p for loop in loops for p in loop]
        if all_pts:
            xs = [p[0] for p in all_pts]
            ys = [p[1] for p in all_pts]
            width = max(xs) - min(xs)
            depth = max(ys) - min(ys)
            area = sum(polygon_area(loop) for loop in loops)
        else:
            width = depth = area = 0.0
        records.append({
            'index': si,
            't': round(t, 6),
            'z_m': round(z, 6),
            'width_m': round(width, 6),
            'depth_m': round(depth, 6),
            'area_m2': round(area, 8),
            'components': len(loops),
            'loops': [[[round(x, 6), round(y, 6)] for x, y in loop] for loop in loops],
        })

    volume = 0.0
    for i in range(len(records) - 1):
        dz = records[i + 1]['z_m'] - records[i]['z_m']
        volume += 0.5 * (records[i]['area_m2'] + records[i + 1]['area_m2']) * dz
    return records, volume


def export_neutral():
    clear_scene()
    ob, before, after = make_neutral()
    slices, volume = measure_slices(ob)
    with open(os.path.join(OUT_DIR, 'slice_profiles.json'), 'w', encoding='utf-8') as f:
        json.dump({'control_slices': CONTROL_SLICES, 'measured_slices': slices, 'volume_m3': volume}, f, indent=2)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, 'neutral.glb'), export_format='GLB', use_selection=True)
    return before, after, slices, volume


def add_slice_curves(obj, records):
    # Visualization only: measured contours are drawn as thin curves around the
    # real generated mesh. They are never exported as character geometry.
    curve_mat = material('SliceGuide', (0.18, 0.52, 0.88))
    chosen = records[::4]
    for rec in chosen:
        for li, loop in enumerate(rec['loops']):
            if len(loop) < 3:
                continue
            cu = bpy.data.curves.new(f'Slice_{rec["index"]}_{li}', 'CURVE')
            cu.dimensions = '3D'
            cu.bevel_depth = 0.0015
            cu.bevel_resolution = 0
            sp = cu.splines.new('POLY')
            sp.points.add(len(loop))
            z = rec['z_m']
            for i, (x, y) in enumerate(loop):
                sp.points[i].co = (x, y, z, 1.0)
            sp.points[-1].co = (loop[0][0], loop[0][1], z, 1.0)
            obc = bpy.data.objects.new(cu.name, cu)
            bpy.context.collection.objects.link(obc)
            obc.data.materials.append(curve_mat)


def studio():
    sc = bpy.context.scene
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 1100
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.engine = 'BLENDER_EEVEE'
    sc.world.color = (0.025, 0.028, 0.034)
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass

    bpy.ops.mesh.primitive_plane_add(size=7, location=(0, 0, -0.006))
    bpy.context.object.data.materials.append(material('Floor', (0.08, 0.083, 0.09)))

    for name, loc, energy, size in [
        ('Key', (-3.0, -4.0, 4.0), 1050, 2.9),
        ('Fill', (3.0, -3.0, 2.6), 430, 2.6),
        ('Rim', (0.0, 3.4, 3.4), 700, 2.1),
    ]:
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.shape = 'DISK'
        ld.size = size
        lob = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(lob)
        lob.location = loc
        lob.rotation_euler = (Vector((0, 0, 0.82)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cd)
    bpy.context.collection.objects.link(cam)
    cam.location = (1.55, -5.8, 1.48)
    cam.rotation_euler = (Vector((0, 0, 0.80)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = 70
    sc.camera = cam


def render_previews(records):
    clear_scene()
    ob, _, _ = make_neutral()
    ob.rotation_euler[2] = math.radians(2.5)
    studio()
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR, 'neutral-preview.png')
    bpy.ops.render.render(write_still=True)

    # Slice-lattice validation preview
    clear_scene()
    ob, _, _ = make_neutral()
    add_slice_curves(ob, records)
    studio()
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR, 'neutral-slices.png')
    bpy.ops.render.render(write_still=True)


before, after, slices, volume = export_neutral()
render_previews(slices)
metrics = {
    'style': 'slice-driven-cute-neutral-basemesh-v12',
    'source': 'Anny/MPFB2 CC0 full body surface only',
    'neutral_only': True,
    'male_female_split': False,
    'extra_character_geometry': False,
    'hair': False,
    'face_addons': False,
    'clothing': False,
    'props': False,
    'target_height_m': TARGET_HEIGHT,
    'target_visual_head_ratio': 6.3,
    'target_tris': TARGET_TRIS,
    'tris_before': before,
    'tris': after,
    'control_slice_count': len(CONTROL_SLICES),
    'measured_slice_count': len(slices),
    'estimated_volume_m3': volume,
    'shading': 'smooth normals on low-poly topology',
    'method': 'control slice lattice -> interpolated body deformation -> symmetric QEM -> real mesh-plane slicing -> sectional verification',
    'blender_version': '.'.join(map(str, bpy.app.version)),
}
with open(os.path.join(OUT_DIR, 'metrics.json'), 'w', encoding='utf-8') as f:
    json.dump(metrics, f, indent=2)
print('SLICE_NEUTRAL_V12_METRICS', json.dumps(metrics))
