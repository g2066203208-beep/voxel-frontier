#!/usr/bin/env python3
"""Sandstone macro-geometry diagnostic pass.

This legacy diagnostic renders a low-pass Gaussian interpretation of the
sandstone Height field for comparison/audit only. It MUST NOT overwrite the
canonical `preview-sphere.png`: extreme sandstone relief is now validated by
`render_sandstone_mesh_preview.py` using a real tessellated UV sphere, vertex
Height displacement and a Z-buffer.

Continuous rock-shell diagnostic policy:
  baseline/median outward shell ~= +22% radius
  positive sigma ~= 7% radius
  +3 sigma ~= +43% radius
  positive cap = +44%
  negative deviations are compressed to 20% strength
  hard minimum shell = +16%
"""
from pathlib import Path
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/generated-materials")
S = 1000
CX, CY, R = 500.0, 465.0, 285.0
MEAN_OUT = 0.22
POS_SIGMA = 0.07
NEG_SIGMA_SCALE = 0.20
MIN_OUT = 0.16
MAX_OUT = 0.44
ITERATIONS = 10
MACRO_SIGMA_PX = 18.0
MID_SIGMA_PX = 6.0
MACRO_WEIGHT = 0.78


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


def periodic_gaussian(tex, sigma_px):
    """Periodic Gaussian convolution in Fourier space; preserves tile seams."""
    h, w = tex.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    kernel = np.exp(-2.0 * (np.pi ** 2) * (sigma_px ** 2) * (fx * fx + fy * fy))
    return np.fft.ifft2(np.fft.fft2(tex) * kernel).real.astype(np.float32)


def geometry_height(height):
    macro = periodic_gaussian(height, MACRO_SIGMA_PX)
    mid = periodic_gaussian(height, MID_SIGMA_PX)
    return (macro * MACRO_WEIGHT + mid * (1.0 - MACRO_WEIGHT)).astype(np.float32)


def displacement_stats(height):
    h50 = float(np.percentile(height, 50.0))
    h005 = float(np.percentile(height, 0.5))
    h995 = float(np.percentile(height, 99.5))
    sigma_h = max((h995 - h50) / 3.0, 0.010)
    return h50, sigma_h, h005, h995


def sigma_displacement(h, h50, sigma_h):
    z = (h - h50) / sigma_h
    pos = np.maximum(z, 0.0) * POS_SIGMA
    neg = np.minimum(z, 0.0) * POS_SIGMA * NEG_SIGMA_SCALE
    return np.clip(MEAN_OUT + pos + neg, MIN_OUT, MAX_OUT)


def displaced_geometry(sx, sy, height, stats):
    h50, sigma_h, _, _ = stats
    qx, qy = sx.copy(), sy.copy()
    disp = np.zeros_like(sx, dtype=np.float32)
    for _ in range(ITERATIONS):
        q2 = qx * qx + qy * qy
        qz = np.sqrt(np.clip(1 - q2, 0, 1))
        n = norm(np.stack([qx, qy, qz], -1))
        u, v = sphere_uv(n)
        hs = bilinear(height, u, v)
        disp = sigma_displacement(hs, h50, sigma_h)
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
    shadow = np.exp(-(((xx - CX) / (R * 1.10)) ** 2 + ((yy - (CY + R * 1.62)) / (R * .17)) ** 2) * 2.5)
    bg *= 1 - .30 * shadow[..., None]
    return np.clip(bg, 0, 1)


