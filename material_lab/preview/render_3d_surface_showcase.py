#!/usr/bin/env python3
"""Specialized geometry validation pass.

The old PIL line/polygon grass/fur/fire mock previews were intentionally removed:
they were not true 3D material validation. This pass now only overrides the
approved sandstone master with a real radial Height displacement whose scale is
fitted from the generated Height distribution.

Sandstone displacement policy:
  median = 0 sigma
  +1 sigma ~= +14% radius
  +2 sigma ~= +28% radius
  +3 sigma ~= +42% radius
  positive tail cap = +44%
  negative tail cap = -4%
"""
from pathlib import Path
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/generated-materials")
S = 1000
CX, CY, R = 500.0, 465.0, 300.0
OUT_PER_SIGMA = 0.14
MAX_OUT = 0.44
MAX_IN = 0.04
ITERATIONS = 9


def srgb_to_linear(x):
    return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    return np.where(x <= .0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - .055)


def norm(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6)


def bilinear(tex, u, v):
    h, w = tex.shape[:2]
    u = np.mod(u, 1.0); v = np.mod(v, 1.0)
    x = u * (w - 1); y = (1 - v) * (h - 1)
    x0 = np.floor(x).astype(np.int32); y0 = np.floor(y).astype(np.int32)
    x1 = (x0 + 1) % w; y1 = (y0 + 1) % h
    if tex.ndim == 3:
        tx = (x - x0)[..., None]; ty = (y - y0)[..., None]
    else:
        tx = x - x0; ty = y - y0
    return (tex[y0, x0] * (1 - tx) + tex[y0, x1] * tx) * (1 - ty) + (tex[y1, x0] * (1 - tx) + tex[y1, x1] * tx) * ty


def sphere_uv(n):
    u = (0.5 + np.arctan2(n[..., 2], n[..., 0]) / (2 * np.pi)) * 2.10
    v = (0.5 - np.arcsin(np.clip(n[..., 1], -1, 1)) / np.pi) * 2.10
    return u, v


def displacement_stats(height):
    # Fit a truncated normal-like z scale to the actual generated Height field.
    # P99.5 is treated as +3 sigma, so rare peaks reach ~42% without lifting
    # every slab by the same amount.
    h50 = float(np.percentile(height, 50.0))
    h005 = float(np.percentile(height, 0.5))
    h995 = float(np.percentile(height, 99.5))
    sigma_pos = max((h995 - h50) / 3.0, 0.012)
    sigma_neg = max((h50 - h005) / 2.0, 0.012)
    return h50, sigma_pos, sigma_neg, h005, h995


def sigma_displacement(h, h50, sigma_pos, sigma_neg):
    zp = np.maximum((h - h50) / sigma_pos, 0.0)
    zn = np.maximum((h50 - h) / sigma_neg, 0.0)
    outward = np.minimum(zp * OUT_PER_SIGMA, MAX_OUT)
    inward = np.minimum(zn * (MAX_IN / 2.0), MAX_IN)
    return outward - inward


def displaced_geometry(sx, sy, height, stats):
    h50, sigma_pos, sigma_neg, _, _ = stats
    qx, qy = sx.copy(), sy.copy()
    disp = np.zeros_like(sx, dtype=np.float32)
    for _ in range(ITERATIONS):
        q2 = qx * qx + qy * qy
        qz = np.sqrt(np.clip(1 - q2, 0, 1))
        n = norm(np.stack([qx, qy, qz], -1))
        u, v = sphere_uv(n)
        hs = bilinear(height, u, v)
        disp = sigma_displacement(hs, h50, sigma_pos, sigma_neg)
        radial = 1.0 + disp
        qx = sx / radial; qy = sy / radial
    q2 = qx * qx + qy * qy
    mask = q2 <= 1.0
    qz = np.sqrt(np.clip(1 - q2, 0, 1))
    return norm(np.stack([qx, qy, qz], -1)), mask, q2, disp


def studio_bg():
    yy, xx = np.mgrid[0:S, 0:S]
    gy = np.linspace(0, 1, S)[:, None, None]
    top = np.array([.78, .81, .85], np.float32)[None, None, :]
    bot = np.array([.16, .18, .20], np.float32)[None, None, :]
    bg = np.repeat(top * (1 - gy) + bot * gy, S, axis=1)
    shadow = np.exp(-(((xx - CX) / (R * 1.0)) ** 2 + ((yy - (CY + R * 1.43)) / (R * .16)) ** 2) * 2.5)
    bg *= 1 - .30 * shadow[..., None]
    return np.clip(bg, 0, 1)


