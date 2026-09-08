#!/usr/bin/env python3
from pathlib import Path
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/generated-materials")


def srgb_to_linear(x):
    return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    return np.where(x <= .0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - .055)


def norm(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-7)


def bilinear(tex, u, v):
    h, w = tex.shape[:2]
    u = np.mod(u, 1.0)
    v = np.mod(v, 1.0)
    x = u * (w - 1)
    y = (1 - v) * (h - 1)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = (x0 + 1) % w
    y1 = (y0 + 1) % h
    tx = x - x0
    ty = y - y0
    if tex.ndim == 3:
        tx = tx[..., None]
        ty = ty[..., None]
    return (tex[y0, x0] * (1 - tx) + tex[y0, x1] * tx) * (1 - ty) + (tex[y1, x0] * (1 - tx) + tex[y1, x1] * tx) * ty


def load_rgb(d, name, suffix):
    return np.asarray(Image.open(d / f"{name}_{suffix}.png").convert("RGB"), dtype=np.float32) / 255


def load_l(d, name, suffix):
    return np.asarray(Image.open(d / f"{name}_{suffix}.png").convert("L"), dtype=np.float32) / 255


def render_one(d: Path):
    name = d.name
    base_srgb = load_rgb(d, name, "baseColor")
    normal_tex = load_rgb(d, name, "normal")
    rough = load_l(d, name, "roughness")
    ao = load_l(d, name, "ao")
    height = load_l(d, name, "height")

    # A real tessellated sphere is required here. The legacy inverse screen-space
    # displacement approximation folds when relief is intentionally extreme.
    nlat, nlon = 100, 200
    vg = np.linspace(0, 1, nlat + 1, dtype=np.float32)
    ug = np.linspace(0, 1, nlon + 1, dtype=np.float32)
    U, V = np.meshgrid(ug, vg)
    lon = 2 * np.pi * (U - .5)
    lat = np.pi * (.5 - V)
    N0 = np.stack([np.cos(lat) * np.cos(lon), np.sin(lat), np.cos(lat) * np.sin(lon)], -1)

    # 1.25 repeats keeps the material clearly tileable while allowing the giant
    # hero outcrops to read as cliffs rather than many small cobbles.
    repeat_scale = 1.25
    tu = U * repeat_scale
    tv = V * repeat_scale
    hs = bilinear(height, tu, tv)
    h05, h50, h95 = [float(x) for x in np.percentile(height, [5, 50, 95])]
    span = max(h95 - h05, .08)
    hd = np.clip((hs - h50) / span, -.22, 1.12)

    # UV-sphere poles are singular. Fade only the tiny polar cap to prevent one
    # texel family from becoming an artificial needle; the rock body remains fully displaced.
    pole = np.clip(np.minimum(V, 1 - V) / .085, 0, 1)
    pole = pole * pole * (3 - 2 * pole)
    hd *= pole

    amp = .38
    radial = 1 + amp * hd
    P = N0 * radial[..., None]

    # Small presentation rotation; no camera trick is used to manufacture relief.
    ay = np.deg2rad(-4)
    ax = np.deg2rad(3)
    Ry = np.array([[np.cos(ay), 0, np.sin(ay)], [0, 1, 0], [-np.sin(ay), 0, np.cos(ay)]], np.float32)
    Rx = np.array([[1, 0, 0], [0, np.cos(ax), -np.sin(ax)], [0, np.sin(ax), np.cos(ax)]], np.float32)
    Rm = Rx @ Ry
    P = P @ Rm.T

    idx = np.arange((nlat + 1) * (nlon + 1), dtype=np.int32).reshape(nlat + 1, nlon + 1)
    a = idx[:-1, :-1].ravel()
    b = idx[:-1, 1:].ravel()
    c = idx[1:, 1:].ravel()
    e = idx[1:, :-1].ravel()
    tris = np.concatenate([np.stack([a, b, c], 1), np.stack([a, c, e], 1)], 0)

    Pf = P.reshape(-1, 3)
    tuf = tu.ravel()
    tvf = tv.ravel()
    fn = np.cross(Pf[tris[:, 1]] - Pf[tris[:, 0]], Pf[tris[:, 2]] - Pf[tris[:, 0]])
    vn = np.zeros_like(Pf)
    for k in range(3):
        np.add.at(vn, tris[:, k], fn)
    vn = norm(vn)

    S = 1100
    cx, cy, radius = S * .5, S * .47, S * .285
    sx = cx + Pf[:, 0] * radius
    sy = cy - Pf[:, 1] * radius
    sz = Pf[:, 2]

    zbuf = np.full((S, S), -1e9, np.float32)
    out_u = np.zeros((S, S), np.float32)
    out_v = np.zeros((S, S), np.float32)
    out_n = np.zeros((S, S, 3), np.float32)

    for t in tris:
        x0, x1, x2 = sx[t]
        y0, y1, y2 = sy[t]
        minx = max(0, int(math.floor(min(x0, x1, x2))))
        maxx = min(S - 1, int(math.ceil(max(x0, x1, x2))))
        miny = max(0, int(math.floor(min(y0, y1, y2))))
        maxy = min(S - 1, int(math.ceil(max(y0, y1, y2))))
        if maxx < minx or maxy < miny:
            continue
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-7:
            continue
        xs = np.arange(minx, maxx + 1, dtype=np.float32) + .5
        ys = np.arange(miny, maxy + 1, dtype=np.float32) + .5
        X, Y = np.meshgrid(xs, ys)
        w0 = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / den
        w1 = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-5) & (w1 >= -1e-5) & (w2 >= -1e-5)
        if not inside.any():
            continue
        depth = w0 * sz[t[0]] + w1 * sz[t[1]] + w2 * sz[t[2]]
        zb = zbuf[miny:maxy + 1, minx:maxx + 1]
        upd = inside & (depth > zb)
        if not upd.any():
            continue
        zb[upd] = depth[upd]
        ou = out_u[miny:maxy + 1, minx:maxx + 1]
        ov = out_v[miny:maxy + 1, minx:maxx + 1]
        on = out_n[miny:maxy + 1, minx:maxx + 1]
        iu = w0 * tuf[t[0]] + w1 * tuf[t[1]] + w2 * tuf[t[2]]
        iv = w0 * tvf[t[0]] + w1 * tvf[t[1]] + w2 * tvf[t[2]]
        nn = w0[..., None] * vn[t[0]] + w1[..., None] * vn[t[1]] + w2[..., None] * vn[t[2]]
        ou[upd] = iu[upd]
        ov[upd] = iv[upd]
        on[upd] = nn[upd]

    mask = zbuf > -1e8
    Ng = norm(np.where(mask[..., None], out_n, np.array([0, 0, 1], np.float32)))
    bc = srgb_to_linear(bilinear(base_srgb, out_u, out_v))
    nt = bilinear(normal_tex, out_u, out_v) * 2 - 1
    rr = np.clip(bilinear(rough, out_u, out_v), .04, 1)
    aa = bilinear(ao, out_u, out_v)

    T = norm(np.stack([-Ng[..., 2], np.zeros((S, S), np.float32), Ng[..., 0]], -1))
    B = norm(np.cross(Ng, T))
    N = norm(T * nt[..., 0:1] + B * nt[..., 1:2] + Ng * np.maximum(nt[..., 2:3], .08))

    color = bc * (.22 + .26 * aa[..., None])
    lights = [
        (np.array([-.58, .72, .38], np.float32), 2.55, np.array([1.0, .80, .58], np.float32)),
        (np.array([.68, .22, .70], np.float32), .95, np.array([.48, .62, 1.0], np.float32)),
        (np.array([-.15, -.78, .60], np.float32), .48, np.array([.75, .35, .28], np.float32)),
    ]
    Vcam = np.array([0, 0, 1], np.float32)
    for L, intensity, lcol in lights:
        L = L / np.linalg.norm(L)
        ndl = np.clip(np.sum(N * L, axis=-1), 0, 1)
        color += bc * ndl[..., None] * intensity * lcol[None, None, :] * .56
        H = (L + Vcam) / np.linalg.norm(L + Vcam)
        ndh = np.clip(np.sum(N * H, axis=-1), 0, 1)
        shin = 4 + 38 * (1 - rr)
        spec = np.power(ndh, shin) * (1 - rr) * .13
        color += spec[..., None] * intensity * lcol[None, None, :]

    rim = np.power(1 - np.clip(Ng[..., 2], 0, 1), 2.2)
    color += rim[..., None] * np.array([.075, .095, .16], np.float32)
    c = np.clip(color * 1.02, 0, None)
    A, Bc, Cc, Dd, Ee = 2.51, .03, 2.43, .59, .14
    c = (c * (A * c + Bc)) / (c * (Cc * c + Dd) + Ee)
    c = linear_to_srgb(np.clip(c, 0, 1))

    gy = np.linspace(0, 1, S, dtype=np.float32)[:, None, None]
    bg = np.repeat(
        np.array([.76, .80, .86], np.float32)[None, None, :] * (1 - gy)
        + np.array([.14, .17, .20], np.float32)[None, None, :] * gy,
        S,
        axis=1,
    )
    mimg = Image.fromarray((mask * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(22))
    shadow = np.roll(np.asarray(mimg, dtype=np.float32) / 255, int(S * .11), axis=0) * .20
    bg *= 1 - shadow[..., None]
    img = np.where(mask[..., None], c, bg)

    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(out)
    draw.rounded_rectangle((28, 28, S - 28, 105), radius=18, fill=(18, 18, 20))
    draw.text((50, 43), f"{name} · TRUE MESH DISPLACEMENT", fill="white")
    draw.text((50, 70), f"angular hero outcrops · amp {amp:.2f} · p50 {h50:.2f} · p95 {h95:.2f}", fill=(205, 205, 210))
    out = out.resize((1000, 1000), Image.Resampling.LANCZOS)
    out.save(d / "preview-sphere.png")

    metrics = {
        "renderer": "true_uv_sphere_mesh_zbuffer_v1",
        "repeatScale": repeat_scale,
        "displacementAmp": amp,
        "heightP05": h05,
        "heightP50": h50,
        "heightP95": h95,
        "heightSpanP05P95": span,
        "meshLatitudeSegments": nlat,
        "meshLongitudeSegments": nlon,
    }
    (d / "preview-mesh-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"material": name, **metrics}))


def main():
    count = 0
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        manifest_path = d / "manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("preset") == "vfLayeredSandstonePainted":
            render_one(d)
            count += 1
    if count == 0:
        print("No vfLayeredSandstonePainted material in this request; mesh preview skipped.")


if __name__ == "__main__":
    main()