def render_sandstone(d: Path, name: str):
    base = srgb_to_linear(np.asarray(Image.open(d / f"{name}_baseColor.png").convert("RGB"), dtype=np.float32) / 255.0)
    normal = np.asarray(Image.open(d / f"{name}_normal.png").convert("RGB"), dtype=np.float32) / 255.0
    rough = np.asarray(Image.open(d / f"{name}_roughness.png").convert("L"), dtype=np.float32) / 255.0
    ao = np.asarray(Image.open(d / f"{name}_ao.png").convert("L"), dtype=np.float32) / 255.0
    height = np.asarray(Image.open(d / f"{name}_height.png").convert("L"), dtype=np.float32) / 255.0
    height_geom = geometry_height(height)

    stats = displacement_stats(height_geom)
    yy, xx = np.mgrid[0:S, 0:S]
    sx = (xx - CX) / R; sy = (CY - yy) / R
    ng, mask, r2, disp = displaced_geometry(sx, sy, height_geom, stats)
    u, v = sphere_uv(ng)

    bc = bilinear(base, u, v)
    nt = bilinear(normal, u, v) * 2 - 1
    rr = np.clip(bilinear(rough, u, v), .08, 1)
    aa = bilinear(ao, u, v)

    t = norm(np.stack([-ng[..., 2], np.zeros_like(sx), ng[..., 0]], -1))
    b = norm(np.cross(ng, t))
    n = norm(t * nt[..., 0:1] + b * nt[..., 1:2] + ng * np.maximum(nt[..., 2:3], .08))

    color = bc * (.20 + .34 * aa[..., None])
    lights = [
        (norm(np.array([[[-.62, .68, .39]]], np.float32))[0, 0], 2.35, np.array([1.00, .91, .80], np.float32)),
        (norm(np.array([[[ .58, .18, .80]]], np.float32))[0, 0], 1.15, np.array([.66, .80, 1.00], np.float32)),
        (norm(np.array([[[-.10,-.82, .55]]], np.float32))[0, 0], .65, np.array([1.00, .60, .38], np.float32)),
    ]
    view = np.array([0, 0, 1], np.float32)
    for light, intensity, tint in lights:
        ndl = np.clip((n * light).sum(-1), 0, 1)
        color += bc * ndl[..., None] * intensity * tint * .50
        hvec = light + view; hvec = hvec / max(np.linalg.norm(hvec), 1e-6)
        ndh = np.clip((n * hvec).sum(-1), 0, 1)
        shininess = 5.0 + 40.0 * (1 - rr)
        spec = np.power(ndh, shininess) * (.025 + .09 * (1 - rr))
        color += spec[..., None] * tint * intensity

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
    draw.rounded_rectangle((28, 26, 970, 104), radius=18, fill=(18, 18, 20))
    draw.text((48, 40), name, fill=(245, 245, 245), font=f1)
    draw.text((48, 74), "legacy Gaussian diagnostic · mean 22% · +3sigma 43% · cap 44%", fill=(190, 195, 200), font=f2)
    # Diagnostic only. Canonical preview-sphere.png is owned by the true mesh renderer.
    out.save(d / "preview-gaussian-height.png")

    h50, sigma_h, h005, h995 = stats
    visible_disp = disp[mask]
    audit = {
        "distribution": "asymmetric-truncated-normal-over-continuous-shell",
        "medianGeometryHeight": h50,
        "sigmaGeometryHeight": sigma_h,
        "geometryHeightP00_5": h005,
        "geometryHeightP99_5": h995,
        "meanOutward": MEAN_OUT,
        "positiveDisplacementSigma": POS_SIGMA,
        "negativeSigmaScale": NEG_SIGMA_SCALE,
        "threeSigmaOutward": MEAN_OUT + 3 * POS_SIGMA,
        "minOutward": MIN_OUT,
        "maxOutward": MAX_OUT,
        "macroGaussianSigmaPx": MACRO_SIGMA_PX,
        "midGaussianSigmaPx": MID_SIGMA_PX,
        "macroWeight": MACRO_WEIGHT,
        "actualDisplacementMin": float(np.min(visible_disp)),
        "actualDisplacementP05": float(np.percentile(visible_disp, 5)),
        "actualDisplacementP16": float(np.percentile(visible_disp, 16)),
        "actualDisplacementP50": float(np.percentile(visible_disp, 50)),
        "actualDisplacementP84": float(np.percentile(visible_disp, 84)),
        "actualDisplacementP97_7": float(np.percentile(visible_disp, 97.7)),
        "actualDisplacementMax": float(np.max(visible_disp)),
    }
    (d / "preview-gaussian-height-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")


def process(d: Path):
    manifest_path = d / "manifest.json"
    if not manifest_path.is_file(): return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("preset") != "vfLayeredSandstonePainted": return
    render_sandstone(d, manifest.get("material") or d.name)


for directory in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    process(directory)
