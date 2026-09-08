import bpy
import json
import math
import os
import sys
import urllib.request
from mathutils import Vector

OUT_DIR = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.path.abspath('artifacts/cute-neutral-human')
os.makedirs(OUT_DIR, exist_ok=True)

# Cute Neutral Basemesh v11
# -------------------------
# One neutral body only. No male/female split, no hair, no facial add-ons,
# no clothing, no props, no extra character shells.
#
# Source: the original CC0 Anny/MPFB2 full body surface.
# Styling goal: a clean Japanese 3D-game basemesh proportion language:
# slightly larger head, short/compact torso, narrow shoulders, slim but healthy
# limbs, small hands/feet, simple silhouette. Low-poly topology, smooth normals.

BASE_URL = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2/3dobjs/base.obj'
TARGET_TRIS = 960
TARGET_HEIGHT = 1.62


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'voxel-frontier-cute-neutral-v11'})
    return urllib.request.urlopen(req, timeout=60).read().decode('utf-8')


def parse_obj_body(text):
    verts = []
    faces = []
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
    up = order[0]
    width = order[1]
    depth = order[2]
    return mins, maxs, ranges, width, depth, up


def gauss(x, c, s):
    return math.exp(-0.5 * ((x - c) / s) ** 2)


def smoothstep(a, b, x):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    t = (x - a) / (b - a)
    return t * t * (3.0 - 2.0 * t)


def vertical_remap(q):
    # Compact Japanese-game character proportions, not chibi:
    # visually around ~6 heads tall with a shorter torso and slightly larger head.
    hip = 0.515
    neck = 0.842
    leg_s = 1.025
    torso_s = 0.900
    head_s = 1.160

    def raw(t):
        if t <= hip:
            return t * leg_s
        if t <= neck:
            return hip * leg_s + (t - hip) * torso_s
        return hip * leg_s + (neck - hip) * torso_s + (t - neck) * head_s

    return raw(q) / raw(1.0)


def style_neutral(verts, faces):
    mins, maxs, ranges, width, depth, up = axis_frame(verts)
    H = ranges[up]
    cw = (mins[width] + maxs[width]) * 0.5
    cd = (mins[depth] + maxs[depth]) * 0.5
    used = sorted({i for f in faces for i in f})
    remap = {old: i for i, old in enumerate(used)}
    out = []

    for old in used:
        v = verts[old]
        x = (v[width] - cw) / H
        y = (v[depth] - cd) / H
        q = (v[up] - mins[up]) / H
        z = vertical_remap(q) * TARGET_HEIGHT

        # Head: clearly larger than realistic, but not chibi.
        head = smoothstep(0.842, 0.900, q)
        x *= 1.0 + 0.145 * head
        y *= 1.0 + 0.115 * head

        # Softer, compact lower face / jaw, still the same body mesh.
        jaw = gauss(q, 0.872, 0.027)
        x *= 1.0 - 0.030 * jaw
        y *= 1.0 - 0.012 * jaw

        # Slim neck and softer shoulder entry.
        neck_gate = gauss(q, 0.826, 0.030)
        x *= 1.0 - 0.125 * neck_gate
        y *= 1.0 - 0.060 * neck_gate

        # Neutral cute torso: narrow shoulders, compact ribcage, slight waist,
        # almost straight pelvis. Avoid clearly male or female cues.
        sx = (1.0
              - 0.065 * gauss(q, 0.785, 0.058)
              - 0.030 * gauss(q, 0.690, 0.082)
              - 0.040 * gauss(q, 0.585, 0.060)
              + 0.018 * gauss(q, 0.505, 0.060))
        sy = (1.0
              - 0.020 * gauss(q, 0.690, 0.085)
              + 0.010 * gauss(q, 0.505, 0.070))
        x *= sx
        y *= sy

        # Slightly shorten the A-pose arms, keep them slender but not needle-thin.
        arm_gate = gauss(q, 0.680, 0.175)
        ax = abs(x)
        torso_edge = 0.108
        if ax > torso_edge:
            collapsed = torso_edge + (ax - torso_edge) * 0.905
            ax = ax * (1.0 - arm_gate) + collapsed * arm_gate
            x = math.copysign(ax, x)
            y *= 1.0 + 0.035 * arm_gate

        # Hands: compress finger spread into a small, clean neutral hand silhouette.
        # No extra geometry and no deletion; this only repositions the source vertices.
        hand_gate = gauss(q, 0.565, 0.105)
        hand_root = 0.245
        if abs(x) > hand_root and hand_gate > 0.05:
            ax = abs(x)
            ax = hand_root + (ax - hand_root) * 0.30
            x = math.copysign(ax, x)
            y *= 1.0 - 0.48 * hand_gate
            zc = 0.565 * TARGET_HEIGHT
            z = zc + (z - zc) * (1.0 - 0.52 * hand_gate)

        # Legs: slim with a soft thigh-knee-calf rhythm; not stick-like.
        thigh = gauss(q, 0.365, 0.110)
        knee = gauss(q, 0.255, 0.042)
        calf = gauss(q, 0.170, 0.075)
        ankle = gauss(q, 0.070, 0.036)
        x *= 1.0 + 0.012 * thigh - 0.012 * knee + 0.012 * calf - 0.020 * ankle
        y *= 1.0 + 0.010 * thigh + 0.010 * calf

        # Feet: small, short and stable; avoid pointed retro toes.
        foot = 1.0 - smoothstep(0.032, 0.090, q)
        if foot > 0.0:
            x *= 1.0 + 0.015 * foot
            y *= 1.0 - 0.120 * foot
            if q < 0.018:
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
        bsdf.inputs['Roughness'].default_value = 0.88
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


