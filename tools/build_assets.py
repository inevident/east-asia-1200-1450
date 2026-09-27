"""
Asset pipeline: Blender renders -> web assets.

For each scene:
  * gentle, consistent colour grade (contrast curve, split-tone, vignette, fine grain)
  * responsive WebP sizes (2560 / 1600 / 960 wide)
  * a parallax depth map derived from Blender's Mist pass
    (mist is linear 0..1 over [start, start+depth]; we convert to disparity 1/z,
    normalise, blur and dilate near regions so the WebGL parallax has no halos)
  * a tiny blurred placeholder (LQIP) embedded in the manifest

Run:  python3 tools/build_assets.py
"""
import base64
import io
import json
import os
import subprocess

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "blender", "renders")
OUT = os.path.join(ROOT, "public", "scenes")
os.makedirs(OUT, exist_ok=True)

# slug: (mist_start, mist_depth, focal point x, y for cover-cropping, grade strength)
SCENES = {
    "hero":          (20.0, 6000.0, 0.66, 0.45, 1.0),
    "political":     (0.5, 400.0, 0.62, 0.45, 0.8),
    "intellectual":  (0.25, 0.9, 0.62, 0.55, 0.8),
    "religious":     (0.5, 40.0, 0.5, 0.5, 0.8),
    "artistic":      (15.0, 260.0, 0.45, 0.5, 0.9),
    "technological": (10.0, 1500.0, 0.62, 0.5, 0.9),
    "economic":      (0.4, 1.3, 0.45, 0.5, 0.8),
    "social":        (60.0, 1800.0, 0.5, 0.62, 0.9),
}
WIDTHS = (2560, 1600, 960)


def grade(img, strength=1.0, seed=0):
    """img float32 RGB 0..1 -> graded image."""
    x = img.copy()
    # soft S-curve around mid grey
    x = x + strength * 0.12 * (x - x ** 2) * (2 * x - 1) * -1.0
    x = np.clip(x, 0, 1)
    # split tone: warm highlights, slightly cool shadows
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    warm = np.array([1.035, 1.0, 0.955], np.float32)
    cool = np.array([0.975, 0.99, 1.03], np.float32)
    tone = cool + (warm - cool) * np.clip(lum * 1.4 - 0.1, 0, 1)
    x = x * (1 + (tone - 1) * strength)
    # gentle saturation lift
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = lum + (x - lum) * (1 + 0.06 * strength)
    # vignette
    h, w = x.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    vig = 1 - 0.16 * strength * np.clip((r - 0.45) / 0.55, 0, 1) ** 1.6
    x = x * vig[..., None]
    # fine luminance grain
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 0.006, (h, w, 1)).astype(np.float32)
    x = x + g
    return np.clip(x, 0, 1)


def to_webp(arr_u8, path, q):
    Image.fromarray(arr_u8).save(path, "WEBP", quality=q, method=6)


def depth_map(slug, start, depth, w_out=1280):
    p = os.path.join(REN, f"{slug}_depthmist.png")
    m = cv2.imread(p, cv2.IMREAD_UNCHANGED).astype(np.float32)
    if m.ndim == 3:
        m = m[..., 0]
    m /= 65535.0 if m.max() > 255 else 255.0
    z = start + np.clip(m, 0, 1) * depth
    disp = 1.0 / np.maximum(z, 1e-4)
    lo, hi = np.percentile(disp, 1.0), np.percentile(disp, 99.5)
    n = np.clip((disp - lo) / max(hi - lo, 1e-9), 0, 1)
    # compress the far range so distant layers still separate
    n = n ** 0.6
    h0, w0 = n.shape
    h_out = int(round(h0 * w_out / w0))
    n = cv2.resize(n, (w_out, h_out), interpolation=cv2.INTER_AREA)
    # dilate near objects slightly then blur: avoids background 'halos' at silhouettes
    k = np.ones((5, 5), np.uint8)
    n8 = (n * 255).astype(np.uint8)
    n8 = cv2.dilate(n8, k, iterations=1)
    n8 = cv2.GaussianBlur(n8, (0, 0), 2.2)
    out = os.path.join(OUT, f"{slug}-depth.webp")
    Image.fromarray(n8).convert("L").save(out, "WEBP", quality=86, method=6)
    return out, float(n.mean())


def lqip(arr_u8):
    im = Image.fromarray(arr_u8).resize((32, 18), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=40)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


manifest = {}
for i, (slug, (start, depth, fx, fy, gs)) in enumerate(SCENES.items()):
    src = os.path.join(REN, f"{slug}.png")
    if not os.path.exists(src):
        print("missing", src)
        continue
    img = np.asarray(Image.open(src).convert("RGB"), np.float32) / 255.0
    graded = (grade(img, gs, seed=i) * 255 + 0.5).astype(np.uint8)
    sizes = {}
    for w in WIDTHS:
        h = int(round(graded.shape[0] * w / graded.shape[1]))
        arr = np.asarray(Image.fromarray(graded).resize((w, h), Image.LANCZOS)) if w != graded.shape[1] else graded
        path = os.path.join(OUT, f"{slug}-{w}.webp")
        to_webp(arr, path, 84 if w >= 2560 else 80)
        sizes[w] = os.path.getsize(path)
    dpath, dmean = depth_map(slug, start, depth)
    manifest[slug] = {
        "w": int(graded.shape[1]), "h": int(graded.shape[0]),
        "focal": [fx, fy],
        "lqip": lqip(graded),
        "depthMean": round(dmean, 3),
        "bytes": sizes,
        "depthBytes": os.path.getsize(dpath),
    }
    print(f"{slug:14s} " + " ".join(f"{w}:{b // 1024}KB" for w, b in sizes.items()) + f" depth:{os.path.getsize(dpath) // 1024}KB mean={dmean:.2f}")

with open(os.path.join(OUT, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=1)
print("manifest written")