def render_sandstone(d: Path, name: str):
    base = srgb_to_linear(np.asarray(Image.open(d / f"{name}_baseColor.png").convert("RGB"), dtype=np.float32) / 255.0)
    normal = np.asarray(Image.open(d / f"{name}_normal.png").convert("RGB"), dtype=np.float32) / 255.0
    rough = np.asarray(Image.open(d / f"{name}_roughness.png").convert("L"), dtype=np.float32) / 255.0
    ao = np.asarray(Image.open(d / f"{name}_ao.png").convert("L"), dtype=np.float32) / 255.0
    height = np.asarray(Image.open(d / f"{name}_height.png").convert("L"), dtype=np.float32) / 255.0

    stats = displacement_stats(height)
    yy, xx = np.mgrid[0:S, 0:S]
    sx = (xx - CX) / R; sy = (CY - yy) / R
    ng, mask, r2, disp = displaced_geometry(sx, sy, height, stats)
    u, v = sphere_uv(ng)

    bc = bilinear(base, u, v)
    nt = bilinear(normal, u, v) * 2 - 1
    rr = np.clip(bilinear(rough, u, v), .08, 1)
    aa = bilinear(ao, u, v)

    t = norm(np.stack([-ng[..., 2], np.zeros_like(sx), ng[..., 0]], -1))
    b = norm(np.cross(ng, t))
    n = norm(t * nt[..., 0:1] + b * nt[..., 1:2] + ng * np.maximum(nt[..., 2:3], .08))

    # Painterly studio lighting: broad warm key, cool fill, warm lower bounce.
    color = bc * (.20 + .34 * aa[..., None])
    lights = [
        (norm(np.array([[[-.62, .68, .39]]], np.float32))[0, 0], 2.35, np.array([1.00, .91, .80], np.float32)),
        (norm(np.array([[[ .58, .18, .80]]], np.float32))[0, 0], 1.15, np.array([.66, .80, 1.00], np.float32)),
        (norm(np.array([[[-.10,-.82, .55]]], np.float32))[0, 0], .65, np.array([1.00, .60, .38], np.float32)),
    ]
    view = np.array([0, 0, 1], np.float32)
    for light, intensity, tint in lights:
        ndl = np.clip((n * light).sum(-1), 0, 1)
        # Broad diffuse plus restrained rough-stone highlight.
        color += bc * ndl[..., None] * intensity * tint * .50
        hvec = (light + view); hvec = hvec / max(np.linalg.norm(hvec), 1e-6)
        ndh = np.clip((n * hvec).sum(-1), 0, 1)
        shininess = 5.0 + 40.0 * (1 - rr)
        spec = np.power(ndh, shininess) * (.025 + .09 * (1 - rr))
        color += spec[..., None] * tint * intensity

    # Slight cool ambient on upward/camera-facing planes preserves the established palette.
    color += np.clip(n[..., 1], 0, 1)[..., None] * np.array([.045, .060, .075], np.float32)
    color *= .88 + .12 * aa[..., None]

    c = np.clip(color * 1.04, 0, None)
    a1, b1, c1, d1, e1 = 2.51, .03, 2.43, .59, .14
    c = (c * (a1 * c + b1)) / (c * (c1 * c + d1) + e1)
    c = linear_to_srgb(np.clip(c, 0, 1))

    bg = studio_bg()
    edge = np.clip((1 - r2) * R * .9, 0, 1)[..., None] * mask[..., None].astype(np.float32)
    img = bg * (1 - edge) + c * edge
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGB")

    draw = ImageDraw.Draw(out)
    try:
        f1 = ImageFont.truetype("DejaVuSans.ttf", 27); f2 = ImageFont.truetype("DejaVuSans.ttf", 18)
    except Exception:
        f1 = ImageFont.load_default(); f2 = f1
    draw.rounded_rectangle((28, 26, 930, 104), radius=18, fill=(18, 18, 20))
    draw.text((48, 40), name, fill=(245, 245, 245), font=f1)
    draw.text((48, 74), "Gaussian Height · 1sigma=14% · 2sigma=28% · 3sigma=42% · cap=44%", fill=(190, 195, 200), font=f2)
    out.save(d / "preview-sphere.png")
    out.save(d / "preview-gaussian-height.png")

    h50, sigma_pos, sigma_neg, h005, h995 = stats
    visible_disp = disp[mask]
    audit = {
        "distribution": "truncated-normal-zscore",
        "medianHeight": h50,
        "positiveSigmaHeight": sigma_pos,
        "negativeSigmaHeight": sigma_neg,
        "heightP00_5": h005,
        "heightP99_5": h995,
        "outwardPerSigma": OUT_PER_SIGMA,
        "maxOutward": MAX_OUT,
        "maxInward": MAX_IN,
        "actualDisplacementMin": float(np.min(visible_disp)),
        "actualDisplacementP50": float(np.percentile(visible_disp, 50)),
        "actualDisplacementP84": float(np.percentile(visible_disp, 84)),
        "actualDisplacementP97_7": float(np.percentile(visible_disp, 97.7)),
        "actualDisplacementMax": float(np.max(visible_disp)),
    }
    (d / "preview-gaussian-height-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")


def process(d: Path):
    manifest_path = d / "manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("preset") != "vfLayeredSandstonePainted":
        return
    name = manifest.get("material") or d.name
    render_sandstone(d, name)


for directory in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    process(directory)