def lowpoly_smooth(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    tri = obj.modifiers.new('Triangulate', 'TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri.name)
    before = tri_count(obj)

    dec = obj.modifiers.new('CuteNeutral_QEM', 'DECIMATE')
    dec.decimate_type = 'COLLAPSE'
    dec.ratio = max(0.001, min(1.0, TARGET_TRIS / max(before, 1)))
    dec.use_collapse_triangulate = True
    try:
        dec.use_symmetry = True
        dec.symmetry_axis = 'X'
    except Exception:
        pass
    bpy.ops.object.modifier_apply(modifier=dec.name)

    # Low polygon count, but smooth normals for the clean anime-game silhouette.
    for p in obj.data.polygons:
        p.use_smooth = True
    obj.data.update()
    return before, tri_count(obj)


def make_neutral():
    verts, faces = parse_obj_body(fetch_text(BASE_URL))
    verts, faces = style_neutral(verts, faces)
    ob = mesh_from_data('CuteNeutralBaseV11', verts, faces, material('NeutralSkin', (0.76, 0.73, 0.71)))
    before, after = lowpoly_smooth(ob)
    return ob, before, after


def export_neutral():
    clear_scene()
    ob, before, after = make_neutral()
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, 'neutral.glb'), export_format='GLB', use_selection=True)
    return before, after


def studio():
    sc = bpy.context.scene
    sc.render.resolution_x = 1100
    sc.render.resolution_y = 1200
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.engine = 'BLENDER_EEVEE'
    sc.world.color = (0.028, 0.030, 0.035)
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass

    bpy.ops.mesh.primitive_plane_add(size=7, location=(0, 0, -0.006))
    bpy.context.object.data.materials.append(material('Floor', (0.085, 0.088, 0.095)))

    for name, loc, energy, size in [
        ('Key', (-3.0, -4.0, 4.0), 1000, 2.8),
        ('Fill', (3.0, -3.0, 2.6), 420, 2.6),
        ('Rim', (0.0, 3.4, 3.4), 680, 2.1),
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
    cam.location = (1.45, -5.8, 1.52)
    cam.rotation_euler = (Vector((0, 0, 0.80)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = 72
    sc.camera = cam


def render_preview():
    clear_scene()
    ob, before, after = make_neutral()
    ob.rotation_euler[2] = math.radians(3.0)
    studio()
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR, 'neutral-preview.png')
    bpy.ops.render.render(write_still=True)
    return before, after


before, after = export_neutral()
render_preview()
metrics = {
    'style': 'cute-neutral-jp-game-basemesh-v11',
    'source': 'Anny/MPFB2 CC0 full body surface only',
    'neutral_only': True,
    'male_female_split': False,
    'extra_character_geometry': False,
    'hair': False,
    'face_addons': False,
    'clothing': False,
    'props': False,
    'target_tris': TARGET_TRIS,
    'tris_before': before,
    'tris': after,
    'target_visual_head_ratio': 6.0,
    'shading': 'smooth normals on low-poly topology',
    'method': 'full neutral basemesh -> cute proportion remap -> hand/foot simplification -> symmetric QEM -> smooth normals',
    'blender_version': '.'.join(map(str, bpy.app.version)),
}
with open(os.path.join(OUT_DIR, 'metrics.json'), 'w', encoding='utf-8') as f:
    json.dump(metrics, f, indent=2)
print('CUTE_NEUTRAL_V11_METRICS', json.dumps(metrics))
